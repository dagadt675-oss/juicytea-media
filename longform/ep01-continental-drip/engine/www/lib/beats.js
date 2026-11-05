// Higher-level beat helpers shared by chapter modules (episode-agnostic where possible).
import * as F from './fx.js';
import { loadGeo, findFeature, rings, makeCanvas, fillEquirect } from './geo.js';
const { PAL, prog, E, clamp, lerp } = F;

// ---- named regions -> arrays of GeoJSON features ----
// continents (union of Natural Earth countries by CONTINENT), countries by name, and tip regions (admin-1)
export async function region(name) {
  const C = await loadGeo('ne_50m_admin_0_countries');
  const conts = { 'south america': 'South America', 'africa': 'Africa', 'north america': 'North America', 'europe': 'Europe', 'asia': 'Asia', 'oceania': 'Oceania', 'antarctica': 'Antarctica' };
  const k = name.toLowerCase();
  if (conts[k]) return C.features.filter(f => f.properties.CONTINENT === conts[k]);
  if (k === 'australia') return [findFeature(C, 'Australia')];
  if (k === 'korea') return [findFeature(C, 'South Korea'), findFeature(C, 'North Korea')].filter(Boolean);
  if (['florida', 'baja', 'kamchatka'].includes(k)) {
    const T = await loadGeo('tips_admin1');
    const want = { florida: ['Florida'], baja: ['Baja California', 'Baja California Sur'], kamchatka: ['Kamchatka'] }[k];
    return T.features.filter(f => want.includes(f.properties.name) && f.properties.admin !== 'Uruguay');
  }
  if (k === 'arctic ocean') { const A = await loadGeo('arctic_ocean'); return A.features; }
  const f = findFeature(C, name); return f ? [f] : [];
}
export function allRings(features) { return features.flatMap(f => rings(f)); }

// ---- a world overlay canvas you can paint regions into progressively ----
export class WorldOverlay {
  constructor(w = 4096, h = 2048) { this.cv = makeCanvas(w, h); this.g = this.cv.getContext('2d'); this.b = [-180, -90, 180, 90]; this.layers = []; this.sig = ''; }
  // layers: [{features, color, alpha, glow}] ; redraw only when the visible set changes (signature)
  set(layers, globe) {
    const sig = layers.map(l => l.key + ':' + (l.alpha ?? 1).toFixed(2)).join('|');
    if (sig === this.sig) return false;
    this.sig = sig; this.g.clearRect(0, 0, this.cv.width, this.cv.height);
    for (const l of layers) fillEquirect(this.cv, this.b, l.features, { color: l.color || PAL.hero, alpha: l.alpha ?? 0.85, glow: l.glow ?? 18 });
    if (globe) { if (globe.u.ovTex.value?.image !== this.cv) globe.setOverlay(this.cv, this.b); else globe.refreshOverlay(); }
    return true;
  }
}

// ---- hemisphere cap mask (center lat/lon) painted into an equirect canvas ----
export function hemisphereCanvas(cLat, cLon, color = PAL.cyan, alpha = 0.35, w = 2048, h = 1024) {
  const cv = makeCanvas(w, h); const g = cv.getContext('2d'); const id = g.createImageData(w, h);
  const D = Math.PI / 180, cl = cLat * D, co = cLon * D;
  const [r, gg, b] = [parseInt(color.slice(1, 3), 16), parseInt(color.slice(3, 5), 16), parseInt(color.slice(5, 7), 16)];
  for (let y = 0; y < h; y++) {
    const la = (90 - (y + 0.5) / h * 180) * D;
    for (let x = 0; x < w; x++) {
      const lo = (-180 + (x + 0.5) / w * 360) * D;
      const c = Math.sin(la) * Math.sin(cl) + Math.cos(la) * Math.cos(cl) * Math.cos(lo - co);
      const a = c > 0 ? alpha : 0; const edge = Math.abs(c) < 0.01 ? 1 : 0;
      const i = (y * w + x) * 4; id.data[i] = edge ? 255 : r; id.data[i + 1] = edge ? 255 : gg; id.data[i + 2] = edge ? 255 : b; id.data[i + 3] = Math.round((edge ? 0.9 : a) * 255);
    }
  }
  g.putImageData(id, 0, 0); return cv;
}

// ---- dripping arrow from a screen point toward screen-down (or along a direction), with a droplet head ----
export function dripArrow(ctx, x, y, p, o = {}) {
  if (p <= 0) return;
  const len = (o.len || 120) * E.outBack(clamp(p)), ang = o.angle ?? Math.PI / 2;
  const x1 = x + Math.cos(ang) * len, y1 = y + Math.sin(ang) * len;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.lineCap = 'round';
  for (const [lw, col] of [[o.width ? o.width + 6 : 10, 'rgba(0,0,0,0.45)'], [o.width || 4, o.color || '#ffffff']]) {
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x1, y1); ctx.stroke();
  }
  // droplet head
  const r = (o.head || 11) * clamp(p * 1.4);
  ctx.translate(x1, y1); ctx.rotate(ang - Math.PI / 2);
  ctx.fillStyle = o.color || '#ffffff';
  ctx.beginPath(); ctx.moveTo(0, r * 1.9); ctx.bezierCurveTo(r * 1.1, r * 0.6, r, -r * 0.2, 0, -r); ctx.bezierCurveTo(-r, -r * 0.2, -r * 1.1, r * 0.6, 0, r * 1.9); ctx.fill();
  ctx.restore();
}

// ---- paleo globe: redraw reconstructed coastlines at time T (Ma) into an overlay canvas ----
export class PaleoOverlay {
  constructor(api, w = 4096, h = 2048) { this.api = api; this.cv = makeCanvas(w, h); this.g = this.cv.getContext('2d'); this.T = null; this.cache = {}; }
  async load(T) { const k = String(T).padStart(3, '0'); if (!this.cache[k]) this.cache[k] = await this.api.loadJSON(`paleo/coast_${k}.json`); return this.cache[k]; }
  async preload(list) { for (const T of list) await this.load(T); }
  // color fn(polyIndex) optional; highlight: array of {test(poly) -> bool, color}
  async draw(T, o = {}) {
    T = Math.max(0, Math.min(200, Math.round(T)));
    const key = T + '|' + (o.key || '');
    if (key === this.T) return false; this.T = key;
    const polys = await this.load(T); const g = this.g, W = this.cv.width, H = this.cv.height;
    const X = lo => (lo + 180) / 360 * W, Y = la => (90 - la) / 180 * H;
    g.clearRect(0, 0, W, H);
    g.fillStyle = o.land || '#c8b383';
    g.beginPath();
    for (const r of polys) { r.forEach(([lo, la], i) => i ? g.lineTo(X(lo), Y(la)) : g.moveTo(X(lo), Y(la))); g.closePath(); }
    g.fill('nonzero');
    if (o.coast !== false) { g.strokeStyle = o.coast || 'rgba(255,255,255,0.35)'; g.lineWidth = 2; g.stroke(); }
    const gl = this.api.g;
    if (gl.u.ovTex.value?.image !== this.cv) gl.setOverlay(this.cv, [-180, -90, 180, 90]); else gl.refreshOverlay();
    return true;
  }
}
// interpolated track position at fractional Ma
export function trackAt(tracks, name, T) {
  const tr = tracks[name]; if (!tr) return null;
  const i = Math.max(0, Math.min(199, Math.floor(T))), f = T - i;
  const a = tr[i], b = tr[i + 1] || a;
  if (!a || !b || a[0] > 900 || b[0] > 900) return null;
  let dlon = b[0] - a[0]; if (dlon > 180) dlon -= 360; if (dlon < -180) dlon += 360;
  return [lerp(a[1], b[1], f), a[0] + dlon * f]; // [lat, lon]
}

// ---- "MILLION YEARS AGO" counter chip ----
export function yearsChip(ctx, W, Ma, alpha = 1, label = 'MILLION YEARS AGO') {
  F.counter(ctx, Ma, Ma, 1, 120, 150, { size: 96, align: 'left', alpha, format: v => Math.round(v).toString() });
  F.text(ctx, label, 124, 200, { size: 30, fam: F.FAM.label, weight: 700, tracking: 0.18, color: PAL.sub, alpha });
}

// ---- tiny-planet Explorer gag scaffold ----
// const gag = await planetGag(api, 'gag1', {clips:[[t,'Walk'],[t2,'Death',{once:true}]], radius:3})  then in draw: gag.draw(ctx, t, {camAng})
export async function planetGag(api, key, o = {}) {
  const { Actor, tinyPlanet, THREE } = await import('./actors.js');
  const st = await api.newStage(key, Object.assign({ shadowExtent: 4, hemi: 1.5, key: 2.6, rim: 1.6 }, o.stage || {}));
  const planet = await tinyPlanet(st, { radius: o.radius || 3 }); planet.position.set(0, -(o.radius || 3), 0);
  const hero = await Actor.create(st, o.model || 'models/adventurer.glb', { scale: o.scale || 0.55 });
  for (const [t, clip, opt] of (o.clips || [])) hero.play(t, clip, opt || {});
  return {
    st, planet, hero, THREE,
    draw(ctx, t, d = {}) {
      const W = api.W, H = api.H;
      const g = ctx.createRadialGradient(W / 2, H * 0.62, 60, W / 2, H * 0.55, H * 1.05); g.addColorStop(0, d.bg0 || '#13254a'); g.addColorStop(1, d.bg1 || '#03050a');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      if (d.planetRot) { planet.rotation.x = d.planetRot[0]; planet.rotation.y = d.planetRot[1]; planet.rotation.z = d.planetRot[2] || 0; }
      const a = d.camAng ?? 0, dist = d.dist ?? 5.2, hgt = d.camH ?? 1.4;
      st.lookFrom([Math.sin(a) * dist, hgt, Math.cos(a) * dist], d.target || [0, 0.75, 0], d.fov || 30);
      ctx.drawImage(st.render(t), 0, 0);
    },
  };
}
