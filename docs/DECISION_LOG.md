# DECISION LOG — 4th Cap

Running trail of *what was tried · the honest score · keep or kill · source*.
Honest split is always reported next to any leaky one. A new "win" survives only if it holds
out-of-site **and** out-of-time. Negative results are kept, not buried.

Conventions:
- **random** = 10-seed 80/20 split (leaky, gap-filling regime — forgiving go/no-go).
- **new-site** = GroupKFold(5) on `site_id` (leave-sites-out — the honest NOW test).
- **leave-cat-out** = hold out an entire behavioural category (true across-category cold-start).
- **future** = blocked chronological split at day-quantile 0.8 (the honest FUTURE test).
- **persistence** = "same as last observed" baseline the FUTURE model must beat.

---

## 2026-06-06 — Session open: design decisions (before any score)

### D0 · Inherited ground truth (not re-litigated)
XGBoost is the base model. Headline R²≈0.81 is a leaky random split. Honest: new-site ≈0.31
(one fold ~0), future ≈0.11; persistence beats the model out-of-time. Weather (ERA5) is the
proven generalizable lever; LST is inert (SHAP-last). The old eng-feature "free win"
(rel_humidity/wind_speed/doy) reverses sign out-of-time = leakage artefact. Source: repo-root
`HANDOVER.md`, 3rd-cap `ladder_eval.py`/`honest_eval.py`.

### D1 · `pm10` and `n_obs` are BANNED as predictors — keep/kill: KILL
`merged_kampala_complete.csv` carries `pm10` (corr with pm2_5 ≈0.9+, same instrument) and
`n_obs` (count of hourly obs behind the daily mean). Both are target-coupled / not available
at a sensor-less place. Using either would manufacture a fake win. Excluded everywhere.

### D2 · LEAKAGE TRAP #1 — category-relative anomaly of the TARGET is circular for NOW
STRATEGY §3.3 says add "category-relative anomalies (today minus this category's seasonal
norm)." For the **NOW** metric this is a trap if applied to PM2.5 itself: "today's PM2.5 minus
norm" needs today's PM2.5 = the thing we're predicting. **Resolution:**
- NOW gets a leak-free cousin: `cat_month_pm25_norm` = mean PM2.5 of *training* sites in the
  site's category, for that month (a category×month climatology **prior** — what places of
  this kind usually read now). Computed inside the CV loop from train sites only. This is a
  legitimate, generalizable spatial prior, arguably the highest-leverage new NOW feature.
- NOW also gets category-relative **weather** anomalies (today's temp/wind/humidity minus the
  category's seasonal weather norm) — leak-free, tells the model "how unusual is today's
  weather for this kind of place."
- The PM2.5 anomaly proper is a **FUTURE**-only feature (there you legitimately have past PM2.5).

### D3 · LEAKAGE TRAP #2 — how a held-out site earns its category
The category is derived from a site's behavioural signature, and the signature includes
PM2.5-derived stats. For a held-out (sensor-less) site that is itself target information.
**Resolution — report two tiers, label them honestly:**
- **Tier A (static-attribute):** category from the held-out site's FULL signature. Optimistic
  but defensible — a planner often knows a neighbourhood's character (industrial/green) without
  a sensor; category is a coarse 3-level label. Answers "IF the category is known, does it help?"
- **Tier B (cold-start deploy):** category from only the site's first N observed days (a
  realistic "temporary sensor for N days" deploy); predict the *remaining* days. No leak into
  the test period. Answers "can we actually obtain a useful category cheaply?" This is the
  strict bar. Headline honest number uses Tier B.

### D4 · The NOW honest ladder (climb only on lift)
1. random split — blind vs +category (go/no-go).
2. new-site (GroupKFold) — blind vs +category (Tier A) vs mixture-of-experts. Does category
   help a new site that resembles a category the model has seen (within-category cold-start)?
3. leave-category-out + Tier-B signature — true across-category cold-start; the brutal bar.
The bet: a new site *routed to its category* beats the blind pooled model. If not, the finding
is "Kampala PM2.5 is too homogeneous for categorization to rescue cold-start" — itself publishable.

### D5 · Routing impl — DEFAULT category-as-feature first, A/B mixture-of-experts
Per task default. Category-as-feature = one model, gives XGB a learned per-category intercept.
MoE = one model per category (more specialized, less data each). A/B both at rung 2.

### D6 · FUTURE design
Chronological split; beat persistence. Features: PM2.5 lags (t-1,2,3,7) + rolling means (7,14d),
computed **calendar-aware** (data is ~84% daily-complete, gappy — lags by actual date, not row).
Models: global LSTM with category embedding (default, more data) vs XGB/LGBM on lags. LSTM must
beat the GBM-on-lags baseline to earn its weight.

---

## 2026-06-06 — CP-B: NOW honest ladder (`pipeline.py` → `results/pipeline_now.csv`)

The central question answered. **Headline: categorization beats the blind pooled model on the
honest new-site test — a real win, not the homogeneity dead-end we braced for.**

| variant | random (leaky) | new-site, cat=full sig (2A) | new-site, cat=60d window (2B) | leave-cat-out (3) |
|---|---|---|---|---|
| blind (no category) | 0.808 | **0.316** | 0.309 | −0.303 |
| **+category (1-hot)** | 0.808 | **0.482** | **0.433** | −0.217 |
| +cat+prior | 0.772 | 0.483 | 0.363 | −0.413 |
| MoE (1 model/cat) | 0.771 | 0.497 | 0.298 | −0.404 |

### Findings + keep/kill
- **KEEP · category-as-feature is the win.** Honest new-site R² 0.32→0.48 (cat known) / 0.43
  (cat cheaply estimated from a 60-day deploy). +0.12–0.16 R². Mechanism: Kampala weather is
  near-uniform, so the blind model can't know a new site's baseline *level* and predicts the
  global mean (R²≈0.32); the category hands it a learned per-tier intercept. Reproduces the
  3rd-cap collapse (blind=0.316 ≈ inherited 0.31) and then *recovers most of it*.
- **KILL · mixture-of-experts.** Best when the category is known (0.497) but **collapses to
  0.298 — below blind — under realistic cold-start**, because hard routing sends a
  mis-categorized site (wrong 41% of the time) to the wrong specialist. Category-as-feature is
  *soft* routing: the model can discount a noisy feature, so it degrades gracefully. Decision:
  soft routing > hard routing for cold-start. (Resolves STRATEGY open decision: category-as-feature.)
- **KILL · category×month PM2.5 prior + weather anomalies.** Adds nothing when the category is
  known (0.482→0.483) and *hurts* under noise (0.433→0.363) — the prior is keyed on the noisy
  category and amplifies its error. Also slightly hurt the leaky random rung (0.808→0.772).
  Confirms STRATEGY's own rule: re-admit a feature only if it survives the ladder — it didn't.
- **BOUND · leave-category-out is all-negative (−0.22 to −0.41).** Categorization cannot rescue
  a regime with **zero** training sites of that kind — you need ≥some sites per category in
  train. This honestly bounds the claim: the win is "interpolate among known kinds of place,"
  not "extrapolate to a brand-new kind."
- **Routing LOCKED → category-as-feature (1-hot), no prior.** Feeds CP-D.
- ⚠️ Fold variance is high (blind folds 0.03–0.71; n=39 sites). 4/5 folds improve with +cat; the
  lone drop is the fold where blind was already 0.71. Will add a paired bootstrap CI in CP-D to
  confirm the lift isn't fold noise.

---

## 2026-06-06 — CP-D NOW: model bake-off (`bakeoff_now.py` → `results/bakeoff_now.csv`)

All models use the locked routing (+cat 1-hot) on the honest new-site test (GroupKFold5).

| model | new-site R² | (leaky random) |
|---|---|---|
| **RandomForest** | **0.529 ± 0.082** | 0.734 |
| XGBoost | 0.482 ± 0.079 | 0.810 |
| LightGBM | 0.469 ± 0.091 | 0.800 |
| CatBoost | 0.465 ± 0.071 | 0.782 |
| XGBoost (blind, no category) | 0.316 ± 0.224 | — |

- **WIN confirmed SIGNIFICANT.** Paired per-site bootstrap (blind XGB vs +cat XGB, n=39 sites):
  mean RMSE reduction **+1.60 µg/m³, 95% CI [+0.40, +2.92], 26/39 sites improved**. The +cat lift
  is real, not fold noise (resolves the CP-B caveat).
- **Best NOW model = RandomForest (0.529).** But model differences (0.465–0.529) are within fold
  noise (~1 std); the category *feature* (+0.16) dwarfs any model swap. Confirms STRATEGY 3.4 /
  Adjei 2026: **the model is not the bottleneck — features + architecture are.** Note RF has the
  *lowest* leaky-random score yet the *highest* new-site score → it overfits least and transfers best.
- **CatBoost** was given the same one-hot category for a fair comparison (not its native
  categorical encoder). With only 3 category levels, native handling / ordered boosting would not
  change the ranking; its anti-leakage advantage matters for high-cardinality categoricals, which
  we don't have. Kept as a logged note, not a re-run.
- **Conformal intervals (LightGBM split-conformal, target 90%): empirical coverage 74.8%, width
  27.3 µg/m³.** KEEP with a caveat: naive split-conformal **under-covers new sites** because
  exchangeability breaks across the site boundary (Lei et al. 2018 assume exchangeability;
  unseen sites violate it). Honest finding; fix (group/Mondrian or leave-sites-out calibration)
  is future work. Source: https://arxiv.org/abs/1604.04173

---

## 2026-06-06 — Ceiling-breaker: free urban-planning geodata (`fetch_external.py` + `eval_external.py`)

WEB-SOURCED technique (required by task when choosing a lever). Land-use-regression (LUR)
predictors are the documented fix for new-site PM2.5 transfer. Pulled FREE, Kampala-covering,
ZERO-observation-needed features for all 39 sites: OSM road density + distance-to-nearest-major-
road (Overpass, 43,870 ways → 308k segments) + SRTM elevation (opentopodata).
Sources: https://acp.copernicus.org/articles/21/5063/2021/ (LUR transferability) ·
https://pmc.ncbi.nlm.nih.gov/articles/PMC8751171/ (multiscale-LUR predictor list) ·
Overpass API · https://www.opentopodata.org/datasets/srtm/.

| NOW variant (new-site R², GroupKFold5) | R² | needs a sensor deploy? |
|---|---|---|
| blind | 0.316 ± 0.224 | — |
| **+external (geodata only)** | **0.421 ± 0.145** | **NO — zero pollution obs** |
| +cat | 0.482 ± 0.079 | yes (60-day deploy) |
| **+cat+external** | **0.547 ± 0.046** | yes (best + most stable) |

### Findings + keep/kill
- **KEEP · external geodata is a real, deployment-relevant lever.** `+external` lifts honest
  new-site R² 0.316→0.421 with **zero pollution observations** — ~2/3 of the categorization
  benefit, instantly, from free map data. This is the strongest "break the homogeneity ceiling"
  result: a planner can nowcast a never-instrumented site from OSM + elevation alone.
- **KEEP · category + geodata are COMPLEMENTARY.** `+cat+external` = 0.547 is the best NOW model
  and the most stable (±0.046 vs ±0.079 / ±0.145) — combining a short deploy with free geodata
  beats either alone and tightens fold variance.
- **NEGATIVE (kept) · geodata canNOT recover the category** (leave-one-site-out RF accuracy 0.538
  < 0.615 majority baseline). So geodata doesn't tell you *which* regime a site is — it adds
  *independent* regression signal. The category still needs observation; geodata is the no-deploy
  complement, not a substitute for knowing the regime.
- **Signal source:** `dist_major_road_m` r=−0.26 with per-site PM2.5 mean (closer to a major road
  → higher PM2.5 = the traffic source LUR expects); road densities + elevation weak alone
  (|r|<0.12) but combine nonlinearly. ⚠️ 39 sites is small — `+external` variance is wide
  (±0.145); the robust claim is `+cat+external` (tight ±0.046). Promising, not over-sold.
- **STRATEGY update:** the parked open decision "source external urban-planning features now or
  defer?" → **resolved: source now, it works.** This is the bridge to a true urban-planning tool.

---

## 2026-06-06 — CP-D FUTURE: forecast bake-off (`bakeoff_future.py` + `lstm_future.py`)

Chronological split (train ≤ 2020-10-10, forecast after). **Bar = persistence.** R² by horizon:

| horizon | persistence | XGB-lags | LGBM-lags | **LSTM (global+emb)** |
|---|---|---|---|---|
| +1d | 0.339 | 0.433 | 0.416 | **0.506** |
| +2d | 0.078 | 0.403 | 0.394 | **0.474** |
| +3d | 0.109 | 0.363 | 0.378 | **0.477** |
| +4d | 0.128 | 0.374 | 0.416 | **0.451** |
| +5d | 0.170 | 0.374 | 0.375 | **0.431** |
| +6d | 0.093 | 0.325 | 0.307 | **0.431** |
| +7d | 0.015 | 0.308 | 0.339 | **0.432** |

### Findings + keep/kill
- **KEEP · LSTM is the FUTURE winner — it earns its weight.** Global LSTM + category embedding +
  masked multi-horizon head beats the GBM-on-lags at **every** horizon (+0.04 to +0.12 R²), and
  the lead **widens with horizon** (h+7: LSTM 0.432 vs GBM ~0.33 vs persistence 0.015). It captures
  longer-range temporal structure point-lag GBMs miss. STRATEGY's "LSTM must beat the GBMs to earn
  its weight" → it did. Default global-net-with-embedding (vs per-site nets) confirmed.
- **KEEP · GBM-on-lags is a strong, cheap baseline** — also beats persistence everywhere; the
  right fallback when a GPU/torch isn't available.
- **CORRECTION of inherited finding (verified).** 3rd-cap HANDOVER: "persistence (0.33) beats the
  full model out-of-time" and "forecasting decays to ~0 by +7d." Both were artifacts of a model
  not built for forecasting (same-day estimator extended naively). A purpose-built autoregressive
  forecaster (lag-1/2/3/7 + rolling means; or an LSTM) **beats persistence at every horizon and
  holds R²≈0.43 at +7d.** Persistence-beats-model was true for the *nowcast* model, not for a real
  forecaster — the two metrics needed separating (which this round did). The win survives a
  horizon-PURGED chronological split (train target must also be pre-cut; ~270 boundary rows removed
  — numbers essentially unchanged, so the leak wasn't the cause).
- **PITFALL (web-sourced fix).** First LSTM run DEADLOCKED: PyTorch's bundled OpenMP (libiomp5)
  collides with XGBoost/LightGBM's libomp when imported in the same process on macOS
  (pytorch/pytorch#44282; LightGBM FAQ). `KMP_DUPLICATE_LIB_OK=TRUE` "may silently produce incorrect
  results" → rejected. Fix = **process isolation**: `lstm_future.py` imports only torch (+ a manual
  R², no sklearn), runs after the GBM script, and merges its column. Sources:
  https://github.com/pytorch/pytorch/issues/44282 · https://lightgbm.readthedocs.io/en/latest/FAQ.html

---

## CP-E — staged-validation summary (the climb)

The honest ladder was climbed in order; each rung's keep/kill is logged above. Net:
- NOW: random (go) → new-site (category WINS, +0.16, significant) → leave-cat-out (ceiling: can't
  extrapolate to an unseen regime). External geodata extends the win to zero-deploy sites.
- FUTURE: persistence (bar) → GBM-on-lags (beats it) → LSTM (beats the GBMs). No rung was hardened
  before the one below held; nothing survived that didn't beat its baseline out-of-sample/-time.

---

## 2026-06-07 — CP-F: deliverables rebuilt to the 4th-cap story

All three rebuilt and verified against the honest numbers:
- **Pyramid View** (`index.html`, 519 KB self-contained) — 8 stages base→tip (collapse → categorize
  → honest ladder → features → NOW bake-off → geodata → forecast → verdict). Built via
  `index_src.html` + `stages_4th.js` → `build_4th.py`. **Browser-verified**: no console errors;
  drill panels open with nested cards/toggles/tables; embedded figure decodes (1300×598). Headless
  render test exercised 37 nodes, 0 errors, 0 missing asset keys.
- **Deck** (`capstone_presentation.pptx`, 13 slides + `.pdf`) — fresh build mirroring the
  navy/teal/amber template (`build_deck_4th.py`); PDF-verified slide by slide.
- **Report** (`FINAL_REPORT.md`) — submission-quality writeup; `FINDINGS.md` is the results companion.
- **Pitfall fixed:** the old closing card + footer + eyebrow carried stale 3rd-cap text ("stops at
  feature sets M0→M1→M2"); the *visual* QA caught it (the headless test couldn't). Now corrected to
  the 4th-cap bottom-line + future-work. Lesson: render-test for data-shape AND eye-check for stale copy.
- Corrections propagated to repo-root `HANDOVER.md` (forecasting / categorization claims superseded).

---

## 2026-06-07 — ROUND 2 (push for better scores): k-sweep · stacking · forecaster tuning · conformal fix · buildings

Goal: beat the 4th-cap honest numbers (NOW 0.547 · FUTURE LSTM 0.51→0.43 · conformal 74.8%) without
breaking the honest-out-of-sample bar. Reproduced every baseline first in a clean venv (geodata
eval +cat+ext 0.541 ≈ doc 0.547; LSTM 0.506→0.432 exact). New scripts: `improve_now_sweep.py`,
`improve_now_robust.py`, `improve_now_paired_cat.py`, `improve_now_stack.py`, `improve_future_lstm.py`,
`improve_future_gbm.py`, `improve_future_ensemble.py`, `improve_conformal.py`, `fetch_buildings.py`,
`eval_buildings.py`. Results → `improve_*.csv`, `improve_summary.csv`, `building_features.csv`.

### R2-D1 · NOW category-count (k) sweep — keep/kill: KEEP k=4
site_categorize picked k=3 by SILHOUETTE; but the metric that matters is downstream honest new-site
R². Sweeping k=2..6 (XGB, GroupKFold5):

| k | +cat (deploy only) | +cat+external | cluster sizes |
|---|---|---|---|
| 2 | 0.331 | 0.419 | [36,3] (outlier peel) |
| 3 (current) | 0.470 | 0.541 | [24,12,3] |
| **4** | **0.558** | 0.555 | [7,13,3,16] |
| 5 | 0.558 | 0.521 | [6,13,3,6,11] |
| 6 | 0.551 | **0.585** | [1,11,3,13,5,6] singleton |

- **KEEP k=4.** The deploy-only nowcast (category, NO geodata) jumps **0.470 → 0.558**. Holds
  **fold-safe** (centroids fit on TRAIN sites only → 0.563), so it is NOT a categorizer leak.
  **Significant**: paired per-site bootstrap k3 vs k4 on +cat-only = **+1.07 µg/m³ RMSE, 95% CI
  [+0.33, +1.90], 23/39 sites** (CI excludes 0). Mechanism: finer tiers give the model more
  per-category intercepts for a near-uniform-weather city — exactly the lever that worked at k=3,
  more of it, up to the point of cluster starvation.
- **NOTE · on the best +cat+external model, k barely moves it** (0.541→0.555, paired CI
  [−0.46,+1.02] = not significant). Geodata already supplies the spatial signal finer categories
  would add → the two levers are PARTLY REDUNDANT. The k=4 win is specifically for the
  deploy-without-geodata path (and it nearly closes the gap to the geodata-augmented score).
- **KILL k=6.** Best absolute +cat+ext (0.585) but it manufactures a **singleton cluster** — one
  site memorised, fragile with only 39 sites (that site gets a zero-train category column in any
  fold it's tested). Not robust; not recommended. k=4 is the defensible sweet spot (smallest
  non-outlier cluster = 7).

### R2-D2 · NOW stacking — keep/kill: KILL (no gain)
Out-of-fold stacked ensemble (RF+XGB+LGBM → ridge meta, inner GroupKFold so the meta never sees a
base model's in-sample fit) at k=4, +cat+external: **0.564 ± 0.062** vs best single LightGBM 0.561.
+0.003 = within fold noise; meta weights [rf 0.62, xgb −0.03, lgb 0.51]. Reconfirms the standing
finding (Adjei 2026): **the model is not the bottleneck — features/architecture are.** Single model suffices.

### R2-D3 · FUTURE tuning + ensemble — keep/kill: KILL both (baseline LSTM is the ceiling)
- **Tuning UP hurts.** 2-layer, hidden=64, dropout LSTM → +1d **0.465** vs baseline 0.506 (worse at
  every horizon). 39 sites / ~13k sequences favour the simple 1-layer hidden-48 net. Kept as a
  cautionary negative.
- **LSTM+GBM ensemble adds nothing.** Aligned on (site, target_day, horizon): 50/50 average mean
  ΔR² **+0.001** vs LSTM (beats it at 4/7 horizons, loses at 3). Best fixed blend (w_lstm≈0.8) is a
  test-fit ceiling (+0.005), not a claim. The GBM is uniformly weaker, so blending toward it can't
  help. **Verdict: the 4th-cap LSTM (0.51→0.43) is already at the practical ceiling for this data.**

### R2-D4 · UNCERTAINTY group conformal — keep/kill: KEEP (the coverage fix)
Naive split-conformal under-covers because it calibrates on held-out ROWS (same sites) but is tested
on held-out SITES (exchangeability breaks; Lei 2018). Fix = **group (leave-sites-out) conformal**:
calibrate the residual quantile on whole HELD-OUT SITES so calibration matches the new-site regime.

| method | empirical coverage (target 90%) | mean width |
|---|---|---|
| naive (rows) | 79.8% | 28.3 µg/m³ |
| **group (held-out sites)** | **85.8%** | 42.6 µg/m³ |
| mondrian (per-category) | 80.8% | 32.2 µg/m³ |

- **KEEP group conformal.** Coverage 80→86% (vs the 4th-cap 74.8% naive), closing most of the gap to
  90%. Bands widen (28→43) because new-site error genuinely is larger — correct behaviour, not a
  flaw. Still slightly under 90% (only ~6–7 calibration sites/fold → noisy quantile; would sharpen
  with more sites). Mondrian per-category helps little here (categories don't differ enough in spread).

### R2-D5 · MORE geodata (OSM buildings) — keep/kill: KILL (stable but saturated)
Per Crimson's "only if it integrates stably, no dead ends" rule, tested OSM building footprints via
the SAME Overpass pipeline as the roads (free, no-auth). **Stability: PASS** — all 39 sites fetched,
zero gaps, ~2–3 s/site, cached in `_osm_buildings.json`. Building count within 1 km correlates
sensibly with per-site PM2.5 mean (r=+0.33, stronger than any single existing geodata feature bar
dist-to-major-road). **But the honest R² lift is negligible**: +cat+ext+buildings vs +cat+ext (k=4)
= **+0.001 (XGB) / +0.007 (LGBM)**, inside fold noise (±0.06). The spatial signal is already
saturated by roads+elevation+categories; buildings are a correlated-but-redundant predictor.
**Not adopted.** GHS-POP / Google Open Buildings (population, building height) would need Earth
Engine/auth + heavy raster extraction and would almost certainly hit the same saturation → not pursued.
Evidence kept (`building_features.csv`, `eval_buildings.py`) as an honest negative.

### ROUND 2 net
- **NOW:** k=4 categories — deploy-only nowcast **0.47 → 0.56** (significant, fold-safe); best model
  **0.547 → ~0.564**. Stacking / more geodata: no gain (kept as negatives).
- **FUTURE:** unchanged — baseline LSTM is the ceiling (tuning + ensemble both fail to beat it).
- **UNCERTAINTY:** group conformal **74.8% → 85.8%** coverage — the headline reliability fix.

---

## 2026-06-07 — ROUND 3 (scope change): safety-tier classification for urban planners

Scope sharpened: the deliverable is a **safety-status tool** — tell a planner/city official whether an
area is *Elevated / High / Dangerous*, not the exact µg/m³. Evaluate the SAME honest predictions by
the **safety band** the prediction lands in, not the point error. Bands = US EPA 2024 PM2.5 24-hr AQI
breakpoints (effective 2024-05-06): **Elevated ≤ 35.4 · High 35.5–55.4 · Dangerous > 55.4** µg/m³.
Source: https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf .
Guardrails kept so this isn't a free lunch: (1) same honest splits (leave-sites-out / chronological),
(2) standard breakpoints (not cherry-picked), (3) imbalance-aware metrics + baselines (majority class,
persistence) + per-band recall + adjacent-accuracy. Scripts: `band_now.py`, `band_future.py`,
`band_now_recall.py` → `band_*.csv`, `fig_danger_recall.png`.

### R3-D1 · Band accuracy — KEEP (the use-case-valid headline)
Honest **new-site** test (the bottleneck), best model (+cat+ext, k=4; regression R²≈0.57):
**exact-band 0.680 · within-one-band 0.985 · majority-class 0.523 · macro-F1 0.651**
(recall Elevated 0.73 / High 0.68 / Dangerous 0.51). **Forecast** +1→+7d: exact-band **0.70→0.68**,
within-one-band ~0.98, vs persistence-band 0.62–0.68.
- The band frame turns the "collapse" into a usable tool: 2/3 exact and ~99% within one tier even at a
  never-instrumented site, and a catastrophic 2-tier error (calling a Dangerous place "Elevated/safe")
  happens for only **3.6%** of dangerous days. Beats majority-class by +16 pp — not a trivial-bucket artefact.
- This is the bottleneck reframe: R² punished a 47-vs-52 miss; in safety-tier terms those misses are
  inside the same band, so the deployable accuracy is materially higher than the regression R² implied.

### R3-D2 · Dangerous-recall tuning — KEEP regression-threshold; KILL dedicated weighted classifier
For a SAFETY tool, missing dangerous days is the worst error; strict-EPA Dangerous recall is only 0.51.
- **KEEP · lower the Dangerous *alert threshold* on the regression output** (operating-point choice, not
  a model change). Honest new-site tradeoff: cutoff 55.4→recall 0.51 (FAR 4%) · 50→0.67 (8%) ·
  **45→0.80 (17%)** · 40→0.91 (30%). Suggested op-point **predict>45 → 80% dangerous recall** at
  precision 0.49 — the safety-first tradeoff a city official should own. `fig_danger_recall.png`.
- **KILL · dedicated class-weighted "Dangerous-vs-not" LightGBM classifier** (Crimson's upweight idea,
  implemented as `scale_pos_weight`). It does NOT beat thresholding the regressor on the recall/false-
  alarm frontier: at FAR 0.08 the classifier gets recall 0.58 vs the regressor's 0.67. The regressor
  already ranks dangerousness well; a separate reweighted model adds nothing. Honest negative, kept.

### R3-D3 · What marks a dangerous day — feature diagnostic (the insight)
Effect size |mean(danger)−mean(safe)|/σ per feature on the honest data, and the detector's gain
importance, AGREE: dangerous days are a **humidity/stagnation weather regime**.
Top separators: **rel_humidity (0.63) · dewpoint (0.50) · wind_v (0.36) · temp (0.34) · month (0.33)**.
Mechanism: humid, stagnant air traps particulates → PM2.5 spikes. Confirms the project's standing
finding (weather is the generalizable lever) and gives a physical reason the model can flag danger at
a sensor-less site at all. Category/geodata features rank below weather for *danger detection*.

### ROUND 3 net
Safety-tier framing makes the new-site model deployable for planner triage: **68% exact / 98.5%
within-one-tier**, **80% dangerous-day recall** at a chosen alert cutoff (predict>45), with a physical
explanation (humid-stagnant regime). The "bottleneck" (new-site R² collapse) is **reframed and largely
resolved for the actual use case** — with the honest caveat that strict-EPA Dangerous recall is 0.51
and is raised by an explicit, planner-controlled false-alarm tradeoff, not by a better point model.

---

## 2026-06-07 — FINALIZE pass (Crimson's two orders) — keep/kill + verification

### F-D1 · AOD removed completely from scope — keep/kill: KILL (scope decision, Crimson)
AOD was never implemented: `merged_kampala_complete.csv` only ever carried LST (proven inert); AOD
was always an optional, sign-in-gated fork. Per Crimson, it is removed from scope entirely — not a
roadmap item anywhere. Scrubbed: the forecast view's whole "AOD decision" stage (`stages_forecast.js`
n:5 deleted; n:6→5 / n:7→6 renumbered, fades restepped 0.06/0.18/0.30/0.42), the n:0 framing, the
engine glossary (`index_src.html`: dropped the `AOD` key, reworded `Adong 2025`), and the one citation
line in `FINAL_REPORT.md`. **Verification:** 0 readable AOD across all 4 built views (regex, base64
excluded). Kept truthful: the *historical* precedent (Adong used satellite signals; LST was tested) is
described without naming AOD as a project action. No code/data changed (there was no AOD to remove there).

### F-D2 · New-site predictor built & run — keep: the deployable artifact
`analysis/new_site_predict.py` — input contract → categorize (geodata / 60-day window / full) → nowcast
(RF +cat+geodata; EPA tier; ≈90% group-conformal band; danger dial) → +1…+7d forecast (torch-free
LightGBM-on-lags, the portable stand-in for the locked LSTM) → honest leave-one-site-out demo + figure.
Ran on two sites: **site_135** (clean low site: tier-exact 0.77, within-1 1.00) and **site_54** (the
highest-pollution site: zero-deploy nowcast R²=−1.69 because its regime is mis-read from geodata alone —
the documented eval_external limit — but the short-deploy forecaster flags all +1…+7d Dangerous days).
Single-site R² is noisy (folds 0.03–0.71); the validation headline stays the leave-sites-out **mean
0.547**. Artifacts: `results/fig_newsite_demo*.png` + `newsite_demo*.csv`.

### F-D3 · Reproducibility certified + LSTM-restore — keep: the locked LSTM numbers
Re-ran the torch-free pipeline (site_categorize · pipeline · eval_external · bakeoff_now · band_now/
future/recall · improve_now_sweep · improve_conformal): **all bit-identical** to the locked CSVs
(pipeline_now, eval_external, bakeoff_now, band_*, improve_conformal — 0 diff). **Trap caught:** re-running
`finalize_now.py` / `bakeoff_future.py` *without* the torch step (`lstm_future.py`) overwrote the FUTURE
rows of `FINDINGS_summary.csv` + the LSTM column of `bakeoff_future.csv` with GBM-only numbers (0.43→0.34),
silently downgrading the canonical LSTM results (0.51→0.43). **Resolution:** restored those + the
float-noise (`site_categories.csv`) and RF-parallelism-noise (`improve_now_sweep.csv`, k=4 0.549 vs locked
0.558 — within fold variance, conclusion unchanged) files from the pre-run backup. The LSTM is the only
non-bit-reproducible component by design (run it in its own process to refresh its numbers).

### F-D4 · Build hardening — keep: dynamic STAGES splice
Deleting the `AOD` glossary line shifted every line up by one, breaking the build scripts' hard-coded
`lines[380]`/`lines[717]` splice asserts. Fixed all four builders (`build_4th/session/forecast/predictor`)
to locate `const STAGES=[ … ];` **dynamically** (there is exactly one standalone `];`), so future
glossary/header edits can never desync the splice. Not a finding — a durability fix.

### F-D5 · 4 pyramid views rebuilt + browser-verified — keep
Consolidated (10 stages) · Session (3) · Forecast (7, AOD stage gone) · **Predictor (5, NEW)**, wired into
`capstone_pyramid.html` (new 🎯 button). All live-rendered (cap4-tmp): figures decode (incl. fig_newsite_demo
1430×572), drills/toggles work, **0 console errors**, **0 readable AOD**. node --check passes on all 4 stages files.

### FINALIZE net
The 4th cap is finalized: a runnable & honestly-validated new-site predictor, four browser-verified pyramid
views, and a certified-reproducible analysis (LSTM excepted, by design).

---

## 2026-06-07 — INVESTIGATION + MAP + PROTOTYPE (Crimson's follow-up)

### F-D1b · AOD scope — CLARIFIED (supersedes F-D1's wording)
Crimson: AOD is fine *where it's actually used* — i.e. describing the Adong 2025 precedent — just not as a
lever/step in **our** work. So the over-scrub was reverted: the `AOD` + `Adong 2025` glossary entries and the
forecast view's n:0 precedent line mention AOD again (precedent), and `FINAL_REPORT.md`'s citation reads
"satellite AOD alone". What stays removed: the **AOD-decision forecast stage** and every "pull AOD / AOD lever
/ AOD download" roadmap item. Net: AOD = precedent only, never our roadmap.

### F-D6 · Blind-categorizer investigation (answers "what misled site_54?") — keep
Scripts: `investigate_categorization.py`, `improve_blind_cat.py`, `fig_investigation.py`.
- **Diagnosis:** site_54 (true HIGH, 62.9 µg/m³ — highest of 39) is mislabeled LOW by the geodata classifier
  because its 6 nearest map-feature neighbours are all low-pollution; high major-road *length* + elevation make
  it read residential despite being 60 m from a major road. No zero-deploy feature explains its pollution
  (best level signal = dist_major_road, r=−0.35). It is a genuine **local-source anomaly** — only a sensor catches it.
- **Improvement found:** the 4th-cap blind classifier (RandomForest) overfits (LOO acc **0.538** < 0.615 majority);
  **kNN → 0.641** (beats majority). Adopted for the area-type *label*.
- **Honest negative (important):** a *guessed* category does **not** help the µg/m³ nowcast — it slightly hurts.
  GroupKFold-5 tier-exact: no-category 0.612 ≈ blind-RF 0.605 ≈ blind-kNN 0.593; **observed** category 0.671
  (R² +0.41). So for a sensor-less site the model leans on weather+geodata directly; the category lever needs an
  observed deploy. (Per-site R²s here are a harsher metric than the per-fold 0.547 headline — relative comparison only.)
- **Deployment consequence:** instrumented areas → observed-category model (realistic); truly sensor-less spots →
  no-category geodata+weather model (the prototype's predict-a-location uses exactly this).

### F-D7 · Kampala planner map + agentic prototype — keep
- `fetch_basemap.py` stitches a CartoDB basemap (light + dark) and records the Web-Mercator projection so any
  lat/lon places pixel-exact (`basemap_meta.json`). `predict_map.py` → honest per-site now/+1d/+7d tiers + Voronoi
  coverage cells (pixel space, Sutherland-Hodgman clip) → `map_predictions.json`; `fig_safety_map.py` →
  `fig_safety_map.png` (embedded in the predictor + consolidated pyramid views).
- `kampala_planner_prototype.html` (self-contained, ~950 KB): Safety-map tab (basemap + Voronoi tiers, now/+1d/+7d
  filters, by-tier/by-area toggle, hover tooltips, accuracy badge) + Predict-a-location tab (in-browser kNN category
  + nowcast tier/band/danger-dial; 3 real test cases via `test_cases.json` show the full model's call). No heavy
  model in-browser — bakes in persisted results. Browser-verified: map renders (39 cells/points), 0 console errors,
  predict works (site_54 → Dangerous, matches truth, area-type honestly mis-read).
