---
title: I had 1,247 articles saved "for later." An open model on my own laptop learned my habits and handed me 5.
published: false
tags: devchallenge, hf26challenge, ai, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

I have a folder called "Read Later." You have one too. Mine had 1,247 things in it.

I am never going to read 1,247 articles. I know this. You know this. "Read later" is the most optimistic lie in software: every tab I save is a tiny promise to a future version of me who does not exist. The pile does not inform me. It sits there and taxes me a little guilt every time I open a new tab.

The challenge this week, "Slow and Steady," asks for something that rewards laziness: channel your inner sloth, build the thing that does the work so you do not have to. So I built the laziest thing I could imagine. An agent that chews through the entire pile overnight, on my own laptop, with the Wi-Fi off, and in the morning hands me the five or six things I will actually read. It silences the rest. No cloud. No account. No cost.

It is called **Unpile**. On the demo pile below it reads 14 saved items, keeps **5**, flags **1** maybe, silences **8**, and hands back **5.5 hours** of reading time I was never going to spend. Point it at a real 1,200-item backlog and it does the same thing while you sleep.

## What I Built

Unpile is a local triage agent for your read-later backlog.

You point it at an export (Pocket, Instapaper, browser bookmarks, a CSV) and it does four things, all on your machine:

1. **Learns your taste** from your own history of what you actually read versus what rotted in the pile.
2. **Decides every item**: keep, skim, or drop, each with a calibrated probability that you will read it.
3. **Writes a calm two-line morning digest** of only the keepers.
4. **Silences everything else**, so you wake up to five good things instead of a wall of guilt.

The effort it saves is the whole point of the challenge. You stop being the triage system. You stop scrolling a backlog deciding, item by item, "do I care about this?" The model does that boring, repetitive judgment call thousands of times and only taps you on the shoulder for the handful that survive. That is the sloth philosophy in one line: it does the work so you do not have to, and you get your attention back.

Who gets to be lazier? Anyone with a doom-pile of unread tabs. Which, let us be honest, is every single person reading this.

## Demo

**Live, in your browser (no setup, real baked model output):** https://simplynadaf.github.io/unpile-read-later-triage
**Video walkthrough:** [watch on YouTube](https://youtu.be/VIDEO_ID)

{% embed https://youtu.be/VIDEO_ID %}

The 60-second walkthrough goes end to end: the open-source repo, then the real pipeline running in a terminal (the reading history TabPFN learns from, the keep/skim/drop call with a reason for every item, the local Gemma digest, and the honest held-out scorecard), then the live site. Nothing is staged; the numbers on screen are the actual program output.

Here is the demo pile getting triaged. On the left, the five items worth my morning, each with the reasons it survived and a one-line digest from Gemma. In the middle, the one borderline "maybe" it set aside for a quick skim. On the right, the eight it silenced: the two-hour video essay I saved at 11pm, the "someday build a cabin" photo essay, the tabs-versus-spaces flamewar.

![Unpile triaging a read-later pile: 5 kept, 1 maybe, 8 silenced, 5.5 hours reclaimed](https://raw.githubusercontent.com/simplynadaf/unpile-read-later-triage/main/docs/screenshots/hero.png)

The keep, maybe, and silenced columns, side by side, each with probabilities and reasons:

![The keep, skim, and drop columns with probabilities and reasons](https://raw.githubusercontent.com/simplynadaf/unpile-read-later-triage/main/docs/screenshots/result.png)

The whole thing runs on a plain CPU. The numbers on the page are the real TabPFN-v2 and Gemma output, frozen into the static site so the demo cannot break in front of you; toggle any item and an in-browser mirror of the model re-decides live.

## Code

{% github https://github.com/simplynadaf/unpile-read-later-triage %}

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

A closed API could summarize an article. It could not become a private, offline, free thing that learns my specific reading habits and keeps running on hardware I already own, long after any free tier would have expired. That is the part only open makes possible, and it is the entire reason Unpile exists.

## The Lazy Payoff

Here is the honest scorecard, measured on a held-out slice of 240 saved items the model never saw, because a number I cannot check is just a vibe.

- **Precision 0.60**: when Unpile surfaces something, I actually read it about 60% of the time, against a **36% base rate** in the raw pile. It nearly doubles the odds that the thing in front of me is worth it.
- **Lift 1.66x**: the kept pile reads 1.66 times better than a random grab from the backlog.
- **Silenced 58%**: it auto-archives well over half the pile with no input from me. That is the laziness, quantified.
- **Reclaimed 5.5 hours** on the 14-item demo alone. Scale that to a real 1,200-item backlog and the model is doing days of triage you were never going to do yourself.

And now the number I am putting right next to the good ones, on purpose:

- **Wrongly dropped 44%.** At this setting, of the items I genuinely would have read, it also silenced about 44% of them. The most painful miss on the demo pile is "this week in AI (issue #214)" at 37% confidence: a fresh newsletter in a topic I follow, and it landed just under the keep line. It got silenced. On another morning I would have wanted it.

I am not hiding that. Unpile is not magic; it trades recall for a calm morning. But the fix is a dial, not a lie: loosen one threshold (`UNPILE_KEEP_T`) and you recover more of those near-misses at the price of a slightly noisier digest. I would rather ship the honest trade-off, with the failure case named out loud, than a demo that pretends false negatives do not exist.

Did it save me effort this week? Completely, and in the most literal way: I stopped being the filter. The pile went from a thing I avoided to a thing that quietly resolves itself overnight. That is the whole promise of the sloth. Move slow, conserve energy, let the boring part happen without you.

## Prize Categories

- **Best Use of TabPFN** (featured): TabPFN-v2 is the decision brain, used as a real prediction agent (predict, decide, explain, measure) over a personal CSV, with honest held-out metrics, exactly the "prediction agent" pattern Prior Labs favors over a bare classifier.
- **Best Use of Gemma** (featured): Gemma 3 runs locally via Ollama to write the morning digest, grounded strictly on the model's own output, with a deterministic offline fallback so it never hard-fails.

Built new for this challenge (Oct 19 to 25). It reuses my own local-AI patterns from earlier weeks, re-applied to a new problem, dataset, agent loop, and UI, disclosed in the README per the credit rule.

Thanks for reading all the way down. You just did something your backlog never let you do: you finished. Now go let a model read the rest for you.

---

*Demo music: Low Mileage - Hold You (Instrumental) [NCS Release], free to stream and download at [ncs.io/HoldYou](http://ncs.io/HoldYou).*
