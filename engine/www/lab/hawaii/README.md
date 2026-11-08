# Hawaii terrain stage (ep02 thumbnail heroes and drain shots)

Prototype, not yet production. `lab_hawaii.html` renders named hero stills (no text) of the Hawaiian Islands with the sea lowered, plus a same-scale Mauna Loa vs Everest comparison.

| File | What |
|---|---|
| `../../lab_hawaii.html` | The page. `SHOTS` table at the top: one entry per hero still (camera, water level, sun, look, devices). Any field can be overridden with `--q` |
| `hterrain.js` | `HawaiiStage`, forked from `lab/drain/terrain.js` (the Gibraltar lab is unchanged). Ray-marched sun shadows (any sun, any exaggeration), dark basalt / sediment seabed, old-shoreline devices, turquoise water with a foam rim, grade |
| `blocks.js` | `BlockStage`: Mauna Loa and Everest as two cut-out DEM blocks on one base line, same scale |
| `tools/fetch_hawaii.sh` | Downloads and bakes everything into `data/` (about 2-4 min; 24 MB baked, about 130 MB of downloads that can be deleted afterwards) |
| `tools/hawaii_bake.py` | The bake: heights, AO, cloud-free MODIS colour composite, Everest heights, and facts from the data (summits, Maui Nui saddle levels) into `data/meta.json` |

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
