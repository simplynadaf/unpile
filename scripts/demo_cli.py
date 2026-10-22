#!/usr/bin/env python3
"""Unpile end-to-end demo, on the command line, for humans and for recording.

One command walks the whole pipeline the article describes, with readable output, so a
viewer sees HOW it works and WHERE every number comes from, not a website scroll:

    Act 1  the data        the real saved-items history TabPFN learns from
    Act 2  the decisions   TabPFN predicts P(read) per item + the plain-language reasons
    Act 3  the digest      Gemma (local, via Ollama) writes the morning note; honest fallback
    Act 4  the scorecard   honest held-out precision / recall / silenced / wrongly-dropped

Everything here calls the SAME code the web app and validator use (unpile.triage,
unpile.pile, unpile.digest). Nothing is faked for the demo. Ships with dummy data
(data/saved_items.csv + a hand-written demo pile) so anyone can clone and run it:

    python scripts/demo_cli.py
    python scripts/demo_cli.py --pause 0   # no pauses, for a fast run / CI

The pile it triages is unpile.pile.demo_pile(); swap in your own export any time via the
web app's upload or unpile.pile.parse_export().
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# run from anywhere: make the repo root importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd

from unpile.pile import demo_pile
from unpile.triage import (
    DATA,
    SOURCE_NAMES,
    TOPIC_NAMES,
    TriageAgent,
)

# ----- tiny, dependency-free terminal styling (no color libs needed) -----
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

_NO_COLOR = bool(os.environ.get("NO_COLOR"))


def c(text: str, color: str) -> str:
    return text if _NO_COLOR else f"{color}{text}{RESET}"


PAUSE = 1.2  # seconds between acts; set with --pause


def beat(mult: float = 1.0) -> None:
    if PAUSE > 0:
        time.sleep(PAUSE * mult)


def rule(title: str) -> None:
    line = "=" * 72
    print()
    print(c(line, DIM))
    print(c(f"  {title}", BOLD + CYAN))
    print(c(line, DIM))
    print()


ACTION_STYLE = {"keep": GREEN, "skim": YELLOW, "drop": RED}


def act1_data(agent: TriageAgent) -> None:
    rule("ACT 1  .  The data Unpile learns from  (your own reading history)")
    df = agent.df
    read = int(df["was_read"].sum())
    n = len(df)
    print(
        f"  {c(str(n), BOLD)} saved items in "
        f"{c(os.path.relpath(DATA, ROOT), CYAN)} "
        f"(dummy data, ships in the repo so you can run this)."
    )
    print(
        f"  You actually read {c(str(read), GREEN)} of them "
        f"({100*read/n:.0f}%). The other "
        f"{c(str(n-read), RED)} rotted. That {c(f'{100*read/n:.0f}%', BOLD)} "
        f"base rate is the bar to beat.\n"
    )
    print(c("  Two honest rows from the history, so you see the signal:", DIM))

    def show_row(mask_desc: str, row: pd.Series) -> None:
        verdict = "READ" if int(row["was_read"]) == 1 else "ROTTED"
        vc = GREEN if verdict == "READ" else RED
        print(
            f"   {c(verdict.rjust(6), vc + BOLD)}  "
            f"{SOURCE_NAMES[int(row['source_id'])]:<22} "
            f"{TOPIC_NAMES[int(row['topic_id'])]:<24} "
            f"{int(row['length_min'])}min  "
            f"reopened {int(row['reopen_count'])}x  "
            f"{int(row['age_days'])}d old   {c('(' + mask_desc + ')', DIM)}"
        )

    read_rows = df[df["was_read"] == 1]
    rot_rows = df[df["was_read"] == 0]
    # a clear "read" example: in-lane + reopened; a clear "rot": long/old/never-reopened
    r = read_rows.sort_values(["reopen_count", "topic_affinity"], ascending=False).iloc[0]
    show_row("reopened, in your lane", r)
    rot = rot_rows.sort_values(["length_min", "age_days"], ascending=False).iloc[0]
    show_row("long, stale, never reopened", rot)
    beat(1.5)


def act2_decisions(agent: TriageAgent, pile: list[dict]):
    rule("ACT 2  .  TabPFN-v2 decides the whole pile in one CPU pass  (and says why)")
    print(
        f"  Conditioning TabPFN-v2 on your history and predicting "
        f"{c('P(you read it)', BOLD)} for all {c(str(len(pile)), BOLD)} items...\n"
    )
    t0 = time.time()
    tri = agent.triage(pile)
    dt = time.time() - t0

    order = tri.kept + tri.skim + tri.dropped
    for d in order:
        style = ACTION_STYLE[d.action]
        tag = c(f"[{d.action.upper():4}]", style + BOLD)
        prob = c(f"p={d.prob:0.2f}", style)
        title = d.title if len(d.title) <= 46 else d.title[:43] + "..."
        print(f"  {tag} {prob}  {title}")
        print(f"         {c('why: ' + '; '.join(d.reasons), DIM)}")
    print()
    print(
        f"  {c('KEEP ' + str(len(tri.kept)), GREEN + BOLD)}   "
        f"{c('SKIM ' + str(len(tri.skim)), YELLOW + BOLD)}   "
        f"{c('DROP ' + str(len(tri.dropped)), RED + BOLD)}   "
        f"in {c(f'{dt:0.1f}s', BOLD)} on CPU."
    )
    print(
        f"  Reading time reclaimed from the drop pile: "
        f"{c(f'{tri.minutes_saved:.0f} min ({tri.minutes_saved/60:.1f} hrs)', GREEN + BOLD)} "
        f"you were never going to spend.\n"
    )
    beat(1.5)
    return tri


def act3_digest(tri) -> None:
    rule("ACT 3  .  Gemma writes your calm two-line morning digest  (local, offline-safe)")
    # write_digest wants list[dict] with title/reasons/length_min; Decision carries those.
    keepers = [
        {"title": d.title, "reasons": d.reasons, "length_min": d.length_min}
        for d in tri.kept
    ]
    try:
        from unpile.digest import write_digest  # imported here so Act 1/2 run even without it
        digest = write_digest(keepers)
    except Exception as e:  # never block the demo
        print(c(f"  digest writer unavailable ({e.__class__.__name__}); "
                f"the offline fallback would still write one.", DIM))
        beat(1.5)
        return

    greeting = (digest.get("greeting") or "").strip()
    blurbs = digest.get("blurbs") or []
    src = (digest.get("source") or "").lower()

    if greeting:
        print(f"  {c(greeting, BOLD)}")
    for b in blurbs:
        print(f"    - {b}")
    print()
    tag = ("Gemma 3 (local via Ollama)" if src == "gemma"
           else f"offline fallback [{digest.get('model', 'rule-based')}]")
    print(c(f"  digest written by: {tag}", DIM))
    beat(1.5)


def act4_scorecard(agent: TriageAgent) -> None:
    rule("ACT 4  .  The honest scorecard  (measured on held-out items, not vibes)")
    print(c("  Fitting on a train split, scoring items the model never saw...\n", DIM))
    m = agent.metrics()
    lift = m.lift
    print(
        f"  {c('precision', BOLD):<22} {c(f'{m.precision:.2f}', GREEN + BOLD)}   "
        f"{c(f'(vs {m.read_rate:.2f} base rate -> {lift:.2f}x better)', DIM)}"
    )
    print(f"  {c('recall', BOLD):<22} {c(f'{m.recall:.2f}', YELLOW)}")
    print(
        f"  {c('silenced', BOLD):<22} {c(f'{m.silenced_pct*100:.0f}%', GREEN + BOLD)}   "
        f"{c('of the pile auto-archived, no input from you', DIM)}"
    )
    print(
        f"  {c('wrongly dropped', BOLD):<22} {c(f'{m.missed_pct*100:.0f}%', RED + BOLD)}   "
        f"{c('of the good stuff (the scary number, shown on purpose)', DIM)}"
    )
    print(f"  {c('held-out items', DIM):<22} {c(str(m.n_test), DIM)}")
    print()
    print(
        c(
            "  Honest trade: it buys a calm morning by accepting some false negatives.\n"
            "  Loosen UNPILE_KEEP_T to recover more near-misses at the cost of a noisier digest.",
            DIM,
        )
    )
    beat()


def main() -> None:
    global PAUSE
    ap = argparse.ArgumentParser(description="Unpile end-to-end CLI demo.")
    ap.add_argument("--pause", type=float, default=PAUSE,
                    help="seconds between acts (0 = no pauses, good for CI/fast runs)")
    ap.add_argument("--no-digest", action="store_true", help="skip the Gemma digest act")
    args = ap.parse_args()
    PAUSE = max(0.0, args.pause)

    print()
    print(c("  UNPILE", BOLD + GREEN) + c("  .  your read-later pile, triaged by an open model on your own machine", DIM))
    print(c("  TabPFN-v2 (decides) + Gemma 3 (writes), 100% local, $0.", DIM))
    beat()

    agent = TriageAgent()           # loads the dummy history (data/saved_items.csv)
    pile = demo_pile()              # a believable 14-item backlog with human titles

    act1_data(agent)
    tri = act2_decisions(agent, pile)
    if not args.no_digest:
        act3_digest(tri)
    act4_scorecard(agent)

    rule("That is the whole loop: your data -> a decision with reasons -> a digest -> honest proof.")
    print(c("  Run the live app:  ", DIM) + c("python run.py", BOLD) + c("   then open http://127.0.0.1:8099", DIM))
    print(c("  Bring your own pile: upload a Pocket / Instapaper / CSV export in the app.", DIM))
    print()


if __name__ == "__main__":
    main()
