# HANDOVER — 4th Cap Handover
# Status: ✅ CLOSED / FINALIZED (2026-06-07) — nothing pending · no carryover. ▶ START HERE: open `index.html`.
#         Built: new-site predictor · blind-cat investigation (site_54 = the Kalerwe market node, externally
#         confirmed) · Kampala planner MAP · agentic PROTOTYPE · START-HERE landing page + rendered doc HTMLs.
#         ✅ COMPLETE (CP-A…CP-F) · ✅ ROUND 2 (k=4 · group conformal) · ✅ ROUND 3 (safety tiers) — all locked.
# Last updated: 2026-06-07 (follow-up — site_54 investigation + kNN blind-cat fix · planner map (Voronoi over a Kampala basemap) · kampala_planner_prototype.html · all views rebuilt & browser-verified)

# ➡️ STATUS — finalize handover DONE; Crimson's follow-up DONE.
#    AOD (clarified): NOT a lever/roadmap item in our work — the "AOD decision" forecast stage stays deleted and no
#        "pull AOD" step exists. AOD appears ONLY where it's factually used: the Adong-2025 precedent (glossary +
#        forecast n:0 + FINAL_REPORT citation + deck precedent line). Decks carry exactly 1 AOD each (precedent).
#    NEW-SITE PREDICTOR — `analysis/new_site_predict.py` (input contract → nowcast tier+band+danger-dial → +1…+7d
#        forecast → leave-one-site-out demo on site_135 + site_54). Surfaced as the 🎯 Predictor view (now 6 stages:
#        + a planner-map tip). Reproducibility certified: torch-free scripts bit-identical; LSTM kept canonical.
#    INVESTIGATION (Crimson's Q on site_54) — `investigate_categorization.py` + `improve_blind_cat.py` + figure:
#        site_54 is a local-source anomaly no free feature reads; the blind categorizer RF→kNN lifts 0.54→0.64
#        (beats majority); a GUESSED category does NOT help the nowcast (only an observed one does). See FINDINGS §🔬.
#    MAP + PROTOTYPE — `fetch_basemap.py`→basemap · `predict_map.py`→per-site tiers+Voronoi · `fig_safety_map.py`→
#        the embedded 3-panel map (in the predictor + consolidated views) · `kampala_planner_prototype.html`
#        (self-contained: safety map with now/+1d/+7d filters + tooltips, and a predict-a-location page). Browser-verified.

## ⏸️ RESUME HERE — ROUND 2 (2026-06-07): pushed for better scores
Goal was to beat the 4th-cap honest numbers. Reproduced every baseline first (clean venv), then:
- **NOW win — k=4 categories.** Deploy-only nowcast (category, no geodata) **0.470 → 0.558**
  (fold-safe 0.563 → not a leak; significant, paired bootstrap +1.07 µg/m³ CI[+0.33,+1.90], 23/39).
  Best combined +cat+geodata model ~**0.564** (was 0.547). k=6 → 0.585 but singleton cluster = fragile.
  Stacking adds +0.003 (noise). **k=4 is the new recommended setting.**
- **UNCERTAINTY win — group conformal.** New-site interval coverage **74.8% → 85.8%** (calibrate on
  held-out SITES not rows); bands honestly widen 28→43 µg/m³. `improve_conformal.py`.
- **FUTURE — no gain (honest negative).** Bigger LSTM is worse (0.465 vs 0.506); LSTM+GBM ensemble
  +0.001. Baseline LSTM (0.51→0.43) is the ceiling for 39 sites.
- **More geodata — dead end (validated then rejected).** OSM building density fetched stably for all
  39 sites (no gaps), correlates with PM2.5 (r=+0.33) BUT adds only +0.001–0.007 R² (saturated).
  Not adopted; kept as honest negative. GHS-POP/Google Open Buildings need auth + likely same result.

**New scripts (in analysis/):** improve_now_sweep.py · improve_now_robust.py · improve_now_paired_cat.py
· improve_now_stack.py · improve_future_lstm.py · improve_future_gbm.py · improve_future_ensemble.py
· improve_conformal.py · fetch_buildings.py · eval_buildings.py.
**New results:** results/improve_*.csv · improve_summary.csv · building_features.csv · fig_improve_now.png.
**Text records UPDATED to Round 2:** FINDINGS.md · DECISION_LOG.md (§ROUND 2) · FINAL_REPORT.md.
**Sandbox venv note:** the Mac `working/.venv` can't run in a Linux sandbox; a fresh venv reproduced
all baselines exactly. catboost was skipped (non-essential; doesn't change rankings per CP-D).

## ⏸️ ROUND 3 (2026-06-07): SCOPE CHANGE → safety-tier classification for planners
The scope sharpened to a **safety-status tool** (Elevated/High/Dangerous on EPA 2024 PM2.5 bands:
≤35.4 / 35.5–55.4 / >55.4). Same honest predictions, graded by the BAND they land in.
- **Bottleneck reframed & largely resolved for the use case.** Honest new-site: **exact-tier 68% ·
  within-one-tier 98.5%** (vs 52% majority); only 3.6% of dangerous days called "safe". Forecast
  +1→+7d: 70%→68% exact, ~98% within one tier (beats persistence-band).
- **Dangerous-day recall is a planner-tunable dial.** Lower the Dangerous alert cutoff on the
  regressor: 55.4→0.51 (4% FAR) · 50→0.67 (8%) · **45→0.80 (17%)** · 40→0.91 (30%). Suggested
  op-point predict>45 → 80% recall. A dedicated class-weighted classifier did NOT beat this (killed).
- **Insight:** dangerous days = humid/stagnant weather regime (rel_humidity + dewpoint separate them
  most). Weather is what lets the model flag danger at a sensor-less site.
- New scripts: `band_now.py · band_future.py · band_now_recall.py`. Results: `band_*.csv ·
  band_summary.csv · fig_danger_recall.png`. Records updated: FINDINGS (⭐ Round-3 section) ·
  DECISION_LOG (§ROUND 3) · FINAL_REPORT (§4.4 + abstract).

**✅ DECK REBUILT** → `capstone_presentation_v2.pptx` (15 slides) + `capstone_presentation_v2.pdf`,
on-brand, +2 new slides (11·Safety Tiers, 12·Danger Alerting), k=4 + group-conformal numbers threaded,
PDF-exported and visually QA'd (slide_12.png / slide_13.png are the QA renders — can be deleted).
Builder: `build_deck_4th.py` (set env `DECK_OUT` for the filename; mount is write-once so a new name
was used rather than overwriting the 4th-cap deck).

**✅ PYRAMID VIEWS — 4 LENSES, REBUILT + BROWSER-VERIFIED (open `capstone_pyramid.html` — the switcher):**
- `index_consolidated.html` (~3.1 MB) — 📚 the WHOLE story, 10 stages base→tip: collapse → categorize →
  ladder → features → NOW bake-off → geodata → forecast → verdict → **(8) sharper model (k=4 +
  conformal + negatives)** → **(9) safety tiers (the tool)**. `stages_4th.js` + `build_4th.py`
  (env `PYRAMID_OUT=index_consolidated.html`).
- `index_session.html` (~3.1 MB) — ④ THIS SESSION only, 3 stages: mission → sharper model → safety tiers.
  `stages_session.js` + `build_session.py`.
- `index_forecast.html` (~3.1 MB) — 🔮 the A→Z arc (road behind / road ahead), now **7 stages** (the AOD
  stage removed, renumbered). `stages_forecast.js` + `build_forecast.py`.
- `index_predictor.html` (~3.1 MB) — 🎯 **NEW** the deployable tool, 5 stages base→tip: **inputs (contract)
  → categorize → nowcast (tier+band+dial) → forecast (+1…+7d) → proof (held-out demo)**. Embeds the new
  `fig_newsite_demo*` + the locked analysis figs. `stages_predictor.js` + `build_predictor.py`.
- All four **live-rendered in a browser** (cap4-tmp preview): figures decode (incl. fig_newsite_demo at
  1430×572), drills/toggles/accordions work, **0 console errors**, **0 readable AOD** (grep, base64 excluded).
- The 4 build scripts were hardened: STAGES is now located **dynamically** (no hard-coded line numbers), so a
  glossary/header edit can never desync the splice again. `capstone_pyramid.html` has the new 🎯 Predictor button.

**Nothing left outstanding for the 4th cap.** Optional (not done, out of this scope): refresh the older
sibling `cap-handover/` + `3rd-cap-handover/` deliverables and `deliverables/cap-handover.zip` to the 4th-cap
state; re-train the LSTM (its numbers are already locked).

---

## What this folder is
A fork of `3rd-cap-handover` that pivoted the capstone from *"which cheap data lever helps?"* to
a usable **categorize-then-predict** pipeline for an urban planner. Two metrics kept separate end
to end: **NOW** (nowcast a sensor-less site) and **FUTURE** (forecast +1…+7 days).

## Read in this order
1. `FINDINGS.md` — the honest results, Flowline-shaped. **START HERE.**
2. `DECISION_LOG.md` — every experiment · honest score · keep/kill · web source.
3. `STRATEGY_4th-cap.md` — the original reframe spec (now executed).
4. `analysis/` — the scripts + `results/` (CSVs + figures) + `models/` (persisted).

## Headline (all honest = out-of-sample / out-of-time)
- **Categorization rescues cold-start (NOW).** New-site R² **0.32 (blind) → 0.48 (+category)**;
  significant by paired per-site bootstrap (+1.60 µg/m³ RMSE, CI [+0.40, +2.92], 26/39 sites).
- **Free geodata is a zero-deploy lever.** OSM roads + SRTM elevation → **0.42 with zero pollution
  observations**, **0.55** combined with the category (best + most stable model).
- **Soft routing wins.** Category-as-a-feature beats mixture-of-experts (MoE collapses to 0.30 under
  realistic cold-start). Best NOW learner = RandomForest (0.529); model barely matters vs features.
- **FUTURE: a real forecaster beats persistence to +7d.** LSTM (global + category embedding) is best
  (+1d 0.51 … +7d 0.43), beating GBM-on-lags at every horizon; persistence decays to ~0.
- **Honest ceiling:** leave-a-whole-category-out goes negative — can't extrapolate to an unseen regime.
- **Two prior claims corrected (verified):** (1) forecasting does NOT decay to ~0 by +7d; (2)
  "persistence beats the model" was true only for the nowcast model, not a purpose-built forecaster.

## Done this session (CP-A…CP-F)
- CP-A (inherited): 39 sites → 3 categories (`analysis/site_categorize.py`, `categorizer.json`).
- CP-B: NOW honest ladder (`pipeline.py`) — blind vs +cat vs +prior vs MoE × 4 rungs. Routing LOCKED
  = category-as-feature; prior + MoE killed.
- CP-C: feature build (`features.py`) — `site_category`, leak-free cat×month priors (tested, killed),
  calendar-aware FUTURE lags. Banned `pm10`/`n_obs` as target-coupled.
- CP-D NOW: model bake-off (`bakeoff_now.py`) + split-conformal intervals + paired significance.
- CP-D FUTURE: `bakeoff_future.py` (persistence + GBM-on-lags) + `lstm_future.py` (LSTM, isolated).
- Ceiling-breaker: `fetch_external.py` (OSM + elevation) + `eval_external.py` (geodata as 0-deploy feature).
- CP-E: staged-validation trail in `DECISION_LOG.md`.
- CP-F: `FINDINGS.md`, `results/FINDINGS_summary.csv`, persisted `models/`, pinned `requirements.txt`.

## Run (venv at ../../working/.venv; run from analysis/)
```
python site_categorize.py   # CP-A
python pipeline.py          # CP-B  NOW ladder
python bakeoff_now.py       # CP-D  NOW models + conformal + significance
python fetch_external.py    # geodata (network)
python eval_external.py     # ceiling-breaker
python bakeoff_future.py    # CP-D  FUTURE GBMs + persistence
python lstm_future.py       # CP-D  FUTURE LSTM  (SEPARATE process — OpenMP isolation, see DECISION_LOG)
python finalize_now.py      # CP-F  persist models + consolidated summary
```

## Deliverables — REBUILT & VERIFIED (this session)
- **Pyramid View** `index.html` (519 KB, self-contained) — 8 stages base→tip telling the full
  categorize-then-predict story; browser-verified (no console errors, drills open, figures decode).
- **Deck** `capstone_presentation.pptx` (13 slides) + `capstone_presentation.pdf` — on-brand
  navy/teal/amber template; PDF-verified slide by slide.
- **Report** `FINAL_REPORT.md` — submission-quality academic writeup (abstract → method → results
  → discussion → reproducibility). `FINDINGS.md` is the results-focused companion.

### Build workflow (the deliverables are *built*, re-runnable)
- Pyramid View: `index_src.html` (stripped engine) + `stages_4th.js` (content) → `build_4th.py`
  (splices stages, refreshes header/footer/glossary, injects figs/scripts/CSVs from `analysis/`).
  Edit `stages_4th.js`, re-run `build_4th.py`. Backup: `index.html.bak` (old 3rd-cap build).
- Deck: `build_deck_4th.py` (python-pptx, mirrors the template). Backup: `capstone_presentation_3rd.pptx.bak`.
- Preview (TCC workaround): copy `index.html` → `/tmp/cap4_preview/`, serve, or use launch config `cap4-tmp`.

## Open / next (future work — not blocking)
- Conformal intervals under-cover new sites (74.8% vs 90%) — group/Mondrian conformal.
- More sites / more categories would sharpen routing (39 sites, 3 categories is small).
- Deploy-window sensitivity sweep (30/60/90 days) · richer geodata (population, NDVI, building density).
