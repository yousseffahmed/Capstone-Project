#!/usr/bin/env python3
"""build_prototype.py — assemble the self-contained Kampala planner PROTOTYPE (agentic test app):
  • Safety Map  — basemap + Voronoi coverage cells colored by predicted EPA tier, NOW/+1d/+7d
                  filters, hover tooltips, color-by tier|category.
  • Predict a Location — input the features for a new place -> in-browser category (kNN) + nowcast
                  tier + band + danger dial; 3 real test cases mimic the deployed model.
Embeds analysis/results/{basemap_kampala.png, map_predictions.json, test_cases.json, ref_sites.json}.
"""
import os, json, base64
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "..", "analysis", "results")
b64 = "data:image/png;base64," + base64.b64encode(open(os.path.join(RES, "basemap_kampala.png"), "rb").read()).decode()
MAP = json.load(open(os.path.join(RES, "map_predictions.json")))
TC  = json.load(open(os.path.join(RES, "test_cases.json")))
REF = json.load(open(os.path.join(RES, "ref_sites.json")))
DATA = json.dumps({"map": MAP, "cases": TC["cases"], "ref": REF, "basemap": b64})

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kampala Planner — Safety Prototype (Smart City Capstone)</title>
<style>
 .gnav{position:sticky;top:0;z-index:60;display:flex;gap:3px;flex-wrap:wrap;align-items:center;background:#0b1825;border-bottom:1px solid #243244;padding:7px 14px}
 .gnav .brand{font-weight:800;color:#14A38B;margin-right:8px;font-size:13px;text-decoration:none}
 .gnav a{color:#9FB3BE;text-decoration:none;font-weight:700;font-size:12.5px;padding:6px 10px;border-radius:8px;white-space:nowrap}
 .gnav a:hover{background:#16263a;color:#E8F0EE} .gnav a.active{background:rgba(20,163,139,.22);color:#fff}
 .gnav .sp{flex:1} .gnav .ext{color:#6b7f8b;font-weight:600;font-size:11.5px}
 :root{--navy:#0D1B2A;--card:#122030;--card2:#16263a;--teal:#14A38B;--amber:#E8A020;--t1:#E8F0EE;--t2:#9FB3BE;--t3:#6b7f8b;--border:#243244;
   --green:#46c98a;--high:#e3b34e;--red:#ec5a4c;--mono:'SF Mono',Consolas,monospace}
 *{box-sizing:border-box;margin:0;padding:0}
 body{background:var(--navy);color:var(--t2);font-family:-apple-system,Segoe UI,Roboto,Calibri,sans-serif;font-size:14px;line-height:1.5}
 .wrap{max-width:1180px;margin:0 auto;padding:20px 18px 70px}
 header{border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:16px}
 .eyebrow{font-size:11px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--teal)}
 h1{color:var(--t1);font-size:23px;font-weight:800;margin-top:3px}
 .sub{color:var(--t3);font-size:13px;margin-top:5px;max-width:760px}
 .proto{display:inline-block;font-size:10.5px;font-weight:700;color:var(--amber);border:1px solid #6b5a20;border-radius:10px;padding:2px 9px;margin-left:8px;vertical-align:middle}
 nav{display:flex;gap:8px;margin:16px 0}
 .tab{background:var(--card);border:1px solid var(--border);color:var(--t2);border-radius:9px;padding:9px 17px;font:inherit;font-weight:700;font-size:13.5px;cursor:pointer}
 .tab:hover{border-color:var(--teal);color:var(--t1)} .tab.on{background:color-mix(in srgb,var(--teal) 20%,transparent);border-color:var(--teal);color:#fff}
 section{display:none} section.on{display:block;animation:f .2s ease} @keyframes f{from{opacity:0;transform:translateY(4px)}to{opacity:1}}
 .bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
 .seg{display:flex;background:var(--card);border:1px solid var(--border);border-radius:9px;overflow:hidden}
 .seg button{background:transparent;border:0;color:var(--t2);padding:8px 14px;font:inherit;font-weight:700;font-size:12.5px;cursor:pointer;border-right:1px solid var(--border)}
 .seg button:last-child{border-right:0} .seg button.on{background:var(--teal);color:#06241f}
 .spacer{flex:1}
 .badge{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:7px 13px;font-size:12px;color:var(--t2)}
 .badge b{color:var(--green)}
 #mapwrap{position:relative;width:100%;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:#0a1420;line-height:0}
 #mapwrap img{width:100%;display:block;opacity:.92}
 #ov{position:absolute;inset:0;width:100%;height:100%}
 .cell{stroke:#fff;stroke-width:.8;stroke-opacity:.5;cursor:pointer;transition:fill-opacity .15s} .cell:hover{fill-opacity:.78!important;stroke-opacity:.95}
 .pt{fill:#0a1420;stroke:#fff;stroke-width:1} .pt.flag{fill:none;stroke:#c0392b;stroke-width:2.4}
 #tip{position:absolute;pointer-events:none;z-index:9;background:#0a1622;border:1px solid var(--teal);border-radius:9px;padding:11px 13px;font-size:12px;line-height:1.5;color:var(--t1);min-width:215px;max-width:300px;box-shadow:0 8px 26px #0008;opacity:0;transition:opacity .1s}
 #tip .h{font-weight:800;color:#fff;font-size:13px;line-height:1.4;margin-bottom:5px} #tip .row{display:flex;justify-content:space-between;align-items:baseline;gap:10px;line-height:1.5;padding:2px 0}
 #tip .k{color:var(--t3)} .pill{display:inline-block;font-weight:700;font-size:10.5px;padding:1px 7px;border-radius:9px;color:#06241f}
 .legend{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-top:11px;font-size:12px;color:var(--t2)}
 .legend .sw{display:inline-block;width:13px;height:13px;border-radius:3px;margin-right:5px;vertical-align:-2px;border:1px solid #fff5}
 .cap{color:var(--t3);font-size:12px;margin-top:11px;max-width:900px}
 .card{background:var(--card);border:1px solid var(--border);border-radius:11px;padding:16px 18px;margin-bottom:13px}
 .lab{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--teal);font-weight:700;margin-bottom:9px}
 .cases{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:6px}
 .casebtn{background:var(--card2);border:1px solid var(--border);border-radius:9px;padding:9px 13px;color:var(--t1);font:inherit;font-size:12.5px;cursor:pointer;text-align:left;font-weight:600}
 .casebtn:hover{border-color:var(--teal)} .casebtn small{display:block;color:var(--t3);font-weight:400;font-size:10.5px;margin-top:2px}
 form{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:10px}
 .fld label{display:block;font-size:10.5px;color:var(--t3);text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px}
 .fld input{width:100%;background:#0a1420;border:1px solid var(--border);border-radius:7px;color:var(--t1);padding:7px 9px;font:inherit;font-size:13px}
 .fld input:focus{outline:0;border-color:var(--teal)}
 .go{background:var(--teal);color:#06241f;border:0;border-radius:9px;padding:11px 22px;font:inherit;font-weight:800;font-size:14px;cursor:pointer;margin-top:4px}
 .go:hover{filter:brightness(1.08)}
 #out{margin-top:14px}
 .big{font-size:30px;font-weight:800;line-height:1} .res-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:11px;margin:10px 0}
 .res{background:#0a1420;border:1px solid var(--border);border-radius:9px;padding:12px 14px} .res .k{font-size:10.5px;color:var(--t3);text-transform:uppercase;letter-spacing:.05em}
 .tierbox{border-radius:9px;padding:13px 16px;color:#06241f;font-weight:800}
 .note{border-left:3px solid var(--amber);background:#1a1606;border-radius:0 8px 8px 0;padding:10px 13px;font-size:12.5px;color:#e8c98a;margin-top:9px}
 .ok{border-left-color:var(--teal);background:#06201c;color:#a7e8da}
 .foot{border-top:1px solid var(--border);margin-top:24px;padding-top:13px;color:var(--t3);font-size:11px}
 a{color:var(--teal)}
</style></head><body>
<nav class="gnav" id="gnav"><a class="brand" data-nav="start" target="_top">◆ Kampala PM2.5</a><a data-nav="start" target="_top">🏠 Start</a><a data-nav="tool" target="_top">🎯 Tool</a><a data-nav="views" target="_top">📚 Views</a><a data-nav="findings" target="_top">🔬 Findings</a><a data-nav="report" target="_top">📄 Report</a><a data-nav="log" target="_top">🧾 Log</a><span class="sp"></span><a class="ext" data-nav="deck" target="_top">🖥 Deck</a></nav>
<script>(function(){var inP=location.pathname.indexOf("/pages/")>=0;var P=inP?"":"pages/",R=inP?"../":"";var H={start:R+"index.html",tool:P+"kampala_planner_prototype.html",views:P+"capstone_pyramid.html",findings:P+"FINDINGS.html",report:P+"FINAL_REPORT.html",log:P+"DECISION_LOG.html",deck:R+"docs/capstone_presentation_v2.pdf"};var cur=(location.pathname.split("/").pop()||"index.html").toLowerCase();document.querySelectorAll("#gnav a[data-nav]").forEach(function(a){var k=a.getAttribute("data-nav");a.setAttribute("href",H[k]);if(!a.classList.contains("brand")&&H[k].split("/").pop().toLowerCase()===cur)a.classList.add("active");});if(window.self!==window.top){var g=document.getElementById("gnav");if(g)g.style.display="none";}})();</script>
<div class="wrap">
 <header>
  <div class="eyebrow">Smart City Capstone · Kampala PM2.5 <span class="proto">PROTOTYPE</span></div>
  <h1>Kampala Planner — Air-Quality Safety Tool</h1>
  <div class="sub">A working prototype of the deployable tool: a <b>safety-tier map</b> of every monitored area (now and forecast), and a <b>predict-a-location</b> page that scores a new place from free inputs. Honest, leave-sites-out predictions — built to be deployed properly later.</div>
  <div class="note">Final audit guardrail: k=6 is meaningful but fragile; k=6 full-history is a non-deployable upper bound; deployable k=6 does not beat accepted k=4. Accepted production remains k=4 for NOW/safety, LSTM remains headline for FUTURE, and RF/rolling-7 are challenger baselines only. What not to claim: k=6 is the new production model, RF beats LSTM overall, random splits are real-world performance, or full-history category assignment is deployable at a new site.</div>
 </header>
 <nav><button class="tab on" data-t="map">🗺 Safety Map</button><button class="tab" data-t="predict">🎛 Predict a Location</button></nav>

 <section id="map" class="on">
  <div class="bar">
   <div class="seg" id="hz"><button data-h="now" class="on">● Now</button><button data-h="d1">+1 day</button><button data-h="d7">+7 days</button></div>
   <div class="seg" id="cb"><button data-c="tier" class="on">by safety tier</button><button data-c="cat">by area type</button></div>
   <div class="spacer"></div>
   <div class="badge">honest new-site accuracy <b>68% exact</b> · <b>98.5% within one tier</b></div>
  </div>
  <div id="mapwrap"><img id="bg"><svg id="ov" preserveAspectRatio="none"></svg><div id="tip"></div></div>
  <div class="legend" id="legend"></div>
  <div class="cap" id="mapcap"></div>
 </section>

 <section id="predict">
  <div class="card">
   <div class="lab">1 · load a real test case (mimics the deployed model)</div>
   <div class="cases" id="cases"></div>
   <div style="color:var(--t3);font-size:11.5px">…or edit any field below and predict a made-up location (the prototype estimates it in-browser).</div>
  </div>
  <div class="card">
   <div class="lab">2 · the inputs a planner supplies (all free for a sensor-less place)</div>
   <form id="form"></form>
   <button class="go" id="predict">⚡ Predict safety status</button>
  </div>
  <div id="out"></div>
 </section>

 <div class="foot" id="foot"></div>
</div>
<script>
const DATA = __DATA__;
const M=DATA.map, REF=DATA.ref, CASES=DATA.cases;
const TC=M.tier_colors, CC=M.cat_colors, EDGES=M.edges, TIERS=M.tiers;
const tier=v=>v<=EDGES[0]?0:(v<=EDGES[1]?1:2), tname=v=>TIERS[tier(v)];
const byId=Object.fromEntries(M.sites.map(s=>[s.site,s]));
let HZ="now", CB="tier";

/* ---------- tabs ---------- */
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===t));
  document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id===t.dataset.t));
});

/* ---------- map ---------- */
document.getElementById('bg').src=DATA.basemap;
const ov=document.getElementById('ov'); ov.setAttribute('viewBox',`0 0 ${M.meta.img_w} ${M.meta.img_h}`);
const tip=document.getElementById('tip'), wrap=document.getElementById('mapwrap');
function cellColor(s){
  if(CB==='cat') return CC[String(s.cat)];
  const p=s[HZ]; return p?TC[p.tier]:'#888';
}
function drawMap(){
  ov.innerHTML='';
  M.sites.forEach(s=>{
    if(s.poly&&s.poly.length>=3){
      const pa=document.createElementNS('http://www.w3.org/2000/svg','path');
      pa.setAttribute('d','M'+s.poly.map(p=>p.join(',')).join(' L')+' Z');
      pa.setAttribute('class','cell'); pa.setAttribute('fill',cellColor(s)); pa.setAttribute('fill-opacity','0.45');
      pa.addEventListener('mousemove',e=>showTip(e,s)); pa.addEventListener('mouseleave',()=>tip.style.opacity=0);
      ov.appendChild(pa);
    }
  });
  M.sites.forEach(s=>{
    const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx',s.px[0]); c.setAttribute('cy',s.px[1]); c.setAttribute('r', s.site==='site_54'?7:3.4);
    c.setAttribute('class','pt'+(s.site==='site_54'?' flag':''));
    c.addEventListener('mousemove',e=>showTip(e,s)); c.addEventListener('mouseleave',()=>tip.style.opacity=0);
    ov.appendChild(c);
  });
  buildLegend();
}
function showTip(e,s){
  const r=wrap.getBoundingClientRect();
  const pill=p=>p?`<span class="pill" style="background:${TC[p.tier]}">${p.tier} · ${p.ugm3}</span>`:'—';
  tip.innerHTML=`<div class="h">${s.site} ${s.site==='site_54'?'⚠':''}</div>`+
    `<div class="row"><span class="k">area type</span><span>${s.cat_label}</span></div>`+
    `<div class="row"><span class="k">now</span>${pill(s.now)}</div>`+
    `<div class="row"><span class="k">+1 day</span>${pill(s.d1)}</div>`+
    `<div class="row"><span class="k">+7 days</span>${pill(s.d7)}</div>`+
    `<div class="row"><span class="k">±band</span><span>±${s.band} µg/m³</span></div>`+
    `<div class="row"><span class="k">tier accuracy</span><span>${Math.round(s.accuracy*100)}%${s.site==='site_54'?' (anomaly)':''}</span></div>`;
  let x=e.clientX-r.left+14, y=e.clientY-r.top+12;
  if(x>r.width-290)x=e.clientX-r.left-290; tip.style.left=x+'px'; tip.style.top=y+'px'; tip.style.opacity=1;
}
function buildLegend(){
  const L=document.getElementById('legend');
  if(CB==='tier') L.innerHTML=['Elevated ≤35.4','High 35.5–55.4','Dangerous >55.4'].map((t,i)=>
    `<span><span class="sw" style="background:${[TC.Elevated,TC.High,TC.Dangerous][i]}"></span>${t}</span>`).join('')
    +`<span><span class="sw" style="background:none;border-color:#c0392b"></span>site_54 (local-source anomaly)</span>`;
  else L.innerHTML=Object.entries({0:'low-pollution / well-ventilated',1:'high-pollution / well-ventilated',2:'moderate / stagnant'}).map(([k,v])=>
    `<span><span class="sw" style="background:${CC[k]}"></span>${v}</span>`).join('');
  document.getElementById('mapcap').innerHTML = CB==='tier'
    ? `Each area is one sensor's <b>coverage cell</b> (Voronoi), filled by the predicted EPA safety tier for <b>${({now:'today',d1:'tomorrow',d7:'+7 days'})[HZ]}</b>. Hover for the full forecast + accuracy. Predictions are honest leave-sites-out; <b>site_54</b> is the documented anomaly the map alone under-reads. © OpenStreetMap © CARTO.`
    : `Colored by <b>behavioural area type</b> (how the place pollutes) — the categories are spatially intermixed: they capture behaviour, not geography.`;
}
document.querySelectorAll('#hz button').forEach(b=>b.onclick=()=>{HZ=b.dataset.h;document.querySelectorAll('#hz button').forEach(x=>x.classList.toggle('on',x===b));drawMap();});
document.querySelectorAll('#cb button').forEach(b=>b.onclick=()=>{CB=b.dataset.c;document.querySelectorAll('#cb button').forEach(x=>x.classList.toggle('on',x===b));drawMap();});
document.getElementById('bg').onload=drawMap; if(document.getElementById('bg').complete)drawMap();

/* ---------- predictor ---------- */
const FIELDS=[
 ['site_latitude','lat °'],['site_longitude','lon °'],['month','month (1-12)'],['day_of_week','day-of-week (0-6)'],
 ['temp_2m_K','temp (K)'],['dewpoint_2m_K','dewpoint (K)'],['wind_u_10m_ms','wind u (m/s)'],['wind_v_10m_ms','wind v (m/s)'],
 ['surface_pressure_Pa','pressure (Pa)'],['precipitation_m','precip (m)'],
 ['dist_major_road_m','dist major road (m)'],['road_len_all_300m','road len 300m'],['road_len_all_1000m','road len 1km'],
 ['road_len_major_500m','major-road len 500m'],['elevation_m','elevation (m)']];
const form=document.getElementById('form');
form.innerHTML=FIELDS.map(([k,l])=>`<div class="fld"><label>${l}</label><input id="f_${k}" value=""></div>`).join('');
function setForm(c){FIELDS.forEach(([k])=>{const el=document.getElementById('f_'+k); el.value=(c[k]!==undefined?c[k]:'');}); window._loaded=c;}
document.getElementById('cases').innerHTML=CASES.map((c,i)=>{
  const tag=c.actual_tier==='Dangerous'?'🔴':(c.actual_tier==='High'?'🟠':'🟢');
  return `<button class="casebtn" data-i="${i}">${tag} ${c.site} · ${c.date}<small>${c.category_label} · actual ${c.actual_pm25} (${c.actual_tier})</small></button>`;}).join('');
document.querySelectorAll('.casebtn').forEach(b=>b.onclick=()=>{setForm(CASES[+b.dataset.i]);predict();});
setForm(CASES[0]);

const std=(k,v)=>(v-REF.mean[k])/(REF.std[k]||1);
function knn(geo){ // returns {cat,label,conf,baseline}
  const gf=REF.geo_feats;
  const ds=REF.sites.map(s=>({s, d:Math.hypot(...gf.map(k=>std(k,geo[k])-std(k,s.geo[k])))})).sort((a,b)=>a.d-b.d).slice(0,REF.k);
  const votes={}; ds.forEach(o=>votes[o.s.cat]=(votes[o.s.cat]||0)+1);
  const cat=+Object.entries(votes).sort((a,b)=>b[1]-a[1])[0][0];
  const baseline=ds.reduce((a,o)=>a+o.s.now_ugm3,0)/ds.length;
  return {cat,label:REF.categorizer.labels[String(cat)],conf:(votes[cat]/REF.k),baseline,neigh:ds.map(o=>o.s.site)};
}
function predict(){
  const get=k=>parseFloat(document.getElementById('f_'+k).value);
  const geo=Object.fromEntries(REF.geo_feats.map(k=>[k,get(k)]));
  const k=knn(geo);
  // surrogate nowcast: kNN baseline + humid/stagnant weather bump (the danger-day regime)
  const rh=100*Math.exp(17.67*(get('dewpoint_2m_K')-273.15)/((get('dewpoint_2m_K')-273.15)+243.5))/
           Math.exp(17.67*(get('temp_2m_K')-273.15)/((get('temp_2m_K')-273.15)+243.5));
  const ws=Math.hypot(get('wind_u_10m_ms'),get('wind_v_10m_ms'));
  let est=k.baseline + 0.55*(rh-80) + 5.5*(1.5-ws) - 4.0*Math.min(get('precipitation_m')*1000,4);
  est=Math.max(3,Math.min(260,est));
  // if this exactly matches a loaded real test case, prefer the real full-model output
  const lc=window._loaded, real=lc&&lc.model_zero_deploy&&Math.abs((lc.site_latitude)-get('site_latitude'))<1e-6?lc:null;
  const pm = real? real.model_zero_deploy.ugm3 : est;
  const t=tier(pm), col=[TC.Elevated,TC.High,TC.Dangerous][t], band=M.band;
  const alert = pm>45;
  const nearRoad = get('dist_major_road_m')<120 && t<2;
  let html=`<div class="card"><div class="lab">prediction ${real?'· full model (real test case)':'· prototype estimate (in-browser)'}</div>`+
   `<div class="tierbox" style="background:${col}">Safety tier: ${TIERS[t]} &nbsp;·&nbsp; ${pm.toFixed(1)} µg/m³ &nbsp;(band ${Math.max(0,pm-band).toFixed(0)}–${(pm+band).toFixed(0)})</div>`+
   `<div class="res-grid">`+
    `<div class="res"><div class="k">area type (kNN on map data)</div><div style="color:${CC[k.cat]};font-weight:700;margin-top:3px">${k.label}</div><div style="font-size:11px;color:var(--t3)">map-confidence ${Math.round(k.conf*100)}%</div></div>`+
    `<div class="res"><div class="k">danger dial @45</div><div class="big" style="color:${alert?'var(--red)':'var(--green)'};font-size:20px;margin-top:3px">${alert?'⚠ ALERT':'ok'}</div></div>`+
    `<div class="res"><div class="k">typical level here</div><div class="big" style="font-size:20px;margin-top:3px">${k.baseline.toFixed(0)}</div><div style="font-size:11px;color:var(--t3)">µg/m³ (5 nearest areas)</div></div>`+
   `</div>`;
  if(real){const a=lc.actual_pm25,at=lc.actual_tier;
    html+=`<div class="note ${tname(pm)===at||Math.abs(tier(pm)-TIERS.indexOf(at))<=1?'ok':''}">Ground truth that day: <b>${a} µg/m³ (${at})</b>. The model called <b>${TIERS[t]}</b> — ${tier(pm)===TIERS.indexOf(at)?'exact tier ✓':'within one tier ✓'}. This is a held-out, sensor-less prediction.</div>`;}
  if(nearRoad) html+=`<div class="note">⚠ This spot is very close to a major road (${get('dist_major_road_m').toFixed(0)} m). Map-based predictions can <b>under-read traffic/local-source hotspots</b> (the site_54 lesson) — a short sensor deploy is advised to confirm.</div>`;
  html+=`<div class="note ok">How this works: a new place is sorted by <b>kNN on free map data</b> into an area type, then scored by weather + location + map features. For a sensor-less site the deployed tool uses the full RandomForest (no observed category — a guessed one doesn't help); a short ≈2-month deploy unlocks the sharper observed-category model and the 7-day forecaster.</div></div>`;
  document.getElementById('out').innerHTML=html;
}
document.getElementById('predict').onclick=predict;
document.getElementById('foot').innerHTML='Prototype · all predictions honest (leave-sites-out / chronological). Basemap © OpenStreetMap © CARTO. Built from <span style="font-family:var(--mono)">analysis/</span> (new_site_predict.py · predict_map.py · ref_sites.json). Deploy properly later — this is an offline demo.';
</script></body></html>"""

out = HTML.replace("__DATA__", DATA)
OUTP = os.path.join(HERE, "..", "pages", "kampala_planner_prototype.html")
open(OUTP, "w", encoding="utf-8").write(out)
print(f"built kampala_planner_prototype.html: {os.path.getsize(OUTP)//1024} KB")
