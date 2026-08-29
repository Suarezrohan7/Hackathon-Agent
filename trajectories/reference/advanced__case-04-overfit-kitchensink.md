# Trajectory — `advanced/case-04-overfit-kitchensink`

_Rendered 2026-08-28T18:57:00+00:00_

**START** `advanced/case-04-overfit-kitchensink` @ 2026-08-28T18:55:47+00:00

- 💭 profile: {"n_params": 5, "param_names": ["a", "b", "c", "d", "e"], "param_grid_size": 432, "reported_is_sharpe": 1.79, "reported_max_drawdown": -0.044, "reported_n_trades": 108, "reported_exposure": 0.724, "static_future_reference_flags": []}

- 🧠 **model** (1165→504 tok): [7 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 1.79, "oos_sharpe": -0.5765, "oos_over_is": -0.322, "oos_max_drawdown": -0.1075, "oos_total_return": -0.0835, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 1.79, "n_perm": 200, "null_sharpe_mean": 0.685, "null_sharpe_p95": 1.748, "p_value": 0.0547, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 432, "reported_sharpe": 1.79, "best_sharpe": 1.79, "median_sharpe": -0.005, "frac_positive": 0.498, "neighbour_mean_sharpe": 1.02, "plateau_score": 0.57, "fragile": true, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.272, "wf_sharpe_refit_mean": 0.092, "fold_sharpes_fixed": [2.31, 0.99, -0.49, 0.24, -1.7], "regime_like": true, "folds": [{"test_sharpe_fixed": 2.3125, "test_sharpe_refit": 1.8577}, {"test_sharpe_fixed": 0.9921, "test_sharpe_refit": 0.6865}, {"test_sharpe_fixed": -0.4872, "test_sharpe_refit": -0.4872}, {"test_sharpe_fixed": 0.2406, "test_sharpe_refit": -0.2`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 1.79, "1bps": 1.7355, "2bps": 1.6808, "5bps": 1.5165, "10bps": 1.2415}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 108, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🔧 **call** `lookahead_probe` — `{}`

- ✅ **result** `lookahead_probe` — `{"static_flags": [], "sharpe_lag1": 1.79, "sharpe_lag2": 1.7885, "sharpe_lag3": 0.8365, "win_rate_lag1": 0.5463, "suspected": false, "reading": "A static future-reference flag, or an implausible Sharpe/win-rate, means the backtest is a bug not an edge."}`

- 🧠 **model** (2855→615 tok): Summary of raw evidence gathered:

- **In-sample vs OOS:** IS Sharpe 1.79 → OOS Sharpe -0.577 (OOS/IS ratio -0.32). OOS max drawdown -10.75% (vs IS -4.4%), OOS total return -8.35%. Result did not generalize.

- **Monte Carlo permutation:** Observed Sharpe 1.79 vs null mean 0.685, null p95 1.748. p-value = 0.055 (borderline, close to the noise ceiling).

- **Parameter sensitivity:** Grid of 432 combos, best Sharpe = reported Sharpe (1.79), but median Sharpe across grid ≈ -0.005, only 49.8% of combos positive. Neighbour-mean Sharpe 1.02, plateau_score 0.57 → flagged "fragile" (lone spike, not a … (+687 chars)

- 💭 verify findings against raw numbers

- 🧠 **model** (2373→194 tok): {"id": "oos_collapse", "evidence": "oos_test: is_sharpe 1.79 -> oos_sharpe -0.5765, oos_over_is -0.322"}
{"id": "param_fragility", "evidence": "param_sensitivity: plateau_score 0.57, fragile true, median_sharpe -0.005, frac_positive 0.498"}
{"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed [2.31, 0.99, -0.49, 0.24, -1.70], regime_like true"}

- 💭 dropped 5 finding(s) not in the allowed set

- 💭 digest: {"reported_is_sharpe": 1.79, "oos_sharpe": -0.5765, "oos_over_is": -0.322, "mc_p_value": 0.0547, "walk_forward_fixed_mean": 0.272, "walk_forward_regime_like": true, "walk_forward_folds": [2.31, 0.99, -0.49, 0.24, -1.7], "param_plateau_score": 0.57, "param_fragile": true, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 108, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> overfit: in-sample Sharpe 1.79 collapsed to -0.58 out of sample; parameters are a fragile spike

- 🧠 **model** (755→393 tok): {"rationale": "The in-sample Sharpe of 1.79 completely inverts out of sample to -0.5765 (ratio -0.322), and the walk-forward folds swing wildly (2.31, 0.99, -0.49, 0.24, -1.7), showing the edge is not stable across time regimes. Combined with a fragile parameter surface (plateau score 0.57, flagged fragile) and a Monte Carlo permutation p-value of 0.0547 that fails to clear significance, the evidence points to a spurious, regime-specific fit rather than a durable edge, despite passing cost stress and having a reasonable 108-trade sample."}


**FINISH** in 73.02s — result: `{"verdict": "overfit", "rationale": "The in-sample Sharpe of 1.79 completely inverts out of sample to -0.5765 (ratio -0.322), and the walk-forward folds swing wildly (2.31, 0.99, -0.49, 0.24, -1.7), showing the edge is not stable across time regimes. Combined with a fragile parameter surface (plateau score 0.57, flagged fragile) and a Monte Carlo permutation p-value of 0.0547 that fails to clear significance, the evidence points to a spurious, regime-specific fit rather than a durable edge, despite passing cost stress and having a reasonable 108-trade sample.", "findings": [{"id": "oos_collaps`
