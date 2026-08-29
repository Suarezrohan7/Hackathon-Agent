# Trajectory — `advanced/case-10-cost-killed`

_Rendered 2026-08-28T19:01:55+00:00_

**START** `advanced/case-10-cost-killed` @ 2026-08-28T19:00:41+00:00

- 💭 profile: {"n_params": 3, "param_names": ["period", "low", "high"], "param_grid_size": 12, "reported_is_sharpe": 0.4889, "reported_max_drawdown": -0.1976, "reported_n_trades": 318, "reported_exposure": 0.842, "static_future_reference_flags": []}

- 🧠 **model** (1157→352 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.4889, "oos_sharpe": 1.0687, "oos_over_is": 2.186, "oos_max_drawdown": -0.1519, "oos_total_return": 1.0007, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.489, "n_perm": 200, "null_sharpe_mean": 0.527, "null_sharpe_p95": 1.283, "p_value": 0.5323, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 12, "reported_sharpe": 0.489, "best_sharpe": 0.635, "median_sharpe": 0.431, "frac_positive": 1.0, "neighbour_mean_sharpe": 0.361, "plateau_score": 0.738, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.814, "wf_sharpe_refit_mean": 0.515, "fold_sharpes_fixed": [0.57, 0.48, 0.79, 0.42, 1.8], "regime_like": false, "folds": [{"test_sharpe_fixed": 0.5658, "test_sharpe_refit": -0.6539}, {"test_sharpe_fixed": 0.485, "test_sharpe_refit": -0.0478}, {"test_sharpe_fixed": 0.7936, "test_sharpe_refit": 1.3086}, {"test_sharpe_fixed": 0.4197, "test_sharpe_refit": 0.3913`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 0.4889, "1bps": 0.4002, "2bps": 0.3114, "5bps": 0.0447, "10bps": -0.3999}, "survives_5bps": false, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 318, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2543→472 tok): Summary of raw numbers gathered:

- **IS vs OOS**: IS Sharpe 0.489; OOS Sharpe 1.069 (OOS/IS ratio 2.19), OOS max drawdown -0.152, OOS total return 1.00.
- **Monte Carlo permutation**: observed Sharpe 0.489 vs null mean 0.527, null p95 1.283, p-value 0.532.
- **Parameter sensitivity** (grid of 12): reported Sharpe 0.489, best 0.635, median 0.431, neighbour-mean 0.361, plateau_score 0.738 (flagged "fragile: false" but reading text says lone spike, not plateau).
- **Walk-forward** (5 folds): fixed-param mean Sharpe 0.814 (fold range 0.42–1.80); refit mean Sharpe 0.515 (fold range -0.65 to 1.58),… (+353 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2230→908 tok): [{"id": "robust_oos", "evidence": "oos_test: oos_sharpe=1.0687 >= 0.45 and oos_over_is=2.186 >= 0.6"}, {"id": "transaction_cost_sensitivity", "evidence": "cost_stress: survives_5bps=false, sharpe drops from 0.489 (0bps) to 0.045 (5bps) and -0.400 (10bps)"}, {"id": "regime_dependence", "evidence": "walk_forward refit fold sharpes swing from -0.6539 and -0.0478 to 1.3086 and 1.5752 across 5 folds"}]

- 💭 digest: {"reported_is_sharpe": 0.4889, "oos_sharpe": 1.0687, "oos_over_is": 2.186, "mc_p_value": 0.5323, "walk_forward_fixed_mean": 0.814, "walk_forward_regime_like": false, "walk_forward_folds": [0.57, 0.48, 0.79, 0.42, 1.8], "param_plateau_score": 0.738, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": false, "n_trades": 318, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> no_edge: gross signal does not survive 5bps costs (oos_sharpe 1.07 gross)

- 🧠 **model** (871→778 tok): {"rationale": "The strategy's edge evaporates once realistic frictions are applied: gross Sharpe falls from 0.489 (0bps) to a near-zero 0.045 at 5bps and turns negative (-0.400) at 10bps, meaning the reported 1.07 OOS Sharpe is a pre-cost artifact that cannot support live risk-taking. The weak Monte Carlo permutation p-value (0.532) reinforces that the raw signal is not statistically distinguishable from noise once you account for the cost sensitivity, so capital should not be committed despite the seemingly strong oos_over_is ratio of 2.186."}


**FINISH** in 74.17s — result: `{"verdict": "no_edge", "rationale": "The strategy's edge evaporates once realistic frictions are applied: gross Sharpe falls from 0.489 (0bps) to a near-zero 0.045 at 5bps and turns negative (-0.400) at 10bps, meaning the reported 1.07 OOS Sharpe is a pre-cost artifact that cannot support live risk-taking. The weak Monte Carlo permutation p-value (0.532) reinforces that the raw signal is not statistically distinguishable from noise once you account for the cost sensitivity, so capital should not be committed despite the seemingly strong oos_over_is ratio of 2.186.", "findings": [{"id": "regime`
