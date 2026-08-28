"""The robustness checks the advanced agent can run. Each is a pure,
deterministic function of the case (no LLM, no network) that returns a small
dict of evidence. The agent decides which to run; the numbers decide the verdict.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

from lib.backtest import backtest


@dataclass
class CheckCtx:
    signal: Callable[..., pd.Series]
    params: dict
    param_grid: dict
    prices_is: pd.DataFrame
    prices_oos: pd.DataFrame
    report: dict
    strategy_src: str
    ppy: int = 252

    def bt(self, df, params=None, *, lag=1, cost=0.0):
        return backtest(df, self.signal(df, **(params or self.params)),
                        execution_lag=lag, cost_bps=cost, periods_per_year=self.ppy)


def _ratio(a: float, b: float) -> float:
    return round(a / b, 3) if abs(b) > 1e-9 else float("nan")


# --- checks ---------------------------------------------------------------------
def oos_test(ctx: CheckCtx) -> dict:
    is_b = ctx.bt(ctx.prices_is)
    oos_b = ctx.bt(ctx.prices_oos)
    return {
        "is_sharpe": is_b["sharpe"], "oos_sharpe": oos_b["sharpe"],
        "oos_over_is": _ratio(oos_b["sharpe"], is_b["sharpe"]),
        "oos_max_drawdown": oos_b["max_drawdown"], "oos_total_return": oos_b["total_return"],
        "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise.",
    }


def walk_forward(ctx: CheckCtx, k: int = 5) -> dict:
    full = pd.concat([ctx.prices_is, ctx.prices_oos], ignore_index=True)
    n = len(full)
    test_len = n // (k + 1)
    keys = list(ctx.param_grid)
    folds = []
    for i in range(1, k + 1):
        split = i * test_len
        train, test = full.iloc[:split], full.iloc[split:split + test_len]
        if len(test) < 30:
            break
        best, best_s = ctx.params, -1e9
        for combo in itertools.product(*[ctx.param_grid[x] for x in keys]) if keys else [()]:
            p = dict(zip(keys, combo)) or ctx.params
            s = backtest(train, ctx.signal(train, **p), periods_per_year=ctx.ppy)["sharpe"]
            if s > best_s:
                best, best_s = p, s
        folds.append({
            "test_sharpe_fixed": backtest(test, ctx.signal(test, **ctx.params), periods_per_year=ctx.ppy)["sharpe"],
            "test_sharpe_refit": backtest(test, ctx.signal(test, **best), periods_per_year=ctx.ppy)["sharpe"],
        })
    fixed = [f["test_sharpe_fixed"] for f in folds] or [0.0]
    refit = [f["test_sharpe_refit"] for f in folds] or [0.0]
    # regime_like: the strategy is strongly positive in some folds and clearly negative in others
    regime_like = len(fixed) >= 3 and max(fixed) > 0.6 and min(fixed) < -0.1
    return {
        "n_folds": len(folds),
        "wf_sharpe_fixed_mean": round(float(np.mean(fixed)), 3),
        "wf_sharpe_refit_mean": round(float(np.mean(refit)), 3),
        "fold_sharpes_fixed": [round(x, 2) for x in fixed],
        "regime_like": bool(regime_like),
        "folds": folds,
        "reading": "Mean out-of-fold Sharpe near zero => no edge that survives honest re-testing; "
                   "strongly positive in some folds and negative in others => regime-dependent.",
    }


def monte_carlo_permutation(ctx: CheckCtx, n_perm: int = 200, block: int = 20, seed: int = 12345) -> dict:
    rng = np.random.default_rng(seed)
    ret = ctx.prices_is["close"].pct_change().dropna().to_numpy()
    n = len(ret)
    s0 = float(ctx.prices_is["close"].iloc[0])
    observed = ctx.bt(ctx.prices_is)["sharpe"]
    null = []
    n_blocks = n // block + 1
    for _ in range(n_perm):
        starts = rng.integers(0, n - block, size=n_blocks)
        boot = np.concatenate([ret[s:s + block] for s in starts])[:n]
        close = s0 * np.cumprod(1.0 + boot)
        noise = np.abs(rng.normal(0, close * 0.001))
        df = pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": close + noise,
                           "low": close - noise, "close": close})
        null.append(backtest(df, ctx.signal(df, **ctx.params), periods_per_year=ctx.ppy)["sharpe"])
    null = np.array(null)
    p = float((1 + np.sum(null >= observed)) / (n_perm + 1))
    return {
        "observed_sharpe": round(observed, 3), "n_perm": n_perm,
        "null_sharpe_mean": round(float(null.mean()), 3),
        "null_sharpe_p95": round(float(np.percentile(null, 95)), 3),
        "p_value": round(p, 4),
        "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces.",
    }


def param_sensitivity(ctx: CheckCtx) -> dict:
    keys = list(ctx.param_grid)
    if not keys:
        return {"note": "no parameter grid supplied", "plateau_score": None}
    grid_pts, sharpes = [], []
    for combo in itertools.product(*[ctx.param_grid[x] for x in keys]):
        p = dict(zip(keys, combo))
        grid_pts.append(p)
        sharpes.append(backtest(ctx.prices_is, ctx.signal(ctx.prices_is, **p), periods_per_year=ctx.ppy)["sharpe"])
    sharpes = np.array(sharpes)
    reported_s = backtest(ctx.prices_is, ctx.signal(ctx.prices_is, **ctx.params), periods_per_year=ctx.ppy)["sharpe"]

    def is_neighbour(p):
        diffs = 0
        for x in keys:
            gi = ctx.param_grid[x]
            if ctx.params.get(x) in gi and p[x] in gi:
                diffs += abs(gi.index(p[x]) - gi.index(ctx.params[x]))
            elif p[x] != ctx.params.get(x):
                diffs += 2
        return 0 < diffs <= 1

    nb = [s for p, s in zip(grid_pts, sharpes) if is_neighbour(p)]
    neighbour_mean = float(np.mean(nb)) if nb else float(sharpes.mean())
    plateau = _ratio(neighbour_mean, float(reported_s))
    fragile = (reported_s > 0.3 and plateau is not None and not np.isnan(plateau) and plateau < 0.6)
    return {
        "grid_size": len(sharpes),
        "reported_sharpe": round(float(reported_s), 3),
        "best_sharpe": round(float(sharpes.max()), 3),
        "median_sharpe": round(float(np.median(sharpes)), 3),
        "frac_positive": round(float((sharpes > 0).mean()), 3),
        "neighbour_mean_sharpe": round(neighbour_mean, 3),
        "plateau_score": plateau,
        "fragile": bool(fragile),
        "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile).",
    }


_FUTURE_PATTERNS = [r"shift\(\s*-", r"\.iloc\[[^\]]*\+\s*1", r"\[\s*i\s*\+\s*1\s*\]",
                    r"close\.shift\(-", r"\.tail\(-", r"iloc\[::-1\]"]


def lookahead_probe(ctx: CheckCtx) -> dict:
    flags = [pat for pat in _FUTURE_PATTERNS if re.search(pat, ctx.strategy_src)]
    b1 = ctx.bt(ctx.prices_is, lag=1)
    s1 = b1["sharpe"]
    s2 = ctx.bt(ctx.prices_is, lag=2)["sharpe"]
    s3 = ctx.bt(ctx.prices_is, lag=3)["sharpe"]
    implausible = s1 > 4.0 or b1["win_rate"] > 0.9
    collapses = s1 > 1.5 and _ratio(s3, s1) < 0.25
    return {
        "static_flags": flags,
        "sharpe_lag1": s1, "sharpe_lag2": s2, "sharpe_lag3": s3,
        "win_rate_lag1": b1["win_rate"],
        "suspected": bool(flags) or implausible or collapses,
        "reading": "A static future-reference flag, or an implausible Sharpe/win-rate, means the backtest is a bug not an edge.",
    }


def cost_stress(ctx: CheckCtx) -> dict:
    by = {f"{b}bps": ctx.bt(ctx.prices_is, cost=b)["sharpe"] for b in (0, 1, 2, 5, 10)}
    survives = by["5bps"] > 0.2 and by["5bps"] > 0.4 * by["0bps"]
    return {"sharpe_by_cost": by, "survives_5bps": bool(survives),
            "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}


def trade_count(ctx: CheckCtx) -> dict:
    n = int(ctx.report.get("in_sample", {}).get("n_trades", ctx.bt(ctx.prices_is)["n_trades"]))
    return {"n_trades": n, "adequate": n >= 30,
            "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}


REGISTRY: dict[str, Callable[[CheckCtx], dict]] = {
    "oos_test": oos_test,
    "walk_forward": walk_forward,
    "monte_carlo_permutation": monte_carlo_permutation,
    "param_sensitivity": param_sensitivity,
    "lookahead_probe": lookahead_probe,
    "cost_stress": cost_stress,
    "trade_count": trade_count,
}

ALLOWED_FINDINGS = [
    "oos_collapse", "param_fragility", "lookahead_bias", "regime_dependence",
    "transaction_cost_sensitivity", "insufficient_trades", "robust_oos",
]
