# Trajectory — `baseline/case-13-meanrev-edge-2`

_Rendered 2026-08-28T18:54:33+00:00_

**START** `baseline/case-13-meanrev-edge-2` @ 2026-08-28T18:54:23+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (841→377 tok): {"verdict": "overfit", "rationale": "The report only presents in-sample results despite an out-of-sample dataset (data_oos.csv) being available and referenced in the config, meaning the strategy's robustness was never actually validated. This is a classic RSI mean-reversion setup tuned over a 36-combination grid (period x low x high), which combined with an in-sample Sharpe of 1.92 and unusually high 75% win rate is a strong signature of parameter overfitting to historical noise. The trade count (88) over what is likely a multi-year sample also implies fairly infrequent signals, adding uncerta… (+465 chars)


**FINISH** in 9.96s — result: `{"verdict": "overfit", "rationale": "The report only presents in-sample results despite an out-of-sample dataset (data_oos.csv) being available and referenced in the config, meaning the strategy's robustness was never actually validated. This is a classic RSI mean-reversion setup tuned over a 36-combination grid (period x low x high), which combined with an in-sample Sharpe of 1.92 and unusually high 75% win rate is a strong signature of parameter overfitting to historical noise. The trade count (88) over what is likely a multi-year sample also implies fairly infrequent signals, adding uncerta`
