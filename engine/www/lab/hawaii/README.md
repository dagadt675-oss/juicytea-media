# Hawaii terrain stage (ep02 thumbnail heroes and drain shots)

Prototype, not yet production. `lab_hawaii.html` renders named hero stills (no text) of the Hawaiian Islands with the sea lowered, plus a same-scale Mauna Loa vs Everest comparison.

| File | What |
|---|---|
| `../../lab_hawaii.html` | The page. `SHOTS` table at the top: one entry per hero still (camera, water level, sun, look, devices). Any field can be overridden with `--q` |
| `hterrain.js` | `HawaiiStage`, forked from `lab/drain/terrain.js` (the Gibraltar lab is unchanged). Ray-marched sun shadows (any sun, any exaggeration), dark basalt / sediment seabed, old-shoreline devices, turquoise water with a foam rim, grade |
| `blocks.js` | `BlockStage`: Mauna Loa and Everest as two cut-out DEM blocks on one base line, same scale (thumbnail stills only; the film's payoff uses `section.js`) |
| `section.js` | `Section`: a terrain cut-away for a `HawaiiStage` (clip plane, section wall with layered basalt, the sagging crust and Moho, old sea floor, trench water, the old ocean in cross-section; optional Everest slab on the same base). Used by the ep02 toolkit's `cutawayShot` |
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

Bake (`region_bake.py --spec SPEC --only NAME --out DATA --dl DL`, or `--name --bbox --wh` for a one-off): ETOPO 2022 15" or 30" (WCS, split at the 15-degree tiles and at the antimeridian), then NOAA NCEI 1/3" and 3" coastal topo-bathy DEMs where listed (OPeNDAP with a stride near the target pixel), each feathered over the coarser grid; Terrarium land detail where no coastal DEM covers (high frequencies only, or `replace`); in the NW Hawaiian Islands a land mask (`mask: "hls"`): land only where the land tiles show more than 2 m and the HLS 30 m imagery is not water, because ETOPO 2022 and the land tiles share false islands there. Colour: 24-48 day MODIS composite, HLS 30 m composite on top for close regions (one luminance gain, cloud and shadow pixels left to MODIS). Lessons from the ep02 bake: the NCEI 6" Hawaii grid (`hawaii_6_mllw_2005`) has gridding artefacts and track striping and adds nothing over ETOPO 2022 15", so it is not used; per-channel colour matching of HLS to MODIS turned land magenta, so only a luminance gain is used. Fixes from the verification stills (2026-11-09): a coarse grid upsampled with a cubic spline rings around each spike ('+'-shaped pits 10-20 m deep around every Lalo islet), so the refill zone also takes a ring of two source pixels around every ETOPO land pixel, with a 120 m reef-flat apron at confirmed islets; surf on reef crests passes the per-pixel land test, so each islet must also pass a vote (15 % or more land-looking pixels and a mean HLS colour that is not water-blue; `vote` in the spec), and `keep` boxes limit land to known islands where the vote is not enough (Kure: Green Island only); `colour.hls.months` takes a list of date ranges (Pali: two summers, because winter scenes leave the NE-facing pali in black topographic shadow) and `gain` with `match: false` fixes the luminance gain where the MODIS reference is cloudy (Pali's matched gain came out 1.34 and turned the ridges neon).

Round 3 (2026-11-09, `region_bake.py` options, all opt-in per region in the spec so other regions bake as before):
- `colour.hls.source: "pc"`: HLS v2 (Sentinel-2 S30 + Landsat L30) with its Fmask cloud mask, read from the Microsoft Planetary Computer (public STAC and data API, no key; NASA public domain): the clearest scenes in the date ranges, cloud, cloud-adjacent and cloud-shadow pixels dropped per scene, the per-pixel median (`stat`) of what is left, rendered through the GIBS HLS tone curve (`HLS_LUT`, measured) so the gains measured on GIBS-based regions still apply. Use it where a ridge is cloudy on most days (the Ko'olau: cloud blobs gone, 3-4 % of pixels never clear). Not for snow: Fmask calls the high snowfields cloud (half of Everest's pixels above 6,500 m were never clear), so Everest uses the GIBS composite of the pre-monsoon high-sun window instead.
- `colour.hls.sat`: one chroma factor about luminance (hue kept), only with a measurement behind it (O'ahu 0.6 = median MODIS / HLS chroma over 53,000 clear land pixels; the same measurement gave the luminance gain 0.734).
- `colour.sea: "depth" | "sat"`: sea-floor texels (the stage shows them from -6 to +4 m, under shallow water or drained) coloured by depth (a sand flat at 0 m to the film's reef grey by -6 m), or with the HLS picture where HLS covers (lagoons and reef flats), never the nearest land colour (Kane'ohe Bay showed olive land colour) and never Blue Marble brightness (the nwhi_west atoll rims were cyan).
- `ao: "tangent"`: sky occlusion measured above the local slope (HBAO), not above the horizontal.
- `land.top`: scale an island's land heights to a surveyed top where the land tiles smooth it (Nihoa 179 m to 273 m, x1.522); `land.mask_floor`: the depth down to which a false island's skirt is refilled (nwhi_west -2 m keeps the atoll tops at -1 to -2 m).
- `features`: a sea stack or pinnacle no grid resolves, modelled at its surveyed or imagery position from lobes `[dx, dy, rx, ry, top]` (m), steep walls, crags, a guano-pale top and an irregular reef flat (`platform`); always marked approximate in the gaps (La Perouse Pinnacle, 37 m).
- `bathy: ["region:NAME"]`: a fine nest takes the cleaned heights of its baked parent (e.g. `laperouse` inside `lalo`, 2.5 m grid).
- `dated`: dated USGS Landsat 8 Collection 2 scenes of the same grid as regions of their own (make_index.py lists `meta.variants` as e.g. `lalo_2018_before`, `lalo_2018_after`): inside a focus circle the land is that day's dry sand (near-infrared unmixing between water 0.02 and dry coral sand 0.60, area-preserving on the grid) in that day's picture, and sand that is gone becomes a shoal 2 m down coloured by depth (the day's bright shoal under the stage's water read as an island still there); outside it the base grid.
- Fixed: a float64 grid (the reef apron maths) was misread by `Image.fromarray(h, 'F')` in the AO resample and zeroed 80 % of Lalo's AO; the grid is cast to float32 before packing.
