# MeghBhed method

> [!IMPORTANT]
> Sections 3, 4, 5 and 8 describe the method **as run on the real data** (pipeline in `pipeline/`, November 2026). The original plan was to map flood hidden under trees. That signal could not be verified (section 3.2), so the headline map is now the **open flood on 12 July** that the 16 July C-band map no longer showed. Other sections still describe the plan.

## Contents

- [1. Study area and dates](#1-study-area-and-dates)
- [2. Preprocessing](#2-preprocessing)
- [3. Flood detection](#3-flood-detection)
- [4. Fair comparison with C-band](#4-fair-comparison-with-c-band)
- [5. People and upazila statistics](#5-people-and-upazila-statistics)
- [6. Hill Risk layer](#6-hill-risk-layer)
- [7. Outputs](#7-outputs)
- [8. Validation](#8-validation)
- [9. Known limits](#9-known-limits)
- [10. Risk maps](#10-risk-maps)
- [11. Benchmark models for the open flood](#11-benchmark-models-for-the-open-flood)
- [12. Under trees again: the coherence test](#12-under-trees-again-the-coherence-test)

## 1. Study area and dates

**Version 1:** Chattogram and Feni districts, Bangladesh. **Next:** haor wetlands, the Sundarbans, and flooded forests elsewhere.

Chattogram was the most affected district in the July 2026 floods, with 785,400 people affected ([UN Sit Rep #2, 23 Jul 2026](https://bangladesh.un.org/en/319868-bangladesh-situation-report-2-flash-flood-and-landslides-23-july-2026)).

> [!WARNING]
> **Feni is not confirmed as flooded.** It is not among the districts named in UN Sit Rep #1 (13 Jul) or #2 (23 Jul). The only July 2026 source found so far is a forecast: on 12 Jul the Flood Forecasting and Warning Centre warned that the Muhuri, Feni and Selonia rivers could cause short-term flash floods in parts of Feni ([The Daily Star, 12 Jul 2026](https://www.thedailystar.net/news/environment/weather/news/10-districts-risk-fresh-flood-next-24-72-hours-ffwc-4221406)). Checked 11 Oct 2026. <!-- TODO: find a report of actual flooding in Feni, or drop Feni from the study area -->

The NISAR scenes below were found with the ASF Search API (`dataset=NISAR`, `processingLevel=GCOV`) on 1 Oct 2026. Dates and times are **UTC**. `DHDH` means dual polarisation, H transmit (HH and HV).

| Role | Date (UTC) | Track / frame | Direction | Mode | Granule |
| --- | --- | --- | --- | --- | --- |
| Before, pair A | 30 Jun 2026, 23:21 | 69 / 13 | Ascending | 4005 DHDH | `NISAR_L2_PR_GCOV_024_069_A_013_4005_DHDH_A_20260630T232101_20260630T232135_P05023_N_F_J_001` |
| During, pair A | 12 Jul 2026, 23:21 | 69 / 13 | Ascending | 4005 DHDH | `NISAR_L2_PR_GCOV_025_069_A_013_4005_DHDH_A_20260712T232100_20260712T232135_P05023_N_F_J_001` |
| Before, pair B | 25 Jun 2026, 12:26 | 163 / 77 | Descending | 4005 DHDH | `NISAR_L2_PR_GCOV_023_163_D_077_4005_DHDH_A_20260625T122638_20260625T122713_P05023_N_F_J_001` |
| During, pair B | 19 Jul 2026, 12:26 | 163 / 77 | Descending | 4005 DHDH | `NISAR_L2_PR_GCOV_025_163_D_077_4005_DHDH_A_20260719T122637_20260719T122711_P05023_N_F_J_001` |
| C-band reference | 16 Jul 2026, 23:47 | MGRS T46QCK, T46QCL | — | Sentinel-1C | `OPERA_L3_DSWx-S1_T46QCK_20260716T234703Z_20260725T000947Z_S1C_30_v1.0` and `…T46QCL…` |

> [!NOTE]
> In the same search, a test point in Feni (23.0° N, 91.4° E) was covered by tracks 69 and 91 but **not** track 163. The two-date rule may therefore only be possible over part of the study area. Track 91 (2 Jul → 14 Jul 2026) is a candidate second pair for Feni. <!-- VERIFY(hackathon): footprint overlap and mode of track 91 -->

## 2. Preprocessing

1. **Download** GCOV HDF5 files with `earthaccess` or `asf_search` (Earthdata login required).
2. **Read** the frequency A diagonal terms `HHHH` and `HVHV` (γ⁰, linear power) and the `mask` layer.
3. **Crop** to the district boundaries ([geoBoundaries](https://www.geoboundaries.org/) gbOpen, admin level 2) plus a small buffer.
4. **Convert to dB:** γ⁰<sub>dB</sub> = 10 · log<sub>10</sub>(γ⁰).
5. **Speckle filter:** a small-window filter such as refined Lee, applied the same way to both dates.
6. **Mask** invalid samples using the GCOV `mask` layer. The layer marks valid and invalid samples only (0 = invalid or partially focused, 1–5 = valid sub-swath number, 255 = outside the acquisition); it does **not** remove layover or shadow, so steep terrain is not screened out by this step.
7. **Co-register:** both dates of a pair share a track and a geocoding grid, so no resampling is expected between them. <!-- VERIFY(hackathon) -->

GCOV frequency A is posted at 10 m for 40 MHz modes ([ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/)). WorldCover is 10 m; DSWx-S1 is 30 m; WorldPop is 100 m.

## 3. Flood detection

Before any rule is applied, backscatter is averaged over 5 × 5 pixels (50 m), and the scene-wide change measured on high forest that cannot flood (HAND above 20 m) is subtracted from ΔHH and ΔHV. Pair A uses the average of two "before" scenes (18 and 30 June).

### 3.1 Open flood (the headline map)

A 10 m pixel is **open flood** when all of these hold (`pipeline/04_detect.py`):

| Step | Rule | Value |
| --- | --- | --- |
| Area | Inside Chattogram district | — |
| Land cover | **Not** WorldCover tree cover (class 10); not permanent water, wetland or mangrove (80, 90, 95) | — |
| Low ground | HAND (height above the nearest river) | ≤ 5 m |
| HH dropped | ΔHH = HH<sub>during</sub> − HH<sub>before</sub> | ≤ −3 dB |
| Dark on the flood date | HH<sub>during</sub> | ≤ −14 dB |
| Clean-up | Morphological opening, minimum patch | 9 pixels |

**Why these tests.** Smooth open water reflects the radar away, so flooded fields go dark. Requiring both a drop and a dark level removes permanent water (dark, but no drop) and fields that only got a little wetter (a drop, but not dark).

**How the −14 dB level was chosen.** On non-tree low ground, the rule was tested against the new open water that C-band mapped on 16 July (water on 16 July but on none of four June dates). New open water has a median HH of −15.6 dB on 12 July, and 73% of it dropped by 3 dB or more. The original −18 dB level caught under 2% of it. At −14 dB the rule catches 66% of the new open water and 28% of the new flooded vegetation, flags 12% of cropland more than 1 km from any mapped water, and 3% of permanent water (`outputs/openwater_rule_sweep.csv`).

**Evidence that it is flood, not farming** (`outputs/peak_flood_check.csv`):

- On cropland it flags 25% in the six upazilas reported badly flooded on 10–12 July (Satkania, Lohagara, Chandanaish, Banshkhali, Patiya, Anowara) against 14% elsewhere.
- Within 500 m of test points in unions reported submerged it flags 23% of open low ground, against 5% near points with no flood report.
- By the 19 July pass (pair B) the flagged share had more than halved in both groups.

It is still not a clean flood map: about 14% of open low ground away from reported flooding is flagged, and the rule cannot tell flood from freshly flooded paddy cell by cell.

### 3.2 Under trees (unverified)

The original hidden-flood rule is kept in the code, but its output is labelled **under trees, unverified** and never feeds a headline total. For each pixel inside the analysis mask:

| Step | Rule | Starting value |
| --- | --- | --- |
| Land-cover mask | ESA WorldCover 2021 class **10 (tree cover)** only | — |
| Exclusion | WorldCover class **50 (built-up)** removed, with a small buffer | 1 pixel |
| Double-bounce test | ΔHH = HH<sub>during</sub> − HH<sub>before</sub> ≥ T<sub>HH</sub> | T<sub>HH</sub> = +3 dB |
| Canopy-change test | ΔHV ≤ T<sub>HV</sub> | T<sub>HV</sub> = +1 dB |
| Low ground | HAND | ≤ 15 m |
| After the flood | HH<sub>during</sub> − HH on 17 August (pair A only) | ≥ +1.5 dB |
| Clean-up | Remove isolated pixels (morphological opening, minimum patch size) | 9 pixels |

**Why these tests.** Water under trees creates a water–trunk double bounce, which raises HH strongly. Volume scattering from the canopy mainly drives HV. A rise in HH without a matching rise in HV therefore points to water below, not to more leaves above ([Tsyganskaya et al., 2018](https://doi.org/10.1080/01431161.2017.1420938); [Refice et al., 2020](https://doi.org/10.3390/w12102745)).

**The test, and its negative result.** The rule flags only 1.7 km² on the flood pass. To check whether a real under-tree signal exists, label sites were built without using NISAR (`labels/README.md`):

- **Train sites** from C-band: 74 groves on low ground standing in new floodwater ("tree islands"), and 245 dry groves more than 1 km from any mapped water.
- **Test sites** from reports: 42 tree points in unions reported submerged on 10–12 July, and 42 in low-lying places with no flood report.

Results:

- At the 74 flooded groves the median HH change is +0.03 dB, the same as at the dry groves. The HH-rise rule catches none of them at grove scale, on either set.
- The best single feature on the train sites is the change in HH minus HV averaged over tree pixels within 150 m. Its AUC is 0.86 on train sites but 0.56 on test sites. HV change reverses direction between the two sets. Features using the 17 August scene are near 0.5 (`outputs/grove_signal.csv`).
- Random Forest and LightGBM given only radar-change features score an AUC of 0.84–0.86 in spatial cross-validation on train sites and 0.51–0.52 on test sites (`outputs/grove_models.csv`). With HAND, slope and backscatter levels added they flag 36–45% of dry test pixels (`outputs/model_test_reports.csv`).
- No feature reaches an AUC of 0.75 on both sets.

The train result probably reflects landscape (near water against far from water), not flooding under the canopy. The test labels are also weak: union-level reports, and "no report" for dry. So the under-tree signal is **not shown**, not disproved. Point-level ground truth, or dry groves close to floodwater, would settle it. A later test with interferometric coherence found a real ranking signal but still no usable map; see section 12.

## 4. Fair comparison with C-band

The comparison is made on the 30 m DSWx-S1 grid (`pipeline/06_compare.py`). NISAR flags are aggregated to 30 m first: a cell is flagged when at least half of its valid 10 m pixels are. The flood pass is pair A (NISAR, 12 July). The C-band map is OPERA DSWx-S1 of 16 July, four days later.

**June water** is removed first: any cell that DSWx-S1 mapped as water on 7, 9, 19 or 21 June 2026 is a river, pond or seasonal water, not flood (`work/aux/june_water_30m.tif`, built in step 3 from `data/dswx_s1_pre/`). Of the water DSWx-S1 mapped on 16 July, 72% was already water on a June date.

| Label | Meaning | Rule |
| --- | --- | --- |
| 1 | **Missed by the 16 July C-band map** | NISAR open flood on 12 July, DSWx-S1 not water on 16 July, not June water |
| 2 | Seen by both | NISAR open flood on 12 July, DSWx-S1 water on 16 July, not June water |
| 5 | Under trees, unverified | The rule of section 3.2, any pass. Not in any total |
| 0 | Not flagged | — |
| 255 | No data | DSWx-S1 masked, or no NISAR flood pass |

Flood patches (labels 1 and 2 together) smaller than 1 ha are dropped, to cut scattered wet-field noise.

**"Missed" does not mean C-band cannot see it.** Open water is easy for C-band. Label 1 is flood that was there on 12 July and was no longer on the map four days later: the C-band pass came after much of the water had gone.

**Drained within a week.** A second raster (`work/drained_30m.tif`) marks, for labels 1 and 2, whether the 19 July pass (pair B) covers the cell and no longer flags it as open flood. Pair B does not cover most of Mirsharai and Sandwip.

Cells where DSWx-S1 has no valid data are left out of the comparison, not counted as "missed".

## 5. People and upazila statistics

Open flood is on fields, where few people live, so people are counted **within 100 m of flood cells**, using WorldPop spread onto the 30 m grid (`pipeline/08_stats.py`). Everything is summed by **upazila** (geoBoundaries gbOpen, admin level 3).

Fields in `stats.json` (names kept from the concept app):

| Field | Meaning |
| --- | --- |
| `hidden` | km² of label 1: flood on 12 July that the 16 July C-band map missed |
| `both` | km² of label 2: seen by both |
| `people` | People within 100 m of label 1 cells. **An upper bound** |
| `people_conservative` | The same, counting only label 1 patches of 5 ha or more |
| `people_within_100m_all_flood` | People within 100 m of labels 1 and 2 |
| `drained_pct` | Share of the upazila's label 1 area no longer dark on 19 July, where that pass covers it |
| `agree` | `both-dates` (shown as "Drained within a week") when the 19 July pass covers at least half of the upazila's label 1 area and `drained_pct` is 50 or more; else `one-date` ("Still wet on 19 July or not covered") |
| `under_trees_unverified_km2` | km² of label 5. Not in any total |
| `hill` | Hill Risk points |

The people figures are an upper bound for two reasons: about 14% of open low ground away from reported flooding is also flagged by the rule, and living within 100 m of a flooded field does not mean a home was flooded.

<!-- TODO(hackathon): settlement points source for the village list (e.g. HDX populated places) -->

## 6. Hill Risk layer

A **possible landslide — check on the ground** flag needs all of:

| Input | Rule | Starting value |
| --- | --- | --- |
| Slope from Copernicus DEM GLO-30 | Steep enough to fail | ≥ 15° |
| GPM IMERG daily rainfall, 5–18 Jul 2026 | Heavy accumulated rain | Set at hackathon |
| LHASA near-real-time nowcast | Moderate or high hazard on any day in the window | — |
| NISAR GCOV change on the slope | Clear before/during backscatter change | Set at hackathon |

The NASA Global Landslide Catalog export runs from 1988 to September 2017 (its 38 events in the grid date from 2007 to 2017) and is used only as historical context. The 5–18 Jul window is the period of heavy rain given in UN Sit Rep #2.

Layover and shadow are **not** masked out: the GCOV `mask` layer marks valid and invalid samples only (see section 2), so steep slopes facing towards or away from the radar can show changes that are not real. Because of this, and because scars are only a few pixels wide, this layer produces **places to inspect, never detections**.

## 7. Outputs

| Output | Format | Audience |
| --- | --- | --- |
| Hidden-flood overlay | Cloud-Optimised GeoTIFF + PNG tiles | Map viewers |
| Swipe map | Web (MapLibre GL JS) | Everyone |
| Upazila statistics | `stats.json`, GeoJSON | Web app, AI assistant |
| Likely-missed villages | CSV, KML | Relief organisations |
| Hill Risk points | GeoJSON, CSV | Local responders |

The AI assistant (Bangla/English) is given `stats.json`, `risk.json` and `model_comparison.json` as its only source of numbers. If the numbers do not answer a question, it says so.

## 8. Validation

What was checked, and where the numbers are:

| Check | Result | File |
| --- | --- | --- |
| Does NISAR on 12 July see the open floodwater C-band mapped on 16 July? | Yes: HH dropped by 3 dB or more on 73% of new open-water cells, against 6% of control cells | `outputs/openwater_check.csv` |
| Which dark level works? | −14 dB gives the best balance | `outputs/openwater_rule_sweep.csv` |
| Is the darkening where floods were reported? | Yes: twice as common on cropland in the reported upazilas, 23% against 5% around reported and unreported test points, and more than halved by 19 July | `outputs/peak_flood_check.csv` |
| Is there an under-tree signal? | Not shown: no feature reaches an AUC of 0.75 on both train and test sites | `outputs/grove_signal.csv`, `outputs/grove_models.csv` |
| Does a classifier beat the open-flood rule? | No. The classifiers score higher in spatial cross-validation (tuned F1 0.85–0.87 against 0.77) but flag 480–569 km² against the rule's 221 km², and 10–17% of open ground near test points with no flood report against the rule's 0.6%. The map keeps the rule; see section 11 | `outputs/flood_model_comparison.csv` |

Label sites and their sources are described in `labels/README.md`. No field visit or geolocated photo was used; the report-based test sites are union-level.

## 9. Known limits

- NISAR July 2026 products are **provisional**: calibrated, partially validated.
- 12-day revisit per track: the flood peak may fall between passes.
- WorldCover dates from 2020–21.
- L-band is weaker than C-band over short crops such as rice; MeghBhed complements C-band maps.
- Landslide scars can be only a few pixels wide.
- All outputs are labelled "likely" or "possible", never certain.
- The open-flood rule also flags about 14% of open low ground away from reported flooding; it cannot separate flood from freshly flooded paddy cell by cell.
- The flood pass (12 July) and the C-band map (16 July) are four days apart, so "missed" partly measures drainage between the two dates.
- Flood under tree cover is not mapped: the under-tree test gave no usable signal (section 3.2).
- The study area is Chattogram district only. Feni is not in the UN list of affected districts and is not reported.

## 10. Risk maps

Two maps answer "where is it likely?", not "where did it happen?". Both are **likelihood (susceptibility) maps, not forecasts**: no rainfall forecast or river level goes in. They are shown in the app as separate layers, off by default, and their people figures are kept apart from the observed flood.

### 10.1 Flood risk on open land

`pipeline/11_flood_risk.py`. How likely is a 30 m cell to flood in rain like July 2026?

**Target.** Flooded on 12 July = labels 1 or 2 of the comparison map (section 4). The model is trained on **one flood**, and only on open land (under half tree cover) where the flood map is valid. June water and WorldCover water, wetland and mangrove are left out.

**Inputs: terrain only** (no land cover, radar or rainfall), at 30 m: HAND and its minimum within 90 m; elevation and its minimum within 90 m; slope; local relief (elevation minus the mean within 1 km); distance to June water; distance to the coast.

**Ground under trees.** The DEM is a surface model, so canopy makes groves look higher than the ground. Under tree cover, elevation and HAND are replaced by the mean of the open land within 300 m, and slope and relief are recomputed from that. Tree-covered cells with no open land within 300 m get no score.

**Models.** Logistic regression (standardised), Random Forest and LightGBM, on about 300,000 cells sampled evenly across 5 km blocks.

| Check | Logistic regression | Random Forest | LightGBM |
| --- | --- | --- | --- |
| 5 km spatial cross-validation, AUC | 0.8407 | 0.8839 | 0.8809 |
| Brier score (baseline 0.0924) | 0.0770 | 0.0685 | 0.0696 |
| Calibration gap | 0.0101 | 0.0050 | 0.0128 |
| Leave one upazila out, mean AUC (six upazilas) | 0.8647 | 0.8525 | 0.8360 |
| Leave one upazila out, lowest AUC | 0.827 | 0.754 | 0.704 |
| AUC against the 19 July flood (**the same event** a week later) | 0.7993 | 0.8262 | 0.8207 |
| Mean risk near flooded test points / near no-report test points | 0.1322 / 0.0640 | 0.1654 / 0.0399 | 0.1706 / 0.0379 |

The Random Forest is used: best spatial cross-validation AUC, and well calibrated. Logistic regression holds up better when a whole upazila is left out, which suggests the tree models partly learn where this flood was.

**Classes**, set from the cross-validated calibration:

| Class | Risk score | Share of such cells that flooded on 12 July (cross-validation) |
| --- | --- | --- |
| Low | under 0.0985 | 2.3% |
| Medium | 0.0985 to 0.3125 | 19.1% |
| High | 0.3125 to 0.4845 | 39.7% (about 1 in 3 or more) |
| Very high | 0.4845 and above | 62.0% (1 in 2 or more) |

**The tree-cover check, and why the map covers open land only.** With the ground estimate, tree-covered land scores much closer to open land at the same ground HAND than before (`outputs/flood_risk_canopy_check.csv`):

| Ground HAND | Tree-covered against open land |
| --- | --- |
| 0 to 1 m | 0.49 times |
| 1 to 2 m | 1.19 times |
| 2 to 3.5 m | 0.92 times |
| 3.5 to 5 m | 0.50 times |

The rule set in advance was 0.5 to 1.5 times in every band. The lowest band, which holds most of the flood risk, misses it at 0.49. So the map and its people figures are **restricted to open land** and labelled "Flood risk on open land". High or very high risk covers 205.4 km² of open land with 265,921 people. **That people figure is a lower bound**: most people live under tree cover, which is not scored.

**What drives it.** SHAP values (TreeExplainer; plots in `outputs/xai/`) rank slope first, then elevation, distance to the coast, distance to June water and HAND. Flat, low ground scores highest. Risk rising with distance from the coast and from June water is specific to this flood.

**Limits.** One flood. Open land only. The 19 July check is the same event, and the test points are union-level reports. Susceptibility, not a forecast.

### 10.2 Landslide risk

`pipeline/12_landslide_risk.py`. A susceptibility class for every 30 m cell that counts as slope.

**What counts as slope.** A slope of 5° or more **and** a rise of 20 m or more within 300 m. In built-up cells the slope is taken from a lightly smoothed DEM. Without these two rules, buildings on flat land looked like slopes: steep land fell from 1,467 to 1,215 km², and Patenga, Double Mooring, Halishahar, Chittagong Port, Bakalia and Pahartali no longer have any.

**No model is trained.** NASA's Global Landslide Catalog export (11,033 events, 1988–2017) has 38 points in the grid and 19 in the district, all from 2007–2017. That is under the 40 set as the minimum, and most are located only to within 5–25 km. The newer COOLR catalogue could not be fetched. The map is a **weighted index**:

| Factor | Weight | Score from 0 to 1 | Why |
| --- | --- | --- | --- |
| Slope | 0.40 | 0 at 5°, 1 at 35° or more | The one factor every landslide needs |
| Relief within 300 m | 0.20 | 1 at 150 m or more | Long, high slopes |
| Rain, 5–18 July (IMERG) | 0.20 | 0 at 300 mm, 1 at 700 mm | The trigger in this event |
| Land cover | 0.10 | Bare 1.0, built-up 0.8, cropland 0.7, other 0.6, tree 0.4 | Roots hold soil; cut and bare slopes do not |
| Nearness to built-up land | 0.10 | 1 next to buildings, 0 at 500 m | A stand-in for hill cutting |

The weights are a judgement, not fitted to data. Classes are **ranks** within the district's slopes: very high = top 5%, high = next 15%, medium = next 30%, low = the rest. So 20% is high or very high by construction.

| Check | Result |
| --- | --- |
| Hill Risk radar sites (36) | 55.6% fall in high or very high, 63.9% within 100 m of it, against 20%. Not independent: both use slope and the same rainfall |
| Catalog points in the district (19) | The slopes around them are 38.8% high or very high on average; 17 of 19 are above 20%. The four located to 1 km average 46.0% |
| Places named in the July reports | Within 1 km of Chattogram City wards 7, 8, 9 and 14: 44.6%, 47.3%, 69.3% and 50.5%. Banshkhali upazila: 36.2%. All above 20%. Ward locations are geocoded points, not boundaries |
| LHASA nowcast maximum | Covers 32.6% of the slopes; rank correlation with the index 0.544 |
| NASA global susceptibility map (1 km) | Rank correlation 0.268 |

946,370 people live within 100 m of high or very high slopes; Khulshi, Bayejid Bostami, Kotwali, Sitakunda and Panchlaish lead.

**Limits.** A judgement-weighted index, not a trained or validated model. Canopy still adds some false slope. Rainfall cells are about 10 km wide; no geology, soil or road-cut data. Susceptibility, not a forecast.

## 11. Benchmark models for the open flood

`pipeline/10_flood_models.py` asks whether a trained classifier maps the 12 July open flood better than the rule of section 3.1. It is an evaluation; it does not change the map.

**Task.** Label a 30 m cell as open flood or not, from NISAR radar alone: HH and HV before and during, HH change, HV change, and HH minus HV during. No HAND, slope or texture.

**Training cells** (95,091 in all):

| Set | Cells | What it is |
| --- | --- | --- |
| Positive | 26,206 | New open water on the C-band map: water on 16 July, on no June date, non-tree, low ground |
| Negative (a) | 8,885 | Non-tree ground on HAND 8–40 m with slope under 5° (cannot flood) |
| Negative (b) | 30,000 | Open water on every June date (permanent water: dark, but not new) |
| Negative (c) | 30,000 | Low non-tree ground seen through the no-flood pair 18 June → 30 June |

**Models.** The threshold rule; logistic regression (standardised, balanced class weights); Random Forest; LightGBM.

**Validation.** 5 km spatial cross-validation, pooled over held-out folds.

**Cut-off tuning.** The default cut-off is a probability of 0.5. The tuned cut-off is the precision–recall break-even point (precision equals recall). Tuning is **nested**: inside each fold the cut-off is picked on that fold's training data only (inner spatial split), then applied to the held-out fold. A final cut-off is fitted on all the training data for use on a map (logistic regression 0.5504, Random Forest 0.5645, LightGBM 0.6091).

| Model | Cut-off | Precision | Recall | F1 | Accuracy | Largest gap among the three | ROC AUC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rule | as it stands | 0.9190 | 0.6555 | 0.7652 | 0.8891 | 0.2635 | — |
| Logistic regression | default | 0.8189 | 0.8696 | 0.8435 | 0.9111 | 0.0507 | 0.9641 |
| Logistic regression | tuned, nested | 0.8575 | 0.8474 | 0.8524 | 0.9191 | 0.0100 | 0.9641 |
| Random Forest | default | 0.8365 | 0.8783 | 0.8569 | 0.9192 | 0.0418 | 0.9690 |
| Random Forest | tuned, nested | 0.8821 | 0.8454 | 0.8634 | 0.9263 | 0.0367 | 0.9690 |
| LightGBM | default | 0.8378 | 0.8967 | 0.8663 | 0.9237 | 0.0590 | 0.9724 |
| LightGBM | tuned, nested | 0.8954 | 0.8551 | 0.8748 | 0.9325 | 0.0402 | 0.9724 |

**Against the targets** (precision, recall and F1 within 0.001 of each other; accuracy of 90% or more):

- Accuracy: all three classifiers pass at every cut-off. The rule does not (88.91%).
- The 0.001 gap: **not met** with nested tuning. The best is logistic regression at 0.0100. The break-even cut-off differs from fold to fold (LightGBM's ranges from 0.60 to 0.77), so a cut-off chosen on four-fifths of the area does not land exactly on break-even in the rest.
- The **precision-recall break-even point on cross-validated predictions** gives a gap of 0.0000 (logistic regression 0.8539, Random Forest 0.8642, LightGBM 0.8753). Precision, recall and F1 are equal there **by definition**: the cut-off is placed where they meet, on the same predictions it is scored on. It is not a tuned threshold tested on unseen data, and it is reported as its own labelled row, apart from the default and the fold-tuned cut-offs.
- The rule would reach break-even at about a 2.0 dB drop and a −11.5 dB level (precision = recall = 0.80, accuracy 0.8897); see `outputs/flood_rule_break_even.csv`.

**Independent tests** (report-based sites, never used to train or tune; tuned rows use the final cut-off):

| Model | Area flagged | Flagged near reported-flooded points | Flagged near no-report points | Cropland flagged, reported upazilas | Cropland flagged, other upazilas |
| --- | --- | --- | --- | --- | --- |
| Rule | 221 km² | 27.5% | 0.6% | 26.0% | 15.0% |
| Logistic regression, tuned | 569 km² | 50.6% | 17.1% | 57.0% | 43.6% |
| Random Forest, tuned | 480 km² | 43.7% | 9.7% | 48.1% | 37.3% |
| LightGBM, tuned | 553 km² | 47.2% | 14.0% | 54.0% | 43.8% |

**Conclusion.** LightGBM is the best benchmark by AUC, F1 and accuracy. But the classifiers are trained to reproduce what C-band saw four days later, and on the independent tests they flag two to three times the rule's area, including 10–17% of open ground near places with no flood report against the rule's 0.6%. Tuning the cut-off changes that by under 10%. **The map keeps the rule.**

**What the models look at (SHAP).** TreeExplainer on 5,000 cells for LightGBM and 500 for the Random Forest (`outputs/flood_shap_importance.csv`, plots in `outputs/xai/`). HV change ranks first in both: a fall in HV marks flood. HH change is second in the Random Forest; HV before is second in LightGBM. The logistic coefficients are large and of opposite sign on the before and during levels, so that model too is reading change. Two waterfall examples are saved: a cell every model flags near a reported-flooded point, and a false alarm near a no-report point where HH fell 4.4 dB to −13.9 dB, which the rule misses by 0.1 dB on the level.

## 12. Under trees again: the coherence test

`pipeline/13_tree_flood.py`. Backscatter brightness did not show flooding under village groves (section 3.2). Interferometric coherence looked more promising: a grove standing in water should lose more coherence between two passes than a dry one. The test was run with **pass criteria fixed in advance**, and the layer **did not pass**, so it is not on the map.

**Feature.** Coherence (30 June → 12 July) minus coherence (18 → 30 June), HH, from the two NISAR GUNW files in `data/nisar_gunw/`, on the 30 m grid. The change on high forest (HAND over 20 m) is subtracted; a scene-wide median did as well as a local one within 10 km, and averaging over tree cells within 150 m did better than 90 m (train AUC 0.8047 against 0.7853). Both choices were made on the train sites only.

**Eligible cells.** At least half tree cover, inside the district, not WorldCover 80/90/95, before-flood coherence of 0.3 or more, and a ground HAND of 5 m or less estimated from the open land within 300 m: 1,576 km² of the 2,737 km² of tree cover.

**Threshold.** The coherence loss that 10% of dry train sites exceed: a change of −0.0752 or lower.

| Criterion (set in advance) | Result | Pass |
| --- | --- | --- |
| Test AUC of 0.75 or more | 0.7998 | Yes |
| Test recall of 40% or more, with test false alarms of 15% or less | Recall 4.8%, false alarms 0% | **No** |
| Share passing within 100 m of new floodwater at least twice the share beyond 1 km | 18.07% against 7.26% (2.49 times) | Yes |
| Share passing higher in the reported upazilas than in the others | 10.17% against 16.74% | **No** |

**What this means.** Coherence loss does rank flooded groves above dry ones in both the train and the test areas (AUC 0.80), and it does fall away with distance from floodwater. But the size of the loss differs from area to area, so one threshold set on the train sites catches almost none of the test sites, and across the district more tree cover passes outside the reported upazilas than inside them. Train recall in cross-validation was 21.6% at 12.3% false alarms.

Models using coherence and backscatter change together score well on the train sites (AUC 0.94 to 0.96) and worse on the test sites (logistic regression 0.77, Random Forest 0.65, LightGBM 0.62); none is clearly better than the simple rule there (`outputs/tree_flood_models.csv`).

Flood under tree cover therefore stays **unverified**: there is a real signal in coherence, but not one that can be turned into a map with a single threshold from one pair of passes.
