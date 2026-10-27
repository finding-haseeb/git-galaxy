#!/usr/bin/env python3
"""Bake the default universe so the site opens instantly, with no API calls.

Needs an authenticated `gh` CLI. Writes docs/snapshot.js in the same shape
the page builds from the live GitHub API.

    python3 tools/bake.py torvalds gaearon ...
"""
import json
import subprocess
import sys
import time
from pathlib import Path

USER = ["login", "name", "avatar_url", "followers", "public_repos", "created_at", "bio"]
REPO = ["name", "stargazers_count", "forks_count", "language", "created_at", "pushed_at", "description", "fork"]
EVENTS = {"PushEvent", "PullRequestEvent", "CreateEvent", "IssuesEvent"}


def api(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, check=True).stdout
    return json.loads(out)


def pick(obj, keys):
    return {k: obj.get(k) for k in keys}


def bake(login):
    user = pick(api(f"users/{login}"), USER)
    repos = [pick(r, REPO) for r in api(f"users/{login}/repos?per_page=100&sort=pushed")]
    for r in repos:
        r["description"] = (r["description"] or "")[:120]
    events = [
        {"type": e["type"], "repo": {"name": e["repo"]["name"]}, "created_at": e["created_at"]}
        for e in api(f"users/{login}/events/public?per_page=100")
        if e["type"] in EVENTS
    ]
    return {"user": user, "repos": repos, "events": events}


def main():
    logins = sys.argv[1:]
    if not logins:
        sys.exit("usage: bake.py LOGIN [LOGIN ...]")
    snap = {"baked": int(time.time()), "people": []}
    for login in logins:
        snap["people"].append(bake(login))
        print(f"✦ {login}")
    out = Path(__file__).resolve().parent.parent / "docs" / "snapshot.js"
    body = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out.write_text(f"window.SNAPSHOT={body};\n", encoding="utf-8")
    print(f"→ {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
