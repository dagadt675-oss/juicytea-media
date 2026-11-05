// Module ch1 — Chapter 1 "Why does Earth look like it's dripping?" (cold open + 400 years of people noticing the drip).
// Segments s001–s024, [C.t0, C.t1) = [0, 175.32). Everything is a pure function of time; heavy assets load once in build().
import * as F from '../../lib/fx.js';
import { globeShot } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, fillEquirect, strokeProjected, fillProjected, gcLine, projectPath } from '../../lib/geo.js';
import { region, allRings, dripArrow } from '../../lib/beats.js';
import { ee, EE_W, EE_H, eeXform, eePath, eeOutline } from './ch1_ee.js';
import * as X from './ch1_fx.js';
const { PAL, E, prog, env, clamp, lerp } = F;
const WB = [-180, -90, 180, 90];
const IMG = (n) => 'ep/ep01/img/' + n;
const D2R = Math.PI / 180;

// southern tips (lat, lon)
const TIPS = {
  froward: [-53.9, -71.3], agulhas: [-34.8, 20.0], kanya: [8.1, 77.5],
  farewell: [59.8, -43.9], sable: [25.3, -81.1], lucas: [22.9, -109.9], lopatka: [50.9, 156.7],
};
const SEVEN = ['froward', 'agulhas', 'kanya', 'farewell', 'sable', 'lucas', 'lopatka'];
const POLE_T = [-78, 20]; // where the cold-open drip arcs converge (Antarctica)

export async function build(api, C) {
  const W = api.W, H = api.H;
  const T = (m, w) => C.T(m, w);
  const norm = (s) => s.toLowerCase().replace(/[^a-z0-9-]/g, '');
  const wf = (seg, w, nth = 0) => { const ws = C.words(seg).filter(x => norm(x.w).startsWith(w)); if (!ws[nth]) throw new Error(`ch1: word ${w} not in ${seg}`); return ws[nth].start; };
  const segS = (id) => C.seg(id).start;
  const cue = (t, n, db) => api.cue(Math.max(0, t), n, db);
  await api.globe();
  const g = api.g;
  try { await Promise.all([document.fonts.load('500 40px "JetBrains Mono"'), document.fonts.load('italic 700 60px "Playfair Display"'), document.fonts.load('400 60px "Anton"')]); } catch (e) { }

  // ------------------------------------------------------------------ timing (all absolute, from the VO)
  const t = {
    melt: T('melt'), sam: T('sam'), afr: T('afr'), ind: T('ind'),
    grl: wf('s003', 'greenland'), fla: wf('s003', 'florida'), baja: wf('s003', 'baja'), kam: T('kam'),
    south: T('south'), dash: wf('s004', 'dashboard'), july: T('july'),
    two: T('twothirds'), eq: T('eq'), nine: T('nine'),
    s006: segS('s006'), southern: wf('s006', 'southern'), coin: T('coin'),
    not: T('not'), entirely: T('entirely'),
    s008: segS('s008'), why: T('why'), pointing: T('pointing'),
    s009: segS('s009'), dig: wf('s009', 'dig'), usa: T('usa'),
    t1875: T('t1875'), wrong: T('wrong'), last: T('last'), crash: T('crash'), eventually: wf('s010', 'eventually'),
    s011: segS('s011'), bacon: T('bacon'), fb: T('fb'), narrow: T('narrow'),
    breath: T('breath'), africa13: wf('s013', 'africa'), accident: T('accident'),
    s014: segS('s014'), open: wf('s014', 'open'), southcont: T('southcont'), antar: T('antar'), cent: T('cent'), rem: T('rem'),
    s015: segS('s015'), scratch: T('scratch'), s016: segS('s016'), puzzle: wf('s016', 'puzzle'), same: T('same'),
    s017: segS('s017'), explain: T('explain'), anyone: T('anyone'), tryW: T('try'),
    s018: segS('s018'), cook: T('cook'), claimed: wf('s018', 'claimed'), alike: T('alike'), mtn: T('mtn'),
    s019: segS('s019'), expl: T('expl'), wave: T('wave'), carved: T('carved'), some: wf('s019', 'some'), bought: T('bought'), refund: T('refund'),
    s020: segS('s020'), pyr: T('pyr'), list: T('list'),
    l1: T('l1'), l2: T('l2'), l3: T('l3'), l4: T('l4'), l5: T('l5'), quote21: wf('s021', 'all'),
    s022: segS('s022'), seventies: T('seventies'), joke: T('joke'), contl: wf('s022', 'continental'), drip: wf('s022', 'drip'), staring: T('staring'),
    s023: segS('s023'), version: T('version'), hold: T('hold'), think: T('think'),
    s024: segS('s024'), first: wf('s024', 'first'), far: T('far'),
  };
  const END = C.t1;

  // ------------------------------------------------------------------ assets
  const IM = {
    ee: 'tex/equal_earth.jpg', north: 'tex/data/land_north.png',
    title: IMG('title_1620.jpg'), bacon: IMG('bacon.jpg'), p246: IMG('ch1_bacon_n246.jpg'), p387: IMG('ch1_bacon_n387.jpg'),
    green45: IMG('green_fig45.jpg'), forster: IMG('forster.jpg'), f12: IMG('ch1_forster_p12.jpg'), f13: IMG('ch1_forster_p13.jpg'),
    greenPref: IMG('ch1_green_preface.jpg'), guyot: IMG('ch1_guyot_p22.jpg'), humboldt: IMG('ch1_humboldt.jpg'),
    // the four future-supercontinent end states (rendered from ch6's model holds) for the s010 teaser flash
    m0: IMG('ch1_model_0.jpg'), m1: IMG('ch1_model_1.jpg'), m2: IMG('ch1_model_2.jpg'), m3: IMG('ch1_model_3.jpg'),
  };
  await api.loadImages(Object.values(IM));
  const img = (k) => api.img(IM[k]);

  const C50 = await loadGeo('ne_50m_admin_0_countries');
  const coast = await loadGeo('ne_50m_coastline');
  const cities = (await loadGeo('ne_110m_populated_places_simple')).features
    .map(f => ({ lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1], pop: f.properties.pop_max || 0 }))
    .sort((a, b) => a.lon - b.lon);
  const F_SA = await region('south america'), F_AF = await region('africa'), F_IN = await region('india');
  const F_GRL = [findFeature(C50, 'Greenland')], F_FLA = await region('florida'), F_BAJA = await region('baja'), F_KAM = await region('kamchatka');
  const F_US = [findFeature(C50, 'United States of America')];
  const R_SA = allRings(F_SA), R_AF = allRings(F_AF);

  // coastline runs inside a box [lon0, lat0, lon1, lat1] (southern-tip outlines)
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

  // ------------------------------------------------------------------ globe overlays (each installed by its owning shot)
  const mk = X.makeCanvas;
  // cold-open composite: SA, Africa, India, each with its own alpha (redrawn only on change)
  const COLD = { parts: [], cv: mk(2048, 1024), sig: '' };
  for (const fs of [F_SA, F_AF, F_IN]) { const c = mk(2048, 1024); fillEquirect(c, WB, fs, { color: PAL.hero, alpha: 0.92, glow: 22 }); COLD.parts.push(c); }
  const coldSet = (a) => {
    const sig = a.map(v => v.toFixed(2)).join(','); if (sig === COLD.sig) return; COLD.sig = sig;
    const cg = COLD.cv.getContext('2d'); cg.clearRect(0, 0, 2048, 1024);
    a.forEach((v, i) => { if (v > 0.004) { cg.globalAlpha = v; cg.drawImage(COLD.parts[i], 0, 0); } }); cg.globalAlpha = 1;
    if (g.u.ovTex.value?.image === COLD.cv) g.refreshOverlay();
  };
  coldSet([1, 1, 1]);
  const NORTH = mk(4096, 2048); NORTH.getContext('2d').drawImage(img('north'), 0, 0, 4096, 2048);
  const USOV = mk(2048, 1024); fillEquirect(USOV, WB, F_US, { color: PAL.hero, alpha: 0.9, glow: 18 });
  // fog over the far south (hides Antarctica's outline until "centuries")
  const FOG = mk(2048, 1024);
  {
    const fg = FOG.getContext('2d'), r = F.rng(91), Y = la => (90 - la) / 180 * 1024;
    const band = fg.createLinearGradient(0, Y(-52), 0, Y(-66)); band.addColorStop(0, 'rgba(214,226,238,0)'); band.addColorStop(1, 'rgba(214,226,238,0.92)');
    fg.fillStyle = band; fg.fillRect(0, Y(-52), 2048, Y(-66) - Y(-52)); fg.fillStyle = 'rgba(214,226,238,0.92)'; fg.fillRect(0, Y(-66), 2048, 1024 - Y(-66));
    for (let i = 0; i < 520; i++) {
      const la = -54 - r() * 34, lo = -180 + r() * 360, ry = 6 + r() * 16, rx = Math.min(700, ry / Math.max(0.12, Math.cos(la * D2R)));
      const x = (lo + 180) / 360 * 2048, y = Y(la);
      const gg = fg.createRadialGradient(0, 0, 0, 0, 0, 1); gg.addColorStop(0, `rgba(245,250,255,${0.25 + r() * 0.3})`); gg.addColorStop(1, 'rgba(245,250,255,0)');
      fg.save(); fg.translate(x, y); fg.scale(rx, ry); fg.fillStyle = gg; fg.beginPath(); fg.arc(0, 0, 1, 0, Math.PI * 2); fg.fill(); fg.restore();
    }
  }
  // paleo globe 180 Ma (South America, Africa, India in orange, clustered around Antarctica)
  const coast180 = await api.loadJSON('paleo/coast_180.json');
  const tracks = await api.loadJSON('paleo/tracks.json');
  const PALEO = mk(2048, 1024);
  const pip = (poly, lon, lat) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j]; if (((yi > lat) !== (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) c = !c; } return c; };
  {
    const pg = PALEO.getContext('2d'), Xp = lo => (lo + 180) / 360 * 2048, Yp = la => (90 - la) / 180 * 1024;
    const path = (ps) => { pg.beginPath(); for (const r of ps) { r.forEach(([lo, la], i) => i ? pg.lineTo(Xp(lo), Yp(la)) : pg.moveTo(Xp(lo), Yp(la))); pg.closePath(); } };
    path(coast180); pg.fillStyle = '#d6c79c'; pg.fill('nonzero'); pg.strokeStyle = 'rgba(255,255,255,0.4)'; pg.lineWidth = 1.5; pg.stroke();
    const hot = coast180.filter(poly => ['samerica_c', 'africa_c', 'india_c'].some(k => { const p = tracks[k][180]; return p && p[0] < 900 && pip(poly, p[0], p[1]); }));
    path(hot); pg.fillStyle = PAL.hero; pg.fill('nonzero'); pg.strokeStyle = '#ffffff'; pg.lineWidth = 2; pg.stroke();
  }
  const ANT180 = tracks.antarctica_c[180]; // [lon, lat]

  // ------------------------------------------------------------------ Equal Earth flat map
  const EEB = mk(EE_W, EE_H);
  {
    const eg = EEB.getContext('2d'); const out = eeOutline();
    eg.save(); eg.clip(out); eg.drawImage(img('ee'), 0, 0);
    eg.globalCompositeOperation = 'saturation'; eg.fillStyle = 'rgba(128,128,128,0.32)'; eg.fillRect(0, 0, EE_W, EE_H);
    eg.globalCompositeOperation = 'multiply'; eg.fillStyle = '#c3cbe0'; eg.fillRect(0, 0, EE_W, EE_H);
    eg.globalCompositeOperation = 'source-over'; eg.strokeStyle = 'rgba(200,220,255,0.07)'; eg.lineWidth = 2;
    for (let lo = -180; lo <= 180; lo += 30) { eg.beginPath(); for (let la = -90; la <= 90; la += 3) { const [x, y] = ee(lo, la); la === -90 ? eg.moveTo(x, y) : eg.lineTo(x, y); } eg.stroke(); }
    for (let la = -60; la <= 60; la += 30) { eg.beginPath(); for (let lo = -180; lo <= 180; lo += 3) { const [x, y] = ee(lo, la); lo === -180 ? eg.moveTo(x, y) : eg.lineTo(x, y); } eg.stroke(); }
    eg.restore(); eg.strokeStyle = 'rgba(120,170,255,0.28)'; eg.lineWidth = 3; eg.stroke(out);
  }
  const EP = { sa: eePath(F_SA), af: eePath(F_AF), in: eePath(F_IN), grl: eePath(F_GRL), fla: eePath(F_FLA), baja: eePath(F_BAJA), kam: eePath(F_KAM) };
  const EETIP = Object.fromEntries(SEVEN.map(k => [k, ee(TIPS[k][1], TIPS[k][0])]));
  const EEV = (lt) => ({ cx: 1850 + 6 * Math.sin(lt * 0.4), cy: 892, zoom: 1.04 + 0.0045 * lt }); // "the s003 framing"
  // draw the flat map; fills: [{path, a, outline}] ; returns xform
  const drawEE = (ctx, view, fills = []) => {
    const k = eeXform(view, W, H);
    ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
    ctx.drawImage(EEB, k.ox, k.oy, EE_W * k.s, EE_H * k.s);
    ctx.save(); ctx.setTransform(k.s, 0, 0, k.s, k.ox, k.oy); ctx.lineJoin = 'round';
    for (const f of fills) {
      if (f.a <= 0.003) continue;
      const pop = f.pop || 0;
      ctx.globalAlpha = f.a * 0.3; ctx.strokeStyle = f.color || PAL.hero; ctx.lineWidth = (10 + 18 * pop) / k.s; ctx.stroke(f.path);
      ctx.globalAlpha = f.a * (0.8 + 0.2 * pop); ctx.fillStyle = f.color || PAL.hero; ctx.fill(f.path, 'evenodd');
      if (f.outline !== false) { ctx.globalAlpha = f.a * (f.outline ?? 1); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = (1.6 + 1.5 * pop) / k.s; ctx.stroke(f.path); }
    }
    ctx.restore();
    k.pt = (x, y) => [k.ox + x * k.s, k.oy + y * k.s];
    k.ll = (lat, lon) => { const [x, y] = ee(lon, lat); return [k.ox + x * k.s, k.oy + y * k.s]; };
    return k;
  };

  // ------------------------------------------------------------------ backdrops
  const DESK = X.makeDesk(W, H, 7);
  const SPACE = X.makeSpace(W, H, 3, true);
  const SPACE2 = X.makeSpace(W, H, 5, false);
  const drawDesk = (ctx, lt) => { const s = 1.03 + 0.01 * Math.sin(lt * 0.3); ctx.drawImage(DESK, W / 2 - W * s / 2 + Math.sin(lt * 0.2) * 8, H / 2 - H * s / 2, W * s, H * s); };

  // ------------------------------------------------------------------ helpers
  const S = [];
  const base = (sc) => { sc.layer = sc.layer || 0; S.push(sc); return sc; };
  const over = (t0, t1, draw, layer = 6) => S.push({ t0, t1, layer, draw: (ctx, lt, tt) => draw(ctx, tt, lt) });
  const LOOK0 = { flatBase: 0, ovMul: 0, ovAlpha: 0, dim: 0, desat: 0.12, relief: 0.8, nightAmt: 1, exposure: 1.25, specAmt: 0.5, rimAmt: 0.35 };
  // globe shot wrapper: absolute-time extra(ctx, tt, lt, cam) + look defaults reset uniforms other shots may have changed
  const G = (o) => {
    const t0 = o.t0, lf = o.look;
    return base(globeShot(Object.assign({}, o, {
      look: (lt) => Object.assign({}, LOOK0, typeof lf === 'function' ? lf(lt, t0 + lt) : (lf || {})),
      pre: o.pre ? (lt) => o.pre(t0 + lt, lt) : undefined,
      extra: o.x ? (ctx, lt, a, cam) => o.x(ctx, t0 + lt, lt, cam) : undefined,
    })));
  };
  const pillT = (ctx, s, x, y, tt, a, b, o = {}) => {
    const al = env(tt, a, b, o.fi ?? 0.16, o.fo ?? 0.25); if (al <= 0.003) return;
    const sc = lerp(0.82, 1, E.outBack(prog(tt, a, a + 0.28, E.lin)));
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); F.pill(ctx, s, 0, 0, Object.assign({ anchor: 'center', size: 40, alpha: al, bg: 'rgba(8,11,18,0.8)' }, o)); ctx.restore();
  };
  const proj = (lat, lon) => g.project(lat, lon);
  const ringLL = (lat, lon, rDeg, n = 120) => { const out = []; for (let i = 0; i <= n; i++) { const a = i / n * Math.PI * 2; out.push([lon + rDeg * Math.cos(a) / Math.max(0.2, Math.cos(lat * D2R)), lat + rDeg * Math.sin(a)]); } return [out]; };
  const triLL = (pts) => { const out = []; for (let i = 0; i < 3; i++) for (const p of gcLine(pts[i], pts[(i + 1) % 3], 24)) out.push([p.lon, p.lat]); return [out]; };
  // the three drip arcs from the tips to Antarctica (p per arc, staggered)
  const drawArcs = (ctx, tt, tStart, o = {}) => {
    ['froward', 'agulhas', 'kanya'].forEach((k, i) => {
      const a0 = tStart + i * (o.stagger ?? 0.15), p = prog(tt, a0, a0 + (o.d ?? 1.0), E.inOut); if (p <= 0) return;
      const pts = projectPath(g, gcLine(TIPS[k], o.to || POLE_T, 80, o.lift ?? 0.08)); if (pts.length < 2) return;
      const head = F.glowPath(ctx, pts, { p, color: '#ffffff', width: 3.2, alpha: o.alpha ?? 0.92, glowColor: '#ffd9c8' });
      if (p < 1 && head) F.dot(ctx, head[0], head[1], { r: 6, color: '#ffffff' });
    });
  };
  const poleRing = (ctx, tt, o = {}) => { const q = proj(-90, 0); if (!q.visible) return; X.southRing(ctx, q.x, q.y, tt, o); };
  const tipMarkers = (ctx, tt, keys, t0, o = {}) => keys.forEach((k, i) => { const a = t0 + i * (o.stagger ?? 0.12); if (tt < a) return; const q = proj(...TIPS[k]); if (!q.visible) return; F.dot(ctx, q.x, q.y, { r: o.r || 7, color: o.color || PAL.hero, ring: ((tt - a) * 0.8) % 1 }); });

  // ================================================================== s001–s002  COLD OPEN globe (thumbnail in motion)
  const coldAlpha = (tt) => {
    const dim = lerp(1, 0.3, prog(tt, t.melt + 0.1, t.melt + 0.4));
    return [Math.max(dim, tt >= t.sam - 0.08 ? 1 : 0), Math.max(dim, tt >= t.afr - 0.08 ? 1 : 0), Math.max(dim, tt >= t.ind - 0.08 ? 1 : 0)];
  };
  G({
    t0: 0, t1: t.grl - 0.07, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.3, sun: { lookOffset: [0, -0.06] },
    keys: [{ t: 0, lat: -28, lon: -24, alt: 3.2 }, { t: 1.6, lat: -29, lon: -15, alt: 3.15, ease: E.out },
      { t: t.afr - 0.3, lat: -28, lon: -8, alt: 3.15, ease: E.inOutSine }, { t: t.ind - 0.2, lat: -22, lon: 52, alt: 3.25, ease: E.inOutExpo },
      { t: t.grl, lat: -22, lon: 56, alt: 3.25 }],
    look: { desat: 0.3, dim: 0.35, ovAlpha: 1 },
    pre: (tt) => coldSet(coldAlpha(tt)),
    x: (ctx, tt) => {
      drawArcs(ctx, tt, t.melt - 0.08);
      [['froward', t.sam], ['agulhas', t.afr], ['kanya', t.ind]].forEach(([k, a]) => {
        if (tt < a - 0.08) return;
        strokeProjected(ctx, g, TIPRUN[k], { p: prog(tt, a - 0.08, a + 0.27, E.out), color: '#ffffff', width: 3.2, glow: true });
        const q = proj(...TIPS[k]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 6, color: '#ffffff', ring: ((tt - a) * 1.2) % 1 });
      });
      poleRing(ctx, tt, { r: 56 });
    },
  });
  cue(0, 'whoosh_soft', -12); cue(t.melt, 'shimmer', -16);
  for (const k of ['sam', 'afr', 'ind']) cue(t[k] - 0.07, 'pop_ui', -14);

  // ================================================================== s003–s004  Equal Earth flat map, the seven tips
  const TIPFILL = [['grl', t.grl, 'GREENLAND', 'farewell', [170, -40]], ['fla', t.fla, 'FLORIDA', 'sable', [150, 60]], ['baja', t.baja, 'BAJA', 'lucas', [-125, 70]], ['kam', t.kam, 'KAMCHATKA', 'lopatka', [-210, 40]]];
  const eeTipsShot = (t0, t1, popTimes, o = {}) => base({
    t0, t1, fadeIn: o.fadeIn || 0, draw(ctx, lt, tt) {
      const v = o.view ? o.view(lt, tt) : EEV(lt + (o.viewOff || 0));
      if (o.slide) v.cx += 260 * (1 - prog(lt, 0, 0.28, E.outExpo));
      const fills = [{ path: EP.sa, a: 1 }, { path: EP.af, a: 1 }, { path: EP.in, a: 1, pop: popTimes.in != null ? Math.max(0, 1 - Math.abs(tt - popTimes.in - 0.1) / 0.3) : 0 }];
      for (const [key, , , ,] of TIPFILL) { const tp = popTimes[key]; if (tp == null || tt < tp - 0.08) continue; fills.push({ path: EP[key], a: prog(tt, tp - 0.08, tp + 0.04), pop: Math.max(0, 1 - (tt - tp + 0.08) / 0.45) }); }
      const k = drawEE(ctx, v, fills);
      if (o.extra) o.extra(ctx, tt, lt, k);
      // one pill at a time, leader to the tip
      const order = TIPFILL.filter(f => popTimes[f[0]] != null).sort((a, b) => popTimes[a[0]] - popTimes[b[0]]);
      order.forEach((f, i) => {
        const a = popTimes[f[0]] - 0.08, b = i + 1 < order.length ? popTimes[order[i + 1][0]] - 0.1 : (o.lastPillEnd ?? a + 1.4);
        const al = env(tt, a, b, 0.12, 0.18); if (al <= 0.003) return;
        const [px, py] = k.pt(...EETIP[f[3]]);
        F.pill(ctx, f[2], px + f[4][0], py + f[4][1], { anchor: f[4][0] < 0 ? 'right' : 'left', leader: [px, py], size: 38, alpha: al, ring: ((tt - a) * 0.9) % 1 });
      });
    },
  });
  const pop003 = { grl: t.grl, fla: t.fla, baja: t.baja, kam: t.kam };
  eeTipsShot(t.grl - 0.07, t.dash - 0.08, pop003, {
    slide: true, lastPillEnd: t.kam + 1.25,
    extra: (ctx, tt, lt, k) => {
      if (tt < t.south - 0.1) return;
      SEVEN.forEach((key, i) => {
        const a = t.south - 0.1 + i * 0.06, p = prog(tt, a, a + 0.45, E.lin);
        const [x, y] = k.pt(...EETIP[key]); const wob = 1 + 0.12 * Math.sin((tt - a) * 5 + i) * prog(tt, a + 0.5, a + 1);
        dripArrow(ctx, x, y + 6, p, { len: 70 * wob, color: PAL.yellow, width: 5, head: 10 });
      });
    },
  });
  cue(t.grl - 0.2, 'whoosh_soft', -12);
  for (const k of ['grl', 'fla', 'baja', 'kam']) cue(t[k] - 0.07, 'pop_ui', -14);
  cue(t.south - 0.1, 'pop_ui', -18);

  // ================================================================== EXPLORER stage (gags 1 and 2 share one stage/actor)
  const { Actor, tinyPlanet, THREE } = await import('../../lib/actors.js');
  const { cutawayEarth, llDir, drillDir } = await import('../../lib/cutaway.js');
  const { tetraEarth } = await import('../../lib/morph.js');
  const gst = await api.newStage('ch1gag', { shadowExtent: 3.2, hemi: 1.45, key: 3.0, rim: 3.2, exposure: 1.18, keyColor: 0xffe2b8, rimColor: 0xa8d0ff, fov: 30 });
  const planet = await tinyPlanet(gst, { radius: 3 }); planet.position.set(0, -3, 0);
  if (planet.children[0]) planet.children[0].visible = false; // its additive glow shell reads as a giant dome at this distance
  const hero = await Actor.create(gst, 'models/adventurer.glb', { scale: 0.55 });
  const clipOK = (n) => !!hero.clips[n];
  const clip = (n, alt) => clipOK(n) ? n : alt;
  const rimL = gst.scene.children.find(o => o.isDirectionalLight && o !== gst.key);
  const dropMat = new THREE.MeshStandardMaterial({ color: 0xff5a36, emissive: 0x8a1c00, emissiveIntensity: 0.55, roughness: 0.22, metalness: 0.05 });
  const drop = new THREE.Group();
  { const s = new THREE.Mesh(new THREE.SphereGeometry(0.15, 32, 16), dropMat); const c = new THREE.Mesh(new THREE.ConeGeometry(0.141, 0.3, 32), dropMat); c.position.y = 0.2; s.castShadow = c.castShadow = true; drop.add(s); drop.add(c); }
  gst.add(drop); drop.visible = false;
  const bead = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 10), new THREE.MeshStandardMaterial({ color: 0x8feaff, emissive: 0x1d7088, roughness: 0.1 }));
  gst.add(bead); bead.visible = false;
  let headBone = null; hero.root.traverse(o => { if (!headBone && o.isBone && /head/i.test(o.name)) headBone = o; });
  const heroMats = []; hero.root.traverse(m => { if (m.isMesh && m.material && m.material.color) heroMats.push({ m: m.material, base: m.material.color.clone() }); });
  const WETC = new THREE.Color(0x2a4f6e);
  const setWet = (w) => { for (const h of heroMats) h.m.color.copy(h.base).lerp(WETC, 0.35 * w).multiplyScalar(1 - 0.22 * w); };
  const orient = (A, At, N, Nt) => { // rotate planet so lat/lon A points along At and N roughly along Nt
    const e1 = llDir(...A), n = llDir(...N); const e2 = n.clone().sub(e1.clone().multiplyScalar(n.dot(e1))).normalize(); const e3 = new THREE.Vector3().crossVectors(e1, e2);
    const f1 = new THREE.Vector3(...At).normalize(), m = new THREE.Vector3(...Nt); const f2 = m.clone().sub(f1.clone().multiplyScalar(m.dot(f1))).normalize(); const f3 = new THREE.Vector3().crossVectors(f1, f2);
    const R = new THREE.Matrix4().makeBasis(f1, f2, f3).multiply(new THREE.Matrix4().makeBasis(e1, e2, e3).transpose());
    return new THREE.Quaternion().setFromRotationMatrix(R);
  };
  const Q_G1 = orient(TIPS.agulhas, [0, Math.cos(0.42), Math.sin(0.42)], [5, 20], [0, Math.cos(-0.9), Math.sin(-0.9)]);
  const Q_G2 = orient([-28, -14], [0, Math.cos(0.22), Math.sin(0.22)], [8, -14], [0, Math.cos(-0.7), Math.sin(-0.7)]);
  const R0 = 3;
  const onYZ = (al, h = 0) => new THREE.Vector3(0, -R0 + (R0 + h) * Math.cos(al), (R0 + h) * Math.sin(al));
  const onXY = (be, h = 0) => new THREE.Vector3((R0 + h) * Math.sin(be), -R0 + (R0 + h) * Math.cos(be), 0);
  // Explorer timeline (absolute times; both gags)
  const G1 = t.dash - 0.08, G1e = t.two - 0.08;
  const G2 = t.wave - 0.04, G2c = t.some + 0.8, G2e = segS('s020');
  hero.play(G1, clip('Walk', 'Idle'), { fade: 0.05 }).play(G1 + 0.5, clip('Interact', 'Idle'), { fade: 0.15, once: true })
    .play(G1 + 1.3, clip('HitRecieve_2', 'HitRecieve'), { fade: 0.12, once: true }).play(G1e - 0.25, 'Idle', { fade: 0.25 });
  hero.play(G2 - 0.5, 'Idle', { fade: 0 }).play(G2 + 0.35, clip('Run_Right', 'Run'), { fade: 0.15 })
    .play(t.carved - 0.06, 'HitRecieve', { fade: 0.06, once: true }).play(t.carved + 0.9, clip('Idle_Neutral', 'Idle'), { fade: 0.35 });
  api.log('ch1 explorer clips: ' + Object.keys(hero.clips).join(','));

  const gagBg = (ctx, warm) => ctx.drawImage(warm ? SPACE : SPACE2, 0, 0);
  // ---- GAG 1: the dashboard melt — Explorer tries to catch the drip at Cape Agulhas and wobbles at the edge
  base({
    t0: G1, t1: G1e, draw(ctx, lt, tt) {
      gagBg(ctx, true);
      planet.quaternion.copy(Q_G1);
      // walk in, lunge toward the drip as it slips (the 'catch'), then teeter at the edge
      const wob = prog(tt, G1 + 1.35, G1 + 1.6) * (1 - prog(tt, G1e - 0.35, G1e));
      const al = lerp(0.02, 0.2, prog(tt, G1, G1 + 0.55, E.out)) + 0.14 * prog(tt, G1 + 0.5, G1 + 1.2, E.inOut) - 0.06 * prog(tt, G1 + 1.3, G1 + 1.6, E.out)
        + 0.05 * wob * Math.sin((tt - G1 - 1.35) * Math.PI * 2 * 2.6);
      const pitch = 0.22 * wob * Math.sin((tt - G1 - 1.35) * Math.PI * 2 * 2.6 + 0.6);
      hero.root.position.copy(onYZ(al)); hero.root.quaternion.setFromEuler(new THREE.Euler(al + pitch, 0, 0, 'XYZ'));
      setWet(0); bead.visible = false;
      // the drip: swells at the cape, slides down the front curve, falls into space
      drop.visible = true;
      const sw = E.outBack(prog(tt, G1 + 0.05, G1 + 0.55, E.lin));
      const sl = prog(tt, G1 + 0.75, G1 + 1.5, E.in), a0 = 0.42, a1 = 0.74;
      const ad = lerp(a0, a1, sl);
      let pos = onYZ(ad, 0.15), dir;
      const n = new THREE.Vector3(0, Math.cos(ad), Math.sin(ad)), tg = new THREE.Vector3(0, -Math.sin(ad), Math.cos(ad));
      dir = n.clone().lerp(tg.clone().negate(), clamp(sl * 3)).normalize();
      if (tt > G1 + 1.5) { const dt = tt - G1 - 1.5; const tg1 = new THREE.Vector3(0, -Math.sin(a1), Math.cos(a1)); pos = onYZ(a1, 0.15).add(tg1.multiplyScalar(1.6 * dt)).add(new THREE.Vector3(0, -2.2 * dt * dt + 0.5 * dt, 0.35 * dt)); dir = new THREE.Vector3(Math.sin(dt * 7) * 0.4, 1, 0.2).normalize(); }
      drop.position.copy(pos); drop.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir); drop.scale.setScalar(Math.max(0.001, sw * (1 + 0.06 * Math.sin(tt * 14) * (1 - sl))));
      gst.key.position.set(-4, 8, 5); if (rimL) rimL.position.set(6, 3, -3.5);
      const ca = lt * 0.04;
      gst.lookFrom([-4.4 + ca, 0.02, 2.6 + ca * 0.5], [0, 0.12, 1.2], 33);
      ctx.drawImage(gst.render(tt), 0, 0);
      drop.visible = false;
      X.sunFlare(ctx, W, H, tt, 1);
      // heat shimmer tint
      ctx.fillStyle = 'rgba(255,120,40,0.06)'; ctx.fillRect(0, 0, W, H);
    },
  });
  cue(G1 + 1.3, 'cartoon_fall', -10);

  // ================================================================== s005–s007  north/south land split, coin, the flash
  const BAR = { x: 1380, y: 800, w: 380, h: 26 };
  const S5_1 = t.entirely - 0.08;
  G({
    t0: G1e, t1: S5_1, overlay: { canvas: NORTH, bounds: WB }, drift: 0.2,
    keys: [{ t: 0, lat: 15, lon: 16, alt: 3.2 }, { t: t.s006 - G1e, lat: 16, lon: 24, alt: 3.1 }, { t: t.coin - G1e, lat: -14, lon: 22, alt: 2.9 }, { t: S5_1 - G1e, lat: -18, lon: 24, alt: 2.8 }],
    look: (lt, tt) => {
      const on = prog(tt, t.two - 0.1, t.two + 0.5), low = prog(tt, t.nine - 0.05, t.nine + 0.35), off = prog(tt, t.s006, t.s006 + 0.6);
      return { ovAlpha: on * lerp(1, 0.3, low) * (1 - off), dim: 0.45 * on * (1 - 0.6 * off), desat: 0.2 };
    },
    x: (ctx, tt) => {
      // equator ring
      if (tt > t.eq - 0.1) strokeProjected(ctx, g, [Array.from({ length: 121 }, (_, i) => [-180 + i * 3, 0])], { p: prog(tt, t.eq - 0.1, t.eq + 0.9, E.inOut), color: '#ffffff', width: 2.6, glow: true, alpha: 1 - prog(tt, t.s006 + 0.2, t.s006 + 0.8) });
      // city dots (nine in ten of us)
      const ca = prog(tt, t.nine - 0.1, t.nine + 0.6, E.lin) * (1 - prog(tt, t.s006 + 0.3, t.s006 + 0.9));
      if (ca > 0) {
        ctx.save();
        cities.forEach((c, i) => {
          const k = clamp((ca * 1.25 - i / cities.length * 0.25) * 4); if (k <= 0) return;
          const q = proj(c.lat, c.lon); if (!q.visible) return;
          const r = (2 + Math.sqrt(c.pop) / 750) * E.outBack(k);
          ctx.globalAlpha = 0.25 * k; ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(q.x, q.y, r * 2.4, 0, Math.PI * 2); ctx.fill();
          ctx.globalAlpha = 0.95 * k; ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, Math.PI * 2); ctx.fill();
        });
        ctx.restore();
      }
      // split bar: north share (orange) vs south (cyan); land 68 % -> people ~ 90 %
      const ba = prog(tt, t.eq - 0.2, t.eq + 0.2) * (1 - prog(tt, t.s006 + 0.2, t.s006 + 0.6));
      if (ba > 0) {
        const fill = lerp(0, 0.68, prog(tt, t.eq, t.eq + 0.9, E.outExpo)) + (0.9 - 0.68) * prog(tt, t.nine, t.nine + 0.8, E.outExpo);
        ctx.save(); ctx.globalAlpha = ba;
        ctx.fillStyle = 'rgba(8,11,18,0.75)'; F.round(ctx, BAR.x - 14, BAR.y - 14, BAR.w + 28, BAR.h + 28, 18); ctx.fill();
        ctx.fillStyle = PAL.cyan; F.round(ctx, BAR.x, BAR.y, BAR.w, BAR.h, 10); ctx.fill();
        ctx.fillStyle = PAL.hero; F.round(ctx, BAR.x, BAR.y, Math.max(2, BAR.w * fill), BAR.h, 10); ctx.fill();
        ctx.fillStyle = '#fff'; ctx.fillRect(BAR.x + BAR.w * fill - 2, BAR.y - 8, 4, BAR.h + 16);
        // N / S glyph arrows (no digits)
        ctx.fillStyle = PAL.hero; ctx.beginPath(); ctx.moveTo(BAR.x + 6, BAR.y - 26); ctx.lineTo(BAR.x + 18, BAR.y - 42); ctx.lineTo(BAR.x + 30, BAR.y - 26); ctx.fill();
        ctx.fillStyle = PAL.cyan; ctx.beginPath(); ctx.moveTo(BAR.x + BAR.w - 30, BAR.y + BAR.h + 26); ctx.lineTo(BAR.x + BAR.w - 18, BAR.y + BAR.h + 42); ctx.lineTo(BAR.x + BAR.w - 6, BAR.y + BAR.h + 26); ctx.fill();
        ctx.restore();
      }
      pillT(ctx, 'TWO-THIRDS OF ALL LAND', BAR.x + BAR.w / 2, BAR.y - 80, tt, t.two - 0.1, t.nine - 0.12);
      pillT(ctx, 'NEARLY 9 IN 10 OF US', BAR.x + BAR.w / 2, BAR.y - 80, tt, t.nine - 0.1, t.s006 + 0.4);
      // "those southern points"
      if (tt > t.southern - 0.1) {
        const a = 1 - prog(tt, t.not, t.not + 0.3);
        [['froward', 0], ['agulhas', 0.12], ['kanya', 0.24]].forEach(([k, d]) => { strokeProjected(ctx, g, TIPRUN[k], { p: prog(tt, t.southern - 0.1 + d, t.southern + 0.35 + d, E.out), color: '#ffffff', width: 3, glow: true, alpha: a }); });
        tipMarkers(ctx, tt, ['froward', 'agulhas', 'kanya'], t.southern - 0.1, { r: 6 });
      }
      // the coin
      if (tt > t.coin - 0.1) {
        const sp = E.outBack(prog(tt, t.coin - 0.1, t.coin + 0.35, E.lin));
        const frozen = tt >= t.not - 0.04; const tp = frozen ? t.not - 0.04 : tt;
        let ph = (tp - t.coin) * Math.PI * 2 * 1.5; if (frozen) ph = Math.round(ph / (Math.PI * 2)) * Math.PI * 2 + 0.25;
        const crack = prog(tt, t.not + 0.02, t.not + 0.55, E.out);
        X.coin(ctx, 960, 470 + 14 * Math.sin(tt * 2.2) * (1 - crack), 150 * sp, ph, { crack, alpha: 1 - prog(tt, t.not + 0.45, t.entirely - 0.1) });
        pillT(ctx, 'JUST A COINCIDENCE?', 960, 790, tt, t.coin - 0.08, t.not + 0.5);
      }
    },
  });
  cue(t.eq, 'tick_counter', -16); cue(t.nine, 'tick_counter', -16); cue(t.coin, 'bell_small', -14); cue(t.not, 'impact_short', -10);

  // ---- 1-second unexplained flash of the answer: 180 Ma, south-polar view
  const S7_1 = t.entirely + 0.95;
  G({
    t0: S5_1, t1: S7_1, overlay: { canvas: PALEO, bounds: WB }, drift: 4,
    keys: [{ t: 0, lat: -50, lon: 0, alt: 2.15, ease: E.lin }, { t: 1, lat: -53, lon: 8, alt: 2.0 }],
    look: { flatBase: 1, ovAlpha: 1, ovMul: 1, nightAmt: 0, relief: 0, desat: 0, exposure: 1.3 },
    x: (ctx, tt, lt) => {
      const q = proj(ANT180[1], ANT180[0]); if (q.visible) X.southRing(ctx, q.x, q.y, tt, { r: 120, q: false });
      // flash frames + film-burn edge
      const fl = 1 - prog(lt, 0, 0.12, E.lin); if (fl > 0) { ctx.fillStyle = `rgba(255,248,235,${0.85 * fl})`; ctx.fillRect(0, 0, W, H); }
      const ed = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H); ed.addColorStop(0, 'rgba(255,140,60,0)'); ed.addColorStop(1, 'rgba(255,140,60,0.22)'); ctx.fillStyle = ed; ctx.fillRect(0, 0, W, H);
    },
  });
  cue(S5_1, 'whoosh_soft', -12);

  // ================================================================== s008  "why do the continents point south?"
  const S8_1 = t.s009 - 0.06;
  G({
    t0: S7_1, t1: S8_1, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.5, sun: { lookOffset: [0, -0.05] },
    keys: [{ t: 0, lat: -36, lon: 18, alt: 3.0, tilt: 0, ease: E.out }, { t: S8_1 - S7_1, lat: -56, lon: 22, alt: 2.15, tilt: 14 }],
    look: { desat: 0.3, dim: 0.3, ovAlpha: 1 },
    pre: () => coldSet([1, 1, 1]),
    x: (ctx, tt) => {
      drawArcs(ctx, tt, S7_1 + 0.25, { d: 1.2, stagger: 0.2, to: [-89.5, 0], lift: 0.06 });
      const fl = prog(tt, t.pointing - 0.06, t.pointing + 0.7, E.out);
      poleRing(ctx, tt, { r: 46, flare: tt > t.pointing - 0.06 ? fl : 0 });
      const hw = [{ w: 'WHY' }, { w: 'DO' }, { w: 'THE' }, { w: 'CONTINENTS' }, { w: 'POINT' }, { w: 'SOUTH?', c: PAL.hero }];
      F.headline(ctx, hw, W / 2, 196, tt - (t.why - 0.1), { size: 116, per: 0.11, tOut: S8_1 - t.why - 0.25 });
    },
  });
  cue(t.pointing - 4, 'riser_tension', -12);

  // ================================================================== s009  teaser: can't dig to China
  const KANSAS = [39.83, -98.58];
  G({
    t0: S8_1, t1: t.usa - 0.07, overlay: { canvas: USOV, bounds: WB }, drift: 0.4,
    keys: [{ t: 0, lat: -40, lon: 0, alt: 2.6, ease: E.inOutExpo }, { t: 1.9, lat: 34, lon: -96, alt: 2.25 }, { t: 3.4, lat: 36, lon: -98, alt: 2.0 }],
    look: (lt) => ({ desat: 0.3, dim: 0.3, ovAlpha: prog(lt, 1.2, 1.9) }),
    x: (ctx, tt) => {
      if (tt < t.dig - 0.3) return;
      const q = proj(...KANSAS); if (!q.visible) return;
      const p = prog(tt, t.dig - 0.1, t.dig + 0.5, E.out);
      F.dot(ctx, q.x, q.y, { r: 8, color: '#ffffff', ring: ((tt - t.dig) * 1.1) % 1 });
      // dashed "dig" line straight down into the planet
      ctx.save(); ctx.strokeStyle = PAL.cyan; ctx.lineWidth = 4; ctx.setLineDash([10, 10]); ctx.lineDashOffset = -tt * 40;
      ctx.beginPath(); ctx.moveTo(q.x, q.y); ctx.lineTo(q.x, q.y + 170 * p); ctx.stroke(); ctx.restore();
    },
  });
  cue(S8_1, 'whoosh_soft', -12);

  // ================================================================== diorama stage: cutaway + tetrahedron
  const dst = await api.newStage('ch1dio', { shadows: false, hemi: 1.5, key: 2.6, rim: 1.8, exposure: 1.12 });
  const ce = await cutawayEarth(dst, { radius: 3, map: IMG('ch1_day4k.jpg') });
  const te = await tetraEarth(dst, { radius: 2.2, map: IMG('ch1_day4k.jpg') });
  const UP = new THREE.Vector3(0, 1, 0);
  const dioBg = (ctx, warm) => {
    const gr = ctx.createRadialGradient(W / 2, H * 0.45, 60, W / 2, H / 2, H * 1.05);
    gr.addColorStop(0, warm ? '#3a3a4a' : '#2c4166'); gr.addColorStop(0.55, warm ? '#161722' : '#111b30'); gr.addColorStop(1, '#04060b');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  };
  const cutShot = (t0, t1, o) => base({
    t0, t1, draw(ctx, lt, tt) {
      dioBg(ctx, false); ce.visible = true; te.visible = false;
      const q0 = new THREE.Quaternion().setFromUnitVectors(llDir(...o.top), UP);
      const qy = new THREE.Quaternion().setFromAxisAngle(UP, (o.spin || 0) * lt);
      ce.userData.shell.quaternion.copy(qy.multiply(q0));
      const p = prog(tt, o.drill0, o.drill0 + o.drillD, E.inOut);
      if (p > 0) { drillDir(ce, UP, p); ce.userData.drill.visible = true; } else if (ce.userData.drill) ce.userData.drill.visible = false;
      const k = prog(lt, 0, t1 - t0, E.inOutSine), cp = o.cam(k);
      dst.lookFrom(cp[0], cp[1], cp[2]);
      ctx.drawImage(dst.render(tt), 0, 0);
      if (o.extra) o.extra(ctx, tt, lt, p);
    },
  });
  cutShot(t.usa - 0.07, t.t1875 - 0.07, {
    top: KANSAS, spin: 0.05, drill0: t.usa + 0.05, drillD: 1.2,
    cam: (k) => [[lerp(7.9, 7.3, k), lerp(4.1, 3.8, k), lerp(7.6, 7.2, k)], [0, -0.35, 0], 32],
    extra: (ctx, tt) => {
      const pa = prog(tt, t.usa + 1.2, t.usa + 1.45, E.lin); if (pa <= 0) return;
      const e = dst.project(new THREE.Vector3(0, -3.25, 0));
      ctx.save(); ctx.translate(e.x, e.y + 20); ctx.scale(E.outBack(pa), E.outBack(pa));
      F.text(ctx, '?', 0, 0, { size: 150, fam: F.FAM.head, weight: 400, align: 'center', baseline: 'middle', color: PAL.yellow, stroke: 8, strokeColor: 'rgba(0,0,0,0.6)' });
      ctx.restore();
      const top = dst.project(new THREE.Vector3(0, 3.06, 0)); F.dot(ctx, top.x, top.y, { r: 7, color: '#ffffff', ring: ((tt - t.usa) * 1.2) % 1 });
    },
  });
  cue(t.usa, 'sonar_ping', -12);

  // ================================================================== s010  1875 tetrahedron -> wrong; the last one; four models; black
  const TET0 = t.t1875 + 0.78;
  base({
    t0: t.t1875 - 0.07, t1: TET0, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      X.printKB(ctx, img('green45'), lt / (TET0 - t.t1875), [460, 70, 1000, 820], [0.5, 0.78, 1.55], [0.5, 0.76, 1.75], { grade: 'sepia', vig: 0.4 });
      const fl = 1 - prog(lt, 0, 0.1, E.lin); if (fl > 0) { ctx.fillStyle = `rgba(255,240,215,${0.6 * fl})`; ctx.fillRect(0, 0, W, H); }
    },
  });
  base({
    t0: TET0, t1: t.last - 0.07, draw(ctx, lt, tt) {
      dioBg(ctx, true); ce.visible = false; te.visible = true;
      const kIn = prog(tt, TET0 + 0.05, TET0 + 1.5, E.inOut), kOut = prog(tt, t.wrong - 0.04, t.wrong + 0.5, E.lin);
      const k = tt < t.wrong - 0.04 ? kIn : 1 - E.outBack(kOut);
      te.userData.set(k, clamp(k * 1.4) * (1 - prog(tt, t.wrong, t.wrong + 0.3)));
      // camera above and pulled back so the whole pyramid (south vertex included) reads in 3D; a lit continental face turned to camera
      te.rotation.y = 2.35 + 0.35 * lt; te.rotation.x = 0.12;
      dst.lookFrom([1.5, 2.0, lerp(11.4, 10.6, prog(lt, 0, 3.8))], [0, lerp(-0.2, -0.75, kIn), 0], 32);
      ctx.drawImage(dst.render(tt), 0, 0);
      // thick yellow tetra edges in 2D (WebGL lines are 1 px): front edges bright, back edges faint
      const ea = clamp(k * 1.4) * (1 - prog(tt, t.wrong, t.wrong + 0.3));
      if (ea > 0.01) {
        te.updateMatrixWorld(true);
        const TV = [[-90, 0], [19.47, -75], [19.47, 45], [19.47, 165]].map(([la, lo]) => llDir(la, lo).multiplyScalar(2.2 * 1.55 * 1.002).applyMatrix4(te.matrixWorld));
        const cam = dst.camera.position, ctr = new THREE.Vector3().setFromMatrixPosition(te.matrixWorld);
        const dC = cam.distanceTo(ctr);
        for (const [i, j] of [[0, 1], [0, 2], [0, 3], [1, 2], [2, 3], [3, 1]]) {
          const mid = TV[i].clone().add(TV[j]).multiplyScalar(0.5), front = cam.distanceTo(mid) < dC;
          const a = dst.project(TV[i]), b = dst.project(TV[j]);
          ctx.save(); ctx.globalAlpha = ea * (front ? 1 : 0.3); ctx.lineCap = 'round';
          ctx.strokeStyle = 'rgba(0,0,0,0.55)'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); ctx.restore();
        }
      }
      X.redX(ctx, 960, 520, 170, prog(tt, t.wrong - 0.05, t.wrong + 0.17, E.lin) * (1 - prog(tt, t.last - 0.4, t.last - 0.1)));
    },
  });
  over(t.t1875 - 0.07, t.wrong - 0.1, (ctx, tt) => pillT(ctx, '1875', 960, 96, tt, t.t1875 - 0.07, t.wrong - 0.1, { size: 52 }));
  cue(t.t1875 - 0.05, 'paper_rustle', -16); cue(t.wrong, 'stamp', -12);
  // the cold-open globe spinning forward fast
  G({
    t0: t.last - 0.07, t1: t.crash - 0.07, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0,
    keys: [{ t: 0, lat: -24, lon: 20, alt: 2.9, ease: E.in }, { t: t.crash - t.last, lat: -18, lon: 260, alt: 2.7 }],
    look: { desat: 0.3, dim: 0.3, ovAlpha: 1 }, pre: () => coldSet([1, 1, 1]),
    x: (ctx, tt) => { poleRing(ctx, tt, { r: 40 }); },
  });
  cue(t.last - 0.1, 'whoosh_big', -12);
  // four model end-states (teaser grid): four views of a future Earth, the US marker pulsing in every tile
  let TILES = null;
  const makeTiles = () => {
    if (TILES) return TILES;
    // s010 '4 MODELS' teaser: the four end states the chapter-6 payoff shows (Pangaea Proxima, Novopangaea, Amasia, Aurica),
    // each already carrying the white US marker; tile colours match ch6's model colours
    TILES = [IM.m0, IM.m1, IM.m2, IM.m3].map((src) => { const c = mk(W / 2, H / 2); c.getContext('2d').drawImage(api.img(src), 0, 0, W / 2, H / 2); return { c, us: null }; });
    return TILES;
  };
  const TILE_COL = [PAL.hero, PAL.cyan, PAL.yellow, PAL.green];
  base({
    t0: t.crash - 0.07, t1: t.eventually - 0.04, draw(ctx, lt, tt) {
      const tiles = makeTiles();
      ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
      tiles.forEach((tl, i) => {
        // full alpha from the first frame (no dark blink on 'crash'); stagger with a scale pop instead
        const x0 = (i % 2) * W / 2, y0 = Math.floor(i / 2) * H / 2, a = 1;
        const s = 1.02 + 0.03 * lt + 0.08 * (1 - E.out(prog(lt, i * 0.05, i * 0.05 + 0.18, E.lin)));
        ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.rect(x0 + 4, y0 + 4, W / 2 - 8, H / 2 - 8); ctx.clip();
        ctx.drawImage(tl.c, x0 + W / 4 - W / 4 * s, y0 + H / 4 - H / 4 * s, W / 2 * s, H / 2 * s);
        if (tl.us) { const ux = x0 + W / 4 + (tl.us[0] - W / 4) * s, uy = y0 + H / 4 + (tl.us[1] - H / 4) * s; F.dot(ctx, ux, uy, { r: 7, color: '#ffffff', ring: ((lt * 1.4) + i * 0.25) % 1 }); }
        ctx.restore();
        ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = TILE_COL[i]; ctx.lineWidth = 4; ctx.strokeRect(x0 + 6, y0 + 6, W / 2 - 12, H / 2 - 12); ctx.restore();
      });
      pillT(ctx, '4 MODELS', W / 2, H / 2, tt, t.crash - 0.07, t.eventually, { size: 50 });
    },
  });
  cue(t.crash - 0.05, 'glitch_click', -14);
  // hard cut to black on "Eventually."
  const UP11 = t.s011 - 0.55;
  base({ t0: t.eventually - 0.04, t1: UP11, draw(ctx) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); } });
  cue(t.eventually - 0.02, 'impact_deep', -6);

  // ================================================================== s011  bad news: 2026 -> 1620
  const ALLTIPS = { grl: -10, fla: -10, baja: -10, kam: -10 };
  const P_TITLE = t.bacon - 0.2;
  eeTipsShot(UP11, P_TITLE + 0.55, ALLTIPS, {
    viewOff: 2, lastPillEnd: -9,
    extra: (ctx, tt, lt) => {
      // sepia paper wash wiping left -> right
      const wx = lerp(-60, W + 60, prog(tt, t.s011 + 0.1, t.s011 + 2.6, E.inOut));
      if (wx > 0) {
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, wx, H); ctx.clip();
        F.grade(ctx, 0, 0, W, H, 'sepia'); ctx.fillStyle = 'rgba(232,210,160,0.16)'; ctx.fillRect(0, 0, W, H);
        ctx.restore();
        const eg = ctx.createLinearGradient(wx - 80, 0, wx + 10, 0); eg.addColorStop(0, 'rgba(255,230,180,0)'); eg.addColorStop(1, 'rgba(255,230,180,0.35)'); ctx.fillStyle = eg; ctx.fillRect(wx - 80, 0, 90, H);
      }
      const fade = 1 - prog(lt, 0, 0.55, E.lin); if (fade > 0) { ctx.fillStyle = `rgba(0,0,0,${fade})`; ctx.fillRect(0, 0, W, H); }
    },
  });
  // title page of 1620 (cross-dissolve), Ken Burns from the galleon up to the title
  base({
    t0: P_TITLE, t1: t.fb - 0.07, fadeIn: 0.5, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      X.printKB(ctx, img('title'), lt / (t.fb - P_TITLE), [560, 60, 800, 900], [0.5, 0.75, 1.6], [0.5, 0.3, 1.15], { grade: 'sepia', vig: 0.35 });
    },
  });
  over(t.s011 + 0.2, t.fb - 0.1, (ctx, tt) => {
    const a = env(tt, t.s011 + 0.2, t.fb - 0.1, 0.25, 0.35); const p = prog(tt, t.s011 + 0.3, t.s011 + 2.6, E.inOut);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(10,8,6,0.62)'; F.round(ctx, 96, 70, 330, 140, 18); ctx.fill(); ctx.restore();
    F.counter(ctx, 2026, 1620, p, 120, 178, { size: 104, fam: F.FAM.mono, weight: 700, align: 'left', alpha: a, color: '#f3e3bd', format: (v) => String(Math.round(v)) });
  });
  cue(t.s011 + 0.05, 'time_rewind', -12); cue(P_TITLE, 'paper_rustle', -16);

  // ================================================================== s012  Bacon, 1620: "narrow and pointed toward the south"
  base({
    t0: t.fb - 0.07, t1: t.narrow - 0.07, draw(ctx, lt) {
      drawDesk(ctx, lt);
      X.printKB(ctx, img('bacon'), lt / (t.narrow - t.fb), [600, 70, 720, 880], [0.48, 0.3, 1.35], [0.47, 0.26, 1.62], { grade: 'sepia', vig: 0.38 });
    },
  });
  const BX = { acum: [0.568, 0.229, 0.130, 0.022], quod: [0.553, 0.131, 0.276, 0.017], cidit: [0.079, 0.153, 0.064, 0.016], austrum: [0.154, 0.334, 0.517, 0.019] };
  const PAGE_R = [200, 150, 1520, 700];
  const P387 = t.narrow + 1.45;
  base({
    t0: t.narrow - 0.07, t1: t.breath - 0.55, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const slide = prog(tt, P387, P387 + 0.45, E.outExpo);
      const m = X.printKB(ctx, img('p246'), lt / 3.2, PAGE_R, [0.47, 0.212, 1.3], [0.48, 0.222, 1.5], { grade: 'sepia', vig: 0.3, dim: 0.45 * slide });
      X.underline(ctx, m, BX.acum, prog(tt, t.narrow + 0.35, t.narrow + 0.8, E.inOut), { alpha: 1 - 0.5 * slide });
      if (slide > 0) {
        const r = [lerp(W + 80, 330, slide), 250, 1220, 560];
        const m2 = X.printKB(ctx, img('p387'), prog(tt, P387, P387 + 2.5), r, [0.42, 0.342, 1.55], [0.42, 0.344, 1.65], { grade: 'sepia', vig: 0.3, rot: -0.025 });
        X.underline(ctx, m2, BX.austrum, prog(tt, P387 + 0.45, P387 + 0.9, E.inOut));
        if (tt > P387 + 0.95) X.stamp(ctx, 'x2', r[0] + r[2] - 40, r[1] + 40, prog(tt, P387 + 0.95, P387 + 1.15, E.lin), { size: 84, color: PAL.hero, rot: 0.18, bg: 'rgba(20,8,4,0.6)' });
      }
      pillT(ctx, '"NARROW AND POINTED TOWARD THE SOUTH"', W / 2, 880, tt, t.narrow - 0.07, t.narrow + 1.9, { size: 46 });
      pillT(ctx, '"ACUMINATI": SHARPENED TO A POINT', W / 2, 880, tt, t.narrow + 1.9, t.breath - 0.6, { size: 46 });
    },
  });
  cue(t.narrow - 0.05, 'paper_rustle', -16); cue(P387 + 0.95, 'stamp', -18);
  // s013: same breath -> tilt up two lines on the same page
  base({
    t0: t.breath - 0.55, t1: t.africa13 - 0.15, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const m = X.printKB(ctx, img('p246'), prog(tt, t.breath - 0.4, t.africa13 - 0.2), PAGE_R, [0.47, 0.232, 1.32], [0.47, 0.135, 1.32], { grade: 'sepia', vig: 0.3, ease: E.inOut });
      X.underline(ctx, m, BX.acum, 1, { alpha: 0.7 });
    },
  });
  // Africa & South America side by side, matching capes pulsing
  G({
    t0: t.africa13 - 0.15, t1: t.accident - 0.08, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.3,
    keys: [{ t: 0, lat: -24, lon: -12, alt: 2.65 }, { t: 3.2, lat: -28, lon: -6, alt: 2.4 }],
    look: { desat: 0.3, dim: 0.35, ovAlpha: 1 }, pre: () => coldSet([0.5, 0.5, 0]),
    x: (ctx, tt, lt) => {
      strokeProjected(ctx, g, R_SA, { p: prog(lt, 0.05, 1.0, E.out), color: '#ffffff', width: 2.2 });
      strokeProjected(ctx, g, R_AF, { p: prog(lt, 0.25, 1.2, E.out), color: '#ffffff', width: 2.2 });
      tipMarkers(ctx, tt, ['froward', 'agulhas'], t.africa13 + 0.5, { r: 9, stagger: 0.25 });
    },
  });
  // "not to be attributed to mere accident"
  base({
    t0: t.accident - 0.08, t1: t.s014 - 0.07, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const m = X.printKB(ctx, img('p246'), lt / 3.0, PAGE_R, [0.46, 0.142, 1.25], [0.47, 0.146, 1.34], { grade: 'sepia', vig: 0.3 });
      X.highlight(ctx, m, BX.quod, prog(tt, t.accident + 0.05, t.accident + 0.4), { alpha: 0.18 });
      X.underline(ctx, m, BX.quod, prog(tt, t.accident, t.accident + 0.4, E.inOut));
      X.underline(ctx, m, BX.cidit, prog(tt, t.accident + 0.4, t.accident + 0.6, E.inOut));
      pillT(ctx, '"NOT TO BE ATTRIBUTED TO MERE ACCIDENT"', W / 2, 920, tt, t.accident - 0.05, t.s014 - 0.1, { size: 40 });
    },
  });
  cue(t.accident, 'shimmer', -18);

  // ================================================================== s014  "whether there is any southern continent" — fog over Antarctica
  G({
    t0: t.s014 - 0.07, t1: t.s015 - 0.07, overlay: { canvas: FOG, bounds: WB }, drift: 0.6,
    keys: [{ t: 0, lat: -18, lon: -8, alt: 3.0 }, { t: t.southcont - t.s014 - 0.2, lat: -26, lon: 2, alt: 2.85 },
      { t: t.southcont - t.s014 + 1.6, lat: -70, lon: 12, alt: 1.55, tilt: 18, ease: E.inOutExpo }, { t: t.s015 - t.s014, lat: -74, lon: 18, alt: 1.4, tilt: 24 }],
    look: (lt, tt) => ({ ovAlpha: lerp(0.95, 0.3, prog(tt, t.cent, t.cent + 1.0)), dim: 0.12, desat: 0.25 }),
    x: (ctx, tt) => {
      const q = proj(-90, 0);
      if (q.visible && tt > t.southcont + 0.4) {
        const a = prog(tt, t.southcont + 0.4, t.southcont + 1.0), s = 1 + 0.03 * Math.sin(tt * 1.6);
        ctx.save(); ctx.translate(q.x, q.y); ctx.scale(s, s); ctx.rotate(0.06 * Math.sin(tt * 0.9));
        F.text(ctx, '?', 0, 0, { size: 230, fam: F.FAM.serif, weight: 'italic 700', align: 'center', baseline: 'middle', color: '#ffffff', alpha: a * lerp(1, 0.85, prog(tt, t.cent, t.cent + 1)), shadowBlur: 30, shadowColor: 'rgba(10,20,40,0.6)' });
        ctx.restore();
      }
      pillT(ctx, '"WHETHER THERE IS ANY SOUTHERN CONTINENT"', W / 2, 900, tt, t.open - 0.1, t.antar - 0.15, { size: 40 });
      pillT(ctx, 'FIRST SEEN: 1820', W / 2, 900, tt, t.cent + 0.1, t.s015 - 0.15, { size: 44 });
      // sepia year ticker 1620 -> 1820
      const ya = env(tt, t.antar - 0.1, t.s015 - 0.15, 0.2, 0.3);
      if (ya > 0) {
        ctx.save(); ctx.globalAlpha = ya; ctx.fillStyle = 'rgba(30,20,10,0.72)'; F.round(ctx, 96, 70, 330, 140, 18); ctx.fill(); ctx.restore();
        F.counter(ctx, 1620, 1820, prog(tt, t.antar, t.cent + 0.1, E.inOut), 120, 178, { size: 104, fam: F.FAM.mono, weight: 700, align: 'left', alpha: ya, color: '#f3e3bd', format: (v) => String(Math.round(v)) });
      }
    },
  });
  cue(t.antar, 'tick_counter', -18); cue(t.southcont, 'whoosh_soft', -14);

  // ================================================================== s015–s016  Bacon "predicted drift"? -> JUICE CHECK: FALSE; rewind
  const BULL = { lat: 44, lon: -30.6, ang: 57 }; // Bullard 1965 South America -> Africa fit
  const rotRings = (rs, ang) => {
    const k = [Math.cos(BULL.lat * D2R) * Math.cos(BULL.lon * D2R), Math.sin(BULL.lat * D2R), -Math.cos(BULL.lat * D2R) * Math.sin(BULL.lon * D2R)];
    const th = ang * D2R, c = Math.cos(th), s = Math.sin(th);
    return rs.map(r => r.map(([lon, lat]) => {
      const p = [Math.cos(lat * D2R) * Math.cos(lon * D2R), Math.sin(lat * D2R), -Math.cos(lat * D2R) * Math.sin(lon * D2R)];
      const kx = [k[1] * p[2] - k[2] * p[1], k[2] * p[0] - k[0] * p[2], k[0] * p[1] - k[1] * p[0]], kd = k[0] * p[0] + k[1] * p[1] + k[2] * p[2];
      const q = [0, 1, 2].map(i => p[i] * c + kx[i] * s + k[i] * kd * (1 - c));
      return [Math.atan2(-q[2], q[0]) / D2R, Math.asin(Math.max(-1, Math.min(1, q[1]))) / D2R];
    }));
  };
  const R_SA_main = R_SA.filter(r => r.length > 40);
  const snapP = (tt) => {
    const go = (x) => E.inOutSine(prog(x, t.s015 + 0.35, t.s015 + 5.1, E.lin));
    if (tt < t.scratch - 0.03) return go(tt);
    const frozen = go(t.scratch - 0.03);
    return frozen * (1 - prog(tt, t.s016 + 0.55, t.s016 + 2.2, E.inOut));
  };
  const S16_EE = t.puzzle - 0.1;
  G({
    t0: t.s015 - 0.07, t1: S16_EE, drift: 0,
    overlay: null,
    keys: [{ t: 0, lat: -10, lon: -20, alt: 2.5, heading: -2 }, { t: t.scratch - t.s015, lat: -13, lon: -15, alt: 2.35, heading: 2 }, { t: t.s016 - t.s015 + 0.4, lat: -13, lon: -15, alt: 2.35, heading: 2 }, { t: S16_EE - t.s015, lat: -12, lon: -18, alt: 2.4, heading: 0 }],
    look: { dim: 0.32, desat: 0.35 },
    x: (ctx, tt, lt) => {
      // shake on the stamp
      const sh = tt > t.scratch && tt < t.scratch + 0.25 ? Math.sin(tt * 90) * 8 * (1 - (tt - t.scratch) / 0.25) : 0;
      ctx.save(); ctx.translate(sh, sh * 0.4);
      strokeProjected(ctx, g, R_AF, { color: 'rgba(255,255,255,0.75)', width: 2 });
      const p = snapP(tt);
      const moved = rotRings(R_SA_main, BULL.ang * p);
      strokeProjected(ctx, g, R_SA_main, { color: 'rgba(255,255,255,0.35)', width: 1.6, dash: [6, 8] });
      fillProjected(ctx, g, moved, { color: PAL.hero, alpha: 0.62 });
      strokeProjected(ctx, g, moved, { color: '#ffffff', width: 2.4 });
      ctx.restore();
      pillT(ctx, 'BACON PREDICTED DRIFT?', W / 2, 110, tt, t.s015 + 0.2, t.s016 + 0.6, { size: 44 });
      if (tt > t.scratch - 0.04) X.stamp(ctx, 'JUICE CHECK: FALSE', W / 2, 560, prog(tt, t.scratch - 0.04, t.scratch + 0.16, E.lin), { size: 104, rot: -0.1, alpha: 1 - prog(tt, t.s016 + 0.35, t.s016 + 0.7) });
      // rewind streaks
      const rw = prog(tt, t.s016 + 0.5, t.s016 + 0.7) * (1 - prog(tt, t.s016 + 2.1, t.s016 + 2.4));
      if (rw > 0) {
        ctx.save(); ctx.globalAlpha = rw * 0.5; ctx.fillStyle = '#ffffff';
        for (let i = 0; i < 7; i++) ctx.fillRect(0, (i * 173 + tt * 1300) % H, W, 2 + (i % 3));
        ctx.globalAlpha = rw; ctx.fillStyle = 'rgba(255,255,255,0.9)';
        for (const dx of [0, 34]) { ctx.beginPath(); ctx.moveTo(110 + dx, 90); ctx.lineTo(140 + dx, 70); ctx.lineTo(140 + dx, 110); ctx.fill(); }
        ctx.restore();
      }
    },
  });
  cue(t.scratch - 0.05, 'record_scratch', -12); cue(t.scratch + 0.02, 'stamp', -10); cue(t.s016 + 0.5, 'time_rewind', -16);
  // side by side on the flat map: same taper, same orientation
  const triEE = (apexK, baseLat, half) => { const [ax, ay] = EETIP[apexK]; const by = ee(0, baseLat)[1]; return [[ax - half, by], [ax + half, by], [ax, ay]]; };
  const TRI_SA = triEE('froward', 4, 250), TRI_AF = triEE('agulhas', 14, 360);
  base({
    t0: S16_EE, t1: t.s017 - 0.07, draw(ctx, lt, tt) {
      const zin = prog(lt, 0, 0.9, E.outExpo);
      const v = { cx: lerp(1850, 1680, zin) + 8 * Math.sin(lt * 0.5), cy: lerp(892, 990, zin), zoom: lerp(1.04, 1.4, zin) + 0.01 * lt };
      const k = drawEE(ctx, v, [{ path: EP.sa, a: 1 }, { path: EP.af, a: 1 }]);
      for (const [tri, d] of [[TRI_SA, 0], [TRI_AF, 0.25]]) {
        const p = prog(tt, t.same - 0.08 + d, t.same + 0.6 + d, E.inOut); if (p <= 0) continue;
        const pts = [...tri, tri[0]].map(q => k.pt(...q));
        ctx.save(); ctx.fillStyle = `rgba(255,255,255,${0.08 * p})`; ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.fill(); ctx.restore();
        F.glowPath(ctx, pts, { p, color: '#ffffff', width: 4, glowColor: '#ffffff' });
      }
      const ap = prog(tt, t.same + 0.6, t.same + 0.9, E.outBack);
      if (ap > 0) {
        const a = k.pt((TRI_SA[1][0] + TRI_AF[0][0]) / 2, (TRI_SA[2][1] * 0.35 + TRI_SA[0][1] * 0.65));
        ctx.save(); ctx.translate(a[0], a[1]); ctx.scale(ap, ap); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 9; ctx.lineCap = 'round';
        for (const dy of [-14, 14]) { ctx.beginPath(); for (let i = 0; i <= 20; i++) { const x = -38 + i * 3.8, y = dy + Math.sin(i / 20 * Math.PI * 2) * 7; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
        ctx.restore();
      }
      pillT(ctx, 'NOT PUZZLE PIECES. LOOKALIKES.', W / 2, 96, tt, t.puzzle, t.s017 - 0.1, { size: 44 });
    },
  });
  cue(t.same, 'pop_ui', -16);

  // ================================================================== s017  Bacon saw it; nobody could explain it; the pile topples
  const STACK = [{ k: 'f13', at: t.anyone - 0.05, rot: -0.07, dx: -10, dy: 0 }, { k: 'greenPref', at: t.anyone + 0.9, rot: 0.06, dx: 18, dy: -14 }, { k: 'guyot', at: t.anyone + 1.85, rot: -0.03, dx: -4, dy: -26 }];
  G({
    t0: t.s017 - 0.07, t1: t.s018 - 0.07, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.5,
    keys: [{ t: 0, lat: -38, lon: 10, alt: 2.75 }, { t: t.s018 - t.s017, lat: -44, lon: 32, alt: 2.55, tilt: 6 }],
    look: { desat: 0.3, dim: 0.3, ovAlpha: 1 }, pre: () => coldSet([1, 1, 1]),
    x: (ctx, tt, lt) => {
      drawArcs(ctx, tt, -10, {});
      poleRing(ctx, tt, { r: 42, q: tt < t.explain - 0.1 });
      const qp = prog(tt, t.explain - 0.1, t.explain + 0.3, E.lin);
      if (qp > 0) { const q = proj(-90, 0); if (q.visible) { ctx.save(); ctx.translate(q.x, q.y); const s = E.outBack(qp); ctx.scale(s, s); F.text(ctx, '?', 0, -6, { size: 190, fam: F.FAM.head, weight: 400, align: 'center', baseline: 'middle', color: '#ffffff', stroke: 8, strokeColor: 'rgba(0,0,0,0.5)' }); ctx.restore(); } }
      // n246 shrinks from full frame into a print top-left
      const sk = prog(lt, 0.15, 1.0, E.inOutExpo);
      const r = [lerp(200, 110, sk), lerp(150, 90, sk), lerp(1520, 430, sk), lerp(700, 250, sk)];
      if (sk < 1) { ctx.save(); ctx.globalAlpha = 1 - sk; drawDesk(ctx, lt); ctx.restore(); }
      // topple of the whole pile
      const tp = prog(tt, t.tryW - 0.05, t.tryW + 0.7, E.in);
      ctx.save();
      if (tp > 0) { const px = r[0] + r[2], py = r[1] + r[3]; ctx.translate(px, py); ctx.rotate(tp * 1.3); ctx.translate(-px + tp * 900, -py + tp * tp * 500); }
      const m = X.printKB(ctx, img('p246'), 0.3, r, [0.48, 0.212, lerp(1.4, 1.15, sk)], [0.48, 0.212, lerp(1.4, 1.15, sk)], { grade: 'sepia', vig: 0.3, border: lerp(14, 8, sk) });
      X.underline(ctx, m, BX.acum, 1, { width: lerp(5.5, 3, sk) });
      ctx.restore();
      // archival pages drop onto a stack (bottom-right), then everything slides off
      ctx.save();
      if (tp > 0) { ctx.translate(1600, 900); ctx.rotate(tp * 0.9); ctx.translate(-1600 + tp * 700, -900 + tp * tp * 300); }
      STACK.forEach((s, i) => {
        if (tt < s.at) return;
        const d = prog(tt, s.at, s.at + 0.4, E.in), bounce = Math.sin(prog(tt, s.at + 0.4, s.at + 0.65, E.lin) * Math.PI) * 10;
        const w = 360, h = 470, x = 1380 + s.dx, y = lerp(-560, 380 + s.dy, d) - bounce;
        X.printKB(ctx, img(s.k), 0, [x, y, w, h], [0.5, 0.4, 1.05], [0.5, 0.4, 1.05], { grade: 'sepia', vig: 0.25, border: 8, rot: s.rot + (1 - d) * 0.3 * (i % 2 ? 1 : -1) });
      });
      ctx.restore();
    },
  });
  STACK.forEach(s => cue(s.at + 0.35, 'paper_rustle', -16)); cue(t.tryW - 0.05, 'whoosh_soft', -14);

  // ================================================================== s018  Forster: every great southern tip looks alike
  const F12 = t.claimed - 0.1;
  base({
    t0: t.s018 - 0.07, t1: F12, draw(ctx, lt) {
      drawDesk(ctx, lt);
      X.printKB(ctx, img('forster'), lt / (F12 - t.s018), [620, 60, 680, 900], [0.5, 0.36, 1.45], [0.5, 0.34, 1.85], { grade: 'sepia', vig: 0.35 });
    },
  });
  const FX = { similar: [0.218, 0.288, 0.278, 0.022], flood: [0.236, 0.558, 0.493, 0.024] };
  base({
    t0: F12, t1: t.alike - 0.07, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const m = X.printKB(ctx, img('f12'), lt / 2.6, PAGE_R, [0.5, 0.3, 1.25], [0.47, 0.305, 1.42], { grade: 'sepia', vig: 0.3 });
      X.underline(ctx, m, FX.similar, prog(tt, t.claimed + 0.6, t.claimed + 1.3, E.inOut));
    },
  });
  over(t.claimed + 0.55, t.alike + 1.6, (ctx, tt) => pillT(ctx, '"A GREAT AND STRIKING SIMILARITY"', W / 2, 920, tt, t.claimed + 0.55, t.alike + 1.6, { size: 40 }));
  // real terrain: low over Cape Froward looking north up the Andes
  const WHIP = t.mtn - 0.12;
  G({
    t0: t.alike - 0.07, t1: WHIP, overlay: null, patch: { url: 'tex/patch/s_america_tip.jpg', bounds: [-82, -58, -56, -30] }, drift: 0.15,
    keys: [{ t: 0, lat: -53.6, lon: -71.4, alt: 0.27, tilt: 54, heading: -4 }, { t: WHIP - t.alike + 0.07, lat: -51.6, lon: -72.2, alt: 0.24, tilt: 58, heading: 2 }],
    look: { relief: 1.0, nightAmt: 0, desat: 0.08, exposure: 1.3 },
    x: (ctx, tt) => { const q = proj(...TIPS.froward); if (q.visible) F.dot(ctx, q.x, q.y, { r: 7, color: PAL.hero, ring: ((tt - t.alike) * 0.9) % 1 }); },
  });
  // whip to Kanyakumari, looking north up the Western Ghats
  G({
    t0: WHIP, t1: t.s019 - 0.07, overlay: null, patch: { url: 'tex/patch/s_india.jpg', bounds: [70, 4, 86, 18] }, drift: 0.15,
    keys: [{ t: 0, lat: 7.2, lon: 77.9, alt: 0.24, tilt: 55, heading: 8, ease: E.outExpo }, { t: 0.35, lat: 7.9, lon: 77.6, alt: 0.23, tilt: 56, heading: 0 }, { t: t.s019 - WHIP, lat: 8.8, lon: 77.3, alt: 0.21, tilt: 58, heading: -2 }],
    look: { relief: 1.0, nightAmt: 0, desat: 0.08, exposure: 1.3 },
    x: (ctx, tt, lt) => {
      const q = proj(...TIPS.kanya); if (q.visible) F.dot(ctx, q.x, q.y, { r: 7, color: PAL.hero, ring: ((tt - WHIP) * 0.9) % 1 });
      const wa = 1 - prog(lt, 0, 0.22, E.lin); if (wa > 0) X.smear(ctx, g.canvas, -160 * wa, 4, 0.2 * wa);
    },
  });
  cue(WHIP, 'whoosh_soft', -14);

  // ================================================================== s019  Forster's flood -> Explorer gag 2
  base({
    t0: t.s019 - 0.07, t1: G2, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const m = X.printKB(ctx, img('f12'), lt / 3, PAGE_R, [0.47, 0.56, 1.25], [0.48, 0.565, 1.42], { grade: 'sepia', vig: 0.3 });
      X.underline(ctx, m, FX.flood, prog(tt, t.expl + 0.05, t.expl + 0.85, E.inOut));
      pillT(ctx, 'FORSTER\'S CAUSE: "A VIOLENT FLOOD"', W / 2, 920, tt, t.expl + 0.1, G2 + 0.2, { size: 42 });
    },
  });
  // the wave: lip crosses the Explorer at "carved"
  const WROT = -0.42, WS = 1.05, LIP = [195, -270];
  const HIT = [1150, 520];
  const waveAt = (p) => { const d = (p - 0.6) * 2600; const lx = LIP[0] * WS, ly = LIP[1] * WS; const c = Math.cos(WROT), s = Math.sin(WROT);
    return [HIT[0] + d * c - (lx * c - ly * s), HIT[1] + d * s - (lx * s + ly * c)]; };
  const wp = (tt) => prog(tt, t.carved - 1.25, t.carved + 0.85, E.lin);
  const g2Hero = (tt) => {
    const be = lerp(-0.05, 0.2, prog(tt, G2 + 0.35, t.carved - 0.05, E.inOut)) - 0.05 * prog(tt, t.carved, t.carved + 0.35, E.out);
    hero.root.position.copy(onXY(be)); hero.root.quaternion.setFromEuler(new THREE.Euler(0, 0.0, -be, 'ZYX'));
    setWet(prog(tt, t.carved, t.carved + 0.25));
    planet.quaternion.copy(Q_G2);
    gst.key.position.set(3, 7, 6); if (rimL) rimL.position.set(-2.5, 4, -6);
  };
  const beadAt = (tt) => { // drips falling from the beard after the soaking
    if (tt < t.carved + 1.2 || !headBone) { bead.visible = false; return; }
    const ph = ((tt - t.carved - 1.2) % 1.6) / 1.6; const fall = Math.max(0, ph - 0.45) / 0.55;
    hero.update(tt); hero.root.updateMatrixWorld(true);
    const hp = new THREE.Vector3(); headBone.getWorldPosition(hp);
    bead.visible = true; bead.position.set(hp.x, hp.y - 0.11 - 0.9 * fall * fall, hp.z + 0.1); bead.scale.setScalar(0.4 + 0.6 * Math.min(1, ph / 0.45));
  };
  base({
    t0: G2, t1: G2c, draw(ctx, lt, tt) {
      gagBg(ctx, false); g2Hero(tt); beadAt(tt); drop.visible = false;
      gst.lookFrom([0.15 + lt * 0.03, 0.12, 4.7 - lt * 0.05], [0.35, 0.42, 0], 30);
      ctx.drawImage(gst.render(tt), 0, 0);
      const p = wp(tt);
      if (p > 0 && p < 1) { const [x, y] = waveAt(p); X.wave(ctx, x, y, WS, WROT, { spray: Math.sin(tt * 8) * 0.5 + 0.5 }); }
      // splash burst on impact
      const sp = prog(tt, t.carved - 0.02, t.carved + 0.5, E.out);
      if (sp > 0 && sp < 1) { ctx.save(); ctx.globalAlpha = 1 - sp; ctx.fillStyle = '#e8fbff'; for (let i = 0; i < 14; i++) { const a = -Math.PI * (0.1 + 0.8 * i / 13), d = 40 + sp * (160 + (i % 4) * 40); ctx.beginPath(); ctx.arc(HIT[0] + Math.cos(a) * d, HIT[1] + 40 + Math.sin(a) * d + sp * sp * 120, 9 - (i % 3) * 2, 0, Math.PI * 2); ctx.fill(); } ctx.restore(); }
    },
  });
  // close-up: soaked Explorer; the parked wave gets a wax seal ("bought it"), then deflates ("refund")
  base({
    t0: G2c, t1: G2e, draw(ctx, lt, tt) {
      gagBg(ctx, false); g2Hero(tt); beadAt(tt); drop.visible = false;
      gst.lookFrom([1.05 - lt * 0.03, 0.42, 2.75 - lt * 0.04], [0.5, 0.58, 0], 28);
      // parked wave (behind the Explorer)
      const df = prog(tt, t.refund - 0.05, t.refund + 0.4, E.out);
      const sy = Math.max(0.08, 1 - 0.92 * df + 0.08 * Math.sin(df * 18) * (1 - df));
      const wx = 1480 + 6 * Math.sin(tt * 1.3), wy = 520 + 8 * Math.sin(tt * 1.7) + df * 40;
      X.wave(ctx, wx, wy, 0.5, -0.06, { sy, alpha: 1 - prog(tt, G2e - 0.4, G2e) * 0.3 });
      X.waxSeal(ctx, wx - 150, wy - 200 * sy + 30, 56, prog(tt, t.bought - 0.04, t.bought + 0.18, E.lin));
      ctx.drawImage(gst.render(tt), 0, 0);
    },
  });
  cue(t.wave - 0.05, 'whoosh_big', -10); cue(t.carved - 0.03, 'splash_big', -10); cue(t.bought - 0.03, 'stamp', -18);

  // ================================================================== s020  Humboldt: "pyramidal"; the list
  base({
    t0: G2e, t1: t.pyr - 0.08, draw(ctx, lt) {
      drawDesk(ctx, lt);
      X.printKB(ctx, img('humboldt'), lt / (t.pyr - G2e), [600, 60, 720, 900], [0.5, 0.3, 1.25], [0.5, 0.28, 1.55], { grade: 'sepia', vig: 0.38 });
    },
  });
  const TRIS = [
    [[-36, -73.5], [-36, -56.5], [-54.5, -69]],
    [[-21, 14], [-21, 34.5], [-34.8, 20]],
    [[20.5, 70.5], [20.5, 86.5], [8.1, 77.5]],
  ].map(triLL);
  G({
    t0: t.pyr - 0.08, t1: t.list - 0.07, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.35,
    keys: [{ t: 0, lat: -26, lon: 12, alt: 2.95 }, { t: t.list - t.pyr, lat: -28, lon: 22, alt: 2.75, tilt: 6 }],
    look: { desat: 0.3, dim: 0.35, ovAlpha: 1 }, pre: () => coldSet([1, 1, 1]),
    x: (ctx, tt) => {
      TRIS.forEach((tr, i) => {
        const a = t.pyr - 0.06 + i * 0.3; if (tt < a) return;
        const fl = 1 - prog(tt, a, a + 0.35);
        strokeProjected(ctx, g, tr, { color: '#ffffff', width: 2.6 + 4 * fl, glow: true });
      });
      pillT(ctx, 'HUMBOLDT: "PYRAMIDAL"', W / 2, 110, tt, t.pyr - 0.08, t.list - 0.1, { size: 46 });
    },
  });
  [0, 0.3, 0.6].forEach(d => cue(t.pyr - 0.06 + d, 'pop_ui', -16));
  const GUY = [[0.50, 0.588, 0.43, 0.026], [0.26, 0.640, 0.485, 0.026], [0.125, 0.666, 0.565, 0.026]];
  base({
    t0: t.list - 0.07, t1: t.l1 - 0.07, draw(ctx, lt, tt) {
      drawDesk(ctx, lt);
      const m = X.printKB(ctx, img('guyot'), lt / 2, [230, 150, 1460, 700], [0.53, 0.642, 1.12], [0.53, 0.648, 1.22], { grade: 'sepia', vig: 0.3 });
      GUY.forEach((b, i) => X.underline(ctx, m, b, prog(tt, t.list + 0.05 + i * 0.45, t.list + 0.5 + i * 0.45, E.inOut)));
    },
  });
  cue(t.list, 'paper_rustle', -16);

  // ================================================================== s021  match-cut to the s003 framing: the same list, 170 years apart
  const pop021 = { grl: t.l1, baja: t.l2, fla: t.l3, in: t.l4, kam: t.l5 };
  const QUOTE = '"ALL THEIR POINTS TURNED TOWARDS THE SOUTH"';
  eeTipsShot(t.l1 - 0.07, t.s022 - 0.1, pop021, {
    lastPillEnd: t.quote21 - 0.1,
    extra: (ctx, tt, lt, k) => {
      if (tt > t.l4 - 0.08 && tt < t.quote21) { // India: pill too (it is on the list)
        const [px, py] = k.pt(...EETIP.kanya); F.pill(ctx, 'INDIA', px + 140, py + 40, { anchor: 'left', leader: [px, py], size: 38, alpha: env(tt, t.l4 - 0.08, t.l5 - 0.1, 0.12, 0.18), ring: ((tt - t.l4) * 0.9) % 1 });
      }
      if (tt > t.quote21 - 0.1) {
        const n = Math.floor(prog(tt, t.quote21 - 0.1, t.quote21 + 1.5, E.lin) * QUOTE.length);
        const a = 1 - prog(tt, t.s022 - 0.4, t.s022 - 0.1);
        ctx.save(); ctx.globalAlpha = a * 0.82; ctx.fillStyle = '#0a0d14'; F.round(ctx, 210, 60, 1500, 104, 20); ctx.fill(); ctx.restore();
        F.text(ctx, QUOTE.slice(0, n), 960 - F.measure(ctx, QUOTE, { size: 64, fam: F.FAM.head, weight: 400, tracking: 0.03 }) / 2, 136, { size: 64, fam: F.FAM.head, weight: 400, tracking: 0.03, color: '#ffffff', alpha: a });
        if (n < QUOTE.length && Math.floor(tt * 4) % 2 === 0) { const w = F.measure(ctx, QUOTE.slice(0, n), { size: 64, fam: F.FAM.head, weight: 400, tracking: 0.03 }); ctx.fillStyle = PAL.hero; ctx.fillRect(960 - F.measure(ctx, QUOTE, { size: 64, fam: F.FAM.head, weight: 400, tracking: 0.03 }) / 2 + w + 6, 86, 5, 56); }
      }
    },
  });
  for (const k of ['l1', 'l2', 'l3', 'l4', 'l5']) cue(t[k] - 0.07, 'pop_ui', -14);
  cue(t.quote21 - 0.05, 'typewriter', -18);

  // ================================================================== s022–s023  1973 "continental drip" joke; 1976 version; the byline
  const SHEET_A = X.paperCanvas(860, 1100, 11), SHEET_B = X.paperCanvas(900, 1120, 12, { coffee: [[700, 860, 120], [140, 210, 70]] }), SHEET_C = X.paperCanvas(860, 1100, 13);
  // small world-map card for the magnifier
  const CARD = mk(720, 352);
  { const cg = CARD.getContext('2d'); cg.fillStyle = '#e8dcc0'; cg.fillRect(0, 0, 720, 352); cg.drawImage(EEB, 0, 0, EE_W, EE_H, 0, 0, 720, 352);
    cg.save(); cg.scale(720 / EE_W, 352 / EE_H); cg.fillStyle = PAL.hero; cg.globalAlpha = 0.85; for (const k of ['sa', 'af', 'in', 'grl', 'fla', 'baja', 'kam']) cg.fill(EP[k], 'evenodd'); cg.restore();
    cg.globalCompositeOperation = 'color'; cg.fillStyle = 'rgba(160,120,70,0.35)'; cg.fillRect(0, 0, 720, 352); }
  // Gondwana watermark (200 Ma reconstructed coastlines, Equal Earth)
  const coast200 = await api.loadJSON('paleo/coast_200.json');
  const GOND = mk(900, 440);
  { const gg = GOND.getContext('2d'); gg.scale(900 / EE_W, 440 / EE_H); gg.fillStyle = 'rgba(90,60,30,1)'; gg.beginPath();
    for (const r of coast200) { r.forEach(([lo, la], i) => { const [x, y] = ee(lo, la); i ? gg.lineTo(x, y) : gg.moveTo(x, y); }); gg.closePath(); } gg.fill('nonzero'); }
  const HEAD = 'CONTINENTAL DRIFT', HF = { size: 70, fam: F.FAM.mono, weight: 500, color: '#2a2420', shadow: false };
  // virtual camera with hard "cuts" between framings: [tStart, cx, cy, scale0, scale1]
  const CAMS = [[t.s022 - 0.1, 960, 560, 0.92, 0.97], [t.joke - 0.06, 1010, 470, 1.18, 1.25], [t.contl - 0.25, 980, 430, 1.32, 1.4], [t.staring - 0.6, 1030, 760, 1.25, 1.33],
    [t.s023 - 0.07, 960, 560, 0.88, 0.93], [t.version - 0.07, 1060, 560, 0.86, 0.9], [t.hold - 0.07, 1290, 300, 1.25, 1.75]];
  const typeCam = (tt) => { let i = 0; while (i + 1 < CAMS.length && tt >= CAMS[i + 1][0]) i++; const c = CAMS[i], e = i + 1 < CAMS.length ? CAMS[i + 1][0] : END; const k = prog(tt, c[0], e, E.inOutSine); return { cx: c[1], cy: c[2], s: lerp(c[3], c[4], k) }; };
  const sheet = (ctx, cv, x, y, w, rot, alpha = 1) => {
    const h = w * cv.height / cv.width;
    ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot);
    for (let i = 4; i >= 1; i--) { ctx.fillStyle = 'rgba(0,0,0,0.12)'; ctx.fillRect(-w / 2 - i * 4, -h / 2 - i * 2 + 12, w + i * 8, h + i * 8); }
    ctx.drawImage(cv, -w / 2, -h / 2, w, h); ctx.restore();
    return { x, y, w, h, rot };
  };
  const local = (ctx, sh, fn) => { ctx.save(); ctx.translate(sh.x, sh.y); ctx.rotate(sh.rot); ctx.translate(-sh.w / 2, -sh.h / 2); fn(); ctx.restore(); };
  base({
    t0: t.s022 - 0.1, t1: t.s024 - 0.07, draw(ctx, lt, tt) {
      const cam = typeCam(tt);
      drawDesk(ctx, lt);
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(cam.s, cam.s); ctx.translate(-cam.cx, -cam.cy);
      const slideA = prog(tt, t.s022 - 0.1, t.s022 + 0.45, E.outExpo);
      const shiftA = prog(tt, t.version - 0.07, t.version + 0.5, E.inOut);
      // sheet C (1976) slides in behind
      const cIn = prog(tt, t.version - 0.07, t.version + 0.5, E.outExpo);
      if (cIn > 0) {
        const sc = sheet(ctx, SHEET_C, lerp(2500, 1280, cIn), 560, 760, 0.035);
        local(ctx, sc, () => {
          X.inkLines(ctx, 70, 260, 620, 16, 34, prog(tt, t.version + 0.1, t.version + 2.5, E.lin), 41);
          F.text(ctx, 'THE DRIP, REVISITED', 70, 150, { size: 46, fam: F.FAM.mono, weight: 700, color: '#2a2420', shadow: false, alpha: prog(tt, t.version + 0.1, t.version + 0.4) });
          // blurred byline
          ctx.save(); ctx.globalAlpha = prog(tt, t.version + 0.2, t.version + 0.5); for (let i = 0; i < 5; i++) { ctx.fillStyle = `rgba(55,45,35,${0.16})`; F.round(ctx, 70 + i * 3, 190 - i * 2 + (i % 2) * 4, 300 - i * 6, 22, 11); ctx.fill(); } ctx.restore();
          // Gondwana watermark flicker
          const fk = tt > t.think - 0.05 && tt < t.think + 0.5 ? [0.0, 0.35, 0.08, 0.42, 0.12, 0.3, 0.05][Math.floor((tt - t.think + 0.05) / 0.08) % 7] : 0;
          if (fk > 0) { ctx.save(); ctx.globalAlpha = fk; ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(GOND, -20, 380, 800, 391); ctx.restore(); }
        });
        if (tt > t.hold - 0.08) { // yellow ring around the blurred byline
          const p = prog(tt, t.hold - 0.08, t.hold + 0.5, E.inOut);
          local(ctx, sc, () => {
            ctx.save(); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.beginPath(); ctx.ellipse(220, 200, 200, 52, -0.04, -Math.PI * 0.9, -Math.PI * 0.9 + Math.PI * 2.1 * p); ctx.stroke(); ctx.restore();
          });
        }
        pillT(ctx, '1976', 1500, 210, tt, t.version + 0.1, t.s024 - 0.2, { size: 52 });
      }
      // sheet A (magazine page)
      const sa = sheet(ctx, SHEET_A, lerp(960, 760, shiftA), lerp(1500, 560, slideA), 760, -0.02);
      local(ctx, sa, () => {
        X.inkLines(ctx, 70, 280, 620, 18, 36, prog(tt, t.s022, t.s022 + 3.2, E.lin), 17);
        ctx.fillStyle = 'rgba(45,38,30,0.75)'; ctx.fillRect(70, 120, 420, 24); ctx.fillRect(70, 160, 300, 16);
      });
      // sheet B (coffee-stained) slides over at "joke": the headline gets retyped
      const bIn = prog(tt, t.joke - 0.06, t.joke + 0.4, E.outExpo);
      if (bIn > 0) {
        const sb = sheet(ctx, SHEET_B, lerp(-700, lerp(1000, 820, shiftA), bIn), lerp(520, 540, shiftA), 800, lerp(-0.15, 0.03, bIn));
        local(ctx, sb, () => {
          const n = Math.floor(prog(tt, t.contl - 0.05, t.drip - 0.12, E.lin) * HEAD.length);
          F.text(ctx, HEAD.slice(0, n), 60, 260, HF);
          const charW = F.measure(ctx, 'M', { size: 70, fam: F.FAM.mono, weight: 500 });
          if (tt > t.drip - 0.06) { // strike "FT", overtype "P"
            const sp = prog(tt, t.drip - 0.06, t.drip + 0.15, E.lin);
            const x0 = 60 + charW * 15 - 4, x1 = x0 + charW * 2 * sp + 8;
            ctx.fillStyle = '#c4281c'; ctx.fillRect(x0, 236, x1 - x0, 7); ctx.fillRect(x0, 222, x1 - x0, 5);
            if (tt > t.drip + 0.2) F.text(ctx, 'P', 60 + charW * 15 + charW * 0.5, 186, { size: 84, fam: F.FAM.mono, weight: 700, color: '#c4281c', shadow: false });
          }
          if (n > 0 && n < HEAD.length && Math.floor(tt * 6) % 2 === 0) { ctx.fillStyle = '#2a2420'; ctx.fillRect(60 + charW * n + 4, 210, 6, 60); }
          X.inkLines(ctx, 60, 340, 640, 7, 34, prog(tt, t.drip + 0.3, t.staring - 0.3, E.lin), 23);
          // world-map card + magnifier ("staring at a map")
          const cy0 = 640, cw = 560, ch = cw * 352 / 720;
          ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(116, cy0 + 8, cw + 8, ch + 8); ctx.restore();
          ctx.drawImage(CARD, 110, cy0, cw, ch); ctx.strokeStyle = 'rgba(60,40,20,0.5)'; ctx.lineWidth = 2; ctx.strokeRect(110, cy0, cw, ch);
          if (tt > t.staring - 0.5 && tt < t.s023 + 0.5) {
            const mp = prog(tt, t.staring - 0.4, t.staring + 1.2, E.inOut);
            const mx = lerp(120, 640, mp), my = cy0 + ch * 0.62 + Math.sin(mp * Math.PI * 2) * 40;
            X.magnifier(ctx, CARD, mx, my, 92, 2.2, [110, cy0, cw, ch]);
          }
        });
      }
      ctx.restore();
      pillT(ctx, '1973', 1700, 110, tt, t.seventies - 0.08, t.s023 - 0.1, { size: 52 });
    },
  });
  cue(t.s022 + 0.05, 'typewriter', -12); cue(t.contl - 0.05, 'typewriter', -12); cue(t.drip + 0.15, 'bell_small', -16);
  cue(t.version, 'typewriter', -16); cue(t.joke - 0.05, 'paper_rustle', -16);

  // ================================================================== s024  first clue; the far side (cutaway, North Pole on top)
  G({
    t0: t.s024 - 0.07, t1: t.far - 0.07, overlay: { canvas: COLD.cv, bounds: WB }, drift: 0.6,
    keys: [{ t: 0, lat: 6, lon: -14, alt: 3.3 }, { t: t.far - t.s024, lat: 0, lon: 6, alt: 2.35, tilt: 6 }],
    look: { desat: 0.3, dim: 0.32, ovAlpha: 1 }, pre: () => coldSet([1, 1, 1]),
    x: (ctx, tt) => {
      const a = env(tt, t.first - 0.1, t.first + 1.2, 0.08, 0.4);
      if (a > 0) SEVEN.forEach((k, i) => { const q = proj(...TIPS[k]); if (!q.visible) return; dripArrow(ctx, q.x, q.y + 6, prog(tt, t.first - 0.1 + i * 0.05, t.first + 0.3 + i * 0.05, E.lin), { len: 70, color: PAL.yellow, width: 5, head: 10, alpha: a }); });
      poleRing(ctx, tt, { r: 38 });
    },
  });
  cutShot(t.far - 0.07, END, {
    top: [90, 0], spin: 0.12, drill0: t.far + 0.05, drillD: 1.4,
    cam: (k) => [[lerp(8.0, 6.2, k), lerp(4.4, 3.4, k), lerp(8.0, 6.2, k)], [0, lerp(-0.2, 0.2, k), 0], 32],
  });
  cue(END - 4, 'riser_tension', -12); cue(t.far, 'sonar_ping', -12);

  // ------------------------------------------------------------------ coverage check (base layer must cover [t0, t1))
  const bs = S.filter(s => (s.layer || 0) === 0).sort((a, b) => a.t0 - b.t0);
  let cur = C.t0; for (const s of bs) { if (s.t0 > cur + 1e-3) api.log(`ch1 GAP ${cur.toFixed(3)}..${s.t0.toFixed(3)}`); cur = Math.max(cur, s.t1); }
  if (cur < C.t1 - 1e-3) api.log(`ch1 GAP at end ${cur.toFixed(3)}..${C.t1}`);
  for (const s of S) s.id = s.id || 'ch1';
  return S;
}
