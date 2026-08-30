"""Strategy Validation Agent — local dashboard.

    python app.py         ->  http://127.0.0.1:7600

Paste a strategy, hit Validate, and watch the agent run its seven checks on
out-of-sample data and return an evidence-backed verdict. Read-only — it never
places a trade.

By default the checks + the evidence rule run in-process (deterministic, no API
key, no cost). Tick "use model for the write-up" to also have the LLM phrase the
rationale (needs ANTHROPIC_API_KEY; ~$0.03).
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from pathlib import Path

import pandas as pd
from flask import Flask, Response, jsonify, render_template_string, request

from advanced.checks import REGISTRY
from advanced.run import (_build_ctx, _digest, _profile, derive_findings,
                          evidence_verdict, run as advanced_run)
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

EXAMPLE = (ROOT / "cases" / "case-13-meanrev-edge-2" / "strategy.py").read_text(encoding="utf-8")

CHECK_META = [
    ("trade_count", "trade count",
     lambda r: f"{r['n_trades']} trades — {'adequate' if r['adequate'] else 'thin sample'}",
     lambda r: not r["adequate"]),
    ("oos_test", "out-of-sample test",
     lambda r: f"OOS Sharpe {r['oos_sharpe']} — keeps {int(float(r['oos_over_is'])*100)}% of in-sample edge"
               if r.get("oos_over_is") is not None else f"OOS Sharpe {r['oos_sharpe']}",
     lambda r: (r.get("oos_sharpe") or 0) < 0.3),
    ("walk_forward", "walk-forward",
     lambda r: f"folds {r['fold_sharpes_fixed']} — mean {r['wf_sharpe_fixed_mean']}",
     lambda r: (r.get("wf_sharpe_fixed_mean") or 0) < 0.2),
    ("monte_carlo_permutation", "Monte-Carlo permutation",
     lambda r: f"p-value {r['p_value']} — observed {r['observed_sharpe']} vs null {r['null_sharpe_mean']}",
     lambda r: False),
    ("param_sensitivity", "parameter sensitivity",
     lambda r: f"plateau score {r['plateau_score']} — {'FRAGILE spike' if r['fragile'] else 'broad plateau'}",
     lambda r: bool(r.get("fragile"))),
    ("cost_stress", "transaction-cost stress",
     lambda r: f"{'survives' if r['survives_5bps'] else 'DIES'} at 5 bps",
     lambda r: not r["survives_5bps"]),
    ("lookahead_probe", "look-ahead probe",
     lambda r: "no future-data leak" if not r["suspected"] else f"LEAK: {r['static_flags'] or 'lag-sweep collapse'}",
     lambda r: bool(r["suspected"])),
]


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


def _stage_case(code: str, dataset: str) -> Path:
    rid = uuid.uuid4().hex[:10]
    cdir = RUNS / rid
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "strategy.py").write_text(code, encoding="utf-8")
    mod = _load(cdir)
    params = dict(getattr(mod, "PARAMS", {}))
    grid = dict(getattr(mod, "PARAM_GRID", {}))
    if not callable(getattr(mod, "signal", None)):
        raise ValueError("strategy.py must define signal(df, **params)")

    if dataset.startswith("sample:"):
        src = ROOT / "cases" / dataset.split(":", 1)[1]
        is_df, oos_df = pd.read_csv(src / "data.csv"), pd.read_csv(src / "data_oos.csv")
    elif dataset.startswith("gen:"):
        name = dataset.split(":", 1)[1]
        if name not in GENS:
            raise ValueError(f"unknown generator {name}")
        is_df, oos_df = GENS[name](1000, 20260828), GENS[name](1000, 20260828 + 500)
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
    return cdir


@app.get("/")
def index():
    return render_template_string(PAGE, example=EXAMPLE, cases=CASES, model=MODEL, has_key=not _mock())


@app.get("/present")
def present():
    p = ROOT / "present.html"
    if not p.exists():
        return "present.html not found", 404
    return Response(p.read_text(encoding="utf-8"), mimetype="text/html")


@app.get("/api/sample/<case_id>")
def sample(case_id: str):
    p = ROOT / "cases" / case_id / "strategy.py"
    if case_id not in CASES or not p.exists():
        return jsonify(error="unknown case"), 404
    return jsonify(strategy=p.read_text(encoding="utf-8"))


@app.get("/api/scorecard")
def scorecard():
    raw = ROOT / "results" / "reference-run" / "raw.json"
    if not raw.exists():
        return jsonify(rows=[], baseline=None, advanced=None)
    data = json.loads(raw.read_text(encoding="utf-8"))
    by: dict[str, dict] = {}
    for r in data["rows"]:
        c = by.setdefault(r["case"], {"case": r["case"], "title": r["title"]})
        c[r["which"]] = {"pred": r["score"].get("pred_verdict"),
                        "ok": r["score"].get("verdict_correct") == 1.0,
                        "true": r["score"].get("true_verdict")}
    rows = list(by.values())
    agg = data.get("aggregates", {})
    return jsonify(rows=rows,
                   baseline=agg.get("baseline", {}).get("primary[verdict_correct]"),
                   advanced=agg.get("advanced", {}).get("primary[verdict_correct]"),
                   n=len(rows))


@app.post("/api/validate")
def validate():
    body = request.get_json(force=True)
    code = (body.get("strategy") or "")[:20000]
    dataset = body.get("dataset") or f"sample:{CASES[0]}"
    use_model = bool(body.get("use_model")) and not _mock()

    try:
        cdir = _stage_case(code, dataset)
        cc = _build_ctx(cdir)
        prof = _profile(cc)

        checks = []
        gathered: dict = {}
        for name, label, fmt, is_bad in CHECK_META:
            r = REGISTRY[name](cc)
            gathered[name] = r
            try:
                txt = fmt(r)
            except Exception:
                txt = "done"
            checks.append({"name": name, "label": label, "result": txt, "bad": bool(is_bad(r))})

        digest = _digest(gathered, prof)
        verdict, reason = evidence_verdict(digest)
        findings = derive_findings(digest, verdict, [])

        cost = 0.0
        rationale = reason
        traj_md = ""
        if use_model:
            ctx = _Ctx(cdir.name)
            pred, detail = advanced_run(cdir, ctx, return_detail=True)
            verdict = pred.get("verdict", verdict)
            rationale = pred.get("rationale", reason)
            findings = pred.get("findings", findings)
            cost = ctx.tracker.summary().get("usd", 0.0)
            traj_md = Path(detail["trajectory"]["trajectory_md"]).read_text(encoding="utf-8")

        return jsonify(ok=True, verdict=verdict, reason=rationale, findings=findings,
                       checks=checks, digest=digest, profile=prof,
                       in_sample=cc.report.get("in_sample", {}),
                       used_model=use_model, cost=round(cost, 4), trajectory=traj_md)
    except Exception as e:
        return jsonify(ok=False, error=f"{type(e).__name__}: {e}"), 400


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Strategy Validation Agent</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --bg:#0a0c10; --bg2:#0e1117; --panel:#12161d; --panel2:#161b23; --line:#232a35;
  --ink:#e6ebf2; --mut:#8b97a8; --faint:#5b6675;
  --acc:#38bdf8; --acc-dim:#0e2a3a;
  --ok:#34d399; --ok-dim:#08251a; --amb:#fbbf24; --amb-dim:#2a2109; --no:#f87171; --no-dim:#2a1010;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);
  font:15px/1.6 'IBM Plex Sans','Segoe UI',system-ui,sans-serif;
  background-image:radial-gradient(1200px 600px at 15% -10%, #10203010, transparent);}
.mono{font-family:'IBM Plex Mono',ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1120px;margin:0 auto;padding:30px 24px 90px}

header{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:6px}
h1{font-size:20px;font-weight:600;letter-spacing:-.01em}
.ribbon{margin-left:auto;font-family:'IBM Plex Mono',monospace;font-size:12.5px;color:var(--mut);
  border:1px solid var(--line);border-radius:999px;padding:5px 14px;background:var(--panel)}
.ribbon b.a{color:var(--no)} .ribbon b.b{color:var(--ok)}
.tagline{color:var(--mut);font-size:13.5px;margin-bottom:22px}

.grid{display:grid;grid-template-columns:420px 1fr;gap:18px;align-items:start}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}
.card h2{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);
  font-weight:600;margin-bottom:12px;font-family:'IBM Plex Mono',monospace}

label{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:0 0 7px}
textarea{width:100%;height:270px;background:var(--bg2);color:var(--ink);border:1px solid var(--line);
  border-radius:10px;padding:12px;font:12.5px/1.55 'IBM Plex Mono',ui-monospace,Consolas,monospace;resize:vertical}
select{width:100%;font:13px inherit;border-radius:9px;border:1px solid var(--line);
  background:var(--panel2);color:var(--ink);padding:9px 11px;margin-top:10px}
.shortcuts{display:flex;gap:8px;margin-top:12px}
.sc{flex:1;font:12.5px inherit;border:1px solid var(--line);background:var(--panel2);color:var(--mut);
  padding:9px 8px;border-radius:9px;cursor:pointer;text-align:center;transition:.15s}
.sc:hover{color:var(--ink);border-color:var(--acc)}
.go{width:100%;margin-top:12px;font:15px inherit;font-weight:600;border:0;border-radius:11px;
  background:linear-gradient(180deg,#4cc5fb,#1f9fe0);color:#04141d;padding:13px;cursor:pointer;
  box-shadow:0 6px 20px -8px #38bdf880}
.go:disabled{opacity:.55;cursor:wait;box-shadow:none}
.opt{display:flex;align-items:center;gap:8px;margin-top:12px;color:var(--mut);font-size:12.5px}
.opt input{accent-color:var(--acc)}

/* results */
#panel{min-height:340px;display:flex;flex-direction:column;gap:16px}
.placeholder{color:var(--faint);font-size:14px;padding:40px 0;text-align:center}

.checks{display:flex;flex-direction:column}
.chk{display:grid;grid-template-columns:26px 190px 1fr;gap:12px;align-items:center;
  padding:10px 4px;border-bottom:1px solid var(--line);opacity:0;transform:translateY(6px);
  transition:opacity .35s, transform .35s}
.chk.show{opacity:1;transform:none}
.chk:last-child{border-bottom:0}
.dot{width:18px;height:18px;border-radius:50%;border:2px solid var(--faint);position:relative}
.chk.done .dot{border-color:var(--ok);background:var(--ok-dim)}
.chk.done .dot::after{content:"";position:absolute;left:4px;top:1px;width:5px;height:9px;
  border:solid var(--ok);border-width:0 2px 2px 0;transform:rotate(45deg)}
.chk.bad .dot{border-color:var(--no);background:var(--no-dim)}
.chk.bad .dot::after{content:"!";color:var(--no);position:absolute;left:5px;top:-3px;font-weight:700}
.chk .lbl{color:var(--ink);font-weight:500}
.chk .res{color:var(--mut);font-family:'IBM Plex Mono',monospace;font-size:12.5px}
.chk.bad .res{color:var(--no)}
@keyframes spin{to{transform:rotate(360deg)}}
.chk.run .dot{border-top-color:var(--acc);animation:spin .8s linear infinite}

.verdict{border-radius:14px;padding:20px 22px;border:1px solid var(--line);display:flex;
  gap:20px;align-items:center;opacity:0;transform:scale(.98);transition:.4s}
.verdict.show{opacity:1;transform:none}
.verdict .big{font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:30px;letter-spacing:.02em;white-space:nowrap}
.verdict .why{color:var(--mut);font-size:13.5px}
.verdict.edge{background:var(--ok-dim);border-color:#12513a} .verdict.edge .big{color:var(--ok)}
.verdict.overfit{background:var(--amb-dim);border-color:#4a3a12} .verdict.overfit .big{color:var(--amb)}
.verdict.no_edge{background:var(--no-dim);border-color:#4a1c1c} .verdict.no_edge .big{color:var(--no)}

.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--mut);
  background:var(--panel2);border:1px solid var(--line);border-radius:7px;padding:3px 9px}
.gate{background:var(--amb-dim);border:1px solid #4a3a12;color:var(--amb);border-radius:10px;
  padding:10px 14px;font-size:13px}

.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.stat{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:11px 13px}
.stat .k{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint)}
.stat .v{font-family:'IBM Plex Mono',monospace;font-size:17px;margin-top:3px}
.meta{color:var(--faint);font-size:12px;font-family:'IBM Plex Mono',monospace}
.err{color:var(--no);font-family:'IBM Plex Mono',monospace;font-size:13px}

/* scorecard grid */
.scorecard{margin-top:26px}
.sgrid{display:flex;flex-direction:column;gap:8px}
.srow{display:flex;align-items:center;gap:10px}
.srow .who{width:74px;flex:0 0 74px;font-size:11px;color:var(--mut);font-family:'IBM Plex Mono',monospace;text-transform:uppercase}
.srow>span:last-child{display:inline-flex;flex-wrap:wrap;gap:6px}
.cell{display:inline-block;width:28px;height:28px;border-radius:7px;border:1px solid #1f2733;background:var(--panel2);
  transition:transform .4s cubic-bezier(.3,.7,.3,1), opacity .4s}
.cell.ok{background:var(--ok-dim);border-color:#12513a}
.cell.no{background:var(--no-dim);border-color:#4a1c1c}
.scap{color:var(--mut);font-size:12.5px;margin-top:10px}
.scap b.a{color:var(--no)} .scap b.b{color:var(--ok)}

details{margin-top:22px;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
summary{cursor:pointer;padding:12px 16px;color:var(--mut);font-size:12.5px;
  font-family:'IBM Plex Mono',monospace;letter-spacing:.06em;text-transform:uppercase}
details pre{margin:0;padding:14px 16px;border-top:1px solid var(--line);max-height:420px;overflow:auto;
  font:12px/1.5 'IBM Plex Mono',monospace;color:var(--mut);white-space:pre-wrap}
.autobadge{position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:20;
  font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--acc);border:1px solid #2b5f78;border-radius:999px;padding:6px 16px;
  background:rgba(56,189,248,.08);opacity:0;pointer-events:none;transition:opacity .4s}
body.autodemo .autobadge{opacity:1}
body.autodemo .go,body.autodemo .sc{pointer-events:none}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style></head><body><div class="autobadge">&#9654; auto demo</div><div class="wrap">

<header>
  <h1>Strategy Validation Agent</h1>
  <div class="ribbon">on 13 known strategies &nbsp;·&nbsp; baseline <b class="a" id="rb">–</b>
    &nbsp;→&nbsp; agent <b class="b" id="ra">–</b></div>
</header>
<div class="tagline">Paste a backtested strategy. The agent runs seven checks on data it never
  saw, then a transparent rule assigns the verdict &mdash; <span class="mono">edge</span> /
  <span class="mono">overfit</span> / <span class="mono">no_edge</span>.</div>

<div class="grid">
  <div class="card">
    <h2>strategy.py</h2>
    <label>must define signal(df, **params), PARAMS, PARAM_GRID</label>
    <textarea id="code">{{example}}</textarea>
    <div class="shortcuts">
      <div class="sc" data-case="case-13-meanrev-edge-2" data-ds="sample:case-13-meanrev-edge-2">▶ a real edge</div>
      <div class="sc" data-case="case-06-lookahead-bug" data-ds="sample:case-06-lookahead-bug">▶ a look-ahead fraud</div>
      <div class="sc" data-case="case-04-overfit-kitchensink" data-ds="sample:case-04-overfit-kitchensink">▶ an overfit</div>
    </div>
    <select id="dataset">
      <optgroup label="bundled case data (13, known answers)">
        {% for c in cases %}<option value="sample:{{c}}">{{c}}</option>{% endfor %}
      </optgroup>
      <optgroup label="fresh synthetic series">
        <option value="gen:momentum">momentum process</option>
        <option value="gen:meanrev">mean-reverting process</option>
        <option value="gen:trend">trending process</option>
        <option value="gen:random">random walk</option>
      </optgroup>
    </select>
    <label class="opt"><input type="checkbox" id="usemodel" {{ '' if has_key else 'disabled' }}>
      use the model to phrase the rationale{{ '' if has_key else ' (no ANTHROPIC_API_KEY)' }}</label>
    <button class="go" id="go">Validate</button>
  </div>

  <div class="card">
    <h2>result</h2>
    <div id="panel"><div class="placeholder">Load a strategy on the left and hit Validate.</div></div>
  </div>
</div>

<div class="scorecard card">
  <h2>baseline vs agent &mdash; same 13 strategies</h2>
  <div class="sgrid">
    <div class="srow"><span class="who">baseline</span><span id="row-b"></span></div>
    <div class="srow"><span class="who">agent</span><span id="row-a"></span></div>
  </div>
  <div class="scap" id="scap">loading&hellip;</div>
</div>

<details><summary>agent trajectory (model write-up run)</summary><pre id="traj">run with "use the model" ticked to capture a full trajectory.</pre></details>

</div>
<script>
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const FMT=(v)=>v===null||v===undefined?"–":Array.isArray(v)?("["+v.join(", ")+"]"):(""+v);

async function sample(caseId){const r=await fetch("/api/sample/"+caseId);const j=await r.json();
  if(j.strategy)$("#code").value=j.strategy;}
$$(".sc").forEach(el=>el.onclick=()=>{sample(el.dataset.case);$("#dataset").value=el.dataset.ds;});

async function scorecard(){
  const j=await(await fetch("/api/scorecard")).json();
  if(!j.rows.length)return;
  const mk=(who)=>j.rows.map(r=>{const c=r[who]||{};return `<span class="cell ${c.ok?'ok':'no'}" title="${r.case} — true ${c.true}, said ${c.pred}"></span>`;}).join("");
  $("#row-b").innerHTML=mk("baseline"); $("#row-a").innerHTML=mk("advanced");
  const bp=Math.round((j.baseline||0)*100), ap=Math.round((j.advanced||0)*100);
  $("#rb").textContent=bp+"%"; $("#ra").textContent=ap+"%";
  const bc=j.rows.filter(r=>(r.baseline||{}).ok).length, ac=j.rows.filter(r=>(r.advanced||{}).ok).length;
  $("#scap").innerHTML=`baseline <b class="a">${bc}/${j.n}</b> &nbsp;·&nbsp; agent <b class="b">${ac}/${j.n}</b> &nbsp;·&nbsp; 0 errors`;
}
scorecard();

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function pick(caseId,ds){await sample(caseId);$("#dataset").value=ds;}

async function runDemo(loop){
  document.body.classList.add("autodemo");
  window.scrollTo({top:0,behavior:"smooth"}); await sleep(700);
  await pick("case-06-lookahead-bug","sample:case-06-lookahead-bug"); await sleep(1600);
  await validate();  await sleep(3400);          // OVERFIT — look-ahead flags red
  await pick("case-13-meanrev-edge-2","sample:case-13-meanrev-edge-2"); await sleep(1600);
  await validate();  await sleep(3200);          // EDGE + human gate
  document.querySelector(".scorecard").scrollIntoView({behavior:"smooth",block:"center"}); await sleep(4500);
  document.body.classList.remove("autodemo");
  if(loop){ await sleep(2500); runDemo(true); }
}
addEventListener("keydown",e=>{ if(e.key.toLowerCase()==="d") runDemo(false); });
if(location.search.indexOf("demo")>=0){
  addEventListener("load",()=>setTimeout(()=>runDemo(location.search.indexOf("loop")>=0),1400));
}

async function validate(){
  const btn=$("#go"); btn.disabled=true; btn.textContent="Validating…";
  const P=$("#panel");
  P.innerHTML=`<div class="checks" id="checks"></div>`;
  try{
    const j=await(await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({strategy:$("#code").value,dataset:$("#dataset").value,use_model:$("#usemodel").checked})})).json();
    if(!j.ok){P.innerHTML=`<div class="err">${j.error||"error"}</div>`;return;}

    const C=$("#checks");
    C.innerHTML=j.checks.map(c=>`<div class="chk run" data-n="${c.name}">
      <span class="dot"></span><span class="lbl">${c.label}</span><span class="res">running…</span></div>`).join("");
    const rows=$$(".chk");
    for(let i=0;i<j.checks.length;i++){
      await new Promise(r=>setTimeout(r,430));
      const c=j.checks[i], el=rows[i];
      el.classList.remove("run"); el.classList.add("show","done"); if(c.bad)el.classList.add("bad");
      el.querySelector(".res").textContent=c.result;
    }
    await new Promise(r=>setTimeout(r,450));

    const v=(j.verdict||"?").toLowerCase();
    const d=j.digest;
    const stat=(k,val)=>`<div class="stat"><div class="k">${k}</div><div class="v">${FMT(val)}</div></div>`;
    const chips=(j.findings||[]).map(f=>`<span class="chip">${f.id||f}</span>`).join("")||`<span class="chip">no adverse findings</span>`;
    const gate=v==="edge"?`<div class="gate">⚑ positive verdict — held for human sign-off before any live capital</div>`:"";
    P.insertAdjacentHTML("beforeend",`
      <div class="verdict ${v}" id="vd">
        <div class="big">${v.toUpperCase()}</div>
        <div class="why">${j.reason||""}</div>
      </div>
      <div class="chips">${chips}</div>
      ${gate}
      <div class="stats">
        ${stat("in-sample Sharpe", (j.in_sample||{}).sharpe)}
        ${stat("OOS Sharpe", d.oos_sharpe)}
        ${stat("OOS / in-sample", d.oos_over_is)}
        ${stat("MC p-value", d.mc_p_value)}
        ${stat("param plateau", d.param_plateau_score)}
        ${stat("survives 5bps", d.cost_survives_5bps)}
      </div>
      <div class="meta">${j.checks.length} checks · verdict by rule over verified evidence ·
        ${j.used_model?("model write-up · $"+j.cost.toFixed(4)):"no model call · $0.00"}</div>`);
    requestAnimationFrame(()=>$("#vd").classList.add("show"));
    if(j.trajectory)$("#traj").textContent=j.trajectory;
  }catch(e){P.innerHTML=`<div class="err">${e}</div>`;}
  finally{btn.disabled=false;btn.textContent="Validate";}
}
$("#go").onclick=validate;
</script></body></html>"""


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7600, debug=False)
