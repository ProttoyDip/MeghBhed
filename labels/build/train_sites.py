"""Part B: satellite-derived training sites (independent of NISAR).

Reads only work/aux/{inside,worldcover,hand}.tif, new_floodwater_30m.tif, pre_water_30m.tif, dswx_wtr_30m.tif,
upazila_id_30m.tif, upazila_index.json.

Flooded (1): WorldCover tree, HAND <= 5 m, and at least half of the non-tree land within 100 m is new floodwater.
Dry (0):     WorldCover tree, HAND <= 5 m, and no DSWx water (16 Jul or any pre date) within 1 km.
Sites are the centres of candidate pixels whose whole 70 m x 70 m neighbourhood is also candidate, so the 30 m
disc that 05_classify.py samples around each site stays inside the grove.

Usage: python train_sites.py <repo_root>
"""
import json, sys
from pathlib import Path
import numpy as np, rasterio
from pyproj import Transformer
from rasterio.windows import Window
from scipy import ndimage as ndi

root = Path(sys.argv[1]); here = Path(__file__).parent; sys.path.insert(0, str(root / "pipeline"))
import config as C
A = root / "work" / "aux"; k = C.RES_CMP // C.RES
HAND_MAX, WIN_M, MIN_NONTREE, DRY_DIST_M = 5.0, 100, 0.10, 1000
N_MAX, MIN_SEP_M, BLOCK_M, CAP = 400, 150, 5000, 10

with rasterio.open(A / "inside.tif") as s:
    ins_full = s.read(1) == 1; T = s.transform; crs = s.crs
rows, cols = np.where(ins_full.any(1))[0], np.where(ins_full.any(0))[0]
r0, r1 = (rows[0] // k) * k, -(-(rows[-1] + 1) // k) * k
c0, c1 = (cols[0] // k) * k, -(-(cols[-1] + 1) // k) * k
ins = ins_full[r0:r1, c0:c1]; del ins_full
win = Window(c0, r0, c1 - c0, r1 - r0); sl30 = np.s_[r0 // k:r1 // k, c0 // k:c1 // k]
print(f"working window {ins.shape[1]} x {ins.shape[0]} px at 10 m")
wc = rasterio.open(A / "worldcover.tif").read(1, window=win)
hand = rasterio.open(A / "hand.tif").read(1, window=win)
up = lambda a: np.repeat(np.repeat(a[sl30], k, 0), k, 1)
nf30 = rasterio.open(A / "new_floodwater_30m.tif").read(1)
w16 = rasterio.open(A / "dswx_wtr_30m.tif").read(1)
pw = rasterio.open(A / "pre_water_30m.tif").read(1)
uid10 = up(rasterio.open(A / "upazila_id_30m.tif").read(1))
names = ["-"] + [u["name"] for u in json.loads((A / "upazila_index.json").read_text())]

tree = wc == C.TREE_CLASS
with np.errstate(invalid="ignore"):
    lowtree = tree & (hand <= HAND_MAX) & ins
del hand
nontree = (~tree) & (wc != 80) & (wc != 0)          # non-tree land (permanent water is not land)
size = 2 * (WIN_M // C.RES) + 1
f_nl = ndi.uniform_filter(nontree.astype("float32"), size, mode="constant")
f_fw = ndi.uniform_filter((nontree & np.isin(up(nf30), [1, 3])).astype("float32"), size, mode="constant")
with np.errstate(invalid="ignore", divide="ignore"):
    ratio = np.where(f_nl > 0, f_fw / f_nl, 0).astype("float32")
cand1 = lowtree & (ratio >= 0.5) & (f_nl >= MIN_NONTREE)
del f_fw, nontree

anyw30 = np.isin(w16, list(C.DSWX_WATER)) | np.isin(w16, list(C.DSWX_NODATA)) | ((pw >= 1) & (pw != 255)) | (pw == 255)
far30 = ndi.distance_transform_edt(~anyw30) * C.RES_CMP > DRY_DIST_M
cand0 = lowtree & up(far30)
print(f"low tree pixels inside the district: {lowtree.sum() * C.RES**2 / 1e6:.1f} km²; "
      f"30 m cells farther than 1 km from any DSWx water: {100 * far30[sl30].mean():.1f}% of the window")

st8 = np.ones((3, 3), bool)
def summarise(cand, label):
    lab, n = ndi.label(cand, structure=st8)
    idx = np.flatnonzero(cand)
    labs, u = lab.ravel()[idx], uid10.ravel()[idx]
    px = np.bincount(u, minlength=len(names))
    _, first = np.unique(labs, return_index=True)
    gr = np.bincount(u[first], minlength=len(names))
    sizes = np.bincount(labs)[1:]
    print(f"\nlabel {label}: {cand.sum():,} candidate pixels ({cand.sum() * C.RES**2 / 1e6:.2f} km²) in {n:,} groves "
          f"(median grove {np.median(sizes) * C.RES**2:.0f} m², {(sizes >= 49).sum():,} groves of 0.5 ha or more)")
    return px, gr
px1, gr1 = summarise(cand1, 1)
px0, gr0 = summarise(cand0, 0)

core = lambda cand: ndi.uniform_filter(cand.astype("float32"), 7, mode="constant") > 0.999
inv = Transformer.from_crs(crs, 4326, always_xy=True)
rng = np.random.default_rng(C.RANDOM_SEED)
def sample(cand, label):
    cr = core(cand)
    idx = np.flatnonzero(cr)
    n_core = len(idx)
    if len(idx) > 400000:
        idx = rng.choice(idx, 400000, replace=False)
    idx = rng.permutation(idx)
    rr, cc = np.unravel_index(idx, cand.shape)
    x = T.c + (c0 + cc + 0.5) * T.a; y = T.f + (r0 + rr + 0.5) * T.e
    grid, blocks, out = {}, {}, []
    for i in range(len(idx)):
        b = (int(x[i] // BLOCK_M), int(y[i] // BLOCK_M))
        if blocks.get(b, 0) >= CAP:
            continue
        g = (int(x[i] // MIN_SEP_M), int(y[i] // MIN_SEP_M))
        near = [p for dx in (-1, 0, 1) for dy in (-1, 0, 1) for p in grid.get((g[0] + dx, g[1] + dy), [])]
        if any((x[i] - px) ** 2 + (y[i] - py) ** 2 < MIN_SEP_M ** 2 for px, py in near):
            continue
        grid.setdefault(g, []).append((x[i], y[i])); blocks[b] = blocks.get(b, 0) + 1
        lon, lat = inv.transform(x[i], y[i])
        out.append(dict(lon=round(lon, 6), lat=round(lat, 6), label=label, upazila=names[uid10[rr[i], cc[i]]],
                        fw_share=round(float(ratio[rr[i], cc[i]]), 2), nontree_share=round(float(f_nl[rr[i], cc[i]]), 2)))
        if len(out) == N_MAX:
            break
    print(f"label {label}: {n_core:,} core pixels -> {len(out)} sites in {len(blocks)} blocks of 5 km (cap {CAP} per block)")
    return out
s1, s0 = sample(cand1, 1), sample(cand0, 0)

print(f"\n{'upazila':18s} {'flooded px':>11s} {'groves':>7s} {'sites':>6s} | {'dry px':>10s} {'groves':>7s} {'sites':>6s}")
for i, n in enumerate(names):
    if i == 0: continue
    a, b = sum(s["upazila"] == n for s in s1), sum(s["upazila"] == n for s in s0)
    if px1[i] or px0[i]:
        print(f"{n:18s} {px1[i]:>11,} {gr1[i]:>7,} {a:>6} | {px0[i]:>10,} {gr0[i]:>7,} {b:>6}")
print(f"{'TOTAL':18s} {px1[1:].sum():>11,} {gr1[1:].sum():>7,} {len(s1):>6} | {px0[1:].sum():>10,} {gr0[1:].sum():>7,} {len(s0):>6}")
(here / "train_sites.json").write_text(json.dumps(s1 + s0, indent=1))
if len(s1) < 50:
    print(f"\nSTOP: only {len(s1)} flooded sites (< 50). Rule not loosened.")
