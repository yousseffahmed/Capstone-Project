#!/usr/bin/env python3
"""predict_testcases.py — enrich test_cases.json with the HONEST zero-deploy model prediction for
each case (RF on weather+location+geodata, NO category, the site held out) — the realistic
'new sensor-less location' scenario. Shows the model's real call vs the ground truth."""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EDGES = [35.4, 55.4]; TIERS = ["Elevated", "High", "Dangerous"]
def tname(x): return TIERS[int(np.clip(np.digitize([float(x)], EDGES)[0], 0, 2))]

df = F.load(); EXT = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]
d = df.merge(EXT, on="site_id", how="left")
COLS = list(F.BASE_NOW) + EXTF
RFKW = dict(n_estimators=400, max_depth=30, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)
tc = json.load(open(os.path.join(OUT, "test_cases.json")))
# group-conformal band (reuse the map band)
band = json.load(open(os.path.join(OUT, "map_predictions.json")))["band"]

for c in tc["cases"]:
    s = c["site"]; day = pd.Timestamp(c["date"])
    tr = d[d.site_id != s]
    m = RandomForestRegressor(**RFKW).fit(tr[COLS], tr.pm2_5.values)
    row = d[(d.site_id == s) & (d.day == day)][COLS]
    pred = float(m.predict(row)[0])
    c["model_zero_deploy"] = dict(ugm3=round(pred, 1), tier=tname(pred),
                                  band=[round(max(0, pred-band), 0), round(pred+band, 0)],
                                  danger_dial_45="ALERT" if pred > 45 else "ok")
json.dump(tc, open(os.path.join(OUT, "test_cases.json"), "w"), indent=2)
for c in tc["cases"]:
    z = c["model_zero_deploy"]
    print(f"{c['site']:9s} {c['date']}: model(zero-deploy)={z['ugm3']:6.1f} '{z['tier']}' band{z['band']}"
          f"  | actual {c['actual_pm25']:6.1f} '{c['actual_tier']}'")
print("wrote results/test_cases.json (+ model_zero_deploy)")
