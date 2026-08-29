# Trajectory — `advanced/case-01-momentum-edge`

_Rendered 2026-08-28T18:54:55+00:00_

**START** `advanced/case-01-momentum-edge` @ 2026-08-28T18:54:33+00:00

- 💭 profile: {"n_params": 1, "param_names": ["lookback"], "param_grid_size": 5, "reported_is_sharpe": 1.2095, "reported_max_drawdown": -0.2125, "reported_n_trades": 77, "reported_exposure": 0.979, "static_future_reference_flags": []}

- 🧠 **model** (1149→289 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 1.2095, "oos_sharpe": 0.5003, "oos_over_is": 0.414, "oos_max_drawdown": -0.2099, "oos_total_return": 0.311, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 1.21, "n_perm": 200, "null_sharpe_mean": 1.043, "null_sharpe_p95": 2.093, "p_value": 0.3532, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 5, "reported_sharpe": 1.21, "best_sharpe": 3.124, "median_sharpe": 1.21, "frac_positive": 0.8, "neighbour_mean_sharpe": 0.718, "plateau_score": 0.593, "fragile": true, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.698, "wf_sharpe_refit_mean": 2.65, "fold_sharpes_fixed": [1.31, 1.05, 0.37, 0.91, -0.15], "regime_like": true, "folds": [{"test_sharpe_fixed": 1.3094, "test_sharpe_refit": 2.8124}, {"test_sharpe_fixed": 1.0452, "test_sharpe_refit": 4.65}, {"test_sharpe_fixed": 0.3694, "test_sharpe_refit": 2.0832}, {"test_sharpe_fixed": 0.9104, "test_sharpe_refit": 1.8998}, `

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 1.2095, "1bps": 1.1865, "2bps": 1.1635, "5bps": 1.0942, "10bps": 0.9782}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 77, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2471→572 tok): Summary of raw results:

- **In-sample vs OOS**: IS Sharpe 1.21 → OOS Sharpe 0.50 (ratio 0.41). OOS max drawdown -0.21, similar to IS. Substantial degradation out-of-sample.
- **Monte Carlo permutation**: observed Sharpe 1.21 vs null mean 1.04, null p95 2.09, p-value 0.353 — the observed result is well within the range produced by randomly permuted data.
- **Parameter sensitivity** (grid size 5, lookback): reported Sharpe 1.21, best in grid 3.12, neighbour mean 0.72, plateau_score 0.59 (fragile=true) — the chosen parameter looks like an isolated spike rather than part of a stable plateau.
- **… (+722 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2330→256 tok): [{"id": "oos_collapse", "evidence": "oos_test: oos_over_is = 0.414 (is_sharpe 1.2095 -> oos_sharpe 0.5003)"}, {"id": "param_fragility", "evidence": "param_sensitivity: plateau_score = 0.593, fragile=true, no lookahead flag (lookahead_probe.suspected=false)"}, {"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed = [1.31, 1.05, 0.37, 0.91, -0.15], regime_like=true"}, {"id": "significant_vs_null", "evidence": "monte_carlo_permutation: p_value = 0.3532 (>=0.10)"}]

- 💭 dropped 1 finding(s) not in the allowed set

- 💭 digest: {"reported_is_sharpe": 1.2095, "oos_sharpe": 0.5003, "oos_over_is": 0.414, "mc_p_value": 0.3532, "walk_forward_fixed_mean": 0.698, "walk_forward_regime_like": true, "walk_forward_folds": [1.31, 1.05, 0.37, 0.91, -0.15], "param_plateau_score": 0.593, "param_fragile": true, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 77, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> edge: holds out of sample net of costs: oos_sharpe 0.50

- 🧠 **model** (850→384 tok): {"rationale": "OOS Sharpe of 0.50 (vs 1.21 in-sample, oos_over_is=0.414) still clears the bar net of 5bps costs, but walk-forward folds range from 1.31 down to -0.15 with regime_like=true, and param_plateau_score=0.593 with fragile=true, indicating the edge is regime-dependent and sensitive to parameter choice rather than robust.", "dissent": "mc_p_value = 0.3532 is far above conventional significance thresholds (e.g., 0.05), meaning the observed OOS Sharpe of 0.50 is statistically indistinguishable from noise under permutation testing — this undercuts confidence in calling it a genuine EDGE."… (+1 chars)

- 💭 LLM dissent (not acted on): mc_p_value = 0.3532 is far above conventional significance thresholds (e.g., 0.05), meaning the observed OOS Sharpe of 0.50 is statistically indistinguishable from noise under permutation testing — this undercuts confidence in calling it a genuine EDGE.

- 🧑‍⚖️ **human checkpoint** — Verdict = edge. Advance this strategy to a paper-trading track before any live capital? → **pending human reviewer sign-off**


**FINISH** in 22.12s — result: `{"verdict": "edge", "rationale": "OOS Sharpe of 0.50 (vs 1.21 in-sample, oos_over_is=0.414) still clears the bar net of 5bps costs, but walk-forward folds range from 1.31 down to -0.15 with regime_like=true, and param_plateau_score=0.593 with fragile=true, indicating the edge is regime-dependent and sensitive to parameter choice rather than robust.", "findings": [{"id": "oos_collapse", "evidence": "oos_test: oos_over_is = 0.414 (is_sharpe 1.2095 -> oos_sharpe 0.5003)"}, {"id": "param_fragility", "evidence": "param_sensitivity: plateau_score = 0.593, fragile=true, no lookahead flag (lookahead_p`
