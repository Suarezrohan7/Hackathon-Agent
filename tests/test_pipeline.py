"""Key-free correctness tests. None of these call an LLM — the checks and the
data generators are deterministic. Run: python -m pytest -q
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from advanced.checks import CheckCtx, cost_stress, lookahead_probe, oos_test, param_sensitivity
from eval.scorer import score
from lib.backtest import backtest
from lib.pricegen import mean_revert_series, momentum_series, random_walk

CASES_DIR = Path(__file__).resolve().parents[1] / "cases"
CASE_DIRS = sorted(p for p in CASES_DIR.glob("case-*") if p.is_dir())


# --- backtest engine --------------------------------------------------------
def test_backtest_long_on_uptrend_is_profitable():
    df = random_walk(400, seed=1, mu=0.002, sigma=0.005)
    b = backtest(df, pd.Series(1.0, index=df.index))
    assert b["total_return"] > 0 and b["n_trades"] == 1


def test_backtest_flat_signal_has_no_trades():
    df = random_walk(200, seed=2)
    b = backtest(df, pd.Series(0.0, index=df.index))
    assert b["n_trades"] == 0 and b["sharpe"] == 0.0


# --- generators have the properties we claim -------------------------------
def test_momentum_series_has_positive_return_autocorr():
    r = momentum_series(4000, seed=3, phi=0.35)["close"].pct_change().dropna()
    assert r.autocorr(1) > 0.15


def test_random_walk_has_near_zero_autocorr():
    r = random_walk(4000, seed=4)["close"].pct_change().dropna()
    assert abs(r.autocorr(1)) < 0.06


def test_mean_revert_series_crosses_its_mean_often():
    c = mean_revert_series(2000, seed=5, kappa=0.06)["close"]
    crossings = int((np.sign(c - c.mean()).diff().abs() > 0).sum())
    assert crossings > 40


# --- the frozen test set --------------------------------------------------
def test_thirteen_cases_present_and_well_formed():
    assert len(CASE_DIRS) == 13
    for d in CASE_DIRS:
        for f in ("strategy.py", "data.csv", "data_oos.csv", "backtest_report.json",
                  "meta.yaml", "ground_truth.json"):
            assert (d / f).exists(), f"{d.name} missing {f}"


def _ctx(case_dir: Path) -> CheckCtx:
    spec = importlib.util.spec_from_file_location(f"s_{case_dir.name}", case_dir / "strategy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rpt = json.loads((case_dir / "backtest_report.json").read_text())
    return CheckCtx(signal=mod.signal, params=dict(rpt["params"]), param_grid=dict(rpt["param_grid"]),
                    prices_is=pd.read_csv(case_dir / "data.csv"),
                    prices_oos=pd.read_csv(case_dir / "data_oos.csv"), report=rpt,
                    strategy_src=(case_dir / "strategy.py").read_text(),
                    ppy=int(rpt["periods_per_year"]))


@pytest.mark.parametrize("case_dir", CASE_DIRS, ids=[d.name for d in CASE_DIRS])
def test_ground_truth_invariant_holds(case_dir):
    """The label must still be unambiguous from the checks alone."""
    gt = json.loads((case_dir / "ground_truth.json").read_text())["verdict"]
    cc = _ctx(case_dir)
    o = oos_test(cc)

    if case_dir.name == "case-06-lookahead-bug":
        assert lookahead_probe(cc)["suspected"] is True
        return
    if case_dir.name == "case-10-cost-killed":
        assert cost_stress(cc)["survives_5bps"] is False
        return
    if case_dir.name == "case-09-regime-dependent":
        # labelled no_edge: strong in the trend, gone in the chop-regime OOS
        assert o["is_sharpe"] >= 0.6 and o["oos_sharpe"] <= 0.15
        return

    if gt == "edge":
        assert o["oos_sharpe"] >= 0.35
    elif gt == "overfit":
        assert (o["oos_over_is"] is not None and o["oos_over_is"] < 0.5) or lookahead_probe(cc)["suspected"]
    elif gt == "no_edge":
        assert abs(o["oos_sharpe"]) < 0.6


def test_overfit_cases_show_param_fragility():
    for name in ("case-04-overfit-kitchensink", "case-05-overfit-sma-datamined"):
        ps = param_sensitivity(_ctx(CASES_DIR / name))
        assert ps["plateau_score"] is None or ps["plateau_score"] < 0.8


# --- scorer -------------------------------------------------------------------
def test_scorer_normalises_verdict_synonyms():
    assert score({"verdict": "Curve-fit"}, {"verdict": "overfit"})["verdict_correct"] == 1.0
    assert score({"verdict": "genuine edge"}, {"verdict": "edge"})["verdict_correct"] == 1.0
    assert score({"verdict": "no real edge"}, {"verdict": "no_edge"})["verdict_correct"] == 1.0
    assert score({"verdict": "edge"}, {"verdict": "no_edge"})["verdict_correct"] == 0.0


def test_scorer_findings_f1():
    gt = {"verdict": "overfit", "findings": [{"id": "oos_collapse"}, {"id": "param_fragility"}]}
    pred = {"verdict": "overfit", "findings": [{"id": "oos_collapse"}, {"id": "lookahead_bias"}]}
    s = score(pred, gt)
    assert s["findings_tp"] == 1 and s["findings_fp"] == 1 and s["findings_fn"] == 1
    assert 0.49 < s["f1"] < 0.51
