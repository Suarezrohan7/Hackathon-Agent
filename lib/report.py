"""Self-contained dark-theme HTML report for an eval run. No external assets."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_CSS = """
:root{--bg:#0b0d12;--panel:#12151c;--panel2:#171b24;--line:#232833;--txt:#e7e9ee;
--mut:#8b93a3;--grn:#3fb37f;--red:#e5544b;--amb:#e0a13c;--accent:#5b8def}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:40px 28px 80px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);font-size:13px;margin-bottom:28px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.card h3{margin:0 0 12px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
.big{font-variant-numeric:tabular-nums;font-size:30px;font-weight:600}
.delta{font-size:13px;margin-left:8px}.up{color:var(--grn)}.down{color:var(--red)}
table{width:100%;border-collapse:collapse;margin-top:10px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
td.num{text-align:right}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--line)}
.ok{color:var(--grn);border-color:#1f5c44}.bad{color:var(--red);border-color:#6e2b27}
.tag{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:6px;
padding:1px 6px;margin:1px 3px 1px 0;font-size:12px;color:var(--mut)}
.sectlabel{margin:34px 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
.bar{height:6px;background:var(--panel2);border-radius:3px;overflow:hidden;margin-top:8px}
.bar>i{display:block;height:100%;background:var(--accent)}
"""


def _fmt(v: Any) -> str:
    if v is None:
        return "&ndash;"
    if isinstance(v, float):
        return f"{v:.3g}"
    return html.escape(str(v))


def _delta(b: Any, a: Any) -> str:
    if not isinstance(b, (int, float)) or not isinstance(a, (int, float)):
        return ""
    d = a - b
    cls = "up" if d >= 0 else "down"
    return f'<span class="delta {cls}">{d:+.3g}</span>'


def render(out_dir: Path, rows: list[dict], aggs: dict[str, dict], meta: dict) -> Path:
    b, a = aggs.get("baseline"), aggs.get("advanced")
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def kpi(title: str, key: str, pct: bool = False) -> str:
        bv = (b or {}).get(key)
        av = (a or {}).get(key)
        show = av if av is not None else bv
        txt = f"{show*100:.0f}%" if (pct and isinstance(show, (int, float))) else _fmt(show)
        return f'<div class="card"><h3>{html.escape(title)}</h3><div class="big">{txt}{_delta(bv, av)}</div></div>'

    cards = "".join([
        kpi("Verdict accuracy (advanced)", "primary[verdict_correct]", pct=True),
        kpi("Findings F1 (advanced)", "f1"),
        kpi("USD per case", "usd_per_case"),
        kpi("Avg human min / task", "avg_human_minutes"),
    ])

    head_rows = ""
    for label, key, pct in [
        ("Verdict accuracy", "primary[verdict_correct]", True),
        ("Findings precision", "precision", False),
        ("Findings recall", "recall", False),
        ("Findings F1", "f1", False),
        ("Avg runtime (s)", "avg_runtime_s", False),
        ("USD / case", "usd_per_case", False),
        ("Errors", "n_errors", False),
    ]:
        bv, av = (b or {}).get(key), (a or {}).get(key)
        fmt = (lambda x: f"{x*100:.0f}%" if (pct and isinstance(x, (int, float))) else _fmt(x))
        head_rows += (f"<tr><td>{label}</td><td class='num'>{fmt(bv)}</td>"
                      f"<td class='num'>{fmt(av)}</td><td class='num'>{_delta(bv, av)}</td></tr>")

    by_case: dict[str, dict] = {}
    for r in rows:
        c = by_case.setdefault(r["case"], {"title": r["title"]})
        c[r["which"]] = r

    case_rows = ""
    for cid, c in by_case.items():
        tv = (c.get("advanced") or c.get("baseline") or {}).get("score", {}).get("true_verdict", "?")
        def cell(which):
            r = c.get(which)
            if not r:
                return "<td>&ndash;</td>"
            sc = r["score"]
            good = sc.get("verdict_correct") == 1.0
            pill = "ok" if good else "bad"
            return f'<td><span class="pill {pill}">{_fmt(sc.get("pred_verdict"))}</span></td>'
        findings = ""
        radv = c.get("advanced")
        if radv:
            for f in radv["prediction"].get("findings", []) or []:
                fid = f.get("id") if isinstance(f, dict) else f
                findings += f'<span class="tag">{html.escape(str(fid))}</span>'
        case_rows += (f"<tr><td><code>{html.escape(cid)}</code><br><span style='color:var(--mut)'>"
                      f"{html.escape(c['title'])}</span></td><td>{html.escape(str(tv))}</td>"
                      f"{cell('baseline')}{cell('advanced')}<td>{findings or '&ndash;'}</td></tr>")

    acc = (a or {}).get("primary[verdict_correct]") or 0
    body = f"""
<div class="wrap">
  <h1>{html.escape(meta.get('title', 'Strategy Validation Agent'))} &mdash; eval report</h1>
  <div class="sub">run {html.escape(ts)} &nbsp;&middot;&nbsp; model <code>{html.escape(meta.get('model', '?'))}</code>
    &nbsp;&middot;&nbsp; {len(by_case)} cases</div>
  <div class="grid">{cards}</div>

  <div class="sectlabel">Baseline vs advanced</div>
  <table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">Advanced</th><th class="num">&Delta;</th></tr></thead>
  <tbody>{head_rows}</tbody></table>
  <div class="bar"><i style="width:{acc*100:.0f}%"></i></div>

  <div class="sectlabel">Per case</div>
  <table><thead><tr><th>Case</th><th>True</th><th>Baseline</th><th>Advanced</th><th>Advanced findings</th></tr></thead>
  <tbody>{case_rows}</tbody></table>

  <div class="sectlabel">Artifacts</div>
  <div class="sub"><code>summary.md</code>, <code>raw.json</code> in this folder &middot;
    step-by-step agent trajectories under <code>trajectories/</code></div>
</div>
"""
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(meta.get('title','eval'))}</title><style>{_CSS}</style></head><body>{body}</body></html>"
    p = out_dir / "report.html"
    p.write_text(doc, encoding="utf-8")
    return p
