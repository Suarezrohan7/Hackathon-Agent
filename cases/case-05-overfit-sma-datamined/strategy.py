import numpy as np

def signal(df, fast=10, slow=50):
    f = df["close"].rolling(int(fast)).mean()
    s = df["close"].rolling(int(slow)).mean()
    return np.sign(f - s).fillna(0.0)

PARAMS = {'fast': 8, 'slow': 70}
PARAM_GRID = {'fast': [3, 5, 8, 10, 13, 18, 25, 32], 'slow': [25, 35, 50, 70, 95, 130, 175]}
