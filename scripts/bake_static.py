#!/usr/bin/env python3
"""Bake a judge-proof static demo for GitHub Pages.

GitHub Pages can't run Python, so we run the REAL stack once here -- TabPFN-v2 decides the
whole demo pile, Gemma writes the real morning digest -- and freeze the result into
web/static-data.json. The static site then shows genuine model output with zero setup,
and the in-browser model.js provides live interactivity (toggle items) that mirrors the
same relationships. For the real thing, clone and run `python run.py`.

Run: python scripts/bake_static.py
"""
from __future__ import annotations
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unpile.triage import TriageAgent, FEATURES, Decision
from unpile.digest import write_digest, MODEL
from unpile.pile import demo_pile

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static-data.json")


def _d(d: Decision) -> dict:
    return {"action": d.action, "prob": d.prob, "reasons": d.reasons, "title": d.title,
            "source": d.source, "topic": d.topic, "length_min": d.length_min}


def main():
    agent = TriageAgent()
    pile = demo_pile()
    print(f"Triaging {len(pile)} demo items with real TabPFN-v2 (CPU)...")
    t = agent.triage(pile)
    m = agent.metrics()
    keepers = [{"title": d.title, "reasons": d.reasons, "length_min": d.length_min} for d in t.kept]
    print(f"Kept {len(t.kept)}, skim {len(t.skim)}, dropped {len(t.dropped)}. "
          f"Writing the real Gemma digest...")
    digest = write_digest(keepers)
    print(f"Digest source: {digest.get('source')}")

    data = {
        "generated": "baked static snapshot (real TabPFN-v2 + Gemma output)",
        "model": {"decider": "TabPFN-v2 (CPU)", "writer": MODEL},
        "pile": pile,
        "triage": {
            "kept": [_d(d) for d in t.kept],
            "skim": [_d(d) for d in t.skim],
            "dropped": [_d(d) for d in t.dropped],
            "total": t.total,
            "minutes_saved": t.minutes_saved,
        },
        "digest": digest,
        "metrics": {
            "precision": m.precision, "recall": m.recall, "silenced_pct": m.silenced_pct,
            "missed_pct": m.missed_pct, "read_rate": m.read_rate, "lift": m.lift,
            "n_test": m.n_test,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT}")
    print(f"metrics: precision={m.precision} recall={m.recall} lift={m.lift}x "
          f"silenced={m.silenced_pct} missed={m.missed_pct}")


if __name__ == "__main__":
    main()
