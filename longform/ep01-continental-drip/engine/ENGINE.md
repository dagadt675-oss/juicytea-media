# Myth Juice film engine — API reference (for building scenes)

Everything renders in headless Chromium (software WebGL) at 1920x1080, 30 fps, and is a pure function of time.
Root: `engine/` (absolute path in the task brief). Web root: `engine/www/`.

## Files
- `www/film.html` — runtime. Loads `www/ep/<EP>/edit.js` and `www/ep/<EP>/timing.json` (VO word timings + markers).
- `www/lib/globe.js` — `Globe`: NASA Blue Marble (relief+bathymetry) day texture, VIIRS night lights, DEM normal-map relief, atmosphere, starfield.
- `www/lib/fx.js` — 2D primitives (text, headline, pill labels, counters, glow paths, Ken Burns, chapter cards, vignette).
- `www/lib/geo.js` — Natural Earth GeoJSON helpers (find countries, fill overlay textures, projected outlines, great-circle arcs, true-size moves).
- `www/lib/shots.js` — shot factories that return scene objects: `globeShot`, `photoShot`, `statShot`, `barsShot`, `textShot`, `overlay`.
- `www/geo/*.geojson` — Natural Earth: `ne_50m_admin_0_countries`, `ne_110m_admin_0_countries`, `ne_10m_admin_0_countries`, `ne_50m_coastline`, `ne_50m_lakes`, `ne_50m_rivers_lake_centerlines`, `ne_50m_land`, `ne_110m_populated_places_simple`.
- Tools: `node still.cjs --page film.html --q '{"ep":"EP"}' --frames 0,90,300 --outdir DIR` renders specific frames to JPEG (fast check).
  `node render.cjs --page film.html --q '{"ep":"EP"}' --start F0 --frames N --jobs 3 --out out.mp4` renders video.

## edit.js contract
```js
import * as F from '../../lib/fx.js';
import { globeShot, photoShot, statShot, barsShot, textShot, overlay, camAt } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, fillEquirect, makeCanvas, centroid, moveRings, gcLine, projectPath, strokeProjected, fillProjected } from '../../lib/geo.js';
export const scenes = [];               // filled in init()
export async function init(api) {       // async: load images, geo, build overlays, push scenes
  await api.globe();                    // creates/initialises the shared Globe (api.g)
  await api.loadImages(['ep/EP/img/x.jpg']);  // then api.img('ep/EP/img/x.jpg') returns the HTMLImageElement
  const T = (m, w) => api.T(m, w);      // marker time (s) from timing.json; w = 'end' for word end
  scenes.push(globeShot({...}));
}
// optional: export function post(ctx, t, f, api) {...}  (default: vignette)
```
Scene object: `{t0, t1, layer=0, fadeIn=0, fadeOut=0, draw(ctx, lt, t, api)}` — `lt` = local time (t - t0). Scenes are drawn in
(layer, t0) order every frame they are active. Base shots are layer 0 and must cover every frame (no gaps → no empty frames).
Overlays (layer ≥ 5) draw on top of base shots. A scene with fadeIn renders into an offscreen layer and is alpha-blended over
what is below → use fadeIn on the INCOMING scene for crossfades (keep the outgoing scene running until incoming fade ends).

## Globe camera (`api.drawGlobe(ctx, state, look)` or `globeShot({keys})`)
state: `{lat, lon, alt, tilt=0, heading=0, fov=34, sun:'camera'|'world', sunAz=-35, sunEl=28, sunLat, sunLon, lookOffset:[x,y]}`
- `alt` = camera altitude above the surface in Earth radii (1 = 6371 km). Whole globe ~2.4–3.0; continent ~0.8–1.2; country ~0.3–0.5;
  region ~0.1–0.2 (texture is ~5 km/px: below alt≈0.15 it gets soft; prefer tilt to add depth instead of zooming further).
- `tilt` 0 = straight down; 30–55 = cinematic oblique with horizon & atmosphere. `heading` rotates view (0 = north up).
- `sun:'camera'` = key light relative to camera (always nicely lit). `sun:'world'` + sunLat/sunLon = real day/night terminator with city lights.
- keys for `globeShot`: `[{t, lat, lon, alt, tilt, heading, fov, ease}]`; lat/lon interpolate along great circles, alt logarithmically.
  `drift` (deg/s heading) keeps holds alive (default 0.25). Never hold a fully static frame > 3 s.
look uniforms: `{dim:0..1 (darken everything but overlay), desat, ovAlpha:0..1 (overlay fill opacity), relief:0..1, nightAmt, exposure}`.
Overlay (highlight fill): `const ov = makeCanvas(2048,1024); fillEquirect(ov, bounds, [feature], {color:'#FF5A36', alpha:.8, glow:24});`
then `globeShot({overlay:{canvas:ov, bounds}, look: lt => ({ovAlpha: F.prog(lt,1,1.6), dim: .35*F.prog(lt,1,1.6)})})`.
Only ONE overlay texture is active at a time (installed when the owning shot first draws). Avoid crossfading two globe shots with different overlays.
globeShot extras: `outlines:[{rings, t, d, color, width}]` (draw-on crisp borders), `labels:[{t, d?, text, lat, lon, dx, dy, ring}]`,
`arcs:[{t, d, from:[lat,lon], to:[lat,lon], lift, color, width, dash, headDot}]`, `markers:[{t, lat, lon, color}]`,
`moves:[{t, d, rings, from:[lat,lon], to:[lat,lon], color}]` (true-size drag of a shape across the globe), `extra(ctx, lt, api, cam)`.
`api.g.project(lat, lon)` → `{x, y, visible}` for custom 2D drawing anchored to the globe.

## fx primitives (all in `F`)
- easing `F.E.{inOut, out, in, outExpo, inOutExpo, outBack, inOutSine}`; `F.prog(t, a, b, ease)` 0..1; `F.env(t, a, b, fi, fo)`.
- `F.text(ctx, s, x, y, {size, fam, weight, color, align, tracking, alpha, shadow})` (cached sprites — cheap).
- `F.headline(ctx, words, x, y, lt, {size, t0, per, tOut, align})` — words rise in; word objects `{w, c}` for accent colour.
- `F.pill(ctx, text, x, y, {anchor:'left'|'center'|'right', leader:[x,y], ring, alpha, size, bg, border, color})`.
- `F.counter(ctx, from, to, p, x, y, {size, unit, decimals, prefix, format, align, alpha})` tabular rolling numbers.
- `F.glowPath(ctx, pts, {p, color, width, dash})` draw-on glowing polyline, returns head point.
- `F.dot(ctx, x, y, {r, color, ring})`, `F.round(ctx, x, y, w, h, r)`.
- `F.kenburns(ctx, img, p, x, y, w, h, {from:[cx,cy,zoom], to:[...], frame, grade:'teal'|'sepia'|'cold'})`.
- `F.chapterCard(ctx, W, H, lt, dur, 'CHAPTER 2', 'TITLE WORDS')`.
- Fonts: `F.FAM.head` Bebas Neue (titles), `label` Barlow Condensed (labels, caps), `body` Inter (numbers/body), `mono` JetBrains Mono, `serif` Playfair Display, `black` Anton.
- Palette `F.PAL`: space #05070D, hero #FF5A36 (highlight), cyan #3DE3FF (water/routes/data), yellow #FFD23F (arrows/circles), text #F4F6FA, sub #9AA7B8.

## Style rules (from the 1M-view benchmark)
- A visual event every 2–3 s in the first minute, every 3–5 s afterwards; a cut or mode change every 5–7 s on average; nothing static > 3 s.
- One signature base look: dark-space globe / tilted satellite map; target highlighted hero-orange with white outline; everything else dimmed.
- Max 2 text elements on screen, ≤ 7 words each. No burned-in subtitles. Labels: Barlow Condensed caps in dark pills.
- Numbers roll (counter) and land on/just before the spoken word. Units US-first (miles, °F) with metric in a smaller second line when useful.
- Keep key info out of the bottom 12 % of the frame. Every element inside a 5 % title-safe margin.
- Performance: avoid ctx.shadowBlur and ctx.filter on large areas (software canvas) — use cached text, layered strokes, gradients.

## 3D stages, animated characters, cutaway, morph (lib/actors.js, lib/cutaway.js, lib/morph.js)
- `const st = await api.newStage('key', {shadowExtent, hemi, key, rim, exposure, fov})` — a separate WebGL scene (cached by key; reuse the same key across shots of the same set-up). Draw with `ctx.drawImage(st.render(t), 0, 0)` (transparent background: paint your own background first, e.g. a radial gradient or the globe).
- `import { Actor, tinyPlanet, THREE } from '../../lib/actors.js'` — `const hero = await Actor.create(st, 'models/adventurer.glb', {scale: 0.55})`;
  schedule clips at ABSOLUTE video time: `hero.play(t, 'Walk', {fade: 0.25, once: false, speed: 1})`; `hero.moveAlong([{t, x, y, z, ry}, ...])`.
  Explorer (models/adventurer.glb) clips: Idle, Idle_Neutral, Walk, Run, Run_Back, Run_Left, Run_Right, Wave, Roll, Death (comic collapse), HitRecieve, HitRecieve_2, Interact, Punch_Left/Right, Kick_Left/Right, Gun/Sword clips (DON'T use weapons).
  Also models/astronaut.glb (same clips). Kenney mini: models/mini_male_a.glb (static, idle, walk, sprint, jump, fall, crouch, sit, die, pick-up, emote-yes, emote-no, interact-left/right).
  `const planet = await tinyPlanet(st, {radius: 3})` — Earth-textured small planet (+ glow) to stand on; rotate it under a walking actor.
  Character scale reference: adventurer scale 0.55 ≈ 1 unit tall. Camera: `st.lookFrom([x,y,z],[tx,ty,tz], fov)`; set every frame for slow moves.
  Typical gag framing: actor centre-frame, camera 5–7 units away, low angle, rim-lit; keep gags 2–6 s.
- Cutaway Earth: `import { cutawayEarth, llDir, drillDir } from '../../lib/cutaway.js'` → `const ce = await cutawayEarth(st, {radius: 3})` (quarter wedge x>0 & z>0 removed in WORLD space; view it from camera direction (+x,+y,+z), e.g. `st.lookFrom([6,3.5,6],[0,0.3,0],32)`); rotate only `ce.userData.shell.quaternion` to choose which place is on top (e.g. `setFromUnitVectors(llDir(lat,lon), new THREE.Vector3(0,1,0))`); `drillDir(ce, new THREE.Vector3(0,1,0), p)` grows a cyan drill line from the top through the centre (p 0..1). Layer names in LAYERS (crust, mantle, outer core, inner core). Needs a light background gradient + labels via F.pill.
- Tetrahedron Earth: `import { tetraEarth } from '../../lib/morph.js'` → `const te = await tetraEarth(st, {radius: 2.2})`; each frame `te.userData.set(k, edgeAlpha)` morphs sphere→tetrahedron (k 0..1) with yellow edges; south-pole vertex = Antarctica.

## Paleo-geography (GPlates/EarthByte Müller 2019 reconstructions, simplified)
- `paleo/coast_TTT.json` for T = 0..200 Ma every 1 Myr (plus 250): array of polygons `[[lon,lat],...]` of reconstructed present-day coastlines at T million years ago.
- `paleo/tracks.json`: `{name: [[lon,lat] per Ma 0..200]}` for cape_horn, cape_agulhas, kanyakumari, india_c, cape_farewell, florida_tip, korea_tip, tasmania_s, madagascar_s, south_pole, nyc, africa_c, samerica_c, australia_c, antarctica_c (999.99 = not available).
- Render on the globe: draw polygons into a 4096x2048 equirect canvas (`fillEquirect`-style or manual), `api.g.setOverlay(canvas)` once, then each frame redraw + `api.g.refreshOverlay()`; look `{flatBase: 1, ovAlpha: 1, ovMul: 1, nightAmt: 0, relief: 0}` gives a clean ocean + land paleo-globe. Label "MILLION YEARS AGO" counter. Mark these sequences as simplified.

## Data overlays (computed)
- `tex/data/antipodes.png` (land's antipodes in cyan, land-on-land overlap in yellow), `tex/data/land_north.png` (northern land, hero-orange), `tex/data/land_south.png` (southern land, cyan); load with `await api.g.setOverlayURL(url)`.
- `tex/data/stats.json`: land 28.9 % of surface; 68 % of land is north; ~13 % of land (≈ 1 in 7) has land at its antipode; best land hemisphere centred 40°N 2°E holds 81 % of land yet is 53 % water; the opposite water hemisphere is 89 % water.
- `geo/tips_admin1.geojson`: Florida, Baja California, Baja California Sur, Kamchatka polygons (ignore the Uruguay 'Florida').

## Sound cues
- `api.cue(t, name, gain_db)` registers a sound effect at absolute time t. Library (normalised): whoosh_soft, whoosh_big, impact_deep, impact_short, riser_tension (4 s, peaks at end), pop_ui, tick_counter, shimmer, paper_rustle, typewriter, ice_wind, sonar_ping, rumble_quake, record_scratch, crickets, cartoon_fall, thunk_heavy, time_rewind, glitch_click, heartbeat_low, dig_shovel, splash_big, bell_small, stamp.
- Use: pop_ui on label/tip pops (-14 dB), whoosh on camera flights/transitions (-10), impact_deep on big reveals (-6), riser before reveals (start 4 s early, -12), tick_counter under counters (-16), comedic ones only on gags.

## Hi-res regional patches (sharper close-ups; install with `globeShot({patch: {url, bounds}})` or `await api.g.setPatch(url, bounds)`)
- tex/patch/greenland.jpg [-75, 58, -10, 84]; tex/patch/s_america_tip.jpg [-82, -58, -56, -30]; tex/patch/s_africa.jpg [10, -37, 36, -20];
  tex/patch/s_india.jpg [70, 4, 86, 18]; tex/patch/florida.jpg [-88, 23, -78, 31]; tex/patch/baja.jpg [-118, 21, -108, 33]. Only one patch active at a time.

## Public-domain photos (assets/pd → copy into ep folder when used)
- bacon.jpg (Paul van Somer portrait, 1617), wegener_villumsen_1930.jpg (last known photo of Wegener with Rasmus Villumsen, Greenland 1930), wegener_exp_013.jpg (expedition, 1930). More can be fetched with tools/../assets/pd/wm.py.
