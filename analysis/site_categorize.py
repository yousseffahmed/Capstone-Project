#!/usr/bin/env python3
"""
site_categorize.py — PROOF EXPERIMENT for the 4th-cap reframe.

The problem (from 3rd cap): testing the model on a brand-new site BLINDLY collapses it
(leave-sites-out R2 ~0.31, one fold near 0). A new site is a stranger; the model has
never seen a place like it.

The fix (urban-planning reframe): don't treat sites as one undifferentiated pool. Give
each site a CATEGORY first. A category is a "kind of place" learned from the data itself
(pollution regime + local climate + geography). Then a new site is no longer a stranger —
we compute its signature, drop it into the nearest category, and predict with the model
that already understands that kind of place.

This script proves the categories are (a) real and (b) reproducible for a future site.

  STEP 1  build a per-site SIGNATURE (39 sites x features)
  STEP 2  standardize, then k-means for k=2..6, pick k by silhouette
  STEP 3  sanity-check with Ward hierarchical clustering (agreement?)
  STEP 4  label each site, profile each category in plain terms
  STEP 5  save a PORTABLE categorizer (scaler + centroids) so a NEW site can be
          assigned with one function call -> this is the only thing computed live
          for an unseen site (the "dynamic" step Crimson described)

Outputs -> results/
Run:  python3 site_categorize.py
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data", "merged_kampala_complete.csv"))
OUT  = os.path.join(HERE, "results"); os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["day"]).sort_values(["site_id", "day"]).reset_index(drop=True)

# ---- engineered, human-readable weather (same defs as the model scripts) ----
Tc  = df.temp_2m_K - 273.15; Tdc = df.dewpoint_2m_K - 273.15
es  = lambda t: 6.112 * np.exp(17.67 * t / (t + 243.5))
df["rel_humidity"] = 100 * es(Tdc) / es(Tc)
df["wind_speed"]   = np.hypot(df.wind_u_10m_ms, df.wind_v_10m_ms)

# ============================================================================
# STEP 1 — per-site SIGNATURE  (what KIND of place is this?)
# ============================================================================
def seasonal_amplitude(s):                      # how much PM2.5 swings across months
    m = s.groupby(s.index.month).mean()
    return float(m.max() - m.min()) if len(m) else np.nan

sig = df.groupby("site_id").apply(lambda g: pd.Series({
    "pm25_mean":   g.pm2_5.mean(),              # pollution LEVEL
    "pm25_std":    g.pm2_5.std(),               # pollution VOLATILITY
    "pm25_p90":    g.pm2_5.quantile(0.90),      # how bad the bad days get
    "pm25_season_amp": seasonal_amplitude(g.set_index("day").pm2_5),  # seasonal swing
    "temp_mean":   g.temp_2m_K.mean() - 273.15,
    "humidity_mean": g.rel_humidity.mean(),
    "windspeed_mean": g.wind_speed.mean(),      # ventilation
    "precip_mean": g.precipitation_m.mean() * 1000,  # mm/day, washout
    "lat": g.site_latitude.iloc[0],
    "lon": g.site_longitude.iloc[0],
    "n_days": len(g),
})).reset_index()

# Two candidate signature bases:
#   FULL        = behaviour + climate + geography (where it is matters)
#   BEHAVIOURAL = drop lat/lon -> "what KIND of place" regardless of where it sits.
# Geography tends to peel 3 geographic outliers; behaviour is what the model actually
# needs to route on. We compare both, honestly.
FEATS_FULL = ["pm25_mean","pm25_std","pm25_p90","pm25_season_amp",
              "temp_mean","humidity_mean","windspeed_mean","precip_mean","lat","lon"]
FEATS_BEHAV = ["pm25_mean","pm25_std","pm25_p90","pm25_season_amp",
               "temp_mean","humidity_mean","windspeed_mean","precip_mean"]

def scan(feat_cols):
    Xs_ = StandardScaler().fit_transform(sig[feat_cols].values)
    rows = []
    for k in range(2, 7):
        lab = KMeans(n_clusters=k, n_init=25, random_state=42).fit_predict(Xs_)
        sizes = np.bincount(lab)
        rows.append(dict(k=k, silhouette=round(silhouette_score(Xs_, lab), 3),
                         min_cluster=int(sizes.min()), sizes=sizes.tolist()))
    return pd.DataFrame(rows)

print("=" * 68); print("FEATURE-BASE COMPARISON (balance matters, not just silhouette)"); print("=" * 68)
print("\nFULL signature (incl. lat/lon):"); print(scan(FEATS_FULL).to_string(index=False))
print("\nBEHAVIOURAL signature (no geography):"); print(scan(FEATS_BEHAV).to_string(index=False))

# DECISION (documented, defensible):
#  - Use the BEHAVIOURAL base — routing should follow how a place behaves, not its coords.
#  - k=2 wins silhouette but is an "outlier peel" (3 sites vs 36) — too coarse to route on.
#    Those 3 sites are ROBUST (same 3 at every k, k-means==Ward ARI=1.0) -> a real
#    micro-regime to handle specially, not a routing category.
#  - Working categorization = best silhouette among k>=3 -> k=3 [24,12,3]: a usable
#    3-way planning split (typical / elevated / outlier). Flagged as a choice, revisitable.
FEATS = FEATS_BEHAV
scaler = StandardScaler().fit(sig[FEATS].values); Xs = scaler.transform(sig[FEATS].values)
scan_b = scan(FEATS_BEHAV)
sil = dict(zip(scan_b.k, scan_b.silhouette))
k2_minor = min(scan_b[scan_b.k == 2].iloc[0].sizes)
OUTLIER_PEEL = k2_minor < 0.1 * len(sig)          # k=2 just isolates a few oddballs?
pool = scan_b[scan_b.k >= 3] if OUTLIER_PEEL else scan_b
best_k = int(pool.sort_values("silhouette", ascending=False).iloc[0].k)
km = KMeans(n_clusters=best_k, n_init=50, random_state=42).fit(Xs)
sig["cluster"] = km.labels_

# ============================================================================
# STEP 3 — Ward hierarchical sanity check (do two methods agree?)
# ============================================================================
ward = AgglomerativeClustering(n_clusters=best_k, linkage="ward").fit(Xs)
agreement = adjusted_rand_score(km.labels_, ward.labels_)

# ============================================================================
# STEP 4 — profile + name each category in plain words
# ============================================================================
prof = sig.groupby("cluster")[FEATS + ["n_days"]].mean().round(2)
prof.insert(0, "n_sites", sig.groupby("cluster").size())

def name_cluster(row, all_prof):
    pm = row.pm25_mean; pm_rank = (all_prof.pm25_mean < pm).sum()
    lvl = ["low-pollution", "moderate-pollution", "high-pollution", "severe-pollution"][min(pm_rank, 3)]
    vent = "well-ventilated" if row.windspeed_mean >= all_prof.windspeed_mean.median() else "stagnant"
    return f"{lvl} / {vent}"
prof["label"] = [name_cluster(r, prof) for _, r in prof.iterrows()]
sig["category"] = sig.cluster.map(prof["label"])

# order categories by pollution for stable color/order
order = prof.sort_values("pm25_mean").index.tolist()

# ============================================================================
# STEP 5 — PORTABLE categorizer for a NEW (unseen) site
# ============================================================================
portable = {
    "features": FEATS,
    "scaler_mean": scaler.mean_.tolist(),
    "scaler_scale": scaler.scale_.tolist(),
    "centroids": km.cluster_centers_.tolist(),     # in standardized space
    "cluster_labels": {int(c): prof.loc[c, "label"] for c in prof.index},
    "best_k": int(best_k),
}
with open(os.path.join(OUT, "categorizer.json"), "w") as f:
    json.dump(portable, f, indent=2)

def categorize_new_site(signature_dict):
    """Assign an unseen site to a category from its own signature. The ONLY live step."""
    v = np.array([[signature_dict[f] for f in FEATS]])
    vs = (v - np.array(portable["scaler_mean"])) / np.array(portable["scaler_scale"])
    cen = np.array(portable["centroids"])
    c = int(np.argmin(((vs - cen) ** 2).sum(1)))
    return c, portable["cluster_labels"][c]

# ---- save tables ----
sig.to_csv(os.path.join(OUT, "site_categories.csv"), index=False)
prof.to_csv(os.path.join(OUT, "cluster_profiles.csv"))

# ============================================================================
# FIGURES
# ============================================================================
colors = plt.cm.viridis(np.linspace(0.1, 0.9, best_k))
cmap = {c: colors[i] for i, c in enumerate(order)}

# (a) silhouette vs k
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.plot(list(sil.keys()), list(sil.values()), "o-", color="#14A38B", lw=2)
ax.axvline(best_k, ls="--", color="#E8A020", label=f"chosen k={best_k}")
ax.set(title="How many kinds of place? (silhouette)", xlabel="k clusters", ylabel="silhouette score")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_silhouette.png"), dpi=130); plt.close(fig)

# (b) site map colored by category
fig, ax = plt.subplots(figsize=(7, 6))
for c in order:
    s = sig[sig.cluster == c]
    ax.scatter(s.lon, s.lat, s=90, color=cmap[c], edgecolor="k", lw=.5,
               label=f"{prof.loc[c,'label']} (n={int(prof.loc[c,'n_sites'])})")
ax.set(title=f"Kampala: 39 sites grouped into {best_k} kinds of place",
       xlabel="longitude", ylabel="latitude")
ax.legend(fontsize=8, loc="best"); ax.grid(alpha=.3); fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_site_map_clusters.png"), dpi=130); plt.close(fig)

# ============================================================================
# REPORT
# ============================================================================
print("=" * 68)
print("SITE CATEGORIZATION — proof experiment (4th cap)")
print("=" * 68)
print(f"sites: {len(sig)}   features: {len(FEATS)}")
print(f"silhouette by k: " + "  ".join(f"k{k}={v:.3f}" for k, v in sil.items()))
print(f"-> chosen k = {best_k}")
print(f"k-means vs Ward agreement (ARI) = {agreement:.3f}  "
      f"({'strong' if agreement>0.6 else 'moderate' if agreement>0.3 else 'weak'} — two methods "
      f"{'mostly agree' if agreement>0.5 else 'differ'})")
print("\nCATEGORY PROFILES:")
cols = ["label","n_sites","pm25_mean","pm25_p90","windspeed_mean","precip_mean","humidity_mean"]
print(prof[cols].sort_values("pm25_mean").to_string())
print("\nSITES PER CATEGORY:")
for c in order:
    members = sig[sig.cluster==c].site_id.tolist()
    print(f"  [{prof.loc[c,'label']}] {len(members)} sites")

# demo: categorize a 'new' site = the city-average signature
demo = {f: float(sig[f].mean()) for f in FEATS}
c, lab = categorize_new_site(demo)
print(f"\nNEW-SITE DEMO (city-average signature) -> category '{lab}' (cluster {c})")
print(f"\nwrote: site_categories.csv · cluster_profiles.csv · categorizer.json · 2 figures -> {OUT}")
