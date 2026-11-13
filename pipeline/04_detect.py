"""Step 4: flood detector (rule-based, METHOD.md section 3).

Before differencing, backscatter is averaged over MULTILOOK_PX x MULTILOOK_PX pixels
to beat speckle, and the scene-wide change measured on high forest that cannot flood
(HAND > AUTO_DRY_HAND_M) is subtracted, so wet-season moisture is not read as flood.

OPEN FLOOD (value 2, the headline map). A 10 m pixel is open flood when it is
  inside the districts, NOT tree cover, not permanent water / wetland / mangrove,
  within OPEN_HAND_MAX_M of the nearest river,
  ΔHH <= DARK_DROP (HH dropped) and HH on the flood date <= DARK_DB (dark, smooth water).

UNDER TREES, UNVERIFIED (value 1). The original hidden-flood rule is kept:
  tree cover (WorldCover 10), not built-up, within HAND_MAX_M of the nearest river,
  ΔHH >= T_HH (double bounce under the canopy) and ΔHV <= T_HV (canopy unchanged).
  Tests against independent sites found no reliable under-tree signal, so this class is
  reported separately and never feeds a headline total.

Small patches are removed from both.

Writes work/flood_<pair>.tif  0 = not flagged, 1 = under trees (unverified),
                              2 = open flood, 255 = no data / outside
       work/bias.json         the scene-wide ΔHH, ΔHV per pair

    python pipeline/04_detect.py
"""
import json
import numpy as np
from scipy import ndimage as ndi

import config as C
from common import ensure_dirs, create, tiles, crop, read_win, write_win, pair_arrays, inside_mask, raw_pair

N, A = C.WORK / "nisar", C.WORK / "aux"


def clean(mask):
    if C.OPEN_RADIUS > 0:
        mask = ndi.binary_opening(mask, structure=ndi.generate_binary_structure(2, 1), iterations=C.OPEN_RADIUS)
    if C.MIN_PATCH_PX > 1 and mask.any():
        lab, _ = ndi.label(mask)
        keep = np.bincount(lab.ravel()) >= C.MIN_PATCH_PX
        keep[0] = False
        mask = keep[lab]
    return mask


def measure_bias():
    """Median ΔHH and ΔHV over tree pixels that cannot flood (high above the river)."""
    out = {}
    for pair, (b, d) in C.PAIRS.items():
        dh, dv, da = [], [], []
        for inner, _ in tiles():
            s = np.s_[::10, ::10]
            hand = read_win(A / "hand.tif", inner)[s]
            wc = read_win(A / "worldcover.tif", inner)[s]
            ctrl = (wc == C.TREE_CLASS) & (hand > C.AUTO_DRY_HAND_M)
            if not ctrl.any():
                continue
            r = raw_pair(pair, inner)
            hh = r["HH"][1][s] - r["HH"][0][s]
            hv = r["HV"][1][s] - r["HV"][0][s]
            ok = ctrl & np.isfinite(hh) & np.isfinite(hv)
            dh.append(hh[ok]); dv.append(hv[ok])
            if r["HH"][2] is not None:
                aft = r["HH"][1][s] - r["HH"][2][s]
                da.append(aft[ctrl & np.isfinite(aft)])
        n = sum(len(x) for x in dh)
        if n < 500:
            out[pair] = dict(dhh=0.0, dhv=0.0, n=int(n))
            print(f"pair {pair}: too few high-forest pixels for a bias estimate, using 0")
        else:
            out[pair] = dict(dhh=float(np.median(np.concatenate(dh))), dhv=float(np.median(np.concatenate(dv))), n=int(n))
            print(f"pair {pair}: scene-wide change on high forest ΔHH {out[pair]['dhh']:+.2f} dB, ΔHV {out[pair]['dhv']:+.2f} dB")
        if da and sum(len(x) for x in da) >= 500:
            out[pair]["dhh_after"] = float(np.median(np.concatenate(da)))
            print(f"pair {pair}: during minus after on high forest {out[pair]['dhh_after']:+.2f} dB")
    (C.WORK / "bias.json").write_text(json.dumps(out, indent=1))


def detect_tile(pair, window):
    hh_b, hv_b, hh_d, hv_d, dhh, dhv, exc = pair_arrays(pair, window, with_after=True)
    wc = read_win(A / "worldcover.tif", window)
    hand = read_win(A / "hand.tif", window)
    inside = inside_mask(window)
    valid = np.isfinite(dhh) & np.isfinite(dhv) & inside
    tree = wc == C.TREE_CLASS
    built = wc == C.BUILT_CLASS
    if C.BUILT_BUFFER_PX:
        built = ndi.binary_dilation(built, iterations=C.BUILT_BUFFER_PX)
    with np.errstate(invalid="ignore"):
        low = hand <= C.HAND_MAX_M
        ok = valid & low & ~np.isin(wc, list(C.EXCLUDE_CLASSES))
        hidden = ok & tree & ~built & (dhh >= C.T_HH) & (dhv <= C.T_HV)
        if exc is not None:                       # flood is temporary: brighter than after it drained, too
            hidden &= exc >= C.T_AFTER
        dark = ok & ~tree & (hand <= C.OPEN_HAND_MAX_M) & (hh_d <= C.DARK_DB) & (dhh <= C.DARK_DROP)
    out = np.zeros(dhh.shape, dtype="uint8")
    out[clean(dark)] = 2
    out[clean(hidden)] = 1
    out[~valid] = 255
    return out


def main():
    ensure_dirs()
    if C.BIAS_CORRECT:
        measure_bias()
    for pair, (b, d) in C.PAIRS.items():
        ex = getattr(C, "EXTRA", {}).get(pair, {})
        if ex:
            print(f"pair {pair}: using extra scenes {', '.join(f'{k} ({v})' for k, v in ex.items())}")
        if not all((N / f"{r}_{p}.tif").exists() for r in (b, d) for p in ("HH", "HV")):
            print(f"skip pair {pair}: run 02_nisar.py first")
            continue
        out = C.WORK / f"flood_{pair}.tif"
        create(out, dtype="uint8", nodata=255)
        n_hidden = n_dark = n_valid = 0
        for inner, padded in tiles(pad=32):
            res = crop(detect_tile(pair, padded), inner, padded)
            write_win(out, res, inner)
            n_hidden += int((res == 1).sum()); n_dark += int((res == 2).sum()); n_valid += int((res != 255).sum())
        km = C.RES ** 2 / 1e6
        print(f"pair {pair}: open flood {n_dark*km:.1f} km², under trees (unverified) {n_hidden*km:.1f} km² "
              f"(of {n_valid*km:.0f} km² covered inside the districts)")


if __name__ == "__main__":
    main()
