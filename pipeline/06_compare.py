"""Step 6: comparison with C-band on the 30 m DSWx-S1 grid (METHOD.md section 4).

Each NISAR flood map is aggregated 10 m -> 30 m (a cell is flagged when at least
AGG_FRACTION of its valid 10 m pixels are). The flood pass is PRIMARY_PAIR (12 Jul);
the C-band map is DSWx-S1 of 16 Jul. Every 30 m cell gets one label:

  1 missed by the 16 Jul C-band map   NISAR open flood on 12 Jul, C-band not water on 16 Jul, not June water
  2 seen by both                      NISAR open flood on 12 Jul and C-band water on 16 Jul, not June water
  5 under trees, unverified           the HH-rise rule under tree cover (any pass); never in a headline total
  0 not flagged                       255 no data (DSWx-S1 masked, or no NISAR flood pass)

"June water" is water on any pre-flood DSWx-S1 date (work/aux/june_water_30m.tif): rivers, ponds
and seasonal water, not flood. Flood patches (labels 1 and 2 together) smaller than
OPEN_MIN_PATCH_HA are dropped, to cut scattered wet-field noise.

Writes work/labels_30m.tif
       work/drained_30m.tif   for labels 1 and 2: 1 = DRAIN_PAIR (19 Jul) covers the cell and it is no
                              longer dark ("drained within a week"), 0 = covered and still dark,
                              255 = not covered by that pass, or not a flood cell
       outputs/cband_vs_trees.csv   where C-band's own flood classes fall, and what C-band said
                                    at the cells NISAR flags

    python pipeline/06_compare.py
"""
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

import config as C
from common import ensure_dirs, load_grid, tiles, read_win, read_full, write_full


def flood_path(pair):
    if C.DETECTOR == "ml" and (C.WORK / f"flood_ml_{pair}.tif").exists():
        return C.WORK / f"flood_ml_{pair}.tif"
    return C.WORK / f"flood_{pair}.tif"


def aggregate(path, h30, w30):
    """Return (under_trees_flag, open_flood_flag, covered) at 30 m."""
    k = C.RES_CMP // C.RES
    hid, dark, cov = (np.zeros((h30, w30), bool) for _ in range(3))
    for inner, _ in tiles(size=k * 700):
        a = read_win(path, inner)
        hh, ww = a.shape[0] // k, a.shape[1] // k
        a = a[:hh * k, :ww * k].reshape(hh, k, ww, k)
        valid = (a != 255).sum(axis=(1, 3))
        r, c = int(inner.row_off) // k, int(inner.col_off) // k
        ok = valid >= (k * k) / 2
        hid[r:r + hh, c:c + ww] = ok & ((a == 1).sum(axis=(1, 3)) / np.maximum(valid, 1) >= C.AGG_FRACTION)
        dark[r:r + hh, c:c + ww] = ok & ((a == 2).sum(axis=(1, 3)) / np.maximum(valid, 1) >= C.AGG_FRACTION)
        cov[r:r + hh, c:c + ww] = ok
    return hid, dark, cov


def tree_30m(h30, w30):
    """True where at least half of a 30 m cell is WorldCover tree cover."""
    k = C.RES_CMP // C.RES
    out = np.zeros((h30, w30), bool)
    for inner, _ in tiles(size=k * 700):
        a = read_win(C.WORK / "aux" / "worldcover.tif", inner)
        hh, ww = a.shape[0] // k, a.shape[1] // k
        a = a[:hh * k, :ww * k].reshape(hh, k, ww, k)
        r, c = int(inner.row_off) // k, int(inner.col_off) // k
        out[r:r + hh, c:c + ww] = (a == C.TREE_CLASS).mean(axis=(1, 3)) >= 0.5
    return out


def drop_small(mask, min_ha):
    """Remove 8-connected patches smaller than min_ha from a 30 m mask."""
    min_cells = int(np.ceil(min_ha * 1e4 / C.RES_CMP ** 2))
    lab, _ = ndi.label(mask, structure=np.ones((3, 3), bool))
    keep = np.bincount(lab.ravel()) >= min_cells
    keep[0] = False
    return keep[lab]


def main():
    ensure_dirs()
    A = C.WORK / "aux"
    _, w30, h30, _ = load_grid(C.RES_CMP)
    pairs = [p for p in C.PAIRS if flood_path(p).exists()]
    if C.PRIMARY_PAIR not in pairs:
        raise SystemExit(f"No flood map for the flood pass (pair {C.PRIMARY_PAIR}): run 04_detect.py first")
    print(f"using {C.DETECTOR} maps for pairs {pairs}; flood pass = pair {C.PRIMARY_PAIR}")
    agg = {p: aggregate(flood_path(p), h30, w30) for p in pairs}
    trees, open_p, cov_p = agg[C.PRIMARY_PAIR]
    trees_any = np.any([agg[p][0] & agg[p][2] for p in pairs], axis=0)

    wtr = read_full(A / "dswx_wtr_30m.tif")
    water = np.isin(wtr, list(C.DSWX_WATER))
    dswx_bad = np.isin(wtr, list(C.DSWX_NODATA))
    if (A / "june_water_30m.tif").exists():
        jw = read_full(A / "june_water_30m.tif")
        june = (jw >= 1) & (jw != 255)
    else:
        print("WARNING: no june_water_30m.tif; permanent and seasonal water is NOT removed from the flood labels")
        june = np.zeros((h30, w30), bool)

    km2 = C.RES_CMP ** 2 / 1e6
    flood_raw = open_p & cov_p & ~june & ~dswx_bad
    flood = drop_small(flood_raw, C.OPEN_MIN_PATCH_HA)
    lab = np.zeros((h30, w30), "uint8")
    lab[trees_any] = 5
    lab[flood & ~water] = 1
    lab[flood & water] = 2
    lab[~cov_p | dswx_bad] = 255
    write_full(C.WORK / "labels_30m.tif", lab, res=C.RES_CMP, nodata=255)

    # drained within a week: the later pass covers the cell and no longer flags it dark
    drained = np.full((h30, w30), 255, "uint8")
    is_flood = np.isin(lab, [1, 2])
    if C.DRAIN_PAIR in agg:
        _, open_d, cov_d = agg[C.DRAIN_PAIR]
        drained[is_flood & cov_d & ~open_d] = 1
        drained[is_flood & cov_d & open_d] = 0
    else:
        print(f"WARNING: no flood map for pair {C.DRAIN_PAIR}; drained_30m.tif is all 'not covered'")
    write_full(C.WORK / "drained_30m.tif", drained, res=C.RES_CMP, nodata=255)

    names = {1: "missed by the 16 Jul C-band map", 2: "seen by both", 5: "under trees, unverified"}
    for v, n in names.items():
        print(f"{n:34s} {(lab == v).sum() * km2:8.2f} km²")
    print(f"{'open flood on June water (dropped)':34s} {(open_p & cov_p & june).sum() * km2:8.2f} km²")
    print(f"{'patches under ' + str(C.OPEN_MIN_PATCH_HA) + ' ha (dropped)':34s} {(flood_raw & ~flood).sum() * km2:8.2f} km²")
    print(f"{'no data':34s} {(lab == 255).mean() * 100:7.1f} % of grid")
    cv = is_flood & (drained != 255)
    if cv.any():
        print(f"drained by the pair {C.DRAIN_PAIR} pass: {100 * (drained[cv] == 1).mean():.0f}% of the "
              f"{cv.sum() * km2:.1f} km² of flood that pass covers ({100 * cv.sum() / max(is_flood.sum(), 1):.0f}% of all flood cells)")

    # ---- the premise, tested: where does C-band's own flood mapping fall?
    uid = read_full(A / "upazila_id_30m.tif")
    ins = (uid > 0) & ~dswx_bad
    tree = tree_30m(h30, w30)
    rows = []
    for name, m in (("under tree cover", tree), ("not under tree cover", ~tree)):
        a = ins & m
        rows.append(dict(ground=name, area_km2=round(a.sum() * km2, 1),
                         cband_open_water_km2=round((a & (wtr == 1)).sum() * km2, 2),
                         cband_flooded_vegetation_km2=round((a & (wtr == 3)).sum() * km2, 2),
                         cband_any_water_pct=round(100 * (a & water).sum() / max(a.sum(), 1), 2)))
    df = pd.DataFrame(rows)
    fv = df.cband_flooded_vegetation_km2
    share = 100 * fv[0] / max(fv.sum(), 1e-9)
    print("\nWhere C-band (DSWx-S1, 16 Jul) maps water inside the upazilas:")
    print(df.to_string(index=False))
    print(f"-> {share:.0f}% of C-band's flooded-vegetation area is under tree cover; "
          f"tree cover is {100 * df.area_km2[0] / max(df.area_km2.sum(), 1e-9):.0f}% of the land.")
    extra = []
    for name, f in (("NISAR open-flood cells (12 Jul, labels 1 and 2)", is_flood & ins),
                    ("NISAR under-tree cells (unverified)", (lab == 5) & ins)):
        n = max(f.sum(), 1)
        said = dict(nisar_km2=round(f.sum() * km2, 2),
                    cband_said_not_water_pct=round(100 * (f & ~water).sum() / n, 1),
                    cband_said_open_water_pct=round(100 * (f & (wtr == 1)).sum() / n, 1),
                    cband_said_flooded_vegetation_pct=round(100 * (f & (wtr == 3)).sum() / n, 1))
        print(f"At the {said['nisar_km2']} km² of {name}, C-band said: "
              f"not water {said['cband_said_not_water_pct']}%, open water {said['cband_said_open_water_pct']}%, "
              f"flooded vegetation {said['cband_said_flooded_vegetation_pct']}%.")
        extra.append(dict(ground=name, **said))
    pd.concat([df, pd.DataFrame(extra)], ignore_index=True).to_csv(C.OUT / "cband_vs_trees.csv", index=False)


if __name__ == "__main__":
    main()
