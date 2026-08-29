# Trajectory — `advanced/case-02-meanrev-edge`

_Rendered 2026-08-28T18:55:23+00:00_

**START** `advanced/case-02-meanrev-edge` @ 2026-08-28T18:54:55+00:00

- 💭 profile: {"n_params": 3, "param_names": ["period", "low", "high"], "param_grid_size": 27, "reported_is_sharpe": 0.9199, "reported_max_drawdown": -0.1586, "reported_n_trades": 62, "reported_exposure": 0.186, "static_future_reference_flags": []}

- 🧠 **model** (1157→343 tok): [5 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.9199, "oos_sharpe": 0.9799, "oos_over_is": 1.065, "oos_max_drawdown": -0.1153, "oos_total_return": 0.3091, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.92, "n_perm": 200, "null_sharpe_mean": 0.602, "null_sharpe_p95": 1.368, "p_value": 0.2935, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 27, "reported_sharpe": 0.92, "best_sharpe": 1.455, "median_sharpe": 0.847, "frac_positive": 0.963, "neighbour_mean_sharpe": 0.847, "plateau_score": 0.921, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 1.128, "wf_sharpe_refit_mean": 0.957, "fold_sharpes_fixed": [2.26, 0.3, 2.0, 0.19, 0.89], "regime_like": false, "folds": [{"test_sharpe_fixed": 2.2637, "test_sharpe_refit": 0.8699}, {"test_sharpe_fixed": 0.2987, "test_sharpe_refit": 0.937}, {"test_sharpe_fixed": 2.0027, "test_sharpe_refit": 2.1849}, {"test_sharpe_fixed": 0.1865, "test_sharpe_refit": -0.3979},`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 62, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2397→405 tok): **Summary of raw numbers gathered:**

- **IS vs OOS:** IS Sharpe 0.92, OOS Sharpe 0.98 (ratio 1.07), OOS max drawdown -0.115, OOS total return 0.31.
- **Monte Carlo permutation:** Observed Sharpe 0.92 vs null mean 0.60, null 95th pct 1.37; p-value = 0.29.
- **Parameter sensitivity (grid=27):** Reported Sharpe 0.92, best-in-grid 1.46, median 0.85, 96% of grid positive, neighbour-mean 0.85, plateau score 0.92.
- **Walk-forward (5 folds):** Fixed-param fold Sharpes = [2.26, 0.30, 2.00, 0.19, 0.89], mean 1.13; refit fold Sharpes = [0.87, 0.94, 2.18, -0.40, 1.19], mean 0.96. High variance across fo… (+184 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 🔁 **retry** — safety net: required check 'cost_stress' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2163→820 tok): [{"id": "regime_dependence", "evidence": "walk_forward fold_sharpes_fixed swing from 2.26, 2.00 down to 0.19, 0.30, and refit fold sharpes include -0.40 alongside 2.18 — strongly positive to near-zero/negative across folds despite regime_like flag being false"}, {"id": "robust_oos", "evidence": "oos_test: oos_sharpe=0.9799 (>=0.45) and oos_over_is=1.065 (>=0.6), oos_max_drawdown=-0.1153, oos_total_return=0.3091"}]

- 💭 digest: {"reported_is_sharpe": 0.9199, "oos_sharpe": 0.9799, "oos_over_is": 1.065, "mc_p_value": 0.2935, "walk_forward_fixed_mean": 1.128, "walk_forward_regime_like": false, "walk_forward_folds": [2.26, 0.3, 2.0, 0.19, 0.89], "param_plateau_score": 0.921, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 62, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> edge: holds out of sample net of costs: oos_sharpe 0.98

- 🧠 **model** (846→255 tok): {"rationale": "The strategy clears the OOS bar with oos_sharpe 0.98 (>=0.45) and oos_over_is 1.065 (>=0.6), and it holds up under 5bps cost stress and shows no lookahead flags, supporting an EDGE call. Parameter plateau score of 0.921 and non-fragile flag add some confidence in robustness.", "dissent": "walk_forward_folds show extreme dispersion (2.26, 2.00, 0.89 vs 0.19, 0.30), and mc_p_value of 0.2935 fails typical significance thresholds (>0.05-0.10), meaning the permutation test can't rule out the observed performance arising by chance despite the regime_like flag being false and n_trades … (+10 chars)

- 💭 LLM dissent (not acted on): walk_forward_folds show extreme dispersion (2.26, 2.00, 0.89 vs 0.19, 0.30), and mc_p_value of 0.2935 fails typical significance thresholds (>0.05-0.10), meaning the permutation test can't rule out the observed performance arising by chance despite the regime_like flag being false and n_trades only 62.

- 🧑‍⚖️ **human checkpoint** — Verdict = edge. Advance this strategy to a paper-trading track before any live capital? → **pending human reviewer sign-off**


**FINISH** in 27.85s — result: `{"verdict": "edge", "rationale": "The strategy clears the OOS bar with oos_sharpe 0.98 (>=0.45) and oos_over_is 1.065 (>=0.6), and it holds up under 5bps cost stress and shows no lookahead flags, supporting an EDGE call. Parameter plateau score of 0.921 and non-fragile flag add some confidence in robustness.", "findings": [{"id": "regime_dependence", "evidence": "walk_forward fold_sharpes_fixed swing from 2.26, 2.00 down to 0.19, 0.30, and refit fold sharpes include -0.40 alongside 2.18 \u2014 strongly positive to near-zero/negative across folds despite regime_like flag being false"}, {"id": "`
