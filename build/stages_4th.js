const STAGES=[
{n:0,name:'The collapse',hue:'--s0',sections:[
  {label:'The honest problem',blurb:'leaky 0.81 → real 0.31',node:N({
    kick:'🧠 why we re-scoped',
    title:'A model that looks great — until you point it somewhere new',
    what:'The 3rd-cap model scored a headline {{R²}} ≈ <b>0.81</b>. But that is a <b>leaky</b> random split: it tests on the same sensors it trained on (gap-filling). Graded honestly — hide WHOLE sensors ({{GroupKFold}}), or forecast the real future — it <b>collapses</b>: new-site {{R²}} ≈ 0.31 (one fold near 0), future ≈ 0.11, and a "same-as-yesterday" {{persistence}} guess beats it out-of-time. A planner needs PM2.5 where there is <b>no sensor</b>; the old tool can not be trusted there.',
    blocks:[
      STAT([{v:'0.81',k:'leaky random-split R² (gap-filling)',c:'w'},{v:'0.31',k:'honest new-site R² (collapse)',c:'bad'},{v:'~0',k:'one new-site fold',c:'bad'}]),
      CO('The whole 4th cap exists to answer one question: <b>can we stop the collapse at a sensor-less place — and a few days ahead — without faking the test?</b>','warn')
    ],
    children:[
      N({kick:'🧠 the doctor analogy',title:'One generalist vs a triage clinic',what:'Why categorize-then-predict should help.',blocks:[
        P('The old model is <b>one doctor</b> who treats every patient identically and falls apart on an unfamiliar case. The new model is a <b>clinic</b>: a triage nurse first sorts each place into a <i>kind of place</i> (its category), then the specialist for that kind makes the call. A stranger is no longer a stranger — it is "a patient of type B," and we have a type-B specialist ready.'),
        CO('If even that can not rescue a sensor-less site, that is itself a publishable finding — "Kampala is too homogeneous to categorize." We test it honestly either way.','good')
      ]}),
      N({kick:'📈 two metrics, kept apart',title:'NOW and FUTURE are different problems',what:'Different question, different honest test, different bar, different best model — separated end to end.',blocks:[
        TBL(['','NOW — nowcast','FUTURE — forecast'],[
          ['Question','PM2.5 today at a sensor-less place','PM2.5 +1…7 days at a known place'],
          ['Honest test','leave-sites-out ({{GroupKFold}})','blocked chronological'],
          ['Bar to beat','the blind pooled model','{{persistence}} ("same as yesterday")'],
          ['Best model (result)','RandomForest + category','{{LSTM}} + category embedding']],null),
        CO('Conflating these two is exactly what produced the misleading "persistence beats the model" claim — see the verdict stage.','warn')
      ]})
    ]
  })},
  {label:'The 39 sensors',blurb:'one small city · 13,944 site-days',node:N({
    kick:'📊 the data',
    title:'39 low-cost sensors, ~84% daily coverage, one merged table',
    what:'Everything is learned from 39 {{AirQo}} sensors around greater Kampala — 13,944 site-days (2019-05 → 2020-12), one row per site-day. Predictors are FREE and available at a sensor-less place: {{ERA5}} weather + location + calendar. <b>pm10 and n_obs are banned</b> as predictors (target-coupled). {{LST}} is carried but proven inert.',
    blocks:[
      STAT([{v:'39',k:'AirQo sensors',c:'g'},{v:'13,944',k:'site-days',c:''},{v:'~84%',k:'daily coverage (gappy)',c:'w'},{v:'38',k:'µg/m³ mean PM2.5',c:''}]),
      MAP(),
      CO('These same 39 dots become the <b>exam</b>: we hide whole sensors during training and test only on them — a neighbourhood the model has never seen.','good')
    ],
    children:[
      N({kick:'🧠 why these predictors',title:'Cheap, generalizable, and honest',what:'Weather transfers; pm10/n_obs would cheat.',blocks:[
        P('{{ERA5}} weather is the proven generalizable lever (3rd cap). <b>pm10</b> is the same instrument as the target (corr ≈ 0.9) and <b>n_obs</b> is a by-product of the daily mean — neither is available at a place with no sensor, so using them would manufacture a fake win. Both excluded everywhere.'),
        CO('Honest features first: nothing the planner could not actually obtain at a new address.','good')
      ]})
    ]
  })}
]},

{n:1,name:'Categorize (CP-A)',hue:'--s1',sections:[
  {label:'3 kinds of place',blurb:'24 low · 12 high · 3 stagnant',node:N({
    kick:'⌨️ site_categorize.py',
    title:'Turn 39 sensors into 3 behavioural kinds of place',
    what:'Each site gets a <b>signature</b> from how it behaves — pollution level/volatility/seasonality + local climate, <b>not</b> coordinates (routing should follow behaviour, not geography). k-means (k chosen by silhouette among k≥3, Ward sanity-check) resolves 39 sites into <b>3 categories</b>: 24 low-pollution, 12 high-pollution, 3 stagnant outliers.',
    blocks:[
      TBL(['Category','n','PM2.5 mean','PM2.5 p90','wind','signature'],[
        ['low / well-ventilated','24','31.7','48.7','1.62','the city baseline'],
        ['high / well-ventilated','12','47.5','73.4','1.58','hotter spots, still windy'],
        ['moderate / stagnant','3','46.5','73.5','1.15','low wind + humid — a robust micro-regime']],null),
      CHART('fig_site_map_clusters','The 3 categories are spatially INTERMIXED — they capture behaviour, not geography.')
    ],
    children:[
      N({kick:'📈 how many kinds?',title:'Silhouette picks the usable split',what:'k=2 wins silhouette but is just an outlier-peel (36 vs 3); k=3 is the usable planning split.',blocks:[
        CHART('fig_silhouette','Silhouette by k. k=2 is a coarse outlier-peel; k=3 [24,12,3] is the usable routing split.'),
        P('The 3 stagnant sites are <b>robust</b> — the same 3 at every k, and k-means agrees with Ward ({{Spearman|ARI}}=1.0). A real micro-regime, not noise. Finding: Kampala is fairly homogeneous in <i>level</i>; the structure is low-vs-high pollution + 3 stagnant outliers.')
      ]}),
      N({kick:'⌨️ the signature',title:'What KIND of place is this?',what:'Eight behavioural features per site — four from PM2.5, four from local climate; no coordinates.',blocks:[
        CODE('features.py','site_signature',"return {\n  \"pm25_mean\": g.pm2_5.mean(), \"pm25_std\": g.pm2_5.std(),\n  \"pm25_p90\": g.pm2_5.quantile(0.90),\n  \"pm25_season_amp\": _seasonal_amplitude(...),\n  \"temp_mean\": ..., \"humidity_mean\": ...,\n  \"windspeed_mean\": ..., \"precip_mean\": ... }",'Behaviour + climate, no lat/lon — so routing follows how a place acts, not where it sits.'),
        N({kick:'📄 full script',title:'The whole categorizer',what:'Signature build → k scan → Ward check → profile + name → portable categorizer saved.',blocks:[
          FULLCODE('site_categorize.py','Proves the categories are real (k-means==Ward) and reproducible for a future site.')
        ]})
      ]}),
      N({kick:'🧠 the one live leak',title:'How a NEW site gets its category',what:'The single thing computed live for an unseen site.',blocks:[
        P('A brand-new site is categorized by computing its signature from a <b>short window of observed data</b>, then snapping to the nearest category centroid (saved in <code>categorizer.json</code>). This is the one and only thing computed live for an unseen site — a controlled, single leak. Stage 2 tests how much it actually costs when that window is short and the category is noisy.')
      ]})
    ]
  })}
]},

{n:2,name:'Route & test honestly (CP-B)',hue:'--s2',sections:[
  {label:'The honest ladder',blurb:'category beats blind: 0.32 → 0.48',node:N({
    kick:'⌨️ pipeline.py',
    title:'Categorize → route → predict, on a 3-rung honest ladder',
    what:'Climb only if the rung below holds: (1) random split (go/no-go) → (2) leave-sites-out ({{GroupKFold}}) → (3) leave a WHOLE category out. Compare blind vs +category at each rung. <b>The win:</b> on the honest new-site test, adding the category lifts {{R²}} from blind <b>0.316 → 0.482</b> — most of the 3rd-cap collapse, recovered.',
    blocks:[
      bh(TGL([
        {label:'new-site (cat known)',fig:'fig_now_ladder',cap:'Climb the honest ladder left→right. +category clears the blind baseline on the new-site rungs; everything goes negative when a whole category is unseen.',
         table:{head:['variant','random','new-site','leave-cat-out'],rows:[
           ['blind','0.808','0.316','−0.303'],['+category','0.808','0.482','−0.217'],
           ['+cat+prior','0.772','0.483','−0.413'],['MoE','0.771','0.497','−0.404']]},
         note:'Random split (leaky) hides the difference — the category only pays off on the honest new-site test.'}
      ]),'the honest ladder'),
      CO('Mechanism: Kampala weather is near-uniform, so a blind model can not know a new site’s baseline level and predicts the city mean. The category hands it a learned per-tier intercept.','good')
    ],
    children:[
      N({kick:'📝 is the lift real?',title:'Significant — not fold noise',what:'Paired per-site bootstrap, blind vs +category, n=39 sites.',blocks:[
        STAT([{v:'+1.60',k:'µg/m³ mean RMSE reduction',c:'g'},{v:'[+0.40,+2.92]',k:'95% bootstrap CI (excludes 0)',c:'g'},{v:'26/39',k:'sites improved',c:'g'}]),
        P('The CI excludes zero — the category lift survives the high fold-to-fold variance ({{R²}} folds range 0.03–0.71).')
      ]}),
      N({kick:'🧪 soft routing wins',title:'Why category-as-feature, not experts',what:'Mixture-of-experts collapses under realistic cold-start.',blocks:[
        TBL(['routing','cat KNOWN','cat from 60-day deploy'],[['+category (soft)','0.482','0.433'],['{{MoE}} (hard)','0.497','0.298']],1),
        P('When the category is cheaply estimated from a 60-day window it is <b>wrong 41% of the time</b>. {{MoE}} hard-routes a mis-labelled site to the wrong specialist → collapses below blind (0.30). Category-as-a-feature is <b>soft</b> routing — the model discounts a noisy feature and degrades gracefully (0.43).'),
        CO('Decision: category-as-feature, not mixture-of-experts. Soft routing tolerates a wrong category; hard routing does not.','good')
      ]}),
      N({kick:'⌨️ the code',title:'One model, a learned per-category intercept',what:'Category as a one-hot feature inside the honest CV loop.',blocks:[
        CODE('pipeline.py','fit_eval',"# +cat: category one-hot added to the blind feature set,\n# then a single XGBoost over weather+loc+calendar+category\nohc = onehot_cat(tr); ohe = onehot_cat(ev)\nm = mk(); m.fit(pd.concat([tr,ohc],axis=1)[cols], ytr)\nreturn r2(yev, m.predict(pd.concat([ev,ohe],axis=1)[cols]))",'Held-out sites are never in train; the category is the only thing they bring.'),
        N({kick:'📄 full script',title:'The whole NOW ladder',what:'All 3 rungs × 4 routings, Tier-A (full signature) and Tier-B (60-day window) cold-start.',blocks:[
          FULLCODE('pipeline.py','categorize → route → predict, with the 3-rung honest ladder baked in.')
        ]})
      ]}),
      N({kick:'🧠 the ceiling',title:'Can’t rescue an unseen regime',what:'Leave-a-whole-category-out goes negative.',blocks:[
        P('When an entire category is held out (R² −0.22 to −0.41, worse than guessing the mean), nothing works — the model has never seen that <i>kind</i> of place. Categorization <b>interpolates among known kinds</b>; it can not <b>extrapolate</b> to a brand-new regime. You need ≥ some sites of each kind in training. Stated plainly, this bounds the claim honestly.')
      ]})
    ]
  })}
]},

{n:3,name:'Features (CP-C)',hue:'--s3',sections:[
  {label:'keep · add · kill',blurb:'re-confirmed under the ladder',node:N({
    kick:'📝 feature decisions',
    title:'What survived the honest ladder — and what didn’t',
    what:'Every feature re-graded out-of-site, not assumed. KEEP weather + location + calendar + the new <b>site_category</b>. KILL the category×month prior (helped nothing, hurt under noise), LST (inert), and the old engineered "free win" (reverses sign out-of-time — a leakage artefact).',
    blocks:[
      TBL(['feature','verdict','honest evidence'],[
        ['weather (ERA5)','✅ keep','the proven generalizable lever'],
        ['site_category (1-hot)','✅ keep','+0.16 R² new-site, significant'],
        ['cat×month PM2.5 prior','❌ kill','0.482→0.483 known; 0.433→0.363 noisy (hurts)'],
        ['{{LST}}','❌ demote','SHAP-last every protocol (inherited)'],
        ['rel_hum/wind/doy "free win"','❌ kill','reverses sign out-of-time (leak artefact)'],
        ['pm10, n_obs','⛔ banned','target-coupled — not available at a new site']],null)
    ],
    children:[
      N({kick:'🧠 the leakage traps',title:'Two traps the spec’s one-liner hides',what:'Category-relative anomalies are subtler than they look.',blocks:[
        P('<b>Trap 1:</b> "today minus this category’s norm" on PM2.5 itself is circular for NOW — it needs today’s PM2.5, the thing we predict. The leak-free cousin is a category×month <i>climatology prior</i> from <b>training</b> sites only — but even that added nothing and hurt under noise, so it was killed.'),
        P('<b>Trap 2:</b> a category derived from a site’s own PM2.5 is target info for a sensor-less site. We report two tiers — category from full history (optimistic) and from a 60-day deploy (honest) — and headline the honest one.'),
        CO('The prior failing the ladder is the system working as designed: re-admit a feature ONLY if it survives out-of-site AND out-of-time.','good')
      ]}),
      N({kick:'⌨️ leak-safe fold features',title:'Fit on train, inside the loop',what:'Leave-one-SITE-out target encoding for the prior (the CatBoost-style anti-leak).',blocks:[
        FULLCODE('features.py','Shared feature build: category join, leak-safe priors, calendar-aware FUTURE lags. Banned columns enforced here.')
      ]})
    ]
  })}
]},

{n:4,name:'NOW bake-off (CP-D)',hue:'--s4',sections:[
  {label:'4 models, one honest test',blurb:'RandomForest best · 0.529',node:N({
    kick:'⌨️ bakeoff_now.py',
    title:'XGBoost · RandomForest · LightGBM · CatBoost — on leave-sites-out',
    what:'All four learners, same +category features, same honest new-site test. They <b>cluster</b> (0.465–0.529) and all crush blind (0.316) — the <b>feature</b> moved R² far more than any model swap. {{RandomForest}} edges it (0.529); notably it has the <i>lowest</i> leaky score yet the <i>highest</i> new-site score — it overfits least and transfers best.',
    blocks:[
      bh(TGL([
        {label:'new-site R²',fig:'fig_bakeoff_now',cap:'Honest new-site R² by model; the dashed line is the blind anchor (0.316). All categorized models clear it; differences among them are within fold noise.',
         table:{head:['model (+category)','new-site R²','(leaky random)'],rows:[
           ['RandomForest','0.529','0.734'],['XGBoost','0.482','0.810'],
           ['{{LightGBM}}','0.469','0.800'],['{{CatBoost}}','0.465','0.782'],
           ['blind (no category)','0.316','—']]},
         note:'Reality check confirmed: the model is not the bottleneck — features + the categorize-then-route architecture are.'}
      ]),'the bake-off'),
      CO('{{CatBoost}} was given the same one-hot category for a fair test; with only 3 category levels its native categorical/ordered-boosting edge can not show — kept as a note, not a re-run.','good')
    ],
    children:[
      N({kick:'📝 uncertainty bands',title:'Conformal intervals — honest caveat',what:'90%-target split-conformal under-covers new sites.',blocks:[
        STAT([{v:'90%',k:'target coverage',c:''},{v:'74.8%',k:'empirical (new sites)',c:'bad'},{v:'27.3',k:'µg/m³ mean band width',c:'w'}]),
        P('Split-conformal assumes exchangeability — which <b>breaks across the site boundary</b>, so bands built on seen sites are over-confident for unseen ones. An honest caveat; the fix (group/Mondrian conformal) is logged as future work.')
      ]}),
      N({kick:'📊 every honest number',title:'The result table',what:'New-site and random R² per model, plus the conformal + paired-test rows.',blocks:[
        CSVTBL('bakeoff_now.csv','NOW model bake-off — honest new-site vs leaky random, conformal coverage, paired significance.')
      ]}),
      N({kick:'📄 full script',title:'The whole bake-off',what:'4 learners on GroupKFold + LightGBM conformal + the paired per-site bootstrap.',blocks:[
        FULLCODE('bakeoff_now.py','All models on the same honest test; conformal bands; paired blind-vs-cat significance.')
      ]})
    ]
  })}
]},

{n:5,name:'Break the ceiling (geodata)',hue:'--s5',sections:[
  {label:'free map data · zero deploy',blurb:'0.32 → 0.42 with no sensor',node:N({
    kick:'⌨️ eval_external.py',
    title:'Can free map data nowcast a place with ZERO sensors?',
    what:'The category needs observation to estimate. Free, static <b>land-use-regression</b> features — {{OSM}} road density + distance to nearest major road + SRTM elevation — need <b>none</b>. They lift honest new-site {{R²}} to <b>0.421 with zero pollution observations</b>, and to <b>0.547</b> combined with the category — the best and most stable NOW model.',
    blocks:[
      bh(TGL([
        {label:'zero-deploy lever',fig:'fig_external',cap:'+external needs no pollution observations at all; +cat+external is the best and tightest model (±0.046).',
         table:{head:['NOW variant','new-site R²','needs a sensor?'],rows:[
           ['blind','0.316','—'],['+geodata only','0.421','NO — zero obs'],
           ['+category','0.482','yes (60-day deploy)'],['+category+geodata','0.547','yes — best']]},
         note:'dist_major_road is the clearest single signal (r=−0.26: closer to a major road → higher PM2.5 — the expected traffic source).'}
      ]),'the ceiling-breaker'),
      CO('This is the bridge from "a finding" to "a tool a planner can point at any address." Sourced free via Overpass (43,870 OSM ways) + opentopodata SRTM.','good')
    ],
    children:[
      N({kick:'🧪 a complement, not a substitute',title:'Geodata can’t name the category',what:'It adds independent signal but does not recover WHICH regime a site is.',blocks:[
        STAT([{v:'0.538',k:'category-from-geodata accuracy',c:'bad'},{v:'0.615',k:'majority-class baseline',c:''}]),
        P('Classifying a site’s category from geodata alone fails (below the majority baseline). So geodata and category encode <b>different</b> things — geodata is the no-deploy <i>complement</i>, not a replacement for observing the regime. That is why combining them is best.')
      ]}),
      N({kick:'⌨️ how the features are built',title:'OSM roads + SRTM elevation per site',what:'One Overpass query for all Kampala roads, then per-site LUR metrics + batched elevation.',blocks:[
        FULLCODE('fetch_external.py','Free OSM road density / distance-to-major-road (Overpass) + SRTM elevation (opentopodata). Static, zero-observation.')
      ]}),
      N({kick:'🧠 why this is the lever',title:'Intra-urban variation weather lacks',what:'Roads/terrain vary within the city; weather does not.',blocks:[
        P('Kampala’s weather is near-uniform city-wide, so it can not explain why one site runs high and another low. Land-use features (traffic, terrain) <b>do</b> vary at the neighbourhood scale — the documented lever for new-site PM2.5 transfer in the land-use-regression literature (Wong 2021; Chen 2022). This is the homogeneity ceiling, broken.')
      ]})
    ]
  })}
]},

{n:6,name:'Forecast the future (CP-D)',hue:'--s6',sections:[
  {label:'beat persistence to +7d',blurb:'LSTM wins every horizon',node:N({
    kick:'⌨️ bakeoff_future.py',
    title:'A real forecaster holds R²≈0.43 a week out',
    what:'Chronological split (train early, forecast late), bar = {{persistence}}. With calendar-aware PM2.5 lags, every model beats persistence at every horizon — and a global {{LSTM}} with a category embedding <b>beats the GBM-on-lags everywhere</b> (+0.04…+0.12 R²), its lead <b>widening</b> with horizon. Forecasting does NOT decay to ~0 by +7d.',
    blocks:[
      bh(TGL([
        {label:'R² vs horizon',fig:'fig_bakeoff_future',cap:'LSTM (top) beats the GBMs beats persistence (bottom, decaying). All beat persistence; the LSTM earns its weight.',
         table:{head:['horizon','{{persistence}}','GBM-on-lags','{{LSTM}}'],rows:[
           ['+1 day','0.339','0.43','0.506'],['+3 days','0.109','0.37','0.477'],
           ['+7 days','0.015','0.33','0.432']]},
         note:'Split PURGED by horizon (a train row’s target must also be pre-cut) — the win survives, so it is not a boundary leak.'}
      ]),'the forecast bake-off'),
      CO('The LSTM captures longer-range temporal structure the point-lag GBMs miss — which is why its advantage grows as the horizon lengthens.','good')
    ],
    children:[
      N({kick:'⌨️ the LSTM',title:'Global net + category embedding',what:'Past-14-day sequence per site + a 3-way category embedding, masked multi-horizon head.',blocks:[
        P('One global {{LSTM}} (more data per parameter than per-site nets) over each site’s past-14-day sequence, with a learned <b>category embedding</b> concatenated before a head that predicts all 7 horizons at once (masking unobserved days).'),
        N({kick:'📄 full script',title:'The whole forecaster',what:'Sequence build (gap-filled + observed-mask channel), train with early stop, persist the model.',blocks:[
          FULLCODE('lstm_future.py','Run in its OWN process — see the pitfall note. PyTorch only, no GBM libs.')
        ]})
      ]}),
      N({kick:'🧠 the OpenMP pitfall',title:'Why the LSTM runs in its own process',what:'A web-sourced fix for a real deadlock.',blocks:[
        P('The first LSTM run <b>deadlocked</b>: PyTorch bundles its own OpenMP runtime, which collides with XGBoost/LightGBM’s when imported in the same process on macOS (pytorch/pytorch#44282). The hack <code>KMP_DUPLICATE_LIB_OK=TRUE</code> "may silently produce incorrect results" — unacceptable here. Fix = <b>process isolation</b>: the LSTM lives in <code>lstm_future.py</code>, importing only torch.'),
        CO('When results integrity is at stake, isolate the process — do not silence the warning.','good')
      ]}),
      N({kick:'📊 every horizon',title:'The result table',what:'Persistence vs XGB vs LightGBM vs LSTM, +1…+7 days.',blocks:[
        CSVTBL('bakeoff_future.csv','FUTURE bake-off — R² by horizon, all four methods, on the purged chronological split.')
      ]})
    ]
  })}
]},

{n:7,name:'The verdict (CP-F)',hue:'--s7',sections:[
  {label:'honest scorecard',blurb:'what worked · what didn’t · bounded',node:N({
    kick:'📝 findings',
    title:'The reframe works — with honest limits',
    what:'<b>NOW:</b> RandomForest+category (0.529); +category+geodata best (0.547). <b>FUTURE:</b> LSTM (+1d 0.506 → +7d 0.432). <b>Did categorization beat the blind baseline?</b> Yes — +0.16 R², significant. The 3rd-cap collapse (0.31) is recovered (0.48), and free geodata extends the win to truly sensor-less sites.',
    blocks:[
      STAT([{v:'0.547',k:'best NOW (+cat+geodata)',c:'g'},{v:'0.432',k:'LSTM forecast at +7d',c:'g'},{v:'+0.16',k:'category lift (significant)',c:'g'}]),
      bh(TBL(['top 3 needle-movers','honest gain'],[
        ['the category feature','+0.16 R² new-site (the single biggest lever)'],
        ['free urban-planning geodata','+0.11 zero-deploy / +0.23 combined'],
        ['autoregressive structure (LSTM)','"~0 by +7d" → R²≈0.43 at +7d']],null),'what moved the needle')
    ],
    children:[
      N({kick:'🧠 what didn’t work',title:'Kept, not buried',what:'Negative results are findings.',blocks:[
        P('<b>Mixture-of-experts</b> collapses under realistic cold-start (hard routing on a wrong category). <b>Category×month prior</b> adds nothing / hurts under noise. <b>Geodata can’t name the category</b> (0.54 < 0.62). <b>The ceiling:</b> leave-a-whole-category-out goes negative — categorization interpolates among known kinds, it can not extrapolate to an unseen regime.')
      ]}),
      N({kick:'🧠 two prior claims corrected',title:'Verified against scripts',what:'Honesty over headlines.',blocks:[
        P('<b>1.</b> "Forecasting decays to ~0 by +7d / persistence beats the model" — an artefact of using a nowcast model for forecasting. A purpose-built forecaster holds ~0.43 at +7d.'),
        P('<b>2.</b> "Categorization can’t rescue a homogeneous city" — too pessimistic; it lifts new-site R² by +0.16. Correct only for <i>unseen regimes</i> (leave-category-out).')
      ]}),
      N({kick:'📊 the full scorecard',title:'Every headline number, one table',what:'NOW + FUTURE, model · setup · honest test · score.',blocks:[
        CSVTBL('FINDINGS_summary.csv','One tidy table consolidating every honest number — the single source of truth.')
      ]}),
      N({kick:'🧠 future work',title:'What would sharpen it',what:'Honest next levers (✅ = done this session).',blocks:[
        DLB([['✅ group conformal','new-site coverage ≈75% → 85.8% (stage 8)'],['✅ category count','tuned k=3 → k=4, +cat 0.47 → 0.56 (stage 8)'],['✅ richer geodata','tested OSM buildings — saturated, +0.00 (stage 8)'],['more sites/categories','39 sites · k small — fold variance still high'],['push danger recall','cost curve to ~90% recall · conformal to 90%']])
      ]})
    ]
  })}
]},

{n:8,name:'Sharper model (this session)',hue:'--s6',sections:[
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

{n:9,name:'Safety tiers (the tool)',hue:'--s7',sections:[
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
  })},
  {label:'The planner map',blurb:'safety tier per area · now/+1d/+7d',node:N({
    kick:'🗺 the deployable view',
    title:'Every monitored area, coloured by its predicted safety tier',
    what:'The synthesis a planner actually uses: a Kampala map where each sensor’s <b>coverage cell</b> (Voronoi area) is coloured by its predicted EPA tier — switchable <b>now / +1 day / +7 days</b>. An interactive version plus a “predict a new location” page ship as <span style="font-family:var(--mono)">kampala_planner_prototype.html</span>.',
    blocks:[
      CHART('fig_safety_map','Predicted EPA tier per sensor coverage area (Voronoi), now / +1d / +7d. Green Elevated · amber High · red Dangerous. site_54 (circled) = the flagged local-source anomaly. © OpenStreetMap © CARTO.'),
      CO('The {{R²}} becomes a colour a planner can act on — and the never-instrumented gaps between sensors inherit the nearest area’s model. This is the bridge from “an honest result” to “a tool on a desk”.','good')
    ]
  })}
]}
];
