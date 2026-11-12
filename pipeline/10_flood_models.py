"""Step 10 (evaluation only): benchmark models for the 12 Jul open flood, with tuned cut-offs and SHAP.

Task: binary classification of open flood on the flood pass (PRIMARY_PAIR, 12 Jul) from NISAR alone.
Features are radar only: HH and HV before and during, HH change, HV change, HH minus HV during.
No HAND, slope or texture. Samples are 30 m cells (the centre 10 m pixel of each, after the
pipeline's multilook and bias correction).

Train positives  C-band NEW open water: open water on 16 Jul, not water on any June date,
                 non-tree, HAND <= OPEN_HAND_MAX_M, not WorldCover 80/90/95.
Train negatives  (a) non-tree cells on HAND 8-40 m with slope under 5 degrees (cannot flood);
                 (b) cells that were open water on every June date (permanent water: dark, but not new);
                 (c) low-ground non-tree cells with features from the no-flood pair 18 Jun -> 30 Jun.
Models           the rule of step 4 (HH drop and HH level), logistic regression (standardised),
                 Random Forest, LightGBM.
Validation       5 km spatial cross-validation.
Cut-offs         "default" = probability 0.5. "tuned" = the precision-recall break-even point (precision
                 equals recall). Tuning is nested: inside each outer fold the cut-off is picked on that
                 fold's TRAINING data only (inner spatial split), then applied to the held-out fold.
                 A final cut-off is fitted on all training data for use on the map.
                 "global" = one break-even cut-off picked on the pooled held-out predictions; it is
                 reported for comparison only, because it has seen the data it is scored on.
Independent test (report-based sites in labels/sites.csv with set = "test"; NEVER used to train or tune)
                 share of open low ground flagged within 500 m of the flooded test points against the dry
                 ones, and share of cropland flagged in the upazilas reported badly flooded against the
                 others. Map predictions are cross-fitted: a cell is always predicted by a model that did
                 not train on its 5 km block.
Explainable AI   SHAP (TreeExplainer) for Random Forest and LightGBM, logistic coefficients, and two
                 waterfall examples.

Writes outputs/flood_model_comparison.csv, outputs/flood_rule_break_even.csv,
       outputs/flood_shap_importance.csv, outputs/flood_logistic_coefficients.csv, outputs/xai/flood_models_*.png,
       outputs/model_comparison.json and web/public/data/model_comparison.json.
It does NOT change the pipeline's flood map.

    python pipeline/10_flood_models.py
"""
import json
import time
import warnings

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import config as C
from common import ensure_dirs, load_grid, tiles, crop, read_win, read_full, pair_arrays, boxcar_db, inside_mask

warnings.filterwarnings("ignore", category=UserWarning)
FEATS = ["hh_b", "hv_b", "hh_d", "hv_d", "dhh", "dhv", "ratio_d"]
FEAT_LABELS = {"hh_b": "HH before", "hv_b": "HV before", "hh_d": "HH on 12 July", "hv_d": "HV on 12 July",
               "dhh": "HH change", "dhv": "HV change", "ratio_d": "HH minus HV on 12 July"}
RULE = "rule (HH drop and HH level)"
MODEL_LABELS = {RULE: "Threshold rule", "logistic_regression": "Logistic regression", "random_forest": "Random Forest", "lightgbm": "LightGBM"}
N_PER_CLASS = 30000
N_SHAP = {"lightgbm": 5000, "random_forest": 500}       # TreeSHAP on the deep Random Forest is slow, so fewer cells
REPORTED = ["Satkania", "Lohagara", "Chandanaish", "Banshkhali", "Patiya", "Anowara"]   # named badly flooded, 10-12 Jul
SKIP_TEST_PLACES = ["Noapara"]      # "dry" test place that the 12 Jul check showed was flooded: left out
TARGET_GAP, TARGET_ACC = 0.001, 0.90
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


def rule(X, drop=None, level=None):
    drop = C.DARK_DROP if drop is None else drop
    level = C.DARK_DB if level is None else level
    return ((X[:, FEATS.index("dhh")] <= drop) & (X[:, FEATS.index("hh_d")] <= level)).astype(int)


def make_models():
    import lightgbm as lgb
    return {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000)),
        "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=5, class_weight="balanced",
                                                n_jobs=-1, random_state=C.RANDOM_SEED),
        "lightgbm": lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                                       class_weight="balanced", random_state=C.RANDOM_SEED, verbose=-1),
    }


def break_even(p, y):
    """Cut-off at which precision equals recall: flag exactly as many cells as there are positives."""
    n_pos = int(y.sum())
    srt = np.sort(p)[::-1]
    return float((srt[n_pos - 1] + srt[min(n_pos, len(srt) - 1)]) / 2)


def metrics(y, pred, prob=None):
    tp, fp = int(((pred == 1) & (y == 1)).sum()), int(((pred == 1) & (y == 0)).sum())
    fn, tn = int(((pred == 0) & (y == 1)).sum()), int(((pred == 0) & (y == 0)).sum())
    prec, rec = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    spec = tn / max(tn + fp, 1)
    return dict(precision=prec, recall=rec, f1=f1, accuracy=(tp + tn) / len(y), balanced_accuracy=(rec + spec) / 2,
                false_alarm_rate=fp / max(fp + tn, 1), roc_auc=float(roc_auc_score(y, prob)) if prob is not None else None,
                tp=tp, fp=fp, fn=fn, tn=tn, positives=int(y.sum()), negatives=int((y == 0).sum()),
                max_gap_precision_recall_f1=max(prec, rec, f1) - min(prec, rec, f1))


def main():
    t_start = time.time()
    ensure_dirs()
    (C.OUT / "xai").mkdir(exist_ok=True)
    if "before2" not in C.EXTRA.get(C.PRIMARY_PAIR, {}):
        raise SystemExit("Needs the second 'before' scene (18 Jun) for the no-flood pair.")
    t30, w30, h30, crs = load_grid(C.RES_CMP)
    rng = np.random.default_rng(C.RANDOM_SEED)
    F = np.stack(centre_cells(flood_pass), axis=-1)             # (h30, w30, 7), flood pass
    Fn = np.stack(centre_cells(no_flood_pass), axis=-1)         # no-flood pair
    tree, wcx, crop40, hand, slope = land_30m()
    uid = read_full(A / "upazila_id_30m.tif")
    wtr = read_full(A / "dswx_wtr_30m.tif")
    jw, jo = read_full(A / "june_water_30m.tif"), read_full(A / "june_open_30m.tif")
    n_dates = len(json.loads((A / "june_dates.json").read_text()))
    ins = uid > 0
    okF, okN = np.isfinite(F).all(-1) & ins, np.isfinite(Fn).all(-1) & ins
    high = ins & tree & (hand > C.AUTO_DRY_HAND_M)
    for j in (FEATS.index("dhh"), FEATS.index("dhv")):          # the no-flood pair gets its own scene-wide offset
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
    for name, (m, src, y_) in masks.items():
        rr, cc = np.nonzero(m)
        if len(rr) > N_PER_CLASS:
            pick = rng.choice(len(rr), N_PER_CLASS, replace=False)
            rr, cc = rr[pick], cc[pick]
        d = pd.DataFrame(src[rr, cc], columns=FEATS)
        d["y"], d["kind"], d["r"], d["c"] = y_, name, rr, cc
        parts.append(d)
        print(f"{name:52s} {m.sum() * C.RES_CMP**2 / 1e6:8.1f} km² available, {len(d):6d} sampled")
    S = pd.concat(parts, ignore_index=True)
    X, y = S[FEATS].to_numpy(), S.y.to_numpy()
    cells_per_block = C.BLOCK_M // C.RES_CMP
    block = lambda r, c: (r // cells_per_block).astype(np.int64) * 100000 + (c // cells_per_block)
    groups = block(S.r.to_numpy(), S.c.to_numpy())

    # ---- 5 km spatial cross-validation with nested cut-off tuning
    def inner_oof(Xa, ya, ga, name, n_splits=3):
        p = np.zeros(len(ya))
        for tr, te in GroupKFold(n_splits=n_splits).split(Xa, ya, ga):
            p[te] = make_models()[name].fit(Xa[tr], ya[tr]).predict_proba(Xa[te])[:, 1]
        return p

    folds = list(GroupKFold(n_splits=5).split(X, y, groups))
    fold_of_block = {}
    for f, (_, te) in enumerate(folds):
        fold_of_block.update({g: f for g in np.unique(groups[te])})
    names = list(make_models())
    oof = {n: np.zeros(len(y)) for n in names}
    pred_fold = {n: np.zeros(len(y), int) for n in names}
    fold_cuts = {n: [] for n in names}
    fold_models = []
    for tr, te in folds:
        fm = {}
        for n in names:
            cut = break_even(inner_oof(X[tr], y[tr], groups[tr], n), y[tr])     # picked on this fold's training data only
            fm[n] = make_models()[n].fit(X[tr], y[tr])
            oof[n][te] = fm[n].predict_proba(X[te])[:, 1]
            pred_fold[n][te] = (oof[n][te] >= cut).astype(int)
            fold_cuts[n].append(cut)
        fold_models.append(fm)
    full = {n: make_models()[n].fit(X, y) for n in names}
    final_cut = {n: break_even(oof[n], y) for n in names}       # fitted on all training data (out-of-fold scores); used on the map
    global_cut = final_cut                                      # the same number, but scoring it on these data is optimistic

    rows = []
    def add(model, cutoff_type, cutoff, pred, prob=None, note=""):
        rows.append(dict(model=model, cutoff_type=cutoff_type, cutoff=cutoff, **metrics(y, pred, prob), note=note))
    add(RULE, "as it stands", None, rule(X), note=f"HH drop <= {C.DARK_DROP:g} dB and HH <= {C.DARK_DB:g} dB")
    for n in names:
        add(n, "default cut-off (0.5)", 0.5, (oof[n] >= 0.5).astype(int), oof[n])
        add(n, "fold-tuned cut-off (nested)", float(np.mean(fold_cuts[n])), pred_fold[n], oof[n],
            note="Cut-off picked inside each fold on its training data, then applied to the held-out fold; the value shown is the mean of the 5.")
        add(n, "precision-recall break-even point on cross-validated predictions", global_cut[n], (oof[n] >= global_cut[n]).astype(int), oof[n],
            note="Precision, recall and F1 are equal here by definition: the cut-off is placed where they meet, on the same "
                 "predictions it is scored on. It is not a tuned threshold tested on unseen data.")
    for r_ in rows:
        r_["meets_gap_target"] = bool(r_["max_gap_precision_recall_f1"] <= TARGET_GAP)
        r_["meets_accuracy_target"] = bool(r_["accuracy"] >= TARGET_ACC)
        m = S.kind.str.startswith
        pr = rule(X) if r_["model"] == RULE else (pred_fold[r_["model"]] if r_["cutoff_type"].startswith("fold-tuned")
                                                 else (oof[r_["model"]] >= r_["cutoff"]).astype(int))
        for kshort, kname in (("a_high_ground", "negative (a)"), ("b_permanent_water", "negative (b)"), ("c_no_flood_pair", "negative (c)")):
            r_[f"false_alarm_{kshort}"] = float(pr[m(kname).to_numpy()].mean())

    # ---- the rule: what cut-offs would bring it to break-even?
    be = []
    for drop in np.round(np.arange(-6.0, -0.9, 0.1), 2):
        for level in np.round(np.arange(-20.0, -9.9, 0.25), 2):
            mt = metrics(y, rule(X, drop, level))
            be.append(dict(hh_drop_db=drop, hh_level_db=level, **{k: mt[k] for k in ("precision", "recall", "f1", "accuracy", "false_alarm_rate")}))
    bdf = pd.DataFrame(be)
    bdf["gap"] = (bdf.precision - bdf.recall).abs()
    near = bdf[bdf.gap <= 0.005].sort_values("f1", ascending=False)
    keep_level = bdf[bdf.hh_level_db == C.DARK_DB].sort_values("gap").head(1)
    keep_drop = bdf[bdf.hh_drop_db == C.DARK_DROP].sort_values("gap").head(1)
    rule_be = pd.concat([near.head(5).assign(which="best F1 with precision and recall within 0.005"),
                         keep_level.assign(which=f"HH level kept at {C.DARK_DB:g} dB, drop varied"),
                         keep_drop.assign(which=f"HH drop kept at {C.DARK_DROP:g} dB, level varied")])
    rule_be.round(4).to_csv(C.OUT / "flood_rule_break_even.csv", index=False)

    # ---- independent test on the map: cross-fitted predictions over open low ground on the flood pass
    dom = okF & low_open & ~june             # June water is removed from the flood map, so leave it out here too
    rr, cc = np.nonzero(dom)
    Xd = F[rr, cc]
    fold_d = np.array([fold_of_block.get(g, -1) for g in block(rr, cc)])
    prob_map = {}
    for n in names:
        p = np.zeros(len(rr))
        for f in np.unique(fold_d):
            m = fold_d == f
            mdl = full[n] if f < 0 else fold_models[f][n]       # blocks never used in training: the full model
            p[m] = mdl.predict_proba(Xd[m])[:, 1]
        prob_map[n] = p
    upz = ["-"] + [u["name"] for u in json.loads((A / "upazila_index.json").read_text())]
    grp = np.array([0] + [1 if nm in REPORTED else 2 for nm in upz[1:]])[uid]
    sites = pd.read_csv(C.LABELS)
    sites = sites[(sites["set"] == "test") & ~sites.place.isin(SKIP_TEST_PLACES)]
    trf = Transformer.from_crs(4326, crs, always_xy=True)
    P = int(np.ceil(500 / C.RES_CMP))
    yy, xx = np.mgrid[-P:P + 1, -P:P + 1]
    disc = np.hypot(yy, xx) * C.RES_CMP <= 500
    near_pts = {1: np.zeros(dom.shape, bool), 0: np.zeros(dom.shape, bool)}
    for _, s in sites.iterrows():
        x, yv = trf.transform(s.lon, s.lat)
        c, r = int((x - t30.c) / C.RES_CMP), int((t30.f - yv) / C.RES_CMP)
        near_pts[int(s.label)][r - P:r + P + 1, c - P:c + P + 1] |= disc
    km2 = C.RES_CMP ** 2 / 1e6
    flag_maps = {}
    def independent(flag_vec):
        f = np.zeros(dom.shape, bool)
        f[rr, cc] = flag_vec
        share = lambda m: float(100 * (f & m).sum() / max(m.sum(), 1))
        d = dict(flagged_km2=float(f.sum() * km2),
                 test_flagged_pct_near_flooded_points=share(dom & near_pts[1]), test_flagged_pct_near_dry_points=share(dom & near_pts[0]),
                 test_cropland_flagged_pct_reported_upazilas=share(dom & crop40 & (grp == 1)),
                 test_cropland_flagged_pct_other_upazilas=share(dom & crop40 & (grp == 2)))
        d["test_ratio_flooded_to_dry_points"] = d["test_flagged_pct_near_flooded_points"] / max(d["test_flagged_pct_near_dry_points"], 1e-9)
        d["test_ratio_reported_to_other_upazilas"] = d["test_cropland_flagged_pct_reported_upazilas"] / max(d["test_cropland_flagged_pct_other_upazilas"], 1e-9)
        return d, f
    for r_ in rows:
        if r_["model"] == RULE:
            d, flag_maps[(RULE, "rule")] = independent(rule(Xd) == 1)
        elif r_["cutoff_type"].startswith("default"):
            d, flag_maps[(r_["model"], "default")] = independent(prob_map[r_["model"]] >= 0.5)
        else:                                   # both tuned rows use the final cut-off, the one that would go on the map
            d, flag_maps[(r_["model"], "tuned")] = independent(prob_map[r_["model"]] >= final_cut[r_["model"]])
            d["map_cutoff_used"] = final_cut[r_["model"]]
        r_.update(d)
    res = pd.DataFrame(rows)
    res.round(4).to_csv(C.OUT / "flood_model_comparison.csv", index=False)

    # ---------------------------------------------------------------- explainable AI
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap
    labels = [FEAT_LABELS[f] for f in FEATS]
    shap_rows, explainers = [], {}
    for n in ("lightgbm", "random_forest"):
        pick = rng.choice(len(y), N_SHAP[n], replace=False)
        explainers[n] = shap.TreeExplainer(full[n])
        sv = explainers[n].shap_values(X[pick], check_additivity=False)
        sv = np.asarray(sv[1] if isinstance(sv, list) else sv)
        if sv.ndim == 3:
            sv = sv[..., 1]
        direction = [float(np.corrcoef(X[pick][:, j], sv[:, j])[0, 1]) for j in range(len(FEATS))]
        for f, lab_, v, d in zip(FEATS, labels, np.abs(sv).mean(0), direction):
            shap_rows.append(dict(model=n, feature=f, label=lab_, mean_abs_shap=float(v), cells=N_SHAP[n],
                                  higher_value_means="more likely flood" if d > 0 else "less likely flood",
                                  unit="log-odds" if n == "lightgbm" else "probability"))
        order = np.argsort(np.abs(sv).mean(0))
        fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150)
        ax.barh(np.array(labels)[order], np.abs(sv).mean(0)[order], color="#1f6fb2")
        ax.set_xlabel(f"mean |SHAP| ({'log-odds' if n == 'lightgbm' else 'probability'})")
        ax.set_title(f"What drives the {MODEL_LABELS[n]} flood model", fontsize=10)
        fig.tight_layout(); fig.savefig(C.OUT / "xai" / f"flood_models_shap_bar_{n}.png"); plt.close(fig)
        shap.summary_plot(sv, X[pick], feature_names=labels, show=False, plot_size=(8, 4.2))
        plt.tight_layout(); plt.savefig(C.OUT / "xai" / f"flood_models_shap_beeswarm_{n}.png", dpi=150); plt.close()
    shap_df = pd.DataFrame(shap_rows).sort_values(["model", "mean_abs_shap"], ascending=[True, False])
    shap_df.round(5).to_csv(C.OUT / "flood_shap_importance.csv", index=False)
    lr = full["logistic_regression"]
    coef = pd.DataFrame(dict(feature=FEATS, label=labels, standardised_coefficient=lr[-1].coef_[0]))
    coef = coef.sort_values("standardised_coefficient", key=np.abs, ascending=False)
    coef.round(4).to_csv(C.OUT / "flood_logistic_coefficients.csv", index=False)

    # two waterfall examples (LightGBM): one every model agrees on, one false alarm
    examples = []
    tuned_all = np.all([flag_maps[(n, "tuned")] for n in names], axis=0) & flag_maps[(RULE, "rule")]
    cand_a = tuned_all & near_pts[1]
    clf_only = np.any([flag_maps[(n, "tuned")] for n in names], axis=0) & ~flag_maps[(RULE, "rule")] & near_pts[0]
    pm = np.full(dom.shape, np.nan)
    pm[rr, cc] = prob_map["lightgbm"]
    inv = Transformer.from_crs(crs, 4326, always_xy=True)
    for key, cand, title in (("agreed_flood", cand_a, "Flooded cell near a reported-flooded test point, flagged by every model"),
                             ("false_alarm", clf_only & flag_maps[("lightgbm", "tuned")], "Cell near a no-report test point: flagged by LightGBM, not by the rule")):
        if not cand.any():
            examples.append(dict(key=key, title=title, found=False))
            continue
        r_, c_ = np.unravel_index(np.nanargmax(np.where(cand, pm, np.nan)), cand.shape)
        x = F[r_, c_][None, :]
        ev = explainers["lightgbm"](x)
        plt.figure()
        shap.plots.waterfall(shap.Explanation(values=ev.values[0], base_values=float(np.ravel(ev.base_values)[0]), data=x[0], feature_names=labels), show=False)
        plt.title(title, fontsize=9); plt.tight_layout()
        plt.savefig(C.OUT / "xai" / f"flood_models_waterfall_{key}.png", dpi=150, bbox_inches="tight"); plt.close()
        lon, lat = inv.transform(t30.c + (c_ + 0.5) * C.RES_CMP, t30.f - (r_ + 0.5) * C.RES_CMP)
        contrib = sorted(zip(labels, ev.values[0].tolist(), x[0].tolist()), key=lambda t: -abs(t[1]))
        examples.append(dict(key=key, title=title, found=True, lon=round(lon, 5), lat=round(lat, 5), upazila=upz[uid[r_, c_]],
                             features={f: round(float(v), 2) for f, v in zip(FEATS, x[0])},
                             probability={n: round(float(full[n].predict_proba(x)[0, 1]), 4) for n in names},
                             rule_flags=bool(rule(x)[0]), lightgbm_contributions_log_odds=[dict(feature=a, shap=round(b, 3), value=round(v, 2)) for a, b, v in contrib],
                             image=f"flood_models_waterfall_{key}.png"))

    # ---------------------------------------------------------------- summary and JSON
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 44)
    show = ["model", "cutoff_type", "cutoff", "precision", "recall", "f1", "accuracy", "balanced_accuracy", "false_alarm_rate", "roc_auc",
            "max_gap_precision_recall_f1", "meets_gap_target", "meets_accuracy_target"]
    print("\n5 km spatial cross-validation, pooled over held-out folds:\n" + res[show].round(4).to_string(index=False))
    print("\nconfusion matrices (tp, fp, fn, tn) and class counts:\n" + res[["model", "cutoff_type", "tp", "fp", "fn", "tn", "positives", "negatives"]].to_string(index=False))
    print("\nfold-wise cut-offs:", {n: [round(c, 4) for c in v] for n, v in fold_cuts.items()}, "\nfinal cut-offs (all training data):", {n: round(v, 4) for n, v in final_cut.items()})
    print("\nfalse alarms by negative set:\n" + res[["model", "cutoff_type", "false_alarm_a_high_ground", "false_alarm_b_permanent_water", "false_alarm_c_no_flood_pair"]].round(4).to_string(index=False))
    print("\nthe rule at break-even:\n" + rule_be.round(4).to_string(index=False))
    ind = ["model", "cutoff_type", "flagged_km2", "test_flagged_pct_near_flooded_points", "test_flagged_pct_near_dry_points", "test_ratio_flooded_to_dry_points",
           "test_cropland_flagged_pct_reported_upazilas", "test_cropland_flagged_pct_other_upazilas", "test_ratio_reported_to_other_upazilas"]
    print("\nindependent tests (tuned rows use the final cut-off):\n" + res[ind].round(4).to_string(index=False))
    print("\nSHAP:\n" + shap_df[["model", "label", "mean_abs_shap", "higher_value_means"]].round(4).to_string(index=False))
    print("\nlogistic regression, standardised coefficients:\n" + coef.round(4).to_string(index=False))
    for e in examples:
        print("\nexample:", json.dumps({k: v for k, v in e.items() if k != "lightgbm_contributions_log_odds"}), "\n   contributions:", e.get("lightgbm_contributions_log_odds"))
    n_f, n_d = int((sites.label == 1).sum()), int((sites.label == 0).sum())
    print(f"\ntest points used: {n_f} flooded, {n_d} dry (left out: {', '.join(SKIP_TEST_PLACES)})")

    rec = lambda d: json.loads(d.round(4).to_json(orient="records"))
    default_rows = res[res.cutoff_type.isin(["as it stands", "default cut-off (0.5)"])]
    tuned_rows = res[res.cutoff_type.isin(["as it stands", "fold-tuned cut-off (nested)"])]
    break_even_rows = res[res.cutoff_type == "precision-recall break-even point on cross-validated predictions"]
    payload = dict(
        task="Classify open flood on 12 Jul 2026 from NISAR L-band (pair A), radar features only",
        features=[dict(name=f, label=FEAT_LABELS[f]) for f in FEATS], validation="5 km spatial cross-validation, pooled over held-out folds",
        model_labels=MODEL_LABELS,
        cutoffs=dict(default="probability 0.5",
                     tuned="precision-recall break-even, picked inside each fold on that fold's training data (nested), then applied to the held-out fold",
                     break_even="the point where precision equals recall on the cross-validated predictions; the three scores are equal "
                                "there by definition, and it is not a threshold tested on unseen data",
                     final_for_map={n: round(v, 4) for n, v in final_cut.items()},
                     fold_wise={n: [round(c, 4) for c in v] for n, v in fold_cuts.items()}),
        targets=dict(max_gap_precision_recall_f1=TARGET_GAP, min_accuracy=TARGET_ACC),
        train=dict(positives="C-band (DSWx-S1) new open water on 16 Jul, not water on any June date, non-tree, low ground",
                   negatives=["non-tree ground on HAND 8-40 m with slope under 5 degrees",
                              "open water on every June date (permanent water)",
                              "low non-tree ground seen through the no-flood pair 18 Jun to 30 Jun"],
                   samples={k: int(v) for k, v in S.kind.value_counts().items()}),
        test=dict(description="Report-based, never used for training or tuning: share of open low ground flagged within 500 m of test "
                              "points in unions reported submerged against points with no flood report, and share of "
                              "cropland flagged in upazilas reported badly flooded against the others",
                  flooded_points=n_f, dry_points=n_d, left_out=SKIP_TEST_PLACES, reported_upazilas=REPORTED),
        models=rec(default_rows), tuned=rec(tuned_rows), break_even=rec(break_even_rows), all_results=rec(res),
        rule_break_even=rec(rule_be),
        shap=rec(shap_df), logistic_coefficients=rec(coef), examples=examples,
        feature_importance=[dict(feature=f, **{n: round(float(v), 3) for n, v in ((m_, full[m_].feature_importances_[i] / full[m_].feature_importances_.sum()) for m_ in ("random_forest", "lightgbm"))})
                            for i, f in enumerate(FEATS)],
        pipeline_uses=RULE)
    (C.OUT / "model_comparison.json").write_text(json.dumps(payload, indent=1))
    if C.WEB_DATA.parent.exists():
        C.WEB_DATA.mkdir(parents=True, exist_ok=True)
        (C.WEB_DATA / "model_comparison.json").write_text(json.dumps(payload, indent=1))
        print(f"wrote {C.WEB_DATA / 'model_comparison.json'}")
    print(f"({time.time() - t_start:.0f} s)")


if __name__ == "__main__":
    main()
