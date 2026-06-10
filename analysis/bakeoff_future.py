#!/usr/bin/env python3
"""
bakeoff_future.py — CP-D (FUTURE metric): forecast PM2.5 +1..+7 days at a KNOWN site.

Honest test = blocked CHRONOLOGICAL split (train on the early 80% of days, forecast the late
20%). The bar to beat is PERSISTENCE ("tomorrow = today"). A model only earns its place if it
beats persistence out-of-time; an LSTM only earns ITS place if it beats the cheap GBM-on-lags.

Features known at forecast time t (NO peeking at the target day's weather — that would itself
be a forecast): PM2.5 calendar-aware lags (t-1,2,3,7) + rolling means (7,14d) + current weather
at t + calendar of the target day + static site_category/loc. Target = PM2.5 at t+h.

Models:
  persistence            y_hat(t+h) = y(t)                          (the bar)
  XGBoost / LightGBM     gradient boosting on the lag feature table (the cheap strong baseline)

The LSTM lives in a SEPARATE process (lstm_future.py). Reason: on macOS PyTorch ships its own
OpenMP runtime (libiomp5) which DEADLOCKS when imported into a process that already loaded
XGBoost/LightGBM's libomp (confirmed: pytorch/pytorch#44282, LightGBM FAQ). KMP_DUPLICATE_LIB_OK
is a hack that "may silently produce incorrect results" — unacceptable here — so we isolate by
process instead. Run order: this script (writes bakeoff_future.csv) THEN lstm_future.py (adds the
LSTM column + redraws the figure).

Outputs -> results/bakeoff_future.csv, results/fig_bakeoff_future.png
Run: ../../../working/.venv/bin/python bakeoff_future.py   (then lstm_future.py)
"""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
import xgboost as xgb, lightgbm as lgb
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
HORIZONS = [1, 2, 3, 4, 5, 6, 7]
LAGFEATS = ["pm25_lag1", "pm25_lag2", "pm25_lag3", "pm25_lag7", "pm25_roll7", "pm25_roll14"]
np.random.seed(SEED)

# ---------------------------------------------------------------------------
def make_supervised(panel, h):
    """Pair each feature-row at day t with target PM2.5 at t+h (same site, calendar-aligned)."""
    tgt = panel[["site_id", "day", "pm2_5"]].copy()
    tgt["day"] = tgt["day"] - pd.Timedelta(days=h)        # so a t-row matches y at t+h
    tgt = tgt.rename(columns={"pm2_5": "y_future"})
    m = panel.merge(tgt, on=["site_id", "day"], how="inner")
    return m

def chrono_masks(frame, cut, h):
    """Blocked split PURGED by the horizon: a train row's TARGET (at t+h) must also be pre-cut,
    else a training example would peek across the chronological boundary into the test period.
    The h-day band of feature-rows in (cut-h, cut] is dropped (the purge gap)."""
    cutd = np.datetime64(cut)
    tr = (frame.day.values + np.timedelta64(h, "D")) <= cutd
    te = frame.day.values > cutd
    return tr, te

def main():
    df = F.load(); cat = F.load_categorizer()
    site_cat = F.assign_full_categories(df, cat)
    panel = F.build_future_panel(df)
    panel["site_category"] = panel.site_id.map(site_cat)
    cut = df["day"].quantile(0.8)
    print(f"chronological cut = {pd.Timestamp(cut).date()}  (train ≤ cut, forecast > cut)")
    FEATS = LAGFEATS + F.WX + F.ENG + ["month", "day_of_week", "site_latitude", "site_longitude"]

    rows = []
    # ---- persistence + GBMs, all horizons ----
    for h in HORIZONS:
        sup = make_supervised(panel, h)
        trm, tem = chrono_masks(sup, cut, h)
        tr, te = sup[trm], sup[tem]
        yte = te.y_future.values
        # persistence: tomorrow=today (current pm2_5 at t)
        r_pers = r2_score(yte, te.pm2_5.values)
        # XGB on lags
        mx = xgb.XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8,
                              colsample_bytree=0.8, n_jobs=-1, random_state=SEED)
        mx.fit(tr[FEATS], tr.y_future.values); r_xgb = r2_score(yte, mx.predict(te[FEATS]))
        ml = lgb.LGBMRegressor(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8,
                               colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1)
        ml.fit(tr[FEATS], tr.y_future.values); r_lgb = r2_score(yte, ml.predict(te[FEATS]))
        rows.append(dict(horizon=h, persistence=round(r_pers, 4), XGBoost=round(r_xgb, 4),
                         LightGBM=round(r_lgb, 4), LSTM=np.nan, n_test=int(len(te))))
        print(f"  h+{h}: persistence {r_pers:+.3f} | XGB {r_xgb:+.3f} | LGBM {r_lgb:+.3f}  (n_test={len(te)})")

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT, "bakeoff_future.csv"), index=False)
    print("  (LSTM column added by lstm_future.py — separate process, OpenMP isolation)")

    # ---- figure: R² vs horizon, all methods ----
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for col, c, mk in [("persistence", "#d43030", "o"), ("XGBoost", "#14A38B", "s"),
                       ("LightGBM", "#0E7C66", "^"), ("LSTM", "#E8A020", "D")]:
        if res[col].notna().any():
            ax.plot(res.horizon, res[col], mk + "-", color=c, label=col, lw=2)
    ax.axhline(0, color="k", lw=.8, ls=":")
    ax.set_xlabel("forecast horizon (days ahead)"); ax.set_ylabel("R² (chronological, out-of-time)")
    ax.set_title("FUTURE bake-off — must beat persistence; LSTM must beat the GBMs")
    ax.legend(fontsize=9); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_bakeoff_future.png"), dpi=130); plt.close(fig)
    print(f"\nwrote results/bakeoff_future.csv · results/fig_bakeoff_future.png")

if __name__ == "__main__":
    main()
