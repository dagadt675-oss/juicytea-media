# ep02 shot toolkit (for the chapter builders)

Everything for ep02 "Why Can't You See Most of Hawaii? (Look Down)" is built with `shared.js` in this folder. It sits on the ep02 prototypes (`lab/hawaii` HawaiiStage and BlockStage, `lab/globe/cineglobe.js`, `lab/type/type.js`, `lab/story/story.js`) and gives every stage one renderer, one grade and one type system, so the film looks like one film.

Rules that win over anything here: `PLAYBOOK.md`, `PLAYBOOK_craft.md`, `PLAYBOOK_production.md` (repo root). Look book: `longform/ep02-hawaii/research/visual/visual_plan.md`. Shot list: the `visual` and `onscreen` fields of `longform/ep02-hawaii/script/script_locked.json`.

## Files

| File | What |
|---|---|
| `edit.js` | The orchestrator (film.html contract). Loads `ch1.js` .. `ch6.js`, fills uncovered time with a logged placeholder, no post on top (the grade already ran), logs type QC and timings per frame |
| `shared.js` | The toolkit (this document) |
| `ch1.js` | Chapter 1. Built: s001-s006 (DEMO 1 frame 1 = NO OCEAN thumbnail in motion, DEMO 2 Maui Nui -400 ft ONE ISLAND). The rest of the chapter is open |
| `ch2.js` .. `ch6.js` | Stubs: `export async function build(api, kit, scenes)` |
| `payoff.js` | DEMO 3, the payoff block (s168-s172). `buildPayoff(api, kit, scenes, {t0, t1})`: ch6 calls it |
| `payoff_test.html` | Stand-alone test page for the payoff (film frames) |
| `toolkit_test.html` | Smoke tests: `{"test":"globe"}`, `{"test":"paper"}`, `{"test":"xfade"}` |
| `testrt.js` | The small film.html-compatible runtime the two test pages share |
| `timing.json` | Copy of Rodney's narration timing (`scratchpad/audio/ep02_vo/timing.json`). Re-copy it whenever the narration is re-timed: every beat keys off markers, so the film follows |
| `tools/frames.py` | Marker or segment to film frame: `python3 -I tools/frames.py drained most+2.5 s004 tall56-0.1` |
| `tools/camsearch.html` | Dev page: renders many HawaiiStage cameras in one session (used to recover the ONE ISLAND plate camera) |

Render (from `engine/`):

```bash
node still.cjs --page film.html --q '{"ep":"ep02","only":"ch1"}' --frames 0,509 --w 1920 --h 1080 --outdir DIR
node still.cjs --page film.html --q '{"ep":"ep02"}' --frames $(python3 -I www/ep/ep02/tools/frames.py one+0.3) --outdir DIR
node still.cjs --page ep/ep02/payoff_test.html --q '{}' --frames $(python3 -I www/ep/ep02/tools/frames.py tall56-0.1 underwater+0.8) --outdir DIR
```

Q flags (film.html and the test pages): `only` ("ch1".."ch6"), `draft` (no MSAA, light grids, globe ss 1: drafts only), `qc` (log type QC every frame), `strict` (a type QC failure throws), `perf` (sync the GPU after each stage so the `[perf]` times are real), `dev` (placeholder labels), `nolabel` (ch1: frame 1 without the NO OCEAN block, for the thumbnail SSIM check), `dbgCam` (log each terrain shot's camera), `dbgLabel` (log the label placer's choices).

## The chapter module

```js
// chN.js
import { PLACES, PAL, E, F } from './shared.js';
export async function build(api, kit, scenes) {
  const { K, ui } = kit;
  const ch = K.chapter(2);                       // {t0, t1, card}: the card sits 0.9 s before the first voiced segment
  scenes.push(kit.terrainShot({ id: 'ch2-pali', t0: ch.t0, t1: K.s1('s029') + 0.4, region: 'pali', preset: 'today',
    cam: 'pali_ne', push: 0.3, drift: 0.4,
    ui(ctx, lt, t, view) { const q = view.project(...PLACES.pali, 370); if (q) ui.label(ctx, 'PALI LOOKOUT', q[0], q[1], { t, p: F.clamp((t - K.lead('pali')) / 0.3) }); } }));
}
```

`kit` holds: `K` (timing), `ui` (type), `hub` (renderer and stages), `terrainShot`, `blockShot`, `cineGlobeShot`, `island`, `maskTexture`, `flight`, `mixState`, `keyAt`, `valAt`, `xfade`, `seq`, `makePostcard`, `drawPostcard`, `drawStandee`, `drawQuad`, `prepPaper`, `gradeCanvas`, `CAMS`, `PLACES`, `PRESETS`, `REGIONS`, `PAL`, `E`, `F`, `T` (type.js), `P` (story.js).

Scene objects are film.html scenes: `{id, t0, t1, layer, fadeIn, fadeOut, draw(ctx, lt, t, api)}`. Base shots are layer 0 and must cover every frame. A shot's own UI goes in its `ui()` callback (it needs the shot's camera); UI that spans several shots (a gauge across a cut) is its own scene on layer 50 or more.

## Timing: `kit.K`

| Call | Returns |
|---|---|
| `K.T('drained')`, `K.Te('drained')` | word start / end (s) of a `{m:...}` marker |
| `K.lead('ft400', 3)` | 3 frames before the word: highlights land 2-4 frames early, never more than 0.2 s late |
| `K.seg('s004')`, `K.s0('s004')`, `K.s1('s004')` | segment `{start, end}` |
| `K.word('s169', 'base')` | first word of a segment matching (case and punctuation ignored): `{w, start, end}` |
| `K.chapter(n)` | `{t0, t1, card, first}` |
| `K.f(t)`, `K.end` | frame index; film end (last word + 1 s + 12 s end screen) |

Never hard-code seconds: the narration has already been re-timed once (v2 moved the payoff by 0.4 s).

## One renderer, lazy stages: `kit.hub`

One `THREE.WebGLRenderer` for the whole page. A stage (terrain per region and exaggeration, block pair, globe) is created and loaded the first time a scene draws it, then cached; only stages whose scenes are active at a frame render in that frame. A crossfade renders both stages into the same renderer one after the other (each frame is copied to the 2D compositor before the next stage draws). Chunks that never touch the globe never load its 8k textures.

Per stage: WORLD to its HDR target, its own tonemap, then `hub.rtOut` (RGBA8, alpha = class mask), then the SHARED GRADE pass, then the canvas, then `ctx.drawImage`. Stage posts run with vignette 0 and grain 0; the shared grade adds them once.

## The shared grade

`GRADE` (shared.js): navy lift (blacks never pure black), cool shadows, slightly warm highlights, vignette 0.2, frame-seeded grain 0.012, contrast and saturation 1.0. Override per shot with `grade: {vignette: 0.12}` or `grade: (lt) => ({...})`, sparingly: the point is one look.

Masked looks (`MLOOKS`) use the terrain stage's class mask (sky 0, water 0.25, drained seabed 0.5, today's land 1). `noocean` is the NO OCEAN thumbnail grade (packaging `fix_noocean` cand_2, `build.py`) ported to the shader: rainforest green and rust on the cap, darker cool slate flank, deeper blue sky top and the warm anti-solar belt. Water passes through untouched, so the look can fade while the sea refills. Use it via the `noocean` preset or `mlook: {look: 'noocean', amt}`.

2D world assets (paper cards, photos) get the same grade once at prep time: `kit.gradeCanvas(canvas)` (`prepPaper` and `makePostcard` already do).

## terrainShot

```js
kit.terrainShot({
  id, t0, t1, layer: 0, fadeIn, fadeOut,
  region: 'bigisland',            // REGIONS key or a region of ep/ep02/data/regions.json (see Regions)
  vex: 1,                         // 1.0 for anything that compares heights; at most 2 elsewhere (own stage per value; say "heights exaggerated" once)
  preset: 'noocean' | 'mauinui' | 'half' | 'drained' | 'today' | {...},
  state: {...} | (lt) => ({...}), // overrides: look, sun, water, level, fog, set: {uniforms}, post: {exposure, sat, contrast}
  cam: 'noocean' | {...} | [{t, cam, ease}] | (lt) => ({...}),
  push: 0.3,                      // image scale growth per 10 s, accumulated from the shot's t0 (number or fn)
  drift: 0.4,                     // heading drift deg/s around the eye, accumulated from t0: for a long shot with several moves,
                                  // fold the hold moves into a cam function instead (ch1.js does: they fade out during its flight)
  level: -122 | (lt) => m | [{t, v, ease}],
  sun: [az, el] | (lt) => [az, el],
  mask: (lt, S) => ({ tex, bb, hero: 0.58, dim: 0.75 }) | null,
  mlook: { look: 'noocean', amt: 1 },
  grade: {...},
  world(ctx, lt, t, view) {},     // paper, postcards: drawn on the graded world, under the UI
  ui(ctx, lt, t, view) {},        // text, outlines, arrows, numbers (crisp)
})
```

Every uniform is reset from `TERRAIN_DEFAULTS` + preset + state on every frame (pure function of the frame, no leaks between shots). Camera (HawaiiStage.setCamera): eye `lon`, `lat` and `alt` (km above present sea level) or `agl` (km above ground or water below); target `tLon`, `tLat`, `tH` (m); `fov` (vertical degrees); `shiftX`, `shiftY` (lens shift, frame units: keeps a thumbnail crop); `roll`; plus `dPitch` and `dYaw` (degrees, applied after aiming: a "look down" tilt). Use the same height mode (alt or agl) in every key of one move. Named cameras: `CAMS` (`noocean` = frame 1, `mauinui_one` = the ONE ISLAND composition, `bigisland_w`, `bigisland_e`, `mauinui_s`, `mauinui_sw` and the two plate versions).

`kit.flight(c0, c1, t0, t1, {via, tvia, ease})` returns a camera function: one eased segment (a single velocity peak), eye and target on quadratic Bezier paths through optional via points. `kit.mixState(a, b, p)` blends two presets (numbers, colours, looks).

The `view` passed to `world` and `ui`:

| Member | What |
|---|---|
| `view.project(lon, lat, hm)` | screen `[x, y]` or null (hm in m; default the surface or the water) |
| `view.visible(lon, lat, hm)` | false when terrain hides the point (ray-march, curved Earth) |
| `view.runs(rings, hm, {every, occlude})` | lon/lat rings to screen runs, split where hidden or off-screen: feed `ui.outline` |
| `view.horizonY()` | screen y (0..1) of the far horizon |
| `view.level`, `view.S` | water level (m), the HawaiiStage |

### Islands, masks and outlines (the sill.py rule on the production grid)

```js
const one = await kit.island({ bbox: [-157.85, 20.4, -155.9, 21.35], level: -121.92, seeds: [PLACES.maui, PLACES.molokai, PLACES.lanai] });
// one = {g (height grid), mask (Uint8), rings ([[lon, lat], ...]), areaKm2}
const tex = kit.maskTexture(one.g, { r: one.mask, g: kahoolawe.mask });   // R = hero fill, G = dimmed and desaturated
mask: (lt) => ({ tex, bb: one.g.bb, hero: 0.58, dim: 0.75 }),
ui(ctx, lt, t, view) { kit.ui.outline(ctx, view.runs(one.rings, -119), { width: 6, p }); }
```

The fill lives in the terrain shader (the relief shows through, 55-66 %); the white outline is drawn in the UI layer. Every land bridge, join, island or lake label must come from `island()` (or sill.py) at the shot's level, never from a guess. ch1 logs a warning if Kahoʻolawe ever joins the fused island.

## blockShot (Mauna Loa vs Everest from the true base)

```js
kit.blockShot({ id, t0, t1, blocks: { half: 10, gap: 8 },
  cam: [{ t, eye: [x, y, z], target: [x, y, z], fov, ease }],   // km: x east, y up, z toward the camera; base plane y = 0
  ev: 0..1 | fn | keys,      // Everest rises out of the shared base plane
  water: 0..1 | fn,          // translucent sea volume from the base up to Mauna Loa's present sea level
  line: 1,                   // Mauna Loa's luminous sea-level line on the cut faces
  ui(ctx, lt, t, view) {} }) // view.p(x, y, z) -> [sx, sy]; view.ml {x0, x1, top, sea, floor}; view.ev {x0, x1, top, rise}
```

VE is 1.0 by construction. Mauna Loa's column is 17,170 m from the DEM summit to the true base (about 56,000 ft, USGS); Everest's summit is scaled to the surveyed 8,849 m. See `payoff.js` for the full beat (tip down the cut face, bar and counter landing on `tall56`, Everest rising on `ev3`, the sea volume on `underwater`).

## cineGlobeShot

```js
kit.cineGlobeShot({ id, t0, t1, preset: 'STORY' | 'HERO' | 'ESTABLISH', subject: [lat, lon],
  keys: [{ t, lat, lon, alt, tilt, heading, fov, lookOffset, ease }],   // lat/lon slerp, alt log-interpolated
  overlay: { canvas, bounds } | null,       // fill in the globe texture at 55-66 % (lib/geo.js fillEquirect)
  look: {...earth uniforms} | fn, post: {...CineGlobe post}, sun: {sun, sunAz, sunEl}, grade, stars,
  ui(ctx, lt, t, view) { ui.outline(ctx, view.runs(rings)); const q = view.project(lat, lon); } })
```

STORY: clouds 0.25 and cleared over `subject`, haze 0.24, brighter exposure and ocean, no DOF (mean luma about 79 in the smoke test; keep story shots at 70 or more). HERO: clouds 0.6, DOF 6 for low obliques. ESTABLISH: whole globe, world sun. Globe budget: at most 10 % of runtime, 4 s per shot. Known globe defect still open: a vertical seam in the cloud texture near 160° W (visible in the smoke test); keep clouds low or the seam off-frame until the cloud map is fixed (look book U10).

## Paper and the postcard device (story.js)

```js
const card = kit.prepPaper(img);                                    // story.prepCard + the shared grade
kit.drawStandee(ctx, view, card, { lon, lat, hPx: api.H * 0.37, hop, squash, lean, hinge });   // returns {x, y, top, w, h}
const pc = kit.makePostcard(photo, 'HAWAIʻI');                      // off-white card, photo inset, place name in Anton yellow
kit.drawPostcard(ctx, view, pc, { lon, lat, wKm, rot, p, lift, hm });   // drops in (p 0..1), lands flat on the terrain, hinge lift
kit.drawQuad(ctx, img, [tl, tr, br, bl])                             // any image onto a perspective quad (affine triangles)
```

Standees stand on the real terrain at 35-40 % of frame height with a soft contact shadow. Photos must be real public-domain images with a licence line in `engine/ASSETS.md`; `ch1.js` uses `img/postcard_bigisland.jpg` for the s003 postcard only when that file exists (it does not yet), and never a stand-in. `img/_test/` is git-ignored and holds our own renders for the smoke tests.

## Type: `kit.ui` (type.js with the floors enforced)

| Call | Use |
|---|---|
| `ui.block(ctx, lines, x, y, {anchor, p, out, bar, barP, wordTimes, lt, extra, platePre})` | THE text block on a plate with an 8 px accent bar. `lines: [{text | words: [{w, c}], role: 'headline' | 'kicker' | 'title' | 'label', cap, qualifier}]`. `wordTimes` reveals whole words on their spoken words |
| `ui.label(ctx, s, ax, ay, {side: 'auto', dist, accent, t, p})` | map label with pin and leader; `auto` picks right, left, above or below inside the safe area and clear of the block (draw the block first); fades as its anchor leaves the frame |
| `ui.number(ctx, v, x, y, {cap, to, prefix, unit, minus, align, measure})` | odometer with grouping commas; drive it with the true value (it never passes through wrong values) |
| `ui.gauge(ctx, {p, level, range, hero: {v, to, p, unit}})` | the persistent SEA LEVEL gauge, top-left, plate 150 px; the water marker moves on a square-root scale; hero mode hangs one big yellow number under the plate |
| `ui.outline`, `ui.line`, `ui.arrow`, `ui.pin`, `ui.fill` | the type.js line specs (outline 6 px white + under-stroke + glow, lines 10 px, arrows 14 px body) |

Caps: number 170 (150-190), headline 108 (96-120), title 150 (the NO OCEAN thumbnail text), label 64, kicker 52. `T.FLOOR` is set to must 64 and any 48. Every frame `ui` checks: a cap under its floor (raised to the floor and logged), more than one text block, more than 10 visible words, a headline over 4 words, a kicker over 2 words (a `qualifier: true` kicker may carry a mandatory qualifier up to 4 words, logged by design), must-read text below y = 670, in the top 8 % or outside the 5 % margins. Failures log `[typeqc] FAIL f=... ...`; `{"strict":1}` throws. Colour words are the legend (`{w: 'ISLAND', c: PAL.hero}`), never a key box.

## Transitions

`kit.xfade(a, b, 0.5)`: b fades in over 0.5 s while a keeps drawing until the fade ends (no dip to black). `kit.seq(shots, {fade})` chains them. One continuous camera (`flight`) beats a cut whenever subject and framing are shared (PLAYBOOK_craft 8). `WHIP` is the whip-pan ease (6-8 frames); sub-frame motion blur is not built yet (look book U14).

## Regions

`REGIONS.bigisland` is the legacy `lab/hawaii/data` bake (hero 4096² over the main islands from 158.3° W to 153.8° W, ETOPO 30" skirt). Frame 1 and both thumbnails were rendered from it, so ch1's demo stays on it. Every other region (`mauinui`, `oahu_nuuanu`, `pali`, `kauai`, `waimea`, `kilauea_sf`, `halape`, `holei`, `kamaehu`, `kohala`, `maunakea`, `main_chain`, `nwhi_chain`, `nihoa`, `lalo`, `gardner`, `nwhi_west`, `midway`, `kure`, `everest_wide`, `everest`) is listed in `data/regions.json` (spec `tools/regions_spec.json`, baked by `lab/hawaii/tools/region_bake.py` into `data/<name>/`, git-ignored except `meta.json` and `regions.json`). `terrainShot({region: 'mauinui'})` loads the region's stack (1-3 nested layers, finest first) through `HawaiiStage.loadRegion('/ep/ep02/data', name)`; a region missing from the index falls back to `bigisland` with a `[hub]` log line. Smoke test: `toolkit_test.html` `{"test":"region","region":"midway","cam":{...}}`. Masks and outlines (`island()`) read the finest layer that contains their bbox; use the finest region for close Maui Nui work (`mauinui`, about 80 m against 120 m in `bigisland`).

## Measured cost (local SwiftShader, 4 cores, 1920x1080, `{"perf":1}`)

| Stage | Per frame |
|---|---|
| Terrain, full quality (MSAA 4, 1500² + 900x680 grids, ray-marched shadows) | 10-14 s (about 19 s per saved still including UI and JPEG) |
| Terrain, `draft` | about 4-6 s |
| CineGlobe STORY, ss 2 | 2.8-3.2 s (6.4 s on the first frame) |
| BlockStage pair | 1.5-2.8 s |
| Shared grade + copy to the compositor | 0.1-0.35 s |
| UI layer (type, outlines with occlusion) | under 0.05 s |

Local rendering is for stills and phone sheets only; the film renders on the Colab GPU. Keep each local still under about 60 s.

## Checks before a chapter is handed on

1. Stills at every marker the chapter uses (`tools/frames.py`), looked at full size and as a 390x219 phone sheet.
2. No `[typeqc] FAIL` in the log (`{"qc":1}` prints every frame's caps, blocks, labels and words).
3. Mean luma of story shots 70 or more; nothing near-black over 15 % unless it is an establishing globe.
4. Every hero number lands on its word (`K.lead`), every label is anchored to a projected point, every join or island from `island()`.
5. No emojis, no sources on screen, never AI wording (PLAYBOOK section 1 grep).
