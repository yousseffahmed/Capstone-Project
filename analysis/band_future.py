#!/usr/bin/env python3
"""FUTURE safety-band accuracy: bin honest LSTM forecasts into EPA 3-tier bands.
Bands: Elevated<=35.4 | High 35.5-55.4 | Dangerous>55.4. Honest chronological split."""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, recall_score, confusion_matrix
import features as F
OUT=os.path.join(F.HERE,"results")
EDGES=[-1e9,35.4,55.4,1e9]; LAB=["Elevated","High","Dangerous"]
def band(x): return np.clip(np.digitize(x,[35.4,55.4]),0,2)
# recompute persistence + true future per (site,target_day,h) from the panel
df=F.load(); panel=F.build_future_panel(df); cut=df["day"].quantile(0.8); cutd=np.datetime64(cut)
rowsP=[]
for h in [1,2,3,4,5,6,7]:
    tgt=panel[["site_id","day","pm2_5"]].copy(); tgt["day"]=tgt["day"]-pd.Timedelta(days=h); tgt=tgt.rename(columns={"pm2_5":"y"})
    sup=panel.merge(tgt,on=["site_id","day"],how="inner")
    te=sup[sup.day.values>cutd]
    td=(te.day+pd.Timedelta(days=h)).dt.strftime("%Y-%m-%d").values
    for sid,t,persist,y in zip(te.site_id.values,td,te.pm2_5.values,te.y.values):
        rowsP.append((sid,t,h,persist,y))
P=pd.DataFrame(rowsP,columns=["site_id","target_day","h","persist","y"])
L=pd.read_csv(f"{OUT}/lstm_preds_base.csv")[["site_id","target_day","h","pred"]]
m=P.merge(L,on=["site_id","target_day","h"])
print(f"aligned test rows: {len(m)}")
print("\noverall test band distribution:", {LAB[i]:int((band(m.y)==i).sum()) for i in range(3)})
out=[]
for h in [1,3,7]:
    s=m[m.h==h]; yb=band(s.y.values); pb=band(s.pred.values); rb=band(s.persist.values)
    exact=(pb==yb).mean(); adj=(np.abs(pb-yb)<=1).mean(); persist_acc=(rb==yb).mean()
    maj=pd.Series(yb).value_counts(normalize=True).max()
    f1=f1_score(yb,pb,average="macro")
    rec=recall_score(yb,pb,average=None,labels=[0,1,2],zero_division=0)
    out.append(dict(h=h,exact=round(exact,3),adjacent=round(adj,3),persistence=round(persist_acc,3),
                    majority=round(maj,3),macroF1=round(f1,3),
                    rec_elev=round(rec[0],2),rec_high=round(rec[1],2),rec_danger=round(rec[2],2)))
    print(f"\n--- h+{h} ---")
    print(f"  LSTM exact-band acc {exact:.3f} | adjacent {adj:.3f} | persistence-band {persist_acc:.3f} | majority-class {maj:.3f}")
    print(f"  macro-F1 {f1:.3f} | recall Elevated {rec[0]:.2f} High {rec[1]:.2f} Dangerous {rec[2]:.2f}")
    cm=confusion_matrix(yb,pb,labels=[0,1,2])
    print("  confusion (rows=true, cols=pred) Elev/High/Dang:")
    for i,r in enumerate(cm): print(f"    {LAB[i]:9s} {r}")
pd.DataFrame(out).to_csv(f"{OUT}/band_future.csv",index=False)
print("\nwrote band_future.csv")
