"""Advanced solution — the engineered Strategy Validation Agent.

    profile (deterministic)
      -> plan + execute checks   (LLM chooses; tools return real numbers)
      -> verify findings         (LLM keeps only what the numbers support)
      -> decide                  (LLM; sees the evidence, NOT the glossy in-sample report)
      -> human checkpoint        (a positive verdict is gated on sign-off)

Contract: run(case_dir, ctx) -> {"verdict", "rationale", "findings":[{id, evidence}]}
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from advanced.checks import ALLOWED_FINDINGS, REGISTRY, CheckCtx
from lib.llm import chat, run_tool_loop

_FUTURE = [r"shift\(\s*-", r"\.iloc\[[^\]]*\+\s*1", r"\[\s*i\s*\+\s*1\s*\]"]

PLAN_SYSTEM = f"""You audit whether a backtested trading strategy has a REAL edge or is
curve-fit / lucky / buggy. You are given profile facts and a set of check tools.

Rules:
- You MUST call `oos_test` and `monte_carlo_permutation`.
- Call `lookahead_probe` whenever the profile shows any future-reference flag OR the
  reported Sharpe looks implausible.
- Call `param_sensitivity` and `walk_forward` when parameters were or may have been tuned.
- Call `cost_stress` when turnover/exposure looks high; `trade_count` always is cheap.
- After you have enough evidence, STOP calling tools and write a short plain-text
  summary of the raw numbers you gathered. Do not give a verdict yet."""

VERIFY_SYSTEM = f"""You are a skeptical reviewer. Given raw check outputs, return ONLY a JSON list
of findings. Each finding: {{"id": <one of {ALLOWED_FINDINGS}>, "evidence": "<the specific
numbers that justify it>"}}. Include a finding ONLY if the numbers directly support it.
`robust_oos` and `significant_vs_null` are positive findings — include them when warranted."""

DECIDE_SYSTEM = """You issue the final verdict on a trading strategy. You are given the VERIFIED
findings and a numeric digest of the checks. You are deliberately NOT given the strategy's
own in-sample backtest report — decide only from the out-of-sample / statistical evidence.

Return ONLY JSON: {"verdict": "edge"|"overfit"|"no_edge", "rationale": "...",
"findings": [{"id": "...", "evidence": "..."}]}

Guidance (use judgement, these are not hard rules):
- "overfit": a look-ahead flag is present, OR in-sample looked strong but oos_over_is < ~0.35
  AND param plateau_score < ~0.5 (a lone spike).
- "no_edge": oos_sharpe < ~0.3 and p_value >= ~0.10, or the edge dies under costs, without a
  strong tuning/look-ahead signature.
- "edge": oos_sharpe >= ~0.45 AND p_value < ~0.10 AND survives costs AND no look-ahead flag.
  Still report findings like `regime_dependence` or `insufficient_trades` when present."""


def _load_strategy(case_dir: Path):
    spec = importlib.util.spec_from_file_location(f"strat_{case_dir.name}", case_dir / "strategy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _build_ctx(case_dir: Path) -> CheckCtx:
    mod = _load_strategy(case_dir)
    report = json.loads((case_dir / "backtest_report.json").read_text(encoding="utf-8"))
    return CheckCtx(
        signal=mod.signal,
        params=dict(report.get("params", getattr(mod, "PARAMS", {}))),
        param_grid=dict(report.get("param_grid", getattr(mod, "PARAM_GRID", {}))),
        prices_is=pd.read_csv(case_dir / "data.csv"),
        prices_oos=pd.read_csv(case_dir / "data_oos.csv"),
        report=report,
        strategy_src=(case_dir / "strategy.py").read_text(encoding="utf-8"),
        ppy=int(report.get("periods_per_year", 252)),
    )


def _profile(cc: CheckCtx) -> dict:
    ins = cc.report.get("in_sample", {})
    return {
        "n_params": len(cc.params),
        "param_names": list(cc.params),
        "param_grid_size": max(1, _grid_size(cc.param_grid)),
        "reported_is_sharpe": ins.get("sharpe"),
        "reported_max_drawdown": ins.get("max_drawdown"),
        "reported_n_trades": ins.get("n_trades"),
        "reported_exposure": ins.get("exposure"),
        "static_future_reference_flags": [p for p in _FUTURE if re.search(p, cc.strategy_src)],
    }


def _grid_size(grid: dict) -> int:
    out = 1
    for v in grid.values():
        out *= max(1, len(v))
    return out


TOOLS = [{"name": name, "description": fn.__doc__ or f"run the {name} check",
          "input_schema": {"type": "object", "properties": {}}} for name, fn in REGISTRY.items()]


def _digest(gathered: dict) -> dict:
    o = gathered.get("oos_test", {})
    mc = gathered.get("monte_carlo_permutation", {})
    wf = gathered.get("walk_forward", {})
    ps = gathered.get("param_sensitivity", {})
    la = gathered.get("lookahead_probe", {})
    cs = gathered.get("cost_stress", {})
    tc = gathered.get("trade_count", {})
    return {
        "oos_sharpe": o.get("oos_sharpe"),
        "oos_over_is": o.get("oos_over_is"),
        "mc_p_value": mc.get("p_value"),
        "walk_forward_fixed_mean": wf.get("wf_sharpe_fixed_mean"),
        "param_plateau_score": ps.get("plateau_score"),
        "lookahead_suspected": la.get("suspected"),
        "lookahead_static_flags": la.get("static_flags"),
        "cost_survives_5bps": cs.get("survives_5bps"),
        "n_trades": tc.get("n_trades"),
        "checks_run": sorted(gathered),
    }


def _parse(text: str, default: Any):
    try:
        start = text.find("[") if default == [] else text.find("{")
        end = text.rfind("]") if default == [] else text.rfind("}")
        return json.loads(text[start:end + 1])
    except Exception:
        return default


def run(case_dir: Path, ctx: Any, *, return_detail: bool = False) -> Any:
    tr = ctx.trajectory()
    cc = _build_ctx(case_dir)

    prof = _profile(cc)
    tr.note(f"profile: {json.dumps(prof)}")

    gathered: dict[str, dict] = {}

    def dispatch(name: str, _args: dict) -> Any:
        res = REGISTRY[name](cc)
        gathered[name] = res
        return res

    summary = run_tool_loop(
        system=PLAN_SYSTEM,
        user="Profile facts:\n" + json.dumps(prof, indent=2) +
             "\n\nRun the checks you judge necessary, then summarise the raw numbers.",
        tools=TOOLS, dispatch=dispatch,
        tracker=ctx.tracker, trajectory=tr, tag="advanced.plan_execute", max_steps=14,
    )
    # safety net: guarantee the critical evidence exists even if the planner under-called.
    # The model still chooses ordering, reasoning, and any extra checks.
    mandatory = ["oos_test", "monte_carlo_permutation", "trade_count"]
    if prof["static_future_reference_flags"]:
        mandatory.append("lookahead_probe")
    if prof["param_grid_size"] > 4:
        mandatory.append("param_sensitivity")
    for must in mandatory:
        if must not in gathered:
            tr.retry(f"safety net: required check '{must}' not run by the planner; running it directly")
            dispatch(must, {})

    tr.note("verify findings against raw numbers")
    verified = _parse(chat(
        [{"role": "user", "content": "Raw check outputs:\n" + json.dumps(gathered, indent=2, default=str) +
          "\n\nEvidence summary from the run:\n" + summary}],
        system=VERIFY_SYSTEM, tracker=ctx.tracker, trajectory=tr, tag="advanced.verify",
    )["text"], default=[])

    digest = _digest(gathered)
    tr.note(f"digest: {json.dumps(digest, default=str)}")

    decided = _parse(chat(
        [{"role": "user", "content":
          "Verified findings:\n" + json.dumps(verified, indent=2, default=str) +
          "\n\nNumeric digest of the checks:\n" + json.dumps(digest, indent=2, default=str) +
          "\n\nIssue the final verdict."}],
        system=DECIDE_SYSTEM, tracker=ctx.tracker, trajectory=tr, tag="advanced.decide",
    )["text"], default={"verdict": "", "rationale": "unparseable", "findings": []})

    if not isinstance(decided, dict):
        decided = {"verdict": "", "rationale": "unparseable", "findings": []}
    decided.setdefault("findings", verified if isinstance(verified, list) else [])

    if str(decided.get("verdict", "")).lower().strip() == "edge":
        tr.human_checkpoint(
            "Verdict = edge. Advance this strategy to a paper-trading track before any live capital?",
            decision="pending human reviewer sign-off",
        )

    arts = tr.finish(decided)
    if return_detail:
        return decided, {"profile": prof, "digest": digest, "gathered": gathered,
                         "verified_findings": verified, "trajectory": arts}
    return decided
