# Trajectories

Two kinds, both required by the challenge.

## 1. Solution-agent trajectories — `reference/`

The agent that *is* the solution is `advanced/run.py` (the Strategy Validation Agent).
Every run writes a step-by-step trace: each model turn, every tool call and the
numbers it returned, any retry, and the human checkpoint. `reference/` holds the
full set from the committed evaluation run (`../results/reference-run/`): 13 cases
× {baseline, advanced}.

**Start with these three — they show the whole mechanism:**

| File | What it demonstrates |
|---|---|
| `reference/advanced__case-06-lookahead-bug.md` | the look-ahead probe fires on a static `shift(-` flag; the evidence rule returns `overfit`; the LLM writes the rationale |
| `reference/advanced__case-04-overfit-kitchensink.md` | the full 7-check battery; `param_fragile` + `oos_collapse` detected; verdict `overfit` |
| `reference/advanced__case-13-meanrev-edge-2.md` | a clean `edge` verdict, and the **human checkpoint** that gates it before "tradable" |

Read `advanced__*` against the matching `baseline__*` to see the difference: the
baseline is one model turn and a guess; the advanced trace is plan → run checks →
verify findings → rule assigns the verdict → LLM explains → human gate.

## 2. Coding-agent build trajectory — `BUILD_LOG.md`

How this repository was built, using **Claude Code (Claude Sonnet)** as the coding
agent. Curated from the build session: each entry is an instruction given, what the
agent did, the tool output that came back, and the decision it drove — including
the retries and the course-corrections that didn't work the first time.
