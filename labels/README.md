# Label sites

`sites.csv` holds the flooded and dry sites used to train and test the classifier in `pipeline/05_classify.py`.

**The labels are independent of the NISAR results.** No NISAR backscatter, flood map, comparison map or quick-look was read while building them. NISAR is used only afterwards, to evaluate.

## Columns

| Column | Meaning |
| --- | --- |
| `lon`, `lat` | Site centre, WGS84. The classifier uses every 10 m pixel within 30 m of it. |
| `label` | 1 = flooded under trees, 0 = dry |
| `pairs` | NISAR pair the label applies to: `A` (the 12 July flood pass) for flooded sites, empty (all pairs) for dry sites |
| `source` | `DSWx-S1 new floodwater` for train rows; the report URL for test rows |
| `set` | `train` (satellite-derived) or `test` (report-derived, never used for training) |
| `place` | Reported place name (test rows only) |
| `upazila` | Upazila the point falls in |
| `confidence` | `medium` or `low`, see below |
| `note` | How the site was chosen |

## Train sites: satellite-derived (319 sites: 74 flooded, 245 dry)

### Reference layer: new floodwater

Built from OPERA DSWx-S1 (Sentinel-1 C-band) water maps only, on the 30 m grid, tiles T46QCK, T46QCL, T46QDK, T46QDL.

- Flood date: 16 July 2026.
- Pre-flood dates: 7, 9, 19 and 21 June 2026 (the only dates between 1 June and 4 July that cover all four tiles). Files are in `data/dswx_s1_pre/`.
- **New floodwater** = water (class 1 open water or class 3 inundated vegetation) on 16 July, and not water on any of the four pre-flood dates, and no WorldCover class 80, 90 or 95 (permanent water, wetland, mangrove) anywhere in the 30 m cell.
- Saved as `work/aux/new_floodwater_30m.tif` (0 none, 1 new open water, 3 new flooded vegetation, 255 no data).
- Inside the Chattogram upazilas: 53.4 km² of new floodwater (23.7 km² open water, 29.7 km² flooded vegetation). That is 23% of the 237.2 km² of water mapped on 16 July; 72% was already water on at least one June date and 5% is WorldCover water, wetland or mangrove.

The UNOSAT flood-extent product of 22 July 2026 (Charter activation 1042) was searched for on the Charter site, unosat.org and HDX. No downloadable vector was found, so it is not used.

### Flooded under trees (label 1)

A 10 m pixel is a candidate when it is

- WorldCover tree cover (class 10),
- on HAND of 5 m or less,
- inside Chattogram district,
- and at least half of the non-tree land within 100 m is new floodwater ("tree islands in floodwater"). "Within 100 m" is a 210 m square window; non-tree land excludes WorldCover permanent water and must be at least 10% of the window.

43,245 candidate pixels in 898 groves.

### Dry (label 0)

A 10 m pixel is a candidate when it is WorldCover tree cover, on HAND of 5 m or less, inside the district, and has no DSWx-S1 water of any kind within 1 km, neither on 16 July nor on any of the four June dates. Cells with no DSWx observation count as water.

259,392 candidate pixels in 1,273 groves.

### Sampling

- A site must be a candidate pixel whose whole 70 m × 70 m neighbourhood is also candidate, so the 30 m disc the classifier samples stays inside the grove. This leaves 625 flooded and 24,806 dry pixels.
- Up to 400 sites per label, at least 150 m apart, at most 10 per 5 km block, random order with a fixed seed.
- Result: 76 flooded and 245 dry sites. Two flooded sites within 1 km of a test point were removed, leaving 74.

### What these labels can and cannot say

- A flooded label means C-band saw new water around the grove, not under it. Water under the canopy is inferred.
- The reference is 16 July; NISAR pair A is 12 July. Water may have risen or fallen in the four days between.
- Dry sites are far from all mapped water, so they are the easy kind of dry. Dry groves close to floodwater are not represented.
- Confidence is `medium` for all train rows.

## Test sites: report-derived (84 points: 42 flooded, 42 dry)

These rows are never used for training or cross-validation.

### Flooded (label 1, confidence medium)

Unions named as submerged or worst-hit in reports of 10–12 July 2026:

| Upazila | Places | Source |
| --- | --- | --- |
| Satkania | Bajalia, Keochia, Chadaha, Kaliaish, Dharmapur, Nalua | [The Business Standard, 10 July 2026](https://www.tbsnews.net/bangladesh/floods-leave-over-75-lakh-people-marooned-ctg-1484941); confirmed by [BSS, 12 July 2026](https://www.bssnews.net/others/404930) |
| Banshkhali | Baharchhara, Saral, Gunagari | same two reports |
| Banshkhali | Napora | [bdnews24, 10 July 2026](https://bdnews24.com/bangladesh/eda23461240f) |
| Lohagara | Amirabad, Adhunagar, Padua, Lohagara | [bdnews24, 10 July 2026](https://bdnews24.com/bangladesh/eda23461240f) |

A union reported submerged does not mean a particular grove was flooded. Thirteen other named places could not be geocoded inside the right upazila and were dropped.

### Dry (label 0, confidence low)

No report names any place in the district as unaffected, and one report says all 15 upazilas were affected. The dry test places are low-lying places with **no place-level flood report** in any source searched: Zorarganj, Durgapur, Hinguli, Wahedpur, Mayani (Mirsharai); Barabkunda, Kumira, Bhatiari, Muradpur, Saidpur (Sitakunda); Gahira, Noapara (Raozan); Santoshpur, Bauria (Sandwip). Their upazilas were reported with general "low-lying areas" flooding or crop damage, so some of these points may have flooded.

### Geocoding and point selection

- Each place was geocoded with Nominatim (OpenStreetMap) and kept only if it fell inside the expected upazila.
- For each place, up to 3 points were picked within 500 m: WorldCover tree cover with a full 3 × 3 tree neighbourhood, HAND of 5 m or less, at least 150 m apart, closest first.

### Sources searched

- UN Situation Report #1, 13 July 2026; NAWG flash updates of 9 and 11 July 2026; BDRCS Sitrep 1, 7 July 2026. These name upazilas, city wards and roads only, so they gave no test points.
- The Business Standard (10 July), BSS (12 July), bdnews24 (10 July), Prothom Alo (13 July), Daily Observer (11 and 12 July), The Financial Express (19 July), The Daily Star via Asia News Network (15 July).
- UN Situation Report #2 (23 July) was not opened in full.

## Rebuilding

The scripts that built these labels are in `labels/build/`; they are not part of the pipeline, and `pipeline/05_classify.py` only reads `sites.csv`. Run from the repo root, in this order:

1. `python labels/build/build_reference.py .` builds the new-floodwater layer.
2. `python labels/build/train_sites.py .` selects and samples the train sites.
3. `python labels/build/geocode.py .` geocodes the report places listed in `places.py`.
4. `python labels/build/test_points.py .` picks the test points.
5. `python labels/build/write_sites.py .` merges both into `sites.csv`.
