<div align="center">

# Unpile

### Your read-later pile, triaged by an open model on your own machine

[![Live Demo](https://img.shields.io/badge/Live-Demo-16A34A?style=for-the-badge&logo=github)](https://simplynadaf.github.io/unpile)
[![TabPFN](https://img.shields.io/badge/Decides%20with-TabPFN--v2-16A34A?style=for-the-badge)](https://github.com/PriorLabs/TabPFN)
[![Gemma](https://img.shields.io/badge/Writes%20with-Gemma%203-0ea5e9?style=for-the-badge)](https://ai.google.dev/gemma)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

**You have hundreds of articles saved "for later."**<br/>
**You will read about six of them. The rest just make you feel guilty.**<br/>
Unpile is a 100% local agent that learns which is which, and clears the pile for you.

<br/>

[Live Preview](https://simplynadaf.github.io/unpile) &nbsp;|&nbsp; [How It Works](#how-it-works-two-open-models-one-job-each) &nbsp;|&nbsp; [Why Open](#why-open-innovation-matters) &nbsp;|&nbsp; [The Honest Take](#the-honest-take)

</div>

---

## What it does

Point Unpile at your read-later backlog (a Pocket, Instapaper, bookmarks, or CSV export).
Overnight, on your own machine, it:

1. **Learns your taste** from your own history of what you actually read versus what rotted.
2. **Decides every item**: keep (worth your morning), skim (borderline), or drop (it will rot) with a calibrated probability.
3. **Writes a calm two-line morning digest** of only the keepers, grounded on the real items.
4. **Silences the rest** so you wake up to six good things, not a wall of guilt.

The whole point: it does the boring triage so you do not have to. You get your attention back.

On the bundled demo pile it keeps **5 of 14**, silences **9**, and reclaims **5.6 hours** of
reading time you were never going to spend anyway.

---

## One pile, three honest answers

| Output | What you get |
|--------|--------------|
| **A short "keep" list** | Only the items you are actually likely to read, ranked by probability, each with the plain-language reasons it survived (reopened 3x, in your lane, actionable how-to). |
| **A calm morning digest** | A local Gemma model turns the keepers into a warm, low-pressure two-line note, so your morning starts with a nudge, not a backlog. |
| **A measured, honest scorecard** | Held-out precision and recall, the share of the pile it safely silences, a **lift** number (how much better the kept pile reads than a random item), and the good items it wrongly drops. No hiding the cost. |

---

## How it works: two open models, one job each

```
your pile  ->  [ TabPFN-v2 ]  ->  keep / skim / drop  ->  [ Gemma 3 ]  ->  morning digest
  (CSV)         decides, on CPU       + reasons            writes, locally     (2 lines)
```

- **TabPFN-v2 (Prior Labs, open-weight) is the decision brain.** It conditions in-context on
  your own read-versus-rot history in a single CPU forward pass (no training run, no GPU),
  then predicts "will I actually read this?" for every item. This is a real prediction
  **agent**, not one `.predict()` call: it decides an action per item from the probability
  and a tunable keep budget, explains each call, and reports honest held-out metrics.
- **Gemma 3 (Google, open-weight) is the writer.** Running locally through Ollama, it turns
  the survivors into a calm morning digest. It is given the items and their probabilities and
  never invents one. If Ollama is busy or offline, a deterministic fallback still writes a
  correct digest, so your morning summary always arrives.

Everything runs on a plain CPU. Nothing leaves the machine.

---

## Why open innovation matters

Your reading list is a confession: it reveals your job, your health, your politics, your
insecurities. Unpile only works **because** it is open and local.

- **Your history never leaves the laptop.** A closed API would need every row on someone
  else's server. Here, it stays on yours.
- **It works with the Wi-Fi off.** Open weights run on-device, so the overnight triage never
  depends on a connection, a login, or a vendor being up.
- **$0, forever, at any scale.** Triaging a 1,200-item backlog would be a real bill on a
  per-call API. On open weights it costs nothing, so you can run it nightly without thinking.
- **It learns your taste, not the average.** Retrain the decision on your own labels and it
  mirrors you. A generic closed model cannot be bent to one person's backlog the way an open
  one can.

---

## The honest take

On a held-out slice of the saved-items history (default thresholds):

| Metric | Value | Meaning |
|--------|-------|---------|
| Precision | ~0.59 | when it surfaces something, you read it ~59% of the time |
| Lift | ~1.6x | the kept pile reads ~1.6x better than a random item from the backlog |
| Silenced | ~55% | it auto-archives over half the pile |
| Wrongly dropped | ~39% | the cost: good items it also silenced |

That last number is real and I am not hiding it. Unpile is not magic; it trades a little
recall for a calm morning. The fix is a dial, not a lie: loosen `UNPILE_KEEP_T` and you
recover more good items at the price of a noisier digest. The bundled dataset is synthetic
and documented (`scripts/build_dataset.py`); point it at your own export and the numbers
become yours.

---

## Run it locally

```bash
# 1. CPU-only PyTorch, then the deps
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2. a local Gemma via Ollama (any open-weight model works)
ollama pull gemma3:1b

# 3. the dataset is already built and committed; rebuild it if you like
python scripts/build_dataset.py

# 4. go
python run.py          # http://127.0.0.1:8099
```

Bring your own pile: export from Pocket/Instapaper/bookmarks to CSV and parse it with
`unpile/pile.py` (`parse_export`). Nothing you upload leaves your machine.

---

## Project layout

```
unpile/
  unpile/
    triage.py       # TabPFN-v2 prediction agent: predict -> decide -> explain -> measure
    digest.py       # Gemma 3 morning-digest writer (+ offline fallback)
    pile.py         # demo backlog + Pocket/CSV export parser
    api.py          # FastAPI: /api/triage, /api/meta, /api/demo, /api/health
  data/saved_items.csv       # synthetic, documented teaching dataset
  web/                       # premium single-page UI (GitHub Pages demo)
    index.html, assets/app.js, assets/model.js, static-data.json
  scripts/
    build_dataset.py   # generate the dataset
    validate.py        # end-to-end checks against the real stack
    bake_static.py     # freeze real TabPFN + Gemma output for the static demo
  run.py, requirements.txt, LICENSE
```

---

## Verify it

```bash
python scripts/validate.py     # exercises the real TabPFN + Gemma code paths end to end
```

---

## Credits and lineage

Built October 19 to 25, 2026 for the
[Hacktoberfest Open-Source AI Challenge: Week 3 (Slow and Steady)](https://dev.to/challenges/hacktoberfest-week3-2026-10-19).
Brand-new project and repository. It reuses my own local-AI patterns from earlier weeks
(FrostWise and PricePilot): the TabPFN-plus-Gemma, offline-fallback, zero-build, GitHub Pages
approach. That architecture is mine, re-applied here to a new problem, new data, new agent
loop, and new UI, disclosed per the challenge's credit-prior-work rule. Any commit after the
deadline is noted here.

Open weights: [TabPFN-v2](https://github.com/PriorLabs/TabPFN) (Prior Labs) and
[Gemma 3](https://ai.google.dev/gemma) (Google). MIT licensed.

Built by [Sarvar Nadaf](https://dev.to/sarvar_04).
