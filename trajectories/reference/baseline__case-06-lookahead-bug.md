# Trajectory — `baseline/case-06-lookahead-bug`

_Rendered 2026-08-28T18:53:33+00:00_

**START** `baseline/case-06-lookahead-bug` @ 2026-08-28T18:53:29+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (617→268 tok): {"verdict": "overfit", "rationale": "The signal function explicitly uses df['close'].shift(-k), which pulls future price data into the current bar's signal - a textbook look-ahead bias. This mechanically produces impossible results: Sharpe of 21.9, 100% win rate, and zero max drawdown are not achievable by any real trading strategy, since they imply perfect foreknowledge of price direction. There is no out-of-sample validation reported despite an oos_data_file being referenced, and the perfect win rate confirms the backtest is simply measuring the leak rather than any genuine predictive signal… (+175 chars)


**FINISH** in 4.38s — result: `{"verdict": "overfit", "rationale": "The signal function explicitly uses df['close'].shift(-k), which pulls future price data into the current bar's signal - a textbook look-ahead bias. This mechanically produces impossible results: Sharpe of 21.9, 100% win rate, and zero max drawdown are not achievable by any real trading strategy, since they imply perfect foreknowledge of price direction. There is no out-of-sample validation reported despite an oos_data_file being referenced, and the perfect win rate confirms the backtest is simply measuring the leak rather than any genuine predictive signal`
