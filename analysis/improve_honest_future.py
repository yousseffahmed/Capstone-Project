#!/usr/bin/env python3
"""Honest FUTURE forecasting experiments.

Uses a blocked chronological split with horizon purging:
  train rows are allowed only when their target day t+h is <= the cut date;
  test rows use feature day t > the cut date.

The script evaluates richer lag/rolling/trend feature sets and sklearn models.
It does not use random/KFold validation for time series.
"""
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "results", ".mplcache"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import features as F

OUT = os.path.join(F.HERE, "results")
SEED = 42
HORIZONS = [1, 2, 3, 5, 7]


def build_rich_panel(df):
    """Calendar-aware per-site panel using PM2.5 history only up to feature day t."""
    out = []
    for sid, g in df.groupby("site_id"):
        g = g.set_index("day").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="D")
        g = g.reindex(full)
        g["site_id"] = sid
        observed = g["pm2_5"].notna()

        for lag in [1, 2, 3, 4, 5, 6, 7, 14]:
            g[f"pm25_lag{lag}"] = g["pm2_5"].shift(lag)

        past = g["pm2_5"].shift(1)
        for w in [3, 7, 14, 21]:
            r = past.rolling(w, min_periods=max(2, w // 2))
            g[f"pm25_roll{w}_mean"] = r.mean()
            g[f"pm25_roll{w}_std"] = r.std()
            g[f"pm25_roll{w}_min"] = r.min()
            g[f"pm25_roll{w}_max"] = r.max()

        g["trend_lag1_lag7"] = g["pm25_lag1"] - g["pm25_lag7"]
        g["trend_roll3_roll14"] = g["pm25_roll3_mean"] - g["pm25_roll14_mean"]
        g["month"] = g.index.month
        g["day_of_week"] = g.index.dayofweek
        g["doy_sin"] = np.sin(2 * np.pi * g.index.dayofyear / 366.0)
        g["doy_cos"] = np.cos(2 * np.pi * g.index.dayofyear / 366.0)
        g["obs"] = observed.values
        g = g.reset_index().rename(columns={"index": "day"})
        out.append(g)

    panel = pd.concat(out, ignore_index=True)
    needed = ["pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_lag7", "pm25_lag14"]
    return panel[panel["obs"] & panel[needed].notna().all(axis=1)].reset_index(drop=True)


def make_supervised(panel, h):
    tgt = panel[["site_id", "day", "pm2_5"]].copy()
    tgt["day"] = tgt["day"] - pd.Timedelta(days=h)
    sup = panel.merge(tgt.rename(columns={"pm2_5": "y_future"}), on=["site_id", "day"], how="inner")
    target_day = sup["day"] + pd.Timedelta(days=h)
    sup["target_month"] = target_day.dt.month
    sup["target_dow"] = target_day.dt.dayofweek
    sup["target_doy_sin"] = np.sin(2 * np.pi * target_day.dt.dayofyear / 366.0)
    sup["target_doy_cos"] = np.cos(2 * np.pi * target_day.dt.dayofyear / 366.0)
    return sup


def chrono_masks(frame, cut, h):
    cutd = np.datetime64(cut)
    train = (frame.day.values + np.timedelta64(h, "D")) <= cutd
    test = frame.day.values > cutd
    return train, test


def model_grid():
    return {
        "rf": RandomForestRegressor(
            n_estimators=140, max_depth=22, min_samples_leaf=4,
            max_features="sqrt", n_jobs=1, random_state=SEED
        ),
        "hgb_l2": HistGradientBoostingRegressor(
            max_iter=220, learning_rate=0.05, max_leaf_nodes=31,
            l2_regularization=0.05, random_state=SEED
        ),
        "hgb_abs": HistGradientBoostingRegressor(
            loss="absolute_error", max_iter=220, learning_rate=0.05,
            max_leaf_nodes=31, l2_regularization=0.05, random_state=SEED
        ),
    }


def feature_sets(panel):
    base = [
        "pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_lag7",
        "pm25_roll7_mean", "pm25_roll14_mean",
        "month", "day_of_week", "target_month", "target_dow",
    ]
    rich = base + [
        "pm25_lag4", "pm25_lag5", "pm25_lag6", "pm25_lag14",
        "pm25_roll3_mean", "pm25_roll3_std", "pm25_roll3_min", "pm25_roll3_max",
        "pm25_roll7_std", "pm25_roll7_min", "pm25_roll7_max",
        "pm25_roll14_std", "pm25_roll14_min", "pm25_roll14_max",
        "pm25_roll21_mean", "pm25_roll21_std", "pm25_roll21_min", "pm25_roll21_max",
        "trend_lag1_lag7", "trend_roll3_roll14",
        "doy_sin", "doy_cos", "target_doy_sin", "target_doy_cos",
    ]
    weather = rich + F.WX + F.ENG
    loc_cat = weather + ["site_latitude", "site_longitude"]
    for c in [col for col in panel.columns if col.startswith("cat_")]:
        loc_cat.append(c)
    return {
        "base_existing_plus_target_calendar": base,
        "rich_lag_roll_trend": rich,
        "rich_plus_current_weather": weather,
        "rich_plus_weather_loc_category": loc_cat,
    }


def persistence_scores(te):
    y = te["y_future"].values
    variants = {
        "persist_yesterday": te["pm2_5"].values,
        "persist_lag1": te["pm25_lag1"].values,
        "persist_roll7": te["pm25_roll7_mean"].values,
        "persist_lag7": te["pm25_lag7"].values,
    }
    rows = []
    for name, pred in variants.items():
        mask = ~np.isnan(pred)
        rows.append({
            "model": name,
            "feature_set": "persistence",
            "r2": r2_score(y[mask], pred[mask]),
            "rmse": float(np.sqrt(mean_squared_error(y[mask], pred[mask]))),
            "mae": mean_absolute_error(y[mask], pred[mask]),
            "n_test": int(mask.sum()),
        })
    return rows


def conformal_for_best(sup, cut, h, cols, model_name):
    trm, tem = chrono_masks(sup, cut, h)
    train_full = sup[trm].dropna(subset=cols + ["y_future"]).copy()
    test = sup[tem].dropna(subset=cols + ["y_future"]).copy()
    cut2 = train_full["day"].quantile(0.8)
    proper = train_full[train_full["day"] <= cut2]
    cal = train_full[train_full["day"] > cut2]
    m = model_grid()[model_name]
    fill = proper[cols].median(numeric_only=True)
    m.fit(proper[cols].fillna(fill), proper["y_future"].values)
    cal_pred = m.predict(cal[cols].fillna(fill))
    resid = np.abs(cal["y_future"].values - cal_pred)
    q = float(np.quantile(resid, min(1.0, np.ceil((len(resid) + 1) * 0.90) / len(resid))))
    pred = m.predict(test[cols].fillna(fill))
    covered = (test["y_future"].values >= pred - q) & (test["y_future"].values <= pred + q)
    return {
        "task": f"FUTURE +{h}",
        "method": "chronological_split_conformal",
        "target_coverage": 0.90,
        "coverage": float(covered.mean()),
        "width": float(2 * q),
        "config": f"{model_name} {len(cols)} features",
        "folds": "chronological",
    }


def main():
    df = F.load()
    cat = F.load_categorizer()
    site_cat = F.assign_full_categories(df, cat)
    df["site_category"] = df["site_id"].map(site_cat)
    panel = build_rich_panel(df)
    for j in sorted(set(site_cat.values())):
        panel[f"cat_{j}"] = (panel["site_id"].map(site_cat) == j).astype(float)

    cut = df["day"].quantile(0.8)
    print(f"chronological cut = {pd.Timestamp(cut).date()}")

    rows = []
    best_by_h = {}
    for h in HORIZONS:
        sup = make_supervised(panel, h)
        trm, tem = chrono_masks(sup, cut, h)
        train = sup[trm]
        test = sup[tem]
        rows.extend([{"horizon": h, **r} for r in persistence_scores(test)])

        sets = feature_sets(panel)
        for fs_name, cols in sets.items():
            cols = [c for c in cols if c in sup.columns]
            tr = train.dropna(subset=cols + ["y_future"]).copy()
            te = test.dropna(subset=cols + ["y_future"]).copy()
            fill = tr[cols].median(numeric_only=True)
            for model_name, model in model_grid().items():
                print(f"h+{h} {fs_name} {model_name}")
                model.fit(tr[cols].fillna(fill), tr["y_future"].values)
                pred = model.predict(te[cols].fillna(fill))
                row = {
                    "horizon": h,
                    "model": model_name,
                    "feature_set": fs_name,
                    "r2": r2_score(te["y_future"].values, pred),
                    "rmse": float(np.sqrt(mean_squared_error(te["y_future"].values, pred))),
                    "mae": mean_absolute_error(te["y_future"].values, pred),
                    "n_test": int(len(te)),
                    "n_features": int(len(cols)),
                }
                rows.append(row)

    res = pd.DataFrame(rows).sort_values(["horizon", "r2"], ascending=[True, False])
    res.to_csv(os.path.join(OUT, "future_improvement_experiments.csv"), index=False)

    for h in HORIZONS:
        sub = res[(res.horizon == h) & ~res.model.str.startswith("persist")].sort_values("r2", ascending=False)
        if not sub.empty:
            best_by_h[h] = sub.iloc[0].to_dict()

    unc_rows = []
    for h, best in best_by_h.items():
        sup = make_supervised(panel, h)
        cols = feature_sets(panel)[best["feature_set"]]
        cols = [c for c in cols if c in sup.columns]
        unc_rows.append(conformal_for_best(sup, cut, h, cols, best["model"]))

    unc_path = os.path.join(OUT, "uncertainty_calibration.csv")
    old = pd.read_csv(unc_path) if os.path.exists(unc_path) else pd.DataFrame()
    pd.concat([old, pd.DataFrame(unc_rows)], ignore_index=True).to_csv(unc_path, index=False)

    print("\nBest FUTURE configs:")
    print(res.groupby("horizon").head(5).to_string(index=False))
    print("\nWrote future_improvement_experiments.csv and appended FUTURE uncertainty rows")


if __name__ == "__main__":
    main()
