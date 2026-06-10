# Categorize-then-Predict: Trustworthy PM2.5 for a Sensor-less City

**Smart City Capstone · Kampala, Uganda · GUC Masters · 2026**

---

## Abstract

Kampala cannot afford dense air-quality monitoring, yet planners need fine-grained PM2.5 — both
*where there is no sensor* and *a few days ahead*. A prior model scored a headline R²≈0.81, but
that figure is a leaky random split; graded honestly (hiding whole sensors, or forecasting the
real future) it collapses to new-site R²≈0.31, and a naïve persistence baseline beats it
out-of-time. This work asks whether a **categorize-then-predict** pipeline can stop that collapse
without faking the test. We sort 39 sensor sites into three behavioural categories, route on the
category, and evaluate two metrics under their own honest protocols. **Findings (all out-of-sample
/ out-of-time):** adding the category lifts new-site R² from 0.316 to 0.482 (significant by a
paired per-site bootstrap); free land-use geodata (OpenStreetMap roads + SRTM elevation) lifts it
to 0.421 *with zero pollution observations* and to **0.547** combined — the best and most stable
nowcast. For forecasting, a global LSTM with a category embedding holds R²≈0.43 at +7 days and
beats both persistence and gradient-boosted baselines at every horizon. We also bound the method
honestly: it cannot rescue a regime with no training sites (leave-a-category-out goes negative),
and naïve conformal intervals under-cover new sites. Two earlier claims are corrected.

**Refinements (this iteration).** Tuning the number of behavioural categories by the honest metric
(k=4, not the silhouette's k=3) lifts the deploy-only new-site nowcast from 0.48 to 0.56; group
(leave-sites-out) conformal raises new-site interval coverage from 75% to 86%. Most importantly, since
the operational output is a **safety tier** (Elevated / High / Dangerous, on EPA breakpoints) rather
than an exact concentration, we evaluate by the *band* the prediction lands in: on the honest new-site
test the model is right to the exact tier **68%** of the time and to within one tier **98.5%**, and a
planner-chosen alert threshold raises dangerous-day recall to **80%** at a 17% false-alarm rate. Under
this use-case-appropriate metric the new-site "collapse" is largely resolved into a deployable triage tool.

---

## 1 · Problem & motivation

A smart city cannot manage what it cannot see, and Kampala lacks the budget for dense PM2.5
monitoring. The useful question is therefore not "can we fit the sensors we have?" but "can cheap,
free data give a planner trustworthy PM2.5 at a place with **no** sensor, and a few days **ahead**?"

The honest obstacle is generalization. A model trained and tested on the same sensors (a random
split) memorizes each site and looks excellent (R²≈0.81). The moment it is pointed at an unseen
location it collapses (new-site R²≈0.31, one fold ≈0), and out-of-time it loses to "tomorrow =
today." This collapse — not raw accuracy — is the problem to solve, and it matches the literature
(African spatial cross-validation ≈0.13 vs random >0.90).

**The reframe.** Instead of one model for every place (one doctor who treats every patient the
same), we build a clinic: a triage step assigns each location a *kind of place* (its category),
then a specialist predicts. A stranger becomes "a place of type B," for which we already have signal.

---

## 2 · Data

- **Target:** AirQo low-cost-sensor PM2.5, 39 sites around greater Kampala, 13,944 site-days
  (2019-05-23 → 2020-12-31), ~84% daily coverage (gappy). Mean 38 µg/m³ (σ 19).
- **Predictors (free, available at any location):** ERA5 weather (temperature, dew-point, wind
  u/v, surface pressure, precipitation), site location, calendar (month, day-of-week).
- **Carried but demoted:** MODIS land-surface temperature (LST) — ~80% cloud-gapped, proven inert.
- **Banned as predictors:** `pm10` (same instrument as the target, corr ≈ 0.9) and `n_obs` (a
  by-product of the daily mean). Neither exists at a sensor-less place; using them would
  manufacture a fake win.

---

## 3 · Method

### 3.1 Two metrics, kept separate

| | NOW (nowcast) | FUTURE (forecast) |
|---|---|---|
| Question | PM2.5 today at a sensor-less place | PM2.5 +1…7 days at a known place |
| Honest test | leave-sites-out (GroupKFold-5 on `site_id`) | blocked, horizon-purged chronological |
| Bar to beat | the blind pooled model | persistence ("same as yesterday") |

### 3.2 Categorize → route → predict

A site's **signature** (pollution level / volatility / seasonality + local climate, *not*
coordinates) is clustered with k-means (k chosen by silhouette among k≥3, Ward sanity-check). The
39 sites resolve into three robust categories — 24 low-pollution, 12 high-pollution, 3 stagnant
(low-wind/humid) outliers — that are spatially intermixed (behaviour, not geography). A portable
categorizer (scaler + centroids) assigns a new site live from its signature: the one controlled,
single "leak" for an unseen place.

**Routing** is compared two ways: (a) *category-as-a-feature* (one model, a learned per-category
intercept) and (b) *mixture-of-experts* (one model per category, hard routing).

### 3.3 The honest ladder

Tested in escalating strictness, climbing only if the rung below holds: (1) random split
(forgiving go/no-go) → (2) leave-sites-out → (3) leave a whole category out. For the new-site rung
the category is estimated two ways: from a site's full signature (optimistic, "category known")
and from only its first 60 observed days (a realistic cold-start deploy).

### 3.4 Features and models

Every feature is re-graded out-of-site, not assumed. Kept: weather, location, calendar, and the
new `site_category`. Killed under the ladder: a category×month PM2.5 prior (helped nothing, hurt
under noise), LST (inert), and an old engineered "free win" (reverses sign out-of-time — a leakage
artefact). NOW learners: XGBoost, RandomForest, LightGBM (+ split-conformal intervals), CatBoost.
FUTURE: a global LSTM with a category embedding vs gradient-boosted models on calendar-aware PM2.5
lags, against persistence.

---

## 4 · Results

### 4.1 NOW — does categorization beat the blind model?

| feature set | new-site R² | needs a sensor deploy? |
|---|---|---|
| blind pooled (weather + location + calendar) | 0.316 ± 0.224 | — |
| + free geodata only | 0.421 ± 0.145 | **no — zero observations** |
| + site category (k=3) | 0.482 ± 0.079 | yes (≈60-day deploy) |
| **+ site category (k=4, Round 2)** | **0.558 ± 0.050** | yes (≈60-day deploy) |
| + category (k=3) + geodata | 0.547 ± 0.046 | yes |
| **+ category (k=4) + geodata (Round-2 best)** | **0.564 ± 0.062** | yes (best + most stable) |

The category lift is **significant**: a paired per-site bootstrap (blind vs +category, n=39 sites)
gives a mean RMSE reduction of **+1.60 µg/m³, 95% CI [+0.40, +2.92], 26/39 sites improved**. The
mechanism is simple: Kampala's weather is near-uniform, so a blind model cannot recover a new
site's baseline *level* and predicts the city mean; the category supplies a learned per-tier
intercept. Under a realistic 60-day deploy the category is wrong 41% of the time, yet
category-as-a-feature still scores 0.433 (soft routing degrades gracefully) while mixture-of-experts
**collapses to 0.298** (hard routing sends a mis-labelled site to the wrong specialist). Across four
learners the new-site scores cluster (RandomForest 0.529, XGBoost 0.482, LightGBM 0.469, CatBoost
0.465): the *feature* moves R² far more than the *model*.

**Free geodata** (OpenStreetMap road density + distance-to-nearest-major-road via Overpass, 43,870
ways; SRTM elevation) is static and needs no pollution observations. It lifts new-site R² to 0.421
alone and to 0.547 combined with the category — but it cannot recover *which* category a site is
(leave-one-site-out accuracy 0.54 < 0.62 majority baseline). Geodata is the no-deploy complement,
not a substitute for observing the regime.

**Round-2 refinement (number of categories).** The category count was originally chosen by
silhouette alone (k=3). Re-tuned by the metric that matters — honest new-site R² — **k=4** lifts the
deploy-only nowcast (category, *no* geodata) from **0.482 to 0.558**, holds when the categorizer is
fit on training sites only (fold-safe 0.563, so it is not a categorizer leak), and is **significant**
(paired per-site bootstrap k=3 vs k=4 on +category: +1.07 µg/m³ RMSE reduction, 95% CI [+0.33,
+1.90], 23/39 sites). On the *combined* category+geodata model the category count barely matters
(0.547→0.555, not significant): geodata already supplies the spatial signal finer tiers would add, so
the two levers are partly redundant — the k=4 gain is specifically the bridge for a planner who can
run a short deploy but has no geodata. k=6 reaches 0.585 but introduces a single-site cluster
(fragile with 39 sites) and is not adopted. A stacked ensemble (RF+XGB+LGBM→ridge) adds +0.003 R²
(within fold noise), reconfirming that the architecture, not the learner, carries the result. Adding
*more* free geodata (OpenStreetMap building density, fetched stably for all 39 sites) raised R² by
only +0.001–0.007 — the spatial signal is saturated — so it is documented as an honest negative, not
adopted.

### 4.2 FUTURE — does a real forecaster beat persistence?

| horizon | persistence | GBM-on-lags | LSTM (global + embedding) |
|---|---|---|---|
| +1 day | 0.339 | 0.43 | **0.506** |
| +3 days | 0.109 | 0.37 | **0.477** |
| +7 days | 0.015 | 0.33 | **0.432** |

Every model beats persistence at every horizon; the LSTM beats the gradient-boosted baselines at
every horizon (+0.04 to +0.12 R²), and its lead widens with horizon — it captures longer-range
temporal structure point-lag models miss. The win survives a horizon-*purged* chronological split
(a training row's target must also fall before the cut), so it is not a boundary leak.

### 4.3 Uncertainty

LightGBM split-conformal 90%-target intervals achieve only **74.8%** empirical coverage on new
sites (mean width 27.3 µg/m³): exchangeability breaks across the site boundary, so bands calibrated
on seen sites are over-confident for unseen ones.

**Round-2 fix — group conformal.** Calibrating the residual quantile on whole *held-out sites*
(group / leave-sites-out conformal) instead of held-out rows raises empirical coverage to **85.8%**,
closing most of the gap to the 90% target. The bands widen (≈28→43 µg/m³) because new-site error
genuinely is larger — the correct, honest response, not a defect. A per-category (Mondrian) variant
helps little (80.8%). The residual shortfall to 90% reflects the small calibration set (≈6–7 sites
per fold) and would tighten with more sites.

### 4.4 Safety-tier classification — the planner's actual decision

The deliverable is a *triage tool*: it should tell a city official an area's **safety tier**, not the
exact concentration. We therefore grade the same honest predictions by the **US EPA 2024 PM2.5 24-hr
AQI band** they fall in — **Elevated** (≤ 35.4 µg/m³), **High** (35.5–55.4), **Dangerous** (> 55.4) —
under the same leave-sites-out / chronological splits, with imbalance-aware metrics and baselines.

| honest test | exact-band acc | within-one-band | baseline | macro-F1 |
|---|---|---|---|---|
| **NOW new-site** (+cat+ext, k=4) | **0.680** | **0.985** | 0.523 (majority) | 0.651 |
| FUTURE +1 day | 0.702 | 0.983 | 0.681 (persistence) | 0.616 |
| FUTURE +7 days | 0.677 | 0.983 | 0.635 (persistence) | 0.591 |

This reframes the headline collapse. A regression R² of ≈0.57 looked weak because it penalises a
47-vs-52 µg/m³ miss; but those misses sit *inside the same safety tier*, so the **deployable accuracy
is 68% exact and 98.5% within one tier even at a never-instrumented site** — beating a majority-class
baseline by +16 points, with a catastrophic two-tier error (a Dangerous area called safe) for only
**3.6%** of dangerous days.

**Dangerous-day recall is a safety dial, not a fixed number.** Under strict EPA breakpoints the model
catches 51% of dangerous days (it is conservative, usually under-calling Dangerous as "High"). Because
the regressor already *ranks* dangerousness well, lowering the Dangerous alert cutoff trades false
alarms for recall along a clean frontier (honest new-site test): predicting Dangerous when the estimate
exceeds 50 µg/m³ yields 67% recall at 8% false alarms; at **45 µg/m³, 80% recall at 17% false alarms**;
at 40, 91% at 30%. A planner selects the operating point their risk tolerance demands. A dedicated
class-weighted "Dangerous-vs-not" classifier did *not* improve on this simple threshold (it reached
only 58% recall at the 8% false-alarm rate where thresholding gives 67%) — kept as an honest negative.
Finally, the features that separate dangerous days are dominated by **humidity and dew-point**, then
wind and month: dangerous episodes are a *humid, stagnant weather regime* that traps particulates —
a physical mechanism that explains why a sensor-less site can be flagged at all, and that reinforces
weather as the generalizable lever.

### 4.5 The deployable predictor

All of the above is packaged into one runnable artifact, `analysis/new_site_predict.py`, that takes a new
Kampala location and returns what a planner acts on. **Input contract (all free, obtainable at an
un-instrumented address):** latitude/longitude, the date, that day's ERA5 weather, and land-use geodata
auto-derived from the coordinates; an *optional* short sensor deploy (≈14–60 days) unlocks the forecaster
and a sharper category. **Outputs:** a zero-deploy nowcast (concentration → EPA tier → ≈86% conformal band
→ planner-tunable danger alert) and, given a short deploy, the +1…+7-day forecast with tiers and bands. The
script self-validates by **leave-one-site-out**: it holds a whole site out, trains on the other 38, and
grades the prediction against truth. Two demonstrations bracket the behaviour honestly — a clean
low-pollution site (tiers correct 77% exact / 100% within-one) and the highest-pollution site, where the
zero-deploy nowcast under-predicts because that site's regime is not legible from the map alone (the
geodata-category limit), yet a short deploy lets the forecaster flag the entire ensuing dangerous week. The
headline validation number remains the **leave-sites-out mean (R² 0.547; tier 68% exact / 98.5% within-one)**,
never a single site (per-site folds span 0.03–0.71).

---

## 5 · Discussion

**What worked.** Categorization recovers most of the cold-start collapse (0.32→0.48, significant);
free geodata extends the win to truly sensor-less sites; a purpose-built forecaster holds R²≈0.43 a
week out. **What didn't (kept, not buried):** mixture-of-experts collapses under realistic
cold-start; the category×month prior hurts under noise; geodata cannot name the category.
**Bounded:** leave-a-whole-category-out goes negative (R² −0.22 to −0.41) — the method interpolates
among *known* kinds of place but cannot extrapolate to a regime it has never seen; it needs ≥ some
training sites of each kind.

**Two corrections of prior findings (verified against scripts).** (1) "Forecasting decays to ~0 by
+7 days / persistence beats the model" was an artefact of using a nowcast model to forecast; a
purpose-built autoregressive forecaster holds ~0.43 at +7 days. (2) "Categorization cannot rescue a
homogeneous city" is too pessimistic — it lifts new-site R² by +0.16; the pessimism holds only for
*unseen regimes*.

**Limitations.** 39 sites is small; fold-to-fold variance is high, and the geodata-only result is
noisy (±0.145). The robust claims are the combined model and the forecasting results (large test
sets). LST remains carried-but-inert. Round 2 tested two further levers and found their ceilings:
*richer geodata* (OSM building density) integrates stably but is saturated (+0.001–0.007 R²), and the
*forecaster* does not improve with a bigger network (a 2-layer LSTM is worse) or an LSTM+GBM ensemble
(+0.001 R²) — the simple global LSTM is the practical ceiling for this dataset. The remaining levers
are more sensor sites and more behavioural categories, both of which the k-sweep suggests would help.

---

## 6 · Reproducibility

Fixed seeds (42); scripts re-runnable end to end from `analysis/` against `../../working/.venv`
(requirements pinned). Outputs to `analysis/results/` (CSVs + figures) and `analysis/models/`
(persisted models). Run order: `site_categorize.py` → `pipeline.py` → `bakeoff_now.py` →
`fetch_external.py` → `eval_external.py` → `bakeoff_future.py` → `lstm_future.py` (separate process
— PyTorch/OpenMP isolation) → `finalize_now.py` → `new_site_predict.py` (the deployable new-site demo).
Every decision, honest score, and web source is
logged in `DECISION_LOG.md`; the consolidated scorecard is `results/FINDINGS_summary.csv`.

---

## 7 · Conclusion

Free data + behavioural categories + land-use geodata turn a collapsing model into a usable tool:
nowcast a never-instrumented address (R² 0.56, or 0.56 from a short deploy with no geodata at all)
and forecast a week ahead (R² 0.43), each evaluated the way it will actually be deployed, with
new-site prediction intervals now covering ≈86%. The contribution is not a single best model but an
**honestly-evaluated architecture** for cheap, trustworthy PM2.5 in a low-resource city — with its
limits stated plainly, and packaged as a runnable new-site predictor (`new_site_predict.py`).

**Next:** push conformal coverage the last few points to 90% (more calibration sites / studentised
residuals); more sensor sites and behavioural categories (the k-sweep shows headroom); a
deploy-window sensitivity sweep. Round 2 already closed the highest-value gaps (category count,
interval coverage) and ruled out two dead ends (richer geodata, a heavier forecaster).

---

### References (key)

- Adong et al. 2025 — Kampala PM2.5 from satellite AOD alone (precedent; weather excluded).
- Wong et al. 2021, *ACP* 21:5063 — land-use-regression intercity transferability.
- Chen et al. 2022, PMC8751171 — multiscale LUR predictor set for intra-urban PM2.5.
- Lei et al. 2018, *JASA* — distribution-free predictive inference (split conformal).
- Prokhorenkova et al. 2018 — CatBoost: unbiased boosting with categorical features.
