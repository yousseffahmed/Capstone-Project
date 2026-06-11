#!/usr/bin/env python3
"""build_home.py — the START-HERE landing page (index.html) + clean rendered HTML for the markdown
docs (FINAL_REPORT / FINDINGS / DECISION_LOG). Single entry point that explains how to traverse
every finding, result, and tool in this folder. Self-contained (marked.js embedded), opens offline."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
MARKED = open(os.path.join(HERE, "_assets", "marked.min.js"), encoding="utf-8").read()

# ── shared global nav — the same bar on every page (auto-hides when embedded in the switcher iframe) ──
GNAV_CSS = """
 .gnav{position:sticky;top:0;z-index:60;display:flex;gap:3px;flex-wrap:wrap;align-items:center;background:#0b1825;border-bottom:1px solid #243244;padding:7px 14px;font-family:-apple-system,Segoe UI,Roboto,Calibri,sans-serif}
 .gnav .brand{font-weight:800;color:#14A38B;margin-right:8px;font-size:13px;text-decoration:none}
 .gnav a{color:#9FB3BE;text-decoration:none;font-weight:700;font-size:12.5px;padding:6px 10px;border-radius:8px;white-space:nowrap}
 .gnav a:hover{background:#16263a;color:#E8F0EE} .gnav a.active{background:rgba(20,163,139,.22);color:#fff}
 .gnav .sp{flex:1} .gnav .ext{color:#6b7f8b;font-weight:600;font-size:11.5px}
"""
# location-aware: one definition; the script computes correct relative hrefs whether the page is at
# root (index.html) or inside pages/ — so links never break after the folder reorg.
GNAV = ('<nav class="gnav" id="gnav">'
 '<a class="brand" data-nav="start" target="_top">◆ Kampala PM2.5</a>'
 '<a data-nav="start" target="_top">🏠 Start</a>'
 '<a data-nav="tool" target="_top">🎯 Tool</a>'
 '<a data-nav="views" target="_top">📚 Views</a>'
 '<a data-nav="findings" target="_top">🔬 Findings</a>'
 '<a data-nav="report" target="_top">📄 Report</a>'
 '<a data-nav="log" target="_top">🧾 Log</a>'
 '<span class="sp"></span>'
 '<a class="ext" data-nav="deck" target="_top">🖥 Deck</a>'
 '</nav>'
 '<script>(function(){var inP=location.pathname.indexOf("/pages/")>=0;var P=inP?"":"pages/",R=inP?"../":"";'
 'var H={start:R+"index.html",tool:P+"kampala_planner_prototype.html",views:P+"capstone_pyramid.html",'
 'findings:P+"FINDINGS.html",report:P+"FINAL_REPORT.html",log:P+"DECISION_LOG.html",deck:R+"docs/capstone_presentation_v2.pdf"};'
 'var cur=(location.pathname.split("/").pop()||"index.html").toLowerCase();'
 'document.querySelectorAll("#gnav a[data-nav]").forEach(function(a){var k=a.getAttribute("data-nav");a.setAttribute("href",H[k]);'
 'if(!a.classList.contains("brand")&&H[k].split("/").pop().toLowerCase()===cur)a.classList.add("active");});'
 'if(window.self!==window.top){var g=document.getElementById("gnav");if(g)g.style.display="none";}})();</script>')

DOC_CSS = """
 :root{--navy:#0D1B2A;--card:#122030;--teal:#14A38B;--amber:#E8A020;--t1:#E8F0EE;--t2:#B9C7CE;--t3:#7f93a0;--border:#243244;--mono:'SF Mono',Consolas,monospace}
 *{box-sizing:border-box} html,body{margin:0;background:var(--navy);color:var(--t2);font-family:-apple-system,Segoe UI,Roboto,Calibri,sans-serif;line-height:1.62}
 .top{position:sticky;top:0;background:linear-gradient(180deg,#0e1d2e,#0b1825ee);backdrop-filter:blur(6px);border-bottom:1px solid var(--border);padding:11px 22px;display:flex;gap:14px;align-items:center;z-index:5}
 .top a{color:var(--teal);text-decoration:none;font-weight:700;font-size:13px} .top a:hover{text-decoration:underline}
 .top .crumb{color:var(--t3);font-size:12.5px}
 main{max-width:860px;margin:0 auto;padding:30px 22px 90px}
 h1{color:#fff;font-size:28px;line-height:1.25;margin:.2em 0 .5em;border-bottom:2px solid var(--teal);padding-bottom:.3em}
 h2{color:#fff;font-size:21px;margin:1.7em 0 .5em;border-bottom:1px solid var(--border);padding-bottom:.25em}
 h3{color:var(--t1);font-size:16.5px;margin:1.4em 0 .4em} h4{color:var(--t1);font-size:14.5px;margin:1.2em 0 .3em}
 a{color:var(--teal)} strong{color:var(--t1)} em{color:#cfe} hr{border:0;border-top:1px solid var(--border);margin:1.6em 0}
 code{font-family:var(--mono);font-size:.88em;background:#0a1420;border:1px solid var(--border);border-radius:4px;padding:1px 5px;color:#8fe3d0}
 pre{background:#0a1420;border:1px solid var(--border);border-radius:9px;padding:13px 15px;overflow:auto} pre code{border:0;background:none;padding:0;color:var(--t2)}
 blockquote{border-left:3px solid var(--amber);background:#16140a;margin:1em 0;padding:9px 16px;border-radius:0 8px 8px 0;color:#e8c98a}
 table{border-collapse:collapse;width:100%;margin:1.1em 0;font-size:13.5px;display:block;overflow-x:auto}
 th,td{border:1px solid var(--border);padding:7px 11px;text-align:left} th{background:#16263a;color:var(--t1);font-weight:700} tr:nth-child(even) td{background:#0f1c2b}
 ul,ol{padding-left:1.4em} li{margin:.25em 0}
 .badge{display:inline-block;background:color-mix(in srgb,var(--teal) 18%,transparent);border:1px solid var(--teal);color:#bfeee2;border-radius:11px;padding:2px 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
"""

def doc_page(title, md_path):
    md = open(os.path.join(HERE, "..", "docs", md_path), encoding="utf-8").read()
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — Kampala PM2.5 Capstone</title>
<style>{DOC_CSS}{GNAV_CSS}</style></head><body>
{GNAV}
<main><div class="badge">{title}</div><div id="doc"></div></main>
<script>{MARKED}</script>
<script>const MD={json.dumps(md)};
 marked.setOptions({{gfm:true,breaks:false}});
 document.getElementById('doc').innerHTML=marked.parse(MD);</script>
</body></html>"""

# --- render the three docs ---
for title, src, out in [("Final Report","FINAL_REPORT.md","FINAL_REPORT.html"),
                        ("Findings","FINDINGS.md","FINDINGS.html"),
                        ("Decision Log","DECISION_LOG.md","DECISION_LOG.html")]:
    open(os.path.join(HERE, "..", "pages", out), "w", encoding="utf-8").write(doc_page(title, src))
    print("rendered", out)

# --- the landing page ---
def card(href, icon, title, desc, tag=""):
    t = f'<span class="ct">{tag}</span>' if tag else ""
    return f'<a class="card" href="{href}"><div class="ci">{icon}</div><div class="cb"><div class="ch">{title}{t}</div><div class="cd">{desc}</div></div><div class="cgo">open ↗</div></a>'

LAND = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart City Capstone — Kampala PM2.5 · Start Here</title>
<style>{GNAV_CSS}
 :root{{--navy:#0D1B2A;--card:#122030;--card2:#16263a;--teal:#14A38B;--amber:#E8A020;--green:#46c98a;--red:#ec5a4c;--t1:#E8F0EE;--t2:#9FB3BE;--t3:#6b7f8b;--border:#243244;--mono:'SF Mono',Consolas,monospace}}
 *{{box-sizing:border-box;margin:0;padding:0}} body{{background:radial-gradient(1200px 600px at 70% -10%,#13283d,#0D1B2A 60%);color:var(--t2);font-family:-apple-system,Segoe UI,Roboto,Calibri,sans-serif;line-height:1.55;min-height:100vh}}
 .wrap{{max-width:1060px;margin:0 auto;padding:40px 22px 90px}}
 .eyebrow{{font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--teal)}}
 h1{{color:#fff;font-size:34px;font-weight:800;margin:6px 0 2px;letter-spacing:-.01em}}
 .tag{{display:inline-block;font-size:11px;font-weight:700;color:var(--green);border:1px solid #2f6b50;border-radius:11px;padding:2px 10px;margin-left:10px;vertical-align:6px}}
 .lead{{color:var(--t1);font-size:17px;max-width:760px;margin-top:12px}}
 .lead b{{color:#fff}}
 .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin:24px 0 8px}}
 .kpi{{background:var(--card);border:1px solid var(--border);border-radius:11px;padding:14px 15px}}
 .kpi .n{{font-size:23px;font-weight:800;color:var(--green);line-height:1}} .kpi .l{{font-size:11px;color:var(--t3);text-transform:uppercase;letter-spacing:.04em;margin-top:6px;line-height:1.35}}
 .sec{{font-size:12px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--teal);margin:34px 0 14px;display:flex;align-items:center;gap:11px}}
 .sec::after{{content:"";flex:1;height:1px;background:var(--border)}}
 .path{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
 .step{{background:var(--card);border:1px solid var(--border);border-radius:11px;padding:15px 16px;position:relative}}
 .step .nr{{position:absolute;top:-10px;left:14px;width:24px;height:24px;border-radius:50%;background:var(--teal);color:#06241f;font-weight:800;font-size:13px;display:flex;align-items:center;justify-content:center}}
 .step h4{{color:#fff;font-size:14.5px;margin:6px 0 4px}} .step p{{font-size:12.5px;color:var(--t2)}} .step a{{color:var(--teal);text-decoration:none;font-weight:700;font-size:12.5px}} .step a:hover{{text-decoration:underline}}
 .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}}
 .card{{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:15px 17px;text-decoration:none;transition:.15s}}
 .card:hover{{border-color:var(--teal);background:var(--card2);transform:translateY(-1px)}}
 .card .ci{{font-size:26px;flex:0 0 auto;width:34px;text-align:center}}
 .card .cb{{flex:1}} .card .ch{{color:#fff;font-weight:700;font-size:15px}} .card .cd{{color:var(--t2);font-size:12.5px;margin-top:2px}}
 .card .ct{{font-size:10px;font-weight:700;color:var(--amber);border:1px solid #6b5a20;border-radius:9px;padding:1px 7px;margin-left:8px;vertical-align:2px;text-transform:uppercase}}
 .card .cgo{{color:var(--t3);font-size:12px;font-weight:700;flex:0 0 auto}}
 .lenses{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
 .lens{{background:#0f1c2b;border:1px solid var(--border);border-radius:10px;padding:12px 14px}} .lens b{{color:#fff}} .lens span{{font-size:12.5px;color:var(--t2)}}
 .note{{background:var(--card);border-left:3px solid var(--teal);border-radius:0 10px 10px 0;padding:13px 17px;margin-top:14px;color:var(--t2);font-size:13px}}
 .foot{{border-top:1px solid var(--border);margin-top:36px;padding-top:16px;color:var(--t3);font-size:11.5px;line-height:1.7}}
 @media(max-width:720px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body>{GNAV}
<div class="wrap">

 <div class="eyebrow">Smart City Capstone · Data Science × Smart Cities</div>
 <h1>Kampala PM2.5 — Start Here <span class="tag">finalized</span></h1>
 <div class="lead">Can <b>free data</b> give a Kampala planner trustworthy PM2.5 <b>where there is no sensor</b> — and a few days <b>ahead</b>? <b>Yes, with honest limits.</b> We sort each place into a <i>kind</i>, predict on it, and grade by the <b>EPA safety tier</b> a planner acts on. This page is the map to everything we built.</div>

 <div class="kpis">
  <div class="kpi"><div class="n">0.32→0.55</div><div class="l">new-site R² · collapse → recovered (honest)</div></div>
  <div class="kpi"><div class="n">68% / 98.5%</div><div class="l">safety tier · exact / within-one (new site)</div></div>
  <div class="kpi"><div class="n">0.43</div><div class="l">forecast R² at +7 days (persistence ~0)</div></div>
  <div class="kpi"><div class="n">80%</div><div class="l">dangerous-day recall · tunable dial</div></div>
 </div>

 <div class="sec">How to traverse — the 4-step path</div>
 <div class="path">
  <div class="step"><div class="nr">1</div><h4>▶ Play with the tool</h4><p>See it work: a Kampala safety map (now / +1d / +7d) and a predict-a-location page.</p><a href="pages/kampala_planner_prototype.html">Open the prototype →</a></div>
  <div class="step"><div class="nr">2</div><h4>📚 Read the full story</h4><p>The whole arc in stacked “pyramid” checkpoints — start with the <b>Consolidated</b> lens.</p><a href="pages/capstone_pyramid.html">Open the pyramid views →</a></div>
  <div class="step"><div class="nr">3</div><h4>🔬 Dig into results</h4><p>The honest numbers and the academic write-up, every claim sourced to a script.</p><a href="pages/FINDINGS.html">Findings →</a> &nbsp;·&nbsp; <a href="pages/FINAL_REPORT.html">Report →</a></div>
  <div class="step"><div class="nr">4</div><h4>⌨️ Inspect the code</h4><p>Every number reproduces from fixed-seed scripts + result CSVs.</p><a href="analysis/">Open analysis/ →</a></div>
 </div>

 <div class="sec">All deliverables</div>
 <div class="cards">
  {card('pages/kampala_planner_prototype.html','🎯','The interactive tool','Safety map (Voronoi areas, now/+1d/+7d, tooltips) + predict-a-location page.','prototype')}
  {card('pages/capstone_pyramid.html','📚','The Pyramid Views','4 lenses of the whole story — Consolidated · Fourth Index · Forecast · Predictor.')}
  {card('pages/FINAL_REPORT.html','📄','Final report','Thesis-chapter write-up: problem → method → results → discussion → reproducibility.')}
  {card('pages/FINDINGS.html','🔬','Findings','The honest, results-focused companion — every number traceable to a script.')}
  {card('pages/DECISION_LOG.html','🧾','Decision log','Every experiment · honest score · keep/kill · web source.')}
  {card('docs/capstone_presentation_v2.pdf','🖥','Slide deck','15 slides, safety-tier framing (PDF).')}
  {card('analysis/','💾','Code & data','Reproducible scripts, result CSVs, figures, persisted models.')}
  {card('docs/HANDOVER.md','📌','Handover (status)','The closed project state — what is done, where everything lives.')}
 </div>

 <div class="sec">Inside the Pyramid Views — the 4 lenses</div>
 <div class="lenses">
  <div class="lens"><b>📚 Consolidated</b><br><span>the whole 10-stage story, base → tip. <b>Start here.</b></span></div>
  <div class="lens"><b>④ Fourth Index</b><br><span>only what this iteration changed (k=4, conformal, safety tiers).</span></div>
  <div class="lens"><b>🔮 Forecast</b><br><span>the project arc — the road behind and the road ahead.</span></div>
  <div class="lens"><b>🎯 Predictor</b><br><span>the deployable tool: inputs → nowcast → forecast → proof → the planner map.</span></div>
 </div>

 <div class="note"><b>The one honest limit, stated plainly:</b> a few places (e.g. <b>site_54</b>, the Kalerwe market node) pollute from a <i>local land-use source</i> no free map feature can see — there the map under-reads, and a cheap confirming sensor is needed. That boundary is itself a finding, not a bug.</div>

 <div class="sec">Final honest improvement audit</div>
 <div class="note"><b>No production replacement after the audit.</b> k=6 is <b>meaningful but fragile</b>: it splits finer pollution regimes, but its strongest full-history score is a <b>non-deployable upper bound</b>. Deployable k=6 improves with a <b>30-45 day</b> early window but still does <b>not</b> beat accepted k=4, so accepted production remains <b>k=4 for NOW/safety</b>. For FUTURE, <b>LSTM remains the headline</b>; RandomForest and rolling-7 persistence are <b>challenger baselines only</b>. What not to claim: k=6 is production, RF beats LSTM overall, random split is real-world performance, or full-history category assignment is deployable.</div>

 <div class="foot">
  <b>Honest methodology:</b> every headline number is out-of-sample — NOW = leave-sites-out (a brand-new place), FUTURE = chronological (the real future). Leaky random-split numbers are labelled as such. Negatives are kept, not buried.<br>
  <b>Scope:</b> 39 AirQo sensors · 13,944 site-days · Kampala 2019–2020. Extends Adong 2025 (the precedent, which used satellite AOD alone). Basemap © OpenStreetMap © CARTO.<br>
  Smart City Capstone · finalized 2026-06-07.
 </div>
</div></body></html>"""

open(os.path.join(HERE, "..", "index.html"), "w", encoding="utf-8").write(LAND)
print("built index.html (START-HERE landing,", len(LAND)//1024, "KB)")
