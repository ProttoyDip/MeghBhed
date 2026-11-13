"""Step 8: people and upazila statistics + files for the web app (METHOD.md sections 5, 7).

Writes to outputs/ (and copies to web/public/data/):
  stats.json            per-upazila numbers in the same fields the app uses in concept.js
  flood.geojson         flood polygons: kind "hidden" (missed by the 16 Jul C-band map), "open" (seen by both)
                        or "trees" (under trees, unverified), each with a "drained" property
  flood_preview.geojson a light copy for the landing page: larger "hidden" and "open" patches only,
                        simplified harder, kind as the only property
  upazila_stats.csv     the same table for the slides and the validation check
  labels_30m.tif, drained_30m.tif   the 30 m comparison map and the drained flag

Field meanings (names kept so the front end still works):
  hidden   km² of open flood on 12 Jul that the 16 Jul C-band map did not show (label 1)
  both     km² of open flood seen by both (label 2)
  people   WorldPop population within PEOPLE_BUFFER_M of label 1 cells (an upper bound)
  agree    "both-dates" when the 19 Jul pass covers at least half of the upazila's label 1 area AND at
           least half of that covered area had drained; otherwise "one-date"
  hill     Hill Risk points

    python pipeline/08_stats.py
"""
import json
import shutil
from datetime import date

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import shapes
from scipy import ndimage as ndi
from shapely.geometry import shape

import config as C
from common import ensure_dirs, load_grid, read_full

MAX_GEOJSON_MB = 5.0
MAX_PREVIEW_KB = 450      # flood_preview.geojson, the light copy for the landing page's small map


def within(mask, metres):
    """Cells within `metres` of any True cell (30 m grid)."""
    if not mask.any():
        return np.zeros(mask.shape, bool)
    return ndi.distance_transform_edt(~mask) * C.RES_CMP <= metres


def write_geojson(g, path, digits=5):
    """Write GeoJSON by hand: coordinates rounded to ~1 m, and true / false / null kept as such."""
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], digits), round(c[1], digits)]
    feats = []
    for geom, row in zip(g.geometry, g.drop(columns="geometry").to_dict("records")):
        gj = geom.__geo_interface__
        props = {k: (None if v is None or v != v else (bool(v) if isinstance(v, (bool, np.bool_)) else v)) for k, v in row.items()}
        feats.append({"type": "Feature", "properties": props, "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))


def main():
    ensure_dirs()
    A = C.WORK / "aux"
    lab = read_full(C.WORK / "labels_30m.tif")
    drained = read_full(C.WORK / "drained_30m.tif")
    pop = np.nan_to_num(read_full(A / "population_30m.tif")).astype("float64")
    uid = read_full(A / "upazila_id_30m.tif")
    index = json.loads((A / "upazila_index.json").read_text())
    km2 = C.RES_CMP ** 2 / 1e6
    up = gpd.read_file(C.WORK / "upazilas.geojson")

    hill = None
    if (C.OUT / "hill_risk.geojson").exists():
        hp = gpd.read_file(C.OUT / "hill_risk.geojson")
        if len(hp):
            hill = gpd.sjoin(hp, up[["id", "geometry"]], predicate="within").groupby("id").size()

    n = len(index) + 1
    ins = uid > 0
    def per(mask, w=None):
        m = mask & ins
        return np.bincount(uid[m].ravel(), weights=None if w is None else w[m].ravel(), minlength=n)

    missed, both, trees = lab == 1, lab == 2, lab == 5
    # conservative: only missed-flood patches of CONSERVATIVE_PATCH_HA or more
    plab, _ = ndi.label(missed, structure=np.ones((3, 3), bool))
    big = np.bincount(plab.ravel()) >= int(np.ceil(C.CONSERVATIVE_PATCH_HA * 1e4 / C.RES_CMP ** 2))
    big[0] = False
    missed_big = big[plab]

    a_missed, a_both, a_trees, a_big = (per(m) * km2 for m in (missed, both, trees, missed_big))
    p_missed = per(within(missed, C.PEOPLE_BUFFER_M), pop)
    p_all = per(within(missed | both, C.PEOPLE_BUFFER_M), pop)
    p_cons = per(within(missed_big, C.PEOPLE_BUFFER_M), pop)
    n_missed = per(missed)
    cov = per(missed & (drained != 255))
    dr = per(missed & (drained == 1))

    rows = []
    for i, u in enumerate(index, start=1):
        g = up[up.id == u["id"]].geometry.iloc[0].representative_point()
        dpct = round(100 * dr[i] / cov[i], 1) if cov[i] > 0 else None
        cpct = round(100 * cov[i] / n_missed[i], 0) if n_missed[i] > 0 else None
        rows.append(dict(
            id=u["id"], name=u["name"], bn="", district=u["district"], districtBn="",
            center=[round(g.x, 3), round(g.y, 3)],
            hidden=round(float(a_missed[i]), 2), both=round(float(a_both[i]), 2),
            people=int(round(p_missed[i])),
            agree="both-dates" if cpct is not None and cpct >= 50 and dpct is not None and dpct >= 50 else "one-date",
            hill=int(hill.get(u["id"], 0)) if hill is not None else 0,
            under_trees_unverified_km2=round(float(a_trees[i]), 2),
            people_within_100m_all_flood=int(round(p_all[i])),
            people_conservative=int(round(p_cons[i])),
            hidden_5ha_km2=round(float(a_big[i]), 2),
            drained_pct=dpct,
            drain_pass_covers_pct=cpct))
    rows.sort(key=lambda r: r["people"], reverse=True)
    df = pd.DataFrame(rows)
    df.drop(columns=["bn", "districtBn", "center"]).to_csv(C.OUT / "upazila_stats.csv", index=False)

    dates_p = A / "june_dates.json"
    june_dates = json.loads(dates_p.read_text()) if dates_p.exists() else []
    tcov, tdr = int(cov.sum()), int(dr.sum())
    stats = dict(
        is_concept=False, generated=str(date.today()), detector=C.DETECTOR,
        method=dict(
            rule=(f"Open flood: non-tree land, HAND <= {C.OPEN_HAND_MAX_M:g} m, not WorldCover 80/90/95, "
                  f"HH dropped by at least {abs(C.DARK_DROP):g} dB and HH on the flood date <= {C.DARK_DB:g} dB; "
                  f"30 m patches under {C.OPEN_MIN_PATCH_HA:g} ha dropped; water on any June date removed."),
            dates=dict(nisar_flood_pass="2026-07-12", nisar_before=["2026-06-18", "2026-06-30"], nisar_later_pass="2026-07-19",
                       cband_map="OPERA DSWx-S1 2026-07-16", june_water_dates=june_dates),
            DARK_DB=C.DARK_DB, DARK_DROP_dB=C.DARK_DROP, open_hand_max_m=C.OPEN_HAND_MAX_M,
            open_min_patch_ha=C.OPEN_MIN_PATCH_HA, conservative_patch_ha=C.CONSERVATIVE_PATCH_HA,
            people_buffer_m=C.PEOPLE_BUFFER_M, grid_m=C.RES_CMP, agg_fraction=C.AGG_FRACTION, multilook_px=C.MULTILOOK_PX,
            pairs={k: list(v) for k, v in C.PAIRS.items()}, extra=getattr(C, "EXTRA", {}),
            primary_pair=C.PRIMARY_PAIR, drain_pair=C.DRAIN_PAIR,
            people_note=("People figures are an upper bound: about 14% of open low ground away from reported flooding is "
                         "also flagged by this rule, and the count is everyone living within 100 m of a flagged cell. "
                         "people_conservative counts only missed-flood patches of "
                         f"{C.CONSERVATIVE_PATCH_HA:g} ha or more."),
            under_trees_note=("Under-tree cells (HH-rise rule) are unverified: no radar feature separated flooded from dry "
                              "groves on independent test sites. They are not in any total."),
            note="NISAR flood pass 12 Jul vs C-band 16 Jul: a four-day gap. 'Missed' means not on the 16 Jul C-band map."),
        upazilas=[r for r in rows if r["hidden"] > 0 or r["both"] > 0 or r["hill"] > 0],
        totals=dict(hidden=round(float(df.hidden.sum()), 2), both=round(float(df.both.sum()), 2),
                    people=int(df.people.sum()), hill=int(df.hill.sum()),
                    under_trees_unverified_km2=round(float(df.under_trees_unverified_km2.sum()), 2),
                    people_within_100m_all_flood=int(df.people_within_100m_all_flood.sum()),
                    people_conservative=int(df.people_conservative.sum()),
                    hidden_5ha_km2=round(float(df.hidden_5ha_km2.sum()), 2),
                    drained_pct=round(100 * tdr / tcov, 1) if tcov else None),
        labels={"1": "Missed by the 16 Jul C-band map", "2": "Seen by both", "5": "Under trees, unverified"},
    )
    (C.OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))

    # flood polygons (30 m cells merged), in lon/lat for MapLibre
    t, *_ = load_grid(C.RES_CMP)
    kinds = {1: "hidden", 2: "open", 5: "trees"}
    code = np.zeros(lab.shape, "uint8")                 # label * 10 + drained code (0 still dark, 1 drained, 2 not covered)
    for v in kinds:
        m = lab == v
        code[m] = v * 10 + np.where(drained[m] == 1, 1, np.where(drained[m] == 0, 0, 2))
    feats = []
    for geom, v in shapes(code, mask=code > 0, transform=t):
        v = int(v)
        feats.append(dict(geometry=shape(geom), kind=kinds[v // 10], label=v // 10, drained={0: False, 1: True, 2: None}[v % 10]))
    size_mb = 0.0
    if feats:
        g0 = gpd.GeoDataFrame(feats, crs=C.CRS)
        g0["agree"] = np.where(g0.kind == "hidden", np.where(g0.drained == True, "both-dates", "one-date"), None)
        upz = up.to_crs(C.CRS)[["id", "geometry"]].rename(columns={"id": "upazila"})
        g0 = gpd.sjoin(g0, upz, predicate="intersects", how="left").drop(columns="index_right")
        g0 = g0[~g0.index.duplicated(keep="first")]
        for tol in (C.RES_CMP / 2, C.RES_CMP, C.RES_CMP * 2, C.RES_CMP * 3):     # simplify harder until the file is small enough
            g = g0.copy()
            g["geometry"] = g.geometry.simplify(tol)
            g = g[~g.geometry.is_empty]
            write_geojson(g.to_crs(4326), C.OUT / "flood.geojson")
            size_mb = (C.OUT / "flood.geojson").stat().st_size / 1e6
            if size_mb <= MAX_GEOJSON_MB:
                break
        print(f"flood.geojson: {len(g):,} polygons, {size_mb:.2f} MB (simplified to {tol:g} m)")
        # light copy for the landing page: no under-tree cells, and only patches big enough to see at district scale
        prev = g0[g0.kind.isin(["hidden", "open"])][["kind", "geometry"]]
        for min_ha in (2, 3, 5, 8, 12, 20, 40):
            pv = prev[prev.geometry.area >= min_ha * 1e4].copy()
            pv["geometry"] = pv.geometry.simplify(C.RES_CMP * 2)
            pv = pv[~pv.geometry.is_empty]
            write_geojson(pv.to_crs(4326), C.OUT / "flood_preview.geojson", digits=4)
            kb = (C.OUT / "flood_preview.geojson").stat().st_size / 1e3
            if kb <= MAX_PREVIEW_KB:
                break
        print(f"flood_preview.geojson: {len(pv):,} polygons of {min_ha} ha or more, {kb:.0f} KB, "
              f"{pv.geometry.area.sum() / 1e6:.0f} of {prev.geometry.area.sum() / 1e6:.0f} km² kept")
    shutil.copy(C.WORK / "labels_30m.tif", C.OUT / "labels_30m.tif")
    shutil.copy(C.WORK / "drained_30m.tif", C.OUT / "drained_30m.tif")

    t = stats["totals"]
    print(f"missed by the 16 Jul C-band map {t['hidden']} km², seen by both {t['both']} km², "
          f"under trees (unverified, not in totals) {t['under_trees_unverified_km2']} km²")
    print(f"people within {C.PEOPLE_BUFFER_M} m of missed flood {t['people']:,} (upper bound), conservative "
          f"({C.CONSERVATIVE_PATCH_HA:g} ha patches) {t['people_conservative']:,}, within {C.PEOPLE_BUFFER_M} m of all flood "
          f"{t['people_within_100m_all_flood']:,}; drained by 19 Jul {t['drained_pct']}%; hill points {t['hill']}")
    print(df.head(10)[["name", "hidden", "both", "people", "people_conservative", "drained_pct", "agree", "hill"]].to_string(index=False))

    if C.WEB_DATA.parent.exists():
        C.WEB_DATA.mkdir(parents=True, exist_ok=True)
        for f in ("stats.json", "flood.geojson", "flood_preview.geojson", "hill_risk.geojson"):
            if (C.OUT / f).exists():
                shutil.copy(C.OUT / f, C.WEB_DATA / f)
        print(f"copied app files to {C.WEB_DATA}")


if __name__ == "__main__":
    main()
