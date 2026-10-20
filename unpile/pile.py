"""Unpile demo-pile + import helpers.

Two jobs:
  1. demo_pile(): a hand-written, realistic read-later backlog with human titles, so the
     live demo tells a story (not anonymous rows). Features are set to be faithful to the
     dataset's drivers so TabPFN behaves exactly as it would on real data.
  2. parse_export(): turn a user's own export into Unpile items. Supports a simple CSV
     (title,url,length_min,...) and a Pocket/Instapaper-style CSV. This is the "make it
     yours" path: your pile never leaves your machine.
"""
from __future__ import annotations
import csv
import io

from unpile.triage import FEATURES, SOURCE_NAMES, TOPIC_NAMES

_SRC = {v: k for k, v in SOURCE_NAMES.items()}
_TOP = {v: k for k, v in TOPIC_NAMES.items()}


def demo_pile() -> list[dict]:
    """A believable 14-item backlog: a few real keepers buried under aspirational rot."""
    return [
        dict(title="The one Postgres index you forgot to add",
             source_id=4, topic_id=0, length_min=8, age_days=2, reopen_count=3,
             topic_affinity=0.92, is_howto=1, has_video=0, save_hour=9, backlog_size=180),
        dict(title="A calmer git rebase workflow (that you'll actually keep)",
             source_id=7, topic_id=0, length_min=11, age_days=6, reopen_count=1,
             topic_affinity=0.85, is_howto=1, has_video=0, save_hour=10, backlog_size=180),
        dict(title="DM from a friend: 'this one explains CRDTs properly'",
             source_id=5, topic_id=2, length_min=18, age_days=4, reopen_count=2,
             topic_affinity=0.74, is_howto=0, has_video=0, save_hour=8, backlog_size=180),
        dict(title="A 2-hour video essay on medieval trade routes",
             source_id=3, topic_id=5, length_min=120, age_days=260, reopen_count=0,
             topic_affinity=0.18, is_howto=0, has_video=1, save_hour=23, backlog_size=620),
        dict(title="Thread: 12 productivity hacks that changed my life",
             source_id=2, topic_id=1, length_min=6, age_days=95, reopen_count=0,
             topic_affinity=0.44, is_howto=0, has_video=0, save_hour=15, backlog_size=620),
        dict(title="The complete history of the JavaScript framework wars",
             source_id=1, topic_id=4, length_min=42, age_days=180, reopen_count=0,
             topic_affinity=0.3, is_howto=0, has_video=0, save_hour=1, backlog_size=620),
        dict(title="How to actually use your air fryer (saved during lunch)",
             source_id=6, topic_id=3, length_min=7, age_days=40, reopen_count=0,
             topic_affinity=0.6, is_howto=1, has_video=0, save_hour=13, backlog_size=400),
        dict(title="Someday: build a cabin in the woods, a photo essay",
             source_id=0, topic_id=5, length_min=15, age_days=320, reopen_count=0,
             topic_affinity=0.2, is_howto=0, has_video=0, save_hour=22, backlog_size=620),
        dict(title="Reference: the full CSS grid spec, for 'later'",
             source_id=4, topic_id=0, length_min=35, age_days=150, reopen_count=1,
             topic_affinity=0.7, is_howto=1, has_video=0, save_hour=11, backlog_size=400),
        dict(title="Watch later: 90-min conference keynote",
             source_id=3, topic_id=2, length_min=90, age_days=70, reopen_count=0,
             topic_affinity=0.4, is_howto=0, has_video=1, save_hour=20, backlog_size=620),
        dict(title="Hacker News flamewar about tabs vs spaces (again)",
             source_id=1, topic_id=4, length_min=25, age_days=210, reopen_count=0,
             topic_affinity=0.25, is_howto=0, has_video=0, save_hour=0, backlog_size=620),
        dict(title="Newsletter: this week in AI (issue #214)",
             source_id=0, topic_id=4, length_min=12, age_days=9, reopen_count=0,
             topic_affinity=0.55, is_howto=0, has_video=0, save_hour=7, backlog_size=180),
        dict(title="DM: 'the on-call runbook you asked me for'",
             source_id=5, topic_id=0, length_min=9, age_days=1, reopen_count=2,
             topic_affinity=0.88, is_howto=1, has_video=0, save_hour=9, backlog_size=180),
        dict(title="Aspirational: learn to play jazz piano in 2026",
             source_id=2, topic_id=5, length_min=20, age_days=300, reopen_count=0,
             topic_affinity=0.15, is_howto=0, has_video=1, save_hour=23, backlog_size=620),
    ]


def _num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def parse_export(text: str) -> list[dict]:
    """Parse a user CSV export into Unpile items. Accepts flexible headers:

    - Unpile-native: title + all FEATURES columns -> used directly.
    - Light export: title,url,length_min,age_days,reopen_count,source,topic,is_howto -> we
      map source/topic names to ids and fill sane defaults for the rest.

    Returns a list of item dicts ready for TriageAgent.triage(). Private data stays local:
    this runs in-process on text the user uploaded; nothing is sent anywhere.
    """
    items: list[dict] = []
    reader = csv.DictReader(io.StringIO(text))
    for raw in reader:
        row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
        title = row.get("title") or row.get("name") or row.get("url") or "saved item"
        if all(c in row for c in FEATURES):
            item = {c: _num(row[c]) for c in FEATURES}
            item["title"] = title
            items.append(item)
            continue
        src_name = (row.get("source") or "blog / rss").lower()
        top_name = (row.get("topic") or "work / current project").lower()
        item = dict(
            title=title,
            source_id=_SRC.get(src_name, 7),
            topic_id=_TOP.get(top_name, 0),
            length_min=_num(row.get("length_min"), 10.0),
            age_days=_num(row.get("age_days"), 30.0),
            reopen_count=_num(row.get("reopen_count"), 0.0),
            topic_affinity=_num(row.get("topic_affinity"), 0.5),
            is_howto=_num(row.get("is_howto"), 0.0),
            has_video=_num(row.get("has_video"), 0.0),
            save_hour=_num(row.get("save_hour"), 12.0),
            backlog_size=_num(row.get("backlog_size"), 300.0),
        )
        items.append(item)
    return items
