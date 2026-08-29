# Trajectory — `advanced/case-13-meanrev-edge-2`

_Rendered 2026-08-28T19:06:43+00:00_

**START** `advanced/case-13-meanrev-edge-2` @ 2026-08-28T19:05:54+00:00

- 💭 profile: {"n_params": 3, "param_names": ["period", "low", "high"], "param_grid_size": 36, "reported_is_sharpe": 1.9199, "reported_max_drawdown": -0.0699, "reported_n_trades": 88, "reported_exposure": 0.21, "static_future_reference_flags": []}

- 🧠 **model** (1157→605 tok): [6 tool_use]

- 🔧 **call** `oos_test` — `{}`

- ✅ **result** `oos_test` — `{"is_sharpe": 1.9199, "oos_sharpe": 1.7486, "oos_over_is": 0.911, "oos_max_drawdown": -0.0534, "oos_total_return": 0.7137, "reading": "OOS Sharpe far below IS Sharpe => the in-sample result did not generalise."}`

- 🔧 **call** `monte_carlo_permutation` — `{}`

- ✅ **result** `monte_carlo_permutation` — `{"observed_sharpe": 1.92, "n_perm": 200, "null_sharpe_mean": 1.416, "null_sharpe_p95": 2.201, "p_value": 0.1642, "reading": "p_value >= 0.10 => the in-sample Sharpe is within what random data produces."}`

- 🔧 **call** `param_sensitivity` — `{}`

- ✅ **result** `param_sensitivity` — `{"grid_size": 36, "reported_sharpe": 1.92, "best_sharpe": 2.342, "median_sharpe": 1.454, "frac_positive": 0.944, "neighbour_mean_sharpe": 1.663, "plateau_score": 0.866, "fragile": false, "reading": "plateau_score well below 1 (or negative) => the reported params are a lone spike, not a plateau (fragile)."}`

- 🔧 **call** `walk_forward` — `{}`

- ✅ **result** `walk_forward` — `{"n_folds": 5, "wf_sharpe_fixed_mean": 1.896, "wf_sharpe_refit_mean": 2.12, "fold_sharpes_fixed": [2.82, 1.5, 1.89, 2.05, 1.22], "regime_like": false, "folds": [{"test_sharpe_fixed": 2.8194, "test_sharpe_refit": 2.5844}, {"test_sharpe_fixed": 1.501, "test_sharpe_refit": 2.703}, {"test_sharpe_fixed": 1.889, "test_sharpe_refit": 1.8999}, {"test_sharpe_fixed": 2.0529, "test_sharpe_refit": 2.0571}, {"`

- 🔧 **call** `trade_count` — `{}`

- ✅ **result** `trade_count` — `{"n_trades": 88, "adequate": true, "reading": "Fewer than ~30 trades => the result is not statistically distinguishable from noise."}`

- 🔧 **call** `lookahead_probe` — `{}`

- ✅ **result** `lookahead_probe` — `{"static_flags": [], "sharpe_lag1": 1.9199, "sharpe_lag2": 1.6955, "sharpe_lag3": 0.8253, "win_rate_lag1": 0.75, "suspected": false, "reading": "A static future-reference flag, or an implausible Sharpe/win-rate, means the backtest is a bug not an edge."}`

- 🧠 **model** (2811→536 tok): Summary of raw evidence gathered:

- **In-sample stats:** Sharpe 1.92, max drawdown ‑7.0%, 88 trades, exposure 21%.
- **OOS test:** OOS Sharpe 1.75 (91% of IS), OOS max drawdown ‑5.3%, OOS total return 71%.
- **Monte Carlo permutation:** Observed Sharpe 1.92 vs null mean 1.42, null p95 2.20 → p‑value 0.164 (not significant at conventional 0.05/0.10 threshold).
- **Parameter sensitivity (grid=36):** Best Sharpe 2.34, median 1.45, reported 1.92 sits above median; neighbour mean 1.66; plateau score 0.87 (labeled "fragile: false" by the tool despite the "lone spike" wording in the reading text — p… (+535 chars)

- 🔁 **retry** — safety net: required check 'cost_stress' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (2291→399 tok): [{"id": "robust_oos", "evidence": "oos_test: oos_sharpe=1.7486 (>=0.45) and oos_over_is=0.911 (>=0.6)"}]

- 💭 digest: {"reported_is_sharpe": 1.9199, "oos_sharpe": 1.7486, "oos_over_is": 0.911, "mc_p_value": 0.1642, "walk_forward_fixed_mean": 1.896, "walk_forward_regime_like": false, "walk_forward_folds": [2.82, 1.5, 1.89, 2.05, 1.22], "param_plateau_score": 0.866, "param_fragile": false, "lookahead_suspected": false, "lookahead_static_flags": [], "cost_survives_5bps": true, "n_trades": 88, "checks_run": ["cost_stress", "lookahead_probe", "monte_carlo_permutation", "oos_test", "param_sensitivity", "trade_count", "walk_forward"]}

- 💭 evidence rule -> edge: holds out of sample net of costs: oos_sharpe 1.75

- 🧠 **model** (696→432 tok): {"rationale": "The strategy passes the core evidence rule with oos_sharpe=1.7486 (well above the 0.45 bar) and oos_over_is=0.911 (above 0.6), indicating the out-of-sample performance retains 91% of in-sample edge; walk-forward folds are all positive (1.22-2.82) and costs survive at 5bps, supporting robustness.", "dissent": "mc_p_value=0.1642 is above the conventional 0.05 significance threshold, meaning the permutation test cannot rule out that this Sharpe pattern arose by chance, which combined with a modest n_trades=88 warrants caution before sizing capital."}

- 💭 LLM dissent (not acted on): mc_p_value=0.1642 is above the conventional 0.05 significance threshold, meaning the permutation test cannot rule out that this Sharpe pattern arose by chance, which combined with a modest n_trades=88 warrants caution before sizing capital.

- 🧑‍⚖️ **human checkpoint** — Verdict = edge. Advance this strategy to a paper-trading track before any live capital? → **pending human reviewer sign-off**


**FINISH** in 48.47s — result: `{"verdict": "edge", "rationale": "The strategy passes the core evidence rule with oos_sharpe=1.7486 (well above the 0.45 bar) and oos_over_is=0.911 (above 0.6), indicating the out-of-sample performance retains 91% of in-sample edge; walk-forward folds are all positive (1.22-2.82) and costs survive at 5bps, supporting robustness.", "findings": [{"id": "robust_oos", "evidence": "oos_test: oos_sharpe=1.7486 (>=0.45) and oos_over_is=0.911 (>=0.6)"}]}`
