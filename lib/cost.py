"""Token + USD cost tracking, so the reproduction guide can state cost per task.

Prices are USD per 1M tokens. Edit PRICES if you switch models. Numbers here
are placeholders in the right ballpark for Claude Sonnet / Haiku — verify
against current Anthropic pricing before quoting them in the submission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRICES: dict[str, dict[str, float]] = {
    # model substring -> {input, output} USD per 1M tokens
    "sonnet": {"input": 3.00, "output": 15.00},
    "haiku": {"input": 0.80, "output": 4.00},
    "opus": {"input": 15.00, "output": 75.00},
}


def _price_for(model: str) -> dict[str, float]:
    for key, p in PRICES.items():
        if key in (model or "").lower():
            return p
    return {"input": 0.0, "output": 0.0}


@dataclass
class CostTracker:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    by_tag: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(self, model: str, usage: Any, tag: str = "") -> None:
        it = int(getattr(usage, "input_tokens", 0) or (usage.get("input_tokens", 0) if isinstance(usage, dict) else 0))
        ot = int(getattr(usage, "output_tokens", 0) or (usage.get("output_tokens", 0) if isinstance(usage, dict) else 0))
        p = _price_for(model)
        cost = it / 1_000_000 * p["input"] + ot / 1_000_000 * p["output"]
        self.calls += 1
        self.input_tokens += it
        self.output_tokens += ot
        self.usd += cost
        b = self.by_tag.setdefault(tag or "default", {"calls": 0, "input_tokens": 0, "output_tokens": 0, "usd": 0.0})
        b["calls"] += 1
        b["input_tokens"] += it
        b["output_tokens"] += ot
        b["usd"] += cost

    def summary(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "usd": round(self.usd, 4),
            "by_tag": {k: {**v, "usd": round(v["usd"], 4)} for k, v in self.by_tag.items()},
        }
