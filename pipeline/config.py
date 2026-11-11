"""MeghBhed pipeline settings. Edit this file, not the scripts.

Every threshold here is a STARTING value from docs/METHOD.md. Tune them on the
label sites (labels/sites.csv) and write the final values back into METHOD.md.
"""
from pathlib import Path

# ---------------------------------------------------------------- folders
ROOT = Path(__file__).resolve().parent.parent      # repo root
DATA = ROOT / "data"                                # output of download_meghbhed_data.sh
WORK = ROOT / "work"                                # intermediate rasters (git-ignored)
OUT = ROOT / "outputs"                              # final products
LABELS = ROOT / "labels" / "sites.csv"              # Eva's flooded / dry sites
WEB_DATA = ROOT / "web" / "public" / "data"         # where the app reads real results

# ---------------------------------------------------------------- study area
DISTRICTS = ["Chattogram"]                          # reported districts (Feni is not in the UN list of affected districts)
GRID_DISTRICTS = ["Chattogram", "Feni"]             # keeps the grid unchanged, so earlier outputs still line up
DISTRICT_ALIASES = {"Chattogram": ["Chattogram", "Chittagong"], "Feni": ["Feni"]}
BUFFER_M = 2000                                      # buffer around the districts
CRS = "EPSG:32646"                                   # WGS 84 / UTM 46N, metres
RES = 10                                             # analysis grid (m), = GCOV freq A at 40 MHz
RES_CMP = 30                                         # comparison grid (m), = DSWx-S1

# ---------------------------------------------------------------- NISAR scenes
# role -> granule name (file is data/nisar/<granule>.h5)
SCENES = {
    "A_before": "NISAR_L2_PR_GCOV_024_069_A_013_4005_DHDH_A_20260630T232101_20260630T232135_P05023_N_F_J_001",
    "A_during": "NISAR_L2_PR_GCOV_025_069_A_013_4005_DHDH_A_20260712T232100_20260712T232135_P05023_N_F_J_001",
    "B_before": "NISAR_L2_PR_GCOV_023_163_D_077_4005_DHDH_A_20260625T122638_20260625T122713_P05023_N_F_J_001",
    "B_during": "NISAR_L2_PR_GCOV_025_163_D_077_4005_DHDH_A_20260719T122637_20260719T122711_P05023_N_F_J_001",
    # Feni pair (track 91, 20 MHz mode). Used automatically when both files are in data/nisar/.
    "C_before": "NISAR_L2_PR_GCOV_024_091_D_077_2005_DHDH_M_20260702T123457_20260702T123531_P05023_N_F_J_001",
    "C_during": "NISAR_L2_PR_GCOV_025_091_D_077_2005_QPDH_A_20260714T123456_20260714T123512_P05023_F_P_J_001",
}
SCENES["A_before2"] = "NISAR_L2_PR_GCOV_023_069_A_013_4005_DHDH_A_20260618T232102_20260618T232136_P05023_N_F_J_001"   # 18 Jun
SCENES["A_after"] = "NISAR_L2_PR_GCOV_028_069_A_013_4005_DHDH_A_20260817T232058_20260817T232133_P05023_N_F_J_001"     # 17 Aug
PAIRS = {"A": ("A_before", "A_during"), "B": ("B_before", "B_during"), "C": ("C_before", "C_during")}
# Optional extra scenes per pair, used when their files exist:
#   before2 = a second "before" (averaged with the first, for a steadier baseline)
#   after   = a scene after the water drained (flood must be brighter than this too)
EXTRA = {"A": {"before2": "A_before2", "after": "A_after"}}
PRIMARY_PAIR = "A"      # the pass taken during the flood (12 Jul); the comparison with C-band uses this pair
ALL_SCENES = dict(SCENES)
for _p in list(EXTRA):
    for _k, _r in list(EXTRA[_p].items()):
        if not (DATA / "nisar" / f"{SCENES[_r]}.h5").exists():
            del EXTRA[_p][_k]
            SCENES.pop(_r)
for _p, (_b, _d) in list(PAIRS.items()):      # drop pairs whose files are not downloaded
    if not all((DATA / "nisar" / f"{SCENES[_r]}.h5").exists() for _r in (_b, _d)):
        del PAIRS[_p]
        SCENES.pop(_b), SCENES.pop(_d)

FREQ = "frequencyA"
GCOV_GROUP = "/science/LSAR/GCOV/grids"
# GCOV 'mask' values treated as invalid. CHECK with 00_inspect.py and the
# GCOV product specification before trusting this; then edit.
MASK_INVALID = {0, 255}

# ---------------------------------------------------------------- preprocessing
LEE_WINDOW = 5          # speckle filter window (pixels); same for every date
LEE_LOOKS = 4.0         # rough equivalent number of looks, used by the Lee filter

# ---------------------------------------------------------------- detection (METHOD.md §3)
TREE_CLASS = 10         # WorldCover tree cover
BUILT_CLASS = 50        # WorldCover built-up
BUILT_BUFFER_PX = 1
T_HH = 3.0              # ΔHH must be >= this (dB)
T_HV = 1.0              # ΔHV must be <= this (dB)
OPEN_RADIUS = 1         # morphological opening radius (px)
MIN_PATCH_PX = 9        # remove flagged patches smaller than this (900 m²); village groves are small
T_AFTER = 1.5           # with an "after" scene: HH during must also exceed HH after by this (dB)

# Noise control (added after the first real run found only speckle):
MULTILOOK_PX = 5        # average backscatter over a 5x5 window (50 m) before differencing
BIAS_CORRECT = True     # subtract the scene-wide ΔHH/ΔHV measured on high forest that cannot flood
HAND_MAX_M = 15.0       # flood only where the ground is within 15 m of the nearest river
EXCLUDE_CLASSES = {80, 90, 95}   # WorldCover permanent water, wetland, mangrove (tides, not flood)
CLIP_TO_DISTRICTS = True         # ignore sea, tidal flats and hill tracts outside the two districts

# Open flood ("newly dark"): the headline flood map. Non-tree land on low ground that went dark.
# -14 dB was chosen from outputs/openwater_rule_sweep.csv: it keeps about two thirds of the new open
# water C-band mapped on 16 Jul and halves the false flags on cropland far from any water.
DARK_DB = -14.0         # HH on the flood date at or below this = dark (open water)
DARK_DROP = -3.0        # and HH dropped at least this much
OPEN_HAND_MAX_M = 5.0   # open flood only on ground within 5 m of the nearest river
OPEN_MIN_PATCH_HA = 1.0         # 30 m flood patches smaller than this are dropped (scattered wet fields)
CONSERVATIVE_PATCH_HA = 5.0     # the conservative people figure counts only missed-flood patches this large
PEOPLE_BUFFER_M = 100           # people living within this distance of flood cells
DRAIN_PAIR = "B"                # a later pass (19 Jul): flood cells no longer dark there "drained within a week"
# The under-tree HH-rise rule above is kept, but its output is "under trees, unverified": tests against
# independent sites found no radar feature that separates flooded from dry groves (see docs/METHOD.md).
# It never feeds a headline total.

DETECTOR = "threshold"  # "threshold" or "ml" (after 05_classify.py has run)

# ---------------------------------------------------------------- comparison (METHOD.md §4)
AGG_FRACTION = 0.5      # a 30 m cell is flagged if >= 50% of its 10 m pixels are
COMPARE_RULE = "primary"  # "primary": the flood pass (PRIMARY_PAIR) vs C-band; "two_date": every covering pair must agree
# DSWx-S1 WTR band: 0 not water, 1 open water, 3 inundated vegetation,
# 250 masked (HAND too high), 251 masked (layover/shadow), 255 fill.
# DSWx-S1 does try to map flooded vegetation (class 3), so count it as water.
DSWX_WATER = {1, 3}
DSWX_NODATA = {250, 251, 252, 253, 254, 255}
DSWX_TILES = ["T46QCK", "T46QCL", "T46QDK", "T46QDL"]

# ---------------------------------------------------------------- Hill Risk (METHOD.md §6)
SLOPE_DEG = 15.0
RAIN_MM = 300.0         # 5-18 Jul accumulated IMERG rain, tune at hackathon
USE_LHASA = False       # LHASA misses 10-12 Jul and covers ~16% of the area: record it, do not require it
LHASA_MIN = 0.3         # only used when USE_LHASA = True
HILL_HV_DROP_DB = 3.0   # HV must DROP by this much: vegetation stripped off the slope
HILL_MIN_PX = 25        # 0.25 ha

# ---------------------------------------------------------------- classifier (05_classify.py)
FEATURES = ["hh_b", "hv_b", "hh_d", "hv_d", "dhh", "dhv", "ratio_d", "tex_hh", "slope", "hand"]
SITE_RADIUS_M = 30      # pixels within this radius of a label point are used
AUTO_DRY_HAND_M = 20.0  # tree pixels this high above the river are auto-labelled dry
AUTO_DRY_N = 4000
BLOCK_M = 5000          # spatial cross-validation block size
RANDOM_SEED = 42
ML_PROB = 0.5           # classifier probability needed to flag a pixel
ML_MIN_DHH = 1.0        # physics guard: HH must still rise at least this much (dB)
