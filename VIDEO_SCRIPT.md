# Solution Video — how to record it

The whole demo is one self-contained script: `demo.py`. It runs the agent's real
checks in-process (no API key, no cost), styled with panels and colour. You record
**one terminal window** while it plays. ~3.5–4.5 min.

## Setup (2 min, once)

1. Use **Windows Terminal** or the **VS Code integrated terminal** — both do UTF-8 +
   colour. Maximise it. Dark theme. Bump the font size (Ctrl+`+`) so it's readable
   in the recording.
2. ```
   cd "C:\Cotton World Live Dashboard\Hackathon"
   .venv\Scripts\activate
   ```
3. Recorder: **OBS** (Display Capture → your recording monitor) or **Snipping Tool**
   (`Win+Shift+S` → video icon → box around the terminal).
4. For narration room, set a slower pace first:
   ```
   set DEMO_SPEED=2
   ```
   (Leave it unset for the default ~3.5 min pace.)

## Record

1. Start the recorder.
2. Click into the terminal, run:
   ```
   python demo.py
   ```
3. Let it play. Don't touch anything. It ends on the takeaway card.
4. Stop the recorder. Trim the dead second at each end in any editor.

## What each beat shows — and what to say over it

| Beat | On screen | Narration (optional — captions also fine) |
|---|---|---|
| Title | name + one-line question | "Is this backtest a real edge, or overfit, or luck?" |
| 1 · Problem | the IN/OUT contract panel | "A good backtest is the default when you try many strategies. Most are curve-fit or lucky." |
| 2 · Baseline | `baseline/run.py` syntax-highlighted | "The simple version: one model call, no data. Gets **5 of 13** right." |
| 3 · Live validation | the 7-check panel filling in with real numbers, then VERDICT + HUMAN GATE | "The agent runs seven checks on data the strategy never saw — out-of-sample Sharpe 1.75, walk-forward all positive, survives costs, no leak. Verdict: **edge**. And it stops for a human before anything is called tradable." |
| 4 · Scorecard | baseline vs agent table | "Same 13 strategies. Baseline 38%. Agent 100%. Zero errors." |
| 5 · The change | the 38→100 callout | "v1 let the model make the final call — 38%, no better than baseline. It gathered the right evidence and talked itself out of it. I moved the decision to a rule over the verified evidence. That's the jump." |
| 6 · Rigor | the 3-point panel | "The test labels aren't assumed — the generator proves each one. One experiment removed: a Monte-Carlo test whose signal came out backwards. 22 tests run with no API key." |
| 7 · Takeaway | final card + hot take | "An agent can gather the right evidence and still reach the wrong answer. The fix wasn't a better prompt — it was not letting the model cast the vote." |

## Then

- Upload the mp4 with your HackerEarth submission.
- In the submission text: repo URL, "reproduction steps in `REPRODUCTION.md`", "built with Claude Code".
- Delete this file and `demo.py` before the final push only if you want them out of the repo — leaving them in is fine and shows the work.
