#!/usr/bin/env python3
"""
Fix conformal under-coverage (naive 74.8% vs 90% target) for new-site nowcasts.

Naive split-conformal calibrates on held-out ROWS (same sites it trained on), then is tested on
held-out SITES -> exchangeability breaks across the site boundary -> under-covers (Lei 2018).

Fix = GROUP (leave-sites-out) conformal: calibrate the residual quantile on whole HELD-OUT SITES,
so calibration residuals reflect the new-site error the band must cover. Also a MONDRIAN variant:
a separate quantile per site_category (bands adapt to how noisy each kind of place is).

Honest new-site test = outer GroupKFold5. Model = LightGBM on +cat+external, k=4 (this round's best).
Run: ../../capenv/bin/python improve_conformal.py  -> results/improve_conformal.csv
"""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import GroupKFold
import lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; K=4; ALPHA=0.1
EXT=pd.read_csv(os.path.join(OUT,"external_features.csv")); EXTF=[c for c in EXT.columns if c!="site_id"]
def sigs(df): return pd.DataFrame({s:F.site_signature(g) for s,g in df.groupby("site_id")}).T
def mkl(): return lgb.LGBMRegressor(n_estimators=400,max_depth=6,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
def qhat(resid,alpha=ALPHA):
    n=len(resid); return np.quantile(resid,min(1.0,np.ceil((n+1)*(1-alpha))/n))
df=F.load(); sig=sigs(df); feats=F.SIG_FEATS; df=df.merge(EXT,on="site_id",how="left")
sc=StandardScaler().fit(sig[feats].values); km=KMeans(K,n_init=50,random_state=SEED).fit(sc.transform(sig[feats].values))
Xs=sc.transform(sig[feats].values); lab=dict(zip(sig.index,np.argmin(((Xs[:,None,:]-km.cluster_centers_[None,:,:])**2).sum(2),axis=1)))
df["c"]=df.site_id.map(lab); cc=[]
for j in range(K): df[f"cat_{j}"]=(df.c==j).astype(float); cc.append(f"cat_{j}")
cols=list(F.BASE_NOW)+cc+EXTF
folds=list(GroupKFold(5).split(df,df.pm2_5.values,df.site_id.values))
methods={"naive_rows":[],"group_sites":[],"mondrian_cat":[]}
wid={"naive_rows":[],"group_sites":[],"mondrian_cat":[]}
for tr_i,ev_i in folds:
    tr,ev=df.iloc[tr_i],df.iloc[ev_i]
    tr_sites=tr.site_id.unique()
    # split TRAIN sites -> proper-train sites vs calibration sites (group calibration)
    rng=np.random.default_rng(SEED); cal_sites=set(rng.choice(tr_sites,max(3,len(tr_sites)//4),replace=False))
    ptr=tr[~tr.site_id.isin(cal_sites)]; cal=tr[tr.site_id.isin(cal_sites)]
    m=mkl(); m.fit(ptr[cols].values,ptr.pm2_5.values)
    yev=ev.pm2_5.values; pev=m.predict(ev[cols].values)
    # (1) NAIVE rows: calibrate on random rows of the full train (reproduces the 74.8% baseline)
    rng2=np.random.default_rng(SEED); ridx=rng2.permutation(len(tr)); cn=ridx[:int(0.3*len(tr))]
    mn=mkl(); rest=ridx[int(0.3*len(tr)):]; mn.fit(tr.iloc[rest][cols].values,tr.iloc[rest].pm2_5.values)
    qn=qhat(np.abs(tr.iloc[cn].pm2_5.values-mn.predict(tr.iloc[cn][cols].values)))
    pn=mn.predict(ev[cols].values)
    methods["naive_rows"].append(np.mean((yev>=pn-qn)&(yev<=pn+qn))); wid["naive_rows"].append(2*qn)
    # (2) GROUP sites: calibrate q on held-out SITES' residuals
    rcal=np.abs(cal.pm2_5.values-m.predict(cal[cols].values)); qg=qhat(rcal)
    methods["group_sites"].append(np.mean((yev>=pev-qg)&(yev<=pev+qg))); wid["group_sites"].append(2*qg)
    # (3) MONDRIAN per-category: q per category from calibration sites
    cov_m=[]; w_m=[]
    cal=cal.assign(r=rcal)
    for j in range(K):
        rc=cal[cal.c==j].r.values
        qj=qhat(rc) if len(rc)>=5 else qg
        evj=ev[ev.c==j]
        if len(evj):
            pj=m.predict(evj[cols].values); yj=evj.pm2_5.values
            cov_m.append(((yj>=pj-qj)&(yj<=pj+qj)).sum()); w_m.append(qj*2*len(evj))
            cov_m_n=len(evj)
    # aggregate mondrian over this fold (weighted by n)
    tot=len(ev); covm=sum(cov_m)/tot
    # width: per-row average
    wsum=0.0
    for j in range(K):
        rc=cal[cal.c==j].r.values; qj=qhat(rc) if len(rc)>=5 else qg; nj=(ev.c==j).sum(); wsum+=qj*2*nj
    methods["mondrian_cat"].append(covm); wid["mondrian_cat"].append(wsum/tot)
rows=[]
print(f"{'method':>14} | coverage | mean width (target coverage 90%)")
for k in methods:
    cov=np.mean(methods[k])*100; w=np.mean(wid[k])
    rows.append(dict(method=k,coverage_pct=round(cov,1),mean_width=round(w,1)))
    print(f"{k:>14} | {cov:6.1f}% | {w:6.1f} ug/m3")
pd.DataFrame(rows).to_csv(os.path.join(OUT,"improve_conformal.csv"),index=False)
print("\nwrote results/improve_conformal.csv")
