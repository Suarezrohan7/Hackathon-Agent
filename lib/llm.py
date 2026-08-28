"""Thin Claude client shared by baseline/ and advanced/.

- One place to pin the model (reproducibility).
- Logs every call to a CostTracker and a Trajectory if given.
- Minimal tool loop for the advanced agent.
- MOCK mode (env HACKATHON_MOCK=1, or no API key) returns canned output so the
  harness wiring can be tested without spending tokens. Real runs need a key.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable

try:  # load .env if present (never committed)
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

MODEL = "claude-sonnet-5"          # pinned for reproducibility
MAX_TOKENS = 2000


def _mock() -> bool:
    return os.environ.get("HACKATHON_MOCK") == "1" or not os.environ.get("ANTHROPIC_API_KEY")


def chat(
    messages: list[dict[str, Any]],
    *,
    system: str = "",
    tools: list[dict[str, Any]] | None = None,
    tracker: Any = None,
    trajectory: Any = None,
    tag: str = "",
    max_tokens: int = MAX_TOKENS,
) -> dict[str, Any]:
    """Single model turn. Returns {text, tool_uses:[{id,name,input}], raw, usage}."""
    if _mock():
        text = json.dumps({"verdict": "inconclusive", "reason": "MOCK response — set ANTHROPIC_API_KEY for a real run."})
        usage = {"input_tokens": 0, "output_tokens": 0}
        if tracker is not None:
            tracker.add(MODEL, usage, tag=tag)
        if trajectory is not None:
            trajectory.model_turn(response_text=text, usage=usage, system=system, messages=messages, model=MODEL + " [MOCK]")
        return {"text": text, "tool_uses": [], "raw": None, "usage": usage}

    import anthropic  # lazy so MOCK mode needs no dependency

    client = anthropic.Anthropic()
    kwargs: dict[str, Any] = dict(model=MODEL, max_tokens=max_tokens, messages=messages)
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    resp = client.messages.create(**kwargs)

    text_parts, tool_uses = [], []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_uses.append({"id": block.id, "name": block.name, "input": block.input})
    text = "".join(text_parts)

    if tracker is not None:
        tracker.add(MODEL, resp.usage, tag=tag)
    if trajectory is not None:
        trajectory.model_turn(response_text=text or f"[{len(tool_uses)} tool_use]", usage=resp.usage,
                              system=system, messages=messages, model=MODEL)
    return {"text": text, "tool_uses": tool_uses, "raw": resp, "usage": resp.usage}


def run_tool_loop(
    *,
    system: str,
    user: str,
    tools: list[dict[str, Any]],
    dispatch: Callable[[str, dict[str, Any]], Any],
    tracker: Any = None,
    trajectory: Any = None,
    tag: str = "",
    max_steps: int = 12,
) -> str:
    """Drive a tool-using agent until it stops calling tools or hits max_steps."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
    for _ in range(max_steps):
        out = chat(messages, system=system, tools=tools, tracker=tracker, trajectory=trajectory, tag=tag)
        if not out["tool_uses"]:
            return out["text"]
        messages.append({"role": "assistant", "content": out["raw"].content})
        results = []
        for tu in out["tool_uses"]:
            if trajectory is not None:
                trajectory.tool_call(tu["name"], tu["input"])
            try:
                res = dispatch(tu["name"], tu["input"])
                ok = True
            except Exception as e:  # surface tool failure back to the model
                res, ok = {"error": str(e)}, False
                if trajectory is not None:
                    trajectory.retry(f"tool {tu['name']} raised: {e}")
            if trajectory is not None:
                trajectory.tool_result(tu["name"], res, ok=ok)
            results.append({"type": "tool_result", "tool_use_id": tu["id"], "content": json.dumps(res, default=str)})
        messages.append({"role": "user", "content": results})
    return "[max_steps reached]"
