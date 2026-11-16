// Story-mode prototype: two ep01 story beats rebuilt as "Archive in the World".
//  A (0-5 s)  "Bacon, 1620": paper cut-out of the real 1617 portrait standing in front of the photoreal globe;
//             the continents he describes light up and point south. Replaces 1:00-1:25 static portrait + Latin plates.
//  B (5-12 s) "Austria said yes": Wegener as a pop-up paper standee standing ON the tilted photoreal Europe, hops from
//             Hamburg to Graz, Austria lights up. Replaces the 7:35-7:50 low-poly corridor.
import * as F from './fx.js';
import { loadGeo, findFeature, rings, fillEquirect, makeCanvas, strokeProjected, gcLine } from './geo.js';
import * as S from './story.js';

export const scenes = [];
const IMG = 'lab/story/img/';
const D2R = Math.PI / 180;

// split rings into runs that stay inside a lat/lon predicate (to outline one continent of a merged land polygon)
function runsWhere(rs, keep) {
  const out = [];
  for (const r of rs) { let cur = []; for (const p of r) { if (keep(p[0], p[1])) cur.push(p); else { if (cur.length > 1) out.push(cur); cur = []; } } if (cur.length > 1) out.push(cur); }
  return out;
}

export async function init(api) {
  const g = await api.globe();
  await api.loadImages([IMG + 'bacon_card.png', IMG + 'wegener_card.png']);
  await g.setPatch(IMG + 'patch_ceurope.jpg', [2, 42, 24, 58]); // GIBS Blue Marble shaded relief, ~500 m: sharp close-ups of Central Europe
  const bacon = S.prepCard(api.img(IMG + 'bacon_card.png'), { light: 'left', rimColor: '#8FD0FF', rimAlpha: 0.95 });
  const weg = S.prepCard(api.img(IMG + 'wegener_card.png'), { light: 'left', rimColor: '#BFE4FF', rimAlpha: 0.7 });
  const c110 = await loadGeo('ne_110m_admin_0_countries'), c50 = await loadGeo('ne_50m_admin_0_countries'), land = await loadGeo('ne_50m_land');
  const W = api.W, H = api.H;

  // ---------- overlays (one active at a time; installed by the owning scene) ----------
  const B_ALL = [-180, -90, 180, 90];
  const ovA = makeCanvas(4096, 2048);
  const conts = c110.features.filter(f => ['South America', 'Africa'].includes(f.properties.CONTINENT) && f.properties.ADMIN !== 'Falkland Islands');
  fillEquirect(ovA, B_ALL, conts, { color: F.PAL.hero, alpha: 0.62, glow: 30 });
  const landRings = land.features.flatMap(f => rings(f));
  const samRuns = runsWhere(landRings, (lon, lat) => lon > -82.5 && lon < -33 && lat < 12.6 && lat > -56.5 && !(lat > 7.2 && lon < -77.2));
  const afrRuns = runsWhere(landRings, (lon, lat) => lon > -18.5 && lon < 52.5 && lat > -35.5 && lat < 37.6 && !(lat > 11.6 && lon > 43.2) && !(lat > 29.8 && lon > 32.4));
  const austria = findFeature(c50, 'Austria'), germany = findFeature(c50, 'Germany');
  const ovB = makeCanvas(4096, 2048), BB = [-20, 30, 50, 65];
  fillEquirect(ovB, BB, [austria], { color: F.PAL.hero, alpha: 0.72, glow: 40 });
  const own = (k, cvs, b) => { if (g._owner !== k) { g.setOverlay(cvs, b); g._owner = k; } };

  // ===================== A: BACON, 1620 =====================
  const A0 = 0, A1 = 5;
  scenes.push({ t0: A0, t1: A1, id: 'A_bacon', draw: (ctx, lt) => {
    own('A', ovA, B_ALL); g.u.patchOn.value = 0;
    const push = F.prog(lt, 0, 5, F.E.inOutSine);
    const Q = api.Q; const st = { lat: (Q.alat ?? -27) - 2 * push, lon: (Q.alon ?? -8) + 3 * push, alt: (Q.aalt ?? 2.0) - 0.07 * push, tilt: Q.atilt ?? 8, heading: -3 + 2 * push, fov: 34, lookOffset: [Q.alo ?? -0.17, Q.alo2 ?? -0.07], sunAz: -22, sunEl: 26 };
    const fill = F.prog(lt, 0.35, 1.0, F.E.out);
    g.u.ambient.value = 0.2; api.drawGlobe(ctx, st, { ovAlpha: fill, dim: 0.1 * fill, exposure: 1.95, desat: 0.1, relief: 0.9, nightAmt: 0, specAmt: 0.25 });
    // continent outlines (crisp white, dark under-stroke) draw on with the fill
    const op = F.prog(lt, 0.35, 1.3, F.E.out);
    for (const runs of [samRuns, afrRuns]) {
      strokeProjected(ctx, g, runs, { width: 9, color: 'rgba(5,10,20,0.55)', p: op, minStep: 2 });
      strokeProjected(ctx, g, runs, { width: 4.5, color: '#FFFFFF', p: op, minStep: 2 });
    }
    // "pointed toward the south": two thick arrows growing south from each tip
    const ap = F.prog(lt, 1.05, 1.75, F.E.out), wob = Math.sin(lt * 5) * 4 * F.clamp(lt - 1.8);
    for (const [la, lo] of [[-56.6, -67.3], [-35.6, 20.0]]) {
      const pts = [0, 1, 2, 3, 4].map(i => { const q = g.project(la - 0.6 - i * 2.4, lo); return [q.x, q.y + wob]; });
      S.arrow(ctx, pts, ap, { width: 15, head: 50 });
    }
    // light leak from the window side + dust in the air between the viewer and Bacon
    S.leak(ctx, 330, 560, 760, '70,110,170', 0.42);  // cool studio backlight behind the cut-out (separates him from space)
    S.leak(ctx, -60, -120, 1050, '255,170,95', 0.30 + 0.05 * Math.sin(lt * 1.3));
    // Bacon: paper cut-out, slides in with overshoot, then a slow push faster than the globe (parallax)
    const inP = F.prog(lt, 0, 0.55, F.E.outBack);
    const hgt = (Q.bh ?? 1060) * (1 + 0.055 * push);
    S.drawCard(ctx, bacon, (Q.bx ?? 300) - (1 - inP) * 700 + 16 * push, H + 200, hgt, { rot: (-2.4 + 1.2 * push) * D2R, shadowAlpha: 0.62, shadowDx: 34, shadowDy: 18 });
    S.dust(ctx, lt, { seed: 11, n: 46, rect: [0, 0, W, H], vx: 10, vy: 7 });
    S.grade(ctx, W, H, { warm: 0.24, teal: 0.2, vignette: 0.34 });
    // ---- UI layer (crisp, after the grade) ----
    const qa = F.prog(lt, 0.45, 0.8);
    const g2 = ctx.createRadialGradient(1440, 170, 0, 1440, 170, 760); g2.addColorStop(0, `rgba(4,8,16,${0.6 * qa})`); g2.addColorStop(0.55, `rgba(4,8,16,${0.42 * qa})`); g2.addColorStop(1, 'rgba(4,8,16,0)');
    ctx.save(); ctx.translate(1440, 170); ctx.scale(1, 0.48); ctx.translate(-1440, -170); ctx.fillStyle = g2; ctx.fillRect(600, -700, 1700, 1800); ctx.restore();
    S.bigLines(ctx, [[{ w: '“POINTED' }, { w: 'TOWARD' }], [{ w: 'THE' }, { w: 'SOUTH.”', c: F.PAL.hero }]], 1015, 80, lt, { size: 148, t0: 0.5, per: 0.09 });
    const tp = F.prog(lt, 1.3, 1.65, F.E.outBack);
    if (tp > 0.001) {
      ctx.save(); ctx.translate(70, 846); ctx.scale(0.85 + 0.15 * tp, 0.85 + 0.15 * tp); ctx.globalAlpha = F.clamp(tp * 1.5);
      const o1 = { size: 70, fam: F.FAM.label, weight: 700, tracking: 0.03, baseline: 'top', shadow: false }, w1 = F.measure(ctx, 'FRANCIS BACON', o1), w2 = F.measure(ctx, '1620', o1);
      S.plate(ctx, 0, 0, w1 + w2 + 92, 104, { bar: F.PAL.yellow });
      F.text(ctx, 'FRANCIS BACON', 30, 20, o1);
      F.text(ctx, '1620', 30 + w1 + 28, 20, { ...o1, color: F.PAL.yellow });
      ctx.restore();
    }
  } });

  // ===================== B: AUSTRIA SAID YES =====================
  const B0 = 5, B1 = 12;
  const HAM = [53.55, 9.99], GRZ = [47.07, 15.44];
  const hop = gcLine(HAM, GRZ, 64, 0);
  const T_UP = 0.15, T_CROUCH = 1.0, T_JUMP = 1.25, T_LAND = 2.25;
  const HSTAND = 0.043;
  scenes.push({ t0: B0, t1: B1, id: 'B_wegener', draw: (ctx, lt) => {
    own('B', ovB, BB); g.u.patchOn.value = 1;
    const push = F.prog(lt, 0, 7, F.E.inOutSine);
    const Q = api.Q, fol = F.prog(lt, T_JUMP - 0.1, T_LAND + 0.35, F.E.inOut);  // camera follows the hop, landing a beat after him
    const st = { lat: F.lerp(50.6, (Q.blat ?? 47.6), fol) + 0.5 * push, lon: F.lerp(10.6, (Q.blon ?? 12.6), fol) + 0.6 * push, alt: (Q.balt ?? 0.17) - 0.025 * push, tilt: Q.btilt ?? 56, heading: 4 + 5 * push, fov: 34, lookOffset: [0.0, Q.blo ?? 0.25], sunAz: -40, sunEl: 30 };
    const lit = F.prog(lt, T_LAND + 0.05, T_LAND + 0.45, F.E.out);
    g.u.ambient.value = 0.1; api.drawGlobe(ctx, st, { ovAlpha: lit, dim: 0.18 * lit, exposure: 1.6, desat: 0.06, relief: 1.0, nightAmt: 0, specAmt: 0.2 });
    // Germany: thin dashed border so the viewer knows where he is coming from
    strokeProjected(ctx, g, rings(germany), { width: 5, color: 'rgba(5,10,20,0.45)', minStep: 2 });
    strokeProjected(ctx, g, rings(germany), { width: 2.6, color: 'rgba(255,255,255,0.85)', dash: [10, 9], minStep: 2 });
    strokeProjected(ctx, g, rings(austria), { width: 9, color: 'rgba(5,10,20,0.5)', minStep: 2, p: lit });
    strokeProjected(ctx, g, rings(austria), { width: 4.5, color: '#FFFFFF', minStep: 2, p: lit });
    // tilt-shift: far horizon and near foreground melt away -> miniature / diorama feel
    S.sky(ctx, g, W, H);
    S.tiltShift(ctx, W, H, { top: 0.34, bottom: 0.16, strength: 1 });
    // hop trail (dashed yellow arc in the air)
    const jp = F.prog(lt, T_JUMP, T_LAND, F.E.inOut);
    const LIFT = 0.022;
    if (lt > T_JUMP) {
      const n = Math.max(2, Math.round(jp * 64));
      const pts = hop.slice(0, n + 1).map((p, i) => { const q = g.project(p.lat, p.lon, LIFT * Math.sin(Math.PI * i / 64)); return [q.x, q.y]; });
      const ta = 1 - F.prog(lt, 3.6, 4.4);
      ctx.save(); ctx.globalAlpha = ta; ctx.lineCap = 'round'; ctx.setLineDash([18, 16]);
      ctx.strokeStyle = 'rgba(5,10,20,0.55)'; ctx.lineWidth = 15; ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
      ctx.strokeStyle = F.PAL.yellow; ctx.lineWidth = 9; ctx.stroke(); ctx.restore();
    }
    // the standee: pops up (hinge) at Hamburg, crouches, hops, lands with squash + overshoot
    let lat = HAM[0], lon = HAM[1], lift = 0, hinge = 1 - F.prog(lt, T_UP, T_UP + 0.55, F.E.outBack), sq = 0, lean = 0;
    if (lt > T_CROUCH && lt <= T_JUMP) { sq = 0.18 * F.prog(lt, T_CROUCH, T_JUMP, F.E.out); lean = -0.05 * F.prog(lt, T_CROUCH, T_JUMP); }
    if (lt > T_JUMP && lt <= T_LAND) {
      const i = jp * 64, i0 = Math.floor(i), k = i - i0, a = hop[Math.min(64, i0)], b = hop[Math.min(64, i0 + 1)];
      lat = a.lat + (b.lat - a.lat) * k; lon = a.lon + (b.lon - a.lon) * k; lift = LIFT * Math.sin(Math.PI * jp);
      sq = -0.14 * Math.sin(Math.PI * Math.min(1, jp * 1.6)); lean = 0.10 * Math.sin(Math.PI * jp);
    }
    if (lt > T_LAND) {
      lat = GRZ[0]; lon = GRZ[1];
      const u = lt - T_LAND; sq = 0.22 * Math.exp(-u * 7) * Math.cos(u * 22); lean = -0.03 * Math.exp(-u * 6) * Math.sin(u * 18);
    }
    const hgt = HSTAND * (1 + (lt > T_JUMP ? 0 : 0));
    const sd = S.standee(ctx, g, weg, { lat, lon, h: hgt, lift, hinge, squash: sq, lean, shLat: 0.8, shLon: 0.45, shAlpha: 0.3 });
    // landing dust puff
    if (lt > T_LAND && lt < T_LAND + 0.9) {
      const u = (lt - T_LAND) / 0.9, q = g.project(GRZ[0], GRZ[1], 0);
      ctx.save(); const r = F.rng(5);
      for (let i = 0; i < 14; i++) { const an = Math.PI + r() * Math.PI, d = (40 + r() * 120) * F.E.out(u) * (sd.w / 300); const x = q.x + Math.cos(an) * d * 1.6, y = q.y + Math.sin(an) * d * 0.35 - 20 * u; const rr = (14 + r() * 22) * (0.6 + u) * (sd.w / 300);
        const gr = ctx.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, `rgba(235,225,205,${0.5 * (1 - u)})`); gr.addColorStop(1, 'rgba(235,225,205,0)'); ctx.fillStyle = gr; ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
      ctx.restore();
    }
    // sun flare at the horizon side (same key light as globe)
    S.leak(ctx, 120, 40, 700, '255,214,160', 0.22);
    S.grade(ctx, W, H, { warm: 0.2, teal: 0.18, vignette: 0.3 });
    // ---- UI ----
    if (lt > T_LAND + 0.25) {
      const g2 = ctx.createLinearGradient(0, 0, 0, 380); g2.addColorStop(0, 'rgba(4,8,16,0.55)'); g2.addColorStop(1, 'rgba(4,8,16,0)');
      ctx.save(); ctx.globalAlpha = F.prog(lt, T_LAND + 0.25, T_LAND + 0.6); ctx.fillStyle = g2; ctx.fillRect(0, 0, W, 380); ctx.restore();
      S.bigLines(ctx, [[{ w: 'AUSTRIA' }, { w: 'SAID' }, { w: 'YES.', c: F.PAL.hero }]], 110, 72, lt, { size: 158, t0: T_LAND + 0.3, per: 0.12 });
    }
    const pp = F.prog(lt, T_LAND + 0.7, T_LAND + 1.0, F.E.outBack);
    if (pp > 0.001) {
      const pw = 300, x = sd.x - pw / 2, y = sd.y - 46;  // name plate glued to the standee's base, which stands on Graz
      ctx.save(); ctx.globalAlpha = F.clamp(pp * 1.5); ctx.translate(x, y); ctx.scale(0.8 + 0.2 * pp, 0.8 + 0.2 * pp);
      const o1 = { size: 68, fam: F.FAM.label, weight: 700, tracking: 0.03, baseline: 'top', shadow: false }, w1 = F.measure(ctx, 'GRAZ', o1), w2 = F.measure(ctx, '1924', o1);
      S.plate(ctx, 0, 0, w1 + w2 + 86, 100, { bar: F.PAL.yellow });
      F.text(ctx, 'GRAZ', 30, 18, o1);
      F.text(ctx, '1924', 30 + w1 + 24, 18, { ...o1, color: F.PAL.yellow });
      ctx.restore();
    }
  } });
}
export function post(ctx, t, f, api) { F.post(ctx, api.W, api.H, f, { vignette: 0.12, grain: 0.055 }); }
