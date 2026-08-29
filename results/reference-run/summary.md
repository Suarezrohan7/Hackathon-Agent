# Eval run — 2026-08-28T19:06:43+00:00

## Headline

| Metric | Baseline | Advanced | Change |
|---|---|---|---|
| Primary (verdict_correct) | 0.3846 | 1.0 | +0.6154 |
| Precision | 0.2692 | 0.4872 | +0.218 |
| Recall | 0.5769 | 0.9231 | +0.3462 |
| F1 | 0.3436 | 0.6078 | +0.2642 |
| Avg runtime (s) | 9.1154 | 56.1354 | +47.02 |
| Avg human min/task | 30.0 | 5.0 | -25 |
| USD per case | 0.0115 | 0.0501 | +0.0386 |
| Errors | 0 | 0 | +0 |

## Per-case

| Case | Which | Primary | F1 | Runtime s | Error |
|---|---|---|---|---|---|
| case-01-momentum-edge | baseline | 0.0 | 0.0 | 11.48 |  |
| case-02-meanrev-edge | baseline | 0.0 | 0.0 | 10.82 |  |
| case-03-breakout-edge | baseline | 0.0 | 0.0 | 10.68 |  |
| case-04-overfit-kitchensink | baseline | 1.0 | 0.8 | 13.26 |  |
| case-05-overfit-sma-datamined | baseline | 1.0 | 0.8 | 8.41 |  |
| case-06-lookahead-bug | baseline | 1.0 | 0.667 | 4.39 |  |
| case-07-no-edge-random | baseline | 1.0 | 0.0 | 6.89 |  |
| case-08-no-edge-lucky | baseline | 0.0 | 0.5 | 3.52 |  |
| case-09-regime-dependent | baseline | 0.0 | 0.0 | 10.78 |  |
| case-10-cost-killed | baseline | 0.0 | 0.5 | 13.13 |  |
| case-11-thin-sample | baseline | 0.0 | 0.4 | 10.82 |  |
| case-12-overfit-kitchensink-2 | baseline | 1.0 | 0.8 | 4.35 |  |
| case-13-meanrev-edge-2 | baseline | 0.0 | 0.0 | 9.97 |  |
| case-01-momentum-edge | advanced | 1.0 | 0.0 | 22.12 |  |
| case-02-meanrev-edge | advanced | 1.0 | 0.667 | 27.85 |  |
| case-03-breakout-edge | advanced | 1.0 | 0.667 | 24.6 |  |
| case-04-overfit-kitchensink | advanced | 1.0 | 0.8 | 73.03 |  |
| case-05-overfit-sma-datamined | advanced | 1.0 | 0.667 | 37.62 |  |
| case-06-lookahead-bug | advanced | 1.0 | 0.667 | 70.06 |  |
| case-07-no-edge-random | advanced | 1.0 | 0.0 | 33.26 |  |
| case-08-no-edge-lucky | advanced | 1.0 | 0.667 | 47.52 |  |
| case-09-regime-dependent | advanced | 1.0 | 0.667 | 32.06 |  |
| case-10-cost-killed | advanced | 1.0 | 0.5 | 74.18 |  |
| case-11-thin-sample | advanced | 1.0 | 0.8 | 32.65 |  |
| case-12-overfit-kitchensink-2 | advanced | 1.0 | 0.8 | 206.33 |  |
| case-13-meanrev-edge-2 | advanced | 1.0 | 1.0 | 48.48 |  |