#!/usr/bin/env python3
"""paired per-site significance: k=3 vs k=4 on +cat ALONE (no geodata) — the deploy-only claim."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
import xgboost as xgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkx(): return xgb.XGBRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED)
def cen(sig,feats,k):
    sc=StandardScaler().fit(sig[feats].values); km=KMeans(k,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values)); return sc,km.cluster_centers_
def assign(sig,sc,c,feats):
    Xs=sc.transform(sig[feats].values); return dict(zip(sig.index,np.argmin(((Xs[:,None,:]-c[None,:,:])**2).sum(2),axis=1)))
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
sc3,c3=cen(sig,feats,3); sc4,c4=cen(sig,feats,4); rec=[]
for tr_i,ev_i in folds:
    tr,ev=df.iloc[tr_i].copy(),df.iloc[ev_i].copy()
    l3=assign(sig,sc3,c3,feats); l4=assign(sig,sc4,c4,feats)
    tr["c3"]=tr.site_id.map(l3); ev["c3"]=ev.site_id.map(l3); tr["c4"]=tr.site_id.map(l4); ev["c4"]=ev.site_id.map(l4)
    def cols(d,k,tag):
        cc=[]
        for j in range(k): d[f"{tag}{j}"]=(d[f"c{k}"]==j).astype(float) if tag=='a' else (d[f"c{k}"]==j).astype(float); cc.append(f"{tag}{j}")
        return list(F.BASE_NOW)+cc
    ca=cols(tr,3,"a"); cols(ev,3,"a"); cb=cols(tr,4,"b"); cols(ev,4,"b")
    ma=mkx(); ma.fit(tr[ca].values,tr.pm2_5.values); pa=ma.predict(ev[ca].values)
    mb=mkx(); mb.fit(tr[cb].values,tr.pm2_5.values); pb=mb.predict(ev[cb].values)
    ev=ev.assign(pa=pa,pb=pb)
    for sid,g in ev.groupby("site_id"):
        rec.append(np.sqrt(np.mean((g.pm2_5-g.pa)**2))-np.sqrt(np.mean((g.pm2_5-g.pb)**2)))
d=np.array(rec); rng=np.random.default_rng(SEED)
boot=np.array([rng.choice(d,len(d),replace=True).mean() for _ in range(5000)]); lo,hi=np.percentile(boot,[2.5,97.5])
print(f"+cat ONLY  k3 vs k4: mean RMSE reduction {d.mean():+.2f} ug/m3  CI[{lo:+.2f},{hi:+.2f}]  {int((d>0).sum())}/{len(d)} sites better  -> {'SIGNIFICANT' if lo>0 else 'not significant'}")
