"""Part A: new-floodwater reference layer from DSWx-S1 only (independent of NISAR).

Reads   data/dswx_s1_pre/*_B01_WTR.tif, work/aux/dswx_wtr_30m.tif (16 Jul), work/aux/worldcover.tif,
        work/aux/upazila_id_30m.tif
Writes  work/aux/dswx_pre_<date>_30m.tif, work/aux/pre_water_30m.tif (number of pre dates with water, 255 = never observed),
        work/aux/new_floodwater_30m.tif (0 none, 1 new open water, 3 new flooded vegetation, 255 no data)

Usage: python build_reference.py <repo_root>
"""
import re, sys
from pathlib import Path
import numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.windows import Window

root = Path(sys.argv[1]); sys.path.insert(0, str(root / "pipeline"))
import config as C
from common import load_grid, write_full
A = root / "work" / "aux"
t30, w30, h30, crs = load_grid(C.RES_CMP)
k = C.RES_CMP // C.RES
WATER, BAD = list(C.DSWX_WATER), list(C.DSWX_NODATA)

files = sorted((root / "data" / "dswx_s1_pre").glob("*_B01_WTR.tif"))
dates = sorted({re.search(r"_(\d{8})T\d{6}Z_", f.name).group(1) for f in files})
pre = {}
for d in dates:
    mos = np.full((h30, w30), 255, "uint8")
    for f in [f for f in files if f"_{d}T" in f.name]:
        with rasterio.open(f) as src:
            tmp = np.full((h30, w30), 255, "uint8")
            reproject(rasterio.band(src, 1), tmp, dst_transform=t30, dst_crs=crs, src_nodata=255, dst_nodata=255,
                      resampling=Resampling.nearest)
            fill = np.isin(mos, BAD) & ~np.isin(tmp, BAD)      # later tiles only fill gaps
            mos[fill] = tmp[fill]
    write_full(A / f"dswx_pre_{d}_30m.tif", mos, res=C.RES_CMP, nodata=255)
    pre[d] = mos

wtr = rasterio.open(A / "dswx_wtr_30m.tif").read(1)
uid = rasterio.open(A / "upazila_id_30m.tif").read(1)
ins = uid > 0
km2 = C.RES_CMP ** 2 / 1e6

n_valid = sum((~np.isin(m, BAD)).astype("uint8") for m in pre.values())
n_water = sum(np.isin(m, WATER).astype("uint8") for m in pre.values())
for d, m in pre.items():
    print(f"pre date {d}: valid on {100 * (~np.isin(m, BAD) & ins).sum() / ins.sum():5.1f}% of the upazilas, "
          f"water {(np.isin(m, WATER) & ins).sum() * km2:6.1f} km² (open {((m == 1) & ins).sum() * km2:.1f}, veg {((m == 3) & ins).sum() * km2:.1f})")
print(f"cells inside the upazilas with 0 / 1 / 2 / 3 / 4 valid pre dates: "
      + " / ".join(f"{100 * ((n_valid == i) & ins).sum() / ins.sum():.1f}%" for i in range(5)))

# WorldCover permanent water / wetland / mangrove: a 30 m cell is excluded when ANY of its 10 m pixels is 80, 90 or 95
wcx = np.zeros((h30, w30), bool)
with rasterio.open(A / "worldcover.tif") as ws:
    for r in range(0, h30, 600):
        n = min(600, h30 - r)
        a = ws.read(1, window=Window(0, r * k, w30 * k, n * k)).reshape(n, k, w30, k)
        wcx[r:r + n] = np.isin(a, list(C.EXCLUDE_CLASSES)).any(axis=(1, 3))

w16 = np.isin(wtr, WATER)
new = w16 & (n_valid >= 1) & (n_water == 0) & ~wcx
out = np.zeros((h30, w30), "uint8")
out[new & (wtr == 1)] = 1
out[new & (wtr == 3)] = 3
out[np.isin(wtr, BAD) | (n_valid == 0)] = 255
write_full(A / "new_floodwater_30m.tif", out, res=C.RES_CMP, nodata=255)
pw = n_water.copy(); pw[n_valid == 0] = 255
write_full(A / "pre_water_30m.tif", pw, res=C.RES_CMP, nodata=255)

def a(m): return f"{(m & ins).sum() * km2:7.1f}"
print(f"\n16 Jul water inside the upazilas: {a(w16)} km²  (open {a(wtr == 1)}, flooded vegetation {a(wtr == 3)})")
for name, cls in (("open water", 1), ("flooded vegetation", 3)):
    m = wtr == cls
    perm = m & (n_water >= 1)
    always = m & (n_valid >= 1) & (n_water == n_valid)
    nopre = m & (n_valid == 0)
    wcex = m & (n_valid >= 1) & (n_water == 0) & wcx
    print(f"  {name:19s} total {a(m)} | water on >=1 pre date {a(perm)} (on every valid pre date {a(always)}) | "
          f"WorldCover 80/90/95 {a(wcex)} | no pre observation {a(nopre)} | NEW {a(out == cls)}")
tot, nw = (w16 & ins).sum(), (np.isin(out, [1, 3]) & ins).sum()
print(f"new floodwater: {nw * km2:.1f} km² = {100 * nw / tot:.0f}% of the 16 Jul water; "
      f"permanent or seasonal (water on a pre date): {100 * (w16 & (n_water >= 1) & ins).sum() / tot:.0f}%; "
      f"WorldCover-excluded: {100 * (w16 & (n_valid >= 1) & (n_water == 0) & wcx & ins).sum() / tot:.0f}%")
print("pre dates used:", ", ".join(dates))
