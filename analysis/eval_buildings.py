#!/usr/bin/env python3
"""Does OSM building density add honest new-site R²? +cat+ext vs +cat+ext+buildings (k=4)."""
import os, json, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
import xgboost as xgb, lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; K=4
sites=pd.read_csv(f"{OUT}/_site_coords.csv")
cache=json.load(open(f"{OUT}/_osm_buildings.json"))
LAT0=float(sites.site_latitude.mean()); LON0=float(sites.site_longitude.mean())
def to_m(lat,lon): return ((lon-LON0)*111320*math.cos(math.radians(LAT0)),(lat-LAT0)*110540)
# building density features per site
recs=[]
for _,r in sites.iterrows():
    px,py=to_m(r.site_latitude,r.site_longitude); pts=cache.get(r.site_id,[])
    d300=d500=d1000=0
    for la,lo in pts:
        bx,by=to_m(la,lo); dist=math.hypot(bx-px,by-py)
        if dist<=300:d300+=1
        if dist<=500:d500+=1
        if dist<=1000:d1000+=1
    recs.append(dict(site_id=r.site_id,bld_300m=d300,bld_500m=d500,bld_1000m=d1000,
                     bld_dens_300m=round(d300/(math.pi*0.3**2),1)))
B=pd.DataFrame(recs); B.to_csv(f"{OUT}/building_features.csv",index=False)
BF=["bld_300m","bld_500m","bld_1000m","bld_dens_300m"]
print("building features (all 39 sites, no gaps):",B[BF].notna().all().all())
EXT=pd.read_csv(f"{OUT}/external_features.csv"); EXTF=[c for c in EXT.columns if c!="site_id"]
df=F.load(); sig=pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T; feats=F.SIG_FEATS
df=df.merge(EXT,on="site_id").merge(B,on="site_id")
sc=StandardScaler().fit(sig[feats].values); km=KMeans(K,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values))
Xs=sc.transform(sig[feats].values); lab=dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
df["c"]=df.site_id.map(lab); cc=[]
for j in range(K): df[f"cat_{j}"]=(df.c==j).astype(float); cc.append(f"cat_{j}")
# correlation with per-site pm2.5 level
ps=df.groupby("site_id").agg(pm=("pm2_5","mean")).join(B.set_index("site_id"))
print("corr building feats vs per-site PM2.5 mean:")
for c in BF: print(f"  {c:14s} r={ps['pm'].corr(ps[c]):+.3f}")
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
def ev(cols,mk):
    sc=[]
    for tr_i,ev_i in folds:
        tr,ev=df.iloc[tr_i],df.iloc[ev_i]; m=mk(); m.fit(tr[cols].values,tr.pm2_5.values); sc.append(r2_score(ev.pm2_5.values,m.predict(ev[cols].values)))
    return float(np.mean(sc)),float(np.std(sc))
def mkx(): return xgb.XGBRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED)
def mkl(): return lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
base=list(F.BASE_NOW)+cc
print("\nhonest new-site R² (k=4):")
for name,mk in [("XGB",mkx),("LGBM",mkl)]:
    r0,s0=ev(base+EXTF,mk); r1,s1=ev(base+EXTF+BF,mk)
    print(f"  {name}: +cat+ext {r0:.4f}±{s0:.3f}  ->  +cat+ext+bld {r1:.4f}±{s1:.3f}   (dR2 {r1-r0:+.4f})")
