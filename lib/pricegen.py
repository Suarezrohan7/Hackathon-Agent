"""Synthetic price series with *known* statistical properties.

The whole eval rests on trustworthy ground truth, so each generator is explicit
about the edge (if any) it contains:

    random_walk       -> no edge. Any backtest profit on this is luck.
    momentum_series   -> real edge: returns have positive autocorrelation (AR(1)).
    mean_revert_series-> real edge: log-price is Ornstein-Uhlenbeck around a level.
    regime_series     -> trend for the first half, chop for the second: edge exists
                         but only in one regime.

All return a DataFrame indexed 0..n-1 with columns close/open/high/low.
Everything is seeded -> byte-reproducible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _ohlc_from_close(close: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    close = np.asarray(close, dtype=float)
    noise = np.abs(rng.normal(0, close * 0.001))
    high = close + noise
    low = close - noise
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


def random_walk(n: int, seed: int, mu: float = 0.0, sigma: float = 0.01, s0: float = 100.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(mu, sigma, n)
    close = s0 * np.exp(np.cumsum(r))
    return _ohlc_from_close(close, rng)


def momentum_series(n: int, seed: int, phi: float = 0.12, sigma: float = 0.01, s0: float = 100.0) -> pd.DataFrame:
    """AR(1) on returns: r[t] = phi*r[t-1] + eps  ->  genuine, exploitable momentum."""
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, sigma, n)
    r = np.zeros(n)
    for t in range(1, n):
        r[t] = phi * r[t - 1] + eps[t]
    close = s0 * np.exp(np.cumsum(r))
    return _ohlc_from_close(close, rng)


def mean_revert_series(n: int, seed: int, kappa: float = 0.05, sigma: float = 0.01,
                       level: float = np.log(100.0), s0: float = 100.0) -> pd.DataFrame:
    """OU on log-price -> genuine mean reversion."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = np.log(s0)
    for t in range(1, n):
        x[t] = x[t - 1] + kappa * (level - x[t - 1]) + rng.normal(0, sigma)
    return _ohlc_from_close(np.exp(x), rng)


def regime_series(n: int, seed: int, phi: float = 0.15, sigma: float = 0.01, s0: float = 100.0) -> pd.DataFrame:
    """First half: momentum (edge). Second half: random walk (no edge)."""
    half = n // 2
    a = momentum_series(half, seed, phi=phi, sigma=sigma, s0=s0)
    start = float(a["close"].iloc[-1])
    b = random_walk(n - half, seed + 1, sigma=sigma, s0=start)
    close = np.concatenate([a["close"].to_numpy(), b["close"].to_numpy()])
    return _ohlc_from_close(close, np.random.default_rng(seed + 2))
