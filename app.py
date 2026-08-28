"""Local dashboard for the Strategy Validation Agent.

    python app.py         ->  http://127.0.0.1:7600

Paste a strategy (must define `signal(df, **params)`, `PARAMS`, `PARAM_GRID`),
pick a dataset, and watch the agent profile it, run its checks, and return an
evidence-backed verdict. Same engine as `eval/harness.py` — nothing new here,
just a human-facing front door. Read-only: it never places a trade.
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template_string, request

from advanced.run import run as advanced_run
from cases.generate import GENS
from lib.backtest import backtest
from lib.cost import CostTracker
from lib.llm import MODEL, _mock
from lib.trajectory import Trajectory

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "results" / "app"
RUNS.mkdir(parents=True, exist_ok=True)
CASES = sorted(p.name for p in (ROOT / "cases").glob("case-*") if p.is_dir())

EXAMPLE = '''import numpy as np

def signal(df, fast=10, slow=50):
    f = df["close"].rolling(int(fast)).mean()
    s = df["close"].rolling(int(slow)).mean()
    return np.sign(f - s).fillna(0.0)

PARAMS = {"fast": 10, "slow": 50}
PARAM_GRID = {"fast": [5, 10, 20, 40], "slow": [30, 50, 100, 150]}
'''


class _Ctx:
    def __init__(self, rid: str):
        self.case_id, self.which = rid, "advanced"
        self.tracker = CostTracker()
        self.traj_dir = RUNS / rid

    def trajectory(self) -> Trajectory:
        return Trajectory(run_id=f"app/{self.case_id}", out_dir=self.traj_dir)


def _load(cdir: Path):
    spec = importlib.util.spec_from_file_location(f"s_{cdir.name}", cdir / "strategy.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


@app.get("/")
def index():
    return render_template_string(PAGE, example=EXAMPLE, cases=CASES, model=MODEL, mock=_mock())


@app.get("/api/sample/<case_id>")
def sample(case_id: str):
    p = ROOT / "cases" / case_id / "strategy.py"
    if case_id not in CASES or not p.exists():
        return jsonify(error="unknown case"), 404
    return jsonify(strategy=p.read_text(encoding="utf-8"))


@app.post("/api/validate")
def validate():
    body = request.get_json(force=True)
    code = (body.get("strategy") or "")[:20000]
    dataset = body.get("dataset") or f"sample:{CASES[0]}"
    rid = uuid.uuid4().hex[:10]
    cdir = RUNS / rid
    cdir.mkdir(parents=True, exist_ok=True)

    try:
        (cdir / "strategy.py").write_text(code, encoding="utf-8")
        mod = _load(cdir)
        params = dict(getattr(mod, "PARAMS", {}))
        grid = dict(getattr(mod, "PARAM_GRID", {}))
        if not callable(getattr(mod, "signal", None)):
            raise ValueError("strategy.py must define signal(df, **params)")

        if dataset.startswith("sample:"):
            src = ROOT / "cases" / dataset.split(":", 1)[1]
            is_df = pd.read_csv(src / "data.csv")
            oos_df = pd.read_csv(src / "data_oos.csv")
        elif dataset.startswith("gen:"):
            name = dataset.split(":", 1)[1]
            if name not in GENS:
                raise ValueError(f"unknown generator {name}")
            is_df = GENS[name](1000, 20260828)
            oos_df = GENS[name](1000, 20260828 + 500)
        else:
            raise ValueError("dataset must be sample:<case> or gen:<process>")

        is_df.to_csv(cdir / "data.csv", index=False)
        oos_df.to_csv(cdir / "data_oos.csv", index=False)
        b = backtest(is_df, mod.signal(is_df, **params), periods_per_year=252)
        (cdir / "backtest_report.json").write_text(json.dumps({
            "strategy_module": "strategy.py", "params": params, "param_grid": grid,
            "periods_per_year": 252, "data_file": "data.csv", "oos_data_file": "data_oos.csv",
            "in_sample": {k: b[k] for k in ("sharpe", "cagr", "max_drawdown", "win_rate",
                                            "n_trades", "total_return", "exposure")},
        }, indent=2), encoding="utf-8")

        ctx = _Ctx(rid)
        pred, detail = advanced_run(cdir, ctx, return_detail=True)
        traj_md = Path(detail["trajectory"]["trajectory_md"]).read_text(encoding="utf-8")
        return jsonify(ok=True, verdict=pred, profile=detail["profile"], digest=detail["digest"],
                       trajectory=traj_md, cost=ctx.tracker.summary(), mock=_mock())
    except Exception as e:
        return jsonify(ok=False, error=f"{type(e).__name__}: {e}"), 400


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Strategy Validation Agent</title>
<style>
:root{--bg:#0b0d12;--panel:#12151c;--panel2:#171b24;--line:#232833;--txt:#e7e9ee;--mut:#8b93a3;
--grn:#3fb37f;--red:#e5544b;--amb:#e0a13c;--accent:#5b8def}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font:14px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:34px 26px 90px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:22px}
.mock{background:#3a2c12;border:1px solid #6b5320;color:var(--amb);padding:8px 12px;border-radius:8px;
font-size:13px;margin-bottom:18px}
.row{display:grid;grid-template-columns:1.3fr .7fr;gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px}
label{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:0 0 6px}
textarea{width:100%;height:300px;background:#0e1118;color:var(--txt);border:1px solid var(--line);
border-radius:8px;padding:12px;font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;resize:vertical}
select,button{font:13px inherit;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--txt);padding:9px 12px}
button{background:var(--accent);border-color:var(--accent);color:#fff;cursor:pointer;font-weight:600}
button:disabled{opacity:.5;cursor:wait}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:13px;border:1px solid var(--line)}
.v-edge{color:var(--grn);border-color:#1f5c44}.v-overfit{color:var(--amb);border-color:#6b5320}
.v-no_edge{color:var(--red);border-color:#6e2b27}
.tag{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:1px 7px;margin:2px 4px 2px 0;font-size:12px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;margin-top:6px}
td,th{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left}td.num{text-align:right}
th{color:var(--mut);font-weight:500;font-size:12px}
pre{background:#0e1118;border:1px solid var(--line);border-radius:8px;padding:12px;max-height:360px;overflow:auto;font-size:12px;white-space:pre-wrap}
.err{color:var(--red)}
.sectlabel{margin:26px 0 6px;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--mut)}
</style></head><body><div class="wrap">
<h1>Strategy Validation Agent</h1>
<div class="sub">Paste a backtested strategy &rarr; the agent profiles it, runs robustness checks, and returns an evidence-backed verdict. Model <code>{{model}}</code>.</div>
{% if mock %}<div class="mock">No <code>ANTHROPIC_API_KEY</code> set &mdash; the deterministic checks still run and are shown, but the verdict is mocked. Add a key to <code>.env</code> for real verdicts.</div>{% endif %}

<div class="row">
  <div class="card">
    <label>strategy.py &mdash; must define <code>signal(df, **params)</code>, <code>PARAMS</code>, <code>PARAM_GRID</code></label>
    <textarea id="code">{{example}}</textarea>
    <div class="controls">
      <select id="sample"><option value="">Load a sample case&hellip;</option>
        {% for c in cases %}<option value="{{c}}">{{c}}</option>{% endfor %}</select>
      <select id="dataset">
        <optgroup label="Bundled case data">
          {% for c in cases %}<option value="sample:{{c}}">{{c}}</option>{% endfor %}
        </optgroup>
        <optgroup label="Fresh synthetic">
          <option value="gen:momentum">momentum process</option>
          <option value="gen:meanrev">mean-reverting process</option>
          <option value="gen:trend">trending process</option>
          <option value="gen:random">random walk</option>
        </optgroup>
      </select>
      <button id="go">Validate</button>
    </div>
  </div>

  <div class="card" id="out"><div class="sub">Results appear here.</div></div>
</div>

<div class="sectlabel">Agent trajectory</div>
<pre id="traj">&mdash;</pre>
</div>
<script>
const $=s=>document.querySelector(s);
$("#sample").onchange=async e=>{const c=e.target.value;if(!c)return;
  const r=await fetch("/api/sample/"+c);const j=await r.json();if(j.strategy)$("#code").value=j.strategy;};
$("#go").onclick=async()=>{
  const btn=$("#go");btn.disabled=true;btn.textContent="Running…";
  $("#out").innerHTML='<div class="sub">Running checks…</div>';
  try{
    const r=await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({strategy:$("#code").value,dataset:$("#dataset").value})});
    const j=await r.json();
    if(!j.ok){$("#out").innerHTML='<div class="err">'+ (j.error||"error") +'</div>';return;}
    const v=(j.verdict.verdict||"?").toLowerCase();
    const fnd=(j.verdict.findings||[]).map(f=>'<span class="tag">'+(f.id||f)+'</span>').join("")||"–";
    const d=j.digest;
    const rows=Object.entries(d).filter(([k])=>k!=="checks_run")
      .map(([k,val])=>'<tr><td>'+k+'</td><td class="num">'+ (val===null?"–":Array.isArray(val)?val.join(", "):val) +'</td></tr>').join("");
    $("#out").innerHTML=
      '<label>Verdict</label><div><span class="pill v-'+v+'">'+v+'</span></div>'+
      '<p style="color:var(--mut);margin:10px 0 4px">'+(j.verdict.rationale||"")+'</p>'+
      '<label style="margin-top:10px">Findings</label><div>'+fnd+'</div>'+
      '<label style="margin-top:14px">Evidence digest</label><table>'+rows+'</table>'+
      '<div class="sub" style="margin-top:10px">checks run: '+(d.checks_run||[]).join(", ")+
      ' &middot; cost $'+(j.cost.usd||0).toFixed(4)+(j.mock?" (mocked)":"")+'</div>';
    $("#traj").textContent=j.trajectory||"–";
  }catch(e){$("#out").innerHTML='<div class="err">'+e+'</div>';}
  finally{btn.disabled=false;btn.textContent="Validate";}
};
</script></body></html>"""


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7600, debug=False)
