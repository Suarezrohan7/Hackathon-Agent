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

PARAMS = {'a': 8, 'b': 20, 'c': 14, 'd': 50, 'e': 24}
PARAM_GRID = {'a': [3, 5, 8], 'b': [12, 20, 30, 45], 'c': [9, 14, 20], 'd': [50, 56, 62], 'e': [6, 12, 24]}
