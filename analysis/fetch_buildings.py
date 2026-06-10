import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, requests
OUT=os.path.dirname(os.path.abspath(__file__))+"/results"
sites=pd.read_csv(f"{OUT}/_site_coords.csv")
CACHE=f"{OUT}/_osm_buildings.json"
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
OVERPASS=["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]
def fetch(lat,lon):
    q=f'[out:json][timeout:60];nwr["building"](around:1000,{lat},{lon});out center;'
    for url in OVERPASS:
        try:
            r=requests.post(url,data={"data":q},timeout=70,headers={"User-Agent":"kampala-capstone/1.0"}); r.raise_for_status()
            els=r.json().get("elements",[]); pts=[]
            for e in els:
                if "center" in e: pts.append((e["center"]["lat"],e["center"]["lon"]))
                elif "lat" in e: pts.append((e["lat"],e["lon"]))
            return pts
        except Exception as ex: print("  fail",type(ex).__name__,str(ex)[:60]); time.sleep(2)
    return None
done=0
for _,r in sites.iterrows():
    sid=r.site_id
    if sid in cache: continue
    pts=fetch(r.site_latitude,r.site_longitude)
    if pts is None: print(f"  {sid}: FAILED (left for retry)"); continue
    cache[sid]=pts; done+=1
    json.dump(cache,open(CACHE,"w"))
    if done%5==0: print(f"  fetched {done} new (total cached {len(cache)})",flush=True)
print(f"cached sites: {len(cache)}/{len(sites)}")
