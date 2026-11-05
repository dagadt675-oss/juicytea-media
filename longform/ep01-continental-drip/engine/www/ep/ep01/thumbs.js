// Thumbnail variants (rendered at 1920x1080, downscaled to 1280x720 for upload).
//  v0  CAN'T UNSEE IT     globe in the cold-open look (frame 1 palette): South America + Africa tapers, drip arrows into the '?' ring
//  v1  POINTING AT WHAT?  flat Equal Earth map (the 0:08 frame): all three tapers, three drip arrows into the '?' ring on Antarctica
//  v2  THEY POINT HERE    low south-polar globe: both tips huge, one fat arrow, ghost outlines snapped into the ring
import { region, WorldOverlay } from '../../lib/beats.js';
import { gcLine, projectPath } from '../../lib/geo.js';
import { ee, eePath, eeOutline, EE_W, EE_H } from './ch1_ee.js';
const RED = '#FF2B2B', ORANGE = '#FF5A36', YELLOW = '#FFD23F';
const TIPS = { sam: [-53.9, -71.3], afr: [-34.8, 20.0], ind: [8.1, 77.5] };
let OV = null, R = null, EEB = null, EP = null, IND = null;

async function regions() {
  if (!R) R = { sam: await region('south america'), afr: await region('africa'), ind: await region('india') };
  return R;
}
async function globeBase(ctx, api, cam, o = {}) {
  const g = await api.globe(); const r = await regions();
  if (!OV) OV = new WorldOverlay();
  OV.set([{ key: 'sam', features: r.sam, color: ORANGE, alpha: 0.95, glow: 30 }, { key: 'afr', features: r.afr, color: ORANGE, alpha: 0.95, glow: 30 },
    { key: 'ind', features: r.ind, color: ORANGE, alpha: 0.95, glow: 30 }], g);
  g.set(Object.assign({ tilt: 0, heading: 0, fov: 34, sun: 'camera', sunAz: -30, sunEl: 28 }, cam));
  for (const [k, v] of Object.entries(Object.assign({ ovAlpha: 1, dim: 0.38, desat: 0.3, nightAmt: 0, relief: 1.0, exposure: 1.4, ambient: 0.12, ovMul: 0, specAmt: 0.5, rimAmt: 0.5 }, o.look || {}))) g.look(k, v);
  ctx.fillStyle = '#04060B'; ctx.fillRect(0, 0, api.W, api.H);
  ctx.drawImage(g.render(), 0, 0);
  return g;
}
// thick white arrow along screen points (black outline under it), head at the end
function arrowPath(ctx, pts, o = {}) {
  if (pts.length < 2) return;
  const w = o.width || 15, h = o.head || 46, trim = o.trim || 0;
  // pull the shaft back so it ends under the head
  let P = pts.slice();
  if (trim > 0) { let acc = 0; while (P.length > 2) { const [a, b] = [P[P.length - 1], P[P.length - 2]]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (acc + d > trim) break; acc += d; P.pop(); } }
  const [x1, y1] = pts[pts.length - 1]; let k = pts.length - 2; while (k > 0 && Math.hypot(x1 - pts[k][0], y1 - pts[k][1]) < h * 0.8) k--;
  const a = Math.atan2(y1 - pts[k][1], x1 - pts[k][0]);
  for (const [lw, col, s] of [[w + 11, 'rgba(0,0,0,0.6)', 1.22], [w, o.color || '#ffffff', 1]]) {
    ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); P.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); ctx.restore();
    ctx.save(); ctx.fillStyle = col; ctx.translate(x1, y1); ctx.rotate(a); ctx.beginPath();
    ctx.moveTo(h * 0.35 * s, 0); ctx.lineTo(-h * 0.75 * s, h * 0.55 * s); ctx.lineTo(-h * 0.75 * s, -h * 0.55 * s); ctx.closePath(); ctx.fill(); ctx.restore();
  }
}
function cutAt(pts, rx, ry, a, b, m = 10) {
  const out = [];
  for (const p of pts) { const dx = (p[0] - rx) / (a + m), dy = (p[1] - ry) / (b + m); out.push(p); if (dx * dx + dy * dy < 1) break; }
  return out;
}
function quad(x0, y0, x1, y1, bend, n = 60) {
  const mx = (x0 + x1) / 2 - (y1 - y0) * bend, my = (y0 + y1) / 2 + (x1 - x0) * bend, out = [];
  for (let i = 0; i <= n; i++) { const t = i / n, u = 1 - t; out.push([u * u * x0 + 2 * u * t * mx + t * t * x1, u * u * y0 + 2 * u * t * my + t * t * y1]); }
  return out;
}
function ringQ(api, ctx, x, y, r, o = {}) {
  // soft yellow halo (radial gradient, no shadowBlur), then the ring
  const gr = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * 1.9);
  gr.addColorStop(0, 'rgba(255,210,63,0.30)'); gr.addColorStop(1, 'rgba(255,210,63,0)');
  ctx.save(); ctx.fillStyle = gr; ctx.beginPath(); ctx.ellipse(x, y, r * 1.9, r * 1.9 * (o.squash || 1), 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  ctx.save(); ctx.fillStyle = 'rgba(4,6,11,0.55)'; ctx.beginPath(); ctx.ellipse(x, y, r, r * (o.squash || 1), 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  api.ring(ctx, x, y, r, { width: o.width || 16, color: YELLOW, squash: o.squash || 1 });
  if (o.q !== false) api.F.text(ctx, '?', x, y + (o.qSize || 150) * 0.36, { size: o.qSize || 150, fam: api.F.FAM.black, color: '#ffffff', align: 'center', stroke: 12, strokeColor: '#000', shadow: false });
}
// filled white silhouette of a region (union of its country polygons), tip at (x, y), rotated so the tip points along `dir`
function silhouette(ctx, features, tip, x, y, dir, scale) {
  const lat0 = tip[0] * Math.PI / 180;
  ctx.save(); ctx.translate(x, y); ctx.rotate(dir - Math.PI / 2); ctx.beginPath();
  for (const f of features) {
    const gm = f.geometry || f; const polys = gm.type === 'Polygon' ? [gm.coordinates] : gm.type === 'MultiPolygon' ? gm.coordinates : [];
    for (const poly of polys) { const ring = poly[0]; if (ring.length < 30) continue;
      ring.forEach(([lon, lat], i) => { const px = (lon - tip[1]) * Math.cos(lat0) * scale, py = -(lat - tip[0]) * scale; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.closePath(); }
  }
  ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(0,0,0,0.65)'; ctx.lineWidth = 7; ctx.stroke();
  ctx.fillStyle = '#ffffff'; ctx.fill('nonzero'); ctx.restore();
}
// ghost outline of a region, drawn in a local frame: tip at (x, y), shape rotated so its tip points along angle `dir`
function ghost(ctx, features, tip, x, y, dir, scale) {
  const lat0 = tip[0] * Math.PI / 180;
  ctx.save(); ctx.translate(x, y); ctx.rotate(dir - Math.PI / 2); ctx.beginPath();
  for (const f of features) {
    const gm = f.geometry || f; const polys = gm.type === 'Polygon' ? [gm.coordinates] : gm.type === 'MultiPolygon' ? gm.coordinates : [];
    for (const poly of polys) { const ring = poly[0]; if (ring.length < 40) continue;
      ring.forEach(([lon, lat], i) => { const px = (lon - tip[1]) * Math.cos(lat0) * scale, py = -(lat - tip[0]) * scale; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.closePath(); }
  }
  ctx.fillStyle = 'rgba(255,90,54,0.22)'; ctx.fill();
  ctx.setLineDash([10, 8]); ctx.lineWidth = 4; ctx.strokeStyle = '#ffffff'; ctx.stroke(); ctx.restore();
}
async function flatBase(ctx, api, zoom = 1) {
  const W = api.W, H = api.H; const r = await regions();
  if (!EEB) {
    const img = await api.image('tex/equal_earth.jpg');
    EEB = document.createElement('canvas'); EEB.width = EE_W; EEB.height = EE_H;
    const eg = EEB.getContext('2d'); const out = eeOutline();
    eg.save(); eg.clip(out); eg.drawImage(img, 0, 0);
    eg.globalCompositeOperation = 'saturation'; eg.fillStyle = 'rgba(128,128,128,0.40)'; eg.fillRect(0, 0, EE_W, EE_H);
    eg.globalCompositeOperation = 'multiply'; eg.fillStyle = '#a7b2cc'; eg.fillRect(0, 0, EE_W, EE_H);
    // lift the near-black ocean to navy so the tile keeps an edge on dark-mode feeds (land is barely touched)
    eg.globalCompositeOperation = 'lighten'; eg.fillStyle = '#10284C'; eg.fillRect(0, 0, EE_W, EE_H);
    eg.globalCompositeOperation = 'source-over'; eg.strokeStyle = 'rgba(200,220,255,0.08)'; eg.lineWidth = 2;
    for (let lo = -180; lo <= 180; lo += 30) { eg.beginPath(); for (let la = -90; la <= 90; la += 3) { const [x, y] = ee(lo, la); la === -90 ? eg.moveTo(x, y) : eg.lineTo(x, y); } eg.stroke(); }
    for (let la = -60; la <= 60; la += 30) { eg.beginPath(); for (let lo = -180; lo <= 180; lo += 3) { const [x, y] = ee(lo, la); lo === -180 ? eg.moveTo(x, y) : eg.lineTo(x, y); } eg.stroke(); }
    eg.restore();
    const big = (fs) => fs.map(f => { const gm = f.geometry || f; const polys = gm.type === 'Polygon' ? [gm.coordinates] : gm.type === 'MultiPolygon' ? gm.coordinates : [];
      const keep = polys.filter(pl => { const xs = pl[0].map(c => c[0]), ys = pl[0].map(c => c[1]); return Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) > 2.2; });
      return { type: 'Feature', geometry: { type: 'MultiPolygon', coordinates: keep } }; });
    EP = { sam: eePath(big(r.sam)), afr: eePath(big(r.afr)), ind: eePath(big(r.ind)) };
    // India: highlight the peninsula only (fade out north of ~22N), so no contested northern boundary is drawn
    IND = document.createElement('canvas'); IND.width = EE_W; IND.height = EE_H;
    const ig = IND.getContext('2d'); ig.lineJoin = 'round';
    ig.globalAlpha = 0.35; ig.strokeStyle = ORANGE; ig.lineWidth = 30; ig.stroke(EP.ind);
    ig.globalAlpha = 1; ig.strokeStyle = '#ffffff'; ig.lineWidth = 6; ig.stroke(EP.ind); ig.fillStyle = ORANGE; ig.fill(EP.ind, 'nonzero');
    const [, yN] = ee(78, 25), [, yS] = ee(78, 20.5); const mg = ig.createLinearGradient(0, yN, 0, yS); mg.addColorStop(0, 'rgba(0,0,0,0)'); mg.addColorStop(1, 'rgba(0,0,0,1)');
    ig.globalCompositeOperation = 'destination-in'; ig.fillStyle = mg; ig.fillRect(0, 0, EE_W, EE_H);
  }
  // view: lon -92..96, lat 44..-90 (+ margin); then optionally zoom out about the drip ring
  const [xa] = ee(-92, 0), [xb] = ee(96, 0), [, ya] = ee(0, 44); const yb = ee(0, -90)[1] + 170;
  let s = Math.min(W / (xb - xa), H / (yb - ya)), ox = -xa * s + (W - (xb - xa) * s) / 2, oy = -ya * s + (H - (yb - ya) * s) / 2;
  if (zoom !== 1) { const [rx0, ry0] = ee(8, -72); const ax = ox + rx0 * s, ay = oy + ry0 * s; s *= zoom; ox = ax - (ax - ox) * zoom; oy = ay - (ay - oy) * zoom; }
  ctx.fillStyle = '#0B1526'; ctx.fillRect(0, 0, W, H);
  ctx.drawImage(EEB, ox, oy, EE_W * s, EE_H * s);
  ctx.save(); ctx.setTransform(s, 0, 0, s, ox, oy); ctx.lineJoin = 'round';
  for (const k of ['sam', 'afr']) {
    ctx.globalAlpha = 0.35; ctx.strokeStyle = ORANGE; ctx.lineWidth = 30 / s; ctx.stroke(EP[k]);
    ctx.globalAlpha = 1; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 6 / s; ctx.stroke(EP[k]);
    ctx.fillStyle = ORANGE; ctx.fill(EP[k], 'nonzero');
  }
  ctx.restore();
  ctx.drawImage(IND, ox, oy, EE_W * s, EE_H * s);
  return (lat, lon) => { const [x, y] = ee(lon, lat); return [ox + x * s, oy + y * s]; };
}

async function flatScene(ctx, api) {
  const P = await flatBase(ctx, api, 0.92);
  const RR = 128, SQ = 0.66;
  const [rx, ry] = P(-72, 8); const tgt = { sam: [rx - 40, ry + 6], afr: [rx, ry], ind: [rx + 40, ry + 6] };
  const bends = { sam: 0.24, afr: 0.0, ind: -0.26 };
  ringQ(api, ctx, rx, ry, RR, { squash: SQ, qSize: 200, width: 22 });
  for (const k of ['sam', 'afr', 'ind']) {
    const [x0, y0] = P(TIPS[k][0] - 1.2, TIPS[k][1]);
    arrowPath(ctx, cutAt(quad(x0, y0 + 10, tgt[k][0], tgt[k][1], bends[k], 90), rx, ry, RR, RR * SQ, 24), { width: 26, head: 72 });
  }
}
// three hooks on the same art, so Test & Compare measures only the words: B question (default), A perception, S claim (s081: "They're scars")
export async function draw(ctx, W, H, api, variant) {
  const v = variant % 3;
  await flatScene(ctx, api);
  if (v === 0) api.boxText(ctx, [[{ w: "CAN'T" }], [{ w: 'UNSEE', c: YELLOW }, { w: 'IT' }]], 64, 186, { size: 132, bg: '#000000' });
  else if (v === 1) api.boxText(ctx, [[{ w: 'POINTING' }], [{ w: 'AT' }, { w: 'WHAT?', c: YELLOW }]], 64, 186, { size: 132, bg: '#000000' });
  else api.boxText(ctx, [[{ w: "THEY'RE" }], [{ w: 'SCARS', c: YELLOW }]], 64, 186, { size: 132, bg: '#000000' });
}
