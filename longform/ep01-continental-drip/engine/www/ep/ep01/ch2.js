// Module ch2 — Chapter 2 "What's on Earth's other side?" (s025–s044).
// Modes: globe (Arctic fly-in, drag, top-down antipode, China/Kansas, Saint-Paul, caps, flip, Pacific pour, drip callback),
// 3D dioramas (floe gag, tiny-planet dig gags, cut-away drills, tetra-in-globe), 2D profile panels, polar discs,
// Equal Earth flat maps (US/China antipodes, antipode overlay), waffle data card, 2x3 cap tiles, montage.
import * as F from '../../lib/fx.js';
import { camAt } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, makeCanvas, fillEquirect, gcLine, projectPath } from '../../lib/geo.js';
import { region } from '../../lib/beats.js';
import * as L from './ch2_lib.js';
import { makeSets } from './ch2_sets.js';
const { PAL, prog, env, E, clamp, lerp } = F;
const W = 1920, H = 1080;
const IMG = 'ep/ep01/img/';
const LOOK0 = { dim: 0, desat: 0.12, ovAlpha: 0, relief: 0.8, nightAmt: 1, exposure: 1.25, ambient: 0.10, flatBase: 0, ovMul: 0, specAmt: 0.5, rimAmt: 0.35 };
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };

// ---------- globe scene helper (owns overlay/patch state explicitly; full look reset every frame) ----------
function gscene(o) {
  return {
    t0: o.t0, t1: o.t1, layer: o.layer || 0, fadeIn: o.fadeIn || 0, fadeOut: 0, id: 'ch2',
    async draw(ctx, lt, t, api) {
      const g = api.g;
      if (api._patchOwner !== 'ch2') { await g.setPatch(null); api._patchOwner = 'ch2'; }
      const key = o.ovKey || 'ch2:none';
      if (api._ovOwner !== key) { if (o.install) await o.install(g, api); else g.setOverlay(null); api._ovOwner = key; }
      if (o.clip) { ctx.save(); o.clip(ctx, lt, t); }
      if (o.pre) await o.pre(lt, t, g);
      const cam = o.cam(lt, t);
      api.drawGlobe(ctx, Object.assign({ starAlpha: 1 }, cam), Object.assign({}, LOOK0, o.look ? o.look(lt, t) : {}));
      if (o.draw2d) { const pj = L.projector(g); await o.draw2d(ctx, lt, t, pj, g); }
      if (o.clip) ctx.restore();
    },
  };
}

// ---------- hemisphere cap overlay (land-aware), regenerated only when its parameters change ----------
class Cap {
  constructor(landImg, w = 1024, h = 512) {
    this.w = w; this.h = h; this.cv = makeCanvas(w, h); this.g = this.cv.getContext('2d', { willReadFrequently: true });
    this.g.drawImage(landImg, 0, 0, w, h); const d = this.g.getImageData(0, 0, w, h).data;
    this.land = new Float32Array(w * h); this.xyz = new Float32Array(w * h * 3);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x; this.land[i] = d[i * 4] / 255;
      const v = L.dir(90 - (y + 0.5) / h * 180, -180 + (x + 0.5) / w * 360); this.xyz[i * 3] = v[0]; this.xyz[i * 3 + 1] = v[1]; this.xyz[i * 3 + 2] = v[2];
    }
    this.id = this.g.createImageData(w, h); this.sig = '';
  }
  // c: unit vector; o: {inL, inO, outL, outO, edge} colours [r,g,b,a(0..1)], edgeW
  draw(c, o) {
    const sig = c.map(v => v.toFixed(4)).join(',') + JSON.stringify(o);
    if (sig === this.sig) return false; this.sig = sig;
    const D = this.id.data, n = this.w * this.h, ew = o.edgeW ?? 0.011;
    const inL = o.inL, inO = o.inO, outL = o.outL, outO = o.outO, ed = o.edge || [255, 255, 255, 0.95];
    const [cx, cy, cz] = c;
    for (let i = 0; i < n; i++) {
      const dt = this.xyz[i * 3] * cx + this.xyz[i * 3 + 1] * cy + this.xyz[i * 3 + 2] * cz, l = this.land[i];
      const A = dt > 0 ? inL : outL, B = dt > 0 ? inO : outO;
      let r = B[0] + (A[0] - B[0]) * l, g = B[1] + (A[1] - B[1]) * l, b = B[2] + (A[2] - B[2]) * l, a = B[3] + (A[3] - B[3]) * l;
      const e = 1 - Math.abs(dt) / ew;
      if (e > 0) { r += (ed[0] - r) * e; g += (ed[1] - g) * e; b += (ed[2] - b) * e; a += (ed[3] - a) * e; }
      D[i * 4] = r; D[i * 4 + 1] = g; D[i * 4 + 2] = b; D[i * 4 + 3] = a * 255;
    }
    this.g.putImageData(this.id, 0, 0);
    return true;
  }
}

// ---------- Pacific "pour" overlay: fills Pacific cells in order of distance from the basin centre (area-true) ----------
class Pour {
  constructor(img, data) {
    const w = data.w, h = data.h; this.w = w; this.h = h;
    this.cv = makeCanvas(w, h); this.g = this.cv.getContext('2d', { willReadFrequently: true });
    this.g.drawImage(img, 0, 0, w, h); const d = this.g.getImageData(0, 0, w, h).data;
    const c = L.dir(data.centroid[0], data.centroid[1]); this.c = c;
    // tangent basis at the centre for edge azimuths
    let e1 = [-c[2], 0, c[0]]; const n1 = Math.hypot(...e1); e1 = e1.map(v => v / n1);
    const e2 = [c[1] * e1[2] - c[2] * e1[1], c[2] * e1[0] - c[0] * e1[2], c[0] * e1[1] - c[1] * e1[0]];
    const keys = [], edges = [], az = []; let wsum = 0; const wts = new Float32Array(w * h), dist = new Float32Array(w * h);
    for (let y = 0; y < h; y++) {
      const lat = 90 - (y + 0.5) / h * 180, cl = Math.cos(lat * Math.PI / 180);
      for (let x = 0; x < w; x++) {
        const i = y * w + x; if (d[i * 4] < 128) continue;
        const v = L.dir(lat, -180 + (x + 0.5) / w * 360);
        const ds = Math.acos(clamp(v[0] * c[0] + v[1] * c[1] + v[2] * c[2], -1, 1));
        dist[i] = ds; wts[i] = cl; wsum += cl; keys.push(Math.floor(ds * 1e5) * 4194304 + i);
        if (d[i * 4 + 1] > 128) { edges.push(i); az.push((Math.atan2(v[0] * e2[0] + v[1] * e2[1] + v[2] * e2[2], v[0] * e1[0] + v[1] * e1[1] + v[2] * e1[2]) / (Math.PI * 2) + 1.25) % 1); }
      }
    }
    const K = Float64Array.from(keys).sort();
    this.order = new Uint32Array(K.length); this.cum = new Float32Array(K.length); this.dist = new Float32Array(K.length);
    let acc = 0; const scale = data.area / wsum;
    for (let k = 0; k < K.length; k++) { const i = K[k] % 4194304; this.order[k] = i; acc += wts[i] * scale; this.cum[k] = acc; this.dist[k] = dist[i]; }
    this.edges = Uint32Array.from(edges); this.az = Float32Array.from(az);
    this.id = this.g.createImageData(w, h); this.sig = '';
  }
  // fill: km^2 filled; edgeP: 0..1 outline reveal; edgeA alpha
  draw(fill, edgeP, edgeA = 1) {
    let lo = 0, hi = this.cum.length; while (lo < hi) { const m = (lo + hi) >> 1; if (this.cum[m] < fill) lo = m + 1; else hi = m; }
    const N = lo; const sig = N + '|' + edgeP.toFixed(3) + '|' + edgeA.toFixed(2);
    if (sig === this.sig) return false; this.sig = sig;
    const D = this.id.data; D.fill(0);
    const Dm = N > 0 ? this.dist[N - 1] : 0;
    for (let k = 0; k < N; k++) {
      const i = this.order[k] * 4, f = smooth(Dm - 0.05, Dm, this.dist[k]);
      D[i] = 255; D[i + 1] = 90 + 110 * f; D[i + 2] = 54 + 40 * f; D[i + 3] = 235;
    }
    if (edgeP > 0) for (let k = N; k < this.order.length; k++) { const i = this.order[k] * 4; D[i] = 61; D[i + 1] = 227; D[i + 2] = 255; D[i + 3] = 150 * edgeP; }
    if (edgeP > 0 && edgeA > 0) for (let k = 0; k < this.edges.length; k++) { if (this.az[k] > edgeP) continue; const i = this.edges[k] * 4; D[i] = 61; D[i + 1] = 227; D[i + 2] = 255; D[i + 3] = 255 * edgeA; }
    this.g.putImageData(this.id, 0, 0); return true;
  }
}

export async function build(api, C) {
  const g = await api.globe();
  // ---------------- timing ----------------
  const wordAt = (seg, txt, nth = 0) => { const ws = C.words(seg).filter(w => w.w.toLowerCase().replace(/[^a-z0-9'-]/g, '') === txt); return (ws[nth] || ws[0]).start; };
  const FIX = { line: ['s029', 'line'], ant: ['s029', 'antarctica'], going: ['s031', 'going'], flip: ['s040', 'over'], asia: ['s041', 'asia'] };
  const M = (n) => FIX[n] ? wordAt(...FIX[n]) : C.T(n);
  const SEG = (id) => C.seg(id);
  const T0 = C.t0, T1 = C.t1;
  const pre = 3 / 30; // pop a few frames before the word
  const tm = {
    np: M('np'), boat: M('boat'), depth: M('depth'), bottom: M('bottom'), sp: M('sp'), up: M('up'), sheet: M('sheet'), thick: M('thick'),
    neg: M('neg'), drag: M('drag'), match: M('match'), line: M('line'), ant: M('ant'), other: M('other'), poles: M('poles'), avoid: M('avoid'),
    brings: M('brings'), myth: M('myth'), china: M('china'), test: M('test'), kansas: M('kansas'), dig: M('dig'), going: M('going'),
    indian: M('indian'), nearest: M('nearest'), island: M('island'), away: M('away'), notchina: M('notchina'), hemi: M('hemi'), us: M('us'),
    china2: M('china2'), start: M('start'), four: M('four'), dig2: M('dig2'), arg: M('arg'), flipall: M('flipall'), lay: M('lay'), orig: M('orig'),
    eighth: M('eighth'), random: M('random'), puzzle: M('puzzle'), half: M('half'), cram: M('cram'), europe: M('europe'), still: M('still'),
    cut: M('cut'), mostly: M('mostly'), flip: M('flip'), p89: M('p89'), alone: M('alone'), drop: M('drop'), asia: M('asia'),
    ocean: M('ocean'), landb: M('landb'), avoidl: M('avoidl'), lop: M('lop'), see: M('see'), g1875: M('g1875'), shape: M('shape'), ball: M('ball'),
    taught: M('taught'), checks: M('checks'), sub: M('sub'),
    santa: wordAt('s025', "santa's"), ocean25: wordAt('s025', 'ocean'), stand: wordAt('s025', 'stand'), dont: wordAt('s029', "don't"),
    but29: wordAt('s029', 'but'), nz: wordAt('s040', 'new'), spare: wordAt('s041', 'spare'), want: wordAt('s044', 'want'), before: wordAt('s044', 'before'),
    scoops: wordAt('s038', 'scoops'), notHemi: wordAt('s033', 'not', 1),
  };
  // cut points (absolute)
  const cA = T0, cB = tm.santa - 0.25, cProf = tm.depth - pre, cDisc = SEG('s027').start, cDrag = SEG('s028').start, cCut = tm.dont - 0.12,
    cTop = tm.ant - pre, cChina = SEG('s031').start, cGag4 = tm.dig - 0.2, cDrill = cGag4 + 2.3, cOcean = tm.indian - 0.12, cIsl = tm.nearest - 0.3,
    cFlat = tm.notchina - pre, cBob = tm.arg + 1.05, cAnti = SEG('s035').start + 0.4, cWaf = SEG('s036').start, cCap = SEG('s037').start,
    cSettle = tm.europe - 0.2, cTiles = tm.cut - 0.35, cFlip = SEG('s040').start, cPac = SEG('s041').start, cMont = tm.ocean - pre,
    cDrip = tm.lop - pre, cTet = SEG('s043').start - 0.25;

  // ---------------- assets ----------------
  await api.loadImages([IMG + 'ch2_ee_grey.jpg', IMG + 'ch2_ee_anti.png', 'tex/equal_earth.jpg', IMG + 'ch2_disc_n.png', IMG + 'ch2_disc_s.png',
    IMG + 'ch2_landmask.png', IMG + 'ch2_pacific.png', IMG + 'green_globes.jpg']);
  const im = (n) => api.img(n.includes('/') ? n : IMG + n);
  const DATA = await api.loadJSON('ep/ep01/ch2_data.json');
  const CTY = await loadGeo('ne_50m_admin_0_countries');
  const ARC = await loadGeo('arctic_ocean');
  const feat = (n) => findFeature(CTY, n);
  const S = await makeSets(api);
  const sfx = (t, n, db) => { if (t >= T0 - 0.5 && t < T1 + 0.5) api.cue(t, n, db); };

  // geometry
  const arcR = rings(ARC.features[0]);
  const arcX = L.ringsXYZ(arcR);
  const antR = DATA.continents.antarctica.rings;
  const antX = L.ringsXYZ(antR);
  const antMirX = L.ringsXYZ(antR.map(r => r.map(([lo, la]) => [lo + 180, -la])));
  const meanDir = (arrs) => { let x = 0, y = 0, z = 0; for (const a of arrs) for (let i = 0; i < a.length; i += 3) { x += a[i]; y += a[i + 1]; z += a[i + 2]; } const n = Math.hypot(x, y, z); return [x / n, y / n, z / n]; };
  const arcC = ARC.features[0].properties?.centroid_latlon ? L.dir(...ARC.features[0].properties.centroid_latlon) : meanDir(arcX), antC = L.dir(...DATA.continents.antarctica.centroid);

  // ---------------- 3D actor timelines (absolute) ----------------
  S.heroF.play(cB - 1, 'Idle').play(tm.boat - 0.25, 'Wave', { fade: 0.2 }).play(tm.stand + 0.1, 'Interact', { fade: 0.25 }).play(tm.stand + 1.4, 'Idle', { fade: 0.3 });
  S.heroC.play(cProf - 1, 'Idle').play(tm.depth + 1.05, 'HitRecieve_2', { fade: 0.12, once: true }).play(tm.depth + 2.0, 'Idle', { fade: 0.35 })
    .play(tm.up - 0.1, 'Idle_Neutral', { fade: 0.3 }).play(tm.thick + 0.6, 'Idle', { fade: 0.4 });
  S.heroP.play(cGag4 - 1, 'Idle').play(tm.dig - 0.05, 'Interact', { fade: 0.15 }).play(tm.dig + 1.1, 'Idle_Neutral', { fade: 0.3 })
    .play(cOcean - 0.5, 'Idle').play(tm.indian + 0.18, 'Roll', { fade: 0.08, once: true }).play(tm.indian + 0.95, 'Idle', { fade: 0.3 });
  S.heroD.play(cDrill - 1, 'Run');
  // gag 5 (Pacific pour) on the composite hero
  const tAusL = tm.drop + 2.35, tAusA = tAusL + 1.45, tAsiaA = tm.asia + 0.02, tAsiaL = tAsiaA - 1.0;
  S.heroC.play(tAusL - 0.6, 'Idle_Neutral', { fade: 0.2 }).play(tAsiaA + 0.02, 'HitRecieve_2', { fade: 0.1, once: true }).play(tAsiaA + 0.95, 'Wave', { fade: 0.25 });
  S.mini.play(tm.arg - 2, 'idle').play(tm.arg + 0.05, 'jump', { fade: 0.08, once: true }).play(tm.arg + 0.75, 'emote-yes', { fade: 0.2 });

  const scenes = [];
  const push = (s) => { s.id = 'ch2'; scenes.push(s); return s; };

  // ======================= s025 A: Arctic fly-in + chapter card =======================
  const npDir = L.dir(90, 0);
  push(gscene({
    t0: cA, t1: cB,
    cam: (lt) => camAt([{ t: 0, lat: 48, lon: -28, alt: 3.1 }, { t: 2.6, lat: 82, lon: -5, alt: 1.5, tilt: 30, ease: E.inOut }, { t: 6, lat: 83, lon: 8, alt: 1.32, tilt: 36 }], lt, 1.2),
    look: (lt) => ({ dim: 0.12 * prog(lt + cA, tm.np, tm.np + 0.6), desat: 0.15 }),
    draw2d: (ctx, lt, t, pj) => {
      if (t >= tm.ocean25 - 0.3) {
        const k = prog(t, tm.ocean25 - 0.2, tm.ocean25 + 0.9, E.out);
        ctx.save(); ctx.globalAlpha = 0.28 * k; ctx.fillStyle = PAL.cyan; ctx.fill(L.globePath(pj, arcX, true)); ctx.restore();
        L.strokeGlobe(ctx, pj, arcX, { p: k, color: PAL.cyan, width: 2.6 });
      }
      if (t >= tm.np - pre) {
        const q = pj.xyz(...npDir, false);
        L.pulse(ctx, q[0], q[1], t - (tm.np - pre), { color: '#ffffff', r: 9 });
        F.pill(ctx, 'NORTH POLE', q[0] + 70, q[1] - 70, { anchor: 'left', leader: [q[0], q[1]], size: 38, alpha: prog(t, tm.np - pre, tm.np + 0.25) * (1 - prog(t, cB - 0.4, cB)) });
      }
    },
  }));
  sfx(cA, 'whoosh_soft', -12);
  sfx(tm.np - 0.05, 'pop_ui', -14);
  // chapter card overlay
  push({
    t0: cA, t1: cA + 2.35, layer: 6, draw(ctx, lt) {
      const dur = 2.35, a = env(lt, 0, dur, 0.25, 0.4);
      ctx.save(); ctx.fillStyle = `rgba(3,5,10,${0.55 * a})`; ctx.fillRect(0, 0, W, H);
      const p = prog(lt, 0.05, 0.7, E.outExpo); ctx.globalAlpha = a;
      ctx.fillStyle = PAL.hero; const lw = 460 * p; ctx.fillRect(W / 2 - lw / 2, H / 2 + 34, lw, 5);
      F.text(ctx, 'CHAPTER 2', W / 2, H / 2 - 120, { size: 44, fam: F.FAM.label, weight: 700, tracking: 0.35, align: 'center', color: PAL.hero, alpha: p });
      F.headline(ctx, ["WHAT'S", 'ON', "EARTH'S", { w: 'OTHER', c: PAL.yellow }, { w: 'SIDE?', c: PAL.yellow }], W / 2, H / 2 + 6, lt, { size: 118, per: 0.06, t0: 0.1, tOut: dur - 0.42 });
      ctx.restore();
    },
  });

  // ======================= s025 B: floe gag (Explorer on a floe, Santa's houseboat) =======================
  const sky = (ctx, t, o = {}) => {
    const gr = ctx.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#050a18'); gr.addColorStop(0.55, '#0d2140'); gr.addColorStop(0.75, '#21456b'); gr.addColorStop(1, '#0a1626');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    const r = F.rng(99); ctx.fillStyle = '#ffffff';
    for (let i = 0; i < 160; i++) { const x = r() * W, y = r() * H * 0.55, b = r(); ctx.globalAlpha = 0.25 + 0.6 * b * (0.7 + 0.3 * Math.sin(t * 2 + i)); ctx.fillRect(x, y, b > 0.8 ? 2.2 : 1.3, b > 0.8 ? 2.2 : 1.3); }
    ctx.globalAlpha = 1;
    // aurora ribbons
    for (let k = 0; k < 3; k++) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const y0 = (o.auroraY ?? 250) + k * 55, amp = 60 + k * 20;
      const grd = ctx.createLinearGradient(0, y0 - 140, 0, y0 + 60); grd.addColorStop(0, 'rgba(60,255,180,0)'); grd.addColorStop(0.7, `rgba(70,255,170,${0.10 - k * 0.025})`); grd.addColorStop(1, 'rgba(61,227,255,0)');
      ctx.fillStyle = grd; ctx.beginPath(); ctx.moveTo(0, y0 + 60);
      for (let x = 0; x <= W; x += 40) ctx.lineTo(x, y0 - 120 + amp * Math.sin(x * 0.0032 + t * 0.35 + k * 1.7) + 25 * Math.sin(x * 0.011 - t * 0.6));
      for (let x = W; x >= 0; x -= 40) ctx.lineTo(x, y0 + 40 + amp * 0.6 * Math.sin(x * 0.0032 + t * 0.35 + k * 1.7));
      ctx.closePath(); ctx.fill(); ctx.restore();
    }
  };
  push({
    t0: cB, t1: cProf, draw(ctx, lt, t) {
      sky(ctx, t);
      const k = prog(t, cB, cProf, E.inOutSine);
      const cam = [lerp(2.1, 1.45, k), lerp(0.7, 0.55, k), lerp(5.2, 4.35, k)];
      S.floe(ctx, t, lt, { cam, target: [lerp(-0.7, -0.45, k), 0.72, -0.4], cabinX: lerp(-4.6, -2.5, prog(t, cB, tm.boat + 0.2, E.out)), heroRy: lerp(-0.25, -0.75, prog(t, tm.boat - 0.4, tm.boat + 0.2)) });
    },
  });
  sfx(cB, 'whoosh_soft', -16);

  // ======================= s025/s026 C: profile panels (Arctic sea floor, South Pole ice) =======================
  const MI = 130; // px per mile
  const pl = (pts, x) => { for (let i = 1; i < pts.length; i++) if (x <= pts[i][0]) { const a = pts[i - 1], b = pts[i]; const u = (x - a[0]) / (b[0] - a[0]); const s = u * u * (3 - 2 * u); return lerp(a[1], b[1], s); } return pts[pts.length - 1][1]; };
  const AP = [[0, -0.8], [120, -0.62], [225, -0.12], [262, 0.05], [330, 0.13], [430, 0.22], [540, 1.3], [650, 2.35], [730, 2.5], [800, 1.15], [870, 2.3], [960, 2.5], [1100, 2.72], [1220, 2.05], [1320, 2.6], [1450, 2.35], [1560, 0.7], [1630, 0.1], [1780, 0.06], [1820, -0.05], [1920, -0.3]];
  const floorA = (x) => pl(AP, x) + 0.035 * Math.sin(x * 0.051) + 0.025 * Math.sin(x * 0.13 + 1) * (x > 300 && x < 1600 ? 1 : 0.3) - (Math.abs(x - 960) < 40 ? 0 : 0);
  const BP = [[0, -0.55], [200, -0.25], [400, 0.12], [600, -0.18], [800, 0.14], [960, 0.05], [1100, 0.22], [1300, -0.12], [1500, 0.3], [1700, -0.22], [1920, 0.02]];
  const bedB = (x) => pl(BP, x) + 0.03 * Math.sin(x * 0.07 + 2) + 0.02 * Math.sin(x * 0.19);
  const iceTopB = (x, k) => { const full = 1.76 - 0.32 * Math.pow((x - 960) / 960, 2) + 0.015 * Math.sin(x * 0.02); const lo = bedB(x) + 0.16; return lerp(lo, full, k); };
  const ySLA = 400, ySLB = 770;
  function drawArctic(ctx, oy, t) {
    ctx.save(); ctx.translate(0, oy);
    const sg = ctx.createLinearGradient(0, -200, 0, ySLA); sg.addColorStop(0, '#060c1c'); sg.addColorStop(1, '#1e3a5e'); ctx.fillStyle = sg; ctx.fillRect(0, -300, W, ySLA + 300);
    const wg = ctx.createLinearGradient(0, ySLA, 0, ySLA + 2.8 * MI); wg.addColorStop(0, '#15507e'); wg.addColorStop(0.35, '#0d3458'); wg.addColorStop(1, '#061527'); ctx.fillStyle = wg; ctx.fillRect(0, ySLA, W, 2.9 * MI + 10);
    // sea floor rock
    const rp = new Path2D(); rp.moveTo(0, H + 300);
    for (let x = 0; x <= W; x += 8) rp.lineTo(x, ySLA + floorA(x) * MI);
    rp.lineTo(W, H + 300); rp.closePath();
    const rg = ctx.createLinearGradient(0, ySLA, 0, H); rg.addColorStop(0, '#5b4a3c'); rg.addColorStop(1, '#1d1714'); ctx.fillStyle = rg; ctx.fill(rp);
    ctx.save(); ctx.clip(rp); ctx.strokeStyle = 'rgba(255,230,200,0.06)'; ctx.lineWidth = 3;
    for (let k = 1; k < 6; k++) { ctx.beginPath(); for (let x = 0; x <= W; x += 16) { const y = ySLA + floorA(x) * MI + k * 34 + 6 * Math.sin(x * 0.01 + k); x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
    ctx.restore();
    ctx.strokeStyle = 'rgba(255,220,180,0.35)'; ctx.lineWidth = 2; ctx.beginPath(); for (let x = 0; x <= W; x += 8) { const y = ySLA + floorA(x) * MI; x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke();
    // Greenland / Siberia ice caps on land
    ctx.fillStyle = '#e9f3fb'; ctx.beginPath(); ctx.moveTo(0, ySLA + floorA(0) * MI - 2); for (let x = 0; x <= 226; x += 6) ctx.lineTo(x, ySLA + floorA(x) * MI - 2 - 16 * (1 - x / 226)); for (let x = 226; x >= 0; x -= 6) ctx.lineTo(x, ySLA + floorA(x) * MI + 4); ctx.fill();
    // sea ice: thin white line with pressure ridges and a couple of leads
    ctx.fillStyle = '#f4f9ff';
    for (let x = 262; x < 1700; x += 6) { if ((x > 610 && x < 640) || (x > 1290 && x < 1312)) continue; const r = 2 + 3 * Math.max(0, Math.sin(x * 0.09) * Math.sin(x * 0.023)); ctx.fillRect(x, ySLA - r, 6, r + 3); }
    ctx.restore();
  }
  function drawSouth(ctx, oy, t, k) {
    ctx.save(); ctx.translate(0, oy);
    const sg = ctx.createLinearGradient(0, ySLB - 4 * MI, 0, ySLB); sg.addColorStop(0, '#081226'); sg.addColorStop(1, '#2a4a70'); ctx.fillStyle = sg; ctx.fillRect(0, -300, W, ySLB + 300);
    // bedrock
    const rp = new Path2D(); rp.moveTo(0, H + 300); for (let x = 0; x <= W; x += 8) rp.lineTo(x, ySLB - bedB(x) * MI); rp.lineTo(W, H + 300); rp.closePath();
    const rg = ctx.createLinearGradient(0, ySLB - 60, 0, H); rg.addColorStop(0, '#6a5747'); rg.addColorStop(1, '#221a15'); ctx.fillStyle = rg; ctx.fill(rp);
    ctx.save(); ctx.clip(rp); ctx.strokeStyle = 'rgba(255,230,200,0.07)'; ctx.lineWidth = 3;
    for (let j = 1; j < 5; j++) { ctx.beginPath(); for (let x = 0; x <= W; x += 16) { const y = ySLB - bedB(x) * MI + j * 36 + 6 * Math.sin(x * 0.012 + j); x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
    ctx.restore();
    // ice sheet
    const ip = new Path2D(); ip.moveTo(0, ySLB - bedB(0) * MI);
    for (let x = 0; x <= W; x += 8) ip.lineTo(x, ySLB - iceTopB(x, k) * MI);
    for (let x = W; x >= 0; x -= 8) ip.lineTo(x, ySLB - bedB(x) * MI); ip.closePath();
    const ig = ctx.createLinearGradient(0, ySLB - 1.9 * MI, 0, ySLB); ig.addColorStop(0, '#f4f9ff'); ig.addColorStop(0.6, '#cfe6f6'); ig.addColorStop(1, '#8fbedf'); ctx.fillStyle = ig; ctx.fill(ip);
    ctx.save(); ctx.clip(ip); ctx.strokeStyle = 'rgba(80,140,190,0.18)'; ctx.lineWidth = 2;
    for (let j = 1; j < 9; j++) { ctx.beginPath(); for (let x = 0; x <= W; x += 16) { const y = ySLB - lerp(bedB(x), iceTopB(x, k), j / 9) * MI; x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
    ctx.restore();
    // dashed sea level
    ctx.setLineDash([18, 14]); ctx.strokeStyle = 'rgba(61,227,255,0.85)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, ySLB); ctx.lineTo(W, ySLB); ctx.stroke(); ctx.setLineDash([]);
    ctx.restore();
    return ip;
  }
  push({
    t0: cProf, t1: cDisc, draw(ctx, lt, t) {
      ctx.fillStyle = '#060b16'; ctx.fillRect(0, 0, W, H);
      const wk = prog(t, tm.bottom - 0.2, tm.bottom + 0.3, E.inOutExpo);
      // gentle push-in for life
      const z = 1 + 0.035 * prog(t, cProf, tm.bottom, E.inOutSine) + 0.03 * prog(t, tm.bottom, cDisc, E.inOutSine);
      ctx.save(); ctx.translate(W / 2, H * 0.45); ctx.scale(z, z); ctx.translate(-W / 2, -H * 0.45);
      const oyA = -H * 1.05 * wk, oyB = H * 1.05 * (1 - wk);
      if (wk < 1) {
        drawArctic(ctx, oyA, t);
        ctx.save(); ctx.translate(0, oyA);
        // sonar rings
        const ts = t - tm.depth;
        if (ts > -0.1 && ts < 2.2) for (let j = 0; j < 3; j++) { const ph = ts * 0.9 - j * 0.22; if (ph < 0 || ph > 1) continue; ctx.strokeStyle = `rgba(61,227,255,${0.55 * (1 - ph)})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(960, ySLA + 4, 30 + ph * 520, 10 + ph * 330, 0, 0.05 * Math.PI, 0.95 * Math.PI); ctx.stroke(); }
        // depth ruler
        const rk = prog(t, tm.depth + 0.1, tm.depth + 1.15, E.out);
        if (rk > 0) {
          const y0 = ySLA + 6, y1 = ySLA + lerp(0, 2.5 * MI, rk);
          ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(1000, y0); ctx.lineTo(1000, y1); ctx.stroke();
          for (let m = 0.5; m <= 2.5 * rk + 1e-6; m += 0.5) { const yy = ySLA + m * MI; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(1000, yy); ctx.lineTo(m % 1 === 0 ? 1028 : 1018, yy); ctx.stroke(); }
          ctx.fillStyle = PAL.yellow; ctx.beginPath(); ctx.moveTo(1000, y1 + 4); ctx.lineTo(990, y1 - 12); ctx.lineTo(1010, y1 - 12); ctx.closePath(); ctx.fill();
          L.miles(ctx, 2.5 * rk, 1040, Math.min(y1, ySLA + 2.5 * MI - 20) + 22, { size: 54, alpha: prog(t, tm.depth + 0.1, tm.depth + 0.3) });
          if (rk >= 1) L.glowDot(ctx, 1000, ySLA + 2.5 * MI, 60, PAL.yellow, 0.5 * (1 - prog(t, tm.depth + 1.15, tm.depth + 1.8)));
        }
        ctx.restore();
        S.comp(ctx, t, 'hero', 940, ySLA + oyA - 1, 255, { ry: 0.45 });
        F.pill(ctx, 'SEA FLOOR: ~2.5 MILES DOWN', 1140, ySLA + 2.5 * MI + 95 + oyA, { anchor: 'left', size: 40, alpha: prog(t, tm.depth + 1.0, tm.depth + 1.35), border: 'rgba(255,210,63,0.6)' });
      }
      if (wk > 0) {
        const kk = prog(t, tm.up - 0.1, tm.up + 1.5, E.inOutSine) * 0.88 + 0.12;
        const ip = drawSouth(ctx, oyB, t, kk);
        ctx.save(); ctx.translate(0, oyB);
        const top = ySLB - iceTopB(960, kk) * MI;
        // upward ruler from sea level
        const uk = prog(t, tm.up - 0.1, tm.up + 1.5, E.inOutSine);
        if (uk > 0) {
          ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(1015, ySLB); ctx.lineTo(1015, top); ctx.stroke();
          for (let m = 0.5; m <= 1.76 * uk + 1e-6; m += 0.5) { const yy = ySLB - m * MI; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(1015, yy); ctx.lineTo(m % 1 === 0 ? 1043 : 1033, yy); ctx.stroke(); }
          ctx.fillStyle = PAL.yellow; ctx.beginPath(); ctx.moveTo(1015, top - 4); ctx.lineTo(1005, top + 12); ctx.lineTo(1025, top + 12); ctx.closePath(); ctx.fill();
          L.miles(ctx, 1.76 * uk, 1060, top + 50, { size: 54, alpha: prog(t, tm.up - 0.1, tm.up + 0.1) });
        }
        // sheet outline + thickness bracket
        if (t > tm.sheet - pre) { ctx.save(); ctx.lineJoin = 'round'; const a = prog(t, tm.sheet - pre, tm.sheet + 0.5); for (const [lw, c] of [[12, 'rgba(61,227,255,0.18)'], [5, 'rgba(61,227,255,0.45)'], [2.5, '#ffffff']]) { ctx.strokeStyle = c; ctx.lineWidth = lw; ctx.globalAlpha = a; ctx.stroke(ip); } ctx.restore(); }
        if (t > tm.thick - pre) {
          const bx = 1330, yb = ySLB - bedB(bx) * MI, yt = ySLB - iceTopB(bx, kk) * MI, bk = prog(t, tm.thick - pre, tm.thick + 0.55, E.out);
          const ym = (yb + yt) / 2, h2 = (yb - yt) / 2 * bk;
          ctx.strokeStyle = PAL.cyan; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.beginPath();
          ctx.moveTo(bx - 18, ym - h2); ctx.lineTo(bx, ym - h2); ctx.lineTo(bx, ym + h2); ctx.lineTo(bx - 18, ym + h2); ctx.moveTo(bx, ym); ctx.lineTo(bx + 16, ym); ctx.stroke();
        }
        // polar wind streaks
        const r = F.rng(31); ctx.strokeStyle = 'rgba(230,245,255,0.35)'; ctx.lineWidth = 2;
        for (let i = 0; i < 26; i++) { const sp = 700 + r() * 900, y = 120 + r() * 380, x = ((r() * W + (t - tm.sp) * sp) % (W + 400)) - 200; ctx.globalAlpha = 0.25 + 0.4 * r(); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 70 + r() * 120, y + 4); ctx.stroke(); }
        ctx.globalAlpha = 1;
        // South Pole marker
        if (t > tm.sp - pre) L.pulse(ctx, 960, top, t - (tm.sp - pre), { color: '#ffffff', r: 7, alpha: 1 - prog(t, tm.up - 0.2, tm.up + 0.2) });
        ctx.restore();
        S.comp(ctx, t, 'hero', 935, top + oyB - 1, 255, { ry: 0.5 });
        const pa = prog(t, tm.sp - pre, tm.sp + 0.25) * (1 - prog(t, tm.up - pre - 0.25, tm.up - pre));
        F.pill(ctx, 'SOUTH POLE', 1090, top + oyB - 150, { anchor: 'left', leader: [985, top + oyB - 90], size: 40, alpha: pa });
        F.pill(ctx, 'SOUTH POLE: NEARLY 2 MILES UP', 1200, 150, { anchor: 'left', size: 40, alpha: prog(t, tm.up - pre, tm.up + 0.25), border: 'rgba(255,210,63,0.6)' });
      }
      ctx.restore();
      L.streaks(ctx, W, H, Math.sin(Math.PI * clamp(wk)) * 0.9, true);
    },
  });
  sfx(tm.depth - 0.02, 'sonar_ping', -12);
  sfx(tm.depth + 0.1, 'rumble_quake', -18);
  sfx(tm.bottom - 0.2, 'whoosh_big', -14);
  sfx(tm.sp - 0.05, 'ice_wind', -14);

  // ======================= s027 D: polar discs (photographic negatives) =======================
  const discN = im('ch2_disc_n.png'), discS = im('ch2_disc_s.png');
  const invN = makeCanvas(640, 640); { const q = invN.getContext('2d'); q.drawImage(discN, 0, 0); q.globalCompositeOperation = 'difference'; q.fillStyle = '#ffffff'; q.fillRect(0, 0, 640, 640); q.globalCompositeOperation = 'destination-in'; q.drawImage(discN, 0, 0); }
  const navyBg = (ctx, t) => {
    const gr = ctx.createRadialGradient(W / 2, H * 0.48, 80, W / 2, H / 2, H); gr.addColorStop(0, '#13233f'); gr.addColorStop(1, '#03060c'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.strokeStyle = 'rgba(120,170,230,0.06)'; ctx.lineWidth = 1; const off = (t * 6) % 80;
    for (let x = -80 + off; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = -80 + off; y < H; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    ctx.restore();
  };
  const drawDisc = (ctx, img, x, y, r, rot, a = 1) => {
    if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a;
    L.glowDot(ctx, x, y, r * 1.25, '#3d6fb0', 0.35);
    ctx.translate(x, y); ctx.rotate(rot); ctx.drawImage(img, -r, -r, 2 * r, 2 * r); ctx.restore();
    ctx.save(); ctx.globalAlpha *= a * 0.9; ctx.strokeStyle = 'rgba(244,246,250,0.8)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
  };
  const tintCenter = (ctx, x, y, r, col, a) => { if (a <= 0) return; ctx.save(); ctx.globalCompositeOperation = 'lighter'; L.glowDot(ctx, x, y, r, col, a); ctx.restore(); };
  push({
    t0: cDisc, t1: cDrag, draw(ctx, lt, t) {
      navyBg(ctx, t);
      const mv = prog(t, tm.ocean25 > 0 ? wordAt('s027', 'ocean') - 0.1 : t, wordAt('s027', 'ocean') + 0.7, E.inOut);
      const rN = 255, xN = lerp(560, 600, mv), yN = lerp(560, 470, mv), xS = lerp(1360, 1320, mv), yS = lerp(560, 640, mv);
      const popN = E.outBack(prog(t, cDisc, cDisc + 0.5, E.lin)), popS = E.outBack(prog(t, cDisc + 0.15, cDisc + 0.65, E.lin));
      const rot = (t - cDisc) * 0.09;
      const inv = prog(t, tm.neg - pre, tm.neg + 0.3, E.inOut) * (1 - prog(t, wordAt('s027', 'ocean') + 0.6, wordAt('s027', 'ocean') + 1.0, E.inOut));
      drawDisc(ctx, discN, xN, yN, rN * popN, rot, 1);
      if (inv > 0) drawDisc(ctx, invN, xN, yN, rN * popN, rot, inv);
      drawDisc(ctx, discS, xS, yS, rN * popS, -rot, 1);
      const tO = wordAt('s027', 'ocean'), tB = wordAt('s027', 'continent');
      tintCenter(ctx, xN, yN, rN * 0.55, PAL.cyan, 0.45 * prog(t, tO - pre, tO + 0.3) * (0.8 + 0.2 * Math.sin(t * 5)));
      tintCenter(ctx, xS, yS, rN * 0.6, PAL.hero, 0.4 * prog(t, tB - pre, tB + 0.3) * (0.8 + 0.2 * Math.sin(t * 5)));
      const la = prog(t, cDisc + 0.4, cDisc + 0.8) * (1 - prog(t, tO - 0.3, tO));
      F.pill(ctx, 'NORTH POLE', xN, yN + rN + 60, { anchor: 'center', size: 36, alpha: la });
      F.pill(ctx, 'SOUTH POLE', xS, yS + rN + 60, { anchor: 'center', size: 36, alpha: la });
      F.headline(ctx, ['OCEAN', 'ON', { w: 'TOP.', c: PAL.cyan }, 'LAND', 'AT', { w: 'BOTTOM.', c: PAL.hero }], W / 2, 150, t - (tO - pre), { size: 92, per: 0.07 });
      // shutter flash at the inversion
      const fl = 1 - prog(t, tm.neg - pre, tm.neg + 0.2); if (t > tm.neg - pre && fl > 0) { ctx.fillStyle = `rgba(255,255,255,${0.35 * fl})`; ctx.fillRect(0, 0, W, H); }
    },
  });
  sfx(cDisc, 'whoosh_soft', -16);
  sfx(tm.neg - 0.05, 'glitch_click', -14);

  // ======================= s028 E: drag the Arctic Ocean onto Antarctica =======================
  const dragTh = 172 * Math.PI / 180; // rotation about +z: negative angle moves the pole down the 0° meridian
  const tDragE = tm.drag + 2.5, tBack = tm.but29 + 0.25;
  const dragState = (t) => {
    let k = prog(t, tm.drag - pre, tDragE, E.out); k -= prog(t, tBack, tBack + 1.7, E.inOut);
    const R1 = { ax: [0, 0, 1], th: -dragTh * k };
    const c1 = L.rotVec(arcC, R1);
    const R2 = L.rotAB(c1, antC, prog(t, tDragE - 0.6, tDragE + 0.3, E.inOut) * (1 - prog(t, tBack, tBack + 0.6)));
    return { k, R1, R2, c: L.rotVec(c1, R2) };
  };
  push(gscene({
    t0: cDrag, t1: cCut,
    cam: (lt, t) => {
      const s = dragState(t); const [la] = L.ll(s.c);
      const camLat = clamp(la - 6, -64, 66);
      const back = prog(t, tBack, tBack + 1.9, E.inOut);
      return camAt([{ t: 0, lat: camLat, lon: lerp(4, 0, back), alt: lerp(2.55, 3.1, back), tilt: 0 }], 0, 0) && { lat: camLat, lon: 0, alt: lerp(2.55, 3.0, back) * (1 + 0.006 * Math.sin(t * 0.7)), heading: (t - cDrag) * 0.8, tilt: 0 };
    },
    look: () => ({ dim: 0.18, desat: 0.2 }),
    draw2d: (ctx, lt, t, pj) => {
      const s = dragState(t);
      // Antarctica (orange) outline + fill
      if (t > tDragE - 0.2) {
        const k = prog(t, tDragE - 0.1, tm.match, E.out);
        ctx.save(); ctx.globalAlpha = 0.32 * prog(t, tm.match - 0.3, tm.match + 0.2) * (1 - prog(t, tBack, tBack + 0.35)); ctx.fillStyle = PAL.hero; ctx.fill(L.globePath(pj, antX, true)); ctx.restore();
        L.strokeGlobe(ctx, pj, antX, { p: k, color: PAL.hero, width: 3 });
      }
      const R = L.rotXYZ; const moved = arcX.map(a => R(R(a, s.R1), s.R2));
      const path = L.globePath(pj, moved, true);
      const fa = 0.42 + 0.1 * Math.sin(t * 4) * prog(t, tm.match - 0.2, tm.match + 0.2);
      ctx.save(); ctx.globalAlpha = fa * prog(t, cDrag, cDrag + 0.4); ctx.fillStyle = PAL.cyan; ctx.fill(path); ctx.restore();
      ctx.save(); ctx.lineJoin = 'round'; ctx.strokeStyle = PAL.cyan + '55'; ctx.lineWidth = 8; ctx.stroke(path); ctx.strokeStyle = '#E8FBFF'; ctx.lineWidth = 2.2; ctx.stroke(path); ctx.restore();
      F.pill(ctx, 'ARCTIC OCEAN = ANTARCTICA (ALMOST)', W / 2, 120, { anchor: 'center', size: 42, alpha: prog(t, tm.match - pre, tm.match + 0.25) * (1 - prog(t, tBack - 0.3, tBack)) });
    },
  }));
  sfx(tm.drag - 0.05, 'whoosh_soft', -12);
  sfx(tDragE - 0.1, 'thunk_heavy', -18);
  sfx(tm.match - 0.05, 'pop_ui', -14);

  // ======================= s029 F: cut-away, the drill lines up =======================
  push({
    t0: cCut, t1: cTop, draw(ctx, lt, t) {
      const gr = ctx.createRadialGradient(W / 2, H / 2, 80, W / 2, H / 2, H); gr.addColorStop(0, '#12213b'); gr.addColorStop(1, '#03050a'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
      const k = prog(t, cCut, cTop, E.inOutSine);
      const p = prog(t, tm.line - pre, tm.line + 1.0, E.out);
      const d = lerp(12, 11, k), a = Math.PI / 4 + 0.15 - 0.12 * k;
      const r = S.cutaway(ctx, t, { lat: 90, lon: 0, p, spin: 0.6 + 0.15 * k, cam: [Math.cos(a) * d, lerp(5.6, 4.9, k), Math.sin(a) * d], target: [0, 0, 0] });
      const top = S.project(r.top), bot = S.project(r.bottom), hd = S.project(r.end);
      if (p > 0 && p < 1) L.glowDot(ctx, hd.x, hd.y, 46, PAL.cyan, 0.9);
      if (t > tm.line - pre) L.pulse(ctx, top.x, top.y, t - tm.line + pre, { color: PAL.cyan, r: 9 });
      if (p >= 1) { L.pulse(ctx, bot.x, bot.y, t - tm.line - 1.2, { color: PAL.hero, r: 10 }); L.glowDot(ctx, bot.x, bot.y, 120, PAL.hero, 0.5 * (1 - prog(t, tm.line + 1.2, tm.line + 1.9))); }
    },
  });
  sfx(tm.line - 0.03, 'impact_deep', -6);

  // ======================= s029/s030 G: top-down on the Arctic, mirrored Antarctica; pull back; antipode glimpse; headline =======================
  push(gscene({
    t0: cTop, t1: cChina, ovKey: 'ch2:antipodes', install: async (gl) => { await gl.setOverlayURL('tex/data/antipodes.png'); },
    cam: (lt, t) => {
      const k = prog(t, tm.poles - 0.4, tm.poles + 1.8, E.inOut);
      const k2 = prog(t, tm.brings - 0.6, cChina + 0.2, E.inOutSine);
      const ll = L.ll([lerp(1e-3, Math.cos(25 * Math.PI / 180), k), lerp(1, Math.sin(25 * Math.PI / 180), k), 0]);
      const lat = lerp(89.95, 24, k), lon = lerp(10, 8, k) + 80 * k2 + (t - cTop) * 0.4;
      return { lat: lerp(lat, 30, k2), lon, alt: lerp(2.25 + 0.12 * prog(t, cTop, tm.poles, E.inOutSine), 3.0, k) * (1 + 0.006 * Math.sin(t * 0.7)), heading: (1 - k) * (t - cTop) * 3.2, tilt: 0 };
    },
    look: (lt, t) => ({ ovAlpha: 0.95 * env(t, tm.avoid - 0.35, tm.avoid + 1.55, 0.3, 0.45), dim: 0.12 + 0.18 * env(t, tm.avoid - 0.35, tm.avoid + 1.55, 0.3, 0.45) + 0.2 * prog(t, tm.brings - 0.3, tm.brings + 0.3), desat: 0.15 }),
    draw2d: (ctx, lt, t, pj) => {
      const fade = 1 - prog(t, tm.poles + 0.2, tm.poles + 1.2);
      if (fade > 0) {
        ctx.save(); ctx.globalAlpha = fade;
        const ap = L.globePath(pj, arcX, true), mp = L.globePath(pj, antMirX, true);
        ctx.save(); ctx.globalAlpha *= 0.22; ctx.fillStyle = PAL.cyan; ctx.fill(ap); ctx.restore();
        L.strokeGlobe(ctx, pj, arcX, { color: PAL.cyan, width: 2.6 });
        const mk = prog(t, tm.ant - pre, tm.ant + 1.5, E.inOut);
        ctx.save(); ctx.globalAlpha *= 0.25 * prog(t, tm.ant + 1.2, tm.ant + 1.8); ctx.fillStyle = PAL.hero; ctx.fill(mp); ctx.restore();
        L.strokeGlobe(ctx, pj, antMirX, { p: mk, color: PAL.hero, width: 3 });
        const ok = prog(t, tm.other - pre, tm.other + 0.5);
        if (ok > 0) { ctx.save(); ctx.clip(ap); ctx.globalAlpha *= 0.82 * ok * (0.9 + 0.1 * Math.sin(t * 6)); ctx.fillStyle = PAL.yellow; ctx.fill(mp); ctx.restore(); }
        ctx.restore();
        F.pill(ctx, 'MOST OF ANTARCTICA: OPPOSITE THE ARCTIC OCEAN', W / 2, 110, { anchor: 'center', size: 40, alpha: prog(t, wordAt('s029', 'opposite') - pre, wordAt('s029', 'opposite') + 0.3) * (1 - prog(t, tm.poles - 0.2, tm.poles + 0.2)) });
      }
      // kinetic headline
      if (t > tm.brings - 0.2) {
        F.headline(ctx, ['DIG', 'STRAIGHT', 'DOWN', 'TO', { w: 'CHINA?', c: PAL.hero }], W / 2, 200, t - tm.brings, { size: 140, per: (tm.myth - tm.brings - 0.25) / 4, tOut: cChina - tm.brings + 1.6 });
      }
    },
  }));
  sfx(tm.poles - 0.05, 'whoosh_soft', -14);
  sfx(tm.avoid - 0.3, 'shimmer', -18);
  sfx(tm.myth - 0.05, 'impact_short', -14);

  // ======================= s031 H: China -> whip to Kansas =======================
  const chinaF = feat('China');
  const ovChina = makeCanvas(2048, 1024); fillEquirect(ovChina, [-180, -90, 180, 90], [chinaF], { color: PAL.hero, alpha: 0.9, glow: 18 });
  const KS = [39.83, -98.58], KSA = [-39.83, 81.42], STP = [-38.72, 77.53];
  push(gscene({
    t0: cChina, t1: cGag4, ovKey: 'ch2:china', install: (gl) => gl.setOverlay(ovChina),
    cam: (lt, t) => {
      const keys = [{ t: 0, lat: 30, lon: 88, alt: 3.0 }, { t: tm.china - cChina, lat: 35, lon: 104, alt: 2.6 }, { t: tm.test - cChina, lat: 36, lon: 108, alt: 2.55 },
        { t: tm.test - cChina + 0.45, lat: 52, lon: 175, alt: 3.3, ease: E.in }, { t: tm.kansas - cChina - 0.35, lat: 39, lon: -98, alt: 2.5, ease: E.out },
        { t: tm.kansas - cChina + 0.7, lat: 39.5, lon: -98.4, alt: 2.3 }, { t: cGag4 - cChina, lat: 38.2, lon: -98.6, alt: 0.95, tilt: 28 }];
      return camAt(keys, lt, 0.5);
    },
    look: (lt, t) => ({ ovAlpha: prog(t, tm.china - 0.25, tm.china + 0.2), dim: 0.22 * prog(t, tm.china - 0.25, tm.china + 0.2), desat: 0.15 }),
    draw2d: (ctx, lt, t, pj) => {
      if (t > tm.kansas - pre) {
        const q = pj.ll(...KS);
        if (q[2]) { L.pulse(ctx, q[0], q[1], t - tm.kansas + pre, { color: PAL.yellow, r: 9 }); F.pill(ctx, 'KANSAS', q[0] + 90, q[1] - 90, { anchor: 'left', leader: [q[0], q[1]], size: 42, alpha: prog(t, tm.kansas - pre, tm.kansas + 0.25) }); }
      }
      // whip blur
      const wk = env(t, tm.test - 0.05, tm.kansas - 0.35, 0.25, 0.3); L.streaks(ctx, W, H, wk * 0.8, false, 3);
    },
  }));
  sfx(tm.china - 0.1, 'pop_ui', -16);
  sfx(tm.test - 0.05, 'whoosh_big', -10);
  sfx(tm.kansas - 0.05, 'pop_ui', -14);

  // ======================= s031 I: gag 4a — the Explorer digs into Kansas =======================
  const dirt = (ctx, x, y, t, t0) => {
    const r = F.rng(17);
    for (let i = 0; i < 26; i++) {
      const st = t0 + r() * 1.0, ph = (t - st) / 0.7; if (ph < 0 || ph > 1) { r(); r(); r(); continue; }
      const ang = Math.PI * (0.1 + 0.8 * r()), sp = 90 + r() * 120, rr = 8 + r() * 16;
      const px = x + Math.cos(ang) * sp * ph * (r() > 0.5 ? 1 : -1), py = y - Math.sin(ang) * sp * ph * 0.8 + ph * ph * 90;
      ctx.fillStyle = `rgba(${150 + i % 3 * 20},${110 + i % 4 * 10},70,${0.85 * (1 - ph)})`; ctx.beginPath(); ctx.arc(px, py, rr * (0.6 + ph), 0, Math.PI * 2); ctx.fill();
    }
  };
  push({
    t0: cGag4, t1: cDrill, draw(ctx, lt, t) {
      const gr = ctx.createRadialGradient(W / 2, H * 0.62, 60, W / 2, H * 0.55, H * 1.05); gr.addColorStop(0, '#16305a'); gr.addColorStop(1, '#03050a'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
      const sink = prog(t, tm.dig + 0.75, tm.dig + 1.95, E.in);
      const y = -1.25 * sink;
      const k = prog(t, cGag4, cDrill, E.inOutSine);
      S.planet(ctx, t, { lat: KS[0], lon: KS[1], spin: 0.4 + 0.05 * k, hero: { pos: [0, y, 0], ry: 0.25 }, camAng: 0.32 - 0.08 * k, dist: lerp(5.0, 4.6, k), camH: 0.75, target: [0, 0.5, 0] });
      const gp = S.project(new S.THREE.Vector3(0.18, 0, 0.18));
      // beam from the hand into the ground
      const bk = env(t, tm.dig + 0.25, tm.dig + 2.0, 0.12, 0.3);
      if (bk > 0) {
        const hp = S.project(new S.THREE.Vector3(0.22, 0.45 + y, 0.22));
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
        for (const [lw, c] of [[34, 'rgba(61,227,255,0.12)'], [16, 'rgba(61,227,255,0.35)'], [5, 'rgba(230,252,255,0.95)']]) { ctx.strokeStyle = c; ctx.lineWidth = lw * bk; ctx.beginPath(); ctx.moveTo(hp.x, Math.min(hp.y, gp.y)); ctx.lineTo(gp.x, gp.y + 40); ctx.stroke(); }
        ctx.restore();
        L.glowDot(ctx, gp.x, gp.y, 110 * bk, PAL.cyan, 0.8);
      }
      if (t > tm.dig + 0.6) dirt(ctx, gp.x, gp.y, t, tm.dig + 0.6);
    },
  });
  sfx(tm.dig - 0.02, 'dig_shovel', -12);

  // ======================= s031 J: cut-away drill from Kansas with the Explorer riding the head =======================
  push({
    t0: cDrill, t1: cOcean, draw(ctx, lt, t) {
      const gr = ctx.createRadialGradient(W / 2, H / 2, 80, W / 2, H / 2, H); gr.addColorStop(0, '#12213b'); gr.addColorStop(1, '#03050a'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
      const k = prog(t, cDrill, cOcean, E.inOutSine);
      const p = prog(t, cDrill + 0.25, cOcean - 0.15, E.inOutSine);
      const a = Math.PI / 4 + 0.1 - 0.1 * k, d = lerp(11.5, 10.5, k);
      const r = S.cutaway(ctx, t, { lat: KS[0], lon: KS[1], p, spin: 2.2, rider: p > 0.01 && p < 0.985, cam: [Math.cos(a) * d, lerp(5.0, 3.8, k), Math.sin(a) * d], target: [0, -0.15 * k, 0] });
      const top = S.project(r.top), hd = S.project(r.end);
      L.pulse(ctx, top.x, top.y, t - cDrill, { color: PAL.yellow, r: 8, alpha: 1 - prog(t, cDrill + 1.5, cDrill + 2) });
      if (p > 0 && p < 1) L.glowDot(ctx, hd.x, hd.y, 60, PAL.cyan, 0.85);
    },
  });
  sfx(cDrill + 0.25, 'sonar_ping', -14);
  sfx(cDrill + 0.3, 'rumble_quake', -20);

  // ======================= s032 K: gag 4b — he pops out in the southern Indian Ocean =======================
  const bobScene = (t0, t1, popAt, opts = {}) => push({
    t0, t1, draw(ctx, lt, t) {
      const gr = ctx.createRadialGradient(W / 2, H * 0.62, 60, W / 2, H * 0.55, H * 1.05); gr.addColorStop(0, '#123a66'); gr.addColorStop(1, '#03060c'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
      const u = t - popAt;
      let y = -0.47 + 0.035 * Math.sin(t * 2.4), rz = 0.06 * Math.sin(t * 1.9);
      if (popAt != null && u < 0.85) { if (u < 0) y = -1.3; else if (u < 0.32) y = lerp(-1.3, 0.3, E.out(u / 0.32)); else y = lerp(0.3, -0.47, E.in((u - 0.32) / 0.53)); rz = 0; }
      const k = prog(t, t0, t1, E.inOutSine);
      S.planet(ctx, t, { lat: KSA[0], lon: KSA[1], spin: 1.1 + 0.06 * k, hero: { pos: [0, y, 0], ry: opts.ry ?? 0.3, rz }, camAng: (opts.ang ?? 0.3) - 0.06 * k, dist: opts.dist ?? 4.7, camH: 0.62, target: [0, 0.32, 0] });
      const wp = S.project(new S.THREE.Vector3(0, 0, 0));
      // ripple rings at the waterline
      for (let j = 0; j < 3; j++) { const ph = ((t * 0.55) + j / 3) % 1; ctx.strokeStyle = `rgba(210,240,255,${0.55 * (1 - ph)})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(wp.x, wp.y + 4, 60 + ph * 230, 14 + ph * 46, 0, 0, Math.PI * 2); ctx.stroke(); }
      if (popAt != null && u > -0.05 && u < 1.2) {
        const r = F.rng(5);
        for (let i = 0; i < 34; i++) { const ang = Math.PI * (0.15 + 0.7 * r()), sp = 260 + r() * 420, ph = clamp(u / 1.0); const px = wp.x + Math.cos(ang) * sp * ph * (i % 2 ? 1 : -1), py = wp.y - Math.sin(ang) * sp * ph + 520 * ph * ph; ctx.fillStyle = `rgba(220,245,255,${0.9 * (1 - ph)})`; ctx.beginPath(); ctx.arc(px, py, 6 + r() * 10, 0, Math.PI * 2); ctx.fill(); }
      }
      if (opts.pill) F.pill(ctx, 'INDIAN OCEAN', W / 2, 130, { anchor: 'center', size: 44, alpha: prog(t, tm.indian - pre, tm.indian + 0.25) });
    },
  });
  bobScene(cOcean, cIsl, tm.indian - 0.06, { pill: true });
  sfx(tm.indian - 0.02, 'splash_big', -10);

  // ======================= s032 L: globe over the antipode -> Ile Saint-Paul =======================
  push(gscene({
    t0: cIsl, t1: cFlat,
    cam: (lt, t) => camAt([{ t: 0, lat: -44, lon: 80.5, alt: 0.62, tilt: 30 }, { t: cFlat - cIsl, lat: -43.2, lon: 79.6, alt: 0.42, tilt: 40 }], lt, 0.4),
    look: () => ({ desat: 0.1, dim: 0.05 }),
    draw2d: (ctx, lt, t, pj) => {
      const a = pj.ll(...KSA), s = pj.ll(...STP);
      const pts = gcLine(KSA, STP, 60, 0).map(p => pj.ll(p.lat, p.lon)).filter(q => q[2]).map(q => [q[0], q[1]]);
      const dk = prog(t, tm.nearest - 0.05, tm.island - 0.1, E.inOut);
      if (dk > 0) F.glowPath(ctx, pts, { p: dk, color: '#ffffff', width: 3.5, dash: [16, 12] });
      L.pulse(ctx, a[0], a[1], t - cIsl, { color: PAL.yellow, r: 10 });
      if (t > tm.island - pre) { const pk = E.outBack(prog(t, tm.island - pre, tm.island + 0.25, E.lin)); L.glowDot(ctx, s[0], s[1], 30 * pk, '#ffffff', 0.9); ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(s[0], s[1], 5 * pk, 0, Math.PI * 2); ctx.fill(); }
      const swap = prog(t, tm.away - pre - 0.15, tm.away - pre);
      F.pill(ctx, 'INDIAN OCEAN', W / 2, 130, { anchor: 'center', size: 44, alpha: 1 - swap });
      F.pill(ctx, '200+ MILES TO THE NEAREST LAND', W / 2, 130, { anchor: 'center', size: 44, alpha: prog(t, tm.away - pre, tm.away + 0.2), border: 'rgba(255,255,255,0.5)' });
    },
  }));
  sfx(tm.island - 0.05, 'pop_ui', -14);

  // ======================= s033/s034 M: Equal Earth flat map — US vs China antipodes, Argentina =======================
  const usF = feat('USA'), argF = feat('Argentina');
  const usR = rings(usF), chR = rings(chinaF), arR = rings(argF);
  const saR = CTY.features.filter(f => f.properties.CONTINENT === 'South America').flatMap(f => rings(f));
  const chPath = L.eePath(chR), arPath = L.eePath(arR), saPath = L.eePath(saR);
  const usAnti = L.eePath(L.antiRings(usR)), chAnti = L.eePath(L.antiRings(chR)), arAnti = L.eePath(L.antiRings(arR));
  const usOrig = L.eePath(usR);
  const eeOut = L.eeOutline();
  const eqPath = (() => { const p = new Path2D(); const [x0, y0] = L.ee(-180, 0), [x1] = L.ee(180, 0); p.moveTo(x0, y0); p.lineTo(x1, y0); return { p, len: x1 - x0 }; })();
  const eeBase = im('tex/equal_earth.jpg'), eeGrey = im('ch2_ee_grey.jpg'), eeAntiImg = im('ch2_ee_anti.png');
  const vWorld = { cx: 1800, cy: 900, zoom: 1.04 };
  const vIndian = L.eeViewAt(60, -3, 1.3), vSA = L.eeViewAt(-68, -28, 2.15), vWorld2 = { cx: 1800, cy: 880, zoom: 1.06 };
  const tFlipUS0 = tm.us - pre, tFlipUS1 = tm.us + 1.0, tFlipCH0 = tm.start - pre, tFlipCH1 = tm.start + 1.1, tFlipAR0 = tm.arg - 0.6, tFlipAR1 = tm.arg + 0.25;
  const mView = (t) => {
    let v = lerpView(vWorld, vIndian, prog(t, cFlat, tm.hemi + 0.2, E.inOut));
    v = lerpView(v, vWorld, prog(t, tm.us - 0.5, tm.us + 0.4, E.inOut));
    v = lerpView(v, vIndian, prog(t, tFlipUS1 + 0.1, tm.china2 - 0.1, E.inOut));
    v = lerpView(v, vWorld2, prog(t, SEG('s034').start - 0.1, tm.start + 0.2, E.inOut));
    v = lerpView(v, vSA, prog(t, tm.four - 0.6, tm.four + 0.3, E.inOut));
    v = lerpView(v, vWorld2, prog(t, tm.dig2 + 0.1, tm.arg - 0.3, E.inOut));
    const dz = 1 + 0.012 * Math.sin(t * 0.6); return { cx: v.cx + 6 * Math.sin(t * 0.3), cy: v.cy, zoom: v.zoom * dz };
  };
  const lerpView = L.lerpView;
  const strokeImg = (ctx, z, path, col, lw, p = 1, len = 1) => {
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (p < 1) ctx.setLineDash([len * p, len * 2]);
    ctx.strokeStyle = col + '40'; ctx.lineWidth = lw * 3 / z; ctx.stroke(path); ctx.strokeStyle = col; ctx.lineWidth = lw / z; ctx.stroke(path); ctx.restore();
  };
  push({
    t0: cFlat, t1: cBob, draw(ctx, lt, t) {
      ctx.fillStyle = '#04070d'; ctx.fillRect(0, 0, W, H);
      const v = mView(t);
      L.drawEEImg(ctx, eeBase, v, W, H, 0.55 + 0.45 * (1 - prog(t, cFlat, cFlat + 0.6)));
      ctx.fillStyle = 'rgba(4,8,16,0.38)'; ctx.fillRect(0, 0, W, H);
      L.withEE(ctx, v, (z) => {
        ctx.save(); ctx.clip(eeOut);
        // China (orange)
        const cA = prog(t, cFlat, cFlat + 0.4);
        ctx.globalAlpha = 0.8 * cA; ctx.fillStyle = PAL.hero; ctx.fill(chPath.path); ctx.globalAlpha = 1; strokeImg(ctx, z, chPath.path, '#ffffff', 1.6);
        // equator flash
        const eqA = env(t, tm.hemi - pre, tm.hemi + 1.6, 0.15, 0.5);
        if (eqA > 0) { ctx.save(); ctx.globalAlpha = eqA; ctx.setLineDash([]); ctx.strokeStyle = PAL.yellow + '55'; ctx.lineWidth = 14 / z; ctx.stroke(eqPath.p); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 4 / z; ctx.stroke(eqPath.p); ctx.restore(); }
        // Kansas antipode marker (yellow) stays from the previous shot until the US flip
        // US flip: original outline -> antipode (cyan)
        const fk = prog(t, tFlipUS0, tFlipUS1, E.inOut), usA = 1 - prog(t, tm.start - 0.6, tm.start - 0.1);
        if (t > tFlipUS0 - 0.6 && usA > 0) {
          ctx.globalAlpha = usA;
          if (fk < 1) { const pth = L.eePath(L.flipRings(usR, fk)).path; ctx.globalAlpha = usA * 0.55; ctx.fillStyle = PAL.cyan; ctx.fill(pth); ctx.globalAlpha = usA; strokeImg(ctx, z, pth, '#E8FBFF', 1.6); }
          else { ctx.globalAlpha = usA * 0.62; ctx.fillStyle = PAL.cyan; ctx.fill(usAnti.path); ctx.globalAlpha = usA; strokeImg(ctx, z, usAnti.path, '#E8FBFF', 1.8); }
          ctx.globalAlpha = 1;
        }
        // China antipode (cyan over water, yellow over land)
        const ck = prog(t, tFlipCH0, tFlipCH1, E.inOut);
        if (t > tFlipCH0) {
          if (ck < 1) { const pth = L.eePath(L.flipRings(chR, ck)).path; ctx.globalAlpha = 0.5; ctx.fillStyle = PAL.cyan; ctx.fill(pth); ctx.globalAlpha = 1; strokeImg(ctx, z, pth, '#E8FBFF', 1.8); }
          else {
            const fill = prog(t, tm.four - pre, tm.four + 0.35);
            ctx.globalAlpha = 0.25 + 0.4 * fill; ctx.fillStyle = PAL.cyan; ctx.fill(chAnti.path); ctx.globalAlpha = 1;
            if (fill > 0) { ctx.save(); ctx.clip(chAnti.path); ctx.globalAlpha = 0.9 * fill; ctx.fillStyle = PAL.yellow; ctx.fill(saPath.path); ctx.restore(); }
            strokeImg(ctx, z, chAnti.path, '#E8FBFF', 1.8);
          }
        }
        // Argentina orange + its antipode landing on China
        if (t > tm.dig2 - 0.3) {
          const aa = prog(t, tm.arg - pre - 0.25, tm.arg);
          ctx.globalAlpha = 0.9 * aa; ctx.fillStyle = PAL.hero; ctx.fill(arPath.path); ctx.globalAlpha = 1; if (aa > 0) strokeImg(ctx, z, arPath.path, '#ffffff', 1.6);
          if (t > tFlipAR0) {
            const ak = prog(t, tFlipAR0, tFlipAR1, E.inOut);
            if (ak < 1) { const pth = L.eePath(L.flipRings(arR, ak)).path; strokeImg(ctx, z, pth, '#ffffff', 2); }
            else { ctx.save(); ctx.clip(chPath.path); ctx.globalAlpha = 0.95 * prog(t, tFlipAR1, tFlipAR1 + 0.3); ctx.fillStyle = PAL.yellow; ctx.fill(arAnti.path); ctx.restore(); strokeImg(ctx, z, arAnti.path, '#ffffff', 2); }
          }
        }
        ctx.restore();
      }, W, H);
      // Kansas antipode marker
      const ka = L.eeScr(KSA[1], KSA[0], v, W, H);
      L.pulse(ctx, ka[0], ka[1], t - cFlat, { color: PAL.yellow, r: 8, alpha: 1 - prog(t, tm.start - 0.6, tm.start - 0.2) });
      // texts
      const p1 = prog(t, tm.china2 - 0.75, tm.china2 - 0.45) * (1 - prog(t, tm.start - 0.5, tm.start - 0.2));
      F.pill(ctx, 'US AND CHINA: ZERO OVERLAP', 140, 110, { anchor: 'left', size: 42, alpha: p1 });
      const sa = 1 - prog(t, tm.start - 0.5, tm.start - 0.2);
      if (t > tm.china2 - pre && sa > 0) L.juiceStamp(ctx, W / 2 + 360, 330, t - (tm.china2 - pre), 'FALSE', { size: 74, alpha: sa, spin: 0.6 });
      // shovel taps Argentina
      if (t > tm.dig2 - pre && t < tm.arg + 0.4) {
        const ap = L.eeScr(-65, -38, v, W, H); const tap = Math.abs(Math.sin((t - tm.dig2) * 9)) * (1 - prog(t, tm.arg, tm.arg + 0.4));
        L.shovelIcon(ctx, ap[0] + 40, ap[1] - 70 - 14 * tap, 110, prog(t, tm.dig2 - pre, tm.dig2 + 0.15) * (1 - prog(t, tm.arg + 0.2, tm.arg + 0.4)), 0.5 - 0.35 * tap);
      }
      // Kenney mini pops out of a hole in China
      if (t > tm.arg - 0.1) {
        const cp = L.eeScr(112, 34, v, W, H);
        const hk = prog(t, tm.arg - 0.1, tm.arg + 0.1);
        ctx.fillStyle = `rgba(20,12,8,${0.85 * hk})`; ctx.beginPath(); ctx.ellipse(cp[0], cp[1], 34 * hk, 11 * hk, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = `rgba(255,210,63,${0.8 * hk})`; ctx.lineWidth = 3; ctx.stroke();
        const rise = E.outBack(prog(t, tm.arg, tm.arg + 0.35, E.lin));
        S.comp(ctx, t, 'mini', cp[0], cp[1] + 6 + 110 * (1 - rise), 120, { ry: 0.1, clipY: cp[1] + 6, camY: 0.5 });
      }
      L.arrowPill(ctx, 'ARGENTINA', 'CHINA', W / 2, 110, { size: 44, alpha: prog(t, tm.arg - pre, tm.arg + 0.25), border: 'rgba(255,90,54,0.6)' });
    },
  });
  sfx(cFlat, 'whoosh_soft', -14);
  sfx(tm.hemi - 0.05, 'shimmer', -18);
  sfx(tm.us - 0.05, 'whoosh_soft', -16);
  sfx(tm.china2 - 0.08, 'stamp', -10);
  sfx(tm.start - 0.05, 'whoosh_soft', -16);
  sfx(tm.four - 0.05, 'pop_ui', -16);
  sfx(tm.arg - 0.05, 'bell_small', -14);

  // ======================= s034 N: still bobbing alone at sea =======================
  bobScene(cBob, cAnti, null, { ry: -0.2, ang: 0.55, dist: 4.4 });
  sfx(cBob, 'crickets', -20);

  // ======================= s035 O: flip every continent (Equal Earth antipode overlay) =======================
  const ovPairs = [
    { at: tm.orig - pre, pts: [[110, 35], [-62, -30]] },
    { at: tm.orig + 0.62, pts: [[-45, 75], [60, -78]] },
    { at: tm.orig + 1.24, pts: [[-4, 40], [174, -41]] },
  ];
  push({
    t0: cAnti, t1: cWaf, draw(ctx, lt, t) {
      ctx.fillStyle = '#04070d'; ctx.fillRect(0, 0, W, H);
      const pz = ovPairs[2].zoom || [-4, 38, 1.0]; const zk = ovPairs[2].zoom ? env(t, ovPairs[2].at - 0.1, tm.eighth - 0.05, 0.4, 0.4) : 0;
      let v = lerpView({ cx: 1800, cy: 880, zoom: 1.03 + 0.03 * prog(t, cAnti, cWaf) }, L.eeViewAt(pz[0], pz[1], pz[2]), zk * E.inOut(1));
      v = lerpView({ cx: 1800, cy: 880, zoom: 1.03 + 0.03 * prog(t, cAnti, cWaf) }, L.eeViewAt(pz[0], pz[1], pz[2]), E.inOut(zk));
      L.drawEEImg(ctx, eeGrey, v, W, H);
      // left-to-right wipe of the cyan/yellow antipode layer
      const wk = prog(t, tm.flipall - pre, tm.lay, E.inOut);
      if (wk > 0) {
        const a = L.eeAff(v, W, H), xw = a.ox + 3600 * a.z * wk;
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, Math.max(0, xw), H); ctx.clip();
        ctx.globalAlpha = 0.92; ctx.drawImage(eeAntiImg, a.ox, a.oy, 3600 * a.z, 1760 * a.z); ctx.restore();
        if (wk < 1) { const g2 = ctx.createLinearGradient(xw - 60, 0, xw + 6, 0); g2.addColorStop(0, 'rgba(61,227,255,0)'); g2.addColorStop(1, 'rgba(220,250,255,0.9)'); ctx.fillStyle = g2; ctx.fillRect(xw - 60, 0, 66, H); }
      }
      // overlap pulses
      for (const pr of ovPairs) {
        if (t < pr.at) continue;
        for (const [lo, la] of pr.pts) { const q = L.eeScr(lo, la, v, W, H); const u = t - pr.at; for (let j = 0; j < 2; j++) { const ph = clamp(u * 0.9 - j * 0.25); if (ph <= 0 || ph >= 1) continue; L.ring(ctx, q[0], q[1], 20 + ph * 120, PAL.yellow, 4, 1 - ph); } L.glowDot(ctx, q[0], q[1], 90, PAL.yellow, 0.45 * env(u, 0, 1.6, 0.1, 0.8)); }
      }
      // hero counter
      const ck = prog(t, tm.eighth - 0.55, tm.eighth - 0.02, E.outExpo);
      if (t > tm.eighth - 0.7) {
        const ca = prog(t, tm.eighth - 0.7, tm.eighth - 0.4);
        ctx.fillStyle = `rgba(3,5,10,${0.5 * ca})`; ctx.fillRect(0, 0, W, H);
        F.text(ctx, 'ONLY ABOUT', W / 2, 380, { size: 48, fam: F.FAM.label, weight: 700, tracking: 0.3, align: 'center', color: PAL.sub, alpha: ca });
        F.counter(ctx, 2, 8, ck, W / 2, 610, { size: 230, prefix: '1 IN ', alpha: ca, format: v => String(Math.round(v)), color: PAL.yellow });
      }
    },
  });
  sfx(tm.flipall - 0.1, 'whoosh_soft', -14);
  ovPairs.forEach(p => sfx(p.at, 'shimmer', -16));
  sfx(tm.eighth - 0.55, 'tick_counter', -16);

  // ======================= s036 P: waffle data card =======================
  const wr = F.rng(321); const ordL = [...Array(100).keys()], ordR = [...Array(100).keys()];
  for (let i = 99; i > 0; i--) { let j = Math.floor(wr() * (i + 1)); [ordL[i], ordL[j]] = [ordL[j], ordL[i]]; j = Math.floor(wr() * (i + 1)); [ordR[i], ordR[j]] = [ordR[j], ordR[i]]; }
  push({
    t0: cWaf, t1: cCap, draw(ctx, lt, t) {
      navyBg(ctx, t);
      const gs = 46, gap = 9, gw = 10 * gs + 9 * gap; const tops = 250;
      const gx = [W / 2 - 90 - gw, W / 2 + 90];
      const lightA = cWaf + 0.55, lightB = tm.random - 0.75; const sortAt = tm.random - 0.55, sortE = tm.random - 0.05;
      [[29, ordL, 'IF RANDOM', PAL.sub], [13, ordR, 'REAL EARTH', PAL.text]].forEach(([n, ord, lab, lc], gi) => {
        const x0 = gx[gi], pop = E.outBack(prog(t, cWaf + gi * 0.12, cWaf + 0.45 + gi * 0.12, E.lin));
        F.text(ctx, lab, x0 + gw / 2, tops - 50, { size: 48, fam: F.FAM.label, weight: 700, tracking: 0.18, align: 'center', color: gi ? PAL.yellow : PAL.text, alpha: prog(t, cWaf + 0.1, cWaf + 0.4) });
        const lit = Math.floor(n * prog(t, lightA, lightB, E.inOutSine) + 1e-6);
        const sk = prog(t, sortAt, sortE, E.inOut);
        for (let i = 0; i < 100; i++) {
          const rank = ord.indexOf(i); const on = rank < lit;
          // sorted position: lit squares settle into the bottom rows (reading order from the bottom-left)
          let col = i % 10, row = Math.floor(i / 10);
          if (on && sk > 0) { const tr = 9 - Math.floor(rank / 10), tc = rank % 10; col = lerp(col, tc, sk); row = lerp(row, tr, sk); }
          else if (!on && sk > 0) { /* unlit stay */ }
          const x = x0 + col * (gs + gap), y = tops + row * (gs + gap);
          ctx.save(); ctx.translate(x + gs / 2, y + gs / 2); ctx.scale(pop, pop);
          if (on) { const fl = 1 - prog(t, lightA + (rank / n) * (lightB - lightA), lightA + (rank / n) * (lightB - lightA) + 0.25); ctx.fillStyle = PAL.yellow; F.round(ctx, -gs / 2, -gs / 2, gs, gs, 7); ctx.fill(); if (fl > 0) { ctx.fillStyle = `rgba(255,255,255,${0.8 * fl})`; ctx.fill(); } }
          else if (!(sk > 0 && ord.indexOf(9 - Math.floor(i / 10)) < 0)) { ctx.fillStyle = 'rgba(160,190,230,0.13)'; F.round(ctx, -gs / 2, -gs / 2, gs, gs, 7); ctx.fill(); }
          ctx.restore();
        }
      });
      // half line + bracket (right grid stays under half of the left)
      const bk = prog(t, tm.random - pre, tm.random + 0.5, E.out);
      if (bk > 0) {
        const yBot = tops + 10 * (gs + gap) - gap, yHalf = yBot - 1.45 * (gs + gap);
        ctx.save(); ctx.setLineDash([16, 10]); ctx.strokeStyle = `rgba(255,255,255,${0.9 * bk})`; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(gx[0] - 20, yHalf); ctx.lineTo(lerp(gx[0] - 20, gx[1] + gw + 20, bk), yHalf); ctx.stroke(); ctx.setLineDash([]);
        const bx = gx[1] + gw + 34; ctx.lineWidth = 5; ctx.strokeStyle = '#ffffff'; ctx.globalAlpha = bk; ctx.beginPath(); ctx.moveTo(bx - 14, yHalf); ctx.lineTo(bx, yHalf); ctx.lineTo(bx, yBot); ctx.lineTo(bx - 14, yBot); ctx.stroke();
        ctx.restore();
      }
    },
  });
  sfx(cWaf + 0.5, 'tick_counter', -16);
  sfx(tm.random - 0.05, 'pop_ui', -16);

  // ======================= s037/s038 Q,R: hemisphere cap search -> best half (40N 2E) =======================
  const cap = new Cap(im('ch2_landmask.png'));
  const capIns = (gl) => { gl.setOverlay(cap.cv); };
  const capRefresh = (gl) => { if (gl.u.ovTex.value?.image !== cap.cv) gl.setOverlay(cap.cv); else gl.refreshOverlay(); };
  const ORANGE = [255, 90, 54, 0.9], CYAN = (a) => [61, 227, 255, a], DARK = [4, 8, 18, 0.42], DARKL = [40, 40, 48, 0.42];
  const WP = [[tm.half - 0.05, 5, 100], [tm.half + 1.2, 30, -80], [tm.cram + 0.1, -18, -15], [tm.cram + 0.75, 52, 65], [tm.cram + 1.35, -8, -48],
    [tm.cram + 1.95, 32, 48], [tm.cram + 2.55, 55, -22], [tm.cram + 3.25, 30, 18], [tm.cram + 4.0, 44, -6], [tm.europe - 0.05, 40, 2]];
  const capAt = (t) => {
    if (t <= WP[0][0]) return L.dir(WP[0][1], WP[0][2]);
    for (let i = 0; i < WP.length - 1; i++) { const a = WP[i], b = WP[i + 1]; if (t <= b[0]) { const k = E.inOutSine(clamp((t - a[0]) / (b[0] - a[0]))); const A = L.dir(a[1], a[2]), B = L.dir(b[1], b[2]); const R = L.rotAB(A, B, k); return L.rotVec(A, R); } }
    return L.dir(40, 2);
  };
  const capOn = (t) => prog(t, tm.half - pre, tm.half + 0.4);
  push(gscene({
    t0: cCap, t1: cSettle, ovKey: 'ch2:cap', install: capIns,
    pre: (lt, t, gl) => { const a = capOn(t); if (cap.draw(capAt(t), { inL: ORANGE, inO: CYAN(0.25), outL: [ORANGE[0], ORANGE[1], ORANGE[2], 0], outO: [0, 0, 0, 0], edge: [255, 255, 255, 0.95 * a], edgeW: 0.012 })) capRefresh(gl); },
    cam: (lt, t) => camAt([{ t: 0, lat: 18, lon: 30, alt: 3.3 }, { t: cSettle - cCap, lat: 24, lon: -12, alt: 3.15 }], lt, 0.6),
    look: (lt, t) => ({ ovAlpha: capOn(t), dim: 0.25 * capOn(t), desat: 0.25 }),
    draw2d: (ctx, lt, t, pj) => {
      const pa = env(t, tm.puzzle - pre, tm.half + 0.2, 0.25, 0.4);
      if (pa > 0) { const pk = E.outBack(prog(t, tm.puzzle - pre, tm.puzzle + 0.3, E.lin)); L.puzzleIcon(ctx, 1500, 300, 150 * pk, PAL.hero, pa, 0.25 * Math.sin((t - tm.puzzle) * 3)); }
    },
  }));
  sfx(tm.puzzle - 0.05, 'pop_ui', -14);
  sfx(tm.half - 0.05, 'whoosh_soft', -16);
  sfx(tm.cram - 0.05, 'whoosh_soft', -18);
  push(gscene({
    t0: cSettle, t1: cTiles + 0.6, ovKey: 'ch2:cap', install: capIns,
    pre: (lt, t, gl) => { const fl = prog(t, tm.still - pre, tm.still + 0.45); const gl2 = 0.9 + 0.1 * env(t, tm.scoops - 0.1, tm.scoops + 1.4, 0.3, 0.5); if (cap.draw(L.dir(40, 2), { inL: [255, 90 + 40 * (gl2 - 0.9) * 10, 54, gl2], inO: [lerp(61, 40, fl), lerp(227, 200, fl), 255, lerp(0.25, 0.68, fl)], outL: [0, 0, 0, 0], outO: [0, 0, 0, 0], edge: [255, 255, 255, 0.95], edgeW: 0.012 })) capRefresh(gl); },
    cam: (lt, t) => camAt([{ t: 0, lat: 24, lon: -12, alt: 3.15, tilt: 0 }, { t: cTiles + 0.6 - cSettle, lat: 33, lon: -14, alt: 2.55, tilt: 12 }], lt, 0.4),
    look: () => ({ ovAlpha: 1, dim: 0.3, desat: 0.25 }),
    draw2d: (ctx, lt, t, pj) => {
      const c = pj.ll(40, 2); if (c[2]) L.pulse(ctx, c[0], c[1], t - cSettle, { color: '#ffffff', r: 7, alpha: 1 - prog(t, tm.still - 0.5, tm.still) });
      F.pill(ctx, 'BEST HALF: STILL MOSTLY WATER', W / 2, 110, { anchor: 'center', size: 44, alpha: prog(t, tm.still - pre, tm.still + 0.25), border: 'rgba(61,227,255,0.7)' });
    },
  }));
  sfx(tm.europe - 0.1, 'pop_ui', -14);
  sfx(tm.still - 0.03, 'impact_short', -10);

  // ======================= s039 S: 2x3 grid of cap tiles with red X stamps =======================
  const TILES = [[45, 90], [5, 20], [45, -100], [-15, -60], [-90, 0], [-25, 135]];
  let tileCache = null;
  const renderTile = async (clat, clon, colours, camLL) => {
    const c = L.dir(clat, clon); cap.draw(c, colours); g.setOverlay(cap.cv); api._ovOwner = 'ch2:tiles';
    const cv = makeCanvas(W, H); const cx = cv.getContext('2d');
    api.drawGlobe(cx, { lat: camLL[0], lon: camLL[1], alt: 2.5, tilt: 0, heading: 0, starAlpha: 0 }, Object.assign({}, LOOK0, { ovAlpha: 1, dim: 0.28, desat: 0.25 }));
    const pj = L.projector(g); const dc = pj.disc(); const s = Math.ceil(dc.r * 2 + 24);
    const tile = makeCanvas(420, 420); const tc = tile.getContext('2d'); tc.drawImage(cv, dc.x - s / 2, dc.y - s / 2, s, s, 0, 0, 420, 420);
    return tile;
  };
  const tileCols = { inL: ORANGE, inO: CYAN(0.6), outL: [30, 30, 36, 0.45], outO: [0, 0, 0, 0.45], edge: [255, 255, 255, 0.95], edgeW: 0.014 };
  const getTiles = async () => {
    if (tileCache) return tileCache;
    const out = [];
    for (const [la, lo] of TILES) out.push(await renderTile(la, lo, tileCols, la < -80 ? [-55, 10] : [clamp(la - 12, -60, 60), lo - 28]));
    const water = await renderTile(-40, -178, { inL: ORANGE, inO: [0, 150, 215, 0.75], outL: [30, 30, 36, 0.45], outO: [0, 0, 0, 0.45], edge: [255, 255, 255, 0.95], edgeW: 0.014 }, [-34, -165]);
    tileCache = { tiles: out, water }; api._ovOwner = 'ch2:tiles-done'; return tileCache;
  };
  const xTimes = TILES.map((_, i) => lerp(tm.cut + 0.25, tm.mostly - pre, i / 5));
  push({
    t0: cTiles, t1: cFlip, async draw(ctx, lt, t) {
      const TC = await getTiles();
      const sk = prog(t, cTiles, tm.cut + 0.15, E.outExpo); const ox = W * (1 - sk);
      ctx.save(); ctx.translate(ox, 0);
      navyBg(ctx, t);
      const ts = 340, gx = 70, gy = 40, x0 = W / 2 - (3 * ts + 2 * gx) / 2, y0 = 205;
      TC.tiles.forEach((tile, i) => {
        const cxp = x0 + (i % 3) * (ts + gx) + ts / 2, cyp = y0 + Math.floor(i / 3) * (ts + gy) + ts / 2;
        const dr = 1 + 0.02 * Math.sin(t * 0.8 + i), rot = 0.03 * Math.sin(t * 0.5 + i * 1.3);
        ctx.save(); ctx.translate(cxp, cyp); ctx.rotate(rot); ctx.scale(dr, dr); ctx.drawImage(tile, -ts / 2, -ts / 2, ts, ts); ctx.restore();
        if (t > xTimes[i]) L.xStamp(ctx, cxp, cyp, t - xTimes[i], 150);
      });
      ctx.restore();
      F.pill(ctx, 'NO HALF IS MOSTLY LAND', W / 2, 115, { anchor: 'center', size: 46, alpha: prog(t, tm.mostly - pre, tm.mostly + 0.25), border: 'rgba(255,59,59,0.7)' });
    },
  });
  sfx(cTiles, 'whoosh_soft', -14);
  xTimes.forEach(x => sfx(x, 'stamp', -16));

  // ======================= s040 T: flip to the water half (89%) =======================
  const W0 = L.dir(40, 2), W1 = L.dir(-40, -178);
  const flipAxis = (() => { const m = L.dir(0, -88); const a = [W0[1] * m[2] - W0[2] * m[1], W0[2] * m[0] - W0[0] * m[2], W0[0] * m[1] - W0[1] * m[0]]; const n = Math.hypot(...a); return a.map(v => v / n); })();
  const tF0 = tm.flip - 0.75, tF1 = tm.flip + 0.35;
  push(gscene({
    t0: cFlip, t1: cPac, ovKey: 'ch2:cap', install: capIns,
    pre: (lt, t, gl) => {
      const dk = prog(t, tF1 - 0.1, tF1 + 0.5);
      if (cap.draw(W1, { inL: ORANGE, inO: [lerp(20, 0, dk), lerp(40, 150, dk), lerp(70, 215, dk), lerp(0.35, 0.78, dk)], outL: ORANGE, outO: CYAN(0.6), edge: [255, 255, 255, 0.95], edgeW: 0.012 })) capRefresh(gl);
    },
    cam: (lt, t) => {
      const k = prog(t, tF0, tF1, E.inOutExpo); const v = L.rotVec(W0, { ax: flipAxis, th: Math.PI * k }); const [la, lo] = L.ll(v);
      const zk = prog(t, tm.nz - 0.6, tm.nz + 0.8, E.inOut);
      return { lat: lerp(la, -42, zk), lon: lerp(lo, lo < 0 && lo > -180 ? lo : lo, 1) + (zk > 0 ? 0 : 0), alt: lerp(2.8 + 0.4 * Math.sin(Math.PI * k), 2.0, zk) * (1 + 0.006 * Math.sin(t * 0.7)), heading: (t - cFlip) * 0.6, lookOffset: [0.22 * (1 - zk), 0], tilt: 10 * zk };
    },
    look: () => ({ ovAlpha: 1, dim: 0.3, desat: 0.25 }),
    draw2d: (ctx, lt, t, pj) => {
      L.streaks(ctx, W, H, env(t, tF0 + 0.1, tF1, 0.2, 0.3) * 0.8, false, 9);
      const ck = prog(t, tm.p89 - 1.0, tm.p89 - 0.03, E.out);
      const ca = prog(t, tm.p89 - 1.1, tm.p89 - 0.8) * (1 - prog(t, tm.nz - 0.6, tm.nz - 0.2));
      F.pill(ctx, 'THE WATER HALF', 1460, 330, { anchor: 'center', size: 44, alpha: ca, border: 'rgba(61,227,255,0.7)' });
      F.counter(ctx, 0, 89, ck, 1460, 560, { size: 200, unit: '% OCEAN', alpha: ca, color: PAL.cyan, unitColor: PAL.text });
      if (t > tm.p89) L.glowDot(ctx, 1400, 500, 260, PAL.cyan, 0.35 * (1 - prog(t, tm.p89, tm.p89 + 0.8)) * ca);
      if (t > tm.nz - pre) { const q = pj.ll(-41.5, 173); if (q[2]) L.pulse(ctx, q[0], q[1], t - tm.nz + pre, { color: PAL.hero, r: 8 }); }
    },
  }));
  sfx(tF0, 'whoosh_big', -10);
  sfx(tm.p89 - 1.0, 'tick_counter', -16);
  sfx(tm.p89 - 0.03, 'impact_deep', -8);

  // ======================= s041 U: the Pacific swallows every continent (+ gag 5) =======================
  const pour = new Pour(im('ch2_pacific.png'), DATA.pacific);
  const pac = L.dir(...DATA.pacific.centroid);
  const C_ = DATA.continents;
  const drops = [['north america', tm.drop - 0.05, 1.05], ['south america', tm.drop + 0.4, 1.05], ['europe', tm.drop + 0.85, 1.1], ['africa', tm.drop + 1.3, 1.1],
    ['antarctica', tm.drop + 1.75, 1.1], ['australia', tAusL, tAusA - tAusL], ['asia', tAsiaL, tAsiaA - tAsiaL]].map(([n, t0, d]) => ({ n, t0, t1: t0 + d, X: L.ringsXYZ(C_[n].rings), c: L.dir(...C_[n].centroid), area: C_[n].area }));
  drops.forEach((d, i) => sfx(d.t1 - 0.02, 'thunk_heavy', i === drops.length - 1 ? -8 : -14));
  const pourArea = (t) => { let a = 0; for (const d of drops) a += d.area * prog(t, d.t1 - 0.05, d.t1 + 0.55, E.out); return a; };
  const heroEnd = L.dir(-48, -80);
  push(gscene({
    t0: cPac, t1: cMont, ovKey: 'ch2:pour', install: (gl) => gl.setOverlay(pour.cv),
    pre: (lt, t, gl) => { if (pour.draw(pourArea(t), prog(t, tm.alone - pre, tm.alone + 1.1, E.inOut), 1)) { if (gl.u.ovTex.value?.image !== pour.cv) gl.setOverlay(pour.cv); else gl.refreshOverlay(); } },
    cam: (lt, t) => camAt([{ t: 0, lat: -5, lon: -160, alt: 2.6 }, { t: tm.drop - cPac, lat: -5, lon: -160, alt: 2.7 }, { t: tm.drop + 1.6 - cPac, lat: -8, lon: -158, alt: 3.15 },
      { t: tAsiaA - cPac, lat: -8, lon: -156, alt: 3.2 }, { t: cMont - cPac, lat: -28, lon: -122, alt: 3.65 }], lt, 0.3),
    look: (lt, t) => ({ ovAlpha: 1, dim: 0.2 + 0.1 * prog(t, tm.drop, tm.drop + 1), desat: 0.2 }),
    draw2d: (ctx, lt, t, pj) => {
      // flying continents
      let heroAt = null;
      for (const d of drops) {
        if (t < d.t0 - 0.25 || t > d.t1 + 0.45) continue;
        const k = prog(t, d.t0, d.t1, E.inOut); const R = L.rotAB(d.c, pac, k);
        const cc = L.rotVec(d.c, R); if (!pj.xyz(cc[0], cc[1], cc[2], false)[2]) continue;
        const melt = prog(t, d.t1 - 0.05, d.t1 + 0.4, E.in);
        let arrs = d.X.map(a => L.rotXYZ(a, R));
        if (melt > 0) arrs = arrs.map(a => { const o = new Float32Array(a.length); for (let i = 0; i < a.length; i += 3) { const x = lerp(a[i], pac[0], melt * 0.85), y = lerp(a[i + 1], pac[1], melt * 0.85), z = lerp(a[i + 2], pac[2], melt * 0.85), n = Math.hypot(x, y, z); o[i] = x / n; o[i + 1] = y / n; o[i + 2] = z / n; } return o; });
        const path = L.globePath(pj, arrs, true);
        const lift = Math.sin(Math.PI * k) * 14;
        ctx.save(); ctx.translate(0, -lift); ctx.globalAlpha = (1 - melt) * prog(t, d.t0 - 0.25, d.t0 + 0.05);
        ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.translate(0, lift + 10); ctx.fill(path); ctx.translate(0, -lift - 10);
        ctx.fillStyle = d.n === 'asia' ? '#FF6A3D' : PAL.hero; ctx.fill(path); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.stroke(path); ctx.restore();
        if (d.n === 'australia' && t < d.t1) { const c = L.rotVec(d.c, R); const q = pj.xyz(c[0], c[1], c[2], true); heroAt = [q[0], q[1] - lift]; }
      }
      // Explorer: rides Australia, then is pushed to the blue rim by Asia's splash and waves
      if (t >= tAusL - 0.25) {
        let hx, hy;
        if (heroAt) [hx, hy] = heroAt;
        else {
          const k2 = prog(t, tAsiaA + 0.05, tAsiaA + 0.8, E.out); const R = L.rotAB(pac, heroEnd, 0.15 + 0.85 * k2); const v = L.rotVec(pac, R); const q = pj.xyz(v[0], v[1], v[2], true); hx = q[0]; hy = q[1];
        }
        S.comp(ctx, t, 'hero', hx, hy, 205, { ry: 0.35, alpha: prog(t, tAusL - 0.25, tAusL + 0.1) });
        if (t > tAsiaA - 0.05 && t < tAsiaA + 1.1) { const u = (t - tAsiaA) / 1.1; for (let j = 0; j < 3; j++) { const ph = clamp(u * 1.2 - j * 0.15); if (ph <= 0 || ph >= 1) continue; const pp = pj.xyz(...pac, true); L.ring(ctx, pp[0], pp[1], 40 + ph * 420, '#FFD9B0', 6 * (1 - ph), 1 - ph); } }
      }
      F.pill(ctx, 'PACIFIC > ALL LAND COMBINED', W / 2, 105, { anchor: 'center', size: 44, alpha: prog(t, tm.spare - pre - 0.2, tm.spare + 0.2), border: 'rgba(61,227,255,0.7)' });
    },
  }));
  sfx(tm.alone - 0.05, 'shimmer', -16);

  // ======================= s042 V: callback montage =======================
  const tMont2 = tm.landb - pre, tMont3 = tm.avoidl - pre, tMont4 = tm.avoidl + 1.25;
  push({
    t0: cMont, t1: cDrip + 0.05, async draw(ctx, lt, t) {
      if (t < tMont2) { navyBg(ctx, t); const k = prog(t, cMont, tMont2); drawDisc(ctx, discN, W / 2, H / 2 + 20, lerp(330, 360, k), t * 0.12); tintCenter(ctx, W / 2, H / 2 + 20, 200, PAL.cyan, 0.45); }
      else if (t < tMont3) { navyBg(ctx, t); const k = prog(t, tMont2, tMont3); drawDisc(ctx, discS, W / 2, H / 2 + 20, lerp(330, 360, k), -t * 0.12); tintCenter(ctx, W / 2, H / 2 + 20, 220, PAL.hero, 0.45); }
      else if (t < tMont4) {
        ctx.fillStyle = '#04070d'; ctx.fillRect(0, 0, W, H); const k = prog(t, tMont3, tMont4, E.inOutSine);
        const v = { cx: 1800 + 120 * k, cy: 880, zoom: lerp(1.08, 1.22, k) }; L.drawEEImg(ctx, eeGrey, v, W, H); const a = L.eeAff(v, W, H); ctx.globalAlpha = 0.92; ctx.drawImage(eeAntiImg, a.ox, a.oy, 3600 * a.z, 1760 * a.z); ctx.globalAlpha = 1;
      } else {
        const TC = await getTiles(); navyBg(ctx, t); const k = prog(t, tMont4, cDrip, E.inOutSine); const s = lerp(820, 900, k);
        ctx.save(); ctx.translate(W / 2, H / 2 + 10); ctx.rotate(0.05 * k); ctx.drawImage(TC.water, -s / 2, -s / 2, s, s); ctx.restore();
      }
      const fl = Math.max(1 - prog(t, tMont2, tMont2 + 0.12), 1 - prog(t, tMont3, tMont3 + 0.12), 1 - prog(t, tMont4, tMont4 + 0.12));
      if (fl > 0 && t > tMont2) { ctx.fillStyle = `rgba(255,255,255,${0.18 * fl})`; ctx.fillRect(0, 0, W, H); }
    },
  });
  [cMont, tMont2, tMont3, tMont4].forEach(x => sfx(x, 'whoosh_soft', -16));

  // ======================= s042 W: back to the cold-open drip globe =======================
  const ovDrip = makeCanvas(2048, 1024);
  fillEquirect(ovDrip, [-180, -90, 180, 90], [...(await region('south america')), ...(await region('africa')), ...(await region('india'))], { color: PAL.hero, alpha: 0.85, glow: 24 });
  const capes = [[-53.9, -71.3], [-34.8, 20.0], [8.1, 77.5]];
  push(gscene({
    t0: cDrip, t1: cTet + 0.75, ovKey: 'ch2:drip', install: (gl) => gl.setOverlay(ovDrip),
    cam: (lt) => Object.assign(camAt([{ t: 0, lat: -26, lon: 14, alt: 3.15 }, { t: 6, lat: -30, lon: 22, alt: 2.95 }], lt, 2.0), { lookOffset: [0, -0.05] }),
    look: () => ({ ovAlpha: 1, dim: 0.35, desat: 0.3 }),
    draw2d: (ctx, lt, t, pj) => {
      const sp = pj.ll(-90, 0);
      if (sp[2]) { const ph = ((t - cDrip) / 1.2) % 1; L.ring(ctx, sp[0], sp[1], 26 + 8 * Math.sin(ph * Math.PI * 2), PAL.yellow, 5); F.text(ctx, '?', sp[0], sp[1] + 13, { size: 40, fam: F.FAM.head, align: 'center', color: '#ffffff' }); }
      capes.forEach((c, i) => {
        const t0 = tm.see - pre + i * 0.15; if (t < t0) return;
        const pts = projectPath(g, gcLine(c, [-78, 20], 80, 0.08));
        const head = F.glowPath(ctx, pts, { p: prog(t, t0, t0 + 1.0, E.inOut), color: '#ffffff', width: 3.5 });
        if (head) F.dot(ctx, head[0], head[1], { r: 6, color: '#ffffff' });
      });
      F.headline(ctx, ['WHY', 'DO', 'THE', 'CONTINENTS', 'POINT', { w: 'SOUTH?', c: PAL.hero }], W / 2, 175, t - (tm.lop - 0.35), { size: 112, per: 0.07, tOut: cTet - tm.lop + 0.15 });
    },
  }));
  sfx(cDrip, 'whoosh_soft', -14);
  sfx(tm.see - 0.05, 'shimmer', -16);

  // ======================= s043/s044 X: 1875 — tetra hidden in the globe; JUICE CHECK ?; subscribe =======================
  const engr = im('green_globes.jpg');
  const sepiaBg = (ctx, t) => {
    const gr = ctx.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, H * 0.95); gr.addColorStop(0, '#7a6244'); gr.addColorStop(0.6, '#3e2f1f'); gr.addColorStop(1, '#140e08'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.55;
    const s = 1.0 + 0.04 * Math.sin(t * 0.1); const iw = 760 * s, ih = iw * engr.height / engr.width;
    ctx.drawImage(engr, 70 - (t - cTet) * 2, (H - ih) / 2, iw, ih); ctx.drawImage(engr, W - 70 - iw + (t - cTet) * 2, (H - ih) / 2, iw, ih);
    ctx.restore();
    ctx.fillStyle = 'rgba(20,12,6,0.25)'; ctx.fillRect(0, 0, W, H);
  };
  const edgesIdx = [[0, 1], [0, 2], [0, 3], [1, 2], [2, 3], [3, 1]];
  push({
    t0: cTet, t1: T1, async draw(ctx, lt, t) {
      const wp = prog(t, cTet, cTet + 0.7, E.inOut);
      if (wp < 1) { ctx.save(); ctx.beginPath(); const xw = lerp(-300, W + 300, wp); ctx.moveTo(-10, 0); ctx.lineTo(xw + 200, 0); ctx.lineTo(xw - 200, H); ctx.lineTo(-10, H); ctx.closePath(); ctx.clip(); }
      sepiaBg(ctx, t);
      // camera: slow push, then (s044) a lower orbit with the globe offset right
      const k1 = prog(t, cTet, tm.before, E.inOutSine), k2 = prog(t, tm.before - 0.3, tm.before + 0.6, E.inOut);
      const ang = -0.35 + 0.25 * k1 + (t > tm.before ? (t - tm.before) * 0.06 : 0);
      const dist = lerp(lerp(13.2, 11.4, k1), 7.9, k2), camY = lerp(lerp(1.2, 0.6, k1), -0.2, k2);
      const tgt = [lerp(0, -1.5, k2) * Math.cos(ang), 0, lerp(0, -1.5, k2) * -Math.sin(ang)];
      const xr = prog(t, tm.shape - pre, tm.shape + 0.9, E.inOut);
      const r = S.tetra(ctx, t, { ry: (t - cTet) * 0.14 + 0.6, rx: 0.2, cam: [Math.sin(ang) * dist + tgt[0], camY, Math.cos(ang) * dist + tgt[2]], target: tgt, xray: xr * 0.85, edge: 0 });
      // 2D tetra edges: parts outside the sphere glow; hidden parts appear with the x-ray
      const cam = r.cam, R = r.R;
      const glowA = 0.9, flare = env(t, tm.ball - pre, tm.ball + 1.4, 0.08, 0.9);
      ctx.save(); ctx.lineCap = 'round'; ctx.globalCompositeOperation = 'lighter';
      for (const [a, b] of edgesIdx) {
        const A = r.V[a], B = r.V[b]; let run = [], runVis = null; const segs = [];
        for (let i = 0; i <= 48; i++) {
          const P = A.clone().lerp(B, i / 48); const out = P.length() > R * 1.003;
          const D = P.clone().sub(cam); const Ld = D.length(); D.divideScalar(Ld);
          const bq = cam.dot(D), cq = cam.lengthSq() - R * R, disc = bq * bq - cq; let occl = false;
          if (disc > 0) { const th = -bq - Math.sqrt(disc); if (th > 0 && th < Ld - 1e-3) occl = true; }
          const vis = out && !occl; const q = S.project(P);
          if (runVis === null || vis === runVis) run.push([q.x, q.y]); else { segs.push([runVis, run]); run = [run[run.length - 1], [q.x, q.y]]; }
          runVis = vis;
        }
        segs.push([runVis, run]);
        for (const [vis, pts] of segs) {
          const al = vis ? glowA * prog(t, tm.g1875 - pre, tm.g1875 + 0.6) : 0.85 * xr;
          if (al <= 0.01 || pts.length < 2) continue;
          F.glowPath(ctx, pts, { color: PAL.yellow, width: vis ? 4.5 : 3.2, alpha: al * (1 + 0.6 * flare) });
        }
      }
      ctx.restore();
      // corners
      r.V.forEach(V => {
        const q = S.project(V); const D = V.clone().sub(cam); const Ld = D.length(); D.divideScalar(Ld); const bq = cam.dot(D), cq = cam.lengthSq() - R * R, disc = bq * bq - cq;
        const occl = disc > 0 && (-bq - Math.sqrt(disc)) < Ld - 1e-3 && (-bq - Math.sqrt(disc)) > 0;
        const a = (occl ? 0.35 * xr : 1) * prog(t, tm.g1875 - pre, tm.g1875 + 0.6);
        if (a <= 0) return;
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        L.glowDot(ctx, q.x, q.y, 40 + 150 * flare, PAL.yellow, a * (0.55 + 0.45 * flare));
        if (flare > 0) { ctx.globalAlpha = a * flare; ctx.strokeStyle = '#FFF4C8'; ctx.lineWidth = 3; const s = 70 + 120 * flare; ctx.beginPath(); ctx.moveTo(q.x - s, q.y); ctx.lineTo(q.x + s, q.y); ctx.moveTo(q.x, q.y - s); ctx.lineTo(q.x, q.y + s); ctx.stroke(); }
        ctx.restore();
      });
      // "1875"
      const ya = prog(t, tm.g1875 - pre, tm.g1875 + 0.4) * (1 - prog(t, tm.before - 0.2, tm.before + 0.2)) * (1 - prog(t, tm.ball - 0.6, tm.ball - 0.25)) * (t > tm.ball + 1.2 ? 0 : 1);
      if (ya > 0) { F.text(ctx, '1875', 150, 250, { size: 190, fam: F.FAM.head, color: '#F3E3B5', alpha: ya, tracking: 0.04 }); }
      // JUICE CHECK: ? stamp spins in (upper left) then lands on the hidden pyramid
      if (t > tm.taught - pre) {
        const lk = prog(t, tm.checks - 0.35, tm.checks - pre, E.in);
        const gc = S.project(new S.THREE.Vector3(0, 0, 0));
        const sx = lerp(360, gc.x, lk), sy = lerp(230, gc.y, lk);
        const landed = t > tm.checks - pre;
        L.juiceStamp(ctx, sx, sy, landed ? t - (tm.checks - pre) : t - (tm.taught - pre), '?', { size: landed ? 92 : 70, spin: landed ? 0 : 12, dur: landed ? 0.2 : 0.45, from: landed ? 1.5 : 0.2, color: PAL.yellow });
      }
      // subscribe button
      if (t > tm.sub - pre - 0.15) {
        const sk = E.outBack(prog(t, tm.sub - pre - 0.15, tm.sub + 0.15, E.lin)); const glow = 0.5 + 0.5 * Math.sin((t - tm.sub) * 6);
        const bw = 420, bh = 96, bx = W / 2 - bw / 2 + 0, by = 790;
        ctx.save(); ctx.translate(W / 2, by + bh / 2); ctx.scale(sk, sk); ctx.translate(-W / 2, -(by + bh / 2));
        L.glowDot(ctx, W / 2, by + bh / 2, 330, '#FF3B3B', 0.35 + 0.25 * glow);
        ctx.fillStyle = '#E8262B'; F.round(ctx, bx, by, bw, bh, 18); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 3; ctx.stroke();
        F.text(ctx, 'SUBSCRIBE', W / 2, by + bh / 2 + 22, { size: 62, fam: F.FAM.label, weight: 700, tracking: 0.14, align: 'center', color: '#ffffff', shadow: false });
        ctx.restore();
      }
      if (wp < 1) { ctx.restore(); const xw = lerp(-300, W + 300, wp); ctx.save(); ctx.strokeStyle = 'rgba(255,230,180,0.85)'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(xw + 200, 0); ctx.lineTo(xw - 200, H); ctx.stroke(); ctx.restore(); }
    },
  });
  sfx(cTet, 'paper_rustle', -16);
  sfx(tm.ball - 4.0, 'riser_tension', -14);
  sfx(tm.ball - 0.05, 'impact_short', -12);
  sfx(tm.taught - 0.1, 'whoosh_soft', -16);
  sfx(tm.checks - 0.05, 'stamp', -14);
  sfx(tm.sub - 0.08, 'pop_ui', -14);

  // safety: verify base coverage of [T0, T1) with layer 0 scenes (log gaps)
  const base = scenes.filter(s => !s.layer).sort((a, b) => a.t0 - b.t0); let cur = T0;
  for (const s of base) { if (s.t0 > cur + 1e-6) api.log(`ch2 GAP ${cur.toFixed(2)}..${s.t0.toFixed(2)}`); cur = Math.max(cur, s.t1); }
  if (cur < T1 - 1e-6) api.log(`ch2 GAP tail ${cur.toFixed(2)}..${T1.toFixed(2)}`);
  return scenes;
}
