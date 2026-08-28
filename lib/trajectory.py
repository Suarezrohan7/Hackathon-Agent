"""Trajectory capture — a required submission artifact.

Records what an agent did, step by step: model turns, tool calls and their
results, retries, human checkpoints, and the final result. Writes a live
`.jsonl` (append-only, crash-safe) and renders a readable `.md` on finish.

Usage:
    tr = Trajectory(run_id="advanced/case-03", out_dir="trajectories")
    tr.note("planning which robustness tests to run")
    tr.model_turn(system=..., messages=..., response_text=..., usage=...)
    tr.tool_call("walk_forward", {"splits": 5})
    tr.tool_result("walk_forward", {"oos_sharpe": 0.3})
    tr.retry("tool raised: not enough bars")
    tr.human_checkpoint("approve destructive step?", decision="approved")
    tr.finish({"verdict": "overfit"})
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Trajectory:
    def __init__(self, run_id: str, out_dir: str | Path = "trajectories"):
        self.run_id = run_id
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        safe = run_id.replace("/", "__").replace(" ", "_")
        self.jsonl_path = self.out_dir / f"{safe}.jsonl"
        self.md_path = self.out_dir / f"{safe}.md"
        self.steps: list[dict[str, Any]] = []
        self.t0 = time.time()
        self._emit("start", {"run_id": run_id, "ts": _now()})

    # -- recording -----------------------------------------------------------
    def note(self, text: str) -> None:
        self._emit("note", {"text": text})

    def model_turn(self, *, response_text: str, usage: Any = None,
                   system: str | None = None, messages: Any = None,
                   model: str | None = None) -> None:
        self._emit("model_turn", {
            "model": model,
            "system_preview": _clip(system) if system else None,
            "messages_preview": _clip(json.dumps(messages, default=str)) if messages else None,
            "response_text": response_text,
            "usage": _usage_dict(usage),
        })

    def tool_call(self, name: str, args: Any) -> None:
        self._emit("tool_call", {"name": name, "args": args})

    def tool_result(self, name: str, result: Any, ok: bool = True) -> None:
        self._emit("tool_result", {"name": name, "ok": ok, "result": result})

    def retry(self, reason: str) -> None:
        self._emit("retry", {"reason": reason})

    def human_checkpoint(self, prompt: str, decision: str) -> None:
        self._emit("human_checkpoint", {"prompt": prompt, "decision": decision})

    def finish(self, result: Any) -> dict[str, Any]:
        self._emit("finish", {"result": result,
                              "elapsed_s": round(time.time() - self.t0, 2)})
        self._render_md()
        return {"trajectory_md": str(self.md_path), "trajectory_jsonl": str(self.jsonl_path)}

    # -- internals ---------------------------------------------------------
    def _emit(self, kind: str, data: dict[str, Any]) -> None:
        step = {"i": len(self.steps), "kind": kind, "t": round(time.time() - self.t0, 3), **data}
        self.steps.append(step)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(step, default=str) + "\n")

    def _render_md(self) -> None:
        lines = [f"# Trajectory — `{self.run_id}`", "", f"_Rendered {_now()}_", ""]
        for s in self.steps:
            k = s["kind"]
            if k == "start":
                lines.append(f"**START** `{s['run_id']}` @ {s['ts']}")
            elif k == "note":
                lines.append(f"- 💭 {s['text']}")
            elif k == "model_turn":
                u = s.get("usage") or {}
                tok = f" ({u.get('input_tokens','?')}→{u.get('output_tokens','?')} tok)" if u else ""
                lines.append(f"- 🧠 **model**{tok}: {_clip(s['response_text'], 600)}")
            elif k == "tool_call":
                lines.append(f"- 🔧 **call** `{s['name']}` — `{json.dumps(s['args'], default=str)[:400]}`")
            elif k == "tool_result":
                flag = "✅" if s["ok"] else "❌"
                lines.append(f"- {flag} **result** `{s['name']}` — `{json.dumps(s['result'], default=str)[:400]}`")
            elif k == "retry":
                lines.append(f"- 🔁 **retry** — {s['reason']}")
            elif k == "human_checkpoint":
                lines.append(f"- 🧑‍⚖️ **human checkpoint** — {s['prompt']} → **{s['decision']}**")
            elif k == "finish":
                lines.append("")
                lines.append(f"**FINISH** in {s['elapsed_s']}s — result: `{json.dumps(s['result'], default=str)[:600]}`")
            lines.append("")
        self.md_path.write_text("\n".join(lines), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clip(s: str | None, n: int = 300) -> str | None:
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= n else s[:n] + f"… (+{len(s) - n} chars)"


def _usage_dict(usage: Any) -> dict[str, Any] | None:
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
    }
