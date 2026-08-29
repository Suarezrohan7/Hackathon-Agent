# Trajectory — `baseline/case-03-breakout-edge`

_Rendered 2026-08-28T18:53:07+00:00_

**START** `baseline/case-03-breakout-edge` @ 2026-08-28T18:52:57+00:00

- 💭 baseline: single model call — strategy source + in-sample report, no tools

- 🧠 **model** (596→871 tok): {"verdict": "overfit", "rationale": "The report only shows in-sample metrics despite an out-of-sample dataset (data_oos.csv) being referenced \u2013 no OOS performance is given, which is a major red flag suggesting the strategy failed or was never properly validated out-of-sample. The parameter was chosen via a grid search (lookback \u2208 {20,30,40,60}) and the selected value (40) sits in the middle of a small grid, indicating potential curve-fitting to the in-sample data. Additional warning signs include a very low win rate (28.6%) offset only by a few large winning trades, a modest Sharpe (… (+328 chars)


**FINISH** in 10.68s — result: `{"verdict": "overfit", "rationale": "The report only shows in-sample metrics despite an out-of-sample dataset (data_oos.csv) being referenced \u2013 no OOS performance is given, which is a major red flag suggesting the strategy failed or was never properly validated out-of-sample. The parameter was chosen via a grid search (lookback \u2208 {20,30,40,60}) and the selected value (40) sits in the middle of a small grid, indicating potential curve-fitting to the in-sample data. Additional warning signs include a very low win rate (28.6%) offset only by a few large winning trades, a modest Sharpe (`
