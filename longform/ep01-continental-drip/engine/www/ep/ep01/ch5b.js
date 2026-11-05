// Chapter 5b (s082-s096): Holden's teardrop joke, the south-up Blue Marble, Pangooy, the real drip under Nevada,
// the honest part (tiles + needles), Baja / Florida / Agulhas, the verdict, and "a snapshot".
import * as F from '../../lib/fx.js';
import { globeShot } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, makeCanvas, fillEquirect, strokeProjected, fillProjected, gcLine, projectPath, moveRings } from '../../lib/geo.js';
import { region, allRings } from '../../lib/beats.js';
import * as U from './ch5b_util.js';
const { PAL, prog, env, clamp, lerp, E } = F;
const D2R = Math.PI / 180;

export async function build(api, C) {
  const W = api.W, H = api.H;
  await api.globe();
  await Promise.all(['500 40px "JetBrains Mono"', '700 40px "JetBrains Mono"', '800 40px "Barlow Condensed"', '700 40px "Barlow Condensed"', '400 100px "Bebas Neue"', '800 60px "Inter"'].map(f => document.fonts.load(f)));
  const IMG = p => 'ep/ep01/img/' + p;
  await api.loadImages([IMG('bluemarble_original.jpg'), IMG('bluemarble_northup.jpg'), IMG('cape_agulhas_aster.jpg'), 'tex/equal_earth.jpg', 'tex/day_8k.jpg', 'tex/data/land_north.png', 'tex/data/antipodes.png']);
  const tracks = await api.loadJSON('paleo/tracks.json');
  const coast200 = await api.loadJSON('paleo/coast_200.json');
  const C50 = await loadGeo('ne_50m_admin_0_countries');
  const LAND = await loadGeo('ne_50m_land');
  const TIPS = await loadGeo('tips_admin1');
  const MAR = await loadGeo('ne_10m_geography_marine_polys');

  // ---------- markers (verified against their segment; s092 'going' collides with s097 -> word lookup) ----------
  const mk = (name, segId, word) => {
    const s = C.seg(segId); let t = null; try { t = C.T(name); } catch (e) { t = null; }
    if (t == null || t < s.start - 0.05 || t > s.end + 0.05) {
      const w = C.words(segId).find(w => w.w.toLowerCase().replace(/[^a-z]/g, '').startsWith(word || name));
      t = w ? w.start : s.start;
    }
    return t;
  };
  const M = {
    holden: mk('holden', 's082'), tear: mk('tear', 's083', 'teardrop'), down: mk('down', 's084'), upside: mk('upside', 's084'), joking: mk('joking', 's084'),
    photo: mk('photo', 's084', 'photos'), bm: mk('bm', 's084', 'antarctica'), flip: mk('flip', 's084', 'flipped'), first: mk('first', 's085'),
    splash: mk('splash', 's086'), pangooy: mk('pangooy', 's086'), tue: mk('tue', 's086', 'tuesday'), tz: mk('tz', 's086', 'time'),
    twist: mk('twist', 's087', 'heres'), earlier: mk('earlier', 's087'), real: mk('real', 's087'), apart2: mk('apart2', 's087', 'apart'),
    cited: mk('cited', 's088'), pointline: mk('pointline', 's088', 'point'), punch: mk('punch', 's088', 'punchline'), answer: mk('answer', 's088'),
    notdone: mk('notdone', 's089', 'done'), realdrip: mk('realdrip', 's089', 'real'), nev: mk('nev', 's089', 'nevada'), honey: mk('honey', 's089'), anti: mk('anti', 's089', 'antidrip'),
    honest: mk('honest', 's090', 'part'), drips: mk('drips', 's090'),
    york: mk('york', 's091', 'cape'), yuc: mk('yuc', 's091', 'yucat'), jut: mk('jut', 's091', 'jutland'), tay: mk('tay', 's091', 'taymyr'), antpen: mk('antpen', 's091', 'peninsula'), north: mk('north', 's091', 'north'),
    stories: mk('stories', 's092'), baja: mk('baja', 's092'), mex: mk('mex', 's092', 'mexico'), going: mk('going_s092', 's092', 'going'),
    fla: mk('fla', 's093', 'florida'), lime: mk('lime', 's093', 'limestone'), sealife: mk('sealife', 's093', 'sea'), under: mk('under', 's093'), wafr: mk('wafr', 's093', 'west'), else: mk('else', 's093'),
    gh: mk('gh', 's094', 'hope'), agul: mk('agul', 's094', 'agulhas'), needles: mk('needles', 's094'), compass: mk('compass', 's094'), north2: mk('north2', 's094', 'north'),
    coin2: mk('coin2', 's095', 'coincidence'), likely: mk('likely', 's095'), v_ant: mk('v_ant', 's095', 'antarctica'), single: mk('single', 's095', 'answer'), dots: mk('dots', 's095'),
    lopside: mk('lopside', 's096', 'lopsided'), northl: mk('northl', 's096', 'north'), avoid2: mk('avoid2', 's096', 'land'), force: mk('force', 's096'), snap: mk('snap', 's096', 'snapshot'),
  };
  // s091 'north' is the LAST "north" word of the segment; make sure the word fallback (if ever used) does not pick "points north"
  if (M.north < C.seg('s091').start + 5) M.north = C.words('s091').filter(w => /north/i.test(w.w)).pop().start;
  if (M.north2 < C.seg('s094').start + 5) M.north2 = C.words('s094').filter(w => /north/i.test(w.w)).pop().start;
  const SEG = id => C.seg(id);
  const t0 = C.t0, t1 = C.t1;

  // ---------- shared builders ----------
  const BASE_LOOK = { flatBase: 0, ovMul: 0, ambient: 0.10, specAmt: 0.5, rimAmt: 0.35 };
  const gshot = (o) => {
    const look = o.look, ex = o.extra, st0 = o.t0;
    return globeShot(Object.assign({}, o, {
      look: (lt) => Object.assign({}, BASE_LOOK, typeof look === 'function' ? look(lt + st0) : (look || {})),
      pre: async (lt, api) => { api.g.u.tint.value.set(1, 1, 1); },
      keys: o.keys.map(k => Object.assign({}, k, { t: k.t - st0 })),
      extra: ex ? (ctx, lt, api, cam) => ex(ctx, lt + st0, api, cam) : undefined,
    }));
  };
  const scene = (a, b, draw, o = {}) => ({ t0: a, t1: b, layer: o.layer || 0, fadeIn: o.fadeIn || 0, fadeOut: o.fadeOut || 0, draw: (ctx, lt, t, api) => draw(ctx, t, api) });
  const pillAt = (ctx, s, x, y, t, a0, a1, o = {}) => {
    if (t < a0 - 0.02 || (a1 != null && t > a1)) return;
    const a = a1 != null ? env(t, a0, a1, 0.22, 0.3) : prog(t, a0, a0 + 0.22); if (a <= 0) return;
    const pop = lerp(0.82, 1, E.outBack(prog(t, a0, a0 + 0.32)));
    ctx.save(); ctx.translate(x, y); ctx.scale(pop, pop); F.pill(ctx, s, 0, 0, Object.assign({ anchor: 'left', size: 40, alpha: a }, o)); ctx.restore();
  };
  const cue = (t, n, db) => api.cue(t, n, db);

  // ---------- Equal Earth assets ----------
  const EEC = U.cv(2700, 1320); { const g = EEC.getContext('2d'); g.filter = 'saturate(0.72) brightness(0.88) contrast(1.05)'; g.drawImage(api.img('tex/equal_earth.jpg'), 0, 0, 2700, 1320); }
  const landRings = LAND.features.flatMap(f => rings(f));
  const coastPath = U.eePath(landRings.map(r => r.filter((p, i) => i % 2 === 0 || i === r.length - 1)), { skipPole: true });
  const drawEE = (ctx, view, dim = 0) => { const T = U.eeT(view); ctx.drawImage(EEC, T.ox, T.oy, U.EE_W * T.z, U.EE_H * T.z); if (dim) { ctx.fillStyle = `rgba(3,6,13,${dim})`; ctx.fillRect(-W, -H, 3 * W, 3 * H); } return T; };
  const strokeCoast = (ctx, T, a, col = '#ffffff', w = 1.6) => { if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.translate(T.ox, T.oy); ctx.scale(T.z, T.z); ctx.strokeStyle = col; ctx.lineWidth = w / T.z; ctx.lineJoin = 'round'; ctx.stroke(coastPath); ctx.restore(); };
  // continents as teardrops (area-true, centred on centroid, point aimed south)
  const CONTS = [
    { k: 'nam', lat: 47, lon: -101, A: 24.2 }, { k: 'sam', lat: -16, lon: -60, A: 17.8 }, { k: 'eur', lat: 53, lon: 23, A: 10.0 },
    { k: 'afr', lat: 6, lon: 20, A: 30.3 }, { k: 'asia', lat: 45, lon: 93, A: 44.6 }, { k: 'aus', lat: -25, lon: 134, A: 8.5 },
  ];
  for (const c of CONTS) { [c.x, c.y] = U.ee(c.lon, c.lat); c.s = U.eeScaleForArea(c.A); }
  const meanX = CONTS.reduce((a, c) => a + c.x, 0) / CONTS.length, meanY = CONTS.reduce((a, c) => a + c.y, 0) / CONTS.length;
  // draw all drops on an EE view; o: {a (alpha), outline p fn, wob, pos override fn}
  const drawDrops = (ctx, T, t, o = {}) => {
    const shapes = CONTS.map((c, i) => {
      const pos = o.pos ? o.pos(c, i) : [c.x, c.y];
      const x = T.ox + pos[0] * T.z, y = T.oy + pos[1] * T.z;
      const pop = o.pop ? o.pop(i) : 1;
      return U.dropPts(x, y, c.s * T.z * pop, o.rot || 0, o.wob || 0, t, i * 1.7);
    });
    if (o.union) { // merged blob: white rim under, solid fill over
      ctx.save(); ctx.globalAlpha *= o.union; ctx.lineJoin = 'round';
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 9; for (const s of shapes) { ctx.beginPath(); U.polyPath(ctx, s); ctx.stroke(); }
      ctx.fillStyle = PAL.hero; for (const s of shapes) { ctx.beginPath(); U.polyPath(ctx, s); ctx.fill(); }
      // soft highlight
      ctx.fillStyle = 'rgba(255,200,170,0.18)'; for (const s of shapes) { ctx.beginPath(); U.polyPath(ctx, s.map(([x, y]) => [x - 6, y - 8])); ctx.fill(); }
      ctx.restore();
    }
    const ia = o.indiv ?? 1;
    if (ia > 0) shapes.forEach((s, i) => {
      const a = (o.alpha ? o.alpha(i) : 1) * ia; if (a <= 0) return;
      ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = 'rgba(255,90,54,0.55)'; ctx.beginPath(); U.polyPath(ctx, s); ctx.fill(); ctx.restore();
      const p = o.outline ? o.outline(i) : 1; ctx.save(); ctx.globalAlpha *= ia; U.strokeOn(ctx, s, p, { width: 3 }); ctx.restore();
    });
    return shapes;
  };

  // ---------- globe overlays ----------
  const WORLD = [-180, -90, 180, 90];
  const dripOv = makeCanvas(2048, 1024);
  fillEquirect(dripOv, WORLD, [...await region('south america'), ...await region('africa'), findFeature(C50, 'India')], { color: PAL.hero, alpha: 0.85, glow: 24 });
  const dropsOv = makeCanvas(2048, 1024);
  const DROPS_LL = [U.dropLL(-53.9, -71.3, 14.0, 8), U.dropLL(-34.83, 20.0, 24.0, 0), U.dropLL(8.08, 77.55, 3.2, 0)];
  U.paintRings(dropsOv, WORLD, DROPS_LL, { color: PAL.hero, alpha: 0.62, stroke: '#ffffff', width: 3.5 });
  const antOv = makeCanvas(2048, 1024);
  { const ant = findFeature(C50, 'Antarctica'); fillEquirect(antOv, WORLD, [ant], { color: PAL.hero, alpha: 0.3, glow: 0 });
    const g = antOv.getContext('2d'); g.save(); const X = lo => (lo + 180) / 360 * 2048, Y = la => (90 - la) / 180 * 1024;
    g.beginPath(); g.rect(X(-76), Y(-62), X(-54) - X(-76), Y(-75) - Y(-62)); g.clip(); fillEquirect(antOv, WORLD, [ant], { color: PAL.hero, alpha: 0.9, glow: 0 }); g.restore(); }
  const GULF_B = [-116, 20, -104, 33], gulfOv = makeCanvas(1024, 1024);
  { const gf = MAR.features.find(f => f.properties.name === 'Golfo de California'); if (gf) fillEquirect(gulfOv, GULF_B, [gf], { color: PAL.cyan, alpha: 0.85, glow: 16 }); }
  const FL_B = [-88, 24, -79, 31.5], flOv = makeCanvas(1024, 1024);
  const flFeat = TIPS.features.filter(f => f.properties.name === 'Florida' && f.properties.admin !== 'Uruguay');
  fillEquirect(flOv, FL_B, flFeat, { color: PAL.hero, alpha: 0.85, glow: 12 });
  const flRings = allRings(flFeat);
  const northOv = makeCanvas(2048, 1024); northOv.getContext('2d').drawImage(api.img('tex/data/land_north.png'), 0, 0, 2048, 1024);
  const bajaFeat = TIPS.features.filter(f => /Baja California/.test(f.properties.name));
  const bajaR0 = allRings(bajaFeat);
  const BAJA_P = [26.5, -112.5], BAJA_Q = U.dest(26.5, -112.5, 274, 125);
  const bajaStart = moveRings(bajaR0, BAJA_P, BAJA_Q, 1);

  // ---------- antipode map in Equal Earth (forward splat of the equirect data overlay) ----------
  const antiEE = U.cv(1800, 880);
  { const src = U.cv(1024, 512), sg = src.getContext('2d'); sg.drawImage(api.img('tex/data/antipodes.png'), 0, 0, 1024, 512);
    const sd = sg.getImageData(0, 0, 1024, 512).data, dg = antiEE.getContext('2d'), out = dg.createImageData(1800, 880), od = out.data;
    for (let y = 0; y < 512; y++) { const lat = 90 - (y + 0.5) / 512 * 180; for (let x = 0; x < 1024; x++) { const i = (y * 1024 + x) * 4; if (sd[i + 3] < 20) continue; const lon = -180 + (x + 0.5) / 1024 * 360; const [ex, ey] = U.ee(lon, lat); const px = Math.round(ex / 2), py = Math.round(ey / 2);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const qx = px + dx, qy = py + dy; if (qx < 0 || qy < 0 || qx >= 1800 || qy >= 880) continue; const j = (qy * 1800 + qx) * 4; od[j] = sd[i]; od[j + 1] = sd[i + 1]; od[j + 2] = sd[i + 2]; od[j + 3] = Math.max(od[j + 3], sd[i + 3]); } } }
    dg.putImageData(out, 0, 0); }

  const scenes = [];
  // ===================================================================================================
  // A  s082  1976 typewriter sheet, blurred byline -> JOHN C. HOLDEN
  // ===================================================================================================
  const P76 = U.paper(820, 1060, 76);
  { const g = P76.g; g.save(); g.translate(P76.pad, P76.pad);
    U.greek(g, 230, 128, 360, 1, 30, 11, { h: 16, alpha: 0.75 });
    U.greek(g, 290, 168, 240, 1, 30, 12, { h: 12, alpha: 0.6 });
    // figure: our own doodle of the "teardrop world"
    g.strokeStyle = 'rgba(42,36,32,0.65)'; g.lineWidth = 2; g.strokeRect(110, 300, 600, 300);
    g.beginPath(); g.ellipse(410, 450, 270, 130, 0, 0, 7); g.stroke();
    for (const [x, y, s] of [[300, 405, 70], [340, 500, 48], [440, 410, 40], [455, 488, 62], [560, 420, 80], [585, 510, 34]]) { const d = U.dropPts(x, y, s); g.beginPath(); U.polyPath(g, d); g.stroke(); }
    U.greek(g, 230, 640, 360, 1, 28, 13, { h: 8, alpha: 0.45 });
    U.greek(g, 110, 710, 600, 9, 34, 14, { h: 9, alpha: 0.5, indent: true });
    g.restore(); }
  const BYL = U.cv(620, 90), BYLb = U.cv(620, 90);
  U.typeStr(BYL.getContext('2d'), 'JOHN C. HOLDEN', 18, 62, 50, 99);
  { const g = BYLb.getContext('2d'); g.filter = 'blur(8px)'; g.drawImage(BYL, 0, 0); g.filter = 'blur(3px)'; g.globalAlpha = 0.5; g.drawImage(BYL, 0, 0); }
  const A_end = SEG('s083').start + 1.0;
  scenes.push(scene(t0, A_end, (ctx, t) => {
    U.deskBg(ctx, t);
    const inP = prog(t, t0, t0 + 0.6, E.outExpo), outP = prog(t, A_end - 0.85, A_end, E.in);
    const sc0 = lerp(0.86, 0.94, prog(t, t0, M.holden - 0.25, E.inOut)), push = prog(t, M.holden - 0.25, M.holden + 0.6, E.outExpo);
    const sc = lerp(sc0, 1.28, push) * lerp(1, 0.7, outP);
    const bylY0 = 230 - 530; // byline y relative to sheet centre (sheet units)
    const by = lerp(560 + bylY0 * sc0, 430, push);
    const y = by - bylY0 * sc;
    const x = lerp(1560, 960, inP) + lerp(0, -1500, outP);
    const rot = lerp(0.1, -0.018, inP) + lerp(0, -0.25, outP) + 0.004 * Math.sin(t * 0.8);
    U.drawPaper(ctx, P76, x, y, rot, sc, 1, (g) => {
      const sharp = prog(t, M.holden - 0.14, M.holden + 0.2);
      g.drawImage(BYLb, 100, 230 - 60); if (sharp > 0) { g.save(); g.globalAlpha *= sharp; g.drawImage(BYL, 100, 230 - 60); g.restore(); }
      // yellow ring circling the blurred byline (callback), draws on then fades once it is readable
      const rp = prog(t, SEG('s082').start + 2.05, SEG('s082').start + 2.75, E.inOut), ra = 1 - prog(t, M.holden + 0.5, M.holden + 0.9);
      if (rp > 0 && ra > 0) { g.save(); g.globalAlpha *= ra; g.strokeStyle = PAL.yellow; g.lineWidth = 7; g.lineCap = 'round'; g.beginPath(); g.ellipse(410, 220, 330, 62, -0.03, -2.2, -2.2 + Math.PI * 2.15 * rp); g.stroke(); g.restore(); }
    });
    pillAt(ctx, '1976', 150, 150, t, t0 + 0.55, A_end - 0.5, { size: 46 });
  }));
  cue(t0 + 0.02, 'paper_rustle', -16); cue(t0 + 0.45, 'typewriter', -14);

  // ===================================================================================================
  // B1 s083  Equal Earth map: every continent a teardrop
  // ===================================================================================================
  const B1a = A_end - 0.4, B1b = SEG('s084').start - 0.1;
  scenes.push(scene(B1a, B1b, (ctx, t) => {
    ctx.fillStyle = '#04060b'; ctx.fillRect(0, 0, W, H); U.spaceBg(ctx, t, { starAlpha: 0.5 });
    const k = prog(t, B1a, B1b, E.inOut);
    const T = drawEE(ctx, { cx: lerp(1800, 1840, k), cy: lerp(880, 840, k), zoom: lerp(1.0, 1.1, k) }, lerp(0.22, 0.5, prog(t, M.tear - 0.5, M.tear + 0.3)));
    strokeCoast(ctx, T, 0.55 * prog(t, B1a + 0.9, B1a + 1.8) * (1 - 0.7 * prog(t, M.tear, M.tear + 0.5)));
    const ta = M.tear - 0.1;
    const shapes = drawDrops(ctx, T, t, {
      alpha: i => prog(t, ta + i * 0.07, ta + i * 0.07 + 0.35), pop: i => lerp(1.18, 1, E.outBack(prog(t, ta + i * 0.07, ta + i * 0.07 + 0.4))),
      outline: i => prog(t, ta + i * 0.07, ta + i * 0.07 + 0.6, E.inOut), wob: 0.012,
    });
    // "the pointed end showing the direction it came from": arrows out of each tip
    const td = C.words('s083').find(w => /direction/.test(w.w)).start - 0.1;
    shapes.forEach((s, i) => { const p = prog(t, td + i * 0.05, td + i * 0.05 + 0.45, E.outBack); if (p <= 0) return; const tip = s[U.DROP.tipIdx]; const L = 24 + 46 * p + 6 * Math.sin(t * 6 + i);
      U.arrow(ctx, tip[0], tip[1] + 8, tip[0], tip[1] + 8 + L, { color: PAL.yellow, width: 5, head: 12, alpha: clamp(p) }); });
    pillAt(ctx, '"TEAR-DROP SHAPED"', 110, 100, t, M.tear - 0.1, B1b);
  }, { fadeIn: 0.4 }));
  cue(M.tear - 0.05, 'shimmer', -18);

  // ===================================================================================================
  // B2 s084  drips flow down -> the map flips -> JOKE tag
  // ===================================================================================================
  const B2a = B1b, B2b = M.photo - 0.08;
  const tagC = U.cv(300, 150); { const g = tagC.getContext('2d'); g.fillStyle = PAL.yellow; g.beginPath(); g.moveTo(40, 15); g.lineTo(285, 15); g.lineTo(285, 135); g.lineTo(40, 135); g.lineTo(8, 75); g.closePath(); g.fill();
    g.fillStyle = '#0b0f16'; g.beginPath(); g.arc(42, 75, 10, 0, 7); g.fill(); g.font = '400 96px "Bebas Neue"'; g.textAlign = 'center'; g.fillText('JOKE', 172, 112); }
  scenes.push(scene(B2a, B2b, (ctx, t) => {
    U.spaceBg(ctx, t, { starAlpha: 0.7 });
    const flipP = prog(t, M.upside - 0.12, M.upside + 0.62, E.inOut), rot = Math.PI * flipP + 0.006 * Math.max(0, t - M.upside - 0.6);
    const zoom = lerp(0.9, 0.97, prog(t, B2a, B2b)) * (1 - 0.06 * Math.sin(Math.PI * flipP));
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(rot); ctx.translate(-W / 2, -H / 2);
    const T = drawEE(ctx, { cx: 1800, cy: 880, zoom }, 0.48);
    drawDrops(ctx, T, t, { wob: 0.012 });
    ctx.restore();
    // a single drop falls down the frame on "down"
    const fp = prog(t, M.down - 0.25, M.down + 0.45, E.in);
    if (fp > 0 && fp < 1) { const y = lerp(-140, H + 160, fp), s = 110; const pts = U.dropPts(1500, y, s, Math.PI, 0, 0, 0, 1 - 0.15 * fp, 1 + 0.35 * fp);
      ctx.save(); ctx.fillStyle = PAL.cyan; ctx.globalAlpha = 0.95; ctx.beginPath(); U.polyPath(ctx, pts); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.beginPath(); ctx.ellipse(1480, y + 20, 10, 18, 0.4, 0, 7); ctx.fill(); ctx.restore();
      for (let k = 1; k <= 3; k++) { ctx.strokeStyle = `rgba(61,227,255,${0.25 / k})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(1500, y - 120 - k * 30); ctx.lineTo(1500, y - 60 - k * 30); ctx.stroke(); } }
    // JOKE tag wobbles on
    if (t > M.joking - 0.15) { const lt = t - (M.joking - 0.15), drop = E.outBack(prog(lt, 0, 0.35)), sw = 0.55 * Math.exp(-2.6 * lt) * Math.sin(lt * 8.5);
      const px = 1360, py = lerp(-200, 150, drop); ctx.save(); ctx.strokeStyle = 'rgba(244,246,250,0.8)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(px, -10); ctx.lineTo(px, py); ctx.stroke();
      ctx.translate(px, py); ctx.rotate(sw + 0.08); ctx.drawImage(tagC, -42, -75 + 75 - 8, 300, 150); ctx.restore(); }
  }));
  cue(M.upside - 0.12, 'whoosh_soft', -14);

  // ===================================================================================================
  // C  s084  the Apollo 17 photo: frame draws on, fills with the south-up original, rotates 180 to the published version
  // ===================================================================================================
  const Ca = B2b, Cb = SEG('s085').start - 0.06;
  const bmO = api.img(IMG('bluemarble_original.jpg')), bmN = api.img(IMG('bluemarble_northup.jpg'));
  scenes.push(scene(Ca, Cb, (ctx, t) => {
    U.spaceBg(ctx, t, { starAlpha: 0.9, c0: '#0e1a33' });
    const S = 740, cx = 960, cy = 565, x0 = cx - S / 2, y0 = cy - S / 2;
    // frame + photo
    const fillA = prog(t, Ca + 0.25, Ca + 0.85), kb = lerp(1.08, 1.0, prog(t, Ca + 0.25, M.bm + 1.2, E.out)) * (1 + 0.02 * prog(t, M.bm, Cb));
    const rot = Math.PI * prog(t, M.flip - 0.1, M.flip + 0.75, E.inOut), nA = prog(t, M.flip + 0.25, M.flip + 0.8);
    ctx.save(); ctx.fillStyle = '#070a12'; ctx.fillRect(x0, y0, S, S); ctx.beginPath(); ctx.rect(x0, y0, S, S); ctx.clip();
    if (fillA > 0) {
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(kb, kb);
      const d = 2 * 494 / 0.84; ctx.globalAlpha = fillA * (1 - nA); ctx.drawImage(bmO, 757.5 - d / 2, 557 - d / 2, d, d, -S / 2, -S / 2, S, S);
      // yellow ring on Antarctica (top of the original)
      const rr = prog(t, M.bm + 0.55, M.bm + 1.1, E.inOut), ra = 1 - prog(t, M.flip - 0.3, M.flip);
      if (rr > 0 && ra > 0) { ctx.globalAlpha = ra; ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6; ctx.beginPath(); ctx.ellipse((690 - 757.5) / d * S, (190 - 557) / d * S, 150, 72, 0.05, -1.6, -1.6 + Math.PI * 2 * rr); ctx.stroke(); }
      ctx.restore();
      if (nA > 0) { ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot - Math.PI); ctx.scale(kb, kb); ctx.globalAlpha = nA; const dn = 2 * 815 / 0.84; ctx.drawImage(bmN, 950 - dn / 2, 962.5 - dn / 2, dn, dn, -S / 2, -S / 2, S, S); ctx.restore(); }
    }
    ctx.restore();
    // réseau crosses (camera reticle marks)
    for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) { const a = prog(t, Ca + 0.4 + (i + j) * 0.06, Ca + 0.6 + (i + j) * 0.06) * 0.55; if (a <= 0) continue; const px = x0 + S * (0.1 + 0.2 * i), py = y0 + S * (0.1 + 0.2 * j);
      ctx.strokeStyle = `rgba(255,255,255,${a})`; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(px - 9, py); ctx.lineTo(px + 9, py); ctx.moveTo(px, py - 9); ctx.lineTo(px, py + 9); ctx.stroke(); }
    // frame outline draws on
    const fp = prog(t, Ca + 0.02, Ca + 0.9, E.inOut);
    F.glowPath(ctx, [[x0, y0], [x0 + S, y0], [x0 + S, y0 + S], [x0, y0 + S], [x0, y0]], { p: fp, color: '#ffffff', width: 3, glowColor: '#ffffff' });
    for (const [bx, by, sx, sy] of [[x0 - 18, y0 - 18, 1, 1], [x0 + S + 18, y0 - 18, -1, 1], [x0 - 18, y0 + S + 18, 1, -1], [x0 + S + 18, y0 + S + 18, -1, -1]]) { const a = prog(t, Ca + 0.6, Ca + 1.0); ctx.strokeStyle = `rgba(255,210,63,${a})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(bx, by + sy * 46); ctx.lineTo(bx, by); ctx.lineTo(bx + sx * 46, by); ctx.stroke(); }
    pillAt(ctx, 'SHOT WITH ANTARCTICA ON TOP', 960 - 290, 118, t, M.bm + 0.05, Cb);
  }));
  cue(M.photo - 0.05, 'whoosh_soft', -18); cue(M.flip - 0.12, 'whoosh_soft', -14);

  // ===================================================================================================
  // D  s085  EXPLORER GAG 9: hamster-wheel on the flipping planet
  // ===================================================================================================
  const Da = Cb, Db = SEG('s086').start + 0.4;
  const { Actor, tinyPlanet, THREE } = await import('../../lib/actors.js');
  const { llDir } = await import('../../lib/cutaway.js');
  const st9 = await api.newStage('ch5b_gag9', { shadowExtent: 4, hemi: 0.75, key: 2.1, rim: 3.0, exposure: 1.12 });
  const planet = await tinyPlanet(st9, { radius: 3 }); planet.position.set(0, -3, 0);
  const warmRim = new THREE.DirectionalLight(0xffc890, 1.6); warmRim.position.set(7, 3, -5); st9.add(warmRim);
  const hero = await Actor.create(st9, 'models/adventurer.glb', { scale: 0.55 });
  const Q0 = (() => { const f = llDir(-14, 22).normalize(); const n = new THREE.Vector3(0, 1, 0).sub(f.clone().multiplyScalar(f.y)).normalize(); const e = new THREE.Vector3().crossVectors(n, f).normalize();
    const m = new THREE.Matrix4().makeBasis(e, n, f).transpose(); return new THREE.Quaternion().setFromRotationMatrix(m); })();
  const ZAX = new THREE.Vector3(0, 0, 1), Qr = new THREE.Quaternion();
  const r1a = Da + 0.25, r1b = r1a + 1.45, r2a = M.first - 0.02, r2b = r2a + 1.25;
  hero.play(Da - 2, 'Idle_Neutral').play(r1a - 0.05, 'Run', { fade: 0.15, speed: 1.35 }).play(r1b + 0.1, 'Idle_Neutral', { fade: 0.25 })
    .play(r2a - 0.12, 'Run', { fade: 0.15, speed: 1.35 }).play(r2b + 0.05, 'Idle_Neutral', { fade: 0.3 });
  hero.moveAlong([{ t: Da - 1, x: 0, y: 0, z: 0, ry: 20 }, { t: r1a - 0.2, x: 0, y: 0, z: 0, ry: 20 }, { t: r1a + 0.05, x: 0, y: 0, z: 0, ry: 90 }, { t: r2a - 0.25, x: 0, y: 0, z: 0, ry: 90 },
    { t: r2a + 0.02, x: 0, y: 0, z: 0, ry: -90 }, { t: r2b, x: 0, y: 0, z: 0, ry: -90 }, { t: r2b + 0.35, x: 0, y: 0, z: 0, ry: -15 }]);
  const theta = (t) => Math.PI + Math.PI * prog(t, r1a, r1b, E.inOut) - Math.PI * prog(t, r2a, r2b, E.inOut);
  scenes.push(scene(Da, Db, (ctx, t) => {
    U.spaceBg(ctx, t, { c0: '#18305a', cy: 0.75, starAlpha: 0.9 });
    const th = theta(t); Qr.setFromAxisAngle(ZAX, th); planet.quaternion.copy(Qr).multiply(Q0);
    const a = -0.12 + 0.04 * (t - Da);
    st9.lookFrom([Math.sin(a) * 4.9, 0.62, Math.cos(a) * 4.9], [0, 0.62, 0], 31);
    ctx.drawImage(st9.render(t), 0, 0);
    // roll arrows around the rim + speed streaks
    const cP = st9.project(new THREE.Vector3(0, -3, 0)), tP = st9.project(new THREE.Vector3(0, 0, 0)), Rs = Math.abs(cP.y - tP.y);
    const roll = (ra, rb, dir) => { const p = prog(t, ra - 0.1, rb, E.inOut), a = env(t, ra - 0.1, rb + 0.25, 0.15, 0.3); if (a <= 0) return;
      ctx.save(); ctx.globalAlpha = a * 0.9; ctx.strokeStyle = PAL.yellow; ctx.fillStyle = PAL.yellow; ctx.lineWidth = 9; ctx.lineCap = 'round';
      for (const side of [-1, 1]) { const base = -Math.PI / 2 + side * 0.62, span = 0.34; const s0 = base - span / 2 * dir, s1 = base + span / 2 * dir + dir * 0.12 * Math.sin(p * Math.PI);
        ctx.beginPath(); ctx.arc(cP.x, cP.y, Rs * 1.07, Math.min(s0, s1), Math.max(s0, s1)); ctx.stroke();
        const hx = cP.x + Math.cos(s1) * Rs * 1.07, hy = cP.y + Math.sin(s1) * Rs * 1.07, ta = s1 + dir * Math.PI / 2; ctx.beginPath(); ctx.moveTo(hx + Math.cos(ta) * 22, hy + Math.sin(ta) * 22); ctx.lineTo(hx + Math.cos(ta + 2.5) * 20, hy + Math.sin(ta + 2.5) * 20); ctx.lineTo(hx + Math.cos(ta - 2.5) * 20, hy + Math.sin(ta - 2.5) * 20); ctx.closePath(); ctx.fill(); }
      ctx.restore();
      // speed lines behind the runner
      ctx.save(); ctx.globalAlpha = a * 0.5; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; for (let i = 0; i < 4; i++) { const yy = tP.y - 60 - i * 55, ph = ((t * 3 + i * 0.3) % 1); const xx = tP.x - dir * (120 + ph * 160); ctx.beginPath(); ctx.moveTo(xx, yy); ctx.lineTo(xx - dir * 90, yy); ctx.stroke(); } ctx.restore(); };
    roll(r1a, r1b, -1); roll(r2a, r2b, 1);
    // tick when he stops upright on the south-up planet
    const ck = prog(t, r2b + 0.05, r2b + 0.35, E.outBack); if (ck > 0) { ctx.save(); ctx.translate(tP.x + 210, tP.y - 330); ctx.scale(ck, ck); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(-10, 32); ctx.lineTo(48, -40); ctx.stroke(); ctx.restore(); }
  }));
  cue(r1a - 0.05, 'whoosh_soft', -16); cue(r2a - 0.05, 'whoosh_soft', -16);

  // ===================================================================================================
  // E  s086  the drops slosh together into "Pangooy" + Tuesday 9 a.m. card
  // ===================================================================================================
  const Ea = Db, Eb = M.twist - 0.06;
  const [tgx, tgy] = U.ee(-6, 14);
  scenes.push(scene(Ea, Eb, (ctx, t) => {
    U.spaceBg(ctx, t, { starAlpha: 0.6 });
    const k = prog(t, Ea, Eb, E.inOut);
    const T = drawEE(ctx, { cx: lerp(1880, 1960, k), cy: lerp(880, 860, k), zoom: lerp(1.0, 1.06, k) }, 0.45);
    const p = prog(t, M.splash - 0.05, M.pangooy - 0.15, E.inOut), lt = t - (M.pangooy - 0.15);
    const settle = lt > 0 ? 16 * Math.exp(-3 * lt) * Math.sin(lt * 11) : 0;
    const pos = (c, i) => { const tx = tgx + (c.x - meanX) * 0.2, ty = tgy + (c.y - meanY) * 0.2; const px = -(ty - c.y), py = tx - c.x, pl = Math.hypot(px, py) || 1; const sl = Math.sin(Math.PI * p) * 70 * (i % 2 ? 1 : -1);
      return [lerp(c.x, tx, p) + px / pl * sl + settle * (i % 2 ? 1 : -1), lerp(c.y, ty, p) + py / pl * sl + settle * 0.5]; };
    const u = prog(p, 0.55, 0.95);
    const wob = 0.012 + 0.07 * Math.sin(Math.PI * p) + (lt > 0 ? 0.03 + 0.03 * Math.exp(-2 * lt) : 0);
    const shapes = drawDrops(ctx, T, t, { pos, wob, union: u, indiv: 1 - u });
    // googly eyes on the blob
    const ep = E.outBack(prog(t, M.pangooy - 0.12, M.pangooy + 0.2));
    if (ep > 0) { const bx = T.ox + tgx * T.z, by = T.oy + tgy * T.z - 70; ctx.save(); ctx.translate(bx, by); ctx.scale(ep, ep); U.googly(ctx, -40, 0, 30, t, 0.3); U.googly(ctx, 36, -6, 24, t * 1.13, 2.1); ctx.restore(); }
    pillAt(ctx, '"PANGOOY" (A JOKE)', 110, 100, t, M.pangooy - 0.08, Eb);
    // gag card: Tuesday, 9:00 a.m., 1,786,379 A.D.
    const cp = prog(t, M.tue - 0.12, M.tue + 0.4, E.outExpo);
    if (cp > 0) {
      const cx0 = lerp(W + 40, 1150, cp), cy0 = 330, cw = 650, ch = 300;
      ctx.save(); ctx.translate(cx0, cy0); ctx.rotate(lerp(0.12, 0.02, cp) + 0.006 * Math.sin(t));
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, 8, 14, cw, ch, 22); ctx.fill();
      ctx.fillStyle = '#f4efe2'; F.round(ctx, 0, 0, cw, ch, 22); ctx.fill(); ctx.fillStyle = PAL.hero; F.round(ctx, 0, 0, cw, 46, 22); ctx.fill(); ctx.fillRect(0, 24, cw, 22);
      for (let i = 0; i < 6; i++) { ctx.fillStyle = '#c9c1ae'; ctx.beginPath(); ctx.arc(70 + i * 100, 23, 8, 0, 7); ctx.fill(); }
      const ring = M.tue + 0.55, sh = t > ring && t < ring + 0.7 ? Math.sin((t - ring) * 70) * 0.16 * (1 - (t - ring) / 0.7) : 0;
      const sp = prog(t, M.tz - 0.05, M.tz + 1.15, E.inOut);
      ctx.save(); ctx.translate(120, 175); ctx.rotate(sh); U.clockIcon(ctx, 0, 0, 78, Math.PI * 1.5 + sp * Math.PI * 2, sp * Math.PI * 2 * 3); ctx.restore();
      F.text(ctx, 'TUESDAY, 9:00 A.M.,', 230, 160, { size: 54, fam: F.FAM.label, weight: 800, color: '#141922', tracking: 0.03, shadow: false });
      F.text(ctx, '1,786,379 A.D.', 230, 236, { size: 62, fam: F.FAM.body, weight: 800, color: PAL.hero, shadow: false });
      ctx.restore();
    }
  }));
  cue(M.pangooy - 0.35, 'splash_big', -12); cue(M.tue + 0.55, 'bell_small', -14);

  // ===================================================================================================
  // F  s087  the twist: split screen 1970 real map (simplified) vs 1976 joke
  // ===================================================================================================
  const Fa = Eb, Fb = SEG('s088').start - 0.1;
  const PW = 820, PH = Math.round(PW * U.EE_H / U.EE_W), pz = PW / U.EE_W;
  const outl = U.eeOutline();
  const panelBase = (g) => { g.save(); g.beginPath(); outl.forEach(([x, y], i) => i ? g.lineTo(x * pz, y * pz) : g.moveTo(x * pz, y * pz)); g.closePath(); g.clip(); };
  const realPanel = U.cv(PW, PH);
  { const g = realPanel.getContext('2d'); panelBase(g); g.fillStyle = '#0d2442'; g.fillRect(0, 0, PW, PH);
    g.strokeStyle = 'rgba(255,255,255,0.07)'; g.lineWidth = 1; for (let lo = -150; lo <= 150; lo += 30) { g.beginPath(); for (let la = -90; la <= 90; la += 5) { const [x, y] = U.ee(lo, la); la === -90 ? g.moveTo(x * pz, y * pz) : g.lineTo(x * pz, y * pz); } g.stroke(); }
    for (let la = -60; la <= 60; la += 30) { g.beginPath(); const [x0, y0] = U.ee(-180, la), [x1] = U.ee(180, la); g.moveTo(x0 * pz, y0 * pz); g.lineTo(x1 * pz, y0 * pz); g.stroke(); }
    g.beginPath();
    for (const r of coast200) {
      const u = []; let off = 0, prev = null; for (const [lo, la] of r) { let L = lo + off; if (prev !== null) { if (L - prev > 180) { off -= 360; L -= 360; } else if (L - prev < -180) { off += 360; L += 360; } } u.push([L, la]); prev = L; }
      const net = u[u.length - 1][0] - u[0][0]; if (Math.abs(net) > 300) { const pole = u.reduce((a, p) => a + p[1], 0) / u.length > 0 ? 90 : -90; u.push([u[u.length - 1][0], pole], [u[0][0], pole]); }
      let mn = 1e9, mx = -1e9; for (const p of u) { mn = Math.min(mn, p[0]); mx = Math.max(mx, p[0]); }
      for (const sh of [-360, 0, 360]) { if (mx + sh < -180 || mn + sh > 180) continue; u.forEach(([L, la], i) => { const [x, y] = U.ee(L + sh, la); i ? g.lineTo(x * pz, y * pz) : g.moveTo(x * pz, y * pz); }); g.closePath(); }
    }
    g.fillStyle = '#d9c896'; g.fill('nonzero'); g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 1; g.stroke(); g.restore();
    g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 2; g.beginPath(); outl.forEach(([x, y], i) => i ? g.lineTo(x * pz, y * pz) : g.moveTo(x * pz, y * pz)); g.closePath(); g.stroke(); }
  const jokePanel = U.cv(PW, PH);
  { const g = jokePanel.getContext('2d'); panelBase(g); g.drawImage(EEC, 0, 0, PW, PH); g.fillStyle = 'rgba(3,6,13,0.45)'; g.fillRect(0, 0, PW, PH);
    for (const c of CONTS) { const d = U.dropPts(c.x * pz, c.y * pz, c.s * pz); g.fillStyle = 'rgba(255,90,54,0.6)'; g.beginPath(); U.polyPath(g, d); g.fill(); g.strokeStyle = '#fff'; g.lineWidth = 2; g.stroke(); }
    g.restore(); }
  const TRK = ['cape_horn', 'cape_agulhas', 'kanyakumari', 'florida_tip', 'nyc', 'australia_c', 'africa_c', 'samerica_c', 'india_c', 'tasmania_s', 'madagascar_s', 'cape_farewell'];
  const trkPanel = TRK.map(n => { const tr = tracks[n], o = []; for (let i = 200; i >= 0; i -= 2) { const a = tr[i]; if (!a || a[0] > 900) continue; const [x, y] = U.ee(a[0], a[1]); o.push([x * pz, y * pz]); } return o; });
  scenes.push(scene(Fa, Fb, (ctx, t) => {
    U.dataBg(ctx, t);
    const [sx, sy] = U.shake(t, M.twist, 12);
    ctx.save(); ctx.translate(sx, sy); const z = lerp(1, 1.03, prog(t, Fa, Fb)); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
    const Lx = 100, Rx = 1000, Py = 285;
    // divider
    const dv = prog(t, M.twist - 0.04, M.twist + 0.4, E.outExpo); ctx.fillStyle = PAL.yellow; ctx.fillRect(958, 120, 4, 800 * dv);
    const lp = prog(t, M.twist + 0.08, M.twist + 0.6, E.outExpo), rp = prog(t, M.twist + 0.3, M.twist + 0.85, E.outExpo);
    const frame = (img, x, y) => { ctx.fillStyle = 'rgba(0,0,0,0.4)'; F.round(ctx, x - 10, y - 10 + 8, PW + 20, PH + 20, 16); ctx.fill(); ctx.fillStyle = '#081426'; F.round(ctx, x - 10, y - 10, PW + 20, PH + 20, 16); ctx.fill(); ctx.drawImage(img, x, y); };
    if (lp > 0) { const x = lerp(-PW - 40, Lx, lp); frame(realPanel, x, Py);
      // motion trails 200 Ma -> today
      trkPanel.forEach((pts, i) => { const q = prog(t, M.earlier + 0.5 + i * 0.06, M.earlier + 2.6 + i * 0.06, E.inOut); if (q <= 0) return; const sp = pts.map(([a, b]) => [a + x, b + Py]);
        const head = F.glowPath(ctx, sp, { p: q, color: PAL.cyan, width: 2.5 }); if (head && q > 0.98) F.dot(ctx, head[0], head[1], { r: 4.5, color: PAL.cyan }); });
    }
    if (rp > 0) { const x = lerp(W + 40, Rx, rp); frame(jokePanel, x, Py); }
    // labels (faded before the name lands: max two text elements)
    const lblOut = M.apart2 + 0.35;
    if (lp > 0) pillAt(ctx, '1970: THE REAL MAP (SIMPLIFIED)', Lx, Py - 52, t, M.earlier - 0.05, lblOut, { size: 34 });
    if (rp > 0) pillAt(ctx, '1976: THE JOKE', Rx, Py - 52, t, M.real - 0.05, lblOut, { size: 34 });
    // yellow bracket linking both under one name
    const bp = prog(t, M.apart2 - 0.08, M.apart2 + 0.55, E.inOut);
    if (bp > 0) { const yb = Py + PH + 22, ym = Py + PH + 90; const pts = [[Lx + PW / 2, yb], [Lx + PW / 2, ym], [Rx + PW / 2, ym], [Rx + PW / 2, yb]];
      const L1 = U.polyLen(pts.slice(0, 2)), Lt = U.polyLen(pts); // grow from the middle outwards
      const half = (bp * Lt) / 2, mid = [960, ym];
      const segL = [[mid, [Lx + PW / 2, ym], [Lx + PW / 2, yb]], [mid, [Rx + PW / 2, ym], [Rx + PW / 2, yb]]];
      for (const s of segL) F.glowPath(ctx, s, { p: bp, color: PAL.yellow, width: 5 }); }
    pillAt(ctx, 'JOHN C. HOLDEN', 960 - 165, Py + PH + 150, t, M.apart2 + 0.42, Fb + 0.2, { size: 44, border: PAL.yellow });
    ctx.restore();
  }));
  cue(M.twist - 0.02, 'impact_deep', -6); cue(M.earlier - 0.12, 'whoosh_soft', -18); cue(M.real - 0.12, 'whoosh_soft', -18);

  // ===================================================================================================
  // G1 s088  reference card: "DIETZ & HOLDEN (1970)" highlighted
  // ===================================================================================================
  const G1a = Fb, G1b = M.pointline - 0.22;
  const PREF = U.paper(1180, 560, 31, { c0: '#f7f2e6', c1: '#e8ddc4' });
  let refW = 0;
  { const g = PREF.g; g.save(); g.translate(PREF.pad, PREF.pad); U.greek(g, 90, 92, 300, 1, 30, 41, { h: 18, alpha: 0.8 });
    U.greek(g, 90, 165, 1000, 2, 40, 42, { h: 11, alpha: 0.45 });
    refW = U.typeStr(g, 'DIETZ & HOLDEN (1970)', 90, 300, 48, 43); U.greek(g, 90 + refW + 24, 296, 1000 - refW - 30, 1, 40, 44, { h: 12, alpha: 0.55 });
    U.greek(g, 90, 360, 1000, 1, 40, 46, { h: 11, alpha: 0.45 });
    U.greek(g, 90, 440, 1000, 2, 40, 45, { h: 11, alpha: 0.45 }); g.restore(); }
  scenes.push(scene(G1a, G1b, (ctx, t) => {
    U.deskBg(ctx, t);
    const ip = prog(t, G1a, G1a + 0.55, E.outExpo), push = prog(t, G1a, G1b, E.inOut);
    const sc = lerp(0.95, 1.12, push), x = 960 + lerp(0, 120, push), y = lerp(-500, 560, ip) + lerp(0, 40, push);
    U.drawPaper(ctx, PREF, x, y, lerp(-0.12, -0.025, ip), sc, 1, (g) => {
      const hp = prog(t, M.cited - 0.12, M.cited + 0.4, E.out);
      if (hp > 0) { g.save(); g.globalCompositeOperation = 'multiply'; g.fillStyle = 'rgba(255,210,63,0.85)'; g.beginPath(); g.moveTo(78, 252); g.lineTo(78 + (refW + 26) * hp, 248); g.lineTo(78 + (refW + 26) * hp, 318); g.lineTo(78, 316); g.closePath(); g.fill(); g.restore(); }
    });
  }));
  cue(G1a + 0.02, 'paper_rustle', -18);

  // ===================================================================================================
  // G2 s088-s089  teardrop points -> dotted tracks -> converge on Antarctica's ring; ring flares on "answer"
  // ===================================================================================================
  const G2a = G1b, G2b = M.notdone - 0.08;
  const ringPts = U.latCircle(-68, 240);
  const TR3 = [['cape_agulhas', [-34.83, 20.0]], ['cape_horn', [-53.9, -71.3]], ['kanyakumari', [8.08, 77.55]]];
  const drawRing = (ctx, g, t, flareT) => {
    const fl = flareT != null ? Math.max(0, 1 - Math.abs(t - flareT - 0.25) / 0.6) : 0;
    for (const run of U.projRuns(g, ringPts)) { F.glowPath(ctx, run, { p: 1, color: PAL.yellow, width: 3 + 6 * fl, alpha: 0.8 + 0.2 * fl }); }
    if (fl > 0 || (flareT != null && t > flareT)) { const q = g.project(-90, 0); if (q.visible) { const k = flareT != null ? clamp((t - flareT) / 1.4) : 0; const r = 40 + 360 * k;
      ctx.save(); ctx.globalAlpha = 0.6 * (1 - k); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6; ctx.beginPath(); ctx.ellipse(q.x, q.y, r, r * 0.5, 0, 0, 7); ctx.stroke(); ctx.restore(); } }
  };
  scenes.push(gshot({ t0: G2a, t1: G2b, overlay: { canvas: dropsOv, bounds: WORLD }, patch: null, drift: 0.4,
    keys: [{ t: G2a, lat: -28, lon: 22, alt: 3.0 }, { t: G2b, lat: -38, lon: 14, alt: 2.65 }],
    look: (t) => ({ dim: 0.3, desat: 0.3, ovAlpha: 0.95, relief: 0.6 }),
    extra: (ctx, t, api) => {
      const g = api.g;
      drawRing(ctx, g, t, M.answer - 0.1);
      // the point that "shows where it came from" glows
      const tp = g.project(-34.83, 20.0); if (t > M.pointline - 0.1 && tp.visible) { const a = prog(t, M.pointline - 0.1, M.pointline + 0.2); const gl = ctx.createRadialGradient(tp.x, tp.y, 0, tp.x, tp.y, 70); gl.addColorStop(0, `rgba(255,240,200,${0.9 * a})`); gl.addColorStop(1, 'rgba(255,90,54,0)'); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(tp.x, tp.y, 70, 0, 7); ctx.fill(); F.dot(ctx, tp.x, tp.y, { r: 8, color: '#ffffff', ring: ((t - M.pointline) * 0.9) % 1 }); }
      TR3.forEach(([n, tip], i) => { const st = i === 0 ? M.punch - 0.12 : M.punch + 0.55 + i * 0.25; const p = prog(t, st, st + 1.2, E.inOut); if (p <= 0) return;
        const pts = [{ lat: tip[0], lon: tip[1] }, ...U.trackPts(tracks, n, 0, 180)];
        for (const run of U.projRuns(g, pts)) F.glowPath(ctx, run, { p, color: PAL.yellow, width: 5, dash: [2, 13] }); });
    } }));
  cue(M.pointline - 0.1, 'pop_ui', -16); cue(M.answer - 0.08, 'shimmer', -14);

  // ===================================================================================================
  // H1 s089  1 s callback: the 1973 DRIP sheet
  // ===================================================================================================
  const H1a = G2b, H1b = H1a + 1.05;
  const P73 = U.paper(1100, 560, 73, { stain: [880, 150, 110] });
  { const g = P73.g; g.save(); g.translate(P73.pad, P73.pad); U.greek(g, 90, 110, 500, 1, 30, 51, { h: 12, alpha: 0.5 });
    const w1 = U.typeStr(g, 'CONTINENTAL DRI', 90, 300, 84, 52), w2 = U.typeStr(g, 'FT', 90 + w1, 300, 84, 53);
    g.strokeStyle = '#c0392b'; g.lineWidth = 9; g.beginPath(); g.moveTo(90 + w1 - 6, 272); g.lineTo(90 + w1 + w2 + 6, 266); g.stroke();
    U.typeStr(g, 'P', 90 + w1 + w2 * 0.25, 200, 84, 54, { color: '#c0392b' });
    U.greek(g, 90, 400, 920, 3, 40, 55, { h: 10, alpha: 0.45 }); g.restore(); }
  scenes.push(scene(H1a, H1b, (ctx, t) => { U.deskBg(ctx, t); const p = prog(t, H1a, H1a + 0.3, E.outExpo); U.drawPaper(ctx, P73, 960, 540, lerp(0.05, -0.02, p), lerp(1.18, 1.04, p) + 0.04 * prog(t, H1a, H1b), 1); }));
  cue(H1a, 'paper_rustle', -16);

  // ===================================================================================================
  // H2 s089  globe dives to Nevada, pulsing marker
  // ===================================================================================================
  const H2a = H1b, H2b = M.nev - 0.08;
  scenes.push(gshot({ t0: H2a, t1: H2b, overlay: null, patch: null, drift: 0.3,
    keys: [{ t: H2a, lat: 34, lon: -98, alt: 2.0 }, { t: H2a + 1.9, lat: 38.4, lon: -116.5, alt: 0.42, tilt: 36, heading: -6 }],
    look: { dim: 0.08, desat: 0.2 },
    extra: (ctx, t, api) => { if (t < M.realdrip - 0.12) return; const q = api.g.project(39.0, -116.8); if (!q.visible) return; const a = prog(t, M.realdrip - 0.12, M.realdrip + 0.1);
      ctx.save(); ctx.globalAlpha = a; F.dot(ctx, q.x, q.y, { r: 11, color: PAL.cyan, ring: ((t - M.realdrip) * 1.2) % 1 }); F.dot(ctx, q.x, q.y, { r: 11, color: PAL.cyan, ring: ((t - M.realdrip) * 1.2 + 0.5) % 1 }); ctx.restore(); } }));
  cue(H2a, 'whoosh_soft', -16);

  // ===================================================================================================
  // H3 s089  cross-section under the western US: a cold drip sinks; honey-spoon inset; "ANTI-DRIP"
  // ===================================================================================================
  const H3a = H2b, H3b = SEG('s090').start - 0.08;
  const topo = (x) => { if (x < 210) return -14; let e = 0; e += 26 * Math.exp(-Math.pow((x - 300) / 40, 2)); e += 8; e += 54 * Math.exp(-Math.pow((x - 560) / 70, 2)); if (x > 640 && x < 1460) e += 14 + 12 * Math.abs(Math.sin((x - 640) / 46)); e += 46 * Math.exp(-Math.pow((x - 1520) / 50, 2)); if (x > 1560) e += 30; return e; };
  const SURF = 250, CRUST = 300, LITH = 362, BX = 990;
  const sectionStatic = U.cv(W, H);
  { const g = sectionStatic.getContext('2d');
    const sky = g.createLinearGradient(0, 0, 0, SURF); sky.addColorStop(0, '#07101f'); sky.addColorStop(1, '#173052'); g.fillStyle = sky; g.fillRect(0, 0, W, SURF + 40);
    const as = g.createLinearGradient(0, LITH, 0, H); as.addColorStop(0, '#7d2f1e'); as.addColorStop(1, '#c4552a'); g.fillStyle = as; g.fillRect(0, LITH - 2, W, H);
    g.fillStyle = '#4b3a30'; g.fillRect(0, CRUST - 2, W, LITH - CRUST + 2);
    g.beginPath(); g.moveTo(0, SURF + 40); for (let x = 0; x <= W; x += 6) g.lineTo(x, SURF - topo(x)); g.lineTo(W, CRUST); g.lineTo(0, CRUST); g.closePath();
    const cr = g.createLinearGradient(0, SURF - 60, 0, CRUST); cr.addColorStop(0, '#a98a5c'); cr.addColorStop(1, '#6e5238'); g.fillStyle = cr; g.fill();
    g.strokeStyle = 'rgba(255,240,210,0.15)'; g.lineWidth = 1.5; for (let k = 1; k < 4; k++) { g.beginPath(); for (let x = 0; x <= W; x += 10) { const y = lerp(SURF - topo(x), CRUST, k / 4); x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
    g.fillStyle = '#1e5b8c'; g.fillRect(0, SURF - 14, 210, 20); // Pacific edge
    g.strokeStyle = '#e9f2ff'; g.lineWidth = 3; g.beginPath(); for (let x = 0; x <= W; x += 6) { const y = SURF - topo(x); x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
    g.setLineDash([6, 12]); g.strokeStyle = 'rgba(255,255,255,0.12)'; g.lineWidth = 1.5; for (let d = 100; d <= 350; d += 50) { g.beginPath(); g.moveTo(0, CRUST + d * 2); g.lineTo(W, CRUST + d * 2); g.stroke(); } g.setLineDash([]);
  }
  const blobPoly = (Lpx, t) => U.dripPoly(Lpx, { top: 70, neck: 22, bulb: 60, wob: 7, t });
  const honeyIn = M.honey - 0.25, detach = M.honey + 2.55;
  scenes.push(scene(H3a, H3b, (ctx, t) => {
    const push = prog(t, M.anti - 0.1, M.anti + 1.3, E.inOut), k = 1 + 0.035 * prog(t, H3a, H3b) + 0.12 * push;
    ctx.save(); ctx.translate(BX, 560); ctx.scale(k, k); ctx.translate(-BX, -560);
    ctx.drawImage(sectionStatic, 0, 0);
    // convection streaks in the warm mantle
    ctx.save(); ctx.strokeStyle = 'rgba(255,190,120,0.10)'; ctx.lineWidth = 3; for (let i = 0; i < 9; i++) { const y = 470 + i * 70, ph = t * 0.25 + i; ctx.beginPath(); for (let x = 0; x <= W; x += 40) { const yy = y + 18 * Math.sin(x / 210 + ph); x ? ctx.lineTo(x, yy) : ctx.moveTo(x, yy); } ctx.stroke(); } ctx.restore();
    // the drip
    const Lmi = lerp(22, 300, prog(t, M.nev - 0.05, M.nev + 4.0, E.inOut)) + 32 * prog(t, M.honey - 0.1, detach, E.inOut);
    const L = Lmi * 2, poly = blobPoly(L, t).map(([x, y]) => [BX + x, CRUST + 4 + y]);
    const halo = ctx.createRadialGradient(BX, CRUST + L - 60, 10, BX, CRUST + L - 60, 230); halo.addColorStop(0, 'rgba(120,220,255,0.32)'); halo.addColorStop(1, 'rgba(120,220,255,0)'); ctx.fillStyle = halo; ctx.fillRect(BX - 260, CRUST + L - 300, 520, 520);
    const bg = ctx.createLinearGradient(0, CRUST, 0, CRUST + L); bg.addColorStop(0, '#d2f6ff'); bg.addColorStop(0.5, '#6cc4f2'); bg.addColorStop(1, '#2a76d2');
    ctx.fillStyle = bg; ctx.beginPath(); U.polyPath(ctx, poly); ctx.fill(); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(BX - 20, CRUST + L - 80, 12, 22, 0.3, 0, 7); ctx.fill();
    for (let i = 0; i < 3; i++) { const f = ((t * 0.7 + i / 3) % 1), yy = CRUST + 60 + f * Math.max(10, L - 160); if (yy > CRUST + L - 90) continue; ctx.strokeStyle = `rgba(20,60,120,${0.6 * Math.sin(Math.PI * f)})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(BX - 9, yy - 6); ctx.lineTo(BX, yy + 4); ctx.lineTo(BX + 9, yy - 6); ctx.stroke(); }
    // surface pin above the drip
    const py = SURF - topo(BX); F.dot(ctx, BX, py - 4, { r: 9, color: PAL.cyan, ring: ((t - H3a) * 0.8) % 1 });
    ctx.restore();
    pillAt(ctx, 'REAL DRIP: UNDER NEVADA (SIMPLIFIED)', 110, 100, t, M.nev + 0.05, H3b + 0.2);
    // honey off a spoon (inset, top-right), same shape
    const ia = prog(t, honeyIn, honeyIn + 0.3, E.outBack);
    if (ia > 0) {
      const x0 = 1390, y0 = 160, w = 430, h = 430; ctx.save(); ctx.translate(x0 + w / 2, y0 + h / 2); ctx.scale(lerp(0.85, 1, ia), lerp(0.85, 1, ia)); ctx.translate(-(x0 + w / 2), -(y0 + h / 2)); ctx.globalAlpha = clamp(ia);
      ctx.fillStyle = 'rgba(0,0,0,0.45)'; F.round(ctx, x0 + 8, y0 + 12, w, h, 26); ctx.fill();
      const pg = ctx.createLinearGradient(0, y0, 0, y0 + h); pg.addColorStop(0, '#3a2614'); pg.addColorStop(1, '#170e07'); ctx.fillStyle = pg; F.round(ctx, x0, y0, w, h, 26); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 3; ctx.stroke();
      ctx.save(); F.round(ctx, x0, y0, w, h, 26); ctx.clip();
      // spoon
      ctx.strokeStyle = '#c9d2dc'; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0 + w + 20, y0 + 40); ctx.lineTo(x0 + 250, y0 + 108); ctx.stroke();
      const sx = x0 + 175, sy = y0 + 118; ctx.fillStyle = '#d7dee6'; ctx.beginPath(); ctx.ellipse(sx, sy, 92, 34, -0.18, 0, 7); ctx.fill(); ctx.fillStyle = '#9aa7b8'; ctx.beginPath(); ctx.ellipse(sx, sy + 6, 80, 22, -0.18, 0, Math.PI); ctx.fill();
      const hg = ctx.createLinearGradient(0, sy, 0, y0 + h); hg.addColorStop(0, '#ffcb3a'); hg.addColorStop(1, '#c86a00');
      ctx.fillStyle = '#f5a516'; ctx.beginPath(); ctx.ellipse(sx - 4, sy - 2, 70, 18, -0.18, 0, 7); ctx.fill();
      const hp = prog(t, M.honey - 0.1, detach, E.inOut), Lh = t < detach ? lerp(8, 230, hp) : lerp(230, 120, prog(t, detach, detach + 0.6, E.out));
      const hpoly = U.dripPoly(Lh, { top: 30, neck: 7, bulb: 22, wob: 3, t }).map(([x, y]) => [sx - 12 + x, sy + 18 + y]);
      ctx.fillStyle = hg; ctx.beginPath(); U.polyPath(ctx, hpoly); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,0.4)'; ctx.beginPath(); ctx.ellipse(sx - 18, sy + 18 + Lh - 30, 5, 10, 0.3, 0, 7); ctx.fill();
      if (t > detach) { const fy = sy + 18 + 230 - 22 + 260 * Math.pow(clamp((t - detach) / 0.42), 2); if (t < detach + 0.42) { ctx.fillStyle = '#f0a020'; ctx.beginPath(); U.polyPath(ctx, U.dropPts(sx - 12, fy, 26, Math.PI)); ctx.fill(); } }
      const pud = prog(t, detach + 0.4, detach + 0.7, E.outBack); ctx.fillStyle = '#d98a10'; ctx.beginPath(); ctx.ellipse(sx - 12, y0 + h - 24, 30 + 40 * pud, 8 + 6 * pud, 0, 0, 7); ctx.fill();
      ctx.restore(); ctx.restore();
    }
    // "ANTI-DRIP" quote + no-drip icon
    const qa = prog(t, M.anti - 0.12, M.anti + 0.2, E.outBack);
    if (qa > 0) { ctx.save(); ctx.translate(205, 620); ctx.scale(qa, qa); ctx.fillStyle = 'rgba(8,11,18,0.75)'; ctx.beginPath(); ctx.arc(0, 0, 58, 0, 7); ctx.fill();
      ctx.fillStyle = PAL.cyan; ctx.beginPath(); U.polyPath(ctx, U.dropPts(0, 2, 44, Math.PI)); ctx.fill(); ctx.strokeStyle = PAL.danger; ctx.lineWidth = 9; ctx.beginPath(); ctx.arc(0, 0, 46, 0, 7); ctx.moveTo(-32, -32); ctx.lineTo(32, 32); ctx.stroke(); ctx.restore(); }
    pillAt(ctx, '"ANTI-DRIP"', 285, 620, t, M.anti - 0.1, H3b + 0.2, { size: 52 });
  }));
  cue(detach + 0.42, 'pop_ui', -16); cue(M.anti - 0.1, 'pop_ui', -18);

  // ===================================================================================================
  // I  s090-s091  the honest part: 12 peninsula tiles with needles; four swing north
  // ===================================================================================================
  const Ia = H3b, Ib = M.antpen - 0.08;
  const day = api.img('tex/day_8k.jpg');
  const landBB = landRings.map(r => { let a = 1e9, b = 1e9, c = -1e9, d = -1e9; for (const [lo, la] of r) { a = Math.min(a, lo); b = Math.min(b, la); c = Math.max(c, lo); d = Math.max(d, la); } return { r, bb: [a, b, c, d] }; });
  const featR = (fs) => allRings(fs.filter(Boolean));
  const TILES = [
    { k: 'sam', lat: -29, lon: -63, span: 60, base: [-36, -66.5], tip: [-53.9, -71.3], clip: [[-85, 14], [-30, 14], [-30, -60], [-85, -60]] },
    { k: 'grl', lat: 70, lon: -42, span: 30, base: [73, -40], tip: [59.8, -43.9], feat: featR([findFeature(C50, 'Greenland')]) },
    { k: 'ind', lat: 17, lon: 79, span: 26, base: [21.5, 78], tip: [8.08, 77.55], clip: [[66, 25], [89, 25], [80.3, 12], [79.7, 9.8], [77.6, 7.6], [76, 8.5], [70, 15]] },
    { k: 'fla', lat: 27.6, lon: -82.6, span: 8.4, base: [29.9, -82.6], tip: [25.12, -81.08], feat: flRings },
    { k: 'baja', lat: 27.4, lon: -112.6, span: 13.5, base: [31.6, -115.6], tip: [22.88, -109.9], feat: bajaR0 },
    { k: 'kam', lat: 55.6, lon: 158.6, span: 14, base: [59.3, 160.8], tip: [50.87, 156.67], feat: featR(TIPS.features.filter(f => f.properties.name === 'Kamchatka')) },
    { k: 'mal', lat: 6.2, lon: 101.2, span: 15, base: [11.0, 99.3], tip: [1.27, 103.51], clip: [[97.5, 13.5], [99.8, 13.5], [104.8, 1.0], [103, 0.8], [100, 3.6], [98.2, 8]] },
    { k: 'gre', lat: 38.6, lon: 22.6, span: 7.6, base: [40.3, 22.2], tip: [36.38, 22.48], feat: featR([findFeature(C50, 'Greece')]) },
    { k: 'york', lat: -14.2, lon: 143.2, span: 11, base: [-16.8, 143.8], tip: [-10.69, 142.53], clip: [[140.5, -10], [146, -10], [146, -17.6], [140.5, -17.6]], north: 1 },
    { k: 'yuc', lat: 19.6, lon: -89.2, span: 8.4, base: [18.3, -89.6], tip: [21.6, -87.1], clip: [[-92.6, 22], [-86, 22], [-86, 17.9], [-92.6, 17.9]], north: 1 },
    { k: 'jut', lat: 56.3, lon: 9.8, span: 5.2, base: [55.2, 9.2], tip: [57.75, 10.6], clip: [[7.8, 58], [11.0, 58], [11.0, 54.85], [7.8, 54.85]], north: 1 },
    { k: 'tay', lat: 75.2, lon: 101, span: 11, base: [72.9, 97], tip: [77.72, 104.3], clip: [[84, 81], [116, 81], [116, 72.2], [84, 72.2]], north: 1 },
  ];
  const TW = 600, TH = 400;
  for (const s of TILES) {
    const c = U.cv(TW, TH), g = c.getContext('2d'), k = TH / s.span, cl = Math.cos(s.lat * D2R), dLat = TH / 2 / k, dLon = TW / 2 / (k * cl);
    const X = lo => TW / 2 + (lo - s.lon) * cl * k, Y = la => TH / 2 - (la - s.lat) * k;
    g.drawImage(day, (s.lon - dLon + 180) / 360 * 8192, (90 - (s.lat + dLat)) / 180 * 4096, 2 * dLon / 360 * 8192, 2 * dLat / 180 * 4096, 0, 0, TW, TH);
    g.globalCompositeOperation = 'saturation'; g.fillStyle = 'rgba(128,128,128,0.45)'; g.fillRect(0, 0, TW, TH);
    g.globalCompositeOperation = 'multiply'; g.fillStyle = '#8492a8'; g.fillRect(0, 0, TW, TH); g.globalCompositeOperation = 'source-over';
    const path = rs => { g.beginPath(); for (const r of rs) { r.forEach(([lo, la], i) => i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))); g.closePath(); } };
    const fr = s.feat || landBB.filter(o => o.bb[0] < s.lon + dLon && o.bb[2] > s.lon - dLon && o.bb[1] < s.lat + dLat && o.bb[3] > s.lat - dLat).map(o => o.r);
    g.save(); if (s.clip) { path([s.clip]); g.clip(); }
    g.globalAlpha = 0.62; g.fillStyle = PAL.hero; path(fr); g.fill('evenodd'); g.globalAlpha = 0.95; g.strokeStyle = '#ffffff'; g.lineWidth = 2.2; g.stroke(); g.restore();
    const vg = g.createRadialGradient(TW / 2, TH / 2, 120, TW / 2, TH / 2, 380); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.35)'); g.fillStyle = vg; g.fillRect(0, 0, TW, TH);
    s.c = c; s.b = [X(s.base[1]), Y(s.base[0])]; s.tp = [X(s.tip[1]), Y(s.tip[0])];
    s.len = Math.hypot(s.tp[0] - s.b[0], s.tp[1] - s.b[1]); s.ang = Math.atan2(s.tp[1] - s.b[1], s.tp[0] - s.b[0]);
  }
  const swingT = { york: M.york, yuc: M.yuc, jut: M.jut, tay: M.tay };
  const layA = (i) => { const col = i % 4, row = Math.floor(i / 4), tw = 360, th = 240, gx = 22, gy = 22, x0 = (W - (4 * tw + 3 * gx)) / 2; return [x0 + col * (tw + gx), 172 + row * (th + gy), tw, th]; };
  const layB = (i) => { if (i < 8) { const tw = 176, th = 117, gx = 14, x0 = (W - (8 * tw + 7 * gx)) / 2; return [x0 + i * (tw + gx), 165, tw, th]; } const j = i - 8, tw = 405, th = 270, gx = 22, x0 = (W - (4 * tw + 3 * gx)) / 2; return [x0 + j * (tw + gx), 372, tw, th]; };
  scenes.push(scene(Ia, Ib, (ctx, t) => {
    U.dataBg(ctx, t);
    const lB = prog(t, M.york - 0.4, M.york + 0.25, E.inOut), z = 1 + 0.025 * prog(t, Ia, Ib);
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
    // scan sweep before the snap
    if (t < M.honest) { const y = lerp(0, H, prog(t, Ia, M.honest - 0.1, E.inOut)); ctx.fillStyle = 'rgba(61,227,255,0.5)'; ctx.fillRect(0, y, W, 3); const sg = ctx.createLinearGradient(0, y - 120, 0, y); sg.addColorStop(0, 'rgba(61,227,255,0)'); sg.addColorStop(1, 'rgba(61,227,255,0.12)'); ctx.fillStyle = sg; ctx.fillRect(0, y - 120, W, 120); }
    TILES.forEach((s, i) => {
      const ta = M.honest - 0.12 + i * 0.035, ap = prog(t, ta, ta + 0.25, E.outBack); if (ap <= 0) return;
      const A = layA(i), B = layB(i), [x, y, w, h] = A.map((v, j) => lerp(v, B[j], lB));
      const sw = s.north ? swingT[s.k] - 0.06 : null, hl = sw ? env(t, sw - 0.05, sw + 1.3, 0.15, 0.4) : 0;
      const dimS = !s.north ? 1 - 0.45 * lB : 1;
      const sc = lerp(0.8, 1, ap) * (1 + 0.05 * hl);
      ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.scale(sc, sc); ctx.globalAlpha = clamp(ap) * dimS;
      ctx.fillStyle = 'rgba(0,0,0,0.4)'; F.round(ctx, -w / 2 + 4, -h / 2 + 8, w, h, 12); ctx.fill();
      ctx.save(); F.round(ctx, -w / 2, -h / 2, w, h, 12); ctx.clip(); ctx.drawImage(s.c, -w / 2, -h / 2, w, h); ctx.restore();
      ctx.strokeStyle = hl > 0 ? `rgba(255,255,255,${0.25 + 0.75 * hl})` : 'rgba(255,255,255,0.22)'; ctx.lineWidth = 2 + 3 * hl; F.round(ctx, -w / 2, -h / 2, w, h, 12); ctx.stroke();
      // needle: base -> tip; all start pointing south; north tiles swing on their word
      const np = prog(t, M.drips - 0.12 + i * 0.03, M.drips + 0.25 + i * 0.03, E.outBack);
      if (np > 0) { const kx = w / TW, bx = -w / 2 + s.b[0] * kx, by = -h / 2 + s.b[1] * kx;
        let ang = s.ang, col = PAL.yellow;
        if (s.north) { const q = prog(t, sw, sw + 0.55, E.outBack); ang = lerp(Math.PI / 2, s.ang < -Math.PI / 2 ? s.ang + 2 * Math.PI : s.ang, q); if (q > 0.5) col = '#dfe6ef'; }
        const L = Math.max(s.len * kx, 60 * kx * 1.67) * clamp(np);
        U.arrow(ctx, bx, by, bx + Math.cos(ang) * L, by + Math.sin(ang) * L, { color: col, width: Math.max(3, 8 * kx * 1.67), head: Math.max(9, 20 * kx * 1.67) });
        F.dot(ctx, bx, by, { r: Math.max(3, 6 * kx * 1.67), color: col }); }
      ctx.restore();
    });
    ctx.restore();
    pillAt(ctx, 'THE HONEST PART', 960 - 170, 92, t, M.honest - 0.1, M.york - 0.45, { size: 42 });
    pillAt(ctx, 'THESE POINT NORTH', 960 - 185, 92, t, M.york - 0.25, Ib + 0.2, { size: 42 });
  }));
  cue(M.honest - 0.12, 'glitch_click', -16);
  for (const k of ['york', 'yuc', 'jut', 'tay']) cue(M[k] - 0.08, 'whoosh_soft', -18);

  // ===================================================================================================
  // J  s091  Antarctic Peninsula -> top-down South Pole: every direction is north
  // ===================================================================================================
  const Ja = Ib, Jb = SEG('s092').start - 0.05;
  scenes.push(gshot({ t0: Ja, t1: Jb, overlay: { canvas: antOv, bounds: WORLD }, patch: null, drift: 0.3,
    keys: [{ t: Ja, lat: -66.0, lon: -64, alt: 0.95, tilt: 36, heading: 22 }, { t: Ja + 2.0, lat: -67.4, lon: -62.5, alt: 0.85, tilt: 40, heading: 26 }, { t: M.north - 0.35, lat: -89.4, lon: -60, alt: 2.15, tilt: 0, heading: 0 }],
    look: (t) => ({ dim: 0.1, desat: 0.15, ovAlpha: 0.85 * prog(t, Ja, Ja + 0.4), relief: 0.9 }),
    extra: (ctx, t, api) => {
      const g = api.g;
      const pa = prog(t, M.antpen + 0.1, M.antpen + 0.8, E.inOut), pf = 1 - prog(t, M.north - 1.6, M.north - 1.0);
      if (pa > 0 && pf > 0) { const pts = projectPath(g, gcLine([-72.0, -66.5], [-63.3, -57.0], 40, 0)); ctx.save(); ctx.globalAlpha = pf; const head = F.glowPath(ctx, pts, { p: pa, color: PAL.yellow, width: 6 }); if (head && pa > 0.9) { const n = pts.length; U.arrow(ctx, pts[n - 4][0], pts[n - 4][1], pts[n - 1][0], pts[n - 1][1], { color: PAL.yellow, width: 6, head: 18 }); } ctx.restore(); }
      if (t > M.north - 0.15) { const q0 = g.project(-90, 0); if (q0.visible) F.dot(ctx, q0.x, q0.y, { r: 9, color: '#ffffff' });
        for (let k = 0; k < 16; k++) { const p = prog(t, M.north - 0.15 + k * 0.012, M.north + 0.45 + k * 0.012, E.outExpo); const lon = k * 22.5; const a = g.project(-86.5, lon), b = g.project(lerp(-86.5, -61, p), lon); if (!a.visible || !b.visible) continue; U.arrow(ctx, a.x, a.y, b.x, b.y, { color: '#ffffff', width: 5, head: 15 }); } }
      pillAt(ctx, 'EVERY DIRECTION: NORTH', 960 - 245, 100, t, M.north - 0.08, Jb + 0.2, { size: 44 });
    } }));
  cue(M.antpen - 0.1, 'whoosh_soft', -18);

  // ===================================================================================================
  // K  s092  Baja: torn from mainland Mexico (slides NW, Gulf of California opens)
  // ===================================================================================================
  const Ka = Jb, Kb = SEG('s093').start - 0.1;
  const slideA = M.baja + 0.5, slideB = slideA + 2.5;
  scenes.push(gshot({ t0: Ka, t1: Kb, overlay: { canvas: gulfOv, bounds: GULF_B }, patch: { url: 'tex/patch/baja.jpg', bounds: [-118, 21, -108, 33] }, drift: 0.25,
    keys: [{ t: Ka, lat: 23, lon: -121, alt: 2.1 }, { t: M.stories - 0.2, lat: 23.6, lon: -119, alt: 1.8 }, { t: M.stories + 3.0, lat: 25.6, lon: -111.6, alt: 0.40, tilt: 42, heading: -16 }],
    look: (t) => ({ dim: 0.3 * prog(t, M.baja - 0.4, M.baja + 0.1), desat: 0.2, ovAlpha: prog(t, slideA + 0.4, slideB) * (0.75 + 0.25 * Math.sin(t * 5)), relief: 0.9 }),
    extra: (ctx, t, api) => {
      const g = api.g; if (t < M.baja - 0.12) return;
      const ap = prog(t, M.baja - 0.12, M.baja + 0.2), p = prog(t, slideA, slideB, E.inOut);
      const R = moveRings(bajaStart, BAJA_Q, BAJA_P, p);
      fillProjected(ctx, g, R, { color: PAL.hero, alpha: 0.8 * ap }); ctx.save(); ctx.globalAlpha = ap; strokeProjected(ctx, g, R, { color: '#ffffff', width: 2.4 }); ctx.restore();
      // Pacific Plate arrow (NW), pulsing; bigger pulse on "going"
      const aa = prog(t, M.baja + 0.35, M.baja + 0.7); if (aa > 0) { const a = g.project(23.6, -113.6), b = g.project(26.9, -118.4); if (a.visible && b.visible) { const pu = 1 + 0.1 * Math.sin(t * 6) + 0.25 * env(t, M.going - 0.1, M.going + 0.9, 0.15, 0.5);
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2; U.arrow(ctx, mx + (a.x - mx) * pu, my + (a.y - my) * pu, mx + (b.x - mx) * pu, my + (b.y - my) * pu, { color: '#ffffff', width: 12, head: 30, alpha: aa }); } }
      pillAt(ctx, 'BAJA: TORN FROM MAINLAND MEXICO', 110, 100, t, M.baja + 0.05, Kb + 0.2);
    } }));
  cue(M.stories - 0.15, 'whoosh_soft', -16); cue(slideA - 0.1, 'rumble_quake', -14);

  // ===================================================================================================
  // L1 s093  Florida highlighted
  // ===================================================================================================
  const L1a = Kb, L1b = M.lime - 0.12;
  scenes.push(gshot({ t0: L1a, t1: L1b, overlay: { canvas: flOv, bounds: FL_B }, patch: { url: 'tex/patch/florida.jpg', bounds: [-88, 23, -78, 31] }, drift: 0.3,
    keys: [{ t: L1a, lat: 26.5, lon: -104, alt: 0.95, tilt: 22 }, { t: L1a + 1.7, lat: 26.6, lon: -82.6, alt: 0.44, tilt: 36, heading: 0 }],
    look: (t) => ({ dim: 0.15, desat: 0.2, ovAlpha: 0.85 * prog(t, M.fla - 0.12, M.fla + 0.35), relief: 0.9 }),
    extra: (ctx, t, api) => { if (t > M.fla) strokeProjected(ctx, api.g, flRings, { p: prog(t, M.fla, M.fla + 0.9, E.out), color: '#ffffff', width: 2.4 }); } }));
  cue(L1a, 'whoosh_soft', -16);

  // ===================================================================================================
  // L2 s093  Florida cross-section: limestone platform, sea life, basement from Africa
  // ===================================================================================================
  const L2a = L1b, L2b = M.wafr - 0.1;
  const SEA = 360, PT = 372, PB = 690, FLOOR = 780;
  const platPoly = [[300, PT], [1590, PT], [1660, FLOOR], [1600, PB + 20], [380, PB + 20], [200, FLOOR]];
  const locator = U.cv(300, 210);
  { const g = locator.getContext('2d'); const s = { lat: 27.3, lon: -82.5, span: 10 }, k = 210 / s.span, cl = Math.cos(s.lat * D2R), dLat = 105 / k, dLon = 150 / (k * cl);
    g.drawImage(day, (s.lon - dLon + 180) / 360 * 8192, (90 - (s.lat + dLat)) / 180 * 4096, 2 * dLon / 360 * 8192, 2 * dLat / 180 * 4096, 0, 0, 300, 210);
    g.fillStyle = 'rgba(5,10,20,0.35)'; g.fillRect(0, 0, 300, 210);
    const X = lo => 150 + (lo - s.lon) * cl * k, Y = la => 105 - (la - s.lat) * k; g.fillStyle = 'rgba(255,90,54,0.75)'; g.beginPath(); for (const r of flRings) { r.forEach(([lo, la], i) => i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))); g.closePath(); } g.fill();
    g.strokeStyle = PAL.yellow; g.lineWidth = 4; g.setLineDash([10, 6]); g.beginPath(); g.moveTo(X(-86.5), Y(27.2)); g.lineTo(X(-78.6), Y(27.2)); g.stroke(); }
  scenes.push(scene(L2a, L2b, (ctx, t) => {
    const k = 1 + 0.05 * prog(t, L2a, L2b); ctx.save(); ctx.translate(W / 2, 560); ctx.scale(k, k); ctx.translate(-W / 2, -560);
    const sky = ctx.createLinearGradient(0, 0, 0, SEA); sky.addColorStop(0, '#07101f'); sky.addColorStop(1, '#16324f'); ctx.fillStyle = sky; ctx.fillRect(0, 0, W, SEA);
    const wat = ctx.createLinearGradient(0, SEA, 0, FLOOR); wat.addColorStop(0, '#1d6f9c'); wat.addColorStop(1, '#0a2440'); ctx.fillStyle = wat; ctx.fillRect(0, SEA, W, FLOOR - SEA + 4);
    ctx.fillStyle = '#0b0d14'; ctx.fillRect(0, FLOOR, W, H - FLOOR); ctx.fillRect(380, PB, 1220, FLOOR - PB);
    // basement (revealed on "under"), glows near "West Africa"
    const bp = prog(t, M.under - 0.12, M.under + 0.9, E.inOut);
    if (bp > 0) { ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W * bp, H); ctx.clip(); const bg = ctx.createLinearGradient(0, PB, 0, H); bg.addColorStop(0, '#6a3530'); bg.addColorStop(1, '#2a1416'); ctx.fillStyle = bg; ctx.fillRect(0, PB + 10, W, H - PB);
      const r = F.rng(9); ctx.fillStyle = 'rgba(255,200,180,0.18)'; for (let i = 0; i < 260; i++) { ctx.fillRect(r() * W, PB + 20 + r() * (H - PB - 20), 3 + r() * 5, 2 + r() * 3); }
      const gl = prog(t, M.wafr - 1.1, M.wafr - 0.3) * (0.7 + 0.3 * Math.sin(t * 6)); if (gl > 0) { const gg = ctx.createLinearGradient(0, PB, 0, PB + 140); gg.addColorStop(0, `rgba(255,140,60,${0.55 * gl})`); gg.addColorStop(1, 'rgba(255,140,60,0)'); ctx.fillStyle = gg; ctx.fillRect(0, PB + 10, W, 140); ctx.strokeStyle = `rgba(255,190,120,${gl})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(0, PB + 12); ctx.lineTo(W, PB + 12); ctx.stroke(); }
      ctx.restore(); }
    // limestone platform rises (strata stack up from the bottom)
    const rp = prog(t, M.lime - 0.12, M.lime + 2.2, E.outExpo), top = lerp(PB + 20, PT, rp);
    if (rp > 0) { ctx.save(); ctx.beginPath(); ctx.rect(0, top, W, H); ctx.clip(); const lg = ctx.createLinearGradient(0, PT, 0, PB); lg.addColorStop(0, '#f1e6c4'); lg.addColorStop(1, '#c9b386'); ctx.fillStyle = lg; ctx.beginPath(); U.polyPath(ctx, platPoly); ctx.fill();
      ctx.save(); ctx.beginPath(); U.polyPath(ctx, platPoly); ctx.clip(); ctx.strokeStyle = 'rgba(120,95,55,0.35)'; ctx.lineWidth = 2; for (let y = PT + 24; y < PB + 20; y += 26) { ctx.beginPath(); for (let x = 150; x <= 1700; x += 30) { const yy = y + 3 * Math.sin(x / 90 + y); x === 150 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy); } ctx.stroke(); } ctx.restore();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2.5; ctx.beginPath(); U.polyPath(ctx, platPoly); ctx.stroke(); ctx.restore(); }
    // the peninsula above sea level
    ctx.fillStyle = PAL.hero; ctx.beginPath(); ctx.moveTo(800, SEA + 2); ctx.quadraticCurveTo(820, SEA - 16, 860, SEA - 18); ctx.lineTo(1080, SEA - 18); ctx.quadraticCurveTo(1120, SEA - 16, 1140, SEA + 2); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, SEA); ctx.lineTo(800, SEA); ctx.moveTo(1140, SEA); ctx.lineTo(W, SEA); ctx.stroke();
    // shallow-water sea life
    [[470, 0], [640, 1], [730, 0], [1230, 1], [1380, 0], [1500, 1]].forEach(([x, kind], i) => { const a = prog(t, M.sealife - 0.12 + i * 0.1, M.sealife + 0.2 + i * 0.1, E.outBack); if (a <= 0) return; const bob = 3 * Math.sin(t * 2 + i);
      if (kind) U.coralIcon(ctx, x, PT - 4 + bob * 0.2, a * 1.2, 1); else U.shellIcon(ctx, x, PT - 14 + bob * 0.2, a * 0.8, 1); });
    ctx.restore();
    // locator inset
    const la = prog(t, L2a + 0.2, L2a + 0.6); if (la > 0) { ctx.save(); ctx.globalAlpha = la; ctx.fillStyle = 'rgba(0,0,0,0.45)'; F.round(ctx, 1514, 76, 312, 222, 14); ctx.fill(); ctx.save(); F.round(ctx, 1520, 70, 300, 210, 12); ctx.clip(); ctx.drawImage(locator, 1520, 70); ctx.restore(); ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2; F.round(ctx, 1520, 70, 300, 210, 12); ctx.stroke(); ctx.restore(); }
    pillAt(ctx, 'FLORIDA: A GIANT LIMESTONE PLATFORM', 110, 100, t, M.lime - 0.1, L2b + 0.2);
  }));
  cue(M.lime - 0.1, 'whoosh_soft', -18); cue(M.sealife - 0.1, 'pop_ui', -18);

  // ===================================================================================================
  // LM s093-s094  arc Florida -> West Africa (+ moving truck), then fly to the Cape; Good Hope vs Agulhas
  // ===================================================================================================
  const LMa = L2b, LMb = M.agul - 0.07;
  const FLA = [26.0, -81.2], WAF = [12.6, -16.4], GH = [-34.36, 18.48], AG = [-34.83, 20.0];
  const flyA = SEG('s094').start - 0.3;
  scenes.push(gshot({ t0: LMa, t1: LMb, overlay: { canvas: flOv, bounds: FL_B }, patch: { url: 'tex/patch/s_africa.jpg', bounds: [10, -37, 36, -20] }, drift: 0.3,
    keys: [{ t: LMa, lat: 21, lon: -50, alt: 2.4 }, { t: flyA, lat: 19, lon: -45, alt: 2.3 }, { t: M.gh - 0.25, lat: -34.0, lon: 19.3, alt: 0.30, tilt: 38, heading: 6 }],
    look: (t) => ({ dim: 0.12, desat: 0.2, ovAlpha: 0.9, relief: 0.85 }),
    extra: (ctx, t, api) => {
      const g = api.g;
      const fade = 1 - prog(t, flyA + 0.1, flyA + 0.6);
      if (fade > 0) {
        const pts = projectPath(g, gcLine(FLA, WAF, 90, 0.06));
        const ap = prog(t, M.wafr - 0.08, M.wafr + 1.6, E.inOut);
        ctx.save(); ctx.globalAlpha = fade;
        const head = F.glowPath(ctx, pts, { p: ap, color: PAL.cyan, width: 4.5, dash: [3, 12] }); if (head && ap < 1) F.dot(ctx, head[0], head[1], { r: 7, color: PAL.cyan });
        if (ap >= 1) { const q = g.project(WAF[0], WAF[1]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 9, color: PAL.yellow, ring: (t * 0.8) % 1 }); }
        // moving truck pulls up at the Florida end
        const tp = prog(t, M.else - 1.55, M.else - 0.02, E.inOut);
        if (tp > 0 && pts.length > 2) { const q = U.polyAt(pts.slice().reverse(), tp); const bounce = t > M.else ? 4 * Math.exp(-6 * (t - M.else)) * Math.sin((t - M.else) * 25) : 0; U.truck(ctx, q.x, q.y - 26 + bounce, q.a, 1.05, prog(t, M.else - 1.55, M.else - 1.35)); }
        ctx.restore();
        pillAt(ctx, 'ITS BEDROCK: BORN NEXT TO AFRICA', 110, 100, t, M.wafr + 0.1, flyA + 0.3);
      }
      // the Cape: Good Hope marker, hop to Agulhas, latitude line
      if (t > M.gh - 0.12) {
        const lp = prog(t, M.gh + 0.15, M.gh + 0.7, E.inOut); if (lp > 0) { const run = projectPath(g, Array.from({ length: 41 }, (_, i) => ({ lat: AG[0], lon: 16.8 + i * 0.13 }))); ctx.save(); ctx.globalAlpha = 0.85; F.glowPath(ctx, run, { p: lp, color: '#ffffff', width: 2.5, dash: [10, 8] }); ctx.restore(); }
        const q = g.project(GH[0], GH[1]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 9, color: '#ffffff', ring: ((t - M.gh) * 0.9) % 1 });
        const hp = prog(t, M.gh + 0.05, M.gh + 0.6, E.inOut); if (hp > 0) { const pts = projectPath(g, gcLine(GH, AG, 30, 0.004)); const head = F.glowPath(ctx, pts, { p: hp, color: '#ffffff', width: 3.5, dash: [8, 8] });
          if (hp >= 1) { const a2 = g.project(AG[0], AG[1]); if (a2.visible) F.dot(ctx, a2.x, a2.y, { r: 10, color: PAL.hero, ring: ((t - M.gh) * 1.1) % 1 }); } }
      }
    } }));
  cue(flyA, 'whoosh_soft', -14); cue(M.else - 1.5, 'whoosh_soft', -20);

  // ===================================================================================================
  // M2 s094  ASTER view of Cape Agulhas
  // ===================================================================================================
  const M2a = LMb, M2b = M.compass - 0.12;
  const aster = api.img(IMG('cape_agulhas_aster.jpg'));
  const KBf = [0.5, 0.55, 1.04], KBt = [0.47, 0.72, 1.3];
  scenes.push(scene(M2a, M2b, (ctx, t) => {
    const u = (t - M2a) / (M2b - M2a);
    ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
    const k = E.inOutSine(clamp(u)), cxn = lerp(KBf[0], KBt[0], k), cyn = lerp(KBf[1], KBt[1], k), z = lerp(KBf[2], KBt[2], k);
    const iw = aster.width, ih = aster.height, sh = ih / z, sw = sh * (W / H); let sx = clamp(cxn * iw - sw / 2, 0, iw - sw), sy = clamp(cyn * ih - sh / 2, 0, ih - sh);
    const LIFT = 130;
    F.kenburns(ctx, aster, u, 0, -LIFT, W, H, { from: KBf, to: KBt, grade: 'cold' });
    // extend the sea into the vacated band: a gradient from the plate's own bottom-edge colour (no smear, no mirrored land)
    { const d = ctx.getImageData(0, H - LIFT - 6, W, 4).data; let r = 0, gg = 0, b = 0, n = 0; for (let q = 0; q < d.length; q += 32) { r += d[q]; gg += d[q + 1]; b += d[q + 2]; n++; }
      r /= n; gg /= n; b /= n; const bg = ctx.createLinearGradient(0, H - LIFT, 0, H); bg.addColorStop(0, `rgb(${r | 0},${gg | 0},${b | 0})`); bg.addColorStop(1, `rgb(${(r * 0.55) | 0},${(gg * 0.6) | 0},${(b * 0.7) | 0})`);
      ctx.fillStyle = bg; ctx.fillRect(0, H - LIFT, W, LIFT); }
    { const jg = ctx.createLinearGradient(0, H - LIFT - 60, 0, H - LIFT + 60); jg.addColorStop(0, 'rgba(5,10,20,0)'); jg.addColorStop(0.5, 'rgba(5,10,20,0.35)'); jg.addColorStop(1, 'rgba(5,10,20,0)'); ctx.fillStyle = jg; ctx.fillRect(0, H - LIFT - 60, W, 120); }
    ctx.fillStyle = 'rgba(5,10,20,0.18)'; ctx.fillRect(0, 0, W, H);
    // tip marker (replicates the Ken Burns crop)
    const px = (0.452 * iw - sx) / sw * W, py = (0.908 * ih - sy) / sh * H - LIFT;
    F.dot(ctx, px, py, { r: 10, color: PAL.hero, ring: ((t - M2a) * 0.8) % 1 });
    pillAt(ctx, 'REAL TIP: CAPE AGULHAS', 110, 100, t, M.agul - 0.1, M2b + 0.2);
    pillAt(ctx, 'AGULHAS = "NEEDLES"', 110, 180, t, M.needles - 0.1, M2b + 0.2, { border: PAL.yellow });
  }, { fadeIn: 0.12 }));

  // ===================================================================================================
  // M3 s094  compass at Africa's southern tip spins, then settles on north
  // ===================================================================================================
  const M3a = M2b, M3b = SEG('s095').start - 0.12;
  const CR = 125, compassC = U.compassCanvas(CR);
  scenes.push(gshot({ t0: M3a, t1: M3b, overlay: null, patch: { url: 'tex/patch/s_africa.jpg', bounds: [10, -37, 36, -20] }, drift: 0.2,
    keys: [{ t: M3a, lat: -32.6, lon: 20.2, alt: 0.55, tilt: 30, heading: -4 }, { t: M3b, lat: -29.5, lon: 21.5, alt: 1.15, tilt: 18, heading: 4 }],
    look: { dim: 0.18, desat: 0.2, relief: 0.9 },
    extra: (ctx, t, api) => {
      const g = api.g, q = g.project(AG[0], AG[1]), qn = g.project(AG[0] + 1.5, AG[1]); if (!q.visible) return;
      F.dot(ctx, q.x, q.y, { r: 9, color: PAL.hero });
      const northA = Math.atan2(qn.y - q.y, qn.x - q.x) + Math.PI / 2;
      const ap = E.outBack(prog(t, M.compass - 0.2, M.compass + 0.15)); if (ap <= 0) return;
      const cx = q.x, cy = q.y - CR - 30;
      const tc = M.compass - 0.05, tn = M.north2 - 0.06, uu = clamp((t - tc) / (tn - tc));
      let ang = northA + Math.pow(1 - uu, 1.6) * (5 * Math.PI * (1 - uu) + 1.3 * Math.sin(uu * 15));
      if (t > tn) ang = northA + 0.18 * Math.exp(-5 * (t - tn)) * Math.sin((t - tn) * 22);
      ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 2; ctx.setLineDash([5, 6]); ctx.beginPath(); ctx.moveTo(q.x, q.y); ctx.lineTo(cx, cy + CR * ap); ctx.stroke(); ctx.restore();
      ctx.save(); ctx.translate(cx, cy); ctx.scale(ap, ap); ctx.rotate(northA); ctx.drawImage(compassC, -compassC.width / 2, -compassC.height / 2); ctx.restore();
      U.compassNeedle(ctx, cx, cy, CR * ap, ang);
      const fl = env(t, tn, tn + 1.0, 0.05, 0.8); if (fl > 0) { ctx.save(); ctx.globalAlpha = fl; ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(cx, cy, CR + 14 + 30 * (1 - fl), 0, 7); ctx.stroke(); ctx.restore(); }
    } }));
  cue(M.north2 - 0.05, 'bell_small', -16);

  // ===================================================================================================
  // N1 s095  the cold-open coin spins up again -> lands on its edge -> JUICE CHECK: IT'S COMPLICATED
  // ===================================================================================================
  const N1a = M3b, N1b = M.likely + 2.25;
  const stampC = U.stampCanvas('JUICE CHECK', "IT'S COMPLICATED", PAL.yellow, 5);
  const coinT0 = M.coin2 - 0.15, rate = Math.PI * 3;
  const coinPhase = (t) => { const tl = M.likely - 0.25; if (t < tl) return rate * (t - coinT0); const pl = rate * (tl - coinT0), tgt = (Math.floor(pl / Math.PI) + 1) * Math.PI + Math.PI / 2, u = (t - tl) / 0.7;
    return lerp(pl, tgt, E.outExpo(clamp(u))) + 0.12 * Math.exp(-4 * Math.max(0, u)) * Math.sin(Math.max(0, u) * 20); };
  scenes.push(gshot({ t0: N1a, t1: N1b, overlay: { canvas: dripOv, bounds: WORLD }, patch: null, drift: 1.2,
    keys: [{ t: N1a, lat: -30, lon: 20, alt: 3.0 }, { t: N1b, lat: -30, lon: 16, alt: 2.9 }],
    look: (t) => ({ desat: 0.3, dim: 0.35 + 0.2 * prog(t, M.coin2 - 0.2, M.coin2 + 0.3), ovAlpha: 1, relief: 0.7 }),
    extra: (ctx, t, api) => {
      const [sx, sy] = U.shake(t, M.likely - 0.03, 10);
      ctx.save(); ctx.translate(sx, sy);
      const ca = E.outBack(prog(t, coinT0, coinT0 + 0.35)); if (ca > 0) { const lean = t > M.likely ? 0.16 * Math.exp(-1.5 * (t - M.likely)) * Math.sin((t - M.likely) * 6) : 0; if (t > M.likely - 0.2) { ctx.save(); ctx.globalAlpha = 0.45 * prog(t, M.likely - 0.2, M.likely + 0.1); ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(960, 806, 100, 12, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore(); } ctx.save(); ctx.translate(960, 640); ctx.rotate(lean); U.coin(ctx, 0, 0, 160 * ca, coinPhase(t)); ctx.restore(); }
      U.drawStamp(ctx, stampC, 1230, 290, t, M.likely - 0.08, { scale: 0.66, rot: -0.07 });
      ctx.restore();
    } }));
  cue(M.coin2 - 0.12, 'bell_small', -16); cue(M.likely - 0.06, 'stamp', -10);

  // ===================================================================================================
  // N2 s095  scars glow: seam lines from the three big drips to Antarctica
  // ===================================================================================================
  const N2a = N1b, N2b = SEG('s095').start + 9.95;
  scenes.push(gshot({ t0: N2a, t1: N2b, overlay: { canvas: dripOv, bounds: WORLD }, patch: null, drift: 0.6,
    keys: [{ t: N2a, lat: -55, lon: 15, alt: 3.2, heading: 8 }, { t: N2b, lat: -58, lon: 12, alt: 3.1, heading: 8 }],
    look: { desat: 0.3, dim: 0.35, ovAlpha: 0.85, relief: 0.7 },
    extra: (ctx, t, api) => {
      const g = api.g; drawRing(ctx, g, t, null);
      TR3.forEach(([n, tip], i) => { const pts = [{ lat: tip[0], lon: tip[1] }, ...U.trackPts(tracks, n, 0, 180)];
        const st = M.v_ant - 0.12 + i * 0.12, p = prog(t, st, st + 0.9, E.inOut);
        for (const run of U.projRuns(g, pts)) { ctx.save(); ctx.globalAlpha = 0.55 * (1 - p); F.glowPath(ctx, run, { p: 1, color: PAL.yellow, width: 4, dash: [2, 13] }); ctx.restore(); if (p > 0) U.scarLine(ctx, run, p, { width: 4.5 }); } });
    } }));
  cue(N2a, 'whoosh_soft', -18);

  // ===================================================================================================
  // N3 s095  small drips: own icons (Baja tear-away, Florida shell, Greenland ?) -> connecting dots
  // ===================================================================================================
  const N3a = N2b, N3b = SEG('s096').start + 0.45;
  const SMALL = [[22.88, -109.9], [25.12, -81.08], [59.77, -43.9], [21.6, -87.1], [35.2, -75.5], [43.4, -65.6], [15.0, -83.2], [50.9, 156.7]];
  const constel = [0, 3, 1, 4, 5, 2];
  scenes.push(gshot({ t0: N3a, t1: N3b, overlay: { canvas: dripOv, bounds: WORLD }, patch: null, drift: 0.4,
    keys: [{ t: N3a, lat: 30, lon: -84, alt: 2.35 }, { t: N3b, lat: 31, lon: -89, alt: 2.25 }],
    look: { desat: 0.3, dim: 0.4, ovAlpha: 0.6, relief: 0.7 },
    extra: (ctx, t, api) => {
      const g = api.g, fl = (t0) => t < t0 ? 0 : t < t0 + 0.4 ? (Math.sin((t - t0) * 70) > -0.2 ? 1 : 0.25) : 1;
      const icons = [['baja', SMALL[0]], ['fla', SMALL[1]], ['grl', SMALL[2]]];
      icons.forEach(([k, ll], i) => { const a = fl(M.single - 0.15 + i * 0.18) * (1 - prog(t, M.dots + 0.2, M.dots + 0.7)); if (a <= 0) return; const q = g.project(ll[0], ll[1]); if (!q.visible) return;
        F.dot(ctx, q.x, q.y, { r: 7, color: '#ffffff' }); ctx.save(); ctx.globalAlpha *= a;
        if (k === 'baja') { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(q.x - 20, q.y - 30, 46, 0.4, 2.2); ctx.stroke(); U.arrow(ctx, q.x - 50, q.y + 5, q.x - 78, q.y - 22, { color: '#ffffff', width: 5, head: 14, glow: false }); }
        if (k === 'fla') U.shellIcon(ctx, q.x + 50, q.y + 10, 1.0, 1, '#ffffff');
        if (k === 'grl') { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(q.x + 46, q.y - 34, 26, 0, 7); ctx.stroke(); F.text(ctx, '?', q.x + 46, q.y - 34, { size: 38, fam: F.FAM.head, align: 'center', baseline: 'middle', shadow: false }); }
        ctx.restore(); });
      // connecting dots
      const dp = prog(t, M.dots - 0.12, M.dots + 0.55, E.inOut), da = 1 - prog(t, N3b - 0.55, N3b - 0.1);
      if (dp > 0 && da > 0) { const pts = constel.map(i => g.project(SMALL[i][0], SMALL[i][1])).filter(q => q.visible).map(q => [q.x, q.y]);
        ctx.save(); ctx.globalAlpha = da; F.glowPath(ctx, pts, { p: dp, color: '#ffffff', width: 2.5, dash: [3, 9] }); pts.forEach(([x, y], i) => { if (i / (pts.length - 1) <= dp + 0.01) F.dot(ctx, x, y, { r: 5, color: '#ffffff' }); }); ctx.restore(); }
    } }));
  cue(M.single - 0.12, 'glitch_click', -20);

  // ===================================================================================================
  // O1 s096  lopsided planet: northern land flashes
  // ===================================================================================================
  const O1a = N3b, O1b = M.northl + 0.66;
  scenes.push(gshot({ t0: O1a, t1: O1b, overlay: { canvas: northOv, bounds: WORLD }, patch: null, drift: 1.5,
    keys: [{ t: O1a, lat: 34, lon: 34, alt: 2.9 }, { t: O1b, lat: 36, lon: 14, alt: 2.8 }],
    look: (t) => { const f = prog(t, M.lopside - 0.1, M.lopside + 0.05), d = 1 - prog(t, M.lopside + 0.05, M.lopside + 0.7); return { dim: 0.25, desat: 0.25, ovAlpha: f * (0.75 + 0.25 * d), relief: 0.8, exposure: 1.25 + 0.4 * f * d }; } }));
  cue(O1a, 'whoosh_soft', -18);

  // ===================================================================================================
  // O2/O4 s096  equatorial slice with two plumes; grey "north" force arrow gets a red X
  // ===================================================================================================
  const afr = await region('africa'); const afrR = allRings(afr).filter(r => r.length > 30);
  const afrIcon = U.cv(200, 220); { const g = afrIcon.getContext('2d'); let mnx = 1e9, mny = 1e9, mxx = -1e9, mxy = -1e9; for (const r of afrR) for (const [lo, la] of r) { mnx = Math.min(mnx, lo); mxx = Math.max(mxx, lo); mny = Math.min(mny, la); mxy = Math.max(mxy, la); }
    const s = Math.min(180 / (mxx - mnx), 200 / (mxy - mny)); g.fillStyle = '#f4f6fa'; g.beginPath(); for (const r of afrR) { r.forEach(([lo, la], i) => { const x = 10 + (lo - mnx) * s, y = 10 + (mxy - la) * s; i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); } g.fill(); }
  const drawSlice = (ctx, t, a0) => {
    ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H); U.spaceBg(ctx, t, { starAlpha: 0.5, c0: '#101a30' });
    const ap = E.outBack(prog(t, a0 - 0.12, a0 + 0.4)), R = 360 * ap, cx = 960, cy = 560, rot = (t - a0) * 0.025;
    if (R <= 1) return;
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot);
    const gl = ctx.createRadialGradient(0, 0, R * 0.9, 0, 0, R * 1.25); gl.addColorStop(0, 'rgba(255,120,60,0.25)'); gl.addColorStop(1, 'rgba(255,120,60,0)'); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(0, 0, R * 1.25, 0, 7); ctx.fill();
    const mg = ctx.createRadialGradient(0, 0, R * 0.55, 0, 0, R); mg.addColorStop(0, '#c4502a'); mg.addColorStop(1, '#7a2a1a'); ctx.fillStyle = mg; ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.fill();
    // plumes (Africa side up, Pacific side down)
    for (const [dir, ph] of [[-Math.PI / 2, 0], [Math.PI / 2, 1.7]]) { ctx.save(); ctx.rotate(dir + Math.PI / 2);
      const wv = (y) => 6 * Math.sin(y / 30 + t * 1.6 + ph); const r0 = R * 0.546, r1 = R * (0.86 + 0.02 * Math.sin(t * 1.2 + ph));
      const pg = ctx.createLinearGradient(0, -r0, 0, -r1); pg.addColorStop(0, 'rgba(255,200,90,0.95)'); pg.addColorStop(1, 'rgba(255,150,60,0.85)'); ctx.fillStyle = pg;
      ctx.beginPath(); ctx.moveTo(-R * 0.36, -r0 + 10); ctx.bezierCurveTo(-R * 0.16 + wv(0), -r0 - R * 0.05, -R * 0.1 + wv(40), -r1 + R * 0.12, -R * 0.24, -r1 + R * 0.04);
      ctx.bezierCurveTo(-R * 0.28, -r1 - R * 0.04, R * 0.28, -r1 - R * 0.04, R * 0.24, -r1 + R * 0.04); ctx.bezierCurveTo(R * 0.1 + wv(80), -r1 + R * 0.12, R * 0.16 + wv(20), -r0 - R * 0.05, R * 0.36, -r0 + 10); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = 'rgba(255,240,200,0.35)'; ctx.lineWidth = 3; for (let i = 0; i < 3; i++) { const f = ((t * 0.35 + i / 3 + ph) % 1); const y = lerp(-r0, -r1 + R * 0.05, f); ctx.globalAlpha = Math.sin(Math.PI * f); ctx.beginPath(); ctx.moveTo(-R * 0.08, y); ctx.quadraticCurveTo(0, y - 14, R * 0.08, y); ctx.stroke(); } ctx.globalAlpha = 1;
      ctx.restore(); }
    const oc = ctx.createRadialGradient(0, 0, R * 0.1, 0, 0, R * 0.546); oc.addColorStop(0, '#ffd27a'); oc.addColorStop(1, '#e88a1c'); ctx.fillStyle = oc; ctx.beginPath(); ctx.arc(0, 0, R * 0.546, 0, 7); ctx.fill();
    ctx.fillStyle = '#fff3c4'; ctx.beginPath(); ctx.arc(0, 0, R * 0.192, 0, 7); ctx.fill();
    ctx.strokeStyle = '#8a6a48'; ctx.lineWidth = 10 * ap; ctx.beginPath(); ctx.arc(0, 0, R - 5, 0, 7); ctx.stroke();
    // rim silhouettes: Africa on top of one plume, Pacific islands over the other
    ctx.save(); ctx.translate(0, -R - 4); ctx.drawImage(afrIcon, -42 * ap, -96 * ap, 84 * ap, 92 * ap); ctx.restore();
    ctx.save(); ctx.rotate(Math.PI); ctx.fillStyle = '#f4f6fa'; for (const [x, s] of [[-40, 14], [-8, 22], [26, 12], [52, 9]]) { ctx.beginPath(); ctx.moveTo(x * ap - s * ap, -R - 2); ctx.lineTo(x * ap, -R - 2 - s * 1.3 * ap); ctx.lineTo(x * ap + s * ap, -R - 2); ctx.closePath(); ctx.fill(); } ctx.restore();
    ctx.restore();
  };
  const O2b = O1b, O3b = M.avoid2 + 0.5;
  scenes.push(scene(O2b, O3b, (ctx, t) => {
    U.spaceBg(ctx, t, { starAlpha: 0.5 }); const z = lerp(0.98, 1.03, prog(t, O2b, O3b)); const T = drawEE(ctx, { cx: 1800, cy: 880, zoom: z }, 0.42);
    ctx.save(); ctx.globalAlpha = 0.95; ctx.drawImage(antiEE, T.ox, T.oy, U.EE_W * T.z, U.EE_H * T.z); ctx.restore();
  }));
  scenes.push(scene(O3b, M.snap - 0.05, (ctx, t) => {
    drawSlice(ctx, t, O3b);
    const fa = prog(t, M.force - 0.12, M.force + 0.35); if (fa > 0) { U.arrow(ctx, 960, 760, 960, 300, { color: '#9aa7b8', width: 26, head: 48, alpha: 0.92 * fa }); }
    const xa = M.force + 0.62; for (const [i, [x0, y0, x1, y1]] of [[860, 420, 1060, 640], [1060, 420, 860, 640]].entries()) { const p = prog(t, xa + i * 0.16, xa + i * 0.16 + 0.16, E.out); if (p <= 0) continue; ctx.save(); ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 30; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0 + 3, y0 + 5); ctx.lineTo(lerp(x0, x1, p) + 3, lerp(y0, y1, p) + 5); ctx.stroke(); ctx.strokeStyle = PAL.danger; ctx.lineWidth = 24; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(lerp(x0, x1, p), lerp(y0, y1, p)); ctx.stroke(); ctx.restore(); }
  }));
  cue(M.force + 0.6, 'thunk_heavy', -16);

  // ===================================================================================================
  // P  s096  shutter: the drip globe frozen in a Polaroid -> NOT A FORCE. A SNAPSHOT.
  // ===================================================================================================
  let snapC = null;
  const getSnap = () => {
    if (snapC) return snapC;
    const g = api.g; g.setOverlay(dripOv, WORLD); g.u.tint.value.set(1, 1, 1);
    const tmp = U.cv(W, H), tc = tmp.getContext('2d');
    api.drawGlobe(tc, { lat: -30, lon: 20, alt: 3.6, tilt: 0, heading: 0 }, Object.assign({}, BASE_LOOK, { desat: 0.3, dim: 0.3, ovAlpha: 1, relief: 0.8, nightAmt: 1, exposure: 1.25 }));
    // the ring + '?' of the cold open on the South Pole
    const q = g.project(-90, 0); if (q.visible) { tc.strokeStyle = PAL.yellow; tc.lineWidth = 6; tc.beginPath(); tc.ellipse(q.x, q.y, 70, 36, 0, 0, 7); tc.stroke(); }
    api._ovOwner = null; // force the next globe shot to reinstall its own overlay
    snapC = U.cv(1000, 1000); snapC.getContext('2d').drawImage(tmp, 460, 40, 1000, 1000, 0, 0, 1000, 1000);
    return snapC;
  };
  const Pa = M.snap - 0.05, Pb = t1;
  scenes.push(scene(Pa, Pb, (ctx, t) => {
    const S = getSnap(); const u = prog(t, Pa, Pb);
    ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = 0.35; const bz = lerp(1.25, 1.5, u); ctx.drawImage(S, W / 2 - 540 * bz, H / 2 - 540 * bz, 1080 * bz, 1080 * bz); ctx.restore();
    ctx.fillStyle = 'rgba(3,5,10,0.55)'; ctx.fillRect(0, 0, W, H);
    const PSZ = 590, B = 26, BB = 128, cw = PSZ + 2 * B, ch = PSZ + B + BB;
    const ip = prog(t, Pa, Pa + 0.45, E.outExpo);
    ctx.save(); ctx.translate(960, 520 + lerp(30, 0, ip)); ctx.rotate(lerp(-0.09, -0.035, ip) + 0.035 * u); const sc = lerp(1.08, 1.0, ip) * (1 + 0.08 * u); ctx.scale(sc, sc);
    ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(-cw / 2 + 10, -ch / 2 + 18, cw, ch);
    ctx.fillStyle = '#f6f4ee'; ctx.fillRect(-cw / 2, -ch / 2, cw, ch);
    const px = -cw / 2 + B, py = -ch / 2 + B; ctx.drawImage(S, 80, 80, 840, 840, px, py, PSZ, PSZ);
    const dev = 1 - prog(t, Pa + 0.1, Pa + 1.1); if (dev > 0) { ctx.fillStyle = `rgba(235,240,230,${0.85 * dev})`; ctx.fillRect(px, py, PSZ, PSZ); }
    const cp = prog(t, M.snap + 0.3, M.snap + 0.9, E.inOut);
    if (cp > 0) { ctx.save(); ctx.beginPath(); ctx.rect(-cw / 2, py + PSZ, cw * cp, BB + B); ctx.clip(); F.text(ctx, 'NOT A FORCE. A SNAPSHOT.', 0, py + PSZ + BB * 0.62, { size: 54, fam: F.FAM.label, weight: 800, color: '#1b2230', align: 'center', tracking: 0.04, shadow: false }); ctx.restore(); }
    ctx.restore();
    const fl = U.flash(t, M.snap, 0.4); if (fl > 0) { ctx.fillStyle = `rgba(255,255,255,${fl})`; ctx.fillRect(0, 0, W, H); }
  }));
  cue(M.snap - 0.02, 'glitch_click', -12);

  return scenes;
}
