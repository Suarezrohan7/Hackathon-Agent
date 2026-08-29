# Improvement Changelog

Iterations 1–2 are evidenced by `python -m cases.generate` and `python -m pytest -q`
(deterministic, no API key). Iterations 3–4 by `python -m eval.harness --which both`;
the committed run is in `results/reference-run/`.

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| **Baseline** | One model call: strategy source + its in-sample backtest report → verdict. The obvious first approach. | **verdict accuracy 38%** (5/13), findings F1 0.34 | Gets the `overfit` cases from code inspection (grid-search smell, `shift(-`) but cannot separate `edge` from `no_edge` — it never sees out-of-sample data. This is the ceiling of "read the numbers you were handed." |
| **Iteration 1 — self-validating ground truth** | The first generator used fixed seeds + fixed parameters and *assumed* the label. | On first generation only **3/13** cases actually exhibited their labelled behaviour (an "edge" case had OOS Sharpe −0.07). | Generation and validation unified: for each case, search a fixed seed range until its defining invariant holds. Result **13/13**. A labelled set you didn't verify is not a test set. |
| **Iteration 2 — a real bug the self-check surfaced** | With validation on, the Donchian-breakout cases still misbehaved. | The strategy compared `close` to a band built from `high = close + noise`, so the long signal *never fired*; "no-edge" cases "passed" only because a strategy that never trades has ~0 Sharpe. | Fixed Donchian to break the **prior** N-bar range (`.shift(1)`). The harness caught a bug that eyeballing the code would not. |
| **Iteration 3 — advanced v1: the LLM decides** | Full agent: LLM plans and runs the 7 checks in a tool loop, a second LLM pass verifies findings, a third LLM call issues the verdict from the digest (the glossy in-sample report withheld from it). | **verdict accuracy 38%** (5/13) — *no better than baseline*. `case-13` had `robust_oos` verified and the model still returned `no_edge`; `regime_dependence` was emitted on all 13 cases; the model invented a finding id (`statistical_insignificance`) outside the allowed set. | The LLM gathered correct evidence and then **discarded it at the decision**. Prompt-tightening moved the number by ~1 case and stayed incoherent. The decision step, not the evidence-gathering, was the failure. |
| **Iteration 4 — rule over evidence; gate findings in code** | Move the classification to a transparent 6-branch rule over the verified digest (look-ahead → overfit; fails cost stress → no_edge; holds OOS net of costs → edge; in-sample collapsed + fragile params → overfit; collapsed but robust params → luck/no_edge). Findings gated in code against the specific check that supports each. LLM keeps planning, verifying, and writing the rationale, and can log a dissent. | **verdict accuracy 100%** (13/13), findings F1 0.61, recall 0.92, 0 errors. `results/reference-run/`. | The main contribution: **+62 points** from moving the yes/no off the model and onto a rule over the evidence the model had already verified. |
| **Final** | Iterations 1, 2, 4 combined. | 38% → 100% verdict accuracy; 0.34 → 0.61 F1. | Shipped. |

## Removed experiment

**Monte-Carlo block-bootstrap permutation as a finding source.** Intended: block-bootstrap
the in-sample returns, re-run the strategy, and if the real Sharpe beats the null distribution
(low p-value) call it `significant_vs_null`. The real digests showed the signal **inverted** —
overfit cases had low p (0.04–0.07), genuine-edge cases had high p (0.16–0.35). Reason: a block
bootstrap preserves the serial structure *inside* each block, so a series with real momentum
still lets the strategy profit on the shuffled paths; the observed Sharpe doesn't stand out.
The test actually measures "is this fit specific to this exact data ordering" — a data-mining
signal, not a skill signal. The check still runs and appears in the trajectory as context, but
`significant_vs_null` was removed as a finding and out-of-sample performance carries that weight
instead.

## Main failure mode

An agent that gathers correct evidence still reaches the wrong conclusion when the final
judgement is left to the model. The model rationalised a `no_edge` verdict on a strategy for
which it had already verified every "this holds up" signal.

## Hot take

The LLM was the weakest link in its own pipeline — strong at *choosing which tests to run* and
*explaining the result*, unreliable at the *classification*. The fix was not a better prompt; it
was **taking the decision away from the model** and giving it to a six-branch rule over the
evidence the model had verified. Use the LLM for the judgement it is good at — which checks
matter, how to interpret and explain them — and let a transparent rule make the call a rule
makes more reliably. It is also more defensible: the verdict is reproducible and auditable, not
a function of model temperament.
