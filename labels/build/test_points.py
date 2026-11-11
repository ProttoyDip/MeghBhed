"""Pick 1-3 tree-cover points on HAND <= 5 m within 500 m of each geocoded report place.
Reads only work/aux/worldcover.tif, work/aux/hand.tif and work/upazilas.geojson (no NISAR).
Usage: python test_points.py <repo_root>"""
import json, sys
from pathlib import Path
import geopandas as gpd, numpy as np, rasterio
from pyproj import Transformer
from rasterio.windows import Window
from scipy import ndimage as ndi
from shapely.geometry import Point
root = Path(sys.argv[1]); here = Path(__file__).parent; A = root / "work" / "aux"
places = json.loads((here / "places_geocoded.json").read_text())
up = gpd.read_file(root / "work" / "upazilas.geojson").to_crs(4326)
out = []
with rasterio.open(A / "worldcover.tif") as wc, rasterio.open(A / "hand.tif") as hd:
    fwd = Transformer.from_crs(4326, wc.crs, always_xy=True); inv = Transformer.from_crs(wc.crs, 4326, always_xy=True)
    for p in places:
        x, y = fwd.transform(p["lon"], p["lat"]); r, c = wc.index(x, y)
        win = Window(c - 52, r - 52, 105, 105)
        w = wc.read(1, window=win); h = hd.read(1, window=win).astype("float32")
        tree = w == 10
        core = ndi.uniform_filter(tree.astype("float32"), 3) > 0.99          # 3x3 all tree
        rr, cc = np.mgrid[-52:53, -52:53]; d = np.hypot(rr, cc) * 10
        ok = core & (h <= 5) & np.isfinite(h) & (d <= 500)
        cand = sorted(zip(d[ok], rr[ok], cc[ok]))
        chosen = []
        for dist, a, b in cand:
            if all(np.hypot(a - a2, b - b2) * 10 >= 150 for _, a2, b2 in chosen):
                lon, lat = inv.transform(*wc.xy(r + int(a), c + int(b)))
                ins = up[up.contains(Point(lon, lat))]
                if len(ins) and ins.iloc[0]["name"] == p["upazila"]:
                    chosen.append((dist, a, b)); out.append(dict(p, plon=round(lon, 6), plat=round(lat, 6), dist_m=int(dist), hand_m=round(float(h[a + 52, b + 52]), 1)))
            if len(chosen) == 3: break
        print(f"{p['label']} {p['upazila']:11s} {p['place']:14s} tree-core low px within 500 m: {int(ok.sum()):4d} -> {len(chosen)} points")
(here / "test_points.json").write_text(json.dumps(out, indent=1))
print("test points:", sum(o["label"] for o in out), "flooded,", sum(1 - o["label"] for o in out), "dry")
