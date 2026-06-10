#!/usr/bin/env python3
"""Tuned FUTURE LSTM (torch-isolated). 2-layer, hidden=64, L=21, dropout, longer train.
Reports per-horizon R² AND saves test predictions keyed (site,target_day,h) for ensembling."""
import os, sys, warnings; warnings.filterwarnings("ignore")
import torch, torch.nn as nn
torch.set_num_threads(4)
import numpy as np, pandas as pd
import features as F
OUT=os.path.join(F.HERE,"results"); SEED=42; H=[1,2,3,4,5,6,7]
torch.manual_seed(SEED); np.random.seed(SEED)
def r2(y,p):
    y,p=np.asarray(y,float),np.asarray(p,float); ss=((y-p)**2).sum(); st=((y-y.mean())**2).sum()
    return float(1-ss/st) if st>0 else float("nan")
def run(L=14,hidden=48,emb=4,layers=1,dropout=0.0,epochs=40,patience=6,tag="base"):
    df=F.load(); cat=F.load_categorizer(); site_cat=F.assign_full_categories(df,cat)
    cut=df["day"].quantile(0.8); cutd=np.datetime64(cut)
    SEQ=["pm2_5","temp_2m_K","dewpoint_2m_K","wind_u_10m_ms","wind_v_10m_ms","surface_pressure_Pa","precipitation_m","rel_humidity","wind_speed"]
    samples=[]
    for sid,g in df.groupby("site_id"):
        g=g.set_index("day").sort_index(); full=pd.date_range(g.index.min(),g.index.max(),freq="D"); g=g.reindex(full)
        obs=g.pm2_5.notna().values.astype(float); feat=g[SEQ].copy(); feat["pm2_5"]=feat["pm2_5"].ffill().bfill()
        for c in SEQ[1:]: feat[c]=feat[c].interpolate(limit_direction="both")
        feat["obs_mask"]=obs; arr=feat.values.astype(np.float32); y=g.pm2_5.values.astype(np.float32)
        days=np.array(full); c_id=site_cat[sid]
        for t in range(L-1,len(g)-1):
            yh=np.full(7,np.nan,np.float32); ym=np.zeros(7,np.float32)
            for i,h in enumerate(H):
                if t+h<len(g) and obs[t+h]: yh[i]=y[t+h]; ym[i]=1.0
            if ym.sum()==0 or not obs[t]: continue
            samples.append((c_id,arr[t-L+1:t+1],np.nan_to_num(yh),ym,days[t],sid))
    cats=np.array([s[0] for s in samples]); X=np.stack([s[1] for s in samples]); Y=np.stack([s[2] for s in samples])
    M=np.stack([s[3] for s in samples]); anch=np.array([s[4] for s in samples]); sids=np.array([s[5] for s in samples])
    tr=(anch+np.timedelta64(7,"D"))<=cutd; te=anch>cutd
    mu=X[tr].reshape(-1,X.shape[-1]).mean(0); sd=X[tr].reshape(-1,X.shape[-1]).std(0)+1e-6; Xn=(X-mu)/sd
    ymu,ysd=Y[tr][M[tr]>0].mean(),Y[tr][M[tr]>0].std()+1e-6
    to=lambda a: torch.tensor(a,dtype=torch.float32)
    Xtr,Ytr,Mtr,Ctr=to(Xn[tr]),to((Y[tr]-ymu)/ysd),to(M[tr]),torch.tensor(cats[tr]); Xte=to(Xn[te]); Cte=torch.tensor(cats[te])
    class Net(nn.Module):
        def __init__(s):
            super().__init__(); s.lstm=nn.LSTM(X.shape[-1],hidden,num_layers=layers,batch_first=True,dropout=dropout if layers>1 else 0)
            s.emb=nn.Embedding(3,emb); s.head=nn.Sequential(nn.Linear(hidden+emb,48),nn.ReLU(),nn.Dropout(dropout),nn.Linear(48,7))
        def forward(s,x,c): _,(hn,_)=s.lstm(x); return s.head(torch.cat([hn[-1],s.emb(c)],1))
    net=Net(); opt=torch.optim.Adam(net.parameters(),lr=1e-3,weight_decay=1e-5)
    tdays=anch[tr].astype("datetime64[D]").astype(int); vcut=np.quantile(tdays,0.85); vmask=tdays>vcut
    idx_tr,idx_va=np.where(~vmask)[0],np.where(vmask)[0]; best,best_state,bad,bs=1e9,None,0,256
    for ep in range(epochs):
        net.train(); perm=np.random.permutation(idx_tr)
        for i in range(0,len(perm),bs):
            b=perm[i:i+bs]; opt.zero_grad()
            loss=(((net(Xtr[b],Ctr[b])-Ytr[b])**2)*Mtr[b]).sum()/Mtr[b].sum().clamp(min=1); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            pv=net(Xtr[idx_va],Ctr[idx_va]); vl=((((pv-Ytr[idx_va])**2)*Mtr[idx_va]).sum()/Mtr[idx_va].sum().clamp(min=1)).item()
        if vl<best-1e-4: best,best_state,bad=vl,{k:v.clone() for k,v in net.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience: print(f"[{tag}] early stop @ epoch {ep} (val {best:.4f})",flush=True); break
    if best_state: net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad(): pte=net(Xte,Cte).numpy()*ysd+ymu
    Yte,Mte=Y[te],M[te]; ste=sids[te]; ate=anch[te]
    res={}; predrows=[]
    for i,h in enumerate(H):
        sel=Mte[:,i]>0
        if sel.sum()>5: res[h]=r2(Yte[sel,i],pte[sel,i])
        for j in np.where(sel)[0]:
            predrows.append((ste[j],str(np.datetime64(ate[j],"D")+np.timedelta64(h,"D")),h,float(pte[j,i]),float(Yte[j,i])))
    print(f"[{tag}] per-horizon R²:",{h:round(v,3) for h,v in res.items()},flush=True)
    pd.DataFrame(predrows,columns=["site_id","target_day","h","pred","y"]).to_csv(os.path.join(OUT,"lstm_preds_base.csv"),index=False)
    return res
run()
