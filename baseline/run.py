"""Baseline solution — the reasonable simple approach: one model call, no tools.

Contract: run(case_dir, ctx) -> dict  (the prediction, scored by eval.scorer)

This is deliberately thin. It reads the case input, asks the model once for a
verdict, and parses JSON out of the reply. Whatever the advanced agent adds on
top of this is the story the changelog tells.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.llm import chat

SYSTEM = (
    "You are a senior engineer reviewing a piece of work. "
    "Return ONLY a JSON object: {\"verdict\": \"...\", \"rationale\": \"...\"}. "
    "No prose outside the JSON."
)


def _load_input(case_dir: Path) -> str:
    parts = []
    for f in sorted(case_dir.iterdir()):
        if f.name in {"meta.yaml", "ground_truth.json"} or f.is_dir():
            continue
        parts.append(f"### {f.name}\n{f.read_text(encoding='utf-8', errors='replace')}")
    return "\n\n".join(parts)


def run(case_dir: Path, ctx: Any) -> dict[str, Any]:
    tr = ctx.trajectory()
    tr.note("baseline: single model call, no tools")
    user = f"Review the following and give your verdict.\n\n{_load_input(case_dir)}"
    out = chat([{"role": "user", "content": user}], system=SYSTEM,
               tracker=ctx.tracker, trajectory=tr, tag="baseline")
    try:
        pred = json.loads(out["text"][out["text"].find("{"): out["text"].rfind("}") + 1])
    except Exception:
        pred = {"verdict": "", "rationale": f"unparseable: {out['text'][:200]}"}
    tr.finish(pred)
    return pred
