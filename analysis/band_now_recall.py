#!/usr/bin/env python3
"""Lift Dangerous-tier recall on the HONEST new-site test (leave-sites-out, k=4).
(A) regression + lowered Dangerous threshold -> recall/false-alarm tradeoff.
(B) dedicated 'Dangerous vs not' detector with class weighting (Crimson's upweight idea).
(C) which features separate dangerous days (effect size + detector gain importance)."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.metrics import recall_score, precision_score
import lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; K=4; DANGER=55.4
EXT=pd.read_csv(f"{OUT}/external_features.csv"); EXTF=[c for c in EXT.columns if c!="site_id"]
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
sc=StandardScaler().fit(sig[feats].values); km=KMeans(K,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values))
Xs=sc.transform(sig[feats].values); lab=dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
df["c"]=df.site_id.map(lab); cc=[]
for j in range(K): df[f"cat_{j}"]=(df.c==j).astype(float); cc.append(f"cat_{j}")
COLS=list(F.BASE_NOW)+cc+EXTF
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
y=df.pm2_5.values; danger=(y>DANGER).astype(int)
print(f"dangerous days: {danger.sum()}/{len(danger)} ({danger.mean()*100:.1f}%)")

# (A) regression OOF -> threshold sweep
yp=np.zeros(len(df))
for tr_i,ev_i in folds:
    m=lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
    m.fit(df.iloc[tr_i][COLS].values,df.iloc[tr_i].pm2_5.values); yp[ev_i]=m.predict(df.iloc[ev_i][COLS].values)
print("\n(A) REGRESSION + lowered Dangerous cutoff (flag Dangerous if predicted > t):")
print(f"  {'cutoff':>7} | {'recall':>6} | {'precision':>9} | {'false-alarm rate':>16}")
for t in [55.4,50,45,42,40,37.5,35]:
    pred=(yp>t).astype(int); rec=recall_score(danger,pred,zero_division=0); prec=precision_score(danger,pred,zero_division=0)
    far=((pred==1)&(danger==0)).sum()/(danger==0).sum()
    print(f"  {t:7.1f} | {rec:6.2f} | {prec:9.2f} | {far:16.2f}")

# (B) dedicated Dangerous-vs-not detector with class weighting, OOF
print("\n(B) DEDICATED detector (LightGBM classifier, class-weighted) — OOF new-site:")
proba=np.zeros(len(df))
for tr_i,ev_i in folds:
    yt=danger[tr_i]; spw=(yt==0).sum()/max(1,(yt==1).sum())
    clf=lgb.LGBMClassifier(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,
                           scale_pos_weight=spw,n_jobs=-1,random_state=SEED,verbose=-1)
    clf.fit(df.iloc[tr_i][COLS].values,yt); proba[ev_i]=clf.predict_proba(df.iloc[ev_i][COLS].values)[:,1]
print(f"  {'prob thr':>8} | {'recall':>6} | {'precision':>9} | {'false-alarm':>11}")
for th in [0.5,0.6,0.7,0.8]:
    pred=(proba>th).astype(int); rec=recall_score(danger,pred,zero_division=0); prec=precision_score(danger,pred,zero_division=0)
    far=((pred==1)&(danger==0)).sum()/(danger==0).sum()
    print(f"  {th:8.2f} | {rec:6.2f} | {prec:9.2f} | {far:11.2f}")
# detector importance (refit on all for a stable ranking)
spw=(danger==0).sum()/(danger==1).sum()
clf=lgb.LGBMClassifier(n_estimators=400,max_depth=6,learning_rate=0.05,scale_pos_weight=spw,n_jobs=-1,random_state=SEED,verbose=-1).fit(df[COLS].values,danger)
imp=pd.Series(clf.feature_importances_,index=COLS).sort_values(ascending=False)
print("\n(C) TOP features the Dangerous detector relies on (gain importance):")
for k,v in imp.head(8).items(): print(f"    {k:22s} {v}")
print("\n   effect size |mean(danger)-mean(safe)|/std (which features separate dangerous days):")
eff={}
for ccol in F.BASE_NOW+EXTF:
    d=df[ccol].values; eff[ccol]=abs(d[danger==1].mean()-d[danger==0].mean())/(d.std()+1e-9)
for k,v in sorted(eff.items(),key=lambda x:-x[1])[:8]: print(f"    {k:22s} {v:.2f}")
