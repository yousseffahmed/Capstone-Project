#!/usr/bin/env python3
"""Fair same-row FUTURE benchmark.

Aligns all available per-row forecasts on (site_id, target_day, h).

Available in this environment:
  - locked LSTM predictions: results/lstm_preds_base.csv
  - existing LightGBM predictions: results/gbm_preds.csv
  - new RandomForest direct models generated here
  - persistence variants generated here

XGBoost cannot be included fairly because no per-row XGBoost prediction file is
present and the runnable Python environment does not have xgboost installed.
"""
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "results", ".mplcache"))
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import features as F

OUT = os.path.join(F.HERE, "results")
SEED = 42
HORIZONS = [1, 2, 3, 5, 7]


def rmse(y, p):
    return float(np.sqrt(mean_squared_error(y, p)))


def build_panel(df):
    out = []
    for sid, g in df.groupby("site_id"):
        g = g.set_index("day").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="D")
        g = g.reindex(full)
        g["site_id"] = sid
        obs = g.pm2_5.notna()
        for lag in [1, 2, 3, 7, 14]:
            g[f"pm25_lag{lag}"] = g.pm2_5.shift(lag)
        past = g.pm2_5.shift(1)
        for w in [3, 7, 14]:
            g[f"pm25_roll{w}"] = past.rolling(w, min_periods=max(2, w // 2)).mean()
        g["trend_lag1_lag7"] = g.pm25_lag1 - g.pm25_lag7
        g["month"] = g.index.month
        g["day_of_week"] = g.index.dayofweek
        g["obs"] = obs.values
        out.append(g.reset_index().rename(columns={"index": "day"}))
    p = pd.concat(out, ignore_index=True)
    return p[p.obs & p.pm25_lag7.notna()].reset_index(drop=True)


def make_supervised(panel, h):
    tgt = panel[["site_id", "day", "pm2_5"]].copy()
    tgt["day"] = tgt["day"] - pd.Timedelta(days=h)
    return panel.merge(tgt.rename(columns={"pm2_5": "y_future"}), on=["site_id", "day"], how="inner")


def rf_predictions():
    df = F.load()
    panel = build_panel(df)
    cut = df.day.quantile(0.8); cutd = np.datetime64(cut)
    feats = ["pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_lag7", "pm25_roll3", "pm25_roll7", "pm25_roll14", "trend_lag1_lag7", "month", "day_of_week"] + F.WX + F.ENG
    rows = []
    for h in HORIZONS:
        sup = make_supervised(panel, h)
        trm = (sup.day.values + np.timedelta64(h, "D")) <= cutd
        tem = sup.day.values > cutd
        tr = sup[trm].dropna(subset=feats + ["y_future"])
        te = sup[tem].dropna(subset=feats + ["y_future"])
        m = RandomForestRegressor(n_estimators=180, max_depth=22, min_samples_leaf=4, max_features="sqrt", n_jobs=1, random_state=SEED)
        fill = tr[feats].median(numeric_only=True)
        m.fit(tr[feats].fillna(fill), tr.y_future.values)
        pred = m.predict(te[feats].fillna(fill))
        target_day = (te.day + pd.Timedelta(days=h)).dt.strftime("%Y-%m-%d")
        for sid, td, p, y in zip(te.site_id, target_day, pred, te.y_future):
            rows.append({"site_id": sid, "target_day": td, "h": h, "rf_pred": float(p), "y": float(y)})
    return pd.DataFrame(rows)


def persistence_predictions():
    df = F.load()
    panel = build_panel(df)
    cut = df.day.quantile(0.8); cutd = np.datetime64(cut)
    rows = []
    for h in HORIZONS:
        sup = make_supervised(panel, h)
        te = sup[sup.day.values > cutd].copy()
        target_day = (te.day + pd.Timedelta(days=h)).dt.strftime("%Y-%m-%d")
        for _, r in te.iterrows():
            rows.append({
                "site_id": r.site_id,
                "target_day": (r.day + pd.Timedelta(days=h)).strftime("%Y-%m-%d"),
                "h": h,
                "persist_current": float(r.pm2_5),
                "persist_roll7": float(r.pm25_roll7) if pd.notna(r.pm25_roll7) else np.nan,
                "persist_lag7": float(r.pm25_lag7) if pd.notna(r.pm25_lag7) else np.nan,
                "y": float(r.y_future),
            })
    return pd.DataFrame(rows)


def main():
    lstm = pd.read_csv(os.path.join(OUT, "lstm_preds_base.csv")).rename(columns={"pred": "lstm_pred", "y": "y_lstm"})
    lgb = pd.read_csv(os.path.join(OUT, "gbm_preds.csv")).rename(columns={"pred": "lightgbm_pred", "y": "y_lgb"})
    rf = rf_predictions()
    pers = persistence_predictions()
    m = lstm.merge(lgb, on=["site_id", "target_day", "h"], how="inner")
    m = m.merge(rf.drop(columns=["y"]), on=["site_id", "target_day", "h"], how="inner")
    m = m.merge(pers.drop(columns=["y"]), on=["site_id", "target_day", "h"], how="inner")
    m = m[m.h.isin(HORIZONS)].copy()
    m["y"] = m["y_lstm"]

    rows = []
    methods = {
        "LSTM_locked": "lstm_pred",
        "LightGBM_existing": "lightgbm_pred",
        "RandomForest_direct": "rf_pred",
        "persistence_current": "persist_current",
        "persistence_roll7": "persist_roll7",
        "persistence_lag7": "persist_lag7",
    }
    for h in HORIZONS:
        s = m[m.h == h]
        for name, col in methods.items():
            ss = s.dropna(subset=[col, "y"])
            rows.append({
                "horizon": h,
                "method": name,
                "status": "ok",
                "n_rows": len(ss),
                "r2": r2_score(ss.y, ss[col]),
                "rmse": rmse(ss.y, ss[col]),
                "mae": mean_absolute_error(ss.y, ss[col]),
            })
        rows.append({
            "horizon": h,
            "method": "XGBoost",
            "status": "not_run_no_per_row_predictions_and_package_unavailable",
            "n_rows": len(s),
            "r2": np.nan,
            "rmse": np.nan,
            "mae": np.nan,
        })

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT, "future_same_row_benchmark.csv"), index=False)

    fig, ax = plt.subplots(figsize=(8, 4.6))
    for method, color in [
        ("LSTM_locked", "#E8A020"),
        ("LightGBM_existing", "#0E7C66"),
        ("RandomForest_direct", "#14A38B"),
        ("persistence_current", "#d43030"),
        ("persistence_roll7", "#6b7f8b"),
    ]:
        s = res[(res.method == method) & (res.status == "ok")]
        ax.plot(s.horizon, s.r2, "o-", label=method, color=color)
    ax.axhline(0, color="k", lw=.8, ls=":")
    ax.set_xlabel("Horizon")
    ax.set_ylabel("R2 on identical rows")
    ax.set_title("FUTURE same-row benchmark")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_future_same_row_benchmark.png"), dpi=140)
    plt.close(fig)

    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
