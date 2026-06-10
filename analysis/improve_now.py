#!/usr/bin/env python3
"""
improve_now.py — 4th-cap NEXT round (NOW): can we beat new-site R² 0.547?
LEVER 1 category-count (k) sweep scored by HONEST new-site R² (not silhouette).
LEVER 2 stacking (RF+XGB+LGBM base -> ridge meta, out-of-fold) on +cat+external.
Honest leave-sites-out (GroupKFold5) throughout; pm10/n_obs banned; Tier-A categories
(comparable to the 0.465/0.547 baseline) + a fold-safe variant to prove it isn't a categorizer leak.
"""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import xgboost as xgb, lightgbm as lgb
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EXT = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]

def site_signatures(df):
    return pd.DataFrame({sid: F.site_signature(g) for sid, g in df.groupby("site_id")}).T

def mk_xgb(): return xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED)
def mk_rf():  return RandomForestRegressor(n_estimators=400, max_depth=30, max_features="sqrt",
            n_jobs=-1, random_state=SEED)
def mk_lgb(): return lgb.LGBMRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1)

def assign_full(sig, scaler, centroids, feats):
    Xs = scaler.transform(sig[feats].values)
    lab = np.argmin(((Xs[:, None, :] - centroids[None, :, :]) ** 2).sum(2), axis=1)
    return dict(zip(sig.index, lab))

def assign_foldsafe(sig, feats, k, train_sites):
    tr = sig.loc[sig.index.isin(train_sites)]
    sc = StandardScaler().fit(tr[feats].values)
    km = KMeans(n_clusters=k, n_init=25, random_state=SEED).fit(sc.transform(tr[feats].values))
    Xs = sc.transform(sig[feats].values)
    lab = np.argmin(((Xs[:, None, :] - km.cluster_centers_[None, :, :]) ** 2).sum(2), axis=1)
    return dict(zip(sig.index, lab))

def onehot(d, k):
    for c in range(k):
        d[f"cat_{c}"] = (d.site_category == c).astype(float)
    return d, [f"cat_{c}" for c in range(k)]

def newsite_r2(df, folds, base_cols, k, sig, feats, model_fn, with_ext, foldsafe=False,
               scaler=None, centroids=None):
    sc = []
    for tr_i, ev_i in folds:
        tr, ev = df.iloc[tr_i].copy(), df.iloc[ev_i].copy()
        lab = assign_foldsafe(sig, feats, k, set(tr.site_id.unique())) if foldsafe \
              else assign_full(sig, scaler, centroids, feats)
        tr["site_category"] = tr.site_id.map(lab); ev["site_category"] = ev.site_id.map(lab)
        tr, catcols = onehot(tr, k); ev, _ = onehot(ev, k)
        cols = list(base_cols) + catcols + (EXTF if with_ext else [])
        m = model_fn(); m.fit(tr[cols].values, tr.pm2_5.values)
        sc.append(r2_score(ev.pm2_5.values, m.predict(ev[cols].values)))
    return float(np.mean(sc)), float(np.std(sc))

def stacked_newsite(df, folds, base, EXTF, k, sig, scaler, centroids, feats):
    bases = {"rf": mk_rf, "xgb": mk_xgb, "lgb": mk_lgb}
    lab_full = assign_full(sig, scaler, centroids, feats)
    dd = df.copy(); dd["site_category"] = dd.site_id.map(lab_full)
    dd, catcols = onehot(dd, k); cols = list(base) + catcols + EXTF
    outer = []
    for tr_i, ev_i in folds:
        tr, ev = dd.iloc[tr_i], dd.iloc[ev_i]
        inner = GroupKFold(4); oof = {n: np.zeros(len(tr)) for n in bases}
        for itr, iev in inner.split(tr, tr.pm2_5.values, tr.site_id.values):
            for n, fn in bases.items():
                m = fn(); m.fit(tr.iloc[itr][cols].values, tr.iloc[itr].pm2_5.values)
                oof[n][iev] = m.predict(tr.iloc[iev][cols].values)
        meta = Ridge(alpha=1.0).fit(np.column_stack([oof[n] for n in bases]), tr.pm2_5.values)
        preds = []
        for n, fn in bases.items():
            m = fn(); m.fit(tr[cols].values, tr.pm2_5.values); preds.append(m.predict(ev[cols].values))
        outer.append(r2_score(ev.pm2_5.values, meta.predict(np.column_stack(preds))))
    return float(np.mean(outer)), float(np.std(outer))

def main():
    df = F.load(); sig = site_signatures(df); feats = F.SIG_FEATS
    df = df.merge(EXT, on="site_id", how="left")
    folds = list(GroupKFold(5).split(df, df.pm2_5.values, df.site_id.values))
    base = F.BASE_NOW; rows = []
    print("="*70); print("LEVER 1 — category-count (k) sweep, by HONEST new-site R²"); print("="*70)
    for k in [2, 3, 4, 5, 6]:
        sc = StandardScaler().fit(sig[feats].values)
        km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(sc.transform(sig[feats].values))
        cen = km.cluster_centers_
        r_cat, s_cat   = newsite_r2(df, folds, base, k, sig, feats, mk_xgb, False, scaler=sc, centroids=cen)
        r_ext, s_ext   = newsite_r2(df, folds, base, k, sig, feats, mk_xgb, True,  scaler=sc, centroids=cen)
        r_safe, s_safe = newsite_r2(df, folds, base, k, sig, feats, mk_xgb, False, foldsafe=True)
        sizes = np.bincount(km.labels_, minlength=k).tolist()
        rows.append(dict(lever="k_sweep", k=k, plus_cat=round(r_cat,4), plus_cat_std=round(s_cat,4),
                         plus_cat_ext=round(r_ext,4), plus_cat_ext_std=round(s_ext,4),
                         plus_cat_foldsafe=round(r_safe,4), sizes=str(sizes)))
        print(f"k={k} | +cat {r_cat:.4f}±{s_cat:.3f} | +cat+ext {r_ext:.4f}±{s_ext:.3f} | +cat(foldsafe) {r_safe:.4f}±{s_safe:.3f}  sizes={sizes}")
    sweep = pd.DataFrame([r for r in rows if r["lever"] == "k_sweep"])
    best_k = int(sweep.loc[sweep.plus_cat_ext.idxmax(), "k"])
    print(f"\n-> best k by honest +cat+external R² = {best_k} ({sweep.plus_cat_ext.max():.4f})")
    print("\n" + "="*70); print(f"LEVER 2 — stacking at k={best_k}, +cat+external"); print("="*70)
    sc = StandardScaler().fit(sig[feats].values)
    km = KMeans(n_clusters=best_k, n_init=50, random_state=SEED).fit(sc.transform(sig[feats].values))
    cen = km.cluster_centers_
    for n, fn in {"RandomForest": mk_rf, "XGBoost": mk_xgb, "LightGBM": mk_lgb}.items():
        r, s = newsite_r2(df, folds, base, best_k, sig, feats, fn, True, scaler=sc, centroids=cen)
        print(f"  single {n:13s} +cat+ext  R² = {r:.4f} ± {s:.3f}")
        rows.append(dict(lever="single_best_k", k=best_k, model=n, plus_cat_ext=round(r,4), plus_cat_ext_std=round(s,4)))
    r_stack, s_stack = stacked_newsite(df, folds, base, EXTF, best_k, sig, sc, cen, feats)
    print(f"  STACKED (rf+xgb+lgb -> ridge)  +cat+ext  R² = {r_stack:.4f} ± {s_stack:.3f}")
    rows.append(dict(lever="stacked", k=best_k, model="rf+xgb+lgb->ridge", plus_cat_ext=round(r_stack,4), plus_cat_ext_std=round(s_stack,4)))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "improve_now.csv"), index=False)
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ax.plot(sweep.k, sweep.plus_cat, "o-", color="#14A38B", lw=2, label="+cat")
    ax.plot(sweep.k, sweep.plus_cat_ext, "s-", color="#0E7C66", lw=2, label="+cat+external")
    ax.plot(sweep.k, sweep.plus_cat_foldsafe, "^--", color="#9aa0a6", lw=1.6, label="+cat (fold-safe)")
    ax.axhline(0.547, ls=":", color="#E8A020", label="4th-cap best (0.547)")
    ax.set_xlabel("k (site categories)"); ax.set_ylabel("honest new-site R² (GroupKFold5)")
    ax.set_title("NOW: does category count or stacking beat 0.547?"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_improve_now.png"), dpi=130); plt.close(fig)
    print("\nwrote results/improve_now.csv + results/fig_improve_now.png")

if __name__ == "__main__":
    main()
