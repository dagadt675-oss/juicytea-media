// Three ep01 moments re-designed with the phone-first system (type.js). Same information as the ep01 frames, new graphics.
//   A  0:25   "So are nearly nine in ten of us."              (was: grey 30 px label + thin bar + 900 px globe)
//   B  3:02   "Most of Antarctica sits directly opposite the Arctic Ocean"  (was: 7-word 26 px caption, 3 px outlines)
//   C 13:40   "Two: the Pacific closes instead ..."           (was: thin arrows, no text, small globe)
// Each shot = { dur, setup(api), world(ctx, lt, api) (globe + map graphics), ui(ctx, lt, api) (text, drawn after post) }.
import * as F from '../../lib/fx.js';
import { loadGeo, findFeature, rings, makeCanvas, gcLine } from '../../lib/geo.js';
import * as T from './type.js';
const { C, px } = T;
const W0 = 1920;
const D = 5.0; // seconds per shot

// Overlay bounds are padded past +-180 deg: lib/globe.js drops overlay pixels whose u is not strictly inside (0,1), which leaves a
// hairline along the date line under any fill that crosses it. The wrapped copies drawn by ringMask fill the padding.
export const OVB = [-181.5, -90, 181.5, 90];
function equirect(cv) { const g = cv.getContext('2d'); const X = (lon) => (lon - OVB[0]) / (OVB[2] - OVB[0]) * cv.width, Y = (lat) => (90 - lat) / 180 * cv.height; return { g, X, Y }; }
function fadeLat(cv, lat0, lat1) { const { g, Y } = equirect(cv); const gr = g.createLinearGradient(0, Y(lat0), 0, Y(lat1)); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.save(); g.globalCompositeOperation = 'destination-in'; g.fillStyle = gr; g.fillRect(0, 0, cv.width, cv.height); g.restore(); }
// Fill rings into an equirect canvas without seams: longitudes are unwrapped, rings that wind around a pole are closed through
// the pole, each wrapped copy (-360/0/+360) is filled as its own evenodd path into an OPAQUE mask (so copies that overlap by a
// sliver never cancel or double up), then the mask is tinted and composited at alpha a.
function ringMask(w, h, rs) {
  const m = makeCanvas(w, h), { g, X, Y } = equirect(m); g.fillStyle = '#fff';
  const un = rs.map(r0 => { const r = []; let off = 0;
    r0.forEach(([lon, lat], i) => { if (i) { const d = lon - r0[i - 1][0]; if (d > 180) off -= 360; else if (d < -180) off += 360; } r.push([lon + off, lat]); });
    const net = r[r.length - 1][0] - r[0][0];
    if (Math.abs(net) > 300) { const ml = r.reduce((s, p) => s + p[1], 0) / r.length, pl = ml > 0 ? 90 : -90; r.push([r[r.length - 1][0], pl], [r[0][0], pl]); }
    return r; });
  for (const sh of [-360, 0, 360]) { g.beginPath(); for (const r of un) { r.forEach(([lon, lat], i) => i ? g.lineTo(X(lon + sh), Y(lat)) : g.moveTo(X(lon + sh), Y(lat))); g.closePath(); } g.fill('evenodd'); }
  return m;
}
function fillRings(cv, rs, col, a, op = 'source-over') {
  const m = ringMask(cv.width, cv.height, rs), mg = m.getContext('2d');
  mg.globalCompositeOperation = 'source-in'; mg.fillStyle = col; mg.fillRect(0, 0, m.width, m.height);
  const g = cv.getContext('2d'); g.save(); g.globalAlpha = a; g.globalCompositeOperation = op; g.drawImage(m, 0, 0); g.restore();
}
function blurInto(dst, draw, px = 8) { const tmp = makeCanvas(dst.width, dst.height); draw(tmp); const g = dst.getContext('2d'); g.filter = `blur(${px}px)`; g.drawImage(tmp, 0, 0); g.filter = 'none'; }
function drawGlobe(api, ctx, state, look) {
  const g = api.g;
  g.set(Object.assign({ sun: 'camera', tilt: 0, heading: 0, fov: 34, sunAz: -30, sunEl: 26 }, state));
  const L = Object.assign({ dim: 0, desat: 0.08, exposure: 1.5, ambient: 0.13, nightAmt: 0, ovAlpha: 1, relief: 1 }, look);
  for (const k in L) if (g.u[k]) g.look(k, L[k]);
  g.starfield(ctx, 0.8);
  ctx.drawImage(g.render(), 0, 0);
  const d = g.disc(); T.navySpace(ctx, api.W, api.H, d.x, d.y);
}

export async function build(api) {
  const W = api.W, H = api.H;
  const CTY = await loadGeo('ne_50m_admin_0_countries');
  const ARC = await loadGeo('arctic_ocean');
  const POP = await loadGeo('ne_110m_populated_places_simple');
  const MAR = await loadGeo('ne_10m_geography_marine_polys');
  const LAND = await loadGeo('ne_50m_land');
  const landR = LAND.features.flatMap(f => rings(f));

  // ============================== A: nine in ten of us live north ==============================
  const ovA = makeCanvas(2048, 1024);
  { const { g, Y } = equirect(ovA); const gr = g.createLinearGradient(0, Y(2), 0, Y(-3)); gr.addColorStop(0, 'rgba(3,6,14,0)'); gr.addColorStop(1, 'rgba(3,6,14,0.62)'); g.fillStyle = gr; g.fillRect(0, Y(2), ovA.width, ovA.height); }
  const cities = POP.features.map(f => ({ lat: f.properties.latitude, lon: f.properties.longitude, pop: f.properties.pop_max })).sort((a, b) => b.pop - a.pop);
  const EQ = [Array.from({ length: 181 }, (_, i) => [-180 + i * 2, 0])];
  const A = {
    dur: D, ov: ovA,
    cam: (lt) => ({ lat: 24, lon: 30 + lt * 1.1, alt: 1.9 - 0.06 * F.prog(lt, 0, D, F.E.inOutSine), lookOffset: [-0.27, 0] }),
    world(ctx, lt) {
      drawGlobe(api, ctx, this.cam(lt), { desat: 0.1, exposure: 1.36 });
      const g = api.g;
      // city lights of the people: white dots, the southern ones dimmer (the point of the shot)
      const cin = F.prog(lt, 0.15, 1.4, F.E.lin);
      ctx.save();
      cities.forEach((c, i) => {
        const k = F.clamp((cin * 1.3 - i / cities.length * 0.3) * 3); if (k <= 0) return;
        const q = g.project(c.lat, c.lon); if (!q.visible) return;
        const r = px(3.2 + Math.sqrt(c.pop) / 620) * F.E.outBack(k), a = c.lat >= 0 ? 1 : 0.55;
        ctx.globalAlpha = 0.22 * k * a; ctx.fillStyle = '#FFF4D6'; ctx.beginPath(); ctx.arc(q.x, q.y, r * 2.6, 0, 7); ctx.fill();
        ctx.globalAlpha = 0.95 * k * a; ctx.fillStyle = C.inkA(0.6); ctx.beginPath(); ctx.arc(q.x, q.y, r + px(1.5), 0, 7); ctx.fill();
        ctx.fillStyle = '#FFF8E8'; ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, 7); ctx.fill();
      });
      ctx.restore();
      // the equator: a real line, 9 px + under-stroke, drawn on
      T.line(ctx, T.projectRuns(g, EQ), { width: 9, p: F.prog(lt, 0.1, 1.3, F.E.inOut) });
    },
    ui(ctx, lt) {
      const g = api.g, cam = this.cam(lt);
      T.scrim(ctx, W, H, 'left', { extent: 0.5, alpha: 0.55 });
      // stat block: kicker / odometer number / pictogram / punch line  (one idea, read top to bottom)
      const x0 = px(118);
      const kick = T.stack(ctx, [{ role: 'kicker', words: ['NEARLY'], tracking: 0.14 }], x0, px(150), lt, { t0: 0.25 });
      const ny = kick.bottom + px(T.CAP.number) + px(8);
      const nv = 9 * F.prog(lt, 0.35, 1.25, F.E.outExpo);
      const nx = T.slot(ctx, nv, x0 - px(6), ny, { to: 9, alpha: F.prog(lt, 0.3, 0.5) });
      T.txt(ctx, 'IN 10', nx + px(26), ny, { fam: T.FAM.num, cap: T.CAP.number, color: C.yellow, stroke: true, alpha: F.prog(lt, 0.45, 0.7) });
      T.people(ctx, x0, ny + px(130), 10, 9, { h: 86, gap: 0.62, p: F.prog(lt, 0.9, 2.2, F.E.lin) });
      T.stack(ctx, [{ role: 'label', cap: 68, words: ['LIVE', { w: 'NORTH', c: C.yellow }] }], x0, ny + px(170), lt, { t0: 1.6 });
      // map label riding the line it names
      let q = null; for (let d = -60; d <= 60; d += 1) { const c = g.project(0, cam.lon + d); if (c.visible && c.x > W * 0.74) { q = c; break; } }
      if (q) T.label(ctx, 'EQUATOR', q.x, q.y, { anchor: 'center', accent: C.text, p: F.prog(lt, 1.0, 1.6, F.E.lin) });
    },
  };

  // ============================== B: Antarctica opposite the Arctic Ocean ==============================
  const antF = findFeature(CTY, 'Antarctica');
  const antR = rings(antF);
  const antMirFull = antR.map(r => r.map(([lon, lat]) => [lon + 180, -lat]));
  const arcR = rings(ARC.features[0]);
  const ovB = makeCanvas(4096, 2048);
  // secondary shape (water): soft edge where it meets other seas, crisp at every coast (land knocked out after the blur); no outline
  blurInto(ovB, (cv) => fillRings(cv, arcR, C.cyan, 0.55), 10); fillRings(ovB, landR, '#000', 1, 'destination-out');
  fillRings(ovB, antMirFull, C.hero, 0.66);                          // hero shape: crisp fill + white outline
  const antOut = antR.map(r => r.map(([lon, lat]) => Math.abs(Math.abs(lon) - 180) < 1e-6 ? [NaN, lat] : [((lon + 360) % 360) - 180, -lat]));
  const B = {
    dur: D, ov: ovB,
    cam: (lt) => ({ lat: 89.9, lon: 20 + lt * 2.0, alt: 1.5 - 0.05 * F.prog(lt, 0, D, F.E.inOutSine), heading: 0, lookOffset: [-0.2, 0], sunEl: 34 }),
    world(ctx, lt) {
      drawGlobe(api, ctx, this.cam(lt), { ovAlpha: F.prog(lt, 0.2, 1.0), dim: 0.22, desat: 0.3, exposure: 1.4 });
      const g = api.g;
      T.outline(ctx, T.projectRuns(g, antOut, { maxLat: 89 }), { color: C.text, width: 5.5, glow: C.hero, p: F.prog(lt, 0.5, 1.7, F.E.inOut) });
    },
    ui(ctx, lt) {
      T.scrim(ctx, W, H, 'left', { extent: 0.55, alpha: 0.6 });
      T.stack(ctx, [
        { role: 'headline', cap: 104, words: [{ w: 'ANTARCTICA', c: C.hero }] },
        { role: 'kicker', cap: 54, words: ['IS', 'OPPOSITE', 'THE'], tracking: 0.1, lead: 0.5 },
        { role: 'headline', cap: 104, words: [{ w: 'ARCTIC', c: C.cyan }, { w: 'OCEAN', c: C.cyan }] },
      ], px(118), px(300), lt, { t0: 0.6, per: 0.14 });
    },
  };

  // ============================== C: model 2, the Pacific closes ==============================
  const pac = MAR.features.filter(f => /^(North|South) Pacific Ocean$/i.test(f.properties.name || f.properties.NAME || ''));
  const ovC = makeCanvas(4096, 2048);
  blurInto(ovC, (cv) => fillRings(cv, pac.flatMap(f => rings(f)), C.cyan, 0.26), 12); fillRings(ovC, landR, '#000', 1, 'destination-out'); fadeLat(ovC, -32, -56); // soft at sea boundaries, crisp at coasts, fades out south
  const arrows = [
    { a: [-14, -48], b: [-16, -97], lift: 0.025, t0: 0.6, d: 1.3 },
    { a: [-75, -50], b: [-64, -72], lift: 0.02, t0: 1.0, d: 1.0, w: 13 },
  ].map(o => Object.assign(o, { path: gcLine(o.a, o.b, 80, o.lift) }));
  const Cs = {
    dur: D, ov: ovC,
    cam: (lt) => ({ lat: -38, lon: -74 + lt * 0.8, alt: 1.8 - 0.05 * F.prog(lt, 0, D, F.E.inOutSine), lookOffset: [-0.12, 0.0] }),
    world(ctx, lt) {
      drawGlobe(api, ctx, this.cam(lt), { ovAlpha: F.prog(lt, 0.1, 0.9), desat: 0.1 });
      const g = api.g;
      for (const ar of arrows) {
        const pts = []; for (const p of ar.path) { const q = g.project(p.lat, p.lon, p.h); if (q.visible) pts.push([q.x, q.y]); }
        T.arrow(ctx, pts, { p: F.prog(lt, ar.t0, ar.t0 + ar.d, F.E.inOut), width: ar.w || 15, t: lt });
      }
    },
    ui(ctx, lt) {
      T.scrim(ctx, W, H, 'left', { extent: 0.5, alpha: 0.5 });
      T.tag(ctx, 'MODEL', 2, 4, px(118), px(110), { p: F.prog(lt, 0.15, 0.9, F.E.lin) });
      T.stack(ctx, [{ role: 'headline', cap: 112, words: [{ w: 'PACIFIC', c: C.cyan }] }, { role: 'headline', cap: 112, words: ['CLOSES'] }], px(118), px(300), lt, { t0: 0.45, per: 0.16, gap: 0.28 });
    },
  };

  // ============================== S: the system on one card (reference still for the style guide) ==============================
  const S = {
    dur: D, ov: null,
    world(ctx, lt) {
      const g0 = ctx.createLinearGradient(0, 0, 0, H); g0.addColorStop(0, '#0E1C33'); g0.addColorStop(1, '#060B16'); ctx.fillStyle = g0; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(255,255,255,0.04)'; ctx.lineWidth = 1; for (let x = 0; x < W; x += px(60)) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); } for (let y = 0; y < H; y += px(60)) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    },
    ui(ctx, lt) {
      const note = (t, x, y, c = '#A9B8CE') => F.text(ctx, t, x, y, { size: px(25), fam: 'Barlow Condensed', weight: 700, color: c, tracking: 0.03, shadow: false });
      const x0 = px(90);
      note('PHONE-FIRST TYPE SYSTEM     all sizes = CAP HEIGHT at 1080p     phone = x0.203 (390 px wide player)', x0, px(52), '#FFD23F');
      // ---- type ladder, note under each sample
      T.slot(ctx, 115, x0, px(255), { to: 115, cap: 170 });
      note('NUMBER   Anton, cap 150-190 px (14-18 %), phone ~35 px.  Yellow, odometer roll, lands on the spoken word.', x0, px(300));
      T.stack(ctx, [{ role: 'headline', cap: 108, words: [{ w: 'PACIFIC', c: C.cyan }, 'CLOSES'] }], x0, px(345), 10);
      note('HEADLINE   Anton, cap 96-120 px (9-11 %), phone ~22 px.  2-4 words; coloured words replace any legend.', x0, px(500));
      const l1 = T.label(ctx, 'EQUATOR', x0, px(600), { accent: C.text });
      T.label(ctx, 'ANTARCTICA', x0 + l1.w + px(26), px(600), { accent: C.hero });
      note('LABEL   Barlow Condensed 800, cap 64 px (6 %), phone 13 px.  Plate 86 % ink, accent bar = colour of the thing.', x0, px(706));
      const k1 = T.txt(ctx, 'NEARLY', x0, px(800), { cap: 48, tracking: 0.14, stroke: true });
      T.txt(ctx, 'MODEL', x0 + k1 + px(60), px(800), { cap: 48, tracking: 0.12, stroke: true });
      note('KICKER   Barlow Condensed 800, cap 48 px = THE FLOOR (phone 10 px).  Connector words only, never the key fact.', x0, px(846));
      F.text(ctx, 'MILLION YEARS AGO · SIMPLIFIED', x0, px(950), { size: px(30), fam: 'Barlow Condensed', weight: 700, color: '#9AA7B8', tracking: 0.16, shadow: false });
      ctx.strokeStyle = '#FF3B3B'; ctx.lineWidth = px(5); ctx.beginPath(); ctx.moveTo(x0 - px(10), px(940)); ctx.lineTo(x0 + px(500), px(940)); ctx.stroke();
      note('ep01: grey, 21-30 px cap = 4-6 px on a phone.  Retired.', x0, px(995), '#FF8A7A');
      // ---- map graphics column
      const gx = px(1300); let gy = px(140);
      note('MAP GRAPHICS  (lines, shapes, arrows: 2-3x ep01)', gx, gy - px(50), '#FFD23F');
      T.line(ctx, [[[gx, gy + px(20)], [gx + px(260), gy + px(4)], [gx + px(520), gy + px(20)]]], { width: 9 });
      note('line: 9-12 px core + dark under-stroke +8 + glow', gx, gy + px(72));
      gy += px(120);
      T.arrow(ctx, [[gx, gy + px(34)], [gx + px(220), gy + px(4)], [gx + px(500), gy + px(14)]], { width: 15, t: lt });
      note('arrow: 15 px body, 63 px head, flowing dashes = motion', gx, gy + px(90));
      gy += px(140);
      ctx.save(); ctx.globalAlpha = 0.66; ctx.fillStyle = C.hero; ctx.beginPath(); ctx.ellipse(gx + px(110), gy + px(30), px(110), px(48), 0, 0, 7); ctx.fill(); ctx.restore();
      const ring = Array.from({ length: 65 }, (_, i) => [gx + px(110) + Math.cos(i / 64 * Math.PI * 2) * px(110), gy + px(30) + Math.sin(i / 64 * Math.PI * 2) * px(48)]);
      T.outline(ctx, [ring], { width: 5.5, glow: C.hero }); T.pin(ctx, gx + px(320), gy + px(30), { color: C.text, t: 0.3 }); note('pin r 11 + pulse', gx + px(350), gy + px(40));
      note('hero fill 55-66 % + 5.5 px white outline', gx, gy + px(118)); note('water: soft edge at sea limits, crisp at coasts', gx, gy + px(150));
      gy += px(200);
      T.people(ctx, gx, gy + px(60), 10, 9, { h: 70, gap: 0.64 }); note('pictogram for "N in 10"', gx, gy + px(104));
      gy += px(140);
      const tg = T.tag(ctx, 'MODEL', 2, 4, gx, gy, { cap: 48 }); note('list tag + pips: where we are (2 of 4)', gx, tg.bottom + px(44));
      gy = tg.bottom + px(66);
      [[C.hero, 'HERO', '#FF5A36'], [C.cyan, 'WATER', '#3DE3FF'], [C.yellow, 'NUMBERS', '#FFD23F'], [C.text, 'TEXT', '#F4F6FA']].forEach(([c, n, h], i) => {
        const x = gx + i * px(140); ctx.fillStyle = c; F.round(ctx, x, gy, px(120), px(40), px(8)); ctx.fill();
        note(n, x, gy + px(66), '#DCE4EF'); note(h, x, gy + px(92)); });
    },
  };
  return [A, B, Cs, S];
}
