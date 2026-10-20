"""Unpile digest writer: Gemma 3 (open-weight) via local Ollama.

Supporting layer. TabPFN DECIDES what to keep; Gemma turns the kept pile into a calm,
two-line morning digest and a one-line "why this is worth your time today" for each
keeper. Gemma is given the items and their read-probabilities; it never invents an item.

Runs fully offline against local Ollama. The model is swappable via UNPILE_MODEL (any
Ollama open-weight model). If Ollama is unreachable, a deterministic template writes a
correct digest so the agent never hard-fails and your morning summary always arrives.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.environ.get("UNPILE_MODEL", "gemma3:1b")

SYSTEM = (
    "You are Unpile, a calm morning assistant. You are given a short list of articles a "
    "person actually wants to read today (already filtered from a huge backlog), each with "
    "a title and a one-line reason it survived. Write a STRICT JSON object with keys: "
    "greeting, blurbs. 'greeting' is one short, warm, low-pressure sentence summarising the "
    "morning (e.g. how many made the cut and the vibe). 'blurbs' is an array, one per item "
    "in the SAME order, each a single plain sentence (<= 20 words) telling the person why "
    "it is worth their time today. Never invent an item or a title. No ALL CAPS, no hype, "
    "no markdown, no preamble. Output JSON only."
)


def _rule_based(keepers: list[dict]) -> dict:
    """Deterministic fallback digest, correct and useful with no model."""
    n = len(keepers)
    if n == 0:
        greeting = "Your pile is clear this morning. Nothing urgent made the cut, enjoy the quiet."
    else:
        greeting = (f"{n} thing{'s' if n != 1 else ''} worth your coffee today, the rest is "
                    f"archived. No pressure.")
    blurbs = []
    for k in keepers:
        reason = (k.get("reasons") or ["worth a look"])[0]
        mins = int(float(k.get("length_min", 0)) or 0)
        tail = f" (~{mins} min)" if mins else ""
        blurbs.append(f"{reason.capitalize()}{tail}.")
    return {"greeting": greeting, "blurbs": blurbs}


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        if isinstance(obj, dict) and {"greeting", "blurbs"} <= set(obj):
            if isinstance(obj["blurbs"], str):
                obj["blurbs"] = [b.strip() for b in re.split(r"[\n]", obj["blurbs"]) if b.strip()]
            return obj
    except Exception:
        return None
    return None


def write_digest(keepers: list[dict], timeout: float = 60.0) -> dict:
    """Return {greeting, blurbs, source, model}. source is 'gemma' or 'offline-fallback'.

    keepers: list of dicts with 'title', 'reasons' (list), 'length_min'. Kept short
    (num_predict) with a tight timeout so a slow local CPU degrades gracefully to the
    deterministic fallback instead of blocking your morning."""
    if not keepers:
        fb = _rule_based([])
        fb["source"] = "offline-fallback"
        fb["model"] = "rule-based"
        return fb

    listing = "\n".join(
        f"{i+1}. {k.get('title','item')} -- {(k.get('reasons') or ['worth a look'])[0]} "
        f"(~{int(float(k.get('length_min',0)) or 0)} min)"
        for i, k in enumerate(keepers)
    )
    user = (
        f"Items that made the cut today ({len(keepers)}):\n{listing}\n\n"
        f"Write the JSON digest with a greeting and exactly {len(keepers)} blurbs, in order."
    )
    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM}\n\n{user}\n\nJSON:",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.5, "num_predict": 260},
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out = json.loads(resp.read())
        parsed = _extract_json((out.get("response") or "").strip())
        if parsed:
            blurbs = [str(b).strip() for b in parsed.get("blurbs", []) if str(b).strip()]
            # keep alignment with keepers; pad/truncate defensively
            if len(blurbs) < len(keepers):
                fb = _rule_based(keepers)["blurbs"]
                blurbs += fb[len(blurbs):]
            parsed["blurbs"] = blurbs[: len(keepers)]
            parsed["greeting"] = str(parsed.get("greeting", "")).strip()[:160]
            parsed["source"] = "gemma"
            parsed["model"] = MODEL
            return parsed
    except Exception:
        pass
    fb = _rule_based(keepers)
    fb["source"] = "offline-fallback"
    fb["model"] = "rule-based"
    return fb


if __name__ == "__main__":
    keepers = [
        {"title": "The one Postgres index you forgot", "length_min": 8,
         "reasons": ["you reopened it 2x (real intent)"]},
        {"title": "A calmer git rebase workflow", "length_min": 12,
         "reasons": ["squarely in your usual lane"]},
    ]
    print(json.dumps(write_digest(keepers), indent=2))
