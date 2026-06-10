#!/usr/bin/env python3
"""
finalize_now.py — CP-F: persist the production NOW models + consolidate the headline numbers.

Trains the two production nowcast models on ALL site-days and pickles them to models/:
  now_rf_cat.pkl        RandomForest on weather+loc+calendar+site_category   (best learner, deploy)
  now_xgb_cat_ext.pkl   XGBoost on the above + free geodata (best feature set, lowest variance)
Both ship with a feature manifest so a new site is scored by: categorize (categorizer.json) ->
attach geodata (external_features.csv / re-fetch for a new lat-lon) -> predict.

Also writes results/FINDINGS_summary.csv: one tidy table of every headline honest number,
pulled from the per-experiment CSVs (single source of truth for decks/report).

Run: ../../../working/.venv/bin/python finalize_now.py
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score
import xgboost as xgb
import features as F

OUT = os.path.join(F.HERE, "results"); MDIR = os.path.join(F.HERE, "models"); os.makedirs(MDIR, exist_ok=True)
SEED = 42

def main():
    df = F.load(); cat = F.load_categorizer()
    df["site_category"] = df.site_id.map(F.assign_full_categories(df, cat))
    for c in range(3): df[f"cat_{c}"] = (df.site_category == c).astype(float)
    cat_cols = ["cat_0", "cat_1", "cat_2"]
    y = df.pm2_5.values

    # production model 1: RF + category. min_samples_leaf=4 bounds the model size (an unpruned
    # depth-30 RF on 14k rows pickles to ~0.5 GB — impractical) and is a sane deploy config; we
    # VERIFY its honest new-site R² is unchanged vs the bake-off (max_depth=30, msl=1 -> 0.529).
    f1 = F.BASE_NOW + cat_cols
    rf_kw = dict(n_estimators=400, max_depth=30, max_features="sqrt", min_samples_leaf=4,
                 n_jobs=-1, random_state=SEED)
    gkf = GroupKFold(5); folds = list(gkf.split(df, y, df.site_id.values))
    ns = [r2_score(y[ev], RandomForestRegressor(**rf_kw).fit(df[f1].values[tr], y[tr]).predict(df[f1].values[ev]))
          for tr, ev in folds]
    print(f"deploy-RF (min_samples_leaf=4) new-site R² = {np.mean(ns):.3f} (bake-off msl=1 was 0.529)")
    rf = RandomForestRegressor(**rf_kw).fit(df[f1], y)
    joblib.dump({"model": rf, "features": f1, "kind": "RF +category (msl=4)",
                 "newsite_r2": round(float(np.mean(ns)), 3)},
                os.path.join(MDIR, "now_rf_cat.joblib"), compress=3)

    # production model 2: XGB + category + geodata (if external features available)
    extp = os.path.join(OUT, "external_features.csv"); saved2 = None
    if os.path.exists(extp):
        ext = pd.read_csv(extp); EXTF = [c for c in ext.columns if c != "site_id"]
        d2 = df.merge(ext, on="site_id", how="left"); f2 = F.BASE_NOW + cat_cols + EXTF
        xg = xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05, subsample=0.8,
                              colsample_bytree=0.8, n_jobs=-1, random_state=SEED).fit(d2[f2], y)
        joblib.dump({"model": xg, "features": f2, "kind": "XGB +category+geodata"},
                    os.path.join(MDIR, "now_xgb_cat_ext.joblib"), compress=3)
        saved2 = "now_xgb_cat_ext.joblib"

    # ---- consolidate headline numbers into one tidy table ----
    rows = []
    def add(metric, setup, test, score, note=""):
        rows.append(dict(metric=metric, setup=setup, honest_test=test, score=score, note=note))
    nowp = pd.read_csv(os.path.join(OUT, "pipeline_now.csv"))
    g = lambda rung, var: float(nowp[(nowp.rung == rung) & (nowp.variant == var)].r2.iloc[0])
    add("NOW", "blind pooled", "leave-sites-out (cat=full sig)", round(g("2A_newsite_fullsig", "blind"), 3), "the 3rd-cap collapse")
    add("NOW", "+category", "leave-sites-out (cat=full sig)", round(g("2A_newsite_fullsig", "+cat"), 3), "the reframe win")
    add("NOW", "+category", "leave-sites-out (cat=60d deploy)", round(g("2B_newsite_window", "+cat"), 3), "realistic cold-start")
    add("NOW", "MoE", "leave-sites-out (cat=60d deploy)", round(g("2B_newsite_window", "moe"), 3), "collapses — killed")
    add("NOW", "+category", "leave-CATEGORY-out", round(g("3_leavecatout", "+cat"), 3), "ceiling: unseen regime")
    if os.path.exists(os.path.join(OUT, "eval_external.csv")):
        ev = pd.read_csv(os.path.join(OUT, "eval_external.csv"))
        ge = lambda v: float(ev[(ev.test == "newsite_r2") & (ev.variant == v)].score.iloc[0])
        add("NOW", "+geodata only (0 obs)", "leave-sites-out", round(ge("+external"), 3), "zero-deploy lever")
        add("NOW", "+category+geodata", "leave-sites-out", round(ge("+cat+external"), 3), "best + most stable")
    bo = pd.read_csv(os.path.join(OUT, "bakeoff_now.csv"))
    for _, r in bo[bo.model.isin(["RandomForest", "XGBoost", "LightGBM", "CatBoost"])].iterrows():
        add("NOW", f"{r.model} (+cat)", "leave-sites-out", round(r.newsite_r2, 3), "model bake-off")
    fu = pd.read_csv(os.path.join(OUT, "bakeoff_future.csv"))
    for _, r in fu.iterrows():
        best = max([(c, r[c]) for c in ["persistence", "XGBoost", "LightGBM", "LSTM"] if pd.notna(r.get(c))], key=lambda x: x[1])
        add("FUTURE", f"+{r.horizon}d: persistence={r.persistence:.2f}", "purged chronological",
            round(float(r.get("LSTM", np.nan)), 3) if pd.notna(r.get("LSTM")) else round(r.LightGBM, 3),
            f"best={best[0]} ({best[1]:.2f})")
    summ = pd.DataFrame(rows); summ.to_csv(os.path.join(OUT, "FINDINGS_summary.csv"), index=False)

    print("saved models/now_rf_cat.joblib", "+ " + saved2 if saved2 else "(no geodata model — run fetch_external.py)")
    print(f"wrote results/FINDINGS_summary.csv  ({len(summ)} rows)")
    print(summ.to_string(index=False))

if __name__ == "__main__":
    main()
