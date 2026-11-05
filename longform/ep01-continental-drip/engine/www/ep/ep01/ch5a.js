// Chapter 5a (s072–s081), [C.t0, C.t1): Gondwana reassembles around Antarctica (the keypiece), Bacon callback, the drips point
// at it; the clock runs forward (Africa/Antarctica crack, the South Atlantic unzips, everyone moves out while the Explorer keeps
// the house, India sprints and slams into Asia); the geologist's explanation as a paper textbook figure; back to today: the
// tips' real paths converge near Antarctica and turn into scars.
// Everything is a pure function of time. Paleo sequences: simplified (GPlates/EarthByte Müller 2019 via paleo/*.json).
import * as F from '../../lib/fx.js';
import * as THREE from '../../three.module.min.js';
import { camAt } from '../../lib/shots.js';
import { dripArrow } from '../../lib/beats.js';
import { Paleo, PAIRS, TRACKED, v3, ll, apply, cross, dot, norm, circleLL, gcLL, projRuns, strokeRuns, droplet, HERO, ANTC } from './ch5a_paleo.js';
import { EXCL, ANT } from './ch5a_data.js';
const { PAL, prog, env, clamp, lerp, E } = F;
const D = Math.PI / 180;

// monotone cubic interpolation through [[t, v], ...]
function mono(keys) {
  const n = keys.length, xs = keys.map(k => k[0]), ys = keys.map(k => k[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) { const tau = 3 / Math.sqrt(s); m[i] = tau * a * d[i]; m[i + 1] = tau * b * d[i]; }
  }
  return (t) => {
    if (t <= xs[0]) return ys[0]; if (t >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (t > xs[i + 1]) i++;
    const h = xs[i + 1] - xs[i], s = (t - xs[i]) / h, s2 = s * s, s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * ys[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * ys[i + 1] + (s3 - s2) * h * m[i + 1];
  };
}
const angV = (a, b) => Math.acos(clamp(dot(a, b), -1, 1)) / D;
const bump = (t, a, b, c) => t < a || t > c ? 0 : t < b ? E.inOut((t - a) / (b - a)) : 1 - E.inOut((t - b) / (c - b));
const hash = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

export async function build(api, C) {
  const W = api.W, H = api.H;
  const g = await api.globe();
  await Promise.all(['400 100px "Bebas Neue"', '700 40px "Barlow Condensed"', '800 100px "Inter"', '600 40px "Inter"'].map(f => document.fonts.load(f)));
  const IMG = p => 'ep/ep01/img/' + p;
  await api.loadImages([IMG('bacon.jpg'), IMG('ch5a_bacon_n246.jpg')]);
  const tracks = await api.loadJSON('paleo/tracks.json');
  const OW = +(api.Q.ow || 2048);
  const P2 = new Paleo(api, tracks, OW, OW / 2);      // whole-globe views
  const P4 = new Paleo(api, tracks, 4096, 2048);      // close / tilted views
  const coast0 = await P2.load(0);
  const MINE = { id: 'ch5a' };
  const cue = (t, n, db) => api.cue(t, n, db);
  const scenes = [];
  const add = (a, b, draw, o = {}) => scenes.push({ t0: a, t1: b, layer: o.layer || 0, fadeIn: o.fadeIn || 0, fadeOut: o.fadeOut || 0, id: 'ch5a', draw: (ctx, lt, t) => draw(ctx, t, lt) });

  // ---------------------------------------------------------------- markers & cut points (all follow the voice)
  const M = {};
  for (const k of ['r_sam', 'r_afr', 'r_ind', 'r_aus', 'gond', 'ant', 'remember', 'point', 'whole', 'fwd', 'afant', 'zip', 'split', 'firstt', 'seam', 'snap2',
    'leave', 'stay', 'house', 'sprint', 'afaus', 'driving', 'slam', 'best', 'together', 'ant2', 'apart', 'aim', 'scar']) M[k] = C.T(k);
  const SEG = id => C.seg(id);
  const wordAt = (seg, re, last) => { const ws = C.words(seg).filter(w => re.test(w.w)); const w = last ? ws[ws.length - 1] : ws[0]; return w ? w.start : SEG(seg).start; };
  const tCracks = wordAt('s075', /^cracks/i), tUpTo = wordAt('s078', /^up$/i), tBig = wordAt('s081', /^big/i), tKey = wordAt('s073', /^keypiece/i);
  const tStart = C.t0, tEnd = C.t1;
  const tC = M.ant - 0.16, tD = M.remember - 0.1, tE = M.point - 0.12, tF = M.fwd - 0.15, tG = SEG('s076').start - 0.14, tH = M.firstt - 0.22;
  const tI = SEG('s077').start - 0.12, tJ = M.leave - 0.34, tK = SEG('s078').start - 0.09, tL = M.afaus - 0.13, tM = M.driving - 0.19;
  const tN = SEG('s079').start - 0.1, tO = SEG('s080').start - 0.16, tP = SEG('s081').start - 0.11;

  // ---------------------------------------------------------------- geometry prepared once
  const at = (name, T) => P2.at(name, T);                     // [lat, lon] of a track point at T Ma
  const SP180 = at('south_pole', 180);                         // heart of Antarctica at 180 Ma (ring centre)
  const TIPN = ['cape_horn', 'cape_agulhas', 'kanyakumari'], TIPC = ['samerica', 'africa', 'india'];
  const GCv = v3(-63, 16);                                    // assembled-Gondwana view centre (Antarctica slightly below centre)
  const GC = ll(GCv);                                          // Gondwana centre at 180 Ma
  const RING_R = 7.5;
  const ring180 = circleLL(SP180[0], SP180[1], RING_R, 90);
  // Antarctica (present-day points of its coast_000 polygons)
  const antPts = []; for (const j of ANT[0]) for (const [lo, la] of coast0[j]) antPts.push(v3(la, lo));
  const ringOf = c => P2.R0[c][P2.main[c]];
  // contact seams between two plates at time Tc: pairs (a_i on A, b_i on B) ordered along A's coast
  function contact(A, Bn, Bpts, Tc, thr, maxN = 64, gapTol = 60) {
    const RA = P2.rot(A, Tc), RB = P2.rot(Bn, Tc), ring = ringOf(A), n = ring.length;
    const ap = ring.map(p => apply(RA, p)), bp = Bpts.map(p => apply(RB, p)), ct = Math.cos(thr * D);
    const near = ap.map(a => { let best = -2, bj = -1; for (let j = 0; j < bp.length; j++) { const d = a[0] * bp[j][0] + a[1] * bp[j][1] + a[2] * bp[j][2]; if (d > best) { best = d; bj = j; } } return best > ct ? bj : -1; });
    let s0 = near.findIndex(v => v < 0); if (s0 < 0) s0 = 0;
    const runs = []; let cur = null, gap = 0;
    for (let k = 1; k <= n; k++) {
      const i = (s0 + k) % n;
      if (near[i] >= 0) { if (!cur) cur = []; cur.push(i); gap = 0; } else if (cur) { gap++; if (gap > gapTol) { runs.push(cur); cur = null; } }
    }
    if (cur) runs.push(cur);
    runs.sort((a, b) => b.length - a.length);
    const run = runs[0] || [];
    const step = Math.max(1, Math.ceil(run.length / maxN));
    const idx = run.filter((_, k) => k % step === 0);
    const a0 = idx.map(i => ring[i]), b0 = idx.map(i => Bpts[near[i]]);
    const g0 = idx.map((i, k) => angV(ap[i], bp[near[i]]));
    return { A, B: Bn, a0, b0, g0 };
  }
  const afrPts = ringOf('africa');
  const SEAMS = {
    afant: contact('africa', 'antarctica', antPts, 178, 2.5),
    indant: contact('india', 'antarctica', antPts, 178, 2.5),
    ausant: contact('australia', 'antarctica', antPts, 178, 2.5),
    satl: contact('samerica', 'africa', afrPts, 150, 1.8, 72, 120),
  };
  { const s = SEAMS.satl; if (ll(s.a0[0])[0] > ll(s.a0[s.a0.length - 1])[0]) { s.a0.reverse(); s.b0.reverse(); s.g0.reverse(); } } // south -> north
  // seam state at time T: rotated edges, per-pair opening 0..1, midpoints [lat, lon]
  function seamAt(P, s, T, po = {}) {
    const RA = P.plateRot(s.A, T, po), RB = s.B === 'antarctica' ? P.rot('antarctica', T) : P.plateRot(s.B, T, po);
    const A = s.a0.map(p => apply(RA, p)), B = s.b0.map(p => apply(RB, p));
    const open = A.map((a, i) => clamp((angV(a, B[i]) - s.g0[i] - 0.18) / 0.45));
    const mid = A.map((a, i) => ll(norm([a[0] + B[i][0], a[1] + B[i][1], a[2] + B[i][2]])));
    return { A, B, open, mid };
  }
  // the South Atlantic: last seam snaps at T_SNAP (all pairs open)
  let T_SNAP = 112, T_OPEN0 = 145, T_FIRST = null;
  for (let T = 150; T >= 95; T -= 0.25) { const st = seamAt(P2, SEAMS.satl, T); if (T_FIRST == null && st.open[0] > 0.5) T_FIRST = T; if (st.open.some(v => v > 0.5) && T_OPEN0 === 145) T_OPEN0 = T; if (st.open.every(v => v > 0.6)) { T_SNAP = T; break; } }
  T_SNAP = clamp(T_SNAP, 100, 121);
  api.log(`ch5a: T_OPEN0 ${T_OPEN0} T_SNAP ${T_SNAP} seams ${Object.entries(SEAMS).map(([k, s]) => k + ':' + s.a0.length + '[' + ll(s.a0[0]).map(v => v.toFixed(1)) + ' -> ' + ll(s.a0[s.a0.length - 1]).map(v => v.toFixed(1)) + ']').join(' ')}`);

  // ---------------------------------------------------------------- time schedule (Ma) for the forward run
  const Tfwd = mono([[M.fwd - 0.05, 180], [M.afant, 158], [tG, 148], [M.zip + 0.15, T_FIRST ?? 142], [M.split, 139], [M.firstt, Math.max(131, T_SNAP + 9)],
    [M.seam, Math.max(125.5, T_SNAP + 4.5)], [M.snap2, T_SNAP], [tI, T_SNAP - 3], [tJ, T_SNAP - 7.5], [tK, 80], [tL, 66], [tM, 56], [M.slam, 44], [tN + 0.4, 38]]);

  // ---------------------------------------------------------------- shared drawing helpers
  const PLOOK = { flatBase: 1, ovAlpha: 1, ovMul: 1, nightAmt: 0, relief: 0, dim: 0, desat: 0, exposure: 1.25, ambient: 0.12, specAmt: 0.16, rimAmt: 0.35 };
  const RLOOK = { flatBase: 0, ovAlpha: 0, ovMul: 0, nightAmt: 1, relief: 0.8, dim: 0, desat: 0.12, exposure: 1.25, ambient: 0.10, specAmt: 0.5, rimAmt: 0.35 };
  const mixLook = (a, b, k) => { const o = {}; for (const key in a) o[key] = lerp(a[key], b[key], k); return o; };
  const camK = (keys, drift = 0.25) => { const k0 = keys[0].t; const ks = keys.map(k => Object.assign({}, k, { t: k.t - k0 })); return t => camAt(ks, t - k0, drift); };
  async function prep() {
    if (api._patchOwner !== MINE) { await g.setPatch(null); api._patchOwner = MINE; }
    g.u.tint.value.set(1, 1, 1);
  }
  async function paleo(P, T, po) {
    const changed = await P.draw(T, po);
    if (g.u.ovTex.value.image !== P.cv) {
      g.setOverlay(P.cv); const tx = g.u.ovTex.value; tx.generateMipmaps = false; tx.minFilter = THREE.LinearFilter; tx.anisotropy = 1; tx.needsUpdate = true; api._ovOwner = P;
    } else if (changed) g.refreshOverlay();
  }
  const globe = (ctx, cam, look, shake) => {
    const st = Object.assign({}, cam, cam.keepSun ? {} : { sunAz: -15, sunEl: 26 }); if (shake) st.lookOffset = shake;
    api.drawGlobe(ctx, st, look);
  };
  const shakeAt = (t, th, amp = 0.012, dur = 0.5) => { if (t < th || t > th + dur) return null; const k = Math.exp(-(t - th) * 7); return [Math.sin(t * 91) * amp * k, Math.cos(t * 73) * amp * k]; };
  const proj = (lat, lon, h = 0) => g.project(lat, lon, h);
  const plateCen = (P, c, T, po = {}) => ll(apply(P.plateRot(c, T, po), v3(...P.cen0(c))));
  // "MILLION YEARS AGO · SIMPLIFIED" chip (same placement as chapter 4)
  const chip = (ctx, Ma, a, o = {}) => {
    if (a <= 0.003) return;
    const today = o.today || 0, na = a * (1 - today);
    if (o.ink) {
      if (na > 0.003) {
        F.text(ctx, String(Math.round(Ma)), 120, 186, { size: 96, fam: F.FAM.body, weight: 800, color: '#2B2520', alpha: na, shadow: false });
        F.text(ctx, 'MILLION YEARS AGO · SIMPLIFIED', 124, 236, { size: 28, fam: F.FAM.label, weight: 700, tracking: 0.16, color: 'rgba(43,37,32,0.78)', alpha: na, shadow: false });
      }
      return;
    }
    { const gr = ctx.createRadialGradient(300, 175, 20, 300, 175, 330); gr.addColorStop(0, `rgba(3,5,10,${0.55 * a})`); gr.addColorStop(1, 'rgba(3,5,10,0)'); ctx.save(); ctx.fillStyle = gr; ctx.fillRect(-40, -160, 700, 700); ctx.restore(); }
    if (na > 0.003) {
      F.counter(ctx, Ma, Ma, 1, 120, 186, { size: 96, align: 'left', alpha: na, format: v => String(Math.round(v)) });
      F.text(ctx, 'MILLION YEARS AGO · SIMPLIFIED', 124, 236, { size: 28, fam: F.FAM.label, weight: 700, tracking: 0.16, color: PAL.sub, alpha: na });
    }
    if (today > 0.003) F.text(ctx, 'TODAY', 120, 186, { size: 104, fam: F.FAM.head, weight: 400, tracking: 0.03, color: PAL.yellow, alpha: a * today });
  };
  // pill that pops (scale overshoot) at a0 and fades at a1
  const pillAt = (ctx, s, x, y, t, a0, a1, o = {}) => {
    if (t < a0 - 0.02 || (a1 != null && t > a1)) return null;
    const a = a1 != null ? env(t, a0, a1, 0.2, 0.3) : prog(t, a0, a0 + 0.2); if (a <= 0) return null;
    const pop = lerp(0.8, 1, E.outBack(prog(t, a0, a0 + 0.3)));
    ctx.save(); ctx.translate(x, y); ctx.scale(pop, pop);
    const lead = o.leader ? [(o.leader[0] - x) / pop, (o.leader[1] - y) / pop] : null;
    const r = F.pill(ctx, s, 0, 0, Object.assign({ anchor: 'center', size: 40, alpha: a }, o, { leader: lead }));
    ctx.restore(); return r;
  };
  // yellow target ring (with ripples) at the heart of Antarctica
  const drawRing = (ctx, t, a, t0r, o = {}) => {
    if (a <= 0.003) return;
    const runs = projRuns(g, o.pts || ring180);
    strokeRuns(ctx, runs, { color: PAL.yellow, width: o.width || 5, glow: true, glowColor: 'rgba(255,210,63,0.14)', glowColor2: 'rgba(255,210,63,0.3)', under: 'rgba(30,20,0,0.6)', alpha: a });
    if (t0r != null && t > t0r) for (let k = 0; k < 2; k++) {
      const ph = ((t - t0r) * 0.75 + k * 0.5) % 1;
      const rr = circleLL(SP180[0], SP180[1], RING_R * (1 + ph * 1.6), 72);
      strokeRuns(ctx, projRuns(g, rr), { color: PAL.yellow, width: 3.5, under: 'rgba(30,20,0,0.35)', alpha: a * (1 - ph) * 0.9 });
    }
    const c = proj(SP180[0], SP180[1]); if (c.visible) F.dot(ctx, c.x, c.y, { r: 6, color: PAL.yellow });
  };
  // white crack polyline (jagged) through seam midpoints, drawn on
  const crackPts = (mids, seed) => mids.map((m, i) => { const q = proj(m[0], m[1]); return q.visible ? [q.x + (hash(i + seed) - 0.5) * 9, q.y + (hash(i * 3 + seed) - 0.5) * 9] : null; }).filter(Boolean);
  // trail of a track point between two times (Ma) -> [[lat, lon]]
  const trail = (name, Ta, Tb, step = 0.5) => { const out = []; const n = Math.max(2, Math.ceil(Math.abs(Tb - Ta) / step)); for (let i = 0; i <= n; i++) out.push(at(name, lerp(Ta, Tb, i / n))); return out; };
  // cyan "new ocean" strips + ridge line drawn UNDER the land into the overlay
  const seamUnder = (list, T, po = {}, alpha = 1) => (gx, X, Y, P) => {
    for (const [key, a] of list) {
      const s = seamAt(P, SEAMS[key], T, po); const A = s.A.map(ll), B = s.B.map(ll);
      const unwrap = (lo, ref) => { while (lo - ref > 180) lo -= 360; while (lo - ref < -180) lo += 360; return lo; };
      const ref = A[0][1];
      gx.save(); gx.globalAlpha = 0.62 * a * alpha; gx.fillStyle = '#2FB8E0'; gx.beginPath();
      for (let i = 0; i < A.length - 1; i++) {
        if (Math.min(s.open[i], s.open[i + 1]) < 0.02) continue;
        const q = [A[i], A[i + 1], B[i + 1], B[i]];
        q.forEach(([la, lo], k) => { const x = X(unwrap(lo, ref)), y = Y(la); k ? gx.lineTo(x, y) : gx.moveTo(x, y); }); gx.closePath();
      }
      gx.fill('nonzero');
      gx.globalAlpha = 0.95 * a * alpha; gx.strokeStyle = '#BFF6FF'; gx.lineWidth = 2.2 * P.sc; gx.lineJoin = 'round'; gx.lineCap = 'round'; gx.beginPath();
      let pen = false;
      for (let i = 0; i < s.mid.length; i++) {
        if (s.open[i] < 0.5) { pen = false; continue; }
        const x = X(unwrap(s.mid[i][1], ref)), y = Y(s.mid[i][0]); pen ? gx.lineTo(x, y) : gx.moveTo(x, y); pen = true;
      }
      gx.stroke(); gx.restore();
    }
  };
  // rewind / fast-forward scanlines
  const scan = (ctx, t, a) => { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = 0.07 * a; ctx.fillStyle = '#A8DCFF'; for (let y = (t * 420) % 16; y < H; y += 16) ctx.fillRect(0, y, W, 2); ctx.restore(); };
  // short white speed streaks behind a moving point (screen space), direction from prev -> now
  const streaks = (ctx, now, prev, a, len = 70, n = 3) => {
    if (!now.visible || a <= 0.01) return; let dx = now.x - prev.x, dy = now.y - prev.y; const L = Math.hypot(dx, dy); if (L < 0.5) return; dx /= L; dy /= L;
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#ffffff'; ctx.lineCap = 'round';
    for (let k = 0; k < n; k++) { const off = (k - (n - 1) / 2) * 16, back = 40 + (k % 2) * 18; const x0 = now.x - dx * back - dy * off, y0 = now.y - dy * back + dx * off; ctx.lineWidth = 3.5; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0 - dx * len, y0 - dy * len); ctx.stroke(); }
    ctx.restore();
  };

  // ================================================================= A+B  s072–s073a: rewind to 180 Ma, the pieces slide home and lock
  const Tasm = t => 180 * prog(t, tStart + 0.95, M.r_aus + 0.95, E.inOut);
  const exAsm = t => {
    const T = Tasm(t);
    let e = 7.5 * prog(T, 110, 176, E.inOut);
    e = lerp(e, 2.6, prog(t, M.r_aus + 1.6, M.gond - 0.25, E.inOut));
    e *= 1 - prog(t, M.gond - 0.2, M.gond - 0.04, E.in);
    return e;
  };
  const EXW = { samerica: 1, africa: 0.85, india: 1.25, australia: 1.15 };
  const exObj = (e) => ({ samerica: e * EXW.samerica, africa: e * EXW.africa, india: e * EXW.india, australia: e * EXW.australia });
  const NAMES = [['samerica', 'r_sam'], ['africa', 'r_afr'], ['india', 'r_ind'], ['australia', 'r_aus']];
  const tA2 = SEG('s073').start - 0.1;   // cut in closer for "they lock together"
  const camA1 = camK([{ t: tStart, lat: -36, lon: 16, alt: 3.15 }, { t: tStart + 5.2, lat: -52, lon: 16, alt: 2.95 }, { t: tA2, lat: GC[0] + 1, lon: GC[1] - 2, alt: 2.75 }], 0.4);
  const camA2 = camK([{ t: tA2, lat: GC[0] + 3, lon: GC[1] - 8, alt: 2.2, tilt: 14, heading: -12 }, { t: M.gond - 0.1, lat: GC[0] + 1, lon: GC[1] - 2, alt: 2.4, tilt: 8, heading: -4 }, { t: tC, lat: GC[0], lon: GC[1] + 2, alt: 2.5, tilt: 6, heading: 0 }], 0.4);
  const camA = t => t < tA2 ? camA1(t) : camA2(t);
  add(tStart, tC, async (ctx, t) => {
    await prep();
    const T = Tasm(t), e = exAsm(t);
    const hl = {}; for (const [c, m] of NAMES) hl[c] = prog(t, M[m] - 0.12, M[m] + 0.16);
    const flash = Math.exp(-Math.max(0, t - M.gond) * 3.5) * (t >= M.gond - 0.03 ? 1 : 0);
    for (const c of TRACKED) hl[c] = Math.min(1, hl[c] * (1 + 0.6 * flash));
    const po = { hl, explode: exObj(e), center: GCv, key: 'A', shelf: t > M.gond - 0.2 ? 12 : 0 };
    await paleo(P2, T, po);
    const k = prog(t, tStart + 0.6, tStart + 1.9);
    globe(ctx, camA(t), mixLook(RLOOK, PLOOK, k), shakeAt(t, M.gond - 0.02, 0.01, 0.45));
    // rewind scanlines while the clock spins
    const sp = Math.abs(Tasm(t + 0.05) - Tasm(t - 0.05)) * 10;
    scan(ctx, t, clamp(sp / 25));
    // name pulses
    for (const [c, m] of NAMES) {
      if (t < M[m] - 0.12 || t > M[m] + 1.4) continue;
      const [la, lo] = plateCen(P2, c, T, po); const q = proj(la, lo); if (!q.visible) continue;
      F.dot(ctx, q.x, q.y, { r: 7, color: '#ffffff', ring: clamp((t - M[m] + 0.12) * 0.9, 0, 0.999) });
    }
    // lock flash: white rim pulse over the assembled block
    if (flash > 0.02) { ctx.save(); ctx.globalAlpha = 0.18 * flash; ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    chip(ctx, T, prog(t, tStart + 2.35, tStart + 2.75));
    // GONDWANA headline
    if (t > M.gond - 0.12) F.headline(ctx, [{ w: 'GONDWANA', c: PAL.text }], W / 2, 175, t - (M.gond - 0.12), { size: 136, per: 0.05, tOut: tC - (M.gond - 0.12) - 0.3 });
  });
  // chapter card overlay
  add(tStart, tStart + 2.5, (ctx, t, lt) => {
    const dur = 2.5, a = env(lt, 0, dur, 0.28, 0.45); if (a <= 0) return;
    ctx.save(); ctx.fillStyle = `rgba(3,5,10,${0.6 * a})`; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = a;
    const p = prog(lt, 0.05, 0.8, E.outExpo);
    ctx.fillStyle = PAL.hero; ctx.fillRect(W / 2 - 230 * p, 668, 460 * p, 5);
    F.text(ctx, 'CHAPTER 5', W / 2, 330, { size: 46, fam: F.FAM.label, weight: 700, tracking: 0.35, align: 'center', color: PAL.hero, alpha: p });
    F.headline(ctx, ['WHERE', 'ARE', 'THE'], W / 2, 490, lt, { size: 140, per: 0.07, t0: 0.1, tOut: dur - 0.45 });
    F.headline(ctx, [{ w: 'DRIPS', c: PAL.hero }, { w: 'POINTING?', c: PAL.hero }], W / 2, 625, lt, { size: 140, per: 0.07, t0: 0.3, tOut: dur - 0.45 });
    ctx.restore();
  }, { layer: 6 });
  cue(tStart + 0.05, 'whoosh_soft', -12);
  cue(tStart + 0.8, 'time_rewind', -12);
  for (const [, m] of NAMES) cue(M[m] - 0.08, 'pop_ui', -14);
  cue(M.gond - 0.05, 'thunk_heavy', -10);

  // ================================================================= C  s073b: Antarctica, the keypiece
  const camC = camK([{ t: tC, lat: SP180[0] + 9, lon: SP180[1] + 4, alt: 1.75, tilt: 16, heading: -8 }, { t: tD, lat: SP180[0] + 7, lon: SP180[1] + 9, alt: 1.55, tilt: 24, heading: -2 }], 0.3);
  add(tC, tD, async (ctx, t) => {
    await prep();
    const lift = 1.5 * bump(t, tKey - 0.75, tKey - 0.3, tKey + 0.02);
    const ant = 0.68 * prog(t, M.ant - 0.1, M.ant + 0.2);
    const po = { hl: { samerica: 0.72, africa: 0.72, india: 0.72, australia: 0.72 }, ant, explode: exObj(lift), center: GCv, key: 'C', shelf: 12 };
    await paleo(P2, 180, po);
    globe(ctx, camC(t), PLOOK, shakeAt(t, tKey, 0.006, 0.35));
    drawRing(ctx, t, prog(t, M.ant - 0.12, M.ant + 0.2), M.ant);
    chip(ctx, 180, 1);
    const q = proj(SP180[0], SP180[1]);
    pillAt(ctx, 'ANTARCTICA: THE KEYPIECE', W - 520, 150, t, M.ant + 1.05, tD + 0.5, { size: 42, leader: q.visible ? [q.x, q.y] : null, border: 'rgba(255,210,63,0.9)' });
  });
  cue(M.ant - 0.08, 'pop_ui', -14); cue(M.ant + 1.05, 'pop_ui', -16); cue(tKey - 0.02, 'thunk_heavy', -18);

  // ================================================================= D  s074a: Bacon's open question (archival insert)
  const bacon = api.img(IMG('bacon.jpg')), page = api.img(IMG('ch5a_bacon_n246.jpg'));
  const pageBg = document.createElement('canvas'); pageBg.width = 960; pageBg.height = 540;
  { const q = pageBg.getContext('2d'); q.filter = 'blur(2px) sepia(0.75) brightness(0.40) contrast(1.15)'; const sw = page.width * 0.92, sh = sw * 540 / 960; q.drawImage(page, page.width * 0.04, page.height * 0.12, sw, sh, -16, -12, 992, 564); }
  add(tD, tE, (ctx, t, lt) => {
    const dur = tE - tD;
    ctx.fillStyle = '#07060A'; ctx.fillRect(0, 0, W, H);
    const z = 1.12 + lt * 0.018; ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.rotate(-0.012 + lt * 0.002); ctx.drawImage(pageBg, -W / 2 - lt * 6, -H / 2, W, H); ctx.restore();
    const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.2, W / 2, H / 2, H * 0.9); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.7)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
    const ip = prog(lt, 0, 0.45, E.outExpo);
    const pw = 610, ph = 740, px = W / 2 - pw / 2, py = 78;
    ctx.save(); ctx.translate(W / 2, py + ph / 2); ctx.rotate(lerp(0.05, -0.018, ip)); ctx.scale(lerp(1.18, 1, ip), lerp(1.18, 1, ip)); ctx.translate(-W / 2, -(py + ph / 2));
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, px - 10, py + 4, pw + 36, ph + 40, 10); ctx.fill();
    ctx.fillStyle = '#E9DFC8'; F.round(ctx, px - 16, py - 16, pw + 32, ph + 32, 8); ctx.fill();
    F.kenburns(ctx, bacon, lt / dur, px, py, pw, ph, { from: [0.5, 0.42, 1.0], to: [0.55, 0.3, 1.55], grade: 'sepia', ease: E.inOutSine });
    ctx.restore();
    pillAt(ctx, '"WHETHER THERE IS ANY SOUTHERN CONTINENT"', W / 2, 872, t, wordAt('s074', /^is$/i) - 0.08, tE + 0.5, { size: 40, border: 'rgba(255,210,63,0.75)' });
  });
  cue(tD - 0.02, 'whoosh_soft', -12); cue(wordAt('s074', /^is$/i) - 0.08, 'paper_rustle', -16);

  // ================================================================= E  s074b: the drips were pointing at it the whole time
  const camE = camK([{ t: tE, lat: SP180[0] + 10, lon: SP180[1] - 14, alt: 2.05, heading: -6 }, { t: tF, lat: SP180[0] + 8, lon: SP180[1] - 8, alt: 1.85, heading: 2 }], 0.35);
  const TIP180 = TIPN.map(n => at(n, 180));
  add(tE, tF, async (ctx, t) => {
    await prep();
    const po = { hl: { samerica: 1, africa: 1, india: 1, australia: 0.7 }, ant: 0.42, key: 'E', shelf: 12 };
    await paleo(P2, 180, po);
    globe(ctx, camE(t), PLOOK, shakeAt(t, M.whole, 0.008, 0.4));
    drawRing(ctx, t, 1, tE);
    // drip arrows from the three tips converge on the ring
    TIP180.forEach((tp, i) => {
      const t0a = M.whole - 0.12 + i * 0.07, p = prog(t, t0a, t0a + 0.55, E.out); if (p <= 0) return;
      const end = gcLL(tp, SP180, 40, 0, 1 - (RING_R + 1.5) / angV(v3(...tp), v3(...SP180)));
      const pts = []; for (const [la, lo] of end) { const q = proj(la, lo); if (q.visible) pts.push([q.x, q.y]); }
      if (pts.length < 2) return;
      F.glowPath(ctx, pts, { p, color: '#000000', glowColor: '#000000', width: 9, alpha: 0.55 });
      const head = F.glowPath(ctx, pts, { p, color: '#ffffff', glowColor: '#FFFFFF', width: 7 });
      const qa = pts[Math.max(0, Math.floor((pts.length - 1) * p) - 1)];
      if (head && qa) droplet(ctx, head[0], head[1], Math.atan2(head[1] - qa[1], head[0] - qa[0]), 17, '#ffffff');
      const q0 = proj(tp[0], tp[1]); if (q0.visible) F.dot(ctx, q0.x, q0.y, { r: 7, color: PAL.hero });
    });
    chip(ctx, 180, 1);
  });
  cue(tE - 0.03, 'whoosh_soft', -14); cue(M.whole, 'impact_deep', -10);

  // ================================================================= F  s075: the clock runs forward; Africa/Antarctica crack
  const midAfAnt = (() => { const s = seamAt(P2, SEAMS.afant, 165); return s.mid[Math.floor(s.mid.length / 2)]; })();
  const camF = camK([{ t: tF, lat: midAfAnt[0] + 4, lon: midAfAnt[1] - 6, alt: 2.05, tilt: 10 }, { t: tG, lat: midAfAnt[0] + 3, lon: midAfAnt[1] + 2, alt: 1.7, tilt: 24, heading: 6 }], 0.3);
  add(tF, tG, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const afHL = 0.45 + 0.55 * prog(t, M.afant - 0.15, M.afant + 0.2);
    const ga = prog(t, M.afant - 0.15, M.afant + 0.35);
    const po = { hl: { samerica: 0.4, africa: afHL, india: 0.4, australia: 0.4 }, ant: 0.75, key: 'F' + ga.toFixed(2), under: seamUnder([['afant', ga], ['indant', ga], ['satl', ga]], T) };
    await paleo(P2, T, po);
    globe(ctx, camF(t), PLOOK, shakeAt(t, tCracks, 0.009, 0.7));
    // cracks: white jagged lines along the seams, drawn on at "Cracks open"
    const ca = prog(t, tCracks - 0.05, tCracks + 0.8) * (1 - 0.7 * prog(t, M.afant + 0.6, M.afant + 1.6));
    if (ca > 0.01) for (const [k, s0] of [['afant', 11], ['indant', 23], ['satl', 37]]) {
      const s = seamAt(P2, SEAMS[k], T); const pts = crackPts(k === 'satl' ? s.mid.slice(0, Math.ceil(s.mid.length * 0.45)) : s.mid, s0);
      if (pts.length > 1) { F.glowPath(ctx, pts, { p: prog(t, tCracks - 0.05 + s0 * 0.004, tCracks + 0.75), color: '#1A1408', glowColor: '#000000', width: 8, alpha: ca * 0.5 }); F.glowPath(ctx, pts, { p: prog(t, tCracks - 0.05 + s0 * 0.004, tCracks + 0.75), color: '#ffffff', glowColor: '#FFFFFF', width: 4.5, alpha: ca }); }
    }
    // new ocean highlight between Africa and Antarctica
    const na = env(t, M.afant - 0.1, tG, 0.25, 0.5);
    if (na > 0.01) { const s = seamAt(P2, SEAMS.afant, T); const pts = s.mid.map(m => proj(m[0], m[1])).filter(q => q.visible).map(q => [q.x, q.y]); if (pts.length > 1) F.glowPath(ctx, pts, { p: prog(t, M.afant - 0.1, M.afant + 0.6), color: '#9FF3FF', glowColor: '#3DE3FF', width: 4, alpha: na }); }
    scan(ctx, t, 0.5 * prog(t, M.fwd - 0.1, M.fwd + 0.4));
    chip(ctx, T, 1);
  });
  cue(M.fwd - 0.1, 'time_rewind', -16); cue(tCracks - 0.06, 'rumble_quake', -14);

  // ================================================================= G/H  s076: the South Atlantic unzips from the bottom up
  const zipMid = (T, f) => { const s = seamAt(P2, SEAMS.satl, T); return s.mid[Math.floor((s.mid.length - 1) * f)]; };
  const zG = zipMid(140, 0.5), zH = zipMid(T_SNAP + 6, 0.82);
  const camG = camK([{ t: tG, lat: zG[0] - 3, lon: zG[1] + 1, alt: 1.7, tilt: 6, heading: -6 }, { t: tH, lat: zG[0] - 1, lon: zG[1] + 1, alt: 1.45, tilt: 12, heading: 0 }], 0.3);
  const camH = camK([{ t: tH, lat: zH[0] - 6, lon: zH[1] + 1, alt: 0.95, tilt: 24, heading: -4 }, { t: M.snap2, lat: zH[0] - 3, lon: zH[1] + 1, alt: 0.8, tilt: 28, heading: 1 }, { t: tI, lat: zH[0] - 3.5, lon: zH[1] + 1, alt: 0.84, tilt: 28, heading: 2 }], 0.25);
  // zipper teeth on the still-closed part, slider at the frontier
  const drawZipper = (ctx, s, t, o = {}) => {
    const n = s.mid.length; let k = 0; while (k < n && s.open[k] > 0.5) k++;
    const pts = s.mid.map(m => proj(m[0], m[1]));
    const glow = o.glow || 0;
    if (k < n) {
      ctx.save(); ctx.lineCap = 'round';
      const seg = []; for (let i = k; i < n; i++) if (pts[i].visible) seg.push([pts[i].x, pts[i].y]);
      if (seg.length > 1) {
        if (glow > 0) F.glowPath(ctx, seg, { color: PAL.yellow, glowColor: PAL.yellow, width: 9, alpha: glow });
        ctx.strokeStyle = 'rgba(10,12,18,0.9)'; ctx.lineWidth = 9; ctx.beginPath(); seg.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
      }
      for (let i = k; i < n; i++) {
        const p = pts[i]; if (!p.visible) continue;
        const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)]; let dx = b.x - a.x, dy = b.y - a.y; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
        const side = i % 2 ? 1 : -1, len = o.teeth || 12;
        ctx.strokeStyle = glow > 0.3 ? '#FFF2B0' : '#E8EDF5'; ctx.lineWidth = o.toothW || 5;
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - dy * len * side, p.y + dx * len * side); ctx.stroke();
      }
      ctx.restore();
    }
    // slider
    const kk = clamp(k, 1, n - 1), p = pts[kk], q = pts[kk - 1];
    if (k > 0 && k < n && p.visible && q.visible && !o.noSlider) {
      const ang = Math.atan2(p.y - q.y, p.x - q.x), sz = o.slider || 1;
      ctx.save(); ctx.translate(lerp(q.x, p.x, 0.5), lerp(q.y, p.y, 0.5)); ctx.rotate(ang); ctx.scale(sz, sz);
      ctx.fillStyle = 'rgba(0,0,0,0.4)'; F.round(ctx, -20, -13, 44, 30, 7); ctx.fill();
      ctx.fillStyle = PAL.yellow; F.round(ctx, -22, -15, 44, 30, 7); ctx.fill(); ctx.strokeStyle = '#1A1408'; ctx.lineWidth = 3; ctx.stroke();
      const sw = Math.sin(t * 5) * 0.25;
      ctx.rotate(Math.PI / 2 + sw); ctx.fillStyle = PAL.yellow; F.round(ctx, -8, 8, 16, 38, 6); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#1A1408'; F.round(ctx, -3, 30, 6, 10, 3); ctx.fill();
      ctx.restore();
    }
    return { k, pts };
  };
  const satlHL = (t) => 0.5 + 0.5 * prog(t, M.split - 0.12, M.split + 0.25) + 0.25 * bump(t, M.split - 0.1, M.split + 0.3, M.split + 1.2);
  add(tG, tH, async (ctx, t) => {
    await prep();
    const T = Tfwd(t), h = Math.min(1, satlHL(t));
    const po = { hl: { samerica: h, africa: h, india: 0.35, australia: 0.35 }, ant: 0.6, key: 'G', under: seamUnder([['afant', 0.8], ['indant', 0.8], ['satl', 1]], T) };
    await paleo(P2, T, po);
    globe(ctx, camG(t), PLOOK);
    const s = seamAt(P2, SEAMS.satl, T);
    drawZipper(ctx, s, t, { slider: 1.15 });
    chip(ctx, T, 1);
  });
  add(tH, tI, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const po = { hl: { samerica: 1, africa: 1, india: 0.35, australia: 0.35 }, ant: 0.6, key: 'H', under: seamUnder([['afant', 0.8], ['indant', 0.8], ['satl', 1]], T) };
    await paleo(P4, T, po);
    globe(ctx, camH(t), PLOOK, shakeAt(t, M.snap2 - 0.03, 0.006, 0.45));
    const s = seamAt(P4, SEAMS.satl, T);
    const glow = prog(t, M.seam - 0.1, M.seam + 0.3) * (0.7 + 0.3 * Math.sin((t - M.seam) * 9));
    const z = drawZipper(ctx, s, t, { glow: t < M.snap2 + 0.05 ? glow : 0, teeth: 16, toothW: 6, slider: 1.5 });
    if (t > M.seam - 0.1 && t < M.snap2 && z.k < s.mid.length) { const m = s.mid[Math.min(s.mid.length - 1, Math.round((z.k + s.mid.length - 1) / 2))], q = proj(m[0], m[1]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 9, color: PAL.yellow, ring: ((t - M.seam) * 0.9) % 1 }); }
    // snap burst at the last seam
    if (t > M.snap2 - 0.06 && t < M.snap2 + 0.9) {
      const lp = s.mid[s.mid.length - 1], qq = proj(lp[0], lp[1]);
      const sm = s.mid.map(m => proj(m[0], m[1])).filter(q => q.visible); const c = sm[Math.floor(sm.length * 0.85)] || qq;
      if (c && c.visible !== false) {
        const k = prog(t, M.snap2 - 0.06, M.snap2 + 0.6, E.out), a = 1 - prog(t, M.snap2 + 0.25, M.snap2 + 0.9);
        ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#FFF4C0'; ctx.lineCap = 'round';
        for (let i = 0; i < 10; i++) { const an = i / 10 * Math.PI * 2 + 0.3, r0 = 20 + 60 * k, r1 = 40 + 150 * k; ctx.lineWidth = 5 * (1 - k) + 1.5; ctx.beginPath(); ctx.moveTo(c.x + Math.cos(an) * r0, c.y + Math.sin(an) * r0); ctx.lineTo(c.x + Math.cos(an) * r1, c.y + Math.sin(an) * r1); ctx.stroke(); }
        ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(c.x, c.y, 30 + 170 * k, 0, Math.PI * 2); ctx.stroke();
        ctx.restore();
      }
    }
    chip(ctx, T, 1);
  });
  add(M.zip - 0.1, M.seam + 0.6, (ctx, t) => { pillAt(ctx, 'THE SOUTH ATLANTIC UNZIPS NORTHWARD', W - 100 - 380, 124, t, M.zip - 0.1, M.seam + 0.6, { size: 40 }); }, { layer: 6 });
  cue(M.zip - 0.1, 'pop_ui', -16); cue(M.zip, 'whoosh_soft', -14); cue(M.snap2 - 0.03, 'impact_short', -12);

  // ================================================================= I  s077a: everyone moves out (wide)
  const antCen = T => at('antarctica_c', T);
  const camI = camK([{ t: tI, lat: -62, lon: 22, alt: 3.0 }, { t: tJ, lat: -64, lon: 26, alt: 2.85 }], 0.5);
  const ALLSEAMS = T => [['afant', 0.7], ['indant', 0.7], ['ausant', 0.7], ['satl', 0.7]];
  add(tI, tJ, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const po = { hl: { samerica: 0.55, africa: 0.55, india: 0.55, australia: 0.55 }, ant: 0.3, key: 'I', under: seamUnder(ALLSEAMS(T), T) };
    await paleo(P2, T, po);
    globe(ctx, camI(t), PLOOK);
    for (const c of ['samerica', 'africa', 'india']) {
      const a = plateCen(P2, c, T), b = plateCen(P2, c, T + 6);
      streaks(ctx, proj(a[0], a[1]), proj(b[0], b[1]), 0.75 * prog(t, tI + 0.15, tI + 0.5), 60);
    }
    chip(ctx, T, 1);
  });

  // ================================================================= J  s077b: EXPLORER GAG 8 — left behind, he keeps the house
  const { Actor } = await import('../../lib/actors.js');
  const st = await api.newStage('ch5a_gag', { shadowExtent: 3, hemi: 1.3, key: 2.8, rim: 3.6, rimColor: 0x9cc8ff, exposure: 1.18, fov: 30 });
  const hero = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });
  const floor = new THREE.Mesh(new THREE.CircleGeometry(1.1, 64), new THREE.ShadowMaterial({ opacity: 0.4 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; st.add(floor);
  const yRing = new THREE.Mesh(new THREE.RingGeometry(0.55, 0.66, 72), new THREE.MeshBasicMaterial({ color: 0xFFD23F, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }));
  yRing.rotation.x = -Math.PI / 2; yRing.position.y = 0.012; st.add(yRing);
  const yRing2 = yRing.clone(); yRing2.material = yRing.material.clone(); st.add(yRing2);
  // tiny cabin with a porch light
  const cabin = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({ color: 0x9A6A44, roughness: 0.85 }), roofM = new THREE.MeshStandardMaterial({ color: 0x6B2E22, roughness: 0.8 });
  const walls = new THREE.Mesh(new THREE.BoxGeometry(1.25, 0.82, 0.95), wood); walls.position.y = 0.41; walls.castShadow = true; walls.receiveShadow = true; cabin.add(walls);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(1.02, 0.62, 4), roofM); roof.rotation.y = Math.PI / 4; roof.scale.set(1.0, 1, 0.8); roof.position.y = 0.82 + 0.31; roof.castShadow = true; cabin.add(roof);
  const door = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.52, 0.03), new THREE.MeshStandardMaterial({ color: 0x3A2316, roughness: 0.9 })); door.position.set(0.18, 0.26, 0.48); cabin.add(door);
  const winM = new THREE.MeshStandardMaterial({ color: 0x1B2230, emissive: 0xFFB45A, emissiveIntensity: 0, roughness: 0.4 });
  const win = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.22, 0.03), winM); win.position.set(-0.3, 0.46, 0.48); cabin.add(win);
  const lampM = new THREE.MeshStandardMaterial({ color: 0x33302A, emissive: 0xFFC870, emissiveIntensity: 0, roughness: 0.3 });
  const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.055, 16, 12), lampM); lamp.position.set(0.42, 0.64, 0.52); cabin.add(lamp);
  const pl = new THREE.PointLight(0xFFB860, 0, 3.2, 1.6); pl.position.set(0.42, 0.62, 0.7); cabin.add(pl);
  const CAB = { x: -0.6, y: -0.15, z: -0.55, ry: 0.42, rz: 0.2, s: 0.5 };
  cabin.position.set(CAB.x, CAB.y, CAB.z); cabin.rotation.set(0, CAB.ry, CAB.rz); cabin.scale.setScalar(CAB.s); st.add(cabin);
  hero.play(tJ - 1, 'Idle', { fade: 0 });
  hero.play(M.leave - 0.2, 'Wave', { fade: 0.2 });
  hero.play(M.stay + 1.5, 'Idle_Neutral', { fade: 0.35 });
  hero.play(M.house - 0.75, 'Idle', { fade: 0.3 });
  hero.moveAlong([{ t: 0, x: 0.05, z: 0, ry: 26 }, { t: M.stay + 1.4, x: 0.05, z: 0, ry: 26 }, { t: M.stay + 2.0, x: 0.05, z: 0, ry: 8, ease: E.inOut },
    { t: M.house - 0.45, x: 0.05, z: 0, ry: 8 }, { t: M.house + 0.05, x: 0.05, z: 0, ry: -38, ease: E.out }]);
  const lampOn = t => t < M.house - 0.06 ? 0 : t < M.house - 0.02 ? 1 : t < M.house + 0.04 ? 0.15 : t < M.house + 0.1 ? 1 : t < M.house + 0.14 ? 0.4 : 1;
  // spherical helpers: bearing a->b (deg from north) and destination from a along a bearing
  const basis = (a) => { const north = norm([-a[0] * a[1], 1 - a[1] * a[1], -a[2] * a[1]]); return { north, east: cross(north, a) }; };
  const bearingLL = (A, B) => { const a = v3(...A), b = v3(...B), { north, east } = basis(a); const k = dot(a, b); const d = [b[0] - a[0] * k, b[1] - a[1] * k, b[2] - a[2] * k]; return Math.atan2(dot(d, east), dot(d, north)) / D; };
  const destLL = (A, brg, dd) => { const a = v3(...A), { north, east } = basis(a); const c = Math.cos(brg * D), s = Math.sin(brg * D); const dir = [north[0] * c + east[0] * s, north[1] * c + east[1] * s, north[2] * c + east[2] * s]; const cd = Math.cos(dd * D), sd = Math.sin(dd * D); return ll([a[0] * cd + dir[0] * sd, a[1] * cd + dir[1] * sd, a[2] * cd + dir[2] * sd]); };
  const FPX = (H / 2) / Math.tan(17 * D);
  add(tJ, tK, async (ctx, t, lt) => {
    await prep();
    const T = Tfwd(t);
    const ant = 0.3 + 0.55 * prog(t, M.stay - 0.12, M.stay + 0.25);
    const po = { hl: { samerica: 0.9, africa: 0.9, india: 0.9, australia: 0.55 }, ant, key: 'J', under: seamUnder(ALLSEAMS(T), T) };
    await paleo(P2, T, po);
    // tiny-planet framing: Antarctica sits on the top limb of the globe (south up); the continents drift down and out of frame
    const base = at('antarctica_c', T);
    const brg0 = bearingLL(base, at('africa_c', T)) + 12 + lt * 1.4;
    const P0 = destLL(base, brg0, 61), hd = bearingLL(P0, base);
    const alt = 1.42 - lt * 0.012;
    // the Explorer stage camera (low angle); his feet land on the projected base point
    const k = lt * 0.03;
    st.lookFrom([0.15 + k, 0.22, 4.45 - k * 2], [0.05, 0.22, 0], 30); st.camera.updateMatrixWorld();
    const feet = st.project(new THREE.Vector3(0.05, 0, 0));
    let oy = 0; for (let it = 0; it < 3; it++) { g.set({ lat: P0[0], lon: P0[1], alt, tilt: 0, heading: hd, fov: 34, sun: 'camera', lookOffset: [0, oy] }); const q = g.project(base[0], base[1]); oy += (feet.y + 6 - q.y) / FPX; }
    globe(ctx, { lat: P0[0], lon: P0[1], alt, tilt: 0, heading: hd, fov: 34, sunAz: -25, sunEl: 35, keepSun: true }, Object.assign({}, PLOOK, { rimAmt: 0.55 }), [0, oy]);
    // speed streaks on the departing continents
    for (const c of ['samerica', 'africa', 'india']) { const a = plateCen(P2, c, T), b = plateCen(P2, c, T + 5); streaks(ctx, proj(a[0], a[1]), proj(b[0], b[1]), 0.6 * prog(t, M.leave - 0.3, M.leave + 0.2), 60); }
    const s1 = prog(t, M.stay - 0.1, M.stay + 0.25);
    const ph = ((t - M.stay) * 0.8) % 1;
    yRing.visible = yRing2.visible = false;
    // yellow ring on the ground around his feet (2D ellipse: back half behind him, front half in front)
    const ringE = (from, to) => { if (s1 <= 0.01) return; const rx = 150 * (1 + 0.05 * Math.sin((t - M.stay) * 7)), ry = rx * 0.2;
      ctx.save(); ctx.lineCap = 'round';
      ctx.globalAlpha = 0.55 * s1; ctx.strokeStyle = 'rgba(30,20,0,0.8)'; ctx.lineWidth = 10; ctx.beginPath(); ctx.ellipse(feet.x, feet.y + 2, rx, ry, 0, from, to); ctx.stroke();
      ctx.globalAlpha = s1; ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6; ctx.beginPath(); ctx.ellipse(feet.x, feet.y + 2, rx, ry, 0, from, to); ctx.stroke();
      const r2 = rx * (1 + ph * 1.3); ctx.globalAlpha = s1 * (1 - ph) * 0.8; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(feet.x, feet.y + 2, r2, r2 * 0.2, 0, from, to); ctx.stroke();
      ctx.restore(); };
    ringE(Math.PI, Math.PI * 2);
    const L = lampOn(t); lampM.emissiveIntensity = 3.2 * L; pl.intensity = 3.0 * L; winM.emissiveIntensity = 1.6 * L;
    ctx.drawImage(st.render(t), 0, 0);
    ringE(0, Math.PI);
    if (L > 0.01) { cabin.updateMatrixWorld(); const wp = lamp.getWorldPosition(new THREE.Vector3()); const lp = st.project(wp);
      const gr = ctx.createRadialGradient(lp.x, lp.y, 2, lp.x, lp.y, 130); gr.addColorStop(0, `rgba(255,220,150,${0.85 * L})`); gr.addColorStop(0.22, `rgba(255,170,80,${0.3 * L})`); gr.addColorStop(1, 'rgba(255,150,60,0)');
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = gr; ctx.fillRect(lp.x - 130, lp.y - 130, 260, 260); ctx.restore(); }
    chip(ctx, T, 1);
    pillAt(ctx, 'ANTARCTICA STAYS PUT', W - 100 - 250, 124, t, M.stay - 0.1, tK + 0.5, { size: 42, border: 'rgba(255,210,63,0.9)' });
  });
  cue(M.leave - 0.2, 'whoosh_soft', -18); cue(M.leave + 0.45, 'whoosh_soft', -18); cue(M.leave + 1.1, 'whoosh_soft', -18);
  cue(M.stay - 0.1, 'pop_ui', -15); cue(M.house - 0.07, 'glitch_click', -18);

  // ================================================================= K/L/M  s078: India sprints, Africa and Australia crawl, the slam
  const indN = (() => { const ring = ringOf('india'); let best = ring[0]; for (const p of ring) if (p[1] > best[1]) best = p; return best; })(); // northernmost point (present)
  const contactLL = ll(apply(P2.rot('india', 44), indN));
  const camK1 = camK([{ t: tK, lat: at('india_c', 80)[0] + 8, lon: at('india_c', 80)[1] - 2, alt: 2.0 }, { t: tL, lat: at('india_c', 66)[0] + 10, lon: at('india_c', 66)[1], alt: 2.1, heading: 3 }], 0.3);
  const camL = camK([{ t: tL, lat: -30, lon: 74, alt: 3.15, heading: -3 }, { t: tM, lat: -26, lon: 76, alt: 2.95, heading: 2 }], 0.3);
  const camM = camK([{ t: tM, lat: contactLL[0] - 14, lon: contactLL[1] - 2, alt: 1.45, tilt: 26, heading: -4 }, { t: M.slam, lat: contactLL[0] - 9, lon: contactLL[1] - 1, alt: 1.32, tilt: 30, heading: 0 }, { t: tN + 0.4, lat: contactLL[0] - 9.5, lon: contactLL[1] - 1, alt: 1.36, tilt: 30, heading: 1 }], 0.25);
  const tagA = t => env(t, tUpTo - 0.1, M.slam + 0.25, 0.2, 0.3);
  // speed tag attached to India with cartoon motion lines (and a siren at "reckless driving")
  const speedTag = (ctx, t, T) => {
    const a = tagA(t); if (a <= 0.01) return;
    const c = at('india_c', T), cp = at('india_c', T + 2.5), q = proj(c[0], c[1]), qp = proj(cp[0], cp[1]);
    if (!q.visible) return;
    let dx = q.x - qp.x, dy = q.y - qp.y; const Lm = Math.hypot(dx, dy) || 1; dx /= Lm; dy /= Lm;
    const drv = prog(t, M.driving - 0.1, M.driving + 0.2) * (1 - prog(t, M.slam - 0.1, M.slam + 0.1));
    const x = clamp(q.x + 70, 140, W - 820), y = clamp(q.y - 150, 150, 760);
    const jig = drv * Math.sin(t * 60) * 3;
    // motion lines behind the tag (opposite to India's screen motion)
    ctx.save(); ctx.strokeStyle = '#ffffff'; ctx.lineCap = 'round';
    const nL = 6 + Math.round(drv * 4), px0 = x + 330, half = 230;
    for (let i = 0; i < nL; i++) {
      const u = (i / (nL - 1) - 0.5) * 2, ph = ((t * (1.6 + drv * 2.5) + hash(i)) % 1);
      // start just outside the pill edge opposite to the motion, spread along the pill width
      const sx = px0 + u * half * Math.abs(dy), sy = y + u * 22 * Math.abs(dx);
      const edge = Math.abs(dy) * 38 + Math.abs(dx) * 300;
      const L0 = edge + 6 + ph * 18, L1 = L0 + 30 + 50 * drv;
      ctx.globalAlpha = a * (1 - ph) * (0.75 + 0.25 * drv); ctx.lineWidth = 4 + drv * 1.5;
      ctx.beginPath(); ctx.moveTo(sx - dx * L0, sy - dy * L0); ctx.lineTo(sx - dx * L1, sy - dy * L1); ctx.stroke();
    }
    ctx.restore();
    if (drv > 0.01) { // siren glow
      const red = Math.sin(t * 18) > 0;
      const gr = ctx.createRadialGradient(x + 330, y, 10, x + 330, y, 380); gr.addColorStop(0, red ? `rgba(255,60,60,${0.4 * drv})` : `rgba(60,120,255,${0.4 * drv})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = gr; ctx.fillRect(x - 60, y - 380, 780, 760); ctx.restore();
    }
    pillAt(ctx, 'INDIA: UP TO ~8 INCHES A YEAR', x + 330 + jig, y, t, tUpTo - 0.1, M.slam + 0.25, { size: 40, leader: [q.x, q.y], border: drv > 0.01 ? (Math.sin(t * 18) > 0 ? '#FF4040' : '#4C8DFF') : 'rgba(255,90,54,0.95)' });
  };
  const indiaTrail = (ctx, T, a = 1) => {
    const pts = []; for (const [la, lo] of trail('india_c', 92, T)) { const q = proj(la, lo); if (q.visible) pts.push([q.x, q.y]); }
    if (pts.length > 1) { F.glowPath(ctx, pts, { color: '#000000', glowColor: '#000000', width: 11, alpha: 0.35 * a }); F.glowPath(ctx, pts, { color: '#FFC266', glowColor: '#FF5A36', width: 8, alpha: a }); const h = pts[pts.length - 1]; F.dot(ctx, h[0], h[1], { r: 8, color: '#FFE1A8' }); }
  };
  const crawlTrail = (ctx, name, T, a) => {
    const pts = []; for (const [la, lo] of trail(name, T + 26, T)) { const q = proj(la, lo); if (q.visible) pts.push([q.x, q.y]); }
    if (pts.length > 1) { F.glowPath(ctx, pts, { color: '#000000', glowColor: '#000000', width: 9, alpha: 0.35 * a }); F.glowPath(ctx, pts, { color: '#F2FAFF', glowColor: '#3DE3FF', width: 6, alpha: a }); const h = pts[pts.length - 1], q = pts[Math.max(0, pts.length - 4)]; droplet(ctx, h[0], h[1], Math.atan2(h[1] - q[1], h[0] - q[0]), 9, '#ffffff', a); }
  };
  add(tK, tL, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const po = { hl: { samerica: 0.3, africa: 0.3, india: 1, australia: 0.3 }, ant: 0.3, key: 'K', under: seamUnder(ALLSEAMS(T), T, {}, 0.8) };
    await paleo(P2, T, po);
    globe(ctx, camK1(t), PLOOK);
    indiaTrail(ctx, T, prog(t, tK, tK + 0.4));
    const a = at('kanyakumari', T), b = at('kanyakumari', T + 3); streaks(ctx, proj(a[0], a[1]), proj(b[0], b[1]), 0.8 * prog(t, M.sprint - 0.1, M.sprint + 0.2), 80, 4);
    speedTag(ctx, t, T);
    chip(ctx, T, 1);
  });
  add(tL, tM, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const po = { hl: { samerica: 0.3, africa: 0.85, india: 1, australia: 0.85 }, ant: 0.3, key: 'L', under: seamUnder(ALLSEAMS(T), T, {}, 0.8) };
    await paleo(P2, T, po);
    globe(ctx, camL(t), PLOOK);
    indiaTrail(ctx, T);
    const ca = prog(t, M.afaus - 0.1, M.afaus + 0.4);
    crawlTrail(ctx, 'africa_c', T, ca); crawlTrail(ctx, 'australia_c', T, prog(t, M.afaus + 0.5, M.afaus + 0.9));
    const a = at('kanyakumari', T), b = at('kanyakumari', T + 3); streaks(ctx, proj(a[0], a[1]), proj(b[0], b[1]), 0.7, 70, 4);
    speedTag(ctx, t, T);
    chip(ctx, T, 1);
  });
  add(tM, tN + 0.3, async (ctx, t) => {
    await prep();
    const T = Tfwd(t);
    const po = { hl: { samerica: 0.3, africa: 0.3, india: 1, australia: 0.3 }, ant: 0.3, key: 'M', under: seamUnder(ALLSEAMS(T), T, {}, 0.6) };
    await paleo(P2, T, po);
    globe(ctx, camM(t), PLOOK, shakeAt(t, M.slam - 0.02, 0.02, 0.7));
    indiaTrail(ctx, T);
    if (t < M.slam) { const a = at('kanyakumari', T), b = at('kanyakumari', T + 3); streaks(ctx, proj(a[0], a[1]), proj(b[0], b[1]), 0.85, 90, 5); }
    speedTag(ctx, t, T);
    // slam: shock rings + flash + crumple marks
    if (t > M.slam - 0.05) {
      const cpt = ll(apply(P2.rot('india', T), indN)), q = proj(cpt[0], cpt[1]);
      if (q.visible) {
        for (let i = 0; i < 3; i++) { const k = prog(t, M.slam - 0.04 + i * 0.12, M.slam + 0.9 + i * 0.12, E.out); if (k <= 0 || k >= 1) continue; ctx.save(); ctx.globalAlpha = 1 - k; ctx.strokeStyle = i ? '#FFB347' : '#ffffff'; ctx.lineWidth = 8 * (1 - k) + 2; ctx.beginPath(); ctx.ellipse(q.x, q.y, 40 + 360 * k, (40 + 360 * k) * 0.62, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
        const ca = prog(t, M.slam + 0.05, M.slam + 0.5);
        ctx.save(); ctx.globalAlpha = ca; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 4; ctx.lineJoin = 'round';
        for (let r = 0; r < 3; r++) { ctx.beginPath(); for (let i = 0; i <= 10; i++) { const x = q.x - 110 + i * 22, y = q.y - 26 - r * 22 + (i % 2 ? -9 : 9); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
        ctx.restore();
      }
      const fl = Math.exp(-Math.max(0, t - M.slam) * 8); ctx.save(); ctx.globalAlpha = 0.45 * fl; ctx.fillStyle = '#FFF2DC'; ctx.fillRect(0, 0, W, H); ctx.restore();
    }
    chip(ctx, T, 1);
  });
  cue(M.sprint - 0.08, 'whoosh_big', -10); cue(tUpTo - 0.1, 'pop_ui', -15); cue(M.slam - 0.02, 'impact_deep', -8);

  // ================================================================= N  s079: the geologist's explanation (paper textbook figure)
  const paper = document.createElement('canvas'); paper.width = W; paper.height = H;
  {
    const q = paper.getContext('2d'); q.fillStyle = '#ECE2CB'; q.fillRect(0, 0, W, H);
    const id = q.getImageData(0, 0, W, H), r = F.rng(5);
    for (let i = 0; i < id.data.length; i += 4) { const v = (r() - 0.5) * 16; id.data[i] += v; id.data[i + 1] += v; id.data[i + 2] += v * 0.9; }
    q.putImageData(id, 0, 0);
    q.globalAlpha = 0.05; q.strokeStyle = '#6B5A3A'; q.lineWidth = 1; for (let i = 0; i < 260; i++) { const x = r() * W, y = r() * H, l = 20 + r() * 80, an = r() * Math.PI; q.beginPath(); q.moveTo(x, y); q.lineTo(x + Math.cos(an) * l, y + Math.sin(an) * l); q.stroke(); }
    q.globalAlpha = 1; const vg = q.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 1.0); vg.addColorStop(0, 'rgba(80,55,20,0)'); vg.addColorStop(1, 'rgba(80,55,20,0.35)'); q.fillStyle = vg; q.fillRect(0, 0, W, H);
  }
  const coast180 = await P2.load(180);
  const ex180 = new Set(EXCL[180]), an180 = new Set(ANT[180]);
  const isAntX = (r, j) => !ex180.has(j) && !an180.has(j) && r.every(q => q[1] < -58);
  const BASE180 = coast180.filter((r, j) => !ex180.has(j) && !an180.has(j) && !isAntX(r, j)).map(r => r.map(([lo, la]) => v3(la, lo)));
  const ANT180 = coast180.filter((r, j) => an180.has(j) || isAntX(r, j)).map(r => r.map(([lo, la]) => v3(la, lo)));
  const PN = (() => { const c = GCv, up = [0, 1, 0]; const e = norm(cross(up, c)); const n = cross(c, e); return { c, e, n }; })();
  const ortho = (p, view) => { const x = dot(p, PN.e), y = dot(p, PN.n), z = dot(p, PN.c); const s = view.R; return [view.cx + x * s, view.cy - y * s, z]; };
  const polyPath = (ctx, ring, view, R) => { let first = true; for (const p0 of ring) { const p = R ? apply(R, p0) : p0; let [x, y, z] = ortho(p, view); if (z < 0) { const L = Math.hypot(x - view.cx, y - view.cy) || 1; x = view.cx + (x - view.cx) / L * view.R; y = view.cy + (y - view.cy) / L * view.R; } first ? ctx.moveTo(x, y) : ctx.lineTo(x, y); first = false; } ctx.closePath(); };
  const INK = '#2B2520';
  const exN = t => { let e = lerp(13, 9, prog(t, tN + 0.6, M.together - 0.9, E.inOut)); e *= 1 - prog(t, M.together - 0.85, M.together - 0.02, E.inOut); return e; };
  const spinN = (t, i) => (1 - prog(t, M.together - 0.85, M.together - 0.02, E.inOut)) * (7 * Math.sin(t * 0.9 + i * 1.7) + (i % 2 ? 9 : -9));
  add(tN, tO + 0.45, (ctx, t, lt) => {
    ctx.drawImage(paper, 0, 0);
    const view = { cx: W / 2 + 150, cy: H / 2 + 22, R: 468 * (1 + 0.05 * prog(t, tN, tO + 0.45, E.inOut)) };
    const rot = (t - tN) * 0.006;
    ctx.save(); ctx.translate(view.cx, view.cy); ctx.rotate(rot); ctx.translate(-view.cx, -view.cy);
    // globe disc + graticule (paleo frame)
    ctx.fillStyle = 'rgba(214,200,168,0.75)'; ctx.beginPath(); ctx.arc(view.cx, view.cy, view.R, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(43,37,32,0.16)'; ctx.lineWidth = 1.5;
    for (let la = -75; la <= 75; la += 15) { ctx.beginPath(); let f = true; for (let lo = -180; lo <= 180; lo += 4) { const [x, y, z] = ortho(v3(la, lo), view); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
    for (let lo = -180; lo < 180; lo += 30) { ctx.beginPath(); let f = true; for (let la = -88; la <= 88; la += 3) { const [x, y, z] = ortho(v3(la, lo), view); if (z < 0) { f = true; continue; } f ? ctx.moveTo(x, y) : ctx.lineTo(x, y); f = false; } ctx.stroke(); }
    ctx.strokeStyle = 'rgba(43,37,32,0.5)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(view.cx, view.cy, view.R, 0, Math.PI * 2); ctx.stroke();
    // base land (appears once the pieces lock)
    const ba = prog(t, M.together + 0.05, M.together + 0.6);
    if (ba > 0.01) { ctx.save(); ctx.globalAlpha = ba; ctx.beginPath(); for (const r of BASE180) polyPath(ctx, r, view); ctx.strokeStyle = 'rgba(43,37,32,0.45)'; ctx.lineWidth = 2.4; ctx.stroke(); ctx.fillStyle = '#CDBE9C'; ctx.fill('nonzero'); ctx.restore(); }
    // Antarctica (the keypiece, fixed)
    ctx.beginPath(); for (const r of ANT180) polyPath(ctx, r, view);
    ctx.save(); ctx.translate(7, 9); ctx.fillStyle = 'rgba(40,25,10,0.22)'; ctx.fill('nonzero'); ctx.restore();
    ctx.strokeStyle = INK; ctx.lineWidth = 4.8; ctx.lineJoin = 'round'; ctx.stroke(); ctx.fillStyle = '#F2C443'; ctx.fill('nonzero');
    // the four pieces
    const e = exN(t);
    TRACKED.forEach((c, i) => {
      const R = P2.plateRot(c, 180, { explode: { [c]: e * EXW[c] }, spin: { [c]: spinN(t, i) }, center: GCv });
      const bob = Math.sin(t * 1.3 + i * 2.1) * 6 * (e / 13);
      ctx.save(); ctx.translate(0, bob);
      ctx.beginPath(); for (const r of P2.R0[c]) polyPath(ctx, r, view, R);
      ctx.save(); ctx.translate(7 + e * 0.8, 9 + e * 0.9); ctx.fillStyle = `rgba(40,25,10,${0.2 + e * 0.008})`; ctx.fill('nonzero'); ctx.restore();
      ctx.strokeStyle = INK; ctx.lineWidth = 4.8; ctx.lineJoin = 'round'; ctx.stroke(); ctx.fillStyle = '#EE5B3B'; ctx.fill('nonzero');
      ctx.restore();
    });
    // pencil arrows hinting the fit (before the lock)
    const pa = env(t, M.best + 1.6, M.together - 0.4, 0.35, 0.3);
    if (pa > 0.01) TRACKED.forEach((c, i) => {
      const cen = apply(P2.plateRot(c, 180, { explode: { [c]: e * EXW[c] }, center: GCv }), v3(...P2.cen0(c)));
      const [x0, y0] = ortho(cen, view), [x1, y1] = ortho(GCv, view);
      const xa = lerp(x0, x1, 0.38), ya = lerp(y0, y1, 0.38), xb = lerp(x0, x1, 0.62), yb = lerp(y0, y1, 0.62);
      ctx.save(); ctx.globalAlpha = pa * 0.8; ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.setLineDash([10, 9]); ctx.beginPath(); ctx.moveTo(xa, ya); ctx.lineTo(xb, yb); ctx.stroke(); ctx.setLineDash([]);
      const an = Math.atan2(yb - ya, xb - xa); ctx.beginPath(); ctx.moveTo(xb, yb); ctx.lineTo(xb - Math.cos(an - 0.5) * 16, yb - Math.sin(an - 0.5) * 16); ctx.moveTo(xb, yb); ctx.lineTo(xb - Math.cos(an + 0.5) * 16, yb - Math.sin(an + 0.5) * 16); ctx.stroke(); ctx.restore();
    });
    // ring at Antarctica's heart + the tips that touch it
    const ra = prog(t, M.together + 0.1, M.together + 0.6);
    const [rcx, rcy] = ortho(v3(...SP180), view);
    if (ra > 0.01) {
      const rr = Math.hypot(...(([a, b]) => [a - rcx, b - rcy])(ortho(v3(...circleLL(SP180[0], SP180[1], RING_R, 4)[0]), view)));
      ctx.save(); ctx.globalAlpha = ra; ctx.strokeStyle = INK; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(rcx, rcy, rr, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = '#FFE066'; ctx.lineWidth = 5.5; ctx.stroke(); ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(rcx, rcy, 6, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    }
    if (t > M.ant2 - 0.12) TIP180.forEach((tp, i) => {
      const a0 = M.ant2 - 0.12 + i * 0.1, p = prog(t, a0, a0 + 0.5, E.out); if (p <= 0) return;
      const [x, y] = ortho(v3(...tp), view);
      ctx.save(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.setLineDash([3, 10]); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(lerp(x, rcx, p * 0.85), lerp(y, rcy, p * 0.85)); ctx.stroke(); ctx.restore();
      const ph = ((t - a0) * 1.1) % 1;
      ctx.save(); ctx.strokeStyle = '#E2421F'; ctx.globalAlpha = 1 - ph; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(x, y, 16 + ph * 70, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
      const pp = 1 + 0.25 * E.outBack(clamp(p * 1.5)) * (1 - p);
      ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(x, y, 17 * pp, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#FF6A3D'; ctx.beginPath(); ctx.arc(x, y, 12.5 * pp, 0, Math.PI * 2); ctx.fill();
    });
    ctx.restore();
    // counter: jumps back to 180 Ma
    const cv = lerp(38, 180, prog(t, M.best - 0.1, M.best + 0.55, E.outExpo));
    chip(ctx, cv, prog(t, tN + 0.05, tN + 0.3), { ink: true });
  }, { fadeIn: 0.3 });
  cue(tN - 0.05, 'whoosh_soft', -14); cue(M.best - 0.1, 'time_rewind', -16); cue(M.together - 0.03, 'thunk_heavy', -14); cue(M.ant2 - 0.1, 'shimmer', -16);

  // ================================================================= O/P  s080–s081: back to today; the tips' real paths; scars
  const camO = camK([{ t: tO, lat: GC[0] - 2, lon: GC[1] + 4, alt: 2.5 }, { t: tO + 2.2, lat: -46, lon: 18, alt: 3.15, ease: E.inOut }, { t: tP, lat: -50, lon: 16, alt: 3.0 }], 0.3);
  const camP = camK([{ t: tP, lat: -50, lon: 16, alt: 3.0, heading: 0.3 * (tP - tO) }, { t: tEnd, lat: -53, lon: 14, alt: 2.55, tilt: 6, heading: 0.3 * (tP - tO) + 2 }], 0.3);
  const TO = t => 180 * (1 - prog(t, tO + 0.1, M.apart + 0.55, E.inOut));
  const smoothLL = (pts, w) => pts.map((_, i) => { let s = [0, 0, 0]; for (let j = Math.max(0, i - w); j <= Math.min(pts.length - 1, i + w); j++) { const v = v3(...pts[j]); s = [s[0] + v[0], s[1] + v[1], s[2] + v[2]]; } return i === 0 || i === pts.length - 1 ? pts[i] : ll(norm(s)); });
  const PATHS = TIPN.map(n => smoothLL(smoothLL(trail(n, 0, 180, 1), 8), 8));
  const pathP = t => prog(t, M.apart + 0.05, M.aim - 0.05, E.inOut);
  const drawPaths = (ctx, t, o = {}) => {
    const p = o.p ?? pathP(t); if (p <= 0) return;
    PATHS.forEach((path, i) => {
      const n = Math.max(2, Math.round(path.length * p)), sub = path.slice(0, n);
      const runs = projRuns(g, sub);
      if (o.scar > 0) {
        const sa = o.scar;
        strokeRuns(ctx, runs, { color: '#FFE3D6', width: 5, glow: true, glowColor: 'rgba(255,90,54,0.22)', glowColor2: 'rgba(255,110,70,0.45)', alpha: sa });
        // stitches across the seam, appearing along the path
        for (const r of runs) {
          let acc = 0, next = 0; const total = r.reduce((s, q, j) => j ? s + Math.hypot(q[0] - r[j - 1][0], q[1] - r[j - 1][1]) : 0, 0);
          for (let j = 1; j < r.length; j++) {
            const [x0, y0] = r[j - 1], [x1, y1] = r[j], L = Math.hypot(x1 - x0, y1 - y0); if (L < 1e-3) continue;
            while (next <= acc + L) {
              const k = (next - acc) / L, x = lerp(x0, x1, k), y = lerp(y0, y1, k), nx = -(y1 - y0) / L, ny = (x1 - x0) / L;
              const sp = prog(o.st, next / Math.max(1, total) * 0.7, next / Math.max(1, total) * 0.7 + 0.2);
              if (sp > 0) { ctx.save(); ctx.globalAlpha = sa * sp; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - nx * 11, y - ny * 11); ctx.lineTo(x + nx * 11, y + ny * 11); ctx.stroke(); ctx.restore(); }
              next += 30;
            }
            acc += L;
          }
        }
      }
      const da = 1 - (o.scar || 0);
      if (da > 0.01) strokeRuns(ctx, runs, { color: PAL.yellow, width: 6, dash: [0.1, 15], under: null, alpha: da });
      if (p < 1 && runs.length) { const r = runs[runs.length - 1], h = r[r.length - 1]; F.dot(ctx, h[0], h[1], { r: 7, color: PAL.yellow }); }
      const q0 = proj(path[0][0], path[0][1]); if (q0.visible && !o.noTips) F.dot(ctx, q0.x, q0.y, { r: 7, color: PAL.hero });
    });
  };
  // aim: dashed extensions from each path end to the ring
  const drawAim = (ctx, t, a) => {
    if (a <= 0.01) return;
    PATHS.forEach((path, i) => {
      const end = path[path.length - 1], p = prog(t, M.aim - 0.1 + i * 0.06, M.aim + 0.45 + i * 0.06, E.out);
      const q0 = proj(end[0], end[1]), c = proj(SP180[0], SP180[1]); if (!q0.visible || !c.visible || p <= 0) return;
      const an = Math.atan2(c.y - q0.y, c.x - q0.x), L = Math.hypot(c.x - q0.x, c.y - q0.y), d = Math.min(L * 0.5, 64) * E.outBack(p);
      ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(q0.x, q0.y); ctx.lineTo(q0.x + Math.cos(an) * d, q0.y + Math.sin(an) * d); ctx.stroke(); ctx.restore();
      droplet(ctx, q0.x + Math.cos(an) * d, q0.y + Math.sin(an) * d, an, 13, '#ffffff', a);
    });
  };
  add(tO, tP, async (ctx, t) => {
    await prep();
    const T = TO(t);
    const po = { hl: { samerica: 0.8, africa: 0.8, india: 0.8, australia: 0.5 }, ant: 0.8 * (1 - prog(t, tO + 1.0, tO + 1.8)), key: 'O' };
    await paleo(P2, T, po);
    const k = prog(t, M.apart + 0.2, M.apart + 1.1);
    globe(ctx, camO(t), mixLook(PLOOK, RLOOK, k));
    scan(ctx, t, 0.6 * env(t, tO + 0.1, M.apart + 0.5, 0.2, 0.3));
    drawPaths(ctx, t);
    drawAim(ctx, t, prog(t, M.aim - 0.15, M.aim + 0.1));
    drawRing(ctx, t, prog(t, M.aim - 0.4, M.aim) + 0.35 * (1 - prog(t, tO + 0.4, tO + 1.2)), M.aim - 0.05);
    chip(ctx, T, 1 - prog(t, M.apart + 1.6, M.apart + 2.0), { today: prog(t, M.apart + 0.35, M.apart + 0.6) });
  }, { fadeIn: 0.45 });
  add(tP, tEnd, async (ctx, t) => {
    await prep();
    await paleo(P2, 0, { hl: {}, ant: 0, key: 'P' });
    globe(ctx, camP(t), RLOOK, shakeAt(t, M.scar - 0.02, 0.006, 0.4));
    const sc = prog(t, M.scar - 0.1, M.scar + 0.35);
    drawPaths(ctx, t, { p: 1, scar: sc, st: prog(t, M.scar - 0.1, M.scar + 0.9), noTips: sc > 0.5 });
    drawAim(ctx, t, 1 - sc);
    drawRing(ctx, t, 1 - 0.4 * sc, tP);
    // the "drips" on the three present-day tips, before they become scars
    const da = env(t, tBig - 0.1, M.scar + 0.3, 0.25, 0.35);
    if (da > 0.01) PATHS.forEach((path, i) => {
      const q0 = proj(path[0][0], path[0][1]), q1 = proj(path[6][0], path[6][1]); if (!q0.visible) return;
      const ang = q1.visible ? Math.atan2(q1.y - q0.y, q1.x - q0.x) : Math.PI / 2;
      dripArrow(ctx, q0.x, q0.y, prog(t, tBig - 0.1 + i * 0.08, tBig + 0.4 + i * 0.08), { len: 95, angle: ang, color: '#ffffff', head: 12, alpha: da });
    });
    if (t > M.scar - 0.12) F.headline(ctx, ['THE', 'BIG', 'DRIPS', 'ARE', { w: 'SCARS', c: PAL.hero }], W / 2, 170, t - (M.scar - 0.12), { size: 120, per: 0.06 });
  });
  cue(tO, 'whoosh_soft', -14); cue(M.apart - 0.02, 'shimmer', -18); cue(M.aim - 0.05, 'pop_ui', -16);
  cue(tBig - 0.1, 'pop_ui', -16); cue(M.scar - 0.02, 'impact_deep', -6);

  return scenes;

}
