"""Step 0: look inside each NISAR file before processing it.

Prints the layers, projection (EPSG), pixel spacing, size, and the values in the
mask layer. Run it once and check the output against config.py (MASK_INVALID,
RES) before running step 2.

    python pipeline/00_inspect.py
"""
import h5py
import numpy as np

import config as C


def main():
    for role, g in C.SCENES.items():
        path = C.DATA / "nisar" / f"{g}.h5"
        print(f"\n=== {role}: {path.name}")
        if not path.exists():
            print("   MISSING - check data/nisar/")
            continue
        with h5py.File(path, "r") as f:
            grp = f[f"{C.GCOV_GROUP}/{C.FREQ}"]
            print("   layers:", ", ".join(k for k in grp.keys()))
            x, y = grp["xCoordinates"][:], grp["yCoordinates"][:]
            epsg = int(np.array(grp["projection"][()]).ravel()[0])
            print(f"   EPSG:{epsg}  size {len(x)} x {len(y)}  spacing x {x[1]-x[0]:.2f} m, y {y[1]-y[0]:.2f} m")
            print(f"   x {x.min():.0f}..{x.max():.0f}  y {y.min():.0f}..{y.max():.0f}")
            hh = grp["HHHH"]
            print(f"   HHHH dtype {hh.dtype}, shape {hh.shape}")
            # sample the centre 1000x1000 to keep memory low
            cy, cx = hh.shape[0] // 2, hh.shape[1] // 2
            s = np.s_[max(cy - 500, 0):cy + 500, max(cx - 500, 0):cx + 500]
            v = hh[s].astype("float64")
            v = v[np.isfinite(v) & (v > 0)]
            if v.size:
                db = 10 * np.log10(v)
                print(f"   HHHH centre sample (dB): p5 {np.percentile(db,5):.1f}  median {np.median(db):.1f}  p95 {np.percentile(db,95):.1f}")
            if "mask" in grp:
                m = grp["mask"][s]
                vals, counts = np.unique(m, return_counts=True)
                print("   mask values in centre sample:", dict(zip(vals.tolist(), counts.tolist())))
            print("   -> If HHHH median is about -5 to -15 dB, values are linear gamma0 as expected.")


if __name__ == "__main__":
    main()
