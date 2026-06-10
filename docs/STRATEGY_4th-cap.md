# 4th Cap — Strategy & Reframe
*Built on 3rd-cap-handover. Session: 2026-06-06. Flowline-shaped: scope → checkpoints → mechanics → technical steps.*

---

## LAYER 1 — SCOPE (the one idea)

**Old framing (3rd cap):** *"Which cheap data lever helps estimate Kampala PM2.5?"* → answer found: weather helps, LST is inert. Good science, but it ends at a finding, not a usable tool. And the honest tests showed the tool **collapses** the moment we point it at a place it has never seen (new-site R² ≈ 0.31, one fold near 0) or at the future (chronological R² ≈ 0.11 — a "same as yesterday" guess beats it).

**New framing (4th cap):** *"Can a **categorize-then-predict** pipeline give an urban planner trustworthy PM2.5 where there is **no sensor** — and a few days **ahead** — without the model collapsing?"*

Think of it like a doctor. The old model was one doctor who treats every patient identically and falls apart on an unfamiliar case. The new model is a clinic: first a **triage nurse** sorts each location into a *kind of place* (its category), then the **specialist** for that kind makes the call. A stranger is no longer a stranger — they're "a patient of type B," and we have a type-B specialist ready.

**Two metrics, kept separate from here on** (they are different problems, different honest tests, different best models):

| | **Metric 1 — NOW (nowcast / estimation)** | **Metric 2 — FUTURE (forecast)** |
|---|---|---|
| Question | PM2.5 *today* at a place with no sensor | PM2.5 *+1…+7 days* ahead at a known place |
| Planner use | fill the map between sensors | early-warning / advisory |
| Inputs | weather + time + place + **category** | history (PM2.5 lags) + weather + **category** |
| Honest test | **leave-sites-out** (a new place) | **chronological** (the real future) |
| Bar to beat | the blind pooled model (collapsed) | persistence ("same as yesterday") |

---

## LAYER 2 — CHECKPOINTS (the milestones, in order)

1. **CP-A · Categorize sites** — turn 39 sites into a small set of *kinds of place* from the data itself. ✅ **proven this session** (see Layer 4 result).
2. **CP-B · Design the data flow before retraining** — lock the categorize → route → predict → honest-test pipeline on paper so we never again "test new sites blindly and watch it collapse."
3. **CP-C · Feature engineering pass** — decide what to keep / add / drop, including the new category feature and category-relative anomalies.
4. **CP-D · Model bake-off, per metric** — XGBoost · RandomForest · LightGBM(+conformal) · CatBoost for NOW; LSTM (+GBM baselines) for FUTURE.
5. **CP-E · Staged validation** — prove the architecture in *forgiving* mode first (random/leaky); only if it lifts do we escalate to the strict new-site + future tests. Don't harden what doesn't work in easy mode.
6. **CP-F · Package** — fold results into the Pyramid View + decks; refresh the scope view.

---

## LAYER 3 — MECHANICS (how the pieces work, and why)

### 3.1 The categorize-then-predict data flow (the anti-collapse architecture)

```
                OLD (collapses)                         NEW (4th cap)
   all 39 sites ─► one model ─► new site?         site ─► [1 CATEGORIZE] ─► [2 ROUTE] ─► [3 PREDICT + band]
                  model never saw its                     signature →             to the model              metric 1 or 2
                  kind → R² ≈ 0                            nearest category        for that category         + uncertainty
                                                                │
                                                    only LIVE step for a NEW site
```

- **[1] Categorize.** Every site gets a category from its **behavioural signature** (pollution regime + local climate — *not* coordinates; routing should follow how a place behaves, not where it sits). For an existing site we use full history; for a **brand-new site** we compute the signature from whatever short window of observed/"leaked" dynamic data we have, then snap it to the nearest category centroid. **This is the one and only thing computed live for an unseen site** — exactly the controlled, single-leak design you described.
- **[2] Route.** Two implementations to A/B: (a) **mixture-of-experts** — one model per category, send the site to its expert; (b) **single model + category as a feature** + category-stratified CV. Start with (b) (simpler, more data per model), graduate to (a) if a category is distinct enough to deserve its own model.
- **[3] Predict + band.** Output the metric *and* an uncertainty interval (planners need "how sure are we," not just a number).

### 3.2 The honest-test ladder (the order that stops blind collapse)

We test in escalating strictness, and **only climb if the rung below holds** (your "if it performs even while leaking, go on" rule):

1. **Random split** (leaky, forgiving) — does the architecture even show signal? Cheap go/no-go.
2. **Leave-sites-out *within* category** — does routing help a new site that resembles its category?
3. **Leave-sites-out *across* category** (true cold-start) + **chronological** (true future) — the real bars.

The bet: a new site **routed to its category** beats the blind pooled model that scored ~0. If it doesn't, the honest finding becomes *"Kampala PM2.5 is too homogeneous for categorization to rescue cold-start"* — which the proof experiment already hints at and is itself a publishable result.

### 3.3 Feature engineering plan (keep / add / drop)

- **KEEP** — weather (ERA5: temp, dewpoint, wind, pressure, precip), location, calendar. Weather is the *proven generalizable* lever from 3rd cap.
- **ADD — `site_category`** (static per site): the routing key. New this round.
- **ADD — category-relative anomalies**: today's value *minus this category's seasonal norm* → tells the model "how unusual is today **for this kind of place**." Likely the highest-leverage new feature.
- **ADD — for the FUTURE metric only**: PM2.5 lags + rolling means (already in `forecast.py`) — the "sticky" clues that make near-term forecasting work.
- **ADD (data-sourcing, flagged) — urban-planning enrichers** we don't have yet: land-use class, road proximity, population density, NDVI/greenness, elevation. These would sharpen *both* the categories and the nowcast — the bridge to a true urban-planning application.
- **DROP / demote** — **LST** (proven inert, SHAP-last under every protocol) and the old "engineered free win" (rel_humidity / wind_speed / doy) that **reverses sign out-of-time** (a leakage artefact). Re-admit a feature only if it survives the honest ladder.

### 3.4 Model lineup, matched to each metric (your point 6)

> Reality check up front: per 3rd cap **and** the literature (Adjei 2026: African spatial-CV ~0.13 vs random >0.90), **the model is rarely the bottleneck — features and the categorize-then-route architecture are.** Expect the big wins from CP-A/B/C, modest ones from model swaps.

**NOW metric (tabular / cross-sectional):**
- **XGBoost** — the current baseline (note: you've been using XGBoost, *not* random forest). Keep as benchmark, retrained per category.
- **Random Forest** — classic, cheap, interpretable baseline you asked about.
- **LightGBM + conformal intervals** — faster boosting + the uncertainty bands planners need.
- **CatBoost (the 5th — recommended)** — *built for categorical features*, and its **ordered boosting reduces exactly the target-leakage that bit us before.** Since this whole round introduces a categorical `site_category` column, CatBoost is the most natural fit, not a random add-on.

**FUTURE metric (sequential):**
- **LSTM** — learns the temporal sticky pattern directly; the headline candidate for forecasting.
- **GBMs on lag features** (XGB/LGBM) — strong, cheap baselines the LSTM must beat to justify its weight.
- *Stretch goal:* **Temporal Fusion Transformer** — multi-horizon + static covariates (the category!) fits the multi-site framing, but heavy; only if LSTM proves the sequence approach earns its keep.

---

## LAYER 4 — TECHNICAL STEPS

### ✅ Done this session — CP-A proof experiment
`analysis/site_categorize.py` → `analysis/results/`. The 39 sites resolve into **3 behavioural kinds of place** (k-means, k chosen by silhouette among k≥3; Ward sanity-check; portable categorizer saved):

| category | n sites | PM2.5 mean | PM2.5 p90 | wind | signature |
|---|---|---|---|---|---|
| low-pollution / well-ventilated | 24 | 31.7 | 48.7 | 1.62 | the city baseline |
| high-pollution / well-ventilated | 12 | 47.5 | 73.4 | 1.58 | hotter spots, still windy |
| moderate-pollution / **stagnant** | 3 | 46.5 | 73.5 | **1.15** | low wind + high humidity — a **robust** micro-regime (same 3 sites at every k, k-means==Ward) |

**Honest reading:** k=2 has the best silhouette (0.57) but it's just an *outlier peel* (36 vs 3) — too coarse to route on. k=3 (silhouette 0.39, split 24/12/3) is the usable planning categorization. **Finding:** Kampala PM2.5 is fairly homogeneous in *level*; the real structure is **pollution-level (low vs high) plus 3 stagnant outlier sites.** Categories are spatially **intermixed** on the map → they capture *behaviour*, not geography. Reproducible for a new site via `categorizer.json` + `categorize_new_site()`.

### ▶ Next session — execution order
1. **CP-B** — write `pipeline.py`: categorize → route(b: category-as-feature) → predict, with the 3-rung honest ladder baked in.
2. **CP-C** — add `site_category` + category-relative anomalies to the feature build; re-confirm LST/eng-feature demotion under the ladder.
3. **CP-D** — `bakeoff_now.py` (XGB/RF/LGBM+conformal/CatBoost) and `bakeoff_future.py` (LSTM vs GBM-on-lags), each reported on its own honest test.
4. **CP-E** — escalate strictness only on lift; record the decision trail.
5. **Open data question (flag for Crimson):** do we invest in sourcing land-use / road / population enrichers? That's the lever that turns this from "homogeneous city, categorization marginal" into a real urban-planning tool — but it's a data-acquisition task.

### Open decisions parked for Crimson
- Routing impl to start with: **(b) category-as-feature** (recommended) vs (a) one-model-per-category.
- Whether to source external urban-planning features now or defer.
- LSTM scope: single-site sequences vs a global LSTM with category embedding.
