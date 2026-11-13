# MeghBhed data sources

All inputs are free and open. No raw data will be committed to this repository. Links were checked on 1 Oct 2026.

> [!NOTE]
> Most NASA datasets need a free [NASA Earthdata login](https://urs.earthdata.nasa.gov). The pipeline (planned) will use the `earthaccess` Python package, which reads credentials from `~/.netrc` or environment variables.

## Contents

- [Summary table](#summary-table)
- [Access notes](#access-notes)
- [Citations and attribution](#citations-and-attribution)

## Summary table

| Dataset | Short name / version | Provider | Used for | Resolution | Coverage used | Licence | Link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NISAR L2 GCOV | `NISAR_L2_GCOV_PROVISIONAL_V1` | NASA/ISRO, ASF DAAC | Hidden flood, slope change | 10 m (freq. A, 40 MHz); 20 or 80 m in other modes | 25 Jun – 19 Jul 2026 | Open, EOSDIS data use policy | [doi:10.5067/NIL2GCOV-P1](https://doi.org/10.5067/NIL2GCOV-P1) |
| NISAR L2 GUNW (optional) | Provisional | NASA/ISRO, ASF DAAC | Coherence on slopes | 80 m | To be confirmed | Open, EOSDIS data use policy | [ASF product overview](https://nisar-docs.asf.alaska.edu/products-overview/) |
| OPERA DSWx-S1 | `OPERA_L3_DSWX-S1_V1` | NASA JPL OPERA, PO.DAAC | C-band comparison | 30 m | 16 Jul 2026 | PO.DAAC data use policy; contains modified Copernicus Sentinel data | [doi:10.5067/OPDSWS1-L3V1](https://doi.org/10.5067/OPDSWS1-L3V1) |
| GPM IMERG Late, daily | `GPM_3IMERGDL` V07 | NASA GES DISC | July 2026 rainfall | 0.1° | 5–18 Jul 2026 | Open, EOSDIS data use policy | [doi:10.5067/GPM/IMERGDL/DAY/07](https://doi.org/10.5067/GPM/IMERGDL/DAY/07) |
| GPM IMERG Final, half-hourly | `GPM_3IMERGHH` V07 | NASA GES DISC | Rainfall (if released in time) | 0.1°, 30 min | 5–18 Jul 2026 | Open, EOSDIS data use policy | [doi:10.5067/GPM/IMERG/3B-HH/07](https://doi.org/10.5067/GPM/IMERG/3B-HH/07) |
| LHASA nowcast, near real time | LHASA 2 NRT hazard | NASA GSFC | Landslide hazard | ~1 km | Jul 2026 | Open | [NCCS data share](https://portal.nccs.nasa.gov/datashare/landslides/nrt/) |
| Global Landslide Catalog | GLC export (`Global_Landslide_Catalog_Export_rows.csv`) | NASA GSFC | Coarse check of the landslide risk map | Points | Export: 11,033 events, Nov 1988 – Sep 2017. In the grid: 38 events, Jun 2007 – Jul 2017 (19 in the district) | NASA terms (accept on export) | [data.nasa.gov CSV](https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv) (file used); [catalog page](https://catalog.data.gov/dataset/global-landslide-catalog-export) |
| ESA WorldCover | 2021 v200 | ESA | Tree cover (10), built-up (50) masks | 10 m | 2021 | CC BY 4.0 | [doi:10.5281/zenodo.7254221](https://doi.org/10.5281/zenodo.7254221) |
| WorldPop population counts | Bangladesh 100 m (year to be fixed) | WorldPop, University of Southampton | People per upazila | 100 m (3 arc-seconds) | Bangladesh | CC BY 4.0 | [WorldPop hub](https://hub.worldpop.org/geodata/summary?id=25280) |
| Copernicus DEM | GLO-30 | ESA / Copernicus | Slope | 30 m | Chattogram hills | Copernicus DEM licence (free, registration) | [OpenTopography](https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.032021.4326.1) |
| GLO-30 HAND | Global 30 m Height Above Nearest Drainage, v1 (2021) | Alaska Satellite Facility (ASF) | Low ground for the flood rule, risk maps and label sites | 30 m | 5 tiles, N21–N23, E091–E092 | CC0 1.0 | [AWS Registry of Open Data](https://registry.opendata.aws/glo-30-hand/) |
| NASA SRTM (fallback DEM) | `SRTMGL1` V003 | NASA, LP DAAC | Slope | 30 m (1 arc-second) | Chattogram hills | Open, EOSDIS data use policy | [LP DAAC](https://lpdaac.usgs.gov/products/srtmgl1v003/) |
| Bangladesh admin boundaries | geoBoundaries gbOpen, BGD ADM2 and ADM3 (release commit `9469f09`) | geoBoundaries (William & Mary geoLab); original source BBS and OCHA ROAP | District and upazila polygons | Vector | Admin levels 2–3 | CC BY 3.0 IGO | [geoBoundaries](https://www.geoboundaries.org/) |
| Situation reports | ICCG Sit Rep #2 | UN Bangladesh | Validation, context | Text | 5–22 Jul 2026 | Cite source | [UN Bangladesh](https://bangladesh.un.org/en/319868-bangladesh-situation-report-2-flash-flood-and-landslides-23-july-2026) |

## Access notes

### NISAR L2 GCOV (ASF DAAC)

- Calibrated **provisional** NISAR data became public on 20 Jul 2026, covering observations from 17 Jun 2026 ([NASA Earthdata announcement](https://www.earthdata.nasa.gov/data/alerts-outages/nisar-l-band-data-now-publicly-available)).
- Search with [ASF Vertex](https://search.asf.alaska.edu/), NASA Earthdata Search, or the `asf_search` Python package. Filter: dataset `NISAR`, processing level `GCOV`.
- Files are HDF5, several GB each (about 6–7 GB for the scenes in [METHOD.md](METHOD.md#1-study-area-and-dates)).
- Product guide: [nisar-docs.asf.alaska.edu/gcov](https://nisar-docs.asf.alaska.edu/gcov/).

### OPERA DSWx-S1 (PO.DAAC)

- One product per MGRS tile, as three GeoTIFFs: water classification plus confidence layers.
- The study area uses tiles `T46QCK` (Chattogram) and `T46QCL` (Feni) on 16 Jul 2026.
- Maps open inland water larger than about 3 ha. Also mirrored on the [AWS Registry of Open Data](https://registry.opendata.aws/nasa-operal3dswx-s1v1/).

### GPM IMERG (GES DISC)

- IMERG Final has a latency of about 3.5 months, so July 2026 Final data may appear only around the hackathon. The **Late** run (latency about 14 hours) is the default; Final replaces it if available.

### LHASA (NASA GSFC)

- The GES DISC LHASA archive (`Global_Landslide_Nowcast` 2.0.0) covers only 2015–2021.
- July 2026 nowcasts are in the NCCS near-real-time share (`nrt/hazard/`, NetCDF4), listed via the [NASA landslides page](https://gpm.nasa.gov/applications/landslides).

### ESA WorldCover

- Download 3° × 3° COG tiles from the open AWS bucket without an account: `aws s3 sync s3://esa-worldcover/v200/2021/map <dir> --no-sign-request`, or use [esa-worldcover.org](https://esa-worldcover.org/en/data-access).

### WorldPop

- The linked dataset is the 2020 unconstrained, UN-adjusted 100 m count ([doi:10.5258/SOTON/WP00660](https://doi.org/10.5258/SOTON/WP00660)). <!-- TODO(hackathon): decide on 2020 vs a newer WorldPop release and record the DOI -->

### geoBoundaries

- The pipeline reads `geoBoundaries-BGD-ADM2.geojson` (districts) and `geoBoundaries-BGD-ADM3.geojson` (upazilas) from the gbOpen release, pinned to commit `9469f09` of [wmgeolab/geoBoundaries](https://github.com/wmgeolab/geoBoundaries). `download_meghbhed_data.sh` fetches them.
- geoBoundaries lists the Bangladesh Bureau of Statistics (BBS) and OCHA ROAP as the source, under CC BY 3.0 IGO.
- District names can use the older spelling (*Chittagong*); `pipeline/config.py` accepts both (`DISTRICT_ALIASES`).

### GLO-30 HAND

- Height above the nearest drainage, computed by ASF from the Copernicus GLO-30 DEM. Downloaded from the open bucket without an account: `https://glo-30-hand.s3.amazonaws.com/v1/2021/Copernicus_DSM_COG_10_<tile>_HAND.tif` (same five tiles as the DEM).

### Global Landslide Catalog

- The file used is NASA's full export, `Global_Landslide_Catalog_Export_rows.csv` from [data.nasa.gov](https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv), saved as `data/landslide/glc_export.csv`. It holds 11,033 events from 7 Nov 1988 to 28 Sep 2017.
- Inside the analysis grid there are 38 events (11 Jun 2007 to 2 Jul 2017), 19 of them in Chattogram district. They are used only as a coarse check of the landslide risk map; the newer COOLR catalogue could not be fetched.

## Citations and attribution

- **NISAR:** cite the GCOV DOI above and follow the [EOSDIS data use and citation guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance).
- **OPERA DSWx-S1:** cite the DOI above and follow the [PO.DAAC citation policy](https://podaac.jpl.nasa.gov/CitingPODAAC).
- **ESA WorldCover:** "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."
- **WorldPop:** cite the dataset DOI; CC BY 4.0.
- **Global Landslide Catalog:** Kirschbaum et al. (2010) and Kirschbaum, Stanley and Zhou (2015), as requested by NASA.
- **geoBoundaries:** Runfola, D. et al. (2020). geoBoundaries: A global database of political administrative boundaries. *PLoS ONE* 15(4): e0231866. [doi:10.1371/journal.pone.0231866](https://doi.org/10.1371/journal.pone.0231866). Source data: Bangladesh Bureau of Statistics and OCHA ROAP; CC BY 3.0 IGO.
- **GLO-30 HAND:** "Global 30m Height Above Nearest Drainage (HAND) was accessed on <date> from https://registry.opendata.aws/glo-30-hand" (ASF's requested form); CC0 1.0.
