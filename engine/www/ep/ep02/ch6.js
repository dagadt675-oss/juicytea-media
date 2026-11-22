// Chapter 6 (s150-s178 + the end screen), window K.chapter(6) (598.99-746.85 s). Built 2026-11-16.
// Every beat is keyed to Rodney's markers (K.T / K.lead / K.word) and the mix's sync points (mix_ep02_v1.json); the chapter card
// (598.99-600.61) is the orchestrator's.
// Base layer 0, in film order (one camera path per run, hand-offs on the identical camera):
//   kama (kamaehu terrain, 598.99-639.5): opens on ch5's final key; s150 fast eased flight SE to the south coast while the sea drains to
//       about -1,500 m; s151 Kamaʻehuakanaloa's summit breaks the surface on the ping; s152-s153 a slow orbit, KAMAʻEHUAKANALOA;
//       s154 a lift to the south coast, felt rings on the rumble; s155 LŌʻIHI; s156-s158 the push to the summit platform, the paper
//       COMING SOON sign (pop on the sign_pop, dust puff on {fromnow}, droop on the creak); s159 the pull-out while the sea drains to
//       the trench.
//   massif (bigisland, 639.0-644.32): the full drained massif, the cyan trench strip (pulse on {feet}); s160 the push down to the
//       slice framing; s162 the blade runs along the cut line and the cut-away is wiped in behind it (slice_reveal 644.11).
//   cut (bigisland cut-away, 643.92-667.95): framings keep the 36 km wall's lower edge at the frame bottom (no empty space under it);
//       the sag deepens on {bent}; the mattress inset (in the section's own tones) with the ball landing on ball_mattress 652.52;
//       MAUNA LOA; the dented base line on {miles2}, glowing on {dent} with the old floor line; a pan to the trench rim, the strip
//       pulses on {edge}; a 1.2 s motion-blurred move to payoff's key 0.
//   payoff (payoff.js buildPayoff, T0 667.95 = s168's first word, 0.38 s before its first move key).
//   refill (bigisland cut-away 697.41-699.6, then uncut 699.13-734.93): Everest and the old-ocean slab go, the cut closes on {back},
//       the sea comes back from the trench over three compositions to the frame-1 composition at 0 m; the postcard drops back on the
//       cap (postcard_drop 719.12), the dent ghost on {planet}, the tourist on {lookdown3}, the flip to LOUISIANA on the paper tap.
//   end (bigisland, 734.93-746.85): the end-screen background, a slow orbit over the refilled island (nothing drawn).
// Local helpers only (no shared change): orbit/chainPath/route/blurred/ready (ch5), orbitOf (the exact inverse of terrainCamOf),
// secCam (section framings with the wall's lower edge at the frame bottom), a postcard with a width-fitted title (LOUISIANA), the
// card flip, the mattress painter, the felt rings, the dust puff.
import { PAL, E, F, MOVE_WATER, WATER_FILM, LINE, mixState, lookMix } from './shared.js';
import { buildPayoff, ML, CUT_PLANE, SECTION, EVEREST } from './payoff.js';

const D2R = Math.PI / 180, KM = 111.32, RK = 6371.0;
const VS = [-155.2645, 18.9186];                        // Kamaʻehuakanaloa's summit in the grid (-1,021 m; no pit craters at 58.7 m)
const GLOW = [[0.10, 0.75, 0.85], [0.06, 0.55, 0.70], [0.04, 0.42, 0.60]];   // ch3's trench-strip water (the callback)
// open-sea water for the low obliques (WATER_FILM's teal deep read bright turquoise at grazing angles): turquoise only at the shore
const SEA6 = [[0.020, 0.36, 0.40], [0.010, 0.12, 0.17], [0.008, 0.050, 0.105]];
const BASE = ML.summit - ML.total;                      // -12,966 m: payoff's dented true base
const UBAR = -4.0;                                      // payoff's bar column (its avoid box, so MAUNA LOA sits where payoff puts it)
// payoff.js camera keys used here (copied, not exported: keep in sync with payoff.js)
const PAY0 = { u: -14, d: 40, alt: 7.5, tu: 14, te: -1200, fov: 26 };
const PAY6 = { u: 10, d: 76, alt: 13, tu: 10, te: -1800, fov: 25.5 }, PAY7 = { u: 10.4, d: 78, alt: 13.3, tu: 10.4, te: -1800, fov: 25.5 };
const PC_HI = { lon: -155.5, lat: 19.62, wKm: 72, hm: 2600, rot: 4 };   // ch1's postcard footprint on the cap (cold open)

// ---------------------------------------------------------------------------------------------------------------- geo + camera helpers
const offLL = (ll, km, brg) => { const cl = Math.cos(ll[1] * D2R); return [ll[0] + km * Math.sin(brg * D2R) / (KM * cl), ll[1] + km * Math.cos(brg * D2R) / KM]; };
const brgOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return (Math.atan2((b[0] - a[0]) * cl, b[1] - a[1]) / D2R + 360) % 360; };
const kmOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return Math.hypot((b[0] - a[0]) * cl * KM, (b[1] - a[1]) * KM); };
function orbit(t, eye, alt, tgt, h, fov, ease) { const dh = kmOf(eye, tgt), dv = alt - h / 1000;
  return { t, lon: tgt[0], lat: tgt[1], h, d: Math.hypot(dh, dv), tilt: Math.atan2(dh, dv) / D2R, heading: brgOf(eye, tgt), fov, ease }; }
// the exact inverse of kit.terrainCamOf / orbitEye: a terrain camera {lon, lat, alt, tLon, tLat, tH, fov} -> an orbit key
const v3s = (lat, lon, r) => { const la = lat * D2R, lo = lon * D2R; return [Math.cos(la) * Math.cos(lo) * r, Math.sin(la) * r, -Math.cos(la) * Math.sin(lo) * r]; };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
function orbitOf(c, t) {
  const P = v3s(c.tLat, c.tLon, 1), Ev = v3s(c.lat, c.lon, RK + c.alt), V = Ev.map((v, i) => v - P[i] * RK), d = Math.hypot(...V), vp = dot(V, P);
  const n0 = [-P[0] * P[1], 1 - P[1] * P[1], -P[2] * P[1]], nl = Math.hypot(...n0), n = n0.map(v => v / nl);
  const e0 = [n[1] * P[2] - n[2] * P[1], n[2] * P[0] - n[0] * P[2], n[0] * P[1] - n[1] * P[0]], el = Math.hypot(...e0), e = e0.map(v => v / el);
  const Hh = V.map((v, i) => v - vp * P[i]);
  return { t, lon: c.tLon, lat: c.tLat, h: c.tH || 0, d, tilt: Math.acos(F.clamp(vp / d, -1, 1)) / D2R, heading: (Math.atan2(-dot(Hh, e), -dot(Hh, n)) / D2R + 360) % 360, fov: c.fov };
}
// a section framing (eye u, d km, alt A km; target column tu) whose lower frame edge meets the wall at eb km: the wall is 36 km deep,
// so a wide frontal view would otherwise show empty space under it
function secCam(u, d, A, tu, fov = 30, eb = -33) {
  const D = Math.hypot(d, tu - u), tb = Math.atan((A - eb) / D) / D2R, tc = tb - fov / 2;
  return { u, d, alt: A, tu, te: Math.round((A - D * Math.tan(tc * D2R)) * 1000), fov };
}
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
const loadImg = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('cannot load ' + src)); i.src = src; });
const gauss = (t, c, w) => Math.exp(-Math.pow((t - c) / w, 2));
const flexOf = (r, a = SECTION.alphaKm) => { const x = r / a; return Math.exp(-x) * (Math.cos(x) + Math.sin(x)); };

// the cold-open postcard style (kit.makePostcard) with the title fitted to the card's width (LOUISIANA is wider than HAWAIʻI)
function makeCard(kit, photo, title) {
  const w = 1200, h = 800, c = kit.P.cv(w, h), g = c.getContext('2d');
  g.fillStyle = '#F6F1E4'; g.fillRect(0, 0, w, h);
  const m = w * 0.045, pw = w - 2 * m, ph = h - 2 * m, s = Math.max(pw / photo.width, ph / photo.height), sw = pw / s, sh = ph / s;
  g.drawImage(photo, (photo.width - sw) / 2, (photo.height - sh) / 2, sw, sh, m, m, pw, ph);
  g.strokeStyle = 'rgba(120,90,60,0.35)'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, w - 3, h - 3);
  const tt = kit.okina(title), cap = h * 0.26; let size = cap / 0.86;
  g.font = `400 ${size}px "Anton"`; const tw = g.measureText(tt).width + cap * 0.18, room = pw - 2 * w * 0.04;
  if (tw > room) { size *= room / tw; g.font = `400 ${size}px "Anton"`; }
  const y = h - m - h * 0.07; g.textAlign = 'center'; g.lineJoin = 'round'; g.lineWidth = size * 0.86 * 0.18; g.strokeStyle = 'rgba(5,9,18,0.88)'; g.strokeText(tt, w / 2, y);
  g.fillStyle = '#FFD23F'; g.fillText(tt, w / 2, y);
  return kit.gradeCanvas(c);
}
// a postcard lying on the terrain that can flip about its own north-south axis (a paper turn in screen space, like the cut-outs'
// turn): phi 0 shows `front`, pi shows `back`; hop lifts it (m). Returns the quad [TL, TR, BR, BL] or null.
function drawFlipCard(kit, ctx, view, front, back, o) {
  const { lon, lat } = o, wk = o.wKm, hk = wk * front.height / front.width, rot = (o.rot || 0) * D2R, cl = Math.cos(lat * D2R);
  const hm = o.hm + (o.hop || 0), c = Math.cos(o.phi || 0), farUp = (o.lift || 0) * hk * 1000 * 0.35;   // drawPostcard's far-edge lift
  const corner = (sx, sy, up = 0) => { const dx = sx * wk / 2, dy = sy * hk / 2, ex = dx * Math.cos(rot) - dy * Math.sin(rot), ny = dx * Math.sin(rot) + dy * Math.cos(rot);
    return view.project(lon + ex / (KM * cl), lat + ny / KM, up); };
  const q0 = [corner(-1, 1, hm + farUp), corner(1, 1, hm + farUp), corner(1, -1, hm), corner(-1, -1, hm)];
  if (q0.some(v => !v)) return null;
  // contact shadow (on the cap, fainter while the card is up)
  const sh = [corner(-1, 1, o.hm), corner(1, 1, o.hm), corner(1, -1, o.hm), corner(-1, -1, o.hm)];
  const shA = 0.35 * (o.shadow ?? 1) * F.clamp(1 - (o.hop || 0) / 9000);
  if (sh.every(Boolean) && shA > 0.01) { ctx.save(); ctx.globalAlpha = shA; ctx.fillStyle = '#000'; ctx.beginPath(); sh.forEach(([x, y], i) => i ? ctx.lineTo(x + 6, y + 8) : ctx.moveTo(x + 6, y + 8)); ctx.closePath(); ctx.fill(); ctx.restore(); }
  // the turn: each edge squeezes about its own middle by |cos phi|; past 90 degrees the back shows, mapped to the same corners
  // (the squeeze uses |cos phi|, so the quad never mirrors and the back reads left to right; r5 swapped them and LOUISIANA read mirrored)
  const mid = (a, b) => (a[0] + b[0]) / 2, k = Math.abs(c);
  const sq = (p, m) => [m + (p[0] - m) * Math.max(k, 0.0), p[1]];
  const mt = mid(q0[0], q0[1]), mb = mid(q0[3], q0[2]);
  let q = [sq(q0[0], mt), sq(q0[1], mt), sq(q0[2], mb), sq(q0[3], mb)];
  if (k < 0.07) { ctx.save(); ctx.globalAlpha = o.alpha ?? 1; ctx.strokeStyle = '#E9E0CC'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(mt, q[0][1]); ctx.lineTo(mb, q[3][1]); ctx.stroke(); ctx.restore(); return q; }
  const img = c >= 0 ? front : back;
  kit.drawQuad(ctx, img, q, 6, o.alpha ?? 1);
  if (k < 0.95) { ctx.save(); ctx.globalAlpha = (o.alpha ?? 1) * 0.45 * (1 - k); ctx.fillStyle = '#1A140C'; ctx.beginPath(); q.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill(); ctx.restore(); }
  return q;
}
// s164: the bowling ball on a mattress, painted in the cut-away's own tones (the section's pile, crust and mantle bands, the same sky),
// in an inset panel; the bands bend with the same flexure curve as the section (the dip and the small bulge beyond it)
function drawMattress(ctx, box, t, tLand, A, px) {
  const { x, y, w, h } = box; if (A <= 0.002) return;
  ctx.save(); ctx.globalAlpha = A;
  ctx.fillStyle = 'rgba(0,0,0,0.30)'; F.round(ctx, x + px(4), y + px(8), w, h, px(10)); ctx.fill();
  ctx.save(); F.round(ctx, x, y, w, h, px(10)); ctx.clip();
  const sky = ctx.createLinearGradient(0, y, 0, y + h); sky.addColorStop(0, '#8FBEE6'); sky.addColorStop(1, '#CFE2EE'); ctx.fillStyle = sky; ctx.fillRect(x, y, w, h);
  const R = h * 0.15, cx = x + w * 0.5, top = y + h * 0.5;
  const s = t < tLand ? 0 : 1 - Math.exp(-(t - tLand) * 7) * Math.cos((t - tLand) * 19);          // the sag, with a damped bounce
  const sagPx = h * 0.16 * s, dip = (xx) => sagPx * flexOf(Math.abs(xx - cx), w * 0.16);
  const bands = [['#8B7D6E', 0.00], ['#776A5D', 0.09], ['#5F5348', 0.18], ['#3B4A66', 0.27], ['#56603A', 0.37]];   // pile, pile, deep pile, crust, mantle
  for (let i = 0; i < bands.length; i++) {
    const y0 = top + h * bands[i][1], k = 1 - i * 0.12;
    ctx.fillStyle = bands[i][0]; ctx.beginPath(); ctx.moveTo(x, y + h);
    for (let xx = x; xx <= x + w + 1; xx += 4) ctx.lineTo(xx, y0 + dip(xx) * k);
    ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(235,228,212,0.55)'; ctx.lineWidth = px(2.5); ctx.beginPath();
    for (let xx = x; xx <= x + w + 1; xx += 4) { const yy = y0 + dip(xx) * k; xx === x ? ctx.moveTo(xx, yy) : ctx.lineTo(xx, yy); } ctx.stroke();
  }
  // the ball: falls in (eased), rests in the dip; a soft contact shadow; dark and heavy with one cool highlight
  const fall = F.clamp((t - (tLand - 0.5)) / 0.5), y0b = y + R * 1.15, by = t < tLand ? y0b + (top - R - y0b) * E.in(fall) : top - R + dip(cx) * 0.92;
  if (t >= tLand) { const sg = ctx.createRadialGradient(cx, top + dip(cx), 0, cx, top + dip(cx), R * 1.5); sg.addColorStop(0, 'rgba(0,0,0,0.45)'); sg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.save(); ctx.translate(cx, top + dip(cx)); ctx.scale(1, 0.25); ctx.translate(-cx, -(top + dip(cx))); ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(cx, top + dip(cx), R * 1.5, 0, 7); ctx.fill(); ctx.restore(); }
  const bg = ctx.createRadialGradient(cx - R * 0.35, by - R * 0.4, R * 0.1, cx, by, R); bg.addColorStop(0, '#5A606B'); bg.addColorStop(0.45, '#262A31'); bg.addColorStop(1, '#0B0D11');
  ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(cx, by, R, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.85)'; for (const [dx, dy] of [[-0.18, -0.38], [0.08, -0.45], [-0.05, -0.2]]) { ctx.beginPath(); ctx.arc(cx + dx * R, by + dy * R, R * 0.075, 0, 7); ctx.fill(); }
  ctx.restore();
  ctx.strokeStyle = 'rgba(246,241,228,0.9)'; ctx.lineWidth = px(5); F.round(ctx, x, y, w, h, px(10)); ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------------------------------------------------------- build
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const ch = K.chapter(6), T = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f), s0 = (s) => K.s0(s), s1 = (s) => K.s1(s);
  const pr = (t, a, b, e = E.inOut) => e(F.clamp((t - a) / Math.max(1e-6, b - a)));
  const env = (t, a, b, fi = 0.3, fo = 0.3) => F.clamp(Math.min((t - a) / fi, (b - t) / fo));
  const dbg = !!api.Q.ch6dbg;

  // ================================================================ key times (film s)
  const tCard1 = ch.card + 0.26 + 1.1 + 0.26;                        // the chapter card is off (600.61)
  const tCoast = T('coast6'), tGrow = T('growing'), tPing = 607.97, tKama = lead('kama', 4), tKanaloa = T('kanaloa');
  const tQuake = 619.21, tSouth = T('south'), tLoihi = lead('loihi'), tPop = 628.81, tFromnow = T('fromnow'), tCreak = 633.90;
  const tDrain2 = s0('s159'), tWhole = T('whole'), tGurgle = 639.67, tFeet = 641.95, tSlice = 644.11, tBent = T('bent'), tBall = 652.52;
  const tLoa2 = lead('loa2'), tMiles = lead('miles2'), tDent = T('dent'), tEdge = 666.59;
  const tPay = s0('s168');                                            // payoff's T0 (667.95; default s0 - 1.0 would cut the edge beat)
  const PAYT1 = s1('s172') + 2.2, tBack = T('back'), tInrush = 700.13, tSea0 = 714.9, tGiant = T('giant2'), tDrop = 719.12;
  const tPlanet = T('planet'), tLook = 726.41, tHole = T('hole'), tFlip = 731.38, tLast = K.Te('la'), tEndCut = tLast + 1.0;
  const tWide = 637.4, tMassif0 = 636.9, tWipe0 = 643.92, tWipe1 = 644.32;   // the full massif just after {whole}

  // ================================================================ sea level, sun, look, exposure (film time)
  const LV1 = monotone([[603.2, 0], [606.3, -650], [tPing - 0.05, -1021], [608.8, -1380], [609.6, -1500]]);   // the summit breaks the surface on the ping
  const LV2 = monotone([[tDrain2, -1500], [tWhole, -2000], [638.0, -4400], [tGurgle, -5470]]);
  const LV3 = monotone([[tInrush - 0.3, -5470], [703.8, -4300], [708.6, -900], [712.0, -160], [tSea0, 0]]);
  const LEVEL = (t) => t < tDrain2 ? LV1(t) : t < 699.0 ? LV2(t) : LV3(t);
  const SUNK = [[ch.t0, 200, 30], [600.6, 200, 30], [603.1, 238, 20], [612.0, 262, 15], [626.0, 272, 13], [tDrain2, 272, 13], [tMassif0, 200, 24], [699.6, 200, 24], [tSea0, 262, 9]];
  const sunAz = monotone(SUNK.map(k => [k[0], k[1]])), sunEl = monotone(SUNK.map(k => [k[0], k[2]]));
  const SUN = (t) => [sunAz(t), sunEl(t)];
  const GOLD = (t) => pr(t, 600.6, 603.6) * (1 - pr(t, tDrain2, tMassif0));          // the warm low light over Kamaʻehuakanaloa
  const EXPO = (t) => F.lerp(1.2, 1.35, pr(t, 600.6, 603.6)) + (api.Q.ex6 ? +api.Q.ex6 : 0);
  const kOf = (d) => E.inOut(F.clamp((Math.log(d) - Math.log(25)) / (Math.log(500) - Math.log(25))));
  const waterAt = (d) => { const k = kOf(d); return SEA6.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], k))); };
  // the trench strip: cyan once the sea is down to the Hawaiian Deep (ch3's glow), one pulse on {feet} and one on {edge}
  const TGLOW = (t) => 0.85 * pr(t, 637.6, tGurgle) * (1 - pr(t, 667.4, 668.4)) + 0.5 * gauss(t, tFeet + 0.08, 0.22) + 0.45 * gauss(t, tEdge + 0.08, 0.22);
  // the state of every story leg before payoff (today > drained by the level, ch3's drained look; ch5's end state at 598.99)
  const stA = (t, d) => {
    const lv = LEVEL(t), dr = F.clamp(-lv / 900), k = kOf(d);
    const st = mixState('today', 'drained', dr);
    st.level = lv; st.sun = SUN(t); st.look = lookMix('day', 'gold', GOLD(t));
    Object.assign(st.set, { foamAmt: 0.3 * (1 - dr) * k + (1 - dr) * (1 - k), foamPx: 2.5 * (1 - k), tubAmt: 0.6 * dr, oldLine: F.clamp(-lv / 300),
      lineCol: LINE.cream, nearAmt: 0.3 * dr, fresMax: 0.4 });
    let wc = waterAt(d); const g = TGLOW(t);
    if (g > 0.01) { wc = wc.map((c, j) => c.map((v, q) => F.lerp(v, GLOW[j][q] * (1 + 0.6 * Math.max(0, g - 0.85)), Math.min(1, g)))); st.set.edgeGlow = 0.6 + 1.2 * Math.min(1, g); }
    st.waterCols = wc;
    st.post.exposure = F.lerp(t < 640 ? EXPO(t) : 1.3, 1.3, F.clamp(dr * 1.2)); st.post.sat = F.lerp(1.08, 1.0, k);
    return st;
  };

  // ================================================================ the SEA LEVEL gauge (marker only, no digits; ch3/ch5's)
  const GWIN = [[tCoast - 0.1, 610.2], [tDrain2 - 0.2, 640.7]];
  const gState = (t) => { for (const [a, b] of GWIN) if (t > a && t < b) return { p: F.clamp((t - a) / 0.5), out: F.clamp((t - (b - 0.45)) / 0.45) }; return null; };
  scenes.push({ id: 'ch6-gauge', t0: ch.t0, t1: 641, layer: 60, draw(ctx, lt, t) {
    const g = gState(t); if (!g) return;
    ui.gauge(ctx, { p: g.p, out: g.out, level: Math.max(LEVEL(t), -5500), range: 5500, value: false, pulse: Math.max(0, 1 - Math.abs(t - tPing) / 0.45) });
  } });

  // ================================================================ KAMA: ch5's final key > the south coast > Kamaʻehuakanaloa > the sign > pull-out
  const KA = [
    { t: ch.t0, lon: -155.55, lat: 19.75, h: 0, d: 560, tilt: 28, heading: 140, fov: 40 },          // ch5's FINAL KEY (identical camera)
    { t: tCard1 - 0.05, lon: -155.53, lat: 19.71, h: 0, d: 515, tilt: 29.5, heading: 139, fov: 40 }, // a slow drift under the card
    orbit(tCoast, [-155.44, 18.86], 7.0, [-155.29, 19.24], 0, 42),                                  // {coast6}: the south coast, low
    orbit(606.1, [-155.42, 18.80], 5.4, [-155.30, 18.96], -900, 41),                                 // {sea}: down to the water off the coast
    orbit(tGrow, [-155.335, 18.83], 3.4, VS, -1150, 40),                                             // {growing}: the summit breaks the surface
    { t: 612.2, lon: VS[0], lat: VS[1], h: -1200, d: 11.5, tilt: 72, heading: 40, fov: 40 },        // s152-s153: the slow orbit (the name)
    { t: 616.7, lon: VS[0], lat: VS[1], h: -1200, d: 10.5, tilt: 73, heading: 8, fov: 40 },
    { t: 618.95, lon: -155.272, lat: 19.055, h: -600, d: 58, tilt: 67, heading: 6, fov: 40 },       // s154: the lift to the south coast
    { t: 622.6, lon: -155.272, lat: 19.045, h: -600, d: 55, tilt: 67, heading: 4, fov: 40 },        //       (the felt rings)
    { t: 625.6, lon: VS[0], lat: VS[1], h: -1200, d: 19, tilt: 72, heading: 2, fov: 40 },           // s155: back toward the summit (LŌʻIHI)
    { t: 628.75, lon: VS[0], lat: VS[1] + 0.024, h: -1150, d: 8.6, tilt: 74, heading: 0, fov: 40 },  // s156: the push to the platform (aimed
    { t: 634.5, lon: VS[0], lat: VS[1] + 0.022, h: -1120, d: 7.2, tilt: 74.5, heading: -2, fov: 40 }, // 2.5 km past it: the sign sits mid-frame)
    { t: 636.2, lon: VS[0], lat: VS[1] + 0.05, h: -1800, d: 30, tilt: 69, heading: 0, fov: 39 },     // s159: up and back off the sign first
    { t: tWide, lon: -155.33, lat: 19.42, h: -3000, d: 190, tilt: 72, heading: 1, fov: 36 }];        // {whole}: the full massif
  const PA = chainPath(KA);
  // the felt-shaking: a soft camera tremor under the rumble (no magnitude, no eruption)
  const shakeA = (t) => 0.22 * F.clamp((t - tQuake) / 0.15) * Math.exp(-Math.max(0, t - tQuake) * 1.4) * (t > tQuake ? 1 : 0);
  const kamaCam = (t) => { const c = PA(t), a = shakeA(t); if (a > 0.001) { c.heading += a * Math.sin(t * 61) * 0.8; c.tilt += a * Math.sin(t * 47 + 1) * 0.5; } return kit.terrainCamOf(c); };
  // the bigisland legs (from the wide key on) are keyed in section coordinates (the cut plane), converted to orbit keys on first use
  const G = { S: null, SEC: null, PB: null, PR: null, card: null, lou: null, sign: null, tour: null };
  const SK = (t, c) => Object.assign(orbitOf(G.SEC.cam(c)), { t });
  // the cut-away framings: a raised three-quarter view (the island's top surface behind the cut, the face below it), the frame bottom
  // on the wall at -22 km (crust and the Moho in, no flat mantle band); the trench strip at u 127-152 (DEM along the plane)
  // the flexure is ~400 km wide (alphaKm 90), so the dent only reads as a bowl in a wide frame: from {bent} on the frame spans ~150 km
  const C1 = secCam(-8, 100, 24, 12, 30, -22), C1b = secCam(-10, 106, 25, 9, 30, -22), C2 = secCam(-16, 150, 30, 4, 30, -30);
  const C3 = secCam(-14, 150, 30, 2, 30, -30), C3b = secCam(-10, 156, 31, 6, 30, -30);
  const C4 = secCam(70, 150, 30, 100, 30, -30), C4b = secCam(72, 146, 30, 100.5, 30, -30);   // r5 f20001: u 74/tu 103 showed the wall's end at the right edge
  const prep = async () => { if (G.PB) return;
    G.S = await kit.hub.terrain('bigisland', 1, {}); G.SEC = await kit.Section.create(G.S, CUT_PLANE);
    G.PB = chainPath([KA[KA.length - 1],
      Object.assign({}, KA[KA.length - 1], { t: tFeet + 0.4, d: 168, tilt: 73 }),             // s160-s161: the slow push down (the strip pulses)
      SK(643.7, C1),                                                                          // s162: the slice framing
      SK(647.0, Object.assign({}, C1, { u: -9, tu: 10.5 })),
      SK(650.3, C1b),
      SK(652.2, C2),                                                                          // {bent}: wider for the whole sag; the mattress
      SK(656.6, C3),                                                                          // MAUNA LOA, {miles2}
      SK(662.4, C3b),                                                                         // {dent}
      SK(663.9, Object.assign({}, C3b, { u: -6, tu: 9 })),
      SK(665.6, C4),                                                                          // s167: the pan to the rim (the trench)
      SK(666.8, C4b),
      SK(tPay, PAY0)]);                                                                       // payoff's key 0
    // the refill: from payoff's last key through three compositions to the frame-1 composition (CAMS.noocean), then the slow push
    const NO = kit.CAMS.noocean, N0 = orbitOf(NO, tSea0);
    G.PR = chainPath([SK(PAYT1, PAY7),
      SK(699.6, { u: 11.5, d: 82, alt: 14, tu: 12, te: -1900, fov: 26 }),
      orbit(702.6, [-154.25, 18.95], 30, [-154.62, 19.62], -5200, 36),       // A: the trench floods and spreads (east of Hilo)
      orbit(705.2, [-154.5, 18.75], 22, [-154.95, 19.4], -3500, 36),
      orbit(708.8, [-154.95, 18.55], 18, [-155.25, 19.2], -1500, 36),        // B: the lower flanks, the reef steps (Kīlauea's south flank)
      N0,                                                                     // C: the frame-1 composition as the sea reaches 0 m
      Object.assign({}, N0, { t: tEndCut, fov: N0.fov * 0.9 })]);           // s174-s178: the slow push
    if (dbg) { let lo = 1e9, at = 0; for (let u = 100; u <= 185; u += 0.5) { const h = G.SEC.surf(u); if (h < lo) { lo = h; at = u; } }
      api.log(`[ch6] section: trench low ${lo.toFixed(0)} m at u ${at}; C1 te ${C1.te} C2 te ${C2.te} C4 te ${C4.te}; noocean orbit d ${N0.d.toFixed(1)} tilt ${N0.tilt.toFixed(1)} hd ${N0.heading.toFixed(1)}`); }
  };
  // paper and postcards (loaded once, before the shots that use them)
  const PCB = '/ep/ep02/img/postcard_bigisland.jpg', PCL = '/ep/ep02/img/ch6/lake_peigneur_naip.jpg';
  const cards = async () => { if (G.card) return;
    const [hi, lo] = await Promise.all([loadImg(PCB), loadImg(PCL)]);
    G.card = kit.makePostcard(hi, 'HAWAIʻI'); G.lou = makeCard(kit, lo, 'LOUISIANA');
    G.tour = await kit.paper('tourist').catch(e => { api.log('[ch6] tourist cut-out missing: ' + e.message); return null; });
  };
  G.sign = kit.paperProp('sign', { text: 'COMING SOON' });

  // ---------------------------------------------------------------- kama world: felt rings, the COMING SOON sign, the dust puff
  const hmAt = (view, lon, lat) => Math.max(view.S.heightAt(lon, lat), view.level ?? 0);
  const RINGS = [0.15, 0.75, 1.35].map(o => tQuake + o);
  const drawRings = (ctx, view, t) => {
    for (const r0 of RINGS) {
      const p = (t - r0) / 3.2; if (p <= 0 || p >= 1) continue;
      // felt on land only (the ground shakes; no ripples on the sea): each front runs across the seamount, then the island's south
      const R = 3 + 50 * (0.6 * p + 0.4 * E.out(p)), A = 0.9 * F.clamp(p * 8) * Math.pow(1 - p, 1.2); const pts = [];
      for (let a = 0; a <= 360; a += 2) { const ll = offLL(VS, R, a), g = view.S.heightAt(ll[0], ll[1]); pts.push(g > (view.level ?? 0) + 15 ? view.project(ll[0], ll[1], g + 40) : null); }
      ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      for (const [wd, col, aa] of [[px(30), 'rgba(255,226,190,1)', 0.22], [px(13), 'rgba(255,240,215,1)', 0.38], [px(5), 'rgba(255,250,238,1)', 0.92]]) {
        ctx.globalAlpha = A * aa; ctx.strokeStyle = col; ctx.lineWidth = wd; ctx.beginPath(); let on = false;
        for (const q of pts) { if (!q) { on = false; continue; } on ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); on = true; } ctx.stroke(); }
      ctx.restore();
    }
  };
  // the sign: pops on its paper hinge on the sign_pop (in the gap after the line), 35-40 % of the frame height at the pop; wobbles and
  // settles; a tiny dust puff at its base on {fromnow}; the hinge droops a few degrees and it wobbles to a tilt on the creak
  const D_POP = KA[10].d;
  const signDraw = (ctx, view, t, cam) => {
    if (t < tPop - 0.01 || t > 636.95) return null;
    const hm = hmAt(view, VS[0], VS[1]), hPx = 0.35 * H * D_POP / cam.d;
    const pop = F.clamp((t - tPop) / 0.36), wob = 0.07 * Math.exp(-Math.max(0, t - tPop - 0.3) * 2.6) * F.clamp((t - tPop - 0.2) / 0.1);
    const dr = F.clamp((t - (tCreak - 0.08)) / 0.42), droop = E.outBack(dr), wob2 = 0.05 * Math.exp(-Math.max(0, t - tCreak) * 2.4) * (dr > 0 ? 1 : 0);
    const alpha = 1 - F.clamp((t - 636.3) / 0.6);
    return kit.drawCutout(ctx, view, G.sign, { lon: VS[0], lat: VS[1], hm, hPx, pop, t, seed: 3, wobble: wob + wob2, lean: 0.13 * droop, hinge: undefined, alpha, shadowA: 0.32,
      shadow: [hPx * 0.55, -hPx * 0.1] });   // a short soft shadow: the low sun's true one ran off the island as a dark line over the sea (r5 f19062)
  };
  const dustDraw = (ctx, b, t) => {
    const p = (t - (tFromnow + 0.02)) / 0.75; if (!b || p <= 0 || p >= 1) return;
    ctx.save();
    for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI + 0.15 * Math.sin(i * 7.1), side = i % 2 ? 1 : -1;
      const r = b.w * (0.2 + 0.7 * E.out(p)) * (0.7 + 0.3 * Math.sin(i * 3.3)), x = b.x + side * Math.abs(Math.cos(a)) * r, y = b.y - Math.abs(Math.sin(a)) * r * 0.35 - b.h * 0.05 * E.out(p);
      ctx.globalAlpha = 0.7 * (1 - p) * F.clamp(p * 8); ctx.fillStyle = i % 3 ? '#D9CDB4' : '#BFB197';
      ctx.beginPath(); ctx.arc(x, y, b.w * (0.06 + 0.09 * p), 0, 7); ctx.fill(); }
    ctx.restore();
  };

  const kama = kit.terrainShot({ id: 'ch6-kama', t0: ch.t0, t1: tWide, fadeIn: K.XF, region: 'kamaehu', preset: 'today',
    cam: (lt) => kamaCam(ch.t0 + lt), state: (lt) => stA(ch.t0 + lt, PA(ch.t0 + lt).d),
    world(ctx, lt, t, view) {
      if (t > tQuake - 0.05 && t < tQuake + 4.2) drawRings(ctx, view, t);
      const b = signDraw(ctx, view, t, PA(t)); dustDraw(ctx, b, t);
    },
    ui(ctx, lt, t, view) {
      const a = view.project(VS[0], VS[1], hmAt(view, VS[0], VS[1]) + 30); if (!a) return;
      // KAMAʻEHUAKANALOA: 4 frames before {kama}, held through s153 (no second label), out before the felt rings
      if (t > tKama - 0.02 && t < 617.75) ui.label(ctx, 'KAMAʻEHUAKANALOA', a[0], a[1], { t, p: F.clamp((t - tKama) / 0.25), alpha: 1 - F.clamp((t - 617.4) / 0.3), dist: 64 });
      // LŌʻIHI for 2 s, below (the new name came first)
      if (t > tLoihi - 0.02 && t < tLoihi + 2.3) ui.label(ctx, 'LŌʻIHI', a[0], a[1], { t, p: F.clamp((t - tLoihi) / 0.25), alpha: 1 - F.clamp((t - (tLoihi + 2.0)) / 0.3), dist: 64, order: ['below', 'right', 'left'] });
    } });
  scenes.push(kama);

  // ================================================================ MASSIF: the drained Big Island, the trench strip (bigisland, uncut)
  const camB = (t) => kit.terrainCamOf(t < tWide ? PA(t) : G.PB(t));
  const massif = ready(kit.terrainShot({ id: 'ch6-massif', t0: tMassif0, t1: tWipe1, fadeIn: tWide - tMassif0, region: 'bigisland', preset: 'today',
    cam: (lt) => camB(tMassif0 + lt), state: (lt) => { const t = tMassif0 + lt; return stA(t, (t < tWide ? PA(t) : G.PB(t)).d); } }), prep);
  scenes.push(massif);

  // ================================================================ CUT: the slice, the sag, the dent (bigisland cut-away)
  const sagOf = (t) => F.lerp(0.35, 1, pr(t, tBent, tBent + 1.5));
  const cutState = (t) => Object.assign({}, SECTION, { sag: sagOf(t), floorLine: pr(t, tDent - 0.1, tDent + 0.35), trenchA: 0.85 + 0.15 * gauss(t, tEdge + 0.08, 0.25),
    edgeA: 1, waterTop: 0, waterA: 0, waterBot: SECTION.oldFloor, everest: { rise: 0, base: BASE } });
  const MATT = { x: W - px(96) - W * 0.44, y: px(96), w: W * 0.44, h: H * 0.36 }, tM0 = 651.85, tM1 = 653.95;
  const cut = ready(blurred(kit.cutawayShot({ id: 'ch6-cut', t0: tWipe0, t1: tPay, region: 'bigisland', vex: 1, preset: 'drained',
    cam: (lt) => { const c = kit.terrainCamOf(G.PB(tWipe0 + lt)); delete c.near; delete c.far; return c; },
    // payoff's state at T0: WATER_FILM, edgeGlow 0.6, nearAmt 0 (the trench strip glow and the move water hand over during the move)
    state: (lt) => { const t = tWipe0 + lt, s = stA(t, G.PB(t).d), k = pr(t, 666.95, tPay - 0.1);
      return { sun: SUN(t), look: 'day', waterCols: s.waterCols.map((c, j) => c.map((v, q) => F.lerp(v, WATER_FILM[j][q], k))),
        set: { edgeGlow: F.lerp(s.set.edgeGlow ?? 0.6, 0.6, k), nearAmt: 0 } }; },
    cut: { plane: CUT_PLANE, everest: EVEREST, state: (lt) => cutState(tWipe0 + lt) }, level: -5470,
    ui(ctx, lt, t, v) {
      const S = v.sec; if (!S) return;
      const P = (u, e, f = 0.05) => S.project(u, e, f);
      const runs = (pts) => { const out = []; let cur = []; for (const q of pts) { if (!q) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); } if (cur.length > 1) out.push(cur); return out; };
      // the dented base line under Mauna Loa: drawn out from the summit column on {miles2}, glows on {dent}; to the trench rim and back
      // to payoff's -70..70 km for the hand-off (payoff's width and alpha at T0)
      const dp = pr(t, tMiles - 0.05, tMiles + 0.7, E.out);
      if (dp > 0) {
        const glow = gauss(t, tDent + 0.35, 0.45), reach = F.lerp(70, 150, pr(t, 663.6, 665.0) * (1 - pr(t, 666.9, 667.7)));
        const r = reach * dp, of = SECTION.oldFloor;
        // s166: the dent as a shape: the sliver between the old flat floor (the section's white floorLine) and the dented base fills
        // in on {dent} (true scale: at VE 1 the two lines alone read as near-parallel, r5 f19893); gone before payoff's T0
        const fA = pr(t, tDent - 0.1, tDent + 0.35) * (1 - pr(t, 666.6, 667.3));
        if (fA > 0) { const top = [], bot = [];
          for (let u = -r; u <= r; u += 1) { const c = S.crustTop(u); if (c >= of - 5) continue; top.push(P(u, of)); bot.push(P(u, c)); }
          if (top.length > 2 && top.every(Boolean) && bot.every(Boolean)) {
            ctx.save(); ctx.globalAlpha = fA * (0.24 + 0.2 * glow); ctx.fillStyle = PAL.yellow; ctx.beginPath();
            top.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); for (let i = bot.length - 1; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]);
            ctx.closePath(); ctx.fill(); ctx.restore(); } }
        // one line drawn out both ways from the summit column (two lines left a notch where they met, r5 f19893)
        const pts = []; for (let u = -r; u <= r; u += 1) pts.push(P(u, S.crustTop(u)));
        ui.line(ctx, runs(pts), { color: PAL.yellow, width: 9 + 3 * glow, alpha: 0.85 + 0.15 * glow });
      }
      // s167: on {edge} the trench at the rim of the dent lights cyan on the cut face (the ch3 strip's colour) and a ring opens from it
      const eA = env(t, tEdge - 0.1, tEdge + 1.2, 0.12, 0.45) * (1 - pr(t, 666.9, 667.4));
      if (eA > 0) {
        let ut = 129, lo = 1e9; for (let u = 100; u <= 165; u += 0.5) { const sv = S.surf(u); if (sv < lo) { lo = sv; ut = u; } }
        const tr = []; for (let u = 100; u <= 165; u += 0.5) tr.push(S.surf(u) < -5470 ? P(u, -5470) : null);
        ui.line(ctx, runs(tr), { color: PAL.cyan, width: 10, alpha: eA, glow: PAL.cyan, p: 1 });
        const c = P(ut, -5470), k = F.clamp((t - tEdge) / 0.9);
        if (c && k > 0 && k < 1) { ctx.save(); ctx.globalAlpha = eA * (1 - k) * 0.9; ctx.strokeStyle = PAL.cyan; ctx.lineWidth = px(5);
          ctx.beginPath(); ctx.ellipse(c[0], c[1], px(24 + 150 * E.out(k)), px(10 + 60 * E.out(k)), 0, 0, 7); ctx.stroke(); ctx.restore(); }
      }
      // the old sea-level line (payoff's, faint) fades in during the move so nothing pops at T0
      const sA = pr(t, 667.15, tPay - 0.05);
      if (sA > 0) { const sea = []; for (let u = -60; u <= 90; u += 5) sea.push(P(u, 0)); ui.line(ctx, runs(sea), { color: '#FFFFFF', width: 6, alpha: 0.35 * sA, glow: PAL.cyan, p: 1 }); }
      // payoff's avoid boxes (its bar column and the summit), then MAUNA LOA from {loa2} with payoff's options (held into payoff)
      const a0 = P(UBAR, BASE, 0.3), top = P(UBAR, ML.summit, 0.3); if (a0 && top) ui.avoid(ui.boxOf([a0, top], px(36)));
      const sum = P(0, ML.summit, 0); if (sum) ui.avoid({ x: sum[0] - px(40), y: sum[1] - px(30), w: px(80), h: px(60) });
      if (sum && t > tLoa2 - 0.02) ui.label(ctx, 'MAUNA LOA', sum[0], sum[1], { dist: 60, accent: PAL.hero, t, p: F.clamp((t - tLoa2) / 0.25), order: ['above', 'above-left', 'left', 'above-right', 'right'] });
      // s164: the mattress inset (2.1 s, dissolves in and straight back out)
      const mA = env(t, tM0, tM1, 0.2, 0.25); if (mA > 0) drawMattress(ctx, MATT, t, tBall, mA, px);
    } }), 666.85, tPay, 6, 0.5), prep);
  // the wipe: the cut-away is revealed behind the blade as it runs along the cut line (left to right, mid-frame on slice_reveal)
  const wipeX = (t) => W * E.inOut(F.clamp((t - tWipe0) / (tWipe1 - tWipe0)));
  { const inner = cut.draw.bind(cut);
    cut.draw = async function (ctx, lt, t, a) { if (t >= tWipe1) return inner(ctx, lt, t, a);
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, Math.max(1, wipeX(t)), H); ctx.clip(); await inner(ctx, lt, t, a); ctx.restore(); }; }
  scenes.push(cut);
  // the blade: a white scoring line traced along the surface on the cut plane up to the wipe edge, a bright tip; fades after the cut
  const blade = (ctx, xe, left, A, tipOn) => {
    if (!G.SEC || A <= 0.01) return; const S = G.SEC, x1 = xe + (left ? px(8) : -px(8));
    const pts = []; for (let u = -150; u <= 185; u += 0.5) { const q = S.project(u, Math.max(S.surf(u), -5470) + 60, 0); if (q && (left ? q[0] <= x1 : q[0] >= x1)) pts.push(q); }
    if (pts.length < 2) return;
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    for (const [wd, col, aa] of [[px(16), 'rgba(160,240,255,1)', 0.25], [px(5), '#FFFFFF', 1]]) {
      ctx.globalAlpha = A * aa; ctx.strokeStyle = col; ctx.lineWidth = wd; ctx.beginPath(); pts.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); }
    const tip = left ? pts[pts.length - 1] : pts[0];
    if (tipOn) { const g = ctx.createRadialGradient(tip[0], tip[1], 0, tip[0], tip[1], px(46)); g.addColorStop(0, 'rgba(255,255,255,0.95)'); g.addColorStop(0.35, 'rgba(190,245,255,0.5)'); g.addColorStop(1, 'rgba(190,245,255,0)');
      ctx.globalAlpha = A; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(tip[0], tip[1], px(46), 0, 7); ctx.fill(); }
    ctx.restore();
  };
  scenes.push({ id: 'ch6-blade', t0: tWipe0 - 0.12, t1: tWipe1 + 0.5, layer: 40, draw(ctx, lt, t) {
    blade(ctx, wipeX(t), true, F.clamp((t - (tWipe0 - 0.12)) / 0.12) * (1 - F.clamp((t - tWipe1) / 0.45)), t < tWipe1); } });

  // ================================================================ PAYOFF (payoff.js): T0 = s168's first word (the move to its key 0 lands there)
  const pay = buildPayoff(api, kit, scenes, { t0: tPay });

  // ================================================================ REFILL: the cut closes, the sea returns to the frame-1 composition
  const evDown = (t) => 1 - pr(t, 698.0, 698.9, E.in);
  const tSee16 = T('see') + 1.6;
  const refillCut = ready(kit.cutawayShot({ id: 'ch6-refill-cut', t0: PAYT1 - 0.5, t1: 699.6, fadeIn: 0.5, region: 'bigisland', vex: 1, preset: 'drained',
    state: { sun: [200, 24], look: 'day' },
    cam: (lt) => { const t = PAYT1 - 0.5 + lt;
      if (t < PAYT1) { const k = E.inOut(F.clamp((t - tSee16) / (PAYT1 - tSee16))); return G.SEC.cam(Object.fromEntries(Object.keys(PAY6).map(q => [q, F.lerp(PAY6[q], PAY7[q], k)]))); }
      const c = kit.terrainCamOf(G.PR(t)); delete c.near; delete c.far; return c; },
    cut: { plane: CUT_PLANE, everest: EVEREST, state: (lt) => { const t = PAYT1 - 0.5 + lt;
      return Object.assign({}, SECTION, { sag: 1, floorLine: 1 - pr(t, 698.2, 698.9), trenchA: 0.85, edgeA: 1, waterTop: 0, waterA: 0.55 * (1 - pr(t, 698.0, 698.9)), waterBot: SECTION.oldFloor,
        everest: { rise: evDown(t), base: BASE } }); } },
    level: (lt) => LEVEL(PAYT1 - 0.5 + lt) }), prep);
  scenes.push(refillCut);
  const NOO = kit.PRESETS.noocean;
  const stR = (t, d) => {
    const lv = LEVEL(t), dr = F.clamp(-lv / 900), q = 0.5 * pr(t, 707.5, tSea0);   // half the NO OCEAN grade: photoreal at 0 m
    const a = mixState('today', 'drained', dr); a.sun = SUN(t); a.waterCols = waterAt(d); a.set.oldLine = F.clamp(-lv / 300); a.set.lineCol = LINE.cream;
    const st = mixState(a, Object.assign({}, NOO, { level: lv, sun: SUN(t), waterCols: waterAt(d) }), q);
    st.level = lv; st.sun = SUN(t); st.waterCols = waterAt(d); st.set.fresMax = 0.4;
    return st;
  };
  const shiftC = (c, t) => { const q = pr(t, 709.0, tSea0); c.shiftX = kit.CAMS.noocean.shiftX * q; c.shiftY = kit.CAMS.noocean.shiftY * q; return c; };
  // the ending props: the postcard drop (lands on postcard_drop), the dent ghost on {planet}, the tourist on {lookdown3}, the flip on the tap
  const ghost = (ctx, t) => {
    const A = env(t, tPlanet - 0.05, tPlanet + 1.55, 0.25, 0.45); if (A <= 0 || !G.SEC) return;
    // the payoff's dent seen through the island (an x-ray of the same plane, VE 1), drawn exactly as the cut leg showed it on {dent}:
    // the old flat floor in white, the dented base in yellow and the sliver between them filled yellow (r6: a tan pile fill over the
    // island read as a grey band, and two bare lines read as straight lines)
    const S = G.SEC, of = SECTION.oldFloor, crust = [], flo = [];
    for (let u = -200; u <= 200; u += 2) { const c = of - SECTION.sagM * flexOf(Math.abs(u)); crust.push(S.project(u, c, 0)); flo.push(S.project(u, Math.max(of, c), 0)); }
    if (crust.some(v => !v) || flo.some(v => !v)) return;
    const p = F.clamp((t - (tPlanet - 0.05)) / 0.4);
    ctx.save(); ctx.globalAlpha = A * 0.38 * p; ctx.fillStyle = PAL.yellow; ctx.beginPath();
    flo.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); for (let i = crust.length - 1; i >= 0; i--) ctx.lineTo(crust[i][0], crust[i][1]); ctx.closePath(); ctx.fill(); ctx.restore();
    ui.line(ctx, [flo], { color: '#FFFFFF', width: 5, alpha: 0.7 * A });
    ui.line(ctx, [crust], { color: PAL.yellow, width: 9, alpha: 0.95 * A, p });
  };
  const flipP = (t) => F.clamp((t - (tFlip - 0.43)) / 0.43);
  const ending = (ctx, t, view) => {
    if (!G.card || t < tGiant - 0.1) return;
    ghost(ctx, t);
    const pd = F.clamp((t - (tGiant + 0.08)) / (tDrop - (tGiant + 0.08)));
    const fp = flipP(t), phi = Math.PI * E.inOut(fp), hop = 4000 * Math.sin(Math.PI * fp) + (fp >= 1 ? 900 * Math.exp(-(t - tFlip) * 9) * Math.abs(Math.sin((t - tFlip) * 22)) : 0);
    let q;
    if (fp <= 0) q = kit.drawPostcard(ctx, view, G.card, Object.assign({}, PC_HI, { p: pd, lift: 0.1, alpha: 1 }));
    else q = drawFlipCard(kit, ctx, view, G.card, G.lou, Object.assign({}, PC_HI, { phi, hop, lift: 0.1, alpha: 1 }));
    // the paper tourist (appearance 4 of 4): pops up on the card's near edge on the paper tap ({lookdown3}), bows over the edge to look
    // down, his hat drops off and tumbles down the flank; he folds flat before the flip
    if (G.tour && q && t > tLook - 0.02 && t < tHole - 0.25) {
      const bx = q[3][0] + (q[2][0] - q[3][0]) * 0.62, by = q[3][1] + (q[2][1] - q[3][1]) * 0.62;
      const pop = F.clamp((t - tLook) / 0.34), out = F.clamp((t - (tHole - 0.8)) / 0.4);
      const bow = pr(t, tLook + 0.35, tLook + 0.75, E.outBack) * (1 - pr(t, 728.7, 729.2)), hp = F.clamp((t - (tLook + 0.62)) / 0.95);
      const hat = { off: [px(90) * hp, 0.55 * H * E.in(hp)], rot: 3.6 * hp, alpha: 1 - F.clamp((hp - 0.8) / 0.2) };
      const o = { x: bx, y: by, hPx: 0.34 * H, t, seed: 4, wobble: 0.015 * (1 - bow), squash: 0.17 * bow, lean: 0.06 * bow, shadow: [px(40), px(10)], shadowA: 0.25, parts: { hat } };
      if (out > 0) o.hinge = E.inOut(out); else o.pop = pop;
      kit.drawCutout(ctx, view, G.tour, o);
    }
  };
  const refill = ready(kit.terrainShot({ id: 'ch6-refill', t0: tBack, t1: tEndCut, region: 'bigisland', preset: 'today',
    cam: (lt) => { const t = tBack + lt; return shiftC(kit.terrainCamOf(G.PR(t)), t); },
    state: (lt) => { const t = tBack + lt; return stR(t, G.PR(t).d); },
    async world(ctx, lt, t, view) { await cards(); ending(ctx, t, view); } }), prep);
  const tClose1 = tBack + 0.47, closeX = (t) => W * (1 - E.inOut(F.clamp((t - tBack) / (tClose1 - tBack))));
  { const inner = refill.draw.bind(refill);
    refill.draw = async function (ctx, lt, t, a) { if (t >= tClose1) return inner(ctx, lt, t, a);
      ctx.save(); ctx.beginPath(); ctx.rect(closeX(t), 0, W, H); ctx.clip(); await inner(ctx, lt, t, a); ctx.restore(); }; }
  scenes.push(refill);
  scenes.push({ id: 'ch6-blade2', t0: tBack - 0.05, t1: tClose1 + 0.45, layer: 40, draw(ctx, lt, t) {
    blade(ctx, closeX(t), false, F.clamp((t - (tBack - 0.05)) / 0.1) * (1 - F.clamp((t - tClose1) / 0.4)), t < tClose1); } });

  // ================================================================ END SCREEN background: a slow orbit over the refilled island (nothing drawn)
  const EK = [{ t: tEndCut, lon: -155.42, lat: 19.62, h: 0, d: 165, tilt: 60, heading: 328, fov: 38 }, { t: ch.t1, lon: -155.45, lat: 19.62, h: 0, d: 148, tilt: 61, heading: 343, fov: 38 }];
  const PE = (t) => { const p = (t - EK[0].t) / (EK[1].t - EK[0].t); const o = {}; for (const k of ['lon', 'lat', 'h', 'tilt', 'heading', 'fov']) o[k] = F.lerp(EK[0][k], EK[1][k], p); o.d = Math.exp(F.lerp(Math.log(EK[0].d), Math.log(EK[1].d), p)); return o; };
  scenes.push(kit.terrainShot({ id: 'ch6-end', t0: tEndCut, t1: ch.t1, region: 'bigisland', preset: 'today',
    cam: (lt) => kit.terrainCamOf(PE(tEndCut + lt)),
    // the refill's own grade and light (r5: a gold look here dropped the luma from 136 to 85 on the cut)
    state: (lt) => { const st = stR(tEndCut, PE(tEndCut + lt).d); st.set.foamAmt = 1; return st; } }));

  // ================================================================ sound cues (mix_ep02_v1.json names and gains; the mix is already built)
  [[602.86, 'whoosh_big', -14], [tPing, 'sonar_ping', -17], [tQuake, 'rumble_quake', -17], [tPop, 'sign_pop', -16], [tCreak, 'card_creak', -18],
    [tDrain2, 'drain_start', -12], [639.52, 'drain_gurgle_tail', -14.9], [tFeet, 'sonar_ping', -20], [643.77, 'slice_reveal', -14], [648.91, 'tension_groan', -14],
    [tBall, 'ball_mattress', -18], [tEdge, 'sonar_resolve', -16], [667.23, 'deep_sink', -14], [699.13, 'refill_inrush', -12], [700.53, 'water_rise_long', -11],
    [tDrop, 'postcard_drop', -16], [726.40, 'paper_tap', -21.2], [731.37, 'paper_tap', -20]].forEach(c => api.cue(...c));

  // ================================================================ layer-0 contiguity check (gaps would show navy placeholders)
  const base = scenes.filter(s => (s.layer || 0) === 0 && s.t0 < ch.t1x && s.t1 > ch.t0 && /^(ch6-|payoff)/.test(s.id)).sort((a, b) => a.t0 - b.t0);
  let cov = ch.t0; const gaps = []; for (const s of base) { if (s.t0 > cov + 1e-3) gaps.push(`${cov.toFixed(2)}-${s.t0.toFixed(2)}`); cov = Math.max(cov, s.t1); }
  if (cov < ch.t1x - 1e-3) gaps.push(`${cov.toFixed(2)}-${ch.t1x.toFixed(2)}`);
  api.log(`[ch6] ${base.length} base shots ${ch.t0.toFixed(2)}-${ch.t1x.toFixed(2)}${gaps.length ? ' GAPS ' + gaps.join(', ') : ', contiguous'}; payoff ${pay.t0.toFixed(2)}-${pay.t1.toFixed(2)}; end cut ${tEndCut.toFixed(2)}`);
}
