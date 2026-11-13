"""Geocode report places with Nominatim (1 request/s) and check the upazila. Usage: python geocode.py <repo_root>"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
sys.path.insert(0, str(Path(__file__).parent)); from places import PLACES
root = Path(sys.argv[1]); cache_p = Path(__file__).parent / "geocode_cache.json"
cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
up = gpd.read_file(root / "work" / "upazilas.geojson").to_crs(4326)
def ask(q):
    if q in cache: return cache[q]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(dict(q=q, format="jsonv2", limit=5, countrycodes="bd", addressdetails=1))
    req = urllib.request.Request(url, headers={"User-Agent": "flood-label-geocoder/1.0"})
    time.sleep(1.1)
    cache[q] = json.loads(urllib.request.urlopen(req, timeout=30).read()); cache_p.write_text(json.dumps(cache)); return cache[q]
out = []
for place, upz, lab, src, date, quote in PLACES:
    hit = None
    for q in (f"{place}, {upz}, Chattogram, Bangladesh", f"{place} Union, {upz}, Bangladesh", f"{place}, {upz} Upazila, Chittagong District, Bangladesh"):
        for r in ask(q):
            pt = Point(float(r["lon"]), float(r["lat"]))
            inside = up[up.contains(pt)]
            if len(inside) and inside.iloc[0]["name"] == upz:
                hit = dict(lon=float(r["lon"]), lat=float(r["lat"]), osm_type=r.get("addresstype") or r.get("type"), display=r["display_name"][:70]); break
        if hit: break
    print(f"{'OK ' if hit else 'MISS'} {lab} {upz:11s} {place:22s} {hit or ''}")
    if hit: out.append(dict(place=place, upazila=upz, label=lab, source=src, report_date=date, quote=quote, **hit))
(Path(__file__).parent / "places_geocoded.json").write_text(json.dumps(out, indent=1))
print(len(out), "geocoded;", sum(o["label"] for o in out), "flooded,", sum(1 - o["label"] for o in out), "dry")
