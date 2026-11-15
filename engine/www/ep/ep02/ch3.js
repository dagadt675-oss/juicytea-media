// Chapter 3 "The Island Stands Up" (s049-s083), window K.chapter(3) (181.65-315.55 s, last shot to t1x). Built 2026-11-09, round 2 the same
// day after the ch3 review. Every beat is keyed to Rodney's markers (K.T / K.lead / K.word), never to seconds. Base layer 0, in order:
//   s049-s051  opens on ch2's last camera (CH3_IN) and descends in 1.6 s to a low camera off the Hāmākua coast riding the falling sea
//              (SEA LEVEL gauge, marker only); {isl} pullback (bigisland -> main_chain on one camera) until every main island stands on
//              one dry ridge (joined at -3,008 m on this grid); {range} a hero-orange crest line; the dive lands on {up}: a low long-lens
//              camera 72 km NE of Mauna Kea, 0.65 km over the -3,500 m water: base to summits fill about 70 % of the frame, a 10 % push
//              through the pause (impact on the word).
//   s052-s058  the camera rises (pins on the visible summits); {mtn} hero-orange waterline outline (open at the Alenuihāhā saddle);
//              {shape} lateral move along the NE flank in raking light from the east; {slopes} the 0 m line brightens in the upper
//              third (a 6 deg look-down); {upthere} soft cap tint; {going}/{going2} tilt down while the sea falls to -5,470 m; s057 from
//              ENE, 17 km up: the east flank, the water left in the Hawaiian Deep along its foot glows cyan ({trench}); {rem} push,
//              {clue} pulse (the loop paid in ch6).
//   s059-s063  Everest at the same scale (see ACT 2): eye 126 km NE of Mauna Kea, Everest a forced-perspective prop 25 km to its right;
//              four moving framings; {seafloor} Everest sinks 6,000 m, the last water drains and the camera cranes down to the floor so
//              both feet stand on the yellow -6,000 m line; bar + FROM THE SEA FLOOR / 33,000+ FT on {tall33} (punch on the hit_body);
//              {ev2} tick; JUICE CHECK: TRUE at the end of "one.".
//   s064-s065  GAG: Everest's summit from 10 km: the paper climber leans into the wind in paper spindrift, plants a pennant ({this});
//              whip on "road" to Mauna Kea's upper slope from 5.4 km: the paper jeep on the real access road (USGS), the summit
//              cones above; whip back: the pennant hangs limp from the upright pole (flag_droop).
//   s066-s070  fully drained from here: {giant} orbit, Mauna Kea dims under a quick outline; {loa} Mauna Loa's map area takes the hero
//              fill; {bigger} it swells over its drained flanks; {active} LARGEST ACTIVE VOLCANO; s069 today's island, Mauna Loa about
//              half ({half} pulse); s070 lowering to Mauna Loa's southern base.
//   s071-s075  TWIST: the only hot-spot cut-away (az 306 through Kīlauea, 42 km deep): a noise-shaped warm zone clipped to the face;
//              {moving} the glow stays put on screen while the section and island slide NW past it; {candle} paper strip + candle;
//              s073 the chain under an opaque paper sheet, the flame burns each island's own coastline into it; {spots} the sheet
//              dissolves onto the real coasts; {plate} the sheet returns at 36 % over the sea (islands cut out) sliding NW, a yellow
//              arrow along the chain; {deepbelow} marker; {built} the Big Island's outline edges NW.
//   s076-s079  {sinks} the drained Kohala flank (the film's drained look); {reefs} cream lines on each terrace edge from {steps}+0.3 s,
//              kept into s078 where they drown as the sea rises; s079 the sea drains again, the camera tilts down the staircase into
//              the blue distance (the deep lines turn blue).
//   s080-s083  today's sea level: {bornhere} pullback, rims in turn; {last} fade; {baby} rim; {bigbaby} crash zoom OUT (motion blur),
//              a push, a 6-frame settle on the impact_short; {become} back on the Big Island (ch4's card).
// Geometry (no invented shapes; img/ch3/ch3_geo.json, sources in img/ch3/LICENSE.md): volcano map areas USGS OF 2007-1089; Mauna Loa /
// Mauna Kea below the old shore = nearest-volcano partition (APPROXIMATE, fill only, never labelled); the summit access road USGS
// National Map (TIGER); waterlines, coasts, crest and terrace edges from the region grids. Deviations: the Everest prop and the stand-up
// held at -3,500 m during s052-s055 (one waterline for the outline); s072's metaphor moves to the chain view at s073; the jeep is the
// 1942 FSA photo (a civilian 4WD is requested); the climber wears a jacket (the kit's NPS photo).
// Local helpers only (no shared change): camOf/orbit/chainPath (multi-key flights without stops), blurred() sub-frame motion blur, the
// Everest prop (registered in S._sections so other shots on the stage hide it), paper candle / sheet / flag, the JUICE CHECK stamp.
import { PAL, E, F, THREE, MOVE_WATER, WATER_FILM, mixState, heightGrid, terrainCamOf } from './shared.js';
import { loadH16, loadTex, heightTexture, sampleH, KM_DEG } from '../../lab/hawaii/hterrain.js';

const D2R = Math.PI / 180, KM = 111.32, FT = 3.28084;
const MK = [-155.468, 19.82], ML = [-155.6054, 19.4756], KIL = [-155.287, 19.407], HUAL = [-155.864, 19.692], KOH = [-155.716, 20.086];
const EV_SUM = [86.9254, 27.9893];
// ---------------------------------------------------------------------------------------------------------------- geo helpers
const offLL = (ll, km, brg) => { const cl = Math.cos(ll[1] * D2R); return [ll[0] + km * Math.sin(brg * D2R) / (KM * cl), ll[1] + km * Math.cos(brg * D2R) / KM]; };
const brgOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return (Math.atan2((b[0] - a[0]) * cl, b[1] - a[1]) / D2R + 360) % 360; };
const kmOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return Math.hypot((b[0] - a[0]) * cl * KM, (b[1] - a[1]) * KM); };
// orbit camera (target lon/lat/h m, d km eye-target, tilt deg from straight down, heading deg) -> HawaiiStage camera (flat local frame)
function camOf(c) {
  const e = offLL([c.lon, c.lat], c.d * Math.sin(c.tilt * D2R), c.heading + 180);
  return { lon: e[0], lat: e[1], alt: (c.h || 0) / 1000 + c.d * Math.cos(c.tilt * D2R), tLon: c.lon, tLat: c.lat, tH: c.h || 0, fov: c.fov,
    near: F.clamp(c.d * 0.003, 0.004, 2), far: F.clamp(c.d * 300, 400, 9000) };
}
// orbit key from an eye (lon/lat, alt km) and a target (lon/lat, h m)
function orbit(t, eye, alt, tgt, h, fov, ease) { const dh = kmOf(eye, tgt), dv = alt - h / 1000;
  return { t, lon: tgt[0], lat: tgt[1], h, d: Math.hypot(dh, dv), tilt: Math.atan2(dh, dv) / D2R, heading: brgOf(eye, tgt), fov, ease }; }
// monotone cubic (Fritsch-Carlson) through [x, y] keys: never overshoots or reverses, zero slope at both ends
function monotone(keys) {
  const n = keys.length, x = keys.map(k => k[0]), y = keys.map(k => k[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
  m[0] = 0; m[n - 1] = 0;
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : 3 * (x[i + 1] - x[i - 1]) / ((2 * x[i + 1] - x[i] - x[i - 1]) / d[i - 1] + (x[i + 1] + x[i] - 2 * x[i - 1]) / d[i]);   // weighted harmonic mean (Fritsch-Butland)
  return (t) => { if (t <= x[0]) return y[0]; if (t >= x[n - 1]) return y[n - 1];
    let i = 0; while (t > x[i + 1]) i++; const h = x[i + 1] - x[i], s = (t - x[i]) / h, s2 = s * s, s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * y[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * y[i + 1] + (s3 - s2) * h * m[i + 1]; };
}
// one continuous flight through orbit keys (per-channel monotone cubic: eases in at the first key, out at the last, no stop inside)
function chainPath(keys) {
  const hd = [keys[0].heading];
  for (let i = 1; i < keys.length; i++) hd.push(hd[i - 1] + ((((keys[i].heading - keys[i - 1].heading) % 360) + 540) % 360 - 180));
  const ch = (f) => monotone(keys.map((k, i) => [k.t, f(k, i)]));
  const C = { lon: ch(k => k.lon), lat: ch(k => k.lat), ld: ch(k => Math.log(k.d)), tilt: ch(k => k.tilt), hd: ch((k, i) => hd[i]), fov: ch(k => k.fov), h: ch(k => k.h || 0) };
  return (t) => ({ lon: C.lon(t), lat: C.lat(t), d: Math.exp(C.ld(t)), tilt: C.tilt(t), heading: C.hd(t), fov: C.fov(t), h: C.h(t) });
}
// several flights in a row: [[t0, t1, fn], ...] (each fn eases to rest at its own ends: a hold between them)
const route = (...segs) => (t) => { for (const [a, b, f] of segs) if (t <= b) return f(Math.max(t, a)); const L = segs[segs.length - 1]; return L[2](L[1]); };
// film water seen from far above blends toward the globe's navy (as scaleMove does), so far views never read saturated teal
function farWater(d) {
  const k = E.inOut(F.clamp((Math.log(d) - Math.log(25)) / (Math.log(500) - Math.log(25))));
  return k > 0 ? WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], k))) : null;
}
// sub-frame motion blur for whips and the crash zoom (renders the shot n times inside the shutter and averages; drafts 3)
function blurred(shot, w0, w1, n = 6, shutter = 0.5) {
  const inner = shot.draw.bind(shot);
  shot.draw = async function (ctx, lt, t, api) {
    if (t < w0 || t > w1 || api.Q.noblur) return inner(ctx, lt, t, api);
    const A = ctx.globalAlpha, dt = shutter / api.FPS, m = api.Q.draft ? 3 : n;
    for (let k = 0; k < m; k++) { const o = (k / (m - 1) - 0.5) * dt; ctx.save(); ctx.globalAlpha = A / (k + 1); await inner(ctx, lt + o, t + o, api); ctx.restore(); }
  };
  return shot;
}
// await a lazy data step before a shot draws (its mask() runs before world(), so a single still must not miss the data)
function ready(shot, fn) { const d = shot.draw.bind(shot); shot.draw = async function (ctx, lt, t, api) { await fn(); return d(ctx, lt, t, api); }; return shot; }
const hash = (a, b = 0) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };
const inPoly = (x, y, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
const centroid = (r) => { let a = 0, x = 0, y = 0; for (let i = 0; i < r.length - 1; i++) { const [x0, y0] = r[i], [x1, y1] = r[i + 1], c = x0 * y1 - x1 * y0; a += c; x += (x0 + x1) * c; y += (y0 + y1) * c; } return [x / (3 * a), y / (3 * a)]; };

// ---------------------------------------------------------------------------------------------------------------- Everest prop
// Everest's real terrain as a round patch (radius 10.5 km about the summit): region 'everest' (14 m heights, HLS colour) inside its
// bbox, region 'everest_wide' (92 m) out to the rim, heights scaled so the summit is 8,849 m. From the patch rim a rock apron (talus with
// strata bands, the rim's own colour at its top) flares out and down at about 33 deg to the sea-level datum (y 0): no vertical wall
// stands above the datum. Below the datum a darker plain pedestal whose depth is set per frame (it reaches the virtual sea floor at
// -6,000 m and shrinks to nothing as Everest sinks onto that floor). Lit by the stage's sun and sky, hazed like the stage. Forced
// perspective (place): the group is put k of the way from the eye to its virtual spot and scaled by k, curvature and haze computed for
// the virtual distance, so on screen it is exactly the true-scale Everest there, for the eye of that frame (place() runs every frame).
const EV_VS = /* glsl */`
uniform vec3 camPos; uniform float kS, pedD;
attribute vec2 uvW; attribute float wf, tw;
varying vec2 vUv, vUvW; varying vec3 vW, vN; varying float vLy, vWf, vTw;
void main(){
  vUv = uv; vUvW = uvW; vWf = wf; vTw = tw; vec3 p = position; if (p.y < -1e-5) p.y *= pedD;
  vLy = p.y; vec4 w = modelMatrix * vec4(p, 1.0);
  vec2 d = w.xz - camPos.xz; w.y -= dot(d, d) / (kS * 2.0 * 6371.0);
  vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * w;
}`;
const EV_FS = /* glsl */`
uniform vec3 camPos, sunDir, zenithCol, hazeCol, sunCol, glowCol; uniform float fogDens, fogH, fogBg, fogBase;
uniform float sunI, skyI, kS, mode, gain, sat, lift, hScale; uniform vec2 texF, texW, kmF, kmW;
uniform sampler2D colF, colW, aoF, aoW, hF, hW;
varying vec2 vUv, vUvW; varying vec3 vW, vN; varying float vLy, vWf, vTw;
vec3 inscatter(vec3 d){ float mu = max(dot(d, sunDir), 0.0); return hazeCol + glowCol * (pow(mu, 5.0) * 0.40); }
vec3 aerial(vec3 col, vec3 wp, out float T){
  vec3 v = wp - camPos; float dist = length(v); vec3 d = v / max(dist, 1e-4);
  float y0 = max(camPos.y - fogBase, 0.0), y1 = max(wp.y - fogBase, 0.0), dy = y1 - y0;
  float od = abs(dy) < 1e-3 ? fogDens * exp(-y0 / fogH) * dist : fogDens * dist * fogH * (exp(-y0 / fogH) - exp(-y1 / fogH)) / dy;
  od += fogBg * dist; T = exp(-od);
  return col * T + inscatter(d) * (1.0 - T);
}
vec3 nrm(sampler2D h, vec2 uv, vec2 tx, vec2 km){
  float hl = texture2D(h, uv - vec2(tx.x, 0.0)).r, hr = texture2D(h, uv + vec2(tx.x, 0.0)).r, hd = texture2D(h, uv - vec2(0.0, tx.y)).r, hu = texture2D(h, uv + vec2(0.0, tx.y)).r;
  return normalize(vec3(-(hr - hl) * hScale * 0.001 / (2.0 * km.x), 1.0, (hu - hd) * hScale * 0.001 / (2.0 * km.y)));
}
vec3 grade(vec3 a){ float l0 = dot(a, vec3(0.2126, 0.7152, 0.0722)); a = max(mix(vec3(l0), a, sat), 0.0) * gain;
  float ld = dot(a, vec3(0.2126, 0.7152, 0.0722)); return mix(a, max(a, vec3(lift) * vec3(1.0, 0.97, 0.92)), 1.0 - smoothstep(lift * 0.4, lift * 1.4, ld)); }
void main(){
  vec3 n = normalize(vN), alb; float ao = 1.0;
  if (mode < 0.5) {
    n = normalize(mix(nrm(hW, vUvW, texW, kmW), nrm(hF, vUv, texF, kmF), vWf));
    alb = grade(mix(texture2D(colW, vUvW).rgb, texture2D(colF, vUv).rgb, vWf));
    ao = mix(texture2D(aoW, vUvW).r, texture2D(aoF, vUv).r, vWf);
  } else {
    // apron (mode 1): the real colour and relief of the ground at that map position (everest_wide, continued outward) over dark rock in
    // faint strata bands; pedestal (mode 2): plain dark rock with the same bands
    float b = fract(vLy / 0.55 + 0.11 * sin(vLy * 2.3)), band = 0.92 + 0.1 * smoothstep(0.1, 0.3, b) * (1.0 - smoothstep(0.72, 0.95, b));
    vec3 rock = vec3(0.085, 0.079, 0.070) * band;
    if (mode < 1.5) { vec3 nW = nrm(hW, vUvW, texW, kmW); n = normalize(n + (nW - vec3(0.0, 1.0, 0.0)) * 0.8);
      alb = mix(rock, grade(texture2D(colW, vUvW).rgb) * 0.8, vTw); ao = texture2D(aoW, vUvW).r; }
    else alb = rock * (0.55 + 0.12 * smoothstep(-6.0, 0.0, vLy));
  }
  float ndl = max(dot(n, sunDir), 0.0);
  vec3 sky = mix(hazeCol, zenithCol, 0.55);
  vec3 col = alb * (sunCol * sunI * ndl + sky * skyI * ao * (0.55 + 0.45 * n.y) + vec3(0.05, 0.04, 0.03) * (1.0 - n.y));
  vec3 wv = camPos + (vW - camPos) / kS;
  float T; col = aerial(col, wv, T);
  gl_FragColor = vec4(col, 1.0);
}`;
async function everestProp(S, kit) {
  if (S._ch3ev) return S._ch3ev;
  const RI = kit.hub.regionIndex || {}; if (!RI.everest || !RI.everest_wide) throw new Error('region everest / everest_wide missing');
  const ld = async (R) => { const hm = await loadH16(R.dir + '/' + R.files.h16, { hmin: R.hmin ?? -8000, hrange: R.hrange ?? 17000 });
    const [col, ao] = await Promise.all([loadTex(R.dir + '/' + R.files.color, true), loadTex(R.dir + '/' + R.files.ao, false)]); return { bb: R.bbox, hm, col, ao, ht: heightTexture(hm) }; };
  const [LF, LW] = await Promise.all([ld(RI.everest), ld(RI.everest_wide)]);
  const uvOf = (L, lon, lat) => [(lon - L.bb[0]) / (L.bb[2] - L.bb[0]), (lat - L.bb[1]) / (L.bb[3] - L.bb[1])];
  let best = -1e9; for (let j = -30; j <= 30; j++) for (let i = -30; i <= 30; i++) best = Math.max(best, sampleH(LF.hm, ...uvOf(LF, EV_SUM[0] + i * 0.0003, EV_SUM[1] + j * 0.0003)));
  const hS = 8849 / best, RAD = 10.5, NR = 190, NA = 400, NJ = 9, kmLon = KM_DEG * Math.cos(EV_SUM[1] * D2R), SLOPE = Math.tan(33 * D2R);
  const fineW = (lon, lat) => { const b = LF.bb, dk = Math.min((lon - b[0]) * kmLon, (b[2] - lon) * kmLon, (lat - b[1]) * KM_DEG, (b[3] - lat) * KM_DEG), x = F.clamp((dk - 0.3) / 0.9); return x * x * (3 - 2 * x); };
  const vert = (A, e, n) => { const lon = EV_SUM[0] + e / kmLon, lat = EV_SUM[1] + n / KM_DEG, w = fineW(lon, lat), uf = uvOf(LF, lon, lat), uw = uvOf(LW, lon, lat);
    const h = (w > 0 ? w * sampleH(LF.hm, ...uf) : 0) + (1 - w) * sampleH(LW.hm, ...uw);
    A.P.push(e, h * hS * 0.001, -n); A.UV.push(...uf); A.UW.push(...uw); A.WF.push(w); A.TW.push(0); };
  const geo = (A, I, normals) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(A.P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(A.UV, 2));
    g.setAttribute('uvW', new THREE.Float32BufferAttribute(A.UW, 2)); g.setAttribute('wf', new THREE.Float32BufferAttribute(A.WF, 1)); g.setAttribute('tw', new THREE.Float32BufferAttribute(A.TW, 1)); g.setIndex(I);
    if (normals) g.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3)); else g.computeVertexNormals(); g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5); return g; };
  const nA = () => ({ P: [], UV: [], UW: [], WF: [], TW: [] });
  // the terrain patch (polar grid, denser toward the summit)
  const A = nA(), I = []; vert(A, 0, 0);
  for (let r = 1; r <= NR; r++) for (let a = 0; a < NA; a++) { const rk = RAD * Math.pow(r / NR, 1.25), an = a / NA * 2 * Math.PI; vert(A, rk * Math.sin(an), rk * Math.cos(an)); }
  const id = (r, a) => r === 0 ? 0 : 1 + (r - 1) * NA + ((a % NA) + NA) % NA;
  for (let a = 0; a < NA; a++) I.push(0, id(1, a + 1), id(1, a));
  for (let r = 1; r < NR; r++) for (let a = 0; a < NA; a++) { const p = id(r, a), q = id(r, a + 1), s2 = id(r + 1, a), w = id(r + 1, a + 1); I.push(p, q, s2, q, w, s2); }
  const g = geo(A, I, A.P.map((v, i) => i % 3 === 1 ? 1 : 0));
  // the apron: from each rim vertex out and down at ~33 deg to the datum, a little talus noise; the rim colour fades into the rock
  const B = nA(), IB = [], base = [];
  for (let a = 0; a <= NA; a++) { const k = id(NR, a % NA), x0 = A.P[k * 3], y0 = A.P[k * 3 + 1], z0 = A.P[k * 3 + 2], an = a / NA * 2 * Math.PI, sx = Math.sin(an), sz = -Math.cos(an);
    const L = y0 / SLOPE * (1 + 0.10 * Math.sin(an * 7 + 1.3) + 0.06 * Math.sin(an * 17 + 0.4));
    for (let j = 0; j <= NJ; j++) { const f = j / NJ, rr = RAD + L * f + 0.35 * Math.sin(an * 41 + j) * f * (1 - f) * 4, y = y0 * (1 - f);
      const ex = j ? sx * rr : x0, ez = j ? sz * rr : z0, uw = uvOf(LW, EV_SUM[0] + ex / kmLon, EV_SUM[1] - ez / KM_DEG);
      B.P.push(ex, y, ez); B.UV.push(A.UV[k * 2], A.UV[k * 2 + 1]); B.UW.push(...uw); B.WF.push(0); B.TW.push(0.85 - 0.4 * f); }
    base.push([sx * (RAD + L), sz * (RAD + L), sx, sz]);
    if (a < NA) for (let j = 0; j < NJ; j++) { const p = a * (NJ + 1) + j, q = p + NJ + 1; IB.push(p, q, p + 1, q, q + 1, p + 1); } }
  const gw = geo(B, IB);
  // the pedestal: straight down from the apron's foot, unit depth (scaled per frame by pedD)
  const C = nA(), IC = [], CN = [];
  base.forEach(([x, z, sx, sz], a) => { C.P.push(x, 0, z, x, -1, z); CN.push(sx, 0, sz, sx, 0, sz); C.UV.push(0, 0, 0, 0); C.UW.push(0, 0, 0, 0); C.WF.push(0, 0); C.TW.push(0, 0);
    if (a < base.length - 1) { const b2 = a * 2; IC.push(b2, b2 + 1, b2 + 2, b2 + 2, b2 + 1, b2 + 3); } });
  const gc = geo(C, IC, CN);
  const U = S.U, hu = S.heroMat.uniforms;
  const shared = { camPos: U.camPos, sunDir: U.sunDir, zenithCol: U.zenithCol, hazeCol: U.hazeCol, sunCol: U.sunCol, glowCol: U.glowCol, fogDens: U.fogDens, fogH: U.fogH, fogBg: U.fogBg, fogBase: U.fogBase,
    sunI: hu.sunI, skyI: hu.skyI };
  const kS = { value: 1 }, pedD = { value: 6 }, mk = (mode) => new THREE.ShaderMaterial({ vertexShader: EV_VS, fragmentShader: EV_FS, side: mode ? THREE.DoubleSide : THREE.FrontSide,
    uniforms: Object.assign({}, shared, { kS, pedD, mode: { value: mode }, gain: { value: 0.66 }, sat: { value: 1.0 }, lift: { value: 0.07 }, hScale: { value: hS },
      texF: { value: new THREE.Vector2(1 / LF.hm.W, 1 / LF.hm.H) }, texW: { value: new THREE.Vector2(1 / LW.hm.W, 1 / LW.hm.H) },
      kmF: { value: new THREE.Vector2((LF.bb[2] - LF.bb[0]) * kmLon / LF.hm.W, (LF.bb[3] - LF.bb[1]) * KM_DEG / LF.hm.H) },
      kmW: { value: new THREE.Vector2((LW.bb[2] - LW.bb[0]) * kmLon / LW.hm.W, (LW.bb[3] - LW.bb[1]) * KM_DEG / LW.hm.H) },
      colF: { value: LF.col }, colW: { value: LW.col }, aoF: { value: LF.ao }, aoW: { value: LW.ao }, hF: { value: LF.ht }, hW: { value: LW.ht } }) });
  const patch = new THREE.Mesh(g, mk(0)), apron = new THREE.Mesh(gw, mk(1)), ped = new THREE.Mesh(gc, mk(2));
  for (const m of [patch, apron, ped]) { m.frustumCulled = false; m.renderOrder = 1; }
  const group = new THREE.Group(); group.add(patch, apron, ped); group.visible = false; S.scene.add(group);
  (S._sections ||= new Map()).set('ch3-everest-prop', { group });        // every other terrainShot on this stage hides it each frame
  const footR = base.reduce((m, b) => Math.max(m, Math.hypot(b[0], b[1])), 0);
  S._ch3ev = { group, hS, summit: 8849, footR,
    // place: virtual datum spot (lon, lat), datum height base (m, true scale), eye {lon, lat, alt km}, k (forced-perspective scale),
    // pedD: pedestal depth below the datum (virtual km)
    place(o) { const E0 = S.xyz(o.eye.lon, o.eye.lat, 0); E0.y = o.eye.alt; const V = S.xyz(o.lon, o.lat, o.base);
      group.position.copy(E0.clone().add(V.sub(E0).multiplyScalar(o.k))); group.scale.setScalar(o.k); kS.value = o.k; pedD.value = Math.max(o.pedD ?? 0, 0.001);
      ped.visible = (o.pedD ?? 0) > 0.002; group.visible = !!o.visible; group.updateMatrixWorld(true); } };
  return S._ch3ev;
}

// ---------------------------------------------------------------------------------------------------------------- paper props
function candleCard(kit) {
  const S = 2, W = 180, H = 620, c = kit.P.cv(W * S, H * S), g = c.getContext('2d'); g.scale(S, S); g.lineJoin = 'round';
  // stick: cream wax with a soft side shade and a drip
  const lg = g.createLinearGradient(40, 0, 140, 0); lg.addColorStop(0, '#D9CFBC'); lg.addColorStop(0.35, '#F6F0E2'); lg.addColorStop(1, '#CFC4AE');
  g.fillStyle = lg; g.fillRect(44, 250, 92, H - 254);
  g.beginPath(); g.moveTo(44, 256); g.quadraticCurveTo(52, 300, 60, 262); g.quadraticCurveTo(70, 330, 82, 258); g.lineTo(136, 256); g.lineTo(136, 250); g.lineTo(44, 250); g.closePath(); g.fillStyle = '#FBF7EE'; g.fill();
  g.fillStyle = '#3A3028'; g.fillRect(87, 214, 6, 40);                                               // wick
  // flame: paper layers, orange outside, yellow inside, a pale core
  const fl = (sc, col) => { g.beginPath(); g.moveTo(90, 222 - 200 * sc); g.bezierCurveTo(90 + 70 * sc, 222 - 110 * sc, 90 + 60 * sc, 222 - 10 * sc, 90, 222);
    g.bezierCurveTo(90 - 60 * sc, 222 - 10 * sc, 90 - 70 * sc, 222 - 110 * sc, 90, 222 - 200 * sc); g.closePath(); g.fillStyle = col; g.fill(); };
  fl(1.0, '#FF7A2E'); fl(0.74, '#FFB23F'); fl(0.46, '#FFE38A'); fl(0.22, '#FFF8DC');
  return kit.prepPaper(c, { edge: 4 });
}
function paperCanvas(kit, w, h, seed = 3, border = true) {
  const c = kit.P.cv(w, h), g = c.getContext('2d'), R = F.rng(seed);
  g.fillStyle = '#F2ECDD'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${150 + R() * 60 | 0},${135 + R() * 50 | 0},${110 + R() * 40 | 0},${0.04 + R() * 0.05})`; g.fillRect(R() * w, R() * h, 2 + R() * 30, 1 + R() * 2); }
  const vg = g.createLinearGradient(0, 0, 0, h); vg.addColorStop(0, 'rgba(255,255,255,0.10)'); vg.addColorStop(1, 'rgba(90,70,40,0.10)'); g.fillStyle = vg; g.fillRect(0, 0, w, h);
  if (border) { g.strokeStyle = 'rgba(120,95,60,0.45)'; g.lineWidth = Math.max(3, w * 0.004); g.strokeRect(1.5, 1.5, w - 3, h - 3); }
  return kit.gradeCanvas(c);
}

// ---------------------------------------------------------------------------------------------------------------- build
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const ch = K.chapter(3), T = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f), s0 = (s) => K.s0(s), s1 = (s) => K.s1(s);
  const pr = (t, a, b, e = E.inOut) => e(F.clamp((t - a) / Math.max(1e-6, b - a)));
  const env = (t, a, b, fi = 0.3, fo = 0.3) => F.clamp(Math.min((t - a) / fi, (b - t) / fo));
  const dbg = !!api.Q.ch3dbg;
  const GEO = await fetch('/ep/ep02/img/ch3/ch3_geo.json').then(r => r.json());
  const ML_SUB = GEO.VOLC.mloa[0], OTHERS_SUB = ['mkea', 'hual', 'koha', 'kila'].flatMap(k => GEO.VOLC[k]);

  // ---------------------------------------------------------------- UI helpers (crisp, after the grade)
  const gh = (v, lon, lat) => Math.max(v.S.heightAt(lon, lat), v.level);
  const gp = (v, ll, off = 30) => v.project(ll[0], ll[1], gh(v, ll[0], ll[1]) + off);
  // screen runs of a lon/lat polyline draped on the ground (+off m) or at a flat height, split where hidden or off-screen
  const druns = (v, pts, off = 40, every = 3, flat = null) => {
    const out = []; let cur = [];
    for (let i = 0; i < pts.length; i++) { const [lo, la] = pts[i], hm = (flat ?? gh(v, lo, la)) + off, q = v.project(lo, la, hm);
      const ok = q && q[0] > -400 && q[0] < W + 400 && q[1] > -400 && q[1] < H + 400 && (i % every || v.visible(lo, la, hm));
      if (!ok) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); }
    if (cur.length > 1) out.push(cur); return out; };
  const runLen = (runs) => runs.reduce((a, r) => a + r.reduce((b, p, i) => i ? b + Math.hypot(p[0] - r[i - 1][0], p[1] - r[i - 1][1]) : 0, 0), 0);
  const pointAt = (runs, p) => { let tgt = runLen(runs) * p, last = null;
    for (const r of runs) for (let i = 1; i < r.length; i++) { const d = Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1]); last = r[i]; if (tgt <= d) { const k = d ? tgt / d : 0; return [F.lerp(r[i - 1][0], r[i][0], k), F.lerp(r[i - 1][1], r[i][1], k)]; } tgt -= d; }
    return last; };
  // a meaningful line that draws on with a moving head dot (PLAYBOOK_craft 8)
  const lineOn = (ctx, runs, p, o = {}) => { if (p <= 0 || !runs.length) return; ui.line(ctx, runs, Object.assign({}, o, { p }));
    if (p < 0.999) { const q = pointAt(runs, p); if (q) { const r = px((o.width || 10) * 1.15); ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
      ctx.fillStyle = 'rgba(6,9,15,0.6)'; ctx.beginPath(); ctx.arc(q[0], q[1], r + px(4), 0, 7); ctx.fill(); ctx.fillStyle = o.color || PAL.text; ctx.beginPath(); ctx.arc(q[0], q[1], r, 0, 7); ctx.fill(); ctx.restore(); } } };
  // big pin (meaning-carrying marks about 64 px across with the halo) with a pulse ring
  const bigPin = (ctx, x, y, a, t, col = PAL.text, r = 15) => { if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ui.pin(ctx, x, y, { r, t, color: col, p: 1 }); ctx.restore(); };
  // hero albedo brighter for fills on dark drained basalt (ch2's measured fix), set in mask() before the render, reset in world()
  const heroBright = (S) => { const u = S.maskU?.heroCol; if (!u) return; if (!S._heroDef) S._heroDef = u.value.clone(); u.value.setRGB(0.34, 0.068, 0.018); };
  const heroReset = (S) => { const u = S.maskU?.heroCol; if (u && S._heroDef) u.value.copy(S._heroDef); };
  // polygon rings -> Uint8 mask on a height grid (row 0 = south), canvas fill (even-odd)
  const raster = (g, rings) => { const c = kit.P.cv(g.nx, g.ny), x = c.getContext('2d', { willReadFrequently: true }); x.fillStyle = '#fff'; x.beginPath();
    for (const r of rings) r.forEach(([lo, la], i) => { const X = (lo - g.bb[0]) / (g.bb[2] - g.bb[0]) * (g.nx - 1), Y = (la - g.bb[1]) / (g.bb[3] - g.bb[1]) * (g.ny - 1); i ? x.lineTo(X, Y) : x.moveTo(X, Y); });
    x.closePath(); x.fill('evenodd'); const d = x.getImageData(0, 0, g.nx, g.ny).data, m = new Uint8Array(g.nx * g.ny);
    for (let k = 0; k < m.length; k++) m[k] = d[k * 4] > 127 ? 1 : 0; return m; };
  const dataTex = (g) => { const d = new Uint8Array(g.nx * g.ny * 4), t = new THREE.DataTexture(d, g.nx, g.ny, THREE.RGBAFormat); t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true; t.data8 = d; return t; };
  const dummy = kit.P.cv(4, 4).getContext('2d');
  const DEEPW = WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], 0.75)));

  // ================================================================ water level (film time)
  const tUp = T('up'), tG0 = lead('going') - 0.25;
  const dr1 = monotone([[ch.t0, -110], [ch.t0 + 0.9, -650], [T('isl'), -2650], [T('range'), -3320], [tUp - 0.05, -3500]]);
  const dr2 = monotone([[tG0, -3500], [T('going2') + 0.4, -4550], [T('trench') - 0.5, -5470]]);   // -5,470: the pools' edges sit on sloping floor (no speckle)
  const lvl = (t) => t < tUp ? dr1(t) : t < tG0 ? -3500 : dr2(t);
  const LV_HOLD = -3500;

  // ================================================================ ACT 1: the stand-up (bigisland -> main_chain -> bigisland)
  // the low camera (to the {isl} pullback): 15 km beyond the receding shore off Laupāhoehoe (bearing 30), 1.2 km above the water,
  // looking back up the Hāmākua flank (the shoreline distance for a level: the grid's own profile along that bearing)
  const LAUP = [-155.24, 19.99];
  const shore = monotone([[0, 0], [277, 5], [1231, 10], [2485, 15], [2976, 20], [3113, 25], [3921, 30]]);
  const lowCam = (t) => { const L = lvl(t), sd = shore(-L), eye = offLL(LAUP, sd + 17 + 0.6 * (t - ch.t0), 33), tgt = offLL(LAUP, sd - 24, 24);
    return { eye, alt: L / 1000 + 2.6 + 0.1 * (t - ch.t0), tgt, h: L + 300 - 120 * (t - ch.t0) }; };
  const tP0 = T('isl') - 0.25;
  const lc = lowCam(tP0);
  // {up}: a low long-lens camera 72 km NE of Mauna Kea, 0.65 km over the -3,500 m water, summits about 15 % from the top; it pushes in
  // through the pause, then rises into the {mtn} outline view
  const aimH = (alt, D, p) => (alt + D * Math.tan(p * D2R) + D * D / 12742) * 1000;
  const UPK = [orbit(tUp, offLL(MK, 72, 42), -2.85, MK, aimH(-2.85, 72, 1.15), 11.4), orbit(s0('s052') + 0.1, offLL(MK, 70.5, 41.5), -2.7, MK, aimH(-2.7, 70.5, 1.3), 10.3)];
  const A1 = [
    orbit(tP0, lc.eye, lc.alt, lc.tgt, lc.h, 32),
    { t: T('range') - 0.15, lon: -157.62, lat: 20.78, h: -3300, d: 500, tilt: 55, heading: 213, fov: 38 },       // all one ridge
    { t: T('range') + 1.25, lon: -157.52, lat: 20.74, h: -3300, d: 480, tilt: 55, heading: 215, fov: 38 },
    UPK[0],                                                                                                         // {up}: the massif stands
  ];
  const path1a = chainPath(A1);
  const A2 = [   // {up} the massif stands, push through the pause; s052 the camera rises over it (pins on the summits), {mtn} the outline
    UPK[0], UPK[1],
    { t: lead('mtn') - 0.15, lon: -155.48, lat: 19.60, h: -1500, d: 365, tilt: 52, heading: 252, fov: 34 },
    { t: T('shape') - 1.6, lon: -155.48, lat: 19.60, h: -1500, d: 352, tilt: 52.5, heading: 255, fov: 34 },
  ];
  const A3 = [   // {shape}: down to a low track along the Hāmākua base, raking sun; {slopes} the 0 m line in the upper third
    { t: T('shape') - 1.6, lon: -155.48, lat: 19.60, h: -1500, d: 352, tilt: 52.5, heading: 255, fov: 34 },
    { t: T('shape') + 0.25, lon: -155.24, lat: 19.87, h: -2600, d: 78, tilt: 68, heading: 222, fov: 36 },
    { t: T('upthere') + 1.3, lon: -155.06, lat: 19.65, h: -2600, d: 72, tilt: 68, heading: 248, fov: 36 },     // lateral, SE along the coast
  ];
  const A3b = [  // {going}/{going2}: the camera tilts down the flank to its base while the sea falls on
    { t: T('upthere') + 1.3, lon: -155.06, lat: 19.65, h: -2600, d: 72, tilt: 68, heading: 248, fov: 36 },
    { t: T('going') + 0.6, lon: -154.98, lat: 19.72, h: -3300, d: 60, tilt: 63, heading: 246, fov: 36 },
    { t: T('going2') + 0.9, lon: -154.90, lat: 19.82, h: -4400, d: 52, tilt: 57, heading: 240, fov: 38 },
  ];
  const tCutTr = s0('s057') - 0.05;
  const A4 = [   // s057 cut: from ENE of the island, 17 km up, looking WSW: the east flank in the upper middle, the strip of water left in the
                 // Hawaiian Deep curving along its foot in the lower third, horizon about 22 % from the top; {rem} push, {clue} pulse
    orbit(tCutTr, [-153.98, 20.05], 17, [-154.66, 19.75], -5300, 40),
    orbit(T('rem') - 0.1, [-154.03, 20.02], 16, [-154.66, 19.75], -5300, 40),
    orbit(T('clue') + 0.9, [-154.12, 19.97], 13.8, [-154.64, 19.77], -5300, 38),
  ];
  const tA2 = T('shape') - 1.6, tA3 = T('upthere') + 1.3, tEndA = s0('s059') - 0.16;
  const path1 = route([tP0, T('up'), path1a], [tUp, tA2, chainPath(A2)], [tA2, tA3, chainPath(A3)], [tA3, tCutTr, chainPath(A3b)], [tCutTr, tEndA, chainPath(A4)]);
  // stage hand-offs on one camera where d crosses 150 km (out and back)
  const dAt = (t) => path1(t).d;
  const cross = (a, b, up) => { for (let k = 0; k < 40; k++) { const m = (a + b) / 2; if ((dAt(m) > 150) === up) b = m; else a = m; } return (a + b) / 2; };
  const tH1 = cross(tP0, T('range'), true), tH2 = cross(T('range') + 1.25, tUp, false), XF = 0.45;
  if (dbg) api.log(`[ch3] act1 hand-offs ${tH1.toFixed(2)} ${tH2.toFixed(2)}`);
  // ch3 opens on ch2's last camera (CH3_IN in ch2.js, eye about 24.6 km up) under the card and descends to the low camera in 1.6 s
  const CH3_IN = terrainCamOf({ lon: -155.33, lat: 19.83, h: 0, d: 95, tilt: 75, heading: 210, fov: 40 }), tIn = ch.t0 + 1.6;
  const dPA = (t) => -6 * pr(t, T('shape') - 0.6, T('shape') + 0.8) * (1 - pr(t, T('going') - 0.2, T('going2') + 0.9));   // {slopes}: the 0 m line into the upper third
  const cam1 = (t) => { if (t < tP0) { const c = lowCam(t), L = { lon: c.eye[0], lat: c.eye[1], alt: c.alt, tLon: c.tgt[0], tLat: c.tgt[1], tH: c.h, fov: 30, near: 0.01, far: 2000 };
      if (t >= tIn) return L; const k = E.inOutSine(F.clamp((t - ch.t0) / (tIn - ch.t0))), A0 = CH3_IN;
      return { lon: F.lerp(A0.lon, L.lon, k), lat: F.lerp(A0.lat, L.lat, k), alt: Math.exp(F.lerp(Math.log(A0.alt), Math.log(L.alt), k)), tLon: F.lerp(A0.tLon, L.tLon, k), tLat: F.lerp(A0.tLat, L.tLat, k),
        tH: F.lerp(A0.tH, L.tH, k), fov: F.lerp(A0.fov, L.fov, k), near: 0.01, far: 2000 }; }
    const c = camOf(path1(t)), dp = dPA(t); if (dp) c.dPitch = dp; return c; };
  const sunAct1 = (t) => { const k = pr(t, T('shape') - 1.0, T('shape') + 1.5); return [F.lerp(108, 122, k), F.lerp(26, 15, k)]; };   // from the E: the NE flank side-lit
  // masks: the cap above today's shore (s055) on the hero grid
  const M = {};
  const capMask = (S) => { if (!M.cap) { const g = heightGrid(S, [-156.2, 18.85, -154.75, 20.35], 2), m = raster(g, [GEO.COAST.hawaii]);
      for (let k = 0; k < m.length; k++) if (g.h[k] <= 0) m[k] = 0; M.cap = { tex: kit.maskTexture(g, { r: m }), bb: g.bb }; } return M.cap; };
  const drainedState = (t, extra) => { const st = mixState('today', 'drained', F.clamp(-lvl(t) / 900)); st.sun = sunAct1(t); st.set.foamAmt = 0.5 * (1 - F.clamp(-lvl(t) / 400));
    st.set.tubAmt = 0.6; st.set.oldLine = F.clamp(-lvl(t) / 300); st.set.nearAmt = 0.3; st.level = lvl(t);
    const c = t < tP0 ? null : path1(t); const wc = c ? farWater(c.d) : null; if (wc) st.waterCols = wc; return Object.assign(st, extra || {}); };
  // the white line (s054): brighter and wider; cyan glow on the trench water (s057)
  const lineState = (t) => { const b = env(t, lead('slopes') - 0.1, T('going') + 0.6, 0.35, 0.6); return { lineW: 1.4 + 1.6 * b, lineCol: [F.lerp(1.15, 1.6, b), F.lerp(1.1, 1.62, b), F.lerp(1.0, 1.62, b)] }; };
  const trenchGlow = (t) => Math.max(env(t, lead('trench') - 0.05, tEndA + 1, 0.35, 0.5) * 0.85, 0.6 * Math.exp(-Math.pow((t - (T('clue') + 0.1)) / 0.22, 2)));
  const glowWater = (k) => WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, [[0.10, 0.75, 0.85], [0.06, 0.55, 0.70], [0.04, 0.42, 0.60]][j][q], k)));
  const act1State = (t) => { const st = drainedState(t); Object.assign(st.set, lineState(t)); st.post.exposure = (st.post.exposure ?? 1.3) * (1 + 0.3 * env(t, lead('going') - 0.3, tCutTr + 0.1, 0.8, 0.1)); const g = trenchGlow(t); if (g > 0.01) { st.waterCols = glowWater(g); st.set.edgeGlow = 0.6 + 1.2 * g; } return st; };
  const tLand0 = lead('mtn') - 1.9;     // pins: five summits in turn
  const PINS = [KOH, HUAL, MK, ML, KIL];
  // A1a: bigisland (low camera, then the pullback until the main_chain hand-off)
  scenes.push(kit.terrainShot({ id: 'ch3-stand-a', t0: ch.t0, t1: tH1 + XF, fadeIn: K.XF, region: 'bigisland',
    cam: (lt) => cam1(ch.t0 + lt), level: (lt) => lvl(ch.t0 + lt), state: (lt) => act1State(ch.t0 + lt) }));
  // A1b: main_chain over the whole chain: all one ridge; {range} the crest line
  const sB = kit.terrainShot({ id: 'ch3-chain-ridge', t0: tH1, t1: tH2 + XF, fadeIn: XF, region: 'main_chain',
    cam: (lt) => cam1(tH1 + lt), level: (lt) => lvl(tH1 + lt), state: (lt) => { const st = act1State(tH1 + lt); st.set.tubAmt = 0.12; st.set.reefAmt = 0.12; return st; },
    ui(ctx, lt, t, view) {
      const a = env(t, lead('range') - 0.05, tH2 + 0.1, 0.2, 0.4); if (a <= 0) return;
      const runs = druns(view, GEO.CREST, 150, 3);
      ui.line(ctx, runs, { color: PAL.hero, width: 16, alpha: 0.35 * a, p: pr(t, lead('range'), lead('range') + 1.0, E.inOutSine), under: 0 });
      lineOn(ctx, runs, pr(t, lead('range'), lead('range') + 1.0, E.inOutSine), { color: PAL.hero, width: 10, alpha: a });
    } });
  sB.uiFrom = tH1 + XF; scenes.push(sB);
  // A1c: bigisland again from the dive to the end of s058: stand-up, pins, outline, lateral move, white line, cap tint, the trench
  scenes.push(kit.terrainShot({ id: 'ch3-trench', t0: tCutTr, t1: tEndA + 0.02, region: 'bigisland',
    cam: (lt) => cam1(tCutTr + lt), level: (lt) => lvl(tCutTr + lt), state: (lt) => act1State(tCutTr + lt) }));
  scenes.push(kit.terrainShot({ id: 'ch3-stand-c', t0: tH2, t1: tCutTr + 0.02, fadeIn: XF, region: 'bigisland',
    cam: (lt) => cam1(tH2 + lt), level: (lt) => lvl(tH2 + lt), state: (lt) => act1State(tH2 + lt),
    mask: (lt, S) => { const t = tH2 + lt, a = env(t, lead('upthere') - 0.05, T('upthere') + 1.05, 0.25, 0.45); if (a <= 0) return null; const m = capMask(S); heroBright(S); return { tex: m.tex, bb: m.bb, hero: 0.24 * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) {
      // {mtn}: five white pins pulse on the summits in turn (no names, no count), then the massif's waterline outline in hero orange
      PINS.forEach((ll, i) => { const a0 = tLand0 + i * 0.32, a = env(t, a0, a0 + 1.0, 0.15, 0.35); if (a <= 0) return; const hm = gh(view, ll[0], ll[1]) + 60, q = view.project(ll[0], ll[1], hm); if (q && view.visible(ll[0], ll[1], hm)) bigPin(ctx, q[0], q[1], a, t - a0, PAL.text, 22); });
      const oa = env(t, lead('mtn') - 0.05, T('shape') - 1.0, 0.2, 0.5);
      if (oa > 0) { const runs = druns(view, GEO.MASSIF[0], 60, 2, LV_HOLD); ui.avoidRuns(runs, 6);
        ui.line(ctx, runs, { color: PAL.hero, width: 18, alpha: 0.3 * oa, p: pr(t, lead('mtn'), lead('mtn') + 0.9), under: 0 });
        lineOn(ctx, runs, pr(t, lead('mtn'), lead('mtn') + 0.9), { color: PAL.hero, width: 9, alpha: oa }); }
    } }));
  api.cue(T('isl') - 0.17, 'whoosh_soft', -16); api.cue(lead('range'), 'line_draw', -20); api.cue(tUp - 0.08, 'impact_deep', -9);
  // the SEA LEVEL gauge (marker only, no digits: the chapter's hero number is 33,000+ FT): in while the sea falls, out while it holds
  scenes.push({ id: 'ch3-gauge', t0: ch.t0 + 0.2, t1: T('trench') + 1.2, layer: 60, draw(ctx, lt, t) {
    const a = Math.max(env(t, ch.t0 + 0.3, tUp + 0.9, 0.45, 0.6), env(t, tG0 - 0.3, T('trench') + 0.9, 0.4, 0.6)); if (a <= 0) return;
    ui.gauge(ctx, { p: 1, alpha: a, level: Math.max(lvl(t), -6000), range: 6000, value: false });
  } });

  // ================================================================ ACT 2: Everest at the same scale (bigisland + the prop)
  // The eye is 126 km NE of Mauna Kea over the Hawaiian Deep (floor about -5,550 m), looking SW. The virtual Everest stands at Mauna
  // Kea's distance, 11.2 deg to the right (25 km aside, over the Waimea saddle), so both summits stand free. Four framings, each moving:
  //   F1 {ev}: eye 0.35 km above sea level (the white sea-level line lies on Mauna Kea's real shoreline), Everest rises onto its
  //      pedestal (the pedestal reaches the virtual sea floor), slow push;  F2 {easily}: push on both summits, a white tick runs from
  //      Mauna Kea's summit across to Everest (its peak towers over it);  F3 {seafloor}: Everest sinks 6,000 m onto the floor, the last
  //      water drains, and the camera cranes down to 4.3 km below sea level, the height at which the -6,000 m line at the summits'
  //      distance lies on the visible floor at Mauna Kea's foot: both feet stand on the yellow base line, the bar climbs;
  //   F4 {ev2}-{heard}: slow push on the tick and the bar. The prop is re-placed for every frame's eye, so the scale stays exact.
  const MKD = 126, EYE2 = (() => { const e = offLL(MK, MKD, 48); return { lon: e[0], lat: e[1] }; })();
  const bMK = brgOf([EYE2.lon, EYE2.lat], MK), EV_OFF = 11.2, K_EV = 0.18, EYE_LO = -4.3;
  const EVV = offLL([EYE2.lon, EYE2.lat], MKD, bMK + EV_OFF);
  const tAct2 = tEndA, tAct2e = T('heard') + 0.64 + 1.25;                       // the stamp lands at the end of "one." and holds 1.2 s
  const tRise0 = lead('ev') - 0.1, tRise1 = tRise0 + 2.55, tSink0 = lead('seafloor') - 0.05, tSink1 = tSink0 + 1.2;
  const tCr0 = tSink1 - 0.15, tCr1 = tCr0 + 2.0;                                // the crane down to the floor
  const tBar0 = tCr1 - 0.55, tBar1 = lead('tall33', 2), tEv2 = lead('ev2'), tStamp = K.Te('heard'), tEasy = lead('easily');
  const tPunch = T('tall33') + 0.34;                                            // the mix's hit_body (x074): the 6-frame lock-in punch
  const evBase = (t) => t < tSink0 ? F.lerp(-15000, 0, pr(t, tRise0, tRise1, E.outCubic || E.out)) : F.lerp(0, -6000, pr(t, tSink0, tSink1));
  const evPed = (t) => Math.max(0, evBase(t) + 6000) / 1000;                    // pedestal down to the virtual sea floor (-6,000 m), km
  const eyeAlt = (t) => F.lerp(0.35, EYE_LO, pr(t, tCr0, tCr1, E.inOutSine));
  const lvl2 = (t) => F.lerp(-5470, -9000, pr(t, tCr0 - 0.3, tCr0 + 1.0, E.inSine));   // the last water drains as the camera goes down
  // framing keys: b = bearing offset from Mauna Kea (deg, + right), p = pitch of the frame centre (deg), fov
  const FR = [[tAct2, 5.4, 0.9, 14.6], [tEasy - 0.35, 5.5, 1.0, 13.0], [tSink0 - 0.05, 5.8, 1.45, 10.9], [tSink1 + 0.1, 5.6, -0.2, 11.6],
    [tCr1, 5.5, 1.75, 12.4], [tEv2 - 0.3, 5.3, 1.7, 11.5], [tAct2e, 4.8, 1.75, 10.1]];
  const fb = monotone(FR.map(k => [k[0], k[1]])), fp = monotone(FR.map(k => [k[0], k[2]])), ff = monotone(FR.map(k => [k[0], k[3]]));
  const cam2 = (t) => { const alt = eyeAlt(t), tg = offLL([EYE2.lon, EYE2.lat], MKD, bMK + fb(t));
    return { lon: EYE2.lon, lat: EYE2.lat, alt, tLon: tg[0], tLat: tg[1], tH: (alt + MKD * Math.tan(fp(t) * D2R) + MKD * MKD / 12742) * 1000, fov: ff(t), near: 0.05, far: 2000 }; };
  let S2 = null, EVP = null;
  const shot2 = kit.terrainShot({ id: 'ch3-everest-cmp', t0: tAct2, t1: tAct2e, region: 'bigisland', level: (lt) => lvl2(tAct2 + lt),
    state: (lt) => { const t = tAct2 + lt, st = mixState('today', 'drained', 1); st.level = lvl2(t); st.sun = [128, 27]; st.set.oldLine = 1; st.set.lineW = 2.0; st.set.lineCol = [1.4, 1.42, 1.42];
      st.set.tubAmt = 0.4; st.waterCols = DEEPW; return st; },
    set: (lt, S) => { S2 = S; return {}; },
    cam: (lt) => { const t = tAct2 + lt, c = cam2(t); if (EVP) EVP.place({ eye: { lon: EYE2.lon, lat: EYE2.lat, alt: c.alt }, lon: EVV[0], lat: EVV[1], base: evBase(t), pedD: evPed(t), k: K_EV, visible: t > tRise0 - 0.05 }); return c; },
    ui(ctx, lt, t, view) {
      const P = (ll, hm) => view.project(ll[0], ll[1], hm);
      const evTop = (b) => P(EVV, b + 8849), mkTop = P(MK, 4207);
      // the white sea-level line across both (0 m at Mauna Kea and at Everest's virtual spot), out as Everest sinks
      const sl = env(t, tRise0 + 0.4, tSink0 + 0.5, 0.4, 0.4);
      const a0 = P(MK, 0), b0 = P(EVV, 0);
      if (sl > 0 && a0 && b0) { const dx = b0[0] - a0[0], dy = b0[1] - a0[1]; ui.line(ctx, [[[a0[0] - dx * 0.6, a0[1] - dy * 0.6], [b0[0] + dx * 0.9, b0[1] + dy * 0.9]]], { color: '#FFFFFF', width: 6, alpha: sl, p: pr(t, tRise0 + 0.4, tRise0 + 1.2) }); }
      // {easily}: a white tick at Mauna Kea's summit height runs across to Everest, whose peak stands far above it
      const ea2 = env(t, tEasy - 0.1, tSink0 + 0.1, 0.25, 0.35);
      if (ea2 > 0 && mkTop) { const eT0 = evTop(evBase(t)); if (eT0) ui.line(ctx, [[[mkTop[0] - px(36), mkTop[1]], [eT0[0] + px(60), mkTop[1]]]], { color: '#FFFFFF', width: 7, alpha: ea2, p: pr(t, tEasy - 0.1, tEasy + 0.4) }); }
      // the yellow base line at -6,000 m under both, in as the camera reaches the floor (it lies on the floor at Mauna Kea's foot)
      const bl = env(t, tCr0 + 1.1, tAct2e + 1, 0.5, 0.3), a6 = P(MK, -6000), b6 = P(EVV, -6000);
      if (bl > 0 && a6 && b6) { const dx = b6[0] - a6[0], dy = b6[1] - a6[1]; ui.line(ctx, [[[a6[0] - dx * 0.7, a6[1] - dy * 0.7], [b6[0] + dx * 0.8, b6[1] + dy * 0.8]]], { color: PAL.yellow, width: 9, alpha: bl, p: pr(t, tCr0 + 1.1, tCr0 + 1.8) }); }
      // the yellow height bar beside Mauna Kea's summit column: from the base line up the mountain while the counter rolls
      const bp = pr(t, tBar0, tBar1, E.inOutSine), off = px(80);
      if (bp > 0 && a6 && mkTop) { const top = [F.lerp(a6[0], mkTop[0], bp) + off, F.lerp(a6[1], mkTop[1], bp)], tk = px(30);
        ui.line(ctx, [[[a6[0] + off, a6[1]], top]], { color: PAL.yellow, width: 12 });
        ui.line(ctx, [[[top[0] - tk, top[1]], [top[0] + tk, top[1]]]], { color: PAL.yellow, width: 10 });
        ui.avoid(ui.boxOf([[a6[0] + off, a6[1]], [mkTop[0] + off, mkTop[1]]], px(40))); }
      // {ev2}: a white tick from Everest's summit (now 2,849 m above the base line) across to the bar
      const ta = env(t, tEv2 - 0.05, tAct2e + 1, 0.35, 0.3), eT = evTop(-6000);
      if (ta > 0 && eT && mkTop && a6) { const yB = F.lerp(a6[1], mkTop[1], 8849 / 10207); ui.line(ctx, [[[eT[0] - px(30), yB], [a6[0] + off + px(30), yB]]], { color: '#FFFFFF', width: 6, alpha: ta, p: pr(t, tEv2 - 0.05, tEv2 + 0.45) }); }
      // the number block: FROM THE SEA FLOOR (mandatory qualifier kicker, logged) + 33,000+ FT, rolling with the bar, 6-frame punch
      const kp = F.clamp((t - (tBar0 - 0.35)) / 0.4), kout = pr(t, tStamp - 0.75, tStamp - 0.4);
      const eNow = evTop(evBase(t)); if (eNow) ui.avoid(ui.boxOf([eNow, P(EVV, Math.max(evBase(t), -800))], px(36)));
      if (mkTop) ui.avoid({ x: mkTop[0] - px(60), y: mkTop[1] - px(40), w: px(120), h: px(80) });
      if (kp > 0 && kout < 1) {
        const nOpt = { cap: 150, to: 33000, unit: '+ FT', unitCap: 96 };
        const m = ui.number(dummy, 0, 0, 0, Object.assign({ measure: true }, nOpt));
        const punch = 1 + 0.07 * Math.sin(F.clamp((t - tPunch) / 0.2) * Math.PI);
        ctx.save();
        const box = ui.block(ctx, [{ text: 'FROM THE SEA FLOOR', role: 'kicker', cap: 52, qualifier: true }], px(96), px(96),
          { anchor: 'left', p: kp, out: kout, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow, clear: 24,
            at: [{ x: px(96), y: px(96), anchor: 'left' }, { x: W / 2, y: px(96), anchor: 'center' }, { x: W - px(96), y: px(96), anchor: 'right' }] });
        if (box) { ctx.translate(box.x + box.w / 2, box.y + box.h / 2); ctx.scale(punch, punch); ctx.translate(-(box.x + box.w / 2), -(box.y + box.h / 2));
          ui.number(ctx, 33000 * bp, box.inner.x, box.inner.y + m.h, Object.assign({ alpha: F.clamp(kp * 2) * (1 - E.in(kout)) }, nOpt)); }
        ctx.restore();
      }
      // labels: EVEREST on its summit while it stands on the sea-level line; MAUNA KEA on the summit from {seafloor}
      const ea = env(t, tRise1 - 0.6, tSink0 + 0.25, 0.3, 0.3);
      if (ea > 0 && eNow) ui.label(ctx, 'EVEREST', eNow[0], eNow[1], { t, p: ea, dist: 60, accent: PAL.cyan, order: ['right', 'above-right', 'above', 'left'] });
      const ma = env(t, tSink0 + 0.5, tStamp - 0.15, 0.3, 0.3);
      if (ma > 0 && mkTop && ea <= 0) ui.label(ctx, 'MAUNA KEA', mkTop[0], mkTop[1], { t, p: ma, dist: 60, accent: PAL.hero, order: ['above', 'above-left', 'left', 'above-right'] });
      // JUICE CHECK: TRUE, the stamp, at the end of "one." (the stamp sound), held 1.2 s over the still-moving shot
      stamp(ctx, t - tStamp);
    } });
  scenes.push(ready(shot2, async () => { if (!EVP) { const S = await kit.hub.terrain('bigisland', 1, {}); EVP = await everestProp(S, kit); } }));
  api.cue(tRise0 + 0.1, 'rumble_rise', -14); api.cue(tSink0 - 0.2, 'whoosh_big', -20); api.cue(tBar0, 'tick_counter', -19); api.cue(lead('tall33'), 'impact_deep', -10); api.cue(tStamp, 'stamp', -12);
  // the JUICE CHECK stamp (S13): rotated rubber stamp, cyan for TRUE, slams in over 5 frames with a 2-frame settle; one text block
  function stamp(ctx, u) {
    if (u < -0.12 || u > 1.45) return;
    const a = F.clamp((u + 0.12) / 0.06) * (1 - F.clamp((u - 1.2) / 0.25)), s = u < 0 ? F.lerp(1.6, 1.0, E.in(F.clamp((u + 0.12) / 0.12))) : 1 + 0.05 * Math.exp(-u * 18) * Math.cos(u * 60);
    const rot = -7 * D2R, col = PAL.cyan;
    const k1 = 'JUICE CHECK', k2 = 'TRUE', c1 = 56, c2 = 150;
    const w1 = kit.T.width(ctx, k1, { cap: c1 }), w2 = kit.T.width(ctx, k2, { fam: kit.T.FAM.head, cap: c2 }), bw = Math.max(w1, w2) + px(90), bh = px(c1 + c2) + px(110);
    const cx = px(150) + bw / 2, cy = px(130) + bh / 2;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(s, s);
    ctx.fillStyle = 'rgba(6,9,15,0.80)'; F.round(ctx, -bw / 2, -bh / 2, bw, bh, px(14)); ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = px(10); F.round(ctx, -bw / 2 + px(10), -bh / 2 + px(10), bw - px(20), bh - px(20), px(10)); ctx.stroke();
    kit.T.txt(ctx, k1, -w1 / 2, -bh / 2 + px(34) + px(c1), { cap: c1, color: PAL.text, shadow: false });
    kit.T.txt(ctx, k2, -w2 / 2, bh / 2 - px(40), { fam: kit.T.FAM.head, cap: c2, color: col, shadow: false });
    ctx.restore();
    const box = { x: cx - bw / 2 * 1.05, y: cy - bh / 2 * 1.1, w: bw * 1.05, h: bh * 1.1 };
    if (a > 0.5) { ui.Q.blocks.push(box); ui.Q.words += 3; }
  }

  // ================================================================ ACT 3: the summit gag (everest, maunakea, everest)
  // whip out on the word "road" (the road shot holds about 2.4 s), whip back on the end of "one", the flag droops in the gap
  const wRoad = K.word('s065', 'road');
  const tG1 = tAct2e, tWo0 = wRoad.start - 0.1, tWo1 = tWo0 + 0.24, tWb0 = K.Te('road') - 0.05, tWb1 = tWb0 + 0.24, tEndG = s0('s066') + 0.35;
  const CLIMB = await kit.paper('climber').catch(e => { api.log('[ch3] climber cut-out missing: ' + e.message); return null; });
  const JEEP = await kit.paper('jeep').catch(e => { api.log('[ch3] jeep cut-out missing: ' + e.message); return null; });
  const tPop = tG1 + 0.15, tFlag = T('this') + 0.03, tDroop = K.Te('road') + 0.21;
  // the summit seen from 10 km WSW and above (nothing nearer than about 7 km in frame, so the 14 m terrain holds): the summit pyramid,
  // the Lhotse-Nuptse wall behind it
  const evCam = (t) => { const k = pr(t, tG1, tWo0 + 0.2, E.inOutSine), wh = (t < tWb0 ? 70 * E.in(F.clamp((t - tWo0) / (tWo1 - tWo0))) : 0) - (t > tWb1 ? 70 * (1 - E.out(F.clamp((t - tWb1) / 0.18))) : 0);
    return camOf({ lon: EV_SUM[0], lat: EV_SUM[1], h: 9150 + 40 * k, d: F.lerp(10.6, 9.7, k), tilt: F.lerp(75.5, 76.5, k), heading: 64 + 5 * k + wh, fov: 30 }); };
  // paper flag (local): an upright pole and a hero-orange pennant that flies downwind, then hangs limp from the pole top (no half-mast)
  const flag = (ctx, x, y, hp, a, flyA, t) => { const top = y - hp, L = hp * 0.42, Hh = hp * 0.26;
    ctx.save(); ctx.globalAlpha *= a; ctx.lineCap = 'round';
    ctx.strokeStyle = 'rgba(20,18,16,0.35)'; ctx.lineWidth = px(13); ctx.beginPath(); ctx.moveTo(x + px(3), y); ctx.lineTo(x + px(3), top); ctx.stroke();
    ctx.strokeStyle = '#F2ECDD'; ctx.lineWidth = px(11); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, top); ctx.stroke();
    ctx.strokeStyle = '#6E6A64'; ctx.lineWidth = px(6); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, top); ctx.stroke();
    ctx.translate(x, top + px(4)); ctx.rotate(flyA);
    const wv = (u) => Math.sin(u * 5.5 - t * 14) * Hh * 0.10 * u * (1 - Math.abs(flyA) / 1.6);
    ctx.beginPath(); ctx.moveTo(0, 0); for (let i = 1; i <= 12; i++) { const u = i / 12; ctx.lineTo(u * L, Hh * 0.5 * u + wv(u)); }
    for (let i = 12; i >= 0; i--) { const u = i / 12; ctx.lineTo(u * L, Hh * (1 - 0.5 * u) + wv(u)); } ctx.closePath();
    ctx.fillStyle = '#F2ECDD'; ctx.strokeStyle = '#F2ECDD'; ctx.lineWidth = px(7); ctx.lineJoin = 'round'; ctx.stroke(); ctx.fillStyle = PAL.hero; ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.13)'; ctx.fillRect(0, Hh * 0.55, L * 0.5, Hh * 0.2); ctx.restore(); };
  const evShot = (id, t0, t1, fadeIn) => kit.terrainShot({ id, t0, t1, fadeIn, region: 'everest', preset: 'everest',
    cam: (lt) => evCam(t0 + lt),
    world(ctx, lt, t, view) {
      if (!CLIMB) return;
      const p = F.clamp((t - tPop) / 0.45), gust = Math.sin(t * 2.3) * 0.5 + Math.sin(t * 5.1) * 0.25;
      const base = { lon: EV_SUM[0], lat: EV_SUM[1], hPx: H * 0.38, pop: p, lean: -0.3 - 0.05 * gust, wobble: 0.05 + 0.03 * Math.abs(gust), t, seed: 2,
        hop: 14 * Math.max(0, Math.sin(F.clamp((t - tPop - 0.6) / 1.3) * Math.PI * 3)) * (t < tFlag ? 1 : 0) };
      const r = kit.drawCutout(ctx, view, CLIMB, base);
      if (!r) return;
      // frost on the card edge: a few white paper flecks hugging the figure's outline
      ctx.save(); ctx.globalAlpha *= 0.75 * p; ctx.fillStyle = '#F7FAFC';
      for (let i = 0; i < 26; i++) { const side = i % 2 ? 1 : -1, v = hash(i, 3), xx = r.x + side * r.w * (0.30 + 0.12 * hash(i, 5)) - r.h * 0.3 * (1 - v) * 0.3, yy = r.top + r.h * v;
        ctx.beginPath(); ctx.ellipse(xx, yy, px(3 + 4 * hash(i, 7)), px(2 + 2 * hash(i, 9)), hash(i, 11) * 3, 0, 7); ctx.fill(); }
      ctx.restore();
      // the flag: planted on the paper tap ({this}), flies downwind, then hangs limp from the top of the upright pole
      const fp = F.clamp((t - (tFlag - 0.2)) / 0.2), droop = pr(t, tDroop, tDroop + 0.5, E.outBack);
      if (fp > 0) { const drop = (1 - E.in(fp)) * H * 0.35;
        flag(ctx, r.x + r.w * 0.58, r.y - drop, H * 0.25, F.clamp(fp * 3), F.lerp(-0.12 + 0.08 * Math.sin(t * 9), 1.42, droop), t); }
      // spindrift: torn paper snow streaming past with the wind (seeded, a pure function of time)
      ctx.save(); ctx.fillStyle = '#F4F7FA';
      for (let i = 0; i < 46; i++) { const sp = 0.55 + 0.6 * hash(i, 1), u = ((t * sp + hash(i, 2)) % 1), xx = W * (1.08 - 1.16 * u), yy = r.top + r.h * (0.05 + 0.9 * hash(i, 4)) + Math.sin(t * 3 + i) * px(14) + u * px(60);
        ctx.globalAlpha = 0.85 * Math.min(1, u * 6, (1 - u) * 6) * F.clamp((t - tG1) / 0.3); ctx.beginPath(); ctx.ellipse(xx, yy, px(5 + 9 * hash(i, 6)), px(2 + 2.5 * hash(i, 8)), -0.15, 0, 7); ctx.fill(); }
      ctx.restore();
    } });
  const ev1 = evShot('ch3-gag-everest', tG1, tWo1, 0);
  scenes.push(blurred(ev1, tWo0, tWo1 + 0.04));
  // Mauna Kea's upper slope from 5.4 km SE (inside the 10 m maunakea region): the summit access road (USGS National Map / TIGER, img/ch3)
  // leads from the paper jeep at about 3,650 m up to the summit cones at the upper right (the jeep stays well below Puʻuwēkiu)
  const ROAD = GEO.ROAD, RL = [0]; for (let i = 1; i < ROAD.length; i++) RL.push(RL[i - 1] + kmOf(ROAD[i - 1], ROAD[i]));
  const roadAt = (km) => { let i = 1; while (i < ROAD.length - 1 && RL[i] < km) i++; const f = F.clamp((km - RL[i - 1]) / Math.max(1e-6, RL[i] - RL[i - 1])); return [F.lerp(ROAD[i - 1][0], ROAD[i][0], f), F.lerp(ROAD[i - 1][1], ROAD[i][1], f)]; };
  const J0 = RL[262], J1 = J0 + 0.4, MKE = [-155.412, 19.776], MKA = 4.25, MKO = orbit(0, MKE, MKA, offLL(MKE, 6.5, 301), (MKA + 6.5 * Math.tan(-3.8 * D2R)) * 1000, 20);
  const mkCam = (t) => { const wi = -70 * (1 - E.out(F.clamp((t - tWo1) / 0.18))), wo = 70 * E.in(F.clamp((t - tWb0) / (tWb1 - tWb0))), k = pr(t, tWo1, tWb0, E.inOutSine);
    return camOf(Object.assign({}, MKO, { d: MKO.d - 0.45 * k, heading: MKO.heading + 2 * k + wi + wo })); };
  const mkShot = kit.terrainShot({ id: 'ch3-gag-road', t0: tWo1, t1: tWb1, region: 'maunakea', preset: 'today', sun: [205, 40], state: { post: { sat: 0.8 } },
    cam: (lt) => mkCam(tWo1 + lt),
    world(ctx, lt, t, view) {
      // the road ribbon (traced from the USGS transportation layer), draped on the terrain
      const runs = druns(view, ROAD, 2, 1);
      ctx.save(); ctx.lineCap = ctx.lineJoin = 'round';
      for (const [w, c] of [[px(9), 'rgba(40,34,30,0.55)'], [px(5), '#CDBFA6']]) { ctx.strokeStyle = c; ctx.lineWidth = w; for (const r of runs) { ctx.beginPath(); r.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); } }
      ctx.restore();
      if (!JEEP) return;
      const u = pr(t, tWo1 - 0.1, tWb1, (x) => x), ll = roadAt(F.lerp(J0, J1, u)), hm = view.S.heightAt(ll[0], ll[1]);
      // soft dust behind the rear wheels (seeded noise puffs, source-over, no hard edges)
      const q = view.project(ll[0], ll[1], hm); if (!q) return;
      const wPx = W * 0.15;
      ctx.save();
      for (let i = 0; i < 14; i++) { const k = ((t * 1.8 + i / 14) % 1), x = q[0] - wPx * (0.32 + 0.55 * k) + px(18) * Math.sin(i * 2.7), y = q[1] - px(10) - k * px(55) + px(8) * Math.sin(i * 1.9 + t * 3), rr = px(26 + 70 * k) * (0.7 + 0.5 * hash(i, 3));
        const g = ctx.createRadialGradient(x, y, 0, x, y, rr); g.addColorStop(0, `rgba(196,178,150,${0.30 * (1 - k)})`); g.addColorStop(1, 'rgba(196,178,150,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, rr, 0, 7); ctx.fill(); }
      ctx.restore();
      kit.drawCutout(ctx, view, JEEP, { lon: ll[0], lat: ll[1], hm, wPx, lean: 0.03, hop: 2 * Math.abs(Math.sin(t * 17)), t, wobble: 0.01, flip: false, shadowA: 0.35 });
    } });
  scenes.push(blurred(mkShot, tWo1, tWb1));
  const ev2 = evShot('ch3-gag-everest-b', tWb1, tEndG, 0);
  scenes.push(blurred(ev2, tWb1, tWb1 + 0.2));
  api.cue(tFlag, 'paper_tap', -20); api.cue(tWo0, 'whoosh_soft', -14); api.cue(tWb0, 'whoosh_soft', -20); api.cue(tDroop, 'flag_droop', -15);

  // ================================================================ ACT 4: Mauna Loa, the giant (bigisland, drained to -5,500 m)
  const tA4 = tEndG, tOrb0 = lead('giant') - 0.1, tOrb1 = tOrb0 + 2.0, tToday = s0('s069') - 0.05, tBack = s0('s070') + 0.1, tCut = s0('s071') - 0.05;
  const A5 = [
    { t: tA4, lon: -155.55, lat: 19.78, h: 0, d: 150, tilt: 66, heading: 132, fov: 36 },
    { t: tOrb0, lon: -155.55, lat: 19.77, h: 0, d: 146, tilt: 66, heading: 128, fov: 36 },
  ];
  const A6 = [
    { t: tOrb0, lon: -155.55, lat: 19.77, h: 0, d: 146, tilt: 66, heading: 128, fov: 36 },
    { t: tOrb1, lon: -155.66, lat: 19.40, h: -800, d: 158, tilt: 66, heading: 46, fov: 36 },
    { t: tToday, lon: -155.66, lat: 19.42, h: -800, d: 138, tilt: 65, heading: 42, fov: 36 },
  ];
  const path4 = route([tA4, tOrb0, chainPath(A5)], [tOrb0, tToday, chainPath(A6)]);
  // masks: Mauna Loa (r: its map area, then swelling over its drained flanks by distance from it), Mauna Kea dimmed (g)
  const mlMask = (S) => {
    if (!M.ml) { const g = heightGrid(S, [-156.6, 18.4, -154.5, 20.7], 4), sub = raster(g, [ML_SUB]), full = raster(g, GEO.MLFULL), mk = raster(g, GEO.MKFULL);
      // distance (km) from the map area over the full edifice: grassfire on the grid
      const D = new Float32Array(g.nx * g.ny).fill(1e9), cx = (g.bb[2] - g.bb[0]) / (g.nx - 1) * KM * Math.cos(19.5 * D2R), cy = (g.bb[3] - g.bb[1]) / (g.ny - 1) * KM, cd = Math.hypot(cx, cy);
      for (let k = 0; k < D.length; k++) if (sub[k]) D[k] = 0;
      for (let pass = 0; pass < 2; pass++) for (let jj = 0; jj < g.ny; jj++) for (let ii = 0; ii < g.nx; ii++) { const j = pass ? g.ny - 1 - jj : jj, i = pass ? g.nx - 1 - ii : ii, k = j * g.nx + i; if (!full[k] && !sub[k]) continue; let v = D[k];
        const s = pass ? 1 : -1, ni = i + s, nj = j + s;
        if (ni >= 0 && ni < g.nx) v = Math.min(v, D[k + s] + cx); if (nj >= 0 && nj < g.ny) { v = Math.min(v, D[k + s * g.nx] + cy); if (ni >= 0 && ni < g.nx) v = Math.min(v, D[k + s * g.nx + s] + cd); } D[k] = v; }
      let dmax = 0; for (let k = 0; k < D.length; k++) if ((full[k] || sub[k]) && D[k] < 1e8) dmax = Math.max(dmax, D[k]);
      const tex = dataTex(g); for (let k = 0; k < mk.length; k++) tex.data8[k * 4 + 1] = mk[k] && !sub[k] ? 255 : 0;
      M.ml = { g, D, sub, full, tex, dmax, R: -1 }; if (dbg) api.log(`[ch3] ML grid ${g.nx}x${g.ny} dmax ${dmax.toFixed(0)} km`); }
    return M.ml; };
  const mlGrow = (t) => { if (t < lead('loa') - 0.05) return -1; const a = pr(t, lead('bigger') - 0.1, lead('bigger') + 1.4, E.inOutSine); return a; };
  const setML = (m, a) => { const R = a < 0 ? -1 : a * (m.dmax + 4); if (Math.abs(R - m.R) < 0.05) return; m.R = R; const d = m.tex.data8;
    for (let k = 0; k < m.D.length; k++) d[k * 4] = R < 0 ? 0 : m.sub[k] ? 255 : (m.full[k] && m.D[k] < 1e8 ? Math.round(255 * F.clamp((R - m.D[k]) / 3)) : 0);
    m.tex.needsUpdate = true; };
  const shot4 = kit.terrainShot({ id: 'ch3-maunaloa', t0: tA4, t1: tToday + 0.02, region: 'bigisland', level: -9000,
    cam: (lt) => { const t = tA4 + lt, c = camOf(path4(t)), up = 3 * pr(t, lead('active') - 0.8, lead('active') - 0.1); if (up) c.dPitch = up; return c; },
    state: () => { const st = mixState('today', 'drained', 1); st.level = -9000; st.sun = [205, 24]; st.set.tubAmt = 0.5; st.set.oldLine = 1; st.set.lineCol = [1.15, 1.1, 1.0]; st.waterCols = DEEPW; return st; },
    mask: (lt, S) => { const t = tA4 + lt, m = mlMask(S), ga = pr(t, tOrb0, tOrb0 + 0.7), fa = F.clamp((t - (lead('loa') - 0.05)) / 0.3);
      setML(m, mlGrow(t)); heroBright(S); return { tex: m.tex, bb: m.g.bb, hero: 0.58 * fa, dim: 0.97 * ga, pass: 0 }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) {
      // {giant}: a quick white outline on Mauna Kea's whole edifice as it dims (in 0.3 s, out over 0.8 s)
      const ka = env(t, tOrb0 - 0.05, tOrb0 + 1.5, 0.3, 0.8);
      if (ka > 0) ui.outline(ctx, druns(view, GEO.MKFULL[0], 80, 2, null), { width: 6, alpha: ka });
      const la = env(t, lead('loa') - 0.05, tToday + 1, 0.3, 0.3);
      if (la > 0) {
        const gw = mlGrow(t), sub = druns(view, ML_SUB, 80, 2), full = druns(view, GEO.MLFULL[0], 80, 2, null);
        if (gw < 0.5) lineOn(ctx, sub, pr(t, lead('loa') - 0.05, lead('loa') + 0.8), { color: PAL.text, width: 6, alpha: la * (1 - F.clamp(gw * 2)) });
        if (gw > 0) lineOn(ctx, full, gw, { color: PAL.text, width: 6, alpha: la * F.clamp(gw * 2) });
        ui.avoidRuns(gw > 0.5 ? full : sub, 6);
      }
      // {active}: LARGEST ACTIVE VOLCANO in the free third (the qualifier ACTIVE always stays)
      const hp = F.clamp((t - (lead('active') - 0.1)) / 0.5);
      const ms = gp(view, ML, 60);
      if (ms) ui.avoid({ x: ms[0] - px(40), y: ms[1] - px(40), w: px(80), h: px(80) });
      if (hp > 0) ui.block(ctx, [{ text: 'LARGEST ACTIVE VOLCANO', role: 'headline', cap: 100 }], px(96), px(96), { anchor: 'left', p: hp, bar: PAL.hero, clear: 20,
        at: [{ x: px(96), y: px(96), anchor: 'left' }, { x: W - px(96), y: px(96), anchor: 'right' }, { x: W / 2, y: px(96), anchor: 'center' }] });
      const lla = la * (1 - pr(t, lead('active') - 0.45, lead('active') - 0.1)); if (lla > 0 && ms) ui.label(ctx, 'MAUNA LOA', ms[0], ms[1], { t, p: lla, dist: 60, accent: PAL.hero, order: ['above', 'above-left', 'above-right', 'left', 'right'] });
    } });
  scenes.push(shot4);
  api.cue(lead('giant'), 'whoosh_soft', -18);
  // s069: today's island at sea level, Mauna Loa's map area (USGS geologic map) in hero orange, the other volcanoes dimmed
  const todayMask = (S) => { if (!M.today) { const g = heightGrid(S, [-156.15, 18.85, -154.75, 20.35], 2), r = raster(g, [ML_SUB]), o = raster(g, OTHERS_SUB); M.today = { tex: kit.maskTexture(g, { r, g: o }), bb: g.bb }; } return M.today; };
  const shot5 = kit.terrainShot({ id: 'ch3-today-half', t0: tToday, t1: tBack + 0.02, region: 'bigisland', preset: 'today', sun: [200, 36],
    state: (lt) => ({ waterCols: farWater(F.lerp(205, 188, pr(lt, 0, tBack - tToday, E.inOutSine))), set: { foamAmt: 0.6, foamPx: 0, foamM: 2 } }),
    cam: (lt) => camOf({ lon: -155.52, lat: 19.60, h: 0, d: F.lerp(205, 188, pr(lt, 0, tBack - tToday, E.inOutSine)), tilt: 38, heading: 348 + 4 * pr(lt, 0, 3), fov: 36 }),
    mask: (lt, S) => { const m = todayMask(S); const a = pr(tToday + lt, tToday + 0.15, tToday + 0.6); heroBright(S); return { tex: m.tex, bb: m.bb, hero: 0.6 * a, dim: 0.55 * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) { const runs = druns(view, ML_SUB, 60, 2), pu = Math.exp(-Math.pow((t - (T('half') + 0.1)) / 0.25, 2));
      lineOn(ctx, runs, pr(t, tToday + 0.15, tToday + 0.9), { color: PAL.text, width: 6 + 4 * pu }); } });
  scenes.push(shot5);
  // s070: back to the drained massif, lowering toward Mauna Loa's southern base into the shadow
  const shot6 = kit.terrainShot({ id: 'ch3-ml-base', t0: tBack, t1: tCut + 0.02, region: 'bigisland', level: -9000,
    state: () => { const st = mixState('today', 'drained', 1); st.level = -9000; st.sun = [262, 18]; st.set.tubAmt = 0.4; st.set.oldLine = 1; st.set.lineCol = [1.15, 1.1, 1.0]; st.set.nearAmt = 0.6; st.waterCols = DEEPW; return st; },
    cam: (lt) => { const t = tBack + lt, k = pr(t, tBack, lead('allofit') + 0.6, E.inOutSine);
      return camOf({ lon: F.lerp(-155.62, -155.70, k), lat: F.lerp(19.33, 19.02, k), h: F.lerp(0, -4000, k), d: F.lerp(72, 40, k), tilt: F.lerp(72, 70, k), heading: F.lerp(14, 20, k), fov: 40 }); } });
  scenes.push(shot6);

  // ================================================================ ACT 5: the hot spot, the candle, the sheet
  // section along the plate motion (az 306) through Kīlauea, SSW half removed (side -1: camera on the left of 306), 42 km deep, framed to about 36 km
  const HS = [-155.25, 19.30];                                              // the hot spot's map marker spot (SE Big Island)
  const PLANE = { lon: KIL[0], lat: KIL[1], az: 306, side: -1, u0: -260, u1: 300, du: 0.5, bottomKm: 42, loadU: 31, waterTopMax: 0 };
  const SEC = { sag: 1, sagM: 7966, alphaKm: 90, oldFloor: -5000, crustM: 6500, waterA: 0, floorLine: 0, trenchA: 0, edgeA: 1 };
  const tC0 = tCut, tCand = lead('candle'), tC1 = s0('s073') - 0.02, GLOW_E = -26000;
  // {moving}: the glow stays put on screen (the camera rides with it) while the section and the island slide NW past it, most of the
  // slide during the word (u km of the glow under the plate: it falls behind, ESE)
  const glowU = (t) => -22 * pr(t, lead('moving') - 0.05, lead('moving') + 1.25, E.outCubic || E.out);
  const CANDLE = candleCard(kit);
  const GL = kit.P.cv(W / 4 | 0, H / 4 | 0), gl = GL.getContext('2d');
  const cutShot = kit.cutawayShot({ id: 'ch3-hotspot', t0: tC0, t1: tC1 + 0.02, region: 'bigisland', level: -9000, preset: 'drained',
    state: () => { const st = mixState('today', 'drained', 1); st.level = -9000; st.sun = [215, 30]; st.set.oldLine = 0; st.set.tubAmt = 0.3; return st; },
    cut: { plane: PLANE, state: () => SEC,
      cam: (lt) => { const t = tC0 + lt, k = pr(t, tC0, tC1, E.inOutSine), g = glowU(t); return { u: F.lerp(14, 6, k) + g, d: F.lerp(62, 56, k), alt: F.lerp(12, 10, k), tu: F.lerp(10, 4, k) + g, te: -12500, tf: 0, fov: 44 }; } },
    world(ctx, lt, t, view) {
      const sec = view.sec; if (!sec) return;
      const P = (u, e, f = 0.3) => sec.project(u, e, f);
      const ga = F.clamp((t - (lead('stay') - 0.1)) / 0.6), toC = pr(t, tCand - 0.1, tCand + 0.45), u = glowU(t);
      // the hot spot: an irregular warm zone in the mantle (picture only), drawn soft on a quarter-size canvas and clipped to the face
      const c = P(u, GLOW_E, 0), r0 = P(u + 8, GLOW_E, 0);
      if (ga > 0 && c && r0) { const R = Math.abs(r0[0] - c[0]) / 4, cx = c[0] / 4, cy = c[1] / 4;
        gl.setTransform(1, 0, 0, 1, 0, 0); gl.clearRect(0, 0, GL.width, GL.height);
        for (const [sc, col, al] of [[1.6, '255,120,45', 0.3], [1.1, '255,150,60', 0.5], [0.65, '255,205,120', 0.72], [0.3, '255,240,190', 0.85]]) {
          gl.beginPath(); for (let i = 0; i <= 48; i++) { const an = i / 48 * Math.PI * 2, n = 1 + 0.2 * Math.sin(3 * an + t * 0.8 + sc) + 0.12 * Math.sin(5 * an - t * 1.3) + 0.07 * Math.sin(9 * an + t * 2.1);
            const x = cx + Math.cos(an) * R * sc * 1.55 * n, y = cy + Math.sin(an) * R * sc * 0.85 * n - (an > Math.PI ? 0 : 0); i ? gl.lineTo(x, y) : gl.moveTo(x, y); }
          const g2 = gl.createRadialGradient(cx, cy, 0, cx, cy, R * sc * 1.55); g2.addColorStop(0, `rgba(${col},${al})`); g2.addColorStop(0.65, `rgba(${col},${al * 0.55})`); g2.addColorStop(1, `rgba(${col},0)`);
          gl.fillStyle = g2; gl.fill(); }
        const face = []; for (let uu = PLANE.u0; uu <= PLANE.u1; uu += 5) { const q = P(uu, sec.surf(uu), 0); if (q) face.push(q); }
        for (let uu = PLANE.u1; uu >= PLANE.u0; uu -= 5) { const q = P(uu, -PLANE.bottomKm * 1000, 0); if (q) face.push(q); }
        if (face.length > 4) { ctx.save(); ctx.beginPath(); face.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.clip();
          ctx.globalAlpha *= ga * (1 - 0.85 * toC); ctx.imageSmoothingEnabled = true; ctx.drawImage(GL, 0, 0, W, H); ctx.restore(); } }
      // {candle}: the crust band turns into a paper strip, the glow into a paper candle standing in the same place
      if (toC > 0) {
        const strip = [], bot = []; for (let uu = -230; uu <= 280; uu += 5) { const a = P(uu, sec.crustTop(uu) + 400, 0.4), b = P(uu, sec.crustTop(uu) - SEC.crustM - 400, 0.4); if (a && b) { strip.push(a); bot.push(b); } }
        if (strip.length > 2) { ctx.save(); ctx.globalAlpha *= toC; ctx.beginPath(); strip.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); for (let i = bot.length - 1; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]); ctx.closePath();
          ctx.fillStyle = PAPER_PAT || '#F2ECDD'; ctx.fill(); ctx.strokeStyle = 'rgba(110,85,55,0.55)'; ctx.lineWidth = px(3); ctx.stroke(); ctx.restore(); }
        const cb = P(u, -PLANE.bottomKm * 1000 + 1500), ct = P(u, sec.crustTop(u) - SEC.crustM - 600);
        if (cb && ct) kit.drawCutout(ctx, view, CANDLE, { x: cb[0], y: cb[1], hPx: Math.max(10, cb[1] - ct[1]) * E.outBack(toC), alpha: F.clamp(toC * 2), shadow: false, contact: false, base: false, wobble: 0.015, t, seed: 3 });
      }
    } });
  const PAPER_C = paperCanvas(kit, 1024, 512, 7); const PAPER_PAT = dummy.createPattern(paperCanvas(kit, 512, 256, 9, false), 'repeat');
  const SCR = kit.P.cv(W, H), scr = SCR.getContext('2d');   // the sheet drawn opaque here, then composited once (no triangle seams)
  scenes.push(cutShot);
  api.cue(lead('stay'), 'tension_groan', -15); api.cue(tCand, 'candle_flame', -22);

  // ---- s073-s075 the chain at sea level (main_chain), seen from the SSW: the sheet slides NW, scorch marks, then the real islands
  const tS0 = s0('s073') - 0.02, tSpots = lead('spots'), tSlide1 = tSpots - 0.25, tE6 = T('sinks') - 0.02;
  const SLIDE = 306, ACROSS = 36, XS = 600;                                 // slide bearing (plate motion), across, slide length km
  const slideX = (t) => XS * pr(t, tS0 + 0.15, tSlide1, E.inOutSine);
  const TODAY_SET = { foamAmt: 0.6, foamPx: 0, foamM: 2 };                 // foam only on the real coast (2 m), not on submerged banks
  const ISL = ['niihau', 'kauai', 'oahu', 'molokai', 'maui', 'hawaii'].map(n => { const r = GEO.COAST[n], c = centroid(r);
    const a = kmOf(HS, c) * Math.cos((brgOf(HS, c) - SLIDE) * D2R); return { n, r, c, a }; });
  const tArrOut = T('deepbelow') + 1.0;
  const A7 = [
    { t: tS0, lon: -156.75, lat: 20.55, h: 0, d: 760, tilt: 52, heading: 30, fov: 38 },
    { t: tSpots + 0.6, lon: -156.95, lat: 20.70, h: 0, d: 720, tilt: 51, heading: 31, fov: 38 },
    { t: lead('plate') + 0.2, lon: -157.00, lat: 20.72, h: 0, d: 705, tilt: 51, heading: 31, fov: 38 },
    { t: tArrOut + 0.4, lon: -156.85, lat: 20.62, h: 0, d: 660, tilt: 50.5, heading: 30.5, fov: 38 },        // wide until the arrow is gone
    { t: tE6, lon: -155.75, lat: 19.75, h: 0, d: 300, tilt: 48, heading: 28, fov: 38 },
  ];
  const path7 = chainPath(A7);
  const sheetCorners = (x) => { const c0 = offLL(HS, -760 + x, SLIDE), c1 = offLL(HS, 820 + x, SLIDE);
    return [offLL(c0, 260, ACROSS), offLL(c1, 260, ACROSS), offLL(c1, -70, ACROSS), offLL(c0, -70, ACROSS)]; };  // far-left, far-right, near-right, near-left
  // the plate arrow: along the chain (Hawaiʻi -> Maui -> Molokaʻi -> Oʻahu), 45 km off its NE side so no island is covered
  const SMALL = { rings: [] }, PL = { lanai: [-156.92, 20.83], kahoolawe: [-156.60, 20.55] };
  const ARW = [[-155.20, 20.15], [-155.75, 20.62], [-156.40, 21.02], [-157.00, 21.38], [-157.62, 21.72]].map(p => offLL(p, 45, 36));
  const shot7 = kit.terrainShot({ id: 'ch3-chain-sheet', t0: tS0, t1: tE6 + 0.02, region: 'main_chain', preset: 'today', sun: [205, 40],
    cam: (lt) => camOf(path7(tS0 + lt)),
    state: (lt) => ({ set: Object.assign({}, TODAY_SET), waterCols: farWater(path7(tS0 + lt).d) || WATER_FILM }),
    world(ctx, lt, t, view) {
      const proj = (ring, hm = 0) => ring.map(p => view.project(p[0], p[1], hm));
      // the sheet (paper) lying on the sea over the chain, opaque until {spots}; the flame glows through it, scorch marks ride with it
      const so = pr(t, tSpots - 0.05, tSpots + 0.5);
      if (so < 1) {
        const x = slideX(t), q = sheetCorners(x).map(c => view.project(c[0], c[1], 300));
        ctx.save(); ctx.globalAlpha *= 1 - so;
        if (q.every(Boolean)) { scr.setTransform(1, 0, 0, 1, 0, 0); scr.clearRect(0, 0, W, H); kit.drawQuad(scr, PAPER_C, q, 10); ctx.drawImage(SCR, 0, 0); }
        const h = view.project(HS[0], HS[1], 300), hr = view.project(...offLL(HS, 60, 120), 300);
        if (h && hr) { const R = Math.hypot(hr[0] - h[0], hr[1] - h[1]) * (1 + 0.05 * Math.sin(t * 6)); ctx.save();
          for (const [rr, al, col] of [[1.8, 0.25, '255,140,50'], [1.0, 0.4, '255,185,80'], [0.45, 0.55, '255,235,170']]) { const g = ctx.createRadialGradient(h[0], h[1], 0, h[0], h[1], R * rr);
            g.addColorStop(0, `rgba(${col},${al})`); g.addColorStop(1, `rgba(${col},0)`); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(h[0], h[1], R * rr, 0, 7); ctx.fill(); } ctx.restore(); }
        // scorch marks: each island's own coastline, carried on the sheet (its final spot - XS along the slide); it burns in as it passes
        // the flame, so on {spots} the marks are exactly the coasts underneath
        for (const s2 of ISL) { const at = XS - s2.a, k = F.clamp((x - at + 25) / 60); if (k <= 0) continue;
          const pr2 = proj(s2.r.map(p => offLL(p, -(XS - x), SLIDE))); if (!pr2.every(Boolean)) continue;
          const cx = pr2.reduce((a2, p) => a2 + p[0], 0) / pr2.length, cy = pr2.reduce((a2, p) => a2 + p[1], 0) / pr2.length, sk = 0.35 + 0.65 * E.out(k);
          ctx.save(); ctx.beginPath(); pr2.forEach(([X, Y], i) => { const xx = cx + (X - cx) * sk, yy = cy + (Y - cy) * sk; i ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); }); ctx.closePath();
          ctx.fillStyle = `rgba(62,34,16,${0.85 * k})`; ctx.fill(); ctx.strokeStyle = `rgba(170,96,40,${0.7 * k})`; ctx.lineWidth = px(5); ctx.lineJoin = 'round'; ctx.stroke(); ctx.restore(); }
        ctx.restore();
      }
      // {plate}: the same paper sheet comes back at 35 % over the sea (the islands cut out, untinted) and keeps sliding NW with the arrow
      const pa = env(t, lead('plate') - 0.05, tE6 + 1, 0.4, 0.3);
      if (pa > 0) { const x = XS + 140 * pr(t, lead('plate') - 0.05, tE6, (v) => v), q = sheetCorners(x).map(c => view.project(c[0], c[1], 300));
        if (q.every(Boolean)) { scr.setTransform(1, 0, 0, 1, 0, 0); scr.clearRect(0, 0, W, H); kit.drawQuad(scr, PAPER_C, q, 10);
          scr.save(); scr.globalCompositeOperation = 'destination-out'; scr.fillStyle = '#000'; scr.strokeStyle = '#000'; scr.lineWidth = px(8); scr.lineJoin = 'round';
          for (const ring of [...Object.values(GEO.COAST), ...SMALL.rings]) { const pp = proj(ring); if (!pp.every(Boolean)) continue; scr.beginPath(); pp.forEach(([X, Y], i) => i ? scr.lineTo(X, Y) : scr.moveTo(X, Y)); scr.closePath(); scr.fill(); scr.stroke(); }
          scr.restore(); ctx.save(); ctx.globalAlpha *= 0.36 * pa; ctx.drawImage(SCR, 0, 0); ctx.restore(); } }
    },
    ui(ctx, lt, t, view) {
      // {plate}: a big yellow arrow NW along the chain (head kept in the safe area: the camera stays wide until it has faded)
      const arA = env(t, lead('plate') - 0.05, tArrOut, 0.3, 0.5);
      if (arA > 0) { const pts = ARW.map(p => view.project(p[0], p[1], 2000)).filter(Boolean);
        if (pts.length > 2) ui.arrow(ctx, pts, { width: 15, p: pr(t, lead('plate'), lead('plate') + 0.9), t, color: PAL.yellow, alpha: arA }); }
      // {deepbelow}: a small warm marker pulses at the hot spot under the Big Island (map marker)
      const ma = env(t, lead('deepbelow') - 0.05, tE6 + 1, 0.3, 0.3), hq = view.project(HS[0], HS[1], 200);
      if (ma > 0 && hq) { const k = ((t - lead('deepbelow')) * 1.1) % 1; ctx.save(); ctx.globalAlpha *= ma;
        ctx.strokeStyle = '#FF8A3D'; ctx.lineWidth = px(5); ctx.globalAlpha *= (1 - Math.max(0, k)); ctx.beginPath(); ctx.arc(hq[0], hq[1], px(18) * (1.2 + 2.6 * Math.max(0, k)), 0, 7); ctx.stroke(); ctx.restore();
        bigPin(ctx, hq[0], hq[1], ma, null, '#FF8A3D', 18); }
      // {built}: the Big Island's coast outline edges NW off the marker
      const ba = env(t, lead('built') - 0.6, tE6 + 1, 0.3, 0.2);
      if (ba > 0) { const sh = 70 * pr(t, lead('built') - 0.1, lead('built') + 2.0, E.inOutSine), ring = GEO.COAST.hawaii.map(p => offLL(p, sh, SLIDE - 6));
        const runs = druns(view, ring, 60, 1, 0); ui.outline(ctx, runs, { width: 6, alpha: ba }); }
    } });
  shot7.uiFrom = tS0; scenes.push(ready(shot7, async () => { if (!SMALL.done) { SMALL.done = 1; for (const n of ['lanai', 'kahoolawe']) { const c = PL[n];
    try { const r = await kit.island({ region: 'main_chain', bbox: [c[0] - 0.25, c[1] - 0.2, c[0] + 0.25, c[1] + 0.2], level: 0, seeds: [c], step: 1 }); SMALL.rings.push(...r.rings); } catch (e) { api.log('[ch3] ' + n + ' ring: ' + e.message); } } } }));
  // the islands appear under the marks: the sheet dissolves on {spots} while the chain underneath was there all along
  api.cue(tS0 + 0.2, 'paper_slide', -18); api.cue(lead('plate'), 'line_draw', -20);

  // ================================================================ ACT 7: the drowned reefs off Kohala (kohala)
  // the film's one drained look (preset 'drained': slate seabed, day light) raked from the SE so the risers fall into shadow; {reefs}
  // cream lines (10 px, under-stroke) from {steps}+0.3 s on every terrace edge the grid shows, kept into s078 where they drown (blue)
  // as the sea rises; s079 the sea drains away again and the camera, upslope, tilts down the staircase into the blue distance
  const tK0 = T('sinks') - 0.02, tLoop0 = s0('s078') - 0.05, tRise = tLoop0 + 1.25, tRiseE = lead('them') - 0.05, tK1 = s0('s080') - 0.25, tD0 = s0('s079') - 0.03;
  const kLevel = (t) => t < tLoop0 ? -9000 : t < tD0 ? F.lerp(-480, -190, pr(t, tRise, tRiseE, E.inOutSine)) : -9000;
  const A8 = [
    { t: tK0, lon: -156.05, lat: 20.0, h: -650, d: 14, tilt: 70, heading: 52, fov: 42 },
    { t: tLoop0 - 0.05, lon: -156.04, lat: 20.02, h: -560, d: 11, tilt: 71, heading: 56, fov: 42 },
  ];
  const A9 = [   // the reef loop: close on the -460 m step, rising with the water (the waterline stays put in frame), then a push
    { t: tLoop0, lon: -156.035, lat: 20.035, h: -470, d: 8.5, tilt: 73, heading: 58, fov: 42 },
    { t: tRise, lon: -156.035, lat: 20.035, h: -470, d: 8.4, tilt: 73, heading: 58.5, fov: 42 },
    { t: tRiseE, lon: -156.035, lat: 20.035, h: -180, d: 8.2, tilt: 73, heading: 59.5, fov: 42 },
    { t: tD0 + 0.03, lon: -156.03, lat: 20.035, h: -180, d: 7.1, tilt: 73, heading: 63, fov: 42 },
  ];
  // s079: 3 km over the -200 m shelf, looking W down the staircase (-460, -700, -960, -1,210 m steps, their lines kept and turning
  // blue with depth), tilting down and pushing along it into the blue distance
  const A10k = [orbit(tD0, [-155.955, 19.972], 3.1, [-156.10, 19.958], -2600, 44), orbit(tK1 + 0.3, [-155.985, 19.968], 2.5, [-156.09, 19.958], -4300, 44)];
  const path8 = route([tK0, tLoop0, chainPath(A8)], [tLoop0, tD0, chainPath(A9)], [tD0, tK1 + 0.3, chainPath(A10k)]);
  const pLen = (pc) => pc.reduce((a, p, i) => i ? a + kmOf(pc[i - 1], p) : 0, 0);
  const TERR = Object.entries(GEO.TERR).map(([L, pcs]) => ({ L: +L, pcs: pcs.filter(pc => pLen(pc) > 1.8) })).sort((a, b) => b.L - a.L);   // -170 first; pieces over 1.8 km
  const SHORE = {};
  const shores = async () => { if (!SHORE.a) { for (const [k, lv] of [['a', -480], ['b', -190]]) { try { SHORE[k] = await kit.island({ region: 'kohala', bbox: [-156.19, 19.86, -155.81, 20.29], level: lv, seeds: [[-155.85, 20.1]], step: 2 }); } catch (e) { api.log('[ch3] kohala shore ' + lv + ': ' + e.message); SHORE[k] = { rings: [] }; } } } };
  const tSt = lead('steps') + 0.3, KW = [[0.014, 0.19, 0.23], [0.012, 0.12, 0.16], [0.014, 0.075, 0.11]];   // the film's deep blue, no turquoise
  const kohalaShot = kit.terrainShot({ id: 'ch3-kohala', t0: tK0, t1: tK1 + 0.02, region: 'kohala', preset: 'drained',
    cam: (lt) => camOf(path8(tK0 + lt)), level: (lt) => kLevel(tK0 + lt),
    state: (lt) => { const t = tK0 + lt, k = pr(t, lead('steps') - 0.4, lead('steps') + 0.8), fz = pr(t, tD0, lead('deepreef') + 0.2, E.inOutSine);
      return { sun: t < tD0 ? [F.lerp(140, 128, k), F.lerp(24, 12, k)] : [150, 16], waterCols: KW, fog: [F.lerp(0.0028, 0.03, fz), F.lerp(0.00012, 0.006, fz), F.lerp(6, 1.6, fz)],
        set: { tubAmt: 0, oldLine: 0, nearAmt: 0.7, foamAmt: t > tLoop0 && t < tD0 ? 0.9 : 0, reefAmt: 0.6, skyI: 1.0, waveAmt: 0.35, glintAmt: 0.03 }, post: { exposure: F.lerp(1.75, 1.9, k) } }; },
    ui(ctx, lt, t, view) {
      const loop = t > tLoop0 && t < tD0, lv = view.level;
      // {reefs}: a cream line along each terrace edge (only where the grid shows a flat over a riser), staggered from the top step;
      // under water (s078) a line turns blue and dims: the reef drowned
      const ra = env(t, tSt - 0.05, tK1 + 1, 0.2, 0.3), deep = t > tD0;
      if (ra > 0) TERR.forEach((tr, i) => { if (loop && Math.abs(tr.L + 480) < 40) return; const p = pr(t, tSt + i * 0.16, tSt + i * 0.16 + 0.8), wet = loop ? F.clamp((lv - tr.L) / 60) : 0;
        const dz = deep ? F.clamp((-tr.L - 300) / 900) : 0, col = wet > 0.5 ? '#9FD9E6' : dz > 0 ? `rgb(${F.lerp(255, 150, dz) | 0},${F.lerp(233, 214, dz) | 0},${F.lerp(200, 236, dz) | 0})` : '#FFE9C8';
        for (const pc of tr.pcs) ui.line(ctx, druns(view, pc, 25, 1), { color: col, width: 10, alpha: ra * (1 - 0.55 * wet) * (1 - 0.35 * dz), p }); });
      if (!loop) return;
      // the reef loop: the reef line grows at the waterline on the -460 m step, drowns as the sea rises; {them} the next one
      const g1 = pr(t, tLoop0 + 0.3, tLoop0 + 1.1), drown = F.clamp((lv + 470) / 120);
      if (SHORE.a) ui.line(ctx, SHORE.a.rings.flatMap(r => druns(view, r, 10, 3, -480)), { color: drown > 0.5 ? '#9FD9E6' : '#FFC7A8', width: 10, alpha: 1 - 0.55 * drown, p: g1 });
      const g2 = pr(t, lead('them') - 0.1, lead('them') + 0.7);
      if (SHORE.b && g2 > 0) ui.line(ctx, SHORE.b.rings.flatMap(r => druns(view, r, 10, 3, -190)), { color: '#FFC7A8', width: 10, p: g2 });
    } });
  scenes.push(ready(kohalaShot, shores));
  api.cue(tK0, 'deep_sink', -16); api.cue(lead('reefs'), 'line_draw', -20);

  // ================================================================ ACT 8: born right here (main_chain, today's sea level)
  const tC8 = tK1, tPb0 = lead('bornhere') - 0.3, tPb1 = tPb0 + 3.6, tBaby0 = lead('baby') - 1.6, tCZ0 = lead('bigbaby') - 0.12, tCZ1 = tCZ0 + 0.27;
  const A10 = [
    { t: tC8, lon: -155.55, lat: 19.60, h: 0, d: 210, tilt: 50, heading: 18, fov: 38 },
    { t: tPb0, lon: -155.60, lat: 19.64, h: 0, d: 198, tilt: 50, heading: 20, fov: 38 },
    { t: tPb1, lon: -157.55, lat: 20.75, h: 0, d: 640, tilt: 42, heading: 26, fov: 38 },                      // pullback NW: the whole chain
    { t: tBaby0, lon: -157.50, lat: 20.72, h: 0, d: 615, tilt: 42, heading: 27, fov: 38 },
  ];
  const A11 = [
    { t: tBaby0, lon: -157.50, lat: 20.72, h: 0, d: 615, tilt: 42, heading: 27, fov: 38 },
    { t: tCZ0, lon: -155.55, lat: 19.62, h: 0, d: 250, tilt: 46, heading: 22, fov: 38 },                       // {baby}: the young end
  ];
  const A12 = [
    { t: tCZ0, lon: -155.55, lat: 19.62, h: 0, d: 250, tilt: 46, heading: 22, fov: 38 },
    { t: tCZ1, lon: -157.45, lat: 20.70, h: 0, d: 680, tilt: 24, heading: 28, fov: 38, ease: E.outExpo },      // crash zoom OUT
    { t: lead('become') - 0.6, lon: -157.30, lat: 20.62, h: 0, d: 585, tilt: 25, heading: 33, fov: 38 },          // slow push (about 4 %/s)
  ];
  const A13 = [
    { t: lead('become') - 0.6, lon: -157.30, lat: 20.62, h: 0, d: 585, tilt: 25, heading: 33, fov: 38 },
    { t: ch.t1x, lon: -155.55, lat: 19.62, h: 0, d: 240, tilt: 50, heading: 24, fov: 38 },                     // {become}: back on the Big Island
  ];
  const crash = (t) => { const p = F.clamp((t - tCZ0) / (tCZ1 - tCZ0)), q = 1 - Math.pow(1 - p, 3), a = A12[0], b = A12[1];
    return { lon: F.lerp(a.lon, b.lon, q), lat: F.lerp(a.lat, b.lat, q), h: 0, d: Math.exp(F.lerp(Math.log(a.d), Math.log(b.d), q)), tilt: F.lerp(a.tilt, b.tilt, q), heading: F.lerp(a.heading, b.heading, q), fov: 38 }; };
  const path10 = route([tC8, tBaby0, chainPath(A10)], [tBaby0, tCZ0, chainPath(A11)], [tCZ0, tCZ1, crash], [tCZ1, lead('become') - 0.6, chainPath(A12.slice(1))], [lead('become') - 0.6, ch.t1x, chainPath(A13)]);
  const RIMS = [['maui', lead('bornhere') + 0.5], ['oahu', lead('bornhere') + 1.25], ['kauai', lead('bornhere') + 2.0]];
  const biMask = (S) => { if (!M.bi) { const g = heightGrid(S, [-156.2, 18.8, -154.7, 20.4], 1), m = raster(g, [GEO.COAST.hawaii]); for (let k = 0; k < m.length; k++) if (g.h[k] <= 0) m[k] = 0; M.bi = { tex: kit.maskTexture(g, { r: m }), bb: g.bb }; } return M.bi; };
  const tBump = K.Te('bigbaby') + 0.05;                                       // the mix's impact_short (x096): a 6-frame settle
  const bump = (t) => { const u = F.clamp((t - tBump) / 0.2); return u > 0 && u < 1 ? 1 - 0.035 * Math.sin(Math.PI * u) * (1 - u) : 1; };
  const shot8 = kit.terrainShot({ id: 'ch3-born-here', t0: tC8, t1: ch.t1x, region: 'main_chain', preset: 'today', sun: [210, 38],
    cam: (lt) => { const c = path10(tC8 + lt); return camOf(Object.assign({}, c, { d: c.d * bump(tC8 + lt) })); },
    state: (lt) => { const st = { set: Object.assign({}, TODAY_SET) }; const wc = farWater(path10(tC8 + lt).d); if (wc) st.waterCols = wc; return st; },
    mask: (lt, S) => { const t = tC8 + lt, a = env(t, tCZ1 - 0.05, lead('become') + 0.4, 0.2, 0.5); if (a <= 0) return null; const m = biMask(S); heroBright(S); return { tex: m.tex, bb: m.bb, hero: 0.58 * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) {
      // {bornhere}: Maui, Oʻahu, Kauaʻi take a brief hero rim in turn; {last}: they fade youngest to oldest
      RIMS.forEach(([n, t0], i) => { const tOut = lead('last') + i * 0.35, a = env(t, t0, tOut + 0.4, 0.25, 0.4); if (a <= 0) return;
        const runs = druns(view, GEO.COAST[n], 300, 1, 0); ui.line(ctx, runs, { color: PAL.hero, width: 12, alpha: a, p: pr(t, t0, t0 + 0.5) }); });
      // {baby}: the Big Island alone takes the rim; after the crash zoom the other islands keep white outlines next to its fill
      const ba = env(t, lead('baby') - 0.05, lead('become') + 0.3, 0.25, 0.5);
      if (ba > 0) ui.line(ctx, druns(view, GEO.COAST.hawaii, 300, 1, 0), { color: PAL.hero, width: 12, alpha: ba, p: pr(t, lead('baby') - 0.05, lead('baby') + 0.6) });
      const oa = env(t, tCZ1, lead('become') + 0.2, 0.25, 0.5);
      if (oa > 0) for (const n of ['maui', 'molokai', 'oahu', 'kauai', 'niihau']) ui.outline(ctx, druns(view, GEO.COAST[n], 300, 1, 0), { width: 6, alpha: oa });
    } });
  scenes.push(blurred(shot8, tCZ0, tCZ1 + 0.04));
  api.cue(lead('bornhere'), 'whoosh_soft', -16); api.cue(tCZ0, 'whoosh_big', -13);
  if (dbg) api.log(`[ch3] t0 ${ch.t0.toFixed(2)} act2 ${tAct2.toFixed(2)}-${tAct2e.toFixed(2)} gag ${tG1.toFixed(2)}-${tEndG.toFixed(2)} cut ${tC0.toFixed(2)} sheet ${tS0.toFixed(2)} kohala ${tK0.toFixed(2)} born ${tC8.toFixed(2)} end ${ch.t1x.toFixed(2)}`);
}
