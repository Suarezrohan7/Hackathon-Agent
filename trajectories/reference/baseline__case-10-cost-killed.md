# Trajectory — `baseline/case-10-cost-killed`

_Rendered 2026-08-28T18:54:08+00:00_

**START** `baseline/case-10-cost-killed` @ 2026-08-28T18:53:55+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (821→1077 tok): {"verdict": "overfit", "rationale": "The chosen parameters (period=3, low=48, high=52) sit right on top of the neutral RSI value of 50, meaning the 'signal' is essentially reacting to tiny, noisy fluctuations rather than any meaningful momentum/mean-reversion regime. This produces very frequent trading (318 trades, 84% exposure) for a mediocre in-sample Sharpe of 0.49, consistent with fitting noise rather than a genuine edge. The param grid is narrow and centered on these same near-50 thresholds, suggesting the 'optimal' combo was cherry-picked from a small search space rather than validated. … (+501 chars)


**FINISH** in 13.12s — result: `{"verdict": "overfit", "rationale": "The chosen parameters (period=3, low=48, high=52) sit right on top of the neutral RSI value of 50, meaning the 'signal' is essentially reacting to tiny, noisy fluctuations rather than any meaningful momentum/mean-reversion regime. This produces very frequent trading (318 trades, 84% exposure) for a mediocre in-sample Sharpe of 0.49, consistent with fitting noise rather than a genuine edge. The param grid is narrow and centered on these same near-50 thresholds, suggesting the 'optimal' combo was cherry-picked from a small search space rather than validated. `
