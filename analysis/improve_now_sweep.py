#!/usr/bin/env python3
"""k-sweep only: honest new-site R² for +cat and +cat+external at k=2..6 (XGB)."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
import xgboost as xgb
import features as F
OUT = os.path.join(F.HERE, "results"); SEED = 42
EXT = pd.read_csv(os.path.join(OUT, "external_features.csv")); EXTF = [c for c in EXT.columns if c != "site_id"]
def sigs(df): return pd.DataFrame({s: F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkx(): return xgb.XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED)
def assign(sig, sc, cen, feats):
    Xs = sc.transform(sig[feats].values)
    return dict(zip(sig.index, np.argmin(((Xs[:,None,:]-cen[None,:,:])**2).sum(2),axis=1)))
def r2_ns(df, folds, k, sig, feats, sc, cen, with_ext):
    out=[]
    for tr_i,ev_i in folds:
        tr,ev=df.iloc[tr_i].copy(),df.iloc[ev_i].copy()
        lab=assign(sig,sc,cen,feats)
        tr["c"]=tr.site_id.map(lab); ev["c"]=ev.site_id.map(lab)
        cc=[]
        for j in range(k):
            tr[f"cat_{j}"]=(tr.c==j).astype(float); ev[f"cat_{j}"]=(ev.c==j).astype(float); cc.append(f"cat_{j}")
        cols=list(F.BASE_NOW)+cc+(EXTF if with_ext else [])
        m=mkx(); m.fit(tr[cols].values,tr.pm2_5.values); out.append(r2_score(ev.pm2_5.values,m.predict(ev[cols].values)))
    return float(np.mean(out)),float(np.std(out))
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
rows=[]
for k in [2,3,4,5,6]:
    sc=StandardScaler().fit(sig[feats].values)
    km=KMeans(n_clusters=k,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values)); cen=km.cluster_centers_
    rc,scd=r2_ns(df,folds,k,sig,feats,sc,cen,False)
    re,sed=r2_ns(df,folds,k,sig,feats,sc,cen,True)
    sizes=np.bincount(km.labels_,minlength=k).tolist()
    rows.append(dict(k=k,plus_cat=round(rc,4),plus_cat_std=round(scd,4),plus_cat_ext=round(re,4),plus_cat_ext_std=round(sed,4),sizes=str(sizes)))
    print(f"k={k} | +cat {rc:.4f}±{scd:.3f} | +cat+ext {re:.4f}±{sed:.3f} | sizes={sizes}",flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT,"improve_now_sweep.csv"),index=False)
print("DONE")
