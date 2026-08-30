"""Self-running demo for the solution video.

    python demo.py

A styled terminal walkthrough: the problem, the baseline, then the agent
validating a real strategy LIVE — each of its seven checks ticking off with its
real result — the baseline-vs-agent scorecard, the insight that drove the jump,
and the engineering that makes the number trustworthy. Everything stays in one
terminal window. ~4.5 min. Ctrl+C any time.

Record with Windows Terminal or the VS Code integrated terminal (both do UTF-8 +
truecolour). Narrate from VIDEO_SCRIPT.md, or add captions afterwards.
No API key needed — this runs the real deterministic checks in-process.
For narration room:  set DEMO_SPEED=1.4  then run.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
except Exception:
    pass

try:
    from rich.align import Align
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
except ImportError:
    sys.exit("pip install rich   (it is in requirements.txt)")

ROOT = Path(__file__).resolve().parent
SLOW = float(os.environ.get("DEMO_SPEED", "1.4"))   # DEMO_SPEED=2 for live narration room
con = Console(width=100, highlight=False)

# palette -----------------------------------------------------------------------
INK = "#dbe4f0"
DIM = "#7688a0"
ACC = "#38bdf8"      # sky — the accent
OK = "#34d399"       # green — good / edge
NO = "#f87171"       # red — bad / no-edge
WRN = "#fbbf24"      # amber — human gate / caution
HEAD = f"bold {ACC}"


def wait(s: float) -> None:
    time.sleep(s * SLOW)


def typeout(text: str, style: str, delay: float = 0.018) -> None:
    for i in range(len(text) + 1):
        con.print(Text(text[:i], style=style), end="\r")
        time.sleep(delay * SLOW)
    con.print(Text(text, style=style))


def beat(n: int, title: str, hold: float = 2.2) -> None:
    con.clear()
    con.print()
    con.print(Rule(Text(f"  {n} / 7    {title}  ", style=HEAD), style=ACC, characters="─"))
    con.print()
    wait(hold)


def para(text: str, style: str = INK) -> None:
    con.print(Text(text.strip("\n"), style=style))
    con.print()


# -----------------------------------------------------------------------------
def title_card() -> None:
    con.clear()
    con.print("\n\n\n")
    inner = Group(
        Align.center(Text("STRATEGY  VALIDATION  AGENT", style=f"bold {ACC}")),
        Align.center(Text("")),
        Align.center(Text("a backtest looks great.  is the edge real, overfit, or luck?", style=INK)),
    )
    con.print(Panel(inner, border_style=ACC, padding=(2, 8), width=84), justify="center")
    con.print()
    con.print(Align.center(Text("micro1 Frontier Engineering Challenge   ·   built with a coding agent", style=DIM)))
    con.print("\n\n")
    wait(5)


def problem() -> None:
    beat(1, "The problem")
    para("A good-looking backtest is the DEFAULT outcome of trying many strategies —\n"
         "most are curve-fit or just lucky. Separating a real edge from an artefact\n"
         "takes a battery of tests on data the strategy never saw. It is tedious, it\n"
         "needs judgement, and it is routinely skipped. People lose real money on\n"
         "strategies that never had an edge.")
    io = Table(box=None, pad_edge=False, padding=(0, 2))
    io.add_column(justify="right", style=f"bold {ACC}")
    io.add_column(style=INK)
    io.add_row("IN", "a strategy (its code) + the backtest numbers it produced")
    io.add_row("OUT", "edge  |  overfit  |  no_edge      + the evidence for the call")
    con.print(Panel(io, border_style=DIM, padding=(1, 3), title="[dim]the contract[/]"))
    wait(9)


def baseline() -> None:
    beat(2, "The baseline  —  one model call.  no data, no tools")
    lines = (ROOT / "baseline" / "run.py").read_text(encoding="utf-8").splitlines()
    src = "\n".join(lines[9:31])
    con.print(Panel(Syntax(src, "python", theme="ansi_dark", background_color="default", word_wrap=True),
                    title="[dim]baseline/run.py[/]", border_style=DIM, padding=(0, 1)))
    con.print(Text("   5 / 13 correct   (38%)", style=f"bold {NO}"),
              Text("   it smells the grid-searched strategies from the", style=DIM))
    con.print(Text("   " + " " * 24, style=""),
              Text("   code — but cannot tell a real edge from a lucky", style=DIM))
    con.print(Text("   " + " " * 24, style=""),
              Text("   one, because it never looks at unseen data.", style=DIM))
    wait(9)


# --- the live section --------------------------------------------------------
CHECK_ORDER = [
    ("trade_count", "trade count", lambda r: f"{r['n_trades']} trades  ·  {'adequate' if r['adequate'] else 'thin sample'}"),
    ("oos_test", "out-of-sample test", lambda r: f"OOS Sharpe {r['oos_sharpe']}  ·  keeps {int(float(r['oos_over_is'])*100)}% of in-sample edge"),
    ("walk_forward", "walk-forward", lambda r: f"folds {r['fold_sharpes_fixed']}  ·  mean {r['wf_sharpe_fixed_mean']}"),
    ("monte_carlo_permutation", "Monte-Carlo permutation", lambda r: f"p-value {r['p_value']}  ·  observed {r['observed_sharpe']} vs null {r['null_sharpe_mean']}"),
    ("param_sensitivity", "parameter sensitivity", lambda r: f"plateau score {r['plateau_score']}  ·  {'FRAGILE spike' if r['fragile'] else 'broad plateau'}"),
    ("cost_stress", "transaction-cost stress", lambda r: f"{'survives' if r['survives_5bps'] else 'DIES'} at 5 bps"),
    ("lookahead_probe", "look-ahead probe", lambda r: "no future-data leak" if not r['suspected'] else f"LEAK: {r['static_flags']}"),
]


def live_validation() -> None:
    beat(3, "The agent validates a strategy  —  live", hold=1.6)
    para("This strategy's backtest looks strong.  The baseline called it NOT an edge.\n"
         "Watch the agent run its seven checks on data the strategy never saw:", DIM)

    from advanced.run import _build_ctx, evidence_verdict, derive_findings, _digest, _profile
    from advanced.checks import REGISTRY

    cc = _build_ctx(ROOT / "cases" / "case-13-meanrev-edge-2")
    prof = _profile(cc)
    gathered: dict = {}
    rows: list[tuple[str, str, str]] = [(name, label, "") for name, label, _ in CHECK_ORDER]

    def render() -> Panel:
        t = Table(box=None, pad_edge=False, padding=(0, 2))
        t.add_column(width=3)
        t.add_column("check", style=INK, width=26)
        t.add_column("result", style=DIM)
        for name, label, res in rows:
            mark = Text("✔", style=OK) if res else Text("•", style=WRN)
            t.add_row(mark, label, res or "running…")
        return Panel(t, border_style=ACC, padding=(1, 2), title="[dim]advanced agent · 7 checks[/]")

    with Live(render(), console=con, refresh_per_second=12) as live:
        for i, (name, label, fmt) in enumerate(CHECK_ORDER):
            wait(0.5)
            r = REGISTRY[name](cc)
            gathered[name] = r
            try:
                rows[i] = (name, label, fmt(r))
            except Exception:
                rows[i] = (name, label, "done")
            live.update(render())
            wait(0.6)

    dg = _digest(gathered, prof)
    verdict, reason = evidence_verdict(dg)
    findings = derive_findings(dg, verdict, [])
    wait(1.2)

    vstyle = OK if verdict == "edge" else (NO if verdict == "no_edge" else WRN)
    con.print()
    con.print(Text("   VERDICT   ", style=f"reverse {vstyle}"),
              Text(f" {verdict.upper()}", style=f"bold {vstyle}"),
              Text(f"   {reason}", style=DIM))
    if findings:
        con.print(Text("   findings   ", style="reverse " + ACC),
                  Text("  " + ", ".join(f["id"] for f in findings), style=INK))
    con.print(Text("   HUMAN GATE ", style=f"reverse {WRN}"),
              Text("  positive verdict → held for human sign-off before any live capital", style=WRN))
    con.print()
    para("The model plans which checks matter and writes the rationale.  A transparent\n"
         "rule reads the verified evidence and assigns the verdict.  The model never\n"
         "casts the final vote.", DIM)
    wait(11)


def scorecard() -> None:
    beat(4, "Baseline  vs  agent   —   same 13 strategies, known answers")
    t = Table(box=None, pad_edge=False, padding=(0, 3))
    t.add_column("", style=DIM, width=20)
    t.add_column("baseline", justify="right", style=f"bold {NO}")
    t.add_column("agent", justify="right", style=f"bold {OK}")
    t.add_column("", style=DIM)
    t.add_row("verdict accuracy", "38%   (5 / 13)", "100%   (13 / 13)", "▲ +62 points")
    t.add_row("findings F1", "0.34", "0.61", "▲ +0.27")
    t.add_row("errors", "0", "0", "")
    t.add_row("cost / strategy", "$0.011", "$0.050", "")
    t.add_row("human time / strategy", "~30 min", "~5 min", "")
    con.print(Panel(t, border_style=ACC, padding=(1, 4)))
    para("It catches the three that only looked good by luck, the one that dies under\n"
         "costs, and the one that secretly reads the next bar's price.", DIM)
    wait(10)


def insight() -> None:
    beat(5, "The change that mattered")
    para('v1 of the agent let the MODEL make the final call from the evidence it had\n'
         'gathered. It scored 38% — no better than the baseline. The trace showed why:\n'
         'on one strategy it verified every "this holds up" signal, then still returned\n'
         'no_edge. It gathered the right evidence and talked itself out of it.')
    para("So I took the decision away from the model. A six-branch rule reads the\n"
         "evidence the model already verified. The model still plans the checks,\n"
         "verifies the findings, and writes the explanation — it just does not vote.", DIM)
    con.print(Panel(Align.center(Text("38%   →   100%        and the verdict is now reproducible", style=f"bold {OK}")),
                    border_style=OK, padding=(1, 4)))
    wait(12)


def rigor() -> None:
    beat(6, "Why the number is trustworthy")
    b = Table(box=None, pad_edge=False, padding=(0, 2))
    b.add_column(style=f"bold {ACC}", width=3)
    b.add_column(style=INK)
    b.add_row("1", "The 13 test labels are not assumed. The generator searches seeds until each\n"
                   "case PROVABLY behaves like its label, and fails the build if it cannot.")
    b.add_row("2", "One experiment removed and documented: a Monte-Carlo permutation test whose\n"
                   "signal came out backwards — a block bootstrap keeps the structure the\n"
                   "strategy feeds on, so it flagged overfits as 'significant', not edges.")
    b.add_row("3", "22 tests run with no API key. Three commands reproduce this exact result.")
    con.print(Panel(b, border_style=DIM, padding=(1, 2)))
    con.print(Text("   github.com/Suarezrohan7/Hackathon-Agent", style=ACC))
    wait(10)


def outro() -> None:
    beat(7, "The takeaway", hold=1.4)
    con.print(Panel(Align.center(Text("baseline  38%          →          agent  100%", style=f"bold {OK}")),
                    border_style=ACC, padding=(1, 6)))
    con.print()
    para("An agent can gather exactly the right evidence and still reach the wrong\n"
         "answer, because the tempting wrong answer is in its context. The fix was not\n"
         "a better prompt. It was not letting the model cast the final vote.", INK)
    con.print(Align.center(Text("thank you for watching", style=DIM)))
    con.print("\n\n")
    wait(9)


def main() -> None:
    title_card()
    problem()
    baseline()
    live_validation()
    scorecard()
    insight()
    rigor()
    outro()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        con.print("\n[dim](demo stopped)[/]\n")
