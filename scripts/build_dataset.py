#!/usr/bin/env python3
"""Build Unpile's "saved items" dataset.

A grounded, synthetic dataset of items a person saved to a read-later pile (Pocket /
Instapaper / browser bookmarks / "open in a new tab and never close it"). Each row is one
saved item, with the signals you know the moment you save it, plus the honest truth we are
trying to predict: did you ever actually READ it, or did it rot in the pile?

This is a TEACHING dataset: the "was_read" label is generated from documented, realistic
drivers (how long the article is vs. how much time you have, whether it is close to what
you usually read, how many times you reopened the tab, how stale the save is, the source,
whether it is a how-to you can act on vs. an aspirational longread) plus noise, so the
signal -> read relationship is real and learnable by a tabular model, without scraping
anyone's private history. You swap in your own Pocket/CSV export to make it yours, which is
the whole point of the open, local approach.

Columns written to data/saved_items.csv:
    source_id, topic_id, length_min, age_days, reopen_count, topic_affinity,
    is_howto, has_video, save_hour, backlog_size,
    was_read   (target: 1 = you actually read it, 0 = it rotted)

Run: python scripts/build_dataset.py
"""
from __future__ import annotations
import csv
import os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "saved_items.csv")

# Where the item was saved from. weight = baseline "I come back to this source" pull.
SOURCES = [
    # id, name, read_pull
    (0, "newsletter",              0.02),
    (1, "hacker news / reddit",   -0.05),
    (2, "twitter / x thread",     -0.12),
    (3, "youtube (watch later)",  -0.10),
    (4, "docs / reference",        0.18),
    (5, "friend / dm recommend",   0.22),
    (6, "google search result",    0.08),
    (7, "blog / rss",              0.00),
]

# What the item is about, relative to what THIS person usually reads.
TOPICS = [
    (0, "work / current project"),
    (1, "career & productivity"),
    (2, "deep tech / research"),
    (3, "hobby"),
    (4, "news / current events"),
    (5, "aspirational / someday"),
]


def build(n: int = 1200, seed: int = 7) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        src = SOURCES[rng.integers(0, len(SOURCES))]
        topic = TOPICS[rng.integers(0, len(TOPICS))]
        src_id, _, read_pull = src
        topic_id, _ = topic

        length_min = float(np.round(rng.gamma(2.2, 4.5) + 1, 1))   # est. read time, minutes
        age_days = int(rng.integers(0, 400))                        # how long it has sat
        reopen_count = int(rng.poisson(0.5))                        # times you reopened it
        topic_affinity = float(rng.uniform(0, 1))                   # 1 = squarely your lane
        is_howto = int(rng.random() < 0.3)                          # actionable how-to
        has_video = int(src_id == 3 or rng.random() < 0.12)
        save_hour = int(rng.integers(0, 24))                        # hour of day you saved it
        backlog_size = int(rng.integers(20, 900))                   # how buried it is

        # Latent "probability I actually read this". Built from honest behavioural drivers.
        z = 0.0
        z += read_pull * 3.0                                   # source pull
        z += (topic_affinity - 0.5) * 3.2                      # in-your-lane items get read
        z += 0.9 * reopen_count                                # reopening = real intent
        z += 0.8 * is_howto                                    # actionable things get used
        z -= 0.015 * length_min                                # long reads rot (tl;dr)
        z -= 0.004 * age_days                                  # staleness kills it
        z -= 0.0012 * backlog_size                             # buried = forgotten
        z -= 0.35 * has_video                                  # "watch later" = watch never
        z += 0.25 if 6 <= save_hour <= 10 else 0.0             # morning saves get read more
        z -= 0.2 if topic_id == 5 else 0.0                     # "someday/aspirational" rots
        z += rng.normal(0, 0.6)                                # idiosyncratic noise

        p = 1.0 / (1.0 + np.exp(-z))
        was_read = int(rng.random() < p)

        rows.append(dict(
            source_id=src_id,
            topic_id=topic_id,
            length_min=length_min,
            age_days=age_days,
            reopen_count=reopen_count,
            topic_affinity=round(topic_affinity, 3),
            is_howto=is_howto,
            has_video=has_video,
            save_hour=save_hour,
            backlog_size=backlog_size,
            was_read=was_read,
        ))
    return rows


def main():
    rows = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    read = sum(r["was_read"] for r in rows)
    print(f"wrote {len(rows)} saved items -> {OUT}")
    print(f"actually read: {read}/{len(rows)} ({100*read/len(rows):.1f}%)  -> "
          f"{100*(1-read/len(rows)):.1f}% rotted in the pile")


if __name__ == "__main__":
    main()
