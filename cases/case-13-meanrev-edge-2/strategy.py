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

PARAMS = {'period': 10, 'low': 30, 'high': 70}
PARAM_GRID = {'period': [7, 10, 14, 21], 'low': [20, 25, 30], 'high': [70, 75, 80]}
