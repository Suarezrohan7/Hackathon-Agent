"""Baseline solution — the reasonable simple approach a busy quant would take:
hand the strategy code and its in-sample backtest report to the model, ask for a
verdict. No data, no out-of-sample test, no tools.

Contract: run(case_dir, ctx) -> {"verdict", "rationale", "findings":[{id, ...}]}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from advanced.checks import ALLOWED_FINDINGS
from lib.llm import chat

SYSTEM = f"""You are a quantitative analyst reviewing a backtested trading strategy before
capital is allocated. Decide whether its edge is real.

Return ONLY JSON: {{"verdict": "edge"|"overfit"|"no_edge", "rationale": "...",
"findings": [{{"id": "..."}}]}}
Allowed finding ids: {ALLOWED_FINDINGS}"""


def run(case_dir: Path, ctx: Any) -> dict[str, Any]:
    tr = ctx.trajectory()
    tr.note("baseline: single model call — strategy source + in-sample report, no tools")

    src = (case_dir / "strategy.py").read_text(encoding="utf-8")
    report = json.loads((case_dir / "backtest_report.json").read_text(encoding="utf-8"))

    user = (
        "STRATEGY (strategy.py):\n```python\n" + src + "\n```\n\n"
        "IN-SAMPLE BACKTEST REPORT:\n" + json.dumps(report, indent=2) +
        "\n\nIs this a real edge, an overfit, or no edge? Give your verdict."
    )
    out = chat([{"role": "user", "content": user}], system=SYSTEM,
               tracker=ctx.tracker, trajectory=tr, tag="baseline")
    txt = out["text"]
    try:
        pred = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    except Exception:
        pred = {"verdict": "", "rationale": f"unparseable: {txt[:200]}", "findings": []}
    pred.setdefault("findings", [])
    tr.finish(pred)
    return pred
