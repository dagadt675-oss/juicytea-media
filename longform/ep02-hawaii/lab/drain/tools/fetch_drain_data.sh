#!/usr/bin/env bash
# fetch_drain_data.sh DL_DIR OUT_DIR [lon0 lat0 lon1 lat1] [vex sun_az sun_el]
# Rebuilds the drain-stage data for one location (defaults: Strait of Gibraltar hero tile). Needs: curl, python3 + numpy + PIL.
# Note: terrain_bake.py currently has the Gibraltar hero/skirt bboxes in its cfg dict; change them there for a new location.
set -euo pipefail
DL=$1; OUT=$2; B=${3:--9},${4:-34},${5:--1},${6:-38}; VEX=${7:-3}; AZ=${8:-150}; EL=${9:-21}
HERE=$(cd "$(dirname "$0")" && pwd); mkdir -p "$DL" "$OUT"; IFS=, read lon0 lat0 lon1 lat1 <<< "$B"
curl -sS -o "$DL/etopo15.tif" "https://www.ngdc.noaa.gov/thredds/wcs/global/ETOPO2022/15s/15s_surface_elev_netcdf/ETOPO_2022_v1_15s_N45W015_surface.nc?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&bbox=$B&format=GeoTIFF_Float"
curl -sS -o "$DL/skirt.tif" "https://www.ngdc.noaa.gov/thredds/wcs/global/ETOPO2022/30s/30s_surface_elev_netcdf/ETOPO_2022_v1_30s_N90W180_surface.nc?service=WCS&version=1.0.0&request=GetCoverage&coverage=z&bbox=$(python3 -c "print(','.join(str(v) for v in [$lon0-15,$lat0-8,$lon1+13,$lat1+8]))")&format=GeoTIFF_Float"
python3 -I /home/user/juicytea-media/longform/ep01-continental-drip/tools/dem.py 10 4096 2048 "$DL/terr10" $lon0 $lat0 $lon1 $lat1
python3 -I "$HERE/gibs_bbox.py" MODIS_Terra_CorrectedReflectance_TrueColor 250m 2024-08-04 8 jpg "$DL/modis8.jpg" $lon0 $lat0 $lon1 $lat1   # pick a clear date per region
python3 -I "$HERE/gibs_bbox.py" BlueMarble_NextGeneration 500m 2004-08-01 7 jpeg "$DL/bmng08.jpg" $lon0 $lat0 $lon1 $lat1
python3 -I "$HERE/gibs_bbox.py" BlueMarble_NextGeneration 500m 2004-08-01 5 jpeg "$DL/skirt_bm.jpg" $(python3 -c "print(' '.join(str(v) for v in [$lon0-15,$lat0-8,$lon1+13,$lat1+8]))")
python3 -I "$HERE/terrain_bake.py" "$DL" "$OUT" $VEX $AZ $EL
python3 -I "$HERE/sill.py" "$DL/etopo15.tif"
rm -f "$DL"/terr10_normal.png "$DL"/terr10_shade.png "$DL"/terr10_hgt16.png
