#!/usr/bin/env python3
"""Ensemble baseline-LSTM + LightGBM forecasts (aligned on site,target_day,h). numpy/pandas only."""
import os, numpy as np, pandas as pd
OUT=os.path.dirname(os.path.abspath(__file__))+"/results"
def r2(y,p):
    y,p=np.asarray(y,float),np.asarray(p,float); ss=((y-p)**2).sum(); st=((y-y.mean())**2).sum()
    return float(1-ss/st) if st>0 else float("nan")
L=pd.read_csv(f"{OUT}/lstm_preds_base.csv"); G=pd.read_csv(f"{OUT}/gbm_preds.csv")
m=L.merge(G,on=["site_id","target_day","h"],suffixes=("_lstm","_gbm"))
print(f"aligned rows: {len(m)} (lstm {len(L)}, gbm {len(G)})")
print(f"{'h':>2} | {'LSTM':>6} | {'GBM':>6} | {'avg':>6} | {'best-w':>6} (w_lstm)")
out=[]
for h in sorted(m.h.unique()):
    s=m[m.h==h]; y=s.y_lstm.values  # y_lstm==y_gbm (same target); use one
    rl=r2(y,s.pred_lstm); rg=r2(y,s.pred_gbm); ra=r2(y,0.5*s.pred_lstm+0.5*s.pred_gbm)
    # diagnostic: best fixed blend weight (not a claim — shows ceiling)
    ws=np.linspace(0,1,21); rb=max((r2(y,w*s.pred_lstm+(1-w)*s.pred_gbm),w) for w in ws)
    out.append(dict(h=int(h),LSTM=round(rl,4),GBM=round(rg,4),avg=round(ra,4),best_w=round(rb[0],4),w_lstm=round(rb[1],2)))
    print(f"{h:>2} | {rl:6.3f} | {rg:6.3f} | {ra:6.3f} | {rb[0]:6.3f} (w={rb[1]:.2f})")
res=pd.DataFrame(out); res.to_csv(f"{OUT}/improve_future.csv",index=False)
wins=(res.avg>res.LSTM).sum()
print(f"\n50/50 ensemble beats LSTM at {wins}/7 horizons; mean dR2 = {(res.avg-res.LSTM).mean():+.4f}")
