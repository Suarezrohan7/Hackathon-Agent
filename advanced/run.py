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
of findings. Each finding: {{"id": <id>, "evidence": "<the specific check name + numbers>"}}.

The id MUST be exactly one of: {ALLOWED_FINDINGS}. Never invent an id.

A finding may be included ONLY if a check actually produced the evidence for it:
- oos_collapse           -> oos_test shows oos_over_is < ~0.4 (in-sample was strong, OOS was not)
- param_fragility        -> param_sensitivity plateau_score < ~0.6 AND no look-ahead flag
- lookahead_bias         -> lookahead_probe.suspected is true (static flag or lag-sweep collapse)
- regime_dependence      -> walk_forward folds swing from strongly positive to ~0/negative
- transaction_cost_sensitivity -> cost_stress.survives_5bps is false
- insufficient_trades    -> trade_count.adequate is false
- robust_oos             -> oos_test oos_sharpe >= ~0.45 AND oos_over_is >= ~0.6
- significant_vs_null     -> monte_carlo_permutation p_value < ~0.10

If lookahead_bias applies, do NOT also emit param_fragility for the same instability.
Return [] if nothing qualifies. No commentary."""

DECIDE_SYSTEM = """You are a quantitative analyst writing up a strategy validation result. The
verdict has already been assigned by a transparent evidence rule; your job is the write-up.

Return ONLY JSON: {"rationale": "2-3 sentences citing the specific digest numbers that justify
the verdict"}. If — and only if — a digest number clearly contradicts the verdict, add
{"dissent": "the value and why"}. Do not restate the rule; explain it to a human deciding
whether to risk capital."""


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


def _digest(gathered: dict, prof: dict) -> dict:
    o = gathered.get("oos_test", {})
    mc = gathered.get("monte_carlo_permutation", {})
    wf = gathered.get("walk_forward", {})
    ps = gathered.get("param_sensitivity", {})
    la = gathered.get("lookahead_probe", {})
    cs = gathered.get("cost_stress", {})
    tc = gathered.get("trade_count", {})
    return {
        "reported_is_sharpe": prof.get("reported_is_sharpe"),
        "oos_sharpe": o.get("oos_sharpe"),
        "oos_over_is": o.get("oos_over_is"),
        "mc_p_value": mc.get("p_value"),
        "walk_forward_fixed_mean": wf.get("wf_sharpe_fixed_mean"),
        "walk_forward_regime_like": wf.get("regime_like"),
        "walk_forward_folds": wf.get("fold_sharpes_fixed"),
        "param_plateau_score": ps.get("plateau_score"),
        "param_fragile": ps.get("fragile"),
        "lookahead_suspected": bool(la.get("suspected")),
        "lookahead_static_flags": la.get("static_flags"),
        "cost_survives_5bps": cs.get("survives_5bps"),
        "n_trades": tc.get("n_trades", prof.get("reported_n_trades")),
        "checks_run": sorted(gathered),
    }


def _num(x, default=0.0):
    return x if isinstance(x, (int, float)) else default


def evidence_verdict(d: dict) -> tuple[str, str]:
    """Transparent classification over the verified evidence. The LLM plans the
    checks and interprets the findings; this rule assigns the label so the
    verdict is reproducible and cannot drift."""
    is_s = _num(d.get("reported_is_sharpe"))
    oos_s = _num(d.get("oos_sharpe"))
    frag = bool(d.get("param_fragile"))
    cost_ok = d.get("cost_survives_5bps")
    thin = _num(d.get("n_trades"), 999) < 30

    if d.get("lookahead_suspected"):
        return "overfit", "look-ahead leak detected (static future reference / lag-sweep collapse)"
    if cost_ok is False:
        return "no_edge", f"gross signal does not survive 5bps costs (oos_sharpe {oos_s:.2f} gross)"
    if oos_s >= 0.40:
        note = " (thin sample — low confidence)" if thin else ""
        return "edge", f"holds out of sample net of costs: oos_sharpe {oos_s:.2f}{note}"
    if is_s >= 0.70 and oos_s <= 0.15 and frag:
        return "overfit", f"in-sample Sharpe {is_s:.2f} collapsed to {oos_s:.2f} out of sample; parameters are a fragile spike"
    if is_s >= 0.60 and oos_s <= 0.15:
        return "no_edge", f"in-sample Sharpe {is_s:.2f} did not repeat out of sample ({oos_s:.2f}); parameters are not fragile, so this reads as luck / regime, not curve-fitting"
    return "no_edge", f"no out-of-sample edge (oos_sharpe {oos_s:.2f})"


def derive_findings(d: dict, verdict: str, verified: list) -> list:
    """Findings the evidence provably supports. Starts from the code-gated
    verified list, then guarantees the ones the rule itself implies."""
    keep = {f["id"] for f in verified}
    add = set()
    if d.get("lookahead_suspected"):
        add.add("lookahead_bias")
    if d.get("cost_survives_5bps") is False:
        add.add("transaction_cost_sensitivity")
    if _num(d.get("n_trades"), 999) < 30:
        add.add("insufficient_trades")
    if verdict == "overfit" and not d.get("lookahead_suspected"):
        add.update({"oos_collapse", "param_fragility"})
    if verdict == "no_edge" and _num(d.get("reported_is_sharpe")) >= 0.6 and _num(d.get("oos_sharpe")) <= 0.15:
        add.add("oos_collapse")
    if verdict == "edge" and _num(d.get("oos_over_is")) >= 0.6 and _num(d.get("oos_sharpe")) >= 0.45:
        add.add("robust_oos")
    if d.get("walk_forward_regime_like"):
        add.add("regime_dependence")
    ids = (keep | add) & set(ALLOWED_FINDINGS)
    ev = {f["id"]: f.get("evidence", "") for f in verified}
    return [{"id": i, "evidence": ev.get(i, "implied by the evidence rule")} for i in sorted(ids)]


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
    # safety net: every check must have run before we classify. The model still
    # owns ordering, its own reasoning, and the evidence summary above.
    for must in REGISTRY:
        if must not in gathered:
            tr.retry(f"safety net: required check '{must}' not run by the planner; running it directly")
            dispatch(must, {})

    tr.note("verify findings against raw numbers")
    verified_raw = _parse(chat(
        [{"role": "user", "content": "Raw check outputs:\n" + json.dumps(gathered, indent=2, default=str) +
          "\n\nEvidence summary from the run:\n" + summary}],
        system=VERIFY_SYSTEM, tracker=ctx.tracker, trajectory=tr, tag="advanced.verify",
    )["text"], default=[])
    # code-enforce the allowed set — the model does not get to invent finding ids
    verified = []
    seen = set()
    for f in verified_raw if isinstance(verified_raw, list) else []:
        fid = str((f.get("id") if isinstance(f, dict) else f) or "").strip().lower()
        if fid in ALLOWED_FINDINGS and fid not in seen:
            seen.add(fid)
            verified.append({"id": fid, "evidence": f.get("evidence", "") if isinstance(f, dict) else ""})
    if len(verified) != len(verified_raw or []):
        tr.note(f"dropped {len(verified_raw or []) - len(verified)} finding(s) not in the allowed set")

    digest = _digest(gathered, prof)
    tr.note(f"digest: {json.dumps(digest, default=str)}")

    # the verdict is a transparent function of the verified evidence — it cannot drift
    verdict, rule_reason = evidence_verdict(digest)
    findings = derive_findings(digest, verdict, verified)
    tr.note(f"evidence rule -> {verdict}: {rule_reason}")

    # the LLM writes the human-facing rationale and may raise a dissent (logged, not acted on)
    llm = _parse(chat(
        [{"role": "user", "content":
          f"The evidence rule classified this strategy as: {verdict.upper()} ({rule_reason}).\n\n"
          "Verified findings:\n" + json.dumps(findings, indent=2, default=str) +
          "\n\nNumeric digest of the checks:\n" + json.dumps(digest, indent=2, default=str) +
          "\n\nWrite the analyst-facing rationale for this verdict in 2-3 sentences, citing the "
          "specific numbers. If you believe the rule is wrong here, add a field "
          '"dissent" naming the digest value that makes it wrong.'}],
        system=DECIDE_SYSTEM, tracker=ctx.tracker, trajectory=tr, tag="advanced.decide",
    )["text"], default={})
    rationale = (llm.get("rationale") if isinstance(llm, dict) else None) or rule_reason
    if isinstance(llm, dict) and llm.get("dissent"):
        tr.note(f"LLM dissent (not acted on): {llm['dissent']}")

    decided = {"verdict": verdict, "rationale": rationale, "findings": findings}

    if verdict == "edge":
        tr.human_checkpoint(
            "Verdict = edge. Advance this strategy to a paper-trading track before any live capital?",
            decision="pending human reviewer sign-off",
        )

    arts = tr.finish(decided)
    if return_detail:
        return decided, {"profile": prof, "digest": digest, "gathered": gathered,
                         "verified_findings": verified, "trajectory": arts}
    return decided
