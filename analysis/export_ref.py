#!/usr/bin/env python3
"""export_ref.py — compact reference data for the prototype's in-browser predictor:
per-site zero-deploy features (geodata 5 + climate 4) + category + level, plus scaler stats so the
input page can kNN-categorize and kNN-estimate a NEW location with no model files. Light/fast."""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import features as F

OUT = os.path.join(F.HERE, "results")
df = F.load(); CAT = F.load_categorizer(); full = F.assign_full_categories(df, CAT); LAB = CAT["cluster_labels"]
EXT = pd.read_csv(os.path.join(OUT, "external_features.csv")); GEOF=[c for c in EXT.columns if c!="site_id"]
clim = df.groupby("site_id").apply(lambda g: pd.Series({
    "temp_mean": g.temp_2m_K.mean()-273.15, "humidity_mean": g.rel_humidity.mean(),
    "windspeed_mean": g.wind_speed.mean(), "precip_mean": g.precipitation_m.mean()*1000})).reset_index()
CLIMF=["temp_mean","humidity_mean","windspeed_mean","precip_mean"]
mp = json.load(open(os.path.join(OUT,"map_predictions.json")))
now_by = {s["site"]: s["now"]["ugm3"] for s in mp["sites"]}

per = EXT.merge(clim, on="site_id")
per["cat"]=per.site_id.map(full); per["pm25_mean"]=per.site_id.map(df.groupby("site_id").pm2_5.mean())
feats = GEOF + CLIMF
mean = {f: float(per[f].mean()) for f in feats}; std = {f: float(per[f].std() or 1) for f in feats}
sites=[]
for _,r in per.iterrows():
    sites.append(dict(site=r["site_id"], cat=int(r["cat"]), cat_label=LAB[str(int(r["cat"]))],
        pm25_mean=round(float(r["pm25_mean"]),1), now_ugm3=round(float(now_by.get(r["site_id"], r["pm25_mean"])),1),
        geo={k: round(float(r[k]),1) for k in GEOF}, clim={k: round(float(r[k]),2) for k in CLIMF}))
out=dict(geo_feats=GEOF, clim_feats=CLIMF, mean=mean, std=std, k=5,
         danger_features=["rel_humidity","dewpoint_2m_K"],  # the danger-day weather regime
         categorizer={"features":CAT["features"],"scaler_mean":CAT["scaler_mean"],
                      "scaler_scale":CAT["scaler_scale"],"centroids":CAT["centroids"],"labels":LAB},
         sites=sites)
json.dump(out, open(os.path.join(OUT,"ref_sites.json"),"w"))
print(f"wrote results/ref_sites.json ({len(sites)} sites, {len(feats)} zero-deploy feats)")
