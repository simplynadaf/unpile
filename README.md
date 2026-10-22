<div align="center">

# 🦥 Unpile

### Declare Bankruptcy on Your Read-Later Pile

[![Live Demo](https://img.shields.io/badge/Live-Demo-16A34A?style=for-the-badge&logo=github)](https://simplynadaf.github.io/unpile-read-later-triage)
[![YouTube](https://img.shields.io/badge/Watch-Demo-red?style=for-the-badge&logo=youtube)](https://youtu.be/VIDEO_ID)
[![Dev.to](https://img.shields.io/badge/Read-Article-0A0A0A?style=for-the-badge&logo=devdotto)](https://dev.to/sarvar_04)
[![TabPFN](https://img.shields.io/badge/Decides%20with-TabPFN--v2-4ade8a?style=for-the-badge)](https://github.com/PriorLabs/TabPFN)
[![Gemma](https://img.shields.io/badge/Writes%20with-Gemma%203-0ea5e9?style=for-the-badge)](https://ai.google.dev/gemma)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

<img src="https://raw.githubusercontent.com/simplynadaf/unpile-read-later-triage/main/docs/banner.png" alt="Unpile, a 100% local read-later triage agent powered by TabPFN-v2 and Gemma 3" width="100%"/>

<br/>

**You have hundreds of articles saved "for later."**<br/>
**You will read about six of them. The rest just make you feel guilty.**<br/>
I built an open-weight agent that learns which is which, on your own laptop, with the Wi-Fi off.

<br/>

[Live Preview →](https://simplynadaf.github.io/unpile-read-later-triage) &nbsp;|&nbsp; [Watch Demo →](https://youtu.be/VIDEO_ID) &nbsp;|&nbsp; [Read Article →](https://dev.to/sarvar_04) &nbsp;|&nbsp; [How It Works →](#-how-it-works-two-open-models-one-job-each)

</div>

---

## 🎬 Demo

<div align="center">

[![Watch the Unpile demo on YouTube](https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg)](https://youtu.be/VIDEO_ID)

*The whole pipeline on real data: the history TabPFN learns from, the keep/skim/drop decision with the reason for every item, the local Gemma digest, and the honest held-out scorecard. [Watch on YouTube →](https://youtu.be/VIDEO_ID) · [Try the live demo →](https://simplynadaf.github.io/unpile-read-later-triage/)*

</div>

---

## 🎯 One Pile, Three Honest Answers

| Output | What You Get |
|--------|-------------|
| 🎯 **A short "keep" list** | Only the items you are actually likely to read, ranked by probability, each with the plain-language reasons it survived (reopened 3x, in your lane, actionable how-to). |
| ☕ **A calm morning digest** | A local Gemma model turns the keepers into a warm, low-pressure two-line note, so your morning starts with a nudge, not a backlog. |
| 📏 **A measured, honest scorecard** | Held-out precision and recall, the share of the pile it safely silences, a **lift** number (how much better the kept pile reads than a random item), and the good items it wrongly drops. No hiding the cost. |

<div align="center">
<img src="https://raw.githubusercontent.com/simplynadaf/unpile-read-later-triage/main/docs/screenshots/result.png" alt="Unpile triaging a real read-later pile: 5 kept with reasons, 1 maybe, 8 silenced, 5.5 hours reclaimed, with a Gemma morning digest" width="100%"/>
<br/><em>A real backlog triaged on-device: 5 kept (with reasons), 1 maybe, 8 silenced, 5.5 hours reclaimed.</em>
</div>

---

## ✨ Key Features

- 🧮 **Tabular foundation model** - TabPFN-v2 decides the whole pile in one CPU pass, no training
- 🤖 **A real prediction agent** - predict, decide an action, explain it, then measure itself
- 📏 **Honest held-out scorecard** - precision, recall, silenced share, and the good items it wrongly drops
- ☕ **Grounded digest writer** - Gemma 3 turns the keepers into a calm morning note, never inventing one
- 🔒 **100% local** - your reading history never leaves the laptop; no account, no server
- 📴 **Works offline** - open weights run on-device; triage overnight with the Wi-Fi off
- 💸 **$0 at any scale** - open weights mean no per-item API fee on a 1,200-item backlog
- 🔁 **Swappable + tunable** - drop in your own Pocket/CSV export, or point it at any Ollama model
- 🛟 **Never blocked** - a deterministic fallback writes the digest if the LLM is unreachable

---

## 📊 The Problem (Why the Pile Taxes You)

| Reality | Scale |
|---------|-------|
| Items in a typical "read later" pile | Hundreds to thousands |
| How many you will actually read | A handful |
| What the pile does the rest of the time | Sits there and charges you a little guilt |
| What closed read-later AIs want | Your reading history, on their server |
| A reader's actual edge | Their own taste, exactly what they would be uploading |
| What Unpile costs to run | $0, on the laptop they already own |

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Decide | [TabPFN-v2](https://github.com/PriorLabs/TabPFN) (open weights) | Tabular foundation model; decides the pile in one CPU pass, no per-dataset training |
| Write | [Gemma 3](https://ai.google.dev/gemma) via [Ollama](https://ollama.com) | Open-weight LLM, runs locally, swappable |
| Fallback | Deterministic template (Python) | Correct digest with no model reachable |
| API | FastAPI + Uvicorn (localhost only) | Wires the two models, serves the UI |
| Front end | Vanilla HTML/CSS/JS | No build step, premium feel, deploys anywhere |
| Hosting | GitHub Pages (static preview) | Free; serves pre-computed real results |
| Runtime | Pure CPU | No GPU, no cloud, no account |

---

## 🚀 Quick Start

```bash
git clone https://github.com/simplynadaf/unpile-read-later-triage.git
cd unpile-read-later-triage

# CPU-only PyTorch (skip if you have a GPU build you prefer)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# the local language model (open-weight) via Ollama
# install Ollama from https://ollama.com, then:
ollama pull gemma3:1b

python run.py        # → http://127.0.0.1:8099
```

Open the link, load the demo pile (or upload your own export), and hit **Triage**. The
first run downloads the TabPFN-v2 weights once and caches them; after that it runs fully
offline.

> **Prove it is local:** turn off Wi-Fi after the models cache, then triage another pile.
> The decision (TabPFN) still computes; if Gemma is reachable it writes the digest, otherwise
> the deterministic fallback does. Nothing calls out.

<details>
<summary>Watch the whole pipeline in your terminal (no browser)</summary>

```bash
python scripts/demo_cli.py          # data → decisions with reasons → digest → scorecard
python scripts/demo_cli.py --pause 0   # no pauses (fast run / CI)
```
</details>

<details>
<summary>Rebuild the dataset / re-bake the static demo / validate the stack</summary>

```bash
python scripts/build_dataset.py   # regenerate data/saved_items.csv
python scripts/bake_static.py     # regenerate web/static-data.json for the Pages preview
python scripts/validate.py        # end-to-end: API + TabPFN + Gemma + offline fallback
```
</details>

---

## 🧠 How It Works: two open models, one job each

<div align="center">
<img src="https://raw.githubusercontent.com/simplynadaf/unpile-read-later-triage/main/docs/screenshots/how.png" alt="Three steps: your pile goes in, TabPFN-v2 decides keep/skim/drop with reasons, Gemma writes the morning digest" width="100%"/>
</div>

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Your pile   │───▶│   TabPFN-v2      │───▶│  keep / skim / drop │
│ (Pocket, CSV,│    │  (open weights,  │    │  + a calibrated     │
│  bookmarks)  │    │   CPU, no train) │    │  prob + the reasons │
└──────────────┘    └──────────────────┘    └──────────┬──────────┘
                                                        │  (keepers passed in,
                                                        ▼   never invented)
                                               ┌─────────────────────┐
                                               │   Gemma 3 (Ollama)   │
                                               │  writes the digest   │
                                               └──────────┬──────────┘
                                                        │ (if unreachable)
                                                        ▼
                                               ┌─────────────────────┐
                                               │  Deterministic rule  │
                                               │  writes the digest   │
                                               └─────────────────────┘
```

| Layer | Who decides | What happens |
|-------|-------------|--------------|
| **Decide** | **TabPFN-v2** | Predicts "will I actually read this?" for every item from your own read-versus-rot history in one CPU pass. Used as a **prediction agent**: it decides keep/skim/drop from a tunable keep budget, explains each call, and reports honest held-out metrics on itself. |
| **Write** | **Gemma 3** (local) | Turns the keepers into a calm two-line morning digest. Given the items and their probabilities; never invents one. |
| **Fallback** | Deterministic rule | Writes a correct digest from the same keepers if Ollama is unreachable. |

On the bundled data, Unpile keeps **5 of 14** on the demo pile, silences **8**, reclaims
**5.5 hours** of reading, and on a held-out slice surfaces items you actually read with
**0.60 precision**, about **1.66x** better than a random grab from the backlog.

---

## ⚖️ Why Open Innovation Matters

Your reading list is a confession: it reveals your job, your health, your politics, the
thing you are quietly trying to learn. A closed, hosted model would have made this project
*worse* in every way that matters.

| | |
|--|--|
| 🔒 **Your history stays yours** | A closed API would need every row uploaded. TabPFN and Gemma run on-device, so it stays with you. |
| 📴 **It works with the Wi-Fi off** | Open weights mean the overnight triage never depends on a connection, a login, or a vendor being awake. |
| 💸 **$0 at any scale** | Triaging a 1,200-item backlog on a per-call API is a real bill. On open weights it is zero, run it nightly and never think about cost. |
| 🎯 **It learns you, not the average** | Retrain the decision on your own labels and it mirrors your taste, where a general closed model cannot be bent to one person's weird pile. |

---

## 🏆 Built For

**[Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)**

Channel your inner sloth and build something that does the work so you do not have to.

| Category | How |
|----------|-----|
| **Best Use of TabPFN** | TabPFN-v2 is the decision brain, used as a real prediction agent (predict, decide, explain, measure) over a personal CSV, with an honest held-out scorecard. Exactly the "prediction agent" pattern Prior Labs favors over a bare classifier. |
| **Best Use of Gemma** | Gemma 3 runs locally via Ollama to write the morning digest, grounded strictly on the kept items, with a deterministic offline fallback so it never hard-fails. |

---

## 📁 Project Structure

```
unpile-read-later-triage/
├── unpile/                   # the open-weight AI core
│   ├── api.py                # FastAPI: wires decide + write, serves the UI
│   ├── triage.py             # TabPFN-v2 prediction agent (predict, decide, explain, measure)
│   ├── digest.py             # Gemma 3 morning-digest writer + offline fallback
│   └── pile.py               # demo backlog + Pocket/CSV export parser
├── web/                      # static front end (also the GitHub Pages preview)
│   ├── index.html
│   ├── static-data.json      # pre-computed real results for the hosted preview
│   └── assets/{app.js, model.js}
├── data/saved_items.csv      # synthetic, documented teaching dataset (swap in your own)
├── scripts/
│   ├── build_dataset.py      # regenerate the dataset
│   ├── demo_cli.py           # end-to-end terminal demo: data → decisions → digest → scorecard
│   ├── bake_static.py        # bake real results for the Pages preview
│   └── validate.py           # end-to-end validation
├── docs/                     # banner, screenshots, demo video, article draft
├── .github/workflows/deploy.yml   # auto-deploy the preview to GitHub Pages
├── run.py                    # one command to run everything
├── requirements.txt
├── LICENSE                   # MIT
└── README.md
```

---

## 🧾 The Honest Take

On a held-out slice of the saved-items history (default thresholds):

| Metric | Value | Meaning |
|--------|-------|---------|
| Precision | ~0.60 | when it surfaces something, you read it about 60% of the time (vs a 36% base rate) |
| Lift | ~1.66x | the kept pile reads about 1.66x better than a random item from the backlog |
| Silenced | ~58% | it auto-archives well over half the pile with no input from you |
| Wrongly dropped | ~44% | the cost: good items it also silenced |

- **That last number is real and I am not hiding it.** Unpile is not magic; it trades a
  little recall for a calm morning. The fix is a dial, not a lie: loosen `UNPILE_KEEP_T`
  and you recover more good items at the price of a noisier digest.
- **The bundled dataset is grounded but synthetic.** Generated from realistic read-versus-rot
  drivers so the relationships are real and learnable, but it is a teaching dataset. **Swap
  in your own export** to make the numbers yours; that is the whole point.
- **The language model only writes copy.** No decision comes from Gemma; the keep/skim/drop
  call is TabPFN's.
- **CPU, so it is unhurried.** A full triage-plus-digest takes a handful of seconds on a
  laptop CPU. That is the cost of running everything locally instead of in someone's data
  center, worth it to keep your reading history on your own machine.

---

## 🙏 Credits & Prior Work

Built October 19 to 25, 2026 for the Week 3 window. Brand-new project and repository. It
reuses an architecture pattern I built for earlier weeks, **FrostWise** (Week 1) and
**PricePilot** (Week 2): TabPFN-v2 for prediction, a local Gemma model for the language
layer, FastAPI, a no-build front end, and a deterministic offline fallback. **Unpile is a
new project**: new repository, new domain, new dataset, new prediction target, and a new
triage prediction-agent loop, built within the Week 3 window. Lineage noted per the
challenge's "credit prior work" rule. Any commit after the deadline is noted here.

Model weights are licensed by their authors: TabPFN-v2 under the Prior Labs License, Gemma
under the Gemma Terms of Use.

---

## 👤 Author

**Sarvar Nadaf** | Cloud Architect | Cloud, AI Infrastructure & DevOps

| Platform | Link |
|----------|------|
| 🌐 Portfolio | [sarvarnadaf.com](https://sarvarnadaf.com) |
| 💼 LinkedIn | [linkedin.com/in/sarvar04](https://www.linkedin.com/in/sarvar04/) |
| ✍️ Dev.to | [dev.to/sarvar_04](https://dev.to/sarvar_04) |
| 🐙 GitHub | [github.com/simplynadaf](https://github.com/simplynadaf) |

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

**Because a pile of unread tabs should not cost you a morning.**

⭐ Star this repo if it helped you!

[![Star this repo](https://img.shields.io/github/stars/simplynadaf/unpile-read-later-triage?style=social)](https://github.com/simplynadaf/unpile-read-later-triage)

Built for the **Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady** · Made with 🤍 by [Sarvar](https://sarvarnadaf.com)

</div>
