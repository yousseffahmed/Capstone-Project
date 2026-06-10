#!/usr/bin/env python3
"""
new_site_predict.py — deployable NEW-SITE predictor + honest leave-one-site-out demo.

Answers end-to-end: given a brand-new Kampala location, WHAT INPUTS are needed and WHAT does the
model output for (a) the current particle (nowcast PM2.5 + EPA safety tier + uncertainty band +
danger-dial verdict) and (b) the next 7 days.

INPUT CONTRACT for a new site (what a planner supplies):
  REQUIRED (zero-deploy):
    site_latitude, site_longitude   decimal deg (Kampala ~ lat 0.20-0.40, lon 32.50-32.70)
    date                            -> month, day_of_week
    weather for that day (free ERA5): temp_2m_K, dewpoint_2m_K, wind_u_10m_ms, wind_v_10m_ms,
                                      surface_pressure_Pa, precipitation_m
                                      (rel_humidity, wind_speed are DERIVED)
    geodata (auto from lat/lon via fetch_external.py): dist_major_road_m, road_len_all_300m,
                                      road_len_all_1000m, road_len_major_500m, elevation_m
  OPTIONAL (short-deploy, unlocks the real forecaster + a sharper category):
    >= 14 days of recent daily PM2.5 at the site (a temporary low-cost sensor)

MODES:
  zero-deploy : nowcast from weather+location+geodata (+ geodata-inferred category).
  short-deploy: category from the observed window; future from the lag forecaster seeded with it.

DEMO (--demo SITE_ID): leave that site OUT, train on the other 38, predict it, compare to truth.
Run: ./capenv/bin/python new_site_predict.py --demo site_135
     ./capenv/bin/python new_site_predict.py --demo <highest-pollution site> --suffix _hi

Production FUTURE forecaster is the LSTM (models/lstm_future.pt, locked +1d 0.51 -> +7d 0.43). This
torch-free LightGBM-on-lags is the portable equivalent for the live demo; stated in the output.
"""
import os, argparse, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import lightgbm as lgb
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EDGES = [35.4, 55.4]; TIERS = ["Elevated", "High", "Dangerous"]
def tier(x):  return int(np.clip(np.digitize([x], EDGES)[0], 0, 2))
def tname(x): return TIERS[tier(x)]

EXT  = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]
CAT  = F.load_categorizer()


def _qhat(resid, alpha=0.10):
    n = len(resid); return float(np.quantile(resid, min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)))


# ---------- NOWCAST model (RF +category+geodata) on a set of training sites ----------
def build_now(df, train_sites):
    tr = df[df.site_id.isin(train_sites)].copy()
    cols = list(F.BASE_NOW) + ["cat_0", "cat_1", "cat_2"] + EXTF
    kw = dict(n_estimators=400, max_depth=30, max_features="sqrt",
              min_samples_leaf=4, n_jobs=-1, random_state=SEED)
    rf = RandomForestRegressor(**kw).fit(tr[cols], tr.pm2_5.values)
    # group-conformal band: residual quantile on held-out TRAINING sites
    rng = np.random.default_rng(SEED)
    cal_sites = set(rng.choice(sorted(train_sites), max(3, len(train_sites) // 4), replace=False))
    ptr = tr[~tr.site_id.isin(cal_sites)]; cal = tr[tr.site_id.isin(cal_sites)]
    rf2 = RandomForestRegressor(**kw).fit(ptr[cols], ptr.pm2_5.values)
    q = _qhat(np.abs(cal.pm2_5.values - rf2.predict(cal[cols])))
    return rf, cols, q


# ---------- category for a sensor-less new site, from GEODATA alone ----------
def category_from_geodata(df, train_sites, geo_row):
    # kNN(5) on standardized geodata — beats the 4th-cap RandomForest (leave-one-site-out 0.54 -> 0.64,
    # now > the 0.615 majority; see improve_blind_cat.py). NOTE (investigate_categorization.py): a *guessed*
    # category does NOT improve the µg/m³ nowcast (a wrong guess misleads it); this label is for triage/display.
    # For a truly sensor-less site the nowcast leans on weather + geodata directly; the category lever needs a deploy.
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.preprocessing import StandardScaler
    full = F.assign_full_categories(df, CAT)
    per  = EXT.set_index("site_id")
    tr   = [s for s in train_sites if s in per.index]
    sc = StandardScaler().fit(per.loc[tr, EXTF].fillna(per[EXTF].mean()).values)
    X = sc.transform(per.loc[tr, EXTF].fillna(per[EXTF].mean()).values)
    y = np.array([full[s] for s in tr])
    clf = KNeighborsClassifier(n_neighbors=5).fit(X, y)
    return int(clf.predict(sc.transform(np.array([[geo_row[f] for f in EXTF]])))[0])


# ---------- category from a short observed window (short-deploy) ----------
def category_from_window(window_df):
    return F.snap(F.site_signature(window_df), CAT)   # needs pm2_5/temp/rel_humidity/wind_speed/precip/day


# ---------- FUTURE forecaster: torch-free LightGBM multi-horizon on calendar-aware lags ----------
def build_future(df, train_sites):
    panel = F.build_future_panel(df)
    panel = panel[panel.site_id.isin(train_sites)].copy()
    lagcols = [c for c in panel.columns if c.startswith("pm25_lag") or c.startswith("pm25_roll")]
    feats = lagcols + ["month", "day_of_week", "temp_2m_K", "rel_humidity", "wind_speed"]
    models = {}
    for h in range(1, 8):
        tgt = panel[["site_id", "day", "pm2_5"]].copy(); tgt["day"] = tgt["day"] - pd.Timedelta(days=h)
        sup = panel.merge(tgt.rename(columns={"pm2_5": "y"}), on=["site_id", "day"], how="inner").dropna(subset=feats + ["y"])
        m = lgb.LGBMRegressor(n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8,
                              colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1)
        m.fit(sup[feats], sup.y.values); models[h] = m
    return models, feats


def forecast_site(models, feats, df, site_id, anchor_day):
    """Forecast +1..+7 from the site's own observed lags at anchor_day (short-deploy)."""
    panel = F.build_future_panel(df)
    row = panel[(panel.site_id == site_id) & (panel.day == pd.Timestamp(anchor_day))]
    if row.empty: return None
    x = row[feats]
    return {h: float(models[h].predict(x)[0]) for h in range(1, 8)}


def pick_anchor(df, site_id, feats):
    """Pick the first observed day of the held-out site that exists in the FUTURE panel
    (all lags present) — robust to gaps, instead of a blind .iloc[90]."""
    panel = F.build_future_panel(df)
    have = panel[panel.site_id == site_id].sort_values("day")
    if have.empty: return None
    # prefer an anchor ~90 obs-days in (leaves a real forward window to score against)
    idx = min(90, max(0, len(have) - 8))
    return have.iloc[idx].day


# ---------- the honest demo ----------
def demo(site_id, suffix=""):
    df = F.load()
    # attach category one-hots (full-signature) + geodata so the NOW model has its columns
    full = F.assign_full_categories(df, CAT); df["c"] = df.site_id.map(full)
    for j in range(3): df[f"cat_{j}"] = (df.c == j).astype(float)
    df = df.merge(EXT, on="site_id", how="left")
    all_sites = sorted(df.site_id.unique()); assert site_id in all_sites, site_id
    train = [s for s in all_sites if s != site_id]

    print("=" * 78); print(f"NEW-SITE DEMO — held-out site: {site_id} (trained on the other {len(train)})"); print("=" * 78)
    geo = EXT[EXT.site_id == site_id].iloc[0]
    lat = df[df.site_id == site_id].site_latitude.iloc[0]; lon = df[df.site_id == site_id].site_longitude.iloc[0]
    print("\n[ INPUT CONTRACT — what a planner supplies for this new lat/lon ]")
    print(f"  location : ({lat:.4f}, {lon:.4f})  +  date -> month, day_of_week")
    print(f"  weather  : ERA5 temp/dewpoint/wind-u/wind-v/pressure/precip (free, daily)")
    print(f"  geodata  : auto from lat/lon -> " + ", ".join(f"{k}={geo[k]:.0f}" for k in EXTF))

    # --- category, three ways ---
    cat_geo = category_from_geodata(df, train, geo)
    win = df[df.site_id == site_id].sort_values('day').head(60)
    cat_win = category_from_window(win)
    true_cat = full[site_id]
    L = CAT['cluster_labels']
    print("\n[ CATEGORIZE the new place ]")
    print(f"  from geodata (0 obs)  : {cat_geo}  '{L[str(cat_geo)]}'")
    print(f"  from 60-day window    : {cat_win}  '{L[str(cat_win)]}'")
    print(f"  true (full signature) : {true_cat}  '{L[str(true_cat)]}'")

    # --- NOWCAST the held-out site ---
    rf, cols, q = build_now(df, train)
    ev = df[df.site_id == site_id].copy()

    def score(cat_used, tag):
        e = ev.copy()
        for j in range(3): e[f"cat_{j}"] = 1.0 if j == cat_used else 0.0
        p = rf.predict(e[cols]); y = e.pm2_5.values
        ss = ((y - p) ** 2).sum(); st = ((y - y.mean()) ** 2).sum(); r2 = 1 - ss / st
        pb = np.array([tier(v) for v in p]); yb = np.array([tier(v) for v in y])
        ex = (pb == yb).mean(); w1 = (np.abs(pb - yb) <= 1).mean()
        print(f"  {tag:<34} R²={r2:5.3f} | tier-exact={ex:5.3f} | within-1={w1:5.3f}")
        return p, y, r2

    print("\n[ NOWCAST — PM2.5 today (held-out, honest) ]")
    ev_pred, ev_true, r2_geo = score(cat_geo, "zero-deploy (geodata category)")
    score(cat_win, "short-deploy (60-day category)")
    score(true_cat, "best-case (true category)")
    print(f"  conformal half-width  ±{q:.1f} µg/m³  (≈90% group-conformal band)")

    # danger-dial sweep on the held-out site (planner operating point)
    yb = np.array([tier(v) for v in ev_true]); is_dang = yb == 2
    print("\n[ DANGER DIAL — recall vs false-alarm at the held-out site ]")
    if is_dang.sum() > 0:
        for cut in [55.4, 50, 45, 40]:
            flag = ev_pred > cut
            rec = (flag & is_dang).sum() / max(1, is_dang.sum())
            far = (flag & ~is_dang).sum() / max(1, (~is_dang).sum())
            mark = "  <- suggested" if cut == 45 else ""
            print(f"  alert if >{cut:>5} µg/m³ : dangerous-recall={rec:4.2f}  false-alarm={far:4.2f}{mark}")
    else:
        print("  (this site has no Dangerous-tier days — danger dial not exercised here)")

    # example single-day card
    i = len(ev) // 2; v = ev_pred[i]
    print("\n[ EXAMPLE CARD — one day, what the planner sees ]")
    print(f"  {ev.day.iloc[i].date()}:  predicted {v:.1f} µg/m³  ->  tier '{tname(v)}'  "
          f"band [{max(0, v - q):.0f}, {v + q:.0f}]  | danger-dial@45: {'ALERT' if v > 45 else 'ok'}  "
          f"| actual {ev_true[i]:.1f} ('{tname(ev_true[i])}')")

    # --- FORECAST +1..7 from a robust anchor (short-deploy) ---
    fm, ffeats = build_future(df, train)
    anchor = pick_anchor(df, site_id, ffeats)
    fc = forecast_site(fm, ffeats, df, site_id, anchor) if anchor is not None else None
    fdays, fvals, facts = [], [], []
    if fc:
        print(f"\n[ FORECAST +1..+7 days from {pd.Timestamp(anchor).date()} (short-deploy lags) ]")
        ser = df[df.site_id == site_id].set_index('day').pm2_5
        for h in range(1, 8):
            d = pd.Timestamp(anchor) + pd.Timedelta(days=h); pv = fc[h]; act = ser.get(d, np.nan)
            fdays.append(d); fvals.append(pv); facts.append(act)
            print(f"  +{h}d {d.date()}: {pv:5.1f} µg/m³ -> '{tname(pv)}'"
                  + (f"  | actual {act:.1f} ('{tname(act)}')" if not np.isnan(act) else "  | actual n/a"))
        print("  (production forecaster = the locked LSTM, +1d 0.51 -> +7d 0.43; this LightGBM-on-lags is the portable demo)")
    else:
        print("\n[ FORECAST ] no clean anchor with full lags for this site — forecast skipped.")

    # --- figure: nowcast series + the 7-day forecast vs actual, EPA tier shading + conformal ribbon ---
    fig, ax = plt.subplots(figsize=(11, 4.4))
    dd = ev.sort_values('day')
    ax.axhspan(0, 35.4, color='#46c98a', alpha=.10); ax.axhspan(35.4, 55.4, color='#e3b34e', alpha=.10); ax.axhspan(55.4, 220, color='#ec5a4c', alpha=.10)
    ax.plot(dd.day, dd.pm2_5, color='#9aa0a6', lw=1, label='actual PM2.5')
    e2 = dd.copy()
    for j in range(3): e2[f"cat_{j}"] = 1.0 if j == cat_geo else 0.0
    pred_sorted = rf.predict(e2[cols])
    ax.plot(dd.day, pred_sorted, color='#14A38B', lw=1.5, label='nowcast (held-out)')
    ax.fill_between(dd.day, np.clip(pred_sorted - q, 0, None), pred_sorted + q, color='#14A38B', alpha=.15, label='≈90% band')
    if fc:
        ax.plot(fdays, fvals, 'o-', color='#E8A020', lw=1.6, ms=5, label='+1…+7d forecast', zorder=5)
        av = [a for a in facts if not np.isnan(a)]; ad = [d for d, a in zip(fdays, facts) if not np.isnan(a)]
        if av: ax.plot(ad, av, 'x', color='#0D1B2A', ms=7, mew=2, label='forecast actual', zorder=6)
    ax.set_title(f"New-site demo — {site_id}: held-out nowcast + 7-day forecast vs actual (EPA tier shading)")
    ax.set_ylabel("PM2.5 µg/m³"); ax.legend(fontsize=8, ncol=5, loc='upper right'); ax.grid(alpha=.3)
    fig.tight_layout(); figpath = os.path.join(OUT, f"fig_newsite_demo{suffix}.png")
    fig.savefig(figpath, dpi=130); plt.close(fig)
    out = pd.DataFrame({"day": dd.day.values, "actual": dd.pm2_5.values, "nowcast": pred_sorted,
                        "band_lo": np.clip(pred_sorted - q, 0, None), "band_hi": pred_sorted + q,
                        "pred_tier": [tname(v) for v in pred_sorted], "actual_tier": [tname(v) for v in dd.pm2_5.values]})
    csvpath = os.path.join(OUT, f"newsite_demo{suffix}.csv"); out.to_csv(csvpath, index=False)
    print(f"\nwrote {os.path.relpath(figpath, F.HERE)} · {os.path.relpath(csvpath, F.HERE)}")
    return dict(site=site_id, r2_zero_deploy=round(r2_geo, 3), conformal_q=round(q, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", default="site_135")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--worst", action="store_true", help="run the highest-pollution site instead")
    a = ap.parse_args()
    site = a.demo
    if a.worst:
        d = F.load(); site = d.groupby("site_id").pm2_5.mean().idxmax()
        print(f"(highest-pollution site = {site})")
    demo(site, suffix=a.suffix)
