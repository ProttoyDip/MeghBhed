"""Step 5 (optional, after step 4 works): Random Forest vs LightGBM vs the baseline.

Needs labels/sites.csv with columns
  lon, lat, label, pairs, source
  label: 1 = flooded under trees, 0 = dry (forest or homestead that stayed dry)
  pairs: which NISAR pairs the label applies to, e.g. "A;B" (empty = all pairs)
  source: link to the news photo / report
  set (optional): "train" or "test". When present, only "train" rows (plus the automatic
       dry examples) are used for cross-validation and the final fit; "test" rows are
       held out and scored at the end into outputs/model_test_reports.csv.

Adds automatic "dry" examples: tree pixels with HAND > AUTO_DRY_HAND_M.
Cross-validation is split by 5 km blocks, so neighbouring pixels never sit in both
train and test. The winner is trained on everything and used to write
  work/flood_ml_<pair>.tif   (same codes as flood_<pair>.tif)
  outputs/model_comparison.csv, outputs/feature_importance.csv

    python pipeline/05_classify.py
"""
import json
import numpy as np
import pandas as pd
from pyproj import Transformer
from rasterio.windows import Window
from scipy.ndimage import uniform_filter
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import GroupKFold

import config as C
from common import ensure_dirs, load_grid, create, tiles, crop, read_win, write_win, pair_arrays, inside_mask
import importlib
clean = importlib.import_module("04_detect").clean

N, A = C.WORK / "nisar", C.WORK / "aux"


def features(hh_b, hv_b, hh_d, hv_d, dhh, dhv, slope, hand):
    f = dict(hh_b=hh_b, hv_b=hv_b, hh_d=hh_d, hv_d=hv_d, dhh=dhh, dhv=dhv,
             ratio_d=hh_d - hv_d, slope=slope, hand=hand)
    x = np.nan_to_num(hh_d)
    m = uniform_filter(x, 5)
    f["tex_hh"] = np.sqrt(np.maximum(uniform_filter(x * x, 5) - m * m, 0))
    return np.stack([f[k] for k in C.FEATURES], axis=-1).astype("float32")


def stack(pair, window):
    return features(*pair_arrays(pair, window), read_win(A / "slope.tif", window),
                    read_win(A / "hand.tif", window)), read_win(A / "worldcover.tif", window)


def sample_sites(df):
    t, w, h, crs = load_grid()
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    rad = max(1, int(round(C.SITE_RADIUS_M / C.RES)))
    rows = []
    for _, s in df.iterrows():
        x, y = tr.transform(s.lon, s.lat)
        col, row = int((x - t.c) / C.RES), int((t.f - y) / C.RES)
        if not (0 <= col < w and 0 <= row < h):
            continue
        pad = rad + 3
        win = Window(col - pad, row - pad, 2 * pad + 1, 2 * pad + 1)
        raw = s.get("pairs", "")
        raw = "" if pd.isna(raw) else str(raw)          # an empty cell is read as NaN: it means all pairs
        pairs = [p.strip() for p in raw.split(";") if p.strip()] or list(C.PAIRS)
        yy, xx = np.mgrid[-pad:pad + 1, -pad:pad + 1]
        disk = (yy ** 2 + xx ** 2) <= rad ** 2
        for p in pairs:
            if p not in C.PAIRS:
                continue
            X, _ = stack(p, win)
            X = X[disk]
            X = X[np.isfinite(X).all(axis=1)]
            for v in X:
                rows.append((*v, int(s.label), p, x, y, "site"))
    return rows


def sample_auto_dry(n):
    rng = np.random.default_rng(C.RANDOM_SEED)
    t, w, h, crs = load_grid()
    rows, tries = [], 0
    while len(rows) < n and tries < 200:
        tries += 1
        c, r = int(rng.integers(0, max(w - 256, 1))), int(rng.integers(0, max(h - 256, 1)))
        win = Window(c, r, 256, 256)
        for p in C.PAIRS:
            if not (N / f"{C.PAIRS[p][1]}_HH.tif").exists():
                continue
            X, wc = stack(p, win)
            hand = X[..., C.FEATURES.index("hand")]
            ok = (wc == C.TREE_CLASS) & (hand > C.AUTO_DRY_HAND_M) & np.isfinite(X).all(axis=-1)
            idx = np.argwhere(ok)
            if len(idx) == 0:
                continue
            idx = idx[rng.choice(len(idx), min(40, len(idx)), replace=False)]
            for i, j in idx:
                rows.append((*X[i, j], 0, p, t.c + (c + j) * C.RES, t.f - (r + i) * C.RES, "auto_dry"))
    return rows[:n]


def scores(model, y, p, **extra):
    return dict(model=model, **extra, precision=precision_score(y, p, zero_division=0),
                recall=recall_score(y, p, zero_division=0), f1=f1_score(y, p, zero_division=0),
                false_alarm_rate=float(((p == 1) & (y == 0)).sum() / max((y == 0).sum(), 1)))


def baseline_pred(X):
    dhh, dhv = X[:, C.FEATURES.index("dhh")], X[:, C.FEATURES.index("dhv")]
    return ((dhh >= C.T_HH) & (dhv <= C.T_HV)).astype(int)


def make_models():
    import lightgbm as lgb
    return {
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced",
                                                n_jobs=-1, random_state=C.RANDOM_SEED),
        "lightgbm": lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                                       class_weight="balanced", random_state=C.RANDOM_SEED, verbose=-1),
    }


def main():
    ensure_dirs()
    if not C.LABELS.exists():
        C.LABELS.parent.mkdir(parents=True, exist_ok=True)
        C.LABELS.write_text("lon,lat,label,pairs,source\n")
        raise SystemExit(f"Created empty {C.LABELS}. Fill it with flooded (1) and dry (0) sites, then re-run.")
    sites = pd.read_csv(C.LABELS)
    if sites.empty:
        raise SystemExit(f"{C.LABELS} has no rows yet.")
    cols = C.FEATURES + ["label", "pair", "x", "y", "kind"]
    test_sites = None
    if "set" in sites.columns:                 # held-out test sites never reach training
        which = sites["set"].astype(str).str.strip().str.lower()
        test_sites, sites = sites[which == "test"], sites[which == "train"]
        print(f"sites.csv has a 'set' column: {len(sites)} train sites, {len(test_sites)} test sites")
    df = pd.DataFrame(sample_sites(sites) + sample_auto_dry(C.AUTO_DRY_N), columns=cols)
    df.to_csv(C.WORK / "training_samples.csv", index=False)
    n_pos = int((df.label == 1).sum())
    print(f"samples: {len(df)}  flooded {n_pos}  dry {len(df) - n_pos}  (from {len(sites)} sites + auto dry)")
    if n_pos < 20 or df.label.nunique() < 2:
        raise SystemExit("Too few flooded samples to train. Add more flooded sites to labels/sites.csv.")

    X, y = df[C.FEATURES].to_numpy(), df.label.to_numpy()
    groups = (np.floor(df.x / C.BLOCK_M).astype(int) * 100000 + np.floor(df.y / C.BLOCK_M).astype(int)).to_numpy()
    k = min(5, len(np.unique(groups)))
    if k < 2:
        raise SystemExit("All samples fall in one 5 km block; spread label sites out more.")
    oof = {name: np.zeros(len(y)) for name in make_models()}
    for tr_i, te_i in GroupKFold(n_splits=k).split(X, y, groups):
        for name, m in make_models().items():
            m.fit(X[tr_i], y[tr_i])
            oof[name][te_i] = m.predict_proba(X[te_i])[:, 1]

    rows = []
    site = (df.kind == "site").to_numpy()   # score on real sites only
    preds = {"baseline_threshold": baseline_pred(X)} | {n: (p >= 0.5).astype(int) for n, p in oof.items()}
    for name, p in preds.items():
        rows.append(scores(name, y[site], p[site]))
    res = pd.DataFrame(rows).round(3)
    res.to_csv(C.OUT / "model_comparison.csv", index=False)
    print("\nspatial cross-validation on label sites:\n" + res.to_string(index=False))

    best = res[res.model != "baseline_threshold"].sort_values("f1", ascending=False).iloc[0].model
    model = make_models()[best].fit(X, y)
    imp = getattr(model, "feature_importances_", None)
    if imp is not None:
        pd.DataFrame({"feature": C.FEATURES, "importance": imp / imp.sum()}).sort_values(
            "importance", ascending=False).round(3).to_csv(C.OUT / "feature_importance.csv", index=False)
    import joblib
    joblib.dump(model, C.WORK / f"model_{best}.joblib")
    (C.WORK / "model.json").write_text(json.dumps({"best": best}))
    print(f"\nbest: {best}  (beats baseline F1: {res.set_index('model').f1[best] > res.set_index('model').f1['baseline_threshold']})")

    # ---- held-out test sites: every model fitted on all train samples, scored on the test rows
    if test_sites is not None and len(test_sites):
        tdf = pd.DataFrame(sample_sites(test_sites), columns=cols)
        if tdf.empty:
            print("no test samples fall on the grid; model_test_reports.csv not written")
        else:
            Xt, yt = tdf[C.FEATURES].to_numpy(), tdf.label.to_numpy()
            fitted = {n: (model if n == best else m.fit(X, y)) for n, m in make_models().items()}
            tp = {"baseline_threshold": baseline_pred(Xt)} | {n: m.predict(Xt).astype(int) for n, m in fitted.items()}
            n1, n0 = int((yt == 1).sum()), int((yt == 0).sum())
            tres = pd.DataFrame([scores(n, yt, p, test_flooded_px=n1, test_dry_px=n0) for n, p in tp.items()]).round(3)
            tres.to_csv(C.OUT / "model_test_reports.csv", index=False)
            print(f"\nheld-out test sites ({len(test_sites)} sites, never used for training):\n" + tres.to_string(index=False))

    # ---- predict maps with the winner
    for pair, (b, d) in C.PAIRS.items():
        base = C.WORK / f"flood_{pair}.tif"
        if not base.exists():
            continue
        out = C.WORK / f"flood_ml_{pair}.tif"
        create(out, dtype="uint8", nodata=255)
        n_ml = n_base = 0
        for inner, padded in tiles(pad=16):
            Xt, wc = stack(pair, padded)
            ok = np.isfinite(Xt).all(axis=-1)
            prob = np.zeros(ok.shape, dtype="float32")
            if ok.any():
                prob[ok] = model.predict_proba(Xt[ok])[:, 1]
            dhh = Xt[..., C.FEATURES.index("dhh")]
            with np.errstate(invalid="ignore"):
                hand = Xt[..., C.FEATURES.index("hand")]
                hidden = clean(ok & (prob >= C.ML_PROB) & (dhh >= C.ML_MIN_DHH) & (wc == C.TREE_CLASS)
                               & inside_mask(padded) & (hand <= C.HAND_MAX_M))
                exc = pair_arrays(pair, padded, with_after=True)[6]
                if exc is not None:
                    with np.errstate(invalid="ignore"):
                        hidden &= exc >= C.T_AFTER
            b0 = read_win(base, padded)
            o = np.where(b0 == 2, 2, 0).astype("uint8")
            o[hidden] = 1
            o[~ok | (b0 == 255)] = 255
            o, b0 = crop(o, inner, padded), crop(b0, inner, padded)
            write_win(out, o, inner)
            n_ml += int((o == 1).sum()); n_base += int((b0 == 1).sum())
        km = C.RES ** 2 / 1e6
        print(f"pair {pair}: classifier {n_ml*km:.1f} km² vs baseline {n_base*km:.1f} km²")
        if n_base and n_ml > 3 * n_base:
            print("   WARNING: classifier flags >3x the baseline. Check feature_importance.csv: if hand or slope"
                  " dominate, add dry sites at low HAND and re-train before using DETECTOR='ml'.")


if __name__ == "__main__":
    main()
