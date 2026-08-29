# Trajectory — `baseline/case-05-overfit-sma-datamined`

_Rendered 2026-08-28T18:53:29+00:00_

**START** `baseline/case-05-overfit-sma-datamined` @ 2026-08-28T18:53:21+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (736→589 tok): {"verdict": "overfit", "rationale": "The in-sample report shows only 6 trades over the test period, far too few to draw statistically meaningful conclusions about edge, and the Sharpe/CAGR figures are highly sensitive to this tiny sample. The strategy also selects parameters (fast=8, slow=70) from a large 56-combination grid, a classic setup for curve-fitting to a specific price series. Despite an OOS data file being referenced, no out-of-sample results are reported, so there's no evidence the strategy generalizes beyond the in-sample window. Combined with the small trade count and the wide pa… (+232 chars)


**FINISH** in 8.4s — result: `{"verdict": "overfit", "rationale": "The in-sample report shows only 6 trades over the test period, far too few to draw statistically meaningful conclusions about edge, and the Sharpe/CAGR figures are highly sensitive to this tiny sample. The strategy also selects parameters (fast=8, slow=70) from a large 56-combination grid, a classic setup for curve-fitting to a specific price series. Despite an OOS data file being referenced, no out-of-sample results are reported, so there's no evidence the strategy generalizes beyond the in-sample window. Combined with the small trade count and the wide pa`
