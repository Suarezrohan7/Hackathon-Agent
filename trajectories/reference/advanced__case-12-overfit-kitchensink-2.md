# Trajectory — `advanced/case-12-overfit-kitchensink-2`

_Rendered 2026-08-28T19:05:54+00:00_

**START** `advanced/case-12-overfit-kitchensink-2` @ 2026-08-28T19:02:28+00:00

- 💭 profile: {"n_params": 5, "param_names": ["a", "b", "c", "d", "e"], "param_grid_size": 324, "reported_is_sharpe": 1.3869, "reported_max_drawdown": -0.0448, "reported_n_trades": 111, "reported_exposure": 0.964, "static_future_reference_flags": []}

- 🧠 **model** (1167→435 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 1.3869, "oos_sharpe": -0.7016, "oos_over_is": -0.506, "oos_max_drawdown": -0.1657, "oos_total_return": -0.0985, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 1.387, "n_perm": 200, "null_sharpe_mean": 0.096, "null_sharpe_p95": 1.246, "p_value": 0.0398, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 324, "reported_sharpe": 1.387, "best_sharpe": 1.387, "median_sharpe": -0.248, "frac_positive": 0.327, "neighbour_mean_sharpe": 0.718, "plateau_score": 0.517, "fragile": true, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 0.108, "wf_sharpe_refit_mean": -0.137, "fold_sharpes_fixed": [1.12, 0.88, -2.49, 0.38, 0.66], "regime_like": true, "folds": [{"test_sharpe_fixed": 1.1202, "test_sharpe_refit": 1.1202}, {"test_sharpe_fixed": 0.8789, "test_sharpe_refit": -0.0536}, {"test_sharpe_fixed": -2.491, "test_sharpe_refit": -2.491}, {"test_sharpe_fixed": 0.375, "test_sharpe_refit": 1.242`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 1.3869, "1bps": 1.3259, "2bps": 1.2649, "5bps": 1.0808, "10bps": 0.7718}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 111, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2635→537 tok): Summary of raw numbers gathered:

- **In-sample vs OOS:** IS Sharpe 1.387 vs OOS Sharpe -0.702 (OOS/IS ratio -0.51). OOS max drawdown -16.6%, OOS total return -9.85%.
- **Monte Carlo permutation:** observed Sharpe 1.387 vs null mean 0.096, null p95 1.246; p-value = 0.040 (only marginally below the 0.10 threshold used in the tool's own reading text, which flags non-significance at ≥0.10 — here it's just under that bar).
- **Parameter sensitivity (grid=324):** best Sharpe 1.387 (the reported one), median Sharpe across grid -0.248, only 32.7% of combos positive, neighbour-mean Sharpe 0.718, plate… (+506 chars)

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2294→185 tok): ```json
[
  {"id": "oos_collapse", "evidence": "oos_test: is_sharpe 1.3869 vs oos_sharpe -0.7016, oos_over_is -0.506"},
  {"id": "regime_dependence", "evidence": "walk_forward: fold_sharpes_fixed [1.12, 0.88, -2.49, 0.38, 0.66], regime_like true"},
  {"id": "significant_vs_null", "evidence": "monte_carlo_permutation: p_value 0.0398"}
]
```

- 💭 dropped 1 finding(s) not in the allowed set

- 💭 digest: {"reported_is_sharpe": 1.3869, "oos_sharpe": -0.7016, "oos_over_is": -0.506, "mc_p_value": 0.0398, "walk_forward_fixed_mean": 0.108, "walk_forward_regime_like": true, "walk_forward_folds": [1.12, 0.88, -2.49, 0.38, 0.66], "param_plateau_score": 0.517, "param_fragile": true, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 111, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> overfit: in-sample Sharpe 1.39 collapsed to -0.70 out of sample; parameters are a fragile spike

- 🧠 **model** (826→595 tok): {"rationale": "The strategy's Sharpe ratio collapsed from 1.39 in-sample to -0.70 out-of-sample (oos_over_is -0.506), and walk-forward testing shows extreme instability (fold Sharpes 1.12, 0.88, -2.49, 0.38, 0.66, mean 0.108), with a fragile parameter surface (plateau score 0.517, param_fragile=true) indicating the in-sample edge was a narrow overfit spike tied to a specific regime rather than a robust signal. Do not risk capital on this configuration without re-optimizing on a broader, regime-diverse sample.", "dissent": "mc_p_value 0.0398 is below the conventional 0.05 significance threshold… (+211 chars)

- 💭 LLM dissent (not acted on): mc_p_value 0.0398 is below the conventional 0.05 significance threshold, implying the in-sample returns are not fully explainable by random permutation — a data point in tension with a pure 'fragile spike' overfit narrative and worth flagging before fully dismissing the strategy.


**FINISH** in 206.33s — result: `{"verdict": "overfit", "rationale": "The strategy's Sharpe ratio collapsed from 1.39 in-sample to -0.70 out-of-sample (oos_over_is -0.506), and walk-forward testing shows extreme instability (fold Sharpes 1.12, 0.88, -2.49, 0.38, 0.66, mean 0.108), with a fragile parameter surface (plateau score 0.517, param_fragile=true) indicating the in-sample edge was a narrow overfit spike tied to a specific regime rather than a robust signal. Do not risk capital on this configuration without re-optimizing on a broader, regime-diverse sample.", "findings": [{"id": "oos_collapse", "evidence": "oos_test: is`
