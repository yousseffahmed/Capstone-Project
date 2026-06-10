#!/usr/bin/env python3
"""
investigate_categorization.py — why did the ZERO-DEPLOY categorizer mislabel site_54,
and can we improve the blind (sensor-less) category guess + the downstream nowcast?

Crimson's questions:
  (1) exact inputs to categorize a site
  (2) why don't we use more features than geodata for the blind category guess
  (3) what distinguishes site_54 from its true-category peers — what misled it
  (4) can we fix the blind categorization and use it to better train the final model

Two distinct objects (kept separate end to end):
  TRUE categorizer  : 8-feature behavioural SIGNATURE -> nearest centroid (needs observed PM2.5).
  BLIND category    : guess that category for a SENSOR-LESS site from only zero-deploy inputs.
                      4th-cap used geodata-only (5 feats) -> LOO acc 0.54 (< 0.62 majority). This
                      is the one that mislabeled site_54.

Zero-deploy inputs available WITHOUT a sensor: geodata (5) + ERA5 climate means (4).
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneGroupOut
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
np.set_printoptions(suppress=True)

df  = F.load()
CAT = F.load_categorizer()
LAB = CAT["cluster_labels"]
full = F.assign_full_categories(df, CAT)              # {site: TRUE category from full signature}
EXT  = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]

# ---- per-site zero-deploy feature table: geodata (5) + ERA5 climate means (4) ----
clim = df.groupby("site_id").apply(lambda g: pd.Series({
    "temp_mean":      g.temp_2m_K.mean() - 273.15,
    "humidity_mean":  g.rel_humidity.mean(),
    "windspeed_mean": g.wind_speed.mean(),
    "precip_mean":    g.precipitation_m.mean() * 1000,
})).reset_index()
CLIMF = ["temp_mean", "humidity_mean", "windspeed_mean", "precip_mean"]

tbl = EXT.merge(clim, on="site_id")
tbl["cat"] = tbl.site_id.map(full)
tbl["pm25_mean"] = tbl.site_id.map(df.groupby("site_id").pm2_5.mean())
tbl["pm25_p90"]  = tbl.site_id.map(df.groupby("site_id").pm2_5.quantile(0.90))
tbl = tbl.sort_values("site_id").reset_index(drop=True)
sites = tbl.site_id.values
y = tbl.cat.values

print("="*86)
print("CATEGORY SIZES (true, full-signature):", pd.Series(y).value_counts().sort_index().to_dict(),
      "| labels:", {int(k): v for k, v in LAB.items()})
print("="*86)

# =====================================================================================
# 1 — BLIND categorizer LOO accuracy: geodata-only vs +climate vs models
# =====================================================================================
def loo_preds(X, model_fn):
    logo = LeaveOneGroupOut(); pred = np.empty(len(y), int); proba = np.zeros((len(y), 3))
    for tr, te in logo.split(X, y, sites):
        m = model_fn().fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
        if hasattr(m, "predict_proba"):
            pr = m.predict_proba(X[te]);
            for j, c in enumerate(m.classes_): proba[te, c] = pr[:, j]
    return pred, proba

def scaled(cols):
    return StandardScaler().fit_transform(tbl[cols].values)

rf  = lambda: RandomForestClassifier(n_estimators=300, random_state=SEED)
knn = lambda: KNeighborsClassifier(n_neighbors=5)
logr= lambda: LogisticRegression(max_iter=1000, multi_class="multinomial")

feature_sets = {
    "geodata only (5) — 4th-cap blind": EXTF,
    "climate only (4)":                 CLIMF,
    "geodata + climate (9)":            EXTF + CLIMF,
}
maj = pd.Series(y).value_counts().max() / len(y)
print(f"\n[1] BLIND categorizer — leave-one-site-out accuracy (majority baseline = {maj:.3f})")
results = {}
for name, cols in feature_sets.items():
    X = scaled(cols)
    for mname, mfn in [("RF", rf), ("kNN", knn), ("logreg", logr)]:
        pred, proba = loo_preds(X, mfn)
        acc = (pred == y).mean()
        results[(name, mname)] = (pred, proba, acc)
        flag = "  <-- best so far" if acc == max(a for *_, a in results.values()) else ""
        print(f"   {name:34s} {mname:7s} acc={acc:.3f}{flag}")

# pick the best blind feature set/model
best_key = max(results, key=lambda k: results[k][2])
best_pred, best_proba, best_acc = results[best_key]
print(f"   BEST blind config: {best_key} -> acc {best_acc:.3f}")

# =====================================================================================
# 2 — DIAGNOSIS: site_54 — what misled it
# =====================================================================================
S = "site_54"; si = list(sites).index(S)
true_c = y[si]
geo_pred = results[("geodata only (5) — 4th-cap blind", "RF")][0][si]
print("\n" + "="*86)
print(f"[2] DIAGNOSIS — {S}: TRUE cat {true_c} '{LAB[str(true_c)]}' | geodata-RF predicted {geo_pred} '{LAB[str(geo_pred)]}'")
print("="*86)
allF = EXTF + CLIMF + ["pm25_mean", "pm25_p90"]
means = tbl.groupby("cat")[allF].mean()
row = tbl.loc[si, allF]
print(f"   {'feature':22s} {S:>11s} | cat0_mean cat1_mean cat2_mean | nearest-cat-by-feature")
for f in allF:
    vals = means[f]
    nearest = int((vals - row[f]).abs().idxmin())
    star = "  <-- points to WRONG cat" if (nearest == geo_pred and true_c != geo_pred and f in EXTF) else ""
    print(f"   {f:22s} {row[f]:11.1f} | {vals[0]:9.1f} {vals[1]:9.1f} {vals[2]:9.1f} | cat{nearest}{star}")

# which geodata features push toward the wrong cat0 vs the true cat1?
print(f"\n   Read: {S} truly is cat{true_c} (high-pollution). For each GEODATA feature, is its value")
print(f"   more like cat{true_c} (true) or cat{geo_pred} (predicted)?")
for f in EXTF:
    d_true = abs(row[f] - means.loc[true_c, f]); d_pred = abs(row[f] - means.loc[geo_pred, f])
    verdict = f"looks like cat{geo_pred} (misleading)" if d_pred < d_true else f"looks like cat{true_c} (correct signal)"
    print(f"     {f:22s} -> {verdict}")

# nearest geodata neighbours of site_54 and their true categories
Xg = scaled(EXTF)
dists = np.sqrt(((Xg - Xg[si])**2).sum(1))
order = np.argsort(dists)[1:7]
print(f"\n   6 nearest GEODATA neighbours of {S} (and their TRUE category):")
for o in order:
    print(f"     {sites[o]:10s} dist={dists[o]:.2f}  true cat{y[o]} '{LAB[str(y[o])]}'  pm25_mean={tbl.pm25_mean[o]:.1f}")

# =====================================================================================
# 3 — CAN ANY ZERO-DEPLOY FEATURE SEPARATE cat0 (low) FROM cat1 (high)?
#     (the site_54 error is a LEVEL error; climate is identical across 0/1 by design)
# =====================================================================================
print("\n" + "="*86)
print("[3] Which zero-deploy feature actually tracks pollution LEVEL (cat0 low vs cat1 high)?")
print("="*86)
m01 = tbl[tbl.cat.isin([0, 1])]
print(f"   Point-biserial corr of each zero-deploy feature with pm25_mean (n={len(m01)} cat0/1 sites):")
corrs = {f: np.corrcoef(m01[f], m01.pm25_mean)[0, 1] for f in EXTF + CLIMF}
for f, c in sorted(corrs.items(), key=lambda kv: -abs(kv[1])):
    print(f"     {f:22s} r = {c:+.3f}")
best_geo = max(EXTF, key=lambda f: abs(corrs[f]))
print(f"   -> strongest single zero-deploy level signal: {best_geo} (r={corrs[best_geo]:+.3f})")

# =====================================================================================
# 4 — DOES A BETTER CATEGORY STRATEGY IMPROVE THE HONEST NEW-SITE NOWCAST?
#     Compare, leave-sites-out, the nowcast under different category strategies.
# =====================================================================================
print("\n" + "="*86)
print("[4] Honest new-site NOWCAST R² under different category strategies (leave-sites-out)")
print("="*86)
from sklearn.ensemble import RandomForestRegressor
# attach geodata to the row-level frame
d = df.merge(EXT, on="site_id", how="left")
fullmap = full
d["true_cat"] = d.site_id.map(fullmap)
RFKW = dict(n_estimators=300, max_depth=30, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)
cols_base = list(F.BASE_NOW) + EXTF

def newsite_r2(cat_strategy):
    """cat_strategy: 'none' | 'true' | 'geo_hard' | 'geo_soft' | 'best_hard' | 'best_soft'."""
    logo = LeaveOneGroupOut(); per = []
    site_arr = d.site_id.values
    for tr_idx, te_idx in logo.split(d, groups=site_arr):
        tr = d.iloc[tr_idx].copy(); te = d.iloc[te_idx].copy()
        te_site = te.site_id.iloc[0]
        cols = list(cols_base)
        if cat_strategy != "none":
            # build train one-hots from TRUE categories (we observe training sites fully)
            for j in range(3):
                tr[f"c{j}"] = (tr.true_cat == j).astype(float)
            # eval site's category one-hot depends on strategy
            if cat_strategy == "true":
                cj = fullmap[te_site]; oh = [1.0 if j == cj else 0.0 for j in range(3)]
            else:
                # fit the blind categorizer on TRAIN sites only, predict the eval site
                tr_sites = sorted(set(tr.site_id))
                sub = tbl[tbl.site_id.isin(tr_sites)]
                if cat_strategy.startswith("geo"):  fcols = EXTF
                else:                                fcols = EXTF + CLIMF      # 'best'
                sc = StandardScaler().fit(sub[fcols].values)
                clf = RandomForestClassifier(n_estimators=300, random_state=SEED).fit(sc.transform(sub[fcols].values), sub.cat.values)
                ev = tbl[tbl.site_id == te_site]
                if cat_strategy.endswith("soft"):
                    pr = clf.predict_proba(sc.transform(ev[fcols].values))[0]
                    oh = [0.0, 0.0, 0.0]
                    for k, c in enumerate(clf.classes_): oh[c] = pr[k]
                else:
                    cj = int(clf.predict(sc.transform(ev[fcols].values))[0]); oh = [1.0 if j == cj else 0.0 for j in range(3)]
            for j in range(3): te[f"c{j}"] = oh[j]
            cols = cols + ["c0", "c1", "c2"]
        m = RandomForestRegressor(**RFKW).fit(tr[cols], tr.pm2_5.values)
        p = m.predict(te[cols]); a = te.pm2_5.values
        ss = ((a - p)**2).sum(); st = ((a - a.mean())**2).sum()
        per.append((te_site, 1 - ss/st))
    arr = np.array([r for _, r in per]);
    s54 = dict(per).get(S, np.nan)
    return arr.mean(), arr.std(), s54

print(f"   {'strategy':>12s}  mean R²   std    site_54 R²")
for strat in ["none", "geo_hard", "geo_soft", "best_hard", "best_soft", "true"]:
    mean, sd, s54 = newsite_r2(strat)
    tag = {"none":"no category","geo_hard":"geodata hard 1-hot (4th-cap)","geo_soft":"geodata soft probs",
           "best_hard":"geo+climate hard","best_soft":"geo+climate soft","true":"true category (oracle)"}[strat]
    print(f"   {strat:>12s}  {mean:6.3f}  {sd:5.3f}  {s54:8.3f}   {tag}")

# =====================================================================================
# 5 — SUMMARY OUT
# =====================================================================================
summ = {
    "blind_acc_geodata_only": float(results[("geodata only (5) — 4th-cap blind", "RF")][2]),
    "blind_acc_best": float(best_acc), "blind_best_config": str(best_key),
    "site54_true_cat": int(true_c), "site54_geodata_pred": int(geo_pred),
    "best_level_signal": best_geo, "best_level_corr": float(corrs[best_geo]),
}
json.dump(summ, open(os.path.join(OUT, "categorization_investigation.json"), "w"), indent=2)
print("\nwrote results/categorization_investigation.json")
print("\nDONE.")
