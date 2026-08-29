# Trajectory — `advanced/case-05-overfit-sma-datamined`

_Rendered 2026-08-28T18:57:38+00:00_

**START** `advanced/case-05-overfit-sma-datamined` @ 2026-08-28T18:57:00+00:00

- 💭 profile: {"n_params": 2, "param_names": ["fast", "slow"], "param_grid_size": 56, "reported_is_sharpe": 1.2355, "reported_max_drawdown": -0.1131, "reported_n_trades": 6, "reported_exposure": 0.8444, "static_future_reference_flags": []}

- 🧠 **model** (1155→395 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 1.2355, "oos_sharpe": -1.3747, "oos_over_is": -1.113, "oos_max_drawdown": -0.3869, "oos_total_return": -0.3752, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 1.236, "n_perm": 200, "null_sharpe_mean": 0.001, "null_sharpe_p95": 1.289, "p_value": 0.0746, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 56, "reported_sharpe": 1.236, "best_sharpe": 1.236, "median_sharpe": 0.405, "frac_positive": 0.732, "neighbour_mean_sharpe": 0.707, "plateau_score": 0.572, "fragile": true, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": -0.805, "wf_sharpe_refit_mean": -0.422, "fold_sharpes_fixed": [0.87, 1.18, -0.77, -2.54, -2.77], "regime_like": true, "folds": [{"test_sharpe_fixed": 0.8713, "test_sharpe_refit": 1.0026}, {"test_sharpe_fixed": 1.1814, "test_sharpe_refit": 0.2524}, {"test_sharpe_fixed": -0.7691, "test_sharpe_refit": -0.7691}, {"test_sharpe_fixed": -2.5393, "test_sharpe_refit":`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 1.2355, "1bps": 1.232, "2bps": 1.2285, "5bps": 1.218, "10bps": 1.2005}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 6, "adequate": false, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2584→538 tok): Summary of raw findings:

- **In-sample vs OOS:** IS Sharpe 1.2355 → OOS Sharpe -1.3747 (OOS/IS ratio -1.11). OOS max drawdown -38.7%, OOS total return -37.5%. Result does not generalize.
- **Monte Carlo permutation:** observed Sharpe 1.236 vs null mean 0.001, null p95 1.289; p-value = 0.0746 (borderline, close to threshold, not clearly distinguishable from random data).
- **Parameter sensitivity:** grid size 56, best Sharpe 1.236 (= reported, i.e., the reported params are the best in the grid), median grid Sharpe 0.405, neighbor mean Sharpe 0.707, plateau_score 0.572 (well below 1) → flagged … (+605 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2298→732 tok): [
  {"id": "oos_collapse", "evidence": "oos_test: is_sharpe=1.2355, oos_sharpe=-1.3747, oos_over_is=-1.113 (<0.4), oos_max_drawdown=-0.3869"},
  {"id": "param_fragility", "evidence": "param_sensitivity: plateau_score=0.572 (<0.6), fragile=true, lookahead_probe.suspected=false"},
  {"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed=[0.87,1.18,-0.77,-2.54,-2.77], regime_like=true, wf_sharpe_fixed_mean=-0.805"},
  {"id": "insufficient_trades", "evidence": "trade_count: n_trades=6, adequate=false"}
]

- 💭 digest: {"reported_is_sharpe": 1.2355, "oos_sharpe": -1.3747, "oos_over_is": -1.113, "mc_p_value": 0.0746, "walk_forward_fixed_mean": -0.805, "walk_forward_regime_like": true, "walk_forward_folds": [0.87, 1.18, -0.77, -2.54, -2.77], "param_plateau_score": 0.572, "param_fragile": true, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 6, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> overfit: in-sample Sharpe 1.24 collapsed to -1.37 out of sample; parameters are a fragile spike

- 🧠 **model** (951→949 tok): {"rationale": "The strategy's edge evaporates out of sample: IS Sharpe 1.24 flips to OOS Sharpe -1.37 (oos_over_is=-1.113, well below the 0.4 threshold), and walk-forward testing shows a similar decay pattern (fold Sharpes 0.87, 1.18, then -0.77, -2.54, -2.77; mean -0.805), indicating the fit doesn't generalize across regimes. Parameter sensitivity confirms this is a fragile spike rather than a robust edge (plateau_score=0.572, fragile=true), so risking capital on these parameters is unjustified.", "dissent": "n_trades=6 is extremely small, meaning the OOS Sharpe of -1.37 and the walk-forward … (+245 chars)

- 💭 LLM dissent (not acted on): n_trades=6 is extremely small, meaning the OOS Sharpe of -1.37 and the walk-forward fold Sharpes are each based on a handful of trades and carry enormous sampling noise — the 'collapse' could partly reflect small-sample variance rather than genuine overfitting, so confidence in the verdict's magnitude should be tempered.


**FINISH** in 37.62s — result: `{"verdict": "overfit", "rationale": "The strategy's edge evaporates out of sample: IS Sharpe 1.24 flips to OOS Sharpe -1.37 (oos_over_is=-1.113, well below the 0.4 threshold), and walk-forward testing shows a similar decay pattern (fold Sharpes 0.87, 1.18, then -0.77, -2.54, -2.77; mean -0.805), indicating the fit doesn't generalize across regimes. Parameter sensitivity confirms this is a fragile spike rather than a robust edge (plateau_score=0.572, fragile=true), so risking capital on these parameters is unjustified.", "findings": [{"id": "insufficient_trades", "evidence": "trade_count: n_tra`
