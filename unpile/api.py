"""Unpile API: wires the open stack together and serves the UI.

  GET  /api/health              -> model + ollama status
  GET  /api/meta                -> sources, topics, held-out metrics, model status
  GET  /api/demo                -> a realistic demo backlog (list of items)
  POST /api/triage { items[] }  -> { triage {kept, skim, dropped, minutes_saved, ...},
                                     digest {greeting, blurbs, source}, metrics }

Everything runs locally: TabPFN-v2 (CPU) decides, Gemma via Ollama writes. No external calls.
"""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from unpile.triage import (
    TriageAgent, FEATURES, SOURCE_NAMES, TOPIC_NAMES, Decision,
)
from unpile.digest import write_digest, MODEL
from unpile.pile import demo_pile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")

app = FastAPI(title="Unpile", version="1.0.0")
_agent = TriageAgent()


@app.on_event("startup")
def _warm():
    """Condition TabPFN and compute held-out metrics once at startup so the first real
    triage request is fast instead of paying the one-time cost mid-demo."""
    try:
        _agent._ensure_model()
        _agent.metrics()
    except Exception:
        pass


class Item(BaseModel):
    title: str = "saved item"
    source_id: int = 7
    topic_id: int = 0
    length_min: float = 10.0
    age_days: float = 30.0
    reopen_count: float = 0.0
    topic_affinity: float = 0.5
    is_howto: float = 0.0
    has_video: float = 0.0
    save_hour: float = 12.0
    backlog_size: float = 300.0


class TriageIn(BaseModel):
    items: list[Item] = []


def _ollama_ok() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(
            os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/tags", timeout=3
        )
        return True
    except Exception:
        return False


def _d(d: Decision) -> dict:
    return {"action": d.action, "prob": d.prob, "reasons": d.reasons, "title": d.title,
            "source": d.source, "topic": d.topic, "length_min": d.length_min}


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL, "ollama": _ollama_ok(),
            "decider": "TabPFN-v2 (CPU)"}


@app.get("/api/meta")
def meta():
    m = _agent.metrics()
    return {
        "sources": [{"id": k, "name": v} for k, v in SOURCE_NAMES.items()],
        "topics": [{"id": k, "name": v} for k, v in TOPIC_NAMES.items()],
        "metrics": {
            "precision": m.precision, "recall": m.recall,
            "silenced_pct": m.silenced_pct, "missed_pct": m.missed_pct,
            "n_test": m.n_test, "read_rate": m.read_rate, "lift": m.lift,
        },
        "ollama": _ollama_ok(),
        "model": MODEL,
    }


@app.get("/api/demo")
def demo():
    return {"items": demo_pile()}


@app.post("/api/triage")
def triage(inp: TriageIn):
    items = [{**{c: getattr(it, c) for c in FEATURES}, "title": it.title} for it in inp.items]
    t = _agent.triage(items)
    keepers = [{"title": d.title, "reasons": d.reasons, "length_min": d.length_min}
               for d in t.kept]
    digest = write_digest(keepers)
    m = _agent.metrics()
    return JSONResponse({
        "triage": {
            "kept": [_d(d) for d in t.kept],
            "skim": [_d(d) for d in t.skim],
            "dropped": [_d(d) for d in t.dropped],
            "total": t.total,
            "minutes_saved": t.minutes_saved,
            "model": t.model,
        },
        "digest": digest,
        "metrics": {
            "precision": m.precision, "recall": m.recall,
            "silenced_pct": m.silenced_pct, "missed_pct": m.missed_pct, "lift": m.lift,
        },
    })


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(WEB, "assets")), name="assets")
