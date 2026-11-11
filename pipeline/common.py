"""Shared helpers: the analysis grid, tiled raster I/O, reprojection.

The 10 m grid over Chattogram + Feni is ~150 million pixels, too big for laptop
memory, so steps work tile by tile (TILE x TILE pixels, with a small overlap
where filters need neighbours).
"""
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import Window, transform as win_transform

import config as C

TILE = 2048


def ensure_dirs():
    for d in (C.WORK, C.WORK / "nisar", C.WORK / "aux", C.OUT):
        d.mkdir(parents=True, exist_ok=True)


def load_grid(res=None):
    """(transform, width, height, crs) of the 10 m grid, or the 30 m one with res=30."""
    g = json.loads((C.WORK / "grid.json").read_text())
    res = res or C.RES
    w = int(round((g["xmax"] - g["xmin"]) / res))
    h = int(round((g["ymax"] - g["ymin"]) / res))
    return from_origin(g["xmin"], g["ymax"], res, res), w, h, g["crs"]


def create(path, dtype="float32", nodata=np.nan, res=None):
    """Create an empty full-grid GeoTIFF to fill window by window."""
    t, w, h, crs = load_grid(res)
    prof = dict(driver="GTiff", width=w, height=h, count=1, dtype=dtype, crs=crs, transform=t,
                compress="deflate", tiled=True, blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER",
                nodata=nodata)
    with rasterio.open(path, "w", **prof):
        pass


def tiles(res=None, size=TILE, pad=0):
    """Yield (inner_window, padded_window) covering the grid."""
    _, w, h, _ = load_grid(res)
    for r in range(0, h, size):
        for c in range(0, w, size):
            inner = Window(c, r, min(size, w - c), min(size, h - r))
            padded = Window(c - pad, r - pad, inner.width + 2 * pad, inner.height + 2 * pad)
            yield inner, padded


def crop(a, inner, padded):
    """Cut the padded tile back to its inner window."""
    r0, c0 = inner.row_off - padded.row_off, inner.col_off - padded.col_off
    return a[r0:r0 + inner.height, c0:c0 + inner.width]


def read_win(path, window, fill=np.nan):
    """Read a window (may extend past the edge) as float32 with NaN for no data."""
    with rasterio.open(path) as src:
        a = src.read(1, window=window, boundless=True, fill_value=src.nodata if src.nodata is not None else 0)
        if np.issubdtype(a.dtype, np.floating) and src.nodata is not None and not np.isnan(src.nodata):
            a = np.where(a == src.nodata, np.nan, a)
        return a


def write_win(path, arr, window):
    with rasterio.open(path, "r+") as dst:
        dst.write(arr.astype(dst.dtypes[0]), 1, window=window)


def window_transform(window, res=None):
    t, *_ = load_grid(res)
    return win_transform(window, t)


def warp_window(src_paths, window, res=None, resampling=Resampling.nearest,
                dtype="float32", nodata=np.nan, src_nodata=None):
    """Reproject one raster or a mosaic of rasters onto one grid window."""
    _, _, _, crs = load_grid(res)
    t = window_transform(window, res)
    shape = (int(window.height), int(window.width))
    out = np.full(shape, nodata, dtype=dtype)
    isnan = lambda a: np.isnan(a) if np.issubdtype(np.dtype(dtype), np.floating) else (a == nodata)
    for p in (src_paths if isinstance(src_paths, (list, tuple)) else [src_paths]):
        with rasterio.open(p) as src:
            tmp = np.full(shape, nodata, dtype=dtype)
            sn = src_nodata if src_nodata is not None else src.nodata
            reproject(rasterio.band(src, 1), tmp, src_nodata=sn, dst_transform=t, dst_crs=crs,
                      dst_nodata=nodata, resampling=resampling)
            hole = isnan(out)
            out[hole] = tmp[hole]
    return out


def block_reduce_mean(a, k):
    """Average k x k blocks (10 m -> 30 m with k=3), ignoring NaN."""
    h, w = a.shape[0] // k * k, a.shape[1] // k * k
    a = a[:h, :w].astype("float32").reshape(h // k, k, w // k, k)
    with np.errstate(invalid="ignore"), np.testing.suppress_warnings() as s:
        s.filter(RuntimeWarning)
        return np.nanmean(a, axis=(1, 3))


def read_full(path):
    with rasterio.open(path) as src:
        a = src.read(1)
        if np.issubdtype(a.dtype, np.floating) and src.nodata is not None and not np.isnan(src.nodata):
            a = np.where(a == src.nodata, np.nan, a)
        return a


def write_full(path, arr, res=None, nodata=None):
    create(path, dtype=str(arr.dtype), nodata=nodata, res=res)
    with rasterio.open(path, "r+") as dst:
        dst.write(arr, 1)


def boxcar_db(db, k):
    """Multilook: average linear power over a k x k window, ignoring no-data. Input and output in dB."""
    if k <= 1:
        return db
    from scipy.ndimage import uniform_filter
    ok = np.isfinite(db)
    lin = np.where(ok, 10 ** (np.where(ok, db, 0) / 10), 0).astype("float32")
    n = uniform_filter(ok.astype("float32"), k)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = 10 * np.log10(uniform_filter(lin, k) / n)
    return np.where(ok & (n > 0.3), out, np.nan).astype("float32")


def pair_bias(pair):
    p = C.WORK / "bias.json"
    if C.BIAS_CORRECT and p.exists():
        b = json.loads(p.read_text()).get(pair)
        if b:
            return b["dhh"], b["dhv"]
    return 0.0, 0.0


def _role(role, pol, window):
    p = C.WORK / "nisar" / f"{role}_{pol}.tif"
    return read_win(p, window) if role and p.exists() else None


def _mean_db(a, b):
    """Average two dB images in linear power; where one is missing, use the other."""
    if b is None:
        return a
    la, lb = 10 ** (a / 10), 10 ** (b / 10)
    with np.errstate(invalid="ignore"):
        m = np.where(np.isfinite(la) & np.isfinite(lb), (la + lb) / 2, np.where(np.isfinite(la), la, lb))
        return (10 * np.log10(m)).astype("float32")


def raw_pair(pair, window):
    """Unsmoothed dB: HH/HV before (average of the available 'before' scenes), during, and after (or None)."""
    b, d = C.PAIRS[pair]
    ex = getattr(C, "EXTRA", {}).get(pair, {})
    out = {}
    for pol in ("HH", "HV"):
        out[pol] = (_mean_db(_role(b, pol, window), _role(ex.get("before2"), pol, window)),
                    _role(d, pol, window), _role(ex.get("after"), pol, window))
    return out


def pair_arrays(pair, window, with_after=False):
    """Multilooked HH/HV before and during, plus bias-corrected ΔHH and ΔHV, for one grid window.

    with_after=True adds a 7th value: HH during minus HH after (bias-corrected), or None when the
    pair has no 'after' scene.
    """
    r = raw_pair(pair, window)
    k = C.MULTILOOK_PX
    hh_b, hh_d = boxcar_db(r["HH"][0], k), boxcar_db(r["HH"][1], k)
    hv_b, hv_d = boxcar_db(r["HV"][0], k), boxcar_db(r["HV"][1], k)
    bhh, bhv = pair_bias(pair)
    base = (hh_b, hv_b, hh_d, hv_d, hh_d - hh_b - bhh, hv_d - hv_b - bhv)
    if not with_after:
        return base
    exc = None
    if r["HH"][2] is not None:
        bias = 0.0
        p = C.WORK / "bias.json"
        if C.BIAS_CORRECT and p.exists():
            bias = json.loads(p.read_text()).get(pair, {}).get("dhh_after", 0.0)
        exc = hh_d - boxcar_db(r["HH"][2], k) - bias
    return base + (exc,)


def inside_mask(window):
    p = C.WORK / "aux" / "inside.tif"
    if not C.CLIP_TO_DISTRICTS or not p.exists():
        return np.ones((int(window.height), int(window.width)), bool)
    return read_win(p, window) == 1
