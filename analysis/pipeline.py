#!/usr/bin/env python3
"""
pipeline.py — CP-B: the NOW (nowcast) honest ladder. categorize -> route -> predict.

The one question: does a categorize-then-predict pipeline beat the BLIND pooled model when
we point it at a site it has never seen? We answer it on the 3-rung honest ladder, climbing
only if the rung below holds (STRATEGY 3.2 / DECISION_LOG D4):

  RUNG 1  random 80/20 (leaky, forgiving)        -> go/no-go: does the architecture run + signal?
  RUNG 2  leave-sites-out, GroupKFold(5)          -> the honest NOW test (within-category cold-start)
            tier A: held-out site's category from its FULL signature (static attribute known)
            tier B: held-out site's category from its FIRST 60 observed days (cold-start deploy);
                    eval only on the post-window rows -> no target leak (DECISION_LOG D3)
  RUNG 3  leave-CATEGORY-out (hold out a whole regime) -> true across-category cold-start

Routing variants compared at each rung:
  blind        BASE_NOW only (weather+loc+cal+eng)            <- the bar to beat
  +cat         BASE_NOW + site_category one-hot               <- category as a feature (default)
  +cat+prior   +cat + leak-free cat x month PM2.5 prior + weather anomalies
  moe          one XGBoost per category (mixture of experts)  <- A/B variant

Outputs -> results/pipeline_now.csv, results/fig_now_ladder.png
Run: ../../../working/.venv/bin/python pipeline.py
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb
import features as F

OUT = os.path.join(F.HERE, "results")
SEED = 42

def mk():
    return xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=SEED)

def onehot_cat(df, k=3):
    return pd.DataFrame({f"cat_{c}": (df.site_category == c).astype(float) for c in range(k)},
                        index=df.index)

def r2(y, p):
    return r2_score(y, p)

# ---------------------------------------------------------------------------
# one fit/eval given train & eval frames + a variant name -> R2 on eval
# ---------------------------------------------------------------------------
def fit_eval(variant, tr, ev):
    ytr, yev = tr.pm2_5.values, ev.pm2_5.values
    if variant == "blind":
        Xtr, Xev = tr[F.BASE_NOW], ev[F.BASE_NOW]
        m = mk(); m.fit(Xtr, ytr); return r2(yev, m.predict(Xev))

    if variant in ("+cat", "+cat+prior"):
        tr2, ev2 = tr.copy(), ev.copy()
        cols = list(F.BASE_NOW)
        ohc = onehot_cat(tr2); ohe = onehot_cat(ev2)
        tr2 = pd.concat([tr2, ohc], axis=1); ev2 = pd.concat([ev2, ohe], axis=1)
        cols += list(ohc.columns)
        if variant == "+cat+prior":
            tr2, ev2, newc = F.add_category_priors(tr2, ev2)
            cols += newc
        m = mk(); m.fit(tr2[cols], ytr); return r2(yev, m.predict(ev2[cols]))

    if variant == "moe":
        # one expert per category (+ leak-free prior); fall back to a global model if a
        # category has no training rows in this fold.
        tr2, ev2, newc = F.add_category_priors(tr.copy(), ev.copy())
        cols = list(F.BASE_NOW) + newc
        glob = mk(); glob.fit(tr2[cols], ytr)                     # fallback expert
        experts = {}
        for c in sorted(tr2.site_category.unique()):
            sub = tr2[tr2.site_category == c]
            if len(sub) >= 50:
                e = mk(); e.fit(sub[cols], sub.pm2_5.values); experts[c] = e
        pred = np.empty(len(ev2))                                  # batch-predict per category
        ev2 = ev2.reset_index(drop=True)
        for c in ev2.site_category.unique():
            sel = (ev2.site_category == c).values
            e = experts.get(c, glob)
            pred[sel] = e.predict(ev2.loc[sel, cols])
        return r2(yev, pred)
    raise ValueError(variant)

VARIANTS = ["blind", "+cat", "+cat+prior", "moe"]

# ===========================================================================
def main():
    df = F.load(); cat = F.load_categorizer()
    full_cat = F.assign_full_categories(df, cat)
    df["site_category"] = df.site_id.map(full_cat)
    rows = []

    # ---- RUNG 1: random 80/20, 10 seeds -----------------------------------
    print("=" * 72); print("RUNG 1 — random 80/20 (leaky, forgiving go/no-go)"); print("=" * 72)
    idx = np.arange(len(df))
    for v in VARIANTS:
        scores = []
        for s in range(10):
            tr_i, ev_i = train_test_split(idx, test_size=0.2, random_state=s)
            scores.append(fit_eval(v, df.iloc[tr_i], df.iloc[ev_i]))
        m = float(np.mean(scores))
        rows.append(dict(rung="1_random", variant=v, r2=round(m, 4), note="10-seed mean"))
        print(f"  {v:12s} R2 = {m:.4f}")

    # ---- RUNG 2 tier A: leave-sites-out, category from FULL signature ------
    print("\n" + "=" * 72); print("RUNG 2A — leave-sites-out (GroupKFold5), category = FULL signature"); print("=" * 72)
    gkf = GroupKFold(5); g = df.site_id.values
    folds = list(gkf.split(df, df.pm2_5.values, g))
    for v in VARIANTS:
        scores = [fit_eval(v, df.iloc[tr_i], df.iloc[ev_i]) for tr_i, ev_i in folds]
        m = float(np.mean(scores))
        rows.append(dict(rung="2A_newsite_fullsig", variant=v, r2=round(m, 4),
                         note=f"folds={[round(x,3) for x in scores]}"))
        print(f"  {v:12s} R2 = {m:.4f}   folds={[round(x,3) for x in scores]}")

    # ---- RUNG 2 tier B: leave-sites-out, category from 60-day window -------
    print("\n" + "=" * 72); print("RUNG 2B — leave-sites-out, category = first-60-day window (cold-start deploy)"); print("=" * 72)
    win_cat, cutoffs = F.assign_window_categories(df, cat, 60)
    # how often does the cheap window category match the full-history one?
    agree = np.mean([win_cat[s] == full_cat[s] for s in full_cat])
    print(f"  [diagnostic] window-vs-full category agreement = {agree:.2f} "
          f"(a new site's cheaply-estimated category is wrong {100*(1-agree):.0f}% of the time)")
    rows.append(dict(rung="2B_diag", variant="cat_recovery", r2=round(float(agree), 4),
                     note="frac sites whose 60-day-window category == full-signature category"))
    # precompute per-fold (train, window-categorized + warm-up-dropped eval) once
    cut_arr = df.site_id.map(cutoffs); win_arr = df.site_id.map(win_cat)
    folds_B = []
    for tr_i, ev_i in folds:
        tr = df.iloc[tr_i]
        ev = df.iloc[ev_i].copy()
        ev["site_category"] = win_arr.iloc[ev_i].values        # held-out site's cheap category
        ev = ev[ev.day.values > cut_arr.iloc[ev_i].values]     # drop the warm-up window
        folds_B.append((tr, ev))
    for v in VARIANTS:
        scores = [fit_eval(v, tr, ev) for tr, ev in folds_B]
        m = float(np.mean(scores))
        rows.append(dict(rung="2B_newsite_window", variant=v, r2=round(m, 4),
                         note=f"folds={[round(x,3) for x in scores]}"))
        print(f"  {v:12s} R2 = {m:.4f}   folds={[round(x,3) for x in scores]}")

    # ---- RUNG 3: leave-CATEGORY-out (whole regime unseen) -----------------
    print("\n" + "=" * 72); print("RUNG 3 — leave-CATEGORY-out (true across-category cold-start)"); print("=" * 72)
    for v in VARIANTS:
        scores = []
        for c in sorted(df.site_category.unique()):
            tr = df[df.site_category != c]; ev = df[df.site_category == c]
            scores.append(fit_eval(v, tr, ev))
        m = float(np.mean(scores))
        rows.append(dict(rung="3_leavecatout", variant=v, r2=round(m, 4),
                         note=f"per-cat={[round(x,3) for x in scores]}"))
        print(f"  {v:12s} R2 = {m:.4f}   per-cat={[round(x,3) for x in scores]}")

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT, "pipeline_now.csv"), index=False)

    # ---- figure: blind vs categorized across the honest rungs -------------
    plot_rungs = ["1_random", "2A_newsite_fullsig", "2B_newsite_window", "3_leavecatout"]
    labels = ["random\n(leaky)", "new-site\n(cat=full sig)", "new-site\n(cat=60d window)", "leave-\ncategory-out"]
    piv = res[res.variant.isin(VARIANTS)].pivot(index="rung", columns="variant", values="r2").reindex(plot_rungs)[VARIANTS]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(plot_rungs)); w = 0.2
    colors = {"blind": "#9aa0a6", "+cat": "#14A38B", "+cat+prior": "#0E7C66", "moe": "#E8A020"}
    for i, v in enumerate(VARIANTS):
        ax.bar(x + (i - 1.5) * w, piv[v].values, w, label=v, color=colors[v])
    ax.axhline(0, color="k", lw=.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("R²"); ax.set_title("NOW metric — does categorization beat the blind pooled model?\n(climb the honest ladder left → right)")
    ax.legend(title="routing", fontsize=8, ncol=4, loc="upper right"); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_now_ladder.png"), dpi=130); plt.close(fig)

    print(f"\nwrote results/pipeline_now.csv · results/fig_now_ladder.png")
    return res

if __name__ == "__main__":
    main()
