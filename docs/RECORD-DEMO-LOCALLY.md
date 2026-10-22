# Record the Unpile demo locally (the real thing)

Goal: a short screen recording of Unpile actually working on your own machine, so a
viewer sees HOW it works, not a website scroll. The whole pipeline in one command:
your data -> TabPFN decides + explains every item -> Gemma writes the morning digest ->
honest held-out scorecard.

This records a genuine live run (real TabPFN-v2 + real local Gemma), which is the point:
nothing is staged, and anyone can reproduce it with the dummy data that ships in the repo.

## 0. One-time setup (on your machine, not the server)

```bash
git clone https://github.com/simplynadaf/unpile-read-later-triage
cd unpile-read-later-triage

python -m venv .venv && source .venv/bin/activate        # optional but tidy
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

ollama pull gemma3:1b        # the local digest model (any open-weight model works)
```

Warm the caches once so the recording has no first-run download pause:

```bash
python scripts/demo_cli.py --pause 0        # first run caches TabPFN weights; discard this take
```

## 1. Make the terminal look good

- Font size large (18-24pt) so it is readable at 1080p. A dark theme reads best.
- Window ~1280x720 or 1920x1080, 16:9, so it drops straight into YouTube.
- Clear the scrollback right before you hit record: `clear`.
- Keep colors ON (do not set NO_COLOR) so keep=green / skim=yellow / drop=red land.

## 2. Record

Use any screen recorder you already have:

- macOS: QuickTime -> File -> New Screen Recording (or Cmd+Shift+5), or Kap.
- Linux: OBS Studio, or `wf-recorder` / SimpleScreenRecorder.
- Windows: Game Bar (Win+G), or OBS Studio.

Then run the demo at a readable pace (the built-in pauses between acts are deliberate):

```bash
clear
python scripts/demo_cli.py
```

It runs about 30-45 seconds end to end (plus the ~6s CPU pass in Act 2 and the Gemma
call in Act 3, which are real and worth showing: that IS the model working).

If you want a tighter cut, record two takes and keep the better one. Do NOT speed up
Act 2 and Act 3 to zero: the few seconds of real compute are the proof it is not faked.

## 3. What the viewer sees (narration cues, optional)

- Act 1: "This is my own reading history. 36% got read, the rest rotted. That is the bar."
- Act 2: "TabPFN scores all 14 in one CPU pass and tells me WHY it kept or dropped each."
- Act 3: "Gemma, running locally, turns the five keepers into a calm two-line morning note."
- Act 4: "And the honest scorecard, measured on held-out items, including the scary
  wrongly-dropped number I refuse to hide."

## 4. After recording

1. Trim the dead ends (the `clear`, any fumbles).
2. Optional: lay a calm ambient bed under it at ~12% (see docs/youtube-metadata.md for a
   royalty-free note), fade out the last 3s.
3. Upload to YouTube with the title/description/chapters from `docs/youtube-metadata.md`.
4. Grab the video ID and drop it into the 3 placeholders (`VIDEO_ID`) in README.md and
   docs/devto-article.md, then commit.

## Fast, no-pause run (for CI or a quick sanity check, not the recording)

```bash
python scripts/demo_cli.py --pause 0
python scripts/demo_cli.py --no-digest     # skip Gemma if Ollama is not running
```

## Why this instead of the website scroll

The old demo scrolled the finished UI. A judge cannot tell a scroll of baked numbers
from hardcoded output. This run shows the input data, the model deciding with reasons,
the local digest being written, and the honest metrics being measured, in that order.
It proves the thing works and that every number on the website came from somewhere real.
