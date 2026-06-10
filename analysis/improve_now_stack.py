#!/usr/bin/env python3
"""Stacked ensemble (RF+XGB+LGBM -> ridge, out-of-fold) at k=4, +cat+external, honest new-site."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import xgboost as xgb, lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; K=4
EXT=pd.read_csv(os.path.join(OUT,"external_features.csv")); EXTF=[c for c in EXT.columns if c!="site_id"]
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkx(): return xgb.XGBRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED)
def mkr(): return RandomForestRegressor(n_estimators=300,max_depth=30,max_features="sqrt",n_jobs=-1,random_state=SEED)
def mkl(): return lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
sc=StandardScaler().fit(sig[feats].values); km=KMeans(K,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values))
Xs=sc.transform(sig[feats].values); lab=dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
df["c"]=df.site_id.map(lab); cc=[]
for j in range(K): df[f"cat_{j}"]=(df.c==j).astype(float); cc.append(f"cat_{j}")
cols=list(F.BASE_NOW)+cc+EXTF
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
bases={"rf":mkr,"xgb":mkx,"lgb":mkl}; outer=[]; wts=[]
for tr_i,ev_i in folds:
    tr,ev=df.iloc[tr_i],df.iloc[ev_i]; inner=GroupKFold(3); oof={n:np.zeros(len(tr)) for n in bases}
    for itr,iev in inner.split(tr,tr.pm2_5.values,tr.site_id.values):
        for n,fn in bases.items():
            m=fn(); m.fit(tr.iloc[itr][cols].values,tr.iloc[itr].pm2_5.values); oof[n][iev]=m.predict(tr.iloc[iev][cols].values)
    meta=Ridge(alpha=1.0).fit(np.column_stack([oof[n] for n in bases]),tr.pm2_5.values); wts.append(meta.coef_)
    preds=[]
    for n,fn in bases.items():
        m=fn(); m.fit(tr[cols].values,tr.pm2_5.values); preds.append(m.predict(ev[cols].values))
    outer.append(r2_score(ev.pm2_5.values,meta.predict(np.column_stack(preds))))
print(f"STACKED rf+xgb+lgb->ridge  +cat+ext k={K}:  R² = {np.mean(outer):.4f} ± {np.std(outer):.3f}")
print(f"  mean meta weights [rf,xgb,lgb] = {np.mean(wts,axis=0).round(3)}")
print(f"  vs best single (LightGBM 0.561) — stacking {'WINS' if np.mean(outer)>0.561 else 'no gain'}")
