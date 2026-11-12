"""Step 11: flood risk map (susceptibility, not a forecast).

For every 30 m land cell inside the reported district: how likely is it to flood in rain like
July 2026? The model learns, from terrain alone, where the 12 July open flood (labels 1 and 2 of
work/labels_30m.tif) was. It is trained on ONE flood, and only on open (non-tree) land where the
flood map is valid, then applied to all land, tree-covered or not.

Features (terrain only; no land cover, radar or rainfall):
  hand, hand_min90     height above the nearest river, and its minimum within 90 m
  elev, elev_min90     elevation, and its minimum within 90 m
  slope                degrees
  relief_1km           elevation minus the mean elevation within 1 km
  dist_june_water      distance to water mapped on any June date (rivers, ponds, coast)
  dist_coast           distance to the open sea or wide estuary
The DEM is a SURFACE model: canopy makes groves look higher than the ground. The 90 m minima are
closer to ground level.

Models: logistic regression (standardised), Random Forest, LightGBM. Validation: 5 km spatial
cross-validation, leave-one-upazila-out, the 19 July pass (same event), and the report-based test points.

Writes work/flood_risk_30m.tif                 probability 0-1
       outputs/flood_risk_classes_30m.tif      1 low, 2 medium, 3 high, 4 very high, 255 no data
       outputs/flood_risk_*.csv, outputs/xai/  validation tables, SHAP ranking and plots
       outputs/risk.json and, for the app, web/public/data/flood_risk.png, flood_risk_bounds.json, risk.json

    python pipeline/11_flood_risk.py
"""
import importlib
import time
import warnings

import numpy as np
import pandas as pd
from pyproj import Transformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import config as C
import risk_common as R
from common import ensure_dirs, read_full, write_full

warnings.filterwarnings("ignore", category=UserWarning)
FEATS = ["hand", "hand_min90", "elev", "elev_min90", "slope", "relief_1km", "dist_june_water", "dist_coast"]
FEAT_LABELS = {"hand": "Height above nearest river (HAND)", "hand_min90": "Lowest HAND within 90 m", "elev": "Elevation",
               "elev_min90": "Lowest elevation within 90 m", "slope": "Slope", "relief_1km": "Height above the 1 km surroundings",
               "dist_june_water": "Distance to June water", "dist_coast": "Distance to the coast"}
N_TRAIN = 300_000
GROUND_RADIUS_M = 300         # under trees, elevation and HAND come from the open land within this distance
CANOPY_OK = (0.5, 1.5)        # tree-covered land must score within this multiple of open land at the same ground HAND
CANOPY_BANDS = ((0, 1), (1, 2), (2, 3.5), (3.5, 5))
N_SHAP = 5000
N_SHAP_RF = 1000              # TreeSHAP on a deep Random Forest is slow, so fewer cells
MAX_ECE = 0.03                # "reasonably calibrated": mean gap between predicted and observed share
SHARE_MEDIUM, SHARE_HIGH, SHARE_VERY_HIGH = 0.10, 1 / 3, 1 / 2      # observed flood share each class must reach
SKIP_TEST_PLACES = ["Noapara"]
COLOURS = {1: (255, 255, 204, 90), 2: (254, 204, 92, 165), 3: (253, 141, 60, 205), 4: (189, 0, 38, 225)}


def make_models():
    import lightgbm as lgb
    return {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=50, max_features="sqrt",
                                                n_jobs=-1, random_state=C.RANDOM_SEED),
        "lightgbm": lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=200,
                                       subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                       random_state=C.RANDOM_SEED, verbose=-1),
    }


def terrain_features(june, major, tree):
    # Under tree cover the surface model shows the canopy, not the ground: use the open land within 300 m instead.
    z, hand = R.ground_estimate(R.dem_30m(), tree, GROUND_RADIUS_M), R.ground_estimate(R.hand_30m(), tree, GROUND_RADIUS_M)
    f = dict(hand=hand, hand_min90=R.nanmin_filter(hand, 7), elev=z, elev_min90=R.nanmin_filter(z, 7),
             slope=R.slope_deg(z), relief_1km=z - R.nanmean_filter(z, 67),
             dist_june_water=R.distance_m(june), dist_coast=R.distance_m(R.sea_mask(major)))
    return np.stack([f[k] for k in FEATS], axis=-1).astype("float32")


def auc(y, p):
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan")


def main():
    t_start = time.time()
    ensure_dirs()
    (C.OUT / "xai").mkdir(exist_ok=True)
    t30, w, h, crs, _ = R.grid30()
    km2 = C.RES_CMP ** 2 / 1e6
    rng = np.random.default_rng(C.RANDOM_SEED)

    uid = read_full(R.A / "upazila_id_30m.tif")
    lab = read_full(C.WORK / "labels_30m.tif")
    jw = read_full(R.A / "june_water_30m.tif")
    june = (jw >= 1) & (jw != 255)
    major, tree_share, excl = R.worldcover_30m()
    tree = tree_share >= 0.5
    X_all = terrain_features(june, major, tree)
    names, ids = R.upazila_names(), R.upazila_ids()

    land = (uid > 0) & ~june & ~excl & np.isfinite(X_all).all(-1)       # every cell that gets a risk score
    train_dom = land & ~tree & (lab != 255)                             # open land with a valid flood map
    flooded = np.isin(lab, [1, 2])
    print(f"land inside the district: {land.sum() * km2:.0f} km² (tree-covered {(land & tree).sum() * km2:.0f}); "
          f"training domain (open land with pair A): {train_dom.sum() * km2:.0f} km², "
          f"of which flooded on 12 Jul {(train_dom & flooded).sum() * km2:.1f} km² ({100 * flooded[train_dom].mean():.1f}%)")

    rr, cc = np.nonzero(train_dom)
    keep, cap = R.sample_even(rr, cc, N_TRAIN, rng)
    rr, cc = rr[keep], cc[keep]
    X, y = X_all[rr, cc], flooded[rr, cc].astype(int)
    groups = R.block_ids(rr, cc)
    print(f"training sample: {len(y):,} cells from {len(np.unique(groups))} blocks of 5 km (at most {cap:,} per block), "
          f"{100 * y.mean():.1f}% flooded")

    # ---------------------------------------------------------------- 5 km spatial cross-validation
    folds = list(GroupKFold(n_splits=5).split(X, y, groups))
    oof = {n: np.zeros(len(y)) for n in make_models()}
    fold_models = []
    for tr, te in folds:
        fm = {}
        for n, m in make_models().items():
            fm[n] = m.fit(X[tr], y[tr])
            oof[n][te] = m.predict_proba(X[te])[:, 1]
        fold_models.append(fm)
    val, cal = [], {}
    for n, p in oof.items():
        cal[n], ece = R.calibration_table(p, y)
        val.append(dict(model=n, cv_auc=auc(y, p), cv_brier=float(brier_score_loss(y, p)), cv_calibration_gap=ece))
    base_brier = float(brier_score_loss(y, np.full(len(y), y.mean())))

    # ---------------------------------------------------------------- leave one upazila out
    u_s = uid[rr, cc]
    flood_km2 = np.bincount(uid[train_dom & flooded], minlength=len(names)) * km2
    loo_ids = [int(i) for i in np.argsort(-flood_km2) if i > 0][:6]
    loo = []
    for i in loo_ids:
        te = u_s == i
        row = dict(upazila=names[i], flooded_km2=round(float(flood_km2[i]), 1), test_cells=int(te.sum()))
        for n, m in make_models().items():
            row[n] = round(auc(y[te], m.fit(X[~te], y[~te]).predict_proba(X[te])[:, 1]), 3)
        loo.append(row)
    for v in val:
        v["leave_one_upazila_out_auc_mean"] = float(np.mean([r[v["model"]] for r in loo]))
        v["leave_one_upazila_out_auc_min"] = float(np.min([r[v["model"]] for r in loo]))

    # ---------------------------------------------------------------- the 19 July pass (the SAME event, a week later)
    agg = importlib.import_module("06_compare").aggregate
    _, open_b, cov_b = agg(C.WORK / f"flood_{C.DRAIN_PAIR}.tif", h, w)
    mb = cov_b[rr, cc]
    yb = (open_b & cov_b)[rr, cc].astype(int)
    for v in val:
        v["auc_vs_19jul_flood_same_event"] = auc(yb[mb], oof[v["model"]][mb])

    # ---------------------------------------------------------------- choose: best CV AUC among the calibrated ones
    vdf = pd.DataFrame(val)
    ok = vdf[vdf.cv_calibration_gap <= MAX_ECE]
    best = (ok if len(ok) else vdf.sort_values("cv_calibration_gap").head(1)).sort_values("cv_auc", ascending=False).iloc[0].model
    full = {n: m.fit(X, y) for n, m in make_models().items()}
    model = full[best]

    # ---------------------------------------------------------------- report-based test points (cross-fitted scores)
    fold_of_block = {}
    for f, (_, te) in enumerate(folds):
        fold_of_block.update({g: f for g in np.unique(groups[te])})
    dr, dc = np.nonzero(train_dom)
    fold_d = np.array([fold_of_block.get(g, -1) for g in R.block_ids(dr, dc)])
    sites = pd.read_csv(C.LABELS)
    sites = sites[(sites["set"] == "test") & ~sites.place.isin(SKIP_TEST_PLACES)]
    trf = Transformer.from_crs(4326, crs, always_xy=True)
    P = int(np.ceil(500 / C.RES_CMP))
    yy, xx = np.mgrid[-P:P + 1, -P:P + 1]
    disc = np.hypot(yy, xx) * C.RES_CMP <= 500
    near = {1: np.zeros((h, w), bool), 0: np.zeros((h, w), bool)}
    for _, s in sites.iterrows():
        x, yv = trf.transform(s.lon, s.lat)
        c, r = int((x - t30.c) / C.RES_CMP), int((t30.f - yv) / C.RES_CMP)
        near[int(s.label)][r - P:r + P + 1, c - P:c + P + 1] |= disc
    for v in val:
        p = np.zeros(len(dr))
        for f in np.unique(fold_d):
            m = fold_d == f
            mdl = full[v["model"]] if f < 0 else fold_models[f][v["model"]]
            p[m] = mdl.predict_proba(X_all[dr[m], dc[m]])[:, 1]
        cf = np.full((h, w), np.nan, "float32")
        cf[dr, dc] = p
        v["mean_risk_near_flooded_test_points"] = float(np.nanmean(cf[near[1] & train_dom]))
        v["mean_risk_near_dry_test_points"] = float(np.nanmean(cf[near[0] & train_dom]))
    vdf = pd.DataFrame(val).round(4)
    vdf["chosen"] = vdf.model == best
    vdf.to_csv(C.OUT / "flood_risk_validation.csv", index=False)
    pd.DataFrame(loo).to_csv(C.OUT / "flood_risk_leave_one_upazila_out.csv", index=False)
    pd.concat([pd.DataFrame(c).assign(model=n) for n, c in cal.items()]).to_csv(C.OUT / "flood_risk_calibration.csv", index=False)

    # ---------------------------------------------------------------- classes from the calibration of the chosen model
    iso = IsotonicRegression(out_of_bounds="clip").fit(oof[best], y)
    grid = np.linspace(0, 1, 2001)
    obs = iso.predict(grid)
    def cut(share):
        i = np.nonzero(obs >= share)[0]
        return float(grid[i[0]]) if len(i) else None
    cuts = dict(medium=cut(SHARE_MEDIUM), high=cut(SHARE_HIGH), very_high=cut(SHARE_VERY_HIGH))
    edges = [0.0] + [cuts[k] if cuts[k] is not None else 1.01 for k in ("medium", "high", "very_high")] + [1.01]
    class_obs = []
    for k in range(4):
        m = (oof[best] >= edges[k]) & (oof[best] < edges[k + 1])
        class_obs.append(dict(risk_class=R.CLASS_NAMES[k + 1], score_from=round(edges[k], 3), score_to=round(min(edges[k + 1], 1.0), 3),
                              cv_cells=int(m.sum()), observed_flood_share=round(float(y[m].mean()), 3) if m.any() else None))

    # ---------------------------------------------------------------- predict all land, tree-covered or not
    lr_, lc_ = np.nonzero(land)
    prob = np.full((h, w), np.nan, "float32")
    prob[lr_, lc_] = model.predict_proba(X_all[lr_, lc_])[:, 1]
    cls = np.full((h, w), 255, "uint8")
    cls[land] = 1 + np.digitize(prob[land], edges[1:4])

    # canopy check: at the same height above the river, do tree-covered cells score like open ones?
    canopy = []
    for feat in ("hand",):                      # "hand" is now the ground HAND (open land within 300 m under trees)
        v = X_all[..., FEATS.index(feat)]
        for lo, hi in CANOPY_BANDS:
            b = land & (v >= lo) & (v < hi)
            o, t = b & ~tree, b & tree
            canopy.append(dict(binned_by=feat, band_m=f"{lo}-{hi}", open_km2=round(o.sum() * km2, 1), tree_km2=round(t.sum() * km2, 1),
                               open_mean_risk=round(float(prob[o].mean()), 3), tree_mean_risk=round(float(prob[t].mean()), 3),
                               open_high_or_very_high_pct=round(100 * float((cls[o] >= 3).mean()), 1),
                               tree_high_or_very_high_pct=round(100 * float((cls[t] >= 3).mean()), 1)))
    cdf = pd.DataFrame(canopy)
    cdf["tree_to_open_ratio"] = (cdf.tree_mean_risk / cdf.open_mean_risk).round(2)
    cdf["within_limits"] = cdf.tree_to_open_ratio.between(*CANOPY_OK)
    cdf.to_csv(C.OUT / "flood_risk_canopy_check.csv", index=False)
    canopy_ok = bool(cdf.within_limits.all())
    scope = "all land" if canopy_ok else "open land"
    if not canopy_ok:
        # The check failed: tree-covered land is not scored. The map and its people figures cover open land only.
        prob[tree] = np.nan
        cls[tree] = 255
        land = land & ~tree
    write_full(C.WORK / "flood_risk_30m.tif", prob, res=C.RES_CMP, nodata=np.nan)
    write_full(C.OUT / "flood_risk_classes_30m.tif", cls, res=C.RES_CMP, nodata=255)

    # ---------------------------------------------------------------- explainable AI
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap
    shap_rank = {}
    for n in ("lightgbm", "random_forest"):
        k = N_SHAP if n == "lightgbm" else N_SHAP_RF
        pick = rng.choice(len(y), k, replace=False)
        sv = shap.TreeExplainer(full[n]).shap_values(X[pick], check_additivity=False)
        sv = np.asarray(sv[1] if isinstance(sv, list) else sv)
        if sv.ndim == 3:
            sv = sv[..., 1]
        direction = [float(np.corrcoef(X[pick][:, j], sv[:, j])[0, 1]) for j in range(len(FEATS))]
        shap_rank[n] = pd.DataFrame(dict(feature=FEATS, label=[FEAT_LABELS[f] for f in FEATS], mean_abs_shap=np.abs(sv).mean(0),
                                         higher_value_means=["more risk" if d > 0 else "less risk" for d in direction],
                                         cells=k)).sort_values("mean_abs_shap", ascending=False)
        if n == best or (best == "logistic_regression" and n == "lightgbm"):
            sr = shap_rank[n]
            fig, ax = plt.subplots(figsize=(7, 3.8), dpi=150)
            ax.barh(sr.label[::-1], sr.mean_abs_shap[::-1], color="#1f6fb2")
            ax.set_xlabel("mean |SHAP| (" + ("log-odds" if n == "lightgbm" else "probability") + ")")
            ax.set_title(f"What drives flood risk ({n})", fontsize=10)
            fig.tight_layout(); fig.savefig(C.OUT / "xai" / "flood_shap_bar.png"); plt.close(fig)
            shap.summary_plot(sv, X[pick], feature_names=[FEAT_LABELS[f] for f in FEATS], show=False, plot_size=(8, 4.5))
            plt.tight_layout(); plt.savefig(C.OUT / "xai" / "flood_shap_beeswarm.png", dpi=150); plt.close()
            shap_model = n
    pd.concat([d.assign(model=n) for n, d in shap_rank.items()]).round(5).to_csv(C.OUT / "xai" / "flood_shap_mean_abs.csv", index=False)
    lr = full["logistic_regression"]
    coef = pd.DataFrame(dict(feature=FEATS, standardised_coefficient=lr[-1].coef_[0])).sort_values(
        "standardised_coefficient", key=np.abs, ascending=False).round(3)
    coef.to_csv(C.OUT / "xai" / "flood_logistic_coefficients.csv", index=False)
    top = shap_rank[shap_model].head(3)
    driver = ("Flood risk is driven mostly by " + ", then ".join(
        f"{r.label.lower()} ({'higher' if r.higher_value_means == 'more risk' else 'lower'} means more risk)" for r in top.itertuples()) + ".")

    # ---------------------------------------------------------------- per upazila
    pop = R.population_30m()
    rows = []
    for i in range(1, len(names)):
        u = (uid == i) & land
        row = dict(id=ids[i], name=names[i], land_km2=round(u.sum() * km2, 1), people_total=int(round(pop[u].sum())))
        for cname, cval in (("high", 3), ("very_high", 4)):
            for lname, lm in (("open", ~tree), ("tree", tree)):
                m = u & (cls == cval) & lm
                row[f"{cname}_{lname}_km2"] = round(m.sum() * km2, 2)
                row[f"{cname}_{lname}_people"] = int(round(pop[m].sum()))
        hv = u & (cls >= 3)
        row.update(high_or_very_high_km2=round(hv.sum() * km2, 1), high_or_very_high_people=int(round(pop[hv].sum())),
                   high_or_very_high_people_pct=round(100 * pop[hv].sum() / max(pop[u].sum(), 1), 1))
        rows.append(row)
    udf = pd.DataFrame(rows).sort_values("high_or_very_high_people", ascending=False)
    udf.to_csv(C.OUT / "flood_risk_upazilas.csv", index=False)

    # ---------------------------------------------------------------- app files
    C.WEB_DATA.mkdir(parents=True, exist_ok=True) if C.WEB_DATA.parent.exists() else None
    web = C.WEB_DATA if C.WEB_DATA.exists() else C.OUT
    pw, ph, kb = R.write_overlay_png(cls, COLOURS, web / "flood_risk.png", web / "flood_risk_bounds.json")
    class_km2 = {R.CLASS_NAMES[k]: round(float((cls == k).sum() * km2), 1) for k in range(1, 5)}
    R.update_risk_json("flood", dict(
        title="Flood risk (in rain like July 2026)" if canopy_ok else "Flood risk on open land",
        scope=scope, people_figure="for all land" if canopy_ok else "a lower bound: tree-covered land, where most people live, is not scored",
        ground_estimate=f"under tree cover, elevation and HAND are the mean of the open land within {GROUND_RADIUS_M} m",
        meaning="A likelihood map, not a forecast: how likely a 30 m cell is to flood in rain like July 2026, learned from terrain alone.",
        trained_on="ONE flood: the open flood NISAR saw on 12 July 2026 (labels 1 and 2). Open land only; applied to all land.",
        limits=["Trained on a single flood event.", "Susceptibility, not a forecast: no rainfall or river levels go in.",
                "The DEM is a surface model, so tree canopy and buildings look higher than the ground; scores under trees are less certain.",
                "The 19 July check is the same event a week later, not an independent flood."],
        chosen_model=best, features=[dict(name=f, label=FEAT_LABELS[f]) for f in FEATS],
        training=dict(cells=int(len(y)), blocks_5km=int(len(np.unique(groups))), flooded_share=round(float(y.mean()), 4),
                      baseline_brier=round(base_brier, 4)),
        validation=vdf.to_dict("records"), leave_one_upazila_out=loo, calibration=cal[best],
        classes=dict(cutoffs=cuts, target_observed_share=dict(medium=SHARE_MEDIUM, high=round(SHARE_HIGH, 3), very_high=SHARE_VERY_HIGH),
                     observed_in_cross_validation=class_obs, area_km2=class_km2,
                     colours={R.CLASS_NAMES[k]: "#%02x%02x%02x" % v[:3] for k, v in COLOURS.items()}),
        canopy_check=cdf.to_dict("records"),
        shap=dict(model=shap_model, cells=int(shap_rank[shap_model].cells.iloc[0]), sentence=driver,
                  ranking=shap_rank[shap_model][["feature", "label", "mean_abs_shap", "higher_value_means"]].round(4).to_dict("records")),
        logistic_coefficients=coef.to_dict("records"),
        upazilas=udf.to_dict("records"),
        totals=dict(high_or_very_high_km2=round(float(udf.high_or_very_high_km2.sum()), 1),
                    high_or_very_high_people=int(udf.high_or_very_high_people.sum()), people_total=int(udf.people_total.sum())),
        overlay=dict(image="flood_risk.png", bounds="flood_risk_bounds.json", width=pw, height=ph)))

    # ---------------------------------------------------------------- summary
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print("\nvalidation (trained on ONE flood; the 19 July column is the SAME event a week later):")
    print(vdf.T.to_string(header=False))
    print(f"baseline Brier (always predict the flooded share): {base_brier:.4f}")
    print("\nleave one upazila out, AUC:\n" + pd.DataFrame(loo).to_string(index=False))
    print(f"\nchosen model: {best}\ncalibration, 5 km spatial CV:\n" + pd.DataFrame(cal[best]).to_string(index=False))
    print(f"\nclass cut-offs on the risk score: {cuts}\n" + pd.DataFrame(class_obs).to_string(index=False))
    print("class areas (km²):", class_km2)
    print("\ncanopy check (same ground HAND, tree-covered against open):\n" + cdf.to_string(index=False))
    print(f"tree-covered land within {CANOPY_OK[0]}-{CANOPY_OK[1]}x of open land in every band: {canopy_ok} -> the map covers {scope}")
    print(f"\nSHAP ({shap_model}):\n" + shap_rank[shap_model][["label", "mean_abs_shap", "higher_value_means"]].round(4).to_string(index=False))
    print(driver)
    print("\nlogistic regression, standardised coefficients:\n" + coef.to_string(index=False))
    cols = ["name", "high_or_very_high_people", "high_or_very_high_people_pct", "high_or_very_high_km2", "high_open_km2", "high_tree_km2",
            "very_high_open_km2", "very_high_tree_km2", "high_open_people", "high_tree_people", "very_high_open_people", "very_high_tree_people"]
    print("\ntop upazilas by people in high or very high risk:\n" + udf.head(10)[cols].to_string(index=False))
    print(f"\noverlay {pw} x {ph} px, {kb:.0f} KB -> {web / 'flood_risk.png'}")
    print(f"({time.time() - t_start:.0f} s)")


if __name__ == "__main__":
    main()
