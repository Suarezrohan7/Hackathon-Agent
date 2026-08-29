# Trajectory — `advanced/case-06-lookahead-bug`

_Rendered 2026-08-28T18:58:48+00:00_

**START** `advanced/case-06-lookahead-bug` @ 2026-08-28T18:57:38+00:00

- 💭 profile: {"n_params": 1, "param_names": ["k"], "param_grid_size": 3, "reported_is_sharpe": 21.902, "reported_max_drawdown": 0.0, "reported_n_trades": 467, "reported_exposure": 0.999, "static_future_reference_flags": ["shift\\(\\s*-"]}

- 🧠 **model** (1163→337 tok): [7 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 21.902, "oos_sharpe": 21.1023, "oos_over_is": 0.963, "oos_max_drawdown": 0.0, "oos_total_return": 2239.2803, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 21.902, "n_perm": 200, "null_sharpe_mean": 21.807, "null_sharpe_p95": 22.618, "p_value": 0.4328, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `lookahead_probe` — `{}`

- ✅ **result** `lookahead_probe` — `{"static_flags": ["shift\\(\\s*-"], "sharpe_lag1": 21.902, "sharpe_lag2": 1.523, "sharpe_lag3": 0.6961, "win_rate_lag1": 1.0, "suspected": true, "reading": "A static future-reference flag, or an implausible Sharpe/win-rate, means the backtest is a bug not an edge."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 3, "reported_sharpe": 21.902, "best_sharpe": 21.902, "median_sharpe": 11.74, "frac_positive": 1.0, "neighbour_mean_sharpe": 11.74, "plateau_score": 0.536, "fragile": true, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 19.248, "wf_sharpe_refit_mean": 19.248, "fold_sharpes_fixed": [21.2, 22.8, 10.84, 21.33, 20.07], "regime_like": false, "folds": [{"test_sharpe_fixed": 21.1999, "test_sharpe_refit": 21.1999}, {"test_sharpe_fixed": 22.7992, "test_sharpe_refit": 22.7992}, {"test_sharpe_fixed": 10.8377, "test_sharpe_refit": 10.8377}, {"test_sharpe_fixed": 21.3287, "test_sharpe_re`

- 🔧 **call** `cost_stress` — `{}`

- ✅ **result** `cost_stress` — `{"sharpe_by_cost": {"0bps": 21.902, "1bps": 21.6289, "2bps": 21.3508, "5bps": 20.4892, "10bps": 18.9792}, "survives_5bps": true, "reading": "Edge disappears once realistic slippage/fees are applied => not tradable."}`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 467, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🧠 **model** (2696→549 tok): Summary of raw findings:

- **IS Sharpe reported:** 21.902 (implausibly high), max drawdown 0.0, exposure ~0.999, 467 trades.
- **Lookahead probe:** static flag `shift(-...)` present; Sharpe collapses from 21.9 (lag1) to 1.52 (lag2) and 0.70 (lag3); win rate at lag1 = 1.0 (perfect). Flagged as suspected lookahead bug.
- **OOS test:** OOS Sharpe 21.10, ratio OOS/IS = 0.963 — OOS nearly matches IS (unusual given lookahead flag), OOS drawdown also 0.0.
- **Monte Carlo permutation:** observed Sharpe 21.902 vs null mean 21.807, p95 22.618, p-value 0.433 — the observed Sharpe is indistinguishable fr… (+543 chars)

- 💭 verify findings against raw numbers

- 🧠 **model** (2320→1040 tok): [{"id": "lookahead_bias", "evidence": "lookahead_probe.suspected=true; static flag 'shift(-' detected; sharpe_lag1=21.902 vs sharpe_lag2=1.523, sharpe_lag3=0.696; win_rate_lag1=1.0"}, {"id": "robust_oos", "evidence": "oos_test oos_sharpe=21.1023 (>=0.45) and oos_over_is=0.963 (>=0.6)"}]

- 💭 digest: {"reported_is_sharpe": 21.902, "oos_sharpe": 21.1023, "oos_over_is": 0.963, "mc_p_value": 0.4328, "walk_forward_fixed_mean": 19.248, "walk_forward_regime_like": false, "walk_forward_folds": [21.2, 22.8, 10.84, 21.33, 20.07], "param_plateau_score": 0.536, "param_fragile": true, "lookahead_suspected": true, "lookahead_static_flags": ["shift\\(\\s*-"], "cost_survives_5bps": true, "n_trades": 467, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> overfit: look-ahead leak detected (static future reference / lag-sweep collapse)

- 🧠 **model** (825→581 tok): {"rationale": "The lag-sweep collapse (Sharpe 21.902 at lag1 -> 1.523 at lag2 -> 0.696 at lag3, with a suspicious win_rate_lag1=1.0) alongside a detected static 'shift(-' flag is a textbook look-ahead signature, meaning the reported edge only exists when the future reference is present. This also explains why the 'robust' OOS numbers (oos_sharpe=21.1023, oos_over_is=0.963) look implausibly strong and mirror the leaked in-sample result rather than confirming genuine robustness; combined with a non-significant mc_p_value=0.4328 and param_fragile=true, capital should not be risked on this strateg… (+10 chars)


**FINISH** in 70.05s — result: `{"verdict": "overfit", "rationale": "The lag-sweep collapse (Sharpe 21.902 at lag1 -> 1.523 at lag2 -> 0.696 at lag3, with a suspicious win_rate_lag1=1.0) alongside a detected static 'shift(-' flag is a textbook look-ahead signature, meaning the reported edge only exists when the future reference is present. This also explains why the 'robust' OOS numbers (oos_sharpe=21.1023, oos_over_is=0.963) look implausibly strong and mirror the leaked in-sample result rather than confirming genuine robustness; combined with a non-significant mc_p_value=0.4328 and param_fragile=true, capital should not be `
