#!/usr/bin/env python3
"""build_predictor.py — Pyramid View #4: the NEW-SITE PREDICTOR lens.
Same engine as index_src.html, reframed as the deployable tool: inputs (base) ->
categorize -> nowcast -> forecast -> proof (tip). Embeds the new_site_predict.py
demo figures (fig_newsite_demo*) alongside the locked analysis figures."""
import os, re, json, base64, glob
HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "index_src.html")
OUT  = os.path.join(HERE, "..", "pages", "index_predictor.html")
STAGES_JS = os.path.join(HERE, "stages_predictor.js")
RES  = os.path.join(HERE, "..", "analysis", "results"); CODE = os.path.join(HERE, "..", "analysis")

lines = open(SRC, encoding="utf-8").read().split("\n")
_s = next(i for i, l in enumerate(lines) if l.startswith("const STAGES=["))
_e = next(i for i in range(_s + 1, len(lines)) if lines[i].strip() == "];")
new_stages = open(STAGES_JS, encoding="utf-8").read().rstrip("\n")
lines = lines[:_s] + new_stages.split("\n") + lines[_e + 1:]
h = "\n".join(lines)

repl = [
 ("<title>The Pyramid View — Smart City Capstone · Kampala PM2.5</title>",
  "<title>The Pyramid View — New-Site Predictor · Kampala PM2.5</title>"),
 ('<div class="eyebrow">The Pyramid View · deliverable 3 · data → features</div>',
  '<div class="eyebrow">The Pyramid View · the predictor · inputs → proof</div>'),
 ("<h1>Smart City Capstone — from raw data to model-ready features</h1>",
  "<h1>The new-site PM2.5 predictor — from inputs to proof</h1>"),
 ('<div class="sub">The Kampala {{PM2.5}} pipeline so far — three free data sources through to the model-ready feature sets — as one compact pyramid. Open a checkpoint, then expand each point in place — the data → the numbers → the reasoning → the code. Deeper layers (full scripts) open their own panel.</div>',
  '<div class="sub">The deployable tool, end to end: point at <b>any</b> Kampala address and get PM2.5 <b>now</b> (with a safety tier, an uncertainty band, and a danger alert) and for the <b>next 7 days</b>. Read base → tip: the <b>inputs</b> a planner supplies → <b>categorize</b> the place → <b>nowcast</b> today → <b>forecast</b> the week → <b>proof</b> on a real held-out site. Open a checkpoint, expand each point in place; deeper layers (full scripts, the live demo) open their own panel.</div>'),
 ('<div class="cap-b">Base<br>start</div>', '<div class="cap-b">Base<br>the inputs</div>'),
 ('<div class="cap-t">Tip<br>features</div>', '<div class="cap-t">Tip<br>the map</div>'),
]
for a, b in repl:
    assert a in h, f"anchor missing: {a[:50]}"
    h = h.replace(a, b, 1)

NL = "\n"
new_close = (
 '  <section class="nextcard" style="margin-top:22px;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--s7);border-radius:10px;padding:16px 20px">' + NL +
 '    <div style="font-size:9.5px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--s7)">The predictor · the bottom line</div>' + NL +
 '    <div style="color:var(--t1);font-size:15px;font-weight:700;margin-top:4px">A deployable new-site tool — free inputs, honest limits</div>' + NL +
 '    <div style="color:var(--t2);font-size:12.5px;margin-top:7px;max-width:880px">Point at any Kampala address: with only <b>free</b> inputs (location + <b>ERA5</b> weather + auto map geodata) the tool nowcasts PM2.5 today — a number, an <b>EPA safety tier</b> (honest new-site <b>68% exact · 98.5% within one tier</b>), a calibrated <b>≈86%</b> band, and a planner-tunable <b>danger dial</b> (catch <b>80%</b> of dangerous days at a chosen false-alarm cost). Add ≈2 months of a cheap temporary sensor and it <b>forecasts the next 7 days</b> (LSTM, beats persistence to +7d). Validated by holding out whole sites (leave-sites-out mean R² <b>0.547</b>). The one honest limit, stated plainly: where the map alone can’t read a site’s regime, the zero-deploy nowcast can miss — a short deploy fixes it.</div>' + NL +
 '  </section>' + NL +
 '  <div class="foot">' + NL +
 '    <span><b>The tool:</b> <span style="font-family:var(--mono)">analysis/new_site_predict.py</span> — input contract → nowcast → forecast → leave-one-site-out demo.</span>' + NL +
 '    <span><b>Every number traces to</b> the committed scripts + result CSVs in <span style="font-family:var(--mono)">4th-cap-handover/analysis/</span>.</span>' + NL +
 '    <span><b>Honest splits only:</b> NOW = leave-sites-out · FUTURE = chronological.</span>' + NL +
 '  </div>'
)
h2 = re.sub(r'  <section class="nextcard".*?<div class="foot">.*?</div>', lambda m: new_close, h, count=1, flags=re.S)
assert h2 != h, "closing block not matched"; h = h2

anchor = "'LMIC':['Low/Middle-Income Country','Cities with little budget for dense monitoring — where cheap-data methods matter most.'],"
add = anchor + "\n" + "\n".join([
 " 'LSTM':['LSTM','A recurrent neural net for sequences — the production PM2.5 forecaster, with a category embedding.'],",
 " 'nowcast':['Nowcast','Estimate PM2.5 TODAY at a place with no sensor (the NOW metric).'],",
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
print(f"built index_predictor.html: {os.path.getsize(OUT)//1024} KB · {len(figs)} figs · {len(scripts)} scripts · {len(csvs)} csvs")
