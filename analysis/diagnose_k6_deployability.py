#!/usr/bin/env python3
"""Diagnose why k=6 full-history categories outperform deployable k=6 categories.

Outputs:
  results/k4_k6_cluster_comparison.md
  results/k4_k6_site_assignment_diff.csv
  results/window_length_sensitivity.csv
  results/fig_window_length_sensitivity.png
  results/category_assignment_error_analysis.md
  results/deployable_category_improvement.csv
  results/fig_deployable_category_improvement.png

All model scores use leave-whole-sites-out folds. Full-history category rows are
upper bounds only and are labelled non-deployable.
"""
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "results", ".mplcache"))
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

import features as F

OUT = os.path.join(F.HERE, "results")
SEED = 42
EXT = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]


def rmse(y, p):
    return float(np.sqrt(mean_squared_error(y, p)))


def site_sigs(df):
    return pd.DataFrame({sid: F.site_signature(g) for sid, g in df.groupby("site_id")}).T


def fit_k(df, k):
    sig = site_sigs(df)
    sc = StandardScaler().fit(sig[F.SIG_FEATS].values)
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(sc.transform(sig[F.SIG_FEATS].values))
    lab = dict(zip(sig.index, km.labels_))
    return sig, sc, km, lab


def snap(sig_dict, sc, km):
    v = np.array([[sig_dict[f] for f in F.SIG_FEATS]], float)
    v = np.where(np.isnan(v), sc.mean_, v)
    z = sc.transform(v)
    d = ((z - km.cluster_centers_) ** 2).sum(axis=1)
    return int(d.argmin()), d


def profile(sig, labels):
    p = sig.copy()
    p["cluster"] = p.index.map(labels)
    prof = p.groupby("cluster")[F.SIG_FEATS].mean()
    prof.insert(0, "n_sites", p.groupby("cluster").size())
    return prof.sort_values(["pm25_mean", "windspeed_mean"])


def label_cluster(row, allp):
    pm_rank = int((allp["pm25_mean"] < row["pm25_mean"]).sum()) + 1
    vol = "volatile" if row["pm25_std"] >= allp["pm25_std"].median() else "stable"
    vent = "stagnant" if row["windspeed_mean"] < allp["windspeed_mean"].median() else "ventilated"
    humid = "humid" if row["humidity_mean"] >= allp["humidity_mean"].median() else "drier"
    return f"pollution-rank-{pm_rank} / {vol} / {vent} / {humid}"


def write_cluster_comparison(df):
    sig4, sc4, km4, lab4 = fit_k(df, 4)
    sig6, sc6, km6, lab6 = fit_k(df, 6)
    p4, p6 = profile(sig4, lab4), profile(sig6, lab6)
    p4["behavior_label"] = [label_cluster(r, p4) for _, r in p4.iterrows()]
    p6["behavior_label"] = [label_cluster(r, p6) for _, r in p6.iterrows()]

    ass = pd.DataFrame({
        "site_id": sorted(sig4.index),
        "k4_cluster": [lab4[s] for s in sorted(sig4.index)],
        "k6_cluster": [lab6[s] for s in sorted(sig4.index)],
    })
    ass = ass.merge(sig4.reset_index().rename(columns={"index": "site_id"}), on="site_id")
    ass["k4_label"] = ass["k4_cluster"].map(p4["behavior_label"])
    ass["k6_label"] = ass["k6_cluster"].map(p6["behavior_label"])
    ass["k4_cluster_size"] = ass["k4_cluster"].map(ass.k4_cluster.value_counts())
    ass["k6_cluster_size"] = ass["k6_cluster"].map(ass.k6_cluster.value_counts())
    ass["k6_small_cluster"] = ass["k6_cluster_size"] <= 3
    ass.to_csv(os.path.join(OUT, "k4_k6_site_assignment_diff.csv"), index=False)

    cross = pd.crosstab(ass.k4_cluster, ass.k6_cluster)
    small = ass[ass.k6_small_cluster][["site_id", "k4_cluster", "k6_cluster", "pm25_mean", "pm25_p90", "windspeed_mean", "humidity_mean"]]

    md = []
    md.append("# k=4 vs k=6 Cluster Comparison\n")
    md.append("Both k values are fit on full-site behavioral signatures for diagnosis only. Production scoring must still use fold-safe assignment.\n")
    md.append("## k=4 Profiles\n")
    md.append(p4.round(3).to_markdown())
    md.append("\n## k=6 Profiles\n")
    md.append(p6.round(3).to_markdown())
    md.append("\n## k=4 to k=6 Crosswalk\n")
    md.append(cross.to_markdown())
    md.append("\n## Sites in small k=6 clusters\n")
    md.append(small.round(3).to_markdown(index=False))
    md.append("\n## Interpretation\n")
    md.append("- k=6 is not random noise: it separates higher-resolution pollution/volatility/ventilation regimes that k=4 merges.\n")
    md.append("- The risk is sample size. Several k=6 groups contain only one to three sites, so a full-history category can act like a high-resolution site-regime label.\n")
    md.append("- That explains why k=6 full-history can score well: the oracle category captures mature pollution behavior. The deployable problem is recovering that same fine label from early evidence.\n")
    md.append("- Treat k=6 as meaningful but fragile: useful as an upper-bound research lead, not a production replacement until early-window assignment is reliable or more sites stabilize the small groups.\n")
    open(os.path.join(OUT, "k4_k6_cluster_comparison.md"), "w", encoding="utf-8").write("\n".join(md))
    return p4, p6


def add_features(df, k, mode="hard", distances=None, probs=None):
    out = df.copy()
    cols = list(F.BASE_NOW)
    for j in range(k):
        out[f"cat_{j}"] = (out.site_category == j).astype(float)
        cols.append(f"cat_{j}")
    if mode in ("distance", "soft") and distances is not None:
        for j in range(k):
            out[f"dist_cat_{j}"] = distances[:, j]
            cols.append(f"dist_cat_{j}")
    if mode == "soft" and probs is not None:
        for j in range(k):
            out[f"prob_cat_{j}"] = probs[:, j]
            cols.append(f"prob_cat_{j}")
        top2 = np.sort(probs, axis=1)[:, -2:]
        out["prob_top1"] = top2[:, 1]
        out["prob_top2"] = top2[:, 0]
        cols += ["prob_top1", "prob_top2"]
    return out, cols


def soft_from_distance(d):
    inv = 1.0 / (np.sqrt(np.maximum(d, 1e-9)) + 1e-6)
    return inv / inv.sum(axis=1, keepdims=True)


def train_category_classifier(train_df, train_labels, sc, km, window_n):
    ext = EXT.set_index("site_id")
    rows, y = [], []
    for sid, g in train_df.groupby("site_id"):
        win = g.sort_values("day").head(window_n)
        sig = F.site_signature(win)
        _, d = snap(sig, sc, km)
        feat = [sig[f] for f in F.SIG_FEATS] + list(ext.loc[sid, EXTF].values) + list(d)
        rows.append(feat); y.append(train_labels[sid])
    x = np.asarray(rows, float)
    x = np.where(np.isnan(x), np.nanmedian(x, axis=0), x)
    clf = RandomForestClassifier(n_estimators=200, min_samples_leaf=2, random_state=SEED, class_weight="balanced")
    clf.fit(x, y)
    return clf, np.nanmedian(x, axis=0)


def eval_config(df, k=6, method="full_history", window_n=60):
    gkf = GroupKFold(5)
    pred_rows, site_rows = [], []
    all_y, all_p = [], []
    ext = EXT.set_index("site_id")
    model = HistGradientBoostingRegressor(max_iter=220, learning_rate=0.05, max_leaf_nodes=31, l2_regularization=0.05, random_state=SEED)

    for fold, (tr_i, ev_i) in enumerate(gkf.split(df, df.pm2_5, df.site_id), 1):
        tr0, ev0 = df.iloc[tr_i].copy(), df.iloc[ev_i].copy()
        _, sc, km, train_labels = fit_k(tr0, k)
        tr0["site_category"] = tr0.site_id.map(train_labels).astype(int)
        train_dist = np.vstack([snap(F.site_signature(g), sc, km)[1] for _, g in tr0.groupby("site_id")])
        train_site_order = list(tr0.groupby("site_id").groups.keys())
        train_dist_map = dict(zip(train_site_order, train_dist))

        eval_labels, eval_dist, eval_probs, true_labels, keep = {}, {}, {}, {}, {}
        clf = fill = None
        if method == "classifier_window_geo":
            clf, fill = train_category_classifier(tr0, train_labels, sc, km, window_n)
        if method == "geodata":
            xs = ext.loc[sorted(train_labels), EXTF].fillna(ext[EXTF].mean())
            y = np.array([train_labels[s] for s in sorted(train_labels)])
            gs = StandardScaler().fit(xs.values)
            gclf = KNeighborsClassifier(n_neighbors=min(5, len(y))).fit(gs.transform(xs.values), y)

        for sid, g in ev0.groupby("site_id"):
            true_lab, true_d = snap(F.site_signature(g), sc, km)
            true_labels[sid] = true_lab
            if method == "full_history":
                lab, d = true_lab, true_d
            elif method in ("window", "distance", "soft", "classifier_window_geo"):
                win = g.sort_values("day").head(window_n)
                _, d = snap(F.site_signature(win), sc, km)
                if method == "classifier_window_geo":
                    sig = F.site_signature(win)
                    feat = np.array([sig[f] for f in F.SIG_FEATS] + list(ext.loc[sid, EXTF].values) + list(d), float)
                    feat = np.where(np.isnan(feat), fill, feat).reshape(1, -1)
                    prob = np.zeros(k)
                    cp = clf.predict_proba(feat)[0]
                    for cls, pr in zip(clf.classes_, cp):
                        prob[int(cls)] = pr
                    lab = int(prob.argmax())
                    d = d
                else:
                    lab = int(np.argmin(d))
            elif method == "geodata":
                xg = ext.loc[[sid], EXTF].fillna(ext[EXTF].mean())
                lab = int(gclf.predict(gs.transform(xg.values))[0])
                _, d = snap(F.site_signature(g.sort_values("day").head(min(window_n, len(g)))), sc, km)
            else:
                raise ValueError(method)
            eval_labels[sid], eval_dist[sid] = lab, d
            eval_probs[sid] = soft_from_distance(d.reshape(1, -1))[0]
            keep[sid] = g.day.max() if method == "full_history" else g.sort_values("day").head(window_n).day.max()

        ev0["site_category"] = ev0.site_id.map(eval_labels).astype(int)
        if method != "full_history":
            ev0 = ev0[ev0.day.values > ev0.site_id.map(keep).values].copy()
        if ev0.empty:
            continue

        tr_dist_rows = np.vstack([train_dist_map[sid] for sid in tr0.site_id])
        tr_probs = soft_from_distance(tr_dist_rows)
        ev_dist_rows = np.vstack([eval_dist[sid] for sid in ev0.site_id])
        ev_probs = np.vstack([eval_probs[sid] for sid in ev0.site_id])
        feat_mode = "hard"
        if method == "distance":
            feat_mode = "distance"
        elif method in ("soft", "classifier_window_geo"):
            feat_mode = "soft"
        tr, cols = add_features(tr0, k, feat_mode, tr_dist_rows, tr_probs)
        ev, _ = add_features(ev0, k, feat_mode, ev_dist_rows, ev_probs)
        fillx = tr[cols].median(numeric_only=True)
        model.fit(tr[cols].fillna(fillx), tr.pm2_5.values)
        p = model.predict(ev[cols].fillna(fillx))
        ev = ev.copy(); ev["pred"] = p
        all_y.extend(ev.pm2_5.values); all_p.extend(p)
        for sid, g in ev.groupby("site_id"):
            y, pp = g.pm2_5.values, g.pred.values
            pred_rows.append({
                "site_id": sid, "fold": fold, "method": method, "window_days": window_n,
                "true_full_category": true_labels[sid], "assigned_category": eval_labels[sid],
                "category_correct": true_labels[sid] == eval_labels[sid],
                "rmse": rmse(y, pp), "mae": mean_absolute_error(y, pp), "bias": float(np.mean(pp - y)),
            })
    y, p = np.asarray(all_y), np.asarray(all_p)
    return {
        "method": method, "window_days": window_n, "k": k, "deployability": "non_deployable_upper_bound" if method == "full_history" else ("zero_deploy" if method == "geodata" else "short_deploy"),
        "r2": r2_score(y, p), "rmse": rmse(y, p), "mae": mean_absolute_error(y, p),
        "n_eval": len(y),
    }, pd.DataFrame(pred_rows)


def main():
    df = F.load()
    write_cluster_comparison(df)

    rows, site_all = [], []
    # upper bounds / fixed baselines
    for method, w in [("full_history", 0), ("geodata", 60), ("window", 60), ("distance", 60), ("soft", 60), ("classifier_window_geo", 60)]:
        r, s = eval_config(df, 6, method, w)
        rows.append(r); site_all.append(s)

    # window length sensitivity for hard category labels
    win_rows = []
    for w in [14, 30, 45, 60, 90, 120]:
        r, s = eval_config(df, 6, "window", w)
        win_rows.append(r); site_all.append(s)
    win = pd.DataFrame(win_rows)
    win.to_csv(os.path.join(OUT, "window_length_sensitivity.csv"), index=False)

    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    ax1.plot(win.window_days, win.r2, "o-", label="R2")
    ax1.set_xlabel("Early deploy window (days)")
    ax1.set_ylabel("Leave-site-out R2")
    ax1.grid(alpha=.3)
    ax2 = ax1.twinx()
    ax2.plot(win.window_days, win.rmse, "s--", color="#d43030", label="RMSE")
    ax2.set_ylabel("RMSE")
    fig.suptitle("k=6 deployable window length sensitivity")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_window_length_sensitivity.png"), dpi=140)
    plt.close(fig)

    res = pd.DataFrame(rows + win_rows)
    # External accepted baselines as reference rows, not rerun here.
    res = pd.concat([pd.DataFrame([
        {"method": "accepted_k4_baseline_reference", "window_days": np.nan, "k": 4, "deployability": "accepted_reference", "r2": 0.564, "rmse": np.nan, "mae": np.nan, "n_eval": np.nan},
        {"method": "accepted_k4_safety_reference", "window_days": np.nan, "k": 4, "deployability": "accepted_reference", "r2": 0.558, "rmse": np.nan, "mae": np.nan, "n_eval": np.nan},
    ]), res], ignore_index=True)
    res.to_csv(os.path.join(OUT, "deployable_category_improvement.csv"), index=False)

    plot = res[~res.method.str.contains("reference")].copy()
    plot["label"] = plot.method + plot.window_days.fillna(0).astype(int).astype(str).radd(" / w=")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = ["#9aa0a6" if d == "non_deployable_upper_bound" else "#14A38B" for d in plot.deployability]
    ax.barh(plot["label"], plot["r2"], color=colors)
    ax.axvline(0.564, color="#d43030", linestyle="--", label="accepted k4 reference ~0.564")
    ax.set_xlabel("NOW leave-site-out R2")
    ax.set_title("Deployable category inference variants vs k=6 upper bound")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_deployable_category_improvement.png"), dpi=140)
    plt.close(fig)

    site = pd.concat(site_all, ignore_index=True)
    # Keep one row per site/method/window, including repeated window rows.
    site.to_csv(os.path.join(OUT, "category_assignment_site_errors.csv"), index=False)

    w60 = site[(site.window_days == 60) | (site.method == "full_history")]
    wrong = w60[(w60.method != "full_history") & (~w60.category_correct)]
    md = []
    md.append("# Category Assignment Error Analysis\n")
    md.append("k=6 full-history is an upper bound. All window rows use only the first N observed days and evaluate after that window.\n")
    md.append("## Performance Summary\n")
    md.append(res.round(4).to_markdown(index=False))
    md.append("\n## Window-60 wrong category assignments\n")
    md.append(wrong.sort_values(["method", "rmse"], ascending=[True, False]).round(3).to_markdown(index=False))
    md.append("\n## Diagnosis\n")
    md.append("- The full-history k=6 label captures mature pollution level, volatility, seasonality, and ventilation. Early windows often do not contain enough seasonal variation to recover the fine label.\n")
    md.append("- Moving from 14 to 120 days tests whether this is just a short-window problem. If R2 does not approach the full-history upper bound, the gap is also caused by unstable small clusters and category noise.\n")
    md.append("- Distance/probability features reduce hard-routing brittleness in principle, but they must beat the accepted k=4 reference before being promoted.\n")
    md.append("- Geodata-only category inference remains zero-deploy, but it cannot observe the local PM2.5 regime and should be treated as a weak prior, not a true category.\n")
    open(os.path.join(OUT, "category_assignment_error_analysis.md"), "w", encoding="utf-8").write("\n".join(md))
    print(res.sort_values("r2", ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
