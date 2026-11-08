# Hawaii hero renders for ep02 thumbnails (no text)

Built 2026-11-08 with our engine page `engine/www/lab_hawaii.html` (new; the other lab pages are untouched). Every image is our own render of real elevation data. There is no text, label, arrow, number or source on any image.

- Each shot exists at **1920x1080** (`ours_hawaii_<name>_1920.jpg`) and **1280x720** (`ours_hawaii_<name>_1280.jpg`). Both sizes are rendered natively, not resized.
- `ours_hawaii_contact_sheet.jpg` shows all 19 shots.
- `stats.json` holds brightness, area shares and the niche distinctiveness gate for each 1920 image.

## Quick picks

| Need | Best image | Why |
|---|---|---|
| **Postcard signature plate** (niche report 4.2) | `plate_ne` or `plate_ne_wide` | True scale (1.0x). Low north-east oblique with warm side light from the north-west. A green Mauna Kea top sits on a dark basalt plinth. The top 40% is calm sky for the card, and the terrain fills 51-54%. Tan is 0-1%. |
| Plate with the one luminous waterline | `plate_ne_line` | Same camera, plus a cyan line on the real former coastline (the 0 m contour, not a horizontal bar). |
| Half drained, island on a huge skirt | `half_oblique_w`, `half_east_puna` | True scale. Island top, cream old-shoreline line, dark exposed flank, then turquoise water. In `half_east_puna` the Puna Ridge stands out as a peninsula. |
| High-contrast variant | `half_contrast_ne` | Midday light, contrast 1.18. The brightest true-scale half-drain (luma 140). |
| Mid-drain moment | `mid_drain_foam_se`, `mid_drain_foam_kona`, `mid_drain_puna` | A foam rim on the waterline halfway down the dark flank. Bright turquoise water at the shore turns deep teal further out. |
| Maui Nui at -400 ft | `mauinui_400ft_s` (main), `mauinui_400ft_sw` | Maui, Moloka'i and Lana'i (plus Penguin Bank) are joined by grey exposed shelf. Kaho'olawe stays separate, as the data and the brief require. |
| Fully drained massif | `drained_massif_e`, `drained_massif_sw` | True scale. The island sits on its whole dark skirt over a dark grey basalt floor. |
| Film-only, exaggerated 2x | `half_low_se_x2`, `half_golden_kona_x2`, `drained_massif_ne_x2` | Low obliques. At true scale these read as a thin band, which is how a shield volcano really looks, so these use 2x. **Not for the thumbnail.** In the film, narrate "heights exaggerated" once (visual plan section S4). |
| Payoff comparison (film, about 85-90%) | `compare_everest`, `compare_everest_guides`, `compare_everest_34` | Mauna Loa against Everest at the same scale on one base line. **Not for the thumbnail or the first 30 s**: the niche ban list includes "Everest side-by-side or cross-section", and the brief keeps "taller than Everest" out of the title, thumbnail and opening. |

### Not made
**(5) Tiny tourist on the drained cliff.** Our grids are 100-450 m per cell, so a person at true scale would be smaller than one pixel on a cliff that is kilometres tall. Showing one "for scale" needs a forced-perspective cheat, which would mislead. It can be done honestly as a separate close-up plate with a paper cut-out (the `lab/story` cut-out system), clearly not to scale. Ask if wanted.

## Shot parameters (designers: request or run variants)

Rendering one shot takes 8-15 s, well under the 90 s budget. Every field can be overridden. A `cam` override replaces the whole camera.

```bash
cd /home/user/juicytea-media/engine
node still.cjs --page lab_hawaii.html --q '{"shot":"plate_ne"}' --frames 0 --w 1920 --h 1080 --outdir /tmp/x
node still.cjs --page lab_hawaii.html --q '{"shot":"plate_ne","sun":[290,9],"exposure":1.45}' --frames 0 --outdir /tmp/x
node still.cjs --page lab_hawaii.html --q '{"shot":"half_oblique_w","level":-1200,"cam":{"lon":-156.5,"lat":19.2,"alt":14,"tLon":-155.7,"tLat":19.5,"tH":0,"fov":30}}' --frames 0 --outdir /tmp/x
bash research/packaging/renders/tools/render_heroes.sh plate_ne half_oblique_w    # both sizes into this folder (scratchpad path)
```

### Parameters
- **Camera.** The eye is set by `lon`/`lat`, plus either `alt` (km above present sea level, can be negative) or `agl` (km above the ground or water below the eye).
  - The camera aims at `tLon`/`tLat`/`tH`, where `tH` is metres. It defaults to the surface there.
  - `fov` is the vertical field of view in degrees. `shiftY` is a vertical lens shift.
- **`level`** is the sea level in metres: 0 is today, -2400 is half drained, -9000 is fully drained.
- **`sun`** is `[azimuth, elevation]` in degrees. Shadows are ray-marched live, so any sun angle works.
- **`look`** is `gold`, `day` or `warm` (sky, haze and sun colour).
- **`water`** is `turq`, `lagoon` or `ocean`.
- **Devices** (each 0 or 1):
  - `foam` (with `foamPx` for the rim width in pixels);
  - `tub`, a pale crust band just below the old shoreline;
  - `line`, a line on the 0 m contour, with `lineCol` `cream` or `cyan`.
- **Grade:** `exposure`, `contrast`, `sat`, `lift`, `vignette`.
- **Surface:**
  - `vex` sets the vertical exaggeration (default 1.0).
  - `landSat` / `landGain` adjust the satellite land colour.
  - `basalt` / `sed` take linear RGB for the rock and sediment colours.
  - `detail` controls procedural micro-relief from 0 to 1.
  - `shadows` is 0 or 1.
- **Compare shots:** `mode: 'blocks'`. The camera is `eye` and `target` in km (x east, y up, z south). Blocks are 28 km wide, centred at x = -19 (Mauna Loa) and +19 (Everest). Also `guides` (0/1) and `line` (sea-level line on Mauna Loa).

| Shot | vex | Level (m) | Look, sun [az, el] | Camera | Other |
|---|---|---|---|---|---|
| `half_oblique_w` | 1 | -2400 | gold [200,12] | eye 19.15N 156.55W alt 16 km -> 19.50N 155.75W tH 0 m, fov 34 | water=turq, foam, tub, line=cream |
| `half_east_puna` | 1 | -2400 | gold [200,20] | eye 19.25N 154.35W alt 12 km -> 19.55N 155.10W tH 0 m, fov 40 | water=turq, foam, tub, line=cream |
| `half_contrast_ne` | 1 | -2400 | day [150,35] | eye 20.45N 154.85W alt 12 km -> 19.85N 155.40W tH 0 m, fov 38 | water=turq, foam, tub, line=cream, contrast=1.18, sat=1.25 |
| `half_low_se_x2` | 2 | -2400 | gold [235,11] | eye 18.95N 154.80W agl 3 km -> 19.45N 155.55W tH 2000 m, fov 30 | water=lagoon, foam, tub, line=cream |
| `half_golden_kona_x2` | 2 | -2400 | gold [268,8] | eye 19.45N 156.45W agl 4 km -> 19.48N 155.75W tH 1500 m, fov 30 | water=turq, foam, tub, line=cream |
| `drained_massif_e` | 1 | -9000 | day [175,26] | eye 19.35N 154.30W alt 12 km -> 19.60N 155.25W tH -2500 m, fov 40 | tub, line=cream, exposure=1.3, sed=[0.045,0.045,0.048] |
| `drained_massif_sw` | 1 | -9000 | day [190,24] | eye 18.95N 156.45W alt 12 km -> 19.45N 155.75W tH -2500 m, fov 40 | tub, line=cream, exposure=1.3, sed=[0.045,0.045,0.048] |
| `drained_massif_ne_x2` | 2 | -9000 | warm [300,13] | eye 20.55N 154.80W alt 10 km -> 19.75N 155.45W tH -2000 m, fov 36 | tub, line=cream |
| `mauinui_400ft_s` | 1 | -122 | day [120,38] | eye 20.15N 156.55W alt 30 km -> 20.90N 156.65W tH 0 m, fov 34 | water=turq, foam, landSat=0.95 |
| `mauinui_400ft_sw` | 1 | -122 | day [120,38] | eye 20.35N 157.35W alt 25 km -> 20.85N 156.55W tH 0 m, fov 36 | water=turq, foam, landSat=0.95 |
| `compare_everest` | 1 | - | day [228,30] | eye [0,12,230] target [0,7.6,0] fov 12 (near-orthographic, centred: no perspective favours either block) | line=1, guides=0 |
| `compare_everest_guides` | 1 | - | day [228,30] | same | line=1, guides=1 (thin lines at both summit heights) |
| `compare_everest_34` | 1 | - | day [228,30] | eye [60,30,200] target [0,7,0] fov 14 (Everest is nearer, so it looks slightly larger: conservative) | line=1 |
| `mid_drain_foam_se` | 1 | -2000 | gold [235,18] | eye 19.05N 155.00W agl 4 km -> 19.18N 155.10W tH -2000 m, fov 45 | water=turq, foam, foamPx=5, tub, line=cream |
| `mid_drain_foam_kona` | 1 | -2000 | gold [250,16] | eye 19.35N 156.15W agl 4 km -> 19.50N 156.02W tH -2000 m, fov 45 | water=turq, foam, foamPx=5, tub, line=cream |
| `mid_drain_puna` | 1 | -2000 | gold [220,20] | eye 19.40N 154.55W agl 5 km -> 19.55N 154.72W tH -2000 m, fov 45 | water=turq, foam, foamPx=5, tub, line=cream |
| `plate_ne` | 1 | -9000 | warm [300,13] | eye 20.30N 155.00W alt 8 km -> 19.80N 155.45W tH -1000 m, fov 38 | tub, exposure=1.35 |
| `plate_ne_line` | 1 | -9000 | warm [300,13] | same as `plate_ne` | tub, line=cyan, exposure=1.35 |
| `plate_ne_wide` | 1 | -9000 | warm [315,16] | eye 20.40N 155.10W alt 6 km -> 19.82N 155.47W tH 0 m, fov 34 | tub, exposure=1.35 |

## Checks on the 1920 images

**Area shares** are measured on a 480x270 downscale:
- sky is everything connected to the top edge that is sky-coloured;
- water is cyan or blue saturated pixels below the sky;
- terrain is the rest.

**Gate** is `research/niche/work/gate.py`: tan at most 10%, red at most 3%, blue at most 45%, and a mean feature distance of at least 11.0 to both the drain clones (A) and the template farms (D).

| Shot | Luma | Terrain / water / sky % | Colour shares | Nearest cluster, A, D | Gate |
|---|---|---|---|---|---|
| `half_oblique_w` | 124 | 29 / 35 / 36 | tan 0, red 0, blue 29, cyan 7 | C_hawaii 10.35, A 12.43, D 11.32 | PASS |
| `half_east_puna` | 131 | 26 / 34 / 41 | tan 0, red 0, blue 31, cyan 8 | C 10.48, A 12.56, D 11.20 | PASS |
| `half_contrast_ne` | 140 | 28 / 32 / 41 | tan 1, red 0, blue 42, cyan 8 | C 10.44, A 12.65, D 11.31 | PASS |
| `half_low_se_x2` | 138 | 14 / 39 / 47 | tan 0, red 0, blue 32, cyan 24 | C 10.17, A 13.11, D 11.38 | PASS |
| `half_golden_kona_x2` | 138 | 32 / 22 / 45 | tan 1, red 0, blue 38, cyan 5 | C 10.77, A 12.04, D 11.21 | PASS |
| `drained_massif_e` | 135 | 58 / 1 / 40 | tan 0, red 0, blue 13 | C 10.44, A 11.95, D 11.58 | PASS |
| `drained_massif_sw` | 131 | 58 / 2 / 40 | tan 1, red 0, blue 11 | C 10.49, A 11.91, D 11.68 | PASS |
| `drained_massif_ne_x2` | 105 | 33 / 28 / 39 | tan 0, red 0, blue 27 | C 10.72, A 12.92, D 11.72 | PASS |
| `mauinui_400ft_s` | 135 | 36 / 55 / 9 | tan 9, red 0, blue 24, cyan 32 | B_without 10.78, A 11.93, D 11.03 | PASS (D is borderline) |
| `mauinui_400ft_sw` | 141 | 17 / 56 / 27 | tan 5, red 0, blue 25, cyan 32 | C 10.36, A 12.60, D 11.07 | PASS |
| `compare_everest` | 142 | 49 / 5 / 46 | tan 0, red 0, blue 5 | C 10.26, A 13.31, D 11.55 | PASS (banned in thumbnails anyway) |
| `compare_everest_guides` | 143 | 49 / 5 / 46 | tan 0, red 0, blue 5 | C 10.27, A 13.31, D 11.55 | PASS (film only) |
| `compare_everest_34` | 123 | 54 / 9 / 37 | tan 0, red 0, blue 8 | C 10.07, A 13.27, D 11.46 | PASS (film only) |
| `mid_drain_foam_se` | 116 | 25 / 52 / 23 | tan 0, red 0, blue 6, cyan 45 | C 10.37, A 12.50, D 11.30 | PASS |
| `mid_drain_foam_kona` | 117 | 26 / 46 / 28 | tan 1, red 0, blue 32, cyan 15 | C 10.72, A 12.34, D 11.40 | PASS |
| `mid_drain_puna` | 118 | 20 / 50 / 29 | tan 0, red 0, blue 40, cyan 11 | C 10.14, A 12.77, D 11.23 | PASS |
| `plate_ne` | 118 | 51 / 9 / 41 | tan 1, red 0, blue 6 | C 10.93, A 11.98, D 11.76 | PASS |
| `plate_ne_line` | 120 | 50 / 9 / 41 | tan 0, red 0, blue 6 | C 10.81, A 12.28, D 11.81 | PASS |
| `plate_ne_wide` | 128 | 54 / 3 / 44 | tan 1, red 0, blue 1 | A 11.11, D 11.62 | PASS |

**Reading the table:**
- **Tan.** The clones average 21% tan; ours are 0-1%, except Maui Nui (5-9%). There the cause is the real dry leeward land colour of Lana'i and Kaho'olawe, not the seabed.
- **Brightness.** Luma ranges from 105 to 143, with no near-black areas, against ep01's luma of about 40.
- **Subject fill.** In the plates and the drained shots, terrain fills 50-58%. In the half-drain shots the subject is island, flank and water ring together, at 59-64% (terrain plus water).
- **The gate tested on these renders.** With golden light on the drained floor, the first drained renders were brown and failed the gate (A = 10.1-10.2, too close to the drain clones). The final ones use neutral daylight and a cool dark basalt floor, and pass at 11.9.
- **Nearest cluster.** For most images the nearest cluster is the Hawaii-topic set (C, 10.1-10.9). That is expected for the same subject; the postcard card and title type should add distance.
- **Gate scope.** These are plates; the gate must be re-run on the final composed thumbnails.

## Honesty notes

**Vertical scale**
- Everything is at **true scale (1.0x) except the three `_x2` files (2.0x)**.
- The niche report (4.2) asks for 1.0x in the thumbnail. Use the `_x2` files in the film only, with "heights exaggerated" narrated once.

**Drawing devices (not data)**
- The cream old-shoreline line and the pale crust band (`tub`, the 0 to -90 m band) are drawing devices that mark the former sea level.
- The foam rim and the gully and rib texture on steep flanks are also procedural. The gully texture keeps the 450 m sonar grid from looking like plastic.
- The geometry itself is all data.

**Half drained**
- The level is -2,400 m. The sea floor around the Big Island lies at about -4,500 to -5,800 m (deepest cell in our grid: -5,796 m), so this is roughly "half way down".
- Mid-drain is -2,000 m.
- Narrate it as a thought experiment ("if we drained it").

**Maui Nui at -122 m (about 400 ft), measured on our ETOPO 2022 15" grid** (`engine/www/lab/hawaii/data/meta.json`, `facts.maui_nui_saddles_m`):

| Pair | Joins when the sea drops below |
|---|---|
| Maui and Lana'i | -59 m |
| Maui and Moloka'i | -79 m |
| Moloka'i and Lana'i | -79 m |
| Maui and Kaho'olawe | -159 m |

So at -400 ft the three islands are joined and **Kaho'olawe stays separate**, as the brief's must-fix 1 requires. This is checked on ETOPO 2022, which includes multibeam data around Hawai'i, not on the HMRG grid.

**Mauna Loa vs Everest**
- **Mauna Loa** is drawn as one column from its summit down to its true base, **17,170 m (about 56,000 ft)**. The base sits 17,170 m below the DEM summit (4,192 m in the block sampling), at -12,978 m (USGS Volcano Watch, brief fact 2).
- The cut face shows three bands:
  - above sea level;
  - sea level down to the old sea floor (shown at -5,000 m);
  - the part pushed into the crust (8 km).
- That third band is simplified as flat across the 28 km block; the real depression is a broad bowl, deepest under the summit.
- **Everest** is the AWS Terrain Tiles (SRTM) surface. Its DEM peak is 8,741 m, scaled by 1.012 so that the summit is the surveyed **8,849 m (29,032 ft)**. Its column runs from sea level.
- Both blocks are 28 x 28 km, use the same vertical scale (1.0) and share one base plane.
- The ratio as drawn is 1.94, matching "almost twice" in the brief.

**Land colour**
- The colour is a per-pixel cloud-free composite of 48 NASA MODIS Terra and Aqua true-colour days (June-September 2021-2024; August 2023 excluded) at 250 m.
- Persistent windward cloud was filled from neighbouring clear land colour. That makes smooth green patches on windward Mauna Kea, Puna and east Maui, which are visible only in close views.

**Names.** Use the correct Hawaiian spellings when these are captioned: Hawai'i, Moloka'i, Lana'i, Kaho'olawe, Mauna Kea, Mauna Loa, Kilauea (Kīlauea), Hualālai, Kohala, Haleakalā.

## Data and licences

| Data | Used for | Source | Licence / credit |
|---|---|---|---|
| ETOPO 2022 15 arc-second (N30W165 tile) | Hero heights incl. bathymetry, bbox 158.3W-153.8W, 17.9N-21.8N | NOAA NCEI THREDDS WCS | US Government work, public domain. Credit "NOAA NCEI ETOPO 2022" in the description |
| ETOPO 2022 30 arc-second | Wide skirt and horizon, 168W-144W, 12N-30N | NOAA NCEI | Public domain |
| AWS Terrain Tiles (Terrarium), z11 Hawai'i and z12 Everest | High-frequency land detail on Hawai'i; the whole Everest block | Mapzen / Tilezen on AWS Open Data (sources include USGS 3DEP/NED and SRTM) | Open data; credit "Terrain Tiles: Mapzen, data sources (USGS, NASA SRTM, NOAA)" in the description |
| MODIS Terra and Aqua Corrected Reflectance, true colour (48 dates) | Land colour | NASA GIBS / Worldview | NASA, public domain. Credit "NASA GIBS / MODIS" |
| Blue Marble Next Generation 500 m | Fallback colour and skirt colour | NASA GIBS | NASA, public domain |

- No competitor images were used.
- The renders are our own work.
- Per the owner's rules, nothing is credited on screen; credits go in the description only.

## Files

**Renders and tools in this folder**
- `ours_hawaii_<shot>_1920.jpg` and `ours_hawaii_<shot>_1280.jpg`: 19 shots x 2 sizes.
- `ours_hawaii_contact_sheet.jpg`
- `stats.json`
- `tools/render_heroes.sh <shot>...` re-renders shots at both sizes into this folder.
- `tools/stats.py <dir>` rebuilds `stats.json`.

**Engine (repo)**
- Page: `engine/www/lab_hawaii.html`. The `SHOTS` table is at the top.
- Modules: `engine/www/lab/hawaii/hterrain.js` (`HawaiiStage`) and `engine/www/lab/hawaii/blocks.js` (`BlockStage`).
- Notes: `engine/www/lab/hawaii/README.md`.

**Data rebuild**
- Run `bash engine/www/lab/hawaii/tools/fetch_hawaii.sh <dl_dir> engine/www/lab/hawaii/data`. It takes about 2-4 minutes.
- The bake writes heights, AO, the MODIS composite and the Everest heights. It also writes the data facts (summits, Maui Nui saddles) to `meta.json`.
- The 24 MB of baked data is git-ignored; only `meta.json` is tracked.
