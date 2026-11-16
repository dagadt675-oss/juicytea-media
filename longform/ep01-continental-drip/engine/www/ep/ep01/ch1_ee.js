// Equal Earth projection matching tex/equal_earth.jpg (3600x1760 px).
// Local copy for module ch1: lib/equalearth.js contains a Python leftover (`np.float64(...)`) that throws a
// ReferenceError on import, so chapter modules cannot import it. Same constants, fixed.
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2, S = 651.7329707517487, CX = 1800.0, CY = 880.0;
export const EE_W = 3600, EE_H = 1760;
export function ee(lon, lat) {
  const l = lon * Math.PI / 180, p = lat * Math.PI / 180, th = Math.asin(M * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [CX + x * S, CY - y * S];
}
// view {cx, cy, zoom} in IMAGE px -> screen transform for a W x H screen
export function eeXform(view, W, H) { const s = view.zoom * Math.min(W / EE_W, H / EE_H); return { s, ox: W / 2 - view.cx * s, oy: H / 2 - view.cy * s }; }
export function eeScreen(lon, lat, view, W, H) { const [x, y] = ee(lon, lat); const k = eeXform(view, W, H); return [k.ox + x * k.s, k.oy + y * k.s]; }
// Path2D in image px for GeoJSON features (Polygon / MultiPolygon)
export function eePath(features) {
  const p = new Path2D();
  for (const f of features) {
    const g = f.geometry || f; const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
    for (const poly of polys) for (const ring of poly) {
      ring.forEach(([lon, lat], i) => { const [x, y] = ee(lon, lat); if (i) p.lineTo(x, y); else p.moveTo(x, y); });
      p.closePath();
    }
  }
  return p;
}
// outline of the whole projected world (for clipping)
export function eeOutline() {
  const p = new Path2D();
  for (let la = -90; la <= 90; la += 2) { const [x, y] = ee(-180, la); if (la === -90) p.moveTo(x, y); else p.lineTo(x, y); }
  for (let la = 90; la >= -90; la -= 2) { const [x, y] = ee(180, la); p.lineTo(x, y); }
  p.closePath(); return p;
}
