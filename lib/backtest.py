"""Minimal, deterministic vectorised backtester.

Convention (no look-ahead by construction):
    signal[t]  = desired exposure for bar t, computed from data up to & incl. bar t
    position   = signal.shift(execution_lag)      # you act on the *next* bar
    strat_ret[t] = position[t] * asset_ret[t]  - turnover_cost[t]

A strategy that only becomes profitable at execution_lag=0 is leaking future
information — `advanced/checks.py::lookahead_probe` exploits exactly this.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def backtest(
    prices: pd.DataFrame,
    signal: pd.Series,
    *,
    cost_bps: float = 0.0,
    execution_lag: int = 1,
    periods_per_year: int = 252,
) -> dict:
    close = prices["close"].astype(float)
    asset_ret = close.pct_change().fillna(0.0)

    sig = pd.Series(signal, index=prices.index).astype(float).clip(-1, 1).fillna(0.0)
    position = sig.shift(execution_lag).fillna(0.0)

    turnover = position.diff().abs().fillna(position.abs())
    cost = turnover * (cost_bps / 1e4)

    strat_ret = position * asset_ret - cost
    equity = (1.0 + strat_ret).cumprod()

    n = len(strat_ret)
    years = n / periods_per_year if periods_per_year else 1.0
    total_return = float(equity.iloc[-1] - 1.0) if n else 0.0
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if n and years > 0 and equity.iloc[-1] > 0 else float("nan")

    sd = float(strat_ret.std(ddof=1))
    sharpe = float(strat_ret.mean() / sd * np.sqrt(periods_per_year)) if sd > 1e-12 else 0.0

    roll_max = equity.cummax()
    max_dd = float((equity / roll_max - 1.0).min()) if n else 0.0

    # trade segmentation: a trade = a contiguous run of the same non-zero position
    trade_id = (position != position.shift()).cumsum()
    seg = pd.DataFrame({"pos": position, "ret": strat_ret, "tid": trade_id})
    seg = seg[seg["pos"].abs() > 1e-9]
    trade_pnl = seg.groupby("tid")["ret"].apply(lambda r: float((1.0 + r).prod() - 1.0))
    n_trades = int(trade_pnl.shape[0])
    win_rate = float((trade_pnl > 0).mean()) if n_trades else 0.0

    exposure = float((position.abs() > 1e-9).mean()) if n else 0.0

    return {
        "sharpe": round(sharpe, 4),
        "cagr": None if np.isnan(cagr) else round(cagr, 4),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_dd, 4),
        "win_rate": round(win_rate, 4),
        "n_trades": n_trades,
        "exposure": round(exposure, 4),
        "periods": n,
        "equity_final": round(float(equity.iloc[-1]), 4) if n else 1.0,
    }
