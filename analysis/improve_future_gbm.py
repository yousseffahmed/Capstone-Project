#!/usr/bin/env python3
"""LightGBM forecaster, save per-(site,target_day,h) test preds for ensembling with the LSTM."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.metrics import r2_score
import lightgbm as lgb
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; H=[1,2,3,4,5,6,7]
LAG=["pm25_lag1","pm25_lag2","pm25_lag3","pm25_lag7","pm25_roll7","pm25_roll14"]
df=F.load(); cat=F.load_categorizer(); site_cat=F.assign_full_categories(df,cat)
panel=F.build_future_panel(df); panel["site_category"]=panel.site_id.map(site_cat)
cut=df["day"].quantile(0.8); cutd=np.datetime64(cut)
FEATS=LAG+F.WX+F.ENG+["month","day_of_week","site_latitude","site_longitude"]
rows=[]; predrows=[]
for h in H:
    tgt=panel[["site_id","day","pm2_5"]].copy(); tgt["day"]=tgt["day"]-pd.Timedelta(days=h); tgt=tgt.rename(columns={"pm2_5":"y_future"})
    sup=panel.merge(tgt,on=["site_id","day"],how="inner")
    trm=(sup.day.values+np.timedelta64(h,"D"))<=cutd; tem=sup.day.values>cutd
    tr,te=sup[trm],sup[tem]
    ml=lgb.LGBMRegressor(n_estimators=400,max_depth=5,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=-1,random_state=SEED,verbose=-1)
    ml.fit(tr[FEATS],tr.y_future.values); p=ml.predict(te[FEATS])
    rows.append((h,r2_score(te.y_future.values,p)))
    td=(te.day+pd.Timedelta(days=h)).dt.strftime("%Y-%m-%d").values
    for sid,t,pr,y in zip(te.site_id.values,td,p,te.y_future.values):
        predrows.append((sid,t,h,float(pr),float(y)))
print("LightGBM per-horizon R²:",{h:round(r,3) for h,r in rows})
pd.DataFrame(predrows,columns=["site_id","target_day","h","pred","y"]).to_csv(os.path.join(OUT,"gbm_preds.csv"),index=False)
print("saved gbm_preds.csv")
