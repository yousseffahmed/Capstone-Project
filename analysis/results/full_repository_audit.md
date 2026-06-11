# Complete Repository Inheritance Audit

Date: 2026-06-11  
Repository: `4th-cap-handover`  
Auditor stance: distrust all narrative until traced to code, data, or generated output.  
Scope note: this audit creates this one file only. It does not alter pipeline code, docs, HTML, figures, models, or CSV outputs.

## Executive Verdict

The repository is a strong capstone handover with unusually good evidence discipline for the main story, but it is not a clean production repository. It is a research archive plus browser deliverable. The core accepted result is defensible:

- NOW: accepted production/research recommendation remains k=4 categorize-then-predict for new-site/safety framing.
- FUTURE: LSTM remains the headline forecaster, with RF and rolling-7 persistence now documented as challengers.
- k=6 is meaningful but fragile; full-history k=6 is a non-deployable upper bound, not a production replacement.
- Random split metrics are present but mostly labeled as leaky/diagnostic.

The largest risks for a new owner are stale generated artifacts, multiple generations of result files, untracked scripts/outputs, and presentation/report lag behind the newest audit. The project can be defended, but the defender must state clearly which claims are final, which are diagnostic, and which are superseded.

Confidence in this audit: 82/100. I inspected repository files, scripts, CSVs, markdown, HTML, and PPTX slide text. I did not rerun all models end-to-end, did not extract the PDF because `pdftotext` is unavailable, and did not verify binary model contents beyond their presence.

---

## SECTION 1 - REPOSITORY INVENTORY

### Significant File Classification

| path/pattern | classification | role | evidence / notes |
|---|---|---|---|
| `data/merged_kampala_complete.csv` | Active research artifact | Single working table for PM2.5, weather, LST, location, calendar | Read by `analysis/features.py`; docs say raw data was quarantined and this is the kept table. |
| `analysis/features.py` | Active production/research artifact | Shared feature builder, category assignment, future panel builder | Used by most analysis scripts. Contains explicit banned predictors and leak-aware utilities. |
| `analysis/site_categorize.py` | Active research artifact | Builds original k=3 site categorizer | Generates `site_categories.csv`, `cluster_profiles.csv`, `categorizer.json`, figures. |
| `analysis/pipeline.py` | Active research artifact | NOW honest ladder | Generates `pipeline_now.csv`, `fig_now_ladder.png`. Uses random, leave-site-out, leave-category-out. |
| `analysis/bakeoff_now.py` | Active research artifact | NOW model bakeoff | Generates `bakeoff_now.csv`, `fig_bakeoff_now.png`. |
| `analysis/bakeoff_future.py` | Active research artifact | FUTURE GBM/persistence bakeoff | Generates `bakeoff_future.csv`, `fig_bakeoff_future.png`; later updated by LSTM script. |
| `analysis/lstm_future.py` | Active research artifact | FUTURE LSTM training/evaluation | Writes `models/lstm_future.pt`, updates `bakeoff_future.csv`, `fig_bakeoff_future.png`. |
| `analysis/finalize_now.py` | Active production artifact | Persists final NOW models and summary CSV | Writes `models/now_rf_cat.joblib`, `models/now_xgb_cat_ext.joblib`, `FINDINGS_summary.csv`. |
| `analysis/new_site_predict.py` | Active production/demo artifact | Runnable new-site predictor demo | Writes `newsite_demo*.csv/png`; referenced as deployable tool script. |
| `analysis/fetch_external.py` | Active research artifact | Fetches OSM road features and elevation | Generates `external_features.csv`; network dependency. |
| `analysis/fetch_buildings.py`, `analysis/eval_buildings.py` | Active research artifact / negative result | Building density experiment | Generates `building_features.csv`; result documented as saturated/minimal lift. |
| `analysis/fetch_basemap.py`, `fig_safety_map.py`, `predict_map.py`, `predict_testcases.py`, `export_ref.py` | Active deliverable-support artifacts | Planner map/prototype data and figures | Generate basemap, `map_predictions.json`, `test_cases.json`, `ref_sites.json`, `fig_safety_map.png`. |
| `analysis/band_now.py`, `band_future.py`, `band_now_recall.py` | Active research artifact | Safety-tier evaluation and alert threshold | Generate `band_summary.csv`, `band_future.csv`, `band_now_recall_tradeoff.csv`, figures. |
| `analysis/investigate_categorization.py`, `improve_blind_cat.py`, `fig_investigation.py` | Active research artifact | Blind category/site_54 diagnosis | Generate `categorization_investigation.json`, `improve_blind_cat.json`, `fig_blindcat_investigation.png`. |
| `analysis/improve_now.py`, `improve_now_sweep.py`, `improve_now_robust.py`, `improve_now_paired_cat.py`, `improve_now_stack.py` | Active research artifacts / some deprecated by newer audit | Round-2 NOW improvement experiments | Evidence for k=4 refinement, stacking negative, robustness. Some outputs superseded by `improve_honest_now.py` and final decision table. |
| `analysis/improve_future_lstm.py`, `improve_future_gbm.py`, `improve_future_ensemble.py`, `improve_conformal.py` | Active research artifacts / older improvement layer | Future/conformal improvement experiments | Generate `lstm_preds_base.csv`, `gbm_preds.csv`, `improve_future.csv`, `improve_conformal.csv`. |
| `analysis/improve_honest_now.py` | Active research artifact, untracked | Later honest audit for NOW/safety/uncertainty | Generates `now_improvement_experiments.csv`, `safety_improvement_experiments.csv`, uncertainty/figures. |
| `analysis/improve_honest_future.py` | Active research artifact, untracked | Later FUTURE challenger/uncertainty audit | Generates `future_improvement_experiments.csv`, updates `uncertainty_calibration.csv`. |
| `analysis/diagnose_k6_deployability.py` | Active research artifact, untracked | k=4/k=6 and k=6 deployability diagnosis | Generates k4/k6 comparison, window sensitivity, category error analysis, deployable improvement CSV/figure. |
| `analysis/future_same_row_benchmark.py` | Active research artifact, untracked | Fair FUTURE same-row benchmark | Generates `future_same_row_benchmark.csv`, `fig_future_same_row_benchmark.png`. |
| `analysis/models/*.joblib`, `analysis/models/lstm_future.pt` | Generated model output | Persisted fitted models | Need binary loading test before production trust. |
| `analysis/results/*.csv`, `*.json`, `*.png`, `*.md` | Generated output / research evidence | Metrics, figures, summaries | Many are self-contained evidence; some are superseded or diagnostic only. |
| `docs/FINAL_REPORT.md` | Documentation | Main written report | Strong, but not fully updated with final k=6 audit warning. |
| `docs/FINDINGS.md` | Documentation | Results companion | Updated with final honest improvement audit. |
| `docs/DECISION_LOG.md` | Documentation | Running decisions | Good trace record but long and multi-generation. |
| `docs/CONTEXT.md` | Documentation | Folder map / run order | Updated with final audit notes. |
| `docs/HANDOVER.md`, `docs/STRATEGY_4th-cap.md` | Documentation / historical | Handover and strategy | Useful context; not the final defense source. |
| `docs/capstone_presentation_v2.pptx` | Active presentation artifact | Slide deck | Text extracted from PPTX; lacks newest k=6/RF caveat section. |
| `docs/capstone_presentation_v2.pdf` | Generated presentation output | PDF deck | Could not extract text locally (`pdftotext` missing); assume generated from PPTX but unverified. |
| `build/build_home.py` | Active build source | Builds root `index.html` and rendered doc HTML | Recently updated with final audit note. |
| `build/build_4th.py`, `build/build_session.py`, `build/build_forecast.py`, `build/build_predictor.py` | Active build sources | Build pyramid pages from `index_src.html` plus stage JS | Inject all PNGs, Python scripts, CSVs into HTML. |
| `build/build_prototype.py` | Active build source | Builds planner prototype HTML | Recently updated with final audit guardrail. |
| `build/build_deck_4th.py` | Active build source / stale deck source | Builds deck | Deck output appears older than final audit; should be rerun/updated if presentation is final. |
| `build/index_src.html` | Active build source | Generic pyramid engine | Should not contain research claims. |
| `build/stages_*.js` | Active build source | Browser-facing content for pyramid views | Updated with final audit guardrails. |
| `build/_assets/marked.min.js` | Third-party build asset | Markdown renderer | Vendor/generated; active. |
| `index.html` | Generated output / active deliverable | Root browser entry point | Generated by `build_home.py`; contains final audit note. |
| `pages/*.html` | Generated output / active deliverables | Browser pages | Generated except `capstone_pyramid.html` appears static wrapper. |
| `README.txt` | Documentation | User-facing handover | Mostly correct but finalized date 2026-06-07 predates final 2026-06-10 audit. |
| `README.md` | Unknown/dead | One-line or minimal | Not substantive. |

### Dependency Map

```text
Data
  data/merged_kampala_complete.csv
    -> analysis/features.py
    -> site signatures, NOW rows, FUTURE lag panels

Features
  analysis/features.py
    -> BASE_NOW weather/location/calendar/engineered weather
    -> banned predictors list: pm10, n_obs
    -> site signatures: PM2.5 summary + climate
    -> future lag/rolling panel
  analysis/fetch_external.py
    -> analysis/results/external_features.csv
  analysis/fetch_buildings.py + eval_buildings.py
    -> analysis/results/building_features.csv

Models / experiments
  site_categorize.py
    -> categorizer.json, site_categories.csv, cluster_profiles.csv
  pipeline.py
    -> pipeline_now.csv, fig_now_ladder.png
  bakeoff_now.py
    -> bakeoff_now.csv, fig_bakeoff_now.png
  eval_external.py
    -> eval_external.csv, fig_external.png
  bakeoff_future.py + lstm_future.py
    -> bakeoff_future.csv, fig_bakeoff_future.png, models/lstm_future.pt
  band_*.py
    -> band_summary.csv, band_future.csv, band_now_recall_tradeoff.csv
  improve_*.py / diagnose_*.py / future_same_row_benchmark.py
    -> improvement CSVs, figures, final audit markdowns

Results
  analysis/results/*.csv, *.json, *.png, *.md
    -> docs/*.md narrative
    -> build/*.py embeds CSVs/scripts/figures

Docs
  docs/FINDINGS.md, FINAL_REPORT.md, DECISION_LOG.md
    -> pages/FINDINGS.html, FINAL_REPORT.html, DECISION_LOG.html via build_home.py
  docs/capstone_presentation_v2.pptx/pdf
    -> generated by build_deck_4th.py, but appears stale vs final audit

HTML
  build/build_home.py -> index.html + rendered docs pages
  build/build_4th.py + build/stages_4th.js + build/index_src.html -> pages/index_consolidated.html
  build/build_session.py + build/stages_session.js + build/index_src.html -> pages/index_session.html
  build/build_forecast.py + build/stages_forecast.js + build/index_src.html -> pages/index_forecast.html
  build/build_predictor.py + build/stages_predictor.js + build/index_src.html -> pages/index_predictor.html
  build/build_prototype.py -> pages/kampala_planner_prototype.html
```

### Script-to-Output Map

| script | primary outputs |
|---|---|
| `site_categorize.py` | `site_categories.csv`, `cluster_profiles.csv`, `categorizer.json`, `fig_silhouette.png`, `fig_site_map_clusters.png` |
| `pipeline.py` | `pipeline_now.csv`, `fig_now_ladder.png` |
| `bakeoff_now.py` | `bakeoff_now.csv`, `fig_bakeoff_now.png` |
| `fetch_external.py` | `external_features.csv`, cache `_osm_roads.json` if present |
| `eval_external.py` | `eval_external.csv`, `fig_external.png` |
| `fetch_buildings.py` | cache `_osm_buildings.json` if present |
| `eval_buildings.py` | `building_features.csv`; may update improvement summaries |
| `bakeoff_future.py` | `bakeoff_future.csv`, `fig_bakeoff_future.png` |
| `lstm_future.py` | `models/lstm_future.pt`, updates `bakeoff_future.csv`, `fig_bakeoff_future.png` |
| `improve_future_lstm.py` | `lstm_preds_base.csv` |
| `improve_future_gbm.py` | `gbm_preds.csv` |
| `improve_future_ensemble.py` | `improve_future.csv` |
| `improve_conformal.py` | `improve_conformal.csv` |
| `band_now.py` | `band_summary.csv`, `fig_safety_confusion_matrix.png` in newer scripts |
| `band_future.py` | `band_future.csv` |
| `band_now_recall.py` | `band_now_recall_tradeoff.csv`, recall figure |
| `investigate_categorization.py` | `categorization_investigation.json` |
| `improve_blind_cat.py` | `improve_blind_cat.json` |
| `fig_investigation.py` | `fig_blindcat_investigation.png` |
| `fetch_basemap.py` | `basemap_kampala.png`, `basemap_meta.json` |
| `predict_map.py` | `map_predictions.json`, `test_cases.json` |
| `export_ref.py` | `ref_sites.json` |
| `predict_testcases.py` | updates `test_cases.json` |
| `new_site_predict.py` | `newsite_demo.csv/png`, `newsite_demo_hi.csv/png` |
| `finalize_now.py` | `models/now_rf_cat.joblib`, `models/now_xgb_cat_ext.joblib`, `FINDINGS_summary.csv` |
| `improve_honest_now.py` | `now_improvement_experiments.csv`, `safety_improvement_experiments.csv`, `danger_threshold_sweep.csv`, `uncertainty_calibration.csv`, multiple figures |
| `diagnose_k6_deployability.py` | `k4_k6_cluster_comparison.md`, `k4_k6_site_assignment_diff.csv`, `window_length_sensitivity.csv`, `deployable_category_improvement.csv`, `category_assignment_error_analysis.md`, figures |
| `future_same_row_benchmark.py` | `future_same_row_benchmark.csv`, `fig_future_same_row_benchmark.png` |
| `build_home.py` | `index.html`, `pages/FINDINGS.html`, `pages/FINAL_REPORT.html`, `pages/DECISION_LOG.html` |
| `build_4th.py` | `pages/index_consolidated.html` by default |
| `build_session.py` | `pages/index_session.html` |
| `build_forecast.py` | `pages/index_forecast.html` |
| `build_predictor.py` | `pages/index_predictor.html` |
| `build_prototype.py` | `pages/kampala_planner_prototype.html` |
| `build_deck_4th.py` | `docs/capstone_presentation.pptx` by default unless `DECK_OUT` is set; current repo has `capstone_presentation_v2.*` |

### Orphan, Unused, Duplicate, and Stale Files

| item | issue | recommendation |
|---|---|---|
| `README.md` | Minimal/unknown usage. | Either remove or replace with `README.txt`/`docs/CONTEXT.md` summary. |
| `pages/capstone_pyramid.html` | Static wrapper, not regenerated in latest build pass; source builder not identified. | Keep if intentional, but document it as static wrapper. |
| `docs/capstone_presentation_v2.pptx/pdf` | Deck text does not include the final 2026-06-10 k=6/RF audit guardrail. | Update/rebuild before defense. |
| `docs/FINAL_REPORT.md` | Strong main report but does not fully incorporate final honest improvement audit wording. | Add final audit appendix/section or point professor to `FINDINGS.md`. |
| `analysis/improve_now.py` vs `improve_honest_now.py` | Duplicate/superseded NOW improvement layers. | Mark older script as Round-2 historical. |
| `analysis/improve_future_*.py`, `improve_honest_future.py`, `future_same_row_benchmark.py` | Multiple future benchmark generations. | Treat `future_same_row_benchmark.csv` as latest fair comparison; preserve older as provenance. |
| `analysis/results/improve_summary.csv`, `FINDINGS_summary.csv`, `final_model_decision_table.csv` | Overlapping summary tables with different vintages. | Use `final_model_decision_table.csv` for defense; cite older summaries only for chronology. |
| `analysis/results/uncertainty_calibration.csv` vs `improve_conformal.csv` | Two conformal result sources with different configurations. | Clarify which is final. Current `uncertainty_calibration.csv` includes k=6 window60 NOW, while report discusses k=4/group conformal 85.8%. |
| `analysis/results/.wtest` | Unknown generated/test file. | Inspect/remove if not needed. |
| generated HTML embeds all CSV/scripts | Huge self-contained pages may include stale/diagnostic data even if stage copy is updated. | Defense should focus visible claims, not every embedded CSV payload. |

---

## SECTION 2 - RESEARCH QUESTION CONSISTENCY

### Actual Research Question

Best consolidated research question:

> Can a categorize-then-predict pipeline give a Kampala planner trustworthy PM2.5 where there is no sensor, and a few days ahead, without leakage, and can the output be framed as an actionable safety tier?

Evidence:

- `index.html` lead: asks whether free data can give PM2.5 where there is no sensor and a few days ahead, graded by EPA safety tier.
- `docs/FINAL_REPORT.md`: same two-part NOW/FUTURE framing.
- `docs/FINDINGS.md`: same framing, now with final audit note.
- PPTX slide 1: same question; slide 4 separates NOW and FUTURE.
- `analysis/pipeline.py`: explicitly asks whether categorize-then-predict beats blind pooled model at unseen site.
- `analysis/bakeoff_future.py` / `lstm_future.py`: asks whether real forecaster beats persistence.

### Consistency Check

| artifact | question stated | consistent? | issue |
|---|---|---:|---|
| `docs/FINAL_REPORT.md` | PM2.5 where no sensor + few days ahead; safety tier refinement | Mostly | Does not fully reflect final k=6 audit/reject wording. |
| `docs/FINDINGS.md` | Same, plus final honest audit | Yes | Best current narrative source. |
| `docs/CONTEXT.md` | Folder map plus final audit note | Yes | Good handover source. |
| `docs/DECISION_LOG.md` | Chronological experiment log | Yes but verbose | Contains superseded stages; must be read as history. |
| PPTX | Same main question | Partly stale | Missing final “do not replace with k=6 / RF challenger only” audit. |
| `index.html` | Same, with audit note | Yes | Current browser entry point. |
| `pages/index_*.html` | Same, with audit guardrails | Yes after latest rebuild | Generated pages now include final audit stages. |

### Contradiction Flags

| topic | conflict | current defensible interpretation |
|---|---|---|
| PM2.5 estimation vs forecasting | Some documents say “tool” broadly, but protocols differ. | NOW is new-site nowcast; FUTURE is known-site chronological forecast. Never combine their metrics. |
| New-site vs known-site | NOW hides whole sites; FUTURE forecasts known sites with history. | This distinction is correctly stated in report/deck, but must be repeated in defense. |
| Safety tiers vs regression | Report says R2 around 0.56 and safety exact 68%. | Both are valid but answer different decision layers; safety tier is the planner-facing metric. |
| LST contribution | LST is carried but inert/demoted; some older strategy may mention it as a lever. | Final claim: LST is not a useful adopted predictor. |
| Geodata contribution | Geodata helps regression but cannot recover category. | Correct final claim: zero-deploy complement, not replacement for PM2.5-derived category. |
| k=3 vs k=4 vs k=6 | Report still explains k=3 original and k=4 refinement; final audit adds k=6 as fragile. | Final accepted: k=4. k=6 is research/upper-bound only. |
| RF vs LSTM | Older deck says LSTM beats GBMs at every horizon; newer same-row says RF/rolling-7 beat or tie at some horizons. | Final accepted: LSTM headline, RF/rolling-7 challengers only; do not claim LSTM dominates every possible same-row challenger. |

---

## SECTION 3 - MODEL CLAIM AUDIT

| model / method | purpose | inputs | outputs | validation | deployability | trained/evaluated in | reported in | audit verdict |
|---|---|---|---|---|---|---|---|---|
| k=4 categorization | Accepted NOW/safety category setting | Site behavioral signature; deploy setting depends on category source | Site category feature | Leave-site-out NOW, fold-safe variants | Short deploy if category uses PM2.5 history; research/diagnostic if full history | `improve_now_sweep.py`, `improve_honest_now.py`, `diagnose_k6_deployability.py` | report, findings, HTML, decision table | Supported as accepted baseline/reference, but exact 0.564 is a reference row in latest k=6 diagnostic, not rerun there. |
| k=6 categorization | Diagnostic finer regime split | PM2.5 behavior + climate; window/geodata alternatives | Category or soft/distance features | Leave-site-out | Full-history is non-deployable; window is short-deploy; geodata is zero-deploy | `diagnose_k6_deployability.py`, `improve_honest_now.py` | final audit files, HTML guardrails | Meaningful but fragile. Do not promote. |
| XGBoost NOW | Original/locked learner in ladder | BASE_NOW + category/prior variants | PM2.5 nowcast | Random diagnostic; GroupKFold leave-site-out; leave-category-out | Depends on features/category source | `pipeline.py`, `bakeoff_now.py` | report, findings, CSVs | Used and supported. Not final best learner but part of evidence. |
| RandomForest NOW | NOW bakeoff winner at fixed +cat features | BASE_NOW + category | PM2.5 nowcast | GroupKFold leave-site-out | Short deploy/category-dependent | `bakeoff_now.py`, `finalize_now.py` | report, findings | Supported: 0.529 in `bakeoff_now.csv`. Not the same as final k=4 safety reference. |
| LightGBM NOW | NOW bakeoff and conformal intervals | BASE_NOW + category | PM2.5 + intervals | GroupKFold, split conformal | Short deploy/category-dependent | `bakeoff_now.py`, `improve_conformal.py` | report/findings | Supported; uncertainty claims need source disambiguation. |
| CatBoost NOW | Bakeoff comparator | One-hot category, not native categorical handling | PM2.5 nowcast | GroupKFold | Short deploy/category-dependent | `bakeoff_now.py` | report/findings | Discussed and actually used. |
| LSTM FUTURE | Headline forecaster | PM2.5 lag/rolling history + category embedding | +1..+7 PM2.5 | Chronological split; horizon-purged claims in docs | Deployable for known sites with PM2.5 history | `lstm_future.py`, `improve_future_lstm.py` | report, findings, deck, decision table | Supported as headline, but newer same-row benchmark narrows claim: not always best at +3/+7 vs RF/roll7. |
| Persistence current | Baseline for FUTURE | Current PM2.5 | Future PM2.5 | Chronological | Known-site only | `bakeoff_future.py`, `future_same_row_benchmark.py` | report/findings | Supported. |
| Persistence rolling-7 | Challenger baseline | Recent PM2.5 rolling mean | Future PM2.5 | Same-row chronological | Known-site only | `future_same_row_benchmark.py` | final audit | Supported as challenger; not a model replacement. |
| Mixture of experts (MOE) | Alternative routing | Category-specific XGBoost experts | PM2.5 nowcast | Random, leave-site-out, leave-category-out | Short-deploy if category known; fragile | `pipeline.py` | report/findings | Used; killed because window category misrouting collapses. |
| Safety-tier model/framing | Planner-facing decision layer | Regression outputs mapped to EPA tiers; alert threshold | tier, dangerous alert | Same leave-site-out/chronological predictions | Deployable when underlying model deployable | `band_now.py`, `band_future.py`, `band_now_recall.py`, `improve_honest_now.py` | report/findings/deck | Supported as framing. It is not necessarily a separate classifier; mostly thresholded regression. |

### Models Discussed but Not Actually Used or Not Fully Available

- XGBoost in latest FUTURE same-row benchmark: explicitly marked not run because no per-row XGBoost predictions and package unavailable in that specific runnable environment. Note: `analysis/requirements.txt` includes xgboost, so this is an environment/output gap, not necessarily a package impossibility.
- Dedicated class-weighted dangerous-day classifier: mentioned as not beating thresholding, but I did not find a standalone clearly named classifier output. Likely embedded in `improve_honest_now.py`; should be cited carefully.
- “Production pipeline” is a phrase, but there is no production service/API. The production artifact is a research/demo pipeline plus generated HTML/prototype.

---

## SECTION 4 - METRIC CONSISTENCY AUDIT

### Core Reported Metrics

| metric / claim | value | task | protocol | source evidence | status |
|---|---:|---|---|---|---|
| leaky random split blind/+cat | ~0.808 | NOW diagnostic | random 80/20 | `pipeline_now.csv` | Safe if labeled leaky. |
| blind pooled new-site R2 | 0.3159 | NOW | GroupKFold leave-site-out | `pipeline_now.csv`, `bakeoff_now.csv`, `eval_external.csv` | Consistent. |
| +category k=3 full signature R2 | 0.4815/0.482 | NOW | leave-site-out | `pipeline_now.csv`, `bakeoff_now.csv` | Consistent rounding. |
| +category 60d window R2 | 0.433 | NOW | leave-site-out post-window | `pipeline_now.csv`, `FINDINGS_summary.csv` | Consistent. |
| MOE 60d R2 | 0.298 | NOW | leave-site-out post-window | `pipeline_now.csv`, `FINDINGS_summary.csv` | Consistent. |
| +external geodata R2 | 0.4207 | NOW | leave-site-out | `eval_external.csv` | Consistent. |
| +cat+external k=3 R2 | 0.5474 | NOW | leave-site-out | `eval_external.csv` | Consistent with report 0.547. |
| k=4 +cat deploy-only R2 | 0.5575/0.558 | NOW | leave-site-out | `improve_now_sweep.csv`, report | Consistent rounding. |
| k=4 +cat+external R2 | 0.5551 sweep; 0.564 accepted reference | NOW | leave-site-out | `improve_now_sweep.csv`, `final_model_decision_table.csv` | Needs explanation: 0.564 is accepted reference from later/broader configuration; 0.555 is sweep output. |
| k=6 +cat+external full-history R2 | 0.5851 sweep | NOW | leave-site-out with full-history category | `improve_now_sweep.csv` | Non-deployable/fragile; should not be headline. |
| k=6 full-history focused diagnosis R2 | 0.5575 | NOW | leave-site-out, HGB config | `deployable_category_improvement.csv` | Different model/config from 0.580 broader audit; labeled upper bound. |
| k=6 best deployable 45d R2 | 0.5059 | NOW | leave-site-out post-window | `window_length_sensitivity.csv` | Supported. |
| k=6 60d window R2 | 0.4463 | NOW | leave-site-out post-window | `window_length_sensitivity.csv` | Supported. |
| NOW safety exact / within-one | 0.680 / 0.985 | Safety | leave-site-out | `band_summary.csv`, report/deck | Supported. |
| strict Dangerous recall | 0.51 | Safety | leave-site-out | `band_summary.csv`, `band_now_recall_tradeoff.csv` | Supported. |
| alert cutoff 45 recall/false alarm | report says 0.80/17%; newer `danger_threshold_sweep.csv` says 0.656/12.4% | Safety | leave-site-out | `band_now_recall_tradeoff.csv`, `danger_threshold_sweep.csv` | Conflict between old and newer threshold tables. Use `band_now_recall_tradeoff.csv` for report/deck claim; investigate before final defense. |
| LSTM +1/+3/+7 R2 | 0.506/0.477/0.432 | FUTURE | chronological | `bakeoff_future.csv` | Supported. |
| LSTM same-row +1/+3/+7 | 0.492/0.462/0.427 | FUTURE | identical rows benchmark | `future_same_row_benchmark.csv` | Supported; differs from bakeoff due identical-row alignment. |
| RF same-row +3/+7 | 0.467/0.445 | FUTURE | identical rows benchmark | `future_same_row_benchmark.csv` | Supported challenger. |
| rolling-7 same-row +7 | 0.449 | FUTURE | identical rows benchmark | `future_same_row_benchmark.csv` | Supported challenger. |
| conformal naive/group coverage | 79.8/85.8 in `improve_conformal.csv`; report mentions 74.8 -> 85.8 | NOW uncertainty | split/group conformal | `improve_conformal.csv`, `bakeoff_now.csv` likely older 74.8 | Mild mismatch; needs provenance note. |
| latest `uncertainty_calibration.csv` NOW coverage | 0.8819 width 44.8 | NOW uncertainty | group conformal, k=6 window60 HGB | `uncertainty_calibration.csv` | Newer but different config; do not mix with k=4 report claim. |

### Metric Conflict Summary

1. k=4 accepted R2 appears as 0.558, 0.563, 0.564 depending on exact feature set/fold-safe/reference. This is explainable but must be footnoted.
2. k=6 upper-bound appears as 0.585 in sweep, 0.580 in broader audit, 0.558 in focused diagnosis. This is not necessarily contradictory; it is model/config dependent. It is dangerous if quoted without source.
3. Danger threshold at 45 has conflicting recall/false-alarm numbers between `band_now_recall_tradeoff.csv` and `danger_threshold_sweep.csv`. This needs rerun or explanation before defense.
4. LSTM “beats every GBM at every horizon” is true for original GBM comparison, not for newer RF/rolling-7 challengers on same rows.

---

## SECTION 5 - LEAKAGE AUDIT

### Pipeline-Level Findings

| experiment/script | classification | leakage assessment |
|---|---|---|
| `features.py` BASE_NOW | Safe | Uses weather/location/calendar/row-local engineered weather. Explicitly bans `pm10`, `n_obs`. |
| `features.py` future lags | Safe if used as written | Calendar-aware lags and rolling means use past PM2.5 only; rolling uses `shift(1)`. |
| `features.py` full category assignment | Questionable / non-deployable for held-out new site | Uses full PM2.5 behavior of site. Good for upper bound or “known category” scenario, not deployable at a new site. |
| `features.py` 60d window assignment | Safe short-deploy if eval rows after window are dropped | `pipeline.py` and `diagnose_k6_deployability.py` drop warm-up rows. |
| `pipeline.py` random rung | Leaky by design | Random row split mixes same sites; correctly labeled leaky/diagnostic. |
| `pipeline.py` leave-site full-signature category | Questionable | New-site target history used to assign category. It is labeled Tier A/static known/optimistic. |
| `pipeline.py` leave-site 60d category | Safe short-deploy | Uses first 60 observed days and evaluates after cutoff. |
| `pipeline.py` leave-category-out | Safe but harsh | Tests unseen category extrapolation. |
| `add_category_priors` | Safe if called inside fold | Fits category-month priors on train and uses leave-one-site-out for train rows. |
| `bakeoff_now.py` | Mostly safe / category-dependent | Uses locked +cat routing. Need remember category source is from categorizer/full assignment unless fold-specific rerun. |
| `eval_external.py` | Mostly safe | Evaluates geodata as static zero-deploy and category+geodata. Need inspect exact category source before production claim. |
| `improve_now_sweep.py` | Mixed | k sweep includes full-site signatures; reports fold-safe k=4 elsewhere. k=6 high score is fragile and should be non-production. |
| `improve_honest_now.py` | Safe/Questionable depending `category_mode` | Labels `full_history` diagnostic; `window60` short deploy; `geodata` zero deploy. Fold categories fitted on train sites only. |
| `diagnose_k6_deployability.py` | Safe if labels honored | Explicitly labels `full_history` as non-deployable upper bound; window/geodata modes avoid future PM2.5 after warm-up. |
| `bakeoff_future.py` | Safe if target purging is correct | Chronological split; docs claim horizon-purged. Needs code-level check of target date boundaries beyond this audit. |
| `future_same_row_benchmark.py` | Safe | Aligns per-row predictions on `(site_id,target_day,h)`; RF train mask requires target date <= cut and test origin > cut. |
| `new_site_predict.py` | Safe for demo if leave-one-site-out path is used | Demo holds a site out. Live use still requires ERA5/geodata availability and no hidden use of actual PM2.5 except optional deploy. |
| `predict_map.py` | Questionable for real zero-deploy map | Uses observed categories for instrumented areas and predictions over existing sensors; acceptable as deployed sensor-network map, not pure never-seen-site map. |

### Specific Leakage Types

- Future leakage: mostly controlled in lag builders and future benchmark. Highest risk is older scripts not inspected line-by-line; final FUTURE claims should cite `future_same_row_benchmark.py`.
- Site leakage: random split is leaky; full-history category is non-deployable; both are mostly labeled.
- Target leakage: `pm10` and `n_obs` are explicitly banned; category signatures include PM2.5 and are only safe for short/full deploy contexts.
- Normalization leakage: original `site_categorize.py` fits scaler on all sites for the portable categorizer. Later fold-safe variants fit scaler/centroids on train sites. Defense should cite fold-safe result for leak resistance.
- Category prior leakage: `add_category_priors` appears carefully fold-safe; prior was killed anyway.
- Full-history leakage: the main live risk. Any claim using k=6 full-history or full-signature held-out category must be labeled oracle/upper-bound/non-deployable.

---

## SECTION 6 - DEPLOYABILITY AUDIT

| feature/model ingredient | deployability | rationale |
|---|---|---|
| latitude, longitude | Zero deploy | Available for any address. |
| date/month/day-of-week | Zero deploy | Known at prediction time. |
| ERA5 weather same-day or forecast weather | Zero deploy if accessible | Free external weather; operational pipeline needs API/data source. |
| relative humidity, wind speed | Zero deploy | Derived from weather row. |
| OSM road density / distance to major road | Zero deploy | Free static geodata; requires Overpass/cache. |
| SRTM elevation | Zero deploy | Free static geodata; requires source/cache. |
| OSM building density | Zero deploy | Free static geodata; tested as minor/negative. |
| LST | Zero deploy in principle, deprecated | Present but inert/cloud-gapped; not adopted. |
| PM2.5 lag/rolling history | Full/known-site deploy | Requires sensor history at site. |
| first N days PM2.5 | Short deploy | Requires temporary sensor; safe if predicting after window. |
| full-history PM2.5 category | Research only / non-deployable upper bound | Not available at a new site. |
| site category from first N days | Short deploy | Deployable after temporary observation window. |
| site category from geodata | Zero deploy weak prior | Does not reliably recover behavior; can be used cautiously. |
| k=4 NOW accepted | Short deploy / accepted reference | Category needs observed behavior unless using geodata-only/no-category variant. |
| geodata-only NOW | Zero deploy | Lower score but deployable at never-instrumented site. |
| k=6 full-history | Research only | Oracle-like. |
| k=6 30/45d window | Short deploy challenger | Does not beat k=4. |
| LSTM FUTURE | Known-site/full deploy | Requires past PM2.5 sequence. |
| RF/rolling-7 FUTURE | Known-site/full deploy | Requires PM2.5 history. |
| safety-tier output | Same as underlying model | Tiering itself is deployable; inputs determine deployability. |

Presentation consistency: root HTML, FINDINGS, and pyramid pages now correctly state final deployability boundaries. PPTX does not yet state the final k=6/RF warning, so it is presentation-stale.

---

## SECTION 7 - HTML / REPORT CONSISTENCY

| artifact | consistency status | findings |
|---|---|---|
| `docs/FINDINGS.md` | Current | Contains final honest improvement audit and “what not to claim.” |
| `pages/FINDINGS.html` | Current generated | Built from `docs/FINDINGS.md`; contains final audit section. |
| `docs/CONTEXT.md` | Current | Notes final audit scripts and recommendation to keep k=4/LSTM. |
| `docs/FINAL_REPORT.md` | Mostly stale | Strong main report, but conclusion/next steps predate final audit. It says k=6 has headroom and next includes deploy-window sensitivity, which has now been done. |
| `pages/FINAL_REPORT.html` | Mostly stale generated | Mirrors `FINAL_REPORT.md`; regenerated but source narrative remains older. |
| `docs/DECISION_LOG.md` | Historical/current | Useful but not concise; includes older claims and needs chronological interpretation. |
| `pages/DECISION_LOG.html` | Historical/current | Generated from decision log. |
| `analysis/results/professor_summary.md` | Current | Concise final audit summary. |
| `analysis/results/presentation_talking_points.md` | Current | Includes “we did not replace model just because one score looked better.” |
| `index.html` | Current | Contains final audit note. |
| `pages/index_consolidated.html` | Current | Contains final audit guardrail stage. |
| `pages/index_session.html` | Current | Contains final audit stage. |
| `pages/index_forecast.html` | Current | Contains final audit guardrail. |
| `pages/index_predictor.html` | Current | Contains final audit guardrail. |
| `pages/kampala_planner_prototype.html` | Current | Contains final audit guardrail note. |
| `pages/capstone_pyramid.html` | Neutral | Static iframe switcher; no audit content itself. Loaded pages contain audit. |
| PPTX | Stale | Extracted text lacks final k=6 non-deployable / RF challenger-only warning. |
| PDF | Unverified | `pdftotext` unavailable; likely mirrors stale PPTX but not proven. |

### Mismatches to Fix Before Defense

1. Update `docs/FINAL_REPORT.md` with final honest audit section.
2. Update/rebuild `docs/capstone_presentation_v2.pptx/pdf` with final “what not to claim” slide or speaker note.
3. Resolve danger-threshold metric mismatch between `band_now_recall_tradeoff.csv` and `danger_threshold_sweep.csv`.
4. Clarify conformal numbers and configurations: 74.8/79.8/85.8/88.2 appear in different files/configs.

---

## SECTION 8 - REPRODUCIBILITY AUDIT

### Clean Checkout Reproduction Feasibility

Likely reproducible with caveats. The repo includes:

- Single working data file.
- Pinned `analysis/requirements.txt`.
- Most scripts are path-relative and seed-controlled.
- Generated outputs are already present.
- Build scripts are path-relative and can rebuild HTML.

### Missing / Risky Dependencies

| item | risk |
|---|---|
| Python environment | `requirements.txt` is pinned but not a lockfile with platform markers. Torch 2.8.0, xgboost, lightgbm, catboost may be platform-sensitive. |
| Network sources | `fetch_external.py`, `fetch_buildings.py`, `fetch_basemap.py` need external APIs unless caches exist. Caches `_osm_roads.json` / `_osm_buildings.json` are not listed in current file inventory, so full regeneration may require network. |
| PDF verification | No `pdftotext` locally. |
| PPTX build | `build_deck_4th.py` writes `capstone_presentation.pptx` unless `DECK_OUT` set; current file is `capstone_presentation_v2.pptx`. |
| XGBoost same-row FUTURE | `future_same_row_benchmark.py` explicitly says XGBoost not included due missing per-row predictions/package unavailable. |
| Raw/quarantined data | `docs/CONTEXT.md` says raw source data and superseded artifacts were moved to `../../trash/...`; clean checkout may not include them. Main analysis does not need raw files, but provenance may. |
| Model binaries | Present but not verified by loading/predicting in this audit. |

### Reproduction Confidence by Component

| component | confidence | rationale |
|---|---:|---|
| Main CSV/figure regeneration from existing data | 75% | Scripts and requirements present; network/caches and heavy ML dependencies are the main risk. |
| NOW core pipeline | 85% | Central scripts are clear and path-relative. |
| FUTURE LSTM | 65% | Torch/OpenMP process isolation noted; binary reproducibility may vary. |
| External geodata regeneration | 45% | Depends on online APIs and possible caches not present. |
| HTML rebuild | 90% | Build scripts recently ran successfully. |
| Deck rebuild | 55% | Source exists but output naming/versioning is inconsistent and deck stale. |
| Exact metric reproduction | 70% | Fixed seeds help; library versions and environment may alter RF/GBM slightly. |

Overall exact reproduction confidence: 72/100.

---

## SECTION 9 - DEFENSE PREPARATION

| # | professor question | answer | evidence source | confidence |
|---:|---|---|---|---:|
| 1 | What is the actual research question? | Whether categorize-then-predict can give trustworthy PM2.5 at sensor-less Kampala locations and forecast a few days ahead, evaluated honestly and framed as safety tiers. | `index.html`, `FINAL_REPORT.md`, PPTX slide 1, `pipeline.py` | High |
| 2 | Why not trust the 0.81 R2? | It is a random row split that sees the same sensors in train/test; new-site GroupKFold drops to 0.316. | `pipeline_now.csv` | High |
| 3 | What is the accepted NOW model? | k=4 categorize-then-predict/safety reference, with k=4 retained over k=6 because deployable k=6 does not beat it. | `final_model_decision_table.csv`, `deployable_category_improvement.csv` | High |
| 4 | Is k=6 better? | Only as a full-history upper bound or fragile diagnostic. Deployable 45d k=6 reaches ~0.506, below k=4 reference. | `window_length_sensitivity.csv`, `k4_k6_cluster_comparison.md` | High |
| 5 | Why is k=6 fragile? | It creates tiny groups, including 1-3 site regimes, so full-history labels capture mature site behavior that early deploy cannot reliably infer. | `k4_k6_site_assignment_diff.csv`, `k4_k6_cluster_comparison.md` | High |
| 6 | What prevents category leakage? | Fold-safe versions fit scaler/centroids on train sites; window versions use only first N days and evaluate after the window. | `features.py`, `diagnose_k6_deployability.py`, `improve_honest_now.py` | High |
| 7 | Is full-history category deployable? | No. It uses the held-out site’s complete PM2.5 history and must be labeled oracle/non-deployable. | `deployable_category_improvement.csv` | High |
| 8 | What features are zero-deploy? | Lat/lon, date/calendar, ERA5 weather, OSM roads, SRTM elevation, building features. | `features.py`, `fetch_external.py`, `eval_external.csv` | High |
| 9 | What requires short deploy? | PM2.5-derived site category from first N observed days. | `features.py`, `pipeline.py` | High |
| 10 | Why safety tiers? | Planner decisions need Elevated/High/Dangerous; regression misses inside the same band are less operationally harmful. | `band_summary.csv`, report | High |
| 11 | What is the safety performance? | NOW exact tier 0.680, within-one 0.985; strict dangerous recall 0.51. | `band_summary.csv` | High |
| 12 | Can you claim 80% dangerous recall? | Yes only if citing `band_now_recall_tradeoff.csv` at cutoff 45; note newer `danger_threshold_sweep.csv` conflicts and should be reconciled. | two threshold CSVs | Medium |
| 13 | Does RF beat LSTM? | Not overall. RF/rolling-7 are strong challengers and win/tie at some horizons on identical rows, but LSTM remains headline. | `future_same_row_benchmark.csv`, `final_model_decision_table.csv` | High |
| 14 | Why is LSTM deployable only for known sites? | It needs PM2.5 lag/rolling history. It is not a zero-deploy new-address model. | `features.py`, `lstm_future.py` | High |
| 15 | What did geodata add? | Geodata alone raises new-site R2 to 0.421; combined with category gives 0.547 in original external evaluation. | `eval_external.csv` | High |
| 16 | Can geodata infer category? | No, RF leave-one-out category accuracy 0.538 is below majority 0.615 in `eval_external.csv`. | `eval_external.csv` | High |
| 17 | What did not work? | MOE, category prior under noise, geodata category inference, building density as major lift, bigger/ensemble forecaster. | `pipeline_now.csv`, report, improvement CSVs | Medium-high |
| 18 | Is LST useful? | No. It is carried/demoted as inert/cloud-gapped and not adopted. | report, `features.py` LST not in `BASE_NOW` | Medium |
| 19 | Can a clean checkout reproduce everything? | Mostly, but network geodata, heavy ML versions, PPTX/PDF generation, and raw provenance are gaps. | `requirements.txt`, `CONTEXT.md` | Medium |
| 20 | What is the strongest contribution? | Honest separation of NOW new-site and FUTURE forecasting, with deployability-labeled categorization and safety-tier framing. | code + results + docs | High |

---

## SECTION 10 - FINAL VERDICT

### A. What Is Unquestionably Correct

- The repo has one main data table and a coherent analysis/build structure.
- Random split is leaky/diagnostic and new-site evaluation is the honest NOW protocol.
- `pm10` and `n_obs` are explicitly banned in feature code.
- Categorization improves over blind new-site baseline in core outputs.
- Geodata adds zero-deploy signal but does not reliably infer category.
- MOE collapses under realistic cold-start.
- k=6 full-history must not be claimed as deployable.
- FUTURE same-row benchmark supports RF/rolling-7 as challengers, not clean headline replacements.
- Generated HTML now contains final audit guardrails in the main browser-facing pages.

### B. What Is Likely Correct but Should Be Verified

- Exact k=4 accepted 0.564 reference should be traced to the specific run/config, not only reference rows.
- Full LSTM reproducibility under pinned environment should be rerun on a clean machine.
- Conformal coverage lineage should be clarified across 74.8, 79.8, 85.8, and 88.2.
- Danger threshold recall/false alarm should be rerun and a single final table chosen.
- Binary model artifacts should be load-tested.

### C. What Is Unsupported or Under-Supported

- Any claim that k=6 should replace k=4.
- Any claim RF beats LSTM overall.
- Any claim full-history category assignment is deployable at a new site.
- Any claim random split performance represents real-world performance.
- Any claim the PDF deck is current; PDF text was not extracted in this audit.

### D. What Is Outdated

- `docs/FINAL_REPORT.md` next-step language about deploy-window sensitivity is outdated because that sensitivity has been run.
- PPTX/PDF deck lacks final k=6/RF audit guardrails.
- README finalized date 2026-06-07 predates the 2026-06-10 improvement audit.
- Some Round-2 improvement summaries are superseded by final decision table and k=6 diagnosis.

### E. What Should Be Removed or Quarantined

- Do not delete immediately. First mark superseded artifacts:
  - Older `improve_now.py` outputs if `improve_honest_now.py` is final.
  - Older `improve_future.csv` if `future_same_row_benchmark.csv` is final.
  - Unknown `analysis/results/.wtest`.
  - Minimal `README.md`.
- Keep historical logs but clearly label them as provenance, not final claims.

### F. Strongest Contribution to Highlight

The strongest contribution is not a single model. It is the research-integrity architecture:

1. Separate NOW new-site prediction from FUTURE known-site forecasting.
2. Evaluate each under the correct honest protocol.
3. Label deployability of every category source.
4. Convert regression into safety-tier decisions for planners.
5. Refuse to replace the accepted model when a stronger-looking score is non-deployable.

### G. Overall Project Health Score

78/100. Strong evidence base and deliverables, but messy research residue and stale deck/report sections.

### H. Research Integrity Score

86/100. The repo repeatedly labels leakage, diagnostic upper bounds, and negative results. Deductions for metric lineage ambiguity and stale narrative artifacts.

### I. Deployment Readiness Score

55/100. Good prototype and deployability reasoning, but no production API, no automated tests, network dependencies, and short-deploy/full-deploy distinctions must be operationalized.

### J. Presentation Readiness Score

72/100. Browser pages and summaries are much improved; deck/report still need final audit guardrail updates before professor defense.

## Final Recommendation

Do not replace the pipeline. Defend the project as a rigorous, honest capstone result:

- Accepted NOW/safety: k=4.
- Accepted FUTURE headline: LSTM.
- k=6: meaningful research direction, non-deployable upper-bound when full-history is used, not production.
- RF/rolling-7: formal challengers for future benchmark, not headline replacements.
- Safety-tier framing: strong and professor-friendly, but reconcile the danger-threshold tables before relying on a single recall/false-alarm number.
