# ep02 shot toolkit: the chapter builders' manual

Everything in ep02 "Why Can't You See Most of Hawaii? (Look Down)" is built with `shared.js` in this folder: one renderer, one grade, one type system, so the film looks like one film. Six builders work in parallel, one per chapter, each in its own `chN.js`.

Rules that win over anything here: `PLAYBOOK.md`, `PLAYBOOK_craft.md`, `PLAYBOOK_production.md` (repo root). Look book: `longform/ep02-hawaii/research/visual/visual_plan.md`. Shot list: the `visual` and `onscreen` fields of `longform/ep02-hawaii/script/script_locked.json`. Thumbnails the film returns to: `channel/packaging` (final_ep02_1 NO OCEAN = frame 1, final_ep02_2 ONE ISLAND = s006).

## 1. What you may and may not change

| You MAY | You may NOT |
|---|---|
| Edit your own `chN.js` (and only it) | Edit `shared.js`, `edit.js`, `testrt.js`, `payoff.js`, the test pages, `timing.json`, `tools/`, `data/` |
| Add helpers, cameras, places and masks as local constants inside your `chN.js` | Edit `lab/**` (`hterrain.js`, `section.js`, `blocks.js`, `cineglobe.js`, `type.js`, `story.js`), `lib/**`, `film.html`, `still.cjs` |
| Add public-domain photos in `img/chN/` with their licence lines in `img/chN/LICENSE.md` (page URL, credit, date checked); use the shared paper cut-outs in `img/paper/` (sources in `img/SOURCES.md`) | Commit any photo without a licence line; use AI images, stock clips without a per-file licence check, or other channels' frames; edit `img/paper/` (ask the toolkit owner for a new cut-out in `requests/chN.md`) |
| Write toolkit requests in `requests/chN.md` (one file per chapter) and work around them locally meanwhile | Re-bake or add regions (ask; `tools/rebuild_regions.sh` is the toolkit owner's) |
| Render stills of your chapter (`"only":"chN"`) | Commit renders, stills or sheets (scratchpad only); render the full film locally |
| ch6 only: call `buildPayoff()` and import `ML`, `CUT_PLANE`, `SECTION`, `EVEREST` from `payoff.js` for s162-s167 | Draw your own chapter card (the orchestrator does), or draw text over it |

Base shots (layer 0) of your chapter must cover exactly your window, no gaps: start at `ch.t0`, end at `ch.t1x` (the next chapter fades in over `K.XF` = 0.3 s). Your first shot starts at `ch.t0` with `fadeIn: K.XF` (chapters 2-6). Anything uncovered renders as a logged navy placeholder.

| Chapter | Title (card text, description chapters) | Window (s) | Frames | Segments |
|---|---|---|---|---|
| 1 | Only the Top | 0.00-93.81 (no card) | 0-2814 | s001-s025 |
| 2 | Oʻahu's Missing Side | 93.81-181.65 | 2814-5450 | s026-s048 |
| 3 | The Island Stands Up | 181.65-315.55 | 5450-9467 | s049-s083 |
| 4 | Watch It Grow Old | 315.55-435.89 | 9467-13077 | s084-s111 |
| 5 | Fought Over a Volcano | 435.89-598.99 | 13077-17970 | s112-s149 |
| 6 | We Haven't Hit Bottom | 598.99-746.85 (end screen to the end) | 17970-22406 | s150-s178 |

Always read the window from `K.chapter(n)`: the numbers above follow `timing.json`, which changes when the voice is re-timed.

## 2. A chapter module

```js
// chN.js
import { PLACES, PAL, E, F } from './shared.js';
export async function build(api, kit, scenes) {
  const { K, ui } = kit, ch = K.chapter(2);                       // {n, t0, t1, t1x, card, first, title}
  scenes.push(kit.terrainShot({ id: 'ch2-pali', t0: ch.t0, t1: K.s1('s029') + 0.4, fadeIn: K.XF, region: 'pali', preset: 'today',
    cam: { lon: -157.7936, lat: 21.3667, agl: 0.03, heading: 42, pitch: -8, fov: 62, near: 0.005, far: 400 }, push: 0.3, drift: 0.4,
    ui(ctx, lt, t, view) { const q = view.project(...PLACES.pali, 370); if (q) ui.label(ctx, 'PALI LOOKOUT', q[0], q[1], { t, p: F.clamp((t - K.lead('pali')) / 0.3) }); } }));
}
```

`kit` holds: `K` (timing), `ui` (type), `hub` (renderer and stages), `terrainShot`, `cutawayShot`, `cineGlobeShot`, `scaleMove` (space to place, section 4), `blockShot` (deprecated), `island`, `bridges`, `maskTexture`, `flight`, `orbitPath`, `orbitEye`, `terrainCamOf`, `mixState`, `keyAt`, `valAt`, `xfade`, `seq`, `paper`, `drawCutout`, `paperProp`, `PAPER` (the paper kit, section 8), `makePostcard`, `drawPostcard`, `drawStandee`, `drawQuad`, `prepPaper`, `gradeCanvas`, `okina`, `Section`, `CAMS`, `PLACES`, `PRESETS`, `REGIONS`, `SEABED`, `PAL`, `E`, `F`, `T` (type.js), `P` (story.js). Named exports of `shared.js` you may import: `PLACES`, `CAMS`, `PRESETS`, `MLOOKS`, `TERRAIN_DEFAULTS`, `WATER_FILM`, `MOVE_WATER`, `GLOBE_OCEAN`, `GLOBE_CLOUDS`, `PAPER`, `LINE`, `PAL`, `CAP`, `E`, `F`, `T`, `P`, `THREE`, `flight`, `orbitPath`, `orbitEye`, `terrainCamOf`, `mixState`, `keyAt`, `valAt`, `xfade`, `seq`, `WHIP`, `contour`, `component`, `heightGrid`, `distKm`.

Scenes are film.html scenes: `{id, t0, t1, layer, fadeIn, fadeOut, draw(ctx, lt, t, api)}` (`lt` = t - t0). A shot's own UI goes in its `ui()` callback (it needs the shot's camera). UI that spans several shots (a gauge across a cut) is its own scene on layer 50-89. Layer 90+ is the orchestrator's (chapter cards).

Every frame must be a pure function of the frame number: no `Math.random`, `Date.now` or state carried between frames (seed noise with the frame or time).

## 3. Timing: `kit.K` (never hard-code seconds)

| Call | Returns |
|---|---|
| `K.T('drained')`, `K.Te('drained')` | word start / end (s) of a `{m:...}` marker |
| `K.lead('ft400', 3)` | 3 frames before the word: highlights land 2-4 frames early, never more than 0.2 s late |
| `K.seg('s004')`, `K.s0('s004')`, `K.s1('s004')` | segment `{start, end}` |
| `K.word('s169', 'base', nth)` | a word of a segment (case and punctuation ignored): `{w, start, end}` |
| `K.chapter(n)` | `{n, t0, t1, t1x, card, first, title}` |
| `K.XF`, `K.f(t)`, `K.end` | chapter-boundary dissolve (0.3 s); frame index; film end (last word + 1 s + 12 s end screen) |
| `python3 -I tools/frames.py drained most+2.5 s004 s169.end tall56-0.1` | film frames for `still.cjs --frames` |

The narration was re-timed once already (the payoff word moved 0.4 s). Everything keyed to markers follows automatically.

## 4. Shots

### terrainShot (HawaiiStage: DEM terrain and seafloor, live water level)

```js
kit.terrainShot({
  id, t0, t1, layer: 0, fadeIn, fadeOut,
  region: 'bigisland',            // a region (section 6); a region missing from the index falls back to 'bigisland' with a [hub] log
  stage: { origin, midGrid },     // optional stage options (one stage per region + vex + options; reuse the same object across shots)
  vex: 1,                         // 1.0 for anything that compares heights; at most 2 elsewhere (say "heights exaggerated" once)
  preset: 'noocean' | 'mauinui' | 'half' | 'drained' | 'today' | 'everest' | {...},
  state: {...} | (lt) => ({...}), // overrides: look, sun, water, waterCols, level, fog, set: {uniforms}, post: {exposure, sat, contrast}, mlook
  cam: CAMS name | {...} | [{t, cam, ease}] | (lt) => ({...}),
  push: 0.3, drift: 0.4,          // image scale growth per 10 s / heading drift deg/s from t0 (fold them into a cam fn for multi-move shots)
  level: -122 | (lt) => m | [{t, v, ease}],
  sun: [az, el] | (lt) => [az, el],
  mask: (lt, S) => ({ tex, bb, hero: 0.55, dim: 0.75, pass: 1 }) | null,   // R = hero fill, G = dimmed; pass: the masked grade steps aside
  mlook: { look: 'noocean', amt },
  grade: {...} | (lt) => ({...}), // shared-grade overrides, sparingly
  cut: {...},                     // a cut-away (see cutawayShot)
  world(ctx, lt, t, view) {},     // paper, postcards: drawn on the graded world, under the UI
  ui(ctx, lt, t, view) {},        // text, outlines, arrows, numbers (crisp, never graded)
})
```

Camera (`HawaiiStage.setCamera`): eye `lon`, `lat` and `alt` (km above present sea level) or `agl` (km above the ground or water below); target `tLon`, `tLat`, `tH` (m), or `heading`/`pitch`; `fov` (vertical deg); `shiftX`, `shiftY` (lens shift); `roll`; `dPitch`, `dYaw` (deg after aiming: a look-down tilt); `near`/`far` (km; ground cameras need near 0.005-0.02). Use the same height mode in every key of one move. Named cameras `CAMS`: `noocean` (frame 1), `noocean_plate`, `mauinui_one` (the ONE ISLAND composition), `mauinui_one_plate`, `mauinui_s`, `mauinui_sw`, `bigisland_w`, `bigisland_e`.

`view` in `world`/`ui`: `project(lon, lat, hm)` -> `[x, y]` or null; `visible(lon, lat, hm)`; `ground(x, y)` -> `[lon, lat, hm]` where that screen pixel meets the terrain or water (null: sky; place paper on a screen spot with it); `runs(rings, hm, {every, occlude})` -> screen runs split where hidden or off-screen (feed `ui.outline`); `horizonY()`; `level`; `sun` (`[az, el]` of the stage this frame: the paper kit's shadows follow it); `S` (the stage); `sec` (the section of a cut-away, else null).

Every uniform is reset from `TERRAIN_DEFAULTS` + preset + state on every frame, so shots on one stage never leak into each other.

### cutawayShot (the Earth cut open; ch6 s162-s172)

`kit.cutawayShot(spec)` is a terrainShot (defaults: region `bigisland`, vex 1, preset `drained`) with `spec.cut`:

```js
cut: {
  plane: { lon, lat, az: 90, side: 1, u0: -210, u1: 185, du: 0.25, bottomKm: 36, loadU: 0, waterTopMax: 0 },  // build-time (cached per plane)
  state: (lt) => ({ sag: 0..1, sagM: 7966, alphaKm: 90, oldFloor: -5000, crustM: 6500, floorLine: 0..1, trenchTop: -5470, trenchA: 0..1,
                    waterTop: 0, waterBot: -5000, waterA: 0..1, edgeA: 1, everest: { rise: 0..1, base: -12966 } }),
  everest: { u: 21, width: 16, front: 0.15, th: 0.6 } | null,
  cam: [{ t, u, d, alt, tu, te, tf, fov, ease }] | (lt) => ({...}),   // section coordinates: u km along the plane, d km toward the camera
}
```

The plane runs through `lon/lat` at azimuth `az` (90 = east-west); the half on the camera side (`side` 1 = right of the direction of travel: south for az 90) is removed from terrain and water, and a section wall shows the inside at true scale: layered basalt draping the surface, darker below the old sea floor; the top of the oceanic crust sagging under the load (schematic flexure, `sag` 0..1 animates it), the crust (pillow basalt, dikes, gabbro), the Moho, the mantle; `floorLine` draws the old flat sea floor across the dent; `trenchTop/trenchA` the last water in the trench; `waterA` the old ocean in cross-section, outside the rock only and never below `waterBot`. `view.sec` gives `project(u, e, f)`, `surf(u)`, `crustTop(u)`, `ev {u, W, base, summit, rise}`, `cam(c)`, `clip()`. The payoff (`payoff.js`) uses it end to end; ch6 reuses `CUT_PLANE`, `SECTION`, `EVEREST` and `ML` from there so s162-s172 is one cut. The east-west plane is a logged deviation from the script's north-south slice: along the meridian the data shows no trench at either rim; east-west meets the Hawaiian Deep about 125 km east of the summit.

### cineGlobeShot (CineGlobe)

```js
kit.cineGlobeShot({ id, t0, t1, preset: 'STORY' | 'HERO' | 'ESTABLISH', subject: [lat, lon],
  keys: [{ t, lat, lon, alt, tilt, heading, fov, lookOffset, ease }],   // lat/lon slerp, alt log-interpolated
  overlay: { canvas, bounds } | null, look: {...} | fn, post: {...}, sun: {sun, sunAz, sunEl}, grade, stars,
  ui(ctx, lt, t, view) { const runs = view.runs(rings); ui.outline(ctx, runs); ui.avoidRuns(runs); const q = view.project(lat, lon); } })
```

STORY: clouds 0.25 cleared over `subject`, haze 0.24, +0.5 stop over the first toolkit, no DOF; frame the subject at a third of the width or more (alt about 0.25-0.32 for the main Hawaiian chain). HERO: clouds 0.6, DOF 6, exposure x1.83 since round 3 (an oblique at alt 0.35 read luma 49-56; now 87-91). ESTABLISH: whole globe, world sun, 4 s at most. Globe budget: 10 % of runtime at most. `keys` may also be a function `(lt) => ({lat, lon, alt, tilt, heading, fov})`.

Fixed in round 3 (every globe shot, nothing to set): (1) the ocean: the 8k day texture painted bathymetric relief into the sea (the Hawaiian Ridge and the NW chain glowed cyan-white, the "shelf smears") and its dark ocean carried 16x16 JPEG macroblocks that showed as squares west of Hawaii; over open water the globe now reads the texture's mip 4 (one texel per macroblock) and compresses the brightness above the deep ocean by 85 % toward a muted teal (`GLOBE_OCEAN = {shelf: 0.85, oceanSmooth: 1, shelfCol}`; coasts stay sharp, land untouched). (2) the cloud seam: the cloud map's own date-line edge (its two sides come from different passes) drifted with the clouds to lon 180 - 0.04 t; the drift now starts 60° on (`GLOBE_CLOUDS = {base: 60, drift: 0.04, seam: 3}`, the seam stays between 120° E and 90° E, behind the limb of every Hawaiian shot) and is cross-faded over 3° either side with the map shifted half a world, and the cloud shader no longer wraps u with `fract()` (a mip hairline). Stills: STORY globe luma 95.9 (was 96.4), no squares, no glow; scratch `tk3/stills/globe_story2`, `globe_fix2`, `seam_new2`.

### blockShot (deprecated)

The old BlockStage pair (a box in a grey void). Do not use it for story shots; the payoff is a cutawayShot now.

### Transitions and camera helpers

- `kit.flight(c0, c1, t0, t1, {via, tvia, ease})`: one eased segment (one velocity peak), eye and target on Bezier paths; returns a cam fn.
- `kit.xfade(a, b, dur)`: b fades in while a keeps drawing (no dip to black); b's own UI waits until the dissolve ends. `kit.seq(shots, {fade})` chains them. Only between shots of the same scale: never xfade a globe into a terrain shot (two different pictures on top of each other); use `scaleMove`.
- `kit.scaleMove(spec)`: space to place (or back, or one region stack to another) as ONE camera path shared by every stage, so each hand-off dissolves between two renders of the same camera: detail resolves, nothing doubles.

```js
const mv = kit.scaleMove({ id: 'ch4-down', t0: K.T('x') - 0.5, t1: K.s1('s092'), xf: 0.5,          // xf 0.2 = a match-cut
  path: [{ t: 0, lat: 22.5, lon: -163, d: 7000, tilt: 0, heading: 0, fov: 30 },                   // orbit form: the point looked at,
         { t: 4.5, lat: 23.06, lon: -161.92, d: 25, tilt: 62, heading: 300, fov: 42, ease: E.inOut }],  // d km to the eye, tilt from straight down
  legs: [{ stage: 'globe', preset: 'STORY', subject: [23, -162] },
         { stage: 'terrain', region: 'nihoa', preset: 'today', handD: 900, ui(ctx, lt, t, v) { /* labels after the dissolve */ } }] });
scenes.push(...mv.shots);   // mv.at = film times of the hand-offs; mv.cam(t) = the orbit camera (for a UI scene that spans the move)
```

  `d` is log-interpolated (a log-altitude move: the same relative speed all the way down), lat/lon slerped, heading the short way; each key's `ease` is on the destination. Hand-off where `d` crosses the next leg's `handD` (default 900 km; or `at: [s]`): the 8k globe goes soft below about 700 km, and the terrain region stack must fill the whole view there (the log prints `[scaleMove] ... frame corner(s) outside region` otherwise: go lower or pick a wider stack such as `bigisland`, `main_chain`, `nwhi_chain`). Terrain legs blend their water toward the globe's navy ocean (`MOVE_WATER`) and their saturation toward 1 above 25 km, fully above 500 km (`match: [25, 500]`; `match: false` or a leg's own `water` turns it off): seen from far above, the film water renders as a saturated teal (red channel near 0) and the ocean flipped colour at the hand-off. Measured on the test move (`toolkit_test.html` 'move', frames 83/88/99/120): the islands of both legs line up within about 10-15 px at the 900 km hand-off (the globe's coasts are 5 km texels); the ocean stays (88,111,156) -> (69,100,152) -> (38,89,146) across it, luma 95.8 -> 95.6 -> 84.6. Keep the terrain end's `tilt` at 0.5° or more (the stage cannot look straight down), `h` (target height, m) 0 until the last hand-off. `orbitPath(keys)`, `orbitEye(c)` -> `{lat, lon, alt}` and `terrainCamOf(c)` (the terrain camera for an orbit camera) are exported for custom moves.
- `WHIP` = the whip-pan ease (6-8 frames). Sub-frame motion blur is not built yet.
- `kit.mixState(a, b, p)` blends two presets (numbers, arrays, colours, looks).

## 5. Look: presets, seabed, water, grade

| Preset | For |
|---|---|
| `noocean` | frame 1 (the NO OCEAN plate and its masked grade; only the Big Island takes the cap grade, the white rim fades past 190-245 km) |
| `mauinui` | Maui Nui with water (the ONE ISLAND light: warm grey shelf, muted far water, luma about 125-130) |
| `drained` | any fully drained shot (day look, old-coast cream line, bathtub ring) |
| `half` | mid-drain gold light |
| `today` | today's sea level |
| `everest` | the Everest regions (south light, -0.7 stop, lower snow gain, baked shadows lifted): everest_wide luma 196 to 168, blown 6.7 % to 0 % |

Film defaults (`TERRAIN_DEFAULTS.set`; `landLift` lifts black baked-shadow texels in a satellite composite): one depth-coded seabed for every shot (`seaMat` 1: reef flat 0 to -150 m in a warm mid-grey, grey sediment, dark slate basalt deep and on steep flanks; never a pale tan basin), water `film` (`WATER_FILM`: turquoise only in the first metres, deep by about 25-160 m, a muted steel blue offshore), wave normals at real swell scale, a surf band, a little glint. `nearAmt` (0..1) adds near-field basalt detail for close or look-down seabed; `capBB`, `lineFar`, `heroPass` are for masked looks. Other water: `water: 'turq' | 'lagoon' | 'ocean'` or `waterCols`.

The shared grade (`GRADE`) runs once on every stage: navy lift, cool shadows, warm highlights, vignette 0.2, frame-seeded grain 0.012. Masked looks (`MLOOKS.noocean`) read the stage's class mask: sky 0, water 0.25, drained seabed and land outside `capBB` 0.5 (flank grade), hero-filled 0.75 (passed through), cap land 1. Brightness: story shots 70+, the film 85-130 (measure with `tools/luma.py`).

## 6. Regions (`data/regions.json`; baked data is git-ignored, rebuild with `tools/rebuild_regions.sh`)

| Region | Grid | Stack | For |
|---|---|---|---|
| `bigisland` | 115 m, [-158.3,17.9,-153.8,21.8] | + hawaii_skirt | frame 1 and both thumbnails' plates, s001-s003, s047-s070, the cut-away s150-s176 |
| `mauinui` | 78 m, [-157.75,20.4,-155.9,21.35] | + bigisland + skirt | s004-s013, s089; ch1 uses it with `stage: CH1_STAGE` (legacy origin and mesh) so frame 1 is unchanged. Saddles: Maui-Lānaʻi -59 m, Maui-Molokaʻi -80 m, Molokaʻi-Lānaʻi -79 m, Kahoʻolawe -159 m (joins at -160 m) |
| `oahu_nuuanu` | 102 m | + skirt | s025-s043, s090: windward Oʻahu and the Nuʻuanu debris field (Tuscaloosa block about -2,691 m) |
| `pali` | 10 m | + oahu_nuuanu + skirt | s026-s031, s090 lookout ground shot (lookout 343 m, Konahuanui 957 m); soft at ground level: paper props or a higher camera |
| `kauai` / `waimea` | 56 m / 12 m | + skirt / + kauai | s080-s081, s091-s092 / the Waimea Canyon drop (s091) |
| `main_chain` | 333 m | + skirt | s049-s050 (-4,000 m pullback), s057 Hawaiian Deep strip, s080-s082; all main islands one ridge at -3,500 m |
| `kilauea_sf` / `halape` / `holei` | 31 m / 10 m / 10 m | nested | Kīlauea's south flank s014-s024, s044-s046, s086-s088 / Halape cove s016-s023 / Holei Sea Arch site s086-s088 (the arch itself is in no dataset) |
| `maunakea` / `kohala` / `kamaehu` | 10 m / 25 m / 59 m | + bigisland | summit road gag s065, label s061 / drowned reef terraces s076-s079 / Kamaʻehuakanaloa drained to about -1,500 m s150-s158 |
| `nwhi_chain` | 884 m (crosses 180°) | single | every NW Hawaiian flight s092-s111, s140-s146 |
| `nihoa` / `lalo` / `gardner` | 20 / 23 / 24 m | + nwhi_chain | s093-s099 / French Frigate Shoals s100-s108 / Puhahonu s109 |
| `nwhi_west` / `midway` / `kure` | 361 / 14 / 15 m | nested | Midway regional view s123-s146 / s112-s123, s137 / Green Island s140-s143 |
| `everest_wide` / `everest` | 92 / 14 m | nested | the Everest gag (paper climber, s064); use preset `everest` |

Known data faults (do not show these places close without a fix or a workaround): La Perouse Pinnacle and the Gardner pinnacles are below the grids (model them at their surveyed shape or leave them out); Nihoa's cliffs are too gentle (179 m against 273 m) and its colour flat ochre; Lalo and Kure lagoons are flat ETOPO (sat.jpg carries the look); the nwhi_west seamount caps read as snow when drained (tint them in your shot with a mask); everest_wide has north-face shadows baked into its colour, one a dark blob near (1050, 745) in its view camera (preset `everest` lifts them to rock grey with `landLift` and lights from the south; a summer re-bake is still open, keep that blob small or off-frame); the Pali lookout has cloud specks and 10 m softness; the 2018 East Island before/after needs dated imagery.

## 7. Islands, joins and masks (the sill.py rule on the production grid)

```js
const one = await kit.island({ region: 'mauinui', stage, bbox, level: -121.92, seeds: [PLACES.maui, PLACES.molokai, PLACES.lanai], step: 1 });
// {g (height grid), mask, rings ([[lon, lat], ...]: marching squares at the level, 2 Chaikin passes, specks and small holes dropped,
//  rings cut by the grid edge left open), areaKm2}
const br = kit.bridges(one, [maui0, molo0, lanai0], 11);       // new land within 11 km of two of today's islands (soft 0..255)
const tex = kit.maskTexture(one.g, { r: br, g: kaho.mask });   // R = hero fill, G = dimmed
mask: (lt) => ({ tex, bb: one.g.bb, hero: 0.38, dim: 0.75 }),
ui(ctx, lt, t, view) { ui.outline(ctx, view.runs(one.rings, -121.92, { every: 2 }), { width: 6, p }); }
```

Use the finest region that contains your bbox and `step: 1`, and project the outline at the level the water uses, so it sits on the rendered waterline. Every land bridge, join, island or lake you show or say comes from `island()` at the shot's level, never from a guess (ch1 logs a warning if Kahoʻolawe ever joins at -400 ft). Fills: 55-66 % for one hero shape, 35-40 % for joins; outlines 5-6 px white. Keep the natural colours when the land itself is the point (ONE ISLAND).

## 8. Paper: the cut-out kit and the postcard

The recurring paper characters are ready-made cut-outs of public-domain photos in `img/paper/` (every page, licence and edit in `img/SOURCES.md`; cut by `tools/paper_cut.py` from the specs in `tools/paper_specs/`):

| `kit.paper(name)` | What | Script |
|---|---|---|
| `tourist` (+ part `hat`) | the recurring paper tourist: a 1939 FSA traveller (Russell Lee), hand-tinted red aloha shirt, straw hat as a separate part | s008, s028-s029, s090, s176 |
| `suitcase` | his Gladstone bag (same photo) | s008 |
| `climber` | an NPS Denali mountaineer, red jacket, cut at the knees (base tab), frosted paper edge | s064-s065 |
| `jeep` | a 1942 FSA/OWI jeep with riders on a steep track, olive tint (`flip: true` to climb left to right) | s065 |
| `seal`, `seal_pup` | USFWS Hawaiian monk seal (side view) and a pup | s103-s108 |
| `albatross`, `albatross_fly` | USFWS Laysan albatross standing, and one in flight (wings out) | s114-s116 |

```js
const TOUR = await kit.paper('tourist');             // once per build (cached): paper edge, warm rim, the shared grade; parts loaded
const g = view.ground(1250, 900);                    // in world(): the ground under a screen spot (or use real lon/lat)
const r = kit.drawCutout(ctx, view, TOUR, { lon: g[0], lat: g[1], hm: g[2], hPx: api.H * 0.38,
  pop: F.clamp(lt / 0.5),                            // pop-up from flat with an overshoot (or hinge 0..1)
  lean: 0.3, wobble: 0.025, t: lt, seed: 1,          // lean into the wind (rad, about the base); seeded paper wobble
  hop: 0, squash: 0, turn: 0, flip: false,           // hop px, squash, paper turn 0..1 (0.5 edge-on, 1 = facing the other way), mirror
  parts: { hat: { x, y, rot } } });                  // a part at its place, nudged ({off, rot}) or detached (absolute screen x, y, rot)
// r = {x, y (base), top, w, h, parts: {hat: {x, y, w, h}}}: anchor labels and props to it
kit.drawCutout(ctx, view, SEAL, { lon, lat, wPx: api.W * 0.36 });                       // wPx instead of hPx for wide bodies
kit.drawCutout(ctx, view, BIRD, { x, y, wPx: 500, shadow: false, contact: false });    // flying: a screen point, no ground shadows
const sign = kit.paperProp('sign', { text: 'COMING SOON' });    // procedural paper props: 'sign', 'flag' (plain orange pennant), 'drop',
                                                                 // 'envelope' (no writing), 'tag' ('?'), 'tank'; draw them with drawCutout
```

Every cut-out gets a soft contact shadow under its base and a cast shadow laid on the ground away from the stage's sun (`view.sun`, the same sun as the terrain; `shadow: [dx, dy]` overrides, `shadowA` 0.3), a fold-out paper base tab for people and props (`base: false` for animals, the bag and the jeep), and per-character fixes (`sink`/`tilt` put the seal's belly on the sand). People stand at 35-40 % of frame height (`hPx: api.H * 0.38`), on the real terrain at their true spot; a figure that cannot be that big in the shot does not go in it. The sign's text is in-world: keep the sign 30 % of the frame height or more so its caps stay over 64 px. Paper beats in total: 1-1.5 min per film. Test page: `toolkit_test.html` 'cast' (all of the above on the dry ʻAuʻau Channel floor at -122 m; stills scratch `tk3/stills/cast2`).

```js
const pc = kit.makePostcard(photo, 'HAWAIʻI');                      // off-white card, photo inset, Anton title (ʻokina as U+2018), cap 26 % of the card
kit.drawPostcard(ctx, view, pc, { lon, lat, wKm, rot, p, lift, hm, alpha });
const card = kit.prepPaper(img, { edge: 3, edgeColor });            // your own cut-out (chapter photo): paper edge, rim, the shared grade
kit.drawStandee(ctx, view, card, { lon, lat, hPx, hop, squash, lean, hinge, shadowDir });   // older standee (no sun shadows, no parts)
kit.drawQuad(ctx, img, [tl, tr, br, bl]);
```

A postcard whose name must be read needs a card about 450 px wide on screen or more. Photos must be real public-domain images with a licence line (`img/postcard_bigisland.jpg`: USGS, Pohoiki, public domain, in `engine/ASSETS.md` and `img/SOURCES.md`). A new character: ask in `requests/chN.md`; the toolkit owner cuts it with `tools/paper_cut.py SPEC --model isnet-general-use.onnx --srcdir DOWNLOADS --outdir img/paper` (IS-Net, Apache-2.0, downloaded to the scratchpad and deleted after; never in git) and logs it in `img/SOURCES.md`.

## 9. Text and graphics (`kit.ui`, type.js with the floors enforced every frame)

| Call | Use |
|---|---|
| `ui.block(ctx, lines, x, y, o)` | THE text block. `lines: [{text | words: [{w, c}], role: 'headline' | 'kicker' | 'title' | 'label', cap, fam: 'label' | 'head', qualifier, color}]`; `o`: `anchor` 'left' | 'right' | 'center', `p`, `out`, `bar` (accent colour, null = none), `barP`, `plate: false` (ink straight on the sky: no plate, bar or padding), `color`, `glow` (the thumbnails' soft white halo), `wordTimes` + `lt` (whole words on their spoken words), `grow` (the plate widens and deepens with the revealed words and lines), `at: [{x, y, anchor}]` (candidate slots: the first inside the safe area and clear of obstacles by `clear` px, default 40, wins), `extra` (room for a number line: `box.inner`) |
| `ui.label(ctx, s, ax, ay, o)` | map label with pin and leader, anchored ON the surface point. `order` (default above, above-left, left, above-right, right, below): the first placement inside the safe area clear of blocks, labels, obstacles and its own pin; if none fits it is not drawn (its anchor is at the frame edge). Draw blocks first |
| `ui.avoid(box)`, `ui.avoidRuns(runs, step)`, `ui.boxOf(points, pad)` | obstacles for the placers: a bar, a subject's projected bbox, outline points (call before `block`/`label`) |
| `ui.number(ctx, v, x, y, o)` | odometer with grouping commas, driven by the true value; `to` fixes the digits, `prefix`, `unit`, `minus`, `lead0: false`, `win` (the window digits roll inside) |
| `ui.gauge(ctx, {p, out, level, range, to, unit, value, pulse})` | the persistent SEA LEVEL gauge, top-left, plate 150 px: water column (64 px, linear over the shot's own `range` m), title, the current value in the plate (cap 112, yellow, the plate is the odometer window). Fade it out (`out`) whenever no level is changing; `pulse` = a hero-number moment |
| `ui.outline`, `ui.line`, `ui.arrow`, `ui.pin`, `ui.fill` | outline 6 px white + under-stroke + glow; meaningful lines 9-12 px; arrows 14 px body; solid, never dashed |
| `kit.okina(s, fam)` | Anton has no usable ʻokina (it draws a mid-dot): Anton text uses U+2018; `ui.block` does it for you; Barlow keeps U+02BB |

Floors and limits (checked every frame, failures log `[typeqc] FAIL f=...`, `{"strict":1}` throws): must-read caps 64 px or more (labels, names, gauge title), any text 48 px or more, headlines Anton 96-120 at 4 words at most, kicker 2 words (a `qualifier: true` kicker may carry a mandatory qualifier up to 4 words: logged), numbers Anton 150-190 (gauge 110-120); one text block per frame, plus at most one map label plus the gauge, 10 visible words at most; must-read text inside the 5 % margins, below the top 8 % and above y = 670 (top 62 %). Colour words only as a two-colour legend that matches fills on screen (LAND in hero orange, WATER in cyan), never a single emphasis word. No sources, credits, emojis or AI wording on screen; never drop a qualifier (MOST OF, ABOUT, FROM ITS TRUE BASE). Spell Hawaiian names with ʻokina (U+02BB) and kahakō in the strings.

Layouts rotate (never one template): ink on the sky in the thumbnails' slots (NO OCEAN top-right, ONE ISLAND top-left), a plate top-right over the sky with the gauge top-left (names), a number block in the sky placed clear of the subject and its bar (payoff), label-only beats. Palette: hero `#FF5A36`, cyan `#3DE3FF`, yellow `#FFD23F` (numbers, gauge, bars), text `#F4F6FA`, ink `#10161E`, plate `rgba(6,9,15,0.86)`, red `#E8412C` sparingly. Numbers: at most 2 spoken numbers and 1 hero number in any 60 s; each hero number an image on its word, no device more than 3 times. Order in `ui()`: outlines and lines first, then the block, then labels.

## 10. The payoff and ch6

`buildPayoff(api, kit, scenes, {t0, t1})` (default s168 - 1.0 s to s172 end + 2.2 s): the cut-away, VE 1.0; the camera tips down through the cut to the dented base on {basedent}; the yellow bar beside the summit column climbs from the dented base (17,170 m under the DEM summit) while ABOUT 56,000 FT rolls, both landing on {tall56}; Everest's slab (its real profile, 8,849 m) rises out of the same base on {ev3} with a solid white tick at its summit; at {underwater} the old sea-level line glows and the old ocean shows between the old sea floor and sea level, outside the rock only; at {see} the camera eases back to the whole cut-away. The number block is placed in the sky clear of the bar (40 px) and the summit; the MAUNA LOA label sits above the summit. ch6 builds s159-s167 with the same `CUT_PLANE` (opening the cut at {slice} by easing `sag` and the section in) and hands over at s168 - 1.0 s.

Section tones (round 3, `lab/hawaii/section.js`): three bands that read at 390 px: the volcanic pile is the LIGHT layer (warm basalt grey-brown, albedo luminance about 0.11, flow layering kept), the oceanic crust the DARK cool slate band (about 0.035, pillow/dike/gabbro grain stronger), the mantle a MID olive green (about 0.075); the crust top is a darker seam, the Moho a paler line, the depth falloff only 0.86 at -30 km; Everest's slab lifted to a pale limestone (about 0.19) so it stays lighter than the pile behind it. Payoff stills luma 112-118 (was 96-114), near-black 3.6 % or less; phone sheet scratch `tk3/an/payoff_r3b_390.jpg`.

## 11. Rendering and checking stills

```bash
cd engine
node still.cjs --page film.html --q '{"ep":"ep02","only":"ch3"}' --frames $(python3 -I www/ep/ep02/tools/frames.py s049+0.5 s057 s062.end) --w 1920 --h 1080 --outdir DIR
node still.cjs --page ep/ep02/payoff_test.html --q '{}' --frames $(python3 -I www/ep/ep02/tools/frames.py basedent tall56+0.3 underwater+0.8) --outdir DIR
node still.cjs --page ep/ep02/toolkit_test.html --q '{"test":"region","region":"midway"}' --frames 30 --outdir DIR      # also globe, paper, xfade
node still.cjs --page ep/ep02/toolkit_test.html --q '{"test":"move"}' --frames 0,83,88,99,120 --outdir DIR                # scaleMove globe -> terrain ("leg":0|1 = one stage only)
node still.cjs --page ep/ep02/toolkit_test.html --q '{"test":"cast"}' --frames 54,100,160,222 --outdir DIR                # the paper kit on the terrain
node still.cjs --page ep/ep02/toolkit_test.html --q '{"test":"globeq","lat":21,"lon":-160,"alt":0.6,"at":500}' --frames 15030 --outdir DIR   # any globe camera at film time 'at'
python3 www/ep/ep02/tools/sheet.py DIR/sheet390.jpg 390 DIR/f*.jpg       # phone sheet: judge every frame at 390 px
python3 www/ep/ep02/tools/luma.py DIR/f*.jpg                              # luma 70+ per story shot, film 85-130, near-black under 15 %
python3 ../channel/niche/work/gate.py DIR/f000586.jpg                     # clone gate: tan <= 10 %, red <= 3 %, drain-clone distance >= 11.71
python3 www/ep/ep02/tools/frame1_check.py DIR/f000000.jpg THUMB.jpg      # SSIM against a thumbnail (frame 1, s006)
```

Q flags: `only` ("ch1".."ch6"), `draft` (no MSAA, light grids, globe ss 1: drafts only), `qc` (log caps, blocks, labels, words every frame), `strict` (a type QC failure throws), `perf` (sync the GPU so `[perf]` times are real), `dev` (placeholder labels), `nolabel` (frame 1 without NO OCEAN), `dbgCam`, `dbgLabel` (placer choices). Keep each local still under about 60 s; never more than two Chromium renders at once (memory). Put stills in the scratchpad, never in git.

Before handing a chapter on: stills at every marker the chapter uses, looked at full size and as a 390 px sheet; no `[typeqc] FAIL`; luma and near-black in range; the gate on every frame that could be a thumbnail or reads as a drain; every hero number on its word (`K.lead`), every label on a projected surface point, every join from `island()`; nothing static over 2 s, a new visual event every 3-5 s (2-3 s in minute 1); no emojis, no sources, no AI wording (PLAYBOOK section 1 grep).

## 12. Measured cost (local SwiftShader, 4 cores, 1920x1080)

| Stage | Per frame |
|---|---|
| Terrain, full quality (MSAA 4; `mauinui` stack with the 1500² Big Island mesh) | 10-20 s (a saved ch1 still 18-25 s) |
| Cut-away (terrain + section wall + Everest slab) | 9-15 s per saved still |
| Terrain, `draft` | about 4-6 s |
| CineGlobe STORY, ss 2 | 2.8-3.2 s (6.4 s on the first frame) |
| scaleMove test (globe legs / terrain legs from 900 km down) | 5-6 s / 15-60 s per saved still |
| Paper cast on the terrain (`mauinui`, 4-7 cut-outs) | 10-18 s per saved still (the cut-outs add well under 0.1 s) |
| Shared grade + copy | 0.1-0.35 s |
| UI | under 0.05 s; the first frame of ch1 adds about 10 s for the 78 m island grids (cached after) |

The film renders on the Colab L4 (not measured yet for these stages).
