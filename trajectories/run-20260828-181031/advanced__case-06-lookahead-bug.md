# Trajectory — `advanced/case-06-lookahead-bug`

_Rendered 2026-08-28T18:11:02+00:00_

**START** `advanced/case-06-lookahead-bug` @ 2026-08-28T18:10:53+00:00

- 💭 profile: {"n_params": 1, "param_names": ["k"], "param_grid_size": 3, "reported_is_sharpe": 21.902, "reported_max_drawdown": 0.0, "reported_n_trades": 467, "reported_exposure": 0.999, "static_future_reference_flags": ["shift\\(\\s*-"]}

- 🧠 **model** (0→0 tok): {"verdict": "inconclusive", "reason": "MOCK response \u2014 set ANTHROPIC_API_KEY for a real run."}

- 🔁 **retry** — safety net: required check 'oos_test' not run by the planner; running it directly

- 🔁 **retry** — safety net: required check 'monte_carlo_permutation' not run by the planner; running it directly

- 🔁 **retry** — safety net: required check 'trade_count' not run by the planner; running it directly

- 🔁 **retry** — safety net: required check 'lookahead_probe' not run by the planner; running it directly

- 💭 verify findings against raw numbers

- 🧠 **model** (0→0 tok): {"verdict": "inconclusive", "reason": "MOCK response \u2014 set ANTHROPIC_API_KEY for a real run."}

- 💭 digest: {"oos_sharpe": 21.1023, "oos_over_is": 0.963, "mc_p_value": 0.4328, "walk_forward_fixed_mean": null, "param_plateau_score": null, "lookahead_suspected": true, "lookahead_static_flags": ["shift\\(\\s*-"], "cost_survives_5bps": null, "n_trades": 467, "checks_run": ["lookahead_probe", "monte_carlo_permutation", "oos_test", "trade_count"]}

- 🧠 **model** (0→0 tok): {"verdict": "inconclusive", "reason": "MOCK response \u2014 set ANTHROPIC_API_KEY for a real run."}


**FINISH** in 9.05s — result: `{"verdict": "inconclusive", "reason": "MOCK response \u2014 set ANTHROPIC_API_KEY for a real run.", "findings": []}`
