#!/usr/bin/env python3
"""
eval_external.py — does free urban-planning geodata break the homogeneity ceiling?

CP-B/CP-D showed the category lifts new-site R² (+0.16) but the category itself needs a 60-day
deploy to estimate (wrong 41% of the time when cheap). External LUR features (road density,
distance to major road, elevation) are STATIC and need ZERO pollution observations. Two tests:

  TEST 1 — can external features REPLACE the category for a sensor-less site? new-site R²
           (GroupKFold5) for: blind | +external | +cat | +cat+external. If +external >= +cat,
           geodata gives the site-level signal with no deploy at all (strictly better story).
  TEST 2 — do external features PREDICT the category? leave-one-site-out classification of
           site_category from geodata. If accurate, a sensor-less site can be categorized from
           geodata alone -> fixes the Tier-B noise problem.
  + which feature carries the signal (corr with per-site PM2.5 mean).

Outputs -> results/eval_external.csv, results/fig_external.png
Run: ../../../working/.venv/bin/python eval_external.py   (needs results/external_features.csv)
"""
import os, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import r2_score, accuracy_score
import xgboost as xgb
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EXTPATH = os.path.join(OUT, "external_features.csv")

def mk(): return xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED)

def main():
    if not os.path.exists(EXTPATH):
        print("external_features.csv missing — run fetch_external.py first."); return
    df = F.load(); cat = F.load_categorizer()
    df["site_category"] = df.site_id.map(F.assign_full_categories(df, cat))
    ext = pd.read_csv(EXTPATH)
    EXTF = [c for c in ext.columns if c != "site_id"]
    df = df.merge(ext, on="site_id", how="left")
    print("external features:", EXTF)

    # ---- which external feature explains site pollution LEVEL? ----
    persite = df.groupby("site_id").agg(pm25_mean=("pm2_5", "mean"), cat=("site_category", "first")).join(
        ext.set_index("site_id"))
    print("\ncorrelation of each external feature with per-site PM2.5 mean:")
    for c in EXTF:
        print(f"  {c:22s} r = {persite['pm25_mean'].corr(persite[c]):+.3f}")

    gkf = GroupKFold(5); g = df.site_id.values; folds = list(gkf.split(df, df.pm2_5.values, g))
    def onehot(d):
        return pd.concat([d, pd.DataFrame({f"cat_{c}": (d.site_category == c).astype(float)
                                           for c in range(3)}, index=d.index)], axis=1)
    cat_cols = ["cat_0", "cat_1", "cat_2"]
    VARIANTS = {
        "blind":          F.BASE_NOW,
        "+external":      F.BASE_NOW + EXTF,                 # ZERO pollution obs needed
        "+cat":           F.BASE_NOW + cat_cols,             # needs 60-day deploy
        "+cat+external":  F.BASE_NOW + cat_cols + EXTF,
    }
    rows = []
    print("\nTEST 1 — new-site R² (leave-sites-out):")
    for name, cols in VARIANTS.items():
        sc = []
        for tr_i, ev_i in folds:
            tr, ev = onehot(df.iloc[tr_i]), onehot(df.iloc[ev_i])
            m = mk(); m.fit(tr[cols], tr.pm2_5.values); sc.append(r2_score(ev.pm2_5.values, m.predict(ev[cols])))
        rows.append(dict(test="newsite_r2", variant=name, score=round(float(np.mean(sc)), 4),
                         std=round(float(np.std(sc)), 4)))
        print(f"  {name:16s} R² = {np.mean(sc):.4f} ± {np.std(sc):.3f}")

    # ---- TEST 2: predict category from geodata (leave-one-site-out) ----
    print("\nTEST 2 — classify site_category from external geodata (leave-one-site-out):")
    Xs = persite[EXTF].fillna(persite[EXTF].mean()).values
    ys = persite["cat"].values
    logo = LeaveOneGroupOut(); groups = np.arange(len(persite))
    preds = np.empty(len(ys), int)
    for tr_i, te_i in logo.split(Xs, ys, groups):
        clf = RandomForestClassifier(n_estimators=300, random_state=SEED)
        clf.fit(Xs[tr_i], ys[tr_i]); preds[te_i] = clf.predict(Xs[te_i])
    acc = accuracy_score(ys, preds)
    base = pd.Series(ys).value_counts(normalize=True).max()   # majority-class baseline
    print(f"  LOO accuracy = {acc:.3f}  (majority-class baseline {base:.3f})")
    print(f"  -> geodata {'CAN' if acc > base + 0.1 else 'CANNOT'} reliably recover the category for a sensor-less site")
    rows.append(dict(test="cat_from_geodata_acc", variant="RF_LOO", score=round(float(acc), 4),
                     std=round(float(base), 4)))

    res = pd.DataFrame(rows); res.to_csv(os.path.join(OUT, "eval_external.csv"), index=False)

    # ---- figure ----
    t1 = res[res.test == "newsite_r2"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    colors = ["#9aa0a6", "#3B7DD8", "#14A38B", "#0E7C66"]
    ax.bar(t1.variant, t1.score, yerr=t1["std"], color=colors, error_kw=dict(ecolor="#555", lw=1))
    ax.axhline(t1[t1.variant == "blind"].score.iloc[0], ls="--", color="#d43030", lw=1, label="blind anchor")
    ax.set_ylabel("new-site R²"); ax.set_title("Can free geodata replace a sensor deploy?\n(+external needs ZERO pollution observations)")
    ax.legend(fontsize=8); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_external.png"), dpi=130); plt.close(fig)
    print("\nwrote results/eval_external.csv · results/fig_external.png")

if __name__ == "__main__":
    main()
