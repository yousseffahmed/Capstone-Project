#!/usr/bin/env python3
"""
lstm_future.py — the FUTURE-metric LSTM, in its OWN process (OpenMP isolation).

Runs AFTER bakeoff_future.py. Imports ONLY torch + numpy/pandas/matplotlib + features (no
xgboost/lightgbm, no sklearn) so PyTorch's bundled OpenMP never collides with the GBM libs'
libomp on macOS (pytorch/pytorch#44282). Reads results/bakeoff_future.csv, fills the LSTM
column, re-saves, redraws results/fig_bakeoff_future.png with all methods.

Model = one GLOBAL LSTM over each site's past-L-day sequence + a category EMBEDDING, with a
masked multi-horizon head predicting +1..+7 at once (STRATEGY default: global net + embedding
over per-site nets — more data per parameter). Sequences run on each site's daily-complete
calendar; gappy PM2.5 is forward-filled with an explicit observed-mask channel; features are
standardized on TRAIN days only. Honest test = same chronological split as the GBMs.

Run: ../../../working/.venv/bin/python lstm_future.py
"""
import os, warnings; warnings.filterwarnings("ignore")
import torch, torch.nn as nn          # torch FIRST so its OpenMP loads before anything else
torch.set_num_threads(4)
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
HORIZONS = [1, 2, 3, 4, 5, 6, 7]
torch.manual_seed(SEED); np.random.seed(SEED)

def r2(y, p):                          # manual R² — no sklearn import (OpenMP hygiene)
    y, p = np.asarray(y, float), np.asarray(p, float)
    ss = ((y - p) ** 2).sum(); st = ((y - y.mean()) ** 2).sum()
    return float(1 - ss / st) if st > 0 else float("nan")

def main(L=14, hidden=48, emb=4, epochs=40, patience=6):
    df = F.load(); cat = F.load_categorizer(); site_cat = F.assign_full_categories(df, cat)
    cut = df["day"].quantile(0.8); cutd = np.datetime64(cut)
    SEQ = ["pm2_5", "temp_2m_K", "dewpoint_2m_K", "wind_u_10m_ms", "wind_v_10m_ms",
           "surface_pressure_Pa", "precipitation_m", "rel_humidity", "wind_speed"]

    # ---- build per-site daily-complete sequences ----
    samples = []   # (cat_id, X[L,feat], y[7], ymask[7], anchor_day)
    for sid, g in df.groupby("site_id"):
        g = g.set_index("day").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="D")
        g = g.reindex(full)
        obs = g.pm2_5.notna().values.astype(float)
        feat = g[SEQ].copy()
        feat["pm2_5"] = feat["pm2_5"].ffill().bfill()
        for c in SEQ[1:]:
            feat[c] = feat[c].interpolate(limit_direction="both")
        feat["obs_mask"] = obs
        arr = feat.values.astype(np.float32)
        y = g.pm2_5.values.astype(np.float32); days = np.array(full); c_id = site_cat[sid]
        for t in range(L - 1, len(g) - 1):
            yh = np.full(7, np.nan, np.float32); ym = np.zeros(7, np.float32)
            for i, h in enumerate(HORIZONS):
                if t + h < len(g) and obs[t + h]:
                    yh[i] = y[t + h]; ym[i] = 1.0
            if ym.sum() == 0 or not obs[t]:
                continue
            samples.append((c_id, arr[t - L + 1:t + 1], np.nan_to_num(yh), ym, days[t]))
    print(f"built {len(samples)} sequences (L={L}); features/step={samples[0][1].shape[1]}")

    cats = np.array([s[0] for s in samples])
    X = np.stack([s[1] for s in samples]); Y = np.stack([s[2] for s in samples])
    M = np.stack([s[3] for s in samples]); anch = np.array([s[4] for s in samples])
    # PURGE by max horizon: a train anchor's farthest target (t+7) must also be pre-cut, else the
    # multi-horizon head peeks across the chronological boundary. Test = anchor strictly after cut.
    tr = (anch + np.timedelta64(7, "D")) <= cutd; te = anch > cutd
    mu = X[tr].reshape(-1, X.shape[-1]).mean(0); sd = X[tr].reshape(-1, X.shape[-1]).std(0) + 1e-6
    Xn = (X - mu) / sd
    ymu, ysd = Y[tr][M[tr] > 0].mean(), Y[tr][M[tr] > 0].std() + 1e-6
    to = lambda a: torch.tensor(a, dtype=torch.float32)
    Xtr, Ytr, Mtr, Ctr = to(Xn[tr]), to((Y[tr] - ymu) / ysd), to(M[tr]), torch.tensor(cats[tr])
    Xte = to(Xn[te]); Cte = torch.tensor(cats[te])

    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.lstm = nn.LSTM(X.shape[-1], hidden, batch_first=True)
            s.emb = nn.Embedding(3, emb)
            s.head = nn.Sequential(nn.Linear(hidden + emb, 32), nn.ReLU(), nn.Linear(32, 7))
        def forward(s, x, c):
            _, (hn, _) = s.lstm(x); return s.head(torch.cat([hn[-1], s.emb(c)], 1))

    net = Net(); opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-5)
    tdays = anch[tr].astype("datetime64[D]").astype(int)
    vcut = np.quantile(tdays, 0.85); vmask = tdays > vcut
    idx_tr, idx_va = np.where(~vmask)[0], np.where(vmask)[0]
    best, best_state, bad, bs = 1e9, None, 0, 256
    for ep in range(epochs):
        net.train(); perm = np.random.permutation(idx_tr)
        for i in range(0, len(perm), bs):
            b = perm[i:i + bs]; opt.zero_grad()
            loss = (((net(Xtr[b], Ctr[b]) - Ytr[b]) ** 2) * Mtr[b]).sum() / Mtr[b].sum().clamp(min=1)
            loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            pv = net(Xtr[idx_va], Ctr[idx_va])
            vl = ((((pv - Ytr[idx_va]) ** 2) * Mtr[idx_va]).sum() / Mtr[idx_va].sum().clamp(min=1)).item()
        if vl < best - 1e-4: best, best_state, bad = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience:
                print(f"early stop @ epoch {ep} (val {best:.4f})"); break
    if best_state: net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        pte = net(Xte, Cte).numpy() * ysd + ymu
    Yte, Mte = Y[te], M[te]
    lstm_r2 = {}
    for i, h in enumerate(HORIZONS):
        sel = Mte[:, i] > 0
        if sel.sum() > 5: lstm_r2[h] = r2(Yte[sel, i], pte[sel, i])
    print("LSTM per-horizon R²:", {h: round(v, 3) for h, v in lstm_r2.items()})

    # ---- persist the production forecaster ----
    mdir = os.path.join(F.HERE, "models"); os.makedirs(mdir, exist_ok=True)
    torch.save({"state_dict": net.state_dict(), "config": dict(L=L, hidden=hidden, emb=emb),
                "feat_order": SEQ + ["obs_mask"], "feat_mu": mu, "feat_sd": sd,
                "y_mu": float(ymu), "y_sd": float(ysd), "horizons": HORIZONS},
               os.path.join(mdir, "lstm_future.pt"))
    print("saved models/lstm_future.pt")

    # ---- merge into bakeoff_future.csv + redraw figure ----
    csv = os.path.join(OUT, "bakeoff_future.csv")
    res = pd.read_csv(csv)
    res["LSTM"] = res.horizon.map(lstm_r2)
    res.to_csv(csv, index=False)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for col, c, mk in [("persistence", "#d43030", "o"), ("XGBoost", "#14A38B", "s"),
                       ("LightGBM", "#0E7C66", "^"), ("LSTM", "#E8A020", "D")]:
        if col in res and res[col].notna().any():
            ax.plot(res.horizon, res[col], mk + "-", color=c, label=col, lw=2)
    ax.axhline(0, color="k", lw=.8, ls=":")
    ax.set_xlabel("forecast horizon (days ahead)"); ax.set_ylabel("R² (chronological, out-of-time)")
    ax.set_title("FUTURE bake-off — must beat persistence; LSTM must beat the GBMs")
    ax.legend(fontsize=9); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_bakeoff_future.png"), dpi=130); plt.close(fig)
    print("updated results/bakeoff_future.csv + results/fig_bakeoff_future.png with LSTM")

if __name__ == "__main__":
    main()
