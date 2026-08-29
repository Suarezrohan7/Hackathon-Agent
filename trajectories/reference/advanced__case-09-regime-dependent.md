# Trajectory — `advanced/case-09-regime-dependent`

_Rendered 2026-08-28T19:00:41+00:00_

**START** `advanced/case-09-regime-dependent` @ 2026-08-28T19:00:09+00:00

- 💭 profile: {"n_params": 1, "param_names": ["lookback"], "param_grid_size": 3, "reported_is_sharpe": 0.8996, "reported_max_drawdown": -0.1525, "reported_n_trades": 81, "reported_exposure": 0.979, "static_future_reference_flags": []}

- 🧠 **model** (1149→417 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.8996, "oos_sharpe": -0.5774, "oos_over_is": -0.642, "oos_max_drawdown": -0.4523, "oos_total_return": -0.3122, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.9, "n_perm": 200, "null_sharpe_mean": 0.85, "null_sharpe_p95": 1.863, "p_value": 0.4677, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 3, "reported_sharpe": 0.9, "best_sharpe": 1.203, "median_sharpe": 1.02, "frac_positive": 1.0, "neighbour_mean_sharpe": 1.112, "plateau_score": 1.236, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.021, "wf_sharpe_refit_mean": -0.265, "fold_sharpes_fixed": [1.67, -0.01, 0.44, -0.69, -1.3], "regime_like": true, "folds": [{"test_sharpe_fixed": 1.6706, "test_sharpe_refit": 1.755}, {"test_sharpe_fixed": -0.0113, "test_sharpe_refit": -0.0981}, {"test_sharpe_fixed": 0.4372, "test_sharpe_refit": -0.0981}, {"test_sharpe_fixed": -0.6901, "test_sharpe_refit": -`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 0.8996, "1bps": 0.8717, "2bps": 0.8437, "5bps": 0.7597, "10bps": 0.6194}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 81, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2599→491 tok): Summary of raw results:

- **In-sample:** Sharpe 0.90, max drawdown -15.25%, 81 trades, exposure 97.9%.
- **OOS test:** Sharpe drops to -0.58 (OOS/IS ratio -0.64), OOS max drawdown -45.2%, OOS total return -31.2%.
- **Monte Carlo permutation:** observed Sharpe 0.90 vs null mean 0.85, null p95 1.86 → p-value 0.47 (not distinguishable from random).
- **Param sensitivity:** grid of 3, reported Sharpe 0.90 vs neighbour mean 1.11, best 1.20, plateau_score 1.24 (flagged "fragile: false" but reported point is below neighbours/median, i.e. not the best of the grid).
- **Walk-forward (5 folds):** fixed… (+405 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2250→158 tok): [{"id":"oos_collapse","evidence":"oos_test: oos_over_is = -0.642 (is_sharpe 0.8996 -> oos_sharpe -0.5774), far below 0.4 threshold"},{"id":"regime_dependence","evidence":"walk_forward fold_sharpes_fixed = [1.67, -0.01, 0.44, -0.69, -1.3], swinging from strongly positive to negative; regime_like: true"}]

- 💭 digest: {"reported_is_sharpe": 0.8996, "oos_sharpe": -0.5774, "oos_over_is": -0.642, "mc_p_value": 0.4677, "walk_forward_fixed_mean": 0.021, "walk_forward_regime_like": true, "walk_forward_folds": [1.67, -0.01, 0.44, -0.69, -1.3], "param_plateau_score": 1.236, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 81, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> no_edge: in-sample Sharpe 0.90 did not repeat out of sample (-0.58); parameters are not fragile, so this reads as luck / regime, not curve-fitting

- 🧠 **model** (837→321 tok): ```json
{"rationale": "In-sample Sharpe of 0.90 flipped to -0.58 out of sample (oos_over_is -0.642), and walk-forward folds swing wildly (1.67, -0.01, 0.44, -0.69, -1.30) with a near-zero mean (0.021), consistent with regime-dependence rather than a stable edge. Since param_fragile is false (plateau score 1.236), the failure isn't overfitting to fragile parameters — it looks like the in-sample performance was luck or a favorable regime that didn't persist, supporting NO_EDGE and arguing against risking capital here.", "dissent": "mc_p_value of 0.4677 is unremarkable but not damning on its own;… (+223 chars)

- 💭 LLM dissent (not acted on): mc_p_value of 0.4677 is unremarkable but not damning on its own; more notably, cost_survives_5bps is true, meaning the (failed) OOS result is not even an artifact of transaction costs — this reinforces NO_EDGE rather than contradicting it, so no real dissent exists in this digest.


**FINISH** in 32.01s — result: `{"verdict": "no_edge", "rationale": "In-sample Sharpe of 0.90 flipped to -0.58 out of sample (oos_over_is -0.642), and walk-forward folds swing wildly (1.67, -0.01, 0.44, -0.69, -1.30) with a near-zero mean (0.021), consistent with regime-dependence rather than a stable edge. Since param_fragile is false (plateau score 1.236), the failure isn't overfitting to fragile parameters \u2014 it looks like the in-sample performance was luck or a favorable regime that didn't persist, supporting NO_EDGE and arguing against risking capital here.", "findings": [{"id": "oos_collapse", "evidence": "oos_test`
