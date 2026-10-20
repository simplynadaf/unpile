---
title: I had 1,200 articles saved "for later." An open model on my laptop read my habits and kept 6.
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

I have a folder called "Read Later." You have one too. Mine had over a thousand things in it.

I am never going to read a thousand articles. I know this. You know this. "Read later" is the most optimistic lie in software, and every tab I save is a tiny promise to a future version of me who does not exist. The pile does not inform me. It just sits there and makes me feel slightly guilty every time I open a new tab.

So for the "Slow and Steady" challenge, the one that asks you to build something that rewards laziness, I built the laziest possible thing: an agent that goes through the whole pile for me, overnight, on my own laptop, and in the morning hands me the five or six things I will actually read. It silences the rest. No cloud. No account. No cost.

It is called **Unpile**, and on my demo pile it kept 5 items out of 14, silenced 9, and gave me back 5.6 hours of reading time I was never going to spend.

## What I Built

Unpile is a local triage agent for your read-later backlog.

You point it at an export (Pocket, Instapaper, browser bookmarks, a CSV) and it does four things, all on your machine:

1. **Learns your taste** from your own history of what you actually read versus what rotted in the pile.
2. **Decides every item**: keep, skim, or drop, each with a calibrated probability that you will read it.
3. **Writes a calm two-line morning digest** of only the keepers.
4. **Silences everything else**, so you wake up to six good things instead of a wall of guilt.

The effort it saves is the whole point of the challenge. You stop being the triage system. You stop scrolling a backlog deciding, item by item, "do I care about this?" The model does that boring, repetitive judgment call, and it only taps you on the shoulder for the exceptions. That is the sloth philosophy in one sentence: it does the work so you do not have to, and you get your attention back.

Who gets to be lazier? Anyone with a doom-pile. Which is all of us.

## Demo

Live, in your browser (no setup, real baked model output): **https://simplynadaf.github.io/unpile**

Here is the demo pile getting triaged. On the left, the five items worth my morning, each with the reasons it survived and a one-line digest from Gemma. On the right, the nine that got silenced: the two-hour video essay I saved at 11pm, the "someday build a cabin" photo essay, the tabs-versus-spaces flamewar.

![Unpile triaging a read-later pile: 5 kept, 9 silenced, 5.6 hours reclaimed](docs/screenshots/hero.png)

The kept list and the silenced list, side by side:

![The keep and drop columns with probabilities and reasons](docs/screenshots/result.png)

The whole thing runs on a plain CPU. The numbers on the page are the real TabPFN-v2 and Gemma output, frozen into the static site so the demo cannot break in front of you; toggle any item and an in-browser mirror of the model re-decides live.

## Code

{% github https://github.com/simplynadaf/unpile %}

## How I Built It

Two open-weight models, one job each. Neither is decoration; take either one out and the project stops working.

### TabPFN-v2 is the decision brain

[TabPFN](https://github.com/PriorLabs/TabPFN) (Prior Labs) is an open-weight tabular foundation model. You do not train it. You hand it your history as context and it predicts in a single forward pass. For Unpile, the history is a table of saved items with the signals you know the moment you save something (source, topic, estimated read time, how stale it is, how many times you reopened the tab, whether it is an actionable how-to, how buried it is) and one honest label: did you ever actually read it?

Prior Labs specifically favors TabPFN used *inside a wider prediction agent*, not as a bare `.predict()` call. So Unpile wraps it in a real agent loop:

```python
# predict P(you read it) for the whole pile in ONE CPU forward pass
probs = self._proba(items)

for item, p in zip(items, probs):
    action = self._decide(p)        # keep / skim / drop from a tunable keep budget
    reasons = self._reasons(item)   # plain-language "why", so the call is auditable
    ...                             # keep the few, flag the maybes, silence the rot
```

It predicts, decides an action, explains that action in plain language, and then reports honest held-out metrics on itself. That last part matters, and I will come back to it.

I used TabPFN-v2 on purpose: it decides the whole pile in a single CPU forward pass, no GPU and no training run, which is exactly what lets Unpile run overnight on the laptop you already own.

### Gemma 3 is the writer

[Gemma 3](https://ai.google.dev/gemma) runs locally through Ollama and writes the morning digest. It is given the keepers and their probabilities and told to never invent an item. If Ollama is busy or the machine is offline, a deterministic fallback writes a correct digest anyway, so the summary always arrives:

```python
def write_digest(keepers):
    try:
        return gemma_via_ollama(keepers)      # calm two-line morning note, local
    except Exception:
        return rule_based(keepers)            # never blocks your morning
```

The stack is FastAPI, a synthetic-but-documented dataset, a single-file no-build UI, and GitHub Pages for the live demo. All CPU, all local.

## Why Does Open Innovation Matter?

Your reading list is a confession. It leaks your job, your health, your politics, the thing you are quietly trying to learn. That is exactly the data I refuse to send to someone else's server, and it is the reason this had to be open.

- **Your history never leaves the laptop.** A closed API would need every row uploaded. TabPFN and Gemma run on-device, so it stays with you.
- **It works with the Wi-Fi off.** Open weights mean the overnight triage does not depend on a connection, a login, or a vendor being awake.
- **It is free, at any scale.** Triaging a 1,200-item backlog on a per-call API is a real bill. On open weights it is zero, so I can run it nightly and never think about cost.
- **It learns me, not the average.** Retrain the decision on my own labels and it mirrors my taste. A closed, general model cannot be bent to one person's weird pile the way an open one can.

A closed API could summarize an article. It could not become a private, offline, free thing that learns my specific reading habits and runs forever on hardware I already own. That is the part only open makes possible.

## The Lazy Payoff

Here is the honest scorecard, measured on a held-out slice of the history, because a number I cannot check is just a vibe.

- **Precision ~0.59**: when Unpile surfaces something, I read it about 59% of the time, against a 36% base rate in the raw pile.
- **Lift ~1.6x**: the kept pile reads about 1.6 times better than a random grab from the backlog.
- **Silenced ~55%**: it auto-archives over half the pile with no input from me.
- **Wrongly dropped ~39%**: and here is the cost. At this setting it also silences about 39% of the items I *would* have read.

I am putting that last number right next to the good ones on purpose. Unpile is not magic. It trades a little recall for a calm morning. The fix is a dial, not a lie: loosen one threshold and you recover more good items at the price of a noisier digest. I would rather ship the honest trade-off than a demo that pretends false negatives do not exist.

Did it save me effort this week? Yes, in the most literal way: I stopped being the filter. The pile went from a thing I avoided to a thing that quietly resolves itself overnight. That is the whole promise of the sloth: move slow, conserve energy, let the boring part happen without you.

## Prize Categories

- **Best Use of TabPFN** (featured): TabPFN-v2 is the decision brain, used as a real prediction agent (predict, decide, explain, measure) over a personal CSV, exactly the pattern Prior Labs favors.
- **Best Use of Gemma** (featured): Gemma 3 runs locally via Ollama to write the morning digest, grounded on the model's own output, with an offline fallback.

Built new for this challenge. It reuses my own local-AI patterns from earlier weeks, re-applied to a new problem, data, agent, and UI, disclosed in the README.

Thanks for reading all the way down. Now go let a model read the rest for you.
