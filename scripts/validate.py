"""End-to-end validation of the Unpile API via FastAPI TestClient (in-process).

Exercises the real endpoints and the real TabPFN + Gemma code paths, with no need for a
long-running server. Run: python3.11 scripts/validate.py
"""
from __future__ import annotations
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from unpile.api import app

client = TestClient(app)
fails = 0


def check(name, cond, detail=""):
    global fails
    mark = "PASS" if cond else "FAIL"
    if not cond:
        fails += 1
    print(f"[{mark}] {name}{(' - ' + detail) if detail else ''}")


# 1) health
r = client.get("/api/health")
check("GET /api/health 200", r.status_code == 200, str(r.status_code))
h = r.json()
check("health reports TabPFN decider", "TabPFN" in h.get("decider", ""), h.get("decider"))
print(f"      ollama reachable: {h.get('ollama')}, model: {h.get('model')}")

# 2) meta + honest metrics
r = client.get("/api/meta")
check("GET /api/meta 200", r.status_code == 200, str(r.status_code))
m = r.json()
check("meta has 8 sources", len(m.get("sources", [])) == 8, str(len(m.get("sources", []))))
check("meta has 6 topics", len(m.get("topics", [])) == 6, str(len(m.get("topics", []))))
mt = m.get("metrics", {})
check("precision in (0,1]", 0 < mt.get("precision", 0) <= 1, str(mt.get("precision")))
check("recall in (0,1]", 0 < mt.get("recall", 0) <= 1, str(mt.get("recall")))
check("silences some of the pile", 0 < mt.get("silenced_pct", 0) < 1, str(mt.get("silenced_pct")))
print(f"      held-out: precision={mt.get('precision')} recall={mt.get('recall')} "
      f"silenced={mt.get('silenced_pct')} missed={mt.get('missed_pct')}")

# 3) demo pile
r = client.get("/api/demo")
check("GET /api/demo 200", r.status_code == 200, str(r.status_code))
demo = r.json().get("items", [])
check("demo pile non-trivial (>=10 items)", len(demo) >= 10, str(len(demo)))

# 4) a real triage call (TabPFN decides + Gemma writes the digest)
t0 = time.time()
r = client.post("/api/triage", json={"items": demo})
dt = time.time() - t0
check("POST /api/triage 200", r.status_code == 200, str(r.status_code))
body = r.json()
tri = body.get("triage", {})
dig = body.get("digest", {})
kept, skim, dropped = tri.get("kept", []), tri.get("skim", []), tri.get("dropped", [])
check("every item got a decision", len(kept) + len(skim) + len(dropped) == len(demo),
      f"{len(kept)}+{len(skim)}+{len(dropped)} vs {len(demo)}")
check("it kept at least one item", len(kept) >= 1, str(len(kept)))
check("it dropped at least one item (does the work)", len(dropped) >= 1, str(len(dropped)))
check("reclaims reading time", tri.get("minutes_saved", 0) > 0, str(tri.get("minutes_saved")))
check("keepers carry reasons", all(d.get("reasons") for d in kept), "reasons present")
check("kept probs >= skim probs", (not kept or not skim) or
      min(d["prob"] for d in kept) >= max(d["prob"] for d in skim), "ordering sane")
check("digest has a greeting", bool(dig.get("greeting")), dig.get("source", ""))
check("digest blurbs align with keepers", len(dig.get("blurbs", [])) == len(kept),
      f"{len(dig.get('blurbs', []))} vs {len(kept)}")
print(f"      digest source: {dig.get('source')}  (triage+digest took {dt:.1f}s)")

# 5) the "Postgres tip" keeper and the "2h video" drop are the obvious right calls
titles_kept = " ".join(d["title"].lower() for d in kept + skim)
titles_dropped = " ".join(d["title"].lower() for d in dropped)
check("obvious keeper (reopened how-to) is NOT dropped", "postgres index" not in titles_dropped)
check("obvious rot (2h aspirational video) is dropped", "2-hour video essay" in titles_dropped)

# 6) export parsing path
from unpile.pile import parse_export
csv_text = ("title,source,topic,length_min,age_days,reopen_count,is_howto\n"
            "My own saved link,docs / reference,work / current project,9,2,2,1\n")
parsed = parse_export(csv_text)
check("parse_export reads a user CSV", len(parsed) == 1 and parsed[0]["title"] == "My own saved link",
      str(len(parsed)))

print()
if fails:
    print(f"{fails} check(s) FAILED")
    sys.exit(1)
print("ALL CHECKS PASSED")
