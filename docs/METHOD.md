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
3. **Crop** to the district boundaries (HDX COD-AB, admin level 2) plus a small buffer.
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

The train result probably reflects landscape (near water against far from water), not flooding under the canopy. The test labels are also weak: union-level reports, and "no report" for dry. So the under-tree signal is **not shown**, not disproved. Point-level ground truth, or dry groves close to floodwater, would settle it.

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

Open flood is on fields, where few people live, so people are counted **within 100 m of flood cells**, using WorldPop spread onto the 30 m grid (`pipeline/08_stats.py`). Everything is summed by **upazila** (HDX COD-AB, admin level 3).

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

The NASA Global Landslide Catalog ends in 2016 and is used only as historical context. The 5–18 Jul window is the period of heavy rain given in UN Sit Rep #2.

Layover and shadow are **not** masked out: the GCOV `mask` layer marks valid and invalid samples only (see section 2), so steep slopes facing towards or away from the radar can show changes that are not real. Because of this, and because scars are only a few pixels wide, this layer produces **places to inspect, never detections**.

## 7. Outputs

| Output | Format | Audience |
| --- | --- | --- |
| Hidden-flood overlay | Cloud-Optimised GeoTIFF + PNG tiles | Map viewers |
| Swipe map | Web (MapLibre GL JS) | Everyone |
| Upazila statistics | `stats.json`, GeoJSON | Web app, AI assistant |
| Likely-missed villages | CSV, KML | Relief organisations |
| Hill Risk points | GeoJSON, CSV | Local responders |

The AI assistant (Bangla/English) is given `stats.json` as its only source of numbers. If the numbers do not answer a question, it says so.

## 8. Validation

What was checked, and where the numbers are:

| Check | Result | File |
| --- | --- | --- |
| Does NISAR on 12 July see the open floodwater C-band mapped on 16 July? | Yes: HH dropped by 3 dB or more on 73% of new open-water cells, against 6% of control cells | `outputs/openwater_check.csv` |
| Which dark level works? | −14 dB gives the best balance | `outputs/openwater_rule_sweep.csv` |
| Is the darkening where floods were reported? | Yes: twice as common on cropland in the reported upazilas, 23% against 5% around reported and unreported test points, and more than halved by 19 July | `outputs/peak_flood_check.csv` |
| Is there an under-tree signal? | Not shown: no feature reaches an AUC of 0.75 on both train and test sites | `outputs/grove_signal.csv`, `outputs/grove_models.csv` |
| Does a classifier beat the open-flood rule? | No. Random Forest and LightGBM score higher in spatial cross-validation (F1 0.86–0.87 against 0.77) but flag 514–605 km² against the rule's 221 km², including 40–48% of cropland in upazilas with no flood report, and 12–17% of open ground near test points with no flood report against the rule's 0.6%. The pipeline keeps the rule | `outputs/flood_model_comparison.csv` |

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
