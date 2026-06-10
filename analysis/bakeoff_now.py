#!/usr/bin/env python3
"""
bakeoff_now.py — CP-D (NOW metric): model bake-off on the HONEST new-site test.

Per STRATEGY 3.4, four tabular learners compete to nowcast a sensor-less site:
  XGBoost · RandomForest · LightGBM(+split-conformal intervals) · CatBoost(native categorical).
Every model is scored on the SAME honest test = leave-sites-out (GroupKFold5), with random
80/20 reported alongside only as the leaky reference. Reality check (STRATEGY 3.4 / Adjei 2026):
the model is rarely the bottleneck — expect models to cluster; features + architecture move R².

Feature set = the routing that CP-B picked (default +cat+prior: weather+loc+cal+eng + category
one-hot + leak-free cat x month PM2.5 prior + weather anomalies). Category priors are fit INSIDE
each fold on train only (leak-safe). CatBoost additionally gets site_category as a NATIVE
categorical (ordered boosting -> the target-leak-resistant encoding; Prokhorenkova 2018).

Conformal intervals (LightGBM): split-conformal absolute-residual bands (Lei et al. 2018,
"Distribution-Free Predictive Inference for Regression", https://arxiv.org/abs/1604.04173).
We deliberately calibrate on held-out *rows* but test on held-out *sites* and report the
coverage gap — exchangeability breaks across sites, and that gap is itself a finding.

Outputs -> results/bakeoff_now.csv, results/fig_bakeoff_now.png
Run: ../../../working/.venv/bin/python bakeoff_now.py
"""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import xgboost as xgb, lightgbm as lgb
from catboost import CatBoostRegressor
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
ROUTING = "+cat"     # CP-B's locked pick: category one-hot, NO prior (prior hurt under noise)

def build(tr, ev, with_cat=True, with_prior=False):
    """Return (Xtr, ytr, Xev, yev, cols) with leak-safe per-fold features.
    CP-B locked routing = category one-hot, no prior; with_prior kept for the ablation only."""
    tr, ev = tr.copy(), ev.copy()
    cols = list(F.BASE_NOW)
    if with_cat:
        for c in range(3):
            tr[f"cat_{c}"] = (tr.site_category == c).astype(float)
            ev[f"cat_{c}"] = (ev.site_category == c).astype(float)
            cols.append(f"cat_{c}")
        if with_prior:
            tr, ev, newc = F.add_category_priors(tr, ev); cols += newc
    return tr[cols].values, tr.pm2_5.values, ev[cols].values, ev.pm2_5.values, cols

MODELS = {
    "XGBoost":      lambda: xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
                              subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED),
    "RandomForest": lambda: RandomForestRegressor(n_estimators=400, max_depth=30,
                              max_features="sqrt", n_jobs=-1, random_state=SEED),
    "LightGBM":     lambda: lgb.LGBMRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
                              subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1),
    "CatBoost":     lambda: CatBoostRegressor(iterations=600, depth=6, learning_rate=0.05,
                              random_seed=SEED, verbose=0),
}

def paired_site_test(df, folds, n_boot=5000):
    """Per-SITE RMSE for blind-XGB vs +cat-XGB across the leave-sites-out folds, then a paired
    bootstrap CI + sign count. Tests whether the +cat lift is real or just fold noise (CP-B caveat)."""
    recs = []
    for tr_i, ev_i in folds:
        tr, ev = df.iloc[tr_i], df.iloc[ev_i]
        Xb, yb, Xeb, yev, _ = build(tr, ev, with_cat=False)
        Xc, yc, Xec, _, _ = build(tr, ev, with_cat=True)
        mb = MODELS["XGBoost"](); mb.fit(Xb, yb); pb = mb.predict(Xeb)
        mc = MODELS["XGBoost"](); mc.fit(Xc, yc); pc = mc.predict(Xec)
        ev = ev.copy(); ev["pb"] = pb; ev["pc"] = pc
        for sid, g in ev.groupby("site_id"):
            rb = float(np.sqrt(np.mean((g.pm2_5 - g.pb) ** 2)))
            rc = float(np.sqrt(np.mean((g.pm2_5 - g.pc) ** 2)))
            recs.append((sid, rb, rc, rb - rc))   # delta>0 => +cat better
    d = np.array([r[3] for r in recs])
    rng = np.random.default_rng(SEED)
    boot = np.array([rng.choice(d, len(d), replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    improved = int((d > 0).sum())
    print(f"\n--- paired per-site test: blind vs +cat (RMSE reduction, n={len(d)} sites) ---")
    print(f"  mean RMSE reduction = {d.mean():+.2f} µg/m³  95% CI [{lo:+.2f}, {hi:+.2f}]  "
          f"| {improved}/{len(d)} sites improved")
    sig = "significant (CI excludes 0)" if lo > 0 else "not significant"
    print(f"  -> {sig}")
    return dict(mean_rmse_reduction=round(float(d.mean()), 3), ci_lo=round(float(lo), 3),
                ci_hi=round(float(hi), 3), sites_improved=improved, n_sites=len(d), verdict=sig)

def main():
    df = F.load(); cat = F.load_categorizer()
    df["site_category"] = df.site_id.map(F.assign_full_categories(df, cat))
    gkf = GroupKFold(5); folds = list(gkf.split(df, df.pm2_5.values, df.site_id.values))
    idx = np.arange(len(df))
    rows = []

    for name, mk in MODELS.items():
        # honest new-site
        ns = []
        for tr_i, ev_i in folds:
            Xtr, ytr, Xev, yev, cols = build(df.iloc[tr_i], df.iloc[ev_i])
            m = mk(); m.fit(Xtr, ytr); ns.append(r2_score(yev, m.predict(Xev)))
        # leaky random (reference)
        rnd = []
        for s in range(5):
            tr_i, ev_i = train_test_split(idx, test_size=0.2, random_state=s)
            Xtr, ytr, Xev, yev, cols = build(df.iloc[tr_i], df.iloc[ev_i])
            m = mk(); m.fit(Xtr, ytr); rnd.append(r2_score(yev, m.predict(Xev)))
        rows.append(dict(model=name, routing=ROUTING,
                         newsite_r2=round(float(np.mean(ns)), 4), newsite_std=round(float(np.std(ns)), 4),
                         random_r2=round(float(np.mean(rnd)), 4),
                         folds=str([round(x, 3) for x in ns])))
        print(f"{name:13s} new-site R2 = {np.mean(ns):.4f} ± {np.std(ns):.3f}   (random {np.mean(rnd):.4f})   folds={[round(x,3) for x in ns]}")

    # blind XGB anchor (no category) on new-site
    ns = []
    for tr_i, ev_i in folds:
        Xtr, ytr, Xev, yev, cols = build(df.iloc[tr_i], df.iloc[ev_i], with_cat=False)
        m = MODELS["XGBoost"](); m.fit(Xtr, ytr); ns.append(r2_score(yev, m.predict(Xev)))
    rows.append(dict(model="XGBoost(blind)", routing="blind",
                     newsite_r2=round(float(np.mean(ns)), 4), newsite_std=round(float(np.std(ns)), 4),
                     random_r2=np.nan, folds=str([round(x, 3) for x in ns])))
    print(f"{'XGB(blind)':13s} new-site R2 = {np.mean(ns):.4f} ± {np.std(ns):.3f}   (anchor baseline)")

    # ---- LightGBM split-conformal intervals on the new-site test ----
    print("\n--- LightGBM split-conformal 90% intervals (honest new-site) ---")
    alpha = 0.1; covs, widths = [], []
    for tr_i, ev_i in folds:
        tr, ev = df.iloc[tr_i], df.iloc[ev_i]
        Xtr, ytr, Xev, yev, cols = build(tr, ev)
        # split train rows -> proper-train + calibration
        pt, cal = train_test_split(np.arange(len(Xtr)), test_size=0.3, random_state=SEED)
        m = MODELS["LightGBM"](); m.fit(Xtr[pt], ytr[pt])
        resid = np.abs(ytr[cal] - m.predict(Xtr[cal]))
        q = np.quantile(resid, np.ceil((len(cal) + 1) * (1 - alpha)) / len(cal))
        pred = m.predict(Xev)
        lo, hi = pred - q, pred + q
        covs.append(float(np.mean((yev >= lo) & (yev <= hi)))); widths.append(float(2 * q))
    print(f"  target coverage 90%  ->  empirical {np.mean(covs)*100:.1f}%   mean width {np.mean(widths):.1f} µg/m³")
    print(f"  (gap below 90% = exchangeability breaking across unseen sites — an honest caveat)")
    rows.append(dict(model="LightGBM-conformal90", routing=ROUTING, newsite_r2=np.nan, newsite_std=np.nan,
                     random_r2=np.nan, folds=f"coverage={np.mean(covs)*100:.1f}% width={np.mean(widths):.1f}"))

    # ---- is the +cat lift real or fold noise? paired per-site bootstrap ----
    pt = paired_site_test(df, folds)
    rows.append(dict(model="paired_blind_vs_cat", routing="XGBoost", newsite_r2=np.nan, newsite_std=np.nan,
                     random_r2=np.nan, folds=f"meanRMSEred={pt['mean_rmse_reduction']} CI[{pt['ci_lo']},{pt['ci_hi']}] "
                     f"{pt['sites_improved']}/{pt['n_sites']} {pt['verdict']}"))

    res = pd.DataFrame(rows); res.to_csv(os.path.join(OUT, "bakeoff_now.csv"), index=False)

    # ---- figure ----
    plot = res[res.model.isin(list(MODELS) + ["XGBoost(blind)"])].copy()
    fig, ax = plt.subplots(figsize=(8, 4.4))
    order = plot.sort_values("newsite_r2")
    bars = ax.barh(order.model, order.newsite_r2, xerr=order.newsite_std, color="#14A38B",
                   error_kw=dict(ecolor="#555", lw=1))
    blind_v = res[res.model == "XGBoost(blind)"].newsite_r2.iloc[0]
    ax.axvline(blind_v, ls="--", color="#d43030", lw=1.2, label=f"blind XGB anchor ({blind_v:.3f})")
    ax.set_xlabel("new-site R² (leave-sites-out, GroupKFold5)")
    ax.set_title("NOW bake-off — honest new-site generalization"); ax.legend(fontsize=8); ax.grid(axis="x", alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_bakeoff_now.png"), dpi=130); plt.close(fig)
    print(f"\nwrote results/bakeoff_now.csv · results/fig_bakeoff_now.png")

if __name__ == "__main__":
    main()
