# Trajectory — `advanced/case-07-no-edge-random`

_Rendered 2026-08-28T18:59:21+00:00_

**START** `advanced/case-07-no-edge-random` @ 2026-08-28T18:58:48+00:00

- 💭 profile: {"n_params": 1, "param_names": ["lookback"], "param_grid_size": 4, "reported_is_sharpe": 0.2955, "reported_max_drawdown": -0.3104, "reported_n_trades": 29, "reported_exposure": 0.979, "static_future_reference_flags": []}

- 🧠 **model** (1149→369 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 0.2955, "oos_sharpe": 0.1511, "oos_over_is": 0.511, "oos_max_drawdown": -0.3088, "oos_total_return": 0.0464, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 0.295, "n_perm": 200, "null_sharpe_mean": -0.105, "null_sharpe_p95": 0.694, "p_value": 0.1891, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 29, "adequate": false, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 4, "reported_sharpe": 0.295, "best_sharpe": 0.295, "median_sharpe": 0.107, "frac_positive": 0.5, "neighbour_mean_sharpe": 0.081, "plateau_score": 0.274, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.06, "wf_sharpe_refit_mean": 0.239, "fold_sharpes_fixed": [-0.47, 0.39, 1.33, 0.07, -1.02], "regime_like": true, "folds": [{"test_sharpe_fixed": -0.4684, "test_sharpe_refit": -0.4684}, {"test_sharpe_fixed": 0.3895, "test_sharpe_refit": 0.3895}, {"test_sharpe_fixed": 1.3322, "test_sharpe_refit": 1.3322}, {"test_sharpe_fixed": 0.068, "test_sharpe_refit": 1.122`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 0.2955, "1bps": 0.2865, "2bps": 0.2775, "5bps": 0.2504, "10bps": 0.2053}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🧠 **model** (2554→506 tok): Summary of raw findings:

- **In-sample vs OOS:** IS Sharpe 0.2955 → OOS Sharpe 0.1511 (51% retention), OOS max drawdown -0.3088, OOS total return only 4.64%.
- **Monte Carlo permutation:** observed Sharpe 0.295 vs null mean -0.105, null p95 0.694; p-value = 0.189 (not significant at conventional thresholds).
- **Trade count:** only 29 trades, flagged as inadequate (<30) for statistical significance.
- **Parameter sensitivity:** grid size 4; reported/best Sharpe 0.295 but median across grid only 0.107, neighbour mean 0.081, plateau_score 0.274 → flagged as a lone spike rather than a stable pla… (+507 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2266→659 tok): [
  {"id": "param_fragility", "evidence": "param_sensitivity: plateau_score=0.274 (well below 0.6), median_sharpe=0.107 vs best_sharpe=0.295, neighbour_mean_sharpe=0.081, and lookahead_probe.suspected=false"},
  {"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed=[-0.47, 0.39, 1.33, 0.07, -1.02], regime_like=true, wf_sharpe_fixed_mean=0.06"},
  {"id": "insufficient_trades", "evidence": "trade_count: n_trades=29, adequate=false"}
]

- 💭 digest: {"reported_is_sharpe": 0.2955, "oos_sharpe": 0.1511, "oos_over_is": 0.511, "mc_p_value": 0.1891, "walk_forward_fixed_mean": 0.06, "walk_forward_regime_like": true, "walk_forward_folds": [-0.47, 0.39, 1.33, 0.07, -1.02], "param_plateau_score": 0.274, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 29, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> no_edge: no out-of-sample edge (oos_sharpe 0.15)

- 🧠 **model** (881→506 tok): {"rationale": "The strategy fails the out-of-sample test outright: oos_sharpe of 0.15 is only 51% of the in-sample 0.30 (oos_over_is=0.511), the Monte Carlo permutation p-value of 0.189 is not significant, and walk-forward folds swing wildly (-0.47 to 1.33, mean 0.06) with regime_like=true, indicating the edge is not stable across time. Compounding this, param_plateau_score of 0.274 shows the result is fragile to parameter choice and n_trades=29 is too few to draw reliable conclusions, so there is no basis to risk capital on this strategy as configured.", "dissent": "cost_survives_5bps=true is… (+105 chars)

- 💭 LLM dissent (not acted on): cost_survives_5bps=true is the one point in its favor, but it doesn't offset the weak, inconsistent oos/walk-forward performance.


**FINISH** in 33.25s — result: `{"verdict": "no_edge", "rationale": "The strategy fails the out-of-sample test outright: oos_sharpe of 0.15 is only 51% of the in-sample 0.30 (oos_over_is=0.511), the Monte Carlo permutation p-value of 0.189 is not significant, and walk-forward folds swing wildly (-0.47 to 1.33, mean 0.06) with regime_like=true, indicating the edge is not stable across time. Compounding this, param_plateau_score of 0.274 shows the result is fragile to parameter choice and n_trades=29 is too few to draw reliable conclusions, so there is no basis to risk capital on this strategy as configured.", "findings": [{"i`
