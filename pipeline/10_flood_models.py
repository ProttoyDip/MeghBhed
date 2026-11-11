"""Step 10 (evaluation only): can a classifier map the 12 Jul open flood better than the rule?

Task: classify open flood on the flood pass (PRIMARY_PAIR, 12 Jul) from NISAR alone.
Features are radar only: HH and HV before and during, HH change, HV change, HH minus HV during.
No HAND, slope or texture. Samples are 30 m cells (the centre 10 m pixel of each, after the
pipeline's multilook and bias correction).

Train positives  C-band NEW open water: open water on 16 Jul, not water on any June date,
                 non-tree, HAND <= OPEN_HAND_MAX_M, not WorldCover 80/90/95.
Train negatives  (a) non-tree cells on HAND 8-40 m with slope under 5 degrees (cannot flood);
                 (b) cells that were open water on every June date (permanent water: dark, but not new);
                 (c) low-ground non-tree cells with features from the no-flood pair 18 Jun -> 30 Jun.
Models           the rule of step 4 (HH drop and HH level), Random Forest, LightGBM.
Validation       5 km spatial cross-validation.
Independent test (report-based, never used for training)
                 share of open low ground flagged within 500 m of the flooded test points against the dry
                 ones in labels/sites.csv, and share of cropland flagged in the upazilas reported badly
                 flooded against the others. Map predictions are cross-fitted: a cell is always predicted
                 by a model that did not train on its 5 km block.

Writes outputs/flood_model_comparison.csv, outputs/flood_feature_importance.csv and
       web/public/data/model_comparison.json. It does NOT change the pipeline's flood map.

    python pipeline/10_flood_models.py
"""
import json
import warnings

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold

import config as C
from common import ensure_dirs, load_grid, tiles, crop, read_win, read_full, pair_arrays, boxcar_db, inside_mask

FEATS = ["hh_b", "hv_b", "hh_d", "hv_d", "dhh", "dhv", "ratio_d"]
N_PER_CLASS = 30000
REPORTED = ["Satkania", "Lohagara", "Chandanaish", "Banshkhali", "Patiya", "Anowara"]   # named badly flooded, 10-12 Jul
SKIP_TEST_PLACES = ["Noapara"]      # "dry" test place that the 12 Jul check showed was flooded: left out
A = C.WORK / "aux"
K = C.RES_CMP // C.RES


def centre_cells(get):
    """Fill 30 m arrays from a function window -> tuple of 10 m arrays, taking each cell's centre pixel."""
    _, w30, h30, _ = load_grid(C.RES_CMP)
    out = None
    for inner, padded in tiles(pad=8):
        if not inside_mask(inner).any():
            continue
        arrs = [crop(a, inner, padded) for a in get(padded)]
        if out is None:
            out = [np.full((h30, w30), np.nan, "float32") for _ in arrs]
        r, c = int(inner.row_off), int(inner.col_off)
        ii, jj = np.arange(int(inner.height)), np.arange(int(inner.width))
        si, sj = ii[(r + ii) % K == 1], jj[(c + jj) % K == 1]
        R, Cc = (r + si) // K, (c + sj) // K
        o1, o2 = R < h30, Cc < w30
        for dst, src in zip(out, arrs):
            dst[np.ix_(R[o1], Cc[o2])] = src[np.ix_(si[o1], sj[o2])]
    return out


def flood_pass(window):
    hh_b, hv_b, hh_d, hv_d, dhh, dhv = pair_arrays(C.PRIMARY_PAIR, window)
    return hh_b, hv_b, hh_d, hv_d, dhh, dhv, hh_d - hv_d


def no_flood_pass(window):
    """The two 'before' scenes as a pair with no flood between them: before = 18 Jun, during = 30 Jun."""
    b, d = C.EXTRA[C.PRIMARY_PAIR]["before2"], C.PAIRS[C.PRIMARY_PAIR][0]
    N = C.WORK / "nisar"
    hh_b, hv_b, hh_d, hv_d = (boxcar_db(read_win(N / f"{r}_{p}.tif", window), C.MULTILOOK_PX)
                              for r, p in ((b, "HH"), (b, "HV"), (d, "HH"), (d, "HV")))
    return hh_b, hv_b, hh_d, hv_d, hh_d - hh_b, hv_d - hv_b, hh_d - hv_d


def land_30m():
    _, w30, h30, _ = load_grid(C.RES_CMP)
    tree, wcx, crop40 = (np.zeros((h30, w30), bool) for _ in range(3))
    hand, slope = (np.full((h30, w30), np.nan, "float32") for _ in range(2))
    with rasterio.open(A / "worldcover.tif") as ws, rasterio.open(A / "hand.tif") as hs, rasterio.open(A / "slope.tif") as ss:
        for r in range(0, h30, 600):
            n = min(600, h30 - r)
            win = Window(0, r * K, w30 * K, n * K)
            a = ws.read(1, window=win).reshape(n, K, w30, K)
            tree[r:r + n] = (a == C.TREE_CLASS).mean(axis=(1, 3)) >= 0.5
            wcx[r:r + n] = np.isin(a, list(C.EXCLUDE_CLASSES)).any(axis=(1, 3))
            crop40[r:r + n] = (a == 40).mean(axis=(1, 3)) >= 0.5
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)      # all-NaN cells at the grid edge
                hand[r:r + n] = np.nanmean(hs.read(1, window=win).astype("float32").reshape(n, K, w30, K), axis=(1, 3))
                slope[r:r + n] = np.nanmean(ss.read(1, window=win).astype("float32").reshape(n, K, w30, K), axis=(1, 3))
    return tree, wcx, crop40, hand, slope


def rule(X):
    return ((X[:, FEATS.index("dhh")] <= C.DARK_DROP) & (X[:, FEATS.index("hh_d")] <= C.DARK_DB)).astype(int)


def make_models():
    import lightgbm as lgb
    return {
        "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=5, class_weight="balanced",
                                                n_jobs=-1, random_state=C.RANDOM_SEED),
        "lightgbm": lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                                       class_weight="balanced", random_state=C.RANDOM_SEED, verbose=-1),
    }


def main():
    ensure_dirs()
    if "before2" not in C.EXTRA.get(C.PRIMARY_PAIR, {}):
        raise SystemExit("Needs the second 'before' scene (18 Jun) for the no-flood pair.")
    t30, w30, h30, crs = load_grid(C.RES_CMP)
    rng = np.random.default_rng(C.RANDOM_SEED)
    F = np.stack(centre_cells(flood_pass), axis=-1)             # (h30, w30, 7), flood pass
    Fn = np.stack(centre_cells(no_flood_pass), axis=-1)         # no-flood pair
    # the no-flood pair gets its own scene-wide offset, measured the same way: high, flat, non-flooding ground
    tree, wcx, crop40, hand, slope = land_30m()
    uid = read_full(A / "upazila_id_30m.tif")
    wtr = read_full(A / "dswx_wtr_30m.tif")
    jw, jo = read_full(A / "june_water_30m.tif"), read_full(A / "june_open_30m.tif")
    n_dates = len(json.loads((A / "june_dates.json").read_text()))
    ins = uid > 0
    okF, okN = np.isfinite(F).all(-1) & ins, np.isfinite(Fn).all(-1) & ins
    high = ins & tree & (hand > C.AUTO_DRY_HAND_M)
    for j in (FEATS.index("dhh"), FEATS.index("dhv")):
        Fn[..., j] -= np.nanmedian(Fn[..., j][high & okN])
    low_open = ~tree & (hand <= C.OPEN_HAND_MAX_M) & ~wcx
    june = (jw >= 1) & (jw != 255)

    masks = {
        "positive: C-band new open water": (okF & low_open & (wtr == 1) & ~june & (jw != 255), F, 1),
        "negative (a): high flat non-tree ground": (okF & ~tree & (hand >= 8) & (hand <= 40) & (slope < 5), F, 0),
        "negative (b): open water on every June date": (okF & (jo == n_dates) & (jo != 255), F, 0),
        "negative (c): low ground, no-flood pair 18-30 Jun": (okN & low_open & ~june, Fn, 0),
    }
    parts = []
    for name, (m, src, y) in masks.items():
        rr, cc = np.nonzero(m)
        if len(rr) > N_PER_CLASS:
            pick = rng.choice(len(rr), N_PER_CLASS, replace=False)
            rr, cc = rr[pick], cc[pick]
        d = pd.DataFrame(src[rr, cc], columns=FEATS)
        d["y"], d["kind"], d["r"], d["c"] = y, name, rr, cc
        parts.append(d)
        print(f"{name:52s} {m.sum() * C.RES_CMP**2 / 1e6:8.1f} km² available, {len(d):6d} sampled")
    S = pd.concat(parts, ignore_index=True)
    X, y = S[FEATS].to_numpy(), S.y.to_numpy()
    cells_per_block = C.BLOCK_M // C.RES_CMP
    block = lambda r, c: (r // cells_per_block).astype(np.int64) * 100000 + (c // cells_per_block)
    groups = block(S.r.to_numpy(), S.c.to_numpy())

    # ---- 5 km spatial cross-validation
    folds = list(GroupKFold(n_splits=5).split(X, y, groups))
    fold_of_block = {}
    for f, (_, te) in enumerate(folds):
        fold_of_block.update({g: f for g in np.unique(groups[te])})
    oof = {n: np.zeros(len(y)) for n in make_models()}
    fold_models = []
    for tr, te in folds:
        fm = {}
        for n, m in make_models().items():
            fm[n] = m.fit(X[tr], y[tr])
            oof[n][te] = m.predict_proba(X[te])[:, 1]
        fold_models.append(fm)
    full = {n: m.fit(X, y) for n, m in make_models().items()}
    pred = {"rule (HH drop and HH level)": rule(X)} | {n: (p >= 0.5).astype(int) for n, p in oof.items()}

    rows = []
    for name, p in pred.items():
        row = dict(model=name, precision=precision_score(y, p), recall=recall_score(y, p), f1=f1_score(y, p),
                   false_alarm_rate=float(((p == 1) & (y == 0)).mean() / (y == 0).mean()),
                   auc=roc_auc_score(y, oof[name]) if name in oof else np.nan)
        for kshort, kname in (("a_high_ground", "negative (a)"), ("b_permanent_water", "negative (b)"), ("c_no_flood_pair", "negative (c)")):
            m = S.kind.str.startswith(kname).to_numpy()
            row[f"false_alarm_{kshort}"] = float(p[m].mean())
        rows.append(row)

    # ---- independent test on the map: cross-fitted predictions over open low ground on the flood pass
    dom = okF & low_open & ~june             # June water is removed from the flood map, so leave it out here too
    rr, cc = np.nonzero(dom)
    Xd = F[rr, cc]
    fold_d = np.array([fold_of_block.get(g, -1) for g in block(rr, cc)])
    flag = {"rule (HH drop and HH level)": np.zeros(dom.shape, bool)} | {n: np.zeros(dom.shape, bool) for n in full}
    flag["rule (HH drop and HH level)"][rr, cc] = rule(Xd) == 1
    for n in full:
        p = np.zeros(len(rr))
        for f in np.unique(fold_d):
            m = fold_d == f
            mdl = full[n] if f < 0 else fold_models[f][n]       # blocks never used in training: the full model
            p[m] = mdl.predict_proba(Xd[m])[:, 1]
        flag[n][rr, cc] = p >= 0.5

    names = ["-"] + [u["name"] for u in json.loads((A / "upazila_index.json").read_text())]
    grp = np.array([0] + [1 if nm in REPORTED else 2 for nm in names[1:]])[uid]
    sites = pd.read_csv(C.LABELS)
    sites = sites[(sites["set"] == "test") & ~sites.place.isin(SKIP_TEST_PLACES)]
    trf = Transformer.from_crs(4326, crs, always_xy=True)
    P = int(np.ceil(500 / C.RES_CMP))
    yy, xx = np.mgrid[-P:P + 1, -P:P + 1]
    disc = np.hypot(yy, xx) * C.RES_CMP <= 500
    near = {1: np.zeros(dom.shape, bool), 0: np.zeros(dom.shape, bool)}
    for _, s in sites.iterrows():
        x, yv = trf.transform(s.lon, s.lat)
        c, r = int((x - t30.c) / C.RES_CMP), int((t30.f - yv) / C.RES_CMP)
        near[int(s.label)][r - P:r + P + 1, c - P:c + P + 1] |= disc
    km2 = C.RES_CMP ** 2 / 1e6
    for row in rows:
        f = flag[row["model"]]
        share = lambda m: float(100 * (f & m).sum() / max(m.sum(), 1))
        row.update(flagged_km2=float(f.sum() * km2),
                   test_flagged_pct_near_flooded_points=share(dom & near[1]), test_flagged_pct_near_dry_points=share(dom & near[0]),
                   test_cropland_flagged_pct_reported_upazilas=share(dom & crop40 & (grp == 1)),
                   test_cropland_flagged_pct_other_upazilas=share(dom & crop40 & (grp == 2)))
        row["test_ratio_flooded_to_dry_points"] = row["test_flagged_pct_near_flooded_points"] / max(row["test_flagged_pct_near_dry_points"], 1e-9)
        row["test_ratio_reported_to_other_upazilas"] = (row["test_cropland_flagged_pct_reported_upazilas"]
                                                        / max(row["test_cropland_flagged_pct_other_upazilas"], 1e-9))
    res = pd.DataFrame(rows).round(3)
    res.to_csv(C.OUT / "flood_model_comparison.csv", index=False)
    imp = pd.DataFrame({"feature": FEATS} | {n: m.feature_importances_ / m.feature_importances_.sum() for n, m in full.items()}).round(3)
    imp.to_csv(C.OUT / "flood_feature_importance.csv", index=False)

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("\n5 km spatial cross-validation and the report-based test:\n" + res.T.to_string(header=False))
    print("\nfeature importance:\n" + imp.to_string(index=False))
    n_f, n_d = int((sites.label == 1).sum()), int((sites.label == 0).sum())
    print(f"\ntest points used: {n_f} flooded, {n_d} dry (left out: {', '.join(SKIP_TEST_PLACES)})")

    payload = dict(
        task="Classify open flood on 12 Jul 2026 from NISAR L-band (pair A), radar features only",
        features=FEATS, validation="5 km spatial cross-validation",
        train=dict(positives="C-band (DSWx-S1) new open water on 16 Jul, not water on any June date, non-tree, low ground",
                   negatives=["non-tree ground on HAND 8-40 m with slope under 5 degrees",
                              "open water on every June date (permanent water)",
                              "low non-tree ground seen through the no-flood pair 18 Jun to 30 Jun"],
                   samples={k: int(v) for k, v in S.kind.value_counts().items()}),
        test=dict(description="Report-based, never used for training: share of open low ground flagged within 500 m of test "
                              "points in unions reported submerged against points with no flood report, and share of "
                              "cropland flagged in upazilas reported badly flooded against the others",
                  flooded_points=n_f, dry_points=n_d, left_out=SKIP_TEST_PLACES, reported_upazilas=REPORTED),
        models=json.loads(res.to_json(orient="records")),
        feature_importance=json.loads(imp.to_json(orient="records")),
        pipeline_uses="rule (HH drop and HH level)")
    (C.OUT / "model_comparison.json").write_text(json.dumps(payload, indent=1))
    if C.WEB_DATA.parent.exists():
        C.WEB_DATA.mkdir(parents=True, exist_ok=True)
        (C.WEB_DATA / "model_comparison.json").write_text(json.dumps(payload, indent=1))
        print(f"wrote {C.WEB_DATA / 'model_comparison.json'}")


if __name__ == "__main__":
    main()
