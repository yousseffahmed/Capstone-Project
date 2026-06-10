#!/usr/bin/env python3
"""
build_4th.py — assemble the 4th-cap Pyramid View.

Splices the new 8-stage tree (stages_4th.js) into the stripped engine (index_src.html),
refreshes the header / rail captions / title / glossary, then injects the 4th-cap figures
(analysis/results/*.png), scripts (analysis/*.py) and result CSVs (analysis/results/*.csv)
into the FIGS/SCRIPTS/CSVS placeholders. Output -> index.html (self-contained, opens offline).

Run: ../../working/.venv/bin/python build_4th.py   (from 4th-cap-handover/)
"""
import os, re, json, base64, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "index_src.html")
OUT  = os.path.join(HERE, "..", "pages", os.environ.get("PYRAMID_OUT", "index_consolidated.html"))  # index.html (root) is the landing page (build_home.py)
STAGES_JS = os.path.join(HERE, os.environ.get("PYRAMID_STAGES", "stages_4th.js"))
RES  = os.path.join(HERE, "..", "analysis", "results")
CODE = os.path.join(HERE, "..", "analysis")

lines = open(SRC, encoding="utf-8").read().split("\n")

# --- 1) splice STAGES (locate the array dynamically: robust to glossary/header edits) ---
_s = next(i for i, l in enumerate(lines) if l.startswith("const STAGES=["))
_e = next(i for i in range(_s + 1, len(lines)) if lines[i].strip() == "];")
new_stages = open(STAGES_JS, encoding="utf-8").read().rstrip("\n")
lines = lines[:_s] + new_stages.split("\n") + lines[_e + 1:]
h = "\n".join(lines)

# --- 2) header / rail / title refresh ---
repl = [
 ("<title>The Pyramid View — Smart City Capstone · Kampala PM2.5</title>",
  "<title>The Pyramid View — 4th Cap · Kampala PM2.5 (categorize-then-predict)</title>"),
 ('<div class="eyebrow">The Pyramid View · deliverable 3 · data → features</div>',
  '<div class="eyebrow">The Pyramid View · 4th cap · two metrics · honest tests</div>'),
 ("<h1>Smart City Capstone — from raw data to model-ready features</h1>",
  "<h1>Smart City Capstone — categorize-then-predict for Kampala PM2.5</h1>"),
 ('<div class="sub">The Kampala {{PM2.5}} pipeline so far — three free data sources through to the model-ready feature sets — as one compact pyramid. Open a checkpoint, then expand each point in place — the data → the numbers → the reasoning → the code. Deeper layers (full scripts) open their own panel.</div>',
  '<div class="sub">Can a <b>categorize-then-predict</b> pipeline give a planner trustworthy {{PM2.5}} where there is <b>no sensor</b> — and a few days <b>ahead</b> — without collapsing? Read base → tip: the collapse → categorize → route honestly → features → bake-offs → free geodata → forecast → the verdict. Open a checkpoint, expand each point in place; deeper layers (full scripts, raw tables) open their own panel.</div>'),
 ('<div class="cap-b">Base<br>start</div>', '<div class="cap-b">Base<br>the collapse</div>'),
 ('<div class="cap-t">Tip<br>features</div>', '<div class="cap-t">Tip<br>the safety tool</div>'),
]
for a, b in repl:
    assert a in h, f"header anchor missing: {a[:50]}"
    h = h.replace(a, b, 1)

# --- 2b) replace the old 3rd-cap closing card + footer (it stopped at feature sets) ---
NL = "\n"
new_close = (
 '  <section class="nextcard" style="margin-top:22px;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--s2);border-radius:10px;padding:16px 20px">' + NL +
 '    <div style="font-size:9.5px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--s2)">The bottom line · what’s next</div>' + NL +
 '    <div style="color:var(--t1);font-size:15px;font-weight:700;margin-top:4px">A deployable safety-triage tool — with honest limits</div>' + NL +
 '    <div style="color:var(--t2);font-size:12.5px;margin-top:7px;max-width:860px">Categorization recovers the cold-start collapse — honest new-site R² <b>0.32 → 0.56</b> (k=4, significant); free map data reaches a <b>sensor-less</b> site (<b>0.42</b> with zero observations). A forecaster holds <b>R²≈0.43 a week out</b>. But the payoff is the <b>safety-tier</b> reframe (stage 9): graded by EPA band, the new-site tool is right to the exact tier <b>68%</b> and to within one tier <b>98.5%</b>, with a planner-tunable dial catching <b>80% of dangerous days</b> at a chosen false-alarm cost. Negatives kept: bigger/ensembled forecasters, a weighted danger classifier, and extra geodata all failed to beat the simple levers. Honest next moves:</div>' + NL +
 '    <ol style="margin:11px 0 2px;padding-left:0;list-style:none;display:grid;gap:8px;max-width:880px">' + NL +
 ''.join(
   f'      <li style="display:flex;gap:11px;align-items:flex-start"><span style="flex:0 0 auto;width:20px;height:20px;border-radius:50%;background:color-mix(in srgb,var(--s2) 22%,transparent);color:var(--s2);font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center">{i}</span><span style="color:var(--t2);font-size:12.5px"><b style="color:var(--t1)">{t}</b> {d}</span></li>' + NL
   for i, t, d in [
     (1, "Calibrated uncertainty.", "Group/Mondrian conformal to fix the new-site under-coverage (74.8% &rarr; ~90% target)."),
     (2, "More places.", "39 sites &middot; 3 categories is small &mdash; more sensors would sharpen routing and shrink the high fold-to-fold variance."),
     (3, "Cheaper categories.", "Sweep the deploy-window length (30/60/90 days) against category accuracy &mdash; how little observation is enough to route a new site?"),
     (4, "Richer geodata.", "Add population density, greenness (NDVI) and building density &mdash; the next lever to push the zero-sensor nowcast further."),
   ]) +
 '    </ol>' + NL +
 '  </section>' + NL +
 '  <div class="foot">' + NL +
 '    <span><b>Every number traces to</b> the committed scripts + result CSVs in <span style="font-family:var(--mono)">4th-cap-handover/analysis/</span>.</span>' + NL +
 '    <span><b>Grain:</b> site-day · 13,944 rows · 39 sites · 2019–2020.</span>' + NL +
 '    <span><b>Two metrics, kept separate:</b> NOW (leave-sites-out) · FUTURE (chronological).</span>' + NL +
 '  </div>'
)
h2 = re.sub(r'  <section class="nextcard".*?<div class="foot">.*?</div>', lambda m: new_close, h, count=1, flags=re.S)
assert h2 != h, "closing-card/footer block not matched"
h = h2

# --- 3) glossary additions (insert before the closing }; of GLOSSARY) ---
anchor = "'LMIC':['Low/Middle-Income Country','Cities with little budget for dense monitoring — where cheap-data methods matter most.'],"
add = anchor + "\n" + "\n".join([
 " 'LightGBM':['LightGBM','Fast gradient-boosted trees (Microsoft) — a NOW bake-off contender.'],",
 " 'CatBoost':['CatBoost','Gradient boosting built for categorical features; ordered boosting resists target leakage.'],",
 " 'LSTM':['LSTM','A recurrent neural net for sequences — the best PM2.5 forecaster here, with a category embedding.'],",
 " 'MoE':['Mixture of Experts','One model per category, hard-routing a site to its specialist — collapses when the category is wrong.'],",
 " 'OSM':['OpenStreetMap','Free crowd-sourced map data — our source of road density + distance-to-major-road.'],",
 " 'nowcast':['Nowcast','Estimate PM2.5 TODAY at a place with no sensor (the NOW metric).'],",
])
assert anchor in h, "glossary anchor missing"
h = h.replace(anchor, add, 1)

# --- 4) inject figures / scripts / csvs ---
figs = {os.path.splitext(os.path.basename(p))[0]: "data:image/png;base64," +
        base64.b64encode(open(p, "rb").read()).decode() for p in sorted(glob.glob(RES + "/*.png")) if not os.path.basename(p).startswith("basemap")}
scripts = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(CODE + "/*.py"))}
csvs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(RES + "/*.csv"))}
h = h.replace("{/*FIGS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in figs.items()) + "}", 1)
h = h.replace("{/*SCRIPTS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in scripts.items()) + "}", 1)
h = h.replace("{/*CSVS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in csvs.items()) + "}", 1)

open(OUT, "w", encoding="utf-8").write(h)
print(f"built index.html: {os.path.getsize(OUT)//1024} KB")
print(f"injected {len(figs)} figs · {len(scripts)} scripts · {len(csvs)} csvs")
print("figs:", ", ".join(figs))
