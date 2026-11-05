// Chapter 6 (s097-s109 + end screen): where is the drip going next? The Atlantic's school-bus of growth, four future
// supercontinent models (our own hand-keyed rigid-plate redraws on the real Blue Marble imagery, see ch6_future.js),
// the neighbor gag, the hot-supercontinent heat map, the bookend drip globe, Bacon's "no accident" callback,
// Gondwana's breakup, the filmstrip of maps, the Afar Y and the end screen.
import * as F from '../../lib/fx.js';
import { camAt } from '../../lib/shots.js';
import { loadGeo, rings, fillEquirect, gcLine, projectPath, strokeProjected } from '../../lib/geo.js';
import { region, allRings } from '../../lib/beats.js';
import { createFuture, qPole, qMove, rotLL, THREE } from './ch6_future.js';
import * as L from './ch6_lib.js';
import { createGond, drawPaleoPolys } from './ch6_gond.js';

const { PAL, E, prog, env, clamp, lerp } = F;
const inExpo = (x) => x <= 0 ? 0 : Math.pow(2, 10 * x - 10);
const WB = [-180, -90, 180, 90];
const IMG = (n) => 'ep/ep01/img/' + n;
const TIPS = { froward: [-53.9, -71.3], agulhas: [-34.8, 20.0], kanya: [8.1, 77.5] };
const POLE_T = [-78, 20];
const KANSAS = [38.5, -98];
// Mid-Atlantic Ridge axis (lat, lon), simplified
const RIDGE = [[66.5, -18.0], [64.0, -21.0], [62.0, -25.0], [59.0, -29.5], [56.5, -33.5], [53.0, -35.0], [52.3, -31.5], [50.0, -28.5], [45.5, -27.8], [41.5, -29.0],
  [38.0, -30.5], [35.0, -34.0], [30.0, -42.0], [26.0, -44.5], [23.5, -45.0], [20.0, -45.5], [15.5, -46.5], [13.0, -44.8], [10.5, -41.0], [7.5, -37.0], [5.0, -33.5],
  [2.0, -30.5], [0.8, -26.5], [0.0, -18.0], [-1.5, -14.0], [-4.0, -12.5], [-8.0, -13.5], [-12.0, -14.5], [-16.0, -13.5], [-20.0, -12.0], [-25.0, -13.0], [-30.0, -13.5],
  [-34.0, -14.5], [-37.5, -12.5], [-42.0, -16.0], [-46.0, -13.5], [-50.0, -8.0], [-53.0, -3.0], [-54.5, 1.0]];
// Afar triple junction arms
const AFAR = [11.5, 41.5];
const ARM_RS = [[11.5, 41.5], [13.8, 40.6], [16.5, 40.0], [19.5, 38.6], [22.5, 37.0], [25.0, 35.6], [27.0, 34.0]];
const ARM_GA = [[11.5, 41.5], [11.7, 43.0], [12.0, 45.0], [12.3, 48.0], [12.5, 51.0]];
const ARM_EA = [[11.5, 41.5], [9.8, 40.3], [8.2, 39.1], [6.6, 38.3], [5.2, 37.7], [4.0, 37.0]];
const ARM_EA2 = [[4.0, 37.0], [2.2, 36.4], [0.2, 36.1], [-2.0, 36.0], [-4.5, 35.9]];
const densify = (pts, n = 6) => { const out = []; for (let i = 0; i < pts.length - 1; i++) { const seg = gcLine(pts[i], pts[i + 1], n); (i ? seg.slice(1) : seg).forEach(p => out.push([p.lat, p.lon])); } return out; };

export async function build(api, C) {
  const W = api.W, H = api.H;
  const T = (m, w) => C.T(m, w);
  const norm = (s) => s.toLowerCase().replace(/[^a-z0-9-]/g, '');
  const wf = (seg, w, nth = 0) => { const ws = C.words(seg).filter(x => norm(x.w).startsWith(w)); if (!ws[nth]) throw new Error(`ch6: word ${w} not in ${seg}`); return ws[nth].start; };
  const SEG = (id) => C.seg(id);
  const cue = (t, n, db) => api.cue(Math.max(C.t0, t), n, db);
  await api.globe();
  const g = api.g;
  const IM = { bacon: IMG('bacon.jpg'), p246: IMG('ch6_bacon_n246.jpg'), ee: 'tex/equal_earth.jpg' };
  await api.loadImages(Object.values(IM));
  const img = (k) => api.img(IM[k]);
  const fut = await createFuture(api);
  const gond = await createGond(api);
  const I0 = new THREE.Quaternion();
  const scenes = [];
  const base = (t0, t1, draw, o = {}) => scenes.push({ t0, t1, layer: 0, fadeIn: o.fadeIn || 0, draw });
  const over = (t0, t1, draw, layer = 6) => scenes.push({ t0, t1, layer, draw });

  // ------------------------------------------------------------------ marker / word times
  const M = {};
  for (const k of ['going', 'line', 'bus', 'years', 'form', 'agree', 'models', 'prox', 'crash2', 'proxname', 'novo', 'asia', 'middle', 'aurica', 'a1', 'a2', 'a3', 'a4',
    'neighbor', 'comments', 'tuesday', 'tenth', 'mammal', 'wins', 'torn', 'been', 'ago', 'acc2', 'right2', 'breakup', 'frame', 'shot', 'afar', 'cracks', 'eafr', 'here', 'sub2']) M[k] = T(k);
  const w = {
    africa99: wf('s099', 'africa'), years99: wf('s099', 'years'), pangaea: wf('s099', 'pangaea'), pacific100: wf('s100', 'pacific'), novoname: wf('s100', 'novopangaea'),
    arctic: wf('s101', 'arctic'), amasia: wf('s101', 'amasia'), both: wf('s102', 'both'), aus2: wf('s102', 'australia', 1), america102: wf('s102', 'america'),
    oneword: wf('s103', 'one'), inaway: wf('s103', 'in', 1), holden: wf('s103', 'holdens'), splash: wf('s103', 'splash'), sixth: wf('s104', 'sixth'),
    study: wf('s104', 'study'), capes: wf('s106', 'capes'), wasnt: wf('s106', 'wasnt'), accident2: wf('s106', 'accident', 1), giant: wf('s108', 'giant'), fingerprint: wf('s105', 'fingerprint'),
  };
  const END = C.t1;

  // ------------------------------------------------------------------ globe helpers
  const LOOK0 = { dim: 0, desat: 0.12, ovAlpha: 0, relief: 0.8, nightAmt: 1, exposure: 1.25, ambient: 0.10, specAmt: 0.5, rimAmt: 0.35, flatBase: 0, ovMul: 0 };
  const useOv = (cv) => { api._ovOwner = null; if (!cv) { g.u.ovOn.value = 0; return; } if (g.u.ovTex.value?.image !== cv) g.setOverlay(cv, WB); g.u.ovOn.value = 1; };
  const globe = (ctx, cam, look = {}, ov = null) => {
    g.u.patchOn.value = 0; api._patchOwner = null;
    g.u.tint.value.set(1, 1, 1); g.u.flatColor.value.set(0.035, 0.09, 0.19);
    useOv(ov);
    api.drawGlobe(ctx, Object.assign({ sun: 'camera' }, cam), Object.assign({}, LOOK0, look));
  };
  const proj = (lat, lon, h = 0) => g.project(lat, lon, h);
  const projRun = (pts) => { const out = []; for (const [la, lo] of pts) { const q = proj(la, lo); if (q.visible) out.push([q.x, q.y]); else if (out.length) break; } return out; };

  // cold-open drip overlay: South America, Africa, India in hero orange
  const F_SA = await region('south america'), F_AF = await region('africa'), F_IN = await region('india');
  const COLD = L.makeCanvas(2048, 1024);
  fillEquirect(COLD, WB, [...F_SA, ...F_AF, ...F_IN], { color: PAL.hero, alpha: 0.92, glow: 22 });
  const R_SA = allRings(F_SA), R_AF = allRings(F_AF);
  const coast = await loadGeo('ne_50m_coastline');
  const coastRuns = (b) => {
    const out = [];
    for (const f of coast.features) for (const line of rings(f)) {
      let cur = [];
      for (const p of line) { if (p[0] >= b[0] && p[0] <= b[2] && p[1] >= b[1] && p[1] <= b[3]) cur.push(p); else { if (cur.length > 1) out.push(cur); cur = []; } }
      if (cur.length > 1) out.push(cur);
    }
    return out;
  };
  const TIPRUN = { froward: coastRuns([-76.5, -56.2, -63.5, -49]), agulhas: coastRuns([15.5, -35.5, 30, -31.5]), kanya: coastRuns([74.5, 7.6, 80.6, 12.5]) };
  const drawArcs = (ctx, t, tStart, o = {}) => {
    ['froward', 'agulhas', 'kanya'].forEach((k, i) => {
      const a0 = tStart + i * (o.stagger ?? 0.15), p = o.full ? 1 : prog(t, a0, a0 + (o.d ?? 1.0), E.inOut); if (p <= 0) return;
      const pts = projectPath(g, gcLine(TIPS[k], POLE_T, 80, 0.08)); if (pts.length < 2) return;
      const head = F.glowPath(ctx, pts, { p, color: '#ffffff', width: o.width || 3.2, alpha: o.alpha ?? 0.92, glowColor: '#ffd9c8' });
      if (p < 1 && head) F.dot(ctx, head[0], head[1], { r: 6, color: '#ffffff' });
    });
  };
  const poleRing = (ctx, t, a = 1) => { const q = proj(-90, 0); if (!q.visible) return; L.yRing(ctx, q.x, q.y, 40, t, a); F.text(ctx, '?', q.x, q.y, { size: 52, fam: F.FAM.head, weight: 400, align: 'center', baseline: 'middle', color: '#ffffff', alpha: a }); };

  // ------------------------------------------------------------------ backdrops
  const SPACE = L.makeSpace(W, H, 5);
  const DESK = L.makeDesk(W, H, 11);
  const HOT = (() => { const c = L.makeCanvas(W, H), x = c.getContext('2d'); const gr = x.createRadialGradient(W * 0.72, H * 0.2, 30, W * 0.55, H * 0.5, H * 1.25); gr.addColorStop(0, '#ffcf7a'); gr.addColorStop(0.12, '#ff7a35'); gr.addColorStop(0.45, '#8a1e10'); gr.addColorStop(1, '#1c0503'); x.fillStyle = gr; x.fillRect(0, 0, W, H); return c; })();

  // ================================================================== FUTURE MODELS (hand-keyed rigid rotations)
  const crashE = (k) => k * k * (3 - k) / 2;   // starts from rest, arrives with speed (impact)
  const poseAt = (plates, t) => {
    const out = {};
    for (const p in plates) {
      const s = plates[p]; const k = clamp((t - s.t0) / (s.t1 - s.t0));
      let e = s.ease === 'crash' ? crashE(k) : E.inOut(k);
      if (s.ease === 'crash' && t > s.t1) { const u = t - s.t1; e = 1 - 0.03 * Math.exp(-6 * u) * Math.abs(Math.sin(u * 12)); }
      out[p] = new THREE.Quaternion().slerp(s.q, e);
    }
    return out;
  };
  const NA_TINT = [1, 0.36, 0.22, 0.30];
  const neighTint = (t, tc) => { if (t < tc - 0.05) return 0; const u = t - tc; return u < 0.35 ? 0.55 * prog(u, -0.05, 0.3) : 0.32 + 0.23 * Math.exp(-3 * (u - 0.35)); };
  const s100 = SEG('s100').start, s101 = SEG('s101').start, s102 = SEG('s102').start;
  const MODELS = [
    { name: 'PANGAEA PROXIMA', col: PAL.hero, t0: M.models + 0.98, tExp: M.models + 0.98, tShrink: s100 - 0.5, tEnd: s100,
      keys: [{ t: 0, lat: 25, lon: -30, alt: 2.45 }, { t: 897.4, lat: 21, lon: -21, alt: 2.3 }, { t: s100 - 0.5, lat: 19, lon: -15, alt: 2.3 }],
      plates: { SA: { q: qPole(44.0, -30.6, 57), t0: M.prox - 0.08, t1: w.africa99 - 0.3, ease: 'crash' }, NA: { q: qPole(66.95, -12.02, 75.55), t0: M.prox + 0.05, t1: w.africa99 - 0.03, ease: 'crash' }, AU: { q: qMove([-25, 134], [-14, 124]), t0: M.prox, t1: M.prox + 3.3 } },
      neigh: 'AF', contact: { t: w.africa99 - 0.03, plate: 'NA', ll: [34, -77] }, arrows: [['NA', [42, -95]], ['SA', [-12, -58]]] },
    { name: 'NOVOPANGAEA', col: PAL.cyan, t0: s100, tExp: s100 + 0.15, tShrink: s101 - 1.3, tEnd: s101,
      keys: [{ t: 0, lat: -20, lon: -86, alt: 2.65 }, { t: M.novo + 0.3, lat: -30, lon: -100, alt: 2.5 }, { t: s101 - 0.5, lat: -32, lon: -106, alt: 2.48 }],
      plates: { AN: { q: qMove([-90, 0], [-72, -117]), t0: w.pacific100, t1: M.novo - 0.05, ease: 'crash' }, SA: { q: qMove([-15, -60], [-17, -102], 6), t0: w.pacific100, t1: M.novo - 0.05, ease: 'crash' },
        NA: { q: qMove([45, -100], [44, -124]), t0: w.pacific100 + 0.1, t1: M.novo + 0.9 }, AU: { q: qMove([-25, 134], [-12, 139]), t0: w.pacific100 + 0.2, t1: M.novo + 0.8 } },
      neigh: 'AN', contact: { t: M.novo - 0.05, plate: 'SA', ll: [-55.5, -67.5] }, arrows: [['AN', [-80, 0]], ['SA', [-12, -58]]] },
    { name: 'AMASIA', col: PAL.yellow, t0: s101, tExp: s101 + 0.15, tShrink: s102 - 0.5, tEnd: s102,
      keys: [{ t: 0, lat: 70, lon: -112, alt: 2.5 }, { t: M.asia + 0.2, lat: 78, lon: -128, alt: 2.35 }, { t: s102 - 0.5, lat: 80, lon: -140, alt: 2.33 }],
      plates: { NA: { q: qMove([55, -100], [77, -100]), t0: w.arctic - 0.05, t1: M.asia - 0.05, ease: 'crash' }, SA: { q: qMove([-15, -60], [3, -74]), t0: w.arctic + 0.1, t1: M.asia + 0.6 } },
      neigh: 'EU', contact: { t: M.asia - 0.05, plate: 'NA', ll: [66, -166] }, arrows: [['NA', [55, -100]]] },
    { name: 'AURICA', col: PAL.green, t0: s102, tExp: s102 + 0.15, tShrink: SEG('s103').start - 0.75, tEnd: SEG('s103').start - 0.25,
      keys: [{ t: 0, lat: -16, lon: 158, alt: 2.7 }, { t: M.middle + 0.2, lat: -12, lon: -178, alt: 2.55 }, { t: SEG('s103').start - 0.75, lat: -11, lon: -174, alt: 2.52 }],
      plates: { NA: { q: qMove([45, -100], [42, -163], -8), t0: w.both - 0.05, t1: M.middle - 0.4, ease: 'crash' }, SA: { q: qMove([-15, -60], [-15, -149]), t0: w.both - 0.05, t1: M.middle - 0.4, ease: 'crash' },
        EU: { q: qPole(90, 0, 24), t0: w.both, t1: M.middle - 0.2 }, AF: { q: qPole(90, 0, 24), t0: w.both, t1: M.middle - 0.2 }, AU: { q: qMove([-25, 134], [-15, 167], 12), t0: w.both + 0.15, t1: M.middle - 0.4, ease: 'crash' } },
      neigh: 'AU', contact: { t: M.middle - 0.4, plate: 'SA', ll: [-16, -76] }, arrows: [['NA', [42, -95]], ['SA', [-12, -58]], ['AU', [-25, 134]]] },
  ];
  MODELS.forEach((m, i) => {
    m.i = i; m.tLive = m.tExp + 0.55; m.keys[0].t = m.tLive;
    // hold phase: once every plate has settled, the globe frame is rendered once and pushed in 2D (overlays stay live)
    m.tHold = Math.max(m.contact.t + 0.95, ...Object.values(m.plates).map(p => p.t1 + 0.05));
    m.keys = [m.keys[0], Object.assign({}, m.keys[m.keys.length - 1], { t: m.tHold, ease: E.inOutSine })];
  });
  const tintAt = (m, t) => { const o = { NA: NA_TINT }; const a = neighTint(t, m.contact.t); if (a > 0) o[m.neigh] = [1, 0.84, 0.28, a]; return o; };
  const FLOOK = { specAmt: 0.16, exposure: 1.32, ambient: 0.13, rimAmt: 0.35 };
  const drawUS = (ctx, pose, t) => {
    const u = rotLL(pose.NA || I0, KANSAS[0], KANSAS[1]); const q = proj(u[0], u[1]); if (!q.visible) return;
    const fa = Math.max(0, Math.min(1, (q.y - 150) / 80)); if (fa <= 0) return; // fade out at the top edge (clipped dot, pills)
    ctx.save(); ctx.globalAlpha *= fa; ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.beginPath(); ctx.arc(q.x, q.y, 11, 0, Math.PI * 2); ctx.fill();
    F.dot(ctx, q.x, q.y, { r: 7.5, color: '#ffffff', ring: (t * 0.8) % 1 }); ctx.restore();
  };
  const drawLive = (ctx, m, t, still = false) => {
    const pose = poseAt(m.plates, t);
    fut.setPose(pose); fut.setTint(tintAt(m, t));
    let cam = camAt(m.keys, t, 0);
    const u = t - m.contact.t;
    if (u > 0 && u < 0.6) { const s = Math.exp(-7 * u) * Math.sin(u * 55) * 0.35; cam = Object.assign({}, cam, { lat: cam.lat + s, lon: cam.lon + s * 0.7 }); }
    fut.draw(ctx, cam, { look: FLOOK, desat: 0.1 });
    if (!still) for (const [p, c] of m.arrows) {
      const s = m.plates[p]; const a = env(t, s.t0 - 0.12, s.t1 - 0.02, 0.22, 0.3); if (a <= 0) continue;
      const q0 = rotLL(pose[p], c[0], c[1]), q1 = rotLL(s.q, c[0], c[1]);
      const A = proj(q0[0], q0[1]), B = proj(q1[0], q1[1]); if (!A.visible || !B.visible) continue;
      L.arrow(ctx, [A.x, A.y], [B.x, B.y], { alpha: a, width: 7, bend: 0.12 });
    }
    drawUS(ctx, pose, t);
    if (!still && u >= 0 && u < 0.9) { const cp = rotLL(m.plates[m.contact.plate].q, m.contact.ll[0], m.contact.ll[1]); const Q = proj(cp[0], cp[1]); if (Q.visible) L.impact(ctx, Q.x, Q.y, u); }
    if (m.extra) m.extra(ctx, t, pose, still);
  };
  const GSET = (cam) => g.set(Object.assign({ sun: 'camera', lookOffset: null, tilt: 0, heading: 0, fov: 34 }, cam));
  const zoomAbout = (ctx, z, dx = 0, dy = 0) => { ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2); };
  const HOLD = {};
  const holdFrame = (m) => HOLD[m.i] || (HOLD[m.i] = (() => {
    const c = L.makeCanvas(W, H), pose = poseAt(m.plates, m.tHold), cam = camAt(m.keys, m.tHold, 0);
    fut.setPose(pose); fut.setTint(tintAt(m, m.tHold)); fut.draw(c.getContext('2d'), cam, { look: FLOOK, desat: 0.1 });
    return { c, cam, pose };
  })());
  const drawHold = (ctx, m, t) => {
    const h = holdFrame(m), z = 1 + 0.035 * E.inOutSine(prog(t, m.tHold, m.tShrink));
    ctx.save(); zoomAbout(ctx, z); ctx.drawImage(h.c, 0, 0);
    GSET(h.cam); drawUS(ctx, h.pose, t); if (m.extra) m.extra(ctx, t, h.pose, false);
    ctx.restore();
  };
  // Aurica: Australia glows in the middle
  MODELS[3].extra = (ctx, t, pose, still) => {
    const a = still ? 0.5 : prog(t, M.middle - 0.1, M.middle + 0.25);
    if (a <= 0) return;
    const c = rotLL(pose.AU || I0, -25, 134); const q = proj(c[0], c[1]); if (!q.visible) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const rr = 190 * (1 + 0.05 * Math.sin(t * 5)); const gg = ctx.createRadialGradient(q.x, q.y, 10, q.x, q.y, rr);
    gg.addColorStop(0, `rgba(255,210,63,${0.30 * a})`); gg.addColorStop(1, 'rgba(255,210,63,0)'); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(q.x, q.y, rr, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    if (!still) L.yRing(ctx, q.x, q.y, 120, t - M.middle, a);
  };
  // stills (start = today's globe at the model camera; end = model end state), rendered once on demand
  let STILLS = null;
  const ensureStills = () => STILLS || (STILLS = (async () => {
    const out = [];
    for (const m of MODELS) {
      const a = L.makeCanvas(W, H), b = L.makeCanvas(W, H);
      drawLive(a.getContext('2d'), m, m.tLive, true);
      drawHold(b.getContext('2d'), m, m.tShrink);
      out.push({ a, b });
    }
    return out;
  })());

  // ------------------------------------------------------------------ 2x2 grid layout
  const TW = 600, TH = 338, GAP = 36, GX0 = (W - 2 * TW - GAP) / 2, GY0 = 178;
  const SLOT = [0, 1, 2, 3].map(i => [GX0 + (i % 2) * (TW + GAP), GY0 + Math.floor(i / 2) * (TH + GAP), TW, TH]);
  const SLOTC = SLOT.map(r => [r[0] + r[2] / 2, r[1] + r[3] / 2]);
  const lerpR = (a, b, k) => a.map((v, i) => lerp(v, b[i], k));
  const FULL = [0, 0, W, H];
  const spaceBg = (ctx, t) => L.drawDrift(ctx, SPACE, W, H, t, { zoom: 1.08, speed: 6 });
  // tiles: [{img, rect, alpha, border, glow, q}] drawn over the space backdrop
  const drawTiles = (ctx, t, tiles) => {
    for (const tl of tiles) {
      if (!tl || tl.alpha <= 0.003) continue;
      const [x, y, w_, h_] = tl.rect;
      L.tile(ctx, tl.img, x, y, w_, h_, { alpha: tl.alpha, border: tl.border || 'rgba(244,246,250,0.5)', glow: tl.glow || 0, borderW: tl.bw || 2, radius: tl.radius ?? 16, dim: tl.dim });
      if (tl.q) L.qmark(ctx, x + w_ / 2, y + h_ / 2, h_ * 0.42, tl.q * tl.alpha);
    }
  };
  const gridTiles = (S, t, o = {}) => SLOT.map((r, i) => {
    const done = o.done ? o.done[i] : false;
    return { img: done ? S[i].b : S[i].a, rect: r, alpha: 1, border: done ? MODELS[i].col : 'rgba(244,246,250,0.5)', bw: done ? 3 : 2, q: done ? 0 : 0.35 + 0.06 * Math.sin(t * 3 + i) };
  });

  // ================================================================== s097  globe on the Atlantic: ridge, 1620, school bus
  const A0 = C.t0, A1 = SEG('s098').start - 0.15;
  const RIDGE_D = densify(RIDGE, 5);
  const GAP_PTS = densify([[-10.0, -14.2], [-12.0, -14.5], [-14.5, -14.0], [-16.0, -13.5], [-18.0, -12.8], [-20.0, -12.0], [-22.5, -12.4], [-25.0, -13.0]], 6);
  const GAPC = [-17.0, -13.2];
  const camA = (t) => camAt([{ t: A0, lat: -2, lon: -20, alt: 3.1 }, { t: M.line + 0.4, lat: 1, lon: -27, alt: 2.5 }, { t: M.bus - 0.12, lat: -17.5, lon: -13.6, alt: 1.0, tilt: 18, ease: E.inOutExpo }, { t: A1 + 0.6, lat: -17.8, lon: -13.4, alt: 0.9, tilt: 22 }], t, 0);
  const busW = 236;
  const drawRidge = (ctx, t, a = 1) => {
    const p = prog(t, A0 + 2.0, A0 + 3.6, E.inOut); if (p <= 0) return;
    const pts = projRun(RIDGE_D); if (pts.length < 2) return;
    F.glowPath(ctx, pts, { p, color: PAL.cyan, width: 3.6, alpha: a * (0.85 + 0.15 * Math.sin(t * 4)) });
  };
  const drawGap = (ctx, t, a = 1) => {
    if (t < M.bus - 0.15 || a <= 0) return;
    const gw = busW * prog(t, M.bus - 0.12, M.bus + 0.55, E.out);
    const c = proj(GAPC[0], GAPC[1]); if (!c.visible) return;
    const pts = projRun(GAP_PTS); if (pts.length < 3) return;
    const left = [], right = [];
    for (let i = 0; i < pts.length; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[Math.min(pts.length - 1, i + 1)];
      let dx = p1[0] - p0[0], dy = p1[1] - p0[1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
      const d = Math.hypot(pts[i][0] - c.x, pts[i][1] - c.y), taper = Math.pow(clamp(1 - d / 270), 0.7);
      const hw = gw / 2 * taper;
      left.push([pts[i][0] - dy * hw, pts[i][1] + dx * hw]); right.push([pts[i][0] + dy * hw, pts[i][1] - dx * hw]);
    }
    ctx.save(); ctx.globalAlpha *= a;
    ctx.beginPath(); left.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]); ctx.closePath();
    const mg = ctx.createRadialGradient(c.x, c.y, 4, c.x, c.y, 270); mg.addColorStop(0, '#2a0a05'); mg.addColorStop(0.55, '#4a1207'); mg.addColorStop(1, '#7a1d08');
    ctx.fillStyle = mg; ctx.fill();
    ctx.save(); ctx.clip();
    // glowing magma seam down the middle + cooling cracks
    F.glowPath(ctx, pts, { color: '#ffb347', width: 7 + 3 * Math.sin(t * 6), glowColor: '#FF5A36' });
    ctx.strokeStyle = 'rgba(255,120,50,0.35)'; ctx.lineWidth = 2;
    for (let i = 2; i < pts.length - 2; i += 3) { const q = pts[i]; const l = (left[i][0] - q[0]); ctx.beginPath(); ctx.moveTo(q[0], q[1]); ctx.lineTo(q[0] + l * 0.7, q[1] + 8); ctx.moveTo(q[0], q[1]); ctx.lineTo(q[0] - l * 0.6, q[1] - 6); ctx.stroke(); }
    ctx.restore();
    ctx.lineJoin = 'round';
    for (const side of [left, right]) { ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.lineWidth = 3; ctx.beginPath(); side.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); }
    ctx.restore();
    // the bus slides down the gap and drops in, oriented across it
    const bp = prog(t, M.bus - 0.1, M.bus + 0.42, E.outBack);
    if (bp > 0) {
      const i0 = Math.max(0, Math.floor(pts.length / 2) - 3), i1 = Math.min(pts.length - 1, Math.floor(pts.length / 2) + 3);
      let dx = pts[i1][0] - pts[i0][0], dy = pts[i1][1] - pts[i0][1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
      const along = (1 - bp) * -520 + 6 * Math.sin(t * 9) * (1 - prog(t, M.bus + 0.4, M.bus + 1.0));
      const ang = Math.atan2(dy, dx) - Math.PI / 2;
      L.schoolBus(ctx, c.x + dx * along, c.y + dy * along - 10, busW * 0.98, ang, { alpha: a * clamp(bp * 3) });
    }
  };
  base(A0, A1, (ctx, lt, t) => {
    const cam = camA(t);
    const ovA = lerp(0.55, 0.12, prog(t, A0 + 1.6, A0 + 3.2));
    globe(ctx, cam, { desat: 0.2, dim: lerp(0.25, 0.08, prog(t, A0 + 1.5, A0 + 3)), ovAlpha: ovA }, COLD);
    // drip arcs: present, pulse on "going", then fade
    const pulse = env(t, M.going - 0.1, M.going + 0.8, 0.1, 0.5);
    const arcA = lerp(0.65, 0.18, prog(t, M.going + 1.0, M.going + 2.2));
    drawArcs(ctx, t, 0, { full: true, alpha: arcA, width: 3.2 + 3 * pulse });
    if (t > M.going - 0.1 && t < M.going + 1.2) drawArcs(ctx, t, M.going - 0.08, { d: 0.8, stagger: 0.08, alpha: 1, width: 4 });
    drawRidge(ctx, t, 1 - 0.4 * prog(t, M.bus - 0.2, M.bus + 0.3));
    drawGap(ctx, t);
    // 1620 pill on the ridge
    if (t > M.line - 0.12 && t < M.bus - 0.05) {
      const q = proj(24, -45.2);
      if (q.visible) { const a = prog(t, M.line - 0.12, M.line + 0.15) * (1 - prog(t, M.bus - 0.4, M.bus - 0.1)); F.pill(ctx, '1620', q.x + 110, q.y - 90, { anchor: 'left', leader: [q.x, q.y], size: 44, alpha: a, border: PAL.cyan, ring: ((t - M.line) * 0.9) % 1 }); }
    }
  });
  over(A1 - 2.2, A1 + 0.05, (ctx, lt, t) => L.pillT(ctx, 'SINCE 1620: ABOUT ONE SCHOOL BUS', W / 2, 118, t, M.bus - 0.08, A1 + 0.05, { size: 42, border: PAL.yellow }));
  // chapter card
  over(C.t0, C.t0 + 2.3, (ctx, lt) => {
    const dur = 2.3, a = env(lt, 0, dur, 0.22, 0.4);
    ctx.save(); ctx.fillStyle = `rgba(3,5,10,${0.55 * a})`; ctx.fillRect(0, 0, W, H);
    const p = prog(lt, 0.05, 0.7, E.outExpo); ctx.globalAlpha = a;
    ctx.fillStyle = PAL.hero; const lw = 460 * p; ctx.fillRect(W / 2 - lw / 2, H / 2 + 34, lw, 5);
    F.text(ctx, 'CHAPTER 6', W / 2, H / 2 - 120, { size: 44, fam: F.FAM.label, weight: 700, tracking: 0.35, align: 'center', color: PAL.hero, alpha: p });
    F.headline(ctx, ['WHERE', 'IS', 'THE', { w: 'DRIP', c: PAL.hero }, 'GOING', { w: 'NEXT?', c: PAL.yellow }], W / 2, H / 2 + 6, lt, { size: 118, per: 0.06, t0: 0.1, tOut: dur - 0.42 });
    ctx.restore();
  }, 7);
  cue(C.t0 + 0.05, 'whoosh_soft', -14); cue(M.line - 0.1, 'pop_ui', -16); cue(M.bus - 0.6, 'whoosh_soft', -16); cue(M.bus + 0.3, 'thunk_heavy', -20); cue(M.bus - 0.06, 'pop_ui', -14);

  // ================================================================== s098  time scrub forward, spin, fog, four '?'
  const B0 = A1, B1 = M.models - 0.25;
  const SPIN0 = M.form - 0.15, SPIN1 = M.form + 1.75;
  const camB = (t) => {
    if (t < B0 + 1.9) return camAt([{ t: B0, lat: -17.8, lon: -13.4, alt: 0.9, tilt: 22 }, { t: B0 + 1.9, lat: 30, lon: -62, alt: 2.85, tilt: 0, ease: E.inOutExpo }], t, 0);
    const k = prog(t, SPIN0, SPIN1, E.inOut);
    const lat = lerp(lerp(30, 32, prog(t, B0 + 1.9, SPIN0, E.lin)), 38, k);
    const lon = -62 - 8 * prog(t, B0 + 1.9, SPIN0, E.lin) - 750 * k - 1.2 * Math.max(0, t - SPIN1);
    return { lat, lon, alt: lerp(2.85, 2.72, k) * (1 + 0.006 * Math.sin(t * 0.7)), tilt: 0, heading: 0 };
  };
  const SCRUB = { x0: 330, x1: 1590, y: 112 };
  base(B0, B1, (ctx, lt, t) => {
    const fog = prog(t, M.form - 0.05, M.form + 1.3, E.inOut);
    globe(ctx, camB(t), { desat: lerp(0.18, 0.6, fog), dim: 0.06 + 0.12 * fog, ovAlpha: 0 }, null);
    // ridge + bus gap fade out as we pull back
    const fa = 1 - prog(t, B0, B0 + 0.5);
    if (fa > 0) { drawRidge(ctx, t, fa); drawGap(ctx, t, fa); }
    // fog over the globe
    if (fog > 0) {
      const d = g.disc();
      ctx.save();
      const fg = ctx.createRadialGradient(d.x, d.y, d.r * 0.2, d.x, d.y, d.r * 1.25); fg.addColorStop(0, `rgba(205,220,240,${0.55 * fog})`); fg.addColorStop(0.75, `rgba(170,190,220,${0.35 * fog})`); fg.addColorStop(1, 'rgba(170,190,220,0)');
      ctx.fillStyle = fg; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 5; i++) { const bx = d.x + Math.sin(t * 0.4 + i * 1.7) * d.r * 0.6, by = d.y + Math.cos(t * 0.33 + i * 2.3) * d.r * 0.5, br = d.r * (0.45 + 0.1 * i); const bg = ctx.createRadialGradient(bx, by, 0, bx, by, br); bg.addColorStop(0, `rgba(235,242,252,${0.16 * fog})`); bg.addColorStop(1, 'rgba(235,242,252,0)'); ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(bx, by, br, 0, Math.PI * 2); ctx.fill(); }
      ctx.restore();
    }
    // time-scrub bar running forward past TODAY
    const sa = prog(t, B0 + 0.35, B0 + 0.8) * (1 - prog(t, M.form + 0.3, M.form + 0.8));
    if (sa > 0) {
      const v = 250 * prog(t, M.years - 0.35, M.form - 0.1, E.inOut);
      const { x0, x1, y } = SCRUB, xp = x0 + (x1 - x0) * v / 300;
      ctx.save(); ctx.globalAlpha = sa;
      const tg = ctx.createLinearGradient(0, 0, 0, 260); tg.addColorStop(0, 'rgba(3,5,10,0.75)'); tg.addColorStop(1, 'rgba(3,5,10,0)'); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 260);
      ctx.fillStyle = 'rgba(244,246,250,0.3)'; ctx.fillRect(x0, y - 3, x1 - x0, 6);
      for (let k = 0; k <= 6; k++) { const xx = x0 + (x1 - x0) * k / 6; ctx.fillStyle = 'rgba(244,246,250,0.5)'; ctx.fillRect(xx - 1.5, y - (k ? 9 : 15), 3, k ? 18 : 30); }
      ctx.fillStyle = PAL.yellow; ctx.fillRect(x0, y - 4, xp - x0, 8);
      ctx.beginPath(); ctx.moveTo(xp, y + 6); ctx.lineTo(xp - 13, y + 24); ctx.lineTo(xp + 13, y + 24); ctx.closePath(); ctx.fill();
      F.dot(ctx, xp, y, { r: 9, color: PAL.yellow });
      ctx.restore();
      F.text(ctx, 'TODAY', x0, y + 62, { size: 36, fam: F.FAM.label, weight: 700, tracking: 0.16, align: 'center', color: PAL.sub, alpha: sa });
      F.counter(ctx, v, v, 1, clamp(xp + 30, x0 + 150, x1 - 330), y + 118, { size: 84, align: 'left', alpha: sa * prog(t, M.years - 0.45, M.years - 0.2), format: (x) => '+' + Math.round(x), unit: 'MILLION YEARS', color: PAL.yellow });
    }
    // four faint question marks around North America
    SLOTC.forEach(([x, y], i) => { const a = prog(t, M.agree - 0.1 + i * 0.12, M.agree + 0.3 + i * 0.12); L.qmark(ctx, x, y + 4 * Math.sin(t * 2 + i), 150, 0.5 * a); });
  });
  cue(B0 + 0.05, 'whoosh_soft', -14); cue(M.years - 0.3, 'tick_counter', -16); cue(SPIN0, 'whoosh_big', -12); cue(M.models - 4.0, 'riser_tension', -12);
  for (let i = 0; i < 4; i++) cue(M.agree - 0.1 + i * 0.12, 'pop_ui', -22);

  // ================================================================== grid intro: four tiles grow out of the '?'s
  const G0 = B1, G1 = MODELS[0].t0;
  base(G0, G1, async (ctx, lt, t) => {
    const S = await ensureStills();
    spaceBg(ctx, t);
    const tiles = gridTiles(S, t).map((tl, i) => {
      const k = prog(t, G0 + i * 0.07, G0 + 0.5 + i * 0.07, E.outBack);
      const c = SLOTC[i], r = SLOT[i], s = lerp(0.18, 1, k);
      return Object.assign(tl, { rect: [c[0] - r[2] * s / 2, c[1] - r[3] * s / 2, r[2] * s, r[3] * s], alpha: clamp(k * 2), q: lerp(0.55, tl.q, prog(t, G0 + 0.3, G0 + 0.8)) });
    });
    drawTiles(ctx, t, tiles);
  });
  over(M.models - 0.12, MODELS[0].tLive + 0.75, (ctx, lt, t) => L.pillT(ctx, '4 MODELS, 50-300 MILLION YEARS OUT', W / 2, 96, t, M.models - 0.12, MODELS[0].tLive + 0.75, { size: 40, border: PAL.yellow }));
  cue(M.models - 0.08, 'pop_ui', -14);

  // ================================================================== s099-s102  the four models: expand tile -> live -> shrink back
  MODELS.forEach((m, mi) => {
    base(m.t0, m.tEnd, async (ctx, lt, t) => {
      const S = await ensureStills();
      if (t >= m.tLive && t < m.tShrink) { if (t < m.tHold) drawLive(ctx, m, t); else drawHold(ctx, m, t); return; }
      spaceBg(ctx, t);
      const tiles = gridTiles(S, t, { done: MODELS.map((_, j) => j < mi || (j === mi && t >= m.tShrink)) });
      const k = t < m.tLive ? prog(t, m.tExp, m.tLive, E.inOutExpo) : 1 - prog(t, m.tShrink, m.tEnd, E.inOutExpo);
      const act = tiles[mi]; tiles[mi] = null;
      drawTiles(ctx, t, tiles);
      if (k > 0.98) { ctx.drawImage(t < m.tLive ? S[mi].a : S[mi].b, 0, 0); }
      else drawTiles(ctx, t, [Object.assign(act, { rect: lerpR(SLOT[mi], FULL, k), radius: lerp(16, 0, k), q: act.q * (1 - k) })]);
    });
    cue(m.tExp, 'whoosh_soft', -15);
    cue(m.contact.t, 'thunk_heavy', mi === 2 ? -14 : -12);
    // MODEL pill
    const pin = [M.proxname, w.novoname, w.amasia, M.aurica][mi] - 0.09;
    over(pin, m.tShrink - 0.02, (ctx, lt, t) => {
      if (mi === 3) return; // Aurica handles its own (AU + RICA assembly)
      L.pillT(ctx, 'MODEL: ' + m.name, 96 + F.measure(ctx, 'MODEL: ' + m.name, { size: 42, fam: F.FAM.label, weight: 700, tracking: 0.08 }) / 2 + 24, 104, t, pin, m.tShrink - 0.02, { size: 42, border: m.col });
    });
    if (mi < 3) cue(pin + 0.02, 'pop_ui', -14);
  });
  // Proxima: "+250 MILLION YEARS" counter while North America crashes in
  over(w.africa99 + 0.3, M.proxname - 0.2, (ctx, lt, t) => {
    const a = prog(t, w.africa99 + 0.3, w.africa99 + 0.6) * (1 - prog(t, M.proxname - 0.5, M.proxname - 0.2));
    const p = prog(t, w.africa99 + 0.6, w.years99 - 0.05, E.outExpo);
    F.counter(ctx, 0, 250, p, 100, 132, { size: 76, align: 'left', alpha: a, format: (x) => '+' + Math.round(x), unit: 'MILLION YEARS', color: PAL.text });
  });
  cue(w.africa99 + 0.6, 'tick_counter', -16);
  // Aurica: AUSTRALIA + AMERICA, then AU + RICA assemble into the model name
  {
    const m = MODELS[3], tA = w.aus2 - 0.08, tN = M.aurica - 0.1, tOut = m.tShrink - 0.02;
    const PS = 42, fo = { size: PS, fam: F.FAM.label, weight: 700, tracking: 0.08 };
    over(tA, tOut, (ctx, lt, t) => {
      const ctxm = ctx;
      const full = 'AUSTRALIA + AMERICA', fw = F.measure(ctxm, full, fo), px = W / 2, py = 104;
      if (t < tN + 0.3) L.pillT(ctx, full, px, py, t, tA, tN + 0.3, { size: PS, border: PAL.green });
      // flying fragments AU (hero) + RICA (cyan) -> "MODEL: AURICA"
      const target = 'MODEL: AURICA', tw = F.measure(ctxm, target, fo), tx0 = 96 + 24, ty = 104;
      const k = prog(t, tN - 0.05, tN + 0.45, E.inOutExpo);
      if (t >= tN - 0.05) {
        if (k >= 1) { L.pillT(ctx, target, tx0 + tw / 2, ty, t, tN + 0.42, tOut, { size: PS, border: PAL.green }); }
        if (k < 1.0 || t < tN + 0.55) {
          const x0 = px - fw / 2, auX0 = x0, ricaX0 = x0 + F.measure(ctxm, 'AUSTRALIA + AME', fo);
          const auX1 = tx0 + F.measure(ctxm, 'MODEL: ', fo), ricaX1 = auX1 + F.measure(ctxm, 'AU', fo) + PS * 0.08;
          const fa = 1 - prog(t, tN + 0.45, tN + 0.6);
          const yy = lerp(py, ty, k) + PS * 0.36 - 60 * Math.sin(Math.PI * k);
          const sc = 1 + 0.9 * Math.sin(Math.PI * k);
          for (const [str, xa, xb, col] of [['AU', auX0, auX1, PAL.hero], ['RICA', ricaX0, ricaX1, PAL.cyan]]) {
            const xx = lerp(xa, xb, k); ctx.save(); ctx.translate(xx, yy - PS * 0.36); ctx.scale(sc, sc);
            F.text(ctx, str, 0, PS * 0.36, Object.assign({}, fo, { color: col, alpha: fa, shadowBlur: 10 })); ctx.restore();
          }
        }
      }
    });
    cue(tA + 0.02, 'pop_ui', -14); cue(tN + 0.4, 'pop_ui', -14); cue(M.middle - 0.05, 'shimmer', -18);
  }

  // ================================================================== s103  which neighbor? grid pulses, Explorer gag 10a, the splash, Tuesday
  const { Actor, tinyPlanet } = await import('../../lib/actors.js');
  const st = await api.newStage('ch6_gag', { shadowExtent: 4, hemi: 1.5, key: 2.6, rim: 1.7, exposure: 1.05 });
  const planet = await tinyPlanet(st, { radius: 3 }); planet.position.set(0, -3, 0);
  const hero = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });
  const hemi = st.scene.children.find(o => o.isHemisphereLight), rimL = st.scene.children.find(o => o.isDirectionalLight && o !== st.key);
  const dir3 = (lat, lon) => { const a = lat * Math.PI / 180, b = lon * Math.PI / 180; return new THREE.Vector3(Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)); };
  const qTop = (lat, lon) => new THREE.Quaternion().setFromUnitVectors(dir3(lat, lon), new THREE.Vector3(0, 1, 0));
  const Q_NA = qTop(40, -100), Q_AF = qTop(8, 18);
  const GA0 = M.neighbor - 0.14, GA1 = w.inaway + 0.0;
  const runL0 = M.neighbor + 0.05, runL1 = runL0 + 0.85, runR0 = runL1 + 0.3, runR1 = runR0 + 1.0;
  hero.play(runL0, 'Run_Left', { fade: 0.15 }).play(runL1, 'Idle', { fade: 0.15 }).play(runR0, 'Run_Right', { fade: 0.15 }).play(runR1, 'Idle', { fade: 0.2 });
  const GB0 = SEG('s104').start + 6.9, faint = M.mammal - 0.12;   // gag 10b
  hero.play(GB0 - 0.4, 'Idle_Neutral', { fade: 0.3 }).play(faint, 'Death', { fade: 0.12, once: true });
  const GD0 = M.breakup - 0.05;   // Gondwana callback: waving
  hero.play(GD0 - 0.3, 'Wave', { fade: 0.1 });
  const heroX = (t) => {
    if (t < runL0) return 0;
    if (t < runL1 + 0.2) return lerp(0, -1.05, prog(t, runL0 + 0.05, runL1, E.inOutSine));
    if (t < runR1 + 0.2) return lerp(-1.05, 1.0, prog(t, runR0 + 0.05, runR1, E.inOutSine));
    return lerp(1.0, 0.35, prog(t, runR1 + 0.3, runR1 + 1.6, E.inOutSine));
  };
  const setLights = (mode) => {
    if (mode === 'hot') { st.key.color.setHex(0xff6a35); st.key.intensity = 3.4; st.key.position.set(6, 5, 4); hemi.color.setHex(0xff9a6a); hemi.groundColor.setHex(0x3a1008); hemi.intensity = 1.2; rimL.color.setHex(0xffb070); rimL.intensity = 2.2; }
    else { st.key.color.setHex(0xfff1dc); st.key.intensity = 2.6; st.key.position.set(5, 9, 6); hemi.color.setHex(0xbfd8ff); hemi.groundColor.setHex(0x30261c); hemi.intensity = 1.5; rimL.color.setHex(0x7fb4ff); rimL.intensity = 1.9; }
  };
  const renderStage = (t, o) => {
    setLights(o.hot ? 'hot' : 'cool');
    planet.visible = o.planet !== false;
    planet.quaternion.copy(o.pq || Q_NA);
    hero.root.position.set(o.x || 0, o.y || 0, 0);
    hero.root.rotation.set(0, o.ry || 0, o.rz || 0);
    st.lookFrom(o.cam, o.target, o.fov || 30);
    return st.render(t);
  };
  const CORNER = [[100, 80, 456, 257], [W - 100 - 456, 80, 456, 257], [100, 520, 456, 257], [W - 100 - 456, 520, 456, 257]];
  const NEIGH = [{ t: M.a1, col: PAL.hero }, { t: M.a2, col: PAL.cyan }, { t: M.a3, col: PAL.yellow }, { t: M.a4, col: PAL.green }];
  const endTiles = (S, t, rects, glowFn) => S.map((s, i) => {
    const pu = t >= NEIGH[i].t - 0.1 ? Math.exp(-2.2 * (t - NEIGH[i].t + 0.1)) : 0;
    const on = t >= NEIGH[i].t - 0.1;
    return { img: s.b, rect: rects[i], alpha: 1, border: on ? NEIGH[i].col : 'rgba(244,246,250,0.45)', bw: on ? 4 : 2, glow: Math.max(pu, glowFn ? glowFn(i) : 0), dim: on ? 0 : 0.25 };
  });
  const N0 = MODELS[3].tEnd;
  base(N0, GA0, async (ctx, lt, t) => {
    const S = await ensureStills(); spaceBg(ctx, t);
    const tiles = endTiles(S, t, SLOT.map((r, i) => { const pu = t >= NEIGH[i].t - 0.1 ? Math.exp(-5 * (t - NEIGH[i].t + 0.1)) * 0.05 : 0; const c = SLOTC[i]; const s = 1 + pu; return [c[0] - r[2] * s / 2, c[1] - r[3] * s / 2, r[2] * s, r[3] * s]; }));
    drawTiles(ctx, t, tiles);
  });
  NEIGH.forEach(n => cue(n.t - 0.05, 'pop_ui', -20));
  // gag 10a
  base(GA0, GA1, async (ctx, lt, t) => {
    const S = await ensureStills(); spaceBg(ctx, t);
    const k = prog(t, GA0, GA0 + 0.5, E.inOutExpo);
    const x = heroX(t);
    const glowFn = (i) => { const left = i % 2 === 0; const r1 = env(t, runL0, runL1 + 0.3, 0.2, 0.3), r2 = env(t, runR0, runR1 + 0.3, 0.2, 0.3); return left ? r1 * (0.7 + 0.3 * Math.sin(t * 12)) : r2 * (0.7 + 0.3 * Math.sin(t * 12)); };
    drawTiles(ctx, t, endTiles(S, t, SLOT.map((r, i) => lerpR(r, CORNER[i], k)), glowFn));
    const ap = prog(t, GA0 + 0.15, GA0 + 0.6, E.out);
    if (ap > 0) {
      const a = 0.18 * Math.sin(t * 0.35) - 0.05, dist = lerp(4.9, 4.4, prog(t, GA0, GA1, E.inOutSine));
      const cv = renderStage(t, { x, y: -x * x / 6, rz: -Math.asin(x / 3), pq: new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), 0.05 * t).multiply(Q_NA), cam: [Math.sin(a) * dist, 0.42, Math.cos(a) * dist], target: [x * 0.35, 0.6, 0], fov: 30 });
      ctx.save(); ctx.globalAlpha = ap; ctx.drawImage(cv, 0, (1 - ap) * 140); ctx.restore();
    }
    // comment bubble
    const cb = prog(t, M.comments - 0.1, M.comments + 0.25, E.outBack);
    if (cb > 0) L.commentBubble(ctx, W / 2 + 250 + x * 60, 330, 0.85 * cb, t, clamp(cb * 2) * (1 - prog(t, GA1 - 0.25, GA1)));
  });
  over(w.oneword - 0.1, GA1 - 0.05, (ctx, lt, t) => L.pillT(ctx, 'ONE WORD: WHICH NEIGHBOR?', W / 2, 104, t, w.oneword - 0.1, GA1 - 0.05, { size: 42, border: PAL.yellow }));
  cue(runL0, 'whoosh_soft', -18); cue(runR0, 'whoosh_soft', -18); cue(M.comments - 0.08, 'pop_ui', -14);

  // the splash: continents slide together on the Equal Earth map (Antarctica stays home, as in Holden's joke)
  const EEI = img('ee');
  const C50 = await loadGeo('ne_50m_admin_0_countries');
  const ES = 0.5; // working scale of the EE canvases
  const EEG = { AM: [], AF: [], EA: [], OC: [] };
  for (const f of C50.features) {
    const P = f.properties, cont = P.CONTINENT, name = P.ADMIN || P.NAME;
    for (const r of rings(f)) {
      if (r.length < 4) continue;
      let sx = 0, sy = 0; for (const [lo, la] of r) { sx += lo; sy += la; } sx /= r.length; sy /= r.length;
      let k = null;
      if (cont === 'North America' || cont === 'South America') k = (sx < -150 && sy < 30) ? null : 'AM';
      else if (cont === 'Africa') k = 'AF';
      else if (cont === 'Europe' || cont === 'Asia') k = sx < -150 ? null : 'EA';
      else if (['Australia', 'Papua New Guinea', 'New Zealand'].includes(name)) k = 'OC';
      if (k) EEG[k].push(r);
    }
  }
  const eePath = (rs) => { const p = new Path2D(); for (const r of rs) { r.forEach(([lo, la], i) => { const [x, y] = L.ee(lo, la); i ? p.lineTo(x * ES, y * ES) : p.moveTo(x * ES, y * ES); }); p.closePath(); } return p; };
  const EW = Math.round(L.EE_W * ES), EH = Math.round(L.EE_H * ES);
  const EEBASE = L.makeCanvas(EW, EH);
  { const x = EEBASE.getContext('2d'); x.drawImage(EEI, 0, 0, EW, EH); const all = eePath(C50.features.flatMap(f => rings(f))); x.fillStyle = '#0c213d'; x.fill(all); x.strokeStyle = 'rgba(200,220,255,0.22)'; x.lineWidth = 1.4; x.setLineDash([5, 5]); x.stroke(eePath(coast.features.flatMap(f => rings(f)))); x.setLineDash([]); }
  const EECUT = {}, EECEN = {};
  for (const k in EEG) {
    const c = L.makeCanvas(EW, EH), x = c.getContext('2d'); const p = eePath(EEG[k]);
    x.save(); x.clip(p); x.drawImage(EEI, 0, 0, EW, EH); x.restore();
    EECUT[k] = c;
  }
  EECEN.AM = L.ee(-85, 15); EECEN.AF = L.ee(20, 5); EECEN.EA = L.ee(85, 45); EECEN.OC = L.ee(138, -25);
  const EET = L.ee(10, 12);
  const EEF = { AM: 0.52, AF: 0.12, EA: 0.42, OC: 0.62 };
  const SP0 = GA1, SP1 = SEG('s104').start - 0.15, tSplash = w.splash;
  base(SP0, SP1, (ctx, lt, t) => {
    ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
    const kz = prog(t, SP0, SP1, E.inOutSine);
    const z = lerp(0.98, 1.22, kz) * (W * 0.92 / EW), cx = lerp(EW / 2, EET[0] * ES, kz * 0.7), cy = lerp(EH / 2, EET[1] * ES + 30, kz * 0.7);
    ctx.save(); ctx.translate(W / 2, H / 2 + 10); ctx.scale(z, z); ctx.translate(-cx, -cy);
    ctx.drawImage(EEBASE, 0, 0);
    const pm = prog(t, w.holden - 0.1, tSplash, (x) => x * x * (3 - x) / 2);
    const settle = t > tSplash ? Math.exp(-4 * (t - tSplash)) * Math.sin((t - tSplash) * 16) : 0;
    for (const k of ['OC', 'EA', 'AF', 'AM']) {
      const f = EEF[k] * pm, dx = (EET[0] - EECEN[k][0]) * ES * f * (1 + 0.04 * settle), dy = (EET[1] - EECEN[k][1]) * ES * f * (1 + 0.04 * settle);
      ctx.drawImage(EECUT[k], dx, dy);
    }
    ctx.restore();
    // splash ring + droplets
    const u = t - tSplash;
    if (u > -0.05 && u < 1.6) {
      const sx = W / 2 + (EET[0] * ES - cx) * z, sy = H / 2 + 10 + (EET[1] * ES - cy) * z;
      ctx.save();
      for (let r = 0; r < 3; r++) { const uu = u - r * 0.14; if (uu < 0) continue; const rr = 60 + 520 * E.outExpo(clamp(uu / 1.2)); ctx.strokeStyle = `rgba(61,227,255,${0.8 * (1 - clamp(uu / 1.2))})`; ctx.lineWidth = 6 - r * 1.5; ctx.beginPath(); ctx.ellipse(sx, sy, rr, rr * 0.55, 0, 0, Math.PI * 2); ctx.stroke(); }
      const rr = F.rng(41);
      for (let i = 0; i < 18; i++) { const ang = -Math.PI * (0.1 + 0.8 * rr()), sp = 380 + 420 * rr(), x = sx + Math.cos(ang) * sp * u * 0.8, y = sy + Math.sin(ang) * sp * u + 900 * u * u; const a = 1 - clamp(u / 1.1); if (a <= 0) continue; ctx.fillStyle = `rgba(160,240,255,${a})`; ctx.beginPath(); ctx.arc(x, y, 6 + 6 * rr(), 0, Math.PI * 2); ctx.fill(); }
      ctx.restore();
    }
  }, { fadeIn: 0.3 });
  cue(w.holden - 0.1, 'whoosh_soft', -16); cue(tSplash - 0.05, 'splash_big', -18);
  // Tuesday: the Pangooy card flashes back for half a second
  over(M.tuesday - 0.08, M.tuesday + 0.5, (ctx, lt, t) => {
    const a = env(t, M.tuesday - 0.08, M.tuesday + 0.5, 0.06, 0.12);
    ctx.save(); ctx.fillStyle = `rgba(3,5,10,${0.45 * a})`; ctx.fillRect(0, 0, W, H); ctx.restore();
    const s = lerp(1.15, 1, prog(t, M.tuesday - 0.08, M.tuesday + 0.1, E.outBack));
    ctx.save(); ctx.translate(W / 2, H / 2 - 30); ctx.scale(s, s); L.pangooyCard(ctx, 0, 0, -0.04, t, a); ctx.restore();
  }, 7);
  cue(M.tuesday, 'bell_small', -14);

  // ================================================================== s104  heat map on the Proxima supercontinent, gag 10b
  const HT0 = SP1, HT1 = GB0;
  let heatReady = false;
  const PROX_END = (() => { const m = MODELS[0]; const o = {}; for (const p in m.plates) o[p] = m.plates[p].q; return o; })();
  const HTH = w.study + 1.45;  // heat fully on -> hold
  const camHeat = (t) => { const c = camAt([{ t: HT0, lat: 16, lon: -14, alt: 2.5 }, { t: HTH, lat: 12, lon: -6, alt: 2.42, ease: E.inOutSine }], Math.min(t, HTH), 0); c.lookOffset = [0.16, 0]; return c; };
  let HEATHOLD = null;
  base(HT0, HT1, (ctx, lt, t) => {
    if (!heatReady) { fut.setPose(PROX_END); fut.buildHeat(9); heatReady = true; }
    let d;
    if (t < HTH) {
      fut.setPose(PROX_END); fut.setTint({});
      fut.draw(ctx, camHeat(t), { look: FLOOK, desat: 0.1, heat: prog(t, w.study - 0.1, HTH - 0.05, E.inOut) });
      d = g.disc();
    } else {
      if (!HEATHOLD) { const c = L.makeCanvas(W, H); fut.setPose(PROX_END); fut.setTint({}); fut.draw(c.getContext('2d'), camHeat(HTH), { look: FLOOK, desat: 0.1, heat: 1 }); HEATHOLD = { c, d: g.disc() }; }
      const z = 1 + 0.045 * E.inOutSine(prog(t, HTH, HT1));
      ctx.save(); zoomAbout(ctx, z, -40 * prog(t, HTH, HT1)); ctx.drawImage(HEATHOLD.c, 0, 0); ctx.restore();
      d = { x: W / 2 - 40 * prog(t, HTH, HT1) + (HEATHOLD.d.x - W / 2) * z, y: H / 2 + (HEATHOLD.d.y - H / 2) * z, r: HEATHOLD.d.r * z };
    }
    // cool fringe pulse at the counter
    if (t > M.tenth - 0.1) {
      const a = env(t, M.tenth - 0.1, HT1, 0.3, 0.3) * (0.5 + 0.5 * Math.sin((t - M.tenth) * 5));
      ctx.save(); ctx.strokeStyle = `rgba(70,224,138,${0.35 * a})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(d.x, d.y, d.r + 6, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    }
  }, { fadeIn: 0.3 });
  over(HT0 + 0.4, HT1 - 0.05, (ctx, lt, t) => {
    L.pillT(ctx, 'MODEL', 96 + 70, 104, t, HT0 + 0.4, HT1 - 0.05, { size: 38, border: PAL.hero });
    const a = prog(t, M.tenth - 0.1, M.tenth + 0.2) * (1 - prog(t, HT1 - 0.35, HT1 - 0.05));
    if (a > 0) {
      const x = 1480, y = 470;
      F.text(ctx, 'LIVABLE FOR MAMMALS:', x, y - 110, { size: 44, fam: F.FAM.label, weight: 700, tracking: 0.12, align: 'center', color: PAL.text, alpha: a });
      const n = Math.round(lerp(10, 6, prog(t, M.tenth + 0.1, w.sixth - 0.05, E.inOut)));
      F.text(ctx, 'UNDER 1 IN ' + n, x, y + 20, { size: 120, fam: F.FAM.head, weight: 400, tracking: 0.02, align: 'center', color: n <= 6 ? PAL.hero : PAL.text, alpha: a, shadowBlur: 30 });
      ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = PAL.hero; const lw = 360 * prog(t, w.sixth - 0.05, w.sixth + 0.3, E.outExpo); ctx.fillRect(x - lw / 2, y + 52, lw, 5); ctx.restore();
    }
  });
  cue(HT0, 'whoosh_soft', -16); cue(M.tenth - 0.05, 'tick_counter', -16);
  // gag 10b: the Explorer wilts in the heat and faints on "Reminder"
  const GB1 = SEG('s105').start - 0.1;
  base(GB0, GB1, (ctx, lt, t) => {
    L.drawDrift(ctx, HOT, W, H, t, { zoom: 1.05, speed: 4 });
    const k = prog(t, GB0, GB1, E.inOutSine), a = 0.12 + 0.05 * Math.sin(t * 0.5), dist = lerp(4.7, 3.9, k);
    const cv = renderStage(t, { hot: true, x: 0, pq: new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), 0.04 * t).multiply(Q_AF), cam: [Math.sin(a) * dist, 0.38, Math.cos(a) * dist], target: [0, 0.55, 0], fov: 30 });
    // heat shimmer: draw the stage in horizontal strips with a sine x-offset in the band above the ground
    const y0 = 160, y1 = 760, sh = 6;
    ctx.drawImage(cv, 0, 0, W, y0, 0, 0, W, y0);
    for (let y = y0; y < y1; y += sh) { const amp = 2.6 * Math.sin(Math.PI * (y - y0) / (y1 - y0)); ctx.drawImage(cv, 0, y, W, sh, amp * Math.sin(y * 0.045 + t * 9), y, W, sh); }
    ctx.drawImage(cv, 0, y1, W, H - y1, 0, y1, W, H - y1);
    // rising heat lines
    ctx.save(); ctx.strokeStyle = 'rgba(255,220,180,0.10)'; ctx.lineWidth = 3;
    for (let i = 0; i < 7; i++) { const bx = 300 + i * 220, ph = (t * 0.6 + i * 0.37) % 1; ctx.beginPath(); for (let j = 0; j <= 10; j++) { const yy = 900 - ph * 500 - j * 18; const xx = bx + 10 * Math.sin(j * 0.9 + t * 4 + i); j ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); } ctx.stroke(); }
    ctx.restore();
  });
  cue(faint + 0.6, 'thunk_heavy', -22);

  // ================================================================== s105  tiles -> filmstrip; tear; the bookend drip globe
  const FW = 600, FH = 338, PITCH = 690, BANDY = 540, BANDH = 470;
  const drawBand = (ctx, xL, xR, o = {}) => {
    const y0 = BANDY - BANDH / 2;
    ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.fillStyle = '#0d0f14'; ctx.fillRect(xL, y0, xR - xL, BANDH);
    ctx.fillStyle = 'rgba(255,255,255,0.05)'; ctx.fillRect(xL, y0 + 8, xR - xL, 2); ctx.fillRect(xL, y0 + BANDH - 10, xR - xL, 2);
    const off = ((o.scroll || 0) % 70 + 70) % 70;
    ctx.fillStyle = 'rgba(230,236,245,0.78)';
    for (let x = xL - 70 + off; x < xR; x += 70) { F.round(ctx, x, y0 + 18, 34, 22, 5); ctx.fill(); F.round(ctx, x, y0 + BANDH - 40, 34, 22, 5); ctx.fill(); }
    ctx.restore();
  };
  const frameImg = (ctx, im, x, y, o = {}) => {
    ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
    ctx.fillStyle = '#05070D'; ctx.fillRect(x - FW / 2, y - FH / 2, FW, FH);
    if (im) ctx.drawImage(im, x - FW / 2, y - FH / 2, FW, FH);
    ctx.strokeStyle = o.border || 'rgba(255,255,255,0.18)'; ctx.lineWidth = o.bw || 2; ctx.strokeRect(x - FW / 2, y - FH / 2, FW, FH);
    ctx.restore();
  };
  const STRIP_A = GB1, STRIP_B = M.torn - 0.02, V1 = 540;
  const stripX = (i, t) => W / 2 + (i - 1.5) * PITCH - V1 * Math.max(0, t - (M.wins + 0.55));
  const SS = 0.74; // strip scale for the s105 row
  const drawStripComp = (ctx, t, S) => {
    spaceBg(ctx, t);
    const k = prog(t, M.wins - 0.08, M.wins + 0.55, E.inOutExpo);
    const ba = prog(t, M.wins + 0.1, M.wins + 0.5);
    const scr = -V1 * Math.max(0, t - (M.wins + 0.55));
    ctx.save(); ctx.translate(W / 2, BANDY); ctx.scale(SS, SS); ctx.translate(-W / 2, -BANDY);
    if (ba > 0) drawBand(ctx, -W, W * 2, { alpha: ba, scroll: scr });
    for (let i = 4; i < 10; i++) { const x = stripX(i, t); if (ba <= 0) continue; frameImg(ctx, null, x, BANDY, { alpha: ba, border: 'rgba(255,255,255,0.1)' }); }
    ctx.restore();
    S.forEach((s, i) => {
      const cx = W / 2 + (stripX(i, t) - W / 2) * SS, fw = FW * SS, fh = FH * SS;
      const r = lerpR(SLOT[i], [cx - fw / 2, BANDY - fh / 2, fw, fh], k);
      L.tile(ctx, s.b, r[0], r[1], r[2], r[3], { radius: lerp(16, 0, k), border: k > 0.95 ? 'rgba(255,255,255,0.18)' : NEIGH[i].col, borderW: lerp(4, 2, k) });
    });
  };
  base(STRIP_A, STRIP_B, async (ctx, lt, t) => { const S = await ensureStills(); drawStripComp(ctx, t, S); });
  cue(M.wins - 0.05, 'time_rewind', -18);
  // the tear + bookend globe
  const D0 = STRIP_B, D1 = SEG('s106').start - 0.2;
  const TEAR = (() => { const r = F.rng(7), pts = []; for (let y = -20; y <= H + 20; y += 36) pts.push([W / 2 + (r() - 0.5) * 70 + Math.sin(y * 0.02) * 30, y]); return pts; })();
  base(D0, D1, async (ctx, lt, t) => {
    const cam = camAt([{ t: D0, lat: -29, lon: 12, alt: 3.05, ease: E.lin }, { t: D1, lat: -31, lon: 24, alt: 2.9 }], t, 0);
    globe(ctx, cam, { desat: 0.3, dim: 0.35, ovAlpha: 1 }, COLD);
    ['froward', 'agulhas', 'kanya'].forEach((k, i) => {
      const a0 = w.fingerprint - 0.1 + i * 0.15; if (t < a0) return;
      strokeProjected(ctx, g, TIPRUN[k], { p: prog(t, a0, a0 + 0.4, E.out), color: '#ffffff', width: 3.2, glow: true });
      const q = proj(...TIPS[k]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 6, color: '#ffffff', ring: ((t - a0) * 1.2) % 1 });
    });
    drawArcs(ctx, t, M.been - 0.08);
    poleRing(ctx, t);
    // torn halves of the filmstrip fly apart
    const tp = prog(t, D0, D0 + 0.6, (x) => x * x);
    if (tp < 1) {
      const S = await ensureStills();
      for (const side of [-1, 1]) {
        ctx.save();
        ctx.translate(side * tp * W * 0.62, tp * 80); ctx.rotate(side * tp * 0.12);
        ctx.beginPath();
        if (side < 0) { ctx.moveTo(-40, -40); TEAR.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(-40, H + 40); }
        else { ctx.moveTo(W + 40, -40); TEAR.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(W + 40, H + 40); }
        ctx.closePath(); ctx.clip();
        drawStripComp(ctx, D0 + Math.min(lt, 0.3), S);
        ctx.restore();
        // torn paper edge
        ctx.save(); ctx.translate(side * tp * W * 0.62, tp * 80); ctx.rotate(side * tp * 0.12);
        ctx.strokeStyle = 'rgba(240,235,220,0.85)'; ctx.lineWidth = 5; ctx.beginPath(); TEAR.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); ctx.restore();
      }
    }
  });
  cue(M.torn - 0.04, 'paper_rustle', -12); cue(w.fingerprint - 0.1, 'pop_ui', -18); cue(M.been - 0.1, 'shimmer', -18);

  // ================================================================== s106  1620 flick, matching capes, "not an accident", the breakup
  const BC0 = D1, BC1 = wf('s106', 'matching') - 0.2;
  base(BC0, BC1, (ctx, lt, t) => {
    L.drawDrift(ctx, DESK, W, H, t, { zoom: 1.05 });
    L.printKB(ctx, img('bacon'), prog(t, BC0, BC1), [250, 160, 560, 688], [0.5, 0.42, 1.0], [0.5, 0.36, 1.16], { grade: 'sepia', vig: 0.35, rot: -0.02 });
    const p = prog(t, M.ago - 0.75, M.ago - 0.03, E.outExpo);
    const a = prog(t, BC0 + 0.05, BC0 + 0.35);
    F.counter(ctx, 2026, 1620, p, 1330, 590, { size: 230, alpha: a, format: (v) => String(Math.round(v)), color: p >= 1 ? PAL.yellow : PAL.text });
    ctx.save(); ctx.globalAlpha = a * prog(t, M.ago - 0.05, M.ago + 0.3); ctx.fillStyle = PAL.yellow; const lw = 420 * prog(t, M.ago - 0.05, M.ago + 0.4, E.outExpo); ctx.fillRect(1330 - lw / 2, 640, lw, 6); ctx.restore();
  }, { fadeIn: 0.25 });
  cue(BC0 + 0.05, 'paper_rustle', -16); cue(M.ago - 0.75, 'tick_counter', -16);
  const CP0 = BC1, CP1 = M.acc2 - 0.12;
  base(CP0, CP1, (ctx, lt, t) => {
    const cam = camAt([{ t: CP0, lat: -22, lon: -24, alt: 2.95 }, { t: CP1, lat: -27, lon: -18, alt: 2.7 }], t, 0);
    globe(ctx, cam, { desat: 0.3, dim: 0.35, ovAlpha: 1 }, COLD);
    strokeProjected(ctx, g, R_SA, { p: prog(t, CP0 + 0.05, CP0 + 1.0, E.out), color: '#ffffff', width: 2.2 });
    strokeProjected(ctx, g, R_AF, { p: prog(t, CP0 + 0.25, CP0 + 1.2, E.out), color: '#ffffff', width: 2.2 });
    [['froward', 0], ['agulhas', 0.25]].forEach(([k, d]) => { const a0 = w.capes - 0.08 + d; if (t < a0) return; const q = proj(...TIPS[k]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 9, color: '#ffffff', ring: ((t - a0) * 0.9) % 1 }); });
  });
  cue(CP0, 'whoosh_soft', -16); cue(w.capes - 0.06, 'pop_ui', -16);
  const BX = { quod: [0.553, 0.131, 0.276, 0.017], cidit: [0.079, 0.153, 0.064, 0.016] };
  const PG0 = CP1, PG1 = M.breakup - 0.42;
  base(PG0, PG1, (ctx, lt, t) => {
    L.drawDrift(ctx, DESK, W, H, t, { zoom: 1.05 });
    const m = L.printKB(ctx, img('p246'), prog(t, PG0, PG1), [330, 70, 1260, 700], [0.46, 0.142, 1.25], [0.454, 0.146, 1.28], { grade: 'sepia', vig: 0.3 });
    ctx.save(); ctx.beginPath(); ctx.rect(330, 70, 1260, 700); ctx.clip(); // marks never leave the page
    L.highlight(ctx, m, BX.quod, prog(t, M.acc2 + 0.05, M.acc2 + 0.4), { alpha: 0.18 });
    L.underline(ctx, m, BX.quod, prog(t, M.acc2 - 0.08, M.acc2 + 0.35, E.inOut));
    L.underline(ctx, m, BX.cidit, prog(t, M.acc2 + 0.35, M.acc2 + 0.55, E.inOut));
    const gold = prog(t, M.right2 - 0.1, M.right2 + 0.3);
    if (gold > 0) {
      const pu = 1 + 0.6 * Math.exp(-3 * Math.max(0, t - M.right2)) * Math.abs(Math.sin((t - M.right2) * 9));
      L.underline(ctx, m, BX.quod, 1, { color: PAL.yellow, alpha: gold, width: 6 * pu, glowColor: '#FFE27A' });
      L.underline(ctx, m, BX.cidit, 1, { color: PAL.yellow, alpha: gold, width: 6 * pu, glowColor: '#FFE27A' });
    }
    ctx.restore();
  });
  cue(M.acc2 - 0.05, 'shimmer', -18); cue(M.right2 - 0.05, 'pop_ui', -16);
  // headline: NOT AN ACCIDENT. A BREAKUP.
  {
    const hs = 96, tA = w.wasnt - 0.1, tB = M.breakup - 0.08, tOut = SEG('s107').start + 0.55;
    over(tA, tOut, (ctx, lt, t) => {
      const fo = { size: hs, fam: F.FAM.head, weight: 400, tracking: 0.02 };
      const w1 = ['NOT', 'AN', 'ACCIDENT.'], w2 = ['A', 'BREAKUP.'];
      const gap = hs * 0.28, wid = (ws) => ws.reduce((s, x) => s + F.measure(ctx, x, fo), 0) + gap * (ws.length - 1);
      const tw = wid(w1) + gap * 1.4 + wid(w2), x0 = W / 2 - tw / 2, y = 925;
      const a = 1 - prog(t, tOut - 0.35, tOut);
      ctx.save(); ctx.globalAlpha = a;
      const bgA = prog(t, tA, tA + 0.3) * 0.82; const bg = ctx.createLinearGradient(0, y - 150, 0, H); bg.addColorStop(0, 'rgba(3,5,10,0)'); bg.addColorStop(0.5, `rgba(3,5,10,${bgA * 0.9})`); bg.addColorStop(1, `rgba(3,5,10,${bgA})`); ctx.fillStyle = bg; ctx.fillRect(0, y - 150, W, H - y + 150);
      F.headline(ctx, w1, x0, y, t - tA, { size: hs, per: 0.07, align: 'left' });
      F.headline(ctx, ['A', { w: 'BREAKUP.', c: PAL.hero }], x0 + wid(w1) + gap * 1.4, y, t - tB, { size: hs, per: 0.08, align: 'left' });
      ctx.restore();
    }, 7);
  }
  // Gondwana snaps apart; Antarctica keeps the house (waving Explorer + porch light)
  const GO0 = PG1, GO1 = SEG('s107').start + 0.75;
  const tSnap = M.breakup - 0.05;
  const gondView = (t) => {
    const k = prog(t, tSnap + 0.05, tSnap + 0.95, E.inOut);
    const an = gond.ptAt('AN', -86, 40, 180 * (1 - E.outExpo(prog(t, tSnap, tSnap + 1.0))));
    const [alat, alon] = L.ll3(an);
    const lat = lerp(-46, alat + 9, k), lon = lerp(14, alon, k);
    return L.orthoView({ lat, lon, cx: W / 2, cy: lerp(560, 470, k), R: lerp(430, 900, k) * (1 + 0.01 * Math.sin(t)), roll: 0 });
  };
  const drawGond = (ctx, t) => {
    ctx.drawImage(SPACE, 0, 0);
    const V = gondView(t);
    const sp = E.outExpo(prog(t, tSnap, tSnap + 1.0));
    const shake = t > tSnap && t < tSnap + 0.3 ? Math.sin((t - tSnap) * 90) * 6 * (1 - (t - tSnap) / 0.3) : 0;
    ctx.save(); ctx.translate(shake, 0);
    const TT = {}; for (const k of ['SA', 'AF', 'IN', 'MG', 'AU']) TT[k] = 180 * (1 - sp); TT.AN = 180 * (1 - sp);
    // pieces fly north: extra push away from Antarctica (exaggerated, fades as they leave)
    gond.draw(ctx, V, TT, { alpha: { SA: 1 - 0.4 * sp, AF: 1 - 0.4 * sp, IN: 1 - 0.4 * sp, MG: 1 - 0.4 * sp, AU: 1 - 0.4 * sp } });
    // the snap flash along the old seams
    if (t > tSnap - 0.02 && t < tSnap + 0.6) { const c = V.p(-62, 20); L.impact(ctx, c[0], c[1], t - tSnap, { scale: 1.3, color: '#ffffff' }); }
    // Antarctica ring + waving Explorer + porch light
    const anc = gond.ptAt('AN', -84, 40, 180 * (1 - sp)); const P = V.pv(anc);
    const ra = prog(t, tSnap + 0.35, tSnap + 0.7);
    L.yRing(ctx, P[0], P[1] + 10, 60 * V.R / 430, t, ra);
    if (t > tSnap + 0.45) {
      const s = 0.46 * V.R / 430 * E.outBack(prog(t, tSnap + 0.45, tSnap + 0.8));
      const cv = renderStage(t, { planet: false, x: 0, ry: 0.25, cam: [0.4, 0.8, 4.4], target: [0, 0.52, 0], fov: 30 });
      const cw = 700, chh = 900, sx = W / 2 - cw / 2, sy = H / 2 - 520;
      ctx.drawImage(cv, sx, sy, cw, chh, P[0] - cw * s / 2, P[1] - chh * s * 0.78, cw * s, chh * s);
      L.porchLight(ctx, P[0] + 150 * s, P[1] + 10 * s, 1.7 * s, prog(t, tSnap + 0.85, tSnap + 1.05), t);
    }
    ctx.restore();
  };
  base(GO0, GO1, (ctx, lt, t) => drawGond(ctx, t));
  cue(tSnap, 'impact_short', -12);

  // ================================================================== s107-s108  every map is one frame: the filmstrip; the next frame is the live globe
  const PALEO_T = [200, 150, 100, 50];
  let PSTILLS = null;
  const ensurePaleo = () => PSTILLS || (PSTILLS = (async () => {
    const out = [];
    for (const Tm of PALEO_T) {
      const polys = await api.loadJSON(`paleo/coast_${String(Tm).padStart(3, '0')}.json`);
      const c = L.makeCanvas(FW, FH), x = c.getContext('2d'); x.drawImage(SPACE, 0, 0, FW, FH);
      drawPaleoPolys(x, L.orthoView({ lat: -20, lon: 10, cx: FW / 2, cy: FH / 2, R: 148 }), polys);
      out.push(c);
    }
    // today, photoreal, same framing
    const big = L.makeCanvas(W, H);
    globe(big.getContext('2d'), { lat: -20, lon: 10, alt: 2.873 }, { desat: 0.12 }, null);
    const c = L.makeCanvas(FW, FH); c.getContext('2d').drawImage(big, 0, 0, FW, FH); out.push(c);
    return out;
  })());
  const FS0 = GO1, FS1 = M.shot + 0.75;
  const TODAY_I = 4, BLANK_I = 9;
  const V2 = (BLANK_I - TODAY_I) * PITCH / (M.shot - M.frame);
  const fX = (i, t) => W / 2 + (i - TODAY_I) * PITCH + V2 * (M.frame - t);
  // Afar camera (shared by the strip hole and the Afar scene)
  const camAfar = (t) => {
    const c = camAt([{ t: M.shot - 0.05, lat: 4, lon: 30, alt: 3.0 }, { t: M.shot + 2.9, lat: 8.6, lon: 40.3, alt: 0.38, tilt: 40, heading: -8, ease: E.inOut },
      { t: SEG('s109').start - 0.3, lat: 9.0, lon: 40.6, alt: 0.355, tilt: 42, heading: -3 }, { t: SEG('s109').start + 1.45, lat: 9.6, lon: 41.6, alt: 0.44, tilt: 36, heading: 0 },
      ], Math.min(t, SEG('s109').start + 1.45), 0);
    const ko = prog(t, SEG('s109').start - 0.2, SEG('s109').start + 1.4, E.inOut);
    c.lookOffset = ko > 0 ? [0.27 * ko, 0.03 * ko] : null;
    return c;
  };
  const AFLOOK = { desat: 0.08, dim: 0, ovAlpha: 0, relief: 1.0, exposure: 1.3 };
  base(FS0, FS1, async (ctx, lt, t) => {
    const P = await ensurePaleo(); const S = await ensureStills();
    const live = t >= M.shot - 0.05, tt = Math.min(t, M.shot - 0.05);
    const sZ = lerp(0.5, 1, prog(t, FS0 + 0.65, M.frame - 0.12, E.inOut));
    const zoom = live ? lerp(1, W / FW * 1.02, prog(t, M.shot - 0.05, M.shot + 0.7, inExpo)) : 1 + 0.06 * prog(t, M.shot - 1.2, M.shot - 0.05, E.inOut);
    const fxB = fX(BLANK_I, tt);
    const hole = [fxB - FW / 2, BANDY - FH / 2, FW, FH];
    if (live) globe(ctx, camAfar(t), AFLOOK, null);
    ctx.save();
    ctx.translate(fxB, BANDY); ctx.scale(zoom, zoom); ctx.translate(-fxB, -BANDY);
    ctx.translate(W / 2, BANDY); ctx.scale(sZ, sZ); ctx.translate(-W / 2, -BANDY);
    if (live) { ctx.beginPath(); ctx.rect(-W * 8, -H * 8, W * 17, H * 17); ctx.rect(hole[0], hole[1], hole[2], hole[3]); ctx.clip('evenodd'); }
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); spaceBg(ctx, t); ctx.restore();
    drawBand(ctx, -W * 3, W * 4, { scroll: -V2 * tt });
    const xMin = W / 2 - W / 2 / sZ - FW, xMax = W / 2 + W / 2 / sZ + FW;
    const ims = [...P.slice(0, 4), P[4], ...S.map(s => s.b)];
    for (let i = 0; i < 12; i++) {
      const x = fX(i, tt); if (x < xMin || x > xMax) continue;
      if (i === BLANK_I && live) { ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 3; ctx.strokeRect(hole[0], hole[1], FW, FH); continue; }
      const hl = i === TODAY_I ? env(t, M.frame - 0.1, M.frame + 1.6, 0.15, 0.6) : 0;
      if (i < ims.length) {
        frameImg(ctx, ims[i], x, BANDY, { border: hl > 0 ? `rgba(255,210,63,${0.3 + 0.7 * hl})` : 'rgba(255,255,255,0.18)', bw: 2 + 4 * hl });
        if (hl > 0) { ctx.save(); ctx.strokeStyle = `rgba(255,210,63,${0.25 * hl})`; ctx.lineWidth = 16; ctx.strokeRect(x - FW / 2, BANDY - FH / 2, FW, FH); ctx.restore(); }
      } else {
        frameImg(ctx, null, x, BANDY, { border: 'rgba(255,255,255,0.12)' });
        if (i === BLANK_I) { // viewfinder corners + blinking rec dot: "already being shot"
          const bx = x - FW / 2 + 26, by = BANDY - FH / 2 + 22, bw = FW - 52, bh = FH - 44;
          ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = 3;
          for (const [cx, cy, sx, sy] of [[bx, by, 1, 1], [bx + bw, by, -1, 1], [bx, by + bh, 1, -1], [bx + bw, by + bh, -1, -1]]) { ctx.beginPath(); ctx.moveTo(cx + sx * 34, cy); ctx.lineTo(cx, cy); ctx.lineTo(cx, cy + sy * 34); ctx.stroke(); }
          if (Math.floor(t * 2) % 2 === 0) { ctx.fillStyle = '#ff3b3b'; ctx.beginPath(); ctx.arc(bx + 26, by + 26, 9, 0, Math.PI * 2); ctx.fill(); }
          ctx.restore();
        }
      }
    }
    ctx.restore();
    // the Gondwana view shrinks into its frame at the start
    const sk = prog(t, FS0, FS0 + 0.7, E.inOutExpo);
    if (sk < 1) {
      const x3 = W / 2 + (fX(3, tt) - W / 2) * sZ, w3 = FW * sZ, h3 = FH * sZ;
      const tgt = [x3 - w3 / 2, BANDY - h3 / 2, w3, h3], r = lerpR(FULL, tgt, sk);
      ctx.save(); ctx.globalAlpha = 1 - prog(sk, 0.75, 1);
      ctx.beginPath(); ctx.rect(r[0], r[1], r[2], r[3]); ctx.clip();
      ctx.translate(r[0], r[1]); ctx.scale(r[2] / W, r[3] / H); drawGond(ctx, t);
      ctx.restore();
    }
  });
  cue(SEG('s107').start + 0.3, 'riser_tension', -18); cue(M.frame - 0.05, 'bell_small', -22);

  // ================================================================== s108-s109  Afar: three cracks in a Y; end screen
  const AF0 = FS1, AF1 = END;
  const ARMS = [densify(ARM_RS, 6), densify(ARM_GA, 6), densify(ARM_EA, 6)], ARM2 = densify(ARM_EA2, 6);
  const armPts = (pts) => { const out = []; for (const [la, lo] of pts) { const q = proj(la, lo); if (q.visible) out.push([q.x, q.y]); } return out; };
  const band = (ctx, pts, wd, a) => {
    if (pts.length < 2 || wd < 0.5) return;
    const lft = [], rgt = [];
    for (let i = 0; i < pts.length; i++) { const p0 = pts[Math.max(0, i - 1)], p1 = pts[Math.min(pts.length - 1, i + 1)]; let dx = p1[0] - p0[0], dy = p1[1] - p0[1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l; const tp = Math.min(1, i / 3, (pts.length - 1 - i) / 3 + 0.25); lft.push([pts[i][0] - dy * wd * tp, pts[i][1] + dx * wd * tp]); rgt.push([pts[i][0] + dy * wd * tp, pts[i][1] - dx * wd * tp]); }
    ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); lft.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); for (let i = rgt.length - 1; i >= 0; i--) ctx.lineTo(rgt[i][0], rgt[i][1]); ctx.closePath();
    ctx.fillStyle = 'rgba(122,20,6,0.85)'; ctx.fill(); ctx.restore();
  };
  const drawRift = (ctx, t) => {
    const cp = prog(t, M.cracks - 0.1, M.cracks + 0.9, E.inOut);
    const wide = 1.5 + 7 * prog(t, SEG('s109').start, END, E.lin);
    ARMS.forEach((pts, i) => {
      const P = armPts(pts); if (P.length < 2) return;
      const pul = i === 2 && t > M.eafr - 0.1 ? 0.5 + 0.5 * Math.sin((t - M.eafr) * 7) : 0;
      if (cp >= 1) band(ctx, P, wide, 1);
      F.glowPath(ctx, P, { p: cp, color: i === 2 ? '#FF7A45' : PAL.hero, width: 6 + 3 * pul, glowColor: '#FF5A36' });
      F.glowPath(ctx, P, { p: cp, color: '#fff3d6', width: 1.6, alpha: 0.85 });
    });
    const ep = prog(t, M.eafr - 0.1, M.eafr + 1.8, E.inOut);
    if (ep > 0) { const P = armPts(ARM2); if (P.length > 1) { const pul = 0.5 + 0.5 * Math.sin((t - M.eafr) * 7); if (ep >= 1) band(ctx, P, wide * 0.8, 1); F.glowPath(ctx, P, { p: ep, color: '#FF7A45', width: 4.5 + 2.5 * pul, glowColor: '#FF5A36', dash: null }); F.glowPath(ctx, P, { p: ep, color: '#fff3d6', width: 1.4, alpha: 0.8 }); } }
    // sparks drifting along the arms
    if (cp >= 1) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ARMS.forEach((pts, i) => { const P = armPts(pts); if (P.length < 2) return; for (let j = 0; j < 4; j++) { const u = ((t * 0.18 + j / 4 + i * 0.13) % 1); const idx = Math.min(P.length - 1, Math.floor(u * (P.length - 1))); const q = P[idx]; const gg = ctx.createRadialGradient(q[0], q[1], 0, q[0], q[1], 16); gg.addColorStop(0, 'rgba(255,230,170,0.85)'); gg.addColorStop(1, 'rgba(255,120,60,0)'); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(q[0], q[1], 16, 0, Math.PI * 2); ctx.fill(); } });
      ctx.restore();
    }
    // Afar marker
    if (t > M.afar - 0.1) { const q = proj(AFAR[0], AFAR[1]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 8, color: '#ffffff', ring: ((t - M.afar) * 0.8) % 1 }); }
  };
  const S109 = SEG('s109').start;
  const AFH = S109 + 1.45;
  let AFHOLD = null;
  base(AF0, AF1, (ctx, lt, t) => {
    if (t < AFH) { globe(ctx, camAfar(t), AFLOOK, null); drawRift(ctx, t); }
    else {
      const cam = camAfar(AFH);
      if (!AFHOLD) { const c = L.makeCanvas(W, H); globe(c.getContext('2d'), cam, AFLOOK, null); AFHOLD = c; }
      const k = prog(t, AFH, END, E.lin); // keeps drifting to the last frame
      ctx.save(); zoomAbout(ctx, 1 + 0.085 * k, -50 * k, 20 * k); ctx.drawImage(AFHOLD, 0, 0);
      GSET(cam); drawRift(ctx, t); ctx.restore();
    }
    // end screen: calm the right side for the end-screen elements
    const ea = prog(t, S109 - 0.1, S109 + 1.2, E.inOut);
    if (ea > 0) {
      const gr = ctx.createLinearGradient(820, 0, W, 0); gr.addColorStop(0, 'rgba(3,5,10,0)'); gr.addColorStop(0.35, `rgba(3,5,10,${0.55 * ea})`); gr.addColorStop(1, `rgba(3,5,10,${0.72 * ea})`);
      ctx.fillStyle = gr; ctx.fillRect(820, 0, W - 820, H);
    }
  });
  over(w.giant - 0.3, S109 - 0.1, (ctx, lt, t) => L.pillT(ctx, "A CONTINENT CRACKING IN A 'Y'", W / 2, 104, t, w.giant - 0.3, S109 - 0.1, { size: 42, border: PAL.hero }));
  // end-screen placeholders: next-video tile frame + subscribe ring (interior left empty for YouTube elements)
  const VT = [1010, 240, 800, 450], SUB = [1110, 830];
  over(M.here - 0.1, END, (ctx, lt, t) => {
    const a = prog(t, M.here - 0.1, M.here + 0.35, E.out);
    const [x, y, w_, h_] = VT; const s = lerp(0.94, 1, E.outBack(a));
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x + w_ / 2, y + h_ / 2); ctx.scale(s, s); ctx.translate(-(x + w_ / 2), -(y + h_ / 2));
    ctx.fillStyle = 'rgba(5,8,14,0.55)'; F.round(ctx, x, y, w_, h_, 14); ctx.fill();
    ctx.strokeStyle = 'rgba(244,246,250,0.85)'; ctx.lineWidth = 3; F.round(ctx, x, y, w_, h_, 14); ctx.stroke();
    // light sweep running around the border
    const per = 2 * (w_ + h_), u = ((t - M.here) * 420) % per;
    const pt = (d) => { d = ((d % per) + per) % per; if (d < w_) return [x + d, y]; d -= w_; if (d < h_) return [x + w_, y + d]; d -= h_; if (d < w_) return [x + w_ - d, y + h_]; d -= w_; return [x, y + h_ - d]; };
    const pts = []; for (let k = 0; k <= 20; k++) pts.push(pt(u + k * 12));
    F.glowPath(ctx, pts, { color: PAL.yellow, width: 4 });
    ctx.restore();
    F.headline(ctx, ['WATCH', { w: 'NEXT', c: PAL.yellow }], x + w_ / 2, y - 34, t - (M.here - 0.1), { size: 70, per: 0.05 });
    // subscribe ring + label
    const sa = prog(t, M.sub2 - 0.1, M.sub2 + 0.3, E.out);
    if (sa > 0) {
      const [sx, sy] = SUB, r = 74;
      const pul = 0.5 + 0.5 * Math.sin((t - M.sub2) * 4.5);
      ctx.save(); ctx.globalAlpha = sa;
      for (const [lw, al] of [[22, 0.10 + 0.08 * pul], [12, 0.22 + 0.1 * pul]]) { ctx.strokeStyle = `rgba(255,59,59,${al})`; ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI * 2); ctx.stroke(); }
      ctx.strokeStyle = '#FF3B3B'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(sx, sy, r, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
      ctx.save(); const ps = lerp(0.85, 1, E.outBack(sa)); ctx.translate(sx + r + 40, sy); ctx.scale(ps, ps);
      F.pill(ctx, 'SUBSCRIBE', 0, 0, { anchor: 'left', size: 44, alpha: sa, bg: `rgba(220,30,30,${0.75 + 0.2 * pul})`, color: '#ffffff' });
      ctx.restore();
    }
  }, 7);
  cue(M.shot - 0.08, 'whoosh_big', -12); cue(M.cracks - 0.1, 'rumble_quake', -12); cue(M.cracks + 1.0, 'riser_tension', -14);
  cue(M.afar - 0.05, 'pop_ui', -16); cue(M.here - 0.08, 'pop_ui', -14); cue(M.sub2 - 0.05, 'pop_ui', -12);

  // sanity: base coverage report (debug only, no drawing)
  return scenes;
}
