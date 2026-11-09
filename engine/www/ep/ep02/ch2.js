// Chapter 2 "Oʻahu's Missing Side" (s026-s048), window K.chapter(2) (93.81-181.65 s, last shot to t1x). Built 2026-11-09.
// Four terrain stages, one camera path (orbit form, film time) shared by all of them, so every stage hand-off dissolves between two
// renders of the same camera (detail resolves, nothing doubles):
//   S1 'pali'        s026-s031  a high oblique settles behind the lookout (450 m up, looking NE through the pass); a paper stone wall
//                               pops up on the lookout terrace on {pali} with the PALI LOOKOUT label; tilt up to the cliffs on {cliff};
//                               the paper tourist (appearance 2 of 4) pops up at s028 on the inland side of the wall, leans into the
//                               trade wind on {lean} (27 deg, flutter), his hat blows off BACKWARD (up, left, inland, growing toward the
//                               camera) on {hat}, he turns and runs after it out of frame-left; the camera alone rises over the wall,
//                               the view plunges down the windward drop, levels out along the pali and pulls back to windward Oʻahu
//                               from the NE; {huge} a white line traces the Koʻolau crest (our DEM), {tore} a hero-orange glow runs along
//                               it (the scar; the narration keeps 'may'). Nothing falls off the Pali.
//   S2 'oahu_nuuanu' s032-s041  {ne} eased move out to sea (NE, looking SW back at Oʻahu, sun from the ENE), the live drain 0 to
//                               -5,000 m on a monotone curve keyed to {shelf}, {slope}, {first} (the largest block's top, -2,712 m on this
//                               grid, breaks the surface on the word), {more}, {field}, as the camera backs out over the field; SEA LEVEL
//                               gauge while the level moves; the held breath: the camera rises until the whole field is in frame;
//                               {slides} the debris field takes the hero fill and white outline; swing back to
//                               the cliffs, {summit} a white line on the crest where the caldera was cut; {outhere} fast flight back out
//                               low over the deposit; {block} push in on the largest block; {manh} the true-scale Manhattan outline drops
//                               and drapes along the block's long axis (40 % cyan, MANHATTAN label); {spare} camera rise, the outline
//                               settles with the 'tok'; {miles} pull back, a 10 px yellow line with a head dot runs along the mapped
//                               deposit (about 226 km) and lands with MORE THAN / 100 MILES.
//   S3 'main_chain'  s042-s044  pull back over the chain while the sea refills (no dry shelf mid-move: -4,500 (1 - p)^5), then 7 more
//                               slide footprints light up one every 0.25 s and land on {chain}, dim to 30 %, fade after {happen}.
//   S4 'kilauea_sf'  s044-s048  flight SE to Kīlauea's south flank, {flank} hero fill + outline + KĪLAUEA, {creep} yellow arrows inch
//                               seaward (stop-go, nothing collapses), {really} rise to the whole Big Island, {alldown} the drain starts.
// Sources of the drawn geometry (no invented shapes):
//   - Debris field and the 8 slide footprints: outer edge = the coloured extents of USGS I-2809 'Hawaii's Volcanoes Revealed'
//     (Eakins et al. 2003, public domain), interpretive inset, georeferenced from its graticule (conic fit, rms 0.25 px at 300 dpi) and
//     segmented by colour; inner edge = a depth contour on our own grid (Nuʻuanu: Koʻolau extent below -2,500 m on oahu_nuuanu; the
//     others below -2,500 to -3,500 m on main_chain, split into lobes by a bearing sector from the volcano: approximate, a sample).
//     The extents include each volcano's landslide debris (the map's caption); the clip removes the edifice. Tools: scratchpad ch2_tools/.
//   - Manhattan: US Census TIGER New York County (TIGERweb, public domain) minus TIGER area water, main island, 55.9 km2, 21.1 x 4.5 km,
//     laid along the block's long axis (-4,000 m footprint 26.5 x 17.5 km, axis 127 deg / 307 deg, from our oahu_nuuanu grid).
//   - Koʻolau crest: ridge trace on oahu_nuuanu (max along cross-sections, median-snapped). Kīlauea south flank: land at 0 m south of the
//     east and southwest rift zones (rift lines approximate, schematic boundary).
// Deviations: the drain camera backs out to 80-110 km beyond Oʻahu's NE flank (the largest block lies about 100 km NE of Kāneʻohe, so
// a camera 80 km out looking back would have it behind it); the drain goes to -5,000 m, not -4,500 m (the debris floor lies at -4,600
// to -4,800 m on this grid, so at -4,500 the field was still mostly water); the s042 footprints are drawn on the refilled sea as a map
// overlay (a drained chain here would spend chapter 3's one-ridge reveal); the stage's hero albedo is brightened for these fills.
// Shared toolkit unchanged; local helpers below (orbit camera from an eye, ground-draped runs, ring rasteriser, wall card).
import { PAL, E, F, MOVE_WATER, WATER_FILM, heightGrid, contour, mixState, orbitPath } from './shared.js';

const D2R = Math.PI / 180, KM = 111.32;
const LOOKOUT = [-157.7936, 21.3667];                     // Nuʻuanu Pali State Wayside (DLNR; region 'pali' view)
const BLOCK = { lon: -157.1261, lat: 22.0793, axis: -37.4 }; // centroid and long axis (deg from east, ccw) of the -4,000 m footprint
const KILAUEA = [-155.287, 19.407];
const LEVEL_END = -5000;                                  // the debris floor lies at -4,600 to -4,800 m on this grid: drained past it
// ---- geo helpers
const offLL = (ll, km, brg) => { const cl = Math.cos(ll[1] * D2R); return [ll[0] + km * Math.sin(brg * D2R) / (KM * cl), ll[1] + km * Math.cos(brg * D2R) / KM]; };
const brgOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return (Math.atan2((b[0] - a[0]) * cl, b[1] - a[1]) / D2R + 360) % 360; };
// orbit key from an eye: eye [lon, lat], alt km, heading, pitch (deg below the horizon), d km to the target point
function fromEye(t, eye, alt, heading, pitch, d, fov, ease) {
  const T = offLL(eye, d * Math.cos(pitch * D2R), heading);
  return { t, lon: T[0], lat: T[1], h: (alt - d * Math.sin(pitch * D2R)) * 1000, d, tilt: 90 - pitch, heading, fov, ease };
}
// orbit camera -> HawaiiStage camera (flat local frame: the eye sits d sin(tilt) behind and d cos(tilt) above the target)
function camOf(c) {
  const e = offLL([c.lon, c.lat], c.d * Math.sin(c.tilt * D2R), c.heading + 180);
  return { lon: e[0], lat: e[1], alt: (c.h || 0) / 1000 + c.d * Math.cos(c.tilt * D2R), tLon: c.lon, tLat: c.lat, tH: c.h || 0, fov: c.fov,
    near: F.clamp(c.d * 0.003, 0.004, 2), far: F.clamp(c.d * 300, 400, 9000) };
}
const chaikin = (pts, n = 2) => { let p = pts; for (let k = 0; k < n; k++) { const o = [p[0]]; for (let i = 0; i < p.length - 1; i++) { const a = p[i], b = p[i + 1]; o.push(a.map((v, j) => 0.75 * v + 0.25 * b[j]), a.map((v, j) => 0.25 * v + 0.75 * b[j])); } o.push(p[p.length - 1]); p = o; } return p; };
// monotone cubic (Fritsch-Carlson) through [t, v] keys: a level that never overshoots or reverses
function monotone(keys) {
  const n = keys.length, x = keys.map(k => k[0]), y = keys.map(k => k[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
  m[0] = 0; m[n - 1] = 0;
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : 3 * (x[i + 1] - x[i - 1]) / ((2 * x[i + 1] - x[i] - x[i - 1]) / d[i - 1] + (x[i + 1] - 2 * x[i] + x[i - 1]) / d[i]);
  return (t) => { if (t <= x[0]) return y[0]; if (t >= x[n - 1]) return y[n - 1];
    let i = 0; while (t > x[i + 1]) i++; const h = x[i + 1] - x[i], s = (t - x[i]) / h, s2 = s * s, s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * y[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * y[i + 1] + (s3 - s2) * h * m[i + 1]; };
}
// film water seen from far above blends toward the globe's navy (as scaleMove does), so far views never read saturated teal
function farWater(d) {
  const k = E.inOut(F.clamp((Math.log(d) - Math.log(25)) / (Math.log(500) - Math.log(25))));
  return k > 0 ? WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], k))) : null;
}

export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const ch = K.chapter(2), T = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f);
  const pr = (t, a, b, e = E.inOut) => e(F.clamp((t - a) / Math.max(1e-6, b - a)));
  const env = (t, a, b, fi = 0.3, fo = 0.3) => F.clamp(Math.min((t - a) / fi, (b - t) / fo));
  const dbg = !!api.Q.ch2dbg;

  // ================================================================ the one camera path (film time)
  const eyeG = offLL(LOOKOUT, 0.9, 222);                                   // behind the lookout over the Nuʻuanu side, 450 m up
  const tPop0 = K.s0('s028') + 0.05;
  const tDive0 = T('hat') + 0.86, tDive1 = tDive0 + 1.8;                  // the dive starts as the hat flutter plays (gap after 'hat.')
  const tNe0 = lead('ne') - 0.15, tNe1 = tNe0 + 2.5;
  const tSw0 = K.s0('s036') + 0.05, tSw1 = tSw0 + 2.1;
  const tFl0 = lead('outhere') - 1.9, tFl1 = lead('outhere') + 0.25;
  const tRise0 = lead('spare') - 0.1, tRise1 = tRise0 + 1.5;
  const tPb0 = K.s0('s041'), tPb1 = tPb0 + 2.0;
  const tCh0 = K.s0('s042') - 0.05, tCh1 = tCh0 + 3.5;
  const tBi0 = K.s0('s044') - 0.05, tBi1 = tBi0 + 2.5;
  const tUp0 = lead('really') - 2.6, tUp1 = lead('really') + 0.05;
  const KEYS = [
    fromEye(ch.t0, offLL(LOOKOUT, 3.2, 226), 1.55, 46, 15, 5.5, 48),
    fromEye(T('oahu'), eyeG, 0.80, 54, 16, 2.5, 50),                                         // settled behind the lookout by {oahu}
    fromEye(lead('cliff') - 0.1, offLL(LOOKOUT, 0.87, 222.5), 0.79, 56.5, 15, 2.5, 48),
    fromEye(lead('cliff') + 1.3, offLL(LOOKOUT, 0.86, 223), 0.80, 60, 9, 2.5, 48),         // {cliff}: tilt up to the full cliff height
    fromEye(tPop0 + 0.2, offLL(LOOKOUT, 0.84, 223), 0.79, 57, 14, 2.5, 48),                 // back down as the tourist pops up
    fromEye(tDive0, offLL(LOOKOUT, 0.75, 223.5), 0.745, 58.5, 15, 2.5, 47, E.inOutSine),    // slow push in through the gag
    fromEye(tDive0 + 0.75, offLL(LOOKOUT, 0.25, 222), 0.92, 45, 30, 1.5, 52),               // rises over the wall
    fromEye(tDive1, offLL(LOOKOUT, 0.6, 38), 1.05, 36, 36, 2.4, 54),                        // dives: the view plunges down the windward drop
    { t: tDive1 + 1.2, lon: -157.86, lat: 21.44, h: 300, d: 15, tilt: 70, heading: 302, fov: 44 }, // levels out along the pali
    { t: tDive1 + 2.7, lon: -157.81, lat: 21.42, h: 200, d: 40, tilt: 65, heading: 222, fov: 40 }, // pulls back: windward Oʻahu from the NE
    { t: tNe0, lon: -157.83, lat: 21.44, h: 200, d: 36, tilt: 64, heading: 228, fov: 40, ease: E.inOutSine },
    { t: tNe1, lon: -157.62, lat: 21.62, h: -1500, d: 58, tilt: 70, heading: 223, fov: 42 },      // {ne}: out to sea NE, looking SW at Oʻahu
    { t: lead('slope') - 0.15, lon: -157.57, lat: 21.67, h: -1800, d: 62, tilt: 70.5, heading: 224, fov: 42, ease: E.inOutSine },
    { t: lead('first') - 0.2, lon: -157.30, lat: 21.92, h: -3400, d: 82, tilt: 73, heading: 225, fov: 42 },   // back out: the blocks' field
    { t: T('field') + 1.8, lon: -157.27, lat: 21.93, h: -3600, d: 78, tilt: 73.5, heading: 227, fov: 42, ease: E.inOutSine },
    { t: lead('slides') - 0.1, lon: -157.0, lat: 22.2, h: -4200, d: 215, tilt: 64, heading: 226, fov: 42 },   // the held breath: rise to the whole field
    { t: tSw0, lon: -157.01, lat: 22.19, h: -4200, d: 208, tilt: 64, heading: 227, fov: 42, ease: E.inOutSine },
    { t: tSw1, lon: -157.79, lat: 21.40, h: 0, d: 32, tilt: 62, heading: 232, fov: 40 },            // swing back to the cliffs
    { t: tFl0, lon: -157.795, lat: 21.405, h: 0, d: 29, tilt: 62, heading: 234, fov: 40, ease: E.inOutSine },
    { t: tFl1, lon: -157.11, lat: 22.075, h: -3200, d: 26, tilt: 66, heading: 222, fov: 44 },      // {outhere}: fast flight out over the deposit
    { t: lead('block') + 0.1, lon: -157.12, lat: 22.078, h: -3500, d: 20, tilt: 64, heading: 218, fov: 44 },  // {block}: in on the largest block
    { t: tRise0, lon: -157.123, lat: 22.079, h: -3550, d: 18.5, tilt: 63, heading: 216, fov: 44, ease: E.inOutSine },
    { t: tRise1, lon: -157.126, lat: 22.079, h: -3600, d: 27, tilt: 42, heading: 212, fov: 44 },   // {spare}: rise, the width on both sides
    { t: tPb1, lon: -157.0, lat: 22.2, h: -4000, d: 255, tilt: 55, heading: 312, fov: 40 },        // {miles}: side view of the deposit
    { t: tCh0, lon: -157.0, lat: 22.18, h: -4000, d: 245, tilt: 55, heading: 314, fov: 40, ease: E.inOutSine },
    { t: tCh1, lon: -157.45, lat: 20.75, h: 0, d: 760, tilt: 42, heading: 330, fov: 40 },          // s042: over the whole chain
    { t: tBi0, lon: -157.42, lat: 20.72, h: 0, d: 720, tilt: 42, heading: 333, fov: 40, ease: E.inOutSine },
    { t: tBi1, lon: -155.20, lat: 19.30, h: 0, d: 52, tilt: 60, heading: 328, fov: 42 },           // s044: Kīlauea's south flank
    { t: tUp0, lon: -155.21, lat: 19.31, h: 0, d: 44, tilt: 60, heading: 333, fov: 42, ease: E.inOutSine },
    { t: tUp1, lon: -155.50, lat: 19.62, h: 0, d: 240, tilt: 50, heading: 322, fov: 38 },          // {really}: the whole Big Island
    { t: ch.t1x, lon: -155.52, lat: 19.64, h: 0, d: 226, tilt: 50, heading: 319, fov: 38, ease: E.inOutSine },
  ];
  const path = orbitPath(KEYS);
  const camAt = (t) => camOf(path(t));

  // ================================================================ stage windows (identical camera across every hand-off)
  const XF = 0.5;
  const S1 = [ch.t0, tNe0 - 1.2 + XF], S2 = [tNe0 - 1.2, tCh0 + 0.45 + XF], S3 = [tCh0 + 0.45, tBi0 + 1.75 + XF], S4 = [tBi0 + 1.75, ch.t1x];

  // ================================================================ water level
  const drain = monotone([[lead('ne'), 0], [lead('shelf') + 0.05, -150], [lead('slope') + 0.2, -900], [lead('first') - 0.03, -2712], [T('first') + 1.9, -3100],
    [lead('more') + 0.05, -3500], [lead('field') + 0.05, -4150], [K.s1('s034') + 0.12, LEVEL_END]]);
  const tRf0 = tCh0 + 0.45 + 0.5, tRf1 = tRf0 + 1.7;                       // the refill starts as the main_chain stage's dissolve ends
  const refill = (t) => LEVEL_END * Math.pow(1 - F.clamp((t - tRf0) / (tRf1 - tRf0)), 5);
  const tDr0 = T('alldown') - 0.05;
  const bigDrain = (t) => -2600 * E.in(F.clamp((t - tDr0) / 2.6));

  // ================================================================ data, made once
  const card = { tour: await kit.paper('tourist').catch(e => { api.log('[ch2] tourist cut-out missing: ' + e.message); return null; }), wall: wallCard(kit) };
  const dummy = kit.P.cv(4, 4).getContext('2d');
  const DEP = chaikin([[-157.79, 21.46], [-157.47, 21.76], [-157.12, 22.07], [-156.78, 22.40], [-156.47, 22.66], [-156.21, 22.86]], 3);
  const crest = CREST.map(p => [p[0], p[1], p[2]]);
  const caldera = crest.filter(p => p[1] > 21.322 && p[1] < 21.408);
  const manhattanRing = (k = 1) => { const a = BLOCK.axis * D2R, cl = Math.cos(BLOCK.lat * D2R);
    return MANHATTAN_KM.map(([u, v]) => { u *= k; v *= k; const e = u * Math.cos(a) - v * Math.sin(a), n = u * Math.sin(a) + v * Math.cos(a); return [BLOCK.lon + e / (KM * cl), BLOCK.lat + n / KM]; }); };
  const MANH = manhattanRing();
  // ring rasteriser on a height grid (row 0 = south), canvas fill (even-odd)
  const raster = (g, rings) => { const c = kit.P.cv(g.nx, g.ny), x = c.getContext('2d', { willReadFrequently: true }); x.fillStyle = '#fff'; x.beginPath();
    for (const r of rings) r.forEach(([lo, la], i) => { const X = (lo - g.bb[0]) / (g.bb[2] - g.bb[0]) * (g.nx - 1), Y = (la - g.bb[1]) / (g.bb[3] - g.bb[1]) * (g.ny - 1); i ? x.lineTo(X, Y) : x.moveTo(X, Y); });
    x.closePath(); x.fill('evenodd'); const d = x.getImageData(0, 0, g.nx, g.ny).data, m = new Uint8Array(g.nx * g.ny);
    for (let k = 0; k < m.length; k++) m[k] = d[k * 4] > 127 ? 1 : 0; return m; };
  const inPoly = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j]; if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) c = !c; } return c; };
  const M = {};                                        // lazily built masks per stage
  const blockIsl = async () => { if (M.block === undefined) { try { M.block = await kit.island({ region: 'oahu_nuuanu', bbox: [-157.4, 21.9, -156.85, 22.26], level: -4000, seeds: [[-157.0724, 22.0661]], step: 1 }); if (dbg) api.log(`[ch2] block -4000 m: ${Math.round(M.block.areaKm2)} km2, ${M.block.rings.length} rings`); } catch (e) { api.log('[ch2] block outline: ' + e.message); M.block = null; } } return M.block; };
  const nuuMask = (S) => { if (!M.nuu) { const g = heightGrid(S, [-158.25, 21.48, -156.03, 23.06], 2); M.nuu = { tex: kit.maskTexture(g, { r: raster(g, SLIDES.nuuanu) }), bb: g.bb }; } return M.nuu; };
  const flank = (S) => {
    if (!M.flank) {
      const g = heightGrid(S, [-155.6, 19.0, -154.75, 19.55], 1), m = new Uint8Array(g.nx * g.ny);
      for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) { const k = j * g.nx + i; if (g.h[k] > 0 && inPoly(g.ll(i, j), FLANK)) m[k] = 1; }
      const rings = contour(g, m, 0, 0.8, 2, 400);
      M.flank = { tex: kit.maskTexture(g, { r: m }), bb: g.bb, rings };
      if (dbg) api.log(`[ch2] flank ${rings.length} rings ${rings.map(r => r.length).join(',')}`);
    }
    return M.flank;
  };

  // the stage's hero albedo (#FF5A36 x 0.17) reads crimson on the dark drained basalt (round-3 still): brighter and less red for this
  // chapter's fills, set in mask()
  // just before the render and put back in world() right after it, so no other shot on the same stage ever sees it
  const heroBright = (S) => { const u = S.maskU?.heroCol; if (!u) return; if (!S._heroDef) S._heroDef = u.value.clone(); u.value.setRGB(0.34, 0.068, 0.018); };   // linear: brighter, a touch more green than the default, so it renders as #FF5A36
  const heroReset = (S) => { const u = S.maskU?.heroCol; if (u && S._heroDef) u.value.copy(S._heroDef); };

  // ================================================================ UI helpers (crisp, after the grade)
  const gh = (v, lon, lat) => Math.max(v.S.heightAt(lon, lat), v.level);
  const gp = (v, lon, lat, off = 20) => v.project(lon, lat, gh(v, lon, lat) + off);
  // screen runs of a lon/lat polyline draped on the ground (+off m), split where hidden or off-screen
  const druns = (v, pts, off = 40, every = 3, closed = false, flat = null) => {
    const out = []; let cur = []; const P = closed ? pts.concat([pts[0]]) : pts;
    for (let i = 0; i < P.length; i++) { const [lo, la] = P[i], hm = (flat ?? gh(v, lo, la)) + off, q = v.project(lo, la, hm);
      const ok = q && q[0] > -300 && q[0] < W + 300 && q[1] > -300 && q[1] < H + 300 && (i % every || flat != null || v.visible(lo, la, hm));
      if (!ok) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); }
    if (cur.length > 1) out.push(cur); return out; };
  const runLen = (runs) => runs.reduce((a, r) => a + r.reduce((b, p, i) => i ? b + Math.hypot(p[0] - r[i - 1][0], p[1] - r[i - 1][1]) : 0, 0), 0);
  const pointAt = (runs, p) => { let tgt = runLen(runs) * p, last = null;
    for (const r of runs) for (let i = 1; i < r.length; i++) { const d = Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1]); last = r[i]; if (tgt <= d) { const k = d ? tgt / d : 0; return [F.lerp(r[i - 1][0], r[i][0], k), F.lerp(r[i - 1][1], r[i][1], k)]; } tgt -= d; }
    return last; };
  // a meaningful line that draws on with a moving head dot (PLAYBOOK_craft 8)
  const lineOn = (ctx, runs, p, o = {}) => { if (p <= 0 || !runs.length) return; ui.line(ctx, runs, Object.assign({}, o, { p }));
    if (p < 0.999 || o.dotHold) { const q = pointAt(runs, p); if (q) { const r = px((o.width || 10) * 1.15); ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
      ctx.fillStyle = 'rgba(6,9,15,0.6)'; ctx.beginPath(); ctx.arc(q[0], q[1], r + px(4), 0, 7); ctx.fill(); ctx.fillStyle = o.color || PAL.text; ctx.beginPath(); ctx.arc(q[0], q[1], r, 0, 7); ctx.fill(); ctx.restore(); } } };

  // ================================================================ S1 'pali': the lookout, the paper wall, the tourist, the dive
  const tPop = tPop0, tLean = lead('lean'), tHat = lead('hat'), tTurn = tHat + 0.38, tRun = tTurn + 0.24;
  const tourPose = (t) => {
    const lean = t < tHat + 0.12 ? 0.06 + 0.41 * E.outBack(F.clamp((t - tLean) / 0.45)) : F.lerp(0.47, 0.03, pr(t, tHat + 0.12, tHat + 0.36));
    return { pop: F.clamp((t - tPop) / 0.5), lean, wobble: t > tLean && t < tHat + 0.3 ? 0.035 : 0.018, turn: pr(t, tTurn, tTurn + 0.22), run: Math.max(0, t - tRun) };
  };
  const DREF = 1.004;                                                     // camera-to-lookout distance (km) of the settled framing
  scenes.push(kit.terrainShot({ id: 'ch2-pali', t0: S1[0], t1: S1[1], fadeIn: K.XF, region: 'pali', preset: 'today',
    cam: (lt) => camAt(S1[0] + lt),
    state: (lt) => { const t = S1[0] + lt, c = path(t), k = F.clamp(Math.log(c.d / 2) / Math.log(20));
      const st = { sun: [F.lerp(75, 68, k), F.lerp(55, 30, k)], set: { foamAmt: 0.25 } }; const wc = farWater(c.d); if (wc) st.waterCols = wc; return st; },
    world(ctx, lt, t, view) {
      if (t > tDive0 + 0.7) return;
      const S = view.S, cam = S.cam.position, dist = (lon, lat, hm) => S.xyz(lon, lat, hm).distanceTo(cam);
      const hL = gh(view, ...LOOKOUT), b = view.project(LOOKOUT[0], LOOKOUT[1], hL);
      if (!b) return;
      const s = F.clamp(DREF / dist(LOOKOUT[0], LOOKOUT[1], hL), 0, 1.4), hPx = H * 0.36 * s;
      // the lookout wall: a paper stone wall that pops up on {pali}, standing on the real ground just beyond the lookout and running
      // along the edge (perpendicular to the view), between the tourist and the drop; paper-scale like the tourist (waist high to him)
      const wp = F.clamp((t - (lead('pali') - 0.15)) / 0.5), wOut = pr(t, tDive0 + 0.15, tDive0 + 0.45);
      if (wp > 0 && wOut < 1) {
        const W0 = offLL(LOOKOUT, 0.04, 42), E1 = offLL(W0, 0.17, 312), E2 = offLL(W0, 0.30, 132);
        const end = (ll) => { const h = hL, q = view.project(ll[0], ll[1], h); if (!q) return null; const k = DREF / dist(ll[0], ll[1], h); return [q, 0.40 * H * 0.36 * F.clamp(k, 0, 1.6) * E.outBack(wp)]; };
        const A = end(E1), B = end(E2);
        if (A && B) {
          const al = F.clamp(wp * 4) * (1 - wOut);
          ctx.save(); ctx.globalAlpha = 0.3 * al; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.moveTo(A[0][0], A[0][1] - 2); ctx.lineTo(B[0][0], B[0][1] - 2);
          ctx.lineTo(B[0][0] + B[1] * 0.25, B[0][1] + B[1] * 0.09); ctx.lineTo(A[0][0] + A[1] * 0.25, A[0][1] + A[1] * 0.09); ctx.closePath(); ctx.fill(); ctx.restore();
          kit.drawQuad(ctx, card.wall.img, [[A[0][0], A[0][1] - A[1]], [B[0][0], B[0][1] - B[1]], B[0], A[0]], 10, al);
          // the paper's thickness at the near end (a cream strip)
          ctx.save(); ctx.globalAlpha = al; ctx.fillStyle = '#E9E0CC'; ctx.fillRect(B[0][0] - 3, B[0][1] - B[1], Math.max(5, B[1] * 0.05), B[1]); ctx.restore();
        }
      }
      // the paper tourist (appearance 2 of 4): pops up at s028, leans into the trade wind on {lean}, loses his hat on {hat}, turns
      // and runs after it out of frame-left (the hat flies BACKWARD, inland: the wind blows up the cliff into his face)
      const TOUR = card.tour; if (!TOUR || t < tPop) return;
      const P = tourPose(t);
      const runX = -1350 * E.in(F.clamp(P.run / 0.75)) * s, hop = P.run > 0 ? Math.abs(Math.sin(P.run * 15)) * 28 * s : 0;
      if (b[0] + runX < -0.5 * hPx) return;
      const base = { hPx, pop: P.pop, lean: P.lean, wobble: P.wobble, t, seed: 3, turn: P.turn, hop };
      let o;
      if (runX === 0) o = Object.assign({ lon: LOOKOUT[0], lat: LOOKOUT[1] }, base);
      else { const g = view.ground(b[0] + runX, b[1]); o = g ? Object.assign({ lon: g[0], lat: g[1], hm: g[2] }, base) : Object.assign({ x: b[0] + runX, y: b[1] }, base); }
      if (t < tHat) { kit.drawCutout(ctx, view, TOUR, o); return; }
      kit.drawCutout(ctx, view, TOUR, Object.assign({}, o, { parts: { hat: { alpha: 0 } } }));
      // the detached hat: from where it sat at tHat, up and backward (left, toward the camera, so it grows a little), tumbling
      const P0 = tourPose(tHat), r0 = kit.drawCutout(dummy, view, TOUR, Object.assign({ lon: LOOKOUT[0], lat: LOOKOUT[1] }, base, { pop: 1, lean: P0.lean, wobble: 0, turn: 0, hop: 0, alpha: 0.5 }));
      const h0 = r0?.parts?.hat, hc = TOUR.parts?.hat;
      if (h0 && hc) {
        const u = t - tHat, gr = 1.6 + 1.9 * E.inOut(F.clamp(u / 1.1));
        const x = h0.x - 1500 * s * Math.pow(F.clamp(u / 1.25), 1.5), y = h0.y - 230 * s * Math.sin(F.clamp(u / 0.9) * Math.PI / 2) + 300 * s * Math.pow(Math.max(0, u - 0.55), 2);
        if (x > -h0.w * 2) { ctx.save(); ctx.translate(x, y); ctx.rotate(-u * 7.5 - 0.3 * Math.sin(u * 11)); ctx.drawImage(hc.img, -h0.w * gr / 2, -h0.h * gr / 2, h0.w * gr, h0.h * gr); ctx.restore(); }
      }
    },
    ui(ctx, lt, t, view) {
      // s030 {huge}: a white line traces the Koʻolau crest (the cliff top); s031 {tore}: a soft hero-orange glow runs along it
      const out = pr(t, tNe0 - 1.6, tNe0 - 1.0);
      if (t > lead('huge') - 0.05 && out < 1) {
        const runs = druns(view, crest, 30, 4);
        lineOn(ctx, runs, pr(t, lead('huge'), lead('huge') + 0.9), { color: PAL.text, width: 6, alpha: 1 - out });
        const g = pr(t, lead('tore'), lead('tore') + 1.1);
        if (g > 0) { ui.line(ctx, runs, { color: PAL.hero, width: 14, alpha: 0.38 * (1 - out), p: g, under: 0 }); lineOn(ctx, runs, g, { color: PAL.hero, width: 8, alpha: 0.95 * (1 - out) }); }
      }
      // s026 {pali}: PALI LOOKOUT on the lookout, held 2 s and more (clear of the chapter card while it shows)
      const la = env(t, lead('pali') - 0.1, T('oahu') + 1.1, 0.3, 0.35);
      if (la > 0) { const q = gp(view, ...LOOKOUT, 10); if (t < ch.card + 1.65) ui.avoid({ x: W / 2 - px(560), y: px(280), w: px(1120), h: px(190) });
        if (q) ui.label(ctx, 'PALI LOOKOUT', q[0], q[1], { t, p: la, order: ['above-right', 'above', 'right', 'above-left'] }); }
    } }));
  api.cue(tLean, 'card_creak', -17.7); api.cue(T('hat') - 0.2, 'wind_gust', -14); api.cue(K.s1('s029') + 0.14, 'paper_flutter', -10); api.cue(tDive0 + 0.4, 'whoosh_soft', -20);

  // ================================================================ S2 'oahu_nuuanu': the drain, the debris, the block, Manhattan, 100 MILES
  const tSl = lead('slides'), tManh = lead('manh'), tDrop0 = tManh - 0.48;
  const NUU_FILL = api.Q.ch2fill ?? 0.4;                                  // 0.6 read red 19 % and failed the clone gate; 0.38: red 0 %
  const S2shot = kit.terrainShot({ id: 'ch2-nuuanu', t0: S2[0], t1: S2[1], fadeIn: XF, region: 'oahu_nuuanu',
    cam: (lt) => camAt(S2[0] + lt),
    level: (lt) => drain(S2[0] + lt),
    state: (lt) => { const t = S2[0] + lt, lv = drain(t), k = F.clamp(-lv / 700), st = mixState('today', 'drained', k);
      st.sun = [F.lerp(72, 118, k), F.lerp(30, 19, k)]; st.set.foamAmt = 0.4 * (1 - k); st.set.oldLine = 0.6 * k; st.set.tubAmt = 0;
      st.post.exposure = F.lerp(1.2, 1.55, k); const wc = farWater(path(t).d); if (wc) st.waterCols = wc; return st; },
    mask: (lt, S) => { const t = S2[0] + lt, a = pr(t, tSl - 0.05, tSl + 0.2) * (1 - pr(t, tSw0 + 0.2, tSw0 + 0.9)); if (a <= 0) return null; const m = nuuMask(S); heroBright(S); return { tex: m.tex, bb: m.bb, hero: NUU_FILL * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    async ui(ctx, lt, t, view) {
      // s035 {slides}: the debris field's white outline (the 55 % hero fill is in the terrain)
      const fa = pr(t, tSl - 0.05, tSl + 0.2) * (1 - pr(t, tSw0 + 0.2, tSw0 + 0.9));
      if (fa > 0) for (const r of SLIDES.nuuanu) ui.outline(ctx, druns(view, r, 60, 3, true), { width: 6, alpha: fa, p: pr(t, tSl, tSl + 0.5) });
      // s036 {summit}: a white line on the cliffs where the old summit caldera was cut in two (schematic marker on the real crest)
      const ca = pr(t, lead('summit'), lead('summit') + 0.6), cOut = pr(t, tFl0 - 0.1, tFl0 + 0.35);
      if (ca > 0 && cOut < 1) lineOn(ctx, druns(view, caldera, 40, 2), ca, { color: PAL.text, width: 10, alpha: 1 - cOut });
      // s038 {block}: a white outline around the largest block (its -4,000 m footprint on this grid: the contour the Manhattan
      // comparison is made against, 26.5 x 17.5 km), held through Manhattan
      const ba = pr(t, lead('block'), lead('block') + 0.5) * (1 - pr(t, tPb0 + 0.1, tPb0 + 0.6));
      if (ba > 0) { const bk = await blockIsl(); if (bk) for (const r of bk.rings) ui.outline(ctx, druns(view, r, 40, 1, true, -4000), { width: 5, alpha: 0.85 * Math.min(1, ba * 3), p: ba }); }
      // s039 {manh}: true-scale Manhattan drops from above and drapes along the block's long axis; s040 {spare}: it settles ('tok')
      const dp = pr(t, tDrop0, tManh, E.in), mOut = pr(t, tPb0 + 0.1, tPb0 + 0.6);
      if (t > tDrop0 && mOut < 1) {
        const tok = Math.sin(F.clamp((t - (K.Te('spare') + 0.02)) / 0.2) * Math.PI) * 0.018;
        const ring = tok ? manhattanRing(1 - tok) : MANH, top = -2650, fall = 9000 * (1 - dp);
        const runs = [ring.map(([lo, la]) => view.project(lo, la, F.lerp(top, gh(view, lo, la) + 30, dp) + fall))].filter(r => r.every(Boolean));
        ui.fill(ctx, runs, { color: PAL.cyan, fill: 0.4, alpha: (1 - mOut) * F.clamp((t - tDrop0) / 0.2) });
        ui.outline(ctx, runs, { width: 6, alpha: (1 - mOut) * F.clamp((t - tDrop0) / 0.2) });
        ui.avoidRuns(runs, 4);
        const la = env(t, tManh, tPb0 + 0.4, 0.3, 0.3);
        if (la > 0) { const q = gp(view, BLOCK.lon, BLOCK.lat, 40); if (q) ui.label(ctx, 'MANHATTAN', q[0], q[1], { t, p: la, dist: 110, order: ['above', 'above-right', 'above-left', 'right', 'left'] }); }
      }
      // s041 {miles}: a 10 px yellow line with a head dot runs along the mapped deposit, Oʻahu's coast to the farthest blocks (~226 km),
      // landing with the line-draw sound; the number block lands on the word
      const lp = pr(t, tPb0, tPb0 + 2.0, E.inOutSine), lOut = pr(t, S2[1] - XF - 0.55, S2[1] - XF - 0.1);
      if (lp > 0 && lOut < 1) {
        const runs = druns(view, DEP, 150, 4); lineOn(ctx, runs, lp, { color: PAL.yellow, width: 10, alpha: 1 - lOut }); ui.avoidRuns(runs, 3);
        const kp = F.clamp((t - lead('miles')) / 0.3);
        if (kp > 0) {
          const nOpt = { cap: 160, to: 100, unit: 'MILES', unitCap: 100 };
          const m = ui.number(ctx, 0, 0, 0, Object.assign({ measure: true }, nOpt));
          const box = ui.block(ctx, [{ text: 'MORE THAN', role: 'kicker', cap: 60 }], px(96), px(96),
            { anchor: 'left', p: kp, out: lOut, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow, clear: 40,
              at: [{ x: px(96), y: px(96), anchor: 'left' }, { x: W - px(96), y: px(96), anchor: 'right' }, { x: W / 2, y: px(96), anchor: 'center' }] });
          if (box) ui.number(ctx, 100, box.inner.x, box.inner.y + m.h, Object.assign({ alpha: F.clamp(kp * 2) * (1 - E.in(lOut)) }, nOpt));
        }
      }
      // the SEA LEVEL gauge while the level moves (s032-s034); out in the held breath
      const gpIn = F.clamp((t - (tNe0 - 0.1)) / 0.6), gOut = pr(t, K.s1('s034') + 0.3, K.s1('s034') + 0.7);
      if (gpIn > 0 && gOut < 1) ui.gauge(ctx, { p: gpIn, out: gOut, level: view.level, range: 5000, to: 16404, unit: 'FT' });
    } });
  S2shot.uiFrom = S2[0] + XF;
  scenes.push(S2shot);
  api.cue(lead('ne') - 0.28, 'drain_start', -12); api.cue(T('first'), 'block_surface', -16); api.cue(T('more'), 'block_surface', -18); api.cue(T('field') - 1.0, 'rubble_emerge', -14);
  api.cue(T('slides') - 0.08, 'impact_deep', -10); api.cue(tFl0 + 0.3, 'whoosh_big', -15); api.cue(tDrop0, 'whoosh_big', -16); api.cue(tManh, 'impact_short', -14);
  api.cue(K.Te('spare') + 0.05, 'pop_ui', -18); api.cue(tPb0, 'line_draw', -18); api.cue(tPb0 + 2.0, 'impact_short', -12);

  // ================================================================ S3 'main_chain': refill, the slide footprints along the chain
  const ORDER = ['n_kauai', 's_kauai', 'waianae', 'wailau', 'clark', 'alika', 'kalae'];
  const tLast = lead('chain'), tFirst = tLast - 0.25 * (ORDER.length - 1), tNuu = Math.min(tRf1 - 0.1, tFirst - 0.3);
  const tDim0 = T('chain') + 0.7, tFade0 = T('happen') + 0.45;
  const S3shot = kit.terrainShot({ id: 'ch2-chain', t0: S3[0], t1: S3[1], fadeIn: XF, region: 'main_chain',
    cam: (lt) => camAt(S3[0] + lt),
    level: (lt) => refill(S3[0] + lt),
    state: (lt) => { const t = S3[0] + lt, p = F.clamp((t - tRf0) / (tRf1 - tRf0)), st = mixState('drained', 'today', p);
      st.sun = [150, 42]; st.set.foamAmt = 0; const wc = farWater(path(t).d); if (wc) st.waterCols = wc; return st; },
    ui(ctx, lt, t, view) {
      // the footprints, drawn on the sea as a map overlay: Nuʻuanu first (as the refill ends), then 7 more, one every 0.25 s,
      // the last on {chain}; dimmed to 30 % after it, gone after {happen}
      const dim = 1 - 0.7 * pr(t, tDim0, tDim0 + 0.5), fade = 1 - pr(t, tFade0, tFade0 + 0.6);
      const list = [['nuuanu', tNuu]].concat(ORDER.map((k, i) => [k, tFirst + 0.25 * i]));
      for (const [k, t0] of list) {
        const a = F.clamp((t - t0) / 0.2) * dim * fade; if (a <= 0) continue;
        const pop = 1 + 0.06 * Math.sin(F.clamp((t - t0) / 0.25) * Math.PI);
        for (const r of SLIDES[k]) {
          const c = r.reduce((s, p) => [s[0] + p[0] / r.length, s[1] + p[1] / r.length], [0, 0]);
          const runs = druns(view, r.map(p => [c[0] + (p[0] - c[0]) * pop, c[1] + (p[1] - c[1]) * pop]), 0, 1, true, Math.max(view.level, 0));
          ui.fill(ctx, runs, { color: PAL.hero, fill: 0.74, alpha: a }); ui.outline(ctx, runs, { width: 5, alpha: a });
        }
      }
      const gpIn = F.clamp((t - (S3[0] + XF)) / 0.35), gOut = pr(t, tRf1 + 0.1, tRf1 + 0.5);
      if (gpIn > 0 && gOut < 1) ui.gauge(ctx, { p: gpIn, out: gOut, level: view.level, range: 5000, to: 16404, unit: 'FT' });
    } });
  S3shot.uiFrom = S3[0] + XF;
  scenes.push(S3shot);
  api.cue(tFirst - 0.28, 'pop_cascade', -12.8); api.cue(tBi0 + 0.1, 'whoosh_soft', -14);

  // ================================================================ S4 'kilauea_sf': the creeping south flank, the whole Big Island, drain
  const tFk = lead('flank'), tFkOut = tUp0 + 0.05, tCr = lead('creep');
  const ARROWS = [[-155.36, 19.29], [-155.22, 19.31], [-155.08, 19.33], [-154.96, 19.38]];
  const S4shot = kit.terrainShot({ id: 'ch2-kilauea', t0: S4[0], t1: S4[1], fadeIn: XF, region: 'kilauea_sf', preset: 'today',
    cam: (lt) => camAt(S4[0] + lt),
    level: (lt) => bigDrain(S4[0] + lt),
    state: (lt) => { const t = S4[0] + lt, st = { sun: [215, 38], set: { foamAmt: 0.6 } }; const wc = farWater(path(t).d); if (wc) st.waterCols = wc;
      const k = F.clamp(-bigDrain(t) / 300); if (k > 0) Object.assign(st.set, { tubAmt: 0.8 * k, oldLine: k, lineCol: [1.15, 1.1, 1.0] }); return st; },
    mask: (lt, S) => { const t = S4[0] + lt, a = pr(t, tFk - 0.05, tFk + 0.25) * (1 - pr(t, tFkOut, tFkOut + 0.6)); if (a <= 0) return null; const m = flank(S); heroBright(S); return { tex: m.tex, bb: m.bb, hero: 0.58 * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) {
      const a = pr(t, tFk - 0.05, tFk + 0.25) * (1 - pr(t, tFkOut, tFkOut + 0.6));
      if (a <= 0) return;
      const fl = flank(view.S);
      for (const r of fl.rings) ui.outline(ctx, druns(view, r, 25, 3, true), { width: 6, alpha: a, p: pr(t, tFk, tFk + 0.5) });
      // s045 {creep} / s046 {creeping}: yellow arrows on the flank point seaward and inch forward, stop-go (no rate, nothing collapses)
      const ap = pr(t, tCr, tCr + 0.45);
      if (ap > 0) for (let i = 0; i < ARROWS.length; i++) {
        const u = Math.max(0, t - tCr - i * 0.08), n = Math.floor(u / 1.15), f = E.inOut(F.clamp((u % 1.15) / 0.55)), step = 0.55 * (n + f);
        const p0 = offLL(ARROWS[i], step, 158), p1 = offLL(p0, 5.5, 158);
        const A0 = gp(view, p0[0], p0[1], 40), A1 = gp(view, p1[0], p1[1], 40);
        if (A0 && A1) ui.arrow(ctx, [A0, A1], { p: ap, alpha: a, width: 13 });
      }
      const q = gp(view, ...KILAUEA, 30);
      if (q) ui.label(ctx, 'KĪLAUEA', q[0], q[1], { t, p: F.clamp((t - tFk) / 0.3) * a, order: ['above', 'above-left', 'above-right', 'left', 'right'] });
    } });
  S4shot.uiFrom = S4[0] + XF;
  scenes.push(S4shot);
  api.cue(T('alldown'), 'drain_start', -10.4);
  if (dbg) api.log(`[ch2] windows S1 ${S1.map(v => v.toFixed(2))} S2 ${S2.map(v => v.toFixed(2))} S3 ${S3.map(v => v.toFixed(2))} S4 ${S4.map(v => v.toFixed(2))} dive ${tDive0.toFixed(2)}`);
}

// a paper stone wall (the lookout's waist-high wall): grey basalt stones in mortar under a pale cap, cream paper edge, shared grade
function wallCard(kit) {
  const w = 2400, h = 300, c = kit.P.cv(w, h), g = c.getContext('2d'), R = F.rng(11);
  g.fillStyle = '#8f897d'; g.fillRect(0, 0, w, h);                                     // pale mortar
  // irregular basalt stones: jittered blobs on a loose grid, varied grey-brown, a lit top and a dark bottom lip
  for (let row = 0, y = 26; y < h + 20; row++) {
    const rh = 52 + R() * 26; let x = -R() * 90 - (row % 2) * 40;
    while (x < w + 40) {
      const sw = 90 + R() * 120, cx = x + sw / 2, cy = y + rh / 2, n = 9, pts = [];
      for (let k = 0; k < n; k++) { const a = k / n * Math.PI * 2, rr = 0.86 + R() * 0.16; pts.push([cx + Math.cos(a) * sw * 0.47 * rr, cy + Math.sin(a) * rh * 0.45 * rr]); }
      const tn = 58 + R() * 40, warm = R() * 10;
      const path = () => { g.beginPath(); pts.forEach(([px_, py_], i) => i ? g.lineTo(px_, py_) : g.moveTo(px_, py_)); g.closePath(); };
      path(); g.fillStyle = `rgb(${Math.round(tn + 8 + warm)},${Math.round(tn + 4)},${Math.round(tn)})`; g.fill();
      g.save(); path(); g.clip();
      const lg = g.createLinearGradient(0, cy - rh / 2, 0, cy + rh / 2); lg.addColorStop(0, 'rgba(255,246,225,0.22)'); lg.addColorStop(0.45, 'rgba(255,246,225,0)'); lg.addColorStop(1, 'rgba(0,0,0,0.30)');
      g.fillStyle = lg; g.fillRect(cx - sw, cy - rh, sw * 2, rh * 2);
      for (let k = 0; k < 6; k++) { g.fillStyle = `rgba(${R() < 0.5 ? '255,250,240' : '0,0,0'},0.07)`; g.beginPath(); g.arc(cx + (R() - 0.5) * sw * 0.7, cy + (R() - 0.5) * rh * 0.6, 4 + R() * 10, 0, 7); g.fill(); }
      g.restore();
      x += sw * (0.92 + R() * 0.1);
    }
    y += rh * 0.93;
  }
  g.fillStyle = '#b3ab9c'; g.fillRect(0, 0, w, 24); g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(0, 22, w, 7);   // the cap
  return kit.prepPaper(c, { edge: 5 });
}

// Kīlauea's mobile south flank, closed through the sea: from the summit along the east rift zone to Cape Kumukahi, offshore, back up the
// southwest rift zone (rift lines approximate; the coast comes from the grid's 0 m contour)
const FLANK = [[-155.287, 19.398], [-155.25, 19.383], [-155.21, 19.372], [-155.17, 19.364], [-155.106, 19.384], [-155.05, 19.40], [-154.98, 19.424], [-154.90, 19.458],
  [-154.83, 19.503], [-154.78, 19.52], [-154.70, 19.40], [-154.80, 19.20], [-155.10, 19.05], [-155.45, 19.08], [-155.56, 19.17], [-155.47, 19.235], [-155.40, 19.29],
  [-155.34, 19.35], [-155.30, 19.388]];

// ---- data (built in the scratchpad by ch2_tools/segment.py, footprints.py, crest.py and the TIGERweb queries; sources in the header)
// SLIDES: lon/lat rings per slide; CREST: [lon, lat, h m] along the Koʻolau crest; MANHATTAN_KM: the island in km, long axis along +x
const SLIDES = {"nuuanu":[[[-158.196,21.838],[-158.175,21.873],[-158.18,21.965],[-158.165,22.04],[-158.157,22.058],[-158.118,22.096],[-158.058,22.142],[-157.997,22.161],[-157.835,22.179],[-157.665,22.339],[-157.641,22.377],[-157.605,22.414],[-157.585,22.426],[-157.544,22.434],[-157.509,22.467],[-157.484,22.525],[-157.469,22.638],[-157.47,22.656],[-157.498,22.711],[-157.506,22.748],[-157.494,22.767],[-157.474,22.782],[-157.454,22.79],[-157.415,22.779],[-157.392,22.783],[-157.373,22.791],[-157.293,22.847],[-157.252,22.862],[-157.11,22.867],[-157.049,22.89],[-156.909,22.976],[-156.744,23.024],[-156.719,23.024],[-156.642,23.01],[-156.581,22.987],[-156.545,22.953],[-156.508,22.878],[-156.47,22.846],[-156.449,22.838],[-156.328,22.845],[-156.287,22.86],[-156.266,22.875],[-156.246,22.879],[-156.206,22.864],[-156.085,22.733],[-156.077,22.658],[-156.093,22.564],[-156.149,22.452],[-156.238,22.34],[-156.299,22.288],[-156.38,22.25],[-156.46,22.194],[-156.724,22.083],[-156.753,22.049],[-156.79,21.973],[-156.817,21.936],[-157.019,21.78],[-157.073,21.726],[-157.117,21.67],[-157.157,21.575],[-157.161,21.557],[-157.153,21.538],[-157.161,21.519],[-157.281,21.533],[-157.34,21.555],[-157.382,21.548],[-157.422,21.552],[-157.426,21.57],[-157.418,21.59],[-157.418,21.622],[-157.437,21.646],[-157.456,21.652],[-157.535,21.652],[-157.57,21.666],[-157.604,21.651],[-157.627,21.665],[-157.642,21.666],[-157.665,21.688],[-157.665,21.711],[-157.652,21.736],[-157.66,21.758],[-157.671,21.775],[-157.711,21.801],[-157.714,21.812],[-157.742,21.837],[-157.796,21.838],[-157.807,21.846],[-157.872,21.846],[-157.904,21.867],[-157.949,21.868],[-157.973,21.883],[-158.011,21.883],[-158.023,21.891],[-158.04,21.89],[-158.079,21.868],[-158.126,21.853],[-158.16,21.855],[-158.179,21.838],[-158.196,21.838]]],"n_kauai":[[[-159.26,22.634],[-159.27,22.691],[-159.252,22.7],[-159.121,22.7],[-159.089,22.686],[-159.047,22.7],[-158.667,22.699],[-158.654,22.688],[-158.651,22.664],[-158.635,22.629],[-158.577,22.573],[-158.557,22.498],[-158.569,22.426],[-158.581,22.407],[-158.632,22.388],[-158.648,22.371],[-158.651,22.33],[-158.64,22.292],[-158.655,22.272],[-158.67,22.264],[-158.689,22.265],[-158.754,22.291],[-158.775,22.294],[-158.829,22.273],[-158.847,22.257],[-158.859,22.234],[-158.87,22.181],[-158.857,22.07],[-158.886,22.052],[-158.928,22.059],[-158.955,22.082],[-158.965,22.102],[-158.951,22.172],[-158.953,22.201],[-158.968,22.23],[-158.975,22.263],[-158.998,22.281],[-159.03,22.289],[-159.09,22.371],[-159.102,22.417],[-159.096,22.447],[-159.12,22.477],[-159.12,22.512],[-159.126,22.526],[-159.156,22.559],[-159.191,22.57],[-159.199,22.601],[-159.208,22.613],[-159.26,22.634]],[[-159.854,22.6],[-159.858,22.624],[-159.851,22.659],[-159.838,22.691],[-159.825,22.7],[-159.371,22.7],[-159.358,22.695],[-159.351,22.684],[-159.351,22.667],[-159.36,22.656],[-159.389,22.651],[-159.449,22.623],[-159.485,22.582],[-159.529,22.576],[-159.567,22.522],[-159.608,22.525],[-159.644,22.518],[-159.68,22.468],[-159.707,22.459],[-159.721,22.447],[-159.736,22.415],[-159.77,22.391],[-159.793,22.359],[-159.841,22.348],[-159.86,22.357],[-159.862,22.377],[-159.84,22.414],[-159.836,22.438],[-159.807,22.471],[-159.802,22.49],[-159.812,22.51],[-159.861,22.545],[-159.854,22.6]]],"s_kauai":[[[-160.027,21.469],[-160.018,21.486],[-159.934,21.544],[-159.901,21.592],[-159.86,21.595],[-159.847,21.583],[-159.837,21.534],[-159.814,21.51],[-159.769,21.503],[-159.748,21.467],[-159.701,21.441],[-159.66,21.441],[-159.627,21.418],[-159.56,21.422],[-159.552,21.413],[-159.549,21.387],[-159.537,21.361],[-159.522,21.352],[-159.48,21.348],[-159.458,21.327],[-159.454,21.301],[-159.445,21.287],[-159.408,21.263],[-159.387,21.261],[-159.364,21.278],[-159.364,21.317],[-159.355,21.336],[-159.325,21.357],[-159.318,21.401],[-159.305,21.41],[-159.278,21.416],[-159.266,21.433],[-159.266,21.465],[-159.303,21.551],[-159.287,21.606],[-159.288,21.634],[-159.28,21.654],[-159.261,21.672],[-159.24,21.677],[-159.189,21.66],[-159.148,21.668],[-159.115,21.692],[-159.092,21.698],[-159.071,21.714],[-159.042,21.714],[-159.019,21.722],[-158.975,21.722],[-158.932,21.712],[-158.907,21.7],[-158.893,21.68],[-158.906,21.646],[-158.91,21.59],[-158.923,21.537],[-158.942,21.521],[-158.983,21.504],[-159.039,21.45],[-159.051,21.43],[-159.089,21.299],[-159.088,21.258],[-159.069,21.187],[-159.115,21.078],[-159.167,21.0],[-159.208,20.979],[-159.266,20.978],[-159.308,20.988],[-159.407,20.987],[-159.448,20.993],[-159.487,20.985],[-159.547,20.962],[-159.604,20.971],[-159.619,20.991],[-159.621,21.04],[-159.63,21.055],[-159.649,21.067],[-159.698,21.069],[-159.716,21.083],[-159.724,21.157],[-159.772,21.211],[-159.778,21.265],[-159.788,21.285],[-159.812,21.301],[-159.904,21.3],[-159.925,21.308],[-159.938,21.327],[-159.94,21.4],[-159.946,21.418],[-159.966,21.435],[-160.006,21.442],[-160.023,21.456],[-160.027,21.469]]],"waianae":[[[-158.867,20.673],[-158.872,20.793],[-158.807,20.898],[-158.767,20.929],[-158.63,20.974],[-158.615,20.988],[-158.612,21.005],[-158.617,21.018],[-158.688,21.098],[-158.69,21.113],[-158.683,21.124],[-158.621,21.134],[-158.601,21.124],[-158.572,21.071],[-158.584,21.037],[-158.578,21.015],[-158.52,20.987],[-158.486,20.951],[-158.466,20.947],[-158.447,20.956],[-158.422,20.987],[-158.4,20.999],[-158.392,21.015],[-158.394,21.033],[-158.415,21.064],[-158.419,21.086],[-158.439,21.109],[-158.437,21.126],[-158.403,21.147],[-158.373,21.177],[-158.344,21.177],[-158.31,21.191],[-158.288,21.179],[-158.234,21.123],[-158.196,21.117],[-158.154,21.087],[-158.15,21.064],[-158.158,21.04],[-158.156,21.001],[-158.078,20.915],[-158.065,20.892],[-158.031,20.879],[-157.992,20.833],[-157.985,20.752],[-157.976,20.74],[-157.954,20.727],[-157.948,20.711],[-157.97,20.621],[-157.981,20.604],[-158.002,20.597],[-158.084,20.593],[-158.12,20.6],[-158.179,20.624],[-158.205,20.627],[-158.319,20.678],[-158.362,20.719],[-158.369,20.757],[-158.379,20.774],[-158.402,20.791],[-158.424,20.793],[-158.457,20.769],[-158.479,20.736],[-158.485,20.695],[-158.511,20.639],[-158.519,20.564],[-158.535,20.525],[-158.555,20.509],[-158.592,20.494],[-158.653,20.482],[-158.752,20.514],[-158.808,20.56],[-158.867,20.673]]],"wailau":[[[-157.127,21.553],[-157.124,21.583],[-157.089,21.623],[-157.073,21.676],[-157.048,21.712],[-156.985,21.764],[-156.931,21.821],[-156.893,21.842],[-156.848,21.843],[-156.827,21.852],[-156.804,21.888],[-156.734,21.941],[-156.729,21.957],[-156.732,21.988],[-156.701,22.037],[-156.688,22.045],[-156.66,22.044],[-156.648,22.038],[-156.637,22.018],[-156.651,21.966],[-156.642,21.908],[-156.652,21.89],[-156.691,21.873],[-156.703,21.857],[-156.703,21.84],[-156.693,21.818],[-156.693,21.753],[-156.727,21.702],[-156.736,21.577],[-156.662,21.493],[-156.644,21.482],[-156.48,21.487],[-156.438,21.482],[-156.403,21.469],[-156.389,21.445],[-156.401,21.362],[-156.419,21.348],[-156.498,21.358],[-156.525,21.393],[-156.547,21.402],[-156.588,21.39],[-156.644,21.387],[-156.675,21.399],[-156.71,21.39],[-156.768,21.396],[-156.821,21.388],[-156.868,21.404],[-156.911,21.4],[-156.946,21.38],[-156.98,21.392],[-157.088,21.387],[-157.106,21.406],[-157.102,21.46],[-157.086,21.472],[-157.059,21.465],[-157.041,21.47],[-157.023,21.487],[-157.021,21.508],[-157.028,21.521],[-157.043,21.53],[-157.109,21.53],[-157.127,21.553]]],"clark":[[[-157.684,20.395],[-157.607,20.465],[-157.568,20.476],[-157.551,20.474],[-157.527,20.436],[-157.525,20.346],[-157.518,20.327],[-157.494,20.317],[-157.459,20.334],[-157.415,20.338],[-157.399,20.364],[-157.41,20.392],[-157.41,20.409],[-157.385,20.455],[-157.387,20.47],[-157.406,20.5],[-157.396,20.538],[-157.395,20.575],[-157.381,20.593],[-157.354,20.599],[-157.34,20.588],[-157.335,20.555],[-157.28,20.46],[-157.282,20.445],[-157.305,20.419],[-157.318,20.385],[-157.316,20.357],[-157.303,20.341],[-157.264,20.328],[-157.228,20.328],[-157.186,20.318],[-157.141,20.293],[-157.044,20.291],[-157.02,20.277],[-157.004,20.251],[-156.978,20.239],[-156.903,20.256],[-156.857,20.258],[-156.821,20.283],[-156.783,20.278],[-156.739,20.294],[-156.72,20.284],[-156.708,20.254],[-156.719,20.225],[-156.754,20.205],[-156.795,20.207],[-156.851,20.195],[-156.896,20.209],[-156.91,20.204],[-156.921,20.19],[-156.922,20.172],[-156.915,20.159],[-156.866,20.125],[-156.831,20.121],[-156.795,20.13],[-156.781,20.126],[-156.768,20.103],[-156.779,20.084],[-156.863,20.079],[-156.905,20.05],[-156.944,20.042],[-156.964,20.042],[-157.004,20.055],[-157.042,20.047],[-157.078,20.058],[-157.099,20.054],[-157.122,20.037],[-157.136,20.016],[-157.147,19.943],[-157.16,19.928],[-157.174,19.925],[-157.195,19.941],[-157.213,19.973],[-157.175,20.012],[-157.17,20.028],[-157.173,20.077],[-157.202,20.112],[-157.209,20.135],[-157.2,20.165],[-157.188,20.181],[-157.152,20.202],[-157.149,20.228],[-157.18,20.26],[-157.218,20.265],[-157.254,20.285],[-157.279,20.279],[-157.298,20.252],[-157.286,20.216],[-157.294,20.136],[-157.269,20.091],[-157.265,20.015],[-157.249,19.977],[-157.277,19.932],[-157.276,19.917],[-157.249,19.865],[-157.256,19.848],[-157.272,19.843],[-157.321,19.875],[-157.322,19.891],[-157.309,19.92],[-157.321,19.945],[-157.392,19.985],[-157.413,19.981],[-157.438,19.961],[-157.46,19.96],[-157.534,20.018],[-157.557,20.027],[-157.57,20.042],[-157.596,20.114],[-157.614,20.141],[-157.61,20.156],[-157.576,20.189],[-157.568,20.208],[-157.572,20.224],[-157.595,20.247],[-157.6,20.264],[-157.599,20.355],[-157.619,20.375],[-157.634,20.376],[-157.668,20.362],[-157.681,20.367],[-157.688,20.378],[-157.684,20.395]]],"alika":[[[-156.737,19.356],[-156.737,19.38],[-156.73,19.393],[-156.654,19.432],[-156.608,19.448],[-156.518,19.433],[-156.425,19.435],[-156.399,19.453],[-156.368,19.496],[-156.361,19.527],[-156.377,19.552],[-156.409,19.567],[-156.49,19.568],[-156.53,19.586],[-156.553,19.605],[-156.578,19.657],[-156.586,19.695],[-156.586,19.749],[-156.567,19.811],[-156.553,19.826],[-156.532,19.836],[-156.455,19.814],[-156.398,19.767],[-156.396,19.698],[-156.388,19.676],[-156.311,19.614],[-156.294,19.552],[-156.271,19.521],[-156.24,19.498],[-156.241,19.479],[-156.266,19.451],[-156.262,19.426],[-156.207,19.362],[-156.191,19.358],[-156.141,19.36],[-156.119,19.341],[-156.108,19.299],[-156.108,19.216],[-156.097,19.185],[-156.113,19.15],[-156.151,19.135],[-156.162,19.112],[-156.147,19.076],[-156.145,19.048],[-156.129,19.024],[-156.117,18.975],[-156.128,18.945],[-156.131,18.914],[-156.26,18.779],[-156.274,18.773],[-156.3,18.791],[-156.311,18.875],[-156.332,18.898],[-156.349,18.904],[-156.411,18.904],[-156.487,18.89],[-156.529,18.898],[-156.566,18.916],[-156.596,18.952],[-156.611,18.993],[-156.647,19.044],[-156.652,19.063],[-156.641,19.159],[-156.639,19.274],[-156.667,19.307],[-156.725,19.334],[-156.737,19.356]]],"kalae":[[[-156.245,18.567],[-156.262,18.625],[-156.239,18.708],[-156.263,18.759],[-156.263,18.773],[-156.124,18.921],[-156.106,18.927],[-156.081,18.903],[-156.041,18.884],[-155.995,18.889],[-155.976,18.869],[-155.951,18.858],[-155.916,18.818],[-155.85,18.782],[-155.821,18.778],[-155.807,18.766],[-155.8,18.719],[-155.759,18.679],[-155.761,18.664],[-155.782,18.646],[-155.788,18.627],[-155.778,18.572],[-155.751,18.535],[-155.745,18.512],[-155.763,18.457],[-155.806,18.406],[-155.843,18.407],[-155.899,18.446],[-155.906,18.47],[-155.879,18.499],[-155.871,18.526],[-155.847,18.559],[-155.842,18.597],[-155.857,18.633],[-155.872,18.652],[-155.93,18.701],[-155.946,18.726],[-155.961,18.733],[-156.015,18.726],[-156.05,18.695],[-156.054,18.665],[-156.048,18.626],[-156.054,18.6],[-156.042,18.543],[-156.053,18.525],[-156.126,18.524],[-156.149,18.556],[-156.167,18.565],[-156.181,18.564],[-156.203,18.55],[-156.216,18.551],[-156.245,18.567]]]};
const CREST = [[-157.6737,21.309,36],[-157.6773,21.3157,272],[-157.684,21.3197,293],[-157.6971,21.3184,333],[-157.7105,21.3167,405],[-157.72,21.3185,497],[-157.7276,21.3218,549],[-157.7373,21.3233,714],[-157.7463,21.3254,705],[-157.7541,21.3285,693],[-157.7623,21.3313,718],[-157.7716,21.3332,661],[-157.7797,21.336,663],[-157.7858,21.3406,584],[-157.7886,21.3479,764],[-157.7892,21.3571,916],[-157.7921,21.3644,412],[-157.7999,21.3675,518],[-157.8083,21.3701,717],[-157.813,21.3758,413],[-157.8183,21.3811,483],[-157.8235,21.3864,727],[-157.8268,21.3933,775],[-157.8326,21.3981,445],[-157.8379,21.4034,519],[-157.839,21.4121,737],[-157.8426,21.4188,812],[-157.8486,21.4234,717],[-157.8555,21.4273,690],[-157.8616,21.4318,666],[-157.8675,21.4366,669],[-157.8732,21.4414,636],[-157.8751,21.4495,693],[-157.8771,21.4576,740],[-157.8838,21.4616,759],[-157.8896,21.4664,618],[-157.8912,21.4748,805],[-157.8925,21.4833,752],[-157.8941,21.4916,791],[-157.8978,21.4982,754],[-157.9031,21.5035,694],[-157.9079,21.5091,740],[-157.9127,21.5148,661],[-157.9166,21.5212,733],[-157.9198,21.5282,721],[-157.9213,21.5366,761],[-157.9208,21.5467,838],[-157.923,21.5545,838],[-157.9269,21.5609,847],[-157.9321,21.5662,823],[-157.9375,21.5714,792],[-157.9411,21.5781,752],[-157.9459,21.5837,719],[-157.9523,21.588,683],[-157.9573,21.5935,672],[-157.9616,21.5996,640],[-157.9662,21.6053,595],[-157.9716,21.6105,569],[-157.9757,21.6167,504],[-157.9787,21.6239,504],[-157.9836,21.6294,518],[-157.9885,21.6351,486],[-157.9917,21.6421,442]];
const MANHATTAN_KM = [[9.14,-0.72],[7.31,-1.24],[7.25,-1.03],[7.12,-0.98],[6.78,-1.09],[6.8,-1.37],[6.32,-1.47],[6.26,-1.31],[6.14,-1.27],[6.02,-1.37],[6.04,-1.58],[5.74,-1.41],[5.51,-1.49],[5.29,-1.75],[5.11,-1.59],[4.96,-1.62],[4.94,-1.9],[3.92,-2.12],[3.81,-1.99],[3.27,-1.95],[3.16,-2.18],[2.94,-1.95],[2.79,-1.97],[2.75,-2.11],[2.2,-2.08],[1.28,-1.95],[1.18,-1.74],[0.66,-1.69],[0.54,-1.86],[0.39,-1.67],[-4.04,-1.29],[-4.87,-1.12],[-5.0,-1.28],[-5.43,-1.25],[-5.72,-1.04],[-7.53,-1.12],[-8.16,-1.46],[-8.57,-1.24],[-9.43,-1.15],[-10.38,-1.08],[-10.63,-1.18],[-11.3,-1.17],[-11.63,-1.04],[-11.7,-0.77],[-11.59,-0.6],[-11.57,-0.31],[-11.69,0.17],[-11.62,0.41],[-11.21,0.53],[-10.55,0.46],[-9.82,0.22],[-8.24,0.11],[-6.96,0.15],[-5.39,0.92],[-4.37,1.31],[-3.67,2.09],[-3.15,2.29],[-2.47,1.99],[-1.73,1.93],[-1.39,1.75],[-1.17,1.79],[-0.7,2.16],[2.54,1.45],[3.68,1.29],[4.43,1.53],[4.66,1.49],[4.91,1.66],[5.06,1.91],[5.33,2.02],[7.07,2.25],[7.38,1.98],[7.69,1.45],[7.67,1.31],[8.06,0.73],[8.28,0.59],[8.46,0.67],[8.78,0.53],[9.0,0.32],[9.24,0.27],[9.34,0.1],[9.38,-0.33],[9.14,-0.72]];
