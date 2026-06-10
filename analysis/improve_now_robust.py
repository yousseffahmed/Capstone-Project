#!/usr/bin/env python3
"""k=4 robustness: fold-safe (centroids on train only), single models, paired significance vs k=3."""
import os, sys, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import xgboost as xgb, lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42
EXT=pd.read_csv(os.path.join(OUT,"external_features.csv")); EXTF=[c for c in EXT.columns if c!="site_id"]
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkx(): return xgb.XGBRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED)
def mkr(): return RandomForestRegressor(n_estimators=400,max_depth=30,max_features="sqrt",n_jobs=-1,random_state=SEED)
def mkl(): return lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
def cen_full(sig,feats,k):
    sc=StandardScaler().fit(sig[feats].values); km=KMeans(k,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values)); return sc,km.cluster_centers_
def assign(sig,sc,cen,feats):
    Xs=sc.transform(sig[feats].values); return dict(zip(sig.index,np.argmin(((Xs[:,None,:]-cen[None,:,:])**2).sum(2),axis=1)))
def assign_fs(sig,feats,k,train):
    t=sig.loc[sig.index.isin(train)]; sc=StandardScaler().fit(t[feats].values)
    km=KMeans(k,n_init=25,random_state=SEED).fit(sc.transform(t[feats].values)); Xs=sc.transform(sig[feats].values)
    return dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
def oh(d,k):
    cc=[]
    for j in range(k): d[f"cat_{j}"]=(d.c==j).astype(float); cc.append(f"cat_{j}")
    return d,cc
def evalr(df,folds,k,sig,feats,mk,with_ext,foldsafe,sc=None,cen=None):
    out=[]
    for tr_i,ev_i in folds:
        tr,ev=df.iloc[tr_i].copy(),df.iloc[ev_i].copy()
        lab=assign_fs(sig,feats,k,set(tr.site_id.unique())) if foldsafe else assign(sig,sc,cen,feats)
        tr["c"]=tr.site_id.map(lab); ev["c"]=ev.site_id.map(lab); tr,cc=oh(tr,k); ev,_=oh(ev,k)
        cols=list(F.BASE_NOW)+cc+(EXTF if with_ext else [])
        m=mk(); m.fit(tr[cols].values,tr.pm2_5.values); out.append(r2_score(ev.pm2_5.values,m.predict(ev[cols].values)))
    return float(np.mean(out)),float(np.std(out))
def paired(df,folds,sig,feats,k_a,k_b):
    """per-site RMSE: k_a vs k_b (+cat+ext, XGB). delta>0 => k_b better."""
    sca,cena=cen_full(sig,feats,k_a); scb,cenb=cen_full(sig,feats,k_b); rec=[]
    for tr_i,ev_i in folds:
        tr,ev=df.iloc[tr_i].copy(),df.iloc[ev_i].copy()
        for tag,k,sc,cen in [("a",k_a,sca,cena),("b",k_b,scb,cenb)]:
            lab=assign(sig,sc,cen,feats); tr[f"c{tag}"]=tr.site_id.map(lab); ev[f"c{tag}"]=ev.site_id.map(lab)
        def build(d,k,tag):
            cc=[]; 
            for j in range(k): d[f"{tag}cat_{j}"]=(d[f"c{tag}"]==j).astype(float); cc.append(f"{tag}cat_{j}")
            return list(F.BASE_NOW)+cc+EXTF
        ca=build(tr,k_a,"a"); _=build(ev,k_a,"a"); cb=build(tr,k_b,"b"); _=build(ev,k_b,"b")
        ma=mkx(); ma.fit(tr[ca].values,tr.pm2_5.values); pa=ma.predict(ev[ca].values)
        mb=mkx(); mb.fit(tr[cb].values,tr.pm2_5.values); pb=mb.predict(ev[cb].values)
        ev=ev.assign(pa=pa,pb=pb)
        for sid,g in ev.groupby("site_id"):
            ra=np.sqrt(np.mean((g.pm2_5-g.pa)**2)); rb=np.sqrt(np.mean((g.pm2_5-g.pb)**2)); rec.append(ra-rb)
    d=np.array(rec); rng=np.random.default_rng(SEED)
    boot=np.array([rng.choice(d,len(d),replace=True).mean() for _ in range(5000)]); lo,hi=np.percentile(boot,[2.5,97.5])
    return d.mean(),lo,hi,int((d>0).sum()),len(d)
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values)); K=4
sc,cen=cen_full(sig,feats,K)
print(f"=== k={K} robustness ===",flush=True)
rfs,sfs=evalr(df,folds,K,sig,feats,mkx,False,True); print(f"+cat fold-safe (centroids train-only): {rfs:.4f}±{sfs:.3f}",flush=True)
for n,mk in [("RandomForest",mkr),("XGBoost",mkx),("LightGBM",mkl)]:
    r,s=evalr(df,folds,K,sig,feats,mk,True,False,sc,cen); print(f"single {n:13s} +cat+ext: {r:.4f}±{s:.3f}",flush=True)
m,lo,hi,imp,n=paired(df,folds,sig,feats,3,4)
print(f"paired k3 vs k4 (+cat+ext): mean RMSE reduction {m:+.2f} ug/m3 CI[{lo:+.2f},{hi:+.2f}] {imp}/{n} sites better; {'SIGNIFICANT' if lo>0 else 'ns'}",flush=True)
print("DONE")
