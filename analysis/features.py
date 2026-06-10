#!/usr/bin/env python3
"""
features.py — shared feature build for the 4th-cap categorize-then-predict pipeline.

One module so pipeline.py (NOW ladder), bakeoff_now.py and bakeoff_future.py all build
features identically. Everything here is written to be LEAK-AWARE: the functions that touch
the target (category month prior, weather anomalies) take explicit train/eval splits and fit
only on train, so they are safe to call inside a CV loop.

Design notes (see DECISION_LOG.md D1-D3):
  * pm10, n_obs are NEVER features (target-coupled / unavailable at a sensor-less place).
  * site_category comes from the portable categorizer (results/categorizer.json), reproducing
    site_categorize.py's behavioural signature exactly.
  * cat_month_pm25_norm = category x month PM2.5 climatology prior, leave-one-SITE-out target
    encoding on train (avoids the self-site leak CatBoost's ordered boosting was built to kill;
    cf. Prokhorenkova et al. 2018, "CatBoost: unbiased boosting with categorical features",
    https://arxiv.org/abs/1706.09516).
  * FUTURE lags are CALENDAR-AWARE (data is ~84% daily-complete, gappy): a t-1 lag means the
    value one *calendar* day earlier, not one row earlier.
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data", "merged_kampala_complete.csv"))
CATEGORIZER = os.path.join(HERE, "results", "categorizer.json")

# ---- columns ------------------------------------------------------------------
# Leak-free, available-at-a-sensor-less-place predictors for the NOW metric:
WX   = ["temp_2m_K", "dewpoint_2m_K", "wind_u_10m_ms", "wind_v_10m_ms",
        "surface_pressure_Pa", "precipitation_m"]
LOC  = ["site_latitude", "site_longitude"]
CAL  = ["month", "day_of_week"]
ENG  = ["rel_humidity", "wind_speed"]          # human-readable weather (row-local, leak-free)
BASE_NOW = WX + LOC + CAL + ENG                 # the blind-model feature set for NOW
LST  = ["lst_day_k", "lst_night_k", "lst_day_available", "lst_night_available"]
BANNED = ["pm10", "n_obs"]                       # target-coupled — never predictors

# signature features (must match categorizer.json / site_categorize.py order)
SIG_FEATS = ["pm25_mean", "pm25_std", "pm25_p90", "pm25_season_amp",
             "temp_mean", "humidity_mean", "windspeed_mean", "precip_mean"]


# ---- load + engineer ----------------------------------------------------------
def load():
    """Load the merged table, add the two engineered weather features, sort."""
    df = pd.read_csv(DATA, parse_dates=["day"]).sort_values(["site_id", "day"]).reset_index(drop=True)
    Tc  = df.temp_2m_K - 273.15
    Tdc = df.dewpoint_2m_K - 273.15
    es  = lambda t: 6.112 * np.exp(17.67 * t / (t + 243.5))
    df["rel_humidity"] = 100 * es(Tdc) / es(Tc)
    df["wind_speed"]   = np.hypot(df.wind_u_10m_ms, df.wind_v_10m_ms)
    return df


# ---- categorization -----------------------------------------------------------
def load_categorizer(path=CATEGORIZER):
    with open(path) as f:
        return json.load(f)


def _seasonal_amplitude(s):
    m = s.groupby(s.index.month).mean()
    return float(m.max() - m.min()) if len(m) else np.nan


def site_signature(g):
    """Behavioural signature of one site from a slice of its rows (full history OR a window).
    g must have: pm2_5, temp_2m_K, rel_humidity, wind_speed, precipitation_m, day."""
    return {
        "pm25_mean":       g.pm2_5.mean(),
        "pm25_std":        g.pm2_5.std(),
        "pm25_p90":        g.pm2_5.quantile(0.90),
        "pm25_season_amp": _seasonal_amplitude(g.set_index("day").pm2_5),
        "temp_mean":       g.temp_2m_K.mean() - 273.15,
        "humidity_mean":   g.rel_humidity.mean(),
        "windspeed_mean":  g.wind_speed.mean(),
        "precip_mean":     g.precipitation_m.mean() * 1000,
    }


def snap(sig_dict, cat):
    """Snap a signature to the nearest category centroid (the one live step for a new site)."""
    v   = np.array([sig_dict[f] for f in cat["features"]], float)
    # season_amp can be NaN for a very short window -> fall back to the scaler mean (neutral)
    mean, scale = np.array(cat["scaler_mean"]), np.array(cat["scaler_scale"])
    v   = np.where(np.isnan(v), mean, v)
    vs  = (v - mean) / scale
    cen = np.array(cat["centroids"])
    return int(np.argmin(((vs - cen) ** 2).sum(1)))


def assign_full_categories(df, cat):
    """Tier-A: every site -> category from its FULL-history signature. Returns {site_id: cluster}."""
    out = {}
    for sid, g in df.groupby("site_id"):
        out[sid] = snap(site_signature(g), cat)
    return out


def assign_window_categories(df, cat, n_days=60):
    """Tier-B (cold-start deploy): each site -> category from only its FIRST n_days observed days.
    Returns ({site_id: cluster}, {site_id: cutoff_day}) so the eval can drop the warm-up rows."""
    labels, cutoffs = {}, {}
    for sid, g in df.groupby("site_id"):
        g = g.sort_values("day")
        win = g.head(n_days)
        labels[sid]  = snap(site_signature(win), cat)
        cutoffs[sid] = win.day.max()
    return labels, cutoffs


# ---- leak-free fold features (call INSIDE a CV loop with train/eval split) -----
def add_category_priors(train_df, eval_df, cat_col="site_category"):
    """Add leak-free category features, fitting only on train_df.

    Returns (train_df, eval_df, new_cols). New columns:
      cat_month_pm25_norm   category x month PM2.5 climatology prior
                            (train rows: leave-one-SITE-out; eval rows: full train of that cat)
      t_anom, w_anom, h_anom  today's temp/wind/humidity minus the (category,month) train mean
    """
    train_df = train_df.copy(); eval_df = eval_df.copy()

    # --- cat x month PM2.5 prior ---
    grp = train_df.groupby([cat_col, "month"])
    cm_sum = grp.pm2_5.sum(); cm_cnt = grp.pm2_5.count()
    # leave-one-site-out per (cat,month) for TRAIN rows: subtract this site's own contribution
    site_grp = train_df.groupby([cat_col, "month", "site_id"])
    s_sum = site_grp.pm2_5.transform("sum"); s_cnt = site_grp.pm2_5.transform("count")
    cm_sum_b = train_df.set_index([cat_col, "month"]).index.map(cm_sum).astype(float).values
    cm_cnt_b = train_df.set_index([cat_col, "month"]).index.map(cm_cnt).astype(float).values
    loo_cnt = cm_cnt_b - s_cnt.values
    loo = np.where(loo_cnt > 0, (cm_sum_b - s_sum.values) / np.maximum(loo_cnt, 1), np.nan)
    train_df["cat_month_pm25_norm"] = loo
    # eval rows: full train mean of their (cat,month)
    cm_mean = (cm_sum / cm_cnt)
    eval_df["cat_month_pm25_norm"] = eval_df.set_index([cat_col, "month"]).index.map(cm_mean).astype(float).values
    # global train fallback for unseen (cat,month)
    gmean = train_df.pm2_5.mean()
    for d in (train_df, eval_df):
        d["cat_month_pm25_norm"] = d["cat_month_pm25_norm"].fillna(gmean)

    # --- category x month weather anomalies (weather isn't the target -> leak-free) ---
    anoms = {"t_anom": "temp_2m_K", "w_anom": "wind_speed", "h_anom": "rel_humidity"}
    for newc, src in anoms.items():
        m = train_df.groupby([cat_col, "month"])[src].mean()
        for d in (train_df, eval_df):
            base = d.set_index([cat_col, "month"]).index.map(m).astype(float).values
            base = np.where(np.isnan(base), train_df[src].mean(), base)
            d[newc] = d[src].values - base

    new_cols = ["cat_month_pm25_norm", "t_anom", "w_anom", "h_anom"]
    return train_df, eval_df, new_cols


# ---- FUTURE panel: calendar-aware lags + rolling means ------------------------
def build_future_panel(df, lags=(1, 2, 3, 7), rolls=(7, 14)):
    """Per-site daily-complete panel with CALENDAR-AWARE lag/rolling features known at day t.
    Reindexes each site to its full daily date range so a t-1 lag is one calendar day, not one
    row. Returns the long frame restricted to rows where pm2_5 is actually observed AND all
    requested lags exist. Adds: pm25_lag{L}, pm25_roll{R}, plus carries weather/category cols."""
    keep_wx = WX + ENG
    out = []
    for sid, g in df.groupby("site_id"):
        g = g.set_index("day").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="D")
        g = g.reindex(full)
        g["site_id"] = sid
        obs = g.pm2_5.notna()                       # genuine observation mask
        for L in lags:
            g[f"pm25_lag{L}"] = g.pm2_5.shift(L)
        for R in rolls:
            # rolling mean of the PAST R days (shift(1) so day t is excluded)
            g[f"pm25_roll{R}"] = g.pm2_5.shift(1).rolling(R, min_periods=max(2, R // 2)).mean()
        g["month"] = g.index.month; g["day_of_week"] = g.index.dayofweek
        g["obs"] = obs.values
        g = g.reset_index().rename(columns={"index": "day"})
        out.append(g)
    panel = pd.concat(out, ignore_index=True)
    lag_cols = [f"pm25_lag{L}" for L in lags]
    panel = panel[panel.obs & panel[lag_cols].notna().all(axis=1)].reset_index(drop=True)
    return panel


if __name__ == "__main__":
    # self-test: reproduce CP-A category sizes and sanity-check the panel
    df = load(); cat = load_categorizer()
    full = assign_full_categories(df, cat)
    s = pd.Series(full)
    print("Tier-A full-signature category sizes:", s.value_counts().sort_index().to_dict(),
          "(expect {0:24,1:12,2:3})")
    win, cut = assign_window_categories(df, cat, 60)
    sw = pd.Series(win)
    print("Tier-B 60-day-window category sizes:", sw.value_counts().sort_index().to_dict())
    agree = (s.sort_index().values == sw.sort_index().values).mean()
    print(f"Tier-A vs Tier-B agreement: {agree:.2f}")
    panel = build_future_panel(df)
    print("future panel:", panel.shape, "| rows with all lags, observed target")
