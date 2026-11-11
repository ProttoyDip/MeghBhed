"""Step 3: put every non-NISAR layer onto the same grid.

10 m (tiled):   work/aux/worldcover.tif, slope.tif (degrees), hand.tif (m)
30 m (in memory): work/aux/dswx_wtr_30m.tif, upazila_id_30m.tif, population_30m.tif
                  work/aux/june_water_30m.tif  number of pre-flood DSWx-S1 dates with water (255 = never observed)
                  work/aux/june_open_30m.tif   number of pre-flood dates with OPEN water
                  work/aux/june_dates.json     the pre-flood dates found in data/dswx_s1_pre/

    python pipeline/03_ancillary.py
"""
import json
import re
import numpy as np
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.warp import Resampling

import config as C
from common import (ensure_dirs, load_grid, create, tiles, crop, write_win, warp_window,
                    write_full)
from rasterio.windows import Window


def june_water(A, full30):
    """Pre-flood water from the DSWx-S1 files in data/dswx_s1_pre/ (any date before the flood)."""
    files = sorted(p for t in C.DSWX_TILES for p in (C.DATA / "dswx_s1_pre").glob(f"*{t}*_B01_WTR.tif"))
    if not files:
        print("WARNING: no files in data/dswx_s1_pre/; june_water_30m.tif not built, so permanent and "
              "seasonal water cannot be separated from flood")
        return
    dates = sorted({re.search(r"_(\d{8})T\d{6}Z_", f.name).group(1) for f in files})
    bad, water = list(C.DSWX_NODATA), list(C.DSWX_WATER)
    n_water = n_open = n_valid = None
    for d in dates:
        mos = None
        for f in (f for f in files if f"_{d}T" in f.name):
            tile = warp_window(f, full30, res=C.RES_CMP, dtype="uint8", nodata=255, resampling=Resampling.nearest)
            if mos is None:
                mos = tile
            else:
                hole = np.isin(mos, bad) & ~np.isin(tile, bad)      # later tiles only fill gaps
                mos[hole] = tile[hole]
        v, w, o = ~np.isin(mos, bad), np.isin(mos, water), mos == 1
        n_valid = v.astype("uint8") if n_valid is None else n_valid + v
        n_water = w.astype("uint8") if n_water is None else n_water + w
        n_open = o.astype("uint8") if n_open is None else n_open + o
    n_water[n_valid == 0] = 255
    n_open[n_valid == 0] = 255
    write_full(A / "june_water_30m.tif", n_water.astype("uint8"), res=C.RES_CMP, nodata=255)
    write_full(A / "june_open_30m.tif", n_open.astype("uint8"), res=C.RES_CMP, nodata=255)
    (A / "june_dates.json").write_text(json.dumps(dates))
    print(f"30 m: pre-flood water from {len(dates)} DSWx-S1 dates ({', '.join(dates)}), "
          f"{((n_water >= 1) & (n_water != 255)).mean()*100:.1f}% of the grid was water on at least one")


def main():
    ensure_dirs()
    A = C.WORK / "aux"
    wc = sorted((C.DATA / "worldcover").glob("*_Map.tif"))
    dem = sorted((C.DATA / "dem").glob("*_DEM.tif"))
    hand = sorted((C.DATA / "hand").glob("*_HAND.tif"))
    for name, files in (("WorldCover", wc), ("DEM", dem), ("HAND", hand)):
        if not files:
            raise SystemExit(f"No {name} files found under data/")

    # ---- 10 m layers, tile by tile
    create(A / "worldcover.tif", dtype="uint8", nodata=0)
    create(A / "slope.tif")
    create(A / "hand.tif")
    create(A / "inside.tif", dtype="uint8", nodata=255)
    from common import window_transform
    up10 = gpd.read_file(C.WORK / "upazilas.geojson").to_crs(load_grid()[3])
    area = [up10.geometry.union_all() if hasattr(up10.geometry, "union_all") else up10.unary_union]
    for inner, padded in tiles(pad=2):
        write_win(A / "worldcover.tif",
                  warp_window(wc, inner, dtype="uint8", nodata=0, resampling=Resampling.nearest), inner)
        z = warp_window(dem, padded, resampling=Resampling.bilinear)
        gy, gx = np.gradient(z, C.RES, C.RES)
        slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype("float32")
        write_win(A / "slope.tif", crop(slope, inner, padded), inner)
        write_win(A / "hand.tif", warp_window(hand, inner, resampling=Resampling.bilinear), inner)
        write_win(A / "inside.tif", rasterize(area, out_shape=(int(inner.height), int(inner.width)),
                                              transform=window_transform(inner), fill=0, default_value=1,
                                              dtype="uint8"), inner)
    print("10 m: worldcover, slope, hand, inside-districts mask done")

    # ---- 30 m layers
    t30, w30, h30, crs = load_grid(C.RES_CMP)
    full30 = Window(0, 0, w30, h30)

    dswx = sorted(p for t in C.DSWX_TILES for p in (C.DATA / "dswx_s1").glob(f"*{t}*_B01_WTR.tif"))
    if not dswx:
        raise SystemExit("No DSWx-S1 WTR files found under data/dswx_s1/")
    wtr = warp_window(dswx, full30, res=C.RES_CMP, dtype="uint8", nodata=255, resampling=Resampling.nearest)
    write_full(A / "dswx_wtr_30m.tif", wtr, res=C.RES_CMP, nodata=255)
    print(f"30 m: DSWx-S1 mosaic of {len(dswx)} files, {np.isin(wtr, list(C.DSWX_WATER)).mean()*100:.1f}% water")
    june_water(A, full30)

    up = gpd.read_file(C.WORK / "upazilas.geojson").to_crs(crs).reset_index(drop=True)
    uid = rasterize(((g, i + 1) for i, g in enumerate(up.geometry)), out_shape=(h30, w30),
                    transform=t30, fill=0, dtype="int16")
    write_full(A / "upazila_id_30m.tif", uid, res=C.RES_CMP, nodata=-1)
    (A / "upazila_index.json").write_text(json.dumps(up[["id", "name", "district"]].to_dict("records"), indent=1))

    # WorldPop: people per source cell -> people per 30 m cell.
    wp = sorted((C.DATA / "worldpop").glob("*.tif"))[0]
    import rasterio
    with rasterio.open(wp) as src:
        src_deg = abs(src.transform.a)
    cnt = warp_window(wp, full30, res=C.RES_CMP, resampling=Resampling.nearest)
    # each 30 m cell takes the count of the ~90 m source cell it falls in; divide by
    # how many 30 m cells fit in that source cell (depends on latitude).
    from pyproj import Transformer
    ys = t30.f + t30.e * (np.arange(h30) + 0.5)
    lat = Transformer.from_crs(crs, 4326, always_xy=True).transform(np.full(h30, t30.c), ys)[1]
    src_area = (src_deg * 111320.0) ** 2 * np.cos(np.radians(lat))
    pop = cnt * (C.RES_CMP ** 2 / src_area)[:, None]
    pop = np.where(np.isfinite(pop) & (pop > 0), pop, 0).astype("float32")
    write_full(A / "population_30m.tif", pop, res=C.RES_CMP, nodata=None)
    inside = uid > 0
    print(f"30 m: {len(up)} upazilas rasterised; population inside = {pop[inside].sum():,.0f}")


if __name__ == "__main__":
    main()
