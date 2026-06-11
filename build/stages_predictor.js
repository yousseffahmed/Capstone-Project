const STAGES=[

/* ===================== THE NEW-SITE PREDICTOR — inputs (base) → proof (tip) ===================== */

{n:0,name:'The input contract',hue:'--s0',sections:[
  {label:'Point at any address',blurb:'lat/lon + date + free weather + auto geodata',node:N({
    kick:'🎯 what the planner supplies',
    title:'Aim at any Kampala spot — here is everything you provide',
    what:'The predictor turns a brand-new location into a PM2.5 read. For a place with <b>no sensor</b>, everything it needs is <b>free</b> and obtainable from the address alone — a lat/lon, the date, that day’s {{ERA5}} weather, and map geodata fetched automatically from the coordinates. A short temporary sensor is <i>optional</i> and only sharpens things.',
    blocks:[
      DLB([
        ['📍 location','site_latitude, site_longitude (decimal °)'],
        ['📅 date','→ month, day-of-week'],
        ['🌦 weather (free {{ERA5}})','temp, dewpoint, wind u/v, pressure, precip — humidity &amp; wind-speed derived'],
        ['🗺 geodata (auto from lat/lon)','dist-to-major-road, road density 300m/1km, major-road length 500m, elevation']
      ]),
      CO('Every <b>required</b> input is free and available at a never-visited address — nothing the planner could not actually obtain. That is what makes this a <b>zero-deploy</b> tool.','good')
    ],
    children:[
      N({kick:'🔁 two ways to use it',title:'Zero-deploy vs short-deploy',what:'How much you get depends on whether a temporary sensor was placed.',blocks:[
        TBL(['mode','what you supply','what you get'],[
          ['zero-deploy','address + weather + geodata','nowcast today + safety tier + band + danger alert'],
          ['short-deploy','+ ≈14–60 days of a temporary sensor','a sharper category + the 7-day forecaster seeded with real history']],null),
        CO('A planner with no budget gets the zero-deploy nowcast everywhere; one who can drop a cheap sensor for a few weeks unlocks the forecast and a tighter category.','good')
      ]}),
      N({kick:'⌨️ the contract, in code',title:'The exact inputs the model reads',what:'Straight from the deployable script’s header.',blocks:[
        CODE('new_site_predict.py','INPUT CONTRACT',"REQUIRED (zero-deploy):\n  site_latitude, site_longitude   # Kampala ~ lat 0.20-0.40, lon 32.50-32.70\n  date -> month, day_of_week\n  ERA5 weather: temp_2m_K, dewpoint_2m_K, wind_u/v_10m_ms,\n                surface_pressure_Pa, precipitation_m\n  geodata (auto from lat/lon): dist_major_road_m,\n                road_len_*, elevation_m\nOPTIONAL (short-deploy):\n  >= 14 days of recent daily PM2.5  (a temporary sensor)",'The honest rule: nothing target-coupled (no pm10 / n_obs) — only what a new address can actually give.'),
        N({kick:'📄 full script',title:'The whole deployable predictor',what:'Input contract → categorize → nowcast (tier+band+dial) → 7-day forecast → honest leave-one-site-out demo.',blocks:[
          FULLCODE('new_site_predict.py','Run: ./.venv/bin/python new_site_predict.py --demo site_135 — the end-to-end new-site predictor.')
        ]})
      ]})
    ]
  })}
]},

{n:1,name:'Categorize the place',hue:'--s2',sections:[
  {label:'What KIND of place is it?',blurb:'snap to 1 of 3 behavioural kinds',node:N({
    kick:'🧭 triage the new site',
    title:'Sort the new place into a kind of place',
    what:'Before predicting, the tool asks <b>what kind of place</b> this is — because Kampala’s weather is near-uniform, the <i>kind</i> (its pollution regime) is what tells the model a new site’s baseline level. The new site is snapped to the nearest of <b>3 categories</b>, by one of three routes depending on what you have.',
    blocks:[
      TBL(['category','n','PM2.5 mean','meaning'],[
        ['low / well-ventilated','24','31.7','the city baseline'],
        ['high / well-ventilated','12','47.5','hotter spots, still windy'],
        ['moderate / stagnant','3','46.5','low-wind + humid micro-regime']],null),
      CHART('fig_site_map_clusters','The 3 kinds are spatially INTERMIXED — they capture how a place behaves, not where it sits.')
    ],
    children:[
      N({kick:'🔢 three ways to get the category',title:'From geodata, a short window, or full history',what:'Each needs progressively more — and is progressively more reliable.',blocks:[
        TBL(['source','observations needed','use'],[
          ['geodata (roads + elevation)','zero','the pure zero-deploy guess'],
          ['60-day window','≈2 months of a sensor','the realistic cold-start category'],
          ['full history','a permanent sensor','the gold standard (known sites)']],null),
        P('The one thing computed <b>live</b> for an unseen site is its behavioural signature → nearest centroid in <code>categorizer.json</code>. Everything else is pre-trained.')
      ]}),
      N({kick:'📈 why three kinds',title:'Silhouette picks the usable split',what:'k chosen by the honest metric; later sharpened to k=4.',blocks:[
        CHART('fig_silhouette','k=3 is the usable routing split (24 / 12 / 3); re-tuning by honest new-site R² later sharpened it to k=4.')
      ]}),
      N({kick:'🔬 the blind-spot investigation',title:'Why the map mis-reads some sites — and what helps',what:'We dug into the one weak link: guessing a sensor-less site’s category from map data alone.',blocks:[
        STAT([{v:'0.538 → 0.641',k:'blind category accuracy (RF → kNN; clears 0.615 majority)',c:'g'},{v:'site_54',k:'a genuine local-source anomaly the map can’t read',c:'bad'}]),
        CHART('fig_blindcat_investigation','(1) a simple kNN beats the 4th-cap RandomForest and clears the majority baseline · (2) site_54 sits among LOW-pollution sites in map-feature space — its 62.9 µg/m³ isn’t legible from roads/elevation · (3) a GUESSED category does not help the nowcast — only an OBSERVED one does.'),
        CO('Three honest takeaways: (a) a simpler <b>kNN</b> guesses the area-type better than the 4th-cap RF (0.54 → 0.64, now beating the majority baseline); (b) <b>a guessed category does NOT improve the µg/m³ nowcast</b> — a wrong guess misleads it, so for a truly sensor-less place the model leans on weather + map features <i>directly</i>, and the category lever pays off only with a short deploy; (c) <b>site_54</b> is a real anomaly — its pollution has a local source no free feature sees, so some places will always need a cheap sensor to confirm.','warn')
      ],children:[
        N({kick:'🧭 what misled site_54',title:'High-pollution, but its map fingerprint says “quiet”',what:'Its 6 nearest map-neighbours are all low-pollution sites.',blocks:[
          TBL(['','site_54','its 6 map-neighbours'],[
            ['true pollution','62.9 µg/m³ (highest of 39)','27–33 µg/m³ (all low)'],
            ['nearest major road','60 m (looks high-traffic)','—'],
            ['road-length + elevation','look residential','low-pollution pattern']],null),
          P('Closeness to a major road <i>should</i> flag it, but its high major-road <i>length</i> and elevation make it read like a calm residential area. The only zero-deploy feature that tracks pollution level at all is distance-to-major-road (r=−0.35 — weak). Net: the map can’t see <i>why</i> site_54 is so polluted — a textbook case for a confirming sensor. Scripts: <span style="font-family:var(--mono)">investigate_categorization.py · improve_blind_cat.py</span>.')
        ]}),
        N({kick:'🌍 the real-world answer (external check)',title:'It’s the Kalerwe market + abattoir + bypass junction',what:'A web investigation of site_54’s exact coordinates — outside our data — found a real local source.',blocks:[
          P('Reverse-geocoding site_54’s coordinates (0.3519, 32.5726) lands it within ~50–80 m of the <b>Kalerwe Market &amp; abattoir on Gayaza Road at the Northern-Bypass junction</b> (Nsooba / Kyebando, Kawempe) — confirmed by OpenStreetMap + Wikipedia. That one spot stacks four PM2.5 sources its residential neighbours lack: a giant open-air market (~<b>1,548 t of waste/week</b>, much openly burned), an abattoir draining the Nsooba channel, a congested diesel matatu/boda interchange (the “60 m from a major road” clue), and a flood-prone wetland bottom that traps the plume.'),
          CO('The clincher for our finding: the real source is <b>land use</b> (a market), which our road-geometry features physically can’t see — so the model <i>correctly</i> flagged site_54 as “needs a sensor”. The Jan-2020 ≈130 µg/m³ spike adds dry-season regional biomass-burning smoke on northerly winds. Sources: OpenStreetMap · Wikipedia (Kalerwe Market) · The Observer · RSC <i>Environ. Sci.: Atmospheres</i> 2025.','good')
        ]})
      ]})
    ]
  })}
]},

{n:2,name:'Nowcast today',hue:'--s4',sections:[
  {label:'A number → a safety status',blurb:'tier 68% · within-1 98.5% · a danger dial',node:N({
    kick:'🟢 PM2.5 today + safety tier + band + alert',
    title:'Today’s particle: a number, a tier, a band, and an alert',
    what:'The nowcast model (RandomForest on weather + location + the category + geodata) outputs PM2.5 <b>today</b>, then translates it into what a planner actually needs: an <b>EPA safety tier</b>, a calibrated <b>uncertainty band</b>, and a tunable <b>danger alert</b>. Honest (leave-sites-out) best: {{R²}} <b>0.547</b>; graded by tier, <b>68% exact · 98.5% within one tier</b>.',
    blocks:[
      bh(TGL([
        {label:'the NOW ladder',fig:'fig_now_ladder',cap:'Each lever on the honest new-site test. +geodata needs zero observations; +category+geodata is best and tightest (±0.046).',
         table:{head:['NOW variant','new-site R²','needs a sensor?'],rows:[
           ['blind','0.316','—'],['+ geodata only','0.421','NO — zero obs'],
           ['+ category','0.482','yes (≈60-day deploy)'],['+ category + geodata','0.547','yes — best']]},
         note:'Category + free map data together recover the 3rd-cap collapse (0.32) to a deployable 0.55.'}
      ]),'the nowcast engine'),
      STAT([{v:'68%',k:'exact safety tier (new-site)',c:'g'},{v:'98.5%',k:'within one tier',c:'g'},{v:'3.6%',k:'a Dangerous area called “safe”',c:'g'}]),
      CO('R² ≈0.55 sounds modest, but it punished a 47-vs-52 µg/m³ miss — in <b>safety tiers</b> those land in the SAME band. As a triage tool, the new-site nowcast is deployable.','good')
    ],
    children:[
      N({kick:'🎚 the planner’s danger dial',title:'Catch more dangerous days, by choice',what:'Lower the alert cutoff → more dangerous days caught, more false alarms. The planner picks the point.',blocks:[
        TBL(['alert if predicted >','dangerous recall','false alarms'],[
          ['55.4 (strict EPA)','0.51','4%'],['50','0.67','8%'],['45 (suggested)','0.80','17%'],['40','0.91','30%']],null),
        CHART('fig_danger_recall','80% of dangerous days caught at a 45 µg/m³ alert cutoff — the safety operating point is the planner’s to choose.')
      ]}),
      N({kick:'📊 the uncertainty band',title:'A calibrated range, not a false point',what:'Group conformal — honest about new-site error.',blocks:[
        STAT([{v:'≈86%',k:'new-site band coverage (was 75%)',c:'g'},{v:'28→43',k:'µg/m³ band width (honest)',c:'w'}]),
        P('Every nowcast carries a band that <b>covers the truth ≈86% of the time</b> at a brand-new site (calibrated on whole held-out sites, not rows). The band widens honestly because a never-seen place genuinely is harder to call.')
      ]}),
      N({kick:'🟢 one day, what the planner sees',title:'The output card',what:'A single day from the held-out demo site (site_135).',blocks:[
        DLB([['predicted','27.0 µg/m³'],['tier','🟡 Elevated'],['band','[3, 51] µg/m³ (≈90%)'],['danger-dial @45','ok — not flagged'],['actual that day','18.6 µg/m³ — Elevated ✓']]),
        CO('The number, its tier, its band, and the alert verdict — everything an official needs to act, for a site with no sensor.','good')
      ]})
    ]
  })}
]},

{n:3,name:'Forecast the next week',hue:'--s6',sections:[
  {label:'+1 to +7 days ahead',blurb:'beats “same as yesterday” all week',node:N({
    kick:'🔮 the next 7 days',
    title:'Where it is heading: a real 7-day forecast',
    what:'With a short sensor history, the tool forecasts PM2.5 <b>+1 to +7 days</b> ahead. A purpose-built forecaster ({{LSTM}} with a category embedding) <b>beats “same as yesterday” at every horizon</b> and holds {{R²}}≈0.43 a full week out — overturning the old “forecasting is hopeless past a day” read.',
    blocks:[
      bh(TGL([
        {label:'R² vs horizon',fig:'fig_bakeoff_future',cap:'LSTM (top) beats GBM-on-lags beats {{persistence}} (bottom, decaying to ~0). All beat persistence; the LSTM’s lead widens with horizon.',
         table:{head:['horizon','{{persistence}}','LightGBM-on-lags','{{LSTM}} (production)'],rows:[
           ['+1 day','0.34','0.43','0.506'],['+3 days','0.11','0.37','0.477'],['+7 days','0.01','0.33','0.432']]},
         note:'The portable demo uses the LightGBM-on-lags forecaster (torch-free); production uses the marginally-stronger locked LSTM.'}
      ]),'the forecast engine'),
      CO('“Same as yesterday” collapses to ~0 by a week out; the real forecaster still explains ~43% of the variance at +7d. That gap is the usable product.','good')
    ],
    children:[
      N({kick:'🚦 safety tiers on the forecast too',title:'A safety colour for each of the next 7 days',what:'The same EPA-band reframe, applied ahead.',blocks:[
        TBL(['horizon','exact tier','within 1 tier','beats'],[
          ['NOW (today)','0.68','0.985','0.52 majority'],
          ['+1 day','0.70','0.983','0.68 persistence'],
          ['+7 days','0.68','0.983','0.64 persistence']],null),
        P('A planner gets a <b>colour for each of the next seven days</b> — right to the exact tier ≈68% of the time, within one tier ≈98%.')
      ]}),
      N({kick:'🔥 the forecaster in action',title:'A dangerous week, called ahead',what:'The held-out high-pollution site, forecast +1…+7d from a short history.',blocks:[
        CHART('fig_newsite_demo_hi','Held-out site_54 (a Dangerous-heavy place): seeded with a short history, the 7-day forecaster (orange) tracks the dangerous spikes a planner needs warning of.'),
        TBL(['horizon','forecast µg/m³','actual µg/m³','tier called'],[
          ['+1d','102.9','129.7','Dangerous ✓'],['+5d','56.9','70.0','Dangerous ✓'],['+7d','60.9','99.4','Dangerous ✓']],null),
        CO('Even where the zero-deploy <i>nowcast</i> for this site struggles (its kind is hard to read from the map), a short deploy lets the <i>forecaster</i> flag the whole dangerous week.','good')
      ]})
    ]
  })}
]},

{n:4,name:'Proof it works',hue:'--s7',sections:[
  {label:'A real held-out site',blurb:'leave-one-site-out · honest',node:N({
    kick:'✅ does it actually work on a new place?',
    title:'Proof: predict a site the model never saw',
    what:'The honest test holds out a <b>whole site</b>, trains on the other 38, and predicts the held-out one — exactly the cold-start a planner faces. Across all 39 sites the leave-sites-out mean is {{R²}} <b>0.547</b> (the validation number). Single sites vary widely (folds 0.03–0.71), so we read the <b>mean</b>, never one cherry-picked site.',
    blocks:[
      CHART('fig_newsite_demo','Held-out site_135: the nowcast (teal, with ≈90% band) tracks the actual PM2.5 (grey), and the 7-day forecast (orange) is checked against truth — for a site trained-out entirely.'),
      STAT([{v:'0.547',k:'leave-sites-out MEAN R² (the real number)',c:'g'},{v:'68% / 98.5%',k:'safety tier — exact / within-1',c:'g'},{v:'≈86%',k:'uncertainty-band coverage',c:'g'}]),
      CO('The headline is the <b>average over all held-out sites</b>, not a hand-picked one. site_135 nailed its tiers (76.5% exact, 100% within-one); a hard site can still miss — both are shown, honestly.','good')
    ],
    children:[
      N({kick:'⌨️ run it yourself',title:'One command, reproducible',what:'The deployable script does the whole honest demo.',blocks:[
        CODE('new_site_predict.py','demo',"# hold site_135 out, train on the other 38, predict + grade it\n$ ./.venv/bin/python new_site_predict.py --demo site_135\n# prints: input contract -> category -> nowcast (R², tier,\n#   band, danger-dial) -> +1..+7d forecast vs actual\n# writes: results/fig_newsite_demo.png · results/newsite_demo.csv",'Fixed seed 42; honest leave-one-site-out — the held-out site is never in training.'),
        N({kick:'📄 full script',title:'The deployable predictor, end to end',what:'Everything from the input contract to the honest demo + figure.',blocks:[
          FULLCODE('new_site_predict.py','The new-site predictor: zero-deploy nowcast + short-deploy forecast + leave-one-site-out validation.')
        ]})
      ]}),
      N({kick:'📊 the honest scorecard',title:'Every NOW number, one table',what:'The leave-sites-out ladder + the safety-tier summary behind the predictor.',blocks:[
        CSVTBL('eval_external.csv','The NOW ladder — each lever’s honest new-site R² (± fold std).'),
        CSVTBL('band_summary.csv','Safety-tier + danger-dial summary — NOW and FUTURE, with the planner-tunable recall dial.')
      ]}),
      N({kick:'⚠️ the honest hard case',title:'When zero-deploy is not enough',what:'A site whose kind the map mis-reads.',blocks:[
        P('Held-out <b>site_54</b> is genuinely high-pollution, but its category read from geodata alone is wrong → the pure zero-deploy nowcast under-predicts it. This is the documented limit (geodata can’t always name the kind). The fix is a short deploy: with ≈2 months of a temporary sensor, the category sharpens and the forecaster flags its dangerous week (shown above). <b>Stated plainly, not buried.</b>'),
        CO('The tool is honest about where it is strong (most sites, all tiers) and where it needs a cheap sensor (regime-ambiguous sites). That boundary is itself the finding.','warn')
      ]})
    ]
  })}
]},

{n:5,name:'The planner map · point Z',hue:'--s7',sections:[
  {label:'Every area, one glance',blurb:'safety tier per coverage cell · now/+1d/+7d',node:N({
    kick:'🗺 the deployable view',
    title:'The planner map — predicted safety tier for every monitored area',
    what:'The synthesis a city official actually uses: a Kampala map where each sensor’s <b>coverage cell</b> (a Voronoi area) is coloured by its predicted EPA safety tier, switchable across <b>now / +1 day / +7 days</b>. The {{R²}} numbers become a colour a planner can act on.',
    blocks:[
      CHART('fig_safety_map','Predicted EPA tier per sensor coverage area (Voronoi), now / +1 day / +7 days. Green Elevated · amber High · red Dangerous. site_54 (circled) is the flagged anomaly. © OpenStreetMap © CARTO.'),
      CO('This is <b>point Z</b> — the deployable artefact. An <b>interactive</b> version (horizon filters · hover tooltips with each area’s forecast + accuracy · a “predict any new location” page) ships as <span style="font-family:var(--mono)">kampala_planner_prototype.html</span> — a self-contained offline prototype.','good')
    ],
    children:[
      N({kick:'🎛 the agentic prototype',title:'Two tools in one offline page',what:'What the prototype demonstrates, end to end.',blocks:[
        DLB([
          ['🗺 Safety map','every monitored area coloured by predicted tier; switch now/+1d/+7d; hover for the forecast + accuracy; toggle to area-type'],
          ['🎛 Predict a location','type the free inputs for a new place → in-browser category (kNN) + nowcast tier + band + danger dial; 3 real test cases mimic the deployed model'],
          ['Honest by design','all predictions leave-sites-out / chronological; site_54 shown as the anomaly; clearly a prototype to deploy properly later']
        ]),
        CO('The prototype reuses the persisted results (no heavy model in the browser): the map bakes in honest predictions; the predict page kNN-categorises against the 39 reference sites and shows the full model’s call on the test cases.','good')
      ]})
    ]
  })}
]}

,{n:6,name:'Final audit guardrail',hue:'--s5',sections:[
  {label:'What the tool should claim',blurb:'accepted k=4 · LSTM · challengers only',node:N({
    kick:'✅ final honest audit',
    title:'The deployable tool stays on the accepted production path',
    what:'The audit sharpened the defense, not the production setting. k=6 is <b>meaningful but fragile</b>; k=6 full-history is a <b>non-deployable upper bound</b>; deployable k=6 improves with <b>30-45 days</b> but does <b>not</b> beat accepted k=4. So the browser-facing tool should still present <b>k=4 for NOW/safety</b> and the <b>LSTM as the FUTURE headline</b>.',
    blocks:[
      TBL(['claim','status'],[
        ['accepted production remains k=4 for NOW/safety','keep'],
        ['LSTM remains headline FUTURE forecaster','keep'],
        ['RF / rolling-7 persistence','challenger baselines only'],
        ['k=6 full-history','oracle/non-deployable upper bound']],null),
      CO('What not to claim: k=6 is the new production model; RF beats LSTM overall; random split is real-world performance; full-history category assignment is deployable at a new site.','warn')
    ]
  })}
]}

];
