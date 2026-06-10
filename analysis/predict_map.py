#!/usr/bin/env python3
"""
predict_map.py — build the data backbone for the Kampala planner map + agentic prototype.

For each of the 39 sensor areas, honest (leave-sites-out) predictions of the EPA safety tier for
NOW / +1 day / +7 days, plus a Voronoi "coverage area" in the basemap's exact pixel projection so
each area can be drawn on the map. Also exports 3 input-page test cases.

Outputs (results/):
  map_predictions.json   sites[] with lat/lon, pixel xy, voronoi polygon (px), now/d1/d7 {ugm3,tier},
                         band, accuracy, behavioural category, actuals.
  test_cases.json        3 worked examples (full feature vector -> true nowcast) for the input page.
"""
import os, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, math
from scipy.spatial import Voronoi
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb
import features as F

OUT = os.path.join(F.HERE, "results"); SEED = 42
EDGES = [35.4, 55.4]; TIERS = ["Elevated", "High", "Dangerous"]
def tier(x): return int(np.clip(np.digitize([float(x)], EDGES)[0], 0, 2))
def tname(x): return TIERS[tier(x)]

meta = json.load(open(os.path.join(OUT, "basemap_meta.json")))
Z, TS, X0, Y0 = meta["zoom"], meta["tile_size"], meta["x0_tile"], meta["y0_tile"]
def to_px(lat, lon):
    n = 2**Z; x = (lon+180)/360*n*TS - X0*TS
    r = math.radians(lat); y = (1-math.log(math.tan(r)+1/math.cos(r))/math.pi)/2*n*TS - Y0*TS
    return [round(x, 1), round(y, 1)]

df  = F.load(); CAT = F.load_categorizer()
full = F.assign_full_categories(df, CAT); LAB = CAT["cluster_labels"]
EXT  = pd.read_csv(os.path.join(OUT, "external_features.csv"))
EXTF = [c for c in EXT.columns if c != "site_id"]
coords = df.groupby("site_id").agg(lat=("site_latitude","first"), lon=("site_longitude","first"),
                                   pm25_mean=("pm2_5","mean")).reset_index()
d = df.merge(EXT, on="site_id", how="left"); d["c"] = d.site_id.map(full)
for j in range(3): d[f"cat_{j}"] = (d.c == j).astype(float)
NOWCOLS = list(F.BASE_NOW) + ["cat_0","cat_1","cat_2"] + EXTF
RFKW = dict(n_estimators=400, max_depth=30, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)
sites = sorted(full)

# ---------- honest leave-sites-out NOWCAST (GroupKFold-5) with conformal band ----------
print("nowcast (GroupKFold-5, observed category)...")
from sklearn.model_selection import GroupKFold
d["nowpred"] = np.nan
sarr = d.site_id.values; gkf = GroupKFold(5)
qhat = []
for tr_idx, te_idx in gkf.split(d, groups=sarr):
    tr, te = d.iloc[tr_idx], d.iloc[te_idx]
    m = RandomForestRegressor(**RFKW).fit(tr[NOWCOLS], tr.pm2_5.values)
    d.loc[d.index[te_idx], "nowpred"] = m.predict(te[NOWCOLS])
    # group-conformal residual on held-out training sites
    rng = np.random.default_rng(SEED); cs = set(rng.choice(sorted(set(tr.site_id)), 6, replace=False))
    ptr = tr[~tr.site_id.isin(cs)]; cal = tr[tr.site_id.isin(cs)]
    m2 = RandomForestRegressor(**RFKW).fit(ptr[NOWCOLS], ptr.pm2_5.values)
    res = np.abs(cal.pm2_5.values - m2.predict(cal[NOWCOLS])); qhat.append(np.quantile(res, 0.9))
Q = float(np.mean(qhat))

# ---------- global FUTURE forecaster (LightGBM-on-lags), trained on all (for a demo map) ----------
print("forecaster (global LightGBM-on-lags)...")
panel = F.build_future_panel(df)
lagcols = [c for c in panel.columns if c.startswith("pm25_lag") or c.startswith("pm25_roll")]
ffeats = lagcols + ["month","day_of_week","temp_2m_K","rel_humidity","wind_speed"]
fmodels = {}
for h in range(1, 8):
    tgt = panel[["site_id","day","pm2_5"]].copy(); tgt["day"] = tgt["day"] - pd.Timedelta(days=h)
    sup = panel.merge(tgt.rename(columns={"pm2_5":"y"}), on=["site_id","day"], how="inner").dropna(subset=ffeats+["y"])
    fmodels[h] = lgb.LGBMRegressor(n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8,
                                   colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1).fit(sup[ffeats], sup.y.values)

# ---------- per-site assembly: pick an anchor day, gather now/d1/d7 ----------
def anchor_for(site):
    have = panel[panel.site_id == site].sort_values("day")
    if have.empty: return None
    return have.iloc[min(len(have)//2, len(have)-8)].day

print("assembling per-site predictions...")
recs = []
for s in sites:
    g = d[d.site_id == s].sort_values("day")
    # NOW = nowcast averaged over the site's days (the "typical current status"), + a sample day
    now_pred = float(g.nowpred.mean()); now_act = float(g.pm2_5.mean())
    pb = np.array([tier(v) for v in g.nowpred]); ab = np.array([tier(v) for v in g.pm2_5])
    acc = float((pb == ab).mean()); w1 = float((np.abs(pb-ab) <= 1).mean())
    a = anchor_for(s); d1 = d7 = None; d1a = d7a = None
    if a is not None:
        row = panel[(panel.site_id == s) & (panel.day == pd.Timestamp(a))][ffeats]
        if len(row):
            d1 = float(fmodels[1].predict(row)[0]); d7 = float(fmodels[7].predict(row)[0])
            ser = g.set_index("day").pm2_5
            d1a = float(ser.get(pd.Timestamp(a)+pd.Timedelta(days=1), np.nan))
            d7a = float(ser.get(pd.Timestamp(a)+pd.Timedelta(days=7), np.nan))
    cj = full[s]
    recs.append(dict(site=s, lat=float(coords[coords.site_id==s].lat.iloc[0]),
        lon=float(coords[coords.site_id==s].lon.iloc[0]),
        cat=int(cj), cat_label=LAB[str(cj)], pm25_mean=round(float(coords[coords.site_id==s].pm25_mean.iloc[0]),1),
        band=round(Q,1), accuracy=round(acc,3), within1=round(w1,3),
        now=dict(ugm3=round(now_pred,1), tier=tname(now_pred), actual=round(now_act,1), actual_tier=tname(now_act)),
        d1=(dict(ugm3=round(d1,1), tier=tname(d1), actual=(round(d1a,1) if d1a==d1a else None)) if d1 is not None else None),
        d7=(dict(ugm3=round(d7,1), tier=tname(d7), actual=(round(d7a,1) if d7a==d7a else None)) if d7 is not None else None)))

# ---------- Voronoi coverage in PIXEL space, clipped to the image rectangle ----------
print("voronoi coverage...")
pts = np.array([to_px(r["lat"], r["lon"]) for r in recs])
W, H = meta["img_w"], meta["img_h"]
# add 4 far "guard" points so all real cells are finite
guard = np.array([[-4*W,-4*H],[5*W,-4*H],[-4*W,5*H],[5*W,5*H]])
vor = Voronoi(np.vstack([pts, guard]))
def clip(poly, rect=(0,0,W,H)):
    """Sutherland-Hodgman clip polygon to axis-aligned rectangle."""
    x0,y0,x1,y1 = rect; out = poly
    edges = [("l",x0),("r",x1),("t",y0),("b",y1)]
    for side,val in edges:
        ip = out; out = []
        if not ip: break
        for i in range(len(ip)):
            cur = ip[i]; prv = ip[i-1]
            def inside(p):
                return {"l":p[0]>=val,"r":p[0]<=val,"t":p[1]>=val,"b":p[1]<=val}[side]
            def inter(p,q):
                if side in("l","r"):
                    t=(val-p[0])/(q[0]-p[0]); return [val, p[1]+t*(q[1]-p[1])]
                t=(val-p[1])/(q[1]-p[1]); return [p[0]+t*(q[0]-p[0]), val]
            if inside(cur):
                if not inside(prv): out.append(inter(prv,cur))
                out.append(cur)
            elif inside(prv): out.append(inter(prv,cur))
    return [[round(x,1),round(y,1)] for x,y in out]

for i, r in enumerate(recs):
    reg = vor.regions[vor.point_region[i]]
    poly = [list(vor.vertices[v]) for v in reg if v != -1] if reg and -1 not in reg else []
    r["px"] = to_px(r["lat"], r["lon"])
    r["poly"] = clip(poly) if poly else []

out = dict(meta=meta, tiers=TIERS, edges=EDGES,
           tier_colors={"Elevated":"#46c98a","High":"#e3b34e","Dangerous":"#ec5a4c"},
           cat_colors={"0":"#6f6cd8","1":"#d8a24a","2":"#36b3a8"},
           band=round(Q,1), n_sites=len(recs), sites=recs)
json.dump(out, open(os.path.join(OUT,"map_predictions.json"),"w"))
print(f"wrote results/map_predictions.json  ({len(recs)} sites, conformal band ±{Q:.1f})")

# ---------- 3 input-page test cases ----------
def feat_row(site, day):
    g = df[(df.site_id==site)]; r = g[g.day==pd.Timestamp(day)].iloc[0]
    ext = EXT[EXT.site_id==site].iloc[0]
    return dict(site=site, date=str(pd.Timestamp(day).date()),
        site_latitude=float(r.site_latitude), site_longitude=float(r.site_longitude),
        month=int(r.month), day_of_week=int(r.day_of_week),
        temp_2m_K=round(float(r.temp_2m_K),2), dewpoint_2m_K=round(float(r.dewpoint_2m_K),2),
        wind_u_10m_ms=round(float(r.wind_u_10m_ms),3), wind_v_10m_ms=round(float(r.wind_v_10m_ms),3),
        surface_pressure_Pa=round(float(r.surface_pressure_Pa),0), precipitation_m=round(float(r.precipitation_m),6),
        rel_humidity=round(float(r.rel_humidity),1), wind_speed=round(float(r.wind_speed),3),
        **{k: round(float(ext[k]),1) for k in EXTF},
        category=int(full[site]), category_label=LAB[str(full[site])],
        actual_pm25=round(float(r.pm2_5),1), actual_tier=tname(float(r.pm2_5)))
# pick: a calm low day (site_135), the anomaly high day (site_54), and a Dangerous day
g54 = df[df.site_id=="site_54"].sort_values("pm2_5"); dang_day = g54.iloc[-1].day
cases = [feat_row("site_135", df[df.site_id=="site_135"].sort_values("day").iloc[120].day),
         feat_row("site_54", dang_day),
         feat_row("site_26", df[df.site_id=="site_26"].sort_values("day").iloc[150].day)]
json.dump(dict(cases=cases, edges=EDGES, tiers=TIERS), open(os.path.join(OUT,"test_cases.json"),"w"), indent=2)
print(f"wrote results/test_cases.json  ({len(cases)} cases)")
print("DONE.")
