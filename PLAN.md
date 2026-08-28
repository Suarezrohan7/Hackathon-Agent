# micro1 Frontier Engineering Challenge 2026 — working plan

Sprint: 28–31 Aug 2026. Deadline **Aug 31, 18:00 UTC**. Individual. Coding-agent use required + trajectories submitted.

## Status
- [x] Eligibility ruling requested / registration done (per user).
- [x] Theme confirmed pick-your-own; no prescribed starter repo.
- [x] Domain locked: **Strategy Validation Agent**.
- [x] Repo pushed: `github.com/Suarezrohan7/Hackathon-Agent`.
- [x] Deterministic core: backtest engine, price generators, 13 self-validated cases.
- [x] `advanced/checks.py` — 7 robustness checks (no LLM).
- [x] `advanced/run.py` — profile → plan/execute → verify → decide → human gate + safety net.
- [x] `baseline/run.py` — single-call baseline.
- [x] `eval/harness.py` + `eval/scorer.py` + `lib/report.py` (HTML) + `lib/trajectory.py` + `lib/cost.py`.
- [x] `tests/test_pipeline.py` — 22 passing, no API key needed.
- [x] `app.py` — local dashboard (paste strategy → validate).
- [x] README / REPRODUCTION / SPEC / CHANGELOG written.
- [ ] **API key → real eval run** (`eval.harness --which both`) → fill headline numbers in README/CHANGELOG, commit `results/reference-run/`.
- [ ] Iteration 4 experiment (withhold in-sample report from decide) — run A/B, log result.
- [ ] 5-min video.
- [ ] Final submission on HackerEarth (deadline Aug 31, 18:00 UTC).

## Decision log
| Date | Decision | Why |
|---|---|---|
| 2026-08-28 | Language = Python | Every prior project is Python; on the supported list; fastest for an eval harness + agent |
| 2026-08-28 | Repo lives at `C:\Cotton World Live Dashboard\Hackathon` as its **own** git repo (nested; add `/Hackathon/` to the parent repo's .gitignore so the work repo never tracks it) | User's chosen location |
| 2026-08-28 | Build agnostic machinery first (harness, trajectory capture, cost tracker, doc templates) | Reusable regardless of final domain; no wasted time |

## Rubric (score /100) — where the points are
| Criterion | Weight | Note |
|---|---|---|
| Agent Solution & Engineering | 30 | #1 tie-break. Orchestration/tools/verification/memory — each justified |
| End-to-End Quality | 20 | Output must read as senior-engineer work, not an AI draft |
| Measured Improvement | 15 | 10+ cases, baseline vs advanced, changelog tied to evidence |
| Reproducibility | 15 | #2 tie-break. **Hard gate** — must run from clean env |
| Problem & User Value | 15 | Clearly defined user + real bottleneck |
| Hot Take / Insights | 5 | One real agent failure mode → one transferable lesson |

## Day plan
- **Day 0 (28th):** eligibility ruling · register · pull problem PDF · confirm domain · scaffold (this repo) — DONE for scaffold.
- **Day 1 (29th):** baseline + advanced v1 + 12–15 labelled cases · first full eval run · first comparison table · start changelog.
- **Day 2 (30th):** 3–5 iteration cycles (run eval → read failures → one targeted change → re-run → log with evidence) · lock advanced solution · draft README + reproduction guide.
- **Day 3 (31st):** clean-room reproduce test · finalize docs + changelog + hot take · record + edit 5-min video · assemble trajectories · **submit 3–4h before 18:00 UTC**.

## Submission package checklist
- [ ] Full solution code + `IMPROVEMENT_CHANGELOG.md` + hot take
- [ ] `REPRODUCTION.md` — clean-env setup, exact commands for solution/baseline/eval, data, expected output, versions, runtime, cost
- [ ] Solution video ≤5 min
- [ ] Agent trajectories for every agent used
- [ ] Disclosure of coding tools used
