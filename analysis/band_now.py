#!/usr/bin/env python3
"""NOW safety-band accuracy on the HONEST new-site test (leave-sites-out, k=4).
Out-of-fold predictions binned into EPA 3-tier bands. The bottleneck test."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score, recall_score, confusion_matrix, r2_score
import lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; K=4
LAB=["Elevated","High","Dangerous"]
def band(x): return np.clip(np.digitize(x,[35.4,55.4]),0,2)
EXT=pd.read_csv(f"{OUT}/external_features.csv"); EXTF=[c for c in EXT.columns if c!="site_id"]
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkl(): return lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
sc=StandardScaler().fit(sig[feats].values); km=KMeans(K,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values))
Xs=sc.transform(sig[feats].values); lab=dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
df["c"]=df.site_id.map(lab); cc=[]
for j in range(K): df[f"cat_{j}"]=(df.c==j).astype(float); cc.append(f"cat_{j}")
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
def oof(cols):
    yt=np.zeros(len(df)); yp=np.zeros(len(df))
    for tr_i,ev_i in folds:
        tr,ev=df.iloc[tr_i],df.iloc[ev_i]; m=mkl(); m.fit(tr[cols].values,tr.pm2_5.values)
        yp[ev_i]=m.predict(ev[cols].values); yt[ev_i]=ev.pm2_5.values
    return yt,yp
print("overall band distribution:", {LAB[i]:int((band(df.pm2_5.values)==i).sum()) for i in range(3)})
for name,cols in [("+cat (deploy only)",list(F.BASE_NOW)+cc),("+cat+external (best)",list(F.BASE_NOW)+cc+EXTF)]:
    yt,yp=oof(cols); yb=band(yt); pb=band(yp)
    exact=(pb==yb).mean(); adj=(np.abs(pb-yb)<=1).mean(); maj=pd.Series(yb).value_counts(normalize=True).max()
    f1=f1_score(yb,pb,average="macro"); rec=recall_score(yb,pb,average=None,labels=[0,1,2],zero_division=0)
    print(f"\n=== NOW {name} === (regression R²={r2_score(yt,yp):.3f})")
    print(f"  exact-band acc {exact:.3f} | adjacent {adj:.3f} | majority-class {maj:.3f} | macro-F1 {f1:.3f}")
    print(f"  recall: Elevated {rec[0]:.2f} | High {rec[1]:.2f} | Dangerous {rec[2]:.2f}")
    cm=confusion_matrix(yb,pb,labels=[0,1,2])
    print("  confusion (rows=true, cols=pred):")
    for i,r in enumerate(cm): print(f"    {LAB[i]:9s} {r}")
