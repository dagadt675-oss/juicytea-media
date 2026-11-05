// Chapter 4 (s057-s071): "Why did geologists laugh at Wegener?"
// Portrait -> continents fit -> letter -> 1912 lecture -> paleo scrub -> war smoke -> Explorer gag (insult) ->
// slamming university doors -> Graz -> "what pushes a continent?" (spin/tides/gauge) -> Newton quote ->
// Greenland -> last photos -> white -> ice -> ridge -> magnetic zebra stripes -> 33 years -> plate speed vs nails ->
// JUICE CHECK: TRUE -> drip globe -> rewind scrub card.
import * as F from '../../lib/fx.js';
import { camAt } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, fillEquirect, makeCanvas, strokeProjected, fillProjected, gcLine, projectPath } from '../../lib/geo.js';
import { dripArrow } from '../../lib/beats.js';
import { ee, eeScale, eePath, EE_W, EE_H } from './ch4_ee.js';
import * as A from './ch4_art.js';
import { corridor, seafloor } from './ch4_sets.js';
const { PAL, prog, env, E, clamp, lerp } = F;
const IMG = 'ep/ep01/img/';
const D2R = Math.PI / 180;

// ---------------- sphere helpers (same convention as globe.js) ----------------
const v3 = (lat, lon) => [Math.cos(lat * D2R) * Math.cos(lon * D2R), Math.sin(lat * D2R), -Math.cos(lat * D2R) * Math.sin(lon * D2R)];
const ll3 = (p) => { const L = Math.hypot(p[0], p[1], p[2]); return [Math.asin(p[1] / L) / D2R, Math.atan2(-p[2], p[0]) / D2R]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
function rotP(p, k, th) { const c = Math.cos(th), s = Math.sin(th), kx = cross(k, p), kd = dot(k, p); return [p[0] * c + kx[0] * s + k[0] * kd * (1 - c), p[1] * c + kx[1] * s + k[1] * kd * (1 - c), p[2] * c + kx[2] * s + k[2] * kd * (1 - c)]; }
// rotate [lon,lat] rings about an Euler pole [lat,lon] by deg
function euler(ringsArr, pole, deg) { const k = v3(pole[0], pole[1]), th = deg * D2R; return ringsArr.map(r => r.map(([lon, lat]) => { const q = ll3(rotP(v3(lat, lon), k, th)); return [q[1], q[0]]; })); }
// destination point from [lat,lon] along azimuth (deg from north) by dist (deg)
function dest(lat, lon, az, d) {
  const p = lat * D2R, l = lon * D2R, a = az * D2R, dd = d * D2R;
  const p2 = Math.asin(Math.sin(p) * Math.cos(dd) + Math.cos(p) * Math.sin(dd) * Math.cos(a));
  const l2 = l + Math.atan2(Math.sin(a) * Math.sin(dd) * Math.cos(p), Math.cos(dd) - Math.sin(p) * Math.sin(p2));
  return [p2 / D2R, l2 / D2R];
}
// ---------------- coastline extraction from Natural Earth land rings ----------------
function nearestIdx(ring, lat, lon) { let bi = 0, bd = 1e18; const c = Math.cos(lat * D2R); for (let i = 0; i < ring.length; i++) { const dx = (ring[i][0] - lon) * c, dy = ring[i][1] - lat, d = dx * dx + dy * dy; if (d < bd) { bd = d; bi = i; } } return [bi, bd]; }
function ringNear(rs, lat, lon) { let best = null, bd = 1e18; for (const r of rs) { const [, d] = nearestIdx(r, lat, lon); if (d < bd) { bd = d; best = r; } } return best; }
function arcBetween(ring, Ap, Bp, Mp) {
  const n = ring.length - 1; const [ia] = nearestIdx(ring, ...Ap), [ib] = nearestIdx(ring, ...Bp), [im] = nearestIdx(ring, ...Mp);
  const walk = (dir) => { const out = []; let hasM = false; for (let i = ia, k = 0; k <= n; i = (i + dir + n) % n, k++) { out.push(ring[i]); if (i === im) hasM = true; if (i === ib) break; } return { out, hasM }; };
  const f = walk(1); if (f.hasM) return f.out; return walk(-1).out;
}
const poly = (ring) => ({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [ring] } });

// ---------------- globe plumbing (overlay/patch installation robust to frame order) ----------------
function useOverlay(api, spec) {
  const g = api.g;
  if (!spec) { if (g.u.ovOn.value) { g.u.ovOn.value = 0; api._ovOwner = null; } return; }
  if (g.u.ovOn.value !== 1 || g.u.ovTex.value.image !== spec.cv) { g.setOverlay(spec.cv, spec.b); api._ovOwner = null; spec._ver = spec.ver; }
  else if (spec._ver !== spec.ver) { g.refreshOverlay(); spec._ver = spec.ver; }
}
async function usePatch(api, spec) {
  const g = api.g;
  if (!spec) { if (g.u.patchOn.value) { g.u.patchOn.value = 0; api._patchOwner = null; } return; }
  if (!(g.u.patchOn.value === 1 && g.u.patchTex.value.__ch4 === spec.url)) { await g.setPatch(spec.url, spec.b); g.u.patchTex.value.__ch4 = spec.url; api._patchOwner = null; }
}
const LOOK0 = { dim: 0, desat: 0.12, ovAlpha: 0, relief: 0.8, nightAmt: 1, exposure: 1.25, flatBase: 0, ovMul: 0, ambient: 0.10, specAmt: 0.5, rimAmt: 0.35 };
function gscene(o) {
  return {
    t0: o.t0, t1: o.t1, layer: o.layer || 0, fadeIn: o.fadeIn || 0, fadeOut: o.fadeOut || 0, id: 'ch4',
    async draw(ctx, lt, t, api) {
      const g = api.g;
      if (o.pre) await o.pre(lt, t, api);
      useOverlay(api, typeof o.overlay === 'function' ? o.overlay(lt, t) : (o.overlay || null));
      await usePatch(api, typeof o.patch === 'function' ? o.patch(lt, t) : (o.patch || null));
      const cam = o.cam(lt, t);
      const look = Object.assign({}, LOOK0, o.look ? o.look(lt, t) : {});
      const tint = look.tint || [1, 1, 1]; delete look.tint;
      g.u.tint.value.set(tint[0], tint[1], tint[2]);
      api.drawGlobe(ctx, Object.assign({ sun: 'camera', starAlpha: 1, lookOffset: null }, cam), look);
      g.u.tint.value.set(1, 1, 1);
      if (o.extra) await o.extra(ctx, lt, t, api, cam);
    },
  };
}
const kcam = (keys, drift = 0.25, extra) => (lt, t) => { const c = camAt(keys, lt, drift); return extra ? Object.assign(c, extra(lt, t)) : c; };
// overlay canvas spec
function ovSpec(features, o = {}) {
  const b = o.b || [-180, -90, 180, 90]; const cv = makeCanvas(o.w || 2048, o.h || 1024);
  fillEquirect(cv, b, features, { color: o.color || PAL.hero, alpha: o.alpha ?? 0.88, glow: o.glow ?? 22 });
  return { cv, b, ver: 0 };
}

// ---------------- photo helpers ----------------
function kbAt(keys, t) {
  if (t <= keys[0].t) return keys[0];
  for (let i = 0; i < keys.length - 1; i++) { const a = keys[i], b = keys[i + 1]; if (t <= b.t) { const k = (b.ease || E.inOutSine)(clamp((t - a.t) / Math.max(1e-6, b.t - a.t))); return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), z: lerp(a.z, b.z, k) }; } }
  return keys[keys.length - 1];
}
function photo(ctx, img, keys, t, x, y, w, h, o = {}) {
  const c = kbAt(keys, t); const z = c.z * (1 + 0.006 * (t - keys[0].t)); // never fully static
  F.kenburns(ctx, img, 0, x, y, w, h, { from: [c.x, c.y, z], to: [c.x, c.y, z], frame: o.frame, grade: o.grade, radius: o.radius });
}
function darkBg(ctx, W, H, c0 = '#141A26', c1 = '#05070D', cx = 0.5, cy = 0.45) {
  const g = ctx.createRadialGradient(W * cx, H * cy, 40, W * cx, H * cy, H * 1.05); g.addColorStop(0, c0); g.addColorStop(1, c1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
const pillTop = (ctx, W, s, a, o = {}) => F.pill(ctx, s, W / 2, o.y || 112, Object.assign({ anchor: 'center', size: o.size || 40, alpha: a }, o));

// ======================================================================================================
export async function build(api, C) {
  const W = api.W, H = api.H;
  await api.globe();
  const T = (m, w) => C.T(m, w);
  const seg = (id) => C.seg(id);
  const word = (id, pre) => { const w = C.words(id).find(x => x.w.toLowerCase().replace(/[^a-z\-]/g, '').startsWith(pre)); if (!w) throw new Error('ch4: no word ' + pre + ' in ' + id); return w.start; };
  const cue = (t, n, db) => api.cue(t, n, db);
  const S = [];

  // ---------- assets ----------
  const P_PORT = IMG + 'wegener_portrait.jpg', P_LAST = IMG + 'wegener_last_026.jpg', P_VILL = IMG + 'wegener_villumsen_1930.jpg', P_EE = 'tex/equal_earth.jpg';
  await api.loadImages([P_PORT, P_LAST, P_VILL, P_EE]);
  try { await document.fonts.load('italic 700 72px "Playfair Display"'); await document.fonts.load('800 40px "Barlow Condensed"'); } catch (e) { /* fonts optional */ }
  const land = await loadGeo('ne_50m_land');
  const LR = land.features.flatMap(f => rings(f));
  const CN = await loadGeo('ne_50m_admin_0_countries');
  const ringAm = ringNear(LR, 8.0, -77.6), ringAf = ringNear(LR, 31.2, 32.3);
  const SA = [[...arcBetween(ringAm, [8.68, -77.36], [7.22, -77.89], [-8.05, -34.9])]]; SA[0].push(SA[0][0]);
  const AFR = [[...arcBetween(ringAf, [31.25, 32.3], [29.95, 32.55], [-34.8, 20.0])]]; AFR[0].push(AFR[0][0]);
  const MDG = [ringNear(LR, -19.0, 46.8)];
  const IND = rings(findFeature(CN, 'India')), GRL = rings(findFeature(CN, 'Greenland')), AUT = rings(findFeature(CN, 'Austria'));
  const SA_COAST = [arcBetween(ringAm, [8.6, -60.6], [-52.4, -68.4], [-8.05, -34.9])];
  const AF_COAST = [arcBetween(ringAf, [14.7, -17.45], [-34.4, 18.5], [0.0, 9.3])];
  const POLE = [44.0, -30.6], FIT = 57.0; // Bullard-style fit of South America onto Africa
  const SA_FIT = euler(SA, POLE, FIT), SAC_FIT = euler(SA_COAST, POLE, FIT);

  // overlays (one active at a time)
  const OV_AF = ovSpec([poly(AFR[0]), poly(MDG[0])]);
  const OV_AUT = ovSpec([findFeature(CN, 'Austria')], { b: [5, 42, 25, 52], w: 1024, h: 512, glow: 14 });
  const OV_SAAF = ovSpec([poly(SA[0]), poly(AFR[0]), poly(MDG[0])]);
  const OV_DRIP = ovSpec([poly(SA[0]), poly(AFR[0]), poly(MDG[0]), findFeature(CN, 'India')], { glow: 26 });
  const OV_GRL = ovSpec([findFeature(CN, 'Greenland')], { b: [-75, 58, -10, 84], w: 2048, h: 1024, glow: 18 });
  const PATCH_GRL = { url: 'tex/patch/greenland.jpg', b: [-75, 58, -10, 84] };

  // ---------- key times (all from the voice) ----------
  const t0 = C.t0, t1 = C.t1;
  const tFit = T('fit') - 0.18;
  const tS058 = seg('s058').start - 0.12;
  const tS059 = seg('s059').start - 0.1;
  const tMove = T('move') - 0.15;
  const tWar = T('war') - 0.12, tBook = T('book');
  const tGag = seg('s060').start + 0.62;
  const tRot = T('rot') - 0.25;
  const tDoors = word('s060', 'in') - 0.1; // "In Germany"
  const slams = [T('prof') - 0.06, T('prof') + 0.4, T('prof') + 0.86];
  const tOpen = T('austria') - 0.1, tPush = T('austria') + 0.22, tPushEnd = T('austria') + 0.72;
  const tGraz = tPushEnd - 0.32;
  const tSpin = T('spin') - 0.2, tTides = word('s061', 'tides') - 0.1;
  const tQuote = word('s062', 'himself') - 0.08;
  const tGrl = seg('s063').start - 0.28;
  const tPhoto1 = seg('s064').start - 0.06, tPhoto2 = word('s064', 'with') - 0.1;
  const tWhite = T('back'), tIce = seg('s066').start + 0.3;
  const tRidge = seg('s067').start - 0.1, tFloor = T('floor') - 0.2;
  const tCount = seg('s068').start - 0.05, tGPS = seg('s069').start - 0.15;
  const tFight = T('toe') - 0.1, tAgency = word('s069', 'agency');
  const tStamp = seg('s070').start - 0.1, tDrip = T('drip') - 0.12, tWhy = word('s070', 'why') - 0.1, tPoint = word('s070', 'pointing') - 0.1;
  const tScrub = seg('s071').start - 0.1;

  // =========================== s057: portrait + chapter card ===========================
  const imgPort = api.img(P_PORT);
  S.push({ t0, t1: tFit + 0.3, id: 'ch4', draw(ctx, lt, t) {
    photo(ctx, imgPort, [{ t: t0, x: 0.5, y: 0.42, z: 1.0 }, { t: T('wrote') - 0.12, x: 0.468, y: 0.318, z: 2.15, ease: E.inOut }, { t: tFit + 0.4, x: 0.46, y: 0.31, z: 2.3 }], t, 0, 0, W, H, { grade: 'sepia' });
    // warm light leak
    const lg = ctx.createRadialGradient(W * 0.1, H * 0.2, 0, W * 0.1, H * 0.2, W * 0.7); lg.addColorStop(0, 'rgba(255,170,90,0.20)'); lg.addColorStop(1, 'rgba(255,170,90,0)'); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    chapterCard(ctx, W, H, t - t0, 2.75);
    if (t > word('s057', 'alfred') - 0.25) F.pill(ctx, 'ALFRED WEGENER', 130, 852, { anchor: 'left', size: 42, alpha: env(t, word('s057', 'alfred') - 0.25, tFit + 0.2, 0.3, 0.25) });
    // envelope slides in on "wrote"
    const ew = T('wrote') - 0.2; if (t > ew) { const p = prog(t, ew, ew + 0.6, E.outBack); A.envelope(ctx, lerp(2250, 1470, p), 620 + Math.sin((t - ew) * 2) * 8, 340, -0.12 + Math.sin((t - ew) * 1.3) * 0.03, 1); }
  } });
  cue(t0 + 0.02, 'whoosh_soft', -12);
  cue(T('wrote') - 0.2, 'paper_rustle', -18);

  // =========================== s057/s058: the fit + the letter ===========================
  const letter = makeLetter(SA_FIT, AFR, MDG);
  const tSlide0 = T('joined') - 1.15, tSlide1 = T('joined') + 0.42;
  S.push(gscene({ t0: tFit, t1: tS059 + 0.3, fadeIn: 0.25,
    overlay: OV_AF,
    cam: kcam([{ t: 0, lat: -14, lon: -26, alt: 1.85 }, { t: tSlide0 - tFit, lat: -12, lon: -20, alt: 1.8 }, { t: tSlide1 - tFit + 0.3, lat: -9, lon: -6, alt: 1.6 }, { t: 9, lat: -8, lon: -2, alt: 1.5 }], 0.3),
    look: (lt, t) => ({ ovAlpha: 0.95 * prog(t, word('s057', 'africa') - 0.1, word('s057', 'africa') + 0.4), dim: lerp(0.15, 0.42, prog(t, T('fit'), T('fit') + 0.8)) + 0.25 * prog(t, tS058, tS058 + 0.6), desat: 0.25 }),
    extra(ctx, lt, t, api) {
      const g = api.g;
      const ang = FIT * prog(t, tSlide0, tSlide1, E.inOut);
      const R = euler(SA, POLE, ang), RC = euler(SA_COAST, POLE, ang);
      const fa = prog(t, T('fit') + 0.4, T('fit') + 1.0);
      fillProjected(ctx, g, R, { color: '#FF6A40', alpha: 0.82 * fa });
      strokeProjected(ctx, g, R, { color: '#ffffff', width: 1.6, alpha: 0.5 * fa });
      const cp = prog(t, T('fit') - 0.12, T('fit') + 1.0, E.out);
      strokeProjected(ctx, g, RC, { p: cp, color: '#ffffff', width: 3.2, glow: true });
      strokeProjected(ctx, g, AF_COAST, { p: cp, color: '#ffffff', width: 3.2, glow: true });
      // contact flash
      if (t > tSlide1 - 0.05) { const q = g.project(-8, 10); const k = clamp((t - tSlide1 + 0.05) / 0.9); if (k < 1) { ctx.save(); ctx.strokeStyle = PAL.yellow; ctx.globalAlpha = 1 - k; ctx.lineWidth = 6 * (1 - k) + 1; ctx.beginPath(); ctx.arc(q.x, q.y, 30 + k * 260, 0, 6.283); ctx.stroke(); ctx.restore(); } }
      if (t > tS058) letter(ctx, W, H, t, tS058, T('pursue') + 0.3);
    },
  }));
  cue(tFit, 'whoosh_soft', -14);
  cue(tSlide1 - 0.05, 'pop_ui', -18);
  cue(tS058 + 0.05, 'paper_rustle', -18);

  // =========================== s059: 1912 lecture ===========================
  S.push({ t0: tS059, t1: tMove + 0.25, fadeIn: 0.3, id: 'ch4', draw(ctx, lt, t) { lecture(ctx, W, H, t, tS059, imgPort, T('move') - 0.6); } });
  S.push({ t0: T('meeting') - 0.12, t1: tWar + 0.45, layer: 6, id: 'ch4', draw(ctx, lt, t) { pillTop(ctx, W, '1912: THE CONTINENTS MOVE', env(t, T('meeting') - 0.12, tWar + 0.45, 0.25, 0.35), { size: 44, y: 104 }); } });
  cue(T('meeting') - 0.12, 'pop_ui', -14);

  // paleo scrub 200 Ma -> today on the globe
  const pal = paleo(api);
  const ma = (t) => 200 * (1 - prog(t, T('move') - 0.05, T('move') + 2.95, E.inOut));
  S.push(gscene({ t0: tMove, t1: tGag + 0.45,
    pre: async (lt, t) => { await pal.draw(ma(t)); },
    overlay: () => pal.spec,
    cam: kcam([{ t: 0, lat: 2, lon: -6, alt: 2.7 }, { t: tGag + 0.5 - tMove, lat: -2, lon: -22, alt: 2.55 }], 0.4),
    look: () => ({ flatBase: 1, ovAlpha: 1, ovMul: 1, nightAmt: 0, relief: 0, desat: 0 }),
    extra(ctx, lt, t) {
      const a = env(t, tMove + 0.1, tWar + 0.9, 0.3, 0.4);
      if (a > 0) {
        F.counter(ctx, ma(t), ma(t), 1, 120, 186, { size: 96, align: 'left', alpha: a, format: v => String(Math.round(v)) });
        F.text(ctx, 'MILLION YEARS AGO · SIMPLIFIED', 124, 236, { size: 28, fam: F.FAM.label, weight: 700, tracking: 0.16, color: PAL.sub, alpha: a });
      }
    },
  }));
  cue(tMove, 'whoosh_soft', -14);
  // war: smoke rolls in, a 1915 book sinks under it
  S.push({ t0: tWar - 0.1, t1: tGag + 0.6, layer: 5, id: 'ch4', draw(ctx, lt, t) { A.smoke(ctx, W, H, t, tWar - 0.1, env(t, tWar - 0.1, tGag + 0.6, 0.7, 0.55), { front: false }); flashes(ctx, W, H, t, tWar); } });
  S.push({ t0: tWar + 0.15, t1: tGag + 0.3, layer: 6, id: 'ch4', draw(ctx, lt, t) {
    const pin = prog(t, tWar + 0.15, tWar + 0.55, E.outBack), sink = prog(t, tBook - 0.1, tBook + 0.85, E.in);
    const y = 560 + sink * 520 + Math.sin(t * 1.7) * 6, a = (1 - sink * 0.6);
    ctx.save(); ctx.translate(W / 2, y); ctx.scale(pin, pin); ctx.rotate(-0.04 + sink * 0.25);
    A.book(ctx, 0, 0, 270, 0, '#3B2A20', a);
    // 1915 stamp
    ctx.globalAlpha *= a; ctx.rotate(-0.18); ctx.strokeStyle = '#D23A2A'; ctx.lineWidth = 6; F.round(ctx, -95, 20, 190, 82, 10); ctx.stroke();
    F.text(ctx, '1915', 0, 86, { size: 66, fam: F.FAM.head, color: '#E04634', align: 'center', shadow: false, tracking: 0.08 });
    ctx.restore();
  } });
  S.push({ t0: tBook - 0.25, t1: tGag + 0.6, layer: 7, id: 'ch4', draw(ctx, lt, t) { A.smoke(ctx, W, H, t, tWar - 0.4, env(t, tBook - 0.25, tGag + 0.6, 0.6, 0.55) * 0.95, { front: true }); } });
  cue(T('war') - 0.1, 'rumble_quake', -18);

  // =========================== s060: Explorer gag + slamming doors ===========================
  const gag = await explorerGag(api, { tWave: tGag + 0.4, tRot: T('rot'), tDamned: word('s060', 'damned'), tRotW: word('s060', 'rot') });
  S.push({ t0: tGag, t1: tDoors + 0.2, fadeIn: 0.35, id: 'ch4', async draw(ctx, lt, t) { gag.draw(ctx, t, t < tRot ? 'A' : 'B', T('brutal'), tRot); } });
  cue(T('brutal') - 0.1, 'whoosh_soft', -18);
  cue(T('rot') - 0.03, 'impact_short', -10);
  cue(word('s060', 'damned') - 0.03, 'impact_short', -14);
  cue(word('s060', 'rot') - 0.03, 'impact_short', -12);
  S.push({ t0: tDoors, t1: tPushEnd + 0.05, fadeIn: 0.2, id: 'ch4', draw(ctx, lt, t) { corridor(ctx, W, H, t, { t0: tDoors, slams, open: tOpen, pushAt: tPush, pushEnd: tPushEnd }); } });
  for (const s of slams) cue(s, 'thunk_heavy', -18);
  cue(tOpen, 'bell_small', -18);
  S.push({ t0: tOpen - 0.05, t1: tGraz + 2.1, layer: 6, id: 'ch4', draw(ctx, lt, t) { pillTop(ctx, W, 'FULL PROFESSOR AT LAST: AUSTRIA, 1924', env(t, tOpen - 0.05, tGraz + 2.1, 0.25, 0.35), { size: 42 }); } });

  // =========================== s061: Graz -> what pushes a continent? ===========================
  const tPull = tGraz + 1.3;
  S.push(gscene({ t0: tGraz, t1: tSpin + 0.25, fadeIn: 0.32,
    overlay: (lt, t) => t < T('push') - 1.0 ? OV_AUT : OV_SAAF,
    cam: kcam([{ t: 0, lat: 47.5, lon: 15.0, alt: 0.62, tilt: 22 }, { t: 1.3, lat: 47.3, lon: 15.2, alt: 0.55, tilt: 24 }, { t: 4.6, lat: 8, lon: -18, alt: 2.55, tilt: 0 }, { t: 9, lat: 4, lon: -24, alt: 2.45, tilt: 0 }], 0.3),
    look: (lt, t) => t < T('push') - 1.0 ? { ovAlpha: 0.9 * (1 - prog(t, tPull + 0.8, tPull + 2.0)), dim: 0.2 } : { ovAlpha: 0.9 * prog(t, T('push') - 0.25, T('push') + 0.25), dim: 0.2 + 0.2 * prog(t, T('push') - 0.25, T('push') + 0.25) },
    extra(ctx, lt, t, api) {
      const q = api.g.project(47.07, 15.44);
      if (q.visible && t < tPull + 2.0) F.dot(ctx, q.x, q.y, { r: 10 * prog(t, tGraz + 0.15, tGraz + 0.4, E.outBack), color: PAL.yellow, ring: ((t - tGraz) * 0.8) % 1 });
      if (t > T('push') - 0.1) { const m = api.g.project(-2, -16); A.bigQ(ctx, m.x, m.y - 40, t, T('push') - 0.12, 330); }
    },
  }));
  cue(tGraz + 0.15, 'pop_ui', -14);
  cue(tPull, 'whoosh_soft', -14);
  cue(T('push') - 0.12, 'pop_ui', -12);
  // spin + tides + gauge
  S.push(gscene({ t0: tSpin, t1: tQuote + 0.25, fadeIn: 0.2,
    overlay: OV_SAAF,
    cam: (lt) => Object.assign(camAt([{ t: 0, lat: 6, lon: -30, alt: 3.0 }, { t: 6, lat: 6, lon: -78, alt: 3.0, ease: E.inOutSine }], lt, 0.0), { lookOffset: [0.2, 0.0] }),
    look: () => ({ ovAlpha: 0.75, dim: 0.25, desat: 0.15 }),
    extra(ctx, lt, t, api) { spinTides(ctx, W, H, t, api, { tSpin, tTides, tWeak: T('weak') }); },
  }));
  cue(tSpin, 'whoosh_soft', -14);
  cue(T('weak') - 0.6, 'glitch_click', -16); cue(T('weak') - 0.05, 'glitch_click', -16);

  // =========================== s062: the Newton quote ===========================
  S.push({ t0: tQuote, t1: tGrl + 0.3, fadeIn: 0.25, id: 'ch4', draw(ctx, lt, t) {
    darkBg(ctx, W, H, '#16202E', '#04060B', 0.7, 0.5);
    photo(ctx, imgPort, [{ t: tQuote, x: 0.5, y: 0.36, z: 1.05 }, { t: tGrl + 0.3, x: 0.47, y: 0.31, z: 1.55 }], t, 1010, 120, 760, 820, { frame: true, grade: 'cold' });
    const q0 = word('s062', 'the') - 0.05, q1 = T('appeared') + 0.05;
    const lines = ['"THE NEWTON OF', 'DRIFT...', 'NOT YET APPEARED"'];
    const total = lines.join('').length; let n = Math.floor(total * clamp((t - q0) / (q1 - q0)));
    let y = 390;
    for (const L of lines) { const s = L.slice(0, Math.max(0, Math.min(L.length, n))); n -= L.length; if (s) F.text(ctx, s, 150, y, { size: 68, fam: F.FAM.mono, weight: 700, color: PAL.text }); if (n < 0 && s.length < L.length) { if ((t * 2.5) % 1 < 0.6) { const w = F.measure(ctx, s, { size: 68, fam: F.FAM.mono, weight: 700 }); ctx.fillStyle = PAL.hero; ctx.fillRect(152 + w, y - 56, 34, 62); } break; } y += 96; }
    if (t > q1) { const yb = 390 + 96 * 2; if (((t - q1) * 2.5) % 1 < 0.6) { const w = F.measure(ctx, lines[2], { size: 68, fam: F.FAM.mono, weight: 700 }); ctx.fillStyle = PAL.hero; ctx.fillRect(152 + w, yb - 56, 34, 62); } }
    ctx.fillStyle = PAL.hero; ctx.fillRect(150, 260, 120 * prog(t, tQuote, tQuote + 0.6, E.outExpo), 6);
  } });
  cue(word('s062', 'the') - 0.05, 'typewriter', -20);

  // =========================== s063: Greenland ===========================
  const tg = T('grl');
  S.push(gscene({ t0: tGrl, t1: tPhoto1 + 0.3,
    overlay: OV_GRL, patch: PATCH_GRL,
    cam: kcam([{ t: 0, lat: 50, lon: -30, alt: 2.6 }, { t: tg - 0.35 - tGrl, lat: 70, lon: -41, alt: 1.25, tilt: 6 }, { t: tg + 1.6 - tGrl, lat: 69, lon: -41.5, alt: 1.12, tilt: 10 }, { t: tPhoto1 + 0.3 - tGrl, lat: 66.8, lon: -43.5, alt: 0.2, tilt: 52, heading: 14, ease: E.inOut }], 0.3),
    look: (lt, t) => ({ ovAlpha: 0.95 * prog(t, tg - 0.12, tg + 0.05) * (1 - prog(t, tg + 2.0, tg + 2.9)), dim: 0.22 * (1 - prog(t, tg + 1.8, tg + 2.9)), relief: 1.0, desat: 0.15, nightAmt: 0.4 }),
    extra(ctx, lt, t, api) {
      const g = api.g;
      if (t > tg - 0.12 && t < tg + 2.6) strokeProjected(ctx, g, GRL, { p: prog(t, tg - 0.12, tg + 0.6, E.out), color: '#ffffff', width: 2.2, alpha: 1 - prog(t, tg + 2.0, tg + 2.6) });
      const tipT = word('s063', 'drips') - 0.12; const cf = g.project(59.9, -43.9);
      if (t > tipT && cf.visible) dripArrow(ctx, cf.x, cf.y + 8, prog(t, tipT, tipT + 0.55), { len: 120, color: PAL.yellow, alpha: 1 - prog(t, tg + 2.2, tg + 2.8) });
      const c = g.project(72, -40);
      if (t > tg - 0.12 && c.visible) F.pill(ctx, 'GREENLAND, 1930', c.x + 210, c.y - 150, { anchor: 'left', size: 40, leader: [c.x, c.y], alpha: env(t, tg - 0.12, tg + 2.4, 0.2, 0.35) });
      A.snow(ctx, W, H, t, 0.25 * prog(t, tg + 1.8, tg + 3.0), 0.05, 0.8);
    },
  }));
  cue(tGrl, 'whoosh_soft', -12);
  cue(tg - 0.12, 'pop_ui', -12);
  cue(tg + 1.6, 'ice_wind', -14);

  // =========================== s064-s065: the last photos, fade to white ===========================
  const imgLast = api.img(P_LAST), imgVill = api.img(P_VILL);
  S.push({ t0: tPhoto1, t1: tPhoto2 + 0.3, fadeIn: 0.3, id: 'ch4', draw(ctx, lt, t) {
    darkBg(ctx, W, H, '#202833', '#06080C');
    const ph = 840, pw = Math.round(ph * imgLast.width / imgLast.height);
    photo(ctx, imgLast, [{ t: tPhoto1, x: 0.5, y: 0.5, z: 1.0 }, { t: T('camp'), x: 0.47, y: 0.47, z: 1.06 }, { t: tPhoto2 + 0.3, x: 0.6, y: 0.45, z: 1.16 }], t, (W - pw) / 2 + 140, 100, pw, ph, { frame: true, grade: 'cold' });
    A.snow(ctx, W, H, t, 0.22, 0.05, 0.75);
    pillNov(ctx, t);
  } });
  S.push({ t0: tPhoto2, t1: tIce + 0.85, fadeIn: 0.3, id: 'ch4', draw(ctx, lt, t) {
    photo(ctx, imgVill, [{ t: tPhoto2, x: 0.42, y: 0.46, z: 1.06 }, { t: T('villumsen') + 0.2, x: 0.7, y: 0.4, z: 1.55, ease: E.inOut }, { t: tIce + 0.9, x: 0.71, y: 0.39, z: 1.72 }], t, 0, 0, W, H, { grade: 'cold' });
    A.snow(ctx, W, H, t, 0.2, 0.05, 0.6);
    pillNov(ctx, t);
    const wa = prog(t, tWhite, tWhite + 3.0, E.in); if (wa > 0) { ctx.fillStyle = `rgba(250,252,255,${wa})`; ctx.fillRect(0, 0, W, H); }
  } });
  function pillNov(ctx, t) { const a = env(t, word('s064', 'fiftieth') - 0.1, T('back') - 0.2, 0.3, 0.4); if (a > 0) F.pill(ctx, 'NOVEMBER 1930', 130, 150, { anchor: 'left', size: 42, alpha: a }); }
  cue(tPhoto1 + 0.2, 'ice_wind', -14);
  cue(tWhite - 0.4, 'ice_wind', -14);

  // =========================== s066: empty ice ===========================
  S.push(gscene({ t0: tIce, t1: tRidge + 0.1, fadeIn: 0.6, patch: PATCH_GRL, overlay: null,
    cam: kcam([{ t: 0, lat: 68.6, lon: -45.0, alt: 0.14, tilt: 60, heading: 22 }, { t: tRidge - tIce + 0.2, lat: 70.3, lon: -41.6, alt: 0.11, tilt: 63, heading: 30, ease: E.inOutSine }], 0.0),
    look: () => ({ relief: 1.0, desat: 0.4, exposure: 1.18, nightAmt: 0, tint: [0.94, 0.98, 1.06], specAmt: 0.2 }),
    extra(ctx, lt, t) {
      const ff = T('found');
      A.snow(ctx, W, H, t, lerp(0.35, 1.0, prog(t, ff - 0.3, ff + 0.9)), 0.08, 0.9);
      if (t > ff - 0.3) { ctx.fillStyle = `rgba(225,235,245,${0.28 * prog(t, ff - 0.3, ff + 1.2)})`; ctx.fillRect(0, 0, W, H); }
      const wa = 1 - prog(t, tIce, tIce + 1.1, E.out); if (wa > 0) { ctx.fillStyle = `rgba(250,252,255,${wa})`; ctx.fillRect(0, 0, W, H); }
      const a = env(t, T('may') - 0.12, ff + 0.4, 0.3, 0.5); if (a > 0) pillTop(ctx, W, 'FOUND: MAY 1931', a, { size: 44, y: 130 });
    },
  }));
  cue(T('may') - 0.3, 'ice_wind', -16);

  // =========================== s067: ridge -> zebra stripes ===========================
  const MAR = ridgeLine();
  S.push(gscene({ t0: tRidge, t1: tFloor + 0.2, overlay: null, patch: null,
    cam: kcam([{ t: 0, lat: 26, lon: -36, alt: 2.0, tilt: 10 }, { t: tFloor - tRidge + 0.2, lat: 14, lon: -36, alt: 0.95, tilt: 38, heading: -8 }], 0.2),
    look: () => ({ dim: 0.25, desat: 0.3, relief: 1.0, exposure: 1.0, nightAmt: 0.4 }),
    extra(ctx, lt, t, api) {
      const p = prog(t, word('s067', 'proof') - 0.2, word('s067', 'proof') + 1.4, E.inOut);
      if (p > 0) { const pts = projectPath(api.g, MAR); F.glowPath(ctx, pts, { p, color: '#FF8A3D', width: 4 }); }
    },
  }));
  cue(tRidge, 'whoosh_soft', -16);
  const tMir = T('mirror'), tTape = T('tape'), tLock = T('y33');
  S.push({ t0: tFloor, t1: tGPS + 0.2, id: 'ch4', draw(ctx, lt, t) {
    const lockP = prog(t, tCount, tCount + 1.4, E.inOut);
    const orb = Math.sin((t - tFloor) * 0.09) * 2.2;
    const pos = [lerp(orb, 0, lockP), lerp(3.0 - 0.03 * (t - tFloor), 8.6, lockP), lerp(6.4, 2.2, lockP)];
    const tgt = [0, lerp(-0.35, 0, lockP), lerp(-2.6, -3.4, lockP)];
    const shiftT = Math.min(t, tLock) - (tTape - 0.1);
    seafloor(ctx, W, H, t, {
      cam: { pos, target: tgt, fov: 40 },
      rightReveal: prog(t, T('floor') - 0.1, T('floor') + 1.4, E.out),
      flip: prog(t, tMir - 0.15, tMir + 0.85, E.inOut),
      shift: Math.max(0, shiftT) * 0.5,
      ridgeGlow: 0.4 + 0.6 * prog(t, tMir - 0.15, tMir + 0.4) * (1 - 0.5 * prog(t, tLock, tLock + 1)),
      arrows: prog(t, T('floor') + 1.2, T('floor') + 1.8) * (1 - prog(t, tTape - 0.5, tTape)),
      spreadArrows: prog(t, tTape - 0.1, tTape + 0.3) * (1 - prog(t, tLock - 0.2, tLock + 0.2)),
    });
    // lock flash
    if (t > tLock - 0.05 && t < tLock + 0.6) { ctx.fillStyle = `rgba(255,255,255,${0.35 * (1 - (t - tLock + 0.05) / 0.65)})`; ctx.fillRect(0, 0, W, H); }
    // texts
    const ta = env(t, word('s067', 'stripes') - 0.15, tCount - 0.2, 0.3, 0.35);
    if (ta > 0) pillTop(ctx, W, "THE SEAFLOOR'S ZEBRA STRIPES", ta, { size: 44 });
    if (t > tCount) {
      const ca = env(t, tCount + 0.3, tGPS + 0.2, 0.35, 0.25);
      ctx.save(); ctx.globalAlpha = ca; ctx.fillStyle = 'rgba(4,7,13,0.72)'; F.round(ctx, W / 2 - 330, 250, 660, 300, 28); ctx.fill(); ctx.restore();
      const p = prog(t, tLock - 0.95, tLock + 0.02, E.out);
      F.counter(ctx, 1930, 1963, p, W / 2, 470, { size: 190, alpha: ca, format: v => String(Math.round(v)), color: p >= 1 ? PAL.yellow : PAL.text });
      if (t > tLock + 0.35) F.headline(ctx, ['33', 'YEARS', 'TOO', { w: 'LATE', c: PAL.hero }], W / 2, 690, t - tLock - 0.35, { size: 120, per: 0.07, tOut: tGPS - tLock - 0.65 });
    }
  } });
  cue(T('floor') - 0.1, 'shimmer', -20);
  cue(tMir - 0.1, 'shimmer', -22);
  cue(tLock - 1.0, 'tick_counter', -16);
  cue(tLock, 'impact_deep', -10);

  // =========================== s069: plate speed vs fingernails ===========================
  const ARW = [
    [46, -100, 250, 7, 0.0], [34, -84, 255, 6, 0.15], [56, -78, 262, 6, 0.3],
    [-10, -55, 345, 5, 0.45], [-28, -62, 350, 5, 0.55],
    [8, 18, 40, 7, 0.7], [-18, 24, 36, 7, 0.82], [48, 12, 52, 7, 0.95], [44, 34, 58, 6, 1.05],
  ];
  const tArw = word('s069', 'satellites') - 0.1, tNail = T('nail') - 0.25;
  S.push(gscene({ t0: tGPS, t1: tFight + 0.4, overlay: null, patch: null,
    cam: (lt, t) => Object.assign(camAt([{ t: 0, lat: 24, lon: -34, alt: 2.55 }, { t: 9, lat: 20, lon: -26, alt: 2.4 }], lt, 0.25), { lookOffset: [0.24 * prog(t, tNail, tNail + 0.6, E.inOut), 0] }),
    look: (lt, t) => ({ dim: 0.18, desat: 0.2 }),
    extra(ctx, lt, t, api) {
      const g = api.g;
      ctx.save(); ctx.globalAlpha = 0.5; const pts = projectPath(g, MAR); F.glowPath(ctx, pts, { color: '#FF8A3D', width: 2.5 }); ctx.restore();
      for (const [la, lo, az, d, dt] of ARW) {
        const ta = tArw + dt * 1.3; if (t < ta) continue;
        const p = prog(t, ta, ta + 0.7, E.outBack);
        const e = dest(la, lo, az, d * Math.max(0.05, p));
        const a = g.project(la, lo), b = g.project(e[0], e[1]); if (!a.visible || !b.visible) continue;
        arrow2d(ctx, a.x, a.y, b.x, b.y, '#ffffff', 5);
      }
      // nail panel slides in from the right
      if (t > tNail) {
        const k = prog(t, tNail, tNail + 0.55, E.outExpo);
        const px = lerp(W + 20, W * 0.53, k);
        ctx.save(); ctx.fillStyle = 'rgba(10,13,22,0.94)'; F.round(ctx, px, 70, W - px + 40, H - 140, 30); ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 2; F.round(ctx, px, 70, W - px + 40, H - 140, 30); ctx.stroke(); ctx.restore();
        const ng = prog(t, T('nail'), T('nail') + 3.0, E.lin);
        const tip = A.finger(ctx, px + 420, 560, 1.0, ng, -0.04 + Math.sin(t * 1.3) * 0.01);
        // growth ruler under the nail
        const rx = px + 420 + 150, ry = 690; ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.lineWidth = 2;
        for (let i = 0; i <= 8; i++) { ctx.beginPath(); ctx.moveTo(rx + i * 14, ry); ctx.lineTo(rx + i * 14, ry + (i % 4 === 0 ? 22 : 12)); ctx.stroke(); }
        ctx.restore(); F.dot(ctx, px + 420 + tip, ry - 6, { r: 7, color: PAL.yellow });
        const ta = env(t, T('nail') - 0.1, tFight + 0.35, 0.25, 0.2); pillTop(ctx, W, 'PLATE SPEED = FINGERNAIL GROWTH', ta, { size: 42 });
      }
    },
  }));
  cue(tArw, 'whoosh_soft', -18);
  cue(tNail, 'whoosh_soft', -14);
  // fight card
  S.push({ t0: tFight, t1: tStamp + 0.25, fadeIn: 0.25, id: 'ch4', draw(ctx, lt, t) { fightCard(ctx, W, H, t, tFight, tAgency, T('nail')); } });
  cue(tFight, 'whoosh_soft', -12);
  cue(tAgency - 0.05, 'record_scratch', -14);

  // =========================== s070: JUICE CHECK + the drip globe ===========================
  S.push({ t0: tStamp, t1: tDrip + 0.2, fadeIn: 0.2, id: 'ch4', draw(ctx, lt, t) {
    darkBg(ctx, W, H, '#2A2118', '#07060A');
    ctx.save(); ctx.translate(W / 2, 520); ctx.rotate(0.025); ctx.translate(-W / 2, -520);
    photo(ctx, imgPort, [{ t: tStamp, x: 0.5, y: 0.36, z: 1.0 }, { t: tDrip + 0.2, x: 0.5, y: 0.34, z: 1.1 }], t, W / 2 - 330, 110, 660, 800, { frame: true, grade: 'sepia' });
    ctx.restore();
    const sh = t > T('right') - 0.1 ? Math.exp(-(t - T('right') + 0.1) * 12) * 10 : 0;
    A.rubberStamp(ctx, W / 2 + 40 + sh * Math.sin(t * 90), 640, ['JUICE CHECK', 'TRUE'], PAL.green, t, T('right') - 0.1, { rot: -0.14 });
  } });
  cue(T('right') - 0.1, 'stamp', -10);
  const TIPS = [[-55.98, -67.27], [-34.83, 20.0], [8.08, 77.55]];
  S.push(gscene({ t0: tDrip, t1: tScrub + 0.25, overlay: OV_DRIP, patch: null,
    cam: (lt) => Object.assign(camAt([{ t: 0, lat: -30, lon: 14, alt: 3.1, tilt: 0 }, { t: 5.2, lat: -40, lon: 22, alt: 2.75, tilt: 0 }], lt, 0.0), { lookOffset: [0, -0.06] }),
    look: (lt, t) => ({ ovAlpha: 0.95, dim: 0.35, desat: 0.3 }),
    extra(ctx, lt, t, api) {
      const g = api.g;
      TIPS.forEach(([la, lo], i) => { const q = g.project(la, lo); if (!q.visible) return; dripArrow(ctx, q.x, q.y + 6, prog(t, tDrip + 0.25 + i * 0.15, tDrip + 0.8 + i * 0.15), { len: 90, color: '#ffffff' }); });
      // Antarctica ring
      const ring = []; for (let lo = -180; lo <= 180; lo += 4) ring.push({ lat: -72, lon: lo });
      const rp = []; for (const p of ring) { const q = g.project(p.lat, p.lon); if (q.visible) rp.push([q.x, q.y]); }
      if (rp.length > 2) { ctx.save(); ctx.globalAlpha = prog(t, tDrip + 0.3, tDrip + 0.9); F.glowPath(ctx, rp, { color: PAL.yellow, width: 4, p: prog(t, tDrip + 0.3, tDrip + 1.4, E.out) }); ctx.restore(); }
      const sp = g.project(-90, 0); if (sp.visible || true) A.bigQ(ctx, sp.x, sp.y - 30, t, tPoint, 230);
      const a = env(t, tWhy, tScrub + 0.25, 0.3, 0.3); if (a > 0) pillTop(ctx, W, 'WHY DO THEY POINT SOUTH?', a, { size: 46 });
    },
  }));
  cue(tDrip, 'whoosh_soft', -12);
  cue(tPoint + 0.35 - 4.0, 'riser_tension', -12);

  // =========================== s071: rewind scrub card ===========================
  const eeImg = api.img(P_EE);
  const PATH_SA = eePath(SA), PATH_AF = eePath([...AFR, ...MDG]), PATH_IN = eePath(IND);
  S.push({ t0: tScrub, t1: t1, fadeIn: 0.25, id: 'ch4', draw(ctx, lt, t) { scrubCard(ctx, W, H, t, { t0: tScrub, rewind: T('rewind'), place: T('place'), t1, eeImg, paths: [PATH_SA, PATH_AF, PATH_IN], tips: TIPS }); } });
  cue(T('rewind') - 0.1, 'time_rewind', -12);

  return S;

  // ------------------------------------------------------------------------------------------------
  function chapterCard(ctx, W, H, lt, dur) {
    const a = env(lt, 0, dur, 0.3, 0.45); if (a <= 0) return;
    ctx.save(); ctx.fillStyle = `rgba(3,5,10,${0.62 * a})`; ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = a;
    const p = prog(lt, 0.05, 0.8, E.outExpo);
    ctx.fillStyle = PAL.hero; ctx.fillRect(W / 2 - 230 * p, 668, 460 * p, 5);
    F.text(ctx, 'CHAPTER 4', W / 2, 330, { size: 46, fam: F.FAM.label, weight: 700, tracking: 0.35, align: 'center', color: PAL.hero, alpha: p });
    F.headline(ctx, ['WHY', 'DID', 'GEOLOGISTS'], W / 2, 490, lt, { size: 140, per: 0.07, t0: 0.1, tOut: dur - 0.45 });
    F.headline(ctx, ['LAUGH', 'AT', { w: 'WEGENER?', c: PAL.hero }], W / 2, 625, lt, { size: 140, per: 0.07, t0: 0.3, tOut: dur - 0.45 });
    ctx.restore();
  }
}

// ======================================================================================================
// letter card with a handwritten line + a tiny ink sketch of the fitted continents
function makeLetter(SA_FIT, AFR, MDG) {
  const line = '“An idea I’ll have to pursue.”';
  const fnt = 'italic 700 74px "Playfair Display"';
  const m = document.createElement('canvas').getContext('2d'); m.font = fnt; const tw = Math.ceil(m.measureText(line).width);
  const sp = document.createElement('canvas'); sp.width = tw + 40; sp.height = 130; const g = sp.getContext('2d');
  g.font = fnt; g.fillStyle = '#1D2B4A'; g.textBaseline = 'alphabetic'; g.fillText(line, 20, 92);
  // sketch path in a local box (equirect around the fit)
  const sk = new Path2D(); const X = lo => (lo - 12) * 2.3, Y = la => -(la + 2) * 2.3;
  for (const r of [...SA_FIT, ...AFR, ...MDG]) { r.forEach(([lo, la], i) => i ? sk.lineTo(X(lo), Y(la)) : sk.moveTo(X(lo), Y(la))); sk.closePath(); }
  return (ctx, W, H, t, tin, tEnd) => {
    const p = prog(t, tin, tin + 0.5, E.outExpo); if (p <= 0) return;
    const cw = 1240, ch = 470, x = W / 2, y = lerp(H + 300, 520, p);
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.025 + (1 - p) * 0.08);
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, -cw / 2 + 14, -ch / 2 + 22, cw, ch, 10); ctx.fill();
    const pg = ctx.createLinearGradient(0, -ch / 2, 0, ch / 2); pg.addColorStop(0, '#F7F0E0'); pg.addColorStop(1, '#E9DDC3');
    ctx.fillStyle = pg; F.round(ctx, -cw / 2, -ch / 2, cw, ch, 10); ctx.fill();
    ctx.strokeStyle = 'rgba(70,110,170,0.18)'; ctx.lineWidth = 2;
    for (let ly = -ch / 2 + 90; ly < ch / 2 - 30; ly += 62) { ctx.beginPath(); ctx.moveTo(-cw / 2 + 50, ly); ctx.lineTo(cw / 2 - 50, ly); ctx.stroke(); }
    ctx.strokeStyle = 'rgba(200,80,80,0.3)'; ctx.beginPath(); ctx.moveTo(-cw / 2 + 110, -ch / 2 + 20); ctx.lineTo(-cw / 2 + 110, ch / 2 - 20); ctx.stroke();
    // write-on
    const wp = prog(t, tin + 0.35, tEnd, E.lin);
    const sx = -sp.width / 2 - 60, sy = -40 - 92;
    const rw = sp.width * wp;
    if (rw > 1) { ctx.drawImage(sp, 0, 0, rw, sp.height, sx, sy, rw, sp.height); }
    if (wp > 0 && wp < 1) { ctx.fillStyle = '#1D2B4A'; ctx.beginPath(); ctx.arc(sx + rw, sy + 70 + Math.sin(t * 40) * 6, 5, 0, 6.283); ctx.fill(); }
    // ink sketch (bottom-right corner)
    ctx.save(); ctx.translate(cw / 2 - 200, 95); ctx.scale(0.62, 0.62);
    ctx.strokeStyle = 'rgba(29,43,74,0.75)'; ctx.lineWidth = 3.2; ctx.lineJoin = 'round'; ctx.globalAlpha = prog(t, tin + 0.6, tin + 1.6); ctx.stroke(sk);
    ctx.restore();
    ctx.restore();
  };
}

// 1912 lecture: framed portrait on stage, audience silhouettes in front
const AUD = A.particles(5150, 26, (r, i) => ({ row: i < 8 ? 0 : i < 17 ? 1 : 2, x: r(), s: 0.85 + r() * 0.3, hat: r() < 0.45, ph: r() * 6.28, tilt: (r() - 0.5) }));
function lecture(ctx, W, H, t, t0, img, tMurmur) {
  const bg = ctx.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#20160E'); bg.addColorStop(1, '#070504'); ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // spotlight cone
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const sg = ctx.createRadialGradient(W / 2, 430, 40, W / 2, 430, 620); sg.addColorStop(0, 'rgba(255,200,130,0.28)'); sg.addColorStop(1, 'rgba(255,200,130,0)'); ctx.fillStyle = sg; ctx.fillRect(0, 0, W, H);
  ctx.restore();
  // lectern-like easel + framed portrait
  const lt = t - t0;
  photo(ctx, img, [{ t: t0, x: 0.5, y: 0.38, z: 1.0 }, { t: t0 + 5, x: 0.49, y: 0.34, z: 1.18 }], t, W / 2 - 230, 175, 460, 560, { frame: true, grade: 'sepia', radius: 6 });
  ctx.strokeStyle = '#8A6A3A'; ctx.lineWidth = 10; ctx.strokeRect(W / 2 - 236, 169, 472, 572);
  // audience (back rows first)
  for (const row of [2, 1, 0]) {
    const base = [1040, 980, 905][row], sc = [1.25, 1.0, 0.82][row], col = ['#030202', '#0C0907', '#17110C'][row];
    for (const a of AUD) {
      if (a.row !== row) continue;
      const x = (a.x * 1.1 - 0.05) * W + Math.sin(lt * 0.4 + a.ph) * 6 + row * 30;
      const s = 70 * sc * a.s, y = base + Math.sin(lt * 1.3 + a.ph) * 3;
      const murmur = prog(t, tMurmur + a.ph * 0.05, tMurmur + 0.5 + a.ph * 0.05) * a.tilt * 0.35;
      ctx.save(); ctx.translate(x, y); ctx.rotate(murmur); ctx.fillStyle = col;
      ctx.beginPath(); ctx.ellipse(0, s * 1.6, s * 1.55, s * 1.05, 0, Math.PI, 0); ctx.fill(); // shoulders
      ctx.beginPath(); ctx.ellipse(0, 0, s * 0.62, s * 0.74, 0, 0, 6.283); ctx.fill(); // head
      if (a.hat) { ctx.beginPath(); ctx.ellipse(0, -s * 0.42, s * 0.95, s * 0.16, 0, 0, 6.283); ctx.fill(); ctx.beginPath(); ctx.ellipse(0, -s * 0.5, s * 0.55, s * 0.5, 0, Math.PI, 0); ctx.fill(); }
      ctx.restore();
    }
  }
}

// distant artillery flashes on the horizon during the smoke
function flashes(ctx, W, H, t, tw) {
  for (const [dt, x] of [[0.15, 0.25], [0.65, 0.7], [1.2, 0.45]]) {
    const k = t - tw - dt; if (k < 0 || k > 0.5) continue;
    const a = Math.exp(-k * 7) * 0.5; const g = ctx.createRadialGradient(W * x, H * 0.75, 0, W * x, H * 0.75, 520);
    g.addColorStop(0, `rgba(255,150,70,${a})`); g.addColorStop(1, 'rgba(255,120,50,0)');
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
  }
}

// paleo overlay (simplified reconstructions; lazy-loaded every 2 Myr, memoised)
function paleo(api) {
  const cv = makeCanvas(2048, 1024), g = cv.getContext('2d');
  const cache = {}; const spec = { cv, b: [-180, -90, 180, 90], ver: 0 }; let cur = null;
  const load = (T) => cache[T] || (cache[T] = fetch(`paleo/coast_${String(T).padStart(3, '0')}.json`).then(r => r.json()).then(polys => polys.map(p => {
    const out = []; let lx = 1e9, ly = 1e9; for (const [lo, la] of p) { if (Math.abs(lo - lx) + Math.abs(la - ly) < 0.22) continue; out.push(lo, la); lx = lo; ly = la; } return new Float32Array(out);
  }).filter(a => a.length >= 6)));
  return {
    spec,
    async draw(Ma) {
      const T = Math.max(0, Math.min(200, Math.round(Ma / 2) * 2));
      if (T === cur) return; const polys = await load(T); cur = T;
      g.clearRect(0, 0, 2048, 1024);
      g.fillStyle = '#CDB98A'; g.beginPath();
      for (const a of polys) { for (let i = 0; i < a.length; i += 2) { const x = (a[i] + 180) / 360 * 2048, y = (90 - a[i + 1]) / 180 * 1024; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.closePath(); }
      g.fill('nonzero'); g.strokeStyle = 'rgba(255,255,255,0.45)'; g.lineWidth = 1.5; g.stroke();
      spec.ver++;
    },
  };
}

// small 2D arrow with outline
function arrow2d(ctx, x0, y0, x1, y1, col, w) {
  const ang = Math.atan2(y1 - y0, x1 - x0), hl = w * 3.4;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const [lw, c] of [[w + 5, 'rgba(0,0,0,0.55)'], [w, col]]) {
    ctx.strokeStyle = c; ctx.fillStyle = c; ctx.lineWidth = lw;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - Math.cos(ang) * hl * 0.6, y1 - Math.sin(ang) * hl * 0.6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - Math.cos(ang - 0.45) * hl, y1 - Math.sin(ang - 0.45) * hl); ctx.lineTo(x1 - Math.cos(ang + 0.45) * hl, y1 - Math.sin(ang + 0.45) * hl); ctx.closePath();
    if (c === col) ctx.fill(); else { ctx.lineWidth = 5; ctx.stroke(); }
  }
  ctx.restore();
}

// Mid-Atlantic Ridge (approximate crest), densified for projection
function ridgeLine() {
  const P = [[66, -18], [63.5, -22], [60, -29], [56.5, -33.5], [53, -35], [51, -30], [47, -28], [43, -29], [39.5, -29.8], [36.5, -33], [33, -38], [29, -43], [25, -45], [20, -46], [15, -45.5], [11, -43.5], [7.5, -37], [4.5, -32], [1, -27], [-0.5, -19], [-2, -14], [-6, -12], [-11, -13.5], [-16, -13.5], [-21, -12.2], [-26, -13.5], [-31, -14], [-36, -16.5], [-41, -17], [-46, -13.5], [-50, -7.5], [-54, -1]];
  const out = []; for (let i = 0; i < P.length - 1; i++) { const seg = gcLine(P[i], P[i + 1], 8, 0); out.push(...(i ? seg.slice(1) : seg)); } return out;
}

// spin arrows, tidal bulge, force gauge
function spinTides(ctx, W, H, t, api, o) {
  const g = api.g; const d = g.disc();
  // spin arrows: latitude circles slightly above the surface, front half only
  const sp = prog(t, o.tSpin + 0.05, o.tSpin + 0.7, E.out);
  if (sp > 0) {
    for (const lat of [-32, 0, 32]) {
      const pts = []; for (let lo = -180; lo <= 180; lo += 3) { const q = g.project(lat, lo, 0.07); if (q.facing > 0.05) pts.push([q.x, q.y, lo]); }
      if (pts.length < 6) continue;
      pts.sort((a, b) => a[0] - b[0]);
      const path = pts.map(p => [p[0], p[1]]);
      ctx.save(); ctx.globalAlpha = 0.9 * sp; const head = F.glowPath(ctx, path, { color: '#ffffff', width: 4, p: sp * 0.92 });
      if (head) { const n = path.length; const a0 = path[Math.max(0, Math.floor(n * sp * 0.92) - 3)]; arrow2d(ctx, a0[0], a0[1], head[0], head[1], '#ffffff', 4); }
      ctx.restore();
    }
  }
  // moon + tidal bulge toward it
  const mp = prog(t, o.tTides - 0.3, o.tTides + 0.3, E.out);
  if (mp > 0) {
    const mx = 230, my = 250, mr = 64 * mp;
    const mg = ctx.createRadialGradient(mx - 18, my - 18, 4, mx, my, mr); mg.addColorStop(0, '#F4F2EC'); mg.addColorStop(1, '#7D7B78');
    ctx.fillStyle = mg; ctx.beginPath(); ctx.arc(mx, my, mr, 0, 6.283); ctx.fill();
    const ang = Math.atan2(my - d.y, mx - d.x);
    const wob = 1 + 0.02 * Math.sin(t * 3);
    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(ang);
    ctx.globalAlpha = 0.85 * mp; ctx.fillStyle = 'rgba(61,227,255,0.16)'; ctx.strokeStyle = 'rgba(61,227,255,0.9)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(0, 0, d.r * 1.17 * wob, d.r * 1.02, 0, 0, 6.283); ctx.fill(); ctx.stroke();
    ctx.restore();
    // little push arrows on the bulge
    for (const k of [-0.35, 0, 0.35]) { const a = ang + k; const x0 = d.x + Math.cos(a) * d.r * 1.3, y0 = d.y + Math.sin(a) * d.r * 1.3; const x1 = d.x + Math.cos(a) * d.r * (1.12 + 0.03 * Math.sin(t * 6)), y1 = d.y + Math.sin(a) * d.r * (1.12 + 0.03 * Math.sin(t * 6)); ctx.save(); ctx.globalAlpha = mp; arrow2d(ctx, x0, y0, x1, y1, PAL.cyan, 4); ctx.restore(); }
  }
  // gauge
  const ga = prog(t, o.tTides + 0.5, o.tTides + 0.9, E.out);
  if (ga > 0) {
    let v = 0.3 * prog(t, o.tTides + 0.6, o.tTides + 1.3, E.out);
    if (t > o.tWeak - 1.0) v += 0.05 * Math.sin(t * 47) * (t < o.tWeak ? 1 : 0);
    v = lerp(v, 0.035 + 0.01 * Math.sin(t * 5), prog(t, o.tWeak - 0.05, o.tWeak + 0.5, E.outBack));
    A.gauge(ctx, 1470, 640, 210, v, ga);
  }
  const ta = prog(t, o.tWeak - 0.15, o.tWeak + 0.2); if (ta > 0) F.pill(ctx, 'SPIN AND TIDES: FAR TOO WEAK', W / 2, 112, { anchor: 'center', size: 44, alpha: ta });
}

// fingernails vs toenails fight card
function fightCard(ctx, W, H, t, t0, tFreeze, tNail) {
  const tt = Math.min(t, tFreeze);
  const bgL = ctx.createLinearGradient(0, 0, W * 0.6, H); bgL.addColorStop(0, '#5A1418'); bgL.addColorStop(1, '#22070A');
  const bgR = ctx.createLinearGradient(W, 0, W * 0.4, H); bgR.addColorStop(0, '#0F2E5A'); bgR.addColorStop(1, '#060F22');
  const zoom = t > tFreeze ? 1 + 0.05 * prog(t, tFreeze, tFreeze + 0.35, E.outExpo) + 0.01 * (t - tFreeze) : 1;
  const jit = t > tFreeze && t < tFreeze + 0.25 ? Math.sin(t * 160) * 12 : 0;
  ctx.save(); ctx.translate(W / 2 + jit, H / 2); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -H / 2);
  ctx.fillStyle = bgL; ctx.beginPath(); ctx.moveTo(-50, -50); ctx.lineTo(W * 0.56, -50); ctx.lineTo(W * 0.44, H + 50); ctx.lineTo(-50, H + 50); ctx.fill();
  ctx.fillStyle = bgR; ctx.beginPath(); ctx.moveTo(W * 0.56, -50); ctx.lineTo(W + 50, -50); ctx.lineTo(W + 50, H + 50); ctx.lineTo(W * 0.44, H + 50); ctx.fill();
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(W * 0.56, -50); ctx.lineTo(W * 0.44, H + 50); ctx.stroke();
  // spotlights
  for (const [x, c] of [[W * 0.27, 'rgba(255,120,100,0.18)'], [W * 0.73, 'rgba(100,160,255,0.18)']]) { const g = ctx.createRadialGradient(x, H * 0.55, 10, x, H * 0.55, 520); g.addColorStop(0, c); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  const k = prog(t, t0, t0 + 0.45, E.outExpo);
  const lt = tt - t0;
  const argue = 0.05 + 0.06 * Math.max(0, Math.sin(lt * 5.5));
  const bump = Math.max(0, Math.sin(lt * 5.5)) * 26;
  const ng = prog(tt, tNail, tNail + 3.0, E.lin);
  A.finger(ctx, lerp(-500, 520, k) + bump, 590, 0.9, ng, 0.22 * argue * 2);
  A.foot(ctx, lerp(W + 500, 1400, k) - bump, 640, 0.95, ng * 0.6, -0.25 * argue * 2);
  // anger sparks between them
  if (lt > 0.5) { ctx.save(); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.globalAlpha = Math.max(0, Math.sin(lt * 5.5)); for (const [dx, dy, a] of [[-40, -230, -0.6], [0, -260, 0], [40, -230, 0.6]]) { ctx.beginPath(); ctx.moveTo(W / 2 + dx, 470 + dy); ctx.lineTo(W / 2 + dx + Math.sin(a) * 40, 470 + dy - 40); ctx.stroke(); } ctx.restore(); }
  // VS badge
  const vp = prog(t, t0 + 0.25, t0 + 0.6, E.outBack);
  ctx.save(); ctx.translate(W / 2, 560); ctx.scale(vp, vp); ctx.fillStyle = '#0A0C12'; ctx.beginPath(); ctx.arc(0, 0, 105, 0, 6.283); ctx.fill(); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 8; ctx.stroke();
  F.text(ctx, 'VS', 0, 50, { size: 140, fam: F.FAM.head, align: 'center', color: PAL.yellow, shadow: false }); ctx.restore();
  F.headline(ctx, ['FINGERNAILS', { w: 'VS', c: PAL.yellow }, 'TOENAILS'], W / 2, 190, t - t0 - 0.1, { size: 120, per: 0.08 });
  ctx.restore();
  if (t > tFreeze) { ctx.fillStyle = `rgba(20,24,32,${0.25 * prog(t, tFreeze, tFreeze + 0.2)})`; ctx.fillRect(0, 0, W, H); }
}

// Explorer gag: proud author waves, books fan out; words "UTTER, DAMNED ROT!" knock him back
async function explorerGag(api, o) {
  const W = api.W, H = api.H;
  const { Actor, THREE } = await import('../../lib/actors.js');
  const st = await api.newStage('ch4gag', { shadowExtent: 3, hemi: 0.85, key: 2.5, rim: 3.0, rimColor: 0x9cc8ff, exposure: 1.12, fov: 30 });
  const hero = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });
  const floor = new THREE.Mesh(new THREE.CircleGeometry(3.2, 64), new THREE.ShadowMaterial({ opacity: 0.5 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; st.add(floor);
  // small drifting globe (low-res copy of the day texture)
  const im = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'tex/day_8k.jpg'; });
  const cv = makeCanvas(1024, 512); cv.getContext('2d').drawImage(im, 0, 0, 1024, 512);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const mini = new THREE.Mesh(new THREE.SphereGeometry(0.24, 48, 24), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.85, emissive: 0x112244, emissiveIntensity: 0.25 }));
  mini.castShadow = true; st.add(mini);
  hero.play(o.tWave, 'Wave', { fade: 0.3 });
  hero.play(o.tWave + 2.2, 'Idle_Neutral', { fade: 0.35 });
  hero.play(o.tRot - 0.04, 'HitRecieve', { once: true, fade: 0.06 });
  hero.play(o.tDamned - 0.04, 'HitRecieve_2', { once: true, fade: 0.06 });
  hero.play(o.tRotW - 0.04, 'HitRecieve', { once: true, fade: 0.06 });
  hero.play(o.tRotW + 0.75, 'Idle_Neutral', { fade: 0.4 });
  const ry = 14;
  hero.moveAlong([{ t: 0, x: 0, z: 0, ry }, { t: o.tRot - 0.04, x: 0, z: 0, ry }, { t: o.tRot + 0.18, x: 0.03, z: -0.16, ry: ry + 4, ease: E.out },
    { t: o.tDamned - 0.04, x: 0.03, z: -0.16, ry: ry + 4 }, { t: o.tDamned + 0.18, x: 0.06, z: -0.32, ry: ry - 3, ease: E.out },
    { t: o.tRotW - 0.04, x: 0.06, z: -0.32, ry: ry - 3 }, { t: o.tRotW + 0.25, x: 0.1, z: -0.55, ry: ry + 6, ease: E.out }]);
  const BOOKC = ['#C8443A', '#2F6DB5', '#E2B53B', '#3E9A5B', '#8E5BB5'];
  const words = [['UTTER,', o.tRot], ['DAMNED', o.tDamned], ['ROT!', o.tRotW]];
  return {
    draw(ctx, t, shot, tBrutal, tCut) {
      // backdrop
      const bg = ctx.createRadialGradient(W * 0.5, H * 0.62, 40, W * 0.5, H * 0.55, H * 1.1);
      bg.addColorStop(0, shot === 'A' ? '#24365C' : '#3A2234'); bg.addColorStop(1, '#05070D');
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
      mini.position.set(0.78, 0.98 + Math.sin(t * 1.6) * 0.05, 0.22); mini.rotation.y = t * 0.6; mini.rotation.z = 0.41;
      if (shot === 'A') { const k = (t - tCut + 4) * 0.04; st.lookFrom([1.15 - k * 0.6, 0.42, 4.5 - k], [0.18, 0.66, 0], 30); }
      else { const k = t - tCut; st.lookFrom([1.0 + k * 0.03, 0.32, 3.05 - k * 0.05], [0.62, 0.7, -0.2], 30); }
      ctx.drawImage(st.render(t), 0, 0);
      if (shot === 'A') {
        // books fan out around the Explorer
        const c = st.project(new THREE.Vector3(0, 0.62, 0));
        BOOKC.forEach((col, i) => {
          const tb = tBrutal - 0.1 + i * 0.07; if (t < tb) return;
          const p = prog(t, tb, tb + 0.55, E.outBack); const an = -Math.PI / 2 + (i - 2) * 0.55;
          const r = 360 * p; const x = c.x + Math.cos(an) * r * 1.15, y = c.y - 60 + Math.sin(an) * r * 0.82 + Math.sin(t * 2 + i) * 8;
          A.book(ctx, x, y, 92 * Math.min(1, p * 1.2), (i - 2) * 0.18 + Math.sin(t * 1.5 + i) * 0.05, col, Math.min(1, p * 1.5));
        });
      } else {
        // the quote slams in word by word (each word knocks him back)
        const card = prog(t, words[0][1] - 0.08, words[0][1] + 0.1, E.outExpo);
        let sh = 0; for (const [, tw] of words) if (t > tw - 0.05) sh += Math.exp(-(t - tw + 0.05) * 14) * 14;
        ctx.save(); ctx.translate(1340 + Math.sin(t * 95) * sh, 360 + Math.cos(t * 83) * sh); ctx.rotate(-0.06); ctx.scale(lerp(1.6, 1, card), lerp(1.6, 1, card)); ctx.globalAlpha = card;
        ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, -470 + 14, -140 + 18, 940, 280, 18); ctx.fill();
        ctx.fillStyle = '#F4EBD8'; F.round(ctx, -470, -140, 940, 280, 18); ctx.fill();
        let x = -410;
        for (const [w, tw] of words) {
          const wp = prog(t, tw - 0.06, tw + 0.08, E.outExpo); const ww = F.measure(ctx, w, { size: 150, fam: F.FAM.head, weight: 400, tracking: 0.02 });
          if (wp > 0) { ctx.save(); ctx.translate(x + ww / 2, 55); ctx.scale(lerp(2.2, 1, wp), lerp(2.2, 1, wp)); F.text(ctx, w, 0, 0, { size: 150, fam: F.FAM.head, weight: 400, tracking: 0.02, align: 'center', color: w === 'ROT!' ? '#D8352A' : '#14161C', alpha: wp, shadow: false }); ctx.restore(); }
          x += ww + 38;
        }
        ctx.restore();
        // impact lines from the card toward him
        const c = st.project(new THREE.Vector3(0.05, 0.85, -0.3));
        for (const [, tw] of words) { const k = (t - tw + 0.04) / 0.35; if (k < 0 || k > 1) continue; ctx.save(); ctx.globalAlpha = 1 - k; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 7; ctx.lineCap = 'round'; for (let i = -2; i <= 2; i++) { const a = Math.PI + i * 0.16 - 0.25; const r0 = 140 + k * 90, r1 = 220 + k * 120; ctx.beginPath(); ctx.moveTo(c.x - Math.cos(a) * r0 * -1, c.y + Math.sin(a) * r0); ctx.lineTo(c.x - Math.cos(a) * r1 * -1, c.y + Math.sin(a) * r1); ctx.stroke(); } ctx.restore(); }
      }
    },
  };
}

// rewind scrub card: Equal Earth map, three drips swing toward one point below
function scrubCard(ctx, W, H, t, o) {
  ctx.fillStyle = '#04060B'; ctx.fillRect(0, 0, W, H);
  const lt = t - o.t0;
  const view = { cx: EE_W / 2 + 60 + lt * 6, cy: ee(0, -14)[1], zoom: 1.02 + lt * 0.006 };
  const z = eeScale(view, W, H), ox = W / 2 - view.cx * z, oy = H / 2 - view.cy * z;
  ctx.save(); ctx.globalAlpha = 0.85; ctx.drawImage(o.eeImg, ox, oy, EE_W * z, EE_H * z); ctx.restore();
  ctx.fillStyle = 'rgba(3,5,10,0.52)'; ctx.fillRect(0, 0, W, H);
  // highlighted continents
  ctx.save(); ctx.setTransform(z, 0, 0, z, ox, oy);
  ctx.fillStyle = 'rgba(255,90,54,0.82)'; for (const p of o.paths) ctx.fill(p);
  ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2.2 / z; for (const p of o.paths) ctx.stroke(p);
  ctx.restore();
  // rewind tint lines
  const rw = prog(t, o.rewind - 0.1, o.rewind + 0.3);
  if (rw > 0) { ctx.save(); ctx.globalAlpha = 0.08 * rw; ctx.fillStyle = '#9FD8FF'; for (let y = (lt * 380) % 18; y < H; y += 18) ctx.fillRect(0, y, W, 2); ctx.restore(); }
  // drip arrows: straight down, then swing toward one point off-frame below
  const target = [W * 0.47, H + 520];
  const sw = prog(t, o.place - 0.12, o.place + 0.55, E.outBack);
  o.tips.forEach(([la, lo], i) => {
    const [ix, iy] = ee(lo, la); const x = ox + ix * z, y = oy + iy * z;
    const toward = Math.atan2(target[1] - y, target[0] - x);
    const ang = lerp(Math.PI / 2, toward, sw);
    dripArrow(ctx, x, y + 4, prog(t, o.t0 + 0.2 + i * 0.12, o.t0 + 0.7 + i * 0.12), { len: 105, angle: ang, color: '#ffffff', head: 12 });
    if (sw > 0.02) { ctx.save(); ctx.globalAlpha = 0.35 * sw; ctx.setLineDash([10, 12]); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(lerp(x, target[0], 0.55 * sw), lerp(y, target[1], 0.55 * sw)); ctx.stroke(); ctx.restore(); }
  });
  // scrub bar (above the bottom 12 %)
  const bp = prog(t, o.t0 + 0.1, o.t0 + 0.55, E.outExpo);
  const bx = 980, by = 880, bw = 760;
  ctx.save(); ctx.globalAlpha = bp; ctx.translate(0, (1 - bp) * 40);
  ctx.fillStyle = 'rgba(6,9,16,0.85)'; F.round(ctx, bx - 250, by - 52, bw + 290, 104, 22); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; F.round(ctx, bx, by - 5, bw, 10, 5); ctx.fill();
  const back = prog(t, o.rewind - 0.05, o.t1 + 0.2, E.inOut);
  const hx = bx + bw * (1 - back);
  ctx.fillStyle = PAL.cyan; F.round(ctx, hx, by - 5, bx + bw - hx, 10, 5); ctx.fill();
  F.dot(ctx, hx, by, { r: 11, color: PAL.cyan });
  // rewind glyph
  ctx.fillStyle = (lt * 3) % 1 < 0.6 || t < o.rewind ? PAL.cyan : 'rgba(61,227,255,0.35)';
  for (const dx of [0, 26]) { ctx.beginPath(); ctx.moveTo(bx - 210 + dx, by); ctx.lineTo(bx - 180 + dx, by - 20); ctx.lineTo(bx - 180 + dx, by + 20); ctx.closePath(); ctx.fill(); }
  F.counter(ctx, 0, 180, back, bx - 40, by + 26, { size: 64, align: 'right', format: v => String(Math.round(v)), unit: 'MYA' });
  ctx.restore();
}
