"""Step 13: flood under tree cover, from the loss of NISAR coherence (validated before it is used).

Backscatter brightness did not show flooding under village groves (METHOD.md section 3.2). Coherence
does: between two passes 12 days apart, a grove standing in water loses more coherence than a dry one.

Feature   coherence(30 Jun -> 12 Jul) minus coherence(18 Jun -> 30 Jun), HH, from the 20 m layer of the
          two GUNW files in data/nisar_gunw/, averaged onto the 30 m grid. The change seen on high forest
          that cannot flood (HAND > 20 m) is subtracted: either one scene-wide median or a local median
          within 10 km. The result is averaged over tree cells within 90 m or 150 m. The background method
          and the radius are chosen on the TRAIN sites only.
Eligible  30 m cells that are at least half tree cover, inside the district, not WorldCover 80/90/95,
          with before-flood coherence of 0.3 or more, on low ground. Low ground uses the ground HAND
          estimated from the open land within 300 m (the DEM is a surface model): 5 m or less.
Threshold the coherence loss that 10% of DRY train sites exceed, set with 5 km spatial cross-validation on
          the train sites. The test sites (labels/sites.csv, set = "test") are used once, to check it.
Accepted  only if all four criteria in CRITERIA hold. If any fails, nothing is written for the app.

Writes outputs/tree_flood_validation.json, outputs/tree_flood_models.csv and, when accepted,
       work/tree_flood_30m.tif (0 none, 1 possible, 2 likely, 255 not eligible), outputs/tree_flood_upazilas.csv.
Step 8 picks the accepted layer up from there.

    python pipeline/13_tree_flood.py
"""
import glob
import json
import time
import warnings

import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import config as C
import risk_common as R
from common import ensure_dirs, raw_pair, read_full, read_win, write_full

warnings.filterwarnings("ignore")
GUNW = "science/LSAR/GUNW/grids/frequencyA/wrappedInterferogram"
BEFORE_PAIR, FLOOD_PAIR = ("20260618T", "20260630T"), ("20260630T", "20260712T")
RADII_M = (90, 150)
BACKGROUNDS = ("scene-wide median", "local median within 10 km")
MIN_COH_BEFORE = 0.3
GROUND_HAND_MAX_M = 5.0
DRY_FALSE_ALARM = 0.10
LIKELY_WITHIN_M = 300
MIN_PATCH_HA = 0.5
SKIP_TEST_PLACES = ["Noapara"]
REPORTED = ["Satkania", "Lohagara", "Chandanaish", "Banshkhali", "Patiya", "Anowara"]
CRITERIA = dict(test_auc_min=0.75, test_recall_min=0.40, test_false_alarm_max=0.15, near_to_far_ratio_min=2.0)
MODEL_FEATS = ["coh_before", "coh_flood", "coh_change", "dhh", "dhv", "dratio"]


def coherence_30m(path):
    """HH coherence magnitude of one GUNW file, averaged onto the 30 m grid."""
    t30, w, h, crs, _ = R.grid30()
    with h5py.File(path, "r") as f:
        g = f[GUNW]
        x, y = g["xCoordinates"][:], g["yCoordinates"][:]
        epsg = int(np.array(g["projection"][()]).ravel()[0])
        dx, dy = x[1] - x[0], y[1] - y[0]
        tr = Transformer.from_crs(crs, f"EPSG:{epsg}", always_xy=True)
        x0, y1 = t30.c, t30.f
        xs, ys = tr.transform([x0, x0 + w * C.RES_CMP] * 2, [y1 - h * C.RES_CMP] * 2 + [y1] * 2)
        cols = np.where((x >= min(xs) - 200) & (x <= max(xs) + 200))[0]
        rows = np.where((y >= min(ys) - 200) & (y <= max(ys) + 200))[0]
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        a = g["HH/coherenceMagnitude"][r0:r1, c0:c1].astype("float32")
        a[~np.isfinite(a) | (a <= 0) | (a > 1)] = np.nan
        src_t = from_origin(x[c0] - dx / 2, y[r0] - dy / 2, dx, -dy)
    dst = np.full((h, w), np.nan, "float32")
    reproject(a, dst, src_transform=src_t, src_crs=f"EPSG:{epsg}", src_nodata=np.nan, dst_transform=t30, dst_crs=crs,
              dst_nodata=np.nan, resampling=Resampling.average)
    return dst


def find_pair(files, pair):
    hit = [f for f in files if f"_{pair[0]}" in f and f"_{pair[1]}" in f and f.index(f"_{pair[0]}") < f.index(f"_{pair[1]}")]
    if not hit:
        raise SystemExit(f"No GUNW file for {pair[0][:8]} -> {pair[1][:8]} in data/nisar_gunw/")
    return hit[0]


def local_background(d, ref, radius_m=10000, block_m=2000):
    """Median of d over the reference cells within radius_m, on a coarse grid, then spread to every cell."""
    h, w = d.shape
    rr, cc = np.nonzero(ref & np.isfinite(d))
    rr, cc = rr[::7], cc[::7]
    tree = cKDTree(np.c_[rr, cc] * C.RES_CMP)
    vals = d[rr, cc]
    k = block_m // C.RES_CMP
    br, bc = np.arange(k // 2, h, k), np.arange(k // 2, w, k)
    out = np.full((len(br), len(bc)), np.nan, "float32")
    centres = np.array([(r, c) for r in br for c in bc]) * C.RES_CMP
    for i, idx in enumerate(tree.query_ball_point(centres, radius_m)):
        if len(idx) >= 50:
            out.flat[i] = np.median(vals[idx])
    fill = float(np.median(vals))
    out = np.where(np.isfinite(out), out, fill)
    return ndi.zoom(out, (h / out.shape[0], w / out.shape[1]), order=1)[:h, :w].astype("float32"), fill


def site_table(score_maps, coh_b, coh_f, tree):
    """One row per label site: the coherence scores, grove-mean coherence, and grove-mean backscatter change."""
    t30, w, h, crs, _ = R.grid30()
    t10 = R.load_grid()[0] if hasattr(R, "load_grid") else None
    from common import load_grid
    t10, *_ = load_grid()
    bias = json.loads((C.WORK / "bias.json").read_text()).get(C.PRIMARY_PAIR, {}) if (C.WORK / "bias.json").exists() else {}
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    sites = pd.read_csv(C.LABELS)
    recs = []
    lin = lambda db: 10 ** (db / 10)
    from rasterio.windows import Window
    for _, s in sites.iterrows():
        x, y = tr.transform(s.lon, s.lat)
        c30, r30 = int((x - t30.c) / C.RES_CMP), int((t30.f - y) / C.RES_CMP)
        if not (0 <= r30 < h and 0 <= c30 < w):
            continue
        rec = dict(set=s["set"], label=int(s.label), place=s.place if isinstance(s.place, str) else "", upazila=s.upazila, x=x, y=y, r=r30, c=c30)
        for name, m in score_maps.items():
            rec[name] = float(m[r30, c30])
        P = 5
        sl = np.s_[r30 - P:r30 + P + 1, c30 - P:c30 + P + 1]
        yy, xx = np.mgrid[-P:P + 1, -P:P + 1]
        m30 = (np.hypot(yy, xx) * C.RES_CMP <= 150) & tree[sl] & np.isfinite(coh_b[sl]) & np.isfinite(coh_f[sl])
        rec["coh_before"] = float(coh_b[sl][m30].mean()) if m30.any() else np.nan
        rec["coh_flood"] = float(coh_f[sl][m30].mean()) if m30.any() else np.nan
        # backscatter change over the grove's tree pixels (10 m, unsmoothed), as in the earlier grove test
        col, row = int((x - t10.c) / C.RES), int((t10.f - y) / C.RES)
        Q = 15
        win = Window(col - Q, row - Q, 2 * Q + 1, 2 * Q + 1)
        rp = raw_pair(C.PRIMARY_PAIR, win)
        yy, xx = np.mgrid[-Q:Q + 1, -Q:Q + 1]
        arrs = [rp["HH"][0], rp["HH"][1], rp["HV"][0], rp["HV"][1]]
        ok = (read_win(R.A / "worldcover.tif", win) == C.TREE_CLASS) & (np.hypot(yy, xx) * C.RES <= 150) & np.all([np.isfinite(a) for a in arrs], axis=0)
        if ok.sum() >= 5:
            mb = [10 * np.log10(lin(a[ok]).mean()) for a in arrs]
            rec["dhh"] = mb[1] - mb[0] - bias.get("dhh", 0.0)
            rec["dhv"] = mb[3] - mb[2] - bias.get("dhv", 0.0)
            rec["dratio"] = rec["dhh"] - rec["dhv"]
        recs.append(rec)
    return pd.DataFrame(recs)


def auc_loss(y, score):
    """AUC with 'more coherence lost' (a lower score) meaning flooded."""
    return float(roc_auc_score(y, -np.asarray(score))) if 0 < y.sum() < len(y) else float("nan")


def metrics(y, pred, prob=None):
    tp, fp = int(((pred == 1) & (y == 1)).sum()), int(((pred == 1) & (y == 0)).sum())
    fn, tn = int(((pred == 0) & (y == 1)).sum()), int(((pred == 0) & (y == 0)).sum())
    p, r = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return dict(precision=p, recall=r, f1=2 * p * r / max(p + r, 1e-12), accuracy=(tp + tn) / max(len(y), 1),
                false_alarm_rate=fp / max(fp + tn, 1), auc=float(roc_auc_score(y, prob)) if prob is not None and 0 < y.sum() < len(y) else None,
                flooded=int(y.sum()), dry=int((y == 0).sum()))


def make_models():
    import lightgbm as lgb
    return {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000)),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=C.RANDOM_SEED),
        "lightgbm": lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=10, class_weight="balanced",
                                       random_state=C.RANDOM_SEED, verbose=-1),
    }


def main():
    t_start = time.time()
    ensure_dirs()
    t30, w, h, crs, _ = R.grid30()
    km2 = C.RES_CMP ** 2 / 1e6
    files = sorted(glob.glob(str(C.DATA / "nisar_gunw" / "*.h5")))
    coh_b, coh_f = coherence_30m(find_pair(files, BEFORE_PAIR)), coherence_30m(find_pair(files, FLOOD_PAIR))
    d = coh_f - coh_b

    uid = read_full(R.A / "upazila_id_30m.tif")
    names, ids = R.upazila_names(), R.upazila_ids()
    major, tree_share, excl = R.worldcover_30m()
    tree = tree_share >= 0.5
    hand = R.hand_30m()
    ground_hand = R.ground_estimate(hand, tree, 300)
    high_forest = tree & (hand > C.AUTO_DRY_HAND_M) & np.isfinite(d)

    # ---- 1. background and radius, chosen on the train sites
    scene_bg = float(np.median(d[high_forest]))
    local_bg, _ = local_background(d, high_forest)
    corrected = {BACKGROUNDS[0]: d - scene_bg, BACKGROUNDS[1]: d - local_bg}
    score_maps = {}
    for bname, dc in corrected.items():
        for rad in RADII_M:
            score_maps[f"{bname} | {rad} m"], _ = R.disc_mean(dc, tree, rad)
    S = site_table(score_maps, coh_b, coh_f, tree)
    S = S[~((S.set == "test") & S.place.isin(SKIP_TEST_PLACES))].reset_index(drop=True)
    TR, TE = S[S.set == "train"].reset_index(drop=True), S[S.set == "test"].reset_index(drop=True)
    choice = []
    for name in score_maps:
        q = TR.dropna(subset=[name])
        choice.append(dict(background=name.split(" | ")[0], radius_m=int(name.split(" | ")[1].split()[0]), train_auc=round(auc_loss(q.label.to_numpy(), q[name]), 4),
                           train_flooded=int((q.label == 1).sum()), train_dry=int((q.label == 0).sum()), key=name))
    cdf = pd.DataFrame(choice).sort_values("train_auc", ascending=False)
    best = cdf.iloc[0]
    key = best.key
    score = score_maps[key]
    TR, TE = TR.dropna(subset=[key]).reset_index(drop=True), TE.dropna(subset=[key]).reset_index(drop=True)
    TR["coh_change"], TE["coh_change"] = TR[key], TE[key]

    # ---- 3. threshold: 10% false alarms on dry train sites, with 5 km spatial cross-validation
    ytr, str_ = TR.label.to_numpy(), TR[key].to_numpy()
    groups = (np.floor(TR.x / C.BLOCK_M).astype(int) * 100000 + np.floor(TR.y / C.BLOCK_M).astype(int)).to_numpy()
    folds = list(GroupKFold(n_splits=5).split(str_, ytr, groups))
    cv_pred = np.zeros(len(ytr), int)
    fold_thr = []
    for tr_i, te_i in folds:
        t = float(np.quantile(str_[tr_i][ytr[tr_i] == 0], DRY_FALSE_ALARM))
        cv_pred[te_i] = (str_[te_i] <= t).astype(int)
        fold_thr.append(t)
    thr = float(np.quantile(str_[ytr == 0], DRY_FALSE_ALARM))
    yte, ste = TE.label.to_numpy(), TE[key].to_numpy()
    te_pred = (ste <= thr).astype(int)
    cv_m, te_m = metrics(ytr, cv_pred, -str_), metrics(yte, te_pred, -ste)

    # ---- 4. model comparison at grove scale
    rows = [dict(model="coherence threshold rule", scored_on="train sites, 5 km spatial CV", **cv_m),
            dict(model="coherence threshold rule", scored_on="test sites", **te_m)]
    trm, tem = TR.dropna(subset=MODEL_FEATS), TE.dropna(subset=MODEL_FEATS)
    Xtr, ytm, Xte, ytem = trm[MODEL_FEATS].to_numpy(), trm.label.to_numpy(), tem[MODEL_FEATS].to_numpy(), tem.label.to_numpy()
    gm = (np.floor(trm.x / C.BLOCK_M).astype(int) * 100000 + np.floor(trm.y / C.BLOCK_M).astype(int)).to_numpy()
    for n in make_models():
        oof = np.zeros(len(ytm))
        for a_i, b_i in GroupKFold(n_splits=5).split(Xtr, ytm, gm):
            oof[b_i] = make_models()[n].fit(Xtr[a_i], ytm[a_i]).predict_proba(Xtr[b_i])[:, 1]
        pt = make_models()[n].fit(Xtr, ytm).predict_proba(Xte)[:, 1]
        rows.append(dict(model=n, scored_on="train sites, 5 km spatial CV", **metrics(ytm, (oof >= 0.5).astype(int), oof)))
        rows.append(dict(model=n, scored_on="test sites", **metrics(ytem, (pt >= 0.5).astype(int), pt)))
    mdf = pd.DataFrame(rows).round(4)
    mdf.to_csv(C.OUT / "tree_flood_models.csv", index=False)

    # ---- 2. eligible cells and the map
    with np.errstate(invalid="ignore"):
        eligible = tree & (uid > 0) & ~excl & (coh_b >= MIN_COH_BEFORE) & (ground_hand <= GROUND_HAND_MAX_M) & np.isfinite(score)
        passed = eligible & (score <= thr)
    nf = read_full(R.A / "new_floodwater_30m.tif")
    dist_new = ndi.distance_transform_edt(~np.isin(nf, [1, 3])) * C.RES_CMP
    near, far = eligible & (dist_new <= 100), eligible & (dist_new > 1000)
    share = lambda m: float(passed[m].mean()) if m.any() else float("nan")
    grp = np.array([0] + [1 if nm in REPORTED else 2 for nm in names[1:]])[uid]
    s_near, s_far, s_rep, s_oth = share(near), share(far), share(eligible & (grp == 1)), share(eligible & (grp == 2))
    dist_rows = [dict(distance_to_new_floodwater="over 1000 m" if hi > 1e8 else f"{lo}-{hi:g} m", eligible_km2=round(m.sum() * km2, 1), passing_pct=round(100 * share(m), 2))
                 for lo, hi in ((0, 100), (100, 300), (300, 1000), (1000, 1e9)) for m in [eligible & (dist_new > lo if lo else dist_new >= 0) & (dist_new <= hi)]]

    crit = [
        dict(criterion=f"test AUC >= {CRITERIA['test_auc_min']}", value=round(te_m["auc"], 4), passed=bool(te_m["auc"] >= CRITERIA["test_auc_min"])),
        dict(criterion=f"test recall >= {CRITERIA['test_recall_min']:.0%} with test false alarms <= {CRITERIA['test_false_alarm_max']:.0%}",
             value=f"recall {te_m['recall']:.4f}, false alarms {te_m['false_alarm_rate']:.4f}",
             passed=bool(te_m["recall"] >= CRITERIA["test_recall_min"] and te_m["false_alarm_rate"] <= CRITERIA["test_false_alarm_max"])),
        dict(criterion=f"passing share within 100 m of new floodwater >= {CRITERIA['near_to_far_ratio_min']:g}x the share beyond 1 km",
             value=f"{100 * s_near:.2f}% against {100 * s_far:.2f}% (ratio {s_near / max(s_far, 1e-9):.2f})",
             passed=bool(s_near >= CRITERIA["near_to_far_ratio_min"] * s_far)),
        dict(criterion="passing share in the reported upazilas higher than in the others",
             value=f"{100 * s_rep:.2f}% against {100 * s_oth:.2f}%", passed=bool(s_rep > s_oth)),
    ]
    accepted = all(c["passed"] for c in crit)

    result = dict(
        accepted=accepted, criteria=crit,
        feature=dict(background=best.background, radius_m=int(best.radius_m), scene_wide_background=round(scene_bg, 4), choice_on_train_sites=cdf.drop(columns="key").to_dict("records")),
        threshold=dict(coherence_change_at_or_below=round(thr, 4), dry_train_false_alarm_target=DRY_FALSE_ALARM, fold_thresholds=[round(t, 4) for t in fold_thr],
                       train_cv=cv_m, test=te_m, test_left_out=SKIP_TEST_PLACES),
        eligible=dict(rule=f"at least half tree cover, inside the district, not WorldCover 80/90/95, before-flood coherence >= {MIN_COH_BEFORE}, ground HAND <= {GROUND_HAND_MAX_M:g} m (from open land within 300 m)",
                      km2=round(float(eligible.sum() * km2), 1), tree_km2_in_district=round(float((tree & (uid > 0)).sum() * km2), 1), passing_pct=round(100 * float(passed[eligible].mean()), 2)),
        distance_response=dist_rows, reported_upazilas=REPORTED,
        models=mdf.to_dict("records"),
        limits=["One flood, one track: a single pair of 12-day coherence images across the flood and one before it.",
                "Coherence also falls with rain, wind and crop growth; the high-forest background removes the scene-wide part only.",
                "Train sites are groves that C-band shows surrounded by new water; test sites are union-level reports.",
                "At the threshold, 10% of dry train groves pass by design, so part of the layer is noise.",
                "Deep forest with no open land within 300 m has no ground-height estimate and is not eligible."])

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 90)
    print("background and radius, chosen on the train sites:\n" + cdf.drop(columns="key").to_string(index=False))
    print(f"\nchosen: {best.background}, {int(best.radius_m)} m. Threshold: coherence change <= {thr:.4f} (fold thresholds {[round(t, 4) for t in fold_thr]})")
    print(f"train, cross-validated: recall {cv_m['recall']:.4f}, false alarms {cv_m['false_alarm_rate']:.4f}, AUC {cv_m['auc']:.4f} ({cv_m['flooded']} flooded, {cv_m['dry']} dry)")
    print(f"test (without {', '.join(SKIP_TEST_PLACES)}): recall {te_m['recall']:.4f}, false alarms {te_m['false_alarm_rate']:.4f}, AUC {te_m['auc']:.4f} ({te_m['flooded']} flooded, {te_m['dry']} dry)")
    print("\nmodels at grove scale:\n" + mdf.to_string(index=False))
    print(f"\neligible tree cells: {eligible.sum() * km2:.1f} km² of {(tree & (uid > 0)).sum() * km2:.0f} km² tree cover; passing {100 * passed[eligible].mean():.2f}%")
    print(pd.DataFrame(dist_rows).to_string(index=False))
    print("\ncriteria:\n" + pd.DataFrame(crit).to_string(index=False))
    print("\nACCEPTED" if accepted else "\nNOT ACCEPTED: nothing written for the app")

    if accepted:
        lab = read_full(C.WORK / "labels_30m.tif")
        open_flood = np.isin(lab, [1, 2])
        d_open = ndi.distance_transform_edt(~open_flood) * C.RES_CMP if open_flood.any() else np.full((h, w), np.inf)
        plab, _ = ndi.label(passed, structure=np.ones((3, 3), bool))
        keep = np.bincount(plab.ravel()) >= int(np.ceil(MIN_PATCH_HA * 1e4 / C.RES_CMP ** 2))
        keep[0] = False
        kept = keep[plab]
        tier = np.full((h, w), 255, "uint8")
        tier[eligible] = 0
        tier[kept] = 1
        tier[kept & (d_open <= LIKELY_WITHIN_M)] = 2
        write_full(C.WORK / "tree_flood_30m.tif", tier, res=C.RES_CMP, nodata=255)
        wtr = read_full(R.A / "dswx_wtr_30m.tif")
        pop = R.population_30m()
        near_any = ndi.distance_transform_edt(~(tier >= 1)) * C.RES_CMP <= 100
        near_likely = ndi.distance_transform_edt(~(tier == 2)) * C.RES_CMP <= 100 if (tier == 2).any() else np.zeros((h, w), bool)
        background_rate = s_far                                  # passing share far from any new floodwater
        urows = []
        for i in range(1, len(names)):
            u = uid == i
            f = u & (tier >= 1)
            n = max(int(f.sum()), 1)
            urows.append(dict(id=ids[i], name=names[i], likely_km2=round((u & (tier == 2)).sum() * km2, 2), possible_km2=round((u & (tier == 1)).sum() * km2, 2),
                              people_100m=int(round(pop[u & near_any].sum())), people_100m_likely=int(round(pop[u & near_likely].sum())),
                              cband_not_water_pct=round(100 * float((~np.isin(wtr[f], list(C.DSWX_WATER))).sum()) / n, 1) if f.any() else None,
                              cband_open_water_pct=round(100 * float((wtr[f] == 1).sum()) / n, 1) if f.any() else None,
                              cband_flooded_vegetation_pct=round(100 * float((wtr[f] == 3).sum()) / n, 1) if f.any() else None,
                              eligible_km2=round((u & eligible).sum() * km2, 1),
                              noise_km2_at_background_rate=round((u & eligible).sum() * km2 * background_rate, 2)))
        udf = pd.DataFrame(urows).sort_values("people_100m", ascending=False)
        udf.to_csv(C.OUT / "tree_flood_upazilas.csv", index=False)
        fa = tier >= 1
        nall = max(int(fa.sum()), 1)
        tot = dict(likely_km2=round(float((tier == 2).sum() * km2), 2), possible_km2=round(float((tier == 1).sum() * km2), 2),
                   people_100m=int(udf.people_100m.sum()), people_100m_likely=int(udf.people_100m_likely.sum()),
                   cband_not_water_pct=round(100 * float((~np.isin(wtr[fa], list(C.DSWX_WATER))).sum()) / nall, 1),
                   cband_open_water_pct=round(100 * float((wtr[fa] == 1).sum()) / nall, 1),
                   cband_flooded_vegetation_pct=round(100 * float((wtr[fa] == 3).sum()) / nall, 1),
                   dropped_small_patches_km2=round(float((passed & ~kept).sum() * km2), 2),
                   background_passing_pct=round(100 * background_rate, 2),
                   noise_km2_at_background_rate=round(float(eligible.sum() * km2 * background_rate), 2),
                   noise_share_of_layer_pct=round(100 * float(eligible.sum() * background_rate) / max(float(passed.sum()), 1), 1))
        result.update(totals=tot, upazilas=udf.to_dict("records"),
                      tiers=dict(likely=f"passes and within {LIKELY_WITHIN_M} m of NISAR open flood (labels 1 or 2)", possible="passes only", min_patch_ha=MIN_PATCH_HA))
        print("\ntotals:", tot)
        print("\ntop upazilas:\n" + udf.head(12).drop(columns="id").to_string(index=False))
    else:
        for stale in (C.WORK / "tree_flood_30m.tif", C.OUT / "tree_flood_upazilas.csv"):
            stale.unlink(missing_ok=True)
    (C.OUT / "tree_flood_validation.json").write_text(json.dumps(result, indent=1, default=float))
    print(f"({time.time() - t_start:.0f} s)")


if __name__ == "__main__":
    main()
