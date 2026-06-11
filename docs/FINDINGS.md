# 4th Cap — FINDINGS

*The honest results of the categorize-then-predict reframe. Every number here is reproducible
from `analysis/` (scripts + `results/` CSVs) and traceable in `DECISION_LOG.md`. Honest
(out-of-sample / out-of-time) numbers are the headline; leaky numbers are labelled as such.*

---

## ✅ FINAL HONEST IMPROVEMENT AUDIT (2026-06-10) — no production replacement

After the main capstone was finalized, we ran a deliberately conservative improvement audit. The goal was
not to chase a higher score, but to ask whether any stronger-looking result was **honest, deployable, and
worth replacing the accepted pipeline**.

**Bottom line:** no production replacement is justified. The accepted **k=4 categorize-then-predict NOW
pipeline** and the **LSTM FUTURE forecaster** remain the defensible headline models.

| task | candidate | honest result | deployable? | decision |
|---|---:|---:|---|---|
| NOW | accepted k=4 baseline | R² ≈ **0.56** | yes | **keep** |
| NOW | k=6 full-history | R² ≈ **0.56–0.58** | **no — oracle upper bound** | reject as production |
| NOW | k=6 best deployable window | R² **0.506** at 45d | short-deploy | challenger only |
| FUTURE | LSTM | best/tied across most same-row horizons | yes | **keep headline** |
| FUTURE | RandomForest / rolling-7 | strong at +3/+7 | yes | challenger baselines |

**What k=6 taught us.** k=6 is **meaningful but fragile**. It splits real pollution regimes by PM2.5
level, volatility, ventilation, and humidity. But with only 39 sites it creates tiny groups, including a
singleton extreme cluster and a 3-site stagnant/humid cluster. That makes the full-history k=6 category a
useful scientific upper bound, not a production setting.

**Why the full-history score is not deployable.** k=6 full-history assigns the held-out site using its
complete PM2.5 behavior. A real new site does not have that history. Once restricted to deployable
information, k=6 improves with a **30–45 day** early deploy window, but still does **not** beat accepted k=4.
Soft category probabilities, centroid-distance features, and an early-window+geodata classifier did not
close the gap.

**Future forecast audit.** On identical rows, RandomForest and rolling-7 persistence are valid challengers:
RF ties/slightly beats LSTM at some middle/long horizons, and rolling-7 is strong at +7. But RF does **not**
beat LSTM overall; LSTM remains strongest at +1 and +5 and remains the headline forecaster. RF/rolling-7
should be added as formal challenger baselines, not claimed as replacements.

**What not to claim:** do **not** claim k=6 is the new production model; do **not** claim RF beats LSTM
overall; do **not** claim random-split performance is real-world performance; and do **not** claim
full-history category assignment is deployable at a new site.

Artifacts: `analysis/results/model_improvement_report.md` · `final_model_decision_table.csv` ·
`professor_summary.md` · `presentation_talking_points.md`.

---

## ⭐ ROUND 3 (2026-06-07) — SAFETY-TIER FRAMING (the current capstone scope)

**Scope sharpened:** the deliverable is a tool that tells an urban planner an area's **safety tier**
(Elevated / High / Dangerous), not the exact µg/m³. So we grade the *same honest predictions* by the
**EPA safety band** they land in. Bands = US EPA 2024 PM2.5 24-hr AQI breakpoints: **Elevated ≤ 35.4 ·
High 35.5–55.4 · Dangerous > 55.4**. Same honest splits, standard breakpoints, imbalance-aware metrics.

| metric (honest test) | exact-band | within-one-band | baseline | key per-tier |
|---|---|---|---|---|
| **NOW new-site** (+cat+ext, k=4) | **0.680** | **0.985** | 0.523 majority | Dangerous recall 0.51 |
| FUTURE +1 day | 0.702 | 0.983 | 0.681 persistence | Dangerous recall 0.54 |
| FUTURE +7 days | 0.677 | 0.983 | 0.635 persistence | Dangerous recall 0.52 |

- **The bottleneck, reframed and largely resolved for the use case.** Regression R² (≈0.57 new-site)
  punished a 47-vs-52 miss; in *safety-tier* terms those misses are inside the same band, so the
  deployable accuracy is **68% exact / 98.5% within one tier** at a never-instrumented site — beating
  majority-class by +16 pp. A catastrophic 2-tier error (Dangerous called "safe") hits only **3.6%** of
  dangerous days.
- **Dangerous-day recall is tunable for safety.** Strict EPA recall is 0.51; lowering the Dangerous
  *alert cutoff* on the regression output (an operating-point choice) gives, on the honest new-site
  test: cutoff 50 → recall 0.67 (8% false alarms) · **45 → 0.80 (17%)** · 40 → 0.91 (30%). A planner
  picks the point. A dedicated class-weighted classifier did NOT beat this (honest negative).
- **What marks a dangerous day:** humidity + dewpoint (largest separation), then wind/month — a
  **humid, stagnant weather regime** that traps particulates. Physically sensible, and it's what the
  model keys on to flag danger. Scripts: `band_now.py`, `band_future.py`, `band_now_recall.py`.

---

## 🎯 THE NEW-SITE PREDICTOR — the deployable tool (2026-06-07, finalized)

The findings above are packaged into one runnable artifact — **`analysis/new_site_predict.py`** — point it at
any Kampala location and it answers, end to end, what a planner gets.

**Input contract (all free, available at a never-visited address):** lat/lon · date (→ month, day-of-week) ·
that day's ERA5 weather (temp, dewpoint, wind u/v, pressure, precip) · geodata auto-fetched from the coordinates
(OSM road density + distance-to-major-road + SRTM elevation). *Optional* short-deploy: ≈14–60 days of a temporary
low-cost sensor → unlocks the real forecaster and a sharper category.

**Outputs** — zero-deploy nowcast (PM2.5 today → EPA tier → ≈86% conformal band → planner-tunable danger dial)
and, with a short deploy, the +1…+7-day forecast (tiers + bands) — all graded against the site's true values.

**Validated honestly** by leave-one-site-out (hold a whole site out, train on the other 38):

| held-out demo | nowcast | tier-exact | within-1 | forecast |
|---|---|---|---|---|
| **leave-sites-out MEAN (all 39 sites)** | **R² 0.547** | **0.68** | **0.985** | LSTM +1d 0.51 → +7d 0.43 |
| site_135 (a clean low-pollution site) | R² 0.25¹ | 0.77 | 1.00 | +1d 39 vs 41 µg/m³ ✓ |
| site_54 (the highest-pollution site) | R² −1.69¹·² | — | — | +1…+7d **all Dangerous days flagged** ✓ |

¹ Single-site R² is noisy (per-site folds range 0.03–0.71); the validation number is the **mean**, never one site.
² site_54 is the honest hard case: its regime can't be read from the map alone, so the pure zero-deploy nowcast
under-predicts it (the documented "geodata can't always name the kind" limit, eval_external acc 0.54 < 0.62) — but
a short deploy lets the forecaster flag its whole dangerous week. Strength and limit, both stated.

Artifacts: `results/fig_newsite_demo.png` + `newsite_demo.csv` (site_135) · `…_hi.*` (site_54). Surfaced as the
4th pyramid view (`index_predictor.html` — the 🎯 Predictor lens in `capstone_pyramid.html`).

> **Scope note (2026-06-07):** AOD is **not a lever in our pipeline** (it was never implemented — our data
> only ever carried LST, found inert) and is not on the roadmap. It appears only where it is factually used:
> describing the **Adong 2025 precedent** (which used satellite AOD alone).

---

## 🔬 BLIND CATEGORIZATION — what misled site_54, and the planner map (2026-06-07)

Investigating Crimson's question — *why does the sensor-less prediction lean on map data, and can we
categorize a new site better?* Scripts: `investigate_categorization.py`, `improve_blind_cat.py`.

**The exact inputs to categorize a site** = an 8-feature behavioural *signature*: 4 from its PM2.5
(`pm25_mean/std/p90/season_amp` — needs observations) + 4 from ERA5 climate (`temp/humidity/windspeed/
precip` means — zero-deploy). The *blind* guess for a sensor-less site uses only the 5 geodata features.

**Findings (all honest):**
1. **A simpler model guesses the area-type better.** The 4th-cap blind classifier was a RandomForest
   (overfits 39 sites / 5 features → leave-one-site-out **0.538**, below the 0.615 majority). A **kNN
   lifts it to 0.641** — now beating majority. Adopted for the area-type label.
2. **But a guessed category does NOT help the µg/m³ nowcast — it slightly hurts.** On the honest
   new-site test (GroupKFold-5, tier-exact): no-category **0.612** ≈ blind-geo→RF 0.605 ≈ blind-geo→kNN
   0.593; an **observed** category is the only one that helps (**0.671**, R² +0.41). A *wrong* guessed
   category misleads the model, so for a truly sensor-less place the tool leans on weather + map features
   **directly**, and the category lever pays off only with a short (~2-month) deploy.
3. **site_54 is a genuine local-source anomaly.** It is the highest-pollution site (62.9 µg/m³) yet its 6
   nearest map-feature neighbours are all low-pollution; the only zero-deploy level signal is
   distance-to-major-road (r=−0.35 — weak). No free feature explains its pollution — the map under-reads
   it; only a confirming sensor catches it. (On its actual *dangerous day* the weather signal still drives
   the zero-deploy nowcast to Dangerous — 83.8 vs 129.7 µg/m³ — so episodic danger is flagged even where
   the baseline is mis-read.) Figure: `fig_blindcat_investigation.png`.

**External validation of the site_54 anomaly (web investigation, outside our data).** Reverse-geocoding
site_54's coordinates (0.3519, 32.5726) places it within ~50–80 m of the **Kalerwe Market & abattoir on
Gayaza Road at the Northern-Bypass junction** (Nsooba / Kyebando, Kawempe) — confirmed by OpenStreetMap +
Wikipedia. That one spot co-locates four PM2.5 sources its residential neighbours lack: a giant open-air
market (~1,548 t of waste/week, much of it openly burned), an abattoir draining the Nsooba channel, a
congested diesel matatu/boda interchange (the "60 m from a major road" clue), and a flood-prone wetland
bottom that traps the plume. **This vindicates the model's honest conclusion:** the real source is *land use*
(a market), invisible to road-geometry features — exactly why the map can't read it and a confirming sensor
is needed (a future lever: OSM land-use/amenity tags, not just roads). The Jan-2020 ≈130 µg/m³ spike adds
dry-season regional biomass-burning smoke on northerly winds. Sources: OpenStreetMap · Kalerwe Market
(Wikipedia) · The Observer "Why Kawempe is the most polluted division" · RSC *Environ. Sci.: Atmospheres*
D4EA00081A (2025).

**The planner map (the deployable view).** `predict_map.py` → `fig_safety_map.png` (static, embedded in the
pyramid views) and an interactive **`kampala_planner_prototype.html`**: a Kampala basemap with each sensor's
Voronoi **coverage cell** coloured by predicted EPA tier (now / +1d / +7d filters), hover tooltips, and a
**predict-a-location** page (kNN category + nowcast tier + band + danger dial; 3 real test cases). The 39
instrumented areas use their observed category (the realistic deployed model); never-instrumented gaps
inherit the nearest area. Self-contained, offline, honest throughout. © OpenStreetMap © CARTO.

---

## LAYER 1 — SCOPE (the one line)

> **Can a categorize-then-predict pipeline give a Kampala planner trustworthy PM2.5 where there
> is no sensor, and a few days ahead, without collapsing?** — **Yes, with honest limits.**
> Telling the model *what kind of place* a site is recovers most of the cold-start collapse
> (new-site R² 0.32 → 0.48), and free map data pushes it further with **zero** sensors on the
> ground (→ 0.55). For the future, a purpose-built forecaster beats "same as yesterday" out to a
> full week — overturning the prior "forecasting is hopeless past a day" read.

---

## LAYER 2 — THE HONEST NUMBERS (both metrics, side by side)

### NOW — nowcast a sensor-less site (honest test = leave-sites-out, GroupKFold5)

| model / feature set | new-site R² | needs a sensor deploy? |
|---|---|---|
| blind pooled (weather+loc+calendar) — *the 3rd-cap collapse* | **0.316** ± 0.224 | — |
| + free geodata only (OSM roads + elevation) | 0.421 ± 0.145 | **no — zero observations** |
| + site category, k=3 (the reframe) | 0.482 ± 0.079 | yes (≈60-day deploy) |
| **+ site category, k=4 (Round 2 — finer tiers)** | **0.558** ± 0.050 | yes (≈60-day deploy) |
| + category k=4, fold-safe (centroids on train sites only) | 0.563 ± 0.053 | yes |
| + category k=3 + geodata (4th-cap best) | 0.547 ± 0.046 | yes |
| **+ category k=4 + geodata (Round-2 best)** | **0.564** ± 0.062 | yes |
| best learner at fixed features = **RandomForest** (+cat k=3) | 0.529 ± 0.082 | yes |
| *random 80/20 (LEAKY, for reference only)* | *0.73–0.81* | — |

> **Round 2 (2026-06-07) NOW win — finer categories.** The category count was only ever chosen by
> silhouette (k=3). Re-tuned by the metric that matters (honest new-site R²), **k=4** lifts the
> deploy-only nowcast — *category, no geodata* — from **0.470 → 0.558**, holds fold-safe (0.563, so
> not a categorizer leak), and is **significant** (paired per-site bootstrap k3-vs-k4 on +cat:
> +1.07 µg/m³ RMSE, 95% CI [+0.33, +1.90], 23/39 sites). On the *combined* +cat+geodata model k
> barely matters (0.541→0.555, not significant) — geodata already supplies the spatial signal finer
> tiers would add (the two levers are partly redundant). So the k=4 win is the bridge for a planner
> who can do a short deploy but has no geodata. **k=6 hits 0.585 but spawns a one-site cluster →
> fragile with 39 sites, not recommended.** Stacking RF+XGB+LGBM adds +0.003 (within noise) — the
> model still isn't the bottleneck. *More* free geodata (OSM building density) integrates stably
> across all 39 sites but adds only +0.001–0.007 (saturated) — kept as an honest negative, not adopted.

**Is the category lift real?** Paired per-site bootstrap (blind vs +cat, n=39 sites):
**−1.60 µg/m³ RMSE, 95% CI [+0.40, +2.92], 26/39 sites improved → significant.** Not fold noise.

**Uncertainty:** LightGBM split-conformal 90% bands → empirical coverage **74.8%**, width 27.3
µg/m³. They *under-cover* new sites (honest caveat: exchangeability breaks across the site boundary).

> **Round 2 (2026-06-07) UNCERTAINTY fix — group conformal.** Naive split-conformal under-covers
> because it calibrates on held-out *rows* (same sites) but is tested on held-out *sites*. Calibrating
> the residual quantile on whole **held-out sites** (group / leave-sites-out conformal) raises
> empirical coverage to **85.8%** (from the 74.8% naive baseline), closing most of the gap to the 90%
> target. Bands widen (≈28 → 43 µg/m³) because new-site error genuinely is larger — correct, honest
> behaviour. Per-category (Mondrian) conformal helps little (80.8%). Remaining shortfall to 90% is the
> small-sample quantile (only ~6–7 calibration sites per fold); more sites would sharpen it.
> Script: `improve_conformal.py` → `improve_conformal.csv`.

### FUTURE — forecast +1…+7 days at a known site (honest test = purged chronological split)

| horizon | persistence (the bar) | GBM-on-lags | **LSTM (global + category embedding)** |
|---|---|---|---|
| +1 day | 0.339 | 0.43 | **0.506** |
| +3 days | 0.109 | 0.37 | **0.477** |
| +7 days | 0.015 | 0.33 | **0.432** |

Every model beats persistence at every horizon; the **LSTM beats the GBMs at every horizon**
(+0.04…+0.12 R²), and its lead **widens** with horizon.

> **Round 2 (2026-06-07) FUTURE — the LSTM is already at the ceiling (honest negative).** Two attempts
> to push it failed: (1) a *bigger* LSTM (2-layer, hidden 64, dropout) is **worse** at every horizon
> (+1d 0.465 vs 0.506) — 39 sites favour the simpler net; (2) an **LSTM+GBM ensemble** (aligned on
> site/target-day/horizon) adds **+0.001** mean R² (a best-fixed-blend ceiling of +0.005 is test-fit,
> not a claim). The GBM is uniformly weaker, so blending can't help. The 4th-cap LSTM (0.51→0.43) is
> the right model and the practical ceiling for this dataset. Scripts: `improve_future_*.py`.

---

## LAYER 3 — WHAT WORKED, WHAT DIDN'T, WHAT'S BOUNDED

### ✅ Worked
1. **Categorization rescues cold-start (NOW).** Knowing a new site's pollution *kind* lifts honest
   new-site R² from 0.32 to 0.48. Kampala's weather is near-uniform, so the blind model can't tell
   a new site's baseline level and predicts the city mean; the category hands it a learned per-tier
   intercept. Mechanism is simple and defensible.
2. **Free geodata is a zero-deploy lever (NOW).** OSM road density + distance-to-major-road + SRTM
   elevation lift new-site R² to 0.42 **with no pollution observations at all**, and to **0.55**
   combined with the category — the most stable model (±0.046). This is the bridge from "a finding"
   to "a tool a planner can point at any address." `dist_major_road` carries the clearest single
   signal (closer to a major road → higher PM2.5).
3. **A real forecaster beats persistence out to a week (FUTURE).** Autoregressive lags (1/2/3/7 +
   rolling means) + an LSTM hold R²≈0.43 at +7 days while persistence decays to ~0. The LSTM earns
   its weight: it beats the cheap GBM baselines at every horizon.
4. **Soft routing > hard routing.** Category-as-a-feature degrades gracefully when the category is
   estimated wrong (it is, 41% of the time, from a cheap 60-day window); mixture-of-experts
   *collapses* (0.50 → 0.30, below blind) because hard routing sends a mis-labelled site to the
   wrong specialist. **Decision: category-as-feature, not experts.**

### ❌ Didn't work (kept, not buried)
1. **Mixture-of-experts** under realistic cold-start — collapses below the blind baseline. Killed.
2. **Category × month PM2.5 prior + weather anomalies** — adds nothing when the category is known,
   *hurts* when it's noisy (amplifies the wrong category). Killed. (Confirms the strategy's own
   rule: re-admit a feature only if it survives the ladder. It didn't.)
3. **Geodata → category classification** — can't recover *which* category a site is (leave-one-out
   accuracy 0.54 < 0.62 majority baseline). Geodata adds independent regression signal but is not a
   substitute for observing the regime.
4. **LST stays inert / engineered "free win" stays a leak** — re-confirmed demoted (inherited).

### ⛔ Bounded (the honest ceiling)
- **Leave-a-whole-category-out goes negative** (R² −0.22 to −0.41). Categorization interpolates
  *among kinds of place the model has seen*; it cannot extrapolate to a regime with **zero**
  training sites. You need ≥some sites of each kind in the training set. State this plainly.
- **39 sites is small.** Fold variance is high; `+external`-alone is noisy (±0.145). The robust
  claims are `+cat+external` (±0.046) and the FUTURE results (large test sets, 2300–2573 rows).

---

## LAYER 4 — DETAIL

### Top 3 things that moved the needle
1. **The category feature** — +0.16 R² on the honest NOW test (the single biggest lever; significant).
2. **Free urban-planning geodata** — +0.11 alone (zero-deploy) / +0.23 combined; breaks the
   homogeneity ceiling for a sensor-less site.
3. **Proper autoregressive structure for forecasting** — turns "decays to ~0 by +7d" into
   "R²≈0.43 at +7d"; the LSTM with a category embedding is the best forecaster.

### Per-metric verdict
- **NOW best model:** RandomForest on `weather + location + calendar + site_category` (new-site
  **0.529**); add free geodata for **0.547** and tighter variance. *The model barely matters
  (all learners cluster 0.47–0.53); the **features + the categorize-then-route architecture** are
  what moved R².* (Matches the literature: Adjei 2026; Wong 2021 LUR transferability.)
- **FUTURE best model:** global **LSTM + category embedding**, masked multi-horizon (+7d **0.432**);
  GBM-on-lags is the strong cheap fallback (+7d ~0.33).

### Did categorization beat the blind baseline? — **Yes.**
On the honest leave-sites-out test, +0.165 R² (full-signature) / +0.124 (realistic 60-day deploy),
significant by paired per-site bootstrap. The 3rd-cap collapse (0.31) is largely recovered (0.48),
and free geodata extends the win to truly sensor-less sites (0.42 with zero observations).

### Two corrections of prior findings (verified against scripts)
1. **"Persistence beats the model / forecasting decays to ~0 by +7d"** was an artifact of using a
   nowcast model for forecasting. A purpose-built forecaster beats persistence at every horizon and
   holds R²≈0.43 at +7d. (The two metrics genuinely needed separating — this round did that.)
2. **"Categorization can't rescue a homogeneous city"** (the hedge) is too pessimistic *within* the
   set of known kinds — it lifts new-site R² by +0.16. It is correct only for *unseen* regimes
   (leave-category-out), which is a different, narrower claim.

### Reproducibility
```
cd analysis  (venv: ../../working/.venv)
python site_categorize.py     # CP-A  39 sites -> 3 categories (+ portable categorizer)
python pipeline.py            # CP-B  NOW honest ladder (blind vs +cat vs +prior vs MoE)
python bakeoff_now.py         # CP-D  NOW models + conformal + paired significance
python fetch_external.py      # pull free OSM roads + SRTM elevation (network)
python eval_external.py       # ceiling-breaker: geodata as a zero-deploy feature
python bakeoff_future.py      # CP-D  FUTURE persistence + GBM-on-lags
python lstm_future.py         # CP-D  FUTURE LSTM (SEPARATE process — OpenMP isolation)
```
Fixed seeds (42). Outputs → `results/` (CSVs + figures). Banned predictors: `pm10`, `n_obs`
(target-coupled). Decisions + sources → `DECISION_LOG.md`.
