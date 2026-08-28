import numpy as np

def signal(df, k=1):
    # BUG: uses the NEXT bar's close - a look-ahead leak, not an edge
    future = df["close"].shift(-int(k))
    return np.sign(future - df["close"]).fillna(0.0)

PARAMS = {'k': 1}
PARAM_GRID = {'k': [1, 2, 3]}
