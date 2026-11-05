// ch3 helpers: keyframes, paper-page camera, Equal Earth projection (local copy: lib/equalearth.js does not parse),
// 2D graphic devices (inward arrows, question mark, stamps, ripples, checklist panel, clue cards).
import * as F from '../../lib/fx.js';
const { PAL, E, prog, env, clamp, lerp } = F;

// ---------- keyframes ----------
// keys: [{t, ...numbers, ease?}] absolute or local times. Numbers interpolate (key 'z' logarithmically).
export function keyAt(keys, t, ease = E.inOut) {
  if (t <= keys[0].t) return Object.assign({}, keys[0]);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b.t) {
      const k = (b.ease || ease)(clamp((t - a.t) / Math.max(1e-6, b.t - a.t)));
      const o = Object.assign({}, a);
      for (const key in b) {
        if (typeof b[key] === 'number' && typeof a[key] === 'number' && key !== 't') o[key] = key === 'z' ? Math.exp(lerp(Math.log(a[key]), Math.log(b[key]), k)) : lerp(a[key], b[key], k);
      }
      o.t = t; return o;
    }
  }
  return Object.assign({}, keys[keys.length - 1]);
}

// ---------- canvases ----------
export function cv(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// dark "desk" backdrop for paper pages (warm pool of light)
export function deskBg(W, H, warm = true) {
  const c = cv(W, H), g = c.getContext('2d');
  g.fillStyle = '#05070D'; g.fillRect(0, 0, W, H);
  const rg = g.createRadialGradient(W * 0.5, H * 0.42, 60, W * 0.5, H * 0.5, H * 1.05);
  rg.addColorStop(0, warm ? '#2a2318' : '#14223a'); rg.addColorStop(0.55, warm ? '#14110d' : '#0a1222'); rg.addColorStop(1, '#040507');
  g.fillStyle = rg; g.fillRect(0, 0, W, H);
  const r = F.rng(99); g.globalAlpha = 0.05;
  for (let i = 0; i < 2600; i++) { g.fillStyle = r() > 0.5 ? '#ffffff' : '#000000'; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  return c;
}
// soft drop-shadow sprite for a w x h page (drawn in page coordinates)
export function shadowSprite(w, h, pad = 160) {
  const s = 0.25, c = cv(Math.ceil((w + pad * 2) * s), Math.ceil((h + pad * 2) * s)), g = c.getContext('2d');
  g.filter = 'blur(14px)'; g.fillStyle = 'rgba(0,0,0,0.85)'; g.fillRect(pad * s, pad * s, w * s, h * s);
  return { c, pad };
}
export function pageMatrix(W, H, v) {
  return new DOMMatrix().translate(W / 2 + (v.ox || 0), H / 2 + (v.oy || 0)).rotate(v.rot || 0).scale(v.z).translate(-v.cx, -v.cy);
}
// draw a paper page (image in its own pixel space) with a camera v = {cx, cy, z, rot}; returns image->screen mapper
export function drawPage(ctx, img, v, W, H, o = {}) {
  const M = pageMatrix(W, H, v);
  ctx.save(); ctx.setTransform(M);
  if (o.shadow) { const p = o.shadow.pad; ctx.globalAlpha = 0.9; ctx.drawImage(o.shadow.c, -p, -p + img.height * 0.012, img.width + 2 * p, img.height + 2 * p); ctx.globalAlpha = 1; }
  ctx.drawImage(img, 0, 0);
  ctx.restore();
  const map = (ix, iy) => { const p = M.transformPoint(new DOMPoint(ix, iy)); return [p.x, p.y]; };
  map.M = M; return map;
}
// highlighter stroke over printed text (page coords), drawn left->right with progress p
export function highlighter(ctx, map, x0, x1, y, hgt, p, color = 'rgba(255,90,54,0.42)') {
  if (p <= 0) return;
  const [ax, ay] = map(x0, y - hgt / 2), [bx, by] = map(x0 + (x1 - x0) * p, y + hgt / 2);
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = color;
  ctx.setTransform(map.M); ctx.fillRect(x0, y - hgt / 2, (x1 - x0) * p, hgt); ctx.restore();
}
export function underline(ctx, map, x0, x1, y, p, o = {}) {
  if (p <= 0) return;
  const pts = []; for (let i = 0; i <= 12; i++) { const x = x0 + (x1 - x0) * i / 12; pts.push(map(x, y + Math.sin(i * 1.7) * (o.wobble ?? 1.5))); }
  F.glowPath(ctx, pts, { p, color: o.color || PAL.hero, width: o.width || 6 });
}

// ---------- Equal Earth (matches tex/equal_earth.jpg 3600x1760) ----------
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, MM = Math.sqrt(3) / 2, SS = 651.7329707517487, ECX = 1800.0, ECY = 880.0;
export const EE_W = 3600, EE_H = 1760;
export function ee(lon, lat) {
  const l = lon * Math.PI / 180, p = lat * Math.PI / 180, th = Math.asin(MM * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (MM * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [ECX + x * SS, ECY - y * SS];
}

// ---------- 2D devices ----------
// ring of inward-pointing arrows around (cx, cy) at radius R; phase animates the push; alpha fades
export function inwardArrows(ctx, cx, cy, R, phase, alpha = 1, o = {}) {
  if (alpha <= 0.01) return;
  const N = o.n || 10, col = o.color || PAL.cyan;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let i = 0; i < N; i++) {
    const ang = i / N * Math.PI * 2 + (o.rot || 0.31);
    const s = (phase + (i % 2) * 0.5) % 1;
    const push = E.inOutSine(s) * (o.push ?? 34);
    const r1 = R + (o.len ?? 120) - push, r0 = R + 18 - push;
    const ux = Math.cos(ang), uy = Math.sin(ang);
    const x1 = cx + ux * r1, y1 = cy + uy * r1, x0 = cx + ux * r0, y0 = cy + uy * r0;
    const a = 0.65 + 0.35 * Math.sin(Math.PI * s);
    ctx.globalAlpha = alpha * a;
    for (const [lw, c] of [[17, 'rgba(0,0,0,0.5)'], [9, col]]) {
      ctx.strokeStyle = c; ctx.fillStyle = c; ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x0 + ux * 22, y0 + uy * 22); ctx.stroke();
      const hx = x0, hy = y0, hw = lw === 17 ? 26 : 20, hl = lw === 17 ? 34 : 28, px = -uy, py = ux;
      ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(hx + ux * hl + px * hw, hy + uy * hl + py * hw); ctx.lineTo(hx + ux * hl - px * hw, hy + uy * hl - py * hw); ctx.closePath(); ctx.fill();
    }
  }
  ctx.restore();
}
// hand-drawn question mark, draw-on p (0..1), centred at (x, y), height h
export function questionMark(ctx, x, y, h, p, o = {}) {
  if (p <= 0) return;
  const pts = [];
  const r = h * 0.25, cx0 = x, cy0 = y - h * 0.2;
  for (let i = 0; i <= 26; i++) { const a = Math.PI * (1.12 - i / 26 * 1.55); pts.push([cx0 + Math.cos(a) * r * 1.05, cy0 - Math.sin(a) * r]); }
  const last = pts[pts.length - 1];
  pts.push([x + h * 0.02, y + h * 0.02]); pts.push([x, y + h * 0.16]);
  F.glowPath(ctx, pts, { p: clamp(p / 0.85), color: o.color || PAL.yellow, width: o.width || h * 0.075 });
  const dp = clamp((p - 0.85) / 0.15);
  if (dp > 0) { ctx.save(); ctx.fillStyle = o.color || PAL.yellow; ctx.globalAlpha *= dp; ctx.beginPath(); ctx.arc(x, y + h * 0.32, h * 0.06 * E.outBack(dp), 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
}
// rubber stamp: rotated rounded rectangle with big text, slams in (scale 1.7 -> 1) at p
export function stamp(ctx, s, x, y, p, o = {}) {
  if (p <= 0) return;
  const sc = lerp(1.8, 1, E.outBack(clamp(p))), a = clamp(p * 3);
  const size = o.size || 150, col = o.color || PAL.hero;
  const w = F.measure(ctx, s, { size, fam: F.FAM.head, weight: 400, tracking: 0.04 }) + size * 0.7, h = size * 1.15;
  ctx.save(); ctx.translate(x, y); ctx.rotate((o.rot ?? -8) * Math.PI / 180); ctx.scale(sc, sc); ctx.globalAlpha *= a;
  ctx.fillStyle = 'rgba(8,11,18,0.55)'; F.round(ctx, -w / 2, -h / 2, w, h, 18); ctx.fill();
  ctx.strokeStyle = col; ctx.lineWidth = 9; F.round(ctx, -w / 2, -h / 2, w, h, 18); ctx.stroke();
  ctx.lineWidth = 3; F.round(ctx, -w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 10); ctx.stroke();
  F.text(ctx, s, 0, size * 0.36, { size, fam: F.FAM.head, weight: 400, tracking: 0.04, align: 'center', color: col, shadow: false });
  ctx.restore();
}
// big X (red) slammed over a point
export function redX(ctx, x, y, s, p, o = {}) {
  if (p <= 0) return;
  const sc = lerp(1.6, 1, E.outBack(clamp(p))), a = clamp(p * 4);
  ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.globalAlpha *= a; ctx.lineCap = 'round';
  for (const [lw, c] of [[s * 0.2, 'rgba(0,0,0,0.45)'], [s * 0.13, o.color || '#FF3B3B']]) {
    ctx.strokeStyle = c; ctx.lineWidth = lw;
    ctx.beginPath(); ctx.moveTo(-s / 2, -s / 2); ctx.lineTo(s / 2, s / 2); ctx.moveTo(s / 2, -s / 2); ctx.lineTo(-s / 2, s / 2); ctx.stroke();
  }
  ctx.restore();
}
// expanding ripple ellipses
export function ripples(ctx, x, y, t, o = {}) {
  if (t < 0) return;
  ctx.save(); ctx.lineWidth = o.width || 3;
  for (let i = 0; i < (o.n || 3); i++) {
    const s = t - i * 0.28; if (s < 0 || s > 1.6) continue;
    const k = s / 1.6, r = (o.r || 160) * E.out(k);
    ctx.globalAlpha = (1 - k) * 0.8; ctx.strokeStyle = o.color || '#dffbff';
    ctx.beginPath(); ctx.ellipse(x, y, r, r * (o.flat || 0.4), 0, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.restore();
}
// yellow check-mark stroke (draw-on)
export function checkMark(ctx, x, y, s, p, color = PAL.yellow) {
  if (p <= 0) return;
  F.glowPath(ctx, [[x - s * 0.42, y], [x - s * 0.12, y + s * 0.32], [x + s * 0.48, y - s * 0.38]], { p, color, width: s * 0.14 });
}
// word wrap into max N chars per line
export function wrap(s, max = 17) {
  const out = []; let cur = '';
  for (const w of s.split(' ')) { if ((cur + ' ' + w).trim().length > max && cur) { out.push(cur); cur = w; } else cur = (cur + ' ' + w).trim(); }
  if (cur) out.push(cur); return out;
}
// cached starfield for stage backdrops
let STARS = null;
export function stageBg(ctx, W, H, o = {}) {
  const g = ctx.createRadialGradient(W * (o.x ?? 0.5), H * (o.y ?? 0.6), 60, W / 2, H * 0.55, H * 1.05);
  g.addColorStop(0, o.c0 || '#13254a'); g.addColorStop(1, o.c1 || '#03050a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (o.stars !== false) {
    if (!STARS) {
      STARS = cv(W, H); const s = STARS.getContext('2d'), r = F.rng(4242);
      for (let i = 0; i < 700; i++) { const b = Math.pow(r(), 5) * 0.9 + 0.08; s.fillStyle = `rgba(235,240,255,${b})`; s.beginPath(); s.arc(r() * W, r() * H, b > 0.5 ? 1.5 : 1, 0, Math.PI * 2); s.fill(); }
    }
    ctx.save(); ctx.globalAlpha = o.starAlpha ?? 0.7; ctx.drawImage(STARS, -((o.drift || 0) % W), 0); if (o.drift) ctx.drawImage(STARS, W - ((o.drift || 0) % W), 0); ctx.restore();
  }
}
// soft additive glow sprite
const GLOWS = {};
export function glowSprite(color) {
  if (GLOWS[color]) return GLOWS[color];
  const c = cv(64, 64), g = c.getContext('2d'); const rg = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  rg.addColorStop(0, '#ffffff'); rg.addColorStop(0.18, color); rg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = rg; g.fillRect(0, 0, 64, 64); return (GLOWS[color] = c);
}
export { F, PAL, E, prog, env, clamp, lerp };
