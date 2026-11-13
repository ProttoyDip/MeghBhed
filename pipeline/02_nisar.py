"""Step 2: NISAR GCOV -> speckle-filtered dB GeoTIFFs on the shared 10 m grid.

For each scene and each tile of the grid: read only the matching part of
HHHH, HVHV and mask from the HDF5 file, apply a Lee filter (same settings for
every date), reproject onto the grid, convert to dB. Writes
  work/nisar/<role>_HH.tif and <role>_HV.tif   (dB, NaN = no data)

    python pipeline/02_nisar.py
"""
import sys
import h5py
import numpy as np
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.ndimage import uniform_filter

import config as C
from common import ensure_dirs, load_grid, create, tiles, crop, write_win, window_transform


def lee(img, win, looks):
    """Classic Lee filter on linear intensity, NaN-safe."""
    valid = np.isfinite(img)
    x = np.where(valid, img, 0).astype("float64")
    n = uniform_filter(valid.astype("float64"), win)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = uniform_filter(x, win) / n
        var = np.maximum(uniform_filter(x * x, win) / n - mean ** 2, 0)
        ci2 = var / np.maximum(mean ** 2, 1e-12)
        k = np.clip(1 - (1.0 / looks) / np.maximum(ci2, 1e-12), 0, 1)
        out = mean + k * (x - mean)
    return np.where(valid, out, np.nan).astype("float32")


class Scene:
    def __init__(self, path):
        self.f = h5py.File(path, "r")
        self.g = self.f[f"{C.GCOV_GROUP}/{C.FREQ}"]
        self.x, self.y = self.g["xCoordinates"][:], self.g["yCoordinates"][:]
        self.crs = f"EPSG:{int(np.array(self.g['projection'][()]).ravel()[0])}"
        self.dx, self.dy = self.x[1] - self.x[0], self.y[1] - self.y[0]
        self.to_scene = Transformer.from_crs(C.CRS, self.crs, always_xy=True)

    def read(self, bounds, pad_px=8):
        """Read HHHH, HVHV for grid bounds (xmin, ymin, xmax, ymax) in C.CRS."""
        xmin, ymin, xmax, ymax = bounds
        xs, ys = self.to_scene.transform([xmin, xmax, xmin, xmax], [ymin, ymin, ymax, ymax])
        px, py = pad_px * abs(self.dx), pad_px * abs(self.dy)
        cols = np.where((self.x >= min(xs) - px) & (self.x <= max(xs) + px))[0]
        rows = np.where((self.y >= min(ys) - py) & (self.y <= max(ys) + py))[0]
        if cols.size < 2 or rows.size < 2:
            return None
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        bad = None
        if "mask" in self.g:
            bad = np.isin(self.g["mask"][r0:r1, c0:c1], list(C.MASK_INVALID))
        out = {}
        for pol in ("HHHH", "HVHV"):
            a = self.g[pol][r0:r1, c0:c1].astype("float32")
            a[~np.isfinite(a) | (a <= 0)] = np.nan
            if bad is not None:
                a[bad] = np.nan
            out[pol] = a
        # coordinates are pixel centres
        t = from_origin(self.x[c0] - self.dx / 2, self.y[r0] - self.dy / 2, self.dx, -self.dy)
        return out, t


def main():
    ensure_dirs()
    _, w, h, crs = load_grid()
    pad = C.LEE_WINDOW * 2
    for role, gname in C.SCENES.items():
        path = C.DATA / "nisar" / f"{gname}.h5"
        if not path.exists():
            print(f"skip {role}: {path.name} not found")
            continue
        outs = {p: C.WORK / "nisar" / f"{role}_{p}.tif" for p in ("HH", "HV")}
        if all(p.exists() for p in outs.values()) and "--force" not in sys.argv:
            print(f"{role}: already processed (use --force to redo)")
            continue
        sc = Scene(path)
        for p in outs.values():
            create(p)
        covered = 0
        for inner, padded in tiles(pad=pad):
            t = window_transform(padded)
            b = (t.c, t.f + t.e * padded.height, t.c + t.a * padded.width, t.f)
            res = sc.read(b)
            if res is None:
                continue
            bands, src_t = res
            for pol, a in bands.items():
                if np.isfinite(a).sum() == 0:
                    continue
                a = lee(a, C.LEE_WINDOW, C.LEE_LOOKS)
                dst = np.full((int(padded.height), int(padded.width)), np.nan, dtype="float32")
                reproject(a, dst, src_transform=src_t, src_crs=sc.crs, src_nodata=np.nan,
                          dst_transform=t, dst_crs=crs, dst_nodata=np.nan, resampling=Resampling.bilinear)
                with np.errstate(divide="ignore", invalid="ignore"):
                    db = 10 * np.log10(dst)
                db = crop(db, inner, padded)
                tag = "HH" if pol == "HHHH" else "HV"
                write_win(outs[tag], db, inner)
                if tag == "HH":
                    covered += int(np.isfinite(db).sum())
        print(f"{role}: {100 * covered / (w * h):.0f}% of the grid covered")
        sc.f.close()


if __name__ == "__main__":
    main()
