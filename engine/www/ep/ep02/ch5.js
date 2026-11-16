// Chapter 5 "Fought Over a Volcano" (s112-s149), window K.chapter(5) (435.89-598.99 s, last shot to t1x 599.29). Built 2026-11-15.
// Every beat is keyed to Rodney's markers (K.T / K.lead / K.word); the chapter card (435.89-437.51) is the orchestrator's.
// Base layer 0, in film order (one camera per run, hand-offs on the identical camera):
//   drag (midway terrain > STORY globe > midway terrain, 435.89-458.64): opens on ch4's last Midway oblique, MIDWAY + the SEA LEVEL gauge;
//       s113 pull-out to the globe: a white HNL-MIDWAY line (true great circle), the NEW YORK-MIAMI great circle (true length, yellow) lifts
//       off on {ny}, flies across and lands beside it on {miami}, short (no labels, no digits); s114 dive to the ground on Sand Island: a
//       colony of paper albatrosses, LAYSAN ALBATROSS; s115 the hero takes off and glides; s116 crash landing, forward roll, dust, feathers;
//       s117 head shake on {gooney}, pull-up while the sea starts to fall; a white cut line along the section plane.
//   cake (midway cut-away, 458.34-480.64): the drained atoll sliced N-S through Sand Island: dark basalt under a thick cream reef cap,
//       ABOUT 28 MILLION YEARS with a thin pointer; the sea returns; s119 the sinking loop in uneven steps (the reef grows back to the
//       surface after each drop); s120 the loop replays, CHARLES DARWIN; s121-s122 two paper derricks drill down to the basalt, one spark.
//   war (midway terrain, 480.64-558.35): dawn hard cut over the atoll, JUNE 1942, the reef ring outlined hero orange on {volc42}; pull out
//       to the regional map; paper props on Midway's pin for the water trick (drop, intercept streams, AF, telegram with '?', radio rings,
//       bait on a line, the sad tank, the coded report decoding, the tag falls, AF = MIDWAY); four paper carriers turn dark one by one; the
//       Yorktown photo (layer 1); Yorktown dark; wreck rings + YORKTOWN KAGA AKAGI; drain; yellow lines from the atoll; down to the floor:
//       a paper hull in a pool of blue light, MORE THAN / 3 MILES DOWN; hold; lift away.
//   kure (kure terrain, 557.9-571.25): KURE (HŌLANIKŪ), the cyan tint on {blue}; BLUE = SINKING (layer 60, cream paper slip).
//   kcut (kure cut-away, 570.9-575.4): the reef cap barely keeps pace with the sinking, its top flickers at the waterline on {sinking}.
//   chain (kure terrain > STORY globe > bigisland terrain, 575.05-599.29): the DARWIN POINT line (about 29 N); drain past it: drowned flat
//       tops; the Big Island's ghost beside them; up to the globe: the chain lit to the bend, on to Kamchatka; the trench; the last seamounts
//       slide in and vanish; the whip back to the Big Island (final key for ch6 below).
// Local helpers only (no shared change): orbit/chainPath/route/blurred/ready (ch4), spherical great-circle helpers, the paper derrick,
// carrier and hull cards, morse streams, the cake painter.
import { PAL, E, F, MOVE_WATER, LINE } from './shared.js';

const D2R = Math.PI / 180, KM = 111.32, RE = 6371;
const MIDW = [-177.37, 28.22], SAND = [-177.3775, 28.209], MDY = [-177.37, 28.21], HNL = [-157.858, 21.307], NYC = [-74.006, 40.713], MIA = [-80.19, 25.76];
// 1942: Yorktown, Akagi, Kaga wreck positions (found 1998 / 2019 / 2019); Soryu, Hiryu: approximate sinking positions (not found)
const YORK = [-176.5678, 30.5997], AKAGI = [-178.6667, 30.5], KAGA = [-179.2833, 30.3833], SORYU = [-178.625, 30.708], HIRYU = [-179.05, 30.95];
const KURE = [-178.32, 28.42], KAMCH = [-200.6, 56.2], BEND = [-187.7, 32.1];
// the chain (approximate summits, continuous longitudes west of 180): Big Island > bend, then the Emperor seamounts to Meiji
const CHAIN = [[-155.5, 19.6], [-156.3, 20.8], [-158, 21.45], [-159.5, 22.05], [-161.9, 23.06], [-164.7, 23.58], [-166.2, 23.77], [-168, 25], [-170.6, 25.4], [-171.7, 25.77],
  [-173.95, 26.06], [-175.8, 27.8], [-177.37, 28.22], [-178.3, 28.4], [-181.3, 30.27], [-184, 31], [-185.7, 31.8], [-187.7, 32.1]];
const EMPEROR = [[-187.7, 32.1], [-187.7, 32.7], [-188.4, 33.6], [-188.4, 35.2], [-189.5, 38], [-188.9, 38.8], [-189.4, 41.1], [-189.7, 44.6], [-192.3, 51], [-195.5, 53]];
const TRENCH = [[-212, 43], [-207, 46.5], [-203, 49.5], [-200, 51.8], [-197.5, 53.8], [-195.5, 55.4]];
const LAGOON = [[0.020, 0.42, 0.40], [0.005, 0.19, 0.22], [0.002, 0.085, 0.12]];
// the Midway cut: N-S (az 5.5) through Sand Island, the camera side (east) removed; drill holes at u 0 and u 7.6 km
const PLANE = { lon: -177.3775, lat: 28.209, az: 5.5, side: 1, u0: -100, u1: 110, du: 0.05, bottomKm: 20, loadU: 0, waterTopMax: 0 };   // the whole volcano (flanks to about -4,500 m at u -50 and +40)
const bt = (u) => F.lerp(-157, -384, F.clamp(u / 7.6));                 // basalt top (m): about 515 ft (u 0) and 1,260 ft (u 7.6)
// the Kure cut: W-E through the atoll, the south side removed
const KPLANE = { lon: KURE[0], lat: KURE[1], az: 90, side: 1, u0: -12, u1: 12, du: 0.025, bottomKm: 3.5, loadU: 0, waterTopMax: 0 };
const DPL = 28.7;                                                          // the Darwin Point line (about 29 N, between Kure and the drowned banks)

// ---------------------------------------------------------------------------------------------------------------- geo helpers (ch3/ch4)
const offLL = (ll, km, brg) => { const cl = Math.cos(ll[1] * D2R); return [ll[0] + km * Math.sin(brg * D2R) / (KM * cl), ll[1] + km * Math.cos(brg * D2R) / KM]; };
const brgOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return (Math.atan2((b[0] - a[0]) * cl, b[1] - a[1]) / D2R + 360) % 360; };
const kmOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return Math.hypot((b[0] - a[0]) * cl * KM, (b[1] - a[1]) * KM); };
function orbit(t, eye, alt, tgt, h, fov, ease) { const dh = kmOf(eye, tgt), dv = alt - h / 1000;
  return { t, lon: tgt[0], lat: tgt[1], h, d: Math.hypot(dh, dv), tilt: Math.atan2(dh, dv) / D2R, heading: brgOf(eye, tgt), fov, ease }; }
function monotone(keys) {
  const n = keys.length, x = keys.map(k => k[0]), y = keys.map(k => k[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
  m[0] = 0; m[n - 1] = 0;
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : 3 * (x[i + 1] - x[i - 1]) / ((2 * x[i + 1] - x[i] - x[i - 1]) / d[i - 1] + (x[i + 1] + x[i] - 2 * x[i - 1]) / d[i]);
  return (t) => { if (t <= x[0]) return y[0]; if (t >= x[n - 1]) return y[n - 1];
    let i = 0; while (t > x[i + 1]) i++; const h = x[i + 1] - x[i], s = (t - x[i]) / h, s2 = s * s, s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * y[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * y[i + 1] + (s3 - s2) * h * m[i + 1]; };
}
function chainPath(keys) {
  const hd = [keys[0].heading];
  for (let i = 1; i < keys.length; i++) hd.push(hd[i - 1] + ((((keys[i].heading - keys[i - 1].heading) % 360) + 540) % 360 - 180));
  const ch = (f) => monotone(keys.map((k, i) => [k.t, f(k, i)]));
  const C = { lon: ch(k => k.lon), lat: ch(k => k.lat), ld: ch(k => Math.log(k.d)), tilt: ch(k => k.tilt), hd: ch((k, i) => hd[i]), fov: ch(k => k.fov), h: ch(k => k.h || 0) };
  return (t) => ({ lon: C.lon(t), lat: C.lat(t), d: Math.exp(C.ld(t)), tilt: C.tilt(t), heading: C.hd(t), fov: C.fov(t), h: C.h(t) });
}
const route = (...segs) => (t) => { for (const [a, b, f] of segs) if (t <= b) return f(Math.max(t, a)); const L = segs[segs.length - 1]; return L[2](L[1]); };
const cross = (path, a, b, D) => { const up = path(b).d > path(a).d; let lo = a, hi = b; for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if ((path(m).d > D) === up) hi = m; else lo = m; } return (lo + hi) / 2; };
function blurred(shot, w0, w1, n = 6, shutter = 0.5) {
  const inner = shot.draw.bind(shot);
  shot.draw = async function (ctx, lt, t, api) {
    if (t < w0 || t > w1 || api.Q.noblur) return inner(ctx, lt, t, api);
    const A = ctx.globalAlpha, dt = shutter / api.FPS, m = api.Q.draft ? 3 : n;
    for (let k = 0; k < m; k++) { const o = (k / (m - 1) - 0.5) * dt; ctx.save(); ctx.globalAlpha = A / (k + 1); await inner(ctx, lt + o, t + o, api); ctx.restore(); }
  };
  return shot;
}
function ready(shot, fn) { const d = shot.draw.bind(shot); shot.draw = async function (ctx, lt, t, api) { await fn(); return d(ctx, lt, t, api); }; return shot; }
const hash = (a, b = 0) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };
const loadImg = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('cannot load ' + src)); i.src = src; });
// ---------------------------------------------------------------------------------------------------------------- great circles
const v3 = (ll) => { const la = ll[1] * D2R, lo = ll[0] * D2R; return [Math.cos(la) * Math.cos(lo), Math.cos(la) * Math.sin(lo), Math.sin(la)]; };
const unwrap = (lon, ref) => lon + 360 * Math.round((ref - lon) / 360);
const ll3 = (v, ref) => { const r = Math.hypot(v[0], v[1], v[2]), lon = Math.atan2(v[1], v[0]) / D2R; return [ref == null ? lon : unwrap(lon, ref), Math.asin(v[2] / r) / D2R]; };
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const gcKm = (a, b) => RE * Math.acos(F.clamp(dot3(v3(a), v3(b)), -1, 1));
const gcAt = (a, b, f) => { const A = v3(a), B = v3(b), w = Math.acos(F.clamp(dot3(A, B), -1, 1)); if (w < 1e-9) return a.slice();
  const sa = Math.sin((1 - f) * w) / Math.sin(w), sb = Math.sin(f * w) / Math.sin(w); return ll3([A[0] * sa + B[0] * sb, A[1] * sa + B[1] * sb, A[2] * sa + B[2] * sb], F.lerp(a[0], unwrap(b[0], a[0]), f)); };
const gcPts = (a, b, n) => { const o = []; for (let i = 0; i <= n; i++) o.push(gcAt(a, b, i / n)); return o; };
const gcBrg = (a, b) => { const p1 = a[1] * D2R, p2 = b[1] * D2R, dl = (b[0] - a[0]) * D2R;
  return (Math.atan2(Math.sin(dl) * Math.cos(p2), Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl)) / D2R + 360) % 360; };
const dest = (ll, km, brg) => { const d = km / RE, p1 = ll[1] * D2R, l1 = ll[0] * D2R, b = brg * D2R;
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2)); return [unwrap(l2 / D2R, ll[0]), p2 / D2R]; };
const shiftLL = (pts, from, to) => pts.map(([lo, la]) => [to[0] + (lo - from[0]) * Math.cos(from[1] * D2R) / Math.cos(to[1] * D2R), to[1] + (la - from[1])]);
const bez = (a, b, c, u) => [(1 - u) * (1 - u) * a[0] + 2 * (1 - u) * u * b[0] + u * u * c[0], (1 - u) * (1 - u) * a[1] + 2 * (1 - u) * u * b[1] + u * u * c[1]];

// ---------------------------------------------------------------------------------------------------------------- paper cards
// a paper drilling derrick: lattice tower, crown block, the kelly line, a drum on the rig floor (no text)
function derrickCard(kit) {
  const w = 240, h = 560, c = kit.P.cv(w, h), g = c.getContext('2d'); g.lineCap = 'round'; g.lineJoin = 'round';
  const col = '#B04A2C', dark = '#6E2C1C', L = (x0, y0, x1, y1, lw, cc) => { g.strokeStyle = cc; g.lineWidth = lw; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); };
  const top = 46, bot = 500, xl = (y) => F.lerp(88, 18, (y - top) / (bot - top)), xr = (y) => w - xl(y);
  L(w / 2, top, w / 2, bot, 5, '#2B2B2B');
  const n = 6; for (let k = 0; k < n; k++) { const y0 = F.lerp(top, bot, k / n), y1 = F.lerp(top, bot, (k + 1) / n);
    L(xl(y0), y0, xr(y1), y1, 6, dark); L(xr(y0), y0, xl(y1), y1, 6, dark); L(xl(y0), y0, xr(y0), y0, 8, col); }
  L(xl(top), top, xl(bot), bot, 16, col); L(xr(top), top, xr(bot), bot, 16, col); L(xl(bot), bot, xr(bot), bot, 10, col);
  g.fillStyle = dark; g.fillRect(xl(top) - 16, top - 30, xr(top) - xl(top) + 32, 30);
  g.fillStyle = '#D8D0C0'; g.beginPath(); g.arc(w / 2, top - 15, 10, 0, 7); g.fill();
  g.fillStyle = '#7C7468'; g.fillRect(2, bot, w - 4, 26); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(2, bot + 18, w - 4, 8);
  g.fillStyle = '#CFC7B8'; F.round(g, 22, bot - 52, 62, 46, 9); g.fill(); g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(22, bot - 30, 62, 6);
  return kit.prepPaper(c, { edge: 5 });
}
// a carrier from above (bow to the right): hull, flight deck with centre-line dashes, island; light grey or the dark grey of a lost ship
function carrierTopCard(kit, dark) {
  const w = 560, h = 120, c = kit.P.cv(w, h), g = c.getContext('2d');
  g.fillStyle = dark ? '#2C3136' : '#7F858C';
  g.beginPath(); g.moveTo(24, 34); g.lineTo(430, 26); g.quadraticCurveTo(535, 44, 548, 60); g.quadraticCurveTo(535, 76, 430, 94); g.lineTo(24, 86); g.closePath(); g.fill();
  g.fillStyle = dark ? '#3A4046' : '#C2BBAA';
  g.beginPath(); g.moveTo(8, 38); g.lineTo(470, 33); g.lineTo(500, 60); g.lineTo(470, 87); g.lineTo(8, 82); g.closePath(); g.fill();
  g.fillStyle = dark ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.8)'; for (let x = 34; x < 460; x += 44) g.fillRect(x, 58, 24, 5);
  g.fillStyle = dark ? '#24292E' : '#5E646B'; F.round(g, 270, 14, 70, 20, 5); g.fill();
  return kit.prepPaper(c, { edge: 4 });
}
// a carrier hull from the side, sitting upright on the floor (no markings)
function hullSideCard(kit) {
  const w = 1100, h = 300, c = kit.P.cv(w, h), g = c.getContext('2d');
  g.fillStyle = '#525C66'; g.beginPath(); g.moveTo(40, 150); g.lineTo(1060, 138); g.lineTo(1030, 230); g.quadraticCurveTo(990, 280, 900, 286); g.lineTo(140, 286);
  g.quadraticCurveTo(70, 270, 40, 150); g.closePath(); g.fill();
  g.fillStyle = '#6A7580'; g.fillRect(12, 124, 1076, 24);
  g.fillStyle = '#3E464E'; g.fillRect(80, 148, 950, 34);
  for (let x = 110; x < 1000; x += 70) { g.fillStyle = 'rgba(20,24,28,0.55)'; g.fillRect(x, 156, 34, 16); }
  g.fillStyle = '#5E6872'; g.fillRect(610, 62, 130, 62); g.fillRect(645, 30, 56, 34); g.fillRect(668, 6, 10, 26);
  const lg = g.createLinearGradient(0, 180, 0, 290); lg.addColorStop(0, 'rgba(110,80,55,0)'); lg.addColorStop(1, 'rgba(110,80,55,0.38)'); g.fillStyle = lg; g.fillRect(0, 180, w, 110);
  return kit.prepPaper(c, { edge: 5 });
}
// one intercepted group: five morse symbols (dots and dashes, no letters)
const morse = (ctx, x, y, s, seed, col, a) => { if (a <= 0.002) return; ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = 'rgba(5,9,15,0.55)';
  let cx = x; const sy = []; for (let k = 0; k < 5; k++) { const w = hash(seed, k) > 0.5 ? s * 2.6 : s; sy.push([cx, w]); cx += w + s * 0.8; }
  const tot = cx - x - s * 0.8; F.round(ctx, x - s * 0.6, y - s * 1.1, tot + s * 1.2, s * 2.2, s * 0.6); ctx.fill();
  ctx.fillStyle = col; for (const [sx, w] of sy) { F.round(ctx, sx, y - s / 2, w, s, s / 2); ctx.fill(); } ctx.restore(); return tot; };
const feather = (ctx, x, y, s, rot, a) => { if (a <= 0.002) return; ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot);
  ctx.fillStyle = '#FBF8F1'; ctx.beginPath(); ctx.ellipse(0, 0, s, s * 0.32, 0, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(120,110,95,0.6)'; ctx.lineWidth = Math.max(1, s * 0.08); ctx.beginPath(); ctx.moveTo(-s * 1.1, 0); ctx.lineTo(s * 0.9, 0); ctx.stroke(); ctx.restore(); };

// ---------------------------------------------------------------------------------------------------------------- build
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px, TY = kit.T;
  const ch = K.chapter(5), T = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f), s0 = (s) => K.s0(s);
  const pr = (t, a, b, e = E.inOut) => e(F.clamp((t - a) / Math.max(1e-6, b - a)));
  const env = (t, a, b, fi = 0.3, fo = 0.3) => F.clamp(Math.min((t - a) / fi, (b - t) / fo));
  const lin = (x) => x, dbg = !!api.Q.ch5dbg, dummy = kit.P.cv(4, 4).getContext('2d');
  const gh = (v, lon, lat) => Math.max(v.S.heightAt(lon, lat), v.level ?? 0);
  const gp = (v, ll, off = 30) => v.project(ll[0], ll[1], gh(v, ll[0], ll[1]) + off);
  const druns = (v, pts, off = 40, every = 3, flat = null) => {
    const out = []; let cur = [];
    for (let i = 0; i < pts.length; i++) { const [lo, la] = pts[i], hm = (flat ?? gh(v, lo, la)) + off, q = v.project(lo, la, hm);
      const ok = q && q[0] > -400 && q[0] < W + 400 && q[1] > -400 && q[1] < H + 400 && (i % every || v.visible(lo, la, hm));
      if (!ok) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); }
    if (cur.length > 1) out.push(cur); return out; };
  const camDist = (view, lon, lat, hm) => view.S.xyz(lon, lat, hm).distanceTo(view.S.cam.position);
  const ON = (q, m = 0) => q && q[0] > -m && q[0] < W + m && q[1] > -m && q[1] < H + m;
  const once = new Set(), logOnce = (k, s) => { if (!once.has(k)) { once.add(k); api.log(s); } };

  // ================================================================ sea level, sun, water, exposure (film time)
  const LEVEL = (t) => -1500 * (pr(t, 455.38, 457.6) - pr(t, 461.9, 462.5)) - 6000 * (pr(t, 540.91, 543.4) - pr(t, 556.6, 557.6))
    - 2000 * (pr(t, 579.57, 581.0) - pr(t, 584.35, 584.95));
  const SUNK = [[ch.t0, 200, 38], [454.5, 200, 38], [457.3, 125, 35], [480.62, 125, 35], [480.64, 92, 16], [486.3, 98, 22], [489.0, 150, 45], [544.8, 150, 45],
    [545.9, 190, 30], [556.5, 190, 30], [558.6, 200, 38], [575.0, 200, 38], [ch.t1x, 200, 30]];
  const sunAz = monotone(SUNK.map(k => [k[0], k[1]])), sunEl = monotone(SUNK.map(k => [k[0], k[2]]));
  const SUN = (t) => [sunAz(t), sunEl(t)];
  const EXPO = (t) => 1.2 + 0.12 * env(t, 480.6, 487.6, 0.02, 1.0) + 0.35 * env(t, 545.4, 556.5, 0.5, 0.6) + (api.Q.ex5 ? +api.Q.ex5 : 0);
  const kOf = (d) => E.inOut(F.clamp((Math.log(d) - Math.log(25)) / (Math.log(500) - Math.log(25))));
  const waterAt = (d) => { const k = kOf(d); return LAGOON.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], k))); };
  // the shot state: today's stage, the lagoon water blending to the globe's navy from far up, the drained look (nwhi_west film.drained:
  // tubAmt 0, reefAmt 0.55) while the sea is down
  const stOf = (d, t, o = {}) => {
    const lv = o.level ?? LEVEL(t), kd = F.clamp(-lv / 300), k = kOf(d);
    const set = { foamAmt: 0.3 * (1 - kd), foamPx: 0, foamM: 2 };
    if (kd > 0) Object.assign(set, { tubAmt: 0, oldLine: kd, lineCol: LINE.cream, sedCol: [0.045, 0.045, 0.048], reefAmt: F.lerp(0.85, 0.55, kd) });
    return { level: lv, sun: o.sun || SUN(t), waterCols: waterAt(d), set: Object.assign(set, o.set || {}), post: { exposure: EXPO(t), sat: F.lerp(1.2, 1.0, k) } };
  };

  // ================================================================ the SEA LEVEL gauge (marker only, no digits; ch3's)
  const GWIN = [[437.55, 439.5], [455.0, 462.9], [540.6, 550.8], [556.3, 558.0], [579.3, 585.3]];
  const gState = (t) => { for (const [a, b] of GWIN) if (t > a && t < b) return { p: F.clamp((t - a) / 0.5), out: F.clamp((t - (b - 0.45)) / 0.45) }; return null; };
  const GTW = TY.width(dummy, 'SEA LEVEL', { cap: 64 });
  const gBox = (t) => { const g = gState(t); if (!g) return null; const w = px(8 + 24 + 64 + 28 + 32) + GTW; return { x: px(96) - (1 - E.outExpoN(g.p)) * (w + px(120)), y: px(96), w, h: px(150) }; };
  const avoidGauge = (t) => { const b = gBox(t); if (b) ui.avoid(b); };
  scenes.push({ id: 'ch5-gauge', t0: ch.t0, t1: ch.t1x, layer: 60, draw(ctx, lt, t) {
    const g = gState(t); if (!g) return;
    const pulse = Math.max(0, 1 - Math.abs(t - T('threemi')) / 0.45);
    ui.gauge(ctx, { p: g.p, out: g.out, level: Math.max(LEVEL(t), -6000), range: 6000, value: false, pulse });
  } });
  // label helper: in on t0 (0.3 s), out by t1
  const lab = (ctx, s, q, t, t0, t1, o = {}) => { if (!q) return null; const a = F.clamp((t1 - t) / 0.35); if (t < t0 || a <= 0) return null;
    return ui.label(ctx, s, q[0], q[1], Object.assign({ t, p: F.clamp((t - t0) / 0.3), alpha: a, order: ['above', 'above-right', 'above-left', 'right', 'left'] }, o)); };
  // hero number block (ch4's ABOUT / 7 MILLION YEARS): kicker on top, odometer number with unit, a punch on the word
  const heroNum = (ctx, t, kick, v, unit, t0, t1, tp, at) => {
    const nOpt = { cap: 150, to: v, unit, unitCap: 84 }, m = ui.number(dummy, v, 0, 0, Object.assign({ measure: true }, nOpt));
    const kp = F.clamp((t - t0) / 0.45), kout = F.clamp((t - (t1 - 0.35)) / 0.35); if (kp <= 0 || kout >= 1) return null;
    const box = ui.block(ctx, [{ text: kick, role: 'kicker', cap: 52, qualifier: true }], at[0].x, at[0].y, { anchor: at[0].anchor, p: kp, out: kout, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow, clear: 24, at });
    if (!box) return null;
    const punch = 1 + 0.07 * Math.sin(F.clamp((t - (tp - 0.08)) / 0.2) * Math.PI), cx = box.inner.x + m.w / 2, cy = box.inner.y + m.h / 2;
    ctx.save(); ctx.translate(cx, cy); ctx.scale(punch, punch); ctx.translate(-cx, -cy);
    ui.number(ctx, v, box.inner.x, box.inner.y + m.h, Object.assign({ alpha: (1 - E.in(kout)) * E.outExpoN(F.clamp((kp - 0.2) / 0.6)) }, nOpt)); ctx.restore();
    return box;
  };

  // ================================================================ assets
  const ALB = await kit.paper('albatross'), FLY = await kit.paper('albatross_fly');
  const DROP = kit.paperProp('drop'), ENV = kit.paperProp('envelope'), TAG = kit.paperProp('tag'), TANK = kit.paperProp('tank');
  const RIG = derrickCard(kit), CAR_L = carrierTopCard(kit, false), CAR_D = carrierTopCard(kit, true), HULL = hullSideCard(kit);
  const PH = {};
  const coverCrop = (img, s, fx, fy) => { const w = Math.round(W * s), h = Math.round(H * s), c = kit.P.cv(w, h), g = c.getContext('2d'), k = Math.max(w / img.width, h / img.height);
    const dw = img.width * k, dh = img.height * k; g.drawImage(img, F.clamp(w / 2 - fx * dw, w - dw, 0), F.clamp(h / 2 - fy * dh, h - dh, 0), dw, dh); return kit.gradeCanvas(c) || c; };
  const kb = (ctx, cv, s, fx, fy) => { const dw = W * s, dh = H * s; ctx.drawImage(cv, fx * W * (1 - s), fy * H * (1 - s), dw, dh); };
  try { PH.york = coverCrop(await loadImg('/ep/ep02/img/ch5/yorktown_1942.jpg'), 1.04, 0.5, 0.72); } catch (e) { api.log('[ch5] Yorktown photo missing: ' + e.message); }

  // ================================================================ DRAG: Midway > globe (Honolulu-Midway vs New York-Miami) > Sand Island
  // ch4's last flight, its keys verbatim (the dissolve 435.89-436.19 runs on the identical camera)
  const ch4 = K.chapter(4), tEnd0 = s0('s110') - 0.1, tEnd1 = tEnd0 + 1.9, GMID = offLL([-167.9996, 24.9988], 0.05, 235);
  const EN = [{ t: tEnd0, lon: GMID[0], lat: GMID[1], h: 22, d: 0.48, tilt: 85.5, heading: 10, fov: 38 },
    { t: tEnd1, lon: -171.6, lat: 26.0, h: 0, d: 600, tilt: 42, heading: 300, fov: 40 },
    { t: T('onlyreef'), lon: MIDW[0], lat: MIDW[1], h: 0, d: 18, tilt: 59, heading: 28, fov: 42 },
    { t: ch4.t1x + 0.6, lon: MIDW[0], lat: MIDW[1] + 0.002, h: 0, d: 15.2, tilt: 60.5, heading: 31, fov: 42 }];
  // the section camera (section coordinates of PLANE: u km along, f km to the east, alt km, target u, target elevation m); Q.cc overrides
  const secCam = (t, c) => orbit(t, offLL(offLL(SAND, c[0], 5.5), c[1], 95.5), c[2], offLL(SAND, c[3], 5.5), c[4], c[5] ?? 40);
  // keys (film s): 0 457.3 the pull-up over the drained atoll, the cut line; 1 458.64 the cut opens, coming down; 2 460.2 / 3 461.7 the whole
  // volcano in section (its flanks fall away left and right, the cream cap a thin line on top); 4 462.7 / 5 466.5 / 6 469.5 close and
  // straight on over the north half (frame about 6 km: the cap 300-380 m reads; aimed low, the horizon near the top: basalt fills
  // the frame, little sky); 7 472.8 / 8 478.0 both drill sites; 9 478.9 / 10 480.64
  // the push to the north bit
  const CC = Object.assign({ 0: [-2, 16, 4.0, 4, -600, 40], 1: [-4, 17.5, 2.2, 4, -1500, 40], 2: [-6, 18, 0.8, 4, -2600, 40], 3: [-5.6, 17.6, 0.75, 4.1, -2500, 40],
    4: [6.0, 4.4, 0.35, 7.0, -700, 40], 5: [6.3, 4.2, 0.33, 7.1, -700, 40], 6: [6.1, 4.3, 0.34, 7.0, -700, 40], 7: [3.0, 8.4, 0.6, 3.8, -1400, 40],
    8: [3.3, 7.8, 0.7, 3.9, -1400, 40], 9: [6.0, 5.0, 0.4, 7.2, -750, 40], 10: [6.4, 4.4, 0.32, 7.3, -700, 40] }, typeof api.Q.cc === 'object' ? api.Q.cc : {});
  const C0 = secCam(457.3, CC[0]), C0b = secCam(458.64, CC[1]);
  const HD = 335, KD2 = { t: 445.95, lon: -177.379, lat: 28.2085, h: 3, d: 0.115, tilt: 82, heading: HD, fov: 42 };
  const K1 = [EN[3],
    { t: 438.95, lon: MIDW[0], lat: 28.232, h: 0, d: 13.8, tilt: 58, heading: 34, fov: 42 },          // {midway}: a slow push on the ring
    { t: 439.45, lon: -177.15, lat: 28.12, h: 0, d: 95, tilt: 34, heading: 22, fov: 41 },           // s113: pull out, Midway stays in frame
    { t: 439.85, lon: -175.6, lat: 27.8, h: 0, d: 900, tilt: 12, heading: 12, fov: 40 },
    { t: 440.35, lon: -140, lat: 30, h: 0, d: 11000, tilt: 0, heading: 0, fov: 40 },
    { t: 441.2, lon: -122, lat: 32, h: 0, d: 12000, tilt: 0, heading: 0, fov: 40 },                  // {ny}: New York in view
    { t: 442.1, lon: -165.5, lat: 25.6, h: 0, d: 5200, tilt: 0, heading: 0, fov: 40 },               // {miami}: the two lines side by side
    { t: 443.1, lon: -167.5, lat: 25.5, h: 0, d: 4700, tilt: 0, heading: 0, fov: 40 },
    { t: 444.4, lon: -176.5, lat: 28.1, h: 0, d: 1400, tilt: 8, heading: 345, fov: 40 },             // s114: the dive
    KD2,                                                                                              // {earth}: on the ground at the colony
    { t: 454.3, lon: -177.379, lat: 28.2085, h: 3, d: 0.11, tilt: 82, heading: HD + 2.5, fov: 42 },
    { t: 454.45, lon: -177.379, lat: 28.2085, h: 3, d: 0.11, tilt: 82, heading: HD + 2.5, fov: 42 },
    { t: 456.0, lon: -177.37, lat: 28.20, h: 0, d: 2.5, tilt: 70, heading: 315, fov: 40 },          // s117: the pull-up, the sea falls
    C0, C0b];
  const PD = route([ch.t0, EN[3].t, chainPath(EN)], [EN[3].t, 458.64, chainPath(K1)]);
  // the pull-out climbs fast (95 to 900 km in 0.4 s) and the stack's data rectangle shows from about 500 km (mot 440.0 at d 700):
  // the globe takes over at 220 km in 0.25 s
  const tU1 = cross(PD, 438.95, 439.85, 220), tD1 = cross(PD, 444.4, 445.95, 700), XF = 0.4, XU = 0.25;
  const terrLeg = (id, region, a, b, path, o = {}) => {
    const s = kit.terrainShot(Object.assign({ id, t0: a, t1: b, fadeIn: o.fadeIn, region, preset: o.preset || 'today',
      cam: (lt) => kit.terrainCamOf(path(a + lt)), state: (lt) => stOf(path(a + lt).d, a + lt, o.st ? o.st(a + lt) : {}) }, o.spec || {}));
    if (o.fadeIn && o.fadeIn !== K.XF) s.uiFrom = a + o.fadeIn;
    scenes.push(o.wrap ? o.wrap(s) : s); return s; };
  const globeLeg = (id, a, b, path, o = {}) => {
    const s = kit.cineGlobeShot(Object.assign({ id, t0: a, t1: b, fadeIn: o.fadeIn, preset: 'STORY',
      keys: (lt) => { const c = path(a + lt); return { lat: c.lat, lon: c.lon, alt: c.d / RE, tilt: c.tilt, heading: c.heading, fov: c.fov }; } }, o.spec || {}));
    if (o.fadeIn) s.uiFrom = a + o.fadeIn; scenes.push(o.wrap ? o.wrap(s) : s); return s; };
  if (dbg) api.log(`[ch5] onlyreef ${T('onlyreef').toFixed(2)} ch4.t1x ${ch4.t1x.toFixed(2)} drag hand-offs ${tU1.toFixed(2)} ${tD1.toFixed(2)}`);

  // leg 0: Midway, MIDWAY on {midway}
  terrLeg('ch5-drag-0', 'midway', ch.t0, tU1 + XU, PD, { fadeIn: K.XF, wrap: (s) => blurred(s, Math.min(439.55, tU1 - 0.1), tU1 + XU, 5, 0.45), spec: {
    ui(ctx, lt, t, view) { avoidGauge(t); lab(ctx, 'MIDWAY', gp(view, MIDW, 40), t, lead('midway'), 439.45); } } });
  // leg 1: the globe. HNL-MIDWAY (1,312 mi) in white; the NY-MIA great circle (1,092 mi, true length on the sphere) in yellow lifts off,
  // flies with the camera and lands beside it, starting at the Honolulu end: it comes up short
  const LHM = gcKm(HNL, MDY), LNM = gcKm(NYC, MIA), HM = gcPts(HNL, MDY, 64), B0 = gcBrg(NYC, MIA), BL = gcBrg(HNL, MDY), L0 = dest(HNL, 300, BL + 90);
  const dB = ((BL - B0) % 360 + 540) % 360 - 180;
  api.log(`[ch5] HNL-MIDWAY ${(LHM / 1.609344).toFixed(0)} mi, NY-MIAMI ${(LNM / 1.609344).toFixed(0)} mi (great circles, drawn true length)`);
  const nyState = (t) => {
    if (t < 441.0) return { S: NYC, B: B0, h: 0, p: pr(t, 440.75, 441.0) };
    if (t < 441.25) return { S: NYC, B: B0, h: 0.035 * pr(t, 441.0, 441.25), p: 1 };
    const f = pr(t, 441.25, 442.0); if (t < 442.0) return { S: gcAt(NYC, L0, f), B: B0 + dB * f, h: 0.035, p: 1 };
    return { S: L0, B: BL, h: 0.035 * (1 - pr(t, 442.0, 442.11)), p: 1 }; };
  globeLeg('ch5-drag-1', tU1, tD1 + XF, PD, { fadeIn: XU, wrap: (s) => blurred(s, tU1, 440.4, 4, 0.4), spec: {
    ui(ctx, lt, t, view) {
      const P = (ll, h = 0) => { const q = view.project(ll[1], ll[0], h); return q && q.visible ? [q.x, q.y] : null; };
      const fa = 1 - pr(t, 443.9, 444.4), pw = pr(t, 440.15, 440.75);
      if (fa <= 0) return;
      ctx.save(); ctx.globalAlpha *= fa;
      const hq = P(HNL), mq = P(MDY);
      if (hq && t > 440.05) ui.pin(ctx, hq[0], hq[1], { r: 14, t: t - 440.1, color: PAL.text, p: F.clamp((t - 440.05) / 0.25) });
      if (pw > 0) ui.line(ctx, view.runs([HM], { h: 0.0004 }), { color: '#FFFFFF', width: 10, p: pw });
      if (mq && pw > 0.97) ui.pin(ctx, mq[0], mq[1], { r: 14, t: t - 440.75, color: PAL.text, p: F.clamp((t - 440.72) / 0.25) });
      if (t > 440.75) { const s = nyState(t), pts = []; for (let i = 0; i <= 40; i++) pts.push(dest(s.S, LNM * i / 40, s.B));
        if (s.h > 0.001) ui.line(ctx, view.runs([pts], { h: 0.0003 }), { color: '#05080F', width: 12, p: s.p, alpha: 0.35 * F.clamp(s.h / 0.01) });
        ui.line(ctx, view.runs([pts], { h: 0.0005 + s.h }), { color: PAL.yellow, width: 10, p: s.p }); }
      ctx.restore();
    } } });

  // leg 2: the colony on Sand Island (paper albatrosses, deliberately oversized like ch4's seals: a constant on-screen scale per metre of
  // camera distance), the hero's take-off, glide, crash landing and roll; then the pull-up while the sea falls
  const EYE0 = (() => { const e = kit.orbitEye(KD2); return [e.lon, e.lat]; })();
  const fwd = (f, r) => offLL(offLL(EYE0, f, HD), r, HD + 90);
  const HERO = fwd(0.042, 0.006), LAND = fwd(0.040, 0.0015), LAND2 = fwd(0.041, 0.009), D0 = 0.0455, HERO_H = 0.38 * H;
  const COL = { birds: null };
  const colony = (view) => { if (COL.birds) return COL.birds; const S = view.S, out = [];
    for (let i = 0; i < 160 && out.length < 46; i++) { const r = 0.062 + 0.19 * Math.pow(hash(i, 1), 0.8), a = HD + (hash(i, 2) - 0.5) * 72, ll = offLL(EYE0, r, a);
      if (S.heightAt(ll[0], ll[1]) < 0.8) continue; out.push({ ll, r, sit: hash(i, 3) < 0.5, flip: hash(i, 4) < 0.45, sz: 0.85 + 0.3 * hash(i, 5), seed: i }); }
    out.sort((a, b) => b.r - a.r); COL.birds = out;
    logOnce('colony', `[ch5] colony: ${out.length} birds on land; hero ground ${S.heightAt(HERO[0], HERO[1]).toFixed(1)} m, land ${S.heightAt(LAND[0], LAND[1]).toFixed(1)}/${S.heightAt(LAND2[0], LAND2[1]).toFixed(1)} m`);
    return out; };
  const tPop = 446.15, tCrouch = 447.75, tOff = 447.95, tExit = 449.6, tIn = 450.1, tTouch = 451.7, tTum0 = 451.72, tTum1 = 452.25, tShake = T('gooney') - 0.2;
  const HR = { top: null };
  const colonyWorld = (ctx, t, view) => {
    if (t > 456.6) return;
    const birds = colony(view), g0 = (ll) => view.S.heightAt(ll[0], ll[1]);
    const scl = (ll) => D0 / Math.max(1e-4, camDist(view, ll[0], ll[1], g0(ll) + 0.4));
    // the field: standing and sitting birds, far to near
    for (const b of birds) { const hPx = HERO_H * 0.42 * b.sz * scl(b.ll); if (hPx < 6) continue;
      kit.drawCutout(ctx, view, ALB, { lon: b.ll[0], lat: b.ll[1], hm: g0(b.ll), hPx, squash: b.sit ? 0.34 : 0, flip: b.flip, t, seed: b.seed, wobble: 0.008, alpha: F.clamp((hPx - 6) / 6), shadowA: 0.24 }); }
    // two small birds gliding high over the colony
    if (t > 445.6 && t < 455) for (const [k, y0, sp, ph] of [[0, 0.17, 0.055, 0.1], [1, 0.25, 0.04, 0.62]]) {
      const x = ((t - 445.6) * sp + ph) % 1.25 - 0.12, y = H * (y0 + 0.02 * Math.sin((t + k) * 1.3));
      kit.drawCutout(ctx, view, FLY, { x: x * W, y, hPx: px(54 - 12 * k), base: false, shadow: false, contact: false, lean: 0.05 * Math.sin(t * 1.1 + k), t, seed: 20 + k, wobble: 0.02 }); }
    // the hero
    HR.top = null; if (t < tPop) return;
    const hS = HERO_H * scl(HERO), hq = view.project(HERO[0], HERO[1], g0(HERO)), lq = view.project(LAND[0], LAND[1], g0(LAND)), l2q = view.project(LAND2[0], LAND2[1], g0(LAND2));
    if (!hq || !lq || !l2q) return;
    if (t < tOff) {                                                       // standing, then the crouch before the take-off
      const r = kit.drawCutout(ctx, view, ALB, { lon: HERO[0], lat: HERO[1], hm: g0(HERO), hPx: hS, pop: F.clamp((t - tPop) / 0.35), squash: 0.14 * pr(t, tCrouch, tOff - 0.02, E.out), t, seed: 3, wobble: 0.01 });
      if (r) HR.top = [r.x - r.w * 0.12, r.top + r.h * 0.06]; return; }
    const hF = HERO_H * 1.15 * scl(HERO);
    if (t < tExit) {                                                      // the glide out, up and to the left (wings out, slow banks)
      const u = F.clamp((t - tOff) / (tExit - tOff)), e = u * u * (3 - 2 * u) * 0.6 + u * 0.4;
      const p = bez([hq[0], hq[1] - hS * 0.45], [hq[0] - 0.1 * W, hq[1] - 0.66 * H], [-0.3 * W, 0.1 * H], e), hh = hF * (1 - 0.3 * e);
      kit.drawCutout(ctx, view, FLY, { x: p[0], y: p[1] + hh / 2, hPx: hh, flip: true, base: false, shadow: false, contact: false, lean: -0.1 + 0.07 * Math.sin((t - tOff) * 2.4), t, seed: 4, wobble: 0.012 });
      if (u < 0.25) { ctx.save(); ctx.globalAlpha *= 0.3 * (1 - u / 0.25); ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(hq[0], hq[1], hS * 0.5, hS * 0.08, 0, 0, 7); ctx.fill(); ctx.restore(); }
      return; }
    if (t < tIn) return;
    if (t < tTouch) {                                                     // back in from the left: the approach, wobbling harder and harder
      const u = F.clamp((t - tIn) / (tTouch - tIn)), e = u * u * 0.55 + u * 0.45, hh = F.lerp(0.75, 1.0, u) * hF * 0.85;
      const p = bez([-0.25 * W, 0.2 * H], [0.22 * W, 0.12 * H], [lq[0] - hh * 0.25, lq[1] - hh * 0.4], e);
      const wob = (0.04 + 0.3 * u * u) * Math.sin((t - tIn) * (9 + 14 * u));
      kit.drawCutout(ctx, view, FLY, { x: p[0], y: p[1] + hh / 2, hPx: hh, base: false, shadow: false, contact: false, lean: 0.12 * u + wob, t, seed: 6, wobble: 0.03 + 0.05 * u });
      return; }
    const hL = HERO_H * scl(LAND);
    if (t < tTum1) {                                                      // the forward roll: one full turn clockwise, a small hop, to LAND2
      const u = F.clamp((t - tTum0) / (tTum1 - tTum0)), th = 2 * Math.PI * (u * u * (3 - 2 * u) * 0.7 + u * 0.3), hop = Math.sin(Math.PI * u) * hL * 0.35;
      const C = [F.lerp(lq[0], l2q[0], u), F.lerp(lq[1], l2q[1], u) - hL * 0.5 - hop];
      ctx.save(); ctx.globalAlpha *= 0.4 * (1 - hop / (hL * 0.5)); ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(C[0], F.lerp(lq[1], l2q[1], u), hL * 0.45, hL * 0.07, 0, 0, 7); ctx.fill(); ctx.restore();
      kit.drawCutout(ctx, view, ALB, { x: C[0] - Math.sin(th) * hL / 2, y: C[1] + Math.cos(th) * hL / 2, hPx: hL, flip: true, lean: th, base: false, shadow: false, contact: false, squash: t < tTum0 + 0.06 ? 0.18 : 0, t, seed: 5 });
    } else {                                                              // upright, ruffled; the head shake on {gooney}
      const rec = F.clamp((t - tTum1) / 0.4), sq = 0.17 * (1 - E.out(rec)) * Math.cos(rec * 9), us = F.clamp((t - tShake) / 0.42), sh = us > 0 && us < 1 ? Math.sin(us * Math.PI * 4) * (1 - us) : 0;
      const r = kit.drawCutout(ctx, view, ALB, { lon: LAND2[0], lat: LAND2[1], hm: g0(LAND2), hPx: HERO_H * scl(LAND2), flip: true, squash: sq, turn: 0.13 * sh, lean: 0.05 * sh, t, seed: 5, wobble: 0.008 });
      if (r) { HR.top = [r.x, r.top];                                     // three feathers stuck on, sticking out at odd angles
        for (const [fx, fy, rot] of [[0.18, 0.12, -0.9], [-0.05, 0.28, 0.7], [0.3, 0.42, -0.3]]) feather(ctx, r.x + fx * r.w, r.top + fy * r.h, r.h * 0.07, rot + 0.15 * sh, 1); }
    }
    // the dust puff and the loose feathers
    const ud = F.clamp((t - 451.72) / 0.88); if (ud > 0 && ud < 1) { ctx.save();
      for (let k = 0; k < 11; k++) { const f = hash(k, 7), x = F.lerp(lq[0], l2q[0], f) + (hash(k, 8) - 0.5) * hL * 0.5, y = F.lerp(lq[1], l2q[1], f) - hL * 0.05 * hash(k, 9);
        const rr = hL * (0.08 + 0.22 * E.out(ud) * (0.6 + hash(k, 10))); ctx.globalAlpha = 0.55 * (1 - ud) * (0.6 + 0.4 * hash(k, 11)); ctx.fillStyle = k % 2 ? '#E7DAC0' : '#D9CBAF';
        ctx.beginPath(); ctx.arc(x, y - rr * 0.4, rr, 0, 7); ctx.fill(); } ctx.restore(); }
    const uf = (t - 452.3) / 1.3; if (uf > 0 && uf < 1) for (let k = 0; k < 6; k++) {
      const x = l2q[0] + (hash(k, 12) - 0.5) * hL * 0.9 + Math.sin(uf * 6 + k) * hL * 0.1, y = l2q[1] - hL * (0.9 + 0.3 * hash(k, 13)) + uf * hL * (0.7 + 0.25 * hash(k, 14));
      feather(ctx, x, y, hL * 0.06, Math.sin(uf * 5 + k * 2) * 0.9, F.clamp((1 - uf) * 3)); }
  };
  terrLeg('ch5-drag-2', 'midway', tD1, 458.64, PD, { fadeIn: XF, wrap: (s) => blurred(s, tD1, 445.7, 6, 0.4), spec: {
    world(ctx, lt, t, view) { colonyWorld(ctx, t, view); },
    ui(ctx, lt, t, view) { avoidGauge(t);
      if (HR.top && t > 446.2 && t < 448.6) lab(ctx, 'LAYSAN ALBATROSS', HR.top, t, 446.3, 448.3, { order: ['above-right', 'right', 'above', 'above-left', 'left'], dist: 60 });
      const pc = pr(t, 457.8, 458.2); if (pc > 0) {                         // the cut line along the section plane (slice_reveal)
        const pts = []; for (let u = -16; u <= 26; u += 0.1) pts.push(offLL(SAND, u, 5.5));   // across the drained volcano top and flanks in frame
        ui.line(ctx, druns(view, pts, 6, 1), { color: '#FFFFFF', width: 6, p: pc }); }
    } } });

  // ================================================================ CAKE: the cut-away through the drained atoll (s118-s122)
  const K2 = [C0b, ...[[460.2, 2], [461.7, 3], [462.7, 4], [466.5, 5], [469.5, 6], [472.8, 7], [478.0, 8], [478.9, 9], [480.64, 10]].map(([t, k]) => secCam(t, CC[k]))];
  const PC = route([ch.t0, 458.64, PD], [458.64, 480.64, chainPath(K2)]);
  const shake = (c, t) => { let a = 0; for (const t0 of [478.97, 479.69]) if (t > t0) a += 0.35 * Math.exp(-(t - t0) / 0.15) * Math.sin((t - t0) * 70) * (t0 === 478.97 ? 1 : 0.6);
    return a ? Object.assign({}, c, { heading: c.heading + a, tilt: c.tilt + a * 0.6 }) : c; };
  // the sinking loop: X = how far the basalt top still stands above its real place (m), G = how far the reef top lags under the surface (m)
  const XK = (t) => {
    if (t < 462.6) return 0;
    if (t < 463.0) return 380 * pr(t, 462.6, 462.9);
    if (t < 468.3) return 380 - 130 * pr(t, 463.05, 463.2, E.out) - 130 * pr(t, 464.45, 464.6, E.out) - 120 * pr(t, T('upward'), T('upward') + 0.15, E.out);
    if (t < 469.0) return 380 * pr(t, 468.3, 468.6);
    return 380 * (1 - pr(t, 469.0, 472.0, lin)); };
  const GK = (t) => { let g = 0;
    if (t < 468.3) { for (const [a, dx] of [[463.05, 130], [464.45, 130], [T('upward'), 120]]) if (t > a) g += dx * (1 - E.out(F.clamp((t - a) / 0.8))); }
    else if (t > 469.0) g = 18 * env(t, 469.0, 472.2, 0.3, 0.4);
    return g; };
  const BAS = { col: '#4A433D', at: -1 };
  const band = (ctx, sec, us, lo, hi, fill) => { const top = [], bot = [];
    for (let i = 0; i < us.length; i++) { const a = sec.project(us[i], Math.max(lo[i], hi[i]), 0.002), b = sec.project(us[i], lo[i], 0.002); if (a && b) { top.push(a); bot.push(b); } }
    if (top.length < 2) return; ctx.beginPath(); top.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); for (let i = bot.length - 1; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]);
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); };
  const cakePaint = (ctx, view, t) => {
    const sec = view.sec; if (!sec) return;
    // the section face's own basalt colour, sampled once per frame under the cap (painted bands then match it)
    // (pure per frame: the first on-screen point of a fixed list, else a constant; never the previous frame's value)
    if (BAS.at !== t) { BAS.at = t; BAS.col = '#4A433D';
      for (const u of [3.5, 5.5, 1.5, 7.5, 9.5, 0, 11]) { const q = sec.project(u, bt(u) - 140, 0.002);
        if (!(q && q[0] > 2 && q[0] < W - 2 && q[1] > 2 && q[1] < H - 2)) continue;
        try { const d = ctx.getImageData(Math.round(q[0]), Math.round(q[1]), 1, 1).data; BAS.col = `rgb(${d[0]},${d[1]},${d[2]})`; } catch (e) { /* constant */ } break; } }
    const X = XK(t), G = GK(t), runs = []; let cur = null;
    for (let u = -4.8; u <= 12.98 + 1e-6; u += 0.05) { const s = sec.surf(u), b = bt(u);            // the cap's real extent on the DEM (about -4.3 to 12.9)
      if (s < b + 20) { if (cur && cur.us.length > 1) runs.push(cur); cur = null; continue; }
      if (!cur) cur = { us: [], b: [], B: [], c: [], s: [] };
      const B = Math.min(b + X, s), c = Math.max(B, Math.min(s - G, s)); cur.us.push(u); cur.b.push(b); cur.B.push(B); cur.c.push(c); cur.s.push(s); }
    if (cur && cur.us.length > 1) runs.push(cur);
    ctx.save();
    for (const r of runs) {
      if (X > 0.5) band(ctx, sec, r.us, r.b, r.B, BAS.col);
      band(ctx, sec, r.us, r.B, r.c, '#EBDDBE');
      // two faint strata lines in the cap (the cake's layers) and the dark contact line on the basalt
      for (const f of [0.36, 0.7]) { const pts = r.us.map((u, i) => r.c[i] - r.B[i] > 25 ? sec.project(u, F.lerp(r.B[i], r.c[i], f), 0.002) : null);
        ctx.strokeStyle = 'rgba(150,128,95,0.45)'; ctx.lineWidth = px(2); ctx.beginPath(); let on = false; for (const q of pts) { if (!q) { on = false; continue; } if (on) ctx.lineTo(q[0], q[1]); else { ctx.moveTo(q[0], q[1]); on = true; } } ctx.stroke(); }
      ctx.strokeStyle = 'rgba(30,24,20,0.7)'; ctx.lineWidth = px(3); ctx.beginPath(); r.us.forEach((u, i) => { const q = sec.project(u, r.B[i], 0.002); if (q) i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.stroke();
      if (r.s.some((s, i) => s - r.c[i] > 0.5)) band(ctx, sec, r.us, r.c, r.s, 'rgba(38,128,156,0.92)');
    }
    ctx.restore();
  };
  // the two drill sites: paper derricks behind the cut, strings down the face to the basalt
  const DRILL = [0, 7.6], tRig = 472.97, tHit = 478.97;
  const drillDepth = (u, s, t) => { const b = bt(u); if (t < 473.3) return s; if (t < 478.6) return F.lerp(s, b + 28, pr(t, 473.3, T('reefrock'), lin)); return F.lerp(b + 28, b - 6, pr(t, 478.6, tHit, E.in)); };
  const drills = (ctx, view, t) => {
    const sec = view.sec; if (!sec || t < tRig) return;
    for (const [k, u] of DRILL.entries()) {
      const s = sec.surf(u), base = sec.project(u, s, -0.035), top = sec.project(u, s, 0.003), dep = sec.project(u, drillDepth(u, s, t), 0.003); if (!base || !top || !dep) continue;
      const hPx = 0.15 * H;   // one screen size through the camera moves
      const hop = (() => { const v = (t - 479.69) / 0.28; return v > 0 && v < 1 ? Math.sin(Math.PI * v) * px(16) : 0; })();
      // the string and the bit
      if (t > 473.2) { ctx.save(); ctx.strokeStyle = '#1C1C1E'; ctx.lineWidth = px(5); ctx.beginPath(); ctx.moveTo(top[0], top[1]); ctx.lineTo(dep[0], dep[1]); ctx.stroke();
        ctx.strokeStyle = '#B8B2A6'; ctx.lineWidth = px(2); ctx.beginPath(); ctx.moveTo(top[0], top[1]); ctx.lineTo(dep[0], dep[1]); ctx.stroke();
        ctx.fillStyle = '#2A2A2C'; ctx.beginPath(); ctx.moveTo(dep[0] - px(9), dep[1] - px(10)); ctx.lineTo(dep[0] + px(9), dep[1] - px(10)); ctx.lineTo(dep[0], dep[1] + px(6)); ctx.closePath(); ctx.fill(); ctx.restore(); }
      kit.drawCutout(ctx, view, RIG, { x: base[0], y: base[1], hPx, pop: F.clamp((t - tRig - k * 0.12) / 0.4), hop, t, seed: 30 + k, wobble: 0.006, shadow: [hPx * 0.3, -hPx * 0.05] });
      // one spark flash on the strike
      const us = (t - tHit) / 0.3; if (us > 0 && us < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= 1 - us;
        const rg = ctx.createRadialGradient(dep[0], dep[1], 0, dep[0], dep[1], px(70)); rg.addColorStop(0, 'rgba(255,240,190,1)'); rg.addColorStop(0.4, 'rgba(255,190,90,0.6)'); rg.addColorStop(1, 'rgba(255,150,60,0)');
        ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(dep[0], dep[1], px(70), 0, 7); ctx.fill();
        ctx.strokeStyle = 'rgba(255,236,170,1)'; ctx.lineWidth = px(3); for (let j = 0; j < 9; j++) { const a = j / 9 * Math.PI * 2 + 0.3, r0 = px(10), r1 = px(26 + 40 * E.out(us));
          ctx.beginPath(); ctx.moveTo(dep[0] + Math.cos(a) * r0, dep[1] + Math.sin(a) * r0); ctx.lineTo(dep[0] + Math.cos(a) * r1, dep[1] + Math.sin(a) * r1); ctx.stroke(); } ctx.restore(); }
    }
  };
  const CK = { box: null };
  scenes.push(kit.cutawayShot({ id: 'ch5-cake', t0: 458.34, t1: 480.64, fadeIn: 0.3, region: 'midway', preset: 'today',
    cam: (lt) => kit.terrainCamOf(shake(PC(458.34 + lt), 458.34 + lt)),
    state: (lt) => stOf(PC(458.34 + lt).d, 458.34 + lt),
    cut: { plane: PLANE, state: (lt) => { const t = 458.34 + lt, lv = LEVEL(t); return { sag: 0, sagM: 0, alphaKm: 90, oldFloor: -20000, crustM: 6500, waterTop: Math.min(0, lv), waterA: F.clamp(1 + lv / 1500) * 0.85, floorLine: 0, trenchA: 0, edgeA: 1 }; } },   // oldFloor under the wall's bottom: the whole face is the volcano's basalt (no crust band in ch5)
    world(ctx, lt, t, view) { cakePaint(ctx, view, t); drills(ctx, view, t); },
    ui(ctx, lt, t, view) { avoidGauge(t);
      const sec = view.sec; if (!sec) return;
      // ABOUT / 28 MILLION YEARS with a thin straight pointer to the basalt (no arrow)
      const t0 = lead('old28') - 0.1, t1 = 462.4;
      if (t > t0 && t < t1) { const tq = sec.project(4.0, -1600, 0.002);   // into the volcano's body (the age is the volcano's)
        const box = heroNum(ctx, t, 'ABOUT', 28, 'MILLION YEARS', t0, t1, 460.93, [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W - px(96), y: px(250), anchor: 'right' }, { x: W / 2, y: px(96), anchor: 'center' }]);   // punch on hit_body 460.93 (spot notes)
        if (box && tq) { const a = F.clamp((t - t0 - 0.35) / 0.3) * (1 - F.clamp((t - (t1 - 0.3)) / 0.3)), sx = box.x + px(40), sy = box.y + box.h;
          ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = 'rgba(5,9,15,0.6)'; ctx.lineWidth = px(6); ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(tq[0], tq[1]); ctx.stroke();
          ctx.strokeStyle = PAL.text; ctx.lineWidth = px(3); ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(F.lerp(sx, tq[0], pr(t, t0 + 0.35, t0 + 0.75)), F.lerp(sy, tq[1], pr(t, t0 + 0.35, t0 + 0.75))); ctx.stroke();
          if (t > t0 + 0.7) { ctx.fillStyle = PAL.yellow; ctx.beginPath(); ctx.arc(tq[0], tq[1], px(9), 0, 7); ctx.fill(); ctx.strokeStyle = PAL.ink; ctx.lineWidth = px(3); ctx.stroke(); } ctx.restore(); } }
      // CHARLES DARWIN (name plate only)
      const d0 = lead('darwin') - 0.05, d1 = 470.0;
      if (t > d0 && t < d1) ui.block(ctx, [{ text: 'CHARLES DARWIN', role: 'headline' }], W - px(96), px(96), { anchor: 'right', p: F.clamp((t - d0) / 0.45), out: F.clamp((t - (d1 - 0.35)) / 0.35), bar: PAL.yellow,
        at: [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W / 2, y: px(96), anchor: 'center' }] });
    } }));

  // ================================================================ WAR: dawn over the atoll, the water trick, the carriers, the wrecks (s123-s139)
  const GEO = { floor: -5312, plat: null };
  // two paths with a hard cut between them at tC (the end of the s132 pause, just before "Japan"): the globe's own texture seam at the
  // antimeridian shows from about 1,000 km up (seen at 525.8 in a zoom to the fleet), so the globe never comes close to it
  const tC = 525.2;
  const PW1k = [
    { t: 480.64, lon: MIDW[0], lat: 28.215, h: 0, d: 22, tilt: 32, heading: 350, fov: 40 },            // s123: hard cut, dawn
    { t: 486.9, lon: MIDW[0], lat: 28.218, h: 0, d: 17, tilt: 30, heading: 354, fov: 40 },
    { t: 488.5, lon: MIDW[0] + 0.5, lat: 28.08, h: 0, d: 420, tilt: 4, heading: 12, fov: 40 },        // {pac}: straight up, Midway kept in frame
    // the STORY globe of the central Pacific, Midway left and Oʻahu right on one level (heading 21 = the bearing Midway > Oʻahu less 90)
    { t: 489.9, lon: -171.0, lat: 26.0, h: 0, d: 3000, tilt: 12, heading: 21, fov: 40 },
    { t: 497.0, lon: -171.3, lat: 26.1, h: 0, d: 2950, tilt: 12, heading: 20, fov: 40 },             // the intercepts come in from the west
    { t: 504.2, lon: -170.8, lat: 25.95, h: 0, d: 2900, tilt: 12, heading: 21.5, fov: 40 },          // the telegram to Washington (east)
    { t: 513.6, lon: -171.2, lat: 26.1, h: 0, d: 2800, tilt: 12, heading: 21, fov: 40 },             // the bait
    { t: 523.6, lon: -171.4, lat: 26.2, h: 0, d: 2700, tilt: 12, heading: 20.5, fov: 40 },           // AF = MIDWAY
    { t: tC, lon: -172.2, lat: 26.6, h: 0, d: 2350, tilt: 12, heading: 17, fov: 40 }];               // the pause: a slow push west
  const PWk = (fl) => [
    // s133-s137, straight down: the terrain stack ends at 31.5 N and 182 W (a pale strip past it), so the frame top stays under about
    // 31.4 N and the left edge east of 181.8 W; the wrecks (30.4-30.6 N) clear of the gauge (Kaga right of it), the atoll at the bottom
    { t: tC, lon: -178.3, lat: 29.65, h: 0, d: 520, tilt: 0.5, heading: 0, fov: 40 },                 // s133: cut to north and west of Midway, the fleet
    { t: 527.6, lon: -178.5, lat: 29.85, h: 0, d: 450, tilt: 0.5, heading: 0, fov: 40 },
    { t: 533.0, lon: -178.52, lat: 29.8, h: 0, d: 450, tilt: 0.5, heading: 0, fov: 40 },
    { t: 535.9, lon: -178.55, lat: 29.42, h: 0, d: 450, tilt: 0.5, heading: 0, fov: 40 },               // s136: the wrecks and the atoll in one frame
    { t: 540.6, lon: -178.55, lat: 29.4, h: 0, d: 452, tilt: 0.5, heading: 0, fov: 40 },
    { t: 544.75, lon: -178.5, lat: 29.38, h: 0, d: 455, tilt: 1, heading: 0, fov: 40 },
    { t: 545.9, lon: YORK[0], lat: YORK[1], h: fl + 40, d: 2.2, tilt: 80, heading: 300, fov: 40 },   // s138: down on the floor
    { t: 550.9, lon: YORK[0], lat: YORK[1], h: fl + 40, d: 2.1, tilt: 80.5, heading: 312, fov: 40 },
    { t: 555.3, lon: YORK[0], lat: YORK[1], h: fl + 40, d: 2.0, tilt: 81, heading: 322, fov: 40 },
    { t: 556.8, lon: -177.4, lat: 29.4, h: 0, d: 260, tilt: 30, heading: 230, fov: 40 },             // lift away, the sea returns
    { t: 558.6, lon: KURE[0], lat: KURE[1], h: 0, d: 22, tilt: 48, heading: 250, fov: 40 },          // s140: Kure
    { t: 565.8, lon: KURE[0], lat: KURE[1], h: 0, d: 18, tilt: 50, heading: 255, fov: 40 },
    { t: 570.9, lon: KURE[0] + 0.03, lat: KURE[1] - 0.005, h: 0, d: 12, tilt: 54, heading: 258, fov: 40 },
    { t: 571.25, lon: KURE[0] + 0.032, lat: KURE[1] - 0.005, h: 0, d: 11.6, tilt: 54.3, heading: 258.5, fov: 40 }];
  // the switch sits just before tC: route() keeps the first leg at t = tC, and war-2's first frame (525.20) showed the globe camera
  // (d 2,350 km over the terrain stack: its whole data rectangle, one frame; mot f15756)
  const PW1 = chainPath(PW1k), mkPW = (fl) => route([480.64, tC - 1e-4, PW1], [tC - 1e-4, 571.25, chainPath(PWk(fl))]);
  let PW = mkPW(GEO.floor);
  const PWf = (t) => PW(t), tK = cross(PWf, 556.8, 558.6, 70), tW1 = cross(PWf, 486.9, 489.9, 350), tW2 = tC;
  // the globe leg's view in the terrain view's shape (project(lon, lat, hm) -> [x, y] | null), so warWorld/warUI/props serve both
  const gv = (view) => ({ project: (lon, lat, hm = 0) => { const q = view.project(lat, lon, Math.max(0, hm) / 6371000); return q && q.visible ? [q.x, q.y] : null; },
    visible: () => true, level: 0, S: { heightAt: () => 0 }, sec: null });
  const OAHU = [-157.95, 21.36];                                           // Pearl Harbor (the codebreakers)
  const warPrep = async () => {
    if (GEO.plat !== null) return;
    GEO.plat = [];
    try { const S = await kit.hub.terrain('midway', 1, {}); const fl = S.heightAt(YORK[0], YORK[1]);
      if (Math.abs(fl - GEO.floor) > 25) { GEO.floor = fl; PW = mkPW(fl); }
      const isl = await kit.island({ region: 'midway', bbox: [-177.47, 28.15, -177.27, 28.32], level: -25, seeds: [MIDW, SAND], step: 2 });
      GEO.plat = isl.rings || [];
      logOnce('war', `[ch5] floor at Yorktown ${fl.toFixed(0)} m, Akagi ${S.heightAt(AKAGI[0], AKAGI[1]).toFixed(0)} m, Kaga ${S.heightAt(KAGA[0], KAGA[1]).toFixed(0)} m; platform rings ${GEO.plat.length}; war>kure hand-off ${tK.toFixed(2)}`);
    } catch (e) { api.log('[ch5] war prep: ' + e.message); } };
  // the props of the water trick live on Midway's pin (screen space, paper cut-outs); P0 = when the props fade
  const tP1 = 525.1, tAF = 498.59, LANE = [0.2, 0.275, 0.35], SP = px(190), VS = px(470);
  const props = (ctx, t, pin, oq = null) => {
    const pa = 1 - pr(t, tP1 - 0.6, tP1), [x0, y0] = pin; if (pa <= 0) return [];
    const obs = []; ctx.save(); ctx.globalAlpha *= pa;
    // s125: a paper water drop pops on the pin, wobbles and drips
    if (t > T('water0') - 0.1 && t < 495.0) { const a = 1 - pr(t, 494.5, 495.0), w = 0.07 * Math.exp(-(t - T('water0')) * 1.6);
      const r = kit.drawCutout(ctx, null, DROP, { x: x0, y: y0 - px(36), hPx: px(118), pop: F.clamp((t - (T('water0') - 0.1)) / 0.35), lean: w * Math.sin((t - T('water0')) * 11), alpha: a, base: false, shadow: false, contact: false, t, seed: 40 });
      const ud = (t - 492.36) / 0.45; if (r && ud > 0 && ud < 1) { ctx.save(); ctx.globalAlpha *= a * (1 - ud * ud); ctx.fillStyle = PAL.cyan; ctx.beginPath(); ctx.ellipse(x0, y0 - px(30) + E.in(ud) * px(60), px(7), px(10), 0, 0, 7); ctx.fill(); ctx.restore(); }
      if (r) obs.push({ x: r.x - r.w / 2, y: r.top, w: r.w, h: r.h }); }
    // s126: intercepted streams flow west to east over the map; one group lights yellow on {af} and becomes AF
    const sa = env(t, 495.72, 499.7, 0.4, 0.5);
    if (sa > 0) for (const [li, ly] of LANE.entries()) { const ph = [0, 0.37, 0.71][li], y = H * ly;
      for (let k = -14; k <= 14; k++) { const x = x0 + (t - tAF) * VS + (k + ph) * SP; if (x < -px(260) || x > W + px(40)) continue;
        if (li === 0 && k === 0 && t > tAF - 0.12) continue;
        morse(ctx, x, y, px(13), k * 3 + li * 50, PAL.text, sa * F.clamp((t - 495.72) * 2.5) * (x < W ? 1 : 0)); } }
    // AF: lights on {af}, floats down to the pin by "Midway" (s127)
    if (t > tAF - 0.12 && t < 503.95) { const u = pr(t, 499.2, wordAt('s127', 'Midway')), y = F.lerp(H * LANE[0], y0 - px(118), u), a = F.clamp((t - (tAF - 0.12)) / 0.15) * (1 - pr(t, 503.6, 503.95));
      if (t < tAF + 0.1) morse(ctx, x0 - px(60), y, px(13), 0, PAL.yellow, a);
      else { const g = 1 + 0.18 * Math.sin(F.clamp((t - tAF - 0.1) / 0.22) * Math.PI); ctx.save(); ctx.translate(x0, y); ctx.scale(g, g);
        TY.txt(ctx, 'AF', 0, px(76) * 0.5, { cap: 76, color: PAL.yellow, align: 'center', stroke: true, alpha: a }); ctx.restore();
        obs.push({ x: x0 - px(60), y: y - px(50), w: px(120), h: px(100) }); } }
    // s127: the telegram to Washington (off the Hawaiʻi-side edge) and back with a '?' tag; it hovers until the tag falls on {conf}
    const tE0 = wordAt('s127', 'Washington') + 0.05, tE1 = tE0 + 0.7, tR0 = 505.4, tR1 = 506.05;
    const P0 = ON(oq, -px(60)) ? [oq[0], oq[1] - px(70)] : [x0 + px(40), y0 - px(60)], HOV = ON(oq, -px(60)) ? [Math.min(oq[0] - px(40), W - px(170)), oq[1] - px(230)] : [x0 + px(190), y0 - px(200)];
    if (t > tE0 - 0.25) { let p, a = 1, tag = false;
      if (t < tE0) p = P0;
      else if (t < tE1) p = bez(P0, [P0[0] + px(160), P0[1] - px(200)], [W + px(160), P0[1] - px(180)], pr(t, tE0, tE1, E.in));
      else if (t < tR0) p = null;
      else { tag = true; p = t < tR1 ? bez([W + px(160), y0 - px(300)], [x0 + px(520), y0 - px(320)], HOV, pr(t, tR0, tR1, E.out)) : [HOV[0], HOV[1] + Math.sin((t - tR1) * 2.2) * px(6)]; }
      if (p) { const r = kit.drawCutout(ctx, null, ENV, { x: p[0], y: p[1] + px(40), hPx: px(80), pop: F.clamp((t - (tE0 - 0.25)) / 0.25), lean: t < tE1 ? -0.15 : 0.06 * Math.sin(t * 2), base: false, shadow: false, contact: false, t, seed: 41, wobble: 0.02 });
        if (r) obs.push({ x: r.x - r.w / 2, y: r.top, w: r.w, h: r.h });
        const tf = T('conf'), uf = (t - tf) / 0.75;
        if (tag && uf < 1) { const fall = uf > 0 ? E.in(uf) : 0, sw = uf > 0 ? Math.sin(uf * 8) * 0.4 * uf : Math.sin(t * 3) * 0.08;
          const q = kit.drawCutout(ctx, null, TAG, { x: p[0] + px(70), y: p[1] + px(150) + fall * px(260), hPx: px(96), lean: sw, alpha: 1 - F.clamp(uf * 1.4 - 0.3), base: false, shadow: false, contact: false, t, seed: 42 });
          if (uf <= 0) { ctx.save(); ctx.strokeStyle = '#B8A88A'; ctx.lineWidth = px(2.5); ctx.beginPath(); ctx.moveTo(p[0] + px(30), p[1] + px(30)); ctx.lineTo(p[0] + px(70), p[1] + px(62)); ctx.stroke(); ctx.restore(); }
          if (q) obs.push({ x: q.x - q.w / 2, y: q.top, w: q.w, h: q.h }); } } }
    // s128: Midway radios in plain language (rings)
    for (let k = 0; k < 3; k++) { const u = (t - (T('plain') - 0.08) - k * 0.2) / 1.0; if (u <= 0 || u >= 1) continue;
      ctx.save(); ctx.globalAlpha *= 0.85 * (1 - u); ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = px(4); ctx.beginPath(); ctx.arc(x0, y0, px(30) + E.out(u) * px(240), 0, 7); ctx.stroke(); ctx.restore(); }
    // s129: the bait, a paper drop on a fishing line cast west from the pin; s130: Japan bites (tug) and it is pulled away
    const tB = T('bait') - 0.1, tBit = (() => { try { return K.word('s130', 'bit').end - 0.05; } catch (e) { return T('bit') + 0.55; } })();   // the twitch lands at the end of "bit" (spot notes 10)
    if (t > tB && t < tBit + 0.9) { const a = 1 - pr(t, tBit + 0.6, tBit + 0.9), cast = pr(t, tB, tB + 0.6, E.out), tug = F.clamp((t - tBit) / 0.18), gone = pr(t, tBit + 0.25, tBit + 0.85, E.in);
      const tip = [x0 - px(70), y0 - px(150)], hang = [x0 - px(70) - px(300) * cast - px(50) * tug - gone * px(700), y0 - px(40) + Math.sin((t - tB) * 2.6) * px(10) * (1 - tug) - px(40) * tug - gone * px(120)];
      ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = '#7A5A3A'; ctx.lineWidth = px(6); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0 - px(6), y0 - px(6)); ctx.lineTo(tip[0], tip[1]); ctx.stroke();
      ctx.strokeStyle = 'rgba(250,250,250,0.9)'; ctx.lineWidth = px(2.5); ctx.beginPath(); ctx.moveTo(tip[0], tip[1]);
      const sag = px(90) * (1 - tug); ctx.quadraticCurveTo((tip[0] + hang[0]) / 2, Math.max(tip[1], hang[1] - px(60)) - px(40) + sag * 0.2, hang[0], hang[1] - px(60)); ctx.stroke(); ctx.restore();
      kit.drawCutout(ctx, null, DROP, { x: hang[0], y: hang[1] + px(30), hPx: px(84), alpha: a * F.clamp(cast * 3), lean: 0.1 * Math.sin((t - tB) * 2.6) - 0.5 * tug, base: false, shadow: false, contact: false, t, seed: 43 });
      obs.push({ x: hang[0] - px(50), y: hang[1] - px(70), w: px(100), h: px(110) }); }
    // s129: the fresh-water plant (paper tank) pops, droops sadly on {broke} and drips
    const tTk = wordAt('s129', 'fresh-water') - 0.15;
    if (t > tTk) { const ub = F.clamp((t - T('broke')) / 0.9), sad = ub > 0 ? Math.sin(ub * Math.PI * 3) * (1 - ub) : 0, droop = ub > 0 ? 0.08 * E.out(ub) : 0;
      const r = kit.drawCutout(ctx, null, TANK, { x: x0 + px(170), y: y0 + px(36), hPx: px(150), pop: F.clamp((t - tTk) / 0.35), lean: 0.09 * sad - droop * 0.5, squash: droop, base: true, shadow: [px(40), px(8)], t, seed: 44, wobble: 0.01 });
      if (r) { obs.push({ x: r.x - r.w / 2, y: r.top, w: r.w, h: r.h });
        for (const [td, dx] of [[T('broke') + 0.94, 0], [T('broke') + 1.6, px(14)]]) { const ud = (t - td) / 0.5; if (ud > 0 && ud < 1) { ctx.save(); ctx.globalAlpha *= 1 - ud * ud; ctx.fillStyle = PAL.cyan;
          ctx.beginPath(); ctx.ellipse(r.x + dx - px(10), r.y - r.h * 0.38 + E.in(ud) * px(70), px(6), px(9), 0, 0, 7); ctx.fill(); ctx.restore(); } } } }
    // s130: the coded Japanese report runs west from the pin; {along} it decodes (groups flip into water drops); {shortwater} it settles as
    // AF and a drop over the pin
    const tS0 = 515.26, tDec = T('along'), tSet = T('shortwater');
    if (t > tS0 && t < 523.0) { const a = 1 - pr(t, 522.6, 523.0), y = y0 - px(250);
      for (let k = 0; k < 12; k++) { const born = tS0 + k * 0.32; if (t < born) continue; let x = x0 - px(60) - (t - born) * VS * 0.9; if (x < -px(240)) continue;
        const back = pr(t, tSet - 0.6, tSet + 0.2); x = F.lerp(x, x0, back); const yy = F.lerp(y, y0 - px(130), back), fa = a * (1 - (k ? back : 0));
        const flip = F.clamp((t - tDec - k * 0.04) / 0.3), sx = Math.abs(Math.cos(flip * Math.PI));
        ctx.save(); ctx.translate(x, yy); ctx.scale(Math.max(0.05, sx), 1); ctx.translate(-x, -yy);
        if (flip < 0.5) morse(ctx, x - px(70), yy, px(12), 100 + k, PAL.text, fa);
        else if (k === 0) { /* the head group becomes AF (drawn below) */ }
        else kit.drawCutout(ctx, null, DROP, { x, y: yy + px(26), hPx: px(52), alpha: fa, base: false, shadow: false, contact: false, t, seed: 60 + k });
        ctx.restore(); }
      if (t > tDec + 0.15) { const back = pr(t, tSet - 0.6, tSet + 0.2), hx = F.lerp(x0 - px(60) - (t - tS0) * VS * 0.9, x0, back), hy = F.lerp(y, y0 - px(150), back);
        const aa = a * F.clamp((t - tDec - 0.15) / 0.2); TY.txt(ctx, 'AF', Math.max(px(130), hx), hy + px(38), { cap: 76, color: PAL.yellow, align: 'center', stroke: true, alpha: aa });
        if (back > 0.5) kit.drawCutout(ctx, null, DROP, { x: Math.max(px(130), hx) + px(70), y: hy + px(36), hPx: px(64), alpha: aa * F.clamp((back - 0.5) * 3), base: false, shadow: false, contact: false, t, seed: 70 });
        obs.push({ x: hx - px(90), y: hy - px(50), w: px(200), h: px(110) }); } }
    ctx.restore();
    return obs;
  };
  const wordAt = (seg, w) => { try { return K.word(seg, w).start; } catch (e) { api.log('[ch5] ' + e.message); return K.s0(seg) + 1; } };
  // carriers: four Japanese (light paper cards turning dark grey one by one on {force}), then Yorktown (dark on {sub})
  const FLEET = [{ ll: KAGA, td: T('force'), hd: 130 }, { ll: SORYU, td: T('force') + 0.27, hd: 125 }, { ll: AKAGI, td: T('force') + 0.52, hd: 135 }, { ll: HIRYU, td: T('force') + 0.77, hd: 120 }];
  const drawCarrier = (ctx, view, ll, hd, dk, a, sc = 1) => { const q = view.project(ll[0], ll[1], Math.max(view.level, 0) + 20); if (!q || a <= 0) return null;
    const L = px(150) * sc, Hh = L * CAR_L.h / CAR_L.w; ctx.save(); ctx.globalAlpha *= a; ctx.translate(q[0], q[1]); ctx.rotate((hd - 90) * D2R);
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(px(6), px(8), L * 0.5, Hh * 0.45, 0, 0, 7); ctx.fill();
    if (dk < 1) ctx.drawImage(CAR_L.img, -L / 2, -Hh / 2, L, Hh); if (dk > 0) { ctx.globalAlpha *= dk; ctx.drawImage(CAR_D.img, -L / 2, -Hh / 2, L, Hh); } ctx.restore();
    return { x: q[0] - L / 2, y: q[1] - L / 2, w: L, h: L }; };
  const WRECKS = [{ ll: YORK, w: 'york2' }, { ll: KAGA, w: 'kaga' }, { ll: AKAGI, w: 'akagi' }];
  const POOL = { r: 0 };
  const warWorld = (ctx, t, view) => {
    // s133-s137 the fleet on the map (top-down paper cards), on the drained floor too
    if (t > 525.4 && t < 545.6) { const fa = 1 - pr(t, 545.0, 545.6);
      FLEET.forEach((f, i) => { const a = F.clamp((t - 525.5 - i * 0.08) / 0.3) * fa * (i === 1 || i === 3 ? 1 - pr(t, 535.3, 535.8) : 1); drawCarrier(ctx, view, f.ll, f.hd, pr(t, f.td - 0.05, f.td + 0.3), a); });
      if (t > 532.75) drawCarrier(ctx, view, YORK, 80, pr(t, T('sub') - 0.05, T('sub') + 0.35), F.clamp((t - 532.75) / 0.3) * fa); }
    // s138-s139 the floor: Yorktown's hull upright in a pool of soft blue light
    if (t > 545.3 && t < 557.2) { const b = view.project(YORK[0], YORK[1], GEO.floor); if (!b) return;
      const dist = camDist(view, YORK[0], YORK[1], GEO.floor), sc = F.clamp(2.25 / dist, 0.05, 1.4), a = F.clamp((t - 545.3) / 0.5) * (1 - pr(t, 556.2, 557.0));
      const br = 1 + 0.12 * Math.sin(F.clamp((t - (T('alike') - 0.1)) / 0.9) * Math.PI), R = W * 0.62 * sc * br;   // the pool and the hull at one screen size (the subject fills the frame)
      ctx.save(); ctx.globalAlpha *= a; ctx.globalCompositeOperation = 'screen';
      const rg = ctx.createRadialGradient(b[0], b[1] - R * 0.15, 0, b[0], b[1] - R * 0.15, R); rg.addColorStop(0, 'rgba(120,190,245,0.55)'); rg.addColorStop(0.5, 'rgba(70,140,210,0.28)'); rg.addColorStop(1, 'rgba(40,90,160,0)');
      ctx.fillStyle = rg; ctx.beginPath(); ctx.ellipse(b[0], b[1] - R * 0.15, R, R * 0.62, 0, 0, 7); ctx.fill(); ctx.restore();
      kit.drawCutout(ctx, view, HULL, { lon: YORK[0], lat: YORK[1], hm: GEO.floor, wPx: W * 0.5 * sc, alpha: a, base: false, shadowA: 0.35, t, seed: 50, wobble: 0.002 }); }
  };
  const warUI = (ctx, t, view) => {
    avoidGauge(t);
    // s123 JUNE 1942; {volc42} the reef ring (the drowned volcano's rim) outlined hero orange
    if (t > T('y1942') - 0.15 && t < 484.6) ui.block(ctx, [{ text: 'JUNE 1942', role: 'kicker', cap: 72 }], px(96), px(96), { anchor: 'left', p: F.clamp((t - (T('y1942') - 0.15)) / 0.4), out: F.clamp((t - 484.25) / 0.35), bar: PAL.yellow });
    const vo = env(t, T('volc42') - 0.1, 487.2, 0.2, 0.5);
    if (vo > 0 && GEO.plat?.length) { const pulse = 0.75 + 0.25 * Math.sin(F.clamp((t - T('volc42')) / 0.5) * Math.PI);
      for (const r of GEO.plat) ui.line(ctx, druns(view, r, 0, 1, 0), { color: PAL.hero, width: 8, alpha: vo * pulse, p: pr(t, T('volc42') - 0.1, T('volc42') + 0.5) }); }
    // the pin and the props (s124-s132)
    const tPin = Math.max(488.3, tW1 + XF + 0.05), pin = gp(view, MDY, 20), pa = env(t, tPin, tP1, 0.3, 0.6);
    if (pin && pa > 0) { ctx.save(); ctx.globalAlpha *= pa; ui.pin(ctx, pin[0], pin[1], { r: 15, t: t - tPin, color: PAL.text, p: 1 }); ctx.restore(); ui.avoid({ x: pin[0] - px(30), y: pin[1] - px(30), w: px(60), h: px(60) }); }
    if (pin && t > tPin + 0.3 && t < 491.7) lab(ctx, 'MIDWAY', pin, t, tPin + 0.3, 491.6, { order: ['above', 'above-left', 'left', 'above-right'] });
    if (pin && t > 491.5 && t < tP1) for (const b of props(ctx, t, pin, view.project(OAHU[0], OAHU[1], 20))) ui.avoid(b);
    // {mid2}: AF = MIDWAY (the props fade, the map dims a little)
    const dm = 0.13 * env(t, T('mid2') - 0.2, tC, 0.6, 0.05); if (dm > 0) { ctx.save(); ctx.fillStyle = `rgba(4,8,16,${dm})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    const m0 = lead('mid2'), m1 = tC - 0.02;
    if (t > m0 && t < m1) ui.block(ctx, [{ text: 'AF = MIDWAY', role: 'headline' }], W / 2, px(96), { anchor: 'center', p: F.clamp((t - m0) / 0.4), out: F.clamp((t - (m1 - 0.35)) / 0.35), bar: PAL.yellow,
      at: [...(pin ? [{ x: pin[0] + px(80), y: Math.max(px(96), pin[1] - px(250)), anchor: 'left' }] : []), { x: W / 2, y: px(96), anchor: 'center' }, { x: W - px(96), y: px(96), anchor: 'right' }, { x: px(96), y: px(96), anchor: 'left' }] });
    // s136: wreck rings (>= 64 px) on their names, one block, each word on its spoken word
    if (t > T('york2') - 0.2 && t < 545.1) { const fa = 1 - pr(t, 544.7, 545.05);   // gone before the dive's motion blur (it tripled them: mot 545.0)
      for (const w of WRECKS) { const q = view.project(w.ll[0], w.ll[1], Math.max(view.level, 0) + 20), t0 = T(w.w) - 0.08; if (!q || t < t0) continue;
        const a = F.clamp((t - t0) / 0.2) * fa, u = (t - t0) / 0.7; ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = 'rgba(5,9,15,0.6)'; ctx.lineWidth = px(9); ctx.beginPath(); ctx.arc(q[0], q[1], px(44), 0, 7); ctx.stroke();
        ctx.strokeStyle = PAL.text; ctx.lineWidth = px(5); ctx.beginPath(); ctx.arc(q[0], q[1], px(44), 0, 7); ctx.stroke();
        if (u > 0 && u < 1) { ctx.globalAlpha *= 1 - u; ctx.strokeStyle = PAL.yellow; ctx.lineWidth = px(4); ctx.beginPath(); ctx.arc(q[0], q[1], px(44) + E.out(u) * px(60), 0, 7); ctx.stroke(); }
        ctx.restore(); ui.avoid({ x: q[0] - px(60), y: q[1] - px(60), w: px(120), h: px(120) }); } }
    const b0 = T('york2') - 0.08, b1 = 540.5;
    if (t > b0 && t < b1) ui.block(ctx, [{ text: 'YORKTOWN KAGA AKAGI', role: 'headline' }], W - px(96), px(96), { anchor: 'right', p: F.clamp((t - b0) / 0.45), out: F.clamp((t - (b1 - 0.35)) / 0.35), bar: PAL.yellow,
      wordTimes: [T('york2') - 0.08, T('kaga') - 0.08, T('akagi') - 0.08], lt: t, grow: true,
      at: [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W - px(96), y: H * 0.42, anchor: 'right' }, { x: W / 2, y: H * 0.42, anchor: 'center' }, { x: px(96), y: H * 0.42, anchor: 'left' }] });
    // s137 {atoll}: yellow lines from the atoll to the three wrecks
    const pl = pr(t, T('atoll') - 0.1, T('atoll') + 0.5), la = 1 - pr(t, 544.7, 545.05);
    if (pl > 0 && la > 0) { const mq = view.project(MIDW[0], MIDW[1], Math.max(view.level, 0) + 20);
      for (const w of WRECKS) { const q = view.project(w.ll[0], w.ll[1], Math.max(view.level, 0) + 20); if (mq && q) ui.line(ctx, [[mq, q]], { color: PAL.yellow, width: 10, p: pl, alpha: la }); } }
    // s138 {threemi}: MORE THAN / 3 MILES DOWN (the gauge pulses)
    const n0 = lead('threemi') - 0.1, n1 = 550.6;
    if (t > n0 && t < n1) heroNum(ctx, t, 'MORE THAN', 3, 'MILES DOWN', n0, n1, T('threemi'), [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W / 2, y: px(96), anchor: 'center' }]);
  };
  // war-0 dawn over the atoll {midway}; war-1 the STORY globe of the central Pacific ({pac} to the fleet); war-2 the battle, the drained
  // floor and the lift towards Kure {midway}. One camera path PW; both hand-offs where d crosses 700 km (detail resolves, no double image)
  const warTerr = (id, a, b, fadeIn) => { const s = kit.terrainShot({ id, t0: a, t1: b, fadeIn, region: 'midway', preset: 'today',
    cam: (lt) => kit.terrainCamOf(PWf(a + lt)), state: (lt) => stOf(PWf(a + lt).d, a + lt),
    world(ctx, lt, t, view) { const e = view.S.cam.position; if (e.y < Math.max(view.level, view.S.heightAt(PWf(t).lon, PWf(t).lat)) * 0.001 + 0.002) logOnce('under' + Math.round(t), `[ch5] war camera below the surface at ${t.toFixed(2)}`);
      warWorld(ctx, t, view); },
    ui(ctx, lt, t, view) { warUI(ctx, t, view); } }); if (fadeIn) s.uiFrom = a + fadeIn; return s; };
  scenes.push(ready(warTerr('ch5-war-0', 480.64, tW1 + XF, 0), warPrep));
  // the globe: no sun glint under the pin, light cloud (the islands read), hard cut out at tC
  globeLeg('ch5-war-1', tW1, tC, PWf, { fadeIn: XF, spec: { look: { specAmt: 0.08 }, sun: { clouds: 0.1 },
    ui(ctx, lt, t, view) { const v = gv(view); warWorld(ctx, t, v); warUI(ctx, t, v); } } });
  scenes.push(ready(blurred(warTerr('ch5-war-2', tC, tK + 0.45, 0), 544.8, 545.85, 6, 0.4), warPrep));
  api.log(`[ch5] war hand-offs: globe ${tW1.toFixed(2)}, terrain ${tW2.toFixed(2)}, kure ${tK.toFixed(2)}`);
  // s134: the Yorktown photo (U.S. Navy 80-G-21627, public domain; credit in the description), about 3 s, a slow 2 % push
  if (PH.york) { const p0 = 529.6, p1 = 532.6; scenes.push({ id: 'ch5-yorktown-photo', t0: p0, t1: p1, layer: 1, draw(ctx, lt, t) {
    const A = env(t, p0, p1, 0.35, 0.35); if (A <= 0) return; ctx.save(); ctx.globalAlpha *= A; kb(ctx, PH.york, F.lerp(1.0, 1.02, pr(t, p0, p1, lin)), 0.5, 0.6); ctx.restore(); } }); }

  // ================================================================ KURE: the last atoll, Darwin's blue (s140-s142)
  const KM5 = { cv: null, bb: [-178.45, 28.33, -178.2, 28.5] };
  const kurePrep = async () => { if (KM5.cv !== null) return; KM5.cv = false;
    try { const img = await loadImg('/ep/ep02/data/kure/sat.jpg'), w = 400, h = Math.round(400 * img.height / img.width), c = kit.P.cv(w, h), g = c.getContext('2d', { willReadFrequently: true });
      g.drawImage(img, 0, 0, w, h); const im = g.getImageData(0, 0, w, h), d = im.data;
      for (let i = 0; i < d.length; i += 4) { const L = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2], a = F.clamp((L - 40) / 14); d[i] = 0x3D; d[i + 1] = 0xE3; d[i + 2] = 0xFF; d[i + 3] = Math.round(255 * a); }
      g.putImageData(im, 0, 0); KM5.cv = c; } catch (e) { api.log('[ch5] kure mask: ' + e.message); } };
  // drape a lon/lat image over the sea surface: an n x n grid of projected cells, each an affine pair of triangles
  const drape = (ctx, view, img, bb, hm, n, alpha) => {
    const P = (i, j) => view.project(F.lerp(bb[0], bb[2], i / n), F.lerp(bb[3], bb[1], j / n), hm), G = [];
    for (let j = 0; j <= n; j++) { G.push([]); for (let i = 0; i <= n; i++) G[j].push(P(i, j)); }
    const sw = img.width / n, sh = img.height / n; ctx.save(); ctx.globalAlpha *= alpha;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const q = [G[j][i], G[j][i + 1], G[j + 1][i + 1], G[j + 1][i]]; if (q.some(v => !v)) continue;
      for (const tri of [[[0, 0, q[0]], [1, 0, q[1]], [0, 1, q[3]]], [[1, 0, q[1]], [1, 1, q[2]], [0, 1, q[3]]]]) {
        const [[u0, v0, P0], [u1, v1, P1], [u2, v2, P2]] = tri, x0 = (i + u0) * sw, y0 = (j + v0) * sh, x1 = (i + u1) * sw, y1 = (j + v1) * sh, x2 = (i + u2) * sw, y2 = (j + v2) * sh;
        const den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0); if (Math.abs(den) < 1e-9) continue;
        const a = ((P1[0] - P0[0]) * (y2 - y0) - (P2[0] - P0[0]) * (y1 - y0)) / den, b = ((P2[0] - P0[0]) * (x1 - x0) - (P1[0] - P0[0]) * (x2 - x0)) / den;
        const c = ((P1[1] - P0[1]) * (y2 - y0) - (P2[1] - P0[1]) * (y1 - y0)) / den, d = ((P2[1] - P0[1]) * (x1 - x0) - (P1[1] - P0[1]) * (x2 - x0)) / den;
        const cx = (P0[0] + P1[0] + P2[0]) / 3, cy = (P0[1] + P1[1] + P2[1]) / 3, gr = 0.6, ex = (p) => { const dx = p[0] - cx, dy = p[1] - cy, l = Math.hypot(dx, dy) || 1; return [p[0] + dx / l * gr, p[1] + dy / l * gr]; };
        ctx.save(); ctx.beginPath(); const e0 = ex(P0), e1 = ex(P1), e2 = ex(P2); ctx.moveTo(e0[0], e0[1]); ctx.lineTo(e1[0], e1[1]); ctx.lineTo(e2[0], e2[1]); ctx.closePath(); ctx.clip();
        ctx.transform(a, c, b, d, P0[0] - a * x0 - b * y0, P0[1] - c * x0 - d * y0); ctx.drawImage(img, 0, 0); ctx.restore(); } }
    ctx.restore(); };
  scenes.push(ready(kit.terrainShot({ id: 'ch5-kure', t0: tK, t1: 571.25, fadeIn: 0.45, region: 'kure', preset: 'today',
    cam: (lt) => kit.terrainCamOf(PWf(tK + lt)), state: (lt) => stOf(PWf(tK + lt).d, tK + lt),
    world(ctx, lt, t, view) { const a = 0.38 * pr(t, T('blue') - 0.1, T('blue') + 0.35); if (a > 0 && KM5.cv) drape(ctx, view, KM5.cv, KM5.bb, 1, 10, a); },
    ui(ctx, lt, t, view) { avoidGauge(t); lab(ctx, 'KURE (HŌLANIKŪ)', gp(view, KURE, 30), t, lead('kure') - 0.05, 561.6, { order: ['above', 'above-right', 'above-left'] }); } }), kurePrep));
  // {sinkground}: BLUE = SINKING on a cream paper slip (BLUE in cyan ink; not a dark caption plate), over the push and the cut
  const bs0 = lead('sinkground') - 0.05, bs1 = bs0 + 2.05;
  scenes.push({ id: 'ch5-blue', t0: bs0, t1: bs1, layer: 60, draw(ctx, lt, t) {
    ui.block(ctx, [{ words: [{ w: 'BLUE', c: '#0E9BC0' }, { w: '=' }, { w: 'SINKING' }], role: 'headline' }], W / 2, px(96), { anchor: 'center', p: F.clamp((t - bs0) / 0.45), out: F.clamp((t - (bs1 - 0.35)) / 0.35),
      bar: PAL.cyan, bg: '#F6F1E4', color: PAL.ink }); } });

  // ================================================================ KCUT: Kure in section, the cap barely keeps pace (s143)
  const KCT = offLL(KURE, 3.0, 90);
  // aimed at the cap's base, a narrower lens: the waterline sits at about 0.25 H, the sea is a band above it, the section fills the rest
  const KC1 = { t: 570.9, lon: KCT[0], lat: KCT[1], h: -330, d: 2.5, tilt: 74, heading: 0, fov: 34 }, KC2 = { t: 575.05, lon: KCT[0] + 0.004, lat: KCT[1], h: -320, d: 2.3, tilt: 74.5, heading: 2, fov: 34 };
  // the line (28.7 N) at about 0.6 of the frame height, so DARWIN POINT fits above it inside the label area (labels end at 670 px);
  // a slow drift north and out: Kure low right of centre, the drowned banks above the line, room for the ghost beside them
  const DV = { t: 576.6, lon: -179.2, lat: 28.85, h: 0, d: 300, tilt: 6, heading: 0, fov: 40 }, DV2 = { t: 584.39, lon: -178.8, lat: 29.05, h: 0, d: 440, tilt: 6, heading: 0, fov: 40 };
  const PCH = chainPath([KC2, DV, DV2,
    { t: 585.3, lon: -178, lat: 37, h: 0, d: 9500, tilt: 0, heading: 0, fov: 40 },               // s147: up to the globe, the chain lights
    { t: 588.6, lon: -182, lat: 40, h: 0, d: 8500, tilt: 0, heading: 0, fov: 40 },
    { t: 591.0, lon: -196, lat: 50, h: 0, d: 3000, tilt: 10, heading: 0, fov: 40 },              // s148: the trench
    { t: 594.5, lon: -197, lat: 51.5, h: 0, d: 2700, tilt: 10, heading: 0, fov: 40 },
    { t: 597.6, lon: -197.2, lat: 51.6, h: 0, d: 2650, tilt: 10, heading: 0, fov: 40 },
    { t: 598.2, lon: -186, lat: 33.5, h: 0, d: 4200, tilt: 8, heading: 60, fov: 40 },            // s149: the whip back down the chain
    { t: 598.6, lon: -157.2, lat: 20.6, h: 0, d: 1300, tilt: 20, heading: 125, fov: 40 },
    { t: ch.t1, lon: -155.55, lat: 19.75, h: 0, d: 560, tilt: 28, heading: 140, fov: 40 },       // FINAL KEY (ch6 starts here)
    { t: ch.t1x, lon: -155.55, lat: 19.75, h: 0, d: 560, tilt: 28, heading: 140, fov: 40 }]);
  const PK = route([570.9, 575.05, chainPath([KC1, KC2])], [575.05, ch.t1x, PCH]);
  const ZK = (t) => 160 * pr(t, 571.1, 574.9, lin);   // the volcano sinks 160 m in the shot (about 30 px/s): the old top and the reef layers ride down
  const lagK = (t) => 7 + 6 * Math.sin((t - 571.2) * 3.1) + 28 * Math.abs(Math.sin((t - T('sinking')) * Math.PI * 5)) * env(t, T('sinking') - 0.05, T('sinking') + 0.7, 0.05, 0.3);
  scenes.push(kit.cutawayShot({ id: 'ch5-kcut', t0: 570.9, t1: 575.4, fadeIn: 0.35, region: 'kure', preset: 'today',
    cam: (lt) => kit.terrainCamOf(PK(570.9 + lt)), state: (lt) => stOf(2, 570.9 + lt, { level: 0 }),
    cut: { plane: KPLANE, state: { sag: 0, sagM: 0, alphaKm: 90, oldFloor: -5000, crustM: 6500, waterTop: 0, waterA: 0.85, floorLine: 0, trenchA: 0, edgeA: 1 } },
    world(ctx, lt, t, view) { const sec = view.sec; if (!sec) return;
      const us = [], lo = [], Bv = [], ct = [], ss = [], Z = ZK(t), lag = Math.max(0, lagK(t));
      // the cap runs to the bank's edge (no painted end in frame); the old volcano top (Bv, a dark basalt strip) sinks with Z
      for (let u = -11.5; u <= 11.5 + 1e-6; u += 0.05) { const s = sec.surf(u); if (s < -60) continue; us.push(u); ss.push(s); const b = s - 220 - Z; Bv.push(b); lo.push(b - 45); ct.push(Math.max(b, s - lag)); }
      if (us.length < 2) return; ctx.save();
      band(ctx, sec, us, lo, Bv, '#3B3531'); band(ctx, sec, us, Bv, ct, '#EBDDBE'); band(ctx, sec, us, ct, ss, 'rgba(38,128,156,0.92)');
      // reef layers laid down at the top ride down with the volcano: new lines appear under the waterline, old ones sink
      ctx.lineWidth = px(2.5);
      for (let k = 1; k < 10; k++) { ctx.beginPath(); let n = 0, al = 0;
        us.forEach((u, i) => { const e = Bv[i] + k * 55; if (e > ct[i] - 6) return; const q = sec.project(u, e, 0.002); if (!q) return; n ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); n++; al = Math.max(al, F.clamp((ct[i] - 6 - e) / 25)); });
        if (n > 1) { ctx.strokeStyle = `rgba(150,118,78,${(0.55 * al).toFixed(3)})`; ctx.stroke(); } }
      ctx.strokeStyle = 'rgba(30,24,20,0.7)'; ctx.lineWidth = px(3); ctx.beginPath(); us.forEach((u, i) => { const q = sec.project(u, Bv[i], 0.002); if (q) i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.stroke();
      const wl = []; for (let u = -6; u <= 6; u += 0.2) { const q = sec.project(u, 0, 0.003); if (q) wl.push(q); }
      ui.line(ctx, [wl], { color: '#E8FBFF', width: 3, alpha: 0.85 }); ctx.restore(); },
    ui(ctx, lt, t, view) { avoidGauge(t); } }));

  // ================================================================ CHAIN: the Darwin Point, the drowned chain, Kamchatka, the whip (s144-s149)
  // the globe takes over while the camera is still near d 440: the stack's data edge (182 W / 31.5 N) shows from about d 480 (pI 584.6, pJ 584.5)
  const tU2 = 584.15,
        tD2 = cross(PK, 598.6, ch.t1, 900);
  const GH = { rings: null };
  const ghostPrep = async () => { if (GH.rings !== null) return; GH.rings = [];
    try { const isl = await kit.island({ region: 'bigisland', bbox: [-156.1, 18.85, -154.75, 20.3], level: 0, seeds: [[-155.47, 19.82]], step: 2 });
      GH.rings = (isl.rings || []).map(r => shiftLL(r, [-155.45, 19.6], [-177.95, 29.58])); } catch (e) { api.log('[ch5] ghost: ' + e.message); } };
  const DPTS = []; for (let lo = -182.0; lo <= -175.5; lo += 0.05) DPTS.push([lo, DPL]);
  terrLeg('ch5-chain-0', 'kure', 575.05, tU2 + XF, PK, { fadeIn: 0.35, wrap: (s) => ready(s, ghostPrep), spec: {
    world(ctx, lt, t, view) {
      const ga = env(t, T('roadon') - 0.1, T('roadon') + 1.4, 0.3, 0.35); if (ga > 0 && GH.rings?.length) { const runs = GH.rings.map(r => druns(view, r, 0, 1, 0)).flat();
        ui.fill(ctx, runs, { color: PAL.hero, fill: 0.28, alpha: ga }); ui.line(ctx, runs, { color: PAL.hero, width: 4, alpha: 0.75 * ga }); } },
    ui(ctx, lt, t, view) { avoidGauge(t);
      const dp = pr(t, 575.4, 576.6), lit = pr(t, T('point') - 0.1, T('point') + 0.25), fa = 1 - pr(t, 584.4, 584.9);
      if (dp > 0 && fa > 0) { const runs = druns(view, DPTS, 0, 1, 0);
        if (lit < 1) ui.line(ctx, runs, { color: '#FFFFFF', width: 4, p: dp, alpha: fa * (1 - lit) });
        if (lit > 0) ui.line(ctx, runs, { color: PAL.hero, width: 7, alpha: fa * lit });
        ui.avoidRuns(runs, 6); }
      lab(ctx, 'DARWIN POINT', view.project(-179.0, DPL, 0), t, lead('point') - 0.05, 579.4, { order: ['above', 'above-left', 'above-right'], dist: 60 }); } } });
  const CHP = []; for (let i = 0; i < CHAIN.length - 1; i++) { const seg = gcPts(CHAIN[i], CHAIN[i + 1], 6); CHP.push(...(i ? seg.slice(1) : seg)); }
  const EMP = []; for (let i = 0; i < EMPEROR.length - 1; i++) { const seg = gcPts(EMPEROR[i], EMPEROR[i + 1], 8); EMP.push(...(i ? seg.slice(1) : seg)); }
  const TRP = []; for (let i = 0; i < TRENCH.length - 1; i++) { const seg = gcPts(TRENCH[i], TRENCH[i + 1], 8); TRP.push(...(i ? seg.slice(1) : seg)); }
  const SLIDE = (t) => pr(t, 593.35, T('takes'), E.in);
  // the globe also draws the ghost (the compositor fades this whole shot in, UI included), so it holds through the early hand-off:
  // the ghost stays about 1.5 s on {roadon} (s146) although the globe takes over at 584.15. The Darwin Point line is left to the
  // terrain leg and fades with the dissolve (a globe copy doubled it off centre, flat vs curved projection: gag/g2 584.30-584.60)
  const chain1 = globeLeg('ch5-chain-1', tU2, tD2 + 0.3, PK, { fadeIn: XF, wrap: (s) => blurred(s, 597.65, tD2 + 0.3, 4, 0.5), spec: {
    ui(ctx, lt, t, view) {
      if (t > tU2 && t < 584.95) { const v = gv(view), ga = env(t, T('roadon') - 0.1, T('roadon') + 1.4, 0.3, 0.35);
        if (ga > 0 && GH.rings?.length) { const runs = GH.rings.map(r => druns(v, r, 0, 1, 0)).flat();
          ui.fill(ctx, runs, { color: PAL.hero, fill: 0.28, alpha: ga }); ui.line(ctx, runs, { color: PAL.hero, width: 4, alpha: 0.75 * ga }); } }
      const P = (ll, h = 0.0006) => { const q = view.project(ll[1], ll[0], h); return q && q.visible ? [q.x, q.y] : null; };
      const fa = 1 - pr(t, 597.6, 598.1); if (fa <= 0) return;
      ctx.save(); ctx.globalAlpha *= fa;
      const p1 = pr(t, 584.95, 585.6), p2 = pr(t, 585.9, T('kam')), sl = SLIDE(t);
      if (p1 > 0) ui.line(ctx, view.runs([CHP], { h: 0.0006 }), { color: PAL.hero, width: 9, p: p1 });
      // the Emperor chain: its tail (Detroit to Meiji) rides the plate into the trench on s148
      if (p2 > 0) { const n = EMP.length, cut = Math.round(n * 0.78), head = EMP.slice(0, cut + 1), tail = EMP.slice(cut).map(ll => dest(ll, 260 * sl, 302));
        ui.line(ctx, view.runs([head], { h: 0.0006 }), { color: PAL.hero, width: 9, p: F.clamp(p2 / 0.78) });
        if (p2 > 0.78) ui.line(ctx, view.runs([tail], { h: 0.0006 }), { color: PAL.hero, width: 9, p: F.clamp((p2 - 0.78) / 0.22), alpha: 1 - F.clamp((sl - 0.6) / 0.4) });
        EMPEROR.forEach((ll, i) => { const k = i / (EMPEROR.length - 1); if (p2 < k - 0.02) return; const late = i >= EMPEROR.length - 2, q = P(late ? dest(ll, 260 * sl, 302) : ll); if (!q) return;
          const a = F.clamp((p2 - k + 0.02) / 0.06) * (late ? 1 - F.clamp((sl - 0.6) / 0.4) : 1), r = px(9) * (late ? 1 - 0.5 * sl : 1);
          ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = PAL.ink; ctx.beginPath(); ctx.arc(q[0], q[1], r + px(3), 0, 7); ctx.fill(); ctx.fillStyle = PAL.hero; ctx.beginPath(); ctx.arc(q[0], q[1], r, 0, 7); ctx.fill(); ctx.restore(); }); }
      // {bend}: the bend pulses
      const ub = (t - (T('bend') - 0.05)) / 0.8, bq = P(BEND); if (bq && ub > 0 && ub < 1) { ctx.save(); ctx.globalAlpha *= 1 - ub; ctx.strokeStyle = PAL.yellow; ctx.lineWidth = px(5); ctx.beginPath(); ctx.arc(bq[0], bq[1], px(18) + E.out(ub) * px(70), 0, 7); ctx.stroke(); ctx.restore(); }
      // s148: the trench (teeth on the overriding side)
      const pt = pr(t, 590.45, 591.3); if (pt > 0) { const runs = view.runs([TRP], { h: 0.0005 }); ui.line(ctx, runs, { color: '#FFFFFF', width: 6, p: pt });
        for (let i = 2; i < TRP.length - 1; i += 3) { if (i / TRP.length > pt) break; const a = P(TRP[i], 0.0005), b = P(TRP[i + 1], 0.0005); if (!a || !b) continue;
          const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = dy / l, ny = -dx / l, s = px(13);
          ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.moveTo(a[0] - dx / l * s, a[1] - dy / l * s); ctx.lineTo(a[0] + dx / l * s, a[1] + dy / l * s); ctx.lineTo(a[0] + nx * s * 1.4, a[1] + ny * s * 1.4); ctx.closePath(); ctx.fill(); } }
      ctx.restore();
      lab(ctx, 'KAMCHATKA', P(KAMCH, 0), t, lead('kam') - 0.12, 590.5, { order: ['above-left', 'left', 'above', 'above-right'] });
    } } });
  chain1.uiFrom = tU2;   // its UI (the ghost above) from the start of the dissolve; the chain itself starts at 584.95
  terrLeg('ch5-chain-2', 'bigisland', tD2, ch.t1x, PK, { fadeIn: 0.3, st: () => ({ level: 0 }), wrap: (s) => blurred(s, tD2, ch.t1 - 0.05, 4, 0.5) });

  // ================================================================ sound cues (the picture's event times under the mix's names; the mix is spot_sfx.json)
  // Midway hush 524.3-565.3: no one-shot (no thunk on AF = MIDWAY, hero #6 silent); radio_squelch (the line twitch) is OFF in the mix by default
  const tBitC = (() => { try { return K.word('s130', 'bit').end; } catch (e) { return T('bit') + 0.6; } })();
  [[440.92, 'whoosh_big', -15], [445.65, 'whoosh_soft', -18], [446.2, 'paper_tap', -20], [447.96, 'whoosh_soft', -20], [451.76, 'albatross_tumble', -14], [455.38, 'drain_start', -12],
    [457.8, 'slice_reveal', -14], [460.57, 'impact_deep', -10], [460.93, 'hit_body', -14], [463.05, 'impact_short', -14], [464.45, 'impact_short', -14], [473.16, 'drill_grind', -18],
    [478.97, 'impact_deep', -10], [479.69, 'hit_body', -14], [487.28, 'whoosh_soft', -18], [492.36, 'drip_single', -18], [495.72, 'morse_intercept', -20], [505.49, 'paper_flutter', -16],
    [508.33, 'radio_pulse', -16], [tBitC, 'radio_squelch', -18], [515.26, 'morse_intercept', -20], [540.91, 'drain_flow', -14],
    [575.21, 'line_draw', -20], [579.57, 'drain_flow', -14], [584.39, 'whoosh_big', -15], [593.35, 'tension_groan', -15], [597.7, 'whoosh_big', -15]].forEach(c => api.cue(...c));

  // ================================================================ layer-0 contiguity check (gaps would show navy placeholders)
  const base = scenes.filter(s => (s.layer || 0) === 0 && s.t0 < ch.t1x && s.t1 > ch.t0 && /^ch5-/.test(s.id)).sort((a, b) => a.t0 - b.t0);
  let cov = ch.t0, gaps = []; for (const s of base) { if (s.t0 > cov + 1e-3) gaps.push(`${cov.toFixed(2)}-${s.t0.toFixed(2)}`); cov = Math.max(cov, s.t1); }
  if (cov < ch.t1x - 1e-3) gaps.push(`${cov.toFixed(2)}-${ch.t1x.toFixed(2)}`);
  api.log(`[ch5] ${base.length} base shots ${ch.t0.toFixed(2)}-${ch.t1x.toFixed(2)}${gaps.length ? ' GAPS ' + gaps.join(', ') : ', contiguous'}; hand-offs ${[tU1, tD1, tK, tU2, tD2].map(x => x.toFixed(2)).join(' ')}`);
}
