#!/usr/bin/env python3
"""Honest NOW, safety-tier, and uncertainty improvement experiments.

This script is intentionally additive: it does not replace the finalized capstone
pipeline. It evaluates candidate changes under leave-whole-sites-out validation
only, and labels whether each category source is deployable:

  full_history : uses held-out site's full PM2.5 history, diagnostic only.
  window60     : uses first 60 observed PM2.5 days, short-deploy setting.
  geodata      : predicts the category from static geodata, zero-deploy setting.

No random split scores are produced here.
"""
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "results", ".mplcache"))

import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import confusion_matrix, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

import features as F

OUT = os.path.join(F.HERE, "results")
SEED = 42
EDGES = [35.4, 55.4]
TIERS = ["Elevated", "High", "Dangerous"]
BANNED = set(F.BANNED)

EXT_PATH = os.path.join(OUT, "external_features.csv")
BLD_PATH = os.path.join(OUT, "building_features.csv")
EXT = pd.read_csv(EXT_PATH) if os.path.exists(EXT_PATH) else None
BLD = pd.read_csv(BLD_PATH) if os.path.exists(BLD_PATH) else None


def band(a):
    return np.clip(np.digitize(np.asarray(a), EDGES), 0, 2)


def add_row_features(df):
    """Only uses row-local weather/calendar and static geodata. No target history."""
    out = df.copy()
    doy = out["day"].dt.dayofyear.astype(float)
    out["doy_sin"] = np.sin(2 * np.pi * doy / 366.0)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 366.0)
    out["month_sin"] = np.sin(2 * np.pi * out["month"].astype(float) / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * out["month"].astype(float) / 12.0)
    out["precip_mm"] = out["precipitation_m"] * 1000.0
    out["is_rain"] = (out["precipitation_m"] > 0).astype(float)
    out = out.sort_values(["site_id", "day"])
    dry = (out["precipitation_m"] <= 1e-6).astype(float)
    out["dry_days_prev7"] = (
        dry.groupby(out["site_id"])
        .transform(lambda s: s.shift(1).rolling(7, min_periods=1).sum())
        .fillna(0.0)
    )
    return out.sort_index()


def site_sigs(df):
    return pd.DataFrame({sid: F.site_signature(g) for sid, g in df.groupby("site_id")}).T


def fit_fold_categories(train_df, k):
    """Fit scaler/centroids on training sites only to avoid held-out-site leakage."""
    sig = site_sigs(train_df)
    sc = StandardScaler().fit(sig[F.SIG_FEATS].values)
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(sc.transform(sig[F.SIG_FEATS].values))
    train_labels = dict(zip(sig.index, km.labels_))
    return sc, km, train_labels


def snap_signature(sig_dict, sc, km):
    v = np.array([[sig_dict[f] for f in F.SIG_FEATS]], dtype=float)
    v = np.where(np.isnan(v), sc.mean_, v)
    vs = sc.transform(v)
    return int(np.argmin(((vs - km.cluster_centers_) ** 2).sum(axis=1)))


def assign_eval_categories(mode, train_df, eval_df, sc, km, train_labels, k):
    if mode == "full_history":
        labels = {sid: snap_signature(F.site_signature(g), sc, km) for sid, g in eval_df.groupby("site_id")}
        return eval_df["site_id"].map(labels).astype(int), np.ones(len(eval_df), dtype=bool)

    if mode == "window60":
        labels, cutoffs = {}, {}
        for sid, g in eval_df.groupby("site_id"):
            g = g.sort_values("day")
            win = g.head(60)
            labels[sid] = snap_signature(F.site_signature(win), sc, km)
            cutoffs[sid] = win.day.max()
        keep = eval_df["day"].values > eval_df["site_id"].map(cutoffs).values
        return eval_df["site_id"].map(labels).astype(int), keep

    if mode == "geodata":
        if EXT is None:
            raise RuntimeError("external_features.csv is required for geodata category mode")
        ext = EXT.set_index("site_id")
        cols = [c for c in EXT.columns if c != "site_id"]
        train_sites = [s for s in sorted(train_df.site_id.unique()) if s in ext.index]
        xtrain = ext.loc[train_sites, cols].fillna(ext[cols].mean())
        ytrain = np.array([train_labels[s] for s in train_sites])
        geo_sc = StandardScaler().fit(xtrain.values)
        knn = KNeighborsClassifier(n_neighbors=min(5, len(train_sites))).fit(geo_sc.transform(xtrain.values), ytrain)
        eval_sites = sorted(eval_df.site_id.unique())
        xeval = ext.loc[eval_sites, cols].fillna(ext[cols].mean())
        pred = dict(zip(eval_sites, knn.predict(geo_sc.transform(xeval.values)).astype(int)))
        return eval_df["site_id"].map(pred).astype(int), np.ones(len(eval_df), dtype=bool)

    raise ValueError(mode)


def attach_static(df):
    out = df.copy()
    if EXT is not None:
        out = out.merge(EXT, on="site_id", how="left")
    if BLD is not None:
        out = out.merge(BLD, on="site_id", how="left")
    return out


def feature_columns(df, k, family):
    cat_cols = []
    for j in range(k):
        c = f"cat_{j}"
        df[c] = (df["site_category"] == j).astype(float)
        cat_cols.append(c)

    cols = list(F.BASE_NOW) + cat_cols

    if family in {"cyclic_weather", "external", "external_interactions", "external_buildings"}:
        cols += ["doy_sin", "doy_cos", "month_sin", "month_cos", "precip_mm", "is_rain", "dry_days_prev7"]

    if family in {"external", "external_interactions", "external_buildings"} and EXT is not None:
        cols += [c for c in EXT.columns if c != "site_id"]

    if family == "external_buildings" and BLD is not None:
        cols += [c for c in BLD.columns if c != "site_id"]

    if family in {"external_interactions", "external_buildings"}:
        for j in range(k):
            df[f"cat{j}_wind"] = df[f"cat_{j}"] * df["wind_speed"]
            df[f"cat{j}_precip"] = df[f"cat_{j}"] * df["precip_mm"]
            cols += [f"cat{j}_wind", f"cat{j}_precip"]
        if "road_len_all_1000m" in df.columns:
            df["road1000_x_wind"] = df["road_len_all_1000m"] * df["wind_speed"]
            cols.append("road1000_x_wind")
        if "elevation_m" in df.columns:
            df["elevation_x_humidity"] = df["elevation_m"] * df["rel_humidity"]
            cols.append("elevation_x_humidity")

    bad = BANNED.intersection(cols)
    if bad:
        raise RuntimeError(f"Banned predictors requested: {sorted(bad)}")
    return cols


def models():
    return {
        "rf_balanced": RandomForestRegressor(
            n_estimators=140, max_depth=22, min_samples_leaf=4,
            max_features="sqrt", n_jobs=1, random_state=SEED
        ),
        "hgb_l2": HistGradientBoostingRegressor(
            max_iter=220, learning_rate=0.05, max_leaf_nodes=31,
            l2_regularization=0.05, random_state=SEED
        ),
    }


def metrics(y, p):
    yb, pb = band(y), band(p)
    danger_true = yb == 2
    danger_pred = pb == 2
    return {
        "r2": r2_score(y, p),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "mae": mean_absolute_error(y, p),
        "exact_tier": float((yb == pb).mean()),
        "within_one_tier": float((np.abs(yb - pb) <= 1).mean()),
        "macro_f1": f1_score(yb, pb, average="macro", zero_division=0),
        "danger_precision": precision_score(danger_true, danger_pred, zero_division=0),
        "danger_recall": recall_score(danger_true, danger_pred, zero_division=0),
    }


def fit_predict_config(df, k, mode, family, model_name):
    gkf = GroupKFold(5)
    yp = np.full(len(df), np.nan)
    yt = np.full(len(df), np.nan)
    fold_rows = []
    mdl = models()[model_name]

    for fold, (tr_i, ev_i) in enumerate(gkf.split(df, df.pm2_5.values, df.site_id.values), start=1):
        tr, ev = df.iloc[tr_i].copy(), df.iloc[ev_i].copy()
        sc, km, train_labels = fit_fold_categories(tr, k)
        tr["site_category"] = tr["site_id"].map(train_labels).astype(int)
        ev_cat, keep = assign_eval_categories(mode, tr, ev, sc, km, train_labels, k)
        ev["site_category"] = ev_cat.values
        ev = ev.loc[keep].copy()

        tr = attach_static(tr)
        ev = attach_static(ev)
        tr = add_row_features(tr)
        ev = add_row_features(ev)

        cols = feature_columns(tr, k, family)
        feature_columns(ev, k, family)
        fill = tr[cols].median(numeric_only=True)
        xtr = tr[cols].fillna(fill)
        xev = ev[cols].fillna(fill)

        model = mdl
        model.fit(xtr, tr.pm2_5.values)
        pred = model.predict(xev)
        yp[ev.index.values] = pred
        yt[ev.index.values] = ev.pm2_5.values
        fm = metrics(ev.pm2_5.values, pred)
        fold_rows.append({"fold": fold, **fm})

    mask = ~np.isnan(yp)
    overall = metrics(yt[mask], yp[mask])
    overall.update({
        "k": k,
        "category_mode": mode,
        "deployability": {
            "full_history": "diagnostic_non_deployable",
            "window60": "short_deploy_pm25_history",
            "geodata": "zero_deploy_static_geodata",
        }[mode],
        "feature_family": family,
        "model": model_name,
        "n_eval": int(mask.sum()),
        "fold_r2": str([round(r["r2"], 3) for r in fold_rows]),
    })
    return overall, yt[mask], yp[mask]


def conformal_eval(df, best):
    """Group-style split conformal: calibration sites are held out inside each train fold."""
    k = int(best["k"])
    mode = best["category_mode"]
    family = best["feature_family"]
    model_name = best["model"]
    alpha = 0.10
    gkf = GroupKFold(5)
    rows = []
    rng = np.random.default_rng(SEED)

    for fold, (tr_i, ev_i) in enumerate(gkf.split(df, df.pm2_5.values, df.site_id.values), start=1):
        tr_all, ev = df.iloc[tr_i].copy(), df.iloc[ev_i].copy()
        train_sites = np.array(sorted(tr_all.site_id.unique()))
        cal_sites = set(rng.choice(train_sites, max(3, len(train_sites) // 4), replace=False))
        proper = tr_all[~tr_all.site_id.isin(cal_sites)].copy()
        cal = tr_all[tr_all.site_id.isin(cal_sites)].copy()

        sc, km, train_labels = fit_fold_categories(proper, k)
        proper["site_category"] = proper["site_id"].map(train_labels).astype(int)

        cal_cat, cal_keep = assign_eval_categories("full_history", proper, cal, sc, km, train_labels, k)
        cal["site_category"] = cal_cat.values
        cal = cal.loc[cal_keep].copy()

        ev_cat, ev_keep = assign_eval_categories(mode, proper, ev, sc, km, train_labels, k)
        ev["site_category"] = ev_cat.values
        ev = ev.loc[ev_keep].copy()

        proper = add_row_features(attach_static(proper))
        cal = add_row_features(attach_static(cal))
        ev = add_row_features(attach_static(ev))

        cols = feature_columns(proper, k, family)
        feature_columns(cal, k, family)
        feature_columns(ev, k, family)
        fill = proper[cols].median(numeric_only=True)

        m = models()[model_name]
        m.fit(proper[cols].fillna(fill), proper.pm2_5.values)
        cal_pred = m.predict(cal[cols].fillna(fill))
        resid = np.abs(cal.pm2_5.values - cal_pred)
        q = float(np.quantile(resid, min(1.0, np.ceil((len(resid) + 1) * (1 - alpha)) / len(resid))))
        pred = m.predict(ev[cols].fillna(fill))
        covered = (ev.pm2_5.values >= pred - q) & (ev.pm2_5.values <= pred + q)
        rows.append({
            "fold": fold,
            "coverage": float(covered.mean()),
            "width": float(2 * q),
            "n_cal": int(len(cal)),
            "n_eval": int(len(ev)),
        })

    out = pd.DataFrame(rows)
    return {
        "task": "NOW",
        "method": "group_conformal_calibration_sites",
        "target_coverage": 0.90,
        "coverage": out["coverage"].mean(),
        "width": out["width"].mean(),
        "config": f"k={k} {mode} {family} {model_name}",
        "folds": str([round(x, 3) for x in out["coverage"]]),
    }


def danger_threshold_table(y, p):
    yb = band(y)
    is_danger = yb == 2
    rows = []
    for cut in np.arange(35, 61, 2.5):
        flag = p > cut
        tp = int((flag & is_danger).sum())
        fp = int((flag & ~is_danger).sum())
        fn = int((~flag & is_danger).sum())
        tn = int((~flag & ~is_danger).sum())
        rows.append({
            "threshold": cut,
            "danger_precision": tp / max(1, tp + fp),
            "danger_recall": tp / max(1, tp + fn),
            "false_alarm_rate": fp / max(1, fp + tn),
        })
    return pd.DataFrame(rows)


def main():
    df = F.load()
    configs = []
    families = ["base_cat", "cyclic_weather", "external", "external_interactions"]
    if BLD is not None:
        families.append("external_buildings")

    # Bounded grid: enough to test the requested levers without making the
    # 39-site GroupKFold experiment impractically expensive.
    for k in [3, 4, 5, 6]:
        for mode in ["full_history", "window60", "geodata"]:
            for family in families:
                for model_name in models().keys():
                    configs.append((k, mode, family, model_name))

    rows = []
    pred_cache = {}
    for i, cfg in enumerate(configs, start=1):
        print(f"[{i}/{len(configs)}] k={cfg[0]} mode={cfg[1]} family={cfg[2]} model={cfg[3]}")
        try:
            row, y, p = fit_predict_config(df, *cfg)
            rows.append(row)
            pred_cache[(row["r2"], cfg)] = (y, p)
        except Exception as e:
            rows.append({
                "k": cfg[0], "category_mode": cfg[1], "feature_family": cfg[2], "model": cfg[3],
                "error": repr(e)
            })

    res = pd.DataFrame(rows).sort_values(["r2", "exact_tier"], ascending=False, na_position="last")
    res.to_csv(os.path.join(OUT, "now_improvement_experiments.csv"), index=False)

    valid = res.dropna(subset=["r2"]).copy()
    deployable = valid[valid["deployability"] != "diagnostic_non_deployable"].copy()
    best = deployable.iloc[0].to_dict() if not deployable.empty else valid.iloc[0].to_dict()
    best_cfg = (int(best["k"]), best["category_mode"], best["feature_family"], best["model"])
    best_key = next(k for k in pred_cache if k[1] == best_cfg)
    y, p = pred_cache[best_key]

    safety = valid[[
        "k", "category_mode", "deployability", "feature_family", "model", "n_eval",
        "r2", "rmse", "mae", "exact_tier", "within_one_tier", "macro_f1",
        "danger_precision", "danger_recall", "fold_r2"
    ]].copy()
    safety.to_csv(os.path.join(OUT, "safety_improvement_experiments.csv"), index=False)

    cm = confusion_matrix(band(y), band(p), labels=[0, 1, 2])
    fig, ax = plt.subplots(figsize=(5.4, 4.4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(TIERS, rotation=25, ha="right")
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(TIERS)
    ax.set_xlabel("Predicted tier"); ax.set_ylabel("True tier")
    ax.set_title("Best NOW safety confusion matrix")
    for r in range(3):
        for c in range(3):
            ax.text(c, r, str(cm[r, c]), ha="center", va="center", color="#111")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_safety_confusion_matrix.png"), dpi=140)
    plt.close(fig)

    thr = danger_threshold_table(y, p)
    thr.to_csv(os.path.join(OUT, "danger_threshold_sweep.csv"), index=False)
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.plot(thr["threshold"], thr["danger_recall"], "o-", label="Dangerous recall")
    ax.plot(thr["threshold"], thr["danger_precision"], "s-", label="Dangerous precision")
    ax.plot(thr["threshold"], thr["false_alarm_rate"], "^-", label="False-alarm rate")
    ax.set_xlabel("Dangerous alert threshold (ug/m3)")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1)
    ax.grid(alpha=.3)
    ax.legend()
    ax.set_title("NOW danger alert threshold sweep")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_danger_recall_precision.png"), dpi=140)
    plt.close(fig)

    unc = pd.DataFrame([conformal_eval(df, best)])
    unc.to_csv(os.path.join(OUT, "uncertainty_calibration.csv"), index=False)
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    ax.scatter(unc["width"], unc["coverage"], s=90)
    ax.axhline(0.90, color="#d43030", linestyle="--", label="90% target")
    ax.set_xlabel("Average interval width (ug/m3)")
    ax.set_ylabel("Empirical coverage")
    ax.set_ylim(0, 1)
    ax.grid(alpha=.3)
    ax.legend()
    ax.set_title("NOW group conformal coverage vs width")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_interval_coverage_width.png"), dpi=140)
    plt.close(fig)

    print("\nBest NOW config:")
    print(valid.head(8).to_string(index=False))
    print("\nWrote now_improvement_experiments.csv, safety_improvement_experiments.csv, uncertainty_calibration.csv")


if __name__ == "__main__":
    main()
