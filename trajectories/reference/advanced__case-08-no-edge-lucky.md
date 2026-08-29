# Trajectory — `advanced/case-08-no-edge-lucky`

_Rendered 2026-08-28T19:00:09+00:00_

**START** `advanced/case-08-no-edge-lucky` @ 2026-08-28T18:59:21+00:00

- 💭 profile: {"n_params": 3, "param_names": ["period", "low", "high"], "param_grid_size": 12, "reported_is_sharpe": 0.7165, "reported_max_drawdown": -0.0995, "reported_n_trades": 66, "reported_exposure": 0.205, "static_future_reference_flags": []}

- 🧠 **model** (1157→325 tok): [5 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.7165, "oos_sharpe": -0.0618, "oos_over_is": -0.086, "oos_max_drawdown": -0.1529, "oos_total_return": -0.0359, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.717, "n_perm": 200, "null_sharpe_mean": 0.47, "null_sharpe_p95": 1.194, "p_value": 0.3035, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 12, "reported_sharpe": 0.717, "best_sharpe": 0.979, "median_sharpe": 0.62, "frac_positive": 1.0, "neighbour_mean_sharpe": 0.654, "plateau_score": 0.912, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.365, "wf_sharpe_refit_mean": 0.386, "fold_sharpes_fixed": [2.12, -0.06, -0.6, 0.48, -0.12], "regime_like": true, "folds": [{"test_sharpe_fixed": 2.1217, "test_sharpe_refit": 1.2791}, {"test_sharpe_fixed": -0.0604, "test_sharpe_refit": 0.9903}, {"test_sharpe_fixed": -0.5994, "test_sharpe_refit": -0.2606}, {"test_sharpe_fixed": 0.4837, "test_sharpe_refit": -0`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 66, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2380→500 tok): Summary of raw results:

- **In-sample vs OOS:** IS Sharpe 0.7165 → OOS Sharpe -0.0618 (OOS/IS ratio -0.086). OOS max drawdown -0.1529, OOS total return -0.0359. Performance did not carry into the out-of-sample period.

- **Monte Carlo permutation:** Observed Sharpe 0.717 vs null mean 0.47 (p95 = 1.194), p-value = 0.3035 — the observed Sharpe is well within the range produced by randomly permuted data.

- **Parameter sensitivity:** Grid of 12 combos, reported Sharpe 0.717 vs best 0.979, median 0.62. Neighbour mean Sharpe 0.654, plateau score 0.912 (flagged "fragile": lone spike rather than a s… (+483 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 🔁 **retry** — safety net: required check 'cost_stress' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2262→495 tok): [{"id": "oos_collapse", "evidence": "oos_test: is_sharpe 0.7165 -> oos_sharpe -0.0618, oos_over_is -0.086 (<<0.4), oos_total_return -0.0359"}, {"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed [2.12, -0.06, -0.60, 0.48, -0.12], regime_like true, wf_sharpe_fixed_mean 0.365"}]

- 💭 digest: {"reported_is_sharpe": 0.7165, "oos_sharpe": -0.0618, "oos_over_is": -0.086, "mc_p_value": 0.3035, "walk_forward_fixed_mean": 0.365, "walk_forward_regime_like": true, "walk_forward_folds": [2.12, -0.06, -0.6, 0.48, -0.12], "param_plateau_score": 0.912, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 66, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> no_edge: in-sample Sharpe 0.72 did not repeat out of sample (-0.06); parameters are not fragile, so this reads as luck / regime, not curve-fitting

- 🧠 **model** (848→596 tok): {"rationale": "The strategy's in-sample Sharpe of 0.72 evaporated out of sample to -0.06 (oos_over_is -0.086, far below the 0.4 threshold), and it lost -3.59% out of sample, indicating no real edge survived. Walk-forward folds are highly erratic (2.12, -0.06, -0.60, 0.48, -0.12, mean 0.365) with regime_like=true, and param_plateau_score 0.912 (fragile=false) confirms this isn't a fragile/overfit parameter set but rather noise or regime luck—so risking capital on this is not advised despite passing cost and lookahead checks."}


**FINISH** in 47.5s — result: `{"verdict": "no_edge", "rationale": "The strategy's in-sample Sharpe of 0.72 evaporated out of sample to -0.06 (oos_over_is -0.086, far below the 0.4 threshold), and it lost -3.59% out of sample, indicating no real edge survived. Walk-forward folds are highly erratic (2.12, -0.06, -0.60, 0.48, -0.12, mean 0.365) with regime_like=true, and param_plateau_score 0.912 (fragile=false) confirms this isn't a fragile/overfit parameter set but rather noise or regime luck\u2014so risking capital on this is not advised despite passing cost and lookahead checks.", "findings": [{"id": "oos_collapse", "evid`
