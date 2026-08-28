import numpy as np

def signal(df, lookback=20):
    # break of the prior N-bar range (shift(1) -> no look-ahead)
    hh = df["high"].rolling(int(lookback)).max().shift(1)
    ll = df["low"].rolling(int(lookback)).min().shift(1)
    s = df["close"].mul(0.0)
    s[df["close"] > hh] = 1.0
    s[df["close"] < ll] = -1.0
    return s.replace(0.0, np.nan).ffill().fillna(0.0)

PARAMS = {'lookback': 35}
PARAM_GRID = {'lookback': [20, 35, 55]}
