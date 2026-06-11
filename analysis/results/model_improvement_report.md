# Model Improvement Report

Generated: 2026-06-10

## Final Honest Improvement Audit

The audit is now a research result, not a production rewrite. The final decision is to **keep the accepted
k=4 NOW pipeline and LSTM FUTURE forecaster**.

The reason is methodological: the strongest-looking k=6 result is a non-deployable upper bound because it
uses full held-out PM2.5 history to assign the category. Under deployable information, k=6 improves with
30-45 early days but still does not beat the accepted k=4 baseline. For FUTURE, RandomForest and rolling-7
persistence are strong same-row challengers, but they do not justify replacing the LSTM headline overall.

The concise decision record is `final_model_decision_table.csv`. Professor-facing and presentation-facing
summaries are `professor_summary.md` and `presentation_talking_points.md`.

### What Not To Claim

- Do not claim k=6 is the new production model.
- Do not claim RF beats LSTM overall.
- Do not claim random split performance as real-world performance.
- Do not claim full-history category assignment is deployable at a new site.

## Scope

This pass added two reproducible experiment scripts:

- `analysis/improve_honest_now.py`
- `analysis/improve_honest_future.py`

The scripts preserve the project's honest validation rules:

- NOW uses leave-whole-sites-out GroupKFold only.
- FUTURE uses a blocked chronological split with horizon purging.
- `pm10` and `n_obs` remain banned.
- Category priors / category fitting are kept inside folds where relevant.

The local environment did not have XGBoost/LightGBM/CatBoost available in the runnable Python stack, so the new experiments use scikit-learn RandomForest and HistGradientBoosting variants. Existing XGBoost/LightGBM/CatBoost baselines remain recorded in the committed result CSVs.

## Previous baseline

See `performance_baseline.md`.

Key pre-pass baselines:

- NOW recommended: `+cat+external` k=4 around R2 0.56, with stacked k=4 at 0.564.
- NOW diagnostic high score: k=6 at 0.585, but previously marked fragile due to singleton cluster.
- NOW safety: exact tier 0.680, within-one-tier 0.985, Dangerous recall 0.51.
- FUTURE recommended: locked LSTM, R2 +1=0.506, +3=0.477, +7=0.432.
- Uncertainty: group conformal about 85.8% coverage with width about 43 ug/m3.

## NOW experiments

Output: `now_improvement_experiments.csv`

Tested:

- k=3, k=4, k=5, k=6 site categories.
- Category source:
  - `full_history`: diagnostic only; uses the held-out site's full PM2.5 history.
  - `window60`: short-deploy; uses first 60 observed PM2.5 days and evaluates post-window rows.
  - `geodata`: zero-deploy; predicts category from static external features.
- Feature families:
  - base category features.
  - cyclic calendar and weather features.
  - road/elevation external geodata.
  - interaction features.
  - building-density features.
- Models:
  - RandomForest.
  - HistGradientBoosting.

Best diagnostic/non-deployable result:

| k | Category mode | Features | Model | R2 | RMSE | MAE | Exact tier | Within-one | Dangerous recall |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 6 | full_history | external_interactions | RandomForest | 0.580 | 14.18 | 10.50 | 0.733 | 0.987 | 0.542 |

This confirms that finer categories can help when the site's full pollution regime is known, but it is not deployable for a new sensor-less site.

Best deployable short-deploy result:

| k | Category mode | Features | Model | R2 | RMSE | MAE | Exact tier | Within-one | Dangerous recall |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 6 | window60 | base_cat | HistGradientBoosting | 0.473 | 15.96 | 11.54 | 0.681 | 0.983 | 0.342 |

Best zero-deploy result:

| k | Category mode | Features | Model | R2 | RMSE | MAE | Exact tier | Within-one | Dangerous recall |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 4 | geodata | external | HistGradientBoosting | 0.446 | 16.27 | 12.26 | 0.636 | 0.979 | 0.318 |

## NOW recommendation

Do not replace the existing recommended k=4 global pipeline with k=6 globally.

Reason:

- k=6 is strongest only when full held-out PM2.5 history is available, which is diagnostic/non-deployable.
- The best deployable short-deploy result from this pass is R2 0.473, below the existing accepted k=4 baseline around 0.56.
- The best zero-deploy result is useful but also below the existing accepted `+cat+external` result.
- Building-density features and interaction features did not produce an accepted deployable improvement.

Accepted conclusion:

- Keep the current k=4 recommendation for the finalized deliverable.
- Keep k=6 as a research lead only, not the production setting.
- If more sites are added, re-test k=5/k=6 because the current fragility may disappear with more training examples.

## Safety-tier experiments

Outputs:

- `safety_improvement_experiments.csv`
- `danger_threshold_sweep.csv`
- `fig_safety_confusion_matrix.png`
- `fig_danger_recall_precision.png`

The best deployable regression-to-tier model is the same k=6/window60/base_cat HistGradientBoosting model:

- Exact tier: 0.681
- Within-one tier: 0.983
- Dangerous precision: 0.749
- Dangerous recall at strict tier threshold: 0.342

Threshold sweep for the deployable model:

| Alert threshold | Dangerous precision | Dangerous recall | False-alarm rate |
|---:|---:|---:|---:|
| 40.0 | 0.405 | 0.791 | 0.231 |
| 42.5 | 0.463 | 0.724 | 0.168 |
| 45.0 | 0.512 | 0.656 | 0.124 |
| 50.0 | 0.612 | 0.482 | 0.061 |
| 55.0 | 0.731 | 0.347 | 0.025 |

Recommendation:

- Keep the existing safety-tier framing.
- Continue using a tunable Dangerous alert threshold.
- For the deployable model tested here, a 42.5-45 ug/m3 operating point is the practical range depending on tolerance for false alarms.
- The previous report's 45 ug/m3 threshold remains conceptually valid, but exact recall/FAR depends on the selected model.

## FUTURE experiments

Output: `future_improvement_experiments.csv`

Tested:

- More lags: lag1, lag2, lag3, lag4, lag5, lag6, lag7, lag14.
- Rolling mean/std/min/max windows.
- Trend features.
- Target-calendar features.
- Current weather features.
- Location/category features.
- Horizon-specific direct models.
- Persistence variants: yesterday/current, lag1, rolling-7, lag7.

Best new tabular results:

| Horizon | Best new method | Feature set | R2 | RMSE | MAE |
|---:|---|---|---:|---:|---:|
| +1 | RandomForest | rich_plus_current_weather | 0.475 | 11.30 | 8.49 |
| +2 | RandomForest | rich_plus_weather_loc_category | 0.467 | 11.28 | 8.67 |
| +3 | RandomForest | base_existing_plus_target_calendar | 0.476 | 11.23 | 8.64 |
| +5 | RandomForest | base_existing_plus_target_calendar | 0.434 | 11.93 | 8.94 |
| +7 | rolling-7 persistence | persistence | 0.450 | 11.89 | 8.76 |

Comparison to locked LSTM baseline:

- +1: LSTM 0.506 still wins over new tabular 0.475.
- +2: LSTM 0.474 is slightly above new tabular 0.467.
- +3: LSTM 0.477 and new tabular 0.476 are effectively tied.
- +5: new tabular 0.434 is slightly above LSTM 0.431, but this uses a different lag14-complete support.
- +7: rolling-7 persistence 0.450 is above LSTM 0.432 on the reduced lag14-complete support, so it is a candidate baseline to re-check on exactly the original LSTM evaluation support.

FUTURE recommendation:

- Do not replace the locked LSTM yet.
- Add rolling-7 persistence and the base RandomForest direct models as stronger challenger baselines in the next forecast bakeoff.
- Re-run the LSTM, rolling-7 persistence, and RandomForest on exactly the same chronological rows before changing the published FUTURE headline.

## Uncertainty intervals

Output: `uncertainty_calibration.csv`

| Task | Method | Target | Coverage | Width |
|---|---|---:|---:|---:|
| NOW | group conformal on calibration sites | 0.90 | 0.882 | 44.8 |
| FUTURE +1 | chronological split conformal | 0.90 | 0.880 | 33.6 |
| FUTURE +2 | chronological split conformal | 0.90 | 0.892 | 35.0 |
| FUTURE +3 | chronological split conformal | 0.90 | 0.906 | 36.9 |
| FUTURE +5 | chronological split conformal | 0.90 | 0.878 | 34.4 |
| FUTURE +7 | chronological split conformal | 0.90 | 0.867 | 34.9 |

Recommendation:

- Keep group conformal for NOW.
- Add chronological calibration reporting for FUTURE.
- Treat time-series conformal coverage as approximate because temporal dependence weakens exchangeability.

## What did not improve

- k=6 should not replace k=4 globally because the strongest result is non-deployable and the deployable scores do not beat the accepted k=4 baseline.
- External interaction features did not improve deployable NOW enough to accept.
- Building-density features did not improve deployable NOW enough to accept.
- Rich FUTURE lag/weather features did not clearly beat the LSTM on the original locked benchmark.
- Direct safety-tier replacement is not accepted here; regression-to-tier with threshold tuning remains the cleaner approach.

## Scripts to update if continuing

No finalized production scripts should be changed yet.

Candidate future updates:

- Add `persist_roll7` to `bakeoff_future.py` as a formal baseline.
- Add the direct RandomForest future challenger to `bakeoff_future.py`.
- Keep `improve_honest_now.py` and `improve_honest_future.py` as audit/experiment scripts.
- Re-run k=5/k=6 only if more sites are added or if singleton clusters disappear.

## Reproduce

Use the conda Python in this environment; the directory-local `python3` under `analysis/` resolved to a broken framework Python.

```bash
cd /Users/youssefahmed/Downloads/4th-cap-handover/analysis
/opt/anaconda3/bin/python3 improve_honest_now.py
/opt/anaconda3/bin/python3 improve_honest_future.py
```

Baseline tables:

```bash
cat results/performance_baseline.md
```

Primary outputs:

```bash
cat results/now_improvement_experiments.csv
cat results/future_improvement_experiments.csv
cat results/safety_improvement_experiments.csv
cat results/uncertainty_calibration.csv
```

## Leakage and overfitting risks

- `full_history` category rows are explicitly diagnostic and non-deployable.
- `window60` rows use PM2.5 history and are short-deploy, not zero-deploy.
- `geodata` rows are zero-deploy, but category guesses can be wrong and should not be treated as observed regimes.
- k=6 is fragile with 39 sites; do not promote it without more sites or stability checks.
- FUTURE comparisons must use the same row support before changing headline numbers.

---

# Continuation: k=6 Deployability Diagnosis

Generated: 2026-06-10

Additional scripts:

- `analysis/diagnose_k6_deployability.py`
- `analysis/future_same_row_benchmark.py`

Additional outputs:

- `k4_k6_cluster_comparison.md`
- `k4_k6_site_assignment_diff.csv`
- `window_length_sensitivity.csv`
- `fig_window_length_sensitivity.png`
- `category_assignment_error_analysis.md`
- `category_assignment_site_errors.csv`
- `deployable_category_improvement.csv`
- `fig_deployable_category_improvement.png`
- `future_same_row_benchmark.csv`
- `fig_future_same_row_benchmark.png`

## Is k=6 meaningful or overfit?

k=6 is meaningful but fragile.

The k=4 to k=6 comparison shows that k=6 mostly subdivides existing k=4 regimes rather than inventing arbitrary clusters:

- k=4 low-pollution stable group remains intact as a 13-site k=6 group.
- k=4 moderate/stable group splits into two k=6 groups of 10 and 6 sites.
- k=4 high/volatile group splits into a 5-site high/volatile group, one moderate/high site, and a singleton extreme site.
- The stagnant humid outlier group remains a 3-site group.

Behaviorally, k=6 separates finer PM2.5 level, volatility, ventilation, and humidity regimes. The concern is not that the split is meaningless; the concern is that several groups are too small:

- one singleton extreme group.
- one 3-site stagnant/humid group.
- one 5-site high/volatile group.

That structure explains why k=6 full-history can help. It gives the model a near-oracle high-resolution pollution-regime label. It also explains why deployment is hard: early PM2.5 windows often do not contain enough seasonal/volatility information to identify the fine group reliably.

Conclusion: k=6 is a research lead, not production. It should be revisited if more sites are added.

## Full-history vs deployable k=6 gap

`deployable_category_improvement.csv` gives the direct comparison:

| Method | Window | Deployability | R2 | RMSE | MAE |
|---|---:|---|---:|---:|---:|
| accepted k4 baseline reference | n/a | accepted reference | 0.564 | n/a | n/a |
| k=6 full-history | 0 | non-deployable upper bound | 0.558 | 12.81 | 9.38 |
| k=6 window hard category | 45 | short deploy | 0.506 | 13.59 | 9.76 |
| k=6 window hard category | 30 | short deploy | 0.505 | 13.68 | 9.96 |
| k=6 window hard category | 60 | short deploy | 0.446 | 14.20 | 10.42 |
| k=6 geodata category | 60 | zero deploy | 0.416 | 14.58 | 10.38 |
| k=6 soft category probabilities | 60 | short deploy | 0.234 | 16.69 | 13.24 |
| k=6 classifier window+geo | 60 | short deploy | 0.233 | 16.71 | 13.26 |
| k=6 centroid-distance features | 60 | short deploy | 0.117 | 17.93 | 14.45 |

Important finding: 60 days is not the best deploy window for this k=6/HGB diagnostic. The best tested windows were 30-45 days. Longer windows do not monotonically improve performance, because fewer evaluation rows remain and the high-resolution cluster assignment remains unstable.

Window sensitivity:

| Window | R2 | RMSE | MAE |
|---:|---:|---:|---:|
| 14 | 0.404 | 14.94 | 10.71 |
| 30 | 0.505 | 13.68 | 9.96 |
| 45 | 0.506 | 13.59 | 9.76 |
| 60 | 0.446 | 14.20 | 10.42 |
| 90 | 0.380 | 14.75 | 10.85 |
| 120 | 0.427 | 13.80 | 10.10 |

## Did deployable category inference improve?

Partially, but not enough to replace the accepted k=4 pipeline.

What improved:

- Testing window length found that 30-45 days is better than the inherited 60-day setting for this k=6 diagnostic.
- The best k=6 deployable result improved over k=6/window60 in the broad audit.

What failed:

- Soft category probabilities hurt.
- Distance-to-centroid features hurt.
- A fold-safe classifier using early-window features plus geodata hurt.
- Geodata-only category inference remains useful as a zero-deploy prior but not enough to recover the full-history category.

Interpretation: the bottleneck is not just hard routing. The fine k=6 category itself is not recoverable enough from early or static evidence with 39 sites.

## Does any NOW model beat accepted k=4 honestly?

No.

The best short-deploy k=6 result in this focused diagnostic is R2 0.506. The accepted k=4 reference remains around R2 0.56. The full-history k=6 upper bound is close to the accepted reference, but it is explicitly non-deployable.

Final NOW recommendation:

- Do not replace k=4.
- Keep k=6 as a challenger/research diagnostic only.
- If continuing, test k=6 again only after adding more sites or after proving early category assignment is stable.

## FUTURE same-row benchmark

`future_same_row_benchmark.csv` aligns every available method on identical `(site_id, target_day, horizon)` rows.

Available:

- locked LSTM predictions.
- existing LightGBM per-row predictions.
- new RandomForest direct predictions.
- persistence variants.

Not available:

- XGBoost per-row predictions. The saved repository has aggregate XGBoost scores but no per-row XGBoost prediction file, and the runnable Python environment does not have `xgboost` installed. It is therefore marked unavailable instead of being compared unfairly.

Same-row R2:

| Horizon | LSTM | LightGBM | RF direct | Persistence current | Persistence roll7 |
|---:|---:|---:|---:|---:|---:|
| +1 | 0.492 | 0.416 | 0.463 | 0.339 | 0.451 |
| +2 | 0.466 | 0.394 | 0.466 | 0.078 | 0.453 |
| +3 | 0.462 | 0.378 | 0.467 | 0.109 | 0.443 |
| +5 | 0.432 | 0.375 | 0.423 | 0.170 | 0.417 |
| +7 | 0.427 | 0.339 | 0.445 | 0.015 | 0.449 |

Interpretation:

- LSTM remains best at +1 and +5.
- RF ties LSTM at +2 and slightly beats it at +3.
- RF and rolling-7 persistence beat LSTM at +7 on identical rows.
- LightGBM remains behind LSTM/RF on this same-row benchmark.

Final FUTURE recommendation:

- Do not declare a full replacement for the LSTM.
- Promote RandomForest direct and rolling-7 persistence to formal challenger baselines.
- For an operational forecast, consider an ensemble or horizon-specific selection: LSTM for +1/+5, RF for +3, rolling-7 or RF for +7. This needs one more fold-safe/chronological validation pass before changing the published headline.

## Final recommendation

- NOW: reject replacement. Keep accepted k=4.
- k=6: challenger only. Meaningful regimes, but too fragile and not deployably recoverable yet.
- Deployable category inference: improved window selection, but no accepted replacement.
- FUTURE: challenger only. RF and rolling-7 are strong enough to add to the official bakeoff, but not enough to overwrite the LSTM headline without a formal same-script rerun including XGBoost/LightGBM per-row predictions.
