"""Diagnostic: is there a real under-canopy flood signal in these scenes?

Flood can only happen on low ground. So if the radar is seeing flood under trees,
tree pixels close to the river (low HAND) must show a strong HH rise far more often
than tree pixels high above it. If both look the same, what passes the rule is noise
or a scene-wide change, and no threshold will fix that.

Run after 04_detect.py (uses its bias estimate). Writes outputs/diagnose.csv.

    python pipeline/09_diagnose.py
"""
import numpy as np
import pandas as pd

import config as C
from common import ensure_dirs, tiles, read_win, pair_arrays, inside_mask, pair_bias, read_full

A = C.WORK / "aux"
BANDS = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 1e9)]
THRESH = [1.5, 2.0, 2.5, 3.0, 4.0]


def main():
    ensure_dirs()
    rows = []
    for pair in C.PAIRS:
        acc = {b: [] for b in BANDS}
        for inner, _ in tiles():
            wc = read_win(A / "worldcover.tif", inner)
            tree = (wc == C.TREE_CLASS) & inside_mask(inner)
            if not tree.any():
                continue
            *_, dhh, dhv, exc = pair_arrays(pair, inner, with_after=True)
            if exc is None:
                exc = np.full(dhh.shape, np.inf, dtype="float32")
            hand = read_win(A / "hand.tif", inner)
            s = np.s_[::5, ::5]                      # one sample per 50 m window
            tree, dhh, dhv, hand, exc = tree[s], dhh[s], dhv[s], hand[s], exc[s]
            ok = tree & np.isfinite(dhh) & np.isfinite(dhv) & np.isfinite(hand)
            for lo, hi in BANDS:
                m = ok & (hand >= lo) & (hand < hi)
                if m.any():
                    acc[(lo, hi)].append(np.stack([dhh[m], dhv[m], np.nan_to_num(exc[m], nan=-99.0, posinf=99.0)]))
        bhh, bhv = pair_bias(pair)
        print(f"\n=== pair {pair}  (scene-wide change removed: ΔHH {bhh:+.2f} dB, ΔHV {bhv:+.2f} dB)")
        print(f"{'height above river':>20} {'tree samples':>13} {'median ΔHH':>11} {'p95 ΔHH':>9}  "
              + "  ".join(f"≥{t:g} dB" for t in THRESH) + "   (% passing ΔHH ≥ t, ΔHV ≤ T_HV"
              + (", and brighter than the after scene)" if getattr(C, "EXTRA", {}).get(pair, {}).get("after") else ")"))
        for (lo, hi), parts in acc.items():
            if not parts:
                continue
            v = np.concatenate(parts, axis=1)
            name = f"{lo}-{hi:g} m" if hi < 1e8 else f">{lo} m"
            fr = [100 * float(((v[0] >= t) & (v[1] <= C.T_HV) & (v[2] >= C.T_AFTER)).mean()) for t in THRESH]
            print(f"{name:>20} {v.shape[1]:>13,} {np.median(v[0]):>+11.2f} {np.percentile(v[0],95):>+9.2f}  "
                  + "  ".join(f"{f:6.2f}%" for f in fr))
            rows.append(dict(pair=pair, hand_band=name, samples=v.shape[1], median_dhh=round(float(np.median(v[0])), 2),
                             p95_dhh=round(float(np.percentile(v[0], 95)), 2),
                             **{f"pct_ge_{t:g}dB": round(f, 3) for t, f in zip(THRESH, fr)}))
        mine = [r for r in rows if r["pair"] == pair]
        low, high = mine[:1], mine[-1:]
        if len(mine) >= 2:
            k = f"pct_ge_{C.T_HH:g}dB" if f"pct_ge_{C.T_HH:g}dB" in low[0] else "pct_ge_3dB"
            ratio = low[0][k] / max(high[0][k], 1e-3)
            verdict = ("SIGNAL: low ground passes far more often than high ground" if ratio >= 3 and low[0][k] >= 0.5
                       else "WEAK: some excess on low ground; lower T_HH only as far as high ground stays near zero" if ratio >= 1.5
                       else "NO SIGNAL: low and high ground look alike, so passing pixels are noise")
            print(f"   at T_HH = {C.T_HH:g} dB: lowest ground ({low[0]['hand_band']}) {low[0][k]:.2f}% vs highest ground "
                  f"({high[0]['hand_band']}) {high[0][k]:.2f}%  ->  {verdict}")
    pd.DataFrame(rows).to_csv(C.OUT / "diagnose.csv", index=False)

    # how much flood did C-band itself map inland?
    try:
        wtr, uid = read_full(A / "dswx_wtr_30m.tif"), read_full(A / "upazila_id_30m.tif")
        km = C.RES_CMP ** 2 / 1e6
        ins = uid > 0
        print(f"\nDSWx-S1 16 Jul inside the upazilas: open water {((wtr == 1) & ins).sum()*km:.1f} km², "
              f"inundated vegetation {((wtr == 3) & ins).sum()*km:.1f} km², "
              f"masked/no data {(np.isin(wtr, list(C.DSWX_NODATA)) & ins).sum()*km:.1f} km²")
        print("   (open water includes rivers, ponds and the coast; it is not all flood)")
    except Exception as e:
        print("DSWx summary skipped:", e)


if __name__ == "__main__":
    main()
