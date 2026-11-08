#!/usr/bin/env bash
# rebuild_regions.sh [DL_DIR] [name,name,...] : bake the ep02 terrain/seafloor regions into engine/www/ep/ep02/data and write regions.json.
# Spec (bbox, size, sources, stack, verification camera, facts): regions_spec.json in this folder. The baked data is git-ignored;
# only regions.json and each region's meta.json are committed. All regions: about 25-40 min (network bound), about 60-80 MB.
# The Big Island hero + skirt (legacy 'bigisland', 'hawaii_skirt') come from lab/hawaii/data, rebuilt by fetch_hawaii.sh if missing.
# Downloads go to DL_DIR/<region> and are deleted after each bake (pass KEEP=1 to keep them).
# Needs curl, python3 with numpy, scipy and PIL; network to ngdc.noaa.gov, s3.amazonaws.com and gibs.earthdata.nasa.gov.
# Verify one region: cd engine && node still.cjs --page lab_region.html --q '{"region":"midway"}' --frames 0 --outdir <dir>
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../../../../.." && pwd)
DL=${1:-${TMPDIR:-/tmp}/ep02_regions_dl}; ONLY=${2:-}
mkdir -p "$DL"
if [ ! -s "$ROOT/engine/www/lab/hawaii/data/hero_h16.png" ]; then
  bash "$ROOT/engine/www/lab/hawaii/tools/fetch_hawaii.sh" "$DL/hawaii" "$ROOT/engine/www/lab/hawaii/data"
fi
python3 -I -u "$ROOT/engine/www/lab/hawaii/tools/region_bake.py" --spec "$HERE/regions_spec.json" ${ONLY:+--only "$ONLY"} \
  --out "$ROOT/engine/www/ep/ep02/data" --dl "$DL" ${KEEP:+--keep}
python3 -I "$HERE/make_index.py"
