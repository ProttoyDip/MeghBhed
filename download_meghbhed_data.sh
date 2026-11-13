#!/usr/bin/env bash
# MeghBhed — download every input dataset for the July 2026 Chattogram/Feni analysis.
# Links checked 5 Nov 2026 against ASF, NASA CMR, GES DISC and the AWS open buckets.
#
# Before running (NASA files only):
#   1. Make a free Earthdata login: https://urs.earthdata.nasa.gov
#   2. Put it in ~/.netrc (Windows: %USERPROFILE%\_netrc):
#        machine urs.earthdata.nasa.gov login YOUR_USERNAME password YOUR_PASSWORD
#      then: chmod 600 ~/.netrc
#   3. In your Earthdata profile > Applications > Authorized Apps, approve
#      "NASA GESDISC DATA ARCHIVE" (needed for the GPM rainfall files).
#
# Usage:
#   bash download_meghbhed_data.sh            # everything except the optional Feni pair
#   bash download_meghbhed_data.sh small      # everything except NISAR (fast, < ~1.5 GB)
#   bash download_meghbhed_data.sh nisar      # only the 4 NISAR scenes (~26.8 GB)
#   bash download_meghbhed_data.sh feni       # optional track-91 Feni pair (~5.9 GB)
# Re-running resumes partial files and skips finished ones.
set -euo pipefail
OUT="${OUT:-data}"
COOKIES="$HOME/.urs_cookies"; touch "$COOKIES"
WHAT="${1:-all}"

get() {  # get <subfolder> <url> [auth]
  local dir="$OUT/$1" url="$2" name; name="$(basename "${url%%\?*}")"
  mkdir -p "$dir"
  if [[ -s "$dir/$name.done" ]]; then echo "skip  $1/$name"; return; fi
  echo "get   $1/$name"
  if [[ "${3:-}" == auth ]]; then
    curl -fL --retry 5 --retry-delay 10 -C - -n -c "$COOKIES" -b "$COOKIES" -o "$dir/$name" "$url"
  else
    curl -fL --retry 5 --retry-delay 10 -C - -o "$dir/$name" "$url"
  fi
  date > "$dir/$name.done"
}

# ---------- 1. NISAR L2 GCOV (ASF, Earthdata login) — ~26.8 GB ----------
NISAR_BASE=https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1
NISAR=(
  NISAR_L2_PR_GCOV_024_069_A_013_4005_DHDH_A_20260630T232101_20260630T232135_P05023_N_F_J_001  # pair A before, 6.1 GB
  NISAR_L2_PR_GCOV_025_069_A_013_4005_DHDH_A_20260712T232100_20260712T232135_P05023_N_F_J_001  # pair A during, 6.3 GB
  NISAR_L2_PR_GCOV_023_163_D_077_4005_DHDH_A_20260625T122638_20260625T122713_P05023_N_F_J_001  # pair B before, 7.3 GB
  NISAR_L2_PR_GCOV_025_163_D_077_4005_DHDH_A_20260719T122637_20260719T122711_P05023_N_F_J_001  # pair B during, 7.1 GB
)
# Optional: track 91 covers Feni (track 163 does not). Same 20 MHz mode on both dates.
NISAR_FENI=(
  NISAR_L2_PR_GCOV_024_091_D_077_2005_DHDH_M_20260702T123457_20260702T123531_P05023_N_F_J_001  # before, 1.8 GB
  NISAR_L2_PR_GCOV_025_091_D_077_2005_QPDH_A_20260714T123456_20260714T123512_P05023_F_P_J_001  # during, 4.1 GB
)

# ---------- 2. OPERA DSWx-S1, 16 Jul 2026 (PO.DAAC, Earthdata login) ----------
# CK/CL alone miss eastern Chattogram (Rangunia, Satkania, Lohagara, Banshkhali): DK/DL added.
DSWX_BASE=https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/OPERA_L3_DSWX-S1_V1
DSWX_TILES=(T46QCK T46QCL T46QDK T46QDL)
DSWX_STAMP=20260716T234703Z_20260725T000947Z_S1C_30_v1.0
DSWX_BANDS=(B01_WTR B02_BWTR B03_CONF)

# ---------- 3. GPM IMERG Late daily, 5–18 Jul 2026 (GES DISC, Earthdata login) ----------
IMERG_BASE=https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.07/2026/07

# ---------- 4–8. Open data, no login ----------
WORLDCOVER=https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N21E090_Map.tif
WORLDPOP=https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/BGD/bgd_ppp_2020_UNadj.tif
DEM_TILES=(N21_00_E091_00 N21_00_E092_00 N22_00_E091_00 N22_00_E092_00 N23_00_E091_00)
BND_BASE=https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BGD

small() {
  for t in "${DSWX_TILES[@]}"; do for b in "${DSWX_BANDS[@]}"; do
    get dswx_s1 "$DSWX_BASE/OPERA_L3_DSWx-S1_${t}_${DSWX_STAMP}_${b}.tif" auth
  done; done
  for d in $(seq 5 18); do
    dd=$(printf %02d "$d")
    get imerg "$IMERG_BASE/3B-DAY-L.MS.MRG.3IMERG.202607${dd}-S000000-E235959.V07C.nc4" auth
  done
  get worldcover "$WORLDCOVER"
  get worldpop "$WORLDPOP"
  for t in "${DEM_TILES[@]}"; do
    get dem  "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_${t}_DEM/Copernicus_DSM_COG_10_${t}_DEM.tif"
    get hand "https://glo-30-hand.s3.amazonaws.com/v1/2021/Copernicus_DSM_COG_10_${t}_HAND.tif"
  done
  get boundaries "$BND_BASE/ADM2/geoBoundaries-BGD-ADM2.geojson"
  get boundaries "$BND_BASE/ADM3/geoBoundaries-BGD-ADM3.geojson"
  echo
  echo "LHASA landslide nowcast: not scripted. Browse https://portal.nccs.nasa.gov/datashare/landslides/nrt/hazard/tif/"
  echo "and save the files dated 20260705 to 20260718 into $OUT/lhasa/ (see the data page)."
}
nisar() { for g in "${NISAR[@]}"; do get nisar "$NISAR_BASE/$g/$g.h5" auth; done; }
feni()  { for g in "${NISAR_FENI[@]}"; do get nisar "$NISAR_BASE/$g/$g.h5" auth; done; }

case "$WHAT" in
  all)   small; nisar ;;
  small) small ;;
  nisar) nisar ;;
  feni)  feni ;;
  *) echo "unknown option: $WHAT (use all | small | nisar | feni)"; exit 1 ;;
esac
echo "Done. Files are in $OUT/"
