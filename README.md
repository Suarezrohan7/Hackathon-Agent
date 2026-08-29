# Strategy Validation Agent

**An agent that tells you whether a backtested trading strategy has a real edge — or is curve-fit, lucky, or buggy — and backs the verdict with out-of-sample and statistical evidence.**

Built for the micro1 Frontier Engineering Challenge 2026. Theme: *build at the frontier of agentic AI, where correctness, reproducibility and human judgment matter.*

---

## The user and the bottleneck

**Who:** an independent / retail algorithmic trader, or a junior quant at a small fund, about to allocate real capital to a strategy whose backtest looks good.

**The bottleneck:** a good-looking backtest is the *default* outcome of searching over strategies and parameters — most are curve-fit or lucky. Telling a real edge from an artefact means running a disciplined battery:

- out-of-sample test on data the strategy was never fitted to
- walk-forward (rolling re-fit) evaluation
- Monte-Carlo permutation — is the in-sample Sharpe within what random data produces?
- parameter-sensitivity — is the chosen parameter a broad plateau or a lone spike?
- look-ahead-leak probe — does the "edge" survive an honest execution lag?
- transaction-cost stress
- trade-count adequacy

Each step needs judgement, the whole battery is tedious, and it is routinely skipped or half-done. People lose real money on strategies that never had an edge. *Convincing is not enough* — which is exactly this challenge's premise.

---

## What existed before vs. what was built for the challenge

| Existed before | Built for this challenge |
|---|---|
| The author's prior trading projects (backtesting discipline, risk-gate patterns, the habit of rejecting overfit changes) — none of that code is reused here | Everything in this repo: the backtest engine, the synthetic-data ground-truth generator, the 7 check functions, the baseline, the agent pipeline, the eval harness, the trajectory capture, the HTML report, the dashboard, the tests |
| `anthropic`, `numpy`, `pandas`, `flask` (standard libraries) | The agent design and all orchestration around them |

---

## Baseline vs. advanced (both required)

| | **Baseline** — `baseline/run.py` | **Advanced** — `advanced/run.py` |
|---|---|---|
| Method | One model call: strategy source + its in-sample backtest report → verdict. No data, no tools. | `profile` (deterministic) → `plan + execute` checks (model chooses which; tools return real numbers) → `verify` findings (model keeps only what the numbers support; code enforces the allowed set) → **evidence rule assigns the verdict** → model writes the rationale → human checkpoint |
| Key property | Anchors on the glossy in-sample Sharpe — the failure this challenge is about | The classification is a **transparent 6-branch rule over the verified evidence**, so the verdict is reproducible and cannot drift on model temperament. The model does the parts it is good at — planning checks, interpreting findings, explaining — and can log a dissent. A deterministic **safety net** runs any check the planner skipped. A positive verdict is **gated on human sign-off** before any live-capital step. |

Both take the **same input** and are scored on the **same 13 cases** by `eval/`.

---

## Trustworthy ground truth

The eval only means something if the labels are certain. `cases/generate.py` builds 13 cases from **synthetic price series with known statistical properties** (real AR(1) momentum / Ornstein-Uhlenbeck mean-reversion / random walk / trend-then-chop) paired with strategies whose relationship to that data we control. Generation and validation are the **same check**: for each case the script searches a fixed seed range for one where the labelled behaviour is unambiguous (an `edge` case really holds out-of-sample; an `overfit` case really collapses; the look-ahead bug really shows up). If no seed qualifies, generation fails — a case can never ship with an ambiguous label.

The 13 committed cases: 6 `edge` (incl. a regime-dependent one and a thin-sample one), 4 `overfit` (incl. a look-ahead bug and two grid-searched fits), 3 `no_edge` (incl. one that only looks good in-sample by luck, and one killed by transaction costs).

---

## Headline result

One clean `python -m eval.harness --which both` run, 13 cases, same inputs to both:

| Metric | Baseline | Advanced | Change |
|---|---|---|---|
| **Verdict accuracy** | **38%** (5/13) | **100%** (13/13) | **+62 pts** |
| Findings F1 | 0.34 | 0.61 | +0.26 |
| Findings recall | 0.58 | 0.92 | +0.34 |
| Errors | 0 | 0 | — |
| USD per case | $0.011 | $0.050 | +$0.039 |
| Runtime per case | 9 s | 56 s | +47 s |

The committed run — `summary.md`, `report.html`, `raw.json` — is in [`results/reference-run/`](results/reference-run/); the per-case agent traces are in [`trajectories/reference/`](trajectories/reference/). Reproduce with `python -m eval.harness --which both`.

---

## Repo layout

```
baseline/run.py       the simple baseline
advanced/
  run.py              the engineered agent pipeline
  checks.py           7 deterministic robustness checks (no LLM)
eval/
  harness.py          runs baseline + advanced on the same cases -> metric table + HTML report
  scorer.py           verdict accuracy + findings precision/recall/F1
lib/
  backtest.py         minimal vectorised backtester (no look-ahead by construction)
  pricegen.py         synthetic price processes with known properties
  llm.py              pinned Claude client + tool loop + MOCK mode
  trajectory.py       step-by-step capture -> .md + .jsonl  (submission artifact)
  cost.py             token + USD accounting
  report.py           self-contained dark-theme HTML report
cases/
  generate.py         (re)builds the 13 labelled cases, self-validating
  case-*/             the frozen test set (committed)
tests/test_pipeline.py  key-free correctness + ground-truth-invariant tests
app.py                local dashboard: paste a strategy, watch it get validated
```

---

## Run it

Full walkthrough in [`REPRODUCTION.md`](REPRODUCTION.md). Short version:

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows (.venv/bin/activate elsewhere)
pip install -r requirements.txt
python -m pytest -q                                  # 22 tests, no API key needed
cp .env.example .env                                 # add ANTHROPIC_API_KEY
python -m eval.harness --which both                  # the headline comparison
python app.py                                        # optional dashboard -> http://127.0.0.1:7600
```

`python -m cases.generate --seed 7 --fresh` regenerates the test set byte-for-byte; `--check` re-validates the committed one.

---

## Changelog & hot take

[`IMPROVEMENT_CHANGELOG.md`](IMPROVEMENT_CHANGELOG.md) — every iteration, its evidence, the decision it drove; main failure mode and hot take at the bottom.

## Coding tools disclosure

Built with Claude Code (Claude Sonnet). Representative agent trajectories for both the baseline and the advanced agent are under `trajectories/`.
