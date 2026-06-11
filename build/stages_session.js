const STAGES=[
{n:0,name:'This session’s mission',hue:'--s0',sections:[
  {label:'Push the scores · new scope',blurb:'reproduce → improve → safety tiers',node:N({
    kick:'🧠 what this session did',
    title:'Beat the 4th-cap honest numbers — and adopt the safety-status scope',
    what:'Starting from the finished 4th cap, this session (a) <b>reproduced every baseline</b> in a clean environment, (b) pushed for <b>better honest scores</b>, and (c) reframed the output as a planner <b>safety-tier</b> tool. Rule kept throughout: a win counts only if it holds on the honest splits (leave-sites-out / chronological).',
    blocks:[
      STAT([{v:'0.506',k:'LSTM +1d baseline — reproduced EXACT',c:'g'},{v:'0.541',k:'+cat+geodata — reproduced (doc 0.547)',c:'g'},{v:'3',k:'real wins · several honest negatives',c:'w'}]),
      CO('Mac venv could not run in the Linux sandbox; a fresh venv reproduced the baselines exactly before any change — so every delta below is real, not an environment artefact.','good')
    ],
    children:[
      N({kick:'📝 what was attempted',title:'The full slate',what:'Wins and dead-ends, all kept.',blocks:[
        DLB([['✅ k=4 categories','deploy-only nowcast 0.47 → 0.56 (significant)'],['✅ group conformal','new-site coverage ≈75% → 86%'],['✅ safety-tier framing','68% exact tier · 98.5% within one · 80% danger recall'],['✖ bigger/ensembled LSTM','no gain — simple net is the ceiling'],['✖ stacking','+0.003 — within noise'],['✖ extra geodata (buildings)','saturated, +0.00'],['✖ weighted danger classifier','beaten by a simple threshold']])
      ]})
    ]
  })}
]},

{n:1,name:'Sharper model',hue:'--s4',sections:[
  {label:'Finer categories',blurb:'k=4 · 0.47 → 0.56',node:N({
    kick:'⌨️ improve_now_sweep.py',
    title:'Tune the category count by the honest metric — not silhouette',
    what:'The earlier caps fixed k=3 by silhouette. Re-tuning by the metric that matters — honest new-site {{R²}} — <b>k=4</b> lifts the deploy-only nowcast (category, no geodata) from <b>0.470 → 0.558</b>, and it holds <b>fold-safe</b> (centroids fit on train sites only → 0.563), so it is not a categorizer leak.',
    blocks:[
      STAT([{v:'0.558',k:'+cat k=4 (deploy-only, was 0.470)',c:'g'},{v:'0.563',k:'fold-safe — not a leak',c:'g'},{v:'+1.07',k:'µg/m³ paired RMSE drop · CI[+0.33,+1.90]',c:'g'}]),
      CHART('fig_improve_now','Honest new-site R² vs number of categories. k=4 is the robust sweet spot; k=6 (0.585) spawns a one-site cluster — fragile with 39 sites.'),
      CO('On the best +cat+geodata model k barely matters (0.547 → 0.564, not significant): geodata already supplies the spatial signal finer tiers would add. The k=4 win is specifically the no-geodata deploy path.','warn')
    ],
    children:[
      N({kick:'🧪 stacking — no gain',title:'The model still is not the bottleneck',what:'Stacked RF+XGB+LGBM → ridge meta.',blocks:[
        P('A stacked ensemble scored <b>0.564</b> vs the best single learner 0.561 — <b>+0.003</b>, inside fold noise. The category <i>feature</i> moves {{R²}}; swapping the learner does not.')
      ]}),
      N({kick:'📈 uncertainty — fixed',title:'Group conformal lifts new-site coverage',what:'Calibrate on held-out SITES, not rows.',blocks:[
        STAT([{v:'≈75%',k:'naive coverage (target 90%)',c:'bad'},{v:'85.8%',k:'group conformal (held-out sites)',c:'g'},{v:'28→43',k:'µg/m³ band width (honest)',c:'w'}]),
        P('Naive split-conformal calibrates on held-out rows of <i>seen</i> sites, so it is over-confident at an <i>unseen</i> one. Calibrating on whole held-out sites matches the new-site regime — coverage climbs toward 90%, and the bands widen honestly to reflect the larger new-site error.')
      ]}),
      N({kick:'🧪 forecast — at the ceiling',title:'A bigger / ensembled LSTM does not help',what:'Two honest negatives, kept.',blocks:[
        TBL(['attempt','result'],[['2-layer hidden-64 LSTM','0.465 vs 0.506 — WORSE'],['LSTM + GBM ensemble','+0.001 R² — no gain']],1),
        CO('39 sites favour the simple 1-layer net; the 4th-cap LSTM (0.51 → 0.43) is the practical ceiling for this data.','warn')
      ]}),
      N({kick:'🧪 more geodata — dead end',title:'Building density adds nothing',what:'Validated stable first, then rejected.',blocks:[
        P('OSM building density fetched stably for all 39 sites (no gaps) and correlates with PM2.5 (r=+0.33) — but adds only <b>+0.001–0.007</b> {{R²}}. The spatial signal is already saturated by roads + elevation + categories. Kept as an honest negative; not adopted.')
      ]})
    ]
  })}
]},

{n:2,name:'Safety tiers (the tool)',hue:'--s7',sections:[
  {label:'A number → a status',blurb:'exact tier 68% · ±1 tier 98.5%',node:N({
    kick:'⌨️ band_now.py · band_future.py',
    title:'Grade by the safety TIER, not the exact number',
    what:'The deliverable is a planner triage tool: tell an official an area’s <b>safety tier</b>, not 47 vs 52 µg/m³. Grading the same honest predictions by the <b>EPA band</b> (Elevated ≤35.4 · High 35.5–55.4 · Dangerous >55.4) reframes the collapse — the {{R²}} "misses" are mostly inside the same tier.',
    blocks:[
      STAT([{v:'68%',k:'exact tier · honest new-site',c:'g'},{v:'98.5%',k:'within one tier',c:'g'},{v:'3.6%',k:'a Dangerous area called "safe" (rare)',c:'g'}]),
      TBL(['honest test','exact tier','within 1 tier','baseline'],[
        ['NOW new-site','0.680','0.985','0.52 majority'],
        ['FUTURE +1d','0.702','0.983','0.68 persistence'],
        ['FUTURE +7d','0.677','0.983','0.64 persistence']],null),
      CO('R² ≈0.57 looked weak because it punished a 47-vs-52 miss; in safety tiers those are the SAME band — so the new-site tool is deployable for planner triage.','good')
    ],
    children:[
      N({kick:'📈 the planner’s dial',title:'Catch more dangerous days, by choice',what:'Lower the Dangerous alert cutoff → recall vs false alarms.',blocks:[
        TBL(['alert if predicted >','dangerous recall','false-alarm rate'],[
          ['55.4 (strict EPA)','0.51','4%'],['50','0.67','8%'],['45 (suggested)','0.80','17%'],['40','0.91','30%']],null),
        CHART('fig_danger_recall','The safety operating point is the planner’s to choose: 80% of dangerous days caught at a 45 µg/m³ alert cutoff.')
      ]}),
      N({kick:'🧠 what marks a dangerous day',title:'A humid, stagnant weather regime',what:'Crimson’s feature idea — which inputs separate dangerous days.',blocks:[
        TBL(['feature','separation (effect size)'],[['rel_humidity','0.63'],['dewpoint','0.50'],['wind_v','0.36'],['temp','0.34']],1),
        P('Dangerous days are humid and stagnant — air that traps particulates. The model keys on weather to flag danger at a sensor-less site, reinforcing weather as the generalizable lever.')
      ]}),
      N({kick:'🧪 honest negative',title:'A weighted classifier did not beat it',what:'Crimson’s "upweight the dangerous case", tested honestly.',blocks:[
        P('A dedicated class-weighted "Dangerous-vs-not" classifier did <b>not</b> beat simply lowering the regressor’s threshold (at the same 8% false-alarm rate: recall 0.58 vs 0.67). The simpler lever wins — kept as a negative.')
      ]})
    ]
  })}
]},

{n:3,name:'Final audit',hue:'--s5',sections:[
  {label:'Keep production unchanged',blurb:'k=6 upper bound · k=4 stays accepted',node:N({
    kick:'✅ honest improvement audit',
    title:'We did not replace the model just because one score looked better',
    what:'The final audit tested whether the stronger-looking k=6 and RF/rolling-7 results were honest enough to replace production. Answer: <b>no production replacement</b>. k=6 is meaningful but fragile; its full-history score is a <b>non-deployable upper bound</b>. Deployable k=6 improves with <b>30-45 days</b> but still does <b>not</b> beat accepted k=4.',
    blocks:[
      STAT([{v:'k=4',k:'accepted NOW/safety production remains',c:'g'},{v:'0.506',k:'best deployable k=6 at 45d — below k=4',c:'w'},{v:'LSTM',k:'headline FUTURE forecaster remains',c:'g'}]),
      TBL(['candidate','honest result','decision'],[
        ['k=6 full-history','≈0.56-0.58 R²','oracle upper bound only'],
        ['k=6 deployable 45d','0.506 R²','challenger, not replacement'],
        ['RF / rolling-7 FUTURE','strong at some horizons','challenger baselines only']],null),
      CO('What not to claim: k=6 is production; RF beats LSTM overall; random split is real-world performance; or full-history category assignment is deployable at a new site.','warn')
    ]
  })}
]}
];
