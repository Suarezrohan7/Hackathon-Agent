"""Evaluation harness — runs baseline and/or advanced on the same cases and
emits the headline comparison table.

A case is a folder under --cases containing:
    meta.yaml         {id, title, notes, human_minutes_baseline?, human_minutes_advanced?}
    ground_truth.json  the correct answer (shape understood by eval.scorer)
    ...                any input files the solution reads

baseline/run.py and advanced/run.py must each expose:
    def run(case_dir: pathlib.Path, ctx: RunContext) -> dict   # the prediction

Run:
    python -m eval.harness --which both --cases cases/
    python -m eval.harness --which advanced --only case-03
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from eval.scorer import PRIMARY_METRIC, score
from lib.cost import CostTracker
from lib.report import render as render_html
from lib.trajectory import Trajectory


@dataclass
class RunContext:
    """Passed into every solution run: cost + trajectory wiring."""
    case_id: str
    which: str            # "baseline" | "advanced"
    tracker: CostTracker
    traj_dir: Path

    def trajectory(self) -> Trajectory:
        return Trajectory(run_id=f"{self.which}/{self.case_id}", out_dir=self.traj_dir)


def discover_cases(cases_dir: Path, only: str | None) -> list[Path]:
    dirs = sorted(p for p in cases_dir.iterdir() if p.is_dir() and (p / "meta.yaml").exists())
    if only:
        dirs = [p for p in dirs if p.name == only or yaml.safe_load((p / "meta.yaml").read_text()).get("id") == only]
    return dirs


def run_one(mod, case_dir: Path, which: str, tracker: CostTracker, traj_dir: Path) -> dict[str, Any]:
    meta = yaml.safe_load((case_dir / "meta.yaml").read_text(encoding="utf-8"))
    gt = json.loads((case_dir / "ground_truth.json").read_text(encoding="utf-8"))
    ctx = RunContext(case_id=meta.get("id", case_dir.name), which=which, tracker=tracker, traj_dir=traj_dir)
    t0 = time.time()
    err = None
    try:
        pred = mod.run(case_dir, ctx)
    except Exception:
        pred, err = {}, traceback.format_exc()
    elapsed = round(time.time() - t0, 2)
    sc = score(pred, gt) if not err else {"error": True}
    return {
        "case": meta.get("id", case_dir.name),
        "title": meta.get("title", ""),
        "which": which,
        "elapsed_s": elapsed,
        "human_minutes": meta.get(f"human_minutes_{which}"),
        "prediction": pred,
        "ground_truth": gt,
        "score": sc,
        "error": err,
    }


def _mean(xs: list[float]) -> float | None:
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.fmean(xs), 4) if xs else None


def aggregate(rows: list[dict[str, Any]], which: str, tracker_summary: dict) -> dict[str, Any]:
    mine = [r for r in rows if r["which"] == which]
    n = len(mine) or 1
    primary = _mean([r["score"].get(PRIMARY_METRIC) for r in mine])
    return {
        "which": which,
        "n_cases": len(mine),
        "n_errors": sum(1 for r in mine if r["error"]),
        f"primary[{PRIMARY_METRIC}]": primary,
        "precision": _mean([r["score"].get("precision") for r in mine]),
        "recall": _mean([r["score"].get("recall") for r in mine]),
        "f1": _mean([r["score"].get("f1") for r in mine]),
        "avg_runtime_s": _mean([r["elapsed_s"] for r in mine]),
        "avg_human_minutes": _mean([r["human_minutes"] for r in mine]),
        "usd_total": tracker_summary.get("usd"),
        "usd_per_case": round((tracker_summary.get("usd") or 0) / n, 4),
    }


def write_report(out_dir: Path, rows: list[dict], aggs: dict[str, dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw.json").write_text(json.dumps({"rows": rows, "aggregates": aggs}, indent=2, default=str), encoding="utf-8")

    b, a = aggs.get("baseline"), aggs.get("advanced")
    lines = [f"# Eval run — {datetime.now(timezone.utc).isoformat(timespec='seconds')}", ""]

    def cell(d, k):
        return "–" if not d or d.get(k) is None else d[k]

    if b or a:
        lines += ["## Headline", "", "| Metric | Baseline | Advanced | Change |", "|---|---|---|---|"]
        for label, key in [
            (f"Primary ({PRIMARY_METRIC})", f"primary[{PRIMARY_METRIC}]"),
            ("Precision", "precision"), ("Recall", "recall"), ("F1", "f1"),
            ("Avg runtime (s)", "avg_runtime_s"),
            ("Avg human min/task", "avg_human_minutes"),
            ("USD per case", "usd_per_case"),
            ("Errors", "n_errors"),
        ]:
            bv, av = cell(b, key), cell(a, key)
            chg = ""
            if isinstance(bv, (int, float)) and isinstance(av, (int, float)):
                chg = f"{av - bv:+.4g}"
            lines.append(f"| {label} | {bv} | {av} | {chg} |")
        lines.append("")

    lines += ["## Per-case", "", "| Case | Which | Primary | F1 | Runtime s | Error |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| {case} | {which} | {p} | {f1} | {t} | {e} |".format(
            case=r["case"], which=r["which"],
            p=r["score"].get(PRIMARY_METRIC, "–"),
            f1=r["score"].get("f1", "–"),
            t=r["elapsed_s"],
            e="yes" if r["error"] else "",
        ))
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    try:
        from lib.llm import MODEL
        html_path = render_html(out_dir, rows, aggs,
                                {"title": "Strategy Validation Agent", "model": MODEL})
    except Exception as e:  # a report failure must not lose the run
        html_path = f"(report skipped: {e})"

    print("\n".join(lines))
    print(f"\nwrote {out_dir/'summary.md'}, {out_dir/'raw.json'}, {html_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["baseline", "advanced", "both"], default="both")
    ap.add_argument("--cases", default="cases")
    ap.add_argument("--only", default=None, help="run a single case by id")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    which_list = ["baseline", "advanced"] if args.which == "both" else [args.which]
    cases = discover_cases(Path(args.cases), args.only)
    if not cases:
        raise SystemExit(f"no cases found under {args.cases!r}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out or f"results/run-{stamp}")
    traj_dir = Path("trajectories") / f"run-{stamp}"

    rows: list[dict] = []
    aggs: dict[str, dict] = {}
    for which in which_list:
        mod = importlib.import_module(f"{which}.run")
        tracker = CostTracker()
        for case_dir in cases:
            print(f"[{which}] {case_dir.name} …")
            rows.append(run_one(mod, case_dir, which, tracker, traj_dir))
        aggs[which] = aggregate(rows, which, tracker.summary())
        aggs[which]["cost_detail"] = tracker.summary()

    write_report(out_dir, rows, aggs)


if __name__ == "__main__":
    main()
