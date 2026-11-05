// ch5a helpers: smooth paleo-globe renderer (rigid-plate rotations derived from paleo/tracks.json point pairs),
// small spherical-geometry utilities and a local Equal Earth forward projection (lib/equalearth.js throws on import:
// it contains a stray `np.float64(...)`, so it cannot be imported).
import * as F from '../../lib/fx.js';
import { RINGS, EXCL, ANT } from './ch5a_data.js';

const D = Math.PI / 180;
export const v3 = (lat, lon) => [Math.cos(lat * D) * Math.cos(lon * D), Math.sin(lat * D), -Math.cos(lat * D) * Math.sin(lon * D)];
export const ll = (p) => { const L = Math.hypot(p[0], p[1], p[2]); return [Math.asin(p[1] / L) / D, Math.atan2(-p[2], p[0]) / D]; }; // [lat, lon]
export const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const norm = (a) => { const L = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / L, a[1] / L, a[2] / L]; };
export const angDeg = (a, b) => Math.acos(F.clamp(dot(v3(a[0], a[1]), v3(b[0], b[1])), -1, 1)) / D;
// 3x3 matrices as flat arrays (row-major)
const frame = (p1, p2) => { const e1 = norm(p1), e2 = norm(cross(p1, p2)), e3 = cross(e1, e2); return [e1, e2, e3]; };
function rotFromFrames(E, Fm) { // R = F * E^T  where columns of E/F are the frame vectors
  const R = new Array(9).fill(0);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { let s = 0; for (let k = 0; k < 3; k++) s += Fm[k][i] * E[k][j]; R[i * 3 + j] = s; }
  return R;
}
export const apply = (R, p) => [R[0] * p[0] + R[1] * p[1] + R[2] * p[2], R[3] * p[0] + R[4] * p[1] + R[5] * p[2], R[6] * p[0] + R[7] * p[1] + R[8] * p[2]];
export const applyT = (R, p) => [R[0] * p[0] + R[3] * p[1] + R[6] * p[2], R[1] * p[0] + R[4] * p[1] + R[7] * p[2], R[2] * p[0] + R[5] * p[1] + R[8] * p[2]];
export const mul = (A, B) => { const C = new Array(9); for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i * 3 + j] = A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j]; return C; };
// rotation about unit axis k by angle th (radians)
export function axisRot(k, th) {
  const [x, y, z] = k, c = Math.cos(th), s = Math.sin(th), t = 1 - c;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}

export const PAIRS = { africa: ['africa_c', 'cape_agulhas'], samerica: ['samerica_c', 'cape_horn'], india: ['india_c', 'kanyakumari'], australia: ['australia_c', 'tasmania_s'], antarctica: ['antarctica_c', 'south_pole'] };
export const TRACKED = ['samerica', 'africa', 'india', 'australia'];

export class Paleo {
  // w x h equirect overlay canvas. Base land (everything except the tracked plates and Antarctica) is cached per integer Ma;
  // Antarctica (coast_TTT polygons) and the tracked plates (present-day rings rotated continuously) are redrawn on change.
  constructor(api, tracks, w = 2048, h = 1024) {
    this.api = api; this.tracks = tracks; this.w = w; this.h = h; this.sc = w / 2048;
    this.cv = document.createElement('canvas'); this.cv.width = w; this.cv.height = h; this.g = this.cv.getContext('2d');
    this.base = document.createElement('canvas'); this.base.width = w; this.base.height = h; this.bg = this.base.getContext('2d');
    this.baseKey = null; this.sig = null;
    this.E = {}; for (const c in PAIRS) { const [a, b] = PAIRS[c]; this.E[c] = frame(this.pt(a, 0), this.pt(b, 0)); }
    const step = w <= 2048 ? 2 : 1; // ring decimation for whole-globe canvases (invisible at that scale, halves path cost)
    this.R0 = {}; for (const c of TRACKED) this.R0[c] = RINGS[c].map(r => r.filter((_, i) => i % step === 0 || i === r.length - 1).map(([lo, la]) => v3(la, lo)));
    this.main = {}; for (const c of TRACKED) { let bi = 0; this.R0[c].forEach((r, i) => { if (r.length > this.R0[c][bi].length) bi = i; }); this.main[c] = bi; }
  }
  async load(T) { return this.api.loadJSON(`paleo/coast_${String(T).padStart(3, '0')}.json`); }
  async preload(list) { for (const T of list) await this.load(T); }
  at(name, T) {
    const tr = this.tracks[name]; T = F.clamp(T, 0, 200);
    const i = Math.min(199, Math.floor(T)), f = T - i, a = tr[i], b = tr[i + 1];
    let dl = b[0] - a[0]; if (dl > 180) dl -= 360; if (dl < -180) dl += 360;
    return [a[1] + (b[1] - a[1]) * f, a[0] + dl * f];
  }
  pt(name, T) { const [la, lo] = this.at(name, T); return v3(la, lo); }
  rot(c, T) { const [a, b] = PAIRS[c]; return rotFromFrames(this.E[c], frame(this.pt(a, T), this.pt(b, T))); }
  movePt(c, lat, lon, T) { return ll(apply(this.rot(c, T), v3(lat, lon))); }
  explodeRot(c, T, center, deg) {
    if (!deg) return null;
    const m = this.pt(PAIRS[c][0], T); const k = cross(center, m); const L = Math.hypot(...k); if (L < 1e-6) return null;
    return axisRot([k[0] / L, k[1] / L, k[2] / L], deg * D);
  }
  plateRot(c, T, o = {}) {
    let R = this.rot(c, T);
    const X = o.explode && o.explode[c] ? this.explodeRot(c, T, o.center, o.explode[c]) : null; if (X) R = mul(X, R);
    if (o.spin && o.spin[c]) { R = mul(axisRot(norm(apply(R, v3(...this.cen0(c)))), o.spin[c] * D), R); }
    return R;
  }
  cen0(c) { const [lo, la] = this.tracks[PAIRS[c][0]][0]; return [la, lo]; }
  async drawBase(Ti, ant = 0, shelf = 0) {
    const key = Ti + '|' + ant.toFixed(2) + '|' + shelf;
    if (this.baseKey === key) return;
    this.baseKey = key;
    const polys = await this.load(Ti), g = this.bg, W = this.w, H = this.h;
    const X = lo => (lo + 180) / 360 * W, Y = la => (90 - la) / 180 * H;
    g.clearRect(0, 0, W, H);
    const ex = new Set(EXCL[Ti]), an = new Set(ANT[Ti]);
    // polygons lying wholly south of 58°S are Antarctic blocks (e.g. West Antarctica): they join the Antarctica layer
    this.antX = this.antX || {};
    this.antX[Ti] = polys.map((r, j) => (!ex.has(j) && !an.has(j) && r.every(q => q[1] < -58)) ? j : -1).filter(j => j >= 0);
    const ax = new Set(this.antX[Ti]);
    g.fillStyle = SAND; g.beginPath();
    polys.forEach((r, j) => { if (ex.has(j) || an.has(j) || ax.has(j)) return; r.forEach(([lo, la], i) => i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))); g.closePath(); });
    g.fill('nonzero');
    // Antarctica (coast_TTT polygons + Antarctic blocks)
    g.fillStyle = mix(SAND, ANTC, ant); g.beginPath();
    for (const j of [...ANT[Ti], ...this.antX[Ti]]) { const r = polys[j]; r.forEach(([lo, la], i) => i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))); g.closePath(); }
    if (shelf) { g.save(); g.strokeStyle = g.fillStyle; g.lineWidth = shelf * this.sc; g.lineJoin = 'round'; g.stroke(); g.restore(); } // continental shelf: closes coastline-fit gaps
    g.fill('nonzero');
  }
  // o: {hl:{c:0..1}, ant:0..1, antGlow, explode:{c:deg}, spin:{c:deg}, center:[x,y,z], key, under(g,X,Y,P), over(g,X,Y,P), baseAlpha}
  async draw(T, o = {}) {
    T = F.clamp(T, 0, 200);
    const Ti = Math.round(T);
    const hl = o.hl || {};
    const sig = [T.toFixed(3), (Math.round((o.ant || 0) * 50) / 50).toFixed(2), (o.baseAlpha ?? 1).toFixed(2), String(o.shelf || 0), ...TRACKED.map(c => (hl[c] || 0).toFixed(2) + ':' + ((o.explode && o.explode[c]) || 0).toFixed(3) + ':' + ((o.spin && o.spin[c]) || 0).toFixed(2)), o.key || ''].join('|');
    if (sig === this.sig) return false;
    this.sig = sig;
    const antQ = Math.round((o.ant || 0) * 50) / 50;
    await this.load(Ti); await this.drawBase(Ti, antQ, o.shelf || 0);
    const g = this.g, W = this.w, H = this.h, sc = this.sc;
    const X = lo => (lo + 180) / 360 * W, Y = la => (90 - la) / 180 * H;
    g.clearRect(0, 0, W, H);
    if (o.under) o.under(g, X, Y, this);
    g.save(); g.globalAlpha = o.baseAlpha ?? 1; g.drawImage(this.base, 0, 0); g.restore();
    // tracked plates: rotate present-day rings continuously
    for (const c of TRACKED) {
      const R = this.plateRot(c, T, o);
      g.fillStyle = mix(SAND, HERO, hl[c] || 0);
      g.beginPath();
      for (const ring of this.R0[c]) {
        const pts = []; let prev = null, off = 0, mn = 1e9, mx = -1e9;
        for (const p of ring) {
          const q = apply(R, p); let lo = Math.atan2(-q[2], q[0]) / D; const la = Math.asin(F.clamp(q[1], -1, 1)) / D;
          if (prev !== null) { const d = lo + off - prev; if (d > 180) off -= 360; else if (d < -180) off += 360; }
          lo += off; prev = lo; pts.push(lo, la); if (lo < mn) mn = lo; if (lo > mx) mx = lo;
        }
        for (const sh of [0, mn < -180 ? 360 : null, mx > 180 ? -360 : null]) {
          if (sh === null) continue;
          for (let i = 0; i < pts.length; i += 2) { const x = X(pts[i] + sh), y = Y(pts[i + 1]); i ? g.lineTo(x, y) : g.moveTo(x, y); }
          g.closePath();
        }
      }
      // outline drawn UNDER the fill (double width) so only the outer edge shows, not the internal plate seams
      if ((hl[c] || 0) > 0.01) { g.save(); g.globalAlpha = Math.min(1, hl[c]); g.strokeStyle = 'rgba(255,244,232,0.95)'; g.lineWidth = (5.2 + (o.shelf || 0)) * sc; g.lineJoin = 'round'; g.stroke(); g.restore(); }
      if (o.shelf) { g.save(); g.strokeStyle = g.fillStyle; g.lineWidth = o.shelf * sc; g.lineJoin = 'round'; g.stroke(); g.restore(); }
      g.fill('nonzero');
    }
    if (o.over) o.over(g, X, Y, this);
    return true;
  }
}
export const SAND = '#C2AE84', HERO = '#FF5A36', ANTC = '#FFE07A';
const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
export function mix(a, b, k) { const A = hex(a), B = hex(b); k = F.clamp(k); return `rgb(${Math.round(A[0] + (B[0] - A[0]) * k)},${Math.round(A[1] + (B[1] - A[1]) * k)},${Math.round(A[2] + (B[2] - A[2]) * k)})`; }

// ---- spherical helpers for 2D drawing over the globe ----
// small circle of angular radius rDeg around [lat, lon] -> array of [lat, lon]
export function circleLL(lat, lon, rDeg, n = 72) {
  const c = v3(lat, lon); let a = cross(c, [0, 1, 0]); if (Math.hypot(...a) < 1e-6) a = [1, 0, 0]; a = norm(a); const b = cross(c, a);
  const out = []; const cr = Math.cos(rDeg * D), sr = Math.sin(rDeg * D);
  for (let i = 0; i <= n; i++) { const t = i / n * Math.PI * 2; const p = [c[0] * cr + (a[0] * Math.cos(t) + b[0] * Math.sin(t)) * sr, c[1] * cr + (a[1] * Math.cos(t) + b[1] * Math.sin(t)) * sr, c[2] * cr + (a[2] * Math.cos(t) + b[2] * Math.sin(t)) * sr]; out.push(ll(p)); }
  return out;
}
// great-circle samples from A to B ([lat,lon]) -> [[lat,lon]]; frac0..frac1 portion
export function gcLL(A, B, n = 48, f0 = 0, f1 = 1) {
  const a = v3(A[0], A[1]), b = v3(B[0], B[1]); const om = Math.acos(F.clamp(dot(a, b), -1, 1)); const s = Math.sin(om) || 1;
  const out = []; for (let i = 0; i <= n; i++) { const t = f0 + (f1 - f0) * i / n; const k1 = Math.sin((1 - t) * om) / s, k2 = Math.sin(t * om) / s; out.push(ll([a[0] * k1 + b[0] * k2, a[1] * k1 + b[1] * k2, a[2] * k1 + b[2] * k2])); }
  return out;
}
// project [[lat,lon]] with the globe: returns runs of visible screen points
export function projRuns(g, pts, h = 0) {
  const runs = []; let cur = [];
  for (const [la, lo] of pts) { const q = g.project(la, lo, h); if (q.visible) cur.push([q.x, q.y]); else if (cur.length) { runs.push(cur); cur = []; } }
  if (cur.length) runs.push(cur); return runs;
}
export function strokeRuns(ctx, runs, o = {}) {
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha *= (o.alpha ?? 1);
  const pass = (lw, col) => { ctx.strokeStyle = col; ctx.lineWidth = lw; if (o.dash) { ctx.setLineDash(o.dash); ctx.lineDashOffset = o.dashOffset || 0; } ctx.beginPath(); for (const r of runs) { r.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); } ctx.stroke(); };
  if (o.glow) { pass((o.width || 3) * 5, o.glowColor || 'rgba(255,210,63,0.10)'); pass((o.width || 3) * 2.4, o.glowColor2 || 'rgba(255,210,63,0.25)'); }
  if (o.under) pass((o.width || 3) + 4, o.under);
  pass(o.width || 3, o.color || '#fff');
  ctx.restore();
}
// droplet-shaped arrow head at (x,y) pointing along angle ang
export function droplet(ctx, x, y, ang, r, color = '#fff', alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(ang - Math.PI / 2);
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.moveTo(0, r * 2.2); ctx.bezierCurveTo(r * 1.35, r * 0.6, r * 1.25, -r * 0.35, 0, -r * 1.25); ctx.bezierCurveTo(-r * 1.25, -r * 0.35, -r * 1.35, r * 0.6, 0, r * 2.2); ctx.fill();
  ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(0, r * 1.9); ctx.bezierCurveTo(r * 1.1, r * 0.6, r, -r * 0.2, 0, -r); ctx.bezierCurveTo(-r, -r * 0.2, -r * 1.1, r * 0.6, 0, r * 1.9); ctx.fill();
  ctx.restore();
}

// ---- Equal Earth forward projection (matches tex/equal_earth.jpg, 3600x1760) ----
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2, S = 651.7329707517487, CX = 1800, CY = 880;
export const EE_W = 3600, EE_H = 1760;
export function ee(lon, lat) {
  const l = lon * D, p = lat * D, th = Math.asin(M * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [CX + x * S, CY - y * S];
}
export function eeScreen(lon, lat, view, W, H) { const [x, y] = ee(lon, lat); const z = view.zoom * Math.min(W / EE_W, H / EE_H); return [W / 2 + (x - view.cx) * z, H / 2 + (y - view.cy) * z]; }
export function drawEE(ctx, img, view, W, H) { const z = view.zoom * Math.min(W / EE_W, H / EE_H); ctx.drawImage(img, W / 2 - view.cx * z, H / 2 - view.cy * z, EE_W * z, EE_H * z); }
