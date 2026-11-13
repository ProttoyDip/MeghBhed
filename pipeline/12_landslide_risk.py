"""Step 12: landslide risk map (susceptibility, not a forecast and not a trained model).

For every 30 m cell with a slope of 5 degrees or more inside the reported district, a susceptibility
class from a WEIGHTED INDEX. No model is trained: NASA's Global Landslide Catalog has too few points
here, and most are located only to within 5-25 km (see docs/METHOD.md).

Index = sum of weight x factor score, each score from 0 to 1:
  slope            0.40   0 at 5 degrees, 1 at 35 degrees or more        steeper ground fails more easily
  relief           0.20   height range within 300 m; 1 at 150 m or more   long, high slopes
  rainfall         0.20   IMERG total 5-18 Jul; 0 at 300 mm, 1 at 700 mm  the trigger in this event
  land cover       0.10   bare 1.0, built-up 0.8, cropland 0.7, other 0.6, tree 0.4   roots hold soil; cut and bare slopes do not
  hill cutting     0.10   1 next to built-up land, 0 at 500 m or more     a stand-in for cut slopes below settlements
Slope gets the most weight because it is the one factor every landslide needs; relief and rainfall
come next; land cover and nearness to buildings adjust within those. The weights are a judgement,
not fitted to data. Elevation and curvature are computed and reported but carry no weight.

Classes are ranks within the district's steep land: very high = top 5%, high = next 15%,
medium = next 30%, low = the rest.

Checks: the Hill Risk radar sites, the catalog points, the areas named in reports, the LHASA
nowcast and NASA's global susceptibility map.

Writes work/landslide_index_30m.tif, outputs/landslide_risk_classes_30m.tif, outputs/landslide_risk_*.csv,
       outputs/xai/landslide_index_contributions.*, outputs/risk.json and, for the app,
       web/public/data/landslide_risk.png, landslide_risk_bounds.json, risk.json

    python pipeline/12_landslide_risk.py
"""
import time
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from rasterio.warp import Resampling
from scipy import ndimage as ndi
from scipy.stats import spearmanr

import config as C
import risk_common as R
from common import ensure_dirs, read_full, warp_window, write_full

warnings.filterwarnings("ignore")
MIN_SLOPE = 5.0
MIN_RELIEF_M = 20.0           # a cell counts as slope only where the ground rises 20 m or more within 300 m
BUILT_SMOOTH_SIGMA = 2        # in built-up cells, slope comes from a lightly smoothed DEM (60 m), so walls are not slopes
WEIGHTS = dict(slope=0.40, relief=0.20, rainfall=0.20, land_cover=0.10, hill_cutting=0.10)
LABELS = dict(slope="Slope", relief="Relief within 300 m", rainfall="Rain, 5-18 July", land_cover="Land cover",
              hill_cutting="Nearness to built-up land")
LC_SCORE = {"bare": 1.0, "built-up": 0.8, "cropland": 0.7, "other": 0.6, "tree": 0.4}
CLASS_TOP_SHARE = {4: 0.05, 3: 0.20, 2: 0.50}          # cumulative share of steep land, from the top
COLOURS = {1: (237, 231, 246, 80), 2: (179, 157, 219, 160), 3: (126, 87, 194, 205), 4: (74, 20, 140, 230)}
CATALOG = C.DATA / "landslide" / "glc_export.csv"       # NASA Global Landslide Catalog export (1988-2017; 38 events in the grid, 2007-2017)
NASA_SUSC = C.DATA / "landslide" / "susceptibility_2023.tif"
MAX_CATALOG_RADIUS_M = 5000
# Places the July 2026 reports named as high landslide risk (BDRCS, 7 Jul; NAWG, 9 and 11 Jul).
# Ward points were geocoded with Nominatim on 12 Nov 2026; they are approximate (no ward boundaries were available).
NAMED_POINTS = {"CCC ward 7 (West Sholashahar)": (91.82429, 22.36687), "CCC ward 8 (Sholokbahar)": (91.83334, 22.36667),
                "CCC ward 9 (North Pahartali)": (91.78228, 22.36252), "CCC ward 14 (Lalkhan Bazar)": (91.81678, 22.35042)}
NAMED_UPAZILAS = ["Banshkhali"]


def scale(a, lo, hi):
    return np.clip((a - lo) / (hi - lo), 0, 1).astype("float32")


def main():
    t_start = time.time()
    ensure_dirs()
    (C.OUT / "xai").mkdir(exist_ok=True)
    t30, w, h, crs, full = R.grid30()
    km2 = C.RES_CMP ** 2 / 1e6
    uid = read_full(R.A / "upazila_id_30m.tif")
    names, ids = R.upazila_names(), R.upazila_ids()
    major, tree_share, _ = R.worldcover_30m()

    # ---------------------------------------------------------------- features
    z = R.dem_30m()
    zf = np.where(np.isfinite(z), z, np.nan)
    built_up = read_built_share() >= 1 / 3
    z_smooth = ndi.gaussian_filter(np.nan_to_num(zf, nan=float(np.nanmedian(zf))), BUILT_SMOOTH_SIGMA)
    slope = np.where(built_up, R.slope_deg(z_smooth), R.slope_deg(z)).astype("float32")
    relief = ndi.maximum_filter(np.nan_to_num(zf, nan=-1e4), 21) - ndi.minimum_filter(np.nan_to_num(zf, nan=1e4), 21)   # within 300 m
    curvature = -ndi.laplace(ndi.gaussian_filter(np.nan_to_num(zf), 1)) / C.RES_CMP ** 2 * 100       # > 0 = convex (ridges, noses)
    rain = warp_window(R.A / "imerg_total_mm.tif", full, res=C.RES_CMP, resampling=Resampling.bilinear)
    group = np.full((h, w), "other", dtype=object)
    group[major == 10] = "tree"
    group[major == 40] = "cropland"
    group[major == 50] = "built-up"
    group[major == 60] = "bare"
    d_built = R.distance_m(built_up)

    steep_before_fix = (uid > 0) & np.isfinite(z) & (R.slope_deg(z) >= MIN_SLOPE) & (major != 80)
    steep = (uid > 0) & np.isfinite(slope) & (slope >= MIN_SLOPE) & (relief >= MIN_RELIEF_M) & (major != 80)
    score = dict(slope=scale(slope, MIN_SLOPE, 35), relief=scale(relief, 0, 150), rainfall=scale(rain, C.RAIN_MM, 700),
                 land_cover=np.vectorize(LC_SCORE.get, otypes=["float32"])(group), hill_cutting=1 - scale(d_built, 0, 500))
    contrib = {k: WEIGHTS[k] * np.nan_to_num(score[k]) for k in WEIGHTS}
    index = np.where(steep, sum(contrib.values()), np.nan).astype("float32")

    vals = index[steep]
    cuts = {c: float(np.quantile(vals, 1 - s)) for c, s in CLASS_TOP_SHARE.items()}
    cls = np.full((h, w), 255, "uint8")
    cls[steep] = 1 + (vals >= cuts[2]).astype("uint8") + (vals >= cuts[3]) + (vals >= cuts[4])
    write_full(C.WORK / "landslide_index_30m.tif", index, res=C.RES_CMP, nodata=np.nan)
    write_full(C.OUT / "landslide_risk_classes_30m.tif", cls, res=C.RES_CMP, nodata=255)
    hi_cls = steep & (cls >= 3)
    base = 100 * hi_cls.sum() / steep.sum()
    print(f"steep land (slope >= {MIN_SLOPE:g} degrees and relief >= {MIN_RELIEF_M:g} m within 300 m) inside the district: {steep.sum() * km2:.0f} km² "
          f"(was {steep_before_fix.sum() * km2:.0f} km² on slope alone); "
          f"index cut-offs medium {cuts[2]:.3f}, high {cuts[3]:.3f}, very high {cuts[4]:.3f}; "
          f"high or very high = {base:.1f}% of steep land by construction")

    trf = Transformer.from_crs(4326, crs, always_xy=True)
    def cell(lon, lat):
        x, y = trf.transform(lon, lat)
        return int((t30.f - y) / C.RES_CMP), int((x - t30.c) / C.RES_CMP)
    def disc(r, c, radius_m):
        k = int(np.ceil(radius_m / C.RES_CMP))
        yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
        m = np.zeros((h, w), bool)
        r0, r1, c0, c1 = max(r - k, 0), min(r + k + 1, h), max(c - k, 0), min(c + k + 1, w)
        m[r0:r1, c0:c1] = (np.hypot(yy, xx) * C.RES_CMP <= radius_m)[r0 - (r - k):r1 - (r - k), c0 - (c - k):c1 - (c - k)]
        return m
    def share_high(mask):
        s = mask & steep
        return (round(100 * float(hi_cls[s].mean()), 1), round(s.sum() * km2, 2)) if s.any() else (None, 0.0)

    checks = dict(baseline_high_or_very_high_pct_of_steep_land=round(float(base), 1))

    # ---------------------------------------------------------------- check 1: Hill Risk radar sites
    hp = pd.read_csv(C.OUT / "hill_risk.csv") if (C.OUT / "hill_risk.csv").exists() else pd.DataFrame()
    if len(hp):
        rc = [cell(a, b) for a, b in zip(hp.lon, hp.lat)]
        k_site = np.array([cls[r, c] for r, c in rc])
        within = np.array([cls[disc(r, c, 100) & steep].max() if (disc(r, c, 100) & steep).any() else 0 for r, c in rc])
        checks["hill_risk_sites"] = dict(
            sites=int(len(hp)), on_steep_land=int((k_site != 255).sum()),
            high_or_very_high_at_site_pct=round(100 * float(np.isin(k_site, [3, 4]).mean()), 1),
            high_or_very_high_within_100m_pct=round(100 * float((within >= 3).mean()), 1),
            class_counts_at_site={R.CLASS_NAMES.get(int(v), "not steep"): int(n) for v, n in zip(*np.unique(k_site, return_counts=True))},
            note="Not independent of the index: both use slope and the same rainfall, so agreement is expected.")

    # ---------------------------------------------------------------- check 2: catalog points
    cat_rows = []
    if CATALOG.exists():
        cat = pd.read_csv(CATALOG, low_memory=False)
        up = gpd.read_file(C.WORK / "upazilas.geojson").to_crs(4326)
        g = gpd.GeoDataFrame(cat, geometry=gpd.points_from_xy(cat.longitude, cat.latitude), crs=4326)
        g = gpd.sjoin(g, up[["name", "geometry"]], predicate="within", how="inner").drop_duplicates(subset=["event_date", "longitude", "latitude"])
        for r_ in g.itertuples():
            acc = str(r_.location_accuracy)
            rad = float(acc.replace("km", "")) * 1000 if acc.endswith("km") else np.nan
            use = min(rad, MAX_CATALOG_RADIUS_M) if np.isfinite(rad) else MAX_CATALOG_RADIUS_M
            sh, a = share_high(disc(*cell(r_.longitude, r_.latitude), use))
            cat_rows.append(dict(event_date=str(r_.event_date)[:10], place=str(r_.event_title)[:48], upazila=r_.name, stated_accuracy=acc,
                                 radius_used_m=int(use), steep_km2_in_radius=a, high_or_very_high_pct=sh))
        cdf = pd.DataFrame(cat_rows)
        cdf.to_csv(C.OUT / "landslide_risk_catalog_check.csv", index=False)
        ok = cdf.dropna(subset=["high_or_very_high_pct"])
        fine = ok[ok.stated_accuracy.isin(["1km", "exact"])]
        checks["catalog_points"] = dict(
            source="NASA Global Landslide Catalog export (data.nasa.gov), events 2007-2017", in_district=int(len(cdf)),
            with_steep_land_in_radius=int(len(ok)), located_to_1km=int(len(fine)),
            mean_high_or_very_high_pct_in_radius=round(float(ok.high_or_very_high_pct.mean()), 1) if len(ok) else None,
            points_above_baseline=int((ok.high_or_very_high_pct > base).sum()),
            mean_high_or_very_high_pct_1km_points=round(float(fine.high_or_very_high_pct.mean()), 1) if len(fine) else None,
            note="Most points are located only to within 5-25 km, so this compares the steep land around each point with the district.")

    # ---------------------------------------------------------------- check 3: places named in the reports
    named = []
    for nm, (lon, lat) in NAMED_POINTS.items():
        sh, a = share_high(disc(*cell(lon, lat), 1000))
        named.append(dict(place=nm, area="within 1 km of the geocoded point (approximate)", steep_km2=a, high_or_very_high_pct=sh))
    for nm in NAMED_UPAZILAS:
        sh, a = share_high(uid == names.index(nm))
        named.append(dict(place=nm, area="whole upazila", steep_km2=a, high_or_very_high_pct=sh))
    for d in named:
        d["above_district_share"] = None if d["high_or_very_high_pct"] is None else bool(d["high_or_very_high_pct"] > base)
    checks["named_places"] = named

    # ---------------------------------------------------------------- check 4: LHASA nowcast and NASA's global map
    lh = warp_window(R.A / "lhasa_max.tif", full, res=C.RES_CMP, resampling=Resampling.nearest) if (R.A / "lhasa_max.tif").exists() else None
    comp = []
    if lh is not None:
        m = steep & np.isfinite(lh)
        rho = spearmanr(index[m][::25], lh[m][::25]).statistic if m.sum() > 1000 else np.nan
        checks["lhasa"] = dict(steep_land_with_lhasa_pct=round(100 * m.sum() / steep.sum(), 1), spearman_index_vs_lhasa=round(float(rho), 3),
                               note="LHASA files cover 5-9 and 13-18 Jul (10-12 Jul missing) and only part of the area; cells are about 1 km.")
    ns = warp_window(NASA_SUSC, full, res=C.RES_CMP, dtype="float32", nodata=np.nan, resampling=Resampling.nearest, src_nodata=127) if NASA_SUSC.exists() else None
    if ns is not None:
        m2 = steep & np.isfinite(ns)
        checks["nasa_susceptibility"] = dict(
            source="NASA global landslide susceptibility map, 2023 update, about 1 km, classes 1 (very low) to 5 (very high)",
            spearman_index_vs_nasa_class=round(float(spearmanr(index[m2][::25], ns[m2][::25]).statistic), 3),
            our_high_or_very_high_in_nasa_high_or_very_high_pct=round(100 * float((ns[hi_cls & m2] >= 4).mean()), 1),
            all_steep_land_in_nasa_high_or_very_high_pct=round(100 * float((ns[m2] >= 4).mean()), 1))
    for k in range(1, 5):
        c_ = steep & (cls == k)
        row = dict(risk_class=R.CLASS_NAMES[k], km2=round(c_.sum() * km2, 1), mean_slope_deg=round(float(slope[c_].mean()), 1),
                   mean_rain_mm=round(float(np.nanmean(rain[c_])), 0), tree_cover_pct=round(100 * float((group[c_] == "tree").mean()), 1),
                   mean_curvature=round(float(curvature[c_].mean()), 3), mean_elevation_m=round(float(np.nanmean(z[c_])), 0))
        if lh is not None:
            v = lh[c_ & np.isfinite(lh)]
            row.update(mean_lhasa_max=round(float(v.mean()), 3) if len(v) else None, lhasa_ge_0_3_pct=round(100 * float((v >= 0.3).mean()), 1) if len(v) else None)
        if ns is not None:
            v = ns[c_ & np.isfinite(ns)]
            row.update(mean_nasa_class=round(float(v.mean()), 2) if len(v) else None)
        comp.append(row)
    pd.DataFrame(comp).to_csv(C.OUT / "landslide_risk_class_summary.csv", index=False)

    # ---------------------------------------------------------------- explain: each factor's contribution
    ex = []
    for k in WEIGHTS:
        ex.append(dict(factor=k, label=LABELS[k], weight=WEIGHTS[k], mean_contribution_all_steep=round(float(contrib[k][steep].mean()), 4),
                       mean_contribution_high_or_very_high=round(float(contrib[k][hi_cls].mean()), 4),
                       mean_contribution_low=round(float(contrib[k][steep & (cls == 1)].mean()), 4)))
    edf = pd.DataFrame(ex)
    edf["share_of_index_in_high_or_very_high_pct"] = (100 * edf.mean_contribution_high_or_very_high / edf.mean_contribution_high_or_very_high.sum()).round(1)
    edf["lift_high_minus_low"] = (edf.mean_contribution_high_or_very_high - edf.mean_contribution_low).round(4)
    edf.to_csv(C.OUT / "xai" / "landslide_index_contributions.csv", index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    yv = np.arange(len(edf))
    ax.barh(yv + 0.2, edf.mean_contribution_high_or_very_high, 0.4, color="#7e57c2", label="high and very high cells")
    ax.barh(yv - 0.2, edf.mean_contribution_low, 0.4, color="#d1c4e9", label="low cells")
    ax.set_yticks(yv, [f"{l} (weight {wt:g})" for l, wt in zip(edf.label, edf.weight)]); ax.invert_yaxis()
    ax.set_xlabel("mean contribution to the index"); ax.legend(fontsize=8); ax.set_title("Landslide index: what each factor adds", fontsize=10)
    fig.tight_layout(); fig.savefig(C.OUT / "xai" / "landslide_index_contributions.png"); plt.close(fig)
    top = edf.sort_values("lift_high_minus_low", ascending=False).iloc[0]
    sentence = (f"High and very high cells differ from low ones mostly through {top.label.lower()}, "
                f"which adds {top.lift_high_minus_low:.2f} more to their index.")

    # ---------------------------------------------------------------- per upazila
    pop = R.population_30m()
    near_hi = (ndi.distance_transform_edt(~hi_cls) * C.RES_CMP <= 100) if hi_cls.any() else np.zeros((h, w), bool)
    vh = steep & (cls == 4)
    near_vh = (ndi.distance_transform_edt(~vh) * C.RES_CMP <= 100) if vh.any() else np.zeros((h, w), bool)
    rows = []
    for i in range(1, len(names)):
        u = uid == i
        rows.append(dict(id=ids[i], name=names[i], steep_km2=round((u & steep).sum() * km2, 1),
                         steep_km2_before_fix=round((u & steep_before_fix).sum() * km2, 1),
                         high_km2=round((u & steep & (cls == 3)).sum() * km2, 2), very_high_km2=round((u & vh).sum() * km2, 2),
                         people_within_100m_high_or_very_high=int(round(pop[u & near_hi].sum())),
                         people_within_100m_very_high=int(round(pop[u & near_vh].sum())),
                         high_or_very_high_pct_of_steep=round(100 * float(hi_cls[u & steep].mean()), 1) if (u & steep).any() else None))
    udf = pd.DataFrame(rows).sort_values("people_within_100m_high_or_very_high", ascending=False)
    udf.to_csv(C.OUT / "landslide_risk_upazilas.csv", index=False)

    # ---------------------------------------------------------------- app files
    C.WEB_DATA.mkdir(parents=True, exist_ok=True) if C.WEB_DATA.parent.exists() else None
    web = C.WEB_DATA if C.WEB_DATA.exists() else C.OUT
    pw, ph, kb = R.write_overlay_png(cls, COLOURS, web / "landslide_risk.png", web / "landslide_risk_bounds.json")
    R.update_risk_json("landslide", dict(
        title="Landslide risk",
        meaning="A likelihood map, not a forecast: a ranking of steep land by how prone it is to landslides in rain like July 2026.",
        method="Weighted index (not a trained model)", min_slope_deg=MIN_SLOPE, min_relief_m=MIN_RELIEF_M, weights=WEIGHTS,
        slope_definition=f"slope of {MIN_SLOPE:g} degrees or more AND a rise of {MIN_RELIEF_M:g} m or more within 300 m; in built-up cells the slope "
                         "comes from a lightly smoothed DEM, so buildings on flat land are not counted",
        factor_scaling=dict(slope="0 at 5 degrees, 1 at 35 or more", relief="height range within 300 m, 1 at 150 m or more",
                            rainfall=f"IMERG 5-18 Jul, 0 at {C.RAIN_MM:g} mm, 1 at 700 mm", land_cover=LC_SCORE,
                            hill_cutting="1 next to built-up land, 0 at 500 m or more"),
        why_not_a_model="The NASA Global Landslide Catalog has 38 points in the grid (19 in the district, 2007-2017), under the 40 needed, "
                        "and most are located only to within 5-25 km, which cannot label 30 m cells.",
        limits=["Weights are a judgement, not fitted to landslide records.", "Susceptibility, not a forecast.",
                "Classes are ranks within the district's steep land, so 20% is high or very high by construction.",
                "The DEM is a surface model: canopy still adds some false slope; buildings on flat land are screened out by the relief rule.",
                "Rainfall cells are about 10 km wide.", "No geology, soil or road-cut data."],
        classes=dict(index_cutoffs=dict(medium=round(cuts[2], 3), high=round(cuts[3], 3), very_high=round(cuts[4], 3)),
                     share_of_steep_land=dict(very_high=0.05, high=0.15, medium=0.30, low=0.50), summary=comp,
                     colours={R.CLASS_NAMES[k]: "#%02x%02x%02x" % v[:3] for k, v in COLOURS.items()}),
        checks=checks, explain=dict(sentence=sentence, factors=edf.to_dict("records")),
        upazilas=udf.to_dict("records"),
        totals=dict(steep_km2=round(float(steep.sum() * km2), 1), high_or_very_high_km2=round(float(hi_cls.sum() * km2), 1),
                    people_within_100m_high_or_very_high=int(udf.people_within_100m_high_or_very_high.sum()),
                    people_within_100m_very_high=int(udf.people_within_100m_very_high.sum())),
        overlay=dict(image="landslide_risk.png", bounds="landslide_risk_bounds.json", width=pw, height=ph)))

    # ---------------------------------------------------------------- summary
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
    print("\nclasses:\n" + pd.DataFrame(comp).to_string(index=False))
    for k, v in checks.items():
        if k == "named_places":
            print("\nplaces named in the reports:\n" + pd.DataFrame(v).to_string(index=False))
        else:
            print(f"\n{k}: {v}")
    if cat_rows:
        print("\ncatalog points inside the district:\n" + pd.DataFrame(cat_rows).to_string(index=False))
    print("\nfactor contributions:\n" + edf.to_string(index=False)); print(sentence)
    print("\ntop upazilas by people within 100 m of high or very high slopes:\n" + udf.head(10).drop(columns="id").to_string(index=False))
    print(f"\noverlay {pw} x {ph} px, {kb:.0f} KB -> {web / 'landslide_risk.png'}")
    print(f"({time.time() - t_start:.0f} s)")


def read_built_share():
    """Share of each 30 m cell that is WorldCover built-up."""
    import rasterio
    from rasterio.windows import Window
    _, w, h, _, _ = R.grid30()
    out = np.zeros((h, w), "float32")
    with rasterio.open(R.A / "worldcover.tif") as ws:
        for r in range(0, h, 600):
            n = min(600, h - r)
            a = ws.read(1, window=Window(0, r * R.K, w * R.K, n * R.K)).reshape(n, R.K, w, R.K)
            out[r:r + n] = (a == C.BUILT_CLASS).mean(axis=(1, 3))
    return out


if __name__ == "__main__":
    main()
