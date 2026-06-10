#!/usr/bin/env python3
"""
fetch_basemap.py — stitch a Kampala basemap from raster map tiles + record the exact Web-Mercator
projection metadata so any lat/lon can be placed on the image pixel-for-pixel (in Python or JS).

Tiles: CartoDB "dark_matter" (muted dark basemap — city roads/water/labels visible, colored
overlays pop; matches the dark pyramid-view theme). Free for light/research use, © OSM © CARTO.
Output: results/basemap_kampala.png  +  results/basemap_meta.json
"""
import os, json, math, time, io, urllib.request
from PIL import Image
import pandas as pd
import features as F

OUT = os.path.join(F.HERE, "results"); TS = 256; Z = 12
UA = "smart-city-capstone-research/1.0 (academic; contact: crimson)"
STYLES = {  # name -> (url_template, subdomains)
    "dark":  ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", "abcd"),
    "light": ("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", "abcd"),
    "osm":   ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "abc"),
}

def lon2x(lon, z): return (lon + 180.0) / 360.0 * (2**z)
def lat2y(lat, z):
    r = math.radians(lat); return (1 - math.log(math.tan(r) + 1/math.cos(r)) / math.pi) / 2 * (2**z)

def fetch_tile(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.openstreetmap.org/"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return Image.open(io.BytesIO(r.read())).convert("RGB")
        except Exception as e:
            last = e; time.sleep(0.6 * (i + 1))
    raise last

def build(style="dark"):
    d = pd.read_csv(os.path.join(OUT, "site_categories.csv"))
    la, lo = d.lat, d.lon
    mlat = (la.max() - la.min()) * 0.16; mlon = (lo.max() - lo.min()) * 0.16
    S, N, W, E = la.min() - mlat, la.max() + mlat, lo.min() - mlon, lo.max() + mlon
    x0, x1 = int(math.floor(lon2x(W, Z))), int(math.floor(lon2x(E, Z)))
    y0, y1 = int(math.floor(lat2y(N, Z))), int(math.floor(lat2y(S, Z)))   # N has smaller y
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    print(f"style={style} zoom={Z}  tiles x[{x0}..{x1}] y[{y0}..{y1}]  grid {nx}x{ny} = {nx*ny} tiles")
    tpl, subs = STYLES[style]
    canvas = Image.new("RGB", (nx * TS, ny * TS))
    for ix, xt in enumerate(range(x0, x1 + 1)):
        for iy, yt in enumerate(range(y0, y1 + 1)):
            s = subs[(ix + iy) % len(subs)]
            url = tpl.format(s=s, z=Z, x=xt, y=yt)
            canvas.paste(fetch_tile(url), (ix * TS, iy * TS)); time.sleep(0.05)
    path = os.path.join(OUT, "basemap_kampala.png"); canvas.save(path)
    meta = {"zoom": Z, "tile_size": TS, "x0_tile": x0, "y0_tile": y0,
            "img_w": nx * TS, "img_h": ny * TS, "style": style,
            "bbox": {"S": S, "N": N, "W": W, "E": E},
            "attribution": "© OpenStreetMap contributors © CARTO"}
    json.dump(meta, open(os.path.join(OUT, "basemap_meta.json"), "w"), indent=2)
    # sanity: place all sites, report pixel spread
    def px(lat, lon): return (lon2x(lon, Z) - x0) * TS, (lat2y(lat, Z) - y0) * TS
    xs = [px(r.lat, r.lon) for r in d.itertuples()]
    print(f"saved {path} ({nx*TS}x{ny*TS})  sites px-x[{min(x for x,_ in xs):.0f},{max(x for x,_ in xs):.0f}] "
          f"px-y[{min(y for _,y in xs):.0f},{max(y for _,y in xs):.0f}]")
    return path

if __name__ == "__main__":
    import sys
    style = sys.argv[1] if len(sys.argv) > 1 else "dark"
    try:
        build(style)
    except Exception as e:
        print("primary style failed:", e, "-> retrying with osm")
        build("osm")
