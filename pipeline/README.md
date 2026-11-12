# MeghBhed pipeline: step-by-step

This folder turns the downloaded data into the real numbers and maps for the app.
Every step is one script. Settings and thresholds live in `config.py` only.

```
data/  (from download_meghbhed_data.sh)  ->  work/  (intermediate)  ->  outputs/  ->  web/public/data/
```

## 0. Set up (once, every laptop that runs code)

1. Copy this `pipeline/` folder and `environment.yml` into the repo root, next to `web/` and `data/`.
2. Add these lines to `.gitignore`: `data/`, `work/`, `outputs/*.tif`. The NISAR files are far too big for git.
3. Install: `conda env create -f environment.yml`, then `conda activate meghbhed`.
4. Free disk: about 10 GB for `work/`.

Run every command from the **repo root**.

## 1. Look inside the NISAR files

```
python pipeline/00_inspect.py
```

Check three things in the output:
- spacing is **10 m** (40 MHz mode),
- HHHH median is roughly **−5 to −15 dB** (linear γ⁰, as expected),
- the **mask values**. `config.py` treats `0` and `255` as invalid. Confirm what each value means in the GCOV product specification and edit `MASK_INVALID` if needed.

## 2. Run the baseline (threshold detector)

```
python pipeline/run_all.py
```

This runs steps 1–8 in order:

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `01_grid.py` | Picks Chattogram + Feni from the boundaries; makes one 10 m UTM grid |
| 2 | `02_nisar.py` | Reads only the study area from each GCOV file, Lee speckle filter, dB, onto the grid (slowest step) |
| 3 | `03_ancillary.py` | Puts WorldCover, slope (from DEM), HAND, DSWx-S1, WorldPop and upazilas on the same grid; builds June water from `data/dswx_s1_pre/` |
| 4 | `04_detect.py` | **Model 1:** open flood = non-tree low ground, HH dropped ≥ 3 dB and HH ≤ −14 dB, per pair. Also the old under-tree rule, kept as "unverified" |
| 6 | `06_compare.py` | 30 m comparison with DSWx-S1: missed by the 16 Jul C-band map / seen by both / under trees (unverified); drained-by-19-Jul flag |
| 7 | `07_hillrisk.py` | **Model 4:** slope + rain + LHASA + NISAR change → places to check |
| 8 | `08_stats.py` | km² and people within 100 m per upazila → `stats.json`, `flood.geojson`, CSV; copies to `web/public/data/` |

Each step prints a short summary. Read it: coverage %, km² flagged, people counted.

## 3. Tune the thresholds

1. Fill `labels/sites.csv` (Eva and Thouhidul). One row per site:
   ```
   lon,lat,label,pairs,source
   91.8312,22.4521,1,A;B,https://link-to-photo-or-report
   91.8105,22.3702,0,,https://link-to-photo-or-report
   ```
   `label` 1 = flooded under trees, 0 = stayed dry. `pairs` = which NISAR pairs it applies to (empty = all).
   Aim for 20–40 of each, spread across the area, and include **dry sites on low ground**.
2. Open `work/nisar/*_HH.tif` and `work/flood_A.tif` in QGIS next to the sites.
3. Change `T_HH`, `T_HV`, `MIN_PATCH_PX` in `config.py` and re-run from step 4: `python pipeline/run_all.py --from 4`.
4. Write the final values into `docs/METHOD.md`.

## 4. Train the classifier (models 2 and 3)

```
python pipeline/run_all.py --ml --from 5
```

- Trains **Random Forest** and **LightGBM** on the label sites plus automatic dry examples (forest with HAND > 20 m).
- Tests with **spatial cross-validation** (5 km blocks), so nearby pixels never sit in both train and test.
- Writes `outputs/model_comparison.csv`: precision, recall, F1 and false-alarm rate for the **baseline, RF and LightGBM**. This table goes in the pitch.
- Keeps the better model and writes `work/flood_ml_A.tif` etc.
- Then re-runs steps 6–8 with the classifier maps.

Use the classifier only if it beats the baseline **and** the warning below does not appear.
If it prints *"classifier flags >3x the baseline"*, open `outputs/feature_importance.csv`. If `hand` or `slope` is at the top, the model learned "low ground = flood" instead of the radar signal. Add dry sites on low ground and re-train. A physics check (HH must rise ≥ 1 dB) is always applied.

## 5. Put the results in the app (Partho)

`08_stats.py` copies these files to `web/public/data/`:

| File | Used by |
| --- | --- |
| `stats.json` | Statistics page, map side panel, AI assistant |
| `flood.geojson` | Map: `kind` = `hidden` (missed by the 16 Jul C-band map), `open` (seen by both) or `trees` (unverified), each with `drained` |
| `flood_preview.geojson` | Landing-page map preview: a light copy (under 450 KB) with larger patches only |
| `hill_risk.geojson` | Map: Hill Risk points |

The upazila objects in `stats.json` keep the fields the app was designed around: `id, name, bn, district, districtBn, center, hidden, both, people, agree, hill`, plus the fields listed under "Version 4 changes" below. The app reads them through `web/src/data/results.js`.

In the app: load them with `fetch('/data/stats.json')` instead of importing the illustrative arrays, and set `IS_CONCEPT = false`. Fill the Bangla names (`bn`, `districtBn`) by hand. They are left empty on purpose.

## 6. AI assistant (model 5, Sakin)

Give the language model `stats.json` as its only source of numbers (system prompt: answer only from this file; if it isn't there, say so). The API key stays in Vercel environment variables.

## Notes

- **Feni:** track 163 (pair B) does not cover it, so Feni cells come out as "possibly flooded (single track)". Uncomment pair C in `config.py` if you downloaded the track-91 files.
- **DSWx-S1 maps flooded vegetation too** (class 3, "inundated vegetation"). The pipeline counts that as water. So "likely missed" means *C-band said not water, not even flooded vegetation*.
- Every threshold is a starting value. Results are "likely" and "possible", never certain.
- The code was tested end to end on small fake data with the same file formats, not yet on the real files. Expect to fix small things in step 2 on first run.

## Version 2 changes (after the first real run found only speckle)

- **Multilook:** backscatter is averaged over 5×5 pixels (50 m) before differencing (`MULTILOOK_PX`).
- **Bias correction:** the scene-wide ΔHH/ΔHV measured on high forest that cannot flood is subtracted (`BIAS_CORRECT`).
- **Low ground only:** flood is flagged only where HAND ≤ 15 m (`HAND_MAX_M`).
- **Clip and exclusions:** only inside the two districts; WorldCover permanent water, wetland and mangrove are excluded.
- **Feni pair C** is used automatically when its two files are in `data/nisar/`.
- **LHASA** is recorded but no longer required for Hill Risk (`USE_LHASA = False`).
- **New diagnostic:** `python pipeline/09_diagnose.py` (run after step 4). It compares how often tree pixels pass the
  rule on low ground against high ground. Flood can only be on low ground, so:
  - low ground passes far more often → real signal; tune `T_HH` to the lowest value where high ground stays near zero;
  - both look alike → what passes is noise; do not lower thresholds.

After updating, re-run from step 2 if pair C is new, otherwise from step 3: `python pipeline/run_all.py --from 3`.

## Version 3 changes (after the diagnostic showed a faint signal on 12 Jul only)

- **Steadier baseline and an "after" test for pair A.** If the 18 Jun and 17 Aug scenes (track 69) are in `data/nisar/`,
  the "before" image is the average of 18 Jun and 30 Jun, and a pixel counts only if 12 Jul is also at least
  `T_AFTER` dB brighter than 17 Aug. Flood is temporary; noise and seasonal change are not.
- **Comparison rule.** `COMPARE_RULE = "primary"`: the flood pass (pair A, 12 Jul) is compared with C-band on 16 Jul.
  The four-day gap is written into `stats.json`. Set `"two_date"` to go back to the old rule.
- **The premise, tested.** Step 6 writes `outputs/cband_vs_trees.csv`: how much of C-band's flood mapping falls under
  tree cover, and what C-band said at the cells NISAR flags.
- **Chattogram only.** Feni is not in the UN list of affected districts. The grid is unchanged.
- **Hill Risk** now needs HV to drop by 3 dB on a steep, wet slope (vegetation stripped), in patches of 0.25 ha or more.
- **Small groves kept.** Minimum patch is 900 m² instead of 2,500 m².
- `02_nisar.py` skips scenes it has already processed (`--force` redoes them).

After updating: `python pipeline/02_nisar.py`, then `python pipeline/run_all.py --from 3`, then `python pipeline/09_diagnose.py`.

## Version 4 changes (the flood map is rebuilt around the 12 July open flood)

Checks on the real data showed two things. NISAR on 12 July clearly sees open floodwater, and far more of it than
the 16 July C-band map shows. And no radar feature could separate flooded from dry groves on independent test sites.
So the headline map changed from "flood hidden under trees" to "open flood on 12 July that the 16 July C-band map missed".

- **Open-flood rule** (`04_detect.py`): non-tree land, HAND ≤ 5 m (`OPEN_HAND_MAX_M`), not WorldCover 80/90/95,
  HH dropped by at least 3 dB (`DARK_DROP`) and HH on the flood date at or below −14 dB (`DARK_DB`, was −18).
  In `work/flood_<pair>.tif`, value 2 is open flood and value 1 is "under trees, unverified".
- **June water** (`03_ancillary.py`): `work/aux/june_water_30m.tif` counts the pre-flood DSWx-S1 dates with water,
  from the files in `data/dswx_s1_pre/`. Step 3 warns and carries on if that folder is empty.
- **Labels** (`06_compare.py`, 30 m, pair A as the flood pass): 1 = missed by the 16 July C-band map,
  2 = seen by both, 5 = under trees (unverified), 0 = not flagged, 255 = no data. June water is removed and flood
  patches under 1 ha are dropped. `work/drained_30m.tif` marks flood cells no longer dark on 19 July (pair B).
- **Stats** (`08_stats.py`): `hidden` = km² of label 1, `both` = km² of label 2, `people` = people within 100 m of
  label 1 (an upper bound), plus `people_conservative` (patches of 5 ha or more), `people_within_100m_all_flood`,
  `drained_pct` and `under_trees_unverified_km2`. `agree` is `both-dates` when the 19 July pass covers at least half of the
  upazila's label 1 area and at least half of that had drained. `flood.geojson` has kind `hidden`, `open` or `trees`, each with `drained`.
- **Under-tree rule**: still computed, never in a headline total. The test and its negative result are in
  `docs/METHOD.md` section 3.2.
- **Model comparison for open flood** (new, evaluation only): `python pipeline/10_flood_models.py` compares the rule
  with Random Forest and LightGBM on radar-only features and writes `outputs/flood_model_comparison.csv`,
  `outputs/flood_feature_importance.csv` and `web/public/data/model_comparison.json`. It does not change the map.
- `05_classify.py` (the under-tree classifier) reads a `set` column in `labels/sites.csv`: `train` rows are used for
  training, `test` rows are held out and scored into `outputs/model_test_reports.csv`. Its result is negative; do not
  set `DETECTOR = "ml"`.

After updating: `python pipeline/run_all.py --from 3`, then `python pipeline/10_flood_models.py`.

## Risk maps (steps 11 and 12)

Two likelihood (susceptibility) maps, **not forecasts**. They do not change the flood map, the thresholds or the labels.

```
python pipeline/11_flood_risk.py        # about 6 minutes
python pipeline/12_landslide_risk.py    # under 1 minute
```

They need steps 1–8 to have run. Step 11 also needs `shap` (in `environment.yml`). Shared helpers are in `risk_common.py`.

| Script | What it makes |
| --- | --- |
| `11_flood_risk.py` | **Flood risk in rain like July 2026.** A Random Forest trained on the 12 July open flood, from terrain only (HAND, elevation, slope, relief, distance to June water and to the coast), on open land. Writes `work/flood_risk_30m.tif` (0–1), `outputs/flood_risk_classes_30m.tif` (1 low to 4 very high), validation CSVs and SHAP plots in `outputs/xai/` |
| `12_landslide_risk.py` | **Landslide risk** on slopes of 5° or more. A weighted index (slope 0.40, relief 0.20, rain 0.20, land cover 0.10, nearness to buildings 0.10), not a trained model. Writes `outputs/landslide_risk_classes_30m.tif` and check tables. Optional inputs in `data/landslide/`: `glc_export.csv` (NASA Global Landslide Catalog) and `susceptibility_2023.tif` (NASA global susceptibility map) |

Both write to `outputs/risk.json` and, for the app, to `web/public/data/`: `flood_risk.png`, `landslide_risk.png` (transparent Web Mercator images, at most 4,000 px a side), their `*_bounds.json` corner files, and `risk.json` (per-upazila tables, class cut-offs, validation numbers, SHAP ranking).

Read before using the numbers (details in `docs/METHOD.md` section 10):

- **One flood.** The flood-risk model has seen only July 2026.
- **Canopy bias.** The DEM is a surface model, so tree-covered land scores far too low for flood risk. Treat that map as an open-land map and its people figures as a lower bound.
- **Buildings look like slopes.** City thanas get inflated landslide scores.
- **The landslide index is a judgement**, checked against a few coarse records, not validated.

## Data folders added after the first run

All are under `data/` and git-ignored.

| Folder | What is in it | Where it comes from | Used by |
| --- | --- | --- | --- |
| `data/dswx_s1_pre/` | OPERA DSWx-S1 `B01_WTR` for 7, 9, 19 and 21 June 2026, tiles T46QCK, T46QCL, T46QDK, T46QDL (16 files) | PO.DAAC, collection `OPERA_L3_DSWX-S1_V1`, found through NASA CMR; Earthdata login | Step 3 (June water), the label build |
| `data/landslide/glc_export.csv` | NASA Global Landslide Catalog export, events 1988–2017 | `https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv` | Step 12, as a coarse check only |
| `data/landslide/susceptibility_2023.tif` | NASA global landslide susceptibility map, 2023 update, about 1 km (the file NASA names `global-landslide-susceptibility-map-2-27-23.tif`) | `https://gpm.nasa.gov/sites/default/files/downloads/global-landslide-susceptibility-map-2-27-23.tif` | Step 12, comparison only |
| `data/nisar_gunw/` | Two NISAR L2 GUNW interferograms on track 69: 18 Jun → 30 Jun (before the flood) and 30 Jun → 12 Jul (across the flood) | ASF, `NISAR_L2_GUNW_PROVISIONAL_V1`; Earthdata login | The coherence test only; no pipeline step reads it |

The newer COOLR landslide catalogue could not be fetched: its services returned 404 or did not respond in November 2026. Step 12 runs without it.

`10_flood_models.py` now also fits logistic regression, tunes each classifier's cut-off to the precision–recall break-even point inside each spatial fold, and writes SHAP rankings and two waterfall examples. See `docs/METHOD.md` section 11.

## Later changes (steps 10 to 13)

- **`10_flood_models.py`** reports three rows per trained model: the default cut-off, the fold-tuned cut-off (nested), and the "precision-recall break-even point on cross-validated predictions". The last is marked: precision, recall and F1 are equal there by definition, and it is not a threshold tested on unseen data.
- **`11_flood_risk.py`** now estimates the ground under trees from the open land within 300 m. Tree-covered land then scores 0.49 to 1.19 times open land at the same ground HAND; the lowest band misses the 0.5 limit set in advance, so the script restricts the map and its people figures to open land ("Flood risk on open land"; the people figure is a lower bound). If the check passes on other data, the script keeps all land by itself.
- **`12_landslide_risk.py`** counts a cell as slope only where the ground rises 20 m or more within 300 m, and takes slope from a lightly smoothed DEM in built-up cells. Flat built-up thanas no longer appear.
- **`13_tree_flood.py`** (new, about 2 minutes, needs `data/nisar_gunw/`) tests an under-tree flood layer from the loss of NISAR coherence against four criteria fixed in advance. It writes `outputs/tree_flood_validation.json` and `outputs/tree_flood_models.csv`. **Two criteria fail**, so it writes no layer and nothing in the app changes. See `docs/METHOD.md` section 12.
