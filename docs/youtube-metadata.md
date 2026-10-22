# Unpile - YouTube Metadata (Week 3: Slow and Steady)

Everything below is copy-paste ready for the YouTube upload. No em dashes anywhere.
Video file: `docs/demo.mp4` (90s, 1440x810, H.264 + AAC, calm ambient bed at 12 percent).

---

## TITLE (chosen, 58 chars, keyword-forward + payoff + freshness)

**I Built Offline AI That Clears My Read-Later Pile (2026)**

A/B alternatives (all under ~60 chars, first-person DEV-winner pattern):
- An Open Model on My Laptop Read 1,247 Saved Tabs, Kept 5
- Local AI That Triages Your Read-Later Backlog (Free, 2026)
- I Made an Offline AI Clear My Doom-Pile of Saved Articles

Why this one: "Offline AI" is a high-volume evergreen search term, front-loaded; "Read-Later
Pile" names the exact pain a viewer feels; "(2026)" adds freshness for CTR. First-person
"I Built" is the DEV/YouTube hook that performs.

---

## DESCRIPTION (copy-paste; no em dashes)

I have a folder called "Read Later" with over a thousand things in it. I am never going to
read them. You have one too. So I built Unpile: a 100 percent local agent that reads my
"save it, never open it" habits, decides which handful I will actually read, writes a calm
two-line morning digest of only those, and quietly silences the rest. No cloud. No account.
Zero cost per item. It runs on a plain laptop CPU with the Wi-Fi off.

Two open-weight models do the work, one job each:

- TabPFN-v2 (Prior Labs) is the decision brain. It conditions on my own history of what I
  read versus what rotted, in a single CPU forward pass, and predicts "will I actually read
  this?" for every saved item. It is wrapped in a real prediction agent: predict, decide an
  action (keep, skim, or drop), explain each call in plain language, then report honest
  held-out metrics on itself.
- Gemma 3 (Google) runs locally through Ollama and writes the morning digest, grounded only
  on the real keepers. If Ollama is busy or offline, a deterministic fallback still writes a
  correct digest, so the summary always arrives.

On the demo pile of 14 items it keeps 5, flags 1 as a maybe, silences 8, and hands back 5.5
hours of reading time I was never going to spend. Point it at a real 1,200-item backlog and
it does the same thing while you sleep.

Why open and local matters here: your reading list is a confession. It leaks your job, your
health, your politics, the thing you are quietly trying to learn. Open weights keep every
row on your own machine, work with the Wi-Fi off, cost nothing at any scale, and can be
retrained on your own labels so the model learns your taste instead of the average. A closed
API could not become a private, offline, free thing that keeps running on hardware you
already own.

And I do not hide the cost. The honest scorecard is in the video: about 1.66x lift over a
random item, 58 percent of the pile silenced, and the roughly 44 percent of good items it
also wrongly drops at this setting. The fix is a dial, not a lie: loosen one threshold to
recover more near-misses at the price of a slightly noisier digest.

Built for the Hacktoberfest Open-Source AI Challenge, Week 3: Slow and Steady. Channel your
inner sloth and let the model do the pile.

Live demo (runs in your browser, real baked model output):
https://simplynadaf.github.io/unpile-read-later-triage

Code (MIT, open source):
https://github.com/simplynadaf/unpile-read-later-triage

Open weights used:
- TabPFN-v2: https://github.com/PriorLabs/TabPFN
- Gemma 3: https://ai.google.dev/gemma

Built by Sarvar Nadaf: https://dev.to/sarvar_04

Music: calm ambient instrumental, royalty-free.

#OpenSource #LocalAI #TabPFN #Gemma #Hacktoberfest #OfflineAI #Ollama #Privacy

---

## CHAPTERS (paste into the description; first one must be 0:00)

0:00 The read-later pile problem
0:07 You saved 1,247 things for later
0:13 A real backlog, 14 saved items
0:22 The agent triages it in one CPU pass
0:30 Use case 1: the few worth your morning
0:38 Use case 2: the borderline maybe
0:45 Use case 3: the doom-pile it silences
0:54 Your morning digest, written by Gemma 3
1:03 How it works: two open models
1:10 Why open and local matters
1:18 The honest take

(Timestamps are aligned to the final 90s cut. If you trim or re-record, re-check them against
the upload; YouTube reads the first column literally, and the first chapter must be 0:00.)

---

## PINNED COMMENT (optional, drives the click)

Everything runs on a laptop CPU with the Wi-Fi off. No cloud, no account, 0 dollars per item.
Try the live demo (real model output, no setup): https://simplynadaf.github.io/unpile-read-later-triage
Code is MIT: https://github.com/simplynadaf/unpile-read-later-triage

---

## TAGS (YouTube keywords field, comma-separated)

offline AI, local AI, read later, TabPFN, Gemma 3, Ollama, open weight models, open source AI,
on-device AI, privacy AI, read later triage, inbox zero, productivity AI, Hacktoberfest 2026,
prediction agent, no API costs, run AI locally, FastAPI, Python AI project

---

## THUMBNAIL TEXT IDEAS (max 3 words, high contrast on dark bg)

- "KEPT 5 / 1,247"
- "LET IT ROT"
- "READ LATER, SOLVED"

Pair with the green-to-cyan gradient from the site and the "5.5 h reclaimed" stat.

---

## UPLOAD CHECKLIST

- [ ] Upload docs/demo.mp4
- [ ] Title + description + chapters pasted (chapters verified against final cut)
- [ ] Visibility: Public (or Unlisted while the article is in review)
- [ ] After publishing, copy the VIDEO_ID and replace `VIDEO_ID` in:
      - docs/devto-article.md (the youtu.be link and the {% embed %} line)
      - README.md (the Watch Demo badge)
- [ ] Add the live-demo + repo links in the description (already included above)
