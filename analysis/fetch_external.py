#!/usr/bin/env python3
"""
fetch_external.py — pull FREE, Kampala-covering urban-planning features for the 39 sites.

Why (STRATEGY open decision + CP-B): the category mostly encodes a site's pollution LEVEL, and
Kampala's weather is near-uniform, so a sensor-less site has no cheap way to reveal its level
except a 60-day deploy (noisy). Land-use-regression (LUR) predictors VARY at the intra-urban
scale and are the documented lever for new-site PM2.5 transfer:
  - road network density + distance to nearest major road  (traffic = the dominant PM2.5 source)
  - elevation
These are STATIC and derivable for any lat/lon with ZERO pollution observations.

Sources (free, no key):
  - OpenStreetMap roads via Overpass API           https://wiki.openstreetmap.org/wiki/Overpass_API
  - SRTM 30m elevation via opentopodata            https://www.opentopodata.org/datasets/srtm/
LUR predictor set follows: Wong et al. 2021 (ACP 21, 5063, intercity LUR transferability,
https://acp.copernicus.org/articles/21/5063/2021/) and the multiscale-LUR predictor list in
Chen et al. 2022 (PMC8751171, https://pmc.ncbi.nlm.nih.gov/articles/PMC8751171/).

Outputs -> results/external_features.csv  (+ cache results/_osm_roads.json)
Run: ../../../working/.venv/bin/python fetch_external.py
"""
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, requests

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results")
sites = pd.read_csv(os.path.join(OUT, "_site_coords.csv"))
LAT0 = float(sites.site_latitude.mean())
MAJOR = {"motorway", "trunk", "primary", "secondary",
         "motorway_link", "trunk_link", "primary_link", "secondary_link"}
SKIP  = {"footway", "path", "cycleway", "steps", "pedestrian", "bridleway",
         "track", "construction", "proposed", "corridor", "platform"}
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]

def to_m(lat, lon):
    x = (lon - sites.site_longitude.mean()) * 111320 * math.cos(math.radians(LAT0))
    y = (lat - sites.site_latitude.mean()) * 110540
    return x, y

def seg_dist(px, py, ax, ay, bx, by):
    """distance from point P to segment AB (meters, local plane)."""
    dx, dy = bx - ax, by - ay
    if dx == dy == 0: return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)

def fetch_roads():
    cache = os.path.join(OUT, "_osm_roads.json")
    if os.path.exists(cache):
        print("using cached OSM roads"); return json.load(open(cache))
    pad = 0.015
    s, n = sites.site_latitude.min() - pad, sites.site_latitude.max() + pad
    w, e = sites.site_longitude.min() - pad, sites.site_longitude.max() + pad
    q = f'[out:json][timeout:180];way["highway"]({s},{w},{n},{e});out geom;'
    for url in OVERPASS:
        try:
            print(f"querying {url} ...")
            r = requests.post(url, data={"data": q}, timeout=200,
                              headers={"User-Agent": "kampala-capstone/1.0"})
            r.raise_for_status(); d = r.json()
            json.dump(d, open(cache, "w")); print(f"  got {len(d.get('elements',[]))} ways"); return d
        except Exception as ex:
            print(f"  failed: {type(ex).__name__}: {ex}")
            time.sleep(2)
    raise RuntimeError("all Overpass mirrors failed")

def main():
    # ---- roads -> per-site LUR metrics ----
    d = fetch_roads()
    segs_all, segs_major = [], []          # each: (ax,ay,bx,by,length)
    for el in d.get("elements", []):
        if el.get("type") != "way": continue
        hw = el.get("tags", {}).get("highway", "")
        if hw in SKIP: continue
        geom = el.get("geometry", [])
        pts = [to_m(g["lat"], g["lon"]) for g in geom]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            segs_all.append((ax, ay, bx, by, L))
            if hw in MAJOR: segs_major.append((ax, ay, bx, by, L))
    A = np.array(segs_all); M = np.array(segs_major)
    print(f"parsed {len(A)} road segments ({len(M)} major)")

    recs = []
    for _, r in sites.iterrows():
        px, py = to_m(r.site_latitude, r.site_longitude)
        # distance to nearest major road
        dmaj = min(seg_dist(px, py, *s[:4]) for s in M)
        # midpoint-in-buffer road length density
        def dens(segs, R):
            tot = 0.0
            for ax, ay, bx, by, L in segs:
                if math.hypot((ax+bx)/2 - px, (ay+by)/2 - py) <= R: tot += L
            return tot
        recs.append(dict(site_id=r.site_id,
            dist_major_road_m=round(dmaj, 1),
            road_len_all_300m=round(dens(A, 300), 1),
            road_len_all_1000m=round(dens(A, 1000), 1),
            road_len_major_500m=round(dens(M, 500), 1)))
    ext = pd.DataFrame(recs)

    # ---- elevation (SRTM 30m, batched) ----
    elevs = {}
    locs = "|".join(f"{r.site_latitude},{r.site_longitude}" for _, r in sites.iterrows())
    try:
        rr = requests.get(f"https://api.opentopodata.org/v1/srtm30m?locations={locs}", timeout=60)
        res = rr.json()["results"]
        for (_, r), e in zip(sites.iterrows(), res):
            elevs[r.site_id] = e["elevation"]
        ext["elevation_m"] = ext.site_id.map(elevs)
        print("elevation range: %.0f .. %.0f m" % (ext.elevation_m.min(), ext.elevation_m.max()))
    except Exception as ex:
        print("elevation fetch failed:", ex); ext["elevation_m"] = np.nan

    ext.to_csv(os.path.join(OUT, "external_features.csv"), index=False)
    print("\nexternal_features.csv:"); print(ext.describe().round(1).to_string())
    print("\nwrote results/external_features.csv")

if __name__ == "__main__":
    main()
