"""Parameterised strategy templates. Each returns a signal Series in [-1, 1]
computed from data up to and including each bar (no look-ahead) — except
`lookahead_cheat`, which deliberately peeks and is used for the buggy case.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).rolling(period).mean()
    down = (-delta.clip(upper=0)).rolling(period).mean()
    rs = up / down.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def sma_cross(df: pd.DataFrame, fast: int = 10, slow: int = 50) -> pd.Series:
    f = df["close"].rolling(int(fast)).mean()
    s = df["close"].rolling(int(slow)).mean()
    return np.sign(f - s).fillna(0.0)


def rsi_reversion(df: pd.DataFrame, period: int = 14, low: float = 30, high: float = 70) -> pd.Series:
    r = _rsi(df["close"], int(period))
    sig = pd.Series(0.0, index=df.index)
    sig[r < low] = 1.0
    sig[r > high] = -1.0
    return sig


def donchian_breakout(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    hh = df["high"].rolling(int(lookback)).max()
    ll = df["low"].rolling(int(lookback)).min()
    sig = pd.Series(0.0, index=df.index)
    sig[df["close"] >= hh] = 1.0
    sig[df["close"] <= ll] = -1.0
    return sig.replace(0.0, np.nan).ffill().fillna(0.0)


def kitchen_sink(df: pd.DataFrame, a: int = 5, b: int = 20, c: int = 14,
                 d: float = 55, e: int = 10) -> pd.Series:
    """Many knobs, weak parts -> ideal for demonstrating curve-fitting."""
    m = np.sign(df["close"].rolling(int(a)).mean() - df["close"].rolling(int(b)).mean())
    r = _rsi(df["close"], int(c))
    rev = np.where(r > d, -1.0, np.where(r < (100 - d), 1.0, 0.0))
    mom = np.sign(df["close"].diff(int(e)))
    raw = (m.fillna(0) + pd.Series(rev, index=df.index) + mom.fillna(0)) / 3.0
    return raw.clip(-1, 1)


def lookahead_cheat(df: pd.DataFrame, k: int = 1) -> pd.Series:
    """BUG ON PURPOSE: uses the *next* bar's close. Looks amazing in-sample."""
    future = df["close"].shift(-int(k))
    return np.sign(future - df["close"]).fillna(0.0)


REGISTRY = {
    "sma_cross": sma_cross,
    "rsi_reversion": rsi_reversion,
    "donchian_breakout": donchian_breakout,
    "kitchen_sink": kitchen_sink,
    "lookahead_cheat": lookahead_cheat,
}
