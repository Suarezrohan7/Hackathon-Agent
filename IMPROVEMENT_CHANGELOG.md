# Improvement Changelog

Evidence for iterations 1–3 comes from `python -m cases.generate` and
`python -m pytest -q` (deterministic, no API key). Iterations 4+ and the
baseline/advanced accuracy numbers are filled from `python -m eval.harness`
once an `ANTHROPIC_API_KEY` is set — see `results/reference-run/`.

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | One model call: strategy source + its in-sample backtest report → verdict. The obvious first approach. | _pending eval run_ | The starting point. Expected weakness: anchors on the in-sample Sharpe. |
| **Iteration 1 — self-validating ground truth** | First generator used fixed seeds + fixed parameters and *assumed* the label. | On first generation only **3/13** cases actually exhibited their labelled behaviour (e.g. an "edge" case whose OOS Sharpe was −0.07). | Unified generation *with* validation: for each case, search a fixed seed range until its defining invariant holds (edge really holds OOS, overfit really collapses, …). Result **13/13**. A labelled test set you didn't verify is not a test set. |
| **Iteration 2 — a real bug the self-check surfaced** | With validation on, the Donchian-breakout cases still misbehaved. | The strategy compared `close` to a band built from `high = close + noise`, so the long signal *never fired*; "no-edge" cases were "passing" only because a strategy that never trades has ~0 Sharpe. | Fixed Donchian to break the **prior** N-bar range (`.shift(1)`). Cases 03/07/11 went from degenerate to genuine trading behaviour. The eval harness caught a bug the author would have missed by eye. |
| **Iteration 3 — deterministic safety net in the agent** | Ran the advanced pipeline and inspected trajectories. | When the planner under-calls (seen directly in MOCK mode), critical checks were skipped — `lookahead_probe` did not run on the look-ahead-bug case. | Added a safety net: `oos_test`, `monte_carlo_permutation`, `trade_count` always run; `lookahead_probe` runs whenever the profile shows a static future-reference flag; `param_sensitivity` runs when the grid is non-trivial. The model still owns ordering, reasoning, and any extra checks. Look-ahead case now always reports `lookahead_suspected=True` (pattern `shift(-` matched). |
| **Iteration 4 — withhold the in-sample report from the verdict** *(needs API key)* | Hypothesis: with the glossy in-sample Sharpe in context, the model rationalises `edge` even after the checks show an out-of-sample collapse. | Run the `decide` step **with** vs **without** the in-sample report, same 13 cases; compare verdict accuracy. | _pending — this is the anti-anchoring change and the hot take below._ |
| **Final** | Combination that shipped. | _pending eval run_ | Main contribution: _pending — expected to be Iteration 4._ |

---

## Main failure mode

When the strategy's own flattering in-sample backtest is present in the deciding
model's context, the model treats it as the anchor and reinterprets contradicting
out-of-sample / permutation evidence as "noise" rather than as the answer — it
produces a confident `edge` verdict on strategies the checks have already shown
to collapse.

## Hot take

An agent that gathers correct evidence can still reach the wrong conclusion if the
*tempting wrong evidence* is also in the context window. The fix is not a better
prompt — it is **information design**: the step that gathers evidence and the step
that judges should not see the same things. Give the deciding step only the
out-of-sample facts, and structurally deny it the artefact it would rather believe.
