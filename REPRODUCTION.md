# Reproduction Guide

Written for someone starting from a **clean machine**.

## Requirements
- Python 3.11+ (developed on 3.11.x)
- An Anthropic API key with access to Claude Sonnet
- OS: Windows / macOS / Linux (developed on Windows 11)
- No other external services. All test data is in `cases/` (synthetic — safe to share).

## Setup
```bash
git clone <REPO_URL>
cd micro1-hackathon

python -m venv .venv
. .venv/Scripts/activate          # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Run the baseline
```bash
python -m eval.harness --which baseline --cases cases/
```

## Run the advanced solution
```bash
python -m eval.harness --which advanced --cases cases/
```

## Run the full comparison (headline result)
```bash
python -m eval.harness --which both --cases cases/
```
Output: `results/run-<timestamp>/summary.md` — the metric table (primary outcome, human time/task, cost/task; baseline vs advanced vs change), plus per-case detail and captured trajectories under `trajectories/`.

## Expected output
- Baseline primary metric: **_[fill]_**
- Advanced primary metric: **_[fill]_**
- Runtime: ~**_[N]_** min for all cases (baseline), ~**_[N]_** min (advanced)
- Cost: ~**$_[N]_** per full `--which both` run at listed model prices

## Determinism notes
- `temperature=0` on all model calls.
- Case order fixed; any randomness in case generation is seeded (`cases/generate.py --seed 7`).
- Model version pinned in `lib/llm.py` (`MODEL = "..."`).
