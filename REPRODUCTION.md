# Reproduction Guide

Written for a reviewer starting from a **clean machine**. Nothing is hosted; the
whole project is this repository. Clone it, install, run three commands.

## What you need

| | |
|---|---|
| Python | 3.11+ (developed on 3.11) |
| API key | one `ANTHROPIC_API_KEY` with Claude Sonnet access — you supply your own, as the challenge requires |
| OS | Windows / macOS / Linux (developed on Windows 11) |
| Data | none to download — the 13 labelled test cases are committed under `cases/case-*/` |
| Network | only to the Anthropic API |

## Setup

```bash
git clone https://github.com/Suarezrohan7/Hackathon-Agent.git
cd Hackathon-Agent

python -m venv .venv
. .venv/Scripts/activate            # Windows
# source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt
```

## 1. Verify the engine — no API key needed

```bash
python -m pytest -q
```
Expected: **22 passed**. This checks the backtester, the synthetic-data
properties, and that every one of the 13 cases still has an unambiguous
ground-truth label.

```bash
python -m cases.generate --seed 7 --check
```
Expected: **13/13 invariants hold** — the committed test set is internally consistent.
`--fresh` instead of `--check` regenerates it byte-for-byte.

## 2. Run the baseline

```bash
cp .env.example .env      # then edit: ANTHROPIC_API_KEY=sk-ant-...
python -m eval.harness --which baseline
```

## 3. Run the advanced agent

```bash
python -m eval.harness --which advanced
```

## 4. The headline comparison

```bash
python -m eval.harness --which both
```
Writes `results/run-<UTC-timestamp>/`:
- `summary.md` — the baseline-vs-advanced metric table
- `report.html` — self-contained dark-theme report (open in a browser)
- `raw.json` — every prediction, score, and cost
- `trajectories/run-<timestamp>/*.md` — step-by-step agent trace per case (model turns, tool calls, tool results, retries, human checkpoints)

A pre-run copy of these artifacts from the author's environment is committed under
`results/reference-run/` so you can see the expected output before spending a token.

## Expected output

| | Baseline | Advanced |
|---|---|---|
| Verdict accuracy (13 cases) | _filled from reference-run_ | _filled from reference-run_ |
| Findings F1 | – | – |
| Runtime, all cases | ~1–2 min | ~4–8 min |
| Cost, `--which both` | ~$_N_ at listed model prices | |

Single case, for a quick look:
```bash
python -m eval.harness --which advanced --only case-06-lookahead-bug
```

## 5. Optional — the dashboard

```bash
python app.py      # http://127.0.0.1:7600
```
Paste a strategy (must define `signal(df, **params)`, `PARAMS`, `PARAM_GRID`),
pick a dataset (a bundled case or a fresh synthetic process), hit **Validate**,
and watch the agent's checks and trajectory. Read-only — it never places a trade.
Not part of the graded reproduction; it's the human-facing demo.

## Determinism

- `temperature = 0` on every model call.
- Model id pinned in `lib/llm.py` (`MODEL`).
- Case generation is seeded; the seed scan order is fixed.
- The Monte-Carlo permutation check seeds its RNG (`seed=12345`).
- Small run-to-run wording differences in the model's `rationale` field are
  expected; the `verdict` and `findings` are stable.
