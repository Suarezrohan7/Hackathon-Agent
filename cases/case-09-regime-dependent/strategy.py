import numpy as np

def signal(df, lookback=20):
    return np.sign(df["close"].pct_change(int(lookback))).fillna(0.0)

PARAMS = {'lookback': 20}
PARAM_GRID = {'lookback': [10, 20, 40]}
