#!/usr/bin/env python3
"""fig_investigation.py — 3-panel figure for the site_54 / blind-categorization investigation."""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import features as F

OUT = os.path.join(F.HERE, "results")
df = F.load(); CAT = F.load_categorizer(); full = F.assign_full_categories(df, CAT)
EXT = pd.read_csv(os.path.join(OUT, "external_features.csv")); EXTF=[c for c in EXT.columns if c!="site_id"]
inv = json.load(open(os.path.join(OUT,"categorization_investigation.json")))
ibc = json.load(open(os.path.join(OUT,"improve_blind_cat.json")))
CC = {0:"#6f6cd8",1:"#d8a24a",2:"#36b3a8"}; LAB=CAT["cluster_labels"]
per = EXT.copy(); per["cat"]=per.site_id.map(full); per["pm25"]=per.site_id.map(df.groupby("site_id").pm2_5.mean())

fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))

# Panel 1 — blind categorizer accuracy (model + features)
labels = ["geodata\n→RF\n(4th-cap)","geodata\n→kNN\n(better)","geo+clim\n→RF","climate\n→kNN"]
vals = [0.538, 0.641, 0.615, 0.641]; cols=["#c25b5b","#4a9e6f","#7a8bbf","#7a8bbf"]
ax[0].bar(labels, vals, color=cols, edgecolor="white")
ax[0].axhline(0.615, ls="--", color="#555", lw=1.2); ax[0].text(3.4,0.622,"majority 0.615",fontsize=8,color="#555",ha="right")
ax[0].set_ylim(0,0.75); ax[0].set_ylabel("leave-one-site-out accuracy")
ax[0].set_title("(1) The blind category guess: kNN beats RF\nand clears the majority baseline", fontsize=10.5)
for i,v in enumerate(vals): ax[0].text(i,v+0.012,f"{v:.3f}",ha="center",fontsize=9,fontweight="bold")

# Panel 2 — site_54 in geodata space (standardized dist_major_road vs road density)
Xs = StandardScaler().fit_transform(per[["dist_major_road_m","road_len_all_300m"]].values)
for c in [0,1,2]:
    m = per.cat.values==c
    ax[1].scatter(Xs[m,0], Xs[m,1], c=CC[c], s=46, edgecolor="white", lw=.6, label=f"{LAB[str(c)]} (n={m.sum()})")
si = list(per.site_id).index("site_54")
ax[1].scatter(Xs[si,0], Xs[si,1], s=320, facecolor="none", edgecolor="#c0392b", lw=2.4, zorder=5)
ax[1].annotate("site_54\ntrue: HIGH (62.9 µg/m³)\nneighbours: all LOW",
               (Xs[si,0],Xs[si,1]), textcoords="offset points", xytext=(14,-6), fontsize=8.5, color="#c0392b", fontweight="bold")
ax[1].set_xlabel("← closer to major road   |   standardized distance"); ax[1].set_ylabel("road density 300m →")
ax[1].legend(fontsize=7.5, loc="lower right"); ax[1].grid(alpha=.25)
ax[1].set_title("(2) Why it's misread: in map-feature space site_54\nsits among LOW-pollution sites — a local-source anomaly", fontsize=10.5)

# Panel 3 — nowcast tier-exact by category strategy (blind doesn't help; observed does)
order=["none","geo_rf","geo_knn","true"]
labs=["no\ncategory","blind\ngeo→RF","blind\ngeo→kNN","observed\n(deploy)"]
te=[ibc[k]["tier_exact"] for k in order]; r2=[ibc[k]["meanR2"] for k in order]
cc=["#888","#c25b5b","#c8825b","#4a9e6f"]
ax[2].bar(labs, te, color=cc, edgecolor="white")
ax[2].set_ylim(0,0.8); ax[2].set_ylabel("new-site tier-exact accuracy")
ax[2].set_title("(3) A guessed category doesn't help the nowcast —\nonly an OBSERVED one does (short deploy)", fontsize=10.5)
for i,(v,r) in enumerate(zip(te,r2)): ax[2].text(i,v+0.012,f"{v:.2f}\nR²{r:+.2f}",ha="center",fontsize=8.2,fontweight="bold")

fig.suptitle("Blind (sensor-less) categorization — what misled site_54, and what to do about it", fontsize=12.5, fontweight="bold", y=1.02)
fig.tight_layout(); p=os.path.join(OUT,"fig_blindcat_investigation.png"); fig.savefig(p, dpi=130, bbox_inches="tight"); plt.close(fig)
print("wrote", os.path.relpath(p, F.HERE))
