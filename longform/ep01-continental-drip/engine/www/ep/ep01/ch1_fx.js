// ch1 2D helpers: archival print frames with mappable Ken Burns, underlines, the south-pole ring, coin, rubber stamp,
// cartoon wave, wax seal, paper sheets, magnifier. Everything deterministic (seeded rng) and cheap per frame.
import * as F from '../../lib/fx.js';
const { PAL, E, prog, clamp, lerp } = F;

export function makeCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// ---- dark warm desk / archive backdrop (pre-rendered once) ----
export function makeDesk(W, H, seed = 7, o = {}) {
  const c = makeCanvas(W, H), g = c.getContext('2d'), r = F.rng(seed);
  const gr = g.createRadialGradient(W * 0.5, H * 0.45, 80, W * 0.5, H * 0.5, W * 0.75);
  gr.addColorStop(0, o.c0 || '#30271d'); gr.addColorStop(0.55, o.c1 || '#1a140f'); gr.addColorStop(1, o.c2 || '#080605');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // faint wood grain
  g.globalAlpha = 0.05; g.strokeStyle = '#d9b98a'; g.lineWidth = 2;
  for (let i = 0; i < 70; i++) { const y0 = r() * H; g.beginPath(); for (let x = 0; x <= W; x += 40) { const y = y0 + Math.sin(x * 0.004 + i) * 14 + Math.sin(x * 0.013 + i * 3) * 4; x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
  // dust specks
  g.globalAlpha = 1;
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(255,236,200,${0.02 + r() * 0.05})`; g.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  return c;
}
// starry space backdrop for the 3D gags (pre-rendered once)
export function makeSpace(W, H, seed = 3, warm = true) {
  const c = makeCanvas(W, H), g = c.getContext('2d'), r = F.rng(seed);
  const gr = g.createRadialGradient(W * 0.55, H * 0.75, 50, W * 0.5, H * 0.6, H * 1.25);
  gr.addColorStop(0, '#1b2f57'); gr.addColorStop(0.5, '#0b1530'); gr.addColorStop(1, '#03050b');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  for (let i = 0; i < 900; i++) { const b = Math.pow(r(), 5); g.fillStyle = `rgba(235,240,255,${0.15 + b * 0.85})`; g.beginPath(); g.arc(r() * W, r() * H, 0.6 + b * 1.6, 0, Math.PI * 2); g.fill(); }
  if (warm) { const s = g.createRadialGradient(W * 0.86, H * 0.12, 0, W * 0.86, H * 0.12, W * 0.55); s.addColorStop(0, 'rgba(255,170,80,0.40)'); s.addColorStop(0.35, 'rgba(255,120,50,0.12)'); s.addColorStop(1, 'rgba(255,120,50,0)'); g.fillStyle = s; g.fillRect(0, 0, W, H); }
  return c;
}
// additive warm sun flare (top-right); cheap gradients only
export function sunFlare(ctx, W, H, t, a = 1) {
  const x = W * 0.86 + Math.sin(t * 0.7) * 6, y = H * 0.13;
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a;
  let g = ctx.createRadialGradient(x, y, 0, x, y, 260); g.addColorStop(0, 'rgba(255,250,225,0.95)'); g.addColorStop(0.12, 'rgba(255,214,140,0.65)'); g.addColorStop(0.4, 'rgba(255,140,60,0.18)'); g.addColorStop(1, 'rgba(255,120,40,0)');
  ctx.fillStyle = g; ctx.fillRect(x - 260, y - 260, 520, 520);
  // streak + ghosts along the diagonal toward frame centre
  ctx.fillStyle = 'rgba(255,200,140,0.10)'; ctx.fillRect(x - 520, y - 3, 1040, 6);
  for (const [k, rr, al] of [[0.35, 34, 0.10], [0.6, 18, 0.14], [0.85, 60, 0.06]]) {
    const gx = lerp(x, W / 2, k * 1.6), gy = lerp(y, H / 2, k * 1.6);
    const gg = ctx.createRadialGradient(gx, gy, 0, gx, gy, rr); gg.addColorStop(0, `rgba(255,190,120,${al})`); gg.addColorStop(1, 'rgba(255,190,120,0)');
    ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(gx, gy, rr, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// ---- archival print with Ken Burns. k: 0..1 progress; from/to: [cx, cy, zoom] in normalized image coords.
// returns map(u, v) -> [x, y] screen position of a normalized image point (for underlines that stick to the text)
export function printKB(ctx, img, k, rect, from, to, o = {}) {
  const [x, y, w, h] = rect; const kk = (o.ease || E.inOutSine)(clamp(k));
  const cxn = lerp(from[0], to[0], kk), cyn = lerp(from[1], to[1], kk), z = lerp(from[2], to[2], kk);
  const ar = w / h, iar = img.width / img.height;
  let sw, sh; if (iar > ar) { sh = img.height / z; sw = sh * ar; } else { sw = img.width / z; sh = sw / ar; }
  const sx = clamp(cxn * img.width - sw / 2, 0, Math.max(0, img.width - sw)), sy = clamp(cyn * img.height - sh / 2, 0, Math.max(0, img.height - sh));
  const bd = o.border ?? 14, cxr = x + w / 2, cyr = y + h / 2, rot = o.rot || 0;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  if (rot) { ctx.translate(cxr, cyr); ctx.rotate(rot); ctx.translate(-cxr, -cyr); }
  if (o.shadow !== false) for (let i = 5; i >= 1; i--) { ctx.fillStyle = 'rgba(0,0,0,0.09)'; F.round(ctx, x - bd - i * 6, y - bd - i * 4 + 18, w + 2 * bd + i * 12, h + 2 * bd + i * 10, 10 + i * 6); ctx.fill(); }
  if (bd > 0) { ctx.fillStyle = o.paper || '#e9dec6'; F.round(ctx, x - bd, y - bd, w + 2 * bd, h + 2 * bd, 6); ctx.fill(); }
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  if (o.grade) F.grade(ctx, x, y, w, h, o.grade);
  if (o.vig !== false) { const vg = ctx.createRadialGradient(cxr, cyr, Math.min(w, h) * 0.35, cxr, cyr, Math.hypot(w, h) * 0.6); vg.addColorStop(0, 'rgba(40,25,10,0)'); vg.addColorStop(1, `rgba(40,25,10,${o.vig ?? 0.32})`); ctx.fillStyle = vg; ctx.fillRect(x, y, w, h); }
  if (o.dim) { ctx.fillStyle = `rgba(8,6,4,${o.dim})`; ctx.fillRect(x, y, w, h); }
  ctx.restore();
  ctx.strokeStyle = 'rgba(70,50,25,0.45)'; ctx.lineWidth = 1.5; ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  ctx.restore();
  const cr = Math.cos(rot), sr = Math.sin(rot);
  const map = (u, v) => {
    const px = x + (u * img.width - sx) / sw * w, py = y + (v * img.height - sy) / sh * h;
    if (!rot) return [px, py];
    const dx = px - cxr, dy = py - cyr; return [cxr + dx * cr - dy * sr, cyr + dx * sr + dy * cr];
  };
  // the visible print area in screen space, so marks drawn through this map can be clipped to the page
  map.clipPoly = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]].map(([px, py]) => { const dx = px - cxr, dy = py - cyr; return [cxr + dx * cr - dy * sr, cyr + dx * sr + dy * cr]; });
  return map;
}
function clipToPrint(ctx, map) {
  if (!map.clipPoly) return;
  ctx.beginPath(); map.clipPoly.forEach(([px, py], i) => i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)); ctx.closePath(); ctx.clip();
}
// hand-drawn underline under a normalized box [x, y, w, h] of the image
export function underline(ctx, map, box, p, o = {}) {
  if (p <= 0) return;
  const [bx, by, bw, bh] = box, yy = by + bh + (o.dy ?? 0.0025);
  const a = map(bx - 0.004, yy), b = map(bx + bw + 0.004, yy);
  const pts = []; const n = 14;
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push([lerp(a[0], b[0], u), lerp(a[1], b[1], u) + Math.sin(u * 9.3 + bx * 37) * 1.8 + (u - 0.5) * 2]); }
  ctx.save(); clipToPrint(ctx, map);
  F.glowPath(ctx, pts, { p, color: o.color || PAL.hero, width: o.width || 5.5, alpha: o.alpha ?? 1 });
  ctx.restore();
}
// translucent marker highlight behind text box (drawn on top with multiply-ish alpha)
export function highlight(ctx, map, box, p, o = {}) {
  if (p <= 0) return;
  const [bx, by, bw, bh] = box; const a = map(bx - 0.004, by - 0.002), b = map(bx + bw + 0.004, by + bh + 0.004);
  ctx.save(); clipToPrint(ctx, map); ctx.globalAlpha *= (o.alpha ?? 0.28); ctx.fillStyle = o.color || PAL.hero;
  ctx.fillRect(a[0], a[1], (b[0] - a[0]) * clamp(p), b[1] - a[1]); ctx.restore();
}

// ---- the recurring south-pole ring with a '?' ----
export function southRing(ctx, x, y, lt, o = {}) {
  const sc = o.scale ?? 1, a = o.alpha ?? 1; if (a <= 0.002) return;
  const r = (o.r || 40) * sc * (1 + 0.07 * Math.sin(lt * Math.PI * 2 / 1.2));
  ctx.save(); ctx.globalAlpha *= a;
  const k = (lt / 1.2) % 1;
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 3; ctx.globalAlpha *= (1 - k) * 0.6; ctx.beginPath(); ctx.arc(x, y, r * (1 + k * 0.9), 0, Math.PI * 2); ctx.stroke(); ctx.globalAlpha /= Math.max(0.001, (1 - k) * 0.6);
  if (o.flare) { const f = o.flare; const gg = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * (1.5 + 3 * f)); gg.addColorStop(0, `rgba(255,210,63,${0.55 * (1 - f * 0.5)})`); gg.addColorStop(1, 'rgba(255,210,63,0)'); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, r * (1.5 + 3 * f), 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#fff6d0'; ctx.lineWidth = 4 * (1 - f); ctx.beginPath(); ctx.arc(x, y, r * (1 + 2.6 * f), 0, Math.PI * 2); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 11 * Math.sqrt(sc); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 6 * Math.sqrt(sc); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
  if (o.q !== false) F.text(ctx, '?', x, y, { size: Math.round(r * 1.3), fam: F.FAM.head, weight: 400, align: 'center', baseline: 'middle', color: '#ffffff', alpha: o.qAlpha ?? 1 });
  ctx.restore();
}

// ---- spinning gold coin (phase in radians; crack 0..1 splits it) ----
function coinFace(ctx, r, phase) {
  const c = Math.cos(phase), s = Math.sin(phase), sx = Math.max(0.035, Math.abs(c)), front = c >= 0;
  const th = r * 0.13 * Math.abs(s), dir = s >= 0 ? 1 : -1;
  // edge (thickness) as stacked ellipses
  for (let i = 6; i >= 1; i--) { ctx.fillStyle = i % 2 ? '#8d5f0f' : '#a8761a'; ctx.beginPath(); ctx.ellipse(dir * th * i / 6, 0, r * sx, r, 0, 0, Math.PI * 2); ctx.fill(); }
  const gr = ctx.createLinearGradient(-r * sx, -r, r * sx, r);
  gr.addColorStop(0, front ? '#fff1b0' : '#f0cd6a'); gr.addColorStop(0.45, front ? '#f6c84a' : '#dcab35'); gr.addColorStop(1, '#a8720f');
  ctx.fillStyle = gr; ctx.beginPath(); ctx.ellipse(0, 0, r * sx, r, 0, 0, Math.PI * 2); ctx.fill();
  ctx.save(); ctx.scale(sx, 1);
  ctx.strokeStyle = 'rgba(255,248,210,0.75)'; ctx.lineWidth = r * 0.035; ctx.beginPath(); ctx.arc(0, 0, r * 0.88, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = 'rgba(120,78,8,0.85)'; ctx.lineWidth = r * 0.05; ctx.beginPath(); ctx.arc(0, 0, r * 0.8, 0, Math.PI * 2); ctx.stroke();
  // reeded rim dots
  ctx.fillStyle = 'rgba(120,78,8,0.55)'; for (let i = 0; i < 40; i++) { const a = i / 40 * Math.PI * 2; ctx.beginPath(); ctx.arc(Math.cos(a) * r * 0.94, Math.sin(a) * r * 0.94, r * 0.018, 0, Math.PI * 2); ctx.fill(); }
  ctx.strokeStyle = 'rgba(110,70,6,0.9)'; ctx.lineWidth = r * 0.055;
  if (front) { // embossed globe
    ctx.beginPath(); ctx.arc(0, 0, r * 0.52, 0, Math.PI * 2); ctx.stroke();
    for (const k of [0.32, 0.72]) { ctx.beginPath(); ctx.ellipse(0, 0, r * 0.52 * k, r * 0.52, 0, 0, Math.PI * 2); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(-r * 0.52, 0); ctx.lineTo(r * 0.52, 0); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-r * 0.45, -r * 0.26); ctx.quadraticCurveTo(0, -r * 0.31, r * 0.45, -r * 0.26); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-r * 0.45, r * 0.26); ctx.quadraticCurveTo(0, r * 0.31, r * 0.45, r * 0.26); ctx.stroke();
  } else { // star
    ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.22 : r * 0.5; i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); } ctx.closePath(); ctx.stroke();
  }
  ctx.restore();
  // moving glint
  ctx.save(); ctx.beginPath(); ctx.ellipse(0, 0, r * sx, r, 0, 0, Math.PI * 2); ctx.clip();
  const gx = Math.sin(phase * 1.3) * r * sx; const gl = ctx.createLinearGradient(gx - r * 0.4, -r, gx + r * 0.4, r);
  gl.addColorStop(0, 'rgba(255,255,255,0)'); gl.addColorStop(0.5, 'rgba(255,255,240,0.38)'); gl.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gl; ctx.fillRect(-r, -r, 2 * r, 2 * r); ctx.restore();
}
const ZIG = [[0, -1.15], [0.09, -0.62], [-0.07, -0.22], [0.08, 0.2], [-0.06, 0.62], [0.02, 1.15]];
export function coin(ctx, x, y, r, phase, o = {}) {
  const a = o.alpha ?? 1; if (a <= 0.002 || r < 1) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y);
  // soft shadow
  ctx.fillStyle = 'rgba(0,0,0,0.28)'; ctx.beginPath(); ctx.ellipse(r * 0.1, r * 1.25, r * 0.85, r * 0.12, 0, 0, Math.PI * 2); ctx.fill();
  const cr = o.crack || 0;
  if (cr <= 0) coinFace(ctx, r, phase);
  else for (const side of [-1, 1]) {
    ctx.save();
    ctx.translate(side * cr * r * 0.55, cr * cr * r * 0.5); ctx.rotate(side * cr * 0.32);
    ctx.beginPath(); ctx.moveTo(side * r * 1.4, -r * 1.3);
    for (const [zx, zy] of ZIG) ctx.lineTo(zx * r, zy * r);
    ctx.lineTo(side * r * 1.4, r * 1.3); ctx.closePath(); ctx.clip();
    coinFace(ctx, r, phase);
    ctx.strokeStyle = '#5a3a05'; ctx.lineWidth = 3; ctx.beginPath(); ZIG.forEach(([zx, zy], i) => i ? ctx.lineTo(zx * r, zy * r) : ctx.moveTo(zx * r, zy * r)); ctx.stroke();
    ctx.restore();
  }
  ctx.restore();
}

// ---- rubber stamp slam (p: 0..1 slam progress) ----
export function stamp(ctx, text, x, y, p, o = {}) {
  if (p <= 0) return;
  const size = o.size || 92, col = o.color || '#FF3B3B';
  const sc = lerp(o.from ?? 2.0, 1, E.outBack(clamp(p))), a = clamp(p * 3) * (o.alpha ?? 1);
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.12); ctx.scale(sc, sc); ctx.globalAlpha *= a;
  const w = F.measure(ctx, text, { size, fam: o.fam || F.FAM.head, weight: 400, tracking: 0.04 }) + size * 0.9, h = size * 1.35;
  ctx.fillStyle = o.bg || 'rgba(20,4,4,0.55)'; F.round(ctx, -w / 2, -h / 2, w, h, size * 0.14); ctx.fill();
  ctx.strokeStyle = col; ctx.lineWidth = size * 0.075; F.round(ctx, -w / 2, -h / 2, w, h, size * 0.14); ctx.stroke();
  ctx.lineWidth = size * 0.03; F.round(ctx, -w / 2 + size * 0.13, -h / 2 + size * 0.13, w - size * 0.26, h - size * 0.26, size * 0.08); ctx.stroke();
  F.text(ctx, text, 0, 0, { size, fam: o.fam || F.FAM.head, weight: 400, tracking: 0.04, align: 'center', baseline: 'middle', color: col, shadow: false });
  ctx.restore();
}
// big red X (two strokes) slam
export function redX(ctx, x, y, s, p) {
  if (p <= 0) return;
  const sc = lerp(1.8, 1, E.outBack(clamp(p))), a = clamp(p * 3);
  ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.rotate(-0.05); ctx.globalAlpha *= a; ctx.lineCap = 'round';
  for (const [lw, col] of [[s * 0.2, 'rgba(0,0,0,0.45)'], [s * 0.13, '#FF3B3B']]) { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(-s, -s); ctx.lineTo(s, s); ctx.moveTo(s, -s); ctx.lineTo(-s, s); ctx.stroke(); }
  ctx.restore();
}

// ---- cartoon wave in local coords (travels toward +x, base on y = 0); sy squashes vertically (deflate) ----
const WAVE_TOP = [[-900, 0], [-650, -40, -420, -130, -270, -235], [-150, -330, -20, -405, 95, -385], [195, -365, 235, -292, 192, -242], [160, -205, 108, -214, 98, -252]];
export function wave(ctx, x, y, s, rot, o = {}) {
  const sy = o.sy ?? 1, a = o.alpha ?? 1; if (a <= 0.002) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s * sy); ctx.globalAlpha *= a;
  const body = () => {
    ctx.beginPath(); ctx.moveTo(-900, 0);
    for (let i = 1; i < WAVE_TOP.length; i++) { const q = WAVE_TOP[i]; ctx.bezierCurveTo(q[0], q[1], q[2], q[3], q[4], q[5]); }
    ctx.bezierCurveTo(82, -300, 22, -282, 32, -200); ctx.bezierCurveTo(42, -110, 112, -40, 205, 0); ctx.closePath();
  };
  const g = ctx.createLinearGradient(0, -400, 0, 10); g.addColorStop(0, '#8ff4ff'); g.addColorStop(0.35, '#3DE3FF'); g.addColorStop(1, '#0b4f78');
  body(); ctx.fillStyle = g; ctx.fill();
  // darker curl barrel
  ctx.fillStyle = 'rgba(8,60,95,0.55)'; ctx.beginPath(); ctx.moveTo(98, -252); ctx.bezierCurveTo(82, -300, 22, -282, 32, -200); ctx.bezierCurveTo(40, -150, 70, -120, 100, -110); ctx.bezierCurveTo(60, -170, 70, -230, 98, -252); ctx.fill();
  // stripes
  ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.lineWidth = 9;
  for (const k of [0.3, 0.55, 0.78]) { ctx.beginPath(); ctx.moveTo(-820 + k * 300, -12 - k * 40); ctx.bezierCurveTo(-600 + k * 200, -60 - k * 120, -380 + k * 150, -140 - k * 160, -210 + k * 120, -230 - k * 70); ctx.stroke(); }
  // foam line along the crest
  const foam = (lw, col) => { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-430, -120); ctx.bezierCurveTo(-330, -170, -270, -235, -270, -235); for (let i = 2; i < WAVE_TOP.length; i++) { const q = WAVE_TOP[i]; ctx.bezierCurveTo(q[0], q[1], q[2], q[3], q[4], q[5]); } ctx.stroke(); };
  foam(34, 'rgba(255,255,255,0.25)'); foam(14, '#ffffff');
  ctx.fillStyle = '#ffffff';
  const sp = o.spray ?? 0;
  for (let i = 0; i < 9; i++) { const ang = -0.9 + i * 0.22, d = 60 + (i % 3) * 38 + sp * 40; ctx.globalAlpha = a * (0.9 - i * 0.06); ctx.beginPath(); ctx.arc(190 + Math.cos(ang) * d, -300 + Math.sin(ang) * d * 0.8, 9 - (i % 3) * 2, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
// sepia wax seal (scalloped disc with a star)
export function waxSeal(ctx, x, y, r, p) {
  if (p <= 0) return;
  const sc = lerp(1.9, 1, E.outBack(clamp(p))), a = clamp(p * 3);
  ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.rotate(0.2); ctx.globalAlpha *= a;
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.arc(4, 6, r * 1.05, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); for (let i = 0; i <= 64; i++) { const ang = i / 64 * Math.PI * 2, rr = r * (1 + 0.07 * Math.sin(ang * 14)); i ? ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr) : ctx.moveTo(rr, 0); } ctx.closePath();
  const g = ctx.createRadialGradient(-r * 0.3, -r * 0.3, r * 0.1, 0, 0, r * 1.1); g.addColorStop(0, '#c48a52'); g.addColorStop(0.6, '#8f5228'); g.addColorStop(1, '#5c3015'); ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = 'rgba(60,28,8,0.8)'; ctx.lineWidth = r * 0.07; ctx.beginPath(); ctx.arc(0, 0, r * 0.68, 0, Math.PI * 2); ctx.stroke();
  ctx.strokeStyle = 'rgba(235,190,140,0.55)'; ctx.lineWidth = r * 0.06;
  ctx.beginPath(); for (let i = 0; i < 10; i++) { const ang = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.2 : r * 0.46; i ? ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr) : ctx.moveTo(Math.cos(ang) * rr, Math.sin(ang) * rr); } ctx.closePath(); ctx.stroke();
  ctx.restore();
}

// ---- paper sheets ----
export function paperCanvas(w, h, seed, o = {}) {
  const c = makeCanvas(w, h), g = c.getContext('2d'), r = F.rng(seed);
  g.fillStyle = o.color || '#efe5cf'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < w * h / 180; i++) { g.fillStyle = r() < 0.5 ? `rgba(120,95,60,${r() * 0.07})` : `rgba(255,255,255,${r() * 0.12})`; g.fillRect(r() * w, r() * h, 1 + r() * 2.5, 1 + r() * 2.5); }
  g.strokeStyle = 'rgba(130,100,60,0.05)'; g.lineWidth = 1;
  for (let i = 0; i < 160; i++) { const x = r() * w, y = r() * h, l = 10 + r() * 40, a = r() * Math.PI; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
  const vg = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.hypot(w, h) * 0.6); vg.addColorStop(0, 'rgba(120,90,50,0)'); vg.addColorStop(1, 'rgba(120,90,50,0.28)'); g.fillStyle = vg; g.fillRect(0, 0, w, h);
  if (o.coffee) {
    for (const [cx, cy, rr] of o.coffee) {
      for (let k = 0; k < 3; k++) { g.strokeStyle = `rgba(122,74,30,${0.18 + 0.08 * k})`; g.lineWidth = 3 + k * 4; g.beginPath(); g.ellipse(cx + k * 2, cy - k, rr - k * 3, rr * 0.96 - k * 3, 0.2, 0.3 + k * 0.4, Math.PI * 2 - 0.2 * k); g.stroke(); }
      const bl = g.createRadialGradient(cx, cy, 0, cx, cy, rr); bl.addColorStop(0, 'rgba(150,100,45,0.10)'); bl.addColorStop(0.8, 'rgba(150,100,45,0.05)'); bl.addColorStop(1, 'rgba(120,74,30,0.16)'); g.fillStyle = bl; g.beginPath(); g.arc(cx, cy, rr, 0, Math.PI * 2); g.fill();
    }
    g.fillStyle = 'rgba(122,74,30,0.22)'; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(o.coffee[0][0] + 120 + i * 17 + r() * 10, o.coffee[0][1] + 90 + r() * 30, 3 + r() * 5, 0, Math.PI * 2); g.fill(); }
  }
  return c;
}
// typed placeholder copy: rows of ink bars revealed up to `p` (0..1) — stands in for unreadable body text
export function inkLines(ctx, x, y, w, rows, lh, p, seed, o = {}) {
  const r = F.rng(seed); const total = rows; let shown = p * total;
  ctx.save(); ctx.fillStyle = o.color || 'rgba(45,38,30,0.55)';
  for (let i = 0; i < rows; i++) {
    let L = (i === rows - 1 ? 0.45 + r() * 0.2 : 0.86 + r() * 0.14) * w; const vis = clamp(shown - i) * L;
    let cx = x;
    while (cx < x + vis) { const ww = Math.min(26 + r() * 70, x + vis - cx); ctx.fillRect(cx, y + i * lh, ww, o.h || 9); cx += ww + 9 + r() * 4; }
  }
  ctx.restore();
}
// circular magnifier over a card canvas `src` drawn at screen rect [cx0, cy0, cw, ch]; shows it `zoom`x around the lens
export function magnifier(ctx, src, x, y, r, zoom, rect) {
  const [cx0, cy0, cw] = rect; const k = src.width / cw; // src px per screen px of the card
  const sx = (x - cx0) * k, sy = (y - cy0) * k, ss = (2 * r / zoom) * k;
  ctx.save();
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = '#e9dec6'; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
  ctx.drawImage(src, sx - ss / 2, sy - ss / 2, ss, ss, x - r, y - r, 2 * r, 2 * r);
  const gl = ctx.createRadialGradient(x - r * 0.4, y - r * 0.4, 0, x, y, r); gl.addColorStop(0, 'rgba(255,255,255,0.28)'); gl.addColorStop(0.5, 'rgba(255,255,255,0.03)'); gl.addColorStop(1, 'rgba(0,0,0,0.25)'); ctx.fillStyle = gl; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
  ctx.restore();
  ctx.save(); ctx.lineCap = 'round';
  const hx = x + r * 0.72, hy = y + r * 0.72;
  for (const [lw, col] of [[r * 0.32, 'rgba(0,0,0,0.35)'], [r * 0.22, '#3a2a1c']]) { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.moveTo(hx + r * 0.08, hy + r * 0.08); ctx.lineTo(hx + r * 0.95, hy + r * 0.95); ctx.stroke(); }
  for (const [lw, col] of [[r * 0.2, 'rgba(0,0,0,0.4)'], [r * 0.12, '#c9a35a'], [r * 0.04, '#fff1c4']]) { ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); }
  ctx.restore();
}
// cheap horizontal motion-smear for whip cuts: blits the given canvas region offset several times
export function smear(ctx, src, dx, n = 4, a = 0.22) {
  ctx.save(); for (let i = 1; i <= n; i++) { ctx.globalAlpha = a; ctx.drawImage(src, dx * i / n, 0); } ctx.restore();
}
