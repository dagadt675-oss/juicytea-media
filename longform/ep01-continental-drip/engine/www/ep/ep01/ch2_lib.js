// ch2 helpers: Equal Earth flat-map maths (lib/equalearth.js does not load: it contains a stray `np.float64(...)`),
// fast globe projection with horizon clamping, polygon utilities, stamps/icons.
import * as F from '../../lib/fx.js';
const { PAL, prog, E, clamp, lerp } = F;
const D2R = Math.PI / 180;

// ---------------- Equal Earth (matches tex/equal_earth.jpg, 3600x1760) ----------------
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2, S = 651.7329707517487, CX = 1800, CY = 880;
export const EE_W = 3600, EE_H = 1760;
export function ee(lon, lat) {
  const l = lon * D2R, p = lat * D2R, th = Math.asin(M * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [CX + x * S, CY - y * S];
}
// view {cx, cy, zoom} in image px -> affine {z, ox, oy}: screen = o + img * z
export function eeAff(view, W = 1920, H = 1080) { const z = view.zoom * Math.min(W / EE_W, H / EE_H); return { z, ox: W / 2 - view.cx * z, oy: H / 2 - view.cy * z }; }
export function eeScr(lon, lat, view, W = 1920, H = 1080) { const a = eeAff(view, W, H); const [x, y] = ee(lon, lat); return [a.ox + x * a.z, a.oy + y * a.z]; }
export function eeViewAt(lon, lat, zoom) { const [x, y] = ee(lon, lat); return { cx: x, cy: y, zoom }; }
export function lerpView(a, b, k) { return { cx: lerp(a.cx, b.cx, k), cy: lerp(a.cy, b.cy, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)) }; }
export function drawEEImg(ctx, img, view, W = 1920, H = 1080, alpha = 1) {
  const a = eeAff(view, W, H); ctx.save(); ctx.globalAlpha *= alpha; ctx.drawImage(img, a.ox, a.oy, EE_W * a.z, EE_H * a.z); ctx.restore();
}
// Path2D in EE image px for rings ([[lon,lat],...]); returns {path, len}
export function eePath(ringsArr) {
  const p = new Path2D(); let len = 0;
  for (const r of ringsArr) {
    let px = null, py = null;
    r.forEach(([lon, lat], i) => { const [x, y] = ee(lon, lat); if (i) { p.lineTo(x, y); len += Math.hypot(x - px, y - py); } else p.moveTo(x, y); px = x; py = y; });
    p.closePath();
  }
  return { path: p, len };
}
// outline of the whole Equal Earth map (for clipping)
export function eeOutline() {
  const r = []; for (let la = -90; la <= 90; la += 2) r.push([180, la]); for (let la = 90; la >= -90; la -= 2) r.push([-180, la]);
  return eePath([r]).path;
}
// antipode of rings: lat -> -lat, lon -> lon + 180 (each ring kept contiguous)
export function antiRings(ringsArr) {
  return ringsArr.map(r => {
    const out = r.map(([lo, la]) => [lo + 180, -la]);
    const mean = out.reduce((a, p) => a + p[0], 0) / out.length;
    const sh = mean > 180 ? -360 : 0;
    return out.map(([lo, la]) => [lo + sh, la]);
  });
}
// interpolated flip of a ring set: k=0 original, k=1 antipode (slides east and mirrors across the equator)
export function flipRings(ringsArr, k) {
  return ringsArr.map(r => {
    const mean = r.reduce((a, p) => a + p[0], 0) / r.length;
    const sh = mean + 180 > 180 ? -360 : 0;
    return r.map(([lo, la]) => [lo + (180 + sh) * k, la * (1 - 2 * k)]);
  });
}
// with an affine set on ctx (ctx.setTransform(z,0,0,z,ox,oy)) draw things in image px
export function withEE(ctx, view, fn, W = 1920, H = 1080) { const a = eeAff(view, W, H); ctx.save(); ctx.setTransform(a.z, 0, 0, a.z, a.ox, a.oy); fn(a.z); ctx.restore(); }

// ---------------- globe vectors & projection ----------------
export function dir(lat, lon) { const a = lat * D2R, b = lon * D2R; return [Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)]; }
export function ll(v) { const L = Math.hypot(v[0], v[1], v[2]); return [Math.asin(v[1] / L) / D2R, Math.atan2(-v[2], v[0]) / D2R]; }
export function ringsXYZ(ringsArr) { return ringsArr.map(r => { const a = new Float32Array(r.length * 3); r.forEach(([lo, la], i) => { const v = dir(la, lo); a[i * 3] = v[0]; a[i * 3 + 1] = v[1]; a[i * 3 + 2] = v[2]; }); return a; }); }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
// rotation (axis-angle) that takes unit vector A to B, applied with fraction k
export function rotAB(A, B, k = 1) {
  let ax = cross(A, B); const s = Math.hypot(...ax); const th = Math.atan2(s, dot3(A, B)) * k;
  ax = s < 1e-9 ? [0, 1, 0] : ax.map(x => x / s);
  return { ax, th };
}
export function rotXYZ(arr, R) {
  const [kx, ky, kz] = R.ax, c = Math.cos(R.th), s = Math.sin(R.th), out = new Float32Array(arr.length);
  for (let i = 0; i < arr.length; i += 3) {
    const x = arr[i], y = arr[i + 1], z = arr[i + 2], kd = kx * x + ky * y + kz * z;
    const cx = ky * z - kz * y, cy = kz * x - kx * z, cz = kx * y - ky * x;
    out[i] = x * c + cx * s + kx * kd * (1 - c); out[i + 1] = y * c + cy * s + ky * kd * (1 - c); out[i + 2] = z * c + cz * s + kz * kd * (1 - c);
  }
  return out;
}
export function rotVec(v, R) { const a = rotXYZ(new Float32Array(v), R); return [a[0], a[1], a[2]]; }
// per-frame projector from the globe camera (call after api.drawGlobe)
export function projector(g, W = 1920, H = 1080) {
  const cam = g.camera; const m = cam.projectionMatrix.clone().multiply(cam.matrixWorldInverse).elements;
  const c = cam.position, d = c.length(), cx = c.x / d, cy = c.y / d, cz = c.z / d, h = 1 / d, s = Math.sqrt(Math.max(0, 1 - h * h));
  const P = (x, y, z) => { const w = m[3] * x + m[7] * y + m[11] * z + m[15]; return [((m[0] * x + m[4] * y + m[8] * z + m[12]) / w + 1) / 2 * W, (1 - (m[1] * x + m[5] * y + m[9] * z + m[13]) / w) / 2 * H]; };
  return {
    d, h,
    // returns [x, y, visible]; hidden points are squashed onto the horizon circle when clampHidden
    xyz(x, y, z, clampHidden = true, lift = 0) {
      const dt = x * cx + y * cy + z * cz; const vis = dt > h + 1e-4;
      if (!vis && clampHidden) { let tx = x - dt * cx, ty = y - dt * cy, tz = z - dt * cz; const L = Math.hypot(tx, ty, tz) || 1; x = h * cx + s * tx / L; y = h * cy + s * ty / L; z = h * cz + s * tz / L; }
      const r = 1 + lift; const q = P(x * r, y * r, z * r); q.push(vis); return q;
    },
    ll(lat, lon, lift = 0) { const v = dir(lat, lon); return this.xyz(v[0], v[1], v[2], false, lift); },
    // signed distance of a unit vector past the horizon (> 0 visible, < 0 behind the globe)
    facing(x, y, z) { return x * cx + y * cy + z * cz - h; },
    disc() { const ang = Math.asin(Math.min(1, h)); const f = H / 2 / Math.tan(cam.fov * D2R / 2); const c0 = P(0, 0, 0); return { x: c0[0], y: c0[1], r: Math.tan(ang) * f }; },
  };
}
// fill/stroke xyz rings on the globe (2D overlay). Hidden vertices are clamped to the limb so shapes slide over the horizon.
export function globePath(pj, arrs, clampHidden = true) {
  const p = new Path2D();
  for (const a of arrs) { for (let i = 0; i < a.length; i += 3) { const q = pj.xyz(a[i], a[i + 1], a[i + 2], clampHidden); if (i) p.lineTo(q[0], q[1]); else p.moveTo(q[0], q[1]); } p.closePath(); }
  return p;
}
// visible-only stroke runs with draw-on fraction p (0..1)
export function strokeGlobe(ctx, pj, arrs, o = {}) {
  const runs = []; let total = 0;
  for (const a of arrs) {
    let cur = [];
    for (let i = 0; i < a.length; i += 3) {
      const q = pj.xyz(a[i], a[i + 1], a[i + 2], false);
      if (!q[2]) { if (cur.length > 1) runs.push(cur); cur = []; continue; }
      cur.push(q);
    }
    if (o.closed !== false && cur.length > 1 && a.length >= 6) { const q = pj.xyz(a[0], a[1], a[2], false); if (q[2]) cur.push(q); }
    if (cur.length > 1) runs.push(cur);
  }
  const lens = runs.map(r => { let L = 0; for (let i = 1; i < r.length; i++) L += Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1]); total += L; return L; });
  const budget0 = total * clamp(o.p ?? 1);
  const pass = (lw, col) => {
    let bud = budget0; ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
    for (const r of runs) {
      if (bud <= 0) break; ctx.moveTo(r[0][0], r[0][1]);
      for (let i = 1; i < r.length; i++) { const d = Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1]); if (d > bud) { const k = bud / d; ctx.lineTo(lerp(r[i - 1][0], r[i][0], k), lerp(r[i - 1][1], r[i][1], k)); bud = 0; break; } ctx.lineTo(r[i][0], r[i][1]); bud -= d; }
    }
    ctx.stroke();
  };
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); ctx.lineJoin = 'round'; ctx.lineCap = 'round'; if (o.dash) ctx.setLineDash(o.dash);
  const w = o.width || 2.5, col = o.color || '#ffffff';
  if (o.glow !== false) { pass(w * 5, col + '1c'); pass(w * 2.4, col + '44'); }
  pass(w, col);
  ctx.restore();
}

// ---------------- misc drawing ----------------
export function hexA(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }
export function glowDot(ctx, x, y, r, col, a = 1) {
  ctx.save(); ctx.globalAlpha *= a; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(0.25, hexA(col, 0.5)); g.addColorStop(1, hexA(col, 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}
export function ring(ctx, x, y, r, col, lw = 3, a = 1) { ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
// pulse marker: core dot + expanding rings
export function pulse(ctx, x, y, lt, o = {}) {
  const col = o.color || PAL.text, r = o.r || 8, a = o.alpha ?? 1, pop = E.outBack(clamp(lt / 0.3));
  if (a <= 0) return;
  for (let k = 0; k < 2; k++) { const ph = ((lt * (o.speed || 0.8)) + k * 0.5) % 1; ring(ctx, x, y, r + ph * r * (o.spread || 6), col, 2.5, a * (1 - ph) * 0.9); }
  glowDot(ctx, x, y, r * 4 * pop, col, a * 0.55);
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, r * pop, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
}
// brand verdict stamp "JUICE CHECK: <verdict>" — slams in (scale 2.2 -> 1) with a rotation, then breathes
export function juiceStamp(ctx, x, y, lt, verdict, o = {}) {
  if (lt < 0) return;
  const col = o.color || PAL.danger, size = o.size || 64;
  const p = clamp(lt / (o.dur || 0.28)); const s = lerp(o.from ?? 2.4, 1, E.in(p)) * (o.scale || 1);
  const shake = p >= 1 ? Math.sin(lt * 60) * Math.exp(-(lt - (o.dur || 0.28)) * 9) * 6 : 0;
  ctx.save(); ctx.translate(x + shake, y); ctx.rotate((o.rot ?? -8) * D2R + (1 - p) * (o.spin ?? 0)); ctx.scale(s, s); ctx.globalAlpha *= (o.fadeIn === false ? 1 : clamp(p * 3)) * (o.alpha ?? 1);
  const t1 = 'JUICE CHECK', t2 = verdict;
  const w1 = F.measure(ctx, t1, { size: size * 0.42, fam: F.FAM.label, weight: 700, tracking: 0.3 });
  const w2 = F.measure(ctx, t2, { size, fam: F.FAM.head, weight: 400, tracking: 0.06 });
  const bw = Math.max(w1, w2) + size * 1.0, bh = size * 1.75;
  ctx.fillStyle = o.bg || 'rgba(10,6,6,0.55)'; F.round(ctx, -bw / 2, -bh / 2, bw, bh, 12); ctx.fill();
  ctx.strokeStyle = col; ctx.lineWidth = size * 0.08; F.round(ctx, -bw / 2, -bh / 2, bw, bh, 12); ctx.stroke();
  ctx.lineWidth = size * 0.03; F.round(ctx, -bw / 2 + size * 0.14, -bh / 2 + size * 0.14, bw - size * 0.28, bh - size * 0.28, 8); ctx.stroke();
  F.text(ctx, t1, 0, -bh / 2 + size * 0.62, { size: size * 0.42, fam: F.FAM.label, weight: 700, tracking: 0.3, align: 'center', color: col, shadow: false });
  F.text(ctx, t2, 0, bh / 2 - size * 0.3, { size, fam: F.FAM.head, weight: 400, tracking: 0.06, align: 'center', color: col, shadow: false });
  ctx.restore();
}
// red X slam (no words)
export function xStamp(ctx, x, y, lt, size = 90) {
  if (lt < 0) return;
  const p = clamp(lt / 0.18), s = lerp(2.2, 1, E.in(p));
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(-6 * D2R); ctx.globalAlpha *= clamp(p * 3);
  ctx.lineCap = 'round';
  for (const [lw, col] of [[size * 0.34, 'rgba(0,0,0,0.45)'], [size * 0.22, PAL.danger]]) {
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(-size / 2, -size / 2); ctx.lineTo(size / 2, size / 2); ctx.moveTo(size / 2, -size / 2); ctx.lineTo(-size / 2, size / 2); ctx.stroke();
  }
  ctx.restore();
}
// jigsaw puzzle piece icon
export function puzzleIcon(ctx, x, y, s, col, a = 1, rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s / 100, s / 100); ctx.globalAlpha *= a;
  const p = new Path2D();
  p.moveTo(-40, -40); p.lineTo(-10, -40); p.bezierCurveTo(-18, -62, 18, -62, 10, -40); p.lineTo(40, -40); p.lineTo(40, -10);
  p.bezierCurveTo(62, -18, 62, 18, 40, 10); p.lineTo(40, 40); p.lineTo(10, 40); p.bezierCurveTo(18, 62, -18, 62, -10, 40); p.lineTo(-40, 40);
  p.lineTo(-40, 10); p.bezierCurveTo(-18, 18, -18, -18, -40, -10); p.closePath();
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.translate(4, 6); ctx.fill(p); ctx.translate(-4, -6);
  ctx.fillStyle = col; ctx.fill(p); ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 5; ctx.stroke(p);
  ctx.restore();
}
// small shovel icon
export function shovelIcon(ctx, x, y, s, a = 1, rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s / 100, s / 100); ctx.globalAlpha *= a; ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 16; ctx.beginPath(); ctx.moveTo(0, -70); ctx.lineTo(0, 10); ctx.stroke();
  ctx.strokeStyle = '#C89A5B'; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(0, -70); ctx.lineTo(0, 10); ctx.stroke();
  ctx.strokeStyle = '#C89A5B'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(-16, -74); ctx.lineTo(16, -74); ctx.stroke();
  ctx.fillStyle = '#DDE3EA'; ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(-22, 6); ctx.lineTo(22, 6); ctx.lineTo(20, 42); ctx.quadraticCurveTo(0, 70, -20, 42); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
}
// pill with a drawn arrow between two words: "A -> B"
export function arrowPill(ctx, a, b, x, y, o = {}) {
  const size = o.size || 40, al = o.alpha ?? 1; if (al <= 0) return;
  const wa = F.measure(ctx, a, { size, fam: F.FAM.label, weight: 700, tracking: 0.08 }), wb = F.measure(ctx, b, { size, fam: F.FAM.label, weight: 700, tracking: 0.08 });
  const aw = size * 1.3, padX = size * 0.6, padY = size * 0.34, bw = wa + wb + aw + padX * 2 + size * 0.4, bh = size + padY * 2;
  const bx = x - bw / 2, by = y - bh / 2;
  ctx.save(); ctx.globalAlpha *= al;
  ctx.fillStyle = 'rgba(0,0,0,0.22)'; F.round(ctx, bx - 3, by - 1, bw + 6, bh + 8, bh / 2 + 3); ctx.fill();
  ctx.fillStyle = 'rgba(8,11,18,0.78)'; F.round(ctx, bx, by, bw, bh, bh / 2); ctx.fill();
  if (o.border) { ctx.strokeStyle = o.border; ctx.lineWidth = 2.5; F.round(ctx, bx, by, bw, bh, bh / 2); ctx.stroke(); }
  let cx = bx + padX;
  F.text(ctx, a, cx, by + bh / 2 + size * 0.36, { size, fam: F.FAM.label, weight: 700, tracking: 0.08, color: o.ca || PAL.hero, shadow: false });
  cx += wa + size * 0.2;
  const ay = by + bh / 2; ctx.strokeStyle = PAL.text; ctx.fillStyle = PAL.text; ctx.lineWidth = size * 0.1; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx + 4, ay); ctx.lineTo(cx + aw - 12, ay); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx + aw - 2, ay); ctx.lineTo(cx + aw - 18, ay - 11); ctx.lineTo(cx + aw - 18, ay + 11); ctx.closePath(); ctx.fill();
  cx += aw + size * 0.2;
  F.text(ctx, b, cx, by + bh / 2 + size * 0.36, { size, fam: F.FAM.label, weight: 700, tracking: 0.08, color: o.cb || PAL.text, shadow: false });
  ctx.restore();
}
// Bebas headline line centred (cheap wrapper)
export function bigLine(ctx, s, x, y, lt, o = {}) { F.headline(ctx, s.split(' ').map(w => (o.accent || []).includes(w) ? { w, c: PAL.hero } : w), x, y, lt, o); }
// motion streaks for whips
export function streaks(ctx, W, H, k, vertical = true, seed = 7) {
  if (k <= 0.01) return; const r = F.rng(seed);
  ctx.save(); ctx.globalAlpha *= k; ctx.strokeStyle = 'rgba(220,235,255,0.35)';
  for (let i = 0; i < 40; i++) { const a = r() * (vertical ? W : H), b = r() * (vertical ? H : W), L = 80 + r() * 260; ctx.lineWidth = 1 + r() * 2; ctx.beginPath(); if (vertical) { ctx.moveTo(a, b); ctx.lineTo(a, b + L); } else { ctx.moveTo(b, a); ctx.lineTo(b + L, a); } ctx.stroke(); }
  ctx.restore();
}
// counter text "x.x MI" style using Inter tabular digits
export function miles(ctx, v, x, y, o = {}) { F.counter(ctx, v, v, 1, x, y, { size: o.size || 64, decimals: 1, unit: o.unit ?? 'MI', align: o.align || 'left', alpha: o.alpha ?? 1, prefix: o.prefix, color: o.color, unitColor: o.unitColor || PAL.text }); }
