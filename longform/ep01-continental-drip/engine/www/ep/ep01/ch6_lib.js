// ch6 2D helpers: backdrops, archival print with mappable Ken Burns, underlines, school bus, filmstrip, tiles,
// arrows, impact flashes, comment bubble, Pangooy card, Equal Earth projection, 2D orthographic globe.
// Everything is a pure function of its arguments (deterministic, seeded rng only).
import * as F from '../../lib/fx.js';
const { PAL, E, prog, clamp, lerp } = F;
const D2R = Math.PI / 180;

export function makeCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// ---------------------------------------------------------------- backdrops (pre-rendered once)
export function makeSpace(W, H, seed = 5, o = {}) {
  const c = makeCanvas(W, H), g = c.getContext('2d'), r = F.rng(seed);
  const gr = g.createRadialGradient(W * 0.5, H * 0.62, 40, W * 0.5, H * 0.55, H * 1.15);
  gr.addColorStop(0, o.c0 || '#142a52'); gr.addColorStop(0.5, o.c1 || '#0a1430'); gr.addColorStop(1, o.c2 || '#03050b');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 1100; i++) { const b = Math.pow(r(), 5); g.fillStyle = `rgba(235,240,255,${0.12 + b * 0.85})`; g.beginPath(); g.arc(r() * W, r() * H, 0.6 + b * 1.5, 0, Math.PI * 2); g.fill(); }
  return c;
}
// slow drifting draw of a pre-rendered backdrop (scaled up slightly so the drift never shows an edge)
export function drawDrift(ctx, cv, W, H, t, o = {}) {
  const z = o.zoom ?? 1.06, sp = o.speed ?? 6;
  const ox = Math.sin(t * 0.05) * sp * 3 - W * (z - 1) / 2, oy = Math.cos(t * 0.04) * sp * 2 - H * (z - 1) / 2;
  ctx.drawImage(cv, ox, oy, W * z, H * z);
}
export function makeDesk(W, H, seed = 7) {
  const c = makeCanvas(W, H), g = c.getContext('2d'), r = F.rng(seed);
  const gr = g.createRadialGradient(W * 0.5, H * 0.45, 80, W * 0.5, H * 0.5, W * 0.75);
  gr.addColorStop(0, '#30271d'); gr.addColorStop(0.55, '#1a140f'); gr.addColorStop(1, '#080605');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  g.globalAlpha = 0.05; g.strokeStyle = '#d9b98a'; g.lineWidth = 2;
  for (let i = 0; i < 70; i++) { const y0 = r() * H; g.beginPath(); for (let x = 0; x <= W; x += 40) { const y = y0 + Math.sin(x * 0.004 + i) * 14 + Math.sin(x * 0.013 + i * 3) * 4; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
  g.globalAlpha = 1;
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(255,236,200,${0.02 + r() * 0.05})`; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  return c;
}

// ---------------------------------------------------------------- archival print with Ken Burns (returns image->screen map)
export function printKB(ctx, img, k, rect, from, to, o = {}) {
  const [x, y, w, h] = rect; const kk = (o.ease || E.inOutSine)(clamp(k));
  const cxn = lerp(from[0], to[0], kk), cyn = lerp(from[1], to[1], kk), z = lerp(from[2], to[2], kk);
  const ar = w / h, iar = img.width / img.height;
  let sw, sh; if (iar > ar) { sh = img.height / z; sw = sh * ar; } else { sw = img.width / z; sh = sw / ar; }
  const sx = clamp(cxn * img.width - sw / 2, 0, Math.max(0, img.width - sw)), sy = clamp(cyn * img.height - sh / 2, 0, Math.max(0, img.height - sh));
  const bd = o.border ?? 14, cxr = x + w / 2, cyr = y + h / 2, rot = o.rot || 0;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  if (rot) { ctx.translate(cxr, cyr); ctx.rotate(rot); ctx.translate(-cxr, -cyr); }
  for (let i = 5; i >= 1; i--) { ctx.fillStyle = 'rgba(0,0,0,0.09)'; F.round(ctx, x - bd - i * 6, y - bd - i * 4 + 18, w + 2 * bd + i * 12, h + 2 * bd + i * 10, 10 + i * 6); ctx.fill(); }
  if (bd > 0) { ctx.fillStyle = o.paper || '#e9dec6'; F.round(ctx, x - bd, y - bd, w + 2 * bd, h + 2 * bd, 6); ctx.fill(); }
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  if (o.grade) F.grade(ctx, x, y, w, h, o.grade);
  const vg = ctx.createRadialGradient(cxr, cyr, Math.min(w, h) * 0.35, cxr, cyr, Math.hypot(w, h) * 0.6); vg.addColorStop(0, 'rgba(40,25,10,0)'); vg.addColorStop(1, `rgba(40,25,10,${o.vig ?? 0.3})`); ctx.fillStyle = vg; ctx.fillRect(x, y, w, h);
  if (o.dim) { ctx.fillStyle = `rgba(8,6,4,${o.dim})`; ctx.fillRect(x, y, w, h); }
  ctx.restore();
  ctx.strokeStyle = 'rgba(70,50,25,0.45)'; ctx.lineWidth = 1.5; ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  ctx.restore();
  const cr = Math.cos(rot), sr = Math.sin(rot);
  return (u, v) => {
    const px = x + (u * img.width - sx) / sw * w, py = y + (v * img.height - sy) / sh * h;
    if (!rot) return [px, py];
    const dx = px - cxr, dy = py - cyr; return [cxr + dx * cr - dy * sr, cyr + dx * sr + dy * cr];
  };
}
export function underline(ctx, map, box, p, o = {}) {
  if (p <= 0) return;
  const [bx, by, bw, bh] = box, yy = by + bh + (o.dy ?? 0.0025);
  const a = map(bx - 0.004, yy), b = map(bx + bw + 0.004, yy);
  const pts = []; const n = 14;
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push([lerp(a[0], b[0], u), lerp(a[1], b[1], u) + Math.sin(u * 9.3 + bx * 37) * 1.8 + (u - 0.5) * 2]); }
  F.glowPath(ctx, pts, { p, color: o.color || PAL.hero, width: o.width || 5.5, alpha: o.alpha ?? 1, glowColor: o.glowColor });
}
export function highlight(ctx, map, box, p, o = {}) {
  if (p <= 0) return;
  const [bx, by, bw, bh] = box; const a = map(bx - 0.004, by - 0.002), b = map(bx + bw + 0.004, by + bh + 0.004);
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 0.28); ctx.fillStyle = o.color || PAL.hero;
  ctx.fillRect(a[0], a[1], (b[0] - a[0]) * clamp(p), b[1] - a[1]); ctx.restore();
}

// ---------------------------------------------------------------- pills / headline helpers with timing
// pill that pops in at a (outBack) and fades out at b
export function pillT(ctx, s, x, y, t, a, b, o = {}) {
  if (t < a || t > b) return;
  const pin = prog(t, a, a + 0.28, E.outBack), out = 1 - prog(t, b - 0.3, b, E.in);
  const al = clamp(prog(t, a, a + 0.12)) * out; if (al <= 0.003) return;
  ctx.save(); ctx.translate(x, y); const sc = lerp(0.82, 1, pin); ctx.scale(sc, sc);
  F.pill(ctx, s, 0, 0, Object.assign({ anchor: 'center', size: 40, alpha: al, border: o.border }, o, { leader: null }));
  ctx.restore();
}

// ---------------------------------------------------------------- '?' mark (Bebas) with soft glow disc
export function qmark(ctx, x, y, size, a, o = {}) {
  if (a <= 0.003) return;
  ctx.save(); ctx.globalAlpha *= a;
  const g = ctx.createRadialGradient(x, y, 0, x, y, size * 0.9); g.addColorStop(0, o.glow || 'rgba(61,227,255,0.28)'); g.addColorStop(1, 'rgba(61,227,255,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, size * 0.9, 0, Math.PI * 2); ctx.fill();
  F.text(ctx, '?', x, y, { size: Math.round(size), fam: F.FAM.head, weight: 400, align: 'center', baseline: 'middle', color: o.color || '#ffffff', shadowBlur: 18 });
  ctx.restore();
}

// ---------------------------------------------------------------- tile (rounded image card with shadow and border)
export function tile(ctx, img, x, y, w, h, o = {}) {
  const a = o.alpha ?? 1; if (a <= 0.003) return;
  const r = o.radius ?? 16;
  ctx.save(); ctx.globalAlpha *= a;
  for (let i = 4; i >= 1; i--) { ctx.fillStyle = 'rgba(0,0,0,0.12)'; F.round(ctx, x - i * 5, y - i * 3 + 12, w + i * 10, h + i * 8, r + i * 5); ctx.fill(); }
  ctx.save(); F.round(ctx, x, y, w, h, r); ctx.clip();
  if (img) { const sw = o.src ? o.src[2] : img.width, sh = o.src ? o.src[3] : img.height, sx = o.src ? o.src[0] : 0, sy = o.src ? o.src[1] : 0; ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h); }
  else { ctx.fillStyle = o.fill || '#0b1220'; ctx.fillRect(x, y, w, h); }
  if (o.dim) { ctx.fillStyle = `rgba(3,5,10,${o.dim})`; ctx.fillRect(x, y, w, h); }
  ctx.restore();
  const bw = o.borderW ?? 2;
  if (o.glow) { // pulse glow (layered strokes, no shadowBlur)
    for (const [lw, al] of [[18, 0.10], [10, 0.22]]) { ctx.strokeStyle = o.border; ctx.globalAlpha = a * al * o.glow; ctx.lineWidth = lw; F.round(ctx, x, y, w, h, r); ctx.stroke(); }
    ctx.globalAlpha = a;
  }
  ctx.strokeStyle = o.border || 'rgba(244,246,250,0.55)'; ctx.lineWidth = bw; F.round(ctx, x, y, w, h, r); ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------- arrow (curved, yellow) from a to b with a triangle head
export function arrow(ctx, a, b, o = {}) {
  const al = o.alpha ?? 1; if (al <= 0.003) return;
  const bend = o.bend ?? 0.18, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy); if (L < 8) return;
  const mx = (a[0] + b[0]) / 2 - dy * bend, my = (a[1] + b[1]) / 2 + dx * bend;
  const pts = []; for (let i = 0; i <= 24; i++) { const u = i / 24; pts.push([(1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * mx + u * u * b[0], (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * my + u * u * b[1]]); }
  const p = o.p ?? 1, col = o.color || PAL.yellow, w = o.width || 7;
  ctx.save(); ctx.globalAlpha *= al; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const head = F.glowPath(ctx, pts.slice(0, -2), { p, color: col, width: w });
  // head
  const n = Math.max(1, Math.round(pts.length * clamp(p)) - 1), q0 = pts[Math.max(0, n - 3)], q1 = pts[n];
  const ang = Math.atan2(q1[1] - q0[1], q1[0] - q0[0]), hs = w * 3.6;
  ctx.translate(q1[0], q1[1]); ctx.rotate(ang);
  ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.beginPath(); ctx.moveTo(hs * 0.7 + 3, 3); ctx.lineTo(-hs * 0.5, -hs * 0.62); ctx.lineTo(-hs * 0.5, hs * 0.62 + 4); ctx.closePath(); ctx.fill();
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(hs * 0.7, 0); ctx.lineTo(-hs * 0.5, -hs * 0.6); ctx.lineTo(-hs * 0.5, hs * 0.6); ctx.closePath(); ctx.fill();
  ctx.restore();
  return head;
}

// ---------------------------------------------------------------- impact flash: white ring + yellow burst lines (u = time since impact)
export function impact(ctx, x, y, u, o = {}) {
  if (u < 0 || u > 0.9) return;
  const s = o.scale ?? 1;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const r = (30 + 260 * E.outExpo(clamp(u / 0.7))) * s, a = 1 - clamp(u / 0.8);
  const g = ctx.createRadialGradient(x, y, 0, x, y, r * 0.8); g.addColorStop(0, `rgba(255,240,200,${0.55 * a})`); g.addColorStop(1, 'rgba(255,200,120,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 0.8, 0, Math.PI * 2); ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = `rgba(255,255,255,${0.9 * a})`; ctx.lineWidth = 5 * s * a + 1; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = o.color || PAL.yellow; ctx.lineCap = 'round'; ctx.lineWidth = 6 * s;
  for (let i = 0; i < 10; i++) {
    const ang = i / 10 * Math.PI * 2 + 0.3, r0 = (40 + 120 * E.outExpo(clamp(u / 0.4))) * s, r1 = r0 + (50 + 20 * (i % 3)) * s * (1 - clamp(u / 0.6));
    ctx.globalAlpha = a; ctx.beginPath(); ctx.moveTo(x + Math.cos(ang) * r0, y + Math.sin(ang) * r0); ctx.lineTo(x + Math.cos(ang) * r1, y + Math.sin(ang) * r1); ctx.stroke();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- yellow school bus (side view), centred, length L, angle ang
export function schoolBus(ctx, x, y, L, ang = 0, o = {}) {
  const a = o.alpha ?? 1; if (a <= 0.003) return;
  const s = L / 300; // design units: 300 long
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(o.flip ? -s : s, s); ctx.globalAlpha *= a;
  // shadow
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(0, 52, 150, 10, 0, 0, Math.PI * 2); ctx.fill();
  // body (front = +x: hood lower)
  const body = () => { ctx.beginPath(); ctx.moveTo(-150, 40); ctx.lineTo(-150, -48); ctx.quadraticCurveTo(-150, -58, -140, -58); ctx.lineTo(96, -58); ctx.quadraticCurveTo(108, -58, 110, -46); ctx.lineTo(112, -14); ctx.lineTo(140, -10); ctx.quadraticCurveTo(150, -8, 150, 2); ctx.lineTo(150, 40); ctx.closePath(); };
  body(); ctx.fillStyle = '#FFC21A'; ctx.fill();
  ctx.lineWidth = 5; ctx.strokeStyle = '#1b1407'; ctx.stroke();
  // roof light band
  ctx.fillStyle = 'rgba(255,255,255,0.28)'; ctx.fillRect(-140, -54, 236, 6);
  // windows
  ctx.fillStyle = '#20324a';
  for (let i = 0; i < 6; i++) { F.round(ctx, -138 + i * 38, -44, 30, 30, 4); ctx.fill(); }
  F.round(ctx, 92, -44, 16, 30, 3); ctx.fill(); // door window
  ctx.fillStyle = 'rgba(160,210,255,0.35)'; for (let i = 0; i < 6; i++) { ctx.fillRect(-134 + i * 38, -41, 8, 22); }
  // black rails
  ctx.fillStyle = '#1b1407'; ctx.fillRect(-150, -6, 262, 5); ctx.fillRect(-150, 14, 300, 5);
  // stop sign + lights
  ctx.fillStyle = '#E8322B'; ctx.beginPath(); ctx.arc(-120, 2, 9, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ff6d4a'; ctx.beginPath(); ctx.arc(-145, -50, 4, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.arc(100, -50, 4, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#fff4c0'; ctx.beginPath(); ctx.arc(146, 6, 5, 0, Math.PI * 2); ctx.fill();
  // wheels
  for (const wx of [-95, 95]) {
    ctx.fillStyle = '#121212'; ctx.beginPath(); ctx.arc(wx, 40, 22, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#8a8f99'; ctx.beginPath(); ctx.arc(wx, 40, 9, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- comment bubble icon (pops with scale)
export function commentBubble(ctx, x, y, s, t, a = 1) {
  if (a <= 0.003 || s <= 0.01) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha *= a;
  const path = () => { F.round(ctx, -110, -80, 220, 140, 34); ctx.moveTo(-40, 58); ctx.lineTo(-72, 108); ctx.lineTo(-2, 60); };
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.save(); ctx.translate(6, 10); path(); ctx.fill(); ctx.restore();
  path(); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = PAL.yellow; ctx.stroke();
  for (let i = 0; i < 3; i++) { const b = 0.5 + 0.5 * Math.sin(t * 8 - i * 0.9); ctx.fillStyle = `rgba(20,25,34,${0.45 + 0.55 * b})`; ctx.beginPath(); ctx.arc(-50 + i * 50, -10 - 6 * b, 15, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}

// ---------------------------------------------------------------- clock icon + Pangooy card (callback to s086)
export function clockIcon(ctx, x, y, r, hA, mA) {
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.lineWidth = r * 0.12; ctx.strokeStyle = '#141922'; ctx.stroke();
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; ctx.lineWidth = r * 0.05; ctx.beginPath(); ctx.moveTo(Math.cos(a) * r * 0.78, Math.sin(a) * r * 0.78); ctx.lineTo(Math.cos(a) * r * 0.9, Math.sin(a) * r * 0.9); ctx.stroke(); }
  ctx.lineCap = 'round'; ctx.lineWidth = r * 0.1; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(hA) * r * 0.45, Math.sin(hA) * r * 0.45); ctx.stroke();
  ctx.strokeStyle = PAL.hero; ctx.lineWidth = r * 0.07; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(mA) * r * 0.7, Math.sin(mA) * r * 0.7); ctx.stroke();
  ctx.fillStyle = '#141922'; ctx.beginPath(); ctx.arc(0, 0, r * 0.08, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
export function pangooyCard(ctx, x, y, rot, t, a = 1) {
  if (a <= 0.003) return;
  const cw = 740, ch = 300;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x - cw / 2, y - ch / 2); ctx.translate(cw / 2, ch / 2); ctx.rotate(rot); ctx.translate(-cw / 2, -ch / 2);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, 8, 14, cw, ch, 22); ctx.fill();
  ctx.fillStyle = '#f4efe2'; F.round(ctx, 0, 0, cw, ch, 22); ctx.fill(); ctx.fillStyle = PAL.hero; F.round(ctx, 0, 0, cw, 46, 22); ctx.fill(); ctx.fillRect(0, 24, cw, 22);
  for (let i = 0; i < 7; i++) { ctx.fillStyle = '#c9c1ae'; ctx.beginPath(); ctx.arc(70 + i * 100, 23, 8, 0, 7); ctx.fill(); }
  const sh = Math.sin(t * 70) * 0.12;
  ctx.save(); ctx.translate(120, 175); ctx.rotate(sh); clockIcon(ctx, 0, 0, 78, Math.PI * 1.5, Math.PI * 1.5); ctx.restore();
  F.text(ctx, 'TUESDAY, 9:00 A.M.,', 230, 160, { size: 58, fam: F.FAM.label, weight: 700, color: '#141922', tracking: 0.03, shadow: false });
  F.text(ctx, '1,786,379 A.D.', 230, 236, { size: 62, fam: F.FAM.body, weight: 800, color: PAL.hero, shadow: false });
  ctx.restore();
}

// ---------------------------------------------------------------- porch light (tiny lamp post with a warm glow), p = 0..1 on
export function porchLight(ctx, x, y, s, p, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const fl = p <= 0 ? 0 : clamp(p) * (p < 1 ? (0.5 + 0.5 * Math.sign(Math.sin(p * 40))) : 1) * (0.92 + 0.08 * Math.sin(t * 9));
  if (fl > 0) {
    ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createRadialGradient(0, -118, 0, 0, -118, 120); g.addColorStop(0, `rgba(255,214,140,${0.75 * fl})`); g.addColorStop(0.3, `rgba(255,170,80,${0.28 * fl})`); g.addColorStop(1, 'rgba(255,150,60,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, -118, 120, 0, Math.PI * 2); ctx.fill();
    ctx.globalCompositeOperation = 'source-over';
  }
  ctx.fillStyle = '#1d222c'; ctx.fillRect(-3, -110, 6, 110); ctx.fillRect(-14, -4, 28, 6);
  ctx.fillStyle = '#2a303c'; ctx.beginPath(); ctx.moveTo(-14, -126); ctx.lineTo(14, -126); ctx.lineTo(9, -140); ctx.lineTo(-9, -140); ctx.closePath(); ctx.fill();
  ctx.fillStyle = fl > 0 ? `rgba(255,236,170,${0.35 + 0.65 * fl})` : '#4a4f5c'; F.round(ctx, -10, -127, 20, 20, 3); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- Equal Earth (matches tex/equal_earth.jpg 3600x1760)
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, MM = Math.sqrt(3) / 2, ES = 651.7329707517487, ECX = 1800, ECY = 880;
export const EE_W = 3600, EE_H = 1760;
export function ee(lon, lat) {
  const l = lon * D2R, p = lat * D2R, th = Math.asin(MM * Math.sin(p)), t2 = th * th, t6 = t2 * t2 * t2;
  const x = l * Math.cos(th) / (MM * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))), y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [ECX + x * ES, ECY - y * ES];
}

// ---------------------------------------------------------------- 2D orthographic globe
export function v3(lat, lon) { const a = lat * D2R, b = lon * D2R; return [Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)]; }
export function ll3(p) { const L = Math.hypot(p[0], p[1], p[2]); return [Math.asin(p[1] / L) / D2R, Math.atan2(-p[2], p[0]) / D2R]; }
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const nrm = (a) => { const L = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / L, a[1] / L, a[2] / L]; };
// view: {lat, lon, cx, cy, R, roll}
export function orthoView(o) {
  const c = v3(o.lat, o.lon);
  let east = cross([0, 1, 0], c); if (Math.hypot(...east) < 1e-6) east = [1, 0, 0]; east = nrm(east);
  const north = nrm(cross(c, east));   // cross(up, c) = local east in this convention
  const cr = Math.cos(o.roll || 0), sr = Math.sin(o.roll || 0);
  return {
    ...o, c, east, north,
    // project a unit vector; returns [x, y, z]; z < 0 = behind (clamped to limb when clamp=true)
    pv(p, clampLimb = true) {
      let x = dot(p, east), y = dot(p, north); const z = dot(p, c);
      if (z < 0 && clampLimb) { const L = Math.hypot(x, y) || 1; x /= L; y /= L; }
      const X = x * cr - y * sr, Y = x * sr + y * cr;
      return [o.cx + X * o.R, o.cy - Y * o.R, z];
    },
    p(lat, lon, cl = true) { return this.pv(v3(lat, lon), cl); },
  };
}
// globe disc: glow, ocean gradient, graticule
export function orthoDisc(ctx, V, o = {}) {
  const { cx, cy, R } = V;
  ctx.save();
  const halo = ctx.createRadialGradient(cx, cy, R * 0.96, cx, cy, R * 1.16);
  halo.addColorStop(0, 'rgba(90,160,255,0.55)'); halo.addColorStop(0.35, 'rgba(60,120,230,0.18)'); halo.addColorStop(1, 'rgba(40,90,200,0)');
  ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(cx, cy, R * 1.16, 0, Math.PI * 2); ctx.fill();
  const og = ctx.createRadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.1, cx, cy, R);
  og.addColorStop(0, o.ocean0 || '#173a66'); og.addColorStop(0.7, o.ocean1 || '#0c2242'); og.addColorStop(1, o.ocean2 || '#061328');
  ctx.fillStyle = og; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
  if (o.grat !== false) {
    ctx.strokeStyle = 'rgba(160,200,255,0.10)'; ctx.lineWidth = 1.2; ctx.beginPath();
    for (let la = -60; la <= 60; la += 30) { let pen = false; for (let lo = -180; lo <= 180; lo += 4) { const q = V.p(la, lo, false); if (q[2] < 0) { pen = false; continue; } pen ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); pen = true; } }
    for (let lo = -180; lo < 180; lo += 30) { let pen = false; for (let la = -88; la <= 88; la += 4) { const q = V.p(la, lo, false); if (q[2] < 0) { pen = false; continue; } pen ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); pen = true; } }
    ctx.stroke();
  }
  ctx.restore();
}
// terminator-ish shading + rim light over the disc (call after land)
export function orthoShade(ctx, V) {
  const { cx, cy, R } = V;
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  const sg = ctx.createRadialGradient(cx - R * 0.45, cy - R * 0.5, R * 0.2, cx, cy, R * 1.05);
  sg.addColorStop(0, 'rgba(255,255,255,0.06)'); sg.addColorStop(0.55, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,4,12,0.55)');
  ctx.fillStyle = sg; ctx.fillRect(cx - R, cy - R, 2 * R, 2 * R);
  ctx.restore();
  ctx.save(); ctx.strokeStyle = 'rgba(140,190,255,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, R - 1, Math.PI * 0.95, Math.PI * 1.75); ctx.stroke(); ctx.restore();
}
// fill rings of unit vectors (already rotated) on the ortho view; returns nothing
export function orthoFillV(ctx, V, ringsV, o = {}) {
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.beginPath();
  for (const r of ringsV) {
    let anyFront = false; for (let i = 0; i < r.length; i += 4) if (dot(r[i], V.c) > -0.05) { anyFront = true; break; }
    if (!anyFront) continue;
    r.forEach((p, i) => { const q = V.pv(p); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.closePath();
  }
  ctx.fillStyle = o.color || '#d8c39a'; ctx.fill(o.rule || 'nonzero');
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw || 1.6; ctx.stroke(); }
  ctx.restore();
}
// rotation helpers on plain arrays (3x3 row-major)
export function frameOf(p1, p2) { const e1 = nrm(p1), e2 = nrm(cross(p1, p2)), e3 = cross(e1, e2); return [e1, e2, e3]; }
export function rotFrames(Ea, Fb) { const R = new Array(9).fill(0); for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { let s = 0; for (let k = 0; k < 3; k++) s += Fb[k][i] * Ea[k][j]; R[i * 3 + j] = s; } return R; }
export const applyR = (R, p) => [R[0] * p[0] + R[1] * p[1] + R[2] * p[2], R[3] * p[0] + R[4] * p[1] + R[5] * p[2], R[6] * p[0] + R[7] * p[1] + R[8] * p[2]];
export function axisRot(k, th) {
  const [x, y, z] = nrm(k), c = Math.cos(th), s = Math.sin(th), t = 1 - c;
  return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c];
}
export const mulR = (A, B) => { const C = new Array(9); for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i * 3 + j] = A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j]; return C; };
export { cross, dot, nrm };

// ---------------------------------------------------------------- south-pole style ring (yellow), optional flare
export function yRing(ctx, x, y, r, lt, a = 1) {
  if (a <= 0.003) return;
  const rr = r * (1 + 0.06 * Math.sin(lt * Math.PI * 2 / 1.2)), k = (lt / 1.2) % 1;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 3; ctx.globalAlpha *= (1 - k) * 0.6; ctx.beginPath(); ctx.arc(x, y, rr * (1 + k * 0.9), 0, Math.PI * 2); ctx.stroke();
  ctx.globalAlpha = a;
  ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 11; ctx.beginPath(); ctx.arc(x, y, rr, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(x, y, rr, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
}
