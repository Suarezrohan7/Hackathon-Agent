# Trajectory — `advanced/case-03-breakout-edge`

_Rendered 2026-08-28T18:55:47+00:00_

**START** `advanced/case-03-breakout-edge` @ 2026-08-28T18:55:23+00:00

- 💭 profile: {"n_params": 1, "param_names": ["lookback"], "param_grid_size": 4, "reported_is_sharpe": 0.7707, "reported_max_drawdown": -0.3944, "reported_n_trades": 56, "reported_exposure": 0.959, "static_future_reference_flags": []}

- 🧠 **model** (1149→336 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.7707, "oos_sharpe": 1.2558, "oos_over_is": 1.629, "oos_max_drawdown": -0.2995, "oos_total_return": 1.1687, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.771, "n_perm": 200, "null_sharpe_mean": 1.041, "null_sharpe_p95": 2.062, "p_value": 0.6716, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 56, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 0.7707, "1bps": 0.7545, "2bps": 0.7383, "5bps": 0.6898, "10bps": 0.6088}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 4, "reported_sharpe": 0.771, "best_sharpe": 1.321, "median_sharpe": 1.238, "frac_positive": 1.0, "neighbour_mean_sharpe": 1.274, "plateau_score": 1.653, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.694, "wf_sharpe_refit_mean": 0.721, "fold_sharpes_fixed": [0.03, 0.28, 3.05, -0.07, 0.17], "regime_like": false, "folds": [{"test_sharpe_fixed": 0.0272, "test_sharpe_refit": 1.0011}, {"test_sharpe_fixed": 0.2796, "test_sharpe_refit": 0.7759}, {"test_sharpe_fixed": 3.0515, "test_sharpe_refit": 2.1538}, {"test_sharpe_fixed": -0.0652, "test_sharpe_refit": 0.28`

- 🧠 **model** (2520→593 tok): Summary of raw results:

- **In-sample Sharpe:** 0.7707, max drawdown -0.3944, 56 trades, exposure 0.959.
- **OOS test:** OOS Sharpe 1.2558 (higher than IS, oos/is ratio 1.629), OOS drawdown -0.2995, OOS total return 1.1687.
- **Monte Carlo permutation:** observed Sharpe 0.771 vs null mean 1.041, null p95 2.062, p-value 0.6716 (IS Sharpe is within the range produced by random/permuted data).
- **Trade count:** 56 trades, flagged "adequate" by the tool's threshold (~30).
- **Cost stress:** Sharpe decays mildly with slippage: 0.7707 (0bps) → 0.7545 (1bps) → 0.7383 (2bps) → 0.6898 (5bps) → 0.6088… (+649 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2352→498 tok): [{"id": "regime_dependence", "evidence": "walk_forward fold_sharpes_fixed: [0.03, 0.28, 3.05, -0.07, 0.17] — swings from 3.05 (strongly positive) to -0.07 (negative) across folds"}, {"id": "robust_oos", "evidence": "oos_test: oos_sharpe=1.2558 (>=0.45) and oos_over_is=1.629 (>=0.6)"}]

- 💭 digest: {"reported_is_sharpe": 0.7707, "oos_sharpe": 1.2558, "oos_over_is": 1.629, "mc_p_value": 0.6716, "walk_forward_fixed_mean": 0.694, "walk_forward_regime_like": false, "walk_forward_folds": [0.03, 0.28, 3.05, -0.07, 0.17], "param_plateau_score": 1.653, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 56, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> edge: holds out of sample net of costs: oos_sharpe 1.26

- 🧠 **model** (800→503 tok): {"rationale": "The verdict rests on oos_sharpe=1.2558 clearing the 0.45 bar and oos_over_is=1.629 showing OOS outperforming IS, with costs surviving at 5bps and parameters not flagged fragile (param_fragile=false). However, the walk-forward fold Sharpes [0.03, 0.28, 3.05, -0.07, 0.17] show the entire edge is concentrated in one fold, and only 56 trades back the result, so capital risk should be sized accordingly.", "dissent": "mc_p_value=0.6716 is far above any reasonable significance threshold (e.g. 0.05-0.10), meaning the permutation test cannot distinguish this strategy's returns from rando… (+96 chars)

- 💭 LLM dissent (not acted on): mc_p_value=0.6716 is far above any reasonable significance threshold (e.g. 0.05-0.10), meaning the permutation test cannot distinguish this strategy's returns from random chance — this alone undercuts confidence in the 'edge' label despite the passing oos_sharpe.

- 🧑‍⚖️ **human checkpoint** — Verdict = edge. Advance this strategy to a paper-trading track before any live capital? → **pending human reviewer sign-off**


**FINISH** in 24.6s — result: `{"verdict": "edge", "rationale": "The verdict rests on oos_sharpe=1.2558 clearing the 0.45 bar and oos_over_is=1.629 showing OOS outperforming IS, with costs surviving at 5bps and parameters not flagged fragile (param_fragile=false). However, the walk-forward fold Sharpes [0.03, 0.28, 3.05, -0.07, 0.17] show the entire edge is concentrated in one fold, and only 56 trades back the result, so capital risk should be sized accordingly.", "findings": [{"id": "regime_dependence", "evidence": "walk_forward fold_sharpes_fixed: [0.03, 0.28, 3.05, -0.07, 0.17] \u2014 swings from 3.05 (strongly positive)`
