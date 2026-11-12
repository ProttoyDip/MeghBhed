"""Shared helpers for the two risk maps (11_flood_risk.py, 12_landslide_risk.py).

Everything here works on the 30 m comparison grid, which fits in memory.
"""
import json
from datetime import date

import numpy as np
import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rasterio.windows import Window
from scipy import ndimage as ndi

import config as C
from common import load_grid, read_full, warp_window

A = C.WORK / "aux"
K = C.RES_CMP // C.RES
CLASS_NAMES = {1: "low", 2: "medium", 3: "high", 4: "very high"}


def grid30():
    t, w, h, crs = load_grid(C.RES_CMP)
    return t, w, h, crs, Window(0, 0, w, h)


def dem_30m():
    """Copernicus DEM (a SURFACE model: it includes tree canopy and buildings) on the 30 m grid."""
    *_, full = grid30()
    files = sorted((C.DATA / "dem").glob("*_DEM.tif"))
    return warp_window(files, full, res=C.RES_CMP, resampling=Resampling.bilinear)


def hand_30m():
    *_, full = grid30()
    files = sorted((C.DATA / "hand").glob("*_HAND.tif"))
    return warp_window(files, full, res=C.RES_CMP, resampling=Resampling.bilinear)


def slope_deg(z):
    gy, gx = np.gradient(z, C.RES_CMP, C.RES_CMP)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype("float32")


def nanmin_filter(a, size):
    """Minimum over a size x size window, ignoring NaN."""
    out = ndi.minimum_filter(np.where(np.isfinite(a), a, np.inf), size=size, mode="nearest")
    return np.where(np.isfinite(out), out, np.nan).astype("float32")


def nanmean_filter(a, size):
    ok = np.isfinite(a)
    num = ndi.uniform_filter(np.where(ok, a, 0).astype("float32"), size, mode="nearest")
    den = ndi.uniform_filter(ok.astype("float32"), size, mode="nearest")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan).astype("float32")


def worldcover_30m():
    """Per 30 m cell: majority WorldCover class, tree share, and whether any 10 m pixel is in EXCLUDE_CLASSES."""
    _, w, h, _, _ = grid30()
    major = np.zeros((h, w), "uint8")
    tree = np.zeros((h, w), "float32")
    excl = np.zeros((h, w), bool)
    classes = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100], "uint8")
    with rasterio.open(A / "worldcover.tif") as ws:
        for r in range(0, h, 600):
            n = min(600, h - r)
            a = ws.read(1, window=Window(0, r * K, w * K, n * K)).reshape(n, K, w, K)
            counts = np.stack([(a == c).sum(axis=(1, 3)) for c in classes])
            major[r:r + n] = np.where(counts.max(0) > 0, classes[counts.argmax(0)], 0)
            tree[r:r + n] = (a == C.TREE_CLASS).mean(axis=(1, 3))
            excl[r:r + n] = np.isin(a, list(C.EXCLUDE_CLASSES)).any(axis=(1, 3))
    return major, tree, excl


def distance_m(mask):
    """Distance in metres from every cell to the nearest True cell."""
    if not mask.any():
        return np.full(mask.shape, np.nan, "float32")
    return (ndi.distance_transform_edt(~mask) * C.RES_CMP).astype("float32")


def sea_mask(major):
    """Open sea and wide estuary: WorldCover water at least 1 km wide and connected to the west or south grid edge."""
    water = major == 80
    core = ndi.distance_transform_edt(water) * C.RES_CMP > 500           # middle of water bodies over 1 km wide
    wide = (ndi.distance_transform_edt(~core) * C.RES_CMP <= 500) & water
    lab, _ = ndi.label(wide, structure=np.ones((3, 3), bool))
    edge = np.unique(np.concatenate([lab[:, 0], lab[-1, :]]))
    return np.isin(lab, edge[edge > 0])


def block_ids(rows, cols):
    n = C.BLOCK_M // C.RES_CMP
    return (rows // n).astype(np.int64) * 100000 + (cols // n)


def sample_even(rows, cols, n_max, rng):
    """Up to n_max cells, the same cap for every 5 km block, so no area dominates."""
    blocks = block_ids(rows, cols)
    order = rng.permutation(len(rows))
    b = blocks[order]
    srt = np.argsort(b, kind="stable")
    rank = np.empty(len(b), np.int64)
    _, start, counts = np.unique(b[srt], return_index=True, return_counts=True)
    rank[srt] = np.arange(len(b)) - np.repeat(start, counts)            # position of each cell inside its block
    lo, hi = 1, int(counts.max())
    while lo < hi:                                                      # largest per-block cap that stays under n_max
        mid = (lo + hi + 1) // 2
        if np.minimum(counts, mid).sum() <= n_max:
            lo = mid
        else:
            hi = mid - 1
    keep = order[rank < lo]
    return np.sort(keep), lo


def calibration_table(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        rows.append(dict(bin=f"{edges[b]:.1f}-{edges[b + 1]:.1f}", cells=int(m.sum()),
                         mean_predicted=round(float(p[m].mean()), 3) if m.any() else None,
                         observed_flood_share=round(float(y[m].mean()), 3) if m.any() else None))
    ece = float(sum(r["cells"] * abs(r["mean_predicted"] - r["observed_flood_share"]) for r in rows if r["cells"]) / len(p))
    return rows, ece


def write_overlay_png(classes, colours, png_path, bounds_path, max_px=4000):
    """Colour a class raster (0/255 = nothing) and save it as a transparent PNG in Web Mercator for the app.

    colours: {class value: (r, g, b, alpha)}. The bounds file lists the four corners in lon/lat, in the
    order MapLibre's image source wants (top-left, top-right, bottom-right, bottom-left).
    """
    from PIL import Image
    from pyproj import Transformer

    t, w, h, crs, _ = grid30()
    data = np.where(np.isin(classes, list(colours)), classes, 0).astype("uint8")
    rr, cc = np.where(data.any(1))[0], np.where(data.any(0))[0]
    r0, r1, c0, c1 = rr[0], rr[-1] + 1, cc[0], cc[-1] + 1
    src = data[r0:r1, c0:c1]
    src_t = t * rasterio.Affine.translation(c0, r0)
    left, top = src_t * (0, 0)
    right, bottom = src_t * (src.shape[1], src.shape[0])
    dst_t, dw, dh = calculate_default_transform(crs, "EPSG:3857", src.shape[1], src.shape[0], left, bottom, right, top)
    if max(dw, dh) > max_px:                  # keep both sides under the 4096 px texture limit of many phones
        scale = max(dw, dh) / max_px
        dst_t = dst_t * rasterio.Affine.scale(scale)
        dw, dh = int(np.ceil(dw / scale)), int(np.ceil(dh / scale))
    dst = np.zeros((dh, dw), "uint8")
    reproject(src, dst, src_transform=src_t, src_crs=crs, dst_transform=dst_t, dst_crs="EPSG:3857",
              resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    img = Image.fromarray(dst, mode="P")
    pal, alpha = [0] * 768, [0] * 256
    for v, (r, g, b, a) in colours.items():
        pal[v * 3:v * 3 + 3] = [r, g, b]
        alpha[v] = a
    img.putpalette(pal)
    img.save(png_path, optimize=True, transparency=bytes(alpha))
    x0, y1 = dst_t * (0, 0)
    x1, y0 = dst_t * (dw, dh)
    ll = Transformer.from_crs(3857, 4326, always_xy=True)
    (w_, n_), (e_, s_) = ll.transform(x0, y1), ll.transform(x1, y0)
    corners = [[w_, n_], [e_, n_], [e_, s_], [w_, s_]]
    bounds = dict(coordinates=[[round(x, 6), round(y, 6)] for x, y in corners], crs="EPSG:3857", width=dw, height=dh,
                  classes={str(v): dict(name=CLASS_NAMES.get(v, str(v)), colour="#%02x%02x%02x" % c[:3]) for v, c in colours.items()})
    bounds_path.write_text(json.dumps(bounds, indent=1))
    return dw, dh, png_path.stat().st_size / 1e3


def _json_safe(o):
    """Replace NaN and infinity with null, and numpy scalars with plain numbers, all the way down."""
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    if isinstance(o, np.generic):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def update_risk_json(key, payload):
    """Merge one map's results into outputs/risk.json (and the app's copy), keeping the other map's block."""
    out = C.OUT / "risk.json"
    data = json.loads(out.read_text()) if out.exists() else {}
    data["generated"] = str(date.today())
    data[key] = payload
    text = json.dumps(_json_safe(data), indent=1, ensure_ascii=False, allow_nan=False)   # NaN is not valid JSON
    out.write_text(text, encoding="utf-8")
    if C.WEB_DATA.parent.exists():
        C.WEB_DATA.mkdir(parents=True, exist_ok=True)
        (C.WEB_DATA / "risk.json").write_text(text, encoding="utf-8")


def upazila_names():
    return ["-"] + [u["name"] for u in json.loads((A / "upazila_index.json").read_text())]


def upazila_ids():
    return [None] + [u["id"] for u in json.loads((A / "upazila_index.json").read_text())]


def population_30m():
    return np.nan_to_num(read_full(A / "population_30m.tif")).astype("float64")


def open_land_mean(a, tree, radius_m=300):
    """Mean of `a` over the NON-tree cells within radius_m of each cell (NaN where there are none).

    The DEM is a surface model, so under tree cover elevation and HAND include the canopy. The open
    ground next to a grove is the best available estimate of the ground under it.
    """
    k = int(round(radius_m / C.RES_CMP))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disc = (np.hypot(yy, xx) <= k).astype("float32")
    ok = (~tree) & np.isfinite(a)
    num = ndi.convolve(np.where(ok, a, 0).astype("float32"), disc, mode="constant")
    den = ndi.convolve(ok.astype("float32"), disc, mode="constant")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0.5, num / den, np.nan).astype("float32")


def ground_estimate(a, tree, radius_m=300):
    """`a` on open land; under tree cover, the mean of the open land within radius_m (NaN if none)."""
    return np.where(tree, open_land_mean(a, tree, radius_m), a).astype("float32")


def disc_mean(a, mask, radius_m):
    """Mean of `a` over the cells of `mask` within radius_m, and how many cells that was."""
    k = int(round(radius_m / C.RES_CMP))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disc = (np.hypot(yy, xx) <= k).astype("float32")
    ok = mask & np.isfinite(a)
    num = ndi.convolve(np.where(ok, a, 0).astype("float32"), disc, mode="constant")
    den = ndi.convolve(ok.astype("float32"), disc, mode="constant")
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0.5, num / den, np.nan).astype("float32"), den
