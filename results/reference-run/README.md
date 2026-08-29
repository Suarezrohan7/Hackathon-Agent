# reference-run/

A real `python -m eval.harness --which both` run from the author's machine, so a
reviewer can see the expected output before spending a token, then reproduce it.

| Metric | Baseline | Advanced |
|---|---|---|
| Verdict accuracy (13 cases) | 0.385 (5/13) | 1.000 (13/13) |
| Findings precision / recall / F1 | 0.27 / 0.58 / 0.34 | 0.49 / 0.92 / 0.61 |
| Errors | 0 | 0 |
| USD per case | ~$0.011 | ~$0.050 |
| Runtime per case | ~9 s | ~56 s |

Files: `summary.md` (the table above + per-case), `raw.json` (every prediction, score,
cost), `report.html` (open in a browser). Per-case agent traces: `../../trajectories/reference/`.

Model: `claude-sonnet-5`. Run date: 2026-08-28. Small wording differences in the
`rationale` field are expected between runs; `verdict` and `findings` are stable.
