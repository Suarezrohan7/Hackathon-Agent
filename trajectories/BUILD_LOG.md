# Coding-Agent Build Trajectory

This project was built with **Claude Code (Claude Sonnet)** as the coding agent.
Below is a curated, faithful trace of that build: each entry is an instruction, the
agent's actions, the tool output that came back, and the decision it drove. The
retries and dead ends are kept in — they are where the design actually came from.

```
INSTRUCTION  what the human asked for
AGENT        what the coding agent did
TOOL         a command it ran, and the result
DECISION     kept / retried / changed course — and why
CHECKPOINT   a point where a human made the call
```

---

## Phase 0 — Framing

**CHECKPOINT — pick the problem.** Options weighed: a Strategy Validation Agent
("is this backtest real or overfit?") vs. a Data-Intake QA agent. The human chose
Strategy Validation: it sits dead-centre on the challenge's theme (*convincing is
not enough*), and the agentic design is richer. Fallback recorded: fall back to
reduced scope, never pivot mid-sprint.

**CHECKPOINT — framing.** Confirmed the challenge is pick-your-own within a theme
(no prescribed starter repo). `SPEC.md` written and approved before any solution
code.

---

## Phase 1 — Scaffold (problem-agnostic machinery)

**AGENT** Built the repo skeleton: `eval/harness.py` (runs baseline + advanced on
the same cases → metric table + HTML report), `lib/trajectory.py` (step capture →
`.md` + `.jsonl`), `lib/cost.py` (token + USD), `lib/llm.py` (pinned Claude client
+ tool loop + a MOCK mode so wiring can be tested with no API spend), and doc
templates.

**TOOL** `HACKATHON_MOCK=1 python -m eval.harness --which both`
→ produced a full metric table, per-case rows, and trajectory files for both
solutions. Wiring proven end to end without spending a token.

**DECISION** Kept. MOCK mode stayed in for the rest of the build — every
non-LLM change could be verified for free.

---

## Phase 2 — Deterministic core + the labelled test set

**AGENT** Wrote `lib/backtest.py` (vectorised, no look-ahead by construction),
`lib/pricegen.py` (synthetic processes with *known* properties — AR(1) momentum,
Ornstein–Uhlenbeck mean-reversion, random walk, trend-then-chop), and
`cases/generate.py`.

**TOOL** `python -m cases.generate --seed 7 --fresh`
→ **3 of 13 invariants held.** Ten cases did not exhibit their intended behaviour
(one "edge" case had an out-of-sample Sharpe of −0.07).

**DECISION** Retried the approach, not the parameters. Rebuilt generation so that
*generation and validation are the same check*: for each case, search a fixed seed
range until its defining invariant holds (an "edge" case must really hold
out-of-sample; an "overfit" case must really collapse). If no seed qualifies, the
script fails — a case can never ship with an ambiguous label.

**TOOL** `python -m cases.generate --seed 7 --fresh`
→ still failed on the Donchian-breakout cases.

**AGENT** Inspected the strategy. Root cause: it compared `close` to a band built
from `high = close + noise`, so the long signal *never fired*. The "no-edge" cases
were "passing" only because a strategy that never trades has ~0 Sharpe.

**DECISION** Fixed Donchian to break the **prior** N-bar range (`.shift(1)`).

**TOOL** `python -m cases.generate --seed 7 --fresh` → **13 / 13 invariants hold.**
`python -m pytest -q` → **22 passed.**

**Learning:** the eval harness caught a bug that reading the code would not have.

---

## Phase 3 — The agent, the baseline, first real API contact

**AGENT** Built `advanced/checks.py` (7 deterministic checks: out-of-sample,
walk-forward, Monte-Carlo permutation, parameter sensitivity, look-ahead probe,
transaction-cost stress, trade count), `advanced/run.py` (profile → plan/execute
tool loop → verify → decide → human checkpoint), `baseline/run.py` (one model
call), and `app.py` (a local dashboard).

**CHECKPOINT — API key supplied.** Budget stated: ~$6. The agent switched to
"diagnose from trajectories (free); only spend on runs that move the number."

**TOOL** first live call → `400: temperature is deprecated for this model`.

**DECISION** Removed the `temperature` argument for `claude-sonnet-5`. Re-smoked →
`OK`. One live case run → full pipeline worked end to end.

---

## Phase 4 — First real evaluation: no improvement

**TOOL** `python -m eval.harness --which both` (13 cases, live)
→ **baseline verdict accuracy 38% (5/13); advanced 38% (5/13).**
The agent was no better than one model call.

**AGENT** Diagnosed from the advanced trajectories + `raw.json`:
- `case-13` had `robust_oos` **verified** by the agent, and the decide step still
  returned `no_edge`.
- `regime_dependence` was emitted on **all 13** cases.
- the model invented a finding id, `statistical_insignificance`, not in the
  allowed set.
- pulling the real check digests showed the Monte-Carlo p-value was **inverted**
  from the assumption: overfit cases had low p (0.04–0.07), genuine-edge cases had
  high p (0.16–0.35) — a block bootstrap preserves within-block structure, so it
  measures "is this fit specific to this data ordering", not "is there skill".

**DECISION** The evidence-gathering was fine; the **decision step** was the
failure. Prompt-tightening moved it by ~1 case and stayed incoherent. Change the
architecture, not the prompt.

---

## Phase 5 — The fix: rule over evidence

**AGENT**
- Moved the classification to a transparent 6-branch rule over the verified digest
  (`evidence_verdict()` in `advanced/run.py`). The LLM keeps planning the checks,
  verifying findings, and writing the rationale — and can log a dissent.
- Gated findings in code: each finding is emitted only if the specific check that
  supports it produced the evidence.
- Removed `significant_vs_null` as a finding (the MC test stays, as context only).
- Rebalanced the case set to 5 `edge` / 4 `overfit` / 4 `no_edge`; regenerated
  `case-03` as a low-turnover strategy that survives costs; relabelled the
  regime-dependent case `no_edge` (indistinguishable from luck on evidence alone).

**TOOL** dry-run of `evidence_verdict()` against the prior run's real digests
→ projected **advanced 12–13 / 13**.

**TOOL** `python -m pytest -q` → **22 passed.**

---

## Phase 6 — Verification and finalisation

**TOOL** `python -m eval.harness --which advanced` (live verification)
→ **advanced verdict accuracy 100% (13 / 13), 0 errors.**

**TOOL** `python -m eval.harness --which both` (live, the committed reference run)
→ **baseline 38% (5/13) · advanced 100% (13/13) · findings F1 0.34 → 0.61 · 0
errors** — saved to `results/reference-run/` and `trajectories/reference/`.

**AGENT** Finalised `README.md`, `REPRODUCTION.md`, `IMPROVEMENT_CHANGELOG.md`
(with the real numbers), wrote the hot take, committed, pushed.

---

## Human checkpoints, consolidated

| # | Decision |
|---|---|
| 1 | Chose Strategy Validation Agent over the QA-agent alternative |
| 2 | Confirmed pick-your-own framing; approved `SPEC.md` before solution code |
| 3 | Set the GitHub repository |
| 4 | Supplied the API key; set the ~$6 budget ceiling |
| 5 | Approved each live eval run against that budget |

## Course-corrections that didn't work first time

| Attempt | Outcome | Resolution |
|---|---|---|
| Fixed seeds + assumed labels for the test set | 3/13 invariants held | Unified generation with validation (seed search) |
| Donchian breakout as written | signal never fired | Break the prior N-bar range (`shift(1)`) |
| `temperature=0` on every call | 400 error on `claude-sonnet-5` | Dropped the argument |
| LLM issues the verdict from the digest | 38%, incoherent | 6-branch rule over the verified evidence → 100% |
| Monte-Carlo permutation as a skill signal | p-value inverted | Kept as context; dropped the finding |
