"""Unpile triage core: TabPFN-v2 (Prior Labs, open-weight) as a prediction AGENT.

This is more than one `.predict()` call. Prior Labs favours TabPFN used *inside a wider
prediction agent*, so this module runs the whole lazy-triage loop:

  1. PREDICT, for every item in your read-later pile, the probability you will actually
     read it, learned in-context from YOUR OWN history (items you read vs. let rot) in a
     single CPU forward pass (no per-user training, that is the TabPFN property).
  2. DECIDE an action per item from that probability + an honest, tunable keep budget:
       keep  (you'll read this, surfaced for your morning)
       skim  (borderline, worth a one-line summary)
       drop  (it will rot, archive it silently)
  3. EXPLAIN each decision with the signals that drove it (reopened 3x, in your lane,
     45-min longread, 210 days stale...), so the triage is auditable, not a black box.
  4. REPORT honest held-out metrics: precision/recall of "will-read", the % of the pile it
     safely silences, and -- the scary one -- the recall it would cost you (good items it
     wrongly drops). We surface that number instead of hiding it.

100% local: once the TabPFN-v2 weights are cached, this runs with the network off. Your
reading history never leaves the machine.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

os.environ.setdefault("TABPFN_NO_BROWSER", "1")

from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion

FEATURES = [
    "source_id", "topic_id", "length_min", "age_days", "reopen_count",
    "topic_affinity", "is_howto", "has_video", "save_hour", "backlog_size",
]
TARGET = "was_read"
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "saved_items.csv")

SOURCE_NAMES = {
    0: "newsletter", 1: "hacker news / reddit", 2: "twitter / x thread",
    3: "youtube (watch later)", 4: "docs / reference", 5: "friend / dm recommend",
    6: "google search result", 7: "blog / rss",
}
TOPIC_NAMES = {
    0: "work / current project", 1: "career & productivity", 2: "deep tech / research",
    3: "hobby", 4: "news / current events", 5: "aspirational / someday",
}

KEEP = "keep"
SKIM = "skim"
DROP = "drop"


@dataclass
class Decision:
    action: str            # keep | skim | drop
    prob: float            # P(you actually read it), 0-1
    reasons: list[str] = field(default_factory=list)
    title: str = ""
    source: str = ""
    topic: str = ""
    length_min: float = 0.0


@dataclass
class Triage:
    kept: list[Decision] = field(default_factory=list)
    skim: list[Decision] = field(default_factory=list)
    dropped: list[Decision] = field(default_factory=list)
    total: int = 0
    minutes_saved: float = 0.0     # reading time you no longer owe the dropped pile
    model: str = "TabPFN-v2 (CPU)"


@dataclass
class Metrics:
    precision: float
    recall: float
    silenced_pct: float            # share of the pile auto-dropped
    missed_pct: float              # share of truly-good items wrongly dropped (the scary one)
    n_test: int
    read_rate: float               # base rate of actually-read items
    lift: float = 1.0              # kept read-rate / baseline read-rate (how much better)


class TriageAgent:
    """Loads your saved-items history once, conditions TabPFN-v2 once, then triages any
    pile instantly. 'Fit' here is TabPFN in-context conditioning, not training."""

    # TabPFN scales with context size; cap the in-context sample so triage stays fast on
    # CPU without hurting accuracy on this problem.
    CONTEXT = int(os.environ.get("UNPILE_CONTEXT", "300"))
    # Keep / drop probability thresholds (the "keep budget"). Tunable and honest.
    # Chosen on held-out data to lift the kept pile's read-rate well above baseline while
    # silencing most of the backlog. See metrics() and the README "Honest Take".
    KEEP_T = float(os.environ.get("UNPILE_KEEP_T", "0.55"))
    DROP_T = float(os.environ.get("UNPILE_DROP_T", "0.40"))

    def __init__(self, csv_path: str = DATA):
        self.df = pd.read_csv(csv_path)
        if len(self.df) > self.CONTEXT:
            self.df_ctx = self.df.sample(self.CONTEXT, random_state=1).reset_index(drop=True)
        else:
            self.df_ctx = self.df
        self._clf: TabPFNClassifier | None = None
        self._metrics: Metrics | None = None

    def _ensure_model(self) -> TabPFNClassifier:
        if self._clf is None:
            clf = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cpu")
            clf.fit(self.df_ctx[FEATURES].to_numpy(float), self.df_ctx[TARGET].to_numpy(int))
            self._clf = clf
        return self._clf

    def _proba(self, rows: list[dict]) -> np.ndarray:
        """P(read) for many items in ONE TabPFN forward pass."""
        clf = self._ensure_model()
        x = np.array([[float(r[c]) for c in FEATURES] for r in rows], dtype=float)
        p = clf.predict_proba(x)
        # column for the positive class (was_read == 1)
        classes = list(getattr(clf, "classes_", [0, 1]))
        pos = classes.index(1) if 1 in classes else p.shape[1] - 1
        return np.asarray(p[:, pos], dtype=float)

    def _reasons(self, feats: dict, prob: float) -> list[str]:
        """Plain-language drivers behind the decision (auditable triage)."""
        r = []
        if feats.get("reopen_count", 0) >= 2:
            r.append(f"you reopened it {int(feats['reopen_count'])}x (real intent)")
        aff = float(feats.get("topic_affinity", 0.5))
        if aff >= 0.7:
            r.append("squarely in your usual lane")
        elif aff <= 0.3:
            r.append("far from what you usually read")
        if int(feats.get("is_howto", 0)) == 1:
            r.append("actionable how-to")
        lm = float(feats.get("length_min", 0))
        if lm >= 30:
            r.append(f"{int(lm)}-min longread (likely tl;dr)")
        ad = int(feats.get("age_days", 0))
        if ad >= 120:
            r.append(f"{ad} days stale")
        if int(feats.get("has_video", 0)) == 1:
            r.append("'watch later' video")
        if int(feats.get("backlog_size", 0)) >= 500:
            r.append("buried deep in the pile")
        if not r:
            r.append("a borderline call either way")
        return r[:3]

    def _decide(self, prob: float) -> str:
        if prob >= self.KEEP_T:
            return KEEP
        if prob <= self.DROP_T:
            return DROP
        return SKIM

    def triage(self, items: list[dict]) -> Triage:
        """Run the full agent loop over a pile of saved items.

        Each item dict carries the FEATURES plus optional 'title'. Returns the kept /
        skim / dropped buckets with per-item probabilities and reasons."""
        if not items:
            return Triage(total=0)
        probs = self._proba(items)
        out = Triage(total=len(items))
        for it, p in zip(items, probs):
            p = float(round(p, 4))
            action = self._decide(p)
            d = Decision(
                action=action, prob=p, reasons=self._reasons(it, p),
                title=str(it.get("title", "saved item")),
                source=SOURCE_NAMES.get(int(it.get("source_id", 7)), "web"),
                topic=TOPIC_NAMES.get(int(it.get("topic_id", 0)), "general"),
                length_min=float(it.get("length_min", 0)),
            )
            if action == KEEP:
                out.kept.append(d)
            elif action == SKIM:
                out.skim.append(d)
            else:
                out.dropped.append(d)
                out.minutes_saved += d.length_min
        out.kept.sort(key=lambda d: d.prob, reverse=True)
        out.skim.sort(key=lambda d: d.prob, reverse=True)
        out.dropped.sort(key=lambda d: d.prob)
        out.minutes_saved = round(out.minutes_saved, 1)
        return out

    def metrics(self, test_frac: float = 0.2, seed: int = 11) -> Metrics:
        """Honest accuracy: condition on a train split, predict the held-out items, and
        report precision/recall of 'will-read', how much of the pile we silence, and the
        good items we wrongly drop. Cached after first call."""
        if self._metrics is not None:
            return self._metrics
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(self.df))
        n_test = int(len(self.df) * test_frac)
        te = idx[:n_test]
        tr = idx[n_test:][: self.CONTEXT]
        clf = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cpu")
        clf.fit(self.df.iloc[tr][FEATURES].to_numpy(float), self.df.iloc[tr][TARGET].to_numpy(int))
        proba = clf.predict_proba(self.df.iloc[te][FEATURES].to_numpy(float))
        classes = list(getattr(clf, "classes_", [0, 1]))
        pos = classes.index(1) if 1 in classes else proba.shape[1] - 1
        p = proba[:, pos]
        y = self.df.iloc[te][TARGET].to_numpy(int)

        kept_mask = p >= self.KEEP_T          # what we surface
        dropped_mask = p <= self.DROP_T       # what we silence
        tp = int(np.sum(kept_mask & (y == 1)))
        fp = int(np.sum(kept_mask & (y == 0)))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / int(np.sum(y == 1)) if int(np.sum(y == 1)) else 0.0
        silenced = float(np.mean(dropped_mask))
        # good items we wrongly dropped, as a share of all truly-good items (false-neg rate)
        missed = int(np.sum(dropped_mask & (y == 1)))
        missed_pct = missed / int(np.sum(y == 1)) if int(np.sum(y == 1)) else 0.0
        self._metrics = Metrics(
            precision=round(precision, 3), recall=round(recall, 3),
            silenced_pct=round(silenced, 3), missed_pct=round(missed_pct, 3),
            n_test=n_test, read_rate=round(float(np.mean(y)), 3),
            lift=round(precision / float(np.mean(y)), 2) if float(np.mean(y)) else 1.0,
        )
        return self._metrics


if __name__ == "__main__":
    agent = TriageAgent()
    sample_pile = [
        dict(title="The one Postgres index you forgot", source_id=4, topic_id=0,
             length_min=8.0, age_days=3, reopen_count=2, topic_affinity=0.9,
             is_howto=1, has_video=0, save_hour=9, backlog_size=140),
        dict(title="A 2-hour video essay on medieval economics", source_id=3, topic_id=5,
             length_min=120.0, age_days=240, reopen_count=0, topic_affinity=0.2,
             is_howto=0, has_video=1, save_hour=23, backlog_size=780),
        dict(title="Thread: 12 productivity tips", source_id=2, topic_id=1,
             length_min=6.0, age_days=60, reopen_count=0, topic_affinity=0.5,
             is_howto=0, has_video=0, save_hour=14, backlog_size=400),
    ]
    t = agent.triage(sample_pile)
    print(f"Pile of {t.total}: keep {len(t.kept)}, skim {len(t.skim)}, drop {len(t.dropped)}")
    print(f"Reading time reclaimed from the drop pile: {t.minutes_saved} min")
    for d in t.kept + t.skim + t.dropped:
        print(f"  [{d.action.upper():4}] p={d.prob:.2f}  {d.title}  -- {'; '.join(d.reasons)}")
    m = agent.metrics()
    print(f"\nHeld-out: precision {m.precision}, recall {m.recall}, "
          f"silenced {m.silenced_pct*100:.0f}% of the pile, "
          f"wrongly dropped {m.missed_pct*100:.0f}% of the good stuff")
