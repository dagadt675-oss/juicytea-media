// ch5b helpers: Equal Earth projection (local copy), teardrop geometry, paper sheets, icons, cross-sections.
// Everything deterministic (seeded rng only), heavy canvases are built once in build().
import * as F from '../../lib/fx.js';
const { PAL, prog, env, clamp, lerp, E } = F;
export const W = 1920, H = 1080, D2R = Math.PI / 180;
export function cv(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };

// ---------------- Equal Earth (lib/equalearth.js has a stray `np.float64` -> unusable; local copy) ----------------
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, MM = Math.sqrt(3) / 2;
export const EE_W = 3600, EE_H = 1760, EE_S = 651.7329707517487;
export function ee(lon, lat) {
  const l = lon * D2R, p = lat * D2R, th = Math.asin(MM * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (MM * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [1800 + x * EE_S, 880 - y * EE_S];
}
// view {cx, cy, zoom} (cx, cy in EE image px) -> screen transform
export function eeT(view, w = W, h = H) { const z = view.zoom * Math.min(w / EE_W, h / EE_H); return { z, ox: w / 2 - view.cx * z, oy: h / 2 - view.cy * z }; }
export function eeP(T, lon, lat) { const [x, y] = ee(lon, lat); return [T.ox + x * T.z, T.oy + y * T.z]; }
// km^2 -> EE image px scale factor for a unit-area shape
export const eeScaleForArea = (mkm2) => Math.sqrt(mkm2 * 1e6 / (6371 * 6371)) * EE_S;

// EE outline (map boundary) as an EE-px polygon
export function eeOutline() {
  const pts = [];
  for (let la = -90; la <= 90; la += 2) pts.push(ee(180, la));
  for (let la = 90; la >= -90; la -= 2) pts.push(ee(-180, la));
  return pts;
}

// rings [[lon,lat],...] -> Path2D in EE image px (antimeridian-safe for split data; skips polar closure edges)
export function eePath(ringsArr, o = {}) {
  const p = new Path2D();
  for (const r of ringsArr) {
    let first = true, plon = null;
    for (const [lon, lat] of r) {
      if (o.skipPole && lat < -89.5) { first = true; continue; }
      const [x, y] = ee(lon, lat);
      if (first || (plon !== null && Math.abs(lon - plon) > 180)) { p.moveTo(x, y); first = false; } else p.lineTo(x, y);
      plon = lon;
    }
    if (o.close) p.closePath();
  }
  return p;
}

// ---------------- teardrop geometry ----------------
// unit-area teardrop, round end up, tip down (+y), centroid at the origin (screen coords, y down)
export const DROP = (() => {
  const d = 2.7, a1 = Math.asin(1 / d), pts = [], nA = 64;
  for (let i = 0; i <= nA; i++) { const a = a1 + (-Math.PI - 2 * a1) * i / nA; pts.push([Math.cos(a), Math.sin(a)]); }
  const P2 = pts[pts.length - 1], P1 = pts[0], T = [0, d];
  const quad = (A, B, n, last) => { const c = [(A[0] + B[0]) / 2 * 0.62, (A[1] + B[1]) / 2]; for (let i = 1; i <= (last ? n : n - 1); i++) { const t = i / n; pts.push([(1 - t) * (1 - t) * A[0] + 2 * (1 - t) * t * c[0] + t * t * B[0], (1 - t) * (1 - t) * A[1] + 2 * (1 - t) * t * c[1] + t * t * B[1]]); } };
  quad(P2, T, 16, true); const tipIdx = pts.length - 1; quad(T, P1, 16, false);
  let A = 0, cx = 0, cy = 0;
  for (let i = 0; i < pts.length; i++) { const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % pts.length]; const c = x0 * y1 - x1 * y0; A += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c; }
  A /= 2; cx /= 6 * A; cy /= 6 * A; const s = 1 / Math.sqrt(Math.abs(A));
  const out = pts.map(([x, y]) => [(x - cx) * s, (y - cy) * s]);
  return { pts: out, tip: out[tipIdx], tipIdx, top: (-1 - cy) * s, r: s };
})();
// screen polygon of a drop: centre (x,y), scale s (px for unit area), rotation rad, optional wobble
export function dropPts(x, y, s, rot = 0, wob = 0, t = 0, seed = 0, sx = 1, sy = 1) {
  const c = Math.cos(rot), si = Math.sin(rot);
  return DROP.pts.map(([ux, uy], i) => {
    let k = 1;
    if (wob) { const a = Math.atan2(uy, ux); k = 1 + wob * (Math.sin(3 * a + t * 6.3 + seed) * 0.6 + Math.sin(5 * a - t * 4.1 + seed * 2) * 0.4); }
    const px = ux * k * sx, py = uy * k * sy;
    return [x + s * (px * c - py * si), y + s * (px * si + py * c)];
  });
}
export function polyPath(ctx, pts) { ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
// closed polyline draw-on (white outline)
export function strokeOn(ctx, pts, p, o = {}) {
  if (p <= 0) return;
  const closed = pts.concat([pts[0]]);
  F.glowPath(ctx, closed, { p, color: o.color || '#ffffff', width: o.width || 3, glowColor: o.glowColor || '#ffffff' });
}
// spherical destination: from (lat,lon) go dist km at bearing deg
export function dest(lat, lon, km, brg) {
  const d = km / 6371, b = brg * D2R, p1 = lat * D2R, l1 = lon * D2R;
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2));
  return [p2 / D2R, ((l2 / D2R + 540) % 360) - 180];
}
// teardrop on the sphere: tip at (lat,lon) [anchor 'tip'] or centroid [anchor 'c'], area in million km^2, axis bearing (deg, direction tip->body)
export function dropLL(lat, lon, mkm2, brg = 0, anchor = 'tip') {
  const s = Math.sqrt(mkm2 * 1e6), b = brg * D2R;
  const [ax, ay] = anchor === 'tip' ? DROP.tip : [0, 0];
  return DROP.pts.map(([ux, uy]) => {
    const f = -(uy - ay) * s, r = (ux - ax) * s;
    const e = f * Math.sin(b) + r * Math.cos(b), n = f * Math.cos(b) - r * Math.sin(b);
    const dd = Math.hypot(e, n); if (dd < 1e-6) return [lon, lat];
    const [la, lo] = dest(lat, lon, dd, Math.atan2(e, n) / D2R);
    return [lo, la];
  });
}
// paint lon/lat rings into an equirect canvas covering bounds b
export function paintRings(c, b, ringsArr, o = {}) {
  const g = c.getContext('2d'), sx = c.width / (b[2] - b[0]), sy = c.height / (b[3] - b[1]);
  const path = () => { g.beginPath(); for (const r of ringsArr) { r.forEach(([lo, la], i) => i ? g.lineTo((lo - b[0]) * sx, (b[3] - la) * sy) : g.moveTo((lo - b[0]) * sx, (b[3] - la) * sy)); g.closePath(); } };
  g.save();
  if (o.glow) { g.shadowColor = o.glowColor || o.color; g.shadowBlur = o.glow; }
  if (o.color) { g.globalAlpha = o.alpha ?? 0.85; g.fillStyle = o.color; path(); g.fill(o.rule || 'nonzero'); }
  g.restore();
  if (o.stroke) { g.save(); g.globalAlpha = o.strokeAlpha ?? 1; g.strokeStyle = o.stroke; g.lineWidth = o.width || 3; g.lineJoin = 'round'; path(); g.stroke(); g.restore(); }
  return c;
}

// ---------------- globe projection helpers ----------------
export function projRuns(g, pts) { // pts [{lat,lon,h?}] -> visible screen runs
  const runs = []; let cur = [];
  for (const p of pts) { const q = g.project(p.lat, p.lon, p.h || 0); if (q.visible) cur.push([q.x, q.y]); else { if (cur.length > 1) runs.push(cur); cur = []; } }
  if (cur.length > 1) runs.push(cur); return runs;
}
export function trackPts(tracks, name, T0 = 0, T1 = 180) {
  const tr = tracks[name], out = [];
  for (let i = T0; i <= T1; i++) { const a = tr[i]; if (!a || a[0] > 900) continue; out.push({ lat: a[1], lon: a[0] }); }
  return out;
}
export function latCircle(lat, n = 180) { const o = []; for (let i = 0; i <= n; i++) o.push({ lat, lon: -180 + 360 * i / n }); return o; }
// polyline length helpers
export function polyLen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
export function polyAt(pts, f) { // point + tangent at fraction f of length
  const L = polyLen(pts) * clamp(f); let acc = 0;
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (acc + d >= L) { const k = d ? (L - acc) / d : 0; return { x: lerp(pts[i - 1][0], pts[i][0], k), y: lerp(pts[i - 1][1], pts[i][1], k), a: Math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0]) }; } acc += d; }
  const n = pts.length - 1; return { x: pts[n][0], y: pts[n][1], a: n ? Math.atan2(pts[n][1] - pts[n - 1][1], pts[n][0] - pts[n - 1][0]) : 0 };
}
// dotted / sutured "scar" polyline
export function scarLine(ctx, pts, p, o = {}) {
  if (pts.length < 2 || p <= 0) return;
  const col = o.color || PAL.hero;
  F.glowPath(ctx, pts, { p, color: o.core || '#FFE2C8', width: o.width || 4, glowColor: col });
  // sutures: short perpendicular ticks every `step` px along the drawn part
  const L = polyLen(pts) * clamp(p), step = o.step || 26; ctx.save(); ctx.strokeStyle = o.tick || 'rgba(255,240,225,0.85)'; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
  const Ltot = polyLen(pts);
  for (let d = step * 0.5; d < L; d += step) { const q = polyAt(pts, d / Ltot), nx = -Math.sin(q.a), ny = Math.cos(q.a), k = o.tickLen || 9; ctx.beginPath(); ctx.moveTo(q.x - nx * k, q.y - ny * k); ctx.lineTo(q.x + nx * k, q.y + ny * k); ctx.stroke(); }
  ctx.restore();
}

// ---------------- backgrounds ----------------
let STARS = null;
export function stars() {
  if (STARS) return STARS;
  const c = cv(2200, 1300), g = c.getContext('2d'), r = F.rng(4242);
  for (let i = 0; i < 1300; i++) { const b = Math.pow(r(), 5) * 0.9 + 0.08, s = b > 0.6 ? 1.7 : b > 0.3 ? 1.2 : 0.8; g.fillStyle = `rgba(235,240,255,${b})`; g.beginPath(); g.arc(r() * 2200, r() * 1300, s, 0, 7); g.fill(); }
  return (STARS = c);
}
export function spaceBg(ctx, t, o = {}) {
  const gr = ctx.createRadialGradient(W * (o.cx ?? 0.5), H * (o.cy ?? 0.55), 40, W * 0.5, H * 0.55, H * 1.1);
  gr.addColorStop(0, o.c0 || '#122444'); gr.addColorStop(1, o.c1 || '#03050a'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  const s = stars(); ctx.save(); ctx.globalAlpha = o.starAlpha ?? 0.8; ctx.drawImage(s, -60 - (t * (o.sx ?? 6)) % 140, -60 - (t * (o.sy ?? 2)) % 100); ctx.restore();
}
export function deskBg(ctx, t) {
  const gr = ctx.createRadialGradient(W * 0.5, H * 0.45, 80, W * 0.5, H * 0.5, H * 1.15);
  gr.addColorStop(0, '#2a2230'); gr.addColorStop(0.55, '#141019'); gr.addColorStop(1, '#06050a'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  // faint warm light leak drifting
  const lx = W * (0.25 + 0.05 * Math.sin(t * 0.3)), lg = ctx.createRadialGradient(lx, H * 0.2, 10, lx, H * 0.2, 700);
  lg.addColorStop(0, 'rgba(255,170,90,0.10)'); lg.addColorStop(1, 'rgba(255,170,90,0)'); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
}
export function dataBg(ctx, t) {
  ctx.fillStyle = '#081222'; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.strokeStyle = 'rgba(61,227,255,0.06)'; ctx.lineWidth = 1; const off = (t * 8) % 60;
  ctx.beginPath(); for (let x = -60 + off; x < W; x += 60) { ctx.moveTo(x, 0); ctx.lineTo(x, H); } for (let y = -60 + off * 0.5; y < H; y += 60) { ctx.moveTo(0, y); ctx.lineTo(W, y); } ctx.stroke(); ctx.restore();
  const gr = ctx.createRadialGradient(W / 2, H / 2, 200, W / 2, H / 2, H); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.5)'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
}

// ---------------- paper / typewriter ----------------
export const INK = '#2a2420';
export function paper(w, h, seed, o = {}) {
  const pad = 40, c = cv(w + pad * 2, h + pad * 2), g = c.getContext('2d');
  // baked soft shadow (build-time blur only)
  g.save(); g.filter = 'blur(18px)'; g.fillStyle = 'rgba(0,0,0,0.55)'; g.fillRect(pad + 10, pad + 22, w, h); g.restore();
  g.save(); g.translate(pad, pad);
  const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, o.c0 || '#f4ecd9'); gr.addColorStop(1, o.c1 || '#e4d5b4'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  const r = F.rng(seed);
  for (let i = 0; i < w * h / 160; i++) { g.fillStyle = `rgba(95,70,40,${r() * 0.07})`; g.fillRect(r() * w, r() * h, 1 + r() * 2.2, 1 + r() * 2.2); }
  for (let i = 0; i < 40; i++) { g.strokeStyle = `rgba(120,95,60,${0.03 + r() * 0.04})`; g.lineWidth = 1; g.beginPath(); const y = r() * h; g.moveTo(0, y); g.bezierCurveTo(w * 0.3, y + r() * 8 - 4, w * 0.6, y + r() * 8 - 4, w, y + r() * 10 - 5); g.stroke(); }
  const eg = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.max(w, h) * 0.75); eg.addColorStop(0, 'rgba(110,80,40,0)'); eg.addColorStop(1, 'rgba(110,80,40,0.28)'); g.fillStyle = eg; g.fillRect(0, 0, w, h);
  if (o.stain) { // coffee ring
    const [sx, sy, sr] = o.stain; for (let k = 0; k < 3; k++) { g.strokeStyle = `rgba(120,70,25,${0.10 + 0.05 * k})`; g.lineWidth = 10 - k * 3; g.beginPath(); g.ellipse(sx + k * 2, sy - k, sr - k * 4, sr * 0.93 - k * 4, 0.3, 0.2 + k * 0.4, Math.PI * 1.85 + k * 0.2); g.stroke(); }
    g.fillStyle = 'rgba(140,90,40,0.06)'; g.beginPath(); g.ellipse(sx, sy, sr * 0.9, sr * 0.85, 0.3, 0, 7); g.fill();
  }
  g.restore();
  return { c, pad, w, h, g };
}
// greeked typed lines (word bars) — reads as text at a glance, never legible words
export function greek(g, x, y, w, rows, lh, seed, o = {}) {
  const r = F.rng(seed); g.save(); g.fillStyle = o.color || INK;
  for (let i = 0; i < rows; i++) {
    let cx = x + (i === 0 && o.indent ? 40 : 0); const end = x + w * (i === rows - 1 ? 0.45 + r() * 0.3 : 0.93 + r() * 0.07);
    while (cx < end - 20) { const ww = Math.min(end - cx, 18 + r() * 70); g.globalAlpha = (o.alpha ?? 0.5) * (0.75 + r() * 0.35); g.fillRect(cx, y + i * lh - (o.h || 9), ww, o.h || 9); cx += ww + 12 + r() * 6; }
  }
  g.restore();
}
// typewriter string into a canvas context (per-char ink variation)
export function typeStr(g, s, x, y, size, seed, o = {}) {
  const r = F.rng(seed); g.save(); g.font = `${o.weight || 700} ${size}px "JetBrains Mono"`; g.textBaseline = 'alphabetic';
  let cx = x; for (const ch of s) { g.fillStyle = o.color || INK; g.globalAlpha = (o.alpha ?? 1) * (0.72 + r() * 0.28); g.fillText(ch, cx + (r() - 0.5) * 1.2, y + (r() - 0.5) * 1.6); cx += g.measureText(ch).width + (o.track || 0); }
  g.restore(); return cx - x;
}
// draw a pre-rendered paper (with shadow padding) centred at (x,y) with rotation/scale
export function drawPaper(ctx, P, x, y, rot, sc, alpha = 1, extra) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc); ctx.translate(-P.w / 2, -P.h / 2);
  ctx.drawImage(P.c, -P.pad, -P.pad); if (extra) extra(ctx); ctx.restore();
}

// ---------------- icons ----------------
export function arrow(ctx, x0, y0, x1, y1, o = {}) {
  const a = Math.atan2(y1 - y0, x1 - x0), L = Math.hypot(x1 - x0, y1 - y0), hw = o.head || 18, w = o.width || 6;
  if (L < 1) return;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); ctx.translate(x0, y0); ctx.rotate(a); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const body = () => { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.max(0, L - hw * 0.9), 0); ctx.stroke(); ctx.beginPath(); ctx.moveTo(L, 0); ctx.lineTo(L - hw * 1.3, -hw * 0.75); ctx.lineTo(L - hw * 1.3, hw * 0.75); ctx.closePath(); ctx.fill(); };
  if (o.glow !== false) { ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = w + 6; ctx.save(); ctx.translate(1.5, 3); body(); ctx.restore(); }
  ctx.strokeStyle = o.color || '#fff'; ctx.fillStyle = o.color || '#fff'; ctx.lineWidth = w; body();
  ctx.restore();
}
// gold coin seen at spin phase (cos -> width); face icon = teardrop
export function coin(ctx, x, y, r, phase, alpha = 1) {
  const c = Math.cos(phase), w = Math.max(0.035, Math.abs(c));
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y);
  // edge thickness band
  const th = r * 0.13 * Math.sqrt(1 - w * w) + 2; const sgn = c >= 0 ? 1 : -1;
  ctx.fillStyle = '#8a5a12'; ctx.beginPath(); ctx.ellipse(-sgn * th * 0.5, 0, r * w, r, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#b57c1c'; ctx.fillRect(-th * 0.5 - (sgn < 0 ? 0 : 0), -r, th, 2 * r);
  ctx.scale(w, 1);
  const gr = ctx.createLinearGradient(-r, -r, r, r); gr.addColorStop(0, '#fff4b0'); gr.addColorStop(0.45, '#f2c043'); gr.addColorStop(1, '#a8701a');
  ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(sgn * th * 0.5 / Math.max(w, 0.2), 0, r, 0, 7); ctx.fill();
  ctx.translate(sgn * th * 0.5 / Math.max(w, 0.2), 0);
  ctx.strokeStyle = 'rgba(120,75,10,0.85)'; ctx.lineWidth = r * 0.05; ctx.beginPath(); ctx.arc(0, 0, r * 0.84, 0, 7); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,248,210,0.6)'; ctx.lineWidth = r * 0.02; ctx.beginPath(); ctx.arc(0, 0, r * 0.95, 0, 7); ctx.stroke();
  // embossed drip
  const d = dropPts(0, r * 0.02, r * 0.62, c < 0 ? Math.PI : 0);
  ctx.fillStyle = 'rgba(150,95,15,0.9)'; ctx.beginPath(); polyPath(ctx, d.map(([a, b]) => [a + 3, b + 3])); ctx.fill();
  ctx.fillStyle = '#ffe58a'; ctx.beginPath(); polyPath(ctx, d); ctx.fill();
  // specular sweep
  const sp = ctx.createLinearGradient(-r, -r, r, r); const k = (phase * 0.35) % 1; sp.addColorStop(clamp(k - 0.15), 'rgba(255,255,255,0)'); sp.addColorStop(clamp(k), 'rgba(255,255,255,0.45)'); sp.addColorStop(clamp(k + 0.15), 'rgba(255,255,255,0)');
  ctx.fillStyle = sp; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
  ctx.restore();
}
// rubber-stamp canvas (built once): two lines inside a rounded border, grunge holes
export function stampCanvas(top, main, color, seed = 7) {
  const c = cv(1100, 360), g = c.getContext('2d');
  g.strokeStyle = color; g.fillStyle = color; g.lineWidth = 14; F.round(g, 30, 30, 1040, 300, 34); g.stroke();
  g.lineWidth = 4; F.round(g, 52, 52, 996, 256, 22); g.stroke();
  g.textAlign = 'center'; g.font = '700 58px "Barlow Condensed"'; g.fillText(top.split('').join(String.fromCharCode(8202)), 550, 125);
  g.font = '400 150px "Bebas Neue"'; g.fillText(main, 550, 268);
  const r = F.rng(seed); g.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < 900; i++) { g.globalAlpha = 0.3 + r() * 0.7; g.beginPath(); g.arc(r() * 1100, r() * 360, 0.6 + r() * 2.8, 0, 7); g.fill(); }
  for (let i = 0; i < 14; i++) { g.globalAlpha = 0.5; g.fillRect(r() * 1100, r() * 360, 30 + r() * 120, 2 + r() * 3); }
  return c;
}
export function drawStamp(ctx, S, x, y, t, t0, o = {}) {
  if (t < t0) return;
  const p = prog(t, t0, t0 + 0.16, E.in), sc = lerp(2.3, 1, p) * (o.scale || 0.62), a = prog(t, t0, t0 + 0.08);
  ctx.save(); ctx.globalAlpha *= a * (o.alpha ?? 1); ctx.translate(x, y); ctx.rotate((o.rot ?? -0.1) + (1 - p) * 0.12); ctx.scale(sc, sc);
  ctx.drawImage(S, -S.width / 2, -S.height / 2); ctx.restore();
}
// screen shake offset for an impact at t0
export function shake(t, t0, amp = 14, dur = 0.35) { if (t < t0 || t > t0 + dur) return [0, 0]; const k = 1 - (t - t0) / dur; return [Math.sin((t - t0) * 90) * amp * k, Math.cos((t - t0) * 77) * amp * 0.6 * k]; }
// white flash value
export const flash = (t, t0, d = 0.35) => (t < t0 - 0.03 ? 0 : t < t0 ? 1 : Math.max(0, 1 - (t - t0) / d));

// compass rose (built once)
export function compassCanvas(R = 150) {
  const c = cv(R * 2 + 40, R * 2 + 40), g = c.getContext('2d'), o = R + 20;
  g.translate(o, o);
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath(); g.arc(4, 8, R + 6, 0, 7); g.fill();
  const rim = g.createLinearGradient(-R, -R, R, R); rim.addColorStop(0, '#fbe3a0'); rim.addColorStop(0.5, '#c8922e'); rim.addColorStop(1, '#7a5214');
  g.fillStyle = rim; g.beginPath(); g.arc(0, 0, R, 0, 7); g.fill();
  const face = g.createRadialGradient(-R * 0.3, -R * 0.3, 10, 0, 0, R); face.addColorStop(0, '#fbf6ea'); face.addColorStop(1, '#ddd2b8');
  g.fillStyle = face; g.beginPath(); g.arc(0, 0, R * 0.86, 0, 7); g.fill();
  g.strokeStyle = '#3b3326'; for (let i = 0; i < 72; i++) { const a = i * Math.PI / 36, l = i % 18 === 0 ? 0.2 : i % 9 === 0 ? 0.13 : 0.07; g.lineWidth = i % 9 === 0 ? 3 : 1.5; g.beginPath(); g.moveTo(Math.sin(a) * R * 0.84, -Math.cos(a) * R * 0.84); g.lineTo(Math.sin(a) * R * (0.84 - l), -Math.cos(a) * R * (0.84 - l)); g.stroke(); }
  // star points
  for (let i = 0; i < 4; i++) { g.save(); g.rotate(i * Math.PI / 2); g.fillStyle = 'rgba(60,50,35,0.18)'; g.beginPath(); g.moveTo(0, -R * 0.55); g.lineTo(R * 0.09, 0); g.lineTo(-R * 0.09, 0); g.closePath(); g.fill(); g.restore(); }
  g.fillStyle = '#d23a2a'; g.font = `400 ${Math.round(R * 0.3)}px "Bebas Neue"`; g.textAlign = 'center'; g.fillText('N', 0, -R * 0.5);
  return c;
}
export function compassNeedle(ctx, x, y, R, ang, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(ang);
  ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.moveTo(4, -R * 0.66 + 6); ctx.lineTo(R * 0.09 + 4, 6); ctx.lineTo(4, R * 0.66 + 6); ctx.lineTo(-R * 0.09 + 4, 6); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#e8432f'; ctx.beginPath(); ctx.moveTo(0, -R * 0.68); ctx.lineTo(R * 0.1, 0); ctx.lineTo(-R * 0.1, 0); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#eef1f5'; ctx.beginPath(); ctx.moveTo(0, R * 0.68); ctx.lineTo(R * 0.1, 0); ctx.lineTo(-R * 0.1, 0); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(40,30,20,0.6)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(0, -R * 0.68); ctx.lineTo(R * 0.1, 0); ctx.lineTo(0, R * 0.68); ctx.lineTo(-R * 0.1, 0); ctx.closePath(); ctx.stroke();
  ctx.fillStyle = '#c8922e'; ctx.beginPath(); ctx.arc(0, 0, R * 0.07, 0, 7); ctx.fill();
  ctx.restore();
}
// moving truck icon (box truck), facing +x
export function truck(ctx, x, y, ang, s = 1, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); let a = ang; let flip = 1; if (Math.cos(a) < 0) { a += Math.PI; flip = -1; } ctx.rotate(a); ctx.scale(s * flip, s);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(-40, 6, 86, 8);
  ctx.fillStyle = '#f4f6fa'; F.round(ctx, -42, -30, 58, 34, 4); ctx.fill();
  ctx.fillStyle = PAL.hero; ctx.fillRect(-42, -12, 58, 6);
  ctx.fillStyle = '#dfe5ee'; ctx.beginPath(); ctx.moveTo(18, -22); ctx.lineTo(34, -22); ctx.lineTo(44, -8); ctx.lineTo(44, 4); ctx.lineTo(18, 4); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#5a7fa8'; ctx.beginPath(); ctx.moveTo(22, -19); ctx.lineTo(33, -19); ctx.lineTo(40, -9); ctx.lineTo(22, -9); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#1a1f28'; for (const wx of [-28, 30]) { ctx.beginPath(); ctx.arc(wx, 6, 8, 0, 7); ctx.fill(); ctx.fillStyle = '#9aa7b8'; ctx.beginPath(); ctx.arc(wx, 6, 3, 0, 7); ctx.fill(); ctx.fillStyle = '#1a1f28'; }
  ctx.restore();
}
export function shellIcon(ctx, x, y, s, alpha = 1, col = '#ffe7d0') {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.fillStyle = 'rgba(255,190,150,0.35)'; ctx.lineWidth = 3; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(-26, 4); ctx.quadraticCurveTo(-24, -26, 0, -28); ctx.quadraticCurveTo(24, -26, 26, 4); ctx.lineTo(8, 14); ctx.lineTo(-8, 14); ctx.closePath(); ctx.fill(); ctx.stroke();
  for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(i * 3, 12); ctx.lineTo(i * 11, -22 + Math.abs(i) * 4); ctx.stroke(); }
  ctx.fillStyle = col; ctx.fillRect(-9, 12, 18, 7); ctx.restore();
}
export function coralIcon(ctx, x, y, s, alpha = 1, col = '#ff8f7a') {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.lineWidth = 5; ctx.lineCap = 'round';
  const br = (x0, y0, a, l, d) => { if (d === 0) return; const x1 = x0 + Math.sin(a) * l, y1 = y0 - Math.cos(a) * l; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); br(x1, y1, a - 0.5, l * 0.72, d - 1); br(x1, y1, a + 0.45, l * 0.7, d - 1); };
  br(0, 20, 0, 18, 3); ctx.restore();
}
export function googly(ctx, x, y, r, t, seed = 0) {
  ctx.save(); ctx.fillStyle = '#fff'; ctx.strokeStyle = '#111'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.stroke();
  const a = Math.sin(t * 9 + seed) * 1.2 + seed, k = r * 0.38; ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(x + Math.cos(a) * k * 0.6, y + Math.abs(Math.sin(a)) * k * 0.8 + r * 0.12, r * 0.5, 0, 7); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x + Math.cos(a) * k * 0.6 - r * 0.15, y + Math.abs(Math.sin(a)) * k * 0.8 - r * 0.05, r * 0.12, 0, 7); ctx.fill(); ctx.restore();
}
// analog clock icon
export function clockIcon(ctx, x, y, r, hAng, mAng, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y);
  ctx.fillStyle = '#f4f6fa'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill(); ctx.strokeStyle = PAL.hero; ctx.lineWidth = r * 0.12; ctx.stroke();
  ctx.strokeStyle = '#1a1f28'; for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; ctx.lineWidth = i % 3 ? 2 : 4; ctx.beginPath(); ctx.moveTo(Math.sin(a) * r * 0.78, -Math.cos(a) * r * 0.78); ctx.lineTo(Math.sin(a) * r * 0.66, -Math.cos(a) * r * 0.66); ctx.stroke(); }
  ctx.lineCap = 'round'; ctx.lineWidth = r * 0.09; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(hAng) * r * 0.45, -Math.cos(hAng) * r * 0.45); ctx.stroke();
  ctx.lineWidth = r * 0.06; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(mAng) * r * 0.66, -Math.cos(mAng) * r * 0.66); ctx.stroke();
  ctx.fillStyle = PAL.hero; ctx.beginPath(); ctx.arc(0, 0, r * 0.07, 0, 7); ctx.fill();
  // bells
  for (const s of [-1, 1]) { ctx.fillStyle = PAL.hero; ctx.beginPath(); ctx.arc(s * r * 0.62, -r * 0.92, r * 0.28, Math.PI, 0); ctx.fill(); }
  ctx.restore();
}

// ---------------- lithospheric drip shape (shared by the Nevada blob and the honey) ----------------
// half-width profile along depth y in [0, L] (units arbitrary), returns polygon centred on x=0, top at y=0
export function dripPoly(L, o = {}) {
  const top = o.top ?? 46, neck = o.neck ?? 14, bulb = o.bulb ?? 30, n = 60, wob = o.wob || 0, t = o.t || 0;
  const hw = (y) => {
    const f = top * (1 - smooth(0, Math.min(55, L * 0.45 + 8), y)) + neck * smooth(0, 12, y);
    const bc = L - bulb, bb = y > bc - bulb ? Math.sqrt(Math.max(0, bulb * bulb - (y - bc) * (y - bc))) : 0;
    const neckW = L < 3 * bulb ? lerp(bulb, neck, smooth(0, 3 * bulb, L)) : neck;
    return Math.max(f, y < L - bulb * 0.2 ? neckW * smooth(0, 6, y) : 0, bb);
  };
  const L2 = [], R2 = [];
  for (let i = 0; i <= n; i++) { const y = L * i / n, w = hw(y), dx = wob * Math.sin(y * 0.03 + t * 1.3) * smooth(0, 60, y); L2.push([-w + dx, y]); R2.push([w + dx, y]); }
  return L2.concat(R2.reverse());
}
