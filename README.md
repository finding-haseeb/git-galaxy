<div align="center">

# ✦ git-galaxy

**Your repo is a galaxy. You just haven't seen it yet.**

Every commit is a star. Every contributor is a color.
The first commits are the core. Today's commit is the outer edge.

![A 5,000-commit repo rendered as a spiral galaxy](docs/hero.png)

</div>

## Run it (10 seconds, zero dependencies)

From inside any git repo:

```bash
curl -sL https://raw.githubusercontent.com/finding-haseeb/git-galaxy/main/galaxy.py | python3 -
```

Or clone it and point it anywhere:

```bash
python3 galaxy.py ~/code/linux
```

It reads `git log` and writes a single HTML file. Then it opens your browser and **replays your repo's history as a Big Bang**. Nothing is uploaded anywhere.

## What you can do

- **Watch it form:** the galaxy grows from the first commit to the latest one. Press `space` to replay.
- **Drag** to orbit, **scroll** to zoom.
- **Hover a star** to read its commit message, author, date and lines changed.
- **Click a contributor** to light up only their stars.
- **Save PNG** for a shareable image, stamped with your repo name.

The shape comes from the repo name, so the same repo always grows the same galaxy. Bigger commits make brighter stars. Quiet years leave dark gaps.

## Options

```
python3 galaxy.py [repo] [-o out.html] [--max N] [--no-open]
```

| flag | default | |
|---|---|---|
| `repo` | `.` | path to any git repo |
| `-o` | temp file | where to write the HTML |
| `--max` | `30000` | max stars to draw (huge repos are sampled evenly) |
| `--no-open` | off | don't launch the browser |

Needs Python 3.8+ and git. Merge commits are skipped.

## Star goal

**100,000,000,000,000.**

GitHub has about 150 million users, so we only need each of you to star this about 666,667 times.
Or star it once and post your galaxy. That works too. ⭐

## License

MIT
