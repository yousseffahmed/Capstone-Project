const STAGES=[

/* ===================== THE ROAD BEHIND — solid, done & graded ===================== */

{n:0,name:'Where it started',hue:'--s0',sections:[
  {label:'The smart-city question',blurb:'cheap data → trustworthy PM2.5?',node:N({
    kick:'🧠 the mission · point A',
    title:'Can free data give Kampala planners cheap, trustworthy PM2.5?',
    what:'A smart city can’t manage what it can’t see, and Kampala can’t afford dense air monitors. Extending {{Adong 2025}} (which used satellite {{AOD}} alone, no weather), the plan was to test two cheap levers on Kampala PM2.5 — <b>add {{ERA5}} weather</b> and <b>test a satellite {{LST}} signal</b>.',
    blocks:[
      DLB([['Scope','smart-city air intelligence on a budget'],['Precedent','Adong 2025 — AOD only, no weather'],['Two cheap levers','+ weather · a satellite LST signal']]),
      CO('This is <b>point A</b> — the question the whole arc exists to answer. Everything below is the road taken to answer it.','good')
    ]
  })}
]},

{n:1,name:'Built & graded honestly',hue:'--s1',sections:[
  {label:'The honest ladder',blurb:'weather ✅ · LST ❌ · the collapse',node:N({
    kick:'🧪 the ladder',
    title:'One lever at a time, graded on the hard exams',
    what:'Built the data pipeline (39 sites · 2019–2020), then climbed a controlled ladder and re-graded every rung honestly — {{GroupKFold|leave-sites-out}} (a brand-new place) and chronological (the future), not the easy random split.',
    blocks:[
      TBL(['lever','new-site','verdict'],[
        ['+ weather (ERA5)','+0.25','✅ the generalizable win'],
        ['+ LST','+0.001','❌ adds nothing']],1),
      STAT([{v:'0.81',k:'random-split R² (leaky gap-fill)',c:'w'},{v:'0.31',k:'honest new-site — the collapse',c:'bad'}]),
      CO('The headline 0.81 was gap-filling; honestly the model <b>collapsed</b> at a place it had never seen. That collapse is exactly the problem the next iteration set out to fix.','warn')
    ]
  })}
]},

{n:2,name:'This iteration (the 4th cap)',hue:'--s3',now:true,sections:[
  {label:'Categorize-then-predict + safety tiers',blurb:'collapse recovered · a planner tool',node:N({
    kick:'🧠 where we are right now',
    title:'The 4th iteration — recover the collapse, reframe to a safety tool',
    what:'Telling the model <b>what kind of place</b> a site is recovers most of the cold-start collapse; grading by the US-EPA <b>safety band</b> turns a weak number into a deployable triage tool a planner can act on.',
    blocks:[
      STAT([{v:'0.32 → 0.56',k:'new-site R² recovered (k=4 categories)',c:'g'},{v:'68% / 98.5%',k:'exact tier / within-one-tier',c:'g'},{v:'80%',k:'dangerous days caught (tunable dial)',c:'g'}]),
      CO('◀ <b>You are here.</b> The road above is <b>solid</b> — done and graded. The road below is <b>forecast</b>: the plan to take this from a strong result to a finished, defended capstone.','good')
    ]
  })}
]},

/* ===================== THE ROAD AHEAD — forecast, hatched & fading ===================== */

{n:3,name:'Finalize the forecaster',hue:'--s4',forecast:true,fade:0.06,eta:'next',sections:[
  {label:'Close out +1…+7 days',blurb:'intervals + safety dial per horizon',node:N({
    kick:'🔮 planned · phase 1.1',
    title:'Lock the forecasting product (+1 to +7 days)',
    what:'Add per-horizon {{conformal}} prediction intervals to the {{LSTM}} forecaster, apply the safety-tier + danger-recall dial to the <i>forecast</i> outputs too, and freeze the final figures.',
    blocks:[
      DLB([['Intervals','group / blocked-time conformal, per horizon'],['Safety dial','recall-vs-false-alarm curve for +1…+7d'],['Output','final forecasting numbers, frozen']]),
      CO('Forecast, <b>firm</b>: this is next week’s work and the data already exists — mostly finalizing, not new modelling.','good')
    ]
  })}
]},

{n:4,name:'Push the open dials',hue:'--s5',forecast:true,fade:0.18,eta:'wk +1',sections:[
  {label:'Drive recall & coverage to target',blurb:'danger-recall ~90% · coverage ~90%',node:N({
    kick:'🔮 planned · phase 1.2',
    title:'Push danger-recall and conformal coverage toward target',
    what:'Move the danger-recall cost curve toward ~90% and conformal coverage toward 90% (more calibration sites · studentized or Mondrian-by-tier residuals) — and state honestly if 39 sites simply cap it.',
    blocks:[
      STAT([{v:'~90%',k:'danger-recall target',c:'w'},{v:'86% → 90%',k:'new-site coverage target',c:'w'}]),
      CO('Forecast, <b>softer</b>: the target may not be reachable with only 39 sites — an honest ceiling is an acceptable outcome here.','warn')
    ]
  })}
]},

{n:5,name:'Lock results + writeup',hue:'--s6',forecast:true,fade:0.30,eta:'wk +2',sections:[
  {label:'Freeze the science',blurb:'reproduce · scorecard · thesis report',node:N({
    kick:'🔮 planned · phase 1.3',
    title:'Lock the results, then check in',
    what:'Final pass on FINDINGS / DECISION_LOG / FINAL_REPORT, regenerate the consolidated scorecard, do one clean end-to-end reproduce run, and finalize the thesis-chapter report + all three Pyramid Views + the deck. Then stop and confirm the research is locked.',
    blocks:[
      DLB([['Reproduce','one clean end-to-end run'],['Writeup','thesis-chapter quality'],['Gate','research locked before Phase 2 starts']]),
      CO('Forecast, <b>hazier</b>: a couple of weeks out — the shape is clear, the details firm up as the earlier stages land.','warn')
    ]
  })}
]},

{n:6,name:'The planner tool · point Z',hue:'--s7',forecast:true,fade:0.42,eta:'point Z',sections:[
  {label:'The deployable tool + defense',blurb:'map · horizon slider · danger dial',node:N({
    kick:'🔮 planned · phase 2 · the finish',
    title:'The deployable planner tool — and the defense',
    what:'A web dashboard for an urban planner: a Kampala <b>map</b> coloured by predicted <b>safety tier</b> (including sensor-less areas), a <b>forecast-horizon slider</b> (+1…+7d), a live <b>danger-alert dial</b> (planner-chosen cutoff → recall / false-alarm shown live), and prediction-interval shading. Built on the persisted model artifacts — then the final submission & defense.',
    blocks:[
      DLB([['Map','safety tier per area, incl. no-sensor spots'],['Controls','horizon slider · danger dial · interval shading'],['Then','final submission + defense']]),
      CO('<b>Point Z</b> — the farthest, faintest tier. This is where the whole arc is heading; it only starts once the research above is locked.','good')
    ]
  })}
]}

,{n:7,name:'Final audit guardrail',hue:'--s5',forecast:true,fade:0.50,eta:'defense',sections:[
  {label:'What not to overclaim',blurb:'challengers only · production unchanged',node:N({
    kick:'✅ final honest audit',
    title:'The roadmap keeps the accepted model and adds challengers honestly',
    what:'The audit answers a defense question: did any later experiment justify replacing production? <b>No.</b> k=6 is meaningful but fragile; k=6 full-history is a <b>non-deployable upper bound</b>; deployable k=6 improves with <b>30-45 days</b> but still does <b>not</b> beat accepted k=4. For FUTURE, RF and rolling-7 are real challengers, but the <b>LSTM remains the headline</b>.',
    blocks:[
      DLB([['NOW/safety','accepted production remains k=4'],['FUTURE','LSTM remains headline'],['Challengers','RF and rolling-7 persistence enter the bakeoff only'],['Do not claim','k=6 production · RF beats LSTM overall · random split as real-world · full-history category deployable']]),
      CO('This is a stronger final capstone: the audit proves restraint, not just score-chasing.','good')
    ]
  })}
]}

];
