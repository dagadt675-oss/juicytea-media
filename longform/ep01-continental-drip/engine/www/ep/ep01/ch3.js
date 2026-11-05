// Chapter 3 — "Is Earth secretly a pyramid?" (s045–s056, 5:57.7–8:01.5)
// William Lowthian Green's tetrahedral Earth: title page -> Hawaii -> Figure 1 -> bent-card demo -> callback triangles ->
// tetra-Earth + Explorer gag 6a -> 5-point checklist -> 1899 journal -> North America's antipode -> 1918 kids' page ->
// "how do we know it's wrong?" -> oblate measure / red X / radioactive cut-away -> gag 6b (pyramid pops back) ->
// detective board -> Ortelius 1570 -> photoreal globe coasts -> Greenland tip-pop on the flat map, dip to white.
import * as F from '../../lib/fx.js';
import { globeShot } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, makeCanvas, fillEquirect, strokeProjected, gcLine } from '../../lib/geo.js';
import { region, dripArrow } from '../../lib/beats.js';
import { keyAt, cv, deskBg, shadowSprite, drawPage, highlighter, underline, ee, EE_W, EE_H, inwardArrows, questionMark, stamp, redX, checkMark, wrap, glowSprite } from './ch3_lib.js';
import { makeTetraRig } from './ch3_tetra.js';
import { makeCardRig, makeKidsRig, makeCutRig } from './ch3_stages.js';
const { PAL, E, prog, env, clamp, lerp } = F;

const IMG = 'ep/ep01/img/';
const COAST_SA = [[-50.58, 0.42], [-48.12, -0.74], [-47.4, -0.63], [-44.65, -1.75], [-43.38, -2.38], [-39.96, -2.86], [-37.17, -4.91], [-35.39, -5.25], [-34.97, -8.41], [-38.24, -12.84], [-38.85, -12.79], [-39.15, -17.7], [-41.0, -22.0], [-42.04, -22.95], [-44.64, -23.06], [-48.73, -25.37], [-48.8, -28.58], [-50.58, -30.44], [-52.04, -32.11], [-52.65, -33.14], [-54.17, -34.67], [-57.3, -35.19], [-57.34, -36.03], [-56.7, -36.43], [-57.65, -38.17], [-59.83, -38.84], [-62.33, -38.8], [-62.4, -40.89], [-65.13, -40.88], [-64.99, -42.1], [-65.25, -43.57], [-65.64, -45.01], [-66.94, -45.26], [-67.6, -46.05], [-65.85, -47.16], [-67.47, -48.95], [-67.91, -49.98], [-69.47, -51.58], [-68.44, -52.36]];
const COAST_AF = [[-17.05, 20.81], [-16.21, 20.23], [-16.51, 19.36], [-16.03, 17.89], [-16.57, 15.73], [-17.54, 14.76], [-16.44, 13.35], [-16.78, 12.47], [-15.94, 11.79], [-15.08, 11.97], [-13.69, 9.93], [-12.49, 7.39], [-9.13, 5.05], [-7.54, 4.35], [-4.36, 5.3], [-2.0, 4.76], [3.72, 6.6], [5.46, 5.61], [6.08, 4.29], [8.29, 4.56], [9.69, 4.06], [9.95, 3.08], [9.32, 0.55], [8.7, -0.59], [12.24, -5.81], [12.28, -6.12], [13.38, -8.37], [13.0, -9.05], [13.85, -11.05], [11.75, -15.83], [11.78, -18.0], [14.46, -22.45], [14.97, -26.32], [18.21, -31.74], [17.85, -32.83], [18.35, -34.19], [20.02, -34.79]];

export async function build(api, C) {
  const W = api.W, H = api.H;
  const T = (m) => C.T(m);
  const norm = (s) => s.toLowerCase().replace(/[^a-z'-]/g, '').replace(/'/g, '');
  const word = (seg, w, n = 0) => { const ws = C.words(seg).filter(x => norm(x.w) === norm(w)); if (!ws[n]) throw new Error('ch3 word ' + seg + ' ' + w); return ws[n].start; };
  const S = (id) => C.seg(id).start;
  // ---- anchors (absolute seconds) ----
  const A = {
    hawaii: T('hawaii'), obsessed: T('obsessed'), card: T('card'), water: T('water'), pyr2: T('pyr2'), cool: T('cool'), tet: T('tet'), pyr4: T('pyr4'),
    pred: T('pred'), c1: T('c1'), c2: T('c2'), c3: T('c3'), c4: T('c4'), c5: T('c5'), main: T('main'), geol: T('geol'), squeeze: T('squeeze'), geo: T('geo'),
    io: T('io'), mag: T('mag'), pyramid: T('pyramid'), tight: T('tight'), how: T('how'), measure: T('measure'), notp: T('notp'), rad: T('rad'),
    stall: T('stall'), suspect: T('suspect'), maps: T('maps'), say: T('say'),
    // markers whose names are reused later in the episode (real, drips) -> word times inside our segments
    real: word('s055', 'real.'), drips: word('s056', 'drips.'),
    green: word('s045', 'Green.'), tips: word('s046', 'tips'), demo: word('s046', 'demonstrated'),
    L1: word('s048', 'Most'), L2: word('s048', 'Three'), L3: word('s049', 'An'), L4: word('s049', 'continent'), L5: word('s049', 'Land'), five: word('s049', 'One'),
    y1899: word('s050', 'ninety-nine,'), opposite: word('s051', 'opposite'), dug: word('s051', 'dug'), y1918: word('s052', 'eighteen,'),
    ball: word('s054', 'ball,'), squashed: word('s054', 'squashed'), cut0: word('s054', 'And', 1), cooling: word('s054', 'cooling,'),
    s053: S('s053'), s055: S('s055'), pinned: word('s055', 'pinned'), realSus: word('s056', 'real'), plain: word('s056', 'plain'),
    t0: C.t0, t1: C.t1,
  };
  A.L4 -= 0.16;

  // ---- assets ----
  const imgs = ['ch3_green_title.jpg', 'ch3_green_fig1.jpg', 'ch3_gj237.jpg', 'ch3_gj238.jpg', 'ch3_gj239.jpg', 'ch3_green_globe9.jpg', 'ch3_ortelius_1570.jpg'].map(f => IMG + f);
  await api.loadImages([...imgs, 'tex/equal_earth.jpg']);
  const im = (f) => api.img(IMG + f);
  await api.globe();
  const desk = deskBg(W, H, true);
  const shadows = {};
  const sh = (f) => shadows[f] || (shadows[f] = shadowSprite(im(f).width, im(f).height));

  const ne = await loadGeo('ne_50m_admin_0_countries');
  const featSA = await region('south america'), featAF = await region('africa'), featIN = await region('India');
  const greenland = findFeature(ne, 'Greenland');
  // North America without Hawaii; and its antipode (point reflection through the centre)
  const naRings = [];
  for (const f of ne.features.filter(f => f.properties.CONTINENT === 'North America')) {
    for (const r of rings(f)) { const c = r.reduce((a, p) => [a[0] + p[0] / r.length, a[1] + p[1] / r.length], [0, 0]); if (c[1] < 23 && c[0] < -150) continue; naRings.push(r); }
  }
  const wrapLon = (l) => ((l + 540) % 360) - 180;
  const antiRings = naRings.map(r => r.map(([lo, la]) => [wrapLon(lo + 180), -la]));
  const asFeat = (rs) => rs.map(r => ({ geometry: { type: 'Polygon', coordinates: [r] } }));
  const B = [-180, -90, 180, 90];

  // ---- 3D rigs ----
  const tetra = await makeTetraRig(api, A);
  const cardRig = await makeCardRig(api, A);
  const kids = await makeKidsRig(api, A);
  const cut = await makeCutRig(api, A);

  const scenes = [];
  const base = (t0, t1, draw, o = {}) => scenes.push(Object.assign({ t0, t1, layer: 0, draw }, o));
  const topPill = (ctx, s, t, a0, a1, o = {}) => { const a = env(t, a0, a1, o.fi ?? 0.25, o.fo ?? 0.3); if (a > 0) F.pill(ctx, s, o.x ?? W / 2, o.y ?? 112, { anchor: 'center', size: o.size || 38, alpha: a, border: o.border, color: o.color }); };

  // =====================================================================================
  // s045 — Green's 1875 title page (chapter card over it), push 4x into the minister line
  // =====================================================================================
  const tTitle1 = 363.85 > A.hawaii + 0.8 ? A.hawaii + 0.93 : 363.85;
  {
    const f = 'ch3_green_title.jpg';
    const K = [
      { t: C.t0, cx: 790, cy: 1090, z: 0.45, rot: -1.6 },
      { t: A.green + 0.3, cx: 790, cy: 1010, z: 0.53, rot: -1.1, ease: E.inOutSine },
      { t: A.green + 1.15, cx: 795, cy: 1255, z: 1.0, rot: -0.6 },
      { t: A.hawaii - 1.2, cx: 790, cy: 1330, z: 1.35, rot: -0.3, ease: E.inOutSine },
      { t: A.hawaii - 0.05, cx: 786, cy: 1360, z: 1.95, rot: 0 },
      { t: tTitle1, cx: 772, cy: 1364, z: 2.08, rot: 0.15, ease: E.lin },
    ];
    base(C.t0, tTitle1, (ctx, lt, t) => {
      ctx.drawImage(desk, 0, 0);
      const map = drawPage(ctx, im(f), keyAt(K, t), W, H, { shadow: sh(f) });
      underline(ctx, map, 400, 1190, 1338, prog(t, A.green + 0.25, A.green + 0.75), { color: '#ffffff', width: 4 });
      highlighter(ctx, map, 352, 1222, 1362, 30, prog(t, A.hawaii - 0.1, A.hawaii + 0.3, E.out));
      underline(ctx, map, 355, 1218, 1381, prog(t, A.hawaii - 0.05, A.hawaii + 0.35, E.out), { width: 5 });
      topPill(ctx, "HAWAII'S FOREIGN MINISTER", t, A.hawaii - 0.1, 1e9, { y: 330 });
    });
  }
  // chapter card overlay (2.4 s)
  scenes.push({ t0: C.t0, t1: C.t0 + 2.4, layer: 6, draw: (ctx, lt) => F.chapterCard(ctx, W, H, lt, 2.4, 'CHAPTER 3', 'IS EARTH SECRETLY A PYRAMID?') });
  api.cue(C.t0, 'whoosh_soft', -14);
  api.cue(A.hawaii - 0.08, 'pop_ui', -18);

  // quick cut: pulsing marker on Hawaii
  const tHaw1 = A.obsessed - 0.12;
  scenes.push(Object.assign(globeShot({
    t0: tTitle1, t1: tHaw1, overlay: null, patch: null,
    keys: [{ t: 0, lat: 15, lon: -149, alt: 2.8 }, { t: tHaw1 - tTitle1, lat: 20.4, lon: -157.2, alt: 1.3, ease: E.out }],
    look: { dim: 0.12 },
    markers: [{ t: 0.12, lat: 20.75, lon: -156.9, color: PAL.hero, r: 9 }],
    labels: [{ t: 0.05, text: "HAWAII'S FOREIGN MINISTER", lat: 20.75, lon: -156.9, dx: 120, dy: -130, ring: true }],
  }), { id: 'ch3-hawaii' }));
  api.cue(tTitle1, 'whoosh_soft', -16);

  // =====================================================================================
  // s046 — Green's Figure 1 ("normal form of a continent"), then the bent-card demo
  // =====================================================================================
  const tFig1 = A.card - 0.15;
  {
    const f = 'ch3_green_fig1.jpg';
    const K = [
      { t: tHaw1, cx: 715, cy: 820, z: 0.6, rot: 1.4 },
      { t: A.demo, cx: 705, cy: 880, z: 0.74, rot: 0.6, ease: E.inOutSine },
      { t: tFig1 + 0.3, cx: 700, cy: 1090, z: 1.02, rot: 0 },
    ];
    const shield = [[290, 555], [450, 475], [700, 437], [950, 470], [1105, 540], [1097, 700], [1062, 830], [1002, 955], [890, 1110], [700, 1255], [510, 1110], [408, 958], [343, 830], [300, 700], [290, 555]];
    base(tHaw1, tFig1 + 0.3, (ctx, lt, t) => {
      ctx.drawImage(desk, 0, 0);
      const map = drawPage(ctx, im(f), keyAt(K, t), W, H, { shadow: sh(f) });
      const fillA = prog(t, A.demo - 0.3, A.demo + 0.4);
      if (fillA > 0) { ctx.save(); ctx.setTransform(map.M); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(255,90,54,${0.35 * fillA})`; ctx.beginPath(); shield.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.fill(); ctx.restore(); }
      F.glowPath(ctx, shield.map(([x, y]) => map(x, y)), { p: prog(t, A.obsessed + 0.8, A.tips + 0.05, E.inOut), color: PAL.hero, width: 6 });
      const tip = map(700, 1255);
      if (t > A.tips - 0.1) {
        F.dot(ctx, tip[0], tip[1], { r: 10, color: PAL.yellow, ring: ((t - A.tips + 0.1) * 0.9) % 1 });
        dripArrow(ctx, tip[0], tip[1] + 22, prog(t, A.tips, A.tips + 0.5), { len: 120, color: PAL.yellow, width: 6, head: 13 });
      }
      topPill(ctx, '“THE NORMAL FORM OF A CONTINENT”', t, A.obsessed + 0.1, tFig1 - 0.1);
    });
  }
  base(tFig1, A.pyr2 - 0.08, (ctx, lt, t) => { cardRig.draw(ctx, t); }, { fadeIn: 0.3 });
  api.cue(A.water - 0.05, 'shimmer', -18);

  // =====================================================================================
  // s047 — 1 s callback: Humboldt's 'pyramidal' triangles on the globe
  // =====================================================================================
  const tFlash0 = A.pyr2 - 0.08, tFlash1 = A.pyr2 + 1.3;
  {
    const ov = makeCanvas(2048, 1024);
    fillEquirect(ov, B, [...featSA, ...featAF, ...featIN], { color: PAL.hero, alpha: 0.85, glow: 14 });
    const tri = (pts) => { const out = []; for (let i = 0; i < 3; i++) { const a = pts[i], b = pts[(i + 1) % 3]; for (const p of gcLine(a, b, 24)) out.push([p.lon, p.lat]); } return [out]; };
    const triSA = tri([[-18, -71], [-22.5, -40.5], [-56, -67.3]]), triAF = tri([[-5, 11.8], [-5, 39.5], [-34.8, 20]]), triIN = tri([[22.3, 69.5], [22.3, 88.6], [8.08, 77.55]]);
    scenes.push(Object.assign(globeShot({
      t0: tFlash0, t1: tFlash1, overlay: { canvas: ov, bounds: B }, patch: null,
      keys: [{ t: 0, lat: -12, lon: 6, alt: 2.75, tilt: 8 }, { t: tFlash1 - tFlash0, lat: -13, lon: 9, alt: 2.6, tilt: 10 }],
      look: { dim: 0.32, ovAlpha: 0.85, desat: 0.25 },
      outlines: [{ rings: triSA, t: 0.06, d: 0.25, color: '#ffffff', width: 3.5, glow: true }, { rings: triAF, t: 0.16, d: 0.25, color: '#ffffff', width: 3.5, glow: true }, { rings: triIN, t: 0.26, d: 0.25, color: '#ffffff', width: 3.5, glow: true }],
      extra: (ctx, lt) => { const a = 1 - lt / 0.2; if (a > 0) { ctx.fillStyle = `rgba(255,255,255,${0.75 * a})`; ctx.fillRect(0, 0, W, H); } },
    }), { id: 'ch3-flash' }));
    api.cue(A.pyr2 - 0.05, 'pop_ui', -16);
  }

  // =====================================================================================
  // s047–s049 — tetra-Earth + Explorer gag 6a + five-point checklist
  // =====================================================================================
  const LINES = [
    { s: 'MOST LAND IN THE NORTH', t: A.L1 - 0.08, tick: A.c1 - 0.08 },
    { s: 'THREE CONTINENTS POINTING SOUTH', t: A.L2 - 0.08, tick: A.c2 - 0.08 },
    { s: 'OCEAN AT THE NORTH POLE', t: A.L3 - 0.05, tick: A.c3 - 0.08 },
    { s: 'CONTINENT AT THE SOUTH POLE', t: A.L4, tick: A.c4 - 0.08 },
    { s: 'LAND OPPOSITE WATER', t: A.L5 - 0.08, tick: A.c5 - 0.08 },
  ];
  LINES.forEach(L => api.cue(L.tick, 'pop_ui', -14));
  api.cue(A.five - 0.1, 'stamp', -10);
  api.cue(A.tet + 0.4, 'whoosh_soft', -14); // slide-whistle fallback as he rolls down
  const panelX = (t) => lerp(-760, 92, E.outExpo(prog(t, A.pred - 0.1, A.pred + 0.5)));
  const drawPanel = (ctx, t) => {
    const x = panelX(t); if (x < -700) return;
    const y = 300, w = 620, h = 430;
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.25)'; F.round(ctx, x - 4, y + 6, w + 8, h + 8, 26); ctx.fill();
    ctx.fillStyle = 'rgba(8,11,18,0.8)'; F.round(ctx, x, y, w, h, 22); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.14)'; ctx.lineWidth = 2; F.round(ctx, x, y, w, h, 22); ctx.stroke();
    ctx.fillStyle = PAL.hero; ctx.fillRect(x + 40, y + 34, 70, 5);
    // tally boxes
    LINES.forEach((L, i) => {
      const bx = x + 40 + i * 76, by = y + 64, s = 58;
      const tp = prog(t, L.tick, L.tick + 0.3, E.outBack);
      ctx.fillStyle = tp > 0 ? `rgba(255,210,63,${0.18 * clamp(tp)})` : 'rgba(255,255,255,0.04)'; F.round(ctx, bx, by, s, s, 10); ctx.fill();
      ctx.strokeStyle = tp > 0 ? PAL.yellow : 'rgba(255,255,255,0.32)'; ctx.lineWidth = 3; F.round(ctx, bx, by, s, s, 10); ctx.stroke();
      checkMark(ctx, bx + s / 2, by + s / 2 + 2, s * 0.8, prog(t, L.tick, L.tick + 0.25));
    });
    // current line
    let cur = -1; LINES.forEach((L, i) => { if (t >= L.t) cur = i; });
    const fiveP = prog(t, A.five - 0.1, A.five + 0.25);
    if (cur >= 0) {
      const L = LINES[cur], next = LINES[cur + 1];
      const pin = prog(t, L.t, L.t + 0.35, E.outExpo), pout = next ? prog(t, next.t - 0.2, next.t, E.in) : fiveP;
      const a = pin * (1 - pout);
      wrap(L.s, 16).forEach((ln, j) => F.text(ctx, ln, x + 42, y + 222 + j * 74 + (1 - pin) * 30, { size: 66, fam: F.FAM.label, weight: 700, tracking: 0.04, alpha: a }));
      const ck = prog(t, L.tick, L.tick + 0.3);
      if (ck > 0 && a > 0) { ctx.save(); ctx.globalAlpha *= a; checkMark(ctx, x + w - 92, y + h - 92, 110, ck); ctx.restore(); }
    }
    if (fiveP > 0) stamp(ctx, '5 / 5', x + w / 2, y + 268, fiveP, { size: 170 });
    ctx.restore();
  };
  // Explorer's corner vs. the face opposite it (land opposite water)
  const drawOpposite = (ctx, t) => {
    const a = env(t, A.L5 + 0.5, A.five + 0.6, 0.4, 0.4); if (a <= 0) return;
    const v = tetra.proj(tetra.cornerW(1)), f = tetra.proj(tetra.faceCenterW(1));
    const p = prog(t, A.L5 + 0.5, A.L5 + 1.3, E.inOut);
    ctx.save(); ctx.globalAlpha *= a;
    F.glowPath(ctx, [[v.x, v.y], [lerp(v.x, f.x, p), lerp(v.y, f.y, p)]], { color: '#ffffff', width: 4, dash: [14, 10] });
    F.dot(ctx, v.x, v.y, { r: 13, color: PAL.hero, ring: (t * 0.8) % 1 });
    if (p > 0.95) F.dot(ctx, f.x, f.y, { r: 13, color: PAL.cyan, ring: (t * 0.8 + 0.5) % 1 });
    ctx.restore();
  };
  base(tFlash1, A.main - 0.05, (ctx, lt, t) => {
    const off = 250 * E.outExpo(prog(t, A.pred - 0.1, A.pred + 0.5));
    const P = tetra.draw(ctx, t, { offX: off });
    // cooling / shrinking arrows ring the planet
    const ca = env(t, A.cool - 0.1, A.tet + 0.6, 0.35, 0.5);
    if (ca > 0) inwardArrows(ctx, P.center.x, P.center.y, P.rpx * 1.02, (t * 0.75) % 1, ca, { color: PAL.cyan, n: 10 });
    topPill(ctx, 'EARTH BECOMING A TETRAHEDRON', t, A.tet - 0.08, A.pyr4 + 1.0);
    drawOpposite(ctx, t);
    drawPanel(ctx, t);
  });

  // =====================================================================================
  // s050 — 1899: the idea caught on (journal pages 237 -> 238 Fig. 5 -> 239 underline)
  // =====================================================================================
  const tJ0 = A.main - 0.05, tJ1 = A.geol - 0.08, tJ2 = A.geo - 0.06, tJ3 = S('s051');
  {
    const p237 = 'ch3_gj237.jpg', p238 = 'ch3_gj238.jpg', p239 = 'ch3_gj239.jpg';
    const K1 = [{ t: tJ0, cx: 905, cy: 1480, z: 0.335, rot: -2.2 }, { t: tJ1 + 0.4, cx: 1080, cy: 1300, z: 0.52, rot: -0.8, ease: E.inOutSine }];
    const K2 = [{ t: tJ1, cx: 925, cy: 1420, z: 0.4, rot: 1.6 }, { t: A.squeeze - 0.1, cx: 900, cy: 1300, z: 0.6, rot: 0.6, ease: E.inOutSine }, { t: tJ2 + 0.05, cx: 640, cy: 1255, z: 1.25, rot: 0 }];
    const K3 = [{ t: tJ2, cx: 740, cy: 2262, z: 1.32, rot: 0 }, { t: tJ3, cx: 760, cy: 2258, z: 1.45, rot: 0.2, ease: E.lin }];
    const fig5a = [[395, 1070], [815, 1085], [595, 1432], [395, 1070], [430, 1350], [595, 1432]];
    base(tJ0, tJ3, (ctx, lt, t) => {
      ctx.drawImage(desk, 0, 0);
      if (t < tJ2) {
        if (t < tJ1 + 0.45) drawPage(ctx, im(p237), keyAt(K1, t), W, H, { shadow: sh(p237) });
        if (t >= tJ1) {
          const v = keyAt(K2, t); const sl = E.outExpo(prog(t, tJ1, tJ1 + 0.45)); v.ox = (1 - sl) * 1500; v.rot += (1 - sl) * 6;
          const map = drawPage(ctx, im(p238), v, W, H, { shadow: sh(p238) });
          const gp = prog(t, A.squeeze - 0.05, A.squeeze + 0.45, E.inOut);
          if (gp > 0) F.glowPath(ctx, fig5a.map(([x, y]) => map(x, y)), { p: gp, color: PAL.yellow, width: 6 });
        }
      } else {
        const map = drawPage(ctx, im(p239), keyAt(K3, t), W, H, { shadow: sh(p239) });
        underline(ctx, map, 375, 1112, 2282, prog(t, tJ2 + 0.08, tJ2 + 0.6, E.out), { width: 7 });
        const fl = 1 - (t - tJ2) / 0.12; if (fl > 0) { ctx.fillStyle = `rgba(255,255,255,${0.5 * fl})`; ctx.fillRect(0, 0, W, H); }
      }
      topPill(ctx, '1899: “TENDING TO BECOME TETRAHEDRAL”', t, tJ2 + 0.02, 1e9);
    });
    api.cue(A.main - 0.03, 'paper_rustle', -16);
    api.cue(tJ1, 'paper_rustle', -20);
  }

  // =====================================================================================
  // s051 — most of North America sits opposite the Indian Ocean
  // =====================================================================================
  const tNA0 = tJ3, tNA1 = A.y1918 + 0.05;
  {
    const ov = makeCanvas(4096, 2048);
    fillEquirect(ov, B, asFeat(naRings), { color: PAL.hero, alpha: 0.8, glow: 14 });
    fillEquirect(ov, B, asFeat(antiRings), { color: PAL.cyan, alpha: 0.72, glow: 14 });
    const L = (x) => x - tNA0;
    const kSel = [-39.83, 81.42];
    scenes.push(Object.assign(globeShot({
      t0: tNA0, t1: tNA1, overlay: { canvas: ov, bounds: B }, patch: null,
      keys: [
        { t: 0, lat: 45, lon: -101, alt: 2.6 },
        { t: L(A.opposite - 0.75), lat: 42, lon: -99, alt: 2.45 },
        { t: L(A.opposite - 0.2), lat: 2, lon: -12, alt: 3.3, ease: E.in },
        { t: L(A.opposite + 0.45), lat: -45, lon: 84, alt: 2.35, ease: E.out },
        { t: L(A.io + 0.6), lat: -43, lon: 83, alt: 2.2 },
        { t: L(tNA1), lat: -39.9, lon: 81.4, alt: 1.15, ease: E.inOutSine },
      ],
      look: (lt) => ({ dim: 0.32 * prog(lt, 0, 0.5), ovAlpha: 0.88 * prog(lt, 0.05, 0.6), desat: 0.2 }),
      outlines: [{ rings: naRings, t: 0.1, d: 1.2, color: '#ffffff', width: 2 }, { rings: antiRings, t: L(A.opposite + 0.3), d: 1.1, color: '#ffffff', width: 2.2, glow: true }],
      markers: [{ t: 0.45, lat: 39.83, lon: -98.58, color: PAL.yellow, r: 8 }, { t: L(A.io - 0.08), lat: kSel[0], lon: kSel[1], color: PAL.yellow, r: 10 }],
      extra: (ctx, lt, api2) => {
        const t = tNA0 + lt; const g = api.g;
        const q = g.project(kSel[0], kSel[1]);
        const a = prog(t, A.io - 0.1, A.io + 0.25);
        if (a > 0 && q.visible) F.pill(ctx, 'MOST OF NORTH AMERICA: OPPOSITE INDIAN OCEAN', W / 2, 112, { anchor: 'center', size: 36, alpha: a, leader: [q.x, q.y], ring: ((t - A.io) * 0.8) % 1 });
        if (t > A.dug - 0.1 && q.visible) {
          const s = clamp((t - A.dug + 0.1) / 0.3);
          ctx.save(); ctx.fillStyle = 'rgba(2,6,14,0.85)'; ctx.beginPath(); ctx.ellipse(q.x, q.y + 2, 26 * E.outBack(s), 12 * E.outBack(s), 0, 0, Math.PI * 2); ctx.fill();
          ctx.strokeStyle = PAL.cyan; ctx.lineWidth = 3; ctx.stroke(); ctx.restore();
          for (let i = 0; i < 3; i++) { const k = ((t - A.dug) * 0.9 - i * 0.3); if (k < 0 || k > 1) continue; ctx.save(); ctx.globalAlpha = 1 - k; ctx.strokeStyle = '#dffbff'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.ellipse(q.x, q.y, 30 + 120 * k, 14 + 54 * k, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
        }
      },
    }), { id: 'ch3-na' }));
    api.cue(A.opposite - 0.6, 'whoosh_soft', -14);
    api.cue(A.io - 0.05, 'sonar_ping', -12);
  }

  // =====================================================================================
  // s052 — 1918 children's page: the minis learn Earth will become a pyramid
  // =====================================================================================
  const tK0 = tNA1, tK1 = S('s053');
  {
    // pre-rendered sepia page with ornaments, chalkboard and pseudo-print
    const PW = 1660, PH = 960, page = cv(PW, PH), g = page.getContext('2d');
    g.fillStyle = '#e8dcc0'; g.fillRect(0, 0, PW, PH);
    const r = F.rng(518);
    for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(${r() > 0.5 ? '90,60,30' : '255,250,235'},${0.05 * r()})`; g.fillRect(r() * PW, r() * PH, 2 + r() * 5, 2 + r() * 5); }
    const vg = g.createRadialGradient(PW / 2, PH / 2, PH * 0.3, PW / 2, PH / 2, PH * 1.0); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(70,40,10,0.35)'); g.fillStyle = vg; g.fillRect(0, 0, PW, PH);
    g.strokeStyle = '#5a4127'; g.lineWidth = 6; g.strokeRect(26, 26, PW - 52, PH - 52); g.lineWidth = 2; g.strokeRect(40, 40, PW - 80, PH - 80);
    // header ornament (no words)
    g.fillStyle = '#5a4127'; g.fillRect(120, 78, PW / 2 - 170, 3); g.fillRect(PW / 2 + 50, 78, PW / 2 - 170, 3); g.fillRect(120, 86, PW / 2 - 170, 1.5); g.fillRect(PW / 2 + 50, 86, PW / 2 - 170, 1.5);
    g.save(); g.translate(PW / 2, 82); g.rotate(Math.PI / 4); g.fillRect(-14, -14, 28, 28); g.restore();
    // chalkboard
    const bx = 430, by = 130, bw = 800, bh = 420;
    g.fillStyle = '#6b4a2b'; F.round(g, bx - 22, by - 22, bw + 44, bh + 44, 10); g.fill();
    g.fillStyle = '#2c3a33'; g.fillRect(bx, by, bw, bh);
    const bg2 = g.createRadialGradient(bx + bw / 2, by + bh / 2, 40, bx + bw / 2, by + bh / 2, bw * 0.7); bg2.addColorStop(0, 'rgba(255,255,255,0.06)'); bg2.addColorStop(1, 'rgba(0,0,0,0.25)'); g.fillStyle = bg2; g.fillRect(bx, by, bw, bh);
    for (let i = 0; i < 40; i++) { g.strokeStyle = `rgba(255,255,255,${0.03 + 0.03 * r()})`; g.lineWidth = 8 + 20 * r(); g.beginPath(); const yy = by + r() * bh; g.moveTo(bx + r() * 200, yy); g.lineTo(bx + bw - r() * 200, yy + (r() - 0.5) * 30); g.stroke(); }
    g.fillStyle = '#7d5a37'; g.fillRect(bx - 10, by + bh + 18, bw + 20, 16);
    g.fillStyle = '#f2efe6'; g.fillRect(bx + 120, by + bh + 10, 46, 10); g.fillRect(bx + 600, by + bh + 12, 30, 8);
    // pseudo print columns at the sides
    g.fillStyle = 'rgba(70,50,30,0.35)';
    for (const x0 of [90, PW - 330]) for (let i = 0; i < 16; i++) { const w = 200 + r() * 40 - (i % 5 === 4 ? 90 : 0); g.fillRect(x0, 150 + i * 30, w, 9); }
    const PX = (W - PW) / 2, PY = 70;
    const boardC = [PX + bx + bw / 2, PY + by + bh / 2];
    // chalk globe -> pyramid morph (polar parameterisation around the board centre)
    const N = 96, rr = 150;
    const triV = [[0, -175], [175, 128], [-175, 128]];
    const triAt = (ang) => { // ray from centre at angle hits triangle
      const dx = Math.cos(ang), dy = Math.sin(ang); let best = 1e9;
      for (let i = 0; i < 3; i++) { const [x1, y1] = triV[i], [x2, y2] = triV[(i + 1) % 3]; const ex = x2 - x1, ey = y2 - y1; const den = dx * ey - dy * ex; if (Math.abs(den) < 1e-9) continue; const tt = (x1 * ey - y1 * ex) / den, u = (x1 * dy - y1 * dx) / den; if (tt > 0 && u >= 0 && u <= 1) best = Math.min(best, tt); }
      return [dx * best, dy * best];
    };
    const chalk = (ctx, pts, p, o = {}) => {
      for (const [lw, col, off] of [[o.w || 7, 'rgba(240,240,232,0.85)', 0], [2, 'rgba(255,255,255,0.5)', 1.5]]) F.glowPath(ctx, pts.map(([x, y]) => [x + off, y - off]), { p, color: col, glowColor: '#ffffff', width: lw });
    };
    base(tK0, tK1, (ctx, lt, t) => {
      ctx.drawImage(desk, 0, 0);
      const sl = E.outExpo(prog(t, tK0, tK0 + 0.55));
      const oy = (1 - sl) * -1100, rot = (1 - sl) * -4;
      ctx.save(); ctx.translate(W / 2, H / 2 + oy); ctx.rotate(rot * Math.PI / 180); ctx.scale(1 + 0.02 * (t - tK0) / 8, 1 + 0.02 * (t - tK0) / 8); ctx.translate(-W / 2, -H / 2);
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(PX + 10, PY + 16, PW, PH);
      ctx.drawImage(page, PX, PY);
      // chalk drawing
      const m = E.inOut(prog(t, A.pyramid - 0.12, A.pyramid + 0.5));
      const pts = []; for (let i = 0; i <= N; i++) { const ang = -Math.PI / 2 + i / N * Math.PI * 2; const c = [Math.cos(ang) * rr, Math.sin(ang) * rr], tr = triAt(ang); pts.push([boardC[0] + lerp(c[0], tr[0], m), boardC[1] + lerp(c[1], tr[1], m)]); }
      chalk(ctx, pts, prog(t, A.mag + 0.2, A.mag + 1.1));
      const la = (1 - m) * prog(t, A.mag + 0.8, A.mag + 1.3);
      if (la > 0) { ctx.save(); ctx.globalAlpha *= la; for (const yy of [-70, 0, 70]) { const hw = Math.sqrt(rr * rr - yy * yy); chalk(ctx, [[boardC[0] - hw, boardC[1] + yy], [boardC[0] + hw, boardC[1] + yy]], 1, { w: 4 }); } chalk(ctx, [[boardC[0] - 40, boardC[1] - 110], [boardC[0] + 30, boardC[1] - 80], [boardC[0] + 10, boardC[1] - 20], [boardC[0] - 50, boardC[1] + 10]], 1, { w: 5 }); ctx.restore(); }
      const ia = prog(t, A.pyramid + 0.35, A.pyramid + 0.8);
      if (ia > 0) chalk(ctx, [[boardC[0], boardC[1] - 175], [boardC[0] + 35, boardC[1] + 60], [boardC[0] + 175, boardC[1] + 128], [boardC[0] + 35, boardC[1] + 60], [boardC[0] - 175, boardC[1] + 128]], ia, { w: 6 });
      ctx.restore();
      if (t > A.mag - 0.1) kids.drawKids(ctx, t);
      topPill(ctx, '1918: “A SORT OF PYRAMID”', t, A.y1918 - 0.05, 1e9, { y: 116 });
    });
    api.cue(tK0 + 0.05, 'paper_rustle', -18);
  }

  // =====================================================================================
  // s053 — "how do we know it's wrong?" (frozen tetra, a '?' draws itself) + s054 cooling arrows
  // =====================================================================================
  const tQ1 = A.measure - 0.05;
  const faceToward = (P) => { let best = 0, bd = -2; for (let i = 0; i < 4; i++) { const c = tetra.faceCenterW(i); const d = tetra.faceNormalW(i).dot(P.cp.clone().sub(c).normalize()); if (d > bd) { bd = d; best = i; } } return best; };
  base(tK1, tQ1, (ctx, lt, t) => {
    const P = tetra.draw(ctx, t, { c0: '#0d1a33' });
    const qa = 1 - prog(t, A.cooling - 1.2, A.cooling - 0.8);
    if (t > A.how - 0.1 && qa > 0) {
      const c = tetra.proj(tetra.faceCenterW(faceToward(P)));
      ctx.save(); ctx.globalAlpha *= qa; questionMark(ctx, c.x, c.y - 10, 250, prog(t, A.how - 0.08, A.how + 0.75, E.inOut)); ctx.restore();
    }
    const ca = prog(t, A.cooling - 0.15, A.cooling + 0.35);
    if (ca > 0) inwardArrows(ctx, P.center.x, P.center.y, P.rpx * 0.95, (t * 0.75) % 1, ca, { color: PAL.cyan, n: 10 });
  });

  // =====================================================================================
  // s054 — measured: a slightly squashed ball, not a pyramid (tape, oblate ellipse, red X)
  // =====================================================================================
  const tM1 = A.cut0 - 0.05;
  {
    const L = (x) => x - tQ1;
    const tetraPts = (d) => { const x = d.x, y = d.y, r = d.r; return { TL: [x - 1.02 * r, y - 0.58 * r], TR: [x + 1.0 * r, y - 0.52 * r], B: [x + 0.02 * r, y + 1.12 * r], Fv: [x - 0.18 * r, y + 0.06 * r] }; };
    scenes.push(Object.assign(globeShot({
      t0: tQ1, t1: tM1, overlay: null, patch: null,
      keys: [{ t: 0, lat: 12, lon: -24, alt: 3.45 }, { t: tM1 - tQ1, lat: 10, lon: -18, alt: 3.25, ease: E.lin }],
      look: (lt) => ({ dim: 0.1 + 0.25 * prog(lt, L(A.notp - 0.5), L(A.notp)) }),
      extra: (ctx, lt) => {
        const t = tQ1 + lt, g = api.g, d = g.disc();
        // measuring tape around the equator (front half), drawn on, then fades
        const tp = prog(t, tQ1 + 0.08, tQ1 + 1.0, E.inOut), ta = 1 - prog(t, A.squashed + 0.2, A.squashed + 0.7);
        if (tp > 0 && ta > 0) {
          const pts = []; for (let lon = -180; lon <= 180; lon += 2) { const q = g.project(0, lon); if (q.visible) pts.push([q.x, q.y]); }
          pts.sort((a, b) => a[0] - b[0]);
          const n = Math.max(2, Math.floor(pts.length * tp));
          ctx.save(); ctx.globalAlpha *= ta; ctx.lineCap = 'butt'; ctx.lineJoin = 'round';
          for (const [lw, col] of [[34, 'rgba(0,0,0,0.45)'], [26, '#FFD23F']]) { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); pts.slice(0, n).forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
          ctx.strokeStyle = 'rgba(40,30,10,0.85)'; ctx.lineWidth = 2;
          for (let i = 1; i < n; i += 1) { const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; const dx = x1 - x0, dy = y1 - y0, l = Math.hypot(dx, dy) || 1; const nx = -dy / l, ny = dx / l, big = i % 5 === 0 ? 11 : 6; ctx.beginPath(); ctx.moveTo(x1 + nx * 12, y1 + ny * 12); ctx.lineTo(x1 + nx * (12 - big), y1 + ny * (12 - big)); ctx.stroke(); }
          const hd = pts[n - 1]; ctx.fillStyle = '#c99a1a'; ctx.fillRect(hd[0] - 8, hd[1] - 20, 16, 40);
          ctx.restore();
        }
        // oblate ellipse (exaggerated)
        const ep = prog(t, A.squashed - 0.1, A.squashed + 0.6, E.inOut);
        if (ep > 0) {
          ctx.save(); ctx.lineWidth = 5; ctx.strokeStyle = '#ffffff'; ctx.setLineDash([]);
          for (const [lw, col] of [[16, 'rgba(255,255,255,0.12)'], [5, '#ffffff']]) { ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.beginPath(); ctx.ellipse(d.x, d.y, d.r * 1.08, d.r * 0.9, 0, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ep); ctx.stroke(); }
          ctx.restore();
          F.pill(ctx, 'EXAGGERATED', d.x + d.r * 1.08 + 24, d.y - 30, { anchor: 'left', size: 26, alpha: prog(t, A.squashed + 0.4, A.squashed + 0.7), color: PAL.sub });
        }
        // the pyramid outline gets a red X
        const tp2 = prog(t, A.notp - 0.45, A.notp - 0.05, E.inOut);
        if (tp2 > 0) {
          const V = tetraPts(d);
          F.glowPath(ctx, [V.TL, V.TR, V.B, V.TL, V.Fv, V.B], { p: tp2, color: PAL.yellow, width: 5 });
          F.glowPath(ctx, [V.Fv, V.TR], { p: tp2, color: PAL.yellow, width: 4, dash: [12, 10] });
        }
        redX(ctx, d.x, d.y + d.r * 0.1, d.r * 1.15, prog(t, A.notp - 0.03, A.notp + 0.3));
        topPill(ctx, 'SQUASHED BALL, NOT A PYRAMID', t, A.ball - 0.1, 1e9, { y: 96 });
      },
    }), { id: 'ch3-measure' }));
    api.cue(A.measure, 'whoosh_soft', -18);
    api.cue(A.notp - 0.03, 'stamp', -16);
  }

  // radioactivity: cut-away Earth with glowing specks
  base(tM1, S('s055'), (ctx, lt, t) => {
    cut.draw(ctx, t);
    topPill(ctx, 'RADIOACTIVITY: A HIDDEN HEATER', t, A.rad - 0.08, 1e9, { y: 112 });
  });
  api.cue(A.rad - 0.05, 'shimmer', -16);

  // =====================================================================================
  // s055 — the shrinking engine stalls; EXPLORER GAG 6b: the pyramid pops back into a ball
  // =====================================================================================
  const tB0 = word('s055', "Green's") - 0.1;
  base(S('s055'), tB0, (ctx, lt, t) => {
    const P = tetra.draw(ctx, t);
    const ph = (Math.min(t, A.stall + 0.05) * 0.75) % 1;
    const ca = prog(t, S('s055'), S('s055') + 0.3) * (1 - prog(t, A.stall + 0.1, A.stall + 0.7));
    if (ca > 0) inwardArrows(ctx, P.center.x, P.center.y, P.rpx * 0.95, ph, ca, { color: PAL.cyan, n: 10 });
  });
  api.cue(A.stall + 0.08, 'pop_ui', -8); // boing fallback

  // =====================================================================================
  // s055/s056 — detective board: real clues, wrong suspect; the real suspect = '?'
  // =====================================================================================
  const tBoard1 = A.maps - 0.08;
  {
    const board = cv(W, H), bg = board.getContext('2d');
    const gr = bg.createRadialGradient(W / 2, H * 0.45, 100, W / 2, H / 2, H * 1.0); gr.addColorStop(0, '#26303e'); gr.addColorStop(1, '#0a0d13'); bg.fillStyle = gr; bg.fillRect(0, 0, W, H);
    const rb = F.rng(77); for (let i = 0; i < 6000; i++) { bg.fillStyle = `rgba(${rb() > 0.5 ? '255,255,255' : '0,0,0'},${0.035 * rb()})`; bg.fillRect(rb() * W, rb() * H, 2 + rb() * 3, 2 + rb() * 3); }
    const card = (draw, o = {}) => { const s = o.s || 200, c = cv(s + 40, s + 40), g = c.getContext('2d'); g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(26, 28, s, s); g.fillStyle = o.bg || '#efe6d2'; g.fillRect(20, 20, s, s); g.save(); g.translate(20 + s / 2, 20 + s / 2); draw(g, s); g.restore(); return c; };
    const globe = (g, s, fill = '#0e2a48') => { g.fillStyle = fill; g.beginPath(); g.arc(0, 0, s * 0.36, 0, Math.PI * 2); g.fill(); g.strokeStyle = '#1b1b1b'; g.lineWidth = 3; g.stroke(); };
    const clip = (g, s) => { g.beginPath(); g.arc(0, 0, s * 0.36, 0, Math.PI * 2); g.clip(); };
    const icons = [
      card((g, s) => { globe(g, s); g.save(); clip(g, s); g.fillStyle = PAL.cyan; g.fillRect(-s, -s, 2 * s, s * 0.7); g.restore(); g.strokeStyle = '#1b1b1b'; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, s * 0.36, 0, Math.PI * 2); g.stroke(); }),
      card((g, s) => { globe(g, s); g.save(); clip(g, s); g.fillStyle = '#f4f6fa'; g.beginPath(); g.ellipse(0, s * 0.34, s * 0.3, s * 0.14, 0, 0, Math.PI * 2); g.fill(); g.strokeStyle = PAL.hero; g.lineWidth = 4; g.stroke(); g.restore(); }),
      card((g, s) => { g.fillStyle = PAL.hero; for (const [x, sc] of [[-s * 0.27, 0.8], [0, 1], [s * 0.27, 0.7]]) { g.beginPath(); g.moveTo(x - s * 0.11 * sc, -s * 0.2); g.lineTo(x + s * 0.11 * sc, -s * 0.2); g.lineTo(x, s * 0.26 * sc); g.closePath(); g.fill(); } g.strokeStyle = '#1b1b1b'; g.lineWidth = 3; g.beginPath(); g.moveTo(0, -s * 0.36); g.lineTo(0, -s * 0.28); g.stroke(); }),
      card((g, s) => { globe(g, s); g.save(); clip(g, s); g.fillStyle = PAL.hero; g.fillRect(-s, -s, 2 * s, s * 0.95); g.fillStyle = '#0e2a48'; g.beginPath(); g.arc(0, -s * 0.05, s * 0.12, 0, Math.PI * 2); g.fill(); g.restore(); g.strokeStyle = '#1b1b1b'; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, s * 0.36, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.moveTo(-s * 0.36, 0); g.lineTo(s * 0.36, 0); g.stroke(); }),
      card((g, s) => { globe(g, s); g.strokeStyle = '#ffffff'; g.lineWidth = 4; g.setLineDash([8, 7]); g.beginPath(); g.moveTo(-s * 0.25, -s * 0.25); g.lineTo(s * 0.25, s * 0.25); g.stroke(); g.setLineDash([]); g.fillStyle = PAL.hero; g.beginPath(); g.arc(-s * 0.25, -s * 0.25, s * 0.075, 0, Math.PI * 2); g.fill(); g.fillStyle = PAL.cyan; g.beginPath(); g.arc(s * 0.25, s * 0.25, s * 0.075, 0, Math.PI * 2); g.fill(); }),
    ];
    const tetraIcon = card((g, s) => { g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = '#d9a400'; g.lineWidth = 6; const P = { a: [-s * 0.32, -s * 0.2], b: [s * 0.32, -s * 0.17], c: [0, s * 0.34], d: [-s * 0.08, s * 0.02] }; g.beginPath(); g.moveTo(...P.a); g.lineTo(...P.b); g.lineTo(...P.c); g.closePath(); g.moveTo(...P.a); g.lineTo(...P.d); g.lineTo(...P.c); g.stroke(); g.setLineDash([9, 8]); g.beginPath(); g.moveTo(...P.d); g.lineTo(...P.b); g.stroke(); }, { s: 240 });
    const qCard = card(() => {}, { s: 240, bg: '#151b26' });
    const pos = [[700, 300], [1250, 268], [1600, 500], [1500, 800], [720, 800]];
    const rots = [-5, 4, -3, 6, -4];
    const CEN = [1090, 560];
    const pin = (ctx, x, y) => { F.dot(ctx, x, y, { r: 9, color: '#e8322b' }); };
    const string = (ctx, a, b, p, col = '#e8322b') => { if (p <= 0) return; const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 + 60; const pts = []; for (let i = 0; i <= 24; i++) { const u = i / 24; pts.push([(1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * mx + u * u * b[0], (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * my + u * u * b[1]]); } ctx.save(); ctx.lineCap = 'round'; ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 6; ctx.beginPath(); const n = Math.max(2, Math.ceil(pts.length * p)); pts.slice(0, n).forEach(([x, y], i) => i ? ctx.lineTo(x, y + 3) : ctx.moveTo(x, y + 3)); ctx.stroke(); ctx.strokeStyle = col; ctx.lineWidth = 3.5; ctx.beginPath(); pts.slice(0, n).forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); ctx.restore(); };
    const drawCard = (ctx, c, x, y, rot, sc, a = 1) => { if (sc <= 0.001 || a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot * Math.PI / 180); ctx.scale(sc, sc); ctx.drawImage(c, -c.width / 2, -c.height / 2); ctx.restore(); };
    const tGlob = word('s055', "Green's") - 0.05, tFall = A.realSus - 0.1, tQ = A.realSus + 0.5;
    base(tB0, tBoard1, (ctx, lt, t) => {
      // board camera: slow drift, then push into the '?' card
      const z = lerp(1.0, 1.05, prog(t, tB0, tFall)) * Math.exp(Math.log(1.55) * E.inOut(prog(t, A.plain - 0.4, tBoard1)));
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-lerp(W / 2, CEN[0], prog(t, A.plain - 0.4, tBoard1)), -lerp(H / 2, CEN[1], prog(t, A.plain - 0.4, tBoard1)));
      ctx.drawImage(board, 0, 0);
      // Green's globe engraving drifts in (sepia photo, pinned)
      const gx = lerp(-260, 330, E.outExpo(prog(t, tGlob, tGlob + 0.7))) + (t - tGlob) * 6;
      { const img = im('ch3_green_globe9.jpg'), w = 300, h = 315; ctx.save(); ctx.translate(gx, 545); ctx.rotate(-7 * Math.PI / 180); ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.fillRect(-w / 2 - 10, -h / 2 - 2, w + 28, h + 52); ctx.fillStyle = '#f3ecdc'; ctx.fillRect(-w / 2 - 16, -h / 2 - 16, w + 32, h + 56); ctx.drawImage(img, -w / 2, -h / 2, w, h); ctx.restore(); pin(ctx, gx + 5, 545 - h / 2 - 4); }
      // tetra suspect card (centre), falls away after the X
      const tetA = prog(t, A.pinned - 0.1, A.pinned + 0.3, E.outBack), fall = E.in(prog(t, tFall, tFall + 0.65));
      const tx = CEN[0] + fall * 80, ty = CEN[1] + fall * 900, trot = -2 + fall * 38;
      // strings to the tetra card
      pos.forEach((p, i) => { const s0 = A.pinned + 0.35 + i * 0.12; string(ctx, [p[0], p[1] - 100], [tx, ty - 125], prog(t, s0, s0 + 0.45) * (1 - prog(t, tFall, tFall + 0.25))); });
      drawCard(ctx, tetraIcon, tx, ty, trot, tetA);
      if (tetA > 0) pin(ctx, tx, ty - 125 + fall * 0);
      redX(ctx, tx, ty, 210, prog(t, A.suspect - 0.05, A.suspect + 0.3));
      // the real suspect: '?'
      const qa = prog(t, tQ, tQ + 0.4, E.outBack);
      if (qa > 0) {
        drawCard(ctx, qCard, CEN[0], CEN[1], 1.5, qa);
        ctx.save(); ctx.translate(CEN[0], CEN[1]); ctx.rotate(1.5 * Math.PI / 180); ctx.scale(qa, qa);
        ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 3; ctx.setLineDash([12, 9]); ctx.strokeRect(-110, -110, 220, 220); ctx.setLineDash([]);
        questionMark(ctx, 0, -6, 170, prog(t, tQ + 0.2, tQ + 0.9));
        ctx.restore();
        pin(ctx, CEN[0], CEN[1] - 125);
        pos.forEach((p, i) => { const s0 = tQ + 0.7 + i * 0.1; string(ctx, [p[0], p[1] - 100], [CEN[0], CEN[1] - 125], prog(t, s0, s0 + 0.4), PAL.yellow); });
      }
      // clue cards
      pos.forEach((p, i) => { const s0 = A.real - 0.15 + i * 0.16; const sc = E.outBack(prog(t, s0, s0 + 0.35, E.lin)); drawCard(ctx, icons[i], p[0], p[1], rots[i], sc); if (sc > 0.5) pin(ctx, p[0], p[1] - 100); });
      ctx.restore();
      topPill(ctx, 'REAL CLUES. WRONG SUSPECT.', t, A.real - 0.1, tFall + 0.3, { y: 96 });
    });
    api.cue(A.real - 0.12, 'pop_ui', -20);
    api.cue(A.suspect - 0.05, 'impact_short', -14);
  }

  // =====================================================================================
  // s056 — Ortelius 1570: the matching coasts were on every world map
  // =====================================================================================
  const tO1 = A.say + 0.12, tG0 = A.say - 0.23;
  {
    const f = 'ch3_ortelius_1570.jpg';
    const K = [{ t: tBoard1, cx: 960, cy: 654, z: 1.0, rot: 0 }, { t: tO1, cx: 1010, cy: 750, z: 2.05, rot: 0, ease: E.inOutSine }];
    const SAp = [[818, 662], [850, 672], [893, 688], [895, 720], [885, 750], [862, 785], [840, 802], [826, 830], [822, 848], [812, 872], [795, 895], [778, 918], [768, 935]];
    const AFp = [[975, 542], [970, 585], [985, 605], [1000, 627], [1040, 636], [1080, 641], [1125, 636], [1150, 640], [1155, 665], [1160, 700], [1157, 720], [1155, 755], [1162, 790], [1170, 805], [1185, 845], [1200, 850]];
    base(tBoard1, tO1, (ctx, lt, t) => {
      ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
      const map = drawPage(ctx, im(f), keyAt(K, t), W, H);
      const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.45)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
      const pul = 0.85 + 0.15 * Math.sin(t * 4);
      F.glowPath(ctx, SAp.map(([x, y]) => map(x, y)), { p: prog(t, A.maps + 0.45, A.maps + 1.7), color: PAL.hero, width: 6, alpha: pul });
      F.glowPath(ctx, AFp.map(([x, y]) => map(x, y)), { p: prog(t, A.maps + 0.85, A.maps + 2.1), color: PAL.hero, width: 6, alpha: pul });
    });
    api.cue(A.maps - 0.05, 'paper_rustle', -16);
  }
  // photoreal globe, same two coasts; the continents twitch apart
  {
    const ov = makeCanvas(2048, 1024);
    fillEquirect(ov, B, [...featSA, ...featAF], { color: PAL.hero, alpha: 0.4, glow: 10 });
    const L = (x) => x - tG0;
    const keys = [{ t: 0, lat: -10, lon: -15, alt: 2.45 }];
    const r = F.rng(5);
    for (let i = 0; i < 9; i++) keys.push({ t: L(A.say) + i * 0.06, lat: -10 + (r() - 0.5) * 0.9 * (1 - i / 9), lon: -15 + (r() - 0.5) * 0.9 * (1 - i / 9), alt: 2.42, ease: E.lin });
    keys.push({ t: L(A.drips - 0.25), lat: -9, lon: -14, alt: 2.15, ease: E.inOutSine });
    scenes.push(Object.assign(globeShot({
      t0: tG0, t1: A.drips - 0.25, fadeIn: 0.35, overlay: { canvas: ov, bounds: B }, patch: null, keys,
      look: { dim: 0.25, ovAlpha: 0.75 },
      extra: (ctx, lt) => {
        const t = tG0 + lt, g = api.g;
        const off = 0.6 * E.out(prog(t, A.say, A.say + 0.2));
        strokeProjected(ctx, g, [COAST_SA.map(([lo, la]) => [lo - off, la])], { color: PAL.hero, width: 4.5, glow: true });
        strokeProjected(ctx, g, [COAST_AF.map(([lo, la]) => [lo + off, la])], { color: PAL.hero, width: 4.5, glow: true });
      },
    }), { id: 'ch3-coasts' }));
    api.cue(A.say - 0.02, 'rumble_quake', -12);
  }

  // =====================================================================================
  // s056 end — Greenland tip-pop on the Equal Earth flat map, dip to white (into Chapter 4)
  // =====================================================================================
  {
    const ms = 1800 / EE_W, mx = (W - EE_W * ms) / 2, my = (H - EE_H * ms) / 2 - 10;
    const P = (lo, la) => { const [x, y] = ee(lo, la); return [mx + x * ms, my + y * ms]; };
    const basec = cv(W, H), g = basec.getContext('2d');
    g.fillStyle = '#05070D'; g.fillRect(0, 0, W, H);
    g.drawImage(api.img('tex/equal_earth.jpg'), mx, my, EE_W * ms, EE_H * ms);
    const fillF = (g2, feats, col, a, stroke) => { g2.save(); g2.globalAlpha = a; g2.fillStyle = col; g2.beginPath(); for (const fe of feats) for (const rg of rings(fe)) { rg.forEach(([lo, la], i) => { const [x, y] = P(lo, la); i ? g2.lineTo(x, y) : g2.moveTo(x, y); }); g2.closePath(); } g2.fill('evenodd'); if (stroke) { g2.globalAlpha = 0.9; g2.strokeStyle = stroke; g2.lineWidth = 1.5; g2.stroke(); } g2.restore(); };
    fillF(g, [...featSA, ...featAF, ...featIN], PAL.hero, 0.62, '#ffffff');
    const gc = (() => { let x = 0, y = 0, n = 0; for (const rg of rings(greenland)) for (const [lo, la] of rg) { const p = P(lo, la); x += p[0]; y += p[1]; n++; } return [x / n, y / n]; })();
    const tip = P(-43.9, 59.8);
    const tE0 = A.drips - 0.25;
    base(tE0, C.t1, (ctx, lt, t) => {
      const z = 1 + 0.06 * E.out(prog(t, tE0, C.t1));
      ctx.save(); ctx.translate(gc[0], gc[1]); ctx.scale(z, z); ctx.translate(-gc[0], -gc[1]); ctx.drawImage(basec, 0, 0);
      const pp = prog(t, A.drips - 0.08, A.drips + 0.25, E.lin);
      if (pp > 0) {
        const s = lerp(1.3, 1, E.outBack(pp));
        ctx.save(); ctx.translate(gc[0], gc[1]); ctx.scale(s, s); ctx.translate(-gc[0], -gc[1]); fillF(ctx, [greenland], PAL.hero, 0.9 * clamp(pp * 3), '#ffffff'); ctx.restore();
        F.dot(ctx, tip[0], tip[1], { r: 8, color: '#ffffff', ring: ((t - A.drips) * 1.2) % 1 });
      }
      ctx.restore();
      const wa = 0.95 * prog(t, C.t1 - 0.62, C.t1, E.in); if (wa > 0) { ctx.fillStyle = `rgba(255,255,255,${wa})`; ctx.fillRect(0, 0, W, H); }
    });
    api.cue(A.drips - 0.08, 'pop_ui', -12);
    api.cue(C.t1 - 4.0, 'riser_tension', -16);
  }

  return scenes;
}
