#!/usr/bin/env bash
# fetch_hawaii.sh DL_DIR OUT_DIR : downloads + bakes the Hawaii terrain stage data (lab_hawaii.html). Needs curl, python3 + numpy + PIL.
# Sources (all public): NOAA ETOPO 2022 15" and 30" (bathymetry + topography, NOAA NCEI, public domain),
# AWS Terrain Tiles / Terrarium z11 (Hawaii land detail) and z12 (Everest), NASA GIBS MODIS 250 m true colour (multi-date, composited
# cloud-free) + Blue Marble NG 500 m. About 6-8 min; DL ~90 MB (delete after the bake), OUT ~45 MB (git-ignored, never committed).
set -euo pipefail
DL=$1; OUT=$2; HERE=$(cd "$(dirname "$0")" && pwd); mkdir -p "$DL" "$OUT"
EP01=/home/user/juicytea-media/longform/ep01-continental-drip/tools
DRAIN=$HERE/../../drain/tools
HB="-158.3,17.9,-153.8,21.8"; SB="-168,12,-144,30"
NC=https://www.ngdc.noaa.gov/thredds/wcs/global/ETOPO2022
[ -s "$DL/etopo15.tif" ] || curl -sS -o "$DL/etopo15.tif" "$NC/15s/15s_surface_elev_netcdf/ETOPO_2022_v1_15s_N30W165_surface.nc?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&bbox=$HB&format=GeoTIFF_Float"
[ -s "$DL/skirt.tif" ] || curl -sS -o "$DL/skirt.tif" "$NC/30s/30s_surface_elev_netcdf/ETOPO_2022_v1_30s_N90W180_surface.nc?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&bbox=$SB&format=GeoTIFF_Float"
# Terrarium: Hawaii land detail (z11 ~ 75 m) on the hero grid, Everest (z12 ~ 35 m) for the same-scale comparison
[ -s "$DL/terr11_h.npy" ] || python3 -I $EP01/dem.py 11 4096 4096 "$DL/terr11" -158.3 17.9 -153.8 21.8
[ -s "$DL/everest_h.npy" ] || python3 -I $EP01/dem.py 12 1024 1024 "$DL/everest" 86.700 27.805 87.150 28.205
rm -f "$DL"/*_normal.png "$DL"/*_shade.png "$DL"/*_hgt16.png
# GIBS colour: Blue Marble NG (base colour) + MODIS 250 m on several clear-ish summer days (composited per pixel in the bake)
[ -s "$DL/bmng.jpg" ] || python3 -I $DRAIN/gibs_bbox.py BlueMarble_NextGeneration 500m 2004-07-01 7 jpeg "$DL/bmng.jpg" -158.3 17.9 -153.8 21.8
[ -s "$DL/skirt_bm.jpg" ] || python3 -I $DRAIN/gibs_bbox.py BlueMarble_NextGeneration 500m 2004-07-01 5 jpeg "$DL/skirt_bm.jpg" -168 12 -144 30
mkdir -p "$DL/modis"
for d in 2024-06-03 2024-06-19 2024-07-08 2024-07-21 2024-08-06 2024-08-25 2024-09-10 2024-09-22 2022-06-14 2022-07-17 2022-08-09 2022-09-05 \
         2021-06-10 2021-07-02 2021-07-25 2021-08-18 2021-09-07 2023-06-05 2023-06-28 2023-07-14 2023-09-12 2023-09-29 2022-06-28 2022-07-30; do
  for s in Terra Aqua; do f="$DL/modis/${s}_$d.jpg"; [ -s "$f" ] || python3 -I $DRAIN/gibs_bbox.py MODIS_${s}_CorrectedReflectance_TrueColor 250m $d 8 jpg "$f" -158.3 17.9 -153.8 21.8 || true; done
done
python3 -I "$HERE/hawaii_bake.py" "$DL" "$OUT"
