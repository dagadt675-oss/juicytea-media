// GeoJSON helpers: highlight fills into equirectangular overlay canvases (for the globe shader)
// and crisp projected outlines/paths drawn on the 2D compositor every frame.
import { PAL, clamp } from './fx.js';
const cache = {};
export async function loadGeo(name) {
  if (!cache[name]) cache[name] = fetch(`geo/${name}.geojson`).then(r => r.json());
  return cache[name];
}
export function findFeature(fc, key) {
  const k = key.toLowerCase();
  return fc.features.find(f => {
    const p = f.properties;
    return [p.ADMIN, p.NAME, p.NAME_LONG, p.ISO_A3, p.ADM0_A3, p.SOVEREIGNT, p.name].filter(Boolean).some(v => String(v).toLowerCase() === k);
  });
}
export function rings(feature) {
  const g = feature.geometry || feature;
  if (g.type === 'Polygon') return g.coordinates;
  if (g.type === 'MultiPolygon') return g.coordinates.flat();
  if (g.type === 'LineString') return [g.coordinates];
  if (g.type === 'MultiLineString') return g.coordinates;
  return [];
}
// fill features into an equirectangular canvas covering bounds b=[lon0,lat0,lon1,lat1]
export function fillEquirect(cv, b, features, o = {}) {
  const g = cv.getContext('2d');
  const sx = cv.width / (b[2] - b[0]), sy = cv.height / (b[3] - b[1]);
  const X = lon => (lon - b[0]) * sx, Y = lat => (b[3] - lat) * sy;
  const pathAll = () => {
    g.beginPath();
    for (const f of features) for (const r of rings(f)) {
      r.forEach(([lon, lat], i) => i ? g.lineTo(X(lon), Y(lat)) : g.moveTo(X(lon), Y(lat)));
      g.closePath();
    }
  };
  g.save();
  if (o.glow) { g.shadowColor = o.glowColor || o.color || PAL.hero; g.shadowBlur = o.glow; }
  g.fillStyle = o.color || PAL.hero; g.globalAlpha = o.alpha ?? 0.85;
  pathAll(); g.fill('evenodd');
  g.restore();
  if (o.stroke) { g.save(); g.strokeStyle = o.stroke; g.lineWidth = o.strokeWidth || 2; pathAll(); g.stroke(); g.restore(); }
  return cv;
}
export function makeCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// project rings with the globe and stroke the visible runs; p = draw-on fraction (0..1) along total length
export function strokeProjected(ctx, globe, ringsArr, o = {}) {
  const runs = [];
  for (const r of ringsArr) {
    let cur = [];
    let lx = null, ly = null;
    for (const [lon, lat] of r) {
      const q = globe.project(lat, lon, o.h || 0);
      if (!q.visible) { if (cur.length > 1) runs.push(cur); cur = []; lx = null; continue; }
      if (lx !== null && Math.hypot(q.x - lx, q.y - ly) < (o.minStep ?? 1.2)) continue;
      cur.push([q.x, q.y]); lx = q.x; ly = q.y;
    }
    if (cur.length > 1) runs.push(cur);
  }
  const p = o.p ?? 1;
  let total = 0; const lens = runs.map(run => { let L = 0; for (let i = 1; i < run.length; i++) L += Math.hypot(run[i][0] - run[i - 1][0], run[i][1] - run[i - 1][1]); total += L; return L; });
  let budget = total * clamp(p);
  ctx.save();
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.globalAlpha *= (o.alpha ?? 1);
  const draw = (lw, col, blur) => {
    ctx.strokeStyle = col; ctx.lineWidth = lw;
    if (o.dash) ctx.setLineDash(o.dash);
    let bud = budget;
    ctx.beginPath();
    runs.forEach((run, ri) => {
      if (bud <= 0) return;
      ctx.moveTo(run[0][0], run[0][1]);
      for (let i = 1; i < run.length; i++) {
        const d = Math.hypot(run[i][0] - run[i - 1][0], run[i][1] - run[i - 1][1]);
        if (d > bud) { const k = bud / d; ctx.lineTo(run[i - 1][0] + (run[i][0] - run[i - 1][0]) * k, run[i - 1][1] + (run[i][1] - run[i - 1][1]) * k); bud = 0; break; }
        ctx.lineTo(run[i][0], run[i][1]); bud -= d;
      }
    });
    ctx.stroke();
  };
  if (o.glow === true) { draw((o.width || 2.5) * 6, (o.glowColor || o.color || '#ffffff') + '12', 0); draw((o.width || 2.5) * 3, (o.glowColor || o.color || '#ffffff') + '30', 0); }
  draw(o.width || 2.5, o.color || '#ffffff', 0);
  ctx.restore();
}
// great-circle polyline between two lat/lon points with optional arc height (Earth radii)
export function gcLine(a, b, n = 96, lift = 0) {
  const D = Math.PI / 180;
  const v = (lat, lon) => [Math.cos(lat * D) * Math.cos(lon * D), Math.sin(lat * D), -Math.cos(lat * D) * Math.sin(lon * D)];
  const A = v(...a), B = v(...b);
  const dot = clamp(A[0] * B[0] + A[1] * B[1] + A[2] * B[2], -1, 1), om = Math.acos(dot), s = Math.sin(om) || 1;
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, k1 = Math.sin((1 - t) * om) / s, k2 = Math.sin(t * om) / s;
    const P = [A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2, A[2] * k1 + B[2] * k2];
    const L = Math.hypot(...P); const lat = Math.asin(P[1] / L) / D, lon = Math.atan2(-P[2], P[0]) / D;
    out.push({ lat, lon, h: lift * Math.sin(Math.PI * t) });
  }
  return out;
}
export function projectPath(globe, pts) {
  const out = []; for (const p of pts) { const q = globe.project(p.lat, p.lon, p.h || 0); if (q.visible) out.push([q.x, q.y]); else if (out.length) break; }
  return out;
}

// --- true-size moves: rotate rings on the sphere so that point `from` lands on `to` (shape/area preserved) ---
const D2R_ = Math.PI / 180;
function v3(lat, lon) { const a = lat * D2R_, b = lon * D2R_; return [Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)]; }
function ll3(p) { const L = Math.hypot(p[0], p[1], p[2]); return [Math.atan2(-p[2], p[0]) / D2R_, Math.asin(p[1] / L) / D2R_]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function dot3(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
// Rodrigues rotation of p about unit axis k by angle th
function rot(p, k, th) { const c = Math.cos(th), s = Math.sin(th), kx = cross(k, p), kd = dot3(k, p); return [p[0] * c + kx[0] * s + k[0] * kd * (1 - c), p[1] * c + kx[1] * s + k[1] * kd * (1 - c), p[2] * c + kx[2] * s + k[2] * kd * (1 - c)]; }
// returns rings (lon,lat) moved by fraction t of the rotation from->to; optional extra spin (deg) about the destination normal
export function moveRings(ringsArr, from, to, t = 1, spinDeg = 0) {
  const A = v3(from[0], from[1]), B = v3(to[0], to[1]);
  let k = cross(A, B); const s = Math.hypot(...k); const th = Math.atan2(s, dot3(A, B)) * t;
  k = s < 1e-9 ? [0, 1, 0] : k.map(x => x / s);
  const mid = rot(A, k, th);
  return ringsArr.map(r => r.map(([lon, lat]) => { let p = rot(v3(lat, lon), k, th); if (spinDeg) p = rot(p, mid, spinDeg * D2R_ * t); return ll3(p); }));
}
// area-weighted-ish centroid (mean of unit vectors of all vertices of the largest ring)
export function centroid(ringsArr) {
  let best = ringsArr[0]; for (const r of ringsArr) if (r.length > best.length) best = r;
  let x = 0, y = 0, z = 0; for (const [lon, lat] of best) { const p = v3(lat, lon); x += p[0]; y += p[1]; z += p[2]; }
  const q = ll3([x, y, z]); return [q[1], q[0]];
}
// fill projected rings on the 2D canvas (for moved outlines that are not in the overlay texture)
export function fillProjected(ctx, globe, ringsArr, o = {}) {
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.fillStyle = o.color || PAL.hero;
  ctx.beginPath();
  for (const r of ringsArr) {
    let started = false;
    for (const [lon, lat] of r) { const q = globe.project(lat, lon); if (!started) { ctx.moveTo(q.x, q.y); started = true; } else ctx.lineTo(q.x, q.y); }
    ctx.closePath();
  }
  ctx.fill('evenodd'); ctx.restore();
}

// --- point data layers on equirectangular overlay canvases ---
// points: [[lon, lat, weight?], ...]; draws soft additive blobs (heat-map look) or crisp dots
export function pointsEquirect(cv, b, points, o = {}) {
  const g = cv.getContext('2d');
  const sx = cv.width / (b[2] - b[0]), sy = cv.height / (b[3] - b[1]);
  const r = o.radius || 4, col = o.color || '#FF5A36';
  g.save();
  g.globalCompositeOperation = o.blend || 'lighter';
  if (o.soft !== false) {
    // pre-rendered soft sprite
    const s = document.createElement('canvas'); s.width = s.height = Math.ceil(r * 4); const sg = s.getContext('2d');
    const gr = sg.createRadialGradient(r * 2, r * 2, 0, r * 2, r * 2, r * 2); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)');
    sg.fillStyle = gr; sg.fillRect(0, 0, s.width, s.height);
    for (const p of points) { g.globalAlpha = (o.alpha ?? 0.5) * (p[2] ?? 1); g.drawImage(s, (p[0] - b[0]) * sx - r * 2, (b[3] - p[1]) * sy - r * 2); }
  } else {
    g.fillStyle = col;
    for (const p of points) { g.globalAlpha = (o.alpha ?? 0.9) * (p[2] ?? 1); g.beginPath(); g.arc((p[0] - b[0]) * sx, (b[3] - p[1]) * sy, r * (p[3] ?? 1), 0, Math.PI * 2); g.fill(); }
  }
  g.restore();
  return cv;
}
// polylines (e.g. storm tracks, plate boundaries) into an overlay canvas
export function linesEquirect(cv, b, lines, o = {}) {
  const g = cv.getContext('2d');
  const sx = cv.width / (b[2] - b[0]), sy = cv.height / (b[3] - b[1]);
  g.save(); g.strokeStyle = o.color || '#3DE3FF'; g.lineWidth = o.width || 2; g.globalAlpha = o.alpha ?? 0.8; g.lineJoin = 'round'; g.lineCap = 'round';
  g.globalCompositeOperation = o.blend || 'source-over';
  for (const L of lines) {
    g.beginPath(); let prev = null;
    for (const [lon, lat] of L) { const x = (lon - b[0]) * sx, y = (b[3] - lat) * sy; if (prev && Math.abs(lon - prev) > 180) g.moveTo(x, y); else if (prev === null) g.moveTo(x, y); else g.lineTo(x, y); prev = lon; }
    g.stroke();
  }
  g.restore(); return cv;
}
