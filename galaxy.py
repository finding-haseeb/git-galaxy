#!/usr/bin/env python3
"""git-galaxy: turn any git repo's history into an interactive galaxy.

Every commit is a star. Every contributor is a color. The first commits
form the core; the newest ones are the outer edge. Zero dependencies.

    python3 galaxy.py [repo] [-o out.html] [--max N] [--no-open]
"""
import argparse
import html
import json
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

PALETTE_SIZE = 8  # must match PAL in the page; everyone past this is "others"


def git(repo, *args):
    try:
        res = subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit("git-galaxy: git is not installed")
    except subprocess.CalledProcessError as e:
        sys.exit("git-galaxy: " + (e.stderr.decode("utf-8", "replace").strip() or "git failed"))
    return res.stdout.decode("utf-8", "replace")


def read_history(repo):
    log = git(repo, "log", "--no-merges", "--numstat", "--pretty=format:%x1e%aN%x1f%at%x1f%s")
    counts, commits = {}, []
    for chunk in log.split("\x1e")[1:]:
        head, _, body = chunk.partition("\n")
        name, ts, subject = (head.split("\x1f", 2) + ["", "0", ""])[:3]
        lines = 0
        for row in body.splitlines():
            added, deleted = (row.split("\t") + ["", ""])[:2]
            # binary files report "-" instead of a count
            lines += int(added) if added.isdigit() else 0
            lines += int(deleted) if deleted.isdigit() else 0
        counts[name] = counts.get(name, 0) + 1
        commits.append((name, int(ts) if ts.isdigit() else 0, lines, subject[:140]))
    commits.sort(key=lambda c: c[1])
    return counts, commits


def build(repo, max_commits):
    root = git(repo, "rev-parse", "--show-toplevel").strip()
    counts, commits = read_history(repo)
    if not commits:
        sys.exit("git-galaxy: no commits to map yet")
    authors = sorted(counts.items(), key=lambda kv: -kv[1])
    index = {name: i for i, (name, _) in enumerate(authors)}
    total = len(commits)
    if total > max_commits:
        # sample evenly so the whole timeline keeps its shape
        step = total / max_commits
        commits = [commits[int(i * step)] for i in range(max_commits)]
    return {
        "repo": Path(root).name,
        "total": total,
        "authors": [[name, n] for name, n in authors],
        "commits": [[index[n], t, lines, s] for n, t, lines, s in commits],
    }


def render(data):
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    title = html.escape(f"{data['repo']} · git galaxy")
    return PAGE.replace("__TITLE__", title).replace("/*__DATA__*/null", payload)


def main():
    ap = argparse.ArgumentParser(description="Turn a git repo's history into an interactive galaxy.")
    ap.add_argument("repo", nargs="?", default=".", help="path to a git repo (default: .)")
    ap.add_argument("-o", "--out", help="where to write the HTML (default: a temp file)")
    ap.add_argument("--max", type=int, default=30000, help="max stars to draw (default: 30000)")
    ap.add_argument("--no-open", action="store_true", help="don't open the browser")
    args = ap.parse_args()

    data = build(args.repo, max(1, args.max))
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"{data['repo']}-galaxy.html"
    out.write_text(render(data), encoding="utf-8")
    people = len(data["authors"])
    print(f"✦ {data['total']:,} commits · {people:,} contributor{'s' if people > 1 else ''} → {out}")
    if not args.no_open:
        webbrowser.open(out.resolve().as_uri())


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#03040a;--fg:#e8ecff;--dim:#8a93b8;--panel:rgba(10,12,28,.72);--line:rgba(140,160,255,.18)}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:13px/1.4 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;overflow:hidden}
canvas{display:block;width:100vw;height:100vh;cursor:grab;touch-action:none}
canvas.drag{cursor:grabbing}
.hud{position:fixed;top:16px;left:16px;max-width:calc(100vw - 32px);pointer-events:none}
.hud h1{margin:0;font-size:20px;font-weight:650;letter-spacing:-.01em}
.hud .sub{color:var(--dim);margin-top:2px;font-variant-numeric:tabular-nums}
.hud .when{margin-top:10px;font-size:28px;font-weight:300;letter-spacing:.02em;font-variant-numeric:tabular-nums}
.legend{position:fixed;top:16px;right:16px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:6px;backdrop-filter:blur(8px);max-height:50vh;overflow:auto;min-width:190px}
.legend button{all:unset;box-sizing:border-box;display:flex;gap:8px;align-items:center;width:100%;padding:4px 8px;border-radius:6px;cursor:pointer}
.legend button:hover{background:rgba(255,255,255,.06)}
.legend button.off{opacity:.35}
.legend .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:170px}
.legend .n{margin-left:auto;color:var(--dim);padding-left:12px;font-variant-numeric:tabular-nums}
.dot{width:9px;height:9px;border-radius:50%;flex:none;box-shadow:0 0 8px currentColor}
.bar{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:5px;backdrop-filter:blur(8px)}
.bar button{all:unset;padding:7px 14px;border-radius:999px;cursor:pointer;white-space:nowrap}
.bar button:hover{background:rgba(255,255,255,.08)}
.bar button:focus-visible,.legend button:focus-visible{outline:2px solid #8fa2ff}
.tip{position:fixed;pointer-events:none;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;max-width:320px;backdrop-filter:blur(8px);display:none}
.tip b{display:block;font-weight:600;margin-bottom:2px;word-break:break-word}
.tip span{color:var(--dim)}
@media (max-width:640px){.legend{display:none}.hud .when{font-size:22px}.bar button{padding:7px 10px}}
</style>
</head>
<body>
<canvas id="c" aria-label="Commit history drawn as a galaxy"></canvas>
<div class="hud"><h1 id="name"></h1><div class="sub" id="sub"></div><div class="when" id="when"></div></div>
<div class="legend" id="legend"></div>
<div class="bar"><button id="bang">↺ Big Bang</button><button id="spin">Pause spin</button><button id="save">Save PNG</button></div>
<div class="tip" id="tip"></div>
<script>
(() => {
const D = /*__DATA__*/null;
const $ = id => document.getElementById(id);
const cv = $('c'), g = cv.getContext('2d');
const N = D.commits.length;
const still = location.hash === '#still' || matchMedia('(prefers-reduced-motion: reduce)').matches;
const PAL = ['#7aa2ff','#ff6fb5','#ffd166','#5effc0','#b98bff','#ff9150','#4fd8ff','#c6ff5e'];
const OTHER = '#93a0c4', K = PAL.length;
const fmt = n => n.toLocaleString();
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

// Seeded from the repo name: the same repo always grows the same galaxy.
let seed = 2166136261;
for (const ch of D.repo) seed = Math.imul(seed ^ ch.charCodeAt(0), 16777619) >>> 0;
const rnd = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296;
const gauss = () => Math.sqrt(-2 * Math.log(rnd() || 1e-9)) * Math.cos(6.2832 * rnd());

const ARMS = 2 + Math.floor(rnd() * 3), TWIST = 2 + rnd() * 1.2, ROT = rnd() * 6.2832;
const X = new Float32Array(N), Y = new Float32Array(N), Z = new Float32Array(N), S = new Float32Array(N);
const A = new Uint8Array(N), PX = new Float32Array(N), PY = new Float32Array(N);
const t0 = D.commits[0][1], span = Math.max(1, D.commits[N - 1][1] - t0);
for (let i = 0; i < N; i++) {
  const [a, t, lines] = D.commits[i];
  // blend commit order and wall-clock time so quiet years still leave a gap
  const f = 0.5 * (N > 1 ? i / (N - 1) : 1) + 0.5 * (t - t0) / span;
  A[i] = Math.min(a, K);
  S[i] = 1.25 + Math.log10(1 + lines) * 0.9;
  if (f < 0.06) {
    // the core: the oldest commits, packed into a bulge
    const r = Math.abs(gauss()) * 0.06, th = rnd() * 6.2832;
    X[i] = r * Math.cos(th); Y[i] = r * Math.sin(th); Z[i] = gauss() * 0.03;
    continue;
  }
  // each contributor leans toward a home arm, but wanders
  const arm = rnd() < 0.6 ? a % ARMS : Math.floor(rnd() * ARMS);
  const r = 0.05 + Math.pow(f, 0.9) + gauss() * 0.02;
  const th = ROT + arm * 6.2832 / ARMS + Math.log(1 + r * 10) * TWIST + gauss() * (0.16 + 0.2 * r);
  X[i] = r * Math.cos(th); Y[i] = r * Math.sin(th); Z[i] = gauss() * 0.025 * (1.2 - r);
}

const sprite = c => {
  const s = document.createElement('canvas'); s.width = s.height = 64;
  const x = s.getContext('2d'), gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, '#fff'); gr.addColorStop(0.1, c); gr.addColorStop(0.3, c + '44'); gr.addColorStop(1, c + '00');
  x.fillStyle = gr; x.fillRect(0, 0, 64, 64); return s;
};
const SPR = PAL.concat(OTHER).map(sprite);

let W, H, dpr, dust;
function resize() {
  dpr = Math.min(2, devicePixelRatio || 1);
  W = cv.width = innerWidth * dpr; H = cv.height = innerHeight * dpr;
  dust = document.createElement('canvas'); dust.width = W; dust.height = H;
  const x = dust.getContext('2d');
  for (let i = 0; i < 700; i++) {
    x.fillStyle = `rgba(200,210,255,${Math.random() * 0.35})`;
    x.fillRect(Math.random() * W, Math.random() * H, dpr * (Math.random() < 0.1 ? 1.5 : 0.8), dpr);
  }
}
resize(); addEventListener('resize', resize);

let yaw = 0, pitch = 0.95, zoom = 1, shown = still ? N : 0, playing = !still, spin = !still;
let focus = -1, hover = -1, drag = null, last = performance.now(), whenText = '', subText = '';
const PLAY_MS = clamp(N * 4, 5000, 11000);
const years = Math.max(1, Math.round(span / 3.156e7));
const month = t => new Date(t * 1000).toLocaleDateString(undefined, { year: 'numeric', month: 'short' });

$('name').textContent = D.repo;
$('spin').textContent = spin ? 'Pause spin' : 'Spin';
function hud(n) {
  const sub = `${fmt(Math.round(n / N * D.total))} commits · ${fmt(D.authors.length)} contributor${D.authors.length > 1 ? 's' : ''} · ${years} yr${years > 1 ? 's' : ''}`;
  if (sub !== subText) $('sub').textContent = subText = sub;
  const when = month(D.commits[Math.max(0, n - 1)][1]);
  if (when !== whenText) $('when').textContent = whenText = when;
}

function frame(now) {
  // a page opened in a hidden tab can start at 0×0; wait for a real size
  if (!W || !H) return requestAnimationFrame(frame);
  const dt = Math.min(64, now - last); last = now;
  if (spin && !drag) yaw += dt * 0.00005;
  if (playing && (shown = Math.min(N, shown + N * dt / PLAY_MS)) >= N) playing = false;
  const n = Math.max(1, shown | 0);

  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  g.fillStyle = '#03040a'; g.fillRect(0, 0, W, H); g.drawImage(dust, 0, 0);
  g.globalCompositeOperation = 'lighter';

  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  const R = Math.min(W, H) * 0.44 * zoom, ox = W / 2, oy = H / 2;
  const core = R * (0.06 + 0.16 * Math.sqrt(n / N));
  const cg = g.createRadialGradient(ox, oy, 0, ox, oy, core);
  cg.addColorStop(0, 'rgba(255,236,210,.55)'); cg.addColorStop(1, 'rgba(255,200,160,0)');
  g.fillStyle = cg; g.fillRect(ox - core, oy - core, core * 2, core * 2);

  const fresh = Math.max(1, N * 0.02), grow = dpr * (0.7 + 0.3 * zoom);
  for (let i = 0; i < n; i++) {
    const xr = X[i] * cy - Y[i] * sy, yr = X[i] * sy + Y[i] * cy;
    const ys = yr * cp - Z[i] * sp, p = 2.4 / (2.4 + yr * sp + Z[i] * cp);
    const px = PX[i] = ox + xr * R * p, py = PY[i] = oy + ys * R * p;
    let sz = S[i] * p * grow;
    const age = n - i;
    if (playing && age < fresh) sz *= 1 + 3 * (1 - age / fresh); // newborn stars flare
    g.globalAlpha = focus < 0 || A[i] === focus ? 0.9 : 0.05;
    g.drawImage(SPR[A[i]], px - sz * 2, py - sz * 2, sz * 4, sz * 4);
  }
  if (hover >= 0 && hover < n) {
    g.globalCompositeOperation = 'source-over'; g.globalAlpha = 0.9;
    g.strokeStyle = '#fff'; g.lineWidth = dpr;
    g.beginPath(); g.arc(PX[hover], PY[hover], 9 * dpr, 0, 6.2832); g.stroke();
  }
  hud(n);
  requestAnimationFrame(frame);
}

// legend: top contributors, click to isolate their stars
const legend = $('legend'), rows = [];
const groups = D.authors.slice(0, K).map(([nm, c], a) => [nm, c, PAL[a]]);
if (D.authors.length > K) {
  const rest = D.authors.slice(K);
  groups.push([`+${fmt(rest.length)} others`, rest.reduce((s, r) => s + r[1], 0), OTHER]);
}
groups.forEach(([nm, c, col], a) => {
  const b = document.createElement('button');
  b.innerHTML = `<span class="dot" style="color:${col};background:${col}"></span><span class="nm"></span><span class="n"></span>`;
  b.querySelector('.nm').textContent = nm; b.querySelector('.n').textContent = fmt(c);
  b.onclick = () => { focus = focus === a ? -1 : a; rows.forEach((r, j) => r.classList.toggle('off', focus >= 0 && j !== focus)); };
  legend.append(b); rows.push(b);
});

const tip = $('tip');
function pick(e) {
  const mx = e.clientX * dpr, my = e.clientY * dpr, n = shown | 0;
  let best = -1, bd = (12 * dpr) ** 2;
  for (let i = 0; i < n; i++) {
    if (focus >= 0 && A[i] !== focus) continue;
    const dx = PX[i] - mx, dy = PY[i] - my, d = dx * dx + dy * dy;
    if (d < bd) { bd = d; best = i; }
  }
  hover = best;
  if (best < 0) { tip.style.display = 'none'; return; }
  const [a, t, lines, msg] = D.commits[best];
  tip.replaceChildren();
  const b = document.createElement('b'); b.textContent = msg || '(no message)';
  const s = document.createElement('span');
  s.textContent = `${D.authors[a][0]} · ${new Date(t * 1000).toLocaleDateString()} · ${fmt(lines)} lines`;
  tip.append(b, s); tip.style.display = 'block';
  tip.style.left = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8) + 'px';
  tip.style.top = Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8) + 'px';
}

cv.addEventListener('pointerdown', e => {
  drag = { x: e.clientX, y: e.clientY, yaw, pitch };
  cv.setPointerCapture(e.pointerId); cv.classList.add('drag');
});
cv.addEventListener('pointermove', e => {
  if (!drag) return pick(e);
  yaw = drag.yaw - (e.clientX - drag.x) * 0.005;
  pitch = clamp(drag.pitch + (e.clientY - drag.y) * 0.005, 0, 1.5);
  tip.style.display = 'none'; hover = -1;
});
const end = () => { drag = null; cv.classList.remove('drag'); };
cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
cv.addEventListener('pointerleave', () => { tip.style.display = 'none'; hover = -1; });
cv.addEventListener('wheel', e => { e.preventDefault(); zoom = clamp(zoom * Math.exp(-e.deltaY * 0.001), 0.4, 8); }, { passive: false });

const bang = () => { shown = 0; playing = true; };
$('bang').onclick = bang;
$('spin').onclick = () => { spin = !spin; $('spin').textContent = spin ? 'Pause spin' : 'Spin'; };
$('save').onclick = () => {
  // stamp the PNG so a shared screenshot points back to its repo
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  g.fillStyle = 'rgba(232,236,255,.9)'; g.font = `600 ${20 * dpr}px system-ui,sans-serif`;
  g.fillText(D.repo, 24 * dpr, H - 46 * dpr);
  g.fillStyle = 'rgba(138,147,184,.9)'; g.font = `${12 * dpr}px system-ui,sans-serif`;
  g.fillText(`${fmt(D.total)} commits · ${fmt(D.authors.length)} contributors · made with git-galaxy`, 24 * dpr, H - 24 * dpr);
  cv.toBlob(blob => {
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = `${D.repo}-galaxy.png`; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  });
};
addEventListener('keydown', e => { if (e.key === ' ' && e.target === document.body) { e.preventDefault(); bang(); } });

requestAnimationFrame(frame);
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
