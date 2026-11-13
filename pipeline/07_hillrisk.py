"""Step 7: Hill Risk, places to check for landslides (METHOD.md section 6).

A 10 m pixel is flagged when ALL of these hold:
  slope >= SLOPE_DEG
  IMERG rain 5-18 Jul >= RAIN_MM
  LHASA nowcast >= LHASA_MIN on any day (only when USE_LHASA = True)
  NISAR change on the slope: HV drops by >= HILL_HV_DROP_DB in any pair (vegetation stripped)
Groups of >= HILL_MIN_PX pixels become one point.

Writes outputs/hill_risk.geojson and outputs/hill_risk.csv

    python pipeline/07_hillrisk.py
"""
import json
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import Resampling
from scipy import ndimage as ndi

import config as C
from common import ensure_dirs, load_grid, tiles, crop, read_win, warp_window, window_transform, pair_arrays, inside_mask


def imerg_total():
    files = sorted((C.DATA / "imerg").glob("3B-DAY-L.MS.MRG.3IMERG.*.nc4"))
    if not files:
        raise SystemExit("No IMERG files in data/imerg/")
    tot = None
    for f in files:
        ds = xr.open_dataset(f)
        v = ds["precipitation"].sel(lon=slice(89.5, 93.5), lat=slice(20.5, 24.5)).sum("time")
        v = v.transpose("lat", "lon")
        tot = v if tot is None else tot + v
    lat, lon = tot["lat"].values, tot["lon"].values
    arr = tot.values[::-1].astype("float32")            # north-up
    d = float(lon[1] - lon[0])
    path = C.WORK / "aux" / "imerg_total_mm.tif"
    with rasterio.open(path, "w", driver="GTiff", width=arr.shape[1], height=arr.shape[0], count=1,
                       dtype="float32", crs="EPSG:4326", nodata=np.nan,
                       transform=from_origin(lon.min() - d / 2, lat.max() + d / 2, d, d)) as dst:
        dst.write(arr, 1)
    print(f"IMERG: {len(files)} days, max total {np.nanmax(arr):.0f} mm in the box")
    return path


def lhasa_max():
    """Max LHASA value over all files, cut to the region. Handles south-up files."""
    files = sorted((C.DATA / "lhasa").glob("*.tif"))
    if not files:
        print("WARNING: no LHASA files in data/lhasa/, Hill Risk runs without it")
        return None
    W, S, E, Nn = 89.5, 20.5, 93.5, 24.5
    out = prof = None
    for f in files:
        with rasterio.open(f) as src:
            t = src.transform
            c0, c1 = sorted((int((W - t.c) / t.a), int((E - t.c) / t.a)))
            r0, r1 = sorted((int((Nn - t.f) / t.e), int((S - t.f) / t.e)))
            c0, r0, c1, r1 = max(c0, 0), max(r0, 0), min(c1, src.width), min(r1, src.height)
            a = src.read(1, window=rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0)).astype("float32")
            if src.nodata is not None:
                a[a == src.nodata] = np.nan
            x0 = t.c + c0 * t.a
            if t.e > 0:                       # south-up: flip to north-up
                a = a[::-1]
                top = t.f + r1 * t.e
            else:
                top = t.f + r0 * t.e
            out = a if out is None else np.fmax(out, a)
            prof = dict(driver="GTiff", width=a.shape[1], height=a.shape[0], count=1, dtype="float32",
                        crs=src.crs, transform=from_origin(x0, top, abs(t.a), abs(t.e)), nodata=np.nan)
    path = C.WORK / "aux" / "lhasa_max.tif"
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(out, 1)
    print(f"LHASA: {len(files)} files, max value {np.nanmax(out):.2f}" + ("" if C.USE_LHASA else " (recorded, not required)"))
    return path


def main():
    ensure_dirs()
    rain_p, lhasa_p = imerg_total(), lhasa_max()
    N, A = C.WORK / "nisar", C.WORK / "aux"
    _, _, _, crs = load_grid()
    to_ll = Transformer.from_crs(crs, 4326, always_xy=True)
    pts, lhasa_seen = [], [0, 0]
    for inner, padded in tiles(pad=8):
        slope = read_win(A / "slope.tif", padded)
        if not np.isfinite(slope).any() or np.nanmax(slope) < C.SLOPE_DEG:
            continue
        change = np.zeros(slope.shape, bool)
        for pair, (b, d) in C.PAIRS.items():
            if not (N / f"{d}_HH.tif").exists():
                continue
            *_, dhv = pair_arrays(pair, padded)
            with np.errstate(invalid="ignore"):
                change |= dhv <= -C.HILL_HV_DROP_DB          # vegetation stripped: HV falls
        rain = warp_window(rain_p, padded, resampling=Resampling.bilinear)
        with np.errstate(invalid="ignore"):
            flag = (slope >= C.SLOPE_DEG) & (rain >= C.RAIN_MM) & change & inside_mask(padded)
            if lhasa_p and C.USE_LHASA:
                lh = warp_window(lhasa_p, padded, resampling=Resampling.nearest)
                lhasa_seen[0] += int(np.isfinite(lh).sum()); lhasa_seen[1] += lh.size
                flag &= lh >= C.LHASA_MIN
        if not flag.any():
            continue
        lab, n = ndi.label(flag)
        sizes = np.bincount(lab.ravel())
        idx = np.nonzero(sizes >= C.HILL_MIN_PX)[0]
        idx = idx[idx > 0]
        if idx.size == 0:
            continue
        com = ndi.center_of_mass(flag, lab, idx)
        mslope = ndi.mean(np.nan_to_num(slope), lab, idx)
        mrain = ndi.mean(np.nan_to_num(rain), lab, idx)
        t = window_transform(padded)
        r0, c0 = inner.row_off - padded.row_off, inner.col_off - padded.col_off
        for i, (r, c), sl_, rn in zip(idx, com, mslope, mrain):
            if not (r0 <= r < r0 + inner.height and c0 <= c < c0 + inner.width):
                continue  # belongs to the neighbouring tile
            x, y = t.c + (c + 0.5) * t.a, t.f + (r + 0.5) * t.e
            lon, lat = to_ll.transform(x, y)
            pts.append(dict(lon=round(lon, 5), lat=round(lat, 5), area_m2=int(sizes[i] * C.RES ** 2),
                            slope_deg=round(float(sl_), 1), rain_mm=round(float(rn), 0),
                            label="Possible landslide - check on the ground"))
    if C.USE_LHASA and lhasa_p and lhasa_seen[1] and lhasa_seen[0] / lhasa_seen[1] < 0.5:
        print("WARNING: LHASA files cover less than half of the steep tiles; check data/lhasa/")
    df = pd.DataFrame(pts)
    df.to_csv(C.OUT / "hill_risk.csv", index=False)
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
         "properties": {k: v for k, v in p.items() if k not in ("lon", "lat")}} for p in pts]}
    (C.OUT / "hill_risk.geojson").write_text(json.dumps(fc))
    print(f"Hill Risk: {len(pts)} places to check")


if __name__ == "__main__":
    main()
