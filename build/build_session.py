#!/usr/bin/env python3
"""build_session.py — Pyramid View of THIS SESSION's increments only (3 stages)."""
import os, re, json, base64, glob
HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "index_src.html")
OUT  = os.path.join(HERE, "..", "pages", "index_session.html")
STAGES_JS = os.path.join(HERE, "stages_session.js")
RES  = os.path.join(HERE, "..", "analysis", "results"); CODE = os.path.join(HERE, "..", "analysis")
lines = open(SRC, encoding="utf-8").read().split("\n")
_s = next(i for i, l in enumerate(lines) if l.startswith("const STAGES=["))
_e = next(i for i in range(_s + 1, len(lines)) if lines[i].strip() == "];")
new_stages = open(STAGES_JS, encoding="utf-8").read().rstrip("\n")
lines = lines[:_s] + new_stages.split("\n") + lines[_e + 1:]
h = "\n".join(lines)
repl = [
 ("<title>The Pyramid View — Smart City Capstone · Kampala PM2.5</title>",
  "<title>The Pyramid View — This Session · what we improved (Kampala PM2.5)</title>"),
 ('<div class="eyebrow">The Pyramid View · deliverable 3 · data → features</div>',
  '<div class="eyebrow">The Pyramid View · this session · what we incremented</div>'),
 ("<h1>Smart City Capstone — from raw data to model-ready features</h1>",
  "<h1>This session — sharper scores + a safety-tier planner tool</h1>"),
 ('<div class="sub">The Kampala {{PM2.5}} pipeline so far — three free data sources through to the model-ready feature sets — as one compact pyramid. Open a checkpoint, then expand each point in place — the data → the numbers → the reasoning → the code. Deeper layers (full scripts) open their own panel.</div>',
  '<div class="sub">Only what changed <b>this session</b>, on top of the finished 4th cap. Read base → tip: the <b>mission</b> → a <b>sharper model</b> (k=4 categories, group conformal, plus the honest negatives) → the <b>safety-tier tool</b> (grade by EPA band; a planner-tunable danger dial). Open a checkpoint, expand each point in place; deeper layers open their own panel. For the whole story end-to-end, see <span style="font-family:var(--mono)">index_consolidated.html</span>.</div>'),
 ('<div class="cap-b">Base<br>start</div>', '<div class="cap-b">Base<br>the mission</div>'),
 ('<div class="cap-t">Tip<br>features</div>', '<div class="cap-t">Tip<br>the safety tool</div>'),
]
for a, b in repl:
    assert a in h, f"anchor missing: {a[:50]}"
    h = h.replace(a, b, 1)
NL = "\n"
new_close = (
 '  <section class="nextcard" style="margin-top:22px;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--s7);border-radius:10px;padding:16px 20px">' + NL +
 '    <div style="font-size:9.5px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--s7)">This session · the bottom line</div>' + NL +
 '    <div style="color:var(--t1);font-size:15px;font-weight:700;margin-top:4px">From a collapsing R² to a deployable safety tool</div>' + NL +
 '    <div style="color:var(--t2);font-size:12.5px;margin-top:7px;max-width:860px">Three real wins, all on the honest splits: <b>k=4 categories</b> (deploy-only nowcast 0.47 → 0.56, significant), <b>group conformal</b> (new-site coverage ≈75% → 86%), and the <b>safety-tier</b> reframe — right to the exact EPA tier <b>68%</b> / within one tier <b>98.5%</b> at a sensor-less site, with a planner dial catching <b>80% of dangerous days</b> at a chosen false-alarm cost. Equally important, the honest negatives: a bigger/ensembled forecaster, a weighted danger classifier, stacking, and extra geodata all failed to beat the simple levers — so the wins are real and the limits are stated.</div>' + NL +
 '  </section>' + NL +
 '  <div class="foot">' + NL +
 '    <span><b>Every number traces to</b> the committed scripts + result CSVs in <span style="font-family:var(--mono)">4th-cap-handover/analysis/</span> (improve_*.py · band_*.py).</span>' + NL +
 '    <span><b>Honest splits only:</b> NOW = leave-sites-out · FUTURE = chronological.</span>' + NL +
 '  </div>'
)
h2 = re.sub(r'  <section class="nextcard".*?<div class="foot">.*?</div>', lambda m: new_close, h, count=1, flags=re.S)
assert h2 != h, "closing block not matched"; h = h2
anchor = "'LMIC':['Low/Middle-Income Country','Cities with little budget for dense monitoring — where cheap-data methods matter most.'],"
add = anchor + "\n" + "\n".join([
 " 'LSTM':['LSTM','A recurrent neural net for sequences — the PM2.5 forecaster.'],",
 " 'conformal':['Conformal','Prediction intervals with a coverage guarantee; group conformal calibrates on held-out sites.'],",
 " 'recall':['Recall','Of all truly dangerous days, the fraction the model flags as dangerous.'],",
])
if anchor in h: h = h.replace(anchor, add, 1)
figs = {os.path.splitext(os.path.basename(p))[0]: "data:image/png;base64," +
        base64.b64encode(open(p, "rb").read()).decode() for p in sorted(glob.glob(RES + "/*.png")) if not os.path.basename(p).startswith("basemap")}
scripts = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(CODE + "/*.py"))}
csvs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(RES + "/*.csv"))}
h = h.replace("{/*FIGS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in figs.items()) + "}", 1)
h = h.replace("{/*SCRIPTS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in scripts.items()) + "}", 1)
h = h.replace("{/*CSVS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in csvs.items()) + "}", 1)
open(OUT, "w", encoding="utf-8").write(h)
print(f"built index_session.html: {os.path.getsize(OUT)//1024} KB · {len(figs)} figs")
