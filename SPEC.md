# What we are building — Strategy Validation Agent

## One line
An agent that takes a backtested trading strategy and decides whether its edge is
**real**, **overfit**, or **absent** — from out-of-sample and statistical evidence,
not the glossy in-sample report.

## The user and the bottleneck
- **User:** an independent / retail algo trader (or a small fund's junior quant)
  about to put real capital behind a strategy whose backtest looks good.
- **Bottleneck today:** a good-looking backtest is usually curve-fit or lucky.
  Separating edge from artefact needs a disciplined battery — out-of-sample test,
  walk-forward, Monte-Carlo permutation / significance, parameter sensitivity,
  look-ahead-leak probe, transaction-cost stress, trade-count adequacy. It is
  tedious, needs judgement, and is routinely skipped. People lose money on
  strategies that never had an edge.
- **Why it matters:** a wrong "yes" = real drawdown; a wrong "no" = a missed edge.
  This is the hackathon's thesis — *convincing is not enough*.

## Baseline vs advanced (both required)
- **Baseline:** one LLM call. Input = strategy code + its in-sample backtest
  report. Output = verdict + findings. No data, no tests, no tools. Over-trusts
  the in-sample Sharpe — the weakness the changelog exploits.
- **Advanced:** a pipeline —
  1. **Profile** (deterministic): parse the strategy — parameter count, static
     look-ahead scan, reported Sharpe / drawdown / trade count.
  2. **Plan** (LLM + tools): choose which checks matter for this strategy.
  3. **Execute** (LLM tool-loop): run real check functions, each returning
     numeric evidence — `oos_test`, `walk_forward`, `monte_carlo_permutation`,
     `param_sensitivity`, `lookahead_probe`, `cost_stress`, `trade_count`.
  4. **Verify** (LLM): keep only findings the numbers directly support.
  5. **Decide** (LLM): final verdict + findings as JSON, each claim citing a
     check result. **The glossy in-sample report is withheld from this step**
     (anti-anchoring — also a planned changelog iteration + the hot take).
  6. **Human checkpoint:** verdict `edge` gates on human sign-off before any
     "recommend for live capital" step (logged, per the Rule Book).

## Input / output contract
- A **case** = a folder: `strategy.py` (parameterised signal fn + reported params
  + param grid), `data.csv` (in-sample), `data_oos.csv` (held-out),
  `backtest_report.json` (the in-sample stats being shown off), `meta.yaml`,
  `ground_truth.json`.
- **Prediction** = `{verdict: edge|overfit|no_edge, rationale, findings:[{id, evidence}]}`.
- Allowed finding ids: `oos_collapse`, `param_fragility`, `lookahead_bias`,
  `regime_dependence`, `transaction_cost_sensitivity`, `insufficient_trades`,
  `robust_oos`, `significant_vs_null`.

## Trustworthy ground truth (the crux)
Synthetic price series with **known** properties + strategies with a **known**
relationship to them:
- `edge`: exploits real structure we baked in (AR(1) momentum / OU
  mean-reversion); a-priori params; holds out-of-sample.
- `overfit`: many-parameter strategy grid-searched to max in-sample Sharpe on
  ~random data; collapses out-of-sample.
- `no_edge`: near-random strategy on a random walk; in-sample result is luck.
- Edge cases: look-ahead-bug strategy; genuine-edge-but-regime-dependent (the
  hard case); edge that dies after costs; real edge with too few trades.
- ~13 cases, frozen and committed; `cases/generate.py --seed 7` regenerates them
  byte-for-byte.

## Eval and headline metric
- **Primary:** verdict accuracy (prediction vs known label), all cases.
- **Secondary:** findings precision / recall / F1; USD per task; human minutes.
- Same cases through baseline and advanced. Expected: baseline ~40–55%,
  advanced ~85%+ (to be confirmed once the API key is in).

## Maps to the 4 submission items
1. **Code + changelog** — this repo; `IMPROVEMENT_CHANGELOG.md`, one evidenced row
   per iteration; main failure mode + hot take.
2. **Reproduction guide** — `REPRODUCTION.md`: clean-env, exact commands,
   `--which baseline|advanced|both`, expected numbers, runtime, cost.
3. **Video ≤5 min** — problem → baseline → one real case walk-through → final
   comparison → the one change that mattered → one removed experiment.
4. **Trajectories** — `lib/trajectory.py` captures every model turn, tool call,
   tool result, retry, human checkpoint to `.md` + `.jsonl` per run.

## Build status
- Done + smoke-tested: `eval/harness.py`, `eval/scorer.py`, `lib/trajectory.py`,
  `lib/cost.py`, `lib/llm.py` (MOCK mode), `lib/backtest.py`, `lib/pricegen.py`,
  `lib/strategies.py`. Pushed to `github.com/Suarezrohan7/Hackathon-Agent`.
- Left: `cases/generate.py` + 13 cases · `advanced/checks.py` · `advanced/run.py`
  (specialise) · `baseline/run.py` (specialise) · `tests/test_pipeline.py` · fill
  `README.md` / `REPRODUCTION.md` / changelog baseline row · then real evals.

## BLOCKER
The kickoff **problem document** (Aug 28, 15:00 UTC — "you will receive the problem
document and any starter material you need"). Not yet seen. If it prescribes a
specific problem, a starter repo, dependency limits, or an acceptance harness,
this spec changes. Confirm before the deep build continues.
