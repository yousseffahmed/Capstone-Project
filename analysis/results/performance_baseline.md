# Performance Baseline

Generated from the existing committed result tables before the new improvement pass.

## NOW: leave-whole-sites-out

Primary honest metric: GroupKFold / leave-sites-out R2.

| Setup | Honest score | Source |
|---|---:|---|
| Blind pooled XGBoost | 0.316 R2 | `bakeoff_now.csv` |
| `+cat` k=3 XGBoost | 0.482 R2 | `bakeoff_now.csv` |
| `+cat` k=3 RandomForest | 0.529 R2 | `bakeoff_now.csv` |
| `+cat` k=4 deploy-only | 0.558 R2 | `improve_summary.csv` |
| `+cat` k=4 fold-safe | 0.563 R2 | `improve_summary.csv` |
| `+cat+external` k=4 LightGBM | 0.561 R2 | `improve_summary.csv` |
| `+cat+external` k=4 stacked RF+XGB+LGB | 0.564 R2 | `improve_summary.csv` |
| `+cat+external` k=6 | 0.585 R2 | `improve_summary.csv`; marked fragile because it creates a singleton cluster |

Recommended pre-pass baseline: `+cat+external` k=4, approximately 0.56 R2.

## NOW: safety-tier metrics

EPA 3-tier bands: Elevated <= 35.4, High 35.5-55.4, Dangerous > 55.4.

| Setup | Exact tier | Within one tier | Baseline | Dangerous recall | Source |
|---|---:|---:|---|---:|---|
| NOW new-site `+cat+external` k=4 | 0.680 | 0.985 | 0.523 majority | 0.51 | `band_summary.csv` |
| NOW new-site `+cat` k=4 deploy-only | 0.670 | 0.981 | 0.523 majority | 0.49 | `band_summary.csv` |
| Alert threshold > 50 ug/m3 | n/a | n/a | n/a | 0.67 at 8% false-alarm | `band_summary.csv` |
| Alert threshold > 45 ug/m3 | n/a | n/a | n/a | 0.80 at 17% false-alarm | `band_summary.csv` |
| Alert threshold > 40 ug/m3 | n/a | n/a | n/a | 0.91 at 30% false-alarm | `band_summary.csv` |

Recommended pre-pass safety operating point: use regression predictions and tune the Dangerous alert threshold; >45 ug/m3 was the previous suggested point.

## FUTURE: chronological, horizon-purged

| Horizon | Persistence R2 | XGBoost R2 | LightGBM R2 | LSTM R2 | Source |
|---:|---:|---:|---:|---:|---|
| +1 | 0.339 | 0.433 | 0.416 | 0.506 | `bakeoff_future.csv` |
| +2 | 0.078 | 0.403 | 0.394 | 0.474 | `bakeoff_future.csv` |
| +3 | 0.109 | 0.363 | 0.378 | 0.477 | `bakeoff_future.csv` |
| +5 | 0.170 | 0.374 | 0.375 | 0.431 | `bakeoff_future.csv` |
| +7 | 0.015 | 0.308 | 0.339 | 0.432 | `bakeoff_future.csv` |

Recommended pre-pass FUTURE baseline: locked LSTM.

## Uncertainty

| Setup | Target | Coverage | Width | Source |
|---|---:|---:|---:|---|
| Row split conformal | 90% | 74.8% | 27.3 ug/m3 | `bakeoff_now.csv` |
| Group conformal, held-out sites | 90% | 85.8% | about 43 ug/m3 | `improve_summary.csv` |
| Mondrian per-category conformal | 90% | 80.8% | not selected | `improve_summary.csv` |

Recommended pre-pass uncertainty baseline: group conformal. It widens intervals but is less over-confident for unseen sites.
