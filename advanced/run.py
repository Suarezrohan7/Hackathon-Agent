"""Advanced solution — the engineered agent.

Contract: run(case_dir, ctx) -> dict   (same input, same scorer as the baseline)

Skeleton only until the domain is locked. The shape it will take:

    1. PROFILE   — deterministic pass over the input (no model) → structured facts
    2. PLAN      — model picks which checks/tools matter for THIS case
    3. EXECUTE   — tool loop: each check is a real function returning evidence
    4. VERIFY    — a second model pass re-checks each finding against raw input
                   to kill false positives (the anti-contamination / anti-hallucination step)
    5. DECIDE    — model produces the final verdict + evidence, JSON only
    6. HUMAN     — ctx surfaces a checkpoint before any consequential action

Every step is logged to the Trajectory; every model call to the CostTracker.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.llm import chat, run_tool_loop

PLAN_SYSTEM = (
    "You are a meticulous senior engineer. You are given structured facts about a "
    "piece of work under review. Decide which of the available checks are worth "
    "running and why. Be selective; justify each choice in one line."
)

DECIDE_SYSTEM = (
    "You are a meticulous senior engineer. Given the evidence gathered by the "
    "checks, return ONLY JSON: {\"verdict\": \"...\", \"rationale\": \"...\", "
    "\"findings\": [{\"id\": \"...\", \"evidence\": \"...\"}]}. "
    "Every claim must point at evidence from the checks. No prose outside JSON."
)


# --- step 1: deterministic profile (no model) ----------------------------------
def profile(case_dir: Path) -> dict[str, Any]:
    """Cheap, deterministic facts about the input. Fill in per domain."""
    files = [f.name for f in sorted(case_dir.iterdir())
             if f.is_file() and f.name not in {"meta.yaml", "ground_truth.json"}]
    return {"files": files, "note": "domain-specific profiling goes here"}


# --- step 3: the check tools -------------------------------------------------
# Each tool is a plain function returning evidence. Registered for the model here.
TOOLS: list[dict[str, Any]] = [
    {
        "name": "inspect",
        "description": "Return the raw content of one input file for close reading.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
    # domain checks get added here: walk_forward / monte_carlo / param_sensitivity
    # for the strategy agent; schema_diff / totals_row_scan / type_drift for QA.
]


def make_dispatch(case_dir: Path):
    def dispatch(name: str, args: dict[str, Any]) -> Any:
        if name == "inspect":
            p = case_dir / args["filename"]
            if not p.exists():
                raise FileNotFoundError(args["filename"])
            return {"filename": p.name, "content": p.read_text(encoding="utf-8", errors="replace")[:8000]}
        raise ValueError(f"unknown tool: {name}")
    return dispatch


# --- step 5: parse the verdict --------------------------------------------------
def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception:
        return {"verdict": "", "rationale": f"unparseable: {text[:200]}", "findings": []}


def run(case_dir: Path, ctx: Any) -> dict[str, Any]:
    tr = ctx.trajectory()

    tr.note("step 1 — deterministic profile")
    facts = profile(case_dir)

    tr.note("step 2/3 — plan + execute checks via tool loop")
    gathered = run_tool_loop(
        system=PLAN_SYSTEM,
        user=(
            "Structured facts about the work under review:\n"
            f"{json.dumps(facts, indent=2)}\n\n"
            "Use the tools to gather the evidence you need, then summarise what you found."
        ),
        tools=TOOLS,
        dispatch=make_dispatch(case_dir),
        tracker=ctx.tracker,
        trajectory=tr,
        tag="advanced.plan_execute",
    )

    tr.note("step 4 — verify findings against raw input")
    verified = chat(
        [{"role": "user", "content": (
            "Here is the evidence gathered:\n" + gathered +
            "\n\nRe-check each finding against the raw facts. Drop anything not "
            "directly supported. Return the surviving evidence as a short list."
        )}],
        system="You are a skeptical reviewer. Remove unsupported claims.",
        tracker=ctx.tracker, trajectory=tr, tag="advanced.verify",
    )["text"]

    tr.note("step 5 — final verdict")
    decided = chat(
        [{"role": "user", "content": f"Verified evidence:\n{verified}\n\nGive the final verdict."}],
        system=DECIDE_SYSTEM,
        tracker=ctx.tracker, trajectory=tr, tag="advanced.decide",
    )["text"]
    pred = _parse_json(decided)

    # step 6 — human checkpoint before any consequential action (none yet in skeleton)
    tr.human_checkpoint("Consequential action to take based on this verdict?", decision="none — read-only analysis")

    tr.finish(pred)
    return pred
