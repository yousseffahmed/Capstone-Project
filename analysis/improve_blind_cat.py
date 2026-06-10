#!/usr/bin/env python3
"""
improve_blind_cat.py — validate the blind-categorizer improvement (RF->kNN) end to end, on the
SAME honest protocol as the headline (GroupKFold-5, +category+geodata nowcast). Question: does a
better zero-deploy category GUESS lift the sensor-less nowcast? Reports mean new-site R² + site_54.
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EDGES = [35.4, 55.4]
def tier(x): return int(np.clip(np.digitize([x], EDGES)[0], 0, 2))

df  = F.load(); CAT = F.load_categorizer()
full = F.assign_full_categories(df, CAT)
EXT  = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]
clim = df.groupby("site_id").apply(lambda g: pd.Series({
    "temp_mean": g.temp_2m_K.mean()-273.15, "humidity_mean": g.rel_humidity.mean(),
    "windspeed_mean": g.wind_speed.mean(), "precip_mean": g.precipitation_m.mean()*1000})).reset_index()
CLIMF = ["temp_mean","humidity_mean","windspeed_mean","precip_mean"]
per = EXT.merge(clim, on="site_id"); per["cat"] = per.site_id.map(full)
per = per.set_index("site_id")

d = df.merge(EXT, on="site_id", how="left"); d["true_cat"] = d.site_id.map(full)
RFKW = dict(n_estimators=400, max_depth=30, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)
cols_base = list(F.BASE_NOW) + EXTF
sites = sorted(full); site_arr = d.site_id.values

def blind_clf(kind, train_sites, fcols):
    sub = per.loc[[s for s in train_sites if s in per.index]]
    sc = StandardScaler().fit(sub[fcols].values)
    if kind == "rf":  m = RandomForestClassifier(n_estimators=300, random_state=SEED)
    else:             m = KNeighborsClassifier(n_neighbors=5)
    m.fit(sc.transform(sub[fcols].values), sub.cat.values)
    return lambda s: int(m.predict(sc.transform(per.loc[[s]][fcols].values))[0])

def run(strategy):
    """strategy in: none, geo_rf, geo_knn, geoclim_knn, true."""
    gkf = GroupKFold(5); per_site = {}
    for tr_idx, te_idx in gkf.split(d, groups=site_arr):
        tr = d.iloc[tr_idx].copy(); te = d.iloc[te_idx].copy()
        tr_sites = sorted(set(tr.site_id)); te_sites = sorted(set(te.site_id))
        cols = list(cols_base)
        if strategy != "none":
            for j in range(3): tr[f"c{j}"] = (tr.true_cat == j).astype(float)
            if strategy == "true":
                catf = lambda s: full[s]
            elif strategy == "geo_rf":     catf = blind_clf("rf",  tr_sites, EXTF)
            elif strategy == "geo_knn":    catf = blind_clf("knn", tr_sites, EXTF)
            elif strategy == "geoclim_knn":catf = blind_clf("knn", tr_sites, EXTF+CLIMF)
            cmap = {s: catf(s) for s in te_sites}
            for j in range(3): te[f"c{j}"] = te.site_id.map(lambda s: 1.0 if cmap[s] == j else 0.0)
            cols += ["c0","c1","c2"]
        m = RandomForestRegressor(**RFKW).fit(tr[cols], tr.pm2_5.values)
        for s in te_sites:
            e = te[te.site_id == s]; p = m.predict(e[cols]); a = e.pm2_5.values
            ss=((a-p)**2).sum(); st=((a-a.mean())**2).sum()
            pb=np.array([tier(v) for v in p]); ab=np.array([tier(v) for v in a])
            per_site[s] = dict(r2=1-ss/st, tier_exact=(pb==ab).mean(), within1=(np.abs(pb-ab)<=1).mean())
    r2 = np.array([v["r2"] for v in per_site.values()])
    te_ex = np.mean([v["tier_exact"] for v in per_site.values()])
    return dict(meanR2=float(r2.mean()), medR2=float(np.median(r2)), tier_exact=float(te_ex),
                site54_r2=float(per_site["site_54"]["r2"]), site54_tier=float(per_site["site_54"]["tier_exact"]))

print("Honest sensor-less nowcast (GroupKFold-5, RF +geodata + blind category) by category strategy:")
print(f"  {'strategy':>13s}  meanR²  medR²  tier-exact | site_54 R²  site_54 tier")
rows={}
for strat in ["none","geo_rf","geo_knn","geoclim_knn","true"]:
    r = run(strat); rows[strat]=r
    tag={"none":"no category","geo_rf":"geodata->RF (4th-cap blind)","geo_knn":"geodata->kNN (improved)",
         "geoclim_knn":"geo+climate->kNN","true":"observed category (oracle)"}[strat]
    print(f"  {strat:>13s}  {r['meanR2']:6.3f} {r['medR2']:6.3f}   {r['tier_exact']:.3f}    | {r['site54_r2']:8.3f}    {r['site54_tier']:.3f}   {tag}")
json.dump(rows, open(os.path.join(OUT,"improve_blind_cat.json"),"w"), indent=2)
print("\nwrote results/improve_blind_cat.json")
