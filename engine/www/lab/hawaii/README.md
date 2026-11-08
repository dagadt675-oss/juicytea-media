# Hawaii terrain stage (ep02 thumbnail heroes and drain shots)

Prototype, not yet production. `lab_hawaii.html` renders named hero stills (no text) of the Hawaiian Islands with the sea lowered, plus a same-scale Mauna Loa vs Everest comparison.

| File | What |
|---|---|
| `../../lab_hawaii.html` | The page. `SHOTS` table at the top: one entry per hero still (camera, water level, sun, look, devices). Any field can be overridden with `--q` |
| `hterrain.js` | `HawaiiStage`, forked from `lab/drain/terrain.js` (the Gibraltar lab is unchanged). Ray-marched sun shadows (any sun, any exaggeration), dark basalt / sediment seabed, old-shoreline devices, turquoise water with a foam rim, grade |
| `blocks.js` | `BlockStage`: Mauna Loa and Everest as two cut-out DEM blocks on one base line, same scale |
| `tools/fetch_hawaii.sh` | Downloads and bakes everything into `data/` (about 2-4 min; 24 MB baked, about 130 MB of downloads that can be deleted afterwards) |
| `tools/hawaii_bake.py` | The bake: heights, AO, cloud-free MODIS colour composite, Everest heights, and facts from the data (summits, Maui Nui saddle levels) into `data/meta.json` |
| `tools/region_bake.py` | The general bake for any region (name, bbox, size): ETOPO 2022, NOAA NCEI coastal DEMs, Terrarium land detail, MODIS + HLS colour, AO and sea-level facts into `<out>/<name>/` (see Regions below) |
| `../../lab_region.html` | Renders any baked region with its nested stack (`--q '{"region":"midway"}'`); defaults come from the region's `view` in `regions.json` |

Rebuild the data (git-ignored except `meta.json`):
```bash
bash engine/www/lab/hawaii/tools/fetch_hawaii.sh <scratch>/hawaii_dl engine/www/lab/hawaii/data
```
Render one still:
```bash
cd engine && node still.cjs --page lab_hawaii.html --q '{"shot":"half_oblique_w"}' --frames 0 --w 1920 --h 1080 --outdir <dir>
node still.cjs --page lab_hawaii.html --q '{"shot":"half_oblique_w","sun":[230,9],"level":-1500,"cam":{"lon":-156.5,"lat":19.2,"alt":14,"tLon":-155.7,"tLat":19.5,"tH":0,"fov":34}}' --frames 0 --outdir <dir>
```
About 5-15 s per 1920x1080 still on software WebGL. The shot list, camera parameters, data sources and licences are in the packaging research `renders/index.md`.

Data: NOAA NCEI ETOPO 2022 (15" and 30", bathymetry + topography; public domain), AWS Terrain Tiles / Terrarium (Mapzen/Tilezen; sources include USGS and SRTM; credit "Terrain Tiles: Mapzen, data sources" in the description), NASA GIBS MODIS Terra/Aqua Corrected Reflectance and Blue Marble Next Generation (NASA, public domain).

## Regions (any place, nested up to 3 layers)

`HawaiiStage` loads either the legacy folder above (`S.load('lab/hawaii/data')`, unchanged output: verified pixel-identical on two thumbnail shots) or any region baked by `tools/region_bake.py`: `S.loadRegion('ep/ep02/data', 'midway')`, or `S.load('ep/ep02/data/midway')` (a region folder is detected by its meta.json). A region's `stack` in `regions.json` lists 1-3 layers, finest first, each inside the next (e.g. `halape > kilauea_sf > hawaii_skirt`); every coarser mesh drops out of sight inside the next finer bbox, and the shader height lookup (shadows, water depth) uses the finest layer that covers a point. `meta.hero_bbox` / `hHero` are the finest layer, `meta.skirt_bbox` / `hSkirt` the outermost, so code written for the legacy stage keeps working. `o.stack` overrides the stack; mesh sizes default to at most 1500 / 1000 / 900 vertices on the long side (`o.heroGrid`, `o.midGrid`, `o.skirtGrid`).

ep02's regions: spec `ep/ep02/tools/regions_spec.json`, rebuild `bash engine/www/ep/ep02/tools/rebuild_regions.sh [DL_DIR] [name,name]`, index with facts and gaps `ep/ep02/data/regions.json`.

Bake (`region_bake.py --spec SPEC --only NAME --out DATA --dl DL`, or `--name --bbox --wh` for a one-off): ETOPO 2022 15" or 30" (WCS, split at the 15-degree tiles and at the antimeridian), then NOAA NCEI 1/3" and 3" coastal topo-bathy DEMs where listed (OPeNDAP with a stride near the target pixel), each feathered over the coarser grid; Terrarium land detail where no coastal DEM covers (high frequencies only, or `replace`); in the NW Hawaiian Islands a land mask (`mask: "hls"`): land only where the land tiles show more than 2 m and the HLS 30 m imagery is not water, because ETOPO 2022 and the land tiles share false islands there. Colour: 24-48 day MODIS composite, HLS 30 m composite on top for close regions (one luminance gain, cloud and shadow pixels left to MODIS). Lessons from the ep02 bake: the NCEI 6" Hawaii grid (`hawaii_6_mllw_2005`) has gridding artefacts and track striping and adds nothing over ETOPO 2022 15", so it is not used; per-channel colour matching of HLS to MODIS turned land magenta, so only a luminance gain is used.
