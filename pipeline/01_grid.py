"""Step 1: define the study area and one shared grid for every layer.

Reads the district (ADM2) and upazila (ADM3) boundaries, keeps Chattogram and
Feni, and writes:
  work/grid.json          10 m grid in UTM 46N (the 30 m grid shares its origin)
  work/study_area.geojson the two districts + buffer
  work/upazilas.geojson   upazilas inside the two districts, with a district column

    python pipeline/01_grid.py
"""
import json
import geopandas as gpd

import config as C
from common import ensure_dirs


def name_col(gdf):
    for c in ("shapeName", "ADM2_EN", "ADM3_EN", "NAME", "name"):
        if c in gdf.columns:
            return c
    raise SystemExit(f"No name column found in boundaries: {list(gdf.columns)}")


def main():
    ensure_dirs()
    adm2 = gpd.read_file(C.DATA / "boundaries" / "geoBoundaries-BGD-ADM2.geojson")
    adm3 = gpd.read_file(C.DATA / "boundaries" / "geoBoundaries-BGD-ADM3.geojson")
    n2, n3 = name_col(adm2), name_col(adm3)

    keep = []
    for d in dict.fromkeys(list(C.GRID_DISTRICTS) + list(C.DISTRICTS)):
        aliases = [a.lower() for a in C.DISTRICT_ALIASES.get(d, [d])]
        hit = adm2[adm2[n2].str.lower().isin(aliases)]
        if hit.empty:
            raise SystemExit(f"District {d!r} not found. Names available: {sorted(adm2[n2])[:20]} ...")
        hit = hit.assign(district=d)
        keep.append(hit)
    grid_districts = gpd.GeoDataFrame(gpd.pd.concat(keep), crs=adm2.crs).to_crs(C.CRS)
    districts = grid_districts[grid_districts["district"].isin(C.DISTRICTS)]

    # upazilas: those whose interior point falls inside a kept district
    up = adm3.to_crs(C.CRS)
    pts = up.copy()
    pts["geometry"] = up.representative_point()
    j = gpd.sjoin(pts, districts[["district", "geometry"]], predicate="within", how="inner")
    up = up.loc[j.index].assign(district=j["district"].values, name=up.loc[j.index, n3].values)
    up["id"] = up["name"].str.lower().str.replace(r"[^a-z0-9]+", "-", regex=True).str.strip("-")
    up[["id", "name", "district", "geometry"]].to_crs(4326).to_file(C.WORK / "upazilas.geojson", driver="GeoJSON")

    area = grid_districts.dissolve().buffer(C.BUFFER_M)
    gpd.GeoDataFrame(geometry=area, crs=C.CRS).to_crs(4326).to_file(C.WORK / "study_area.geojson", driver="GeoJSON")

    xmin, ymin, xmax, ymax = area.total_bounds
    s = C.RES_CMP  # snap to 30 m so the 10 m and 30 m grids line up exactly
    xmin, ymin = (xmin // s) * s, (ymin // s) * s
    xmax, ymax = -(-xmax // s) * s, -(-ymax // s) * s
    grid = dict(crs=C.CRS, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)
    (C.WORK / "grid.json").write_text(json.dumps(grid, indent=2))
    w, h = (xmax - xmin) / C.RES, (ymax - ymin) / C.RES
    print(f"Grid {w:.0f} x {h:.0f} px at {C.RES} m  ({(w*h)/1e6:.0f} M pixels)")
    print(f"{len(up)} upazilas: {', '.join(sorted(up['name']))}")


if __name__ == "__main__":
    main()
