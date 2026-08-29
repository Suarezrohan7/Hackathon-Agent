# Trajectory — `baseline/case-09-regime-dependent`

_Rendered 2026-08-28T18:53:55+00:00_

**START** `baseline/case-09-regime-dependent` @ 2026-08-28T18:53:44+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (589→840 tok): {"verdict": "overfit", "rationale": "Only in-sample metrics are reported even though an out-of-sample data file (data_oos.csv) exists, meaning the strategy's performance has not been validated outside the fitting period. The parameter grid (10/20/40) shows the lookback was tuned, and no sensitivity analysis or OOS Sharpe is provided to confirm the choice of 20 is robust. With only 81 trades and a low 27% win rate, the strategy's edge relies on a few large winners, making it fragile to regime shifts and parameter choice. Absent OOS confirmation, the reported in-sample Sharpe (0.90) is likely in… (+122 chars)


**FINISH** in 10.77s — result: `{"verdict": "overfit", "rationale": "Only in-sample metrics are reported even though an out-of-sample data file (data_oos.csv) exists, meaning the strategy's performance has not been validated outside the fitting period. The parameter grid (10/20/40) shows the lookback was tuned, and no sensitivity analysis or OOS Sharpe is provided to confirm the choice of 20 is robust. With only 81 trades and a low 27% win rate, the strategy's edge relies on a few large winners, making it fragile to regime shifts and parameter choice. Absent OOS confirmation, the reported in-sample Sharpe (0.90) is likely in`
