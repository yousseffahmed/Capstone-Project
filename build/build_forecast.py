#!/usr/bin/env python3
"""build_forecast.py — Pyramid View #3: the FORECAST lens.
The whole project arc point A -> point Z; past stages solid, future stages
hatched + fading. Same engine as index_src.html, reframed."""
import os, re, json, base64, glob
HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "index_src.html")
OUT  = os.path.join(HERE, "..", "pages", "index_forecast.html")
STAGES_JS = os.path.join(HERE, "stages_forecast.js")
RES  = os.path.join(HERE, "..", "analysis", "results"); CODE = os.path.join(HERE, "..", "analysis")

lines = open(SRC, encoding="utf-8").read().split("\n")
_s = next(i for i, l in enumerate(lines) if l.startswith("const STAGES=["))
_e = next(i for i in range(_s + 1, len(lines)) if lines[i].strip() == "];")
new_stages = open(STAGES_JS, encoding="utf-8").read().rstrip("\n")
lines = lines[:_s] + new_stages.split("\n") + lines[_e + 1:]
h = "\n".join(lines)

# ---- 1. header / shell reframing -------------------------------------------
repl = [
 ("<title>The Pyramid View — Smart City Capstone · Kampala PM2.5</title>",
  "<title>The Pyramid View — Forecast · the whole arc A→Z (Kampala PM2.5)</title>"),
 ('<div class="eyebrow">The Pyramid View · deliverable 3 · data → features</div>',
  '<div class="eyebrow">The Pyramid View · forecast · the road ahead</div>'),
 ("<h1>Smart City Capstone — from raw data to model-ready features</h1>",
  "<h1>Smart City Capstone — the whole road, point A → point Z</h1>"),
 ('<div class="sub">The Kampala {{PM2.5}} pipeline so far — three free data sources through to the model-ready feature sets — as one compact pyramid. Open a checkpoint, then expand each point in place — the data → the numbers → the reasoning → the code. Deeper layers (full scripts) open their own panel.</div>',
  '<div class="sub">The whole capstone as one arc — <b>point A</b> (the question) down to <b>point Z</b> (the deployed tool). Read base → tip. Above the <b>you-are-here</b> line is <b>solid</b>: done and graded. Below it is <b>forecast</b> — hatched and fading the farther out it goes (firmest next week, faintest at the finish). One of three lenses: the full story (Consolidated), this step’s change (Fourth Index), and this road-ahead view.</div>'),
 ('<div class="cap-b">Base<br>start</div>', '<div class="cap-b">Base<br>point A</div>'),
 ('<div class="cap-t">Tip<br>features</div>', '<div class="cap-t">Tip<br>point Z</div>'),
]
for a, b in repl:
    assert a in h, f"anchor missing: {a[:60]}"
    h = h.replace(a, b, 1)

# ---- 2. legend reworded for solid vs forecast ------------------------------
legend_old = """  <div class="legend">
    <span class="k"><span class="dirdown">▼ down</span> = process order: <b>BASE (raw data)</b> → <b>TIP (model-ready features)</b></span>
    <span class="k"><span class="dirright">▸ right</span> = the sub-steps <b>|&gt;&gt;&gt;|</b></span>
    <span class="k"><b>click a point → it expands in place</b> · deeper layers open a panel</span>
    <span class="gloss-btn" id="glossBtn">📖 Glossary</span>
  </div>"""
legend_new = """  <div class="legend">
    <span class="k"><span class="dirdown">▼ down</span> = the project arc: <b>point A (the question)</b> → <b>point Z (the deployed tool)</b></span>
    <span class="k"><b>solid</b> = done &amp; graded · <b>hatched + fading</b> = forecast (fainter = less certain)</span>
    <span class="k"><b>click a point → it expands in place</b> · deeper layers open a panel</span>
    <span class="gloss-btn" id="glossBtn">📖 Glossary</span>
  </div>"""
assert legend_old in h, "legend anchor missing"
h = h.replace(legend_old, legend_new, 1)

# ---- 3. CSS: forecast hatch + fade + the now-line --------------------------
css_anchor = ".seg.last{clip-path:polygon(0 0,100% 0,100% 100%,0 100%,13px 50%)}"
css_add = css_anchor + """
  /* --- forecast lens additions --- */
  .nowline{display:flex;align-items:center;gap:12px;width:100%;margin:12px 0 6px;color:var(--s3);font-size:9.5px;font-weight:800;letter-spacing:.15em;text-transform:uppercase}
  .nowline:before,.nowline:after{content:"";flex:1;height:2px;border-radius:2px;background:linear-gradient(90deg,transparent,var(--s3),transparent)}
  .barwrap.fc .seg{background:repeating-linear-gradient(135deg,color-mix(in srgb,var(--hue) 13%,var(--surface)),color-mix(in srgb,var(--hue) 13%,var(--surface)) 7px,color-mix(in srgb,var(--hue) 5%,var(--surface)) 7px,color-mix(in srgb,var(--hue) 5%,var(--surface)) 14px)}
  .barwrap.fc .seg:hover{background:repeating-linear-gradient(135deg,color-mix(in srgb,var(--hue) 26%,var(--surface)),color-mix(in srgb,var(--hue) 26%,var(--surface)) 7px,color-mix(in srgb,var(--hue) 14%,var(--surface)) 7px,color-mix(in srgb,var(--hue) 14%,var(--surface)) 14px)}
  .barwrap.fc .seg.cap{background:color-mix(in srgb,var(--hue) 26%,var(--surface))}
  .fcbadge{font-size:7.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--hue);border:1px solid color-mix(in srgb,var(--hue) 55%,transparent);border-radius:10px;padding:1px 6px;margin-top:4px;display:inline-block}"""
assert css_anchor in h, "css anchor missing"
h = h.replace(css_anchor, css_add, 1)

# ---- 4. render loop: honour forecast / fade / now + insert the now-line -----
loop_old = """STAGES.forEach((stg,si)=>{
  const wrap=document.createElement('div'); wrap.className='barwrap';
  const bar=document.createElement('div'); bar.className='bar'; bar.style.width=(100 - si*2.3)+'%';
  const cap=document.createElement('div'); cap.className='seg cap'; cap.style.setProperty('--hue',`var(${stg.hue})`);
  cap.innerHTML=`<div class="cn">Stage ${stg.n}</div><div class="ct">${stg.name}</div>`;
  bar.appendChild(cap);
  stg.sections.forEach((s,xi)=>{
    const id=`s${si}_${xi}`;
    const root={...s.node, _hue:stg.hue, _short:s.label, _crumb:`Stage ${stg.n} · ${s.label}`, kick:s.node.kick||stg.name, title:s.node.title||s.label};
    NODES[id]=root;
    const seg=document.createElement('div');
    seg.className='seg'+(xi===stg.sections.length-1?' last':''); seg.style.setProperty('--hue',`var(${stg.hue})`);
    seg.innerHTML=`<div class="st">${glow(s.label)}</div><div class="sb">${glow(s.blurb)}</div><span class="more">＋</span>`;
    seg.addEventListener('click',()=>openRoot(id,stg.hue));
    bar.appendChild(seg);
  });
  wrap.appendChild(bar);
  if(si<STAGES.length-1){const c=document.createElement('div'); c.className='conn'; c.textContent='▼'; wrap.appendChild(c);}
  stack.appendChild(wrap);
});"""
loop_new = """let FCSTARTED=false;
STAGES.forEach((stg,si)=>{
  if(stg.forecast && !FCSTARTED){ FCSTARTED=true;
    const nl=document.createElement('div'); nl.className='nowline';
    nl.innerHTML='<span>▼ you are here · everything below is forecast ▼</span>';
    stack.appendChild(nl);
  }
  const wrap=document.createElement('div'); wrap.className='barwrap'+(stg.forecast?' fc':'');
  if(stg.forecast) wrap.style.opacity=(1-(stg.fade||0)).toFixed(2);
  const bar=document.createElement('div'); bar.className='bar'; bar.style.width=(100 - si*2.3)+'%';
  const cap=document.createElement('div'); cap.className='seg cap'; cap.style.setProperty('--hue',`var(${stg.hue})`);
  const capcn = stg.forecast ? ('🔮 '+(stg.eta||'planned')) : ((stg.now?'● now · ':'')+'Stage '+stg.n);
  cap.innerHTML=`<div class="cn">${capcn}</div><div class="ct">${stg.name}</div>`+(stg.forecast?'<div class="fcbadge">forecast</div>':'');
  bar.appendChild(cap);
  stg.sections.forEach((s,xi)=>{
    const id=`s${si}_${xi}`;
    const root={...s.node, _hue:stg.hue, _short:s.label, _crumb:`Stage ${stg.n} · ${s.label}`, kick:s.node.kick||stg.name, title:s.node.title||s.label};
    NODES[id]=root;
    const seg=document.createElement('div');
    seg.className='seg'+(xi===stg.sections.length-1?' last':''); seg.style.setProperty('--hue',`var(${stg.hue})`);
    seg.innerHTML=`<div class="st">${glow(s.label)}</div><div class="sb">${glow(s.blurb)}</div><span class="more">${stg.forecast?'🔮':'＋'}</span>`;
    seg.addEventListener('click',()=>openRoot(id,stg.hue));
    bar.appendChild(seg);
  });
  wrap.appendChild(bar);
  if(si<STAGES.length-1){const c=document.createElement('div'); c.className='conn'; c.textContent='▼'; wrap.appendChild(c);}
  stack.appendChild(wrap);
});"""
assert loop_old in h, "render-loop anchor missing"
h = h.replace(loop_old, loop_new, 1)

# ---- 5. glossary: add LSTM (used in the forecast stages) --------------------
gl_anchor = " 'LMIC':['Low/Middle-Income Country','Cities with little budget for dense monitoring — where cheap-data methods matter most.'],"
gl_add = gl_anchor + "\n 'LSTM':['LSTM','A recurrent neural net for sequences — the PM2.5 forecaster.'],"
if gl_anchor in h:
    h = h.replace(gl_anchor, gl_add, 1)

# ---- 6. closing card: the THREE-VIEW doctrine (the "why") -------------------
NL = "\n"
new_close = (
 '  <section class="nextcard" style="margin-top:22px;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--s7);border-radius:10px;padding:16px 20px">' + NL +
 '    <div style="font-size:9.5px;font-weight:800;letter-spacing:.13em;text-transform:uppercase;color:var(--s7)">Why three views · the standard</div>' + NL +
 '    <div style="color:var(--t1);font-size:15px;font-weight:700;margin-top:4px">Cumulative · Delta · Forecast — the three reference points</div>' + NL +
 '    <div style="color:var(--t2);font-size:12.5px;margin-top:7px;max-width:880px">An iterative, checkpoint-driven project needs <b>three photos, not one</b>, to be legible: <b>(1) the road behind</b> — start → now, solid and certain (the <span style="font-family:var(--mono)">Consolidated</span> view); <b>(2) the last stretch</b> — what this checkpoint changed (the <span style="font-family:var(--mono)">Fourth Index</span> / delta view); and <b>(3) the road ahead</b> — now → point Z, drawn as a forecast that firms up each week (this view). Drop any one and a reviewer can’t tell <i>where you are</i>, <i>what just moved</i>, or <i>whether you’re on track to finish</i>. Reusable for any project that re-forecasts its scope at every checkpoint.</div>' + NL +
 '  </section>' + NL +
 '  <div class="foot">' + NL +
 '    <span><b>The arc:</b> point A (the smart-city question) → point Z (the deployed planner tool).</span>' + NL +
 '    <span><b>Forecast source:</b> the locked roadmap in <span style="font-family:var(--mono)">NEXT_SESSION_HANDOVER_PROMPT.md</span> (Phase 1 → Phase 2).</span>' + NL +
 '  </div>'
)
h2 = re.sub(r'  <section class="nextcard".*?<div class="foot">.*?</div>', lambda m: new_close, h, count=1, flags=re.S)
assert h2 != h, "closing block not matched"; h = h2

# ---- 7. inject assets (keeps the file self-contained) ----------------------
figs = {os.path.splitext(os.path.basename(p))[0]: "data:image/png;base64," +
        base64.b64encode(open(p, "rb").read()).decode() for p in sorted(glob.glob(RES + "/*.png")) if not os.path.basename(p).startswith("basemap")}
scripts = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(CODE + "/*.py"))}
csvs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(RES + "/*.csv"))}
h = h.replace("{/*FIGS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in figs.items()) + "}", 1)
h = h.replace("{/*SCRIPTS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in scripts.items()) + "}", 1)
h = h.replace("{/*CSVS_INJECT*/}", "{" + ",".join(f"{json.dumps(k)}:{json.dumps(v)}" for k, v in csvs.items()) + "}", 1)

open(OUT, "w", encoding="utf-8").write(h)
print(f"built index_forecast.html: {os.path.getsize(OUT)//1024} KB · {len(figs)} figs · {len(scripts)} scripts · {len(csvs)} csvs")
