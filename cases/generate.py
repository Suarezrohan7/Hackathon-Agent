"""Generate the frozen, labelled test set.

Design: generation and validation are the SAME check. For each case we search a
small, fixed range of seeds for the first one whose data+strategy actually
exhibits the labelled behaviour (edge really holds out-of-sample, overfit really
collapses, the look-ahead bug really shows up, ...). If no seed in range works
the script raises — so a case can never ship with an ambiguous ground truth.
Fully deterministic: fixed seed-scan order, fixed grids.

    python -m cases.generate --seed 7 --fresh     # (re)generate byte-for-byte
    python -m cases.generate --check              # re-validate existing cases only
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from lib.backtest import backtest
from lib.pricegen import momentum_series, mean_revert_series, random_walk, _ohlc_from_close

PPY = 252
ALLOWED_FINDINGS = [
    "oos_collapse", "param_fragility", "lookahead_bias", "regime_dependence",
    "transaction_cost_sensitivity", "insufficient_trades", "robust_oos",
]

# --- self-contained strategy sources (what the trader hands you) --------------
STRAT_SRC: dict[str, str] = {
    "tsmom": '''\
import numpy as np

def signal(df, lookback=20):
    return np.sign(df["close"].pct_change(int(lookback))).fillna(0.0)
''',
    "sma_cross": '''\
import numpy as np

def signal(df, fast=10, slow=50):
    f = df["close"].rolling(int(fast)).mean()
    s = df["close"].rolling(int(slow)).mean()
    return np.sign(f - s).fillna(0.0)
''',
    "rsi_reversion": '''\
import numpy as np

def _rsi(close, period):
    d = close.diff()
    up = d.clip(lower=0).rolling(int(period)).mean()
    dn = (-d.clip(upper=0)).rolling(int(period)).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def signal(df, period=14, low=30, high=70):
    r = _rsi(df["close"], period)
    s = df["close"].mul(0.0)
    s[r < low] = 1.0
    s[r > high] = -1.0
    return s
''',
    "donchian_breakout": '''\
import numpy as np

def signal(df, lookback=20):
    # break of the prior N-bar range (shift(1) -> no look-ahead)
    hh = df["high"].rolling(int(lookback)).max().shift(1)
    ll = df["low"].rolling(int(lookback)).min().shift(1)
    s = df["close"].mul(0.0)
    s[df["close"] > hh] = 1.0
    s[df["close"] < ll] = -1.0
    return s.replace(0.0, np.nan).ffill().fillna(0.0)
''',
    "kitchen_sink": '''\
import numpy as np
import pandas as pd

def _rsi(close, period):
    d = close.diff()
    up = d.clip(lower=0).rolling(int(period)).mean()
    dn = (-d.clip(upper=0)).rolling(int(period)).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)

def signal(df, a=5, b=20, c=14, d=55, e=10):
    m = np.sign(df["close"].rolling(int(a)).mean() - df["close"].rolling(int(b)).mean())
    r = _rsi(df["close"], c)
    rev = pd.Series(np.where(r > d, -1.0, np.where(r < (100 - d), 1.0, 0.0)), index=df.index)
    mom = np.sign(df["close"].diff(int(e)))
    return ((m.fillna(0) + rev + mom.fillna(0)) / 3.0).clip(-1, 1)
''',
    "lookahead_cheat": '''\
import numpy as np

def signal(df, k=1):
    # BUG: uses the NEXT bar's close - a look-ahead leak, not an edge
    future = df["close"].shift(-int(k))
    return np.sign(future - df["close"]).fillna(0.0)
''',
}


# --- price processes --------------------------------------------------------
def trend_then_chop(n: int, seed: int, mu: float = 0.0010, sigma: float = 0.009) -> pd.DataFrame:
    cut = int(n * 0.6)
    a = random_walk(cut, seed, mu=mu, sigma=sigma)
    b = random_walk(n - cut, seed + 1, mu=0.0, sigma=sigma, s0=float(a["close"].iloc[-1]))
    close = np.concatenate([a["close"].to_numpy(), b["close"].to_numpy()])
    return _ohlc_from_close(close, np.random.default_rng(seed + 2))


GENS = {
    "momentum": lambda n, sd, **kw: momentum_series(n, sd, phi=kw.get("phi", 0.35), sigma=kw.get("sigma", 0.01)),
    "meanrev": lambda n, sd, **kw: mean_revert_series(n, sd, kappa=kw.get("kappa", 0.06), sigma=kw.get("sigma", 0.01)),
    "random": lambda n, sd, **kw: random_walk(n, sd, mu=0.0, sigma=kw.get("sigma", 0.011)),
    "trend": lambda n, sd, **kw: random_walk(n, sd, mu=kw.get("mu", 0.0004), sigma=kw.get("sigma", 0.011)),
    "trendchop": lambda n, sd, **kw: trend_then_chop(n, sd, mu=kw.get("mu", 0.0010), sigma=kw.get("sigma", 0.009)),
}


# --- backtest helpers -----------------------------------------------------------
def _load(cdir: Path):
    spec = importlib.util.spec_from_file_location(f"strat_{cdir.name}", cdir / "strategy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _bt(df, sigfn, params, *, lag=1, cost=0.0):
    return backtest(df, sigfn(df, **params), execution_lag=lag, cost_bps=cost, periods_per_year=PPY)


def _grid_best(sigfn, grid: dict, df) -> tuple[dict, float]:
    keys = list(grid)
    best, best_s = None, -1e9
    for combo in itertools.product(*[grid[k] for k in keys]):
        p = dict(zip(keys, combo))
        s = _bt(df, sigfn, p)["sharpe"]
        if s > best_s:
            best, best_s = p, s
    return best, best_s


# --- predicates: label true iff the case's behaviour is unambiguous -----------
def pred_edge(is_df, oos_df, sigfn, p):
    i = _bt(is_df, sigfn, p)["sharpe"]
    o = _bt(oos_df, sigfn, p)["sharpe"]
    on = _bt(oos_df, sigfn, p, cost=5.0)["sharpe"]
    ok = i >= 0.4 and o >= 0.5 and on >= 0.2
    return ok, f"IS {i:.2f} / OOS {o:.2f} / OOS@5bps {on:.2f} (want IS>=0.4, OOS>=0.5, net>=0.2)"


def pred_overfit(is_df, oos_df, sigfn, p):
    i = _bt(is_df, sigfn, p)["sharpe"]
    o = _bt(oos_df, sigfn, p)["sharpe"]
    return (i >= 1.2 and o <= 0.35), f"IS {i:.2f} / OOS {o:.2f} (want IS>=1.2, OOS<=0.35)"


def pred_no_edge(is_df, oos_df, sigfn, p):
    i = _bt(is_df, sigfn, p)["sharpe"]
    o = _bt(oos_df, sigfn, p)["sharpe"]
    return (abs(i) <= 0.35 and abs(o) <= 0.35), f"IS {i:.2f} / OOS {o:.2f} (want both |.|<=0.35)"


def pred_no_edge_lucky(is_df, oos_df, sigfn, p):
    i = _bt(is_df, sigfn, p)["sharpe"]
    o = _bt(oos_df, sigfn, p)["sharpe"]
    return (i >= 0.7 and abs(o) <= 0.25), f"IS {i:.2f} / OOS {o:.2f} (want IS>=0.7, |OOS|<=0.25)"


def pred_lookahead(is_df, oos_df, sigfn, p):
    s1 = _bt(is_df, sigfn, p, lag=1)["sharpe"]
    return s1 >= 3.0, f"IS Sharpe @lag1 {s1:.2f} (want >=3.0; static shift(-) flag also required)"


def pred_regime(is_df, oos_df, sigfn, p):
    # label = no_edge: strong in-sample, gone out-of-sample because the regime changed.
    # From evidence alone this is indistinguishable from luck, so we don't call it "edge".
    i = _bt(is_df, sigfn, p)["sharpe"]
    o = _bt(oos_df, sigfn, p)["sharpe"]
    return (i >= 0.6 and o <= 0.15), f"IS {i:.2f} (trend) / OOS {o:.2f} (chop) (want IS>=0.6, OOS<=0.15)"


def pred_cost(is_df, oos_df, sigfn, p):
    g = _bt(is_df, sigfn, p, cost=0.0)["sharpe"]
    n = _bt(is_df, sigfn, p, cost=5.0)["sharpe"]
    return (g >= 0.4 and n <= 0.05), f"gross {g:.2f} / net@5bps {n:.2f} (want gross>=0.4, net<=0.05)"


def pred_thin(is_df, oos_df, sigfn, p):
    r = _bt(is_df, sigfn, p)
    o = _bt(oos_df, sigfn, p)["sharpe"]
    return (5 <= r["n_trades"] <= 25 and o >= 0.3), f"n_trades {r['n_trades']} / OOS {o:.2f} (want 5..25 trades, OOS>=0.3)"


# --- case catalogue ---------------------------------------------------------
CASES = [
    dict(id="case-01-momentum-edge", label="edge", strat="tsmom",
         title="Time-series momentum on a series with real return autocorrelation",
         findings=["robust_oos"], gen="momentum", genkw=dict(phi=0.35),
         params=dict(lookback=20), grid=dict(lookback=[5, 10, 20, 40, 60]), pred=pred_edge, n=1000),
    dict(id="case-02-meanrev-edge", label="edge", strat="rsi_reversion",
         title="RSI reversion on a mean-reverting (Ornstein-Uhlenbeck) series",
         findings=["robust_oos"], gen="meanrev", genkw=dict(kappa=0.06),
         params=dict(period=14, low=30, high=70),
         grid=dict(period=[7, 14, 21], low=[20, 30, 35], high=[65, 70, 80]), pred=pred_edge, n=1000),
    dict(id="case-03-breakout-edge", label="edge", strat="tsmom",
         title="Time-series momentum on a persistently trending market (low turnover, survives costs)",
         findings=["robust_oos"], gen="trend", genkw=dict(mu=0.0006, sigma=0.011),
         params=dict(lookback=40), grid=dict(lookback=[20, 30, 40, 60]), pred=pred_edge, n=1000),
    dict(id="case-13-meanrev-edge-2", label="edge", strat="rsi_reversion",
         title="RSI reversion on a faster mean-reverting series",
         findings=["robust_oos"], gen="meanrev", genkw=dict(kappa=0.10),
         params=dict(period=10, low=30, high=70),
         grid=dict(period=[7, 10, 14, 21], low=[20, 25, 30], high=[70, 75, 80]), pred=pred_edge, n=1000),

    dict(id="case-04-overfit-kitchensink", label="overfit", strat="kitchen_sink", tune=True,
         title="5-parameter strategy grid-searched to fit one random history",
         findings=["oos_collapse", "param_fragility"], gen="random", genkw=dict(sigma=0.011),
         grid=dict(a=[3, 5, 8, 12], b=[15, 20, 30, 45], c=[7, 14, 21], d=[52, 56, 62], e=[5, 10, 20]),
         pred=pred_overfit, n=500),
    dict(id="case-05-overfit-sma-datamined", label="overfit", strat="sma_cross", tune=True,
         title="SMA-cross windows tuned to a single history",
         findings=["oos_collapse", "param_fragility"], gen="random", genkw=dict(sigma=0.012),
         grid=dict(fast=[3, 5, 8, 10, 13, 18, 25, 32], slow=[25, 35, 50, 70, 95, 130, 175]),
         pred=pred_overfit, n=450),
    dict(id="case-12-overfit-kitchensink-2", label="overfit", strat="kitchen_sink", tune=True,
         title="Another 5-parameter fit on a different random history",
         findings=["oos_collapse", "param_fragility"], gen="random", genkw=dict(sigma=0.010),
         grid=dict(a=[3, 5, 8], b=[12, 20, 30, 45], c=[9, 14, 20], d=[50, 56, 62], e=[6, 12, 24]),
         pred=pred_overfit, n=500),
    dict(id="case-06-lookahead-bug", label="overfit", strat="lookahead_cheat",
         title="Strategy reads the next bar's close; leakage shows in the lag sweep and implausible stats, not an OOS collapse",
         findings=["lookahead_bias"], gen="momentum", genkw=dict(phi=0.05),
         params=dict(k=1), grid=dict(k=[1, 2, 3]), pred=pred_lookahead, n=1000),

    dict(id="case-07-no-edge-random", label="no_edge", strat="donchian_breakout",
         title="Breakout strategy on a pure random walk",
         findings=[], gen="random", genkw=dict(sigma=0.01),
         params=dict(lookback=20), grid=dict(lookback=[10, 20, 30, 40]), pred=pred_no_edge, n=1000),
    dict(id="case-08-no-edge-lucky", label="no_edge", strat="rsi_reversion",
         title="Untuned strategy that happened to look great on one history",
         findings=["oos_collapse"], gen="random", genkw=dict(sigma=0.011),
         params=dict(period=14, low=30, high=70),
         grid=dict(period=[7, 14, 21], low=[25, 30], high=[70, 75]), pred=pred_no_edge_lucky, n=1000),

    dict(id="case-09-regime-dependent", label="no_edge", strat="tsmom",
         title="Trend-following that worked while the trend lasted, then didn't - regime-dependent, not a durable edge",
         findings=["regime_dependence"], gen="trendchop", genkw=dict(mu=0.0012, sigma=0.009),
         params=dict(lookback=20), grid=dict(lookback=[10, 20, 40]), pred=pred_regime, n=1000),
    dict(id="case-10-cost-killed", label="no_edge", strat="rsi_reversion",
         title="Small gross edge that transaction costs erase",
         findings=["transaction_cost_sensitivity"], gen="meanrev", genkw=dict(kappa=0.05, sigma=0.012),
         params=dict(period=3, low=48, high=52),
         grid=dict(period=[2, 3, 5], low=[45, 48], high=[52, 55]), pred=pred_cost, n=1000),
    dict(id="case-11-thin-sample", label="edge", strat="donchian_breakout",
         title="Real edge, but only a handful of trades to judge it on",
         findings=["insufficient_trades", "robust_oos"], gen="trend", genkw=dict(mu=0.0006, sigma=0.012),
         params=dict(lookback=35), grid=dict(lookback=[20, 35, 55]), pred=pred_thin, n=320),
]

SEED_SCAN = 150  # seeds tried per case before giving up


def _emit(cdir: Path, strat: str, params: dict, grid: dict):
    src = STRAT_SRC[strat] + f"\nPARAMS = {params!r}\nPARAM_GRID = {grid!r}\n"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "strategy.py").write_text(src, encoding="utf-8")
    return _load(cdir)


def _report_block(df, sigfn, params) -> dict:
    b = _bt(df, sigfn, params)
    return {k: b[k] for k in ("sharpe", "cagr", "max_drawdown", "win_rate", "n_trades", "total_return", "exposure")}


def build(out: Path, base_seed: int, check_only: bool) -> int:
    rows = []
    for i, c in enumerate(CASES):
        cdir = out / c["id"]
        gen = GENS[c["gen"]]
        n = c.get("n", 1000)
        strat_probe = STRAT_SRC[c["strat"]]

        if check_only:
            mod = _load(cdir)
            rpt = json.loads((cdir / "backtest_report.json").read_text())
            is_df = pd.read_csv(cdir / "data.csv")
            oos_df = pd.read_csv(cdir / "data_oos.csv")
            ok, detail = c["pred"](is_df, oos_df, mod.signal, mod.PARAMS)
            rows.append((c["id"], c["label"], "ok" if ok else "FAIL", detail))
            continue

        # a throwaway module just to get a callable for the seed search
        tmp = _emit(cdir, c["strat"], c.get("params", {k: v[0] for k, v in c["grid"].items()}), c["grid"])
        base = base_seed + 1000 + i * 37
        chosen = None
        for sd in range(base, base + SEED_SCAN):
            is_df = gen(n, sd, **c["genkw"])
            oos_df = gen(n if c["gen"] != "trendchop" else n, sd + 500, **c["genkw"])
            if c["gen"] == "trendchop":
                oos_df = GENS["random"](n, sd + 500, sigma=c["genkw"]["sigma"])  # regime changed to chop
            params = c.get("params")
            if c.get("tune"):
                params, _ = _grid_best(tmp.signal, c["grid"], is_df)
            ok, detail = c["pred"](is_df, oos_df, tmp.signal, params)
            if ok:
                chosen = (sd, is_df, oos_df, params, detail)
                break
        if chosen is None:
            raise SystemExit(f"{c['id']}: no seed in [{base},{base+SEED_SCAN}) satisfied its predicate — widen search or retune")

        sd, is_df, oos_df, params, detail = chosen
        mod = _emit(cdir, c["strat"], params, c["grid"])
        is_df.to_csv(cdir / "data.csv", index=False)
        oos_df.to_csv(cdir / "data_oos.csv", index=False)
        (cdir / "backtest_report.json").write_text(json.dumps({
            "strategy_module": "strategy.py", "params": mod.PARAMS, "param_grid": mod.PARAM_GRID,
            "periods_per_year": PPY, "data_file": "data.csv", "oos_data_file": "data_oos.csv",
            "in_sample": _report_block(is_df, mod.signal, mod.PARAMS),
            "note": "These are IN-SAMPLE results only.",
        }, indent=2), encoding="utf-8")
        (cdir / "meta.yaml").write_text(yaml.safe_dump(
            {"id": c["id"], "title": c["title"], "seed": sd,
             "human_minutes_baseline": 30, "human_minutes_advanced": 5}, sort_keys=False), encoding="utf-8")
        (cdir / "ground_truth.json").write_text(json.dumps({
            "verdict": c["label"], "findings": [{"id": f} for f in c["findings"]], "rationale": c["title"],
        }, indent=2), encoding="utf-8")
        rows.append((c["id"], c["label"], "ok", detail))

    print(f"\n{'case':<32} {'label':<9} {'inv':<5} detail")
    print("-" * 100)
    for r in rows:
        print(f"{r[0]:<32} {r[1]:<9} {r[2]:<5} {r[3]}")
    fails = [r for r in rows if r[2] != "ok"]
    print(f"\n{len(rows) - len(fails)}/{len(rows)} invariants hold.")
    return 1 if fails else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="cases")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    if args.fresh and not args.check:
        for d in out.glob("case-*"):
            shutil.rmtree(d)
    sys.exit(build(out, args.seed, args.check))


if __name__ == "__main__":
    main()
