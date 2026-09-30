# MeghBhed method

> [!IMPORTANT]
> This is the **planned** method. No code exists yet; it will be written at the hackathon (13–14 Nov 2026). Thresholds below are starting values for tuning, not results.

## Contents

- [1. Study area and dates](#1-study-area-and-dates)
- [2. Preprocessing](#2-preprocessing)
- [3. Hidden-flood detection](#3-hidden-flood-detection)
- [4. Fair comparison with C-band](#4-fair-comparison-with-c-band)
- [5. People and upazila statistics](#5-people-and-upazila-statistics)
- [6. Hill Risk layer](#6-hill-risk-layer)
- [7. Outputs](#7-outputs)
- [8. Validation](#8-validation)
- [9. Known limits](#9-known-limits)

## 1. Study area and dates

**Version 1:** Chattogram and Feni districts, Bangladesh. **Next:** haor wetlands, the Sundarbans, and flooded forests elsewhere.

Chattogram was the most affected district in the July 2026 floods, with 785,400 people affected ([UN Sit Rep #2, 23 Jul 2026](https://bangladesh.un.org/en/319868-bangladesh-situation-report-2-flash-flood-and-landslides-23-july-2026)).
<!-- VERIFY: source for July 2026 flood impact in Feni; Feni is not among the seven districts in Sit Rep #2 -->

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
6. **Mask** layover, shadow and invalid pixels using the GCOV `mask` layer.
7. **Co-register:** both dates of a pair share a track and a geocoding grid, so no resampling is expected between them. <!-- VERIFY(hackathon) -->

GCOV frequency A is posted at 10 m for 40 MHz modes ([ASF GCOV guide](https://nisar-docs.asf.alaska.edu/gcov/)). WorldCover is 10 m; DSWx-S1 is 30 m; WorldPop is 100 m.

## 3. Hidden-flood detection

For each pixel inside the analysis mask:

| Step | Rule | Starting value |
| --- | --- | --- |
| Land-cover mask | ESA WorldCover 2021 class **10 (tree cover)** only | — |
| Exclusion | WorldCover class **50 (built-up)** removed, with a small buffer | 1 pixel |
| Double-bounce test | ΔHH = HH<sub>during</sub> − HH<sub>before</sub> ≥ T<sub>HH</sub> | T<sub>HH</sub> = +3 dB |
| Canopy-change test | ΔHV ≤ T<sub>HV</sub> | T<sub>HV</sub> = +1 dB |
| Clean-up | Remove isolated pixels (morphological opening, minimum patch size) | Set at hackathon |

**Why these tests.** Water under trees creates a water–trunk double bounce, which raises HH strongly. Volume scattering from the canopy mainly drives HV. A rise in HH without a matching rise in HV therefore points to water below, not to more leaves above ([Tsyganskaya et al., 2018](https://doi.org/10.1080/01431161.2017.1420938); [Refice et al., 2020](https://doi.org/10.3390/w12102745)).

**Calibration plan.** Pick known dry forest and known flooded homesteads, using news photos and UN reports, and adjust T<sub>HH</sub> and T<sub>HV</sub> to separate them. <!-- TODO(hackathon): record final thresholds and calibration sites here -->

Open water (dark in both dates or newly dark) is **not** MeghBhed's focus; C-band maps already handle it well.

## 4. Fair comparison with C-band

The comparison is made on the 30 m DSWx-S1 grid. NISAR flags are aggregated to 30 m first. <!-- TODO(hackathon): choose the aggregation rule, e.g. majority of 10 m pixels -->

A 30 m cell is **missed by C-band** only when:

1. pair A (30 Jun → 12 Jul) flags hidden flood, **and**
2. pair B (25 Jun → 19 Jul) flags hidden flood, **and**
3. DSWx-S1 on 16 Jul classifies it as not water (the C-band pass falls between the two NISAR dates).

Cells where DSWx-S1 has no valid data (for example, masked or low confidence) are left out of the comparison, not counted as "missed".

| NISAR pair A | NISAR pair B | DSWx-S1 16 Jul | Label |
| --- | --- | --- | --- |
| Flood | Flood | Not water | **Likely missed by C-band** |
| Flood | Flood | Water | Seen by both |
| Flood | No flood | Any | Possibly flooded (one date) |
| Flood | No coverage | Any | Possibly flooded (single track) |
| No flood | No flood | Any | Not flagged |

## 5. People and upazila statistics

1. Overlay flagged cells with **WorldPop** 100 m population counts. Each WorldPop cell contributes in proportion to its flagged area.
2. Sum by **upazila** (HDX COD-AB, admin level 3).
3. Write per upazila: hidden-flood area (km²), people in hidden-flood areas, people in "likely missed by C-band" areas, and confidence level.
4. Export `stats.json` for the web app and AI assistant, and a CSV/KML list of likely-missed settlements.

<!-- TODO(hackathon): settlement points source for the village list (e.g. HDX populated places) -->

## 6. Hill Risk layer

A **possible landslide — check on the ground** flag needs all of:

| Input | Rule | Starting value |
| --- | --- | --- |
| Slope from Copernicus DEM GLO-30 | Steep enough to fail | ≥ 15° |
| GPM IMERG daily rainfall, 5–18 Jul 2026 | Heavy accumulated rain | Set at hackathon |
| LHASA near-real-time nowcast | Moderate or high hazard on any day in the window | — |
| NISAR GCOV change on the slope | Clear before/during backscatter change, outside layover/shadow | Set at hackathon |

The NASA Global Landslide Catalog ends in 2016 and is used only as historical context. The 5–18 Jul window is the period of heavy rain given in UN Sit Rep #2.

Because of layover and shadow in hilly terrain, and scars only a few pixels wide, this layer produces **places to inspect, never detections**.

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

- Compare flagged upazilas with those named in UN situation reports and flash updates.
- Check a sample of flagged sites against geolocated news photos.
- Report agreement honestly, including false alarms. <!-- TODO(hackathon): results table -->

## 9. Known limits

- NISAR July 2026 products are **provisional**: calibrated, partially validated.
- 12-day revisit per track: the flood peak may fall between passes.
- WorldCover dates from 2020–21.
- L-band is weaker than C-band over short crops such as rice; MeghBhed complements C-band maps.
- Landslide scars can be only a few pixels wide.
- All outputs are labelled "likely" or "possible", never certain.
