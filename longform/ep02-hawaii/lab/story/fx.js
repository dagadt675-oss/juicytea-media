// 2D motion-graphics primitives for the compositor canvas (deterministic: everything is a function of time).
export const PAL = {
  space: '#05070D', ocean: '#0A1A2E', shelf: '#12385A', hero: '#FF5A36', cyan: '#3DE3FF', yellow: '#FFD23F',
  text: '#F4F6FA', sub: '#9AA7B8', ink: '#0B0F16', danger: '#FF3B3B', green: '#46E08A',
};
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const E = {
  lin: t => t,
  inOut: t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
  outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
};
// progress of t within [a, b], eased
export const prog = (t, a, b, ease = E.inOut) => ease(clamp((t - a) / Math.max(1e-6, b - a)));
// envelope: fade in over [a, a+fi], hold, fade out over [b-fo, b]
export const env = (t, a, b, fi = 0.35, fo = 0.35) => clamp(Math.min((t - a) / fi, (b - t) / fo));

export function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

export function font(weight, size, fam) { return `${weight} ${size}px "${fam}"`; }
const FAM = { head: 'Bebas Neue', label: 'Barlow Condensed', body: 'Inter', mono: 'JetBrains Mono', serif: 'Playfair Display', black: 'Anton' };
export { FAM };

// text with letter-spacing (tracking in em) and optional stroke/shadow. Rendered once into a cached sprite
// (shadow blur is expensive in software canvas), then blitted.
const TCACHE = new Map();
function textSprite(s, o) {
  const size = o.size || 48, fam = o.fam || FAM.body, w = o.weight || 700, tr = (o.tracking || 0) * size;
  const shadow = o.shadow !== false;
  const sb = shadow ? (o.shadowBlur ?? size * 0.25) : 0, sy = shadow ? (o.shadowY ?? size * 0.04) : 0;
  const key = [s, size, fam, w, tr, o.color, o.stroke, o.strokeColor, shadow, sb, sy, o.shadowColor].join('|');
  let sp = TCACHE.get(key);
  if (sp) return sp;
  const m = document.createElement('canvas').getContext('2d');
  m.font = font(w, size, fam);
  let width = 0; for (const ch of s) width += m.measureText(ch).width; width = tr ? width + tr * (s.length - 1) : m.measureText(s).width;
  const pad = Math.ceil(sb * 2 + (o.stroke || 0) + size * 0.1);
  const c = document.createElement('canvas'); c.width = Math.ceil(width + pad * 2); c.height = Math.ceil(size * 1.45 + pad * 2);
  const g = c.getContext('2d'); g.font = font(w, size, fam); g.textBaseline = 'alphabetic';
  const by = pad + size * 1.05;
  if (shadow) { g.shadowColor = o.shadowColor || 'rgba(0,0,0,0.55)'; g.shadowBlur = sb; g.shadowOffsetY = sy; }
  g.fillStyle = o.color || PAL.text;
  const drawStr = (fn) => { if (!tr) fn(s, pad); else { let cx = pad; for (const ch of s) { fn(ch, cx); cx += g.measureText(ch).width + tr; } } };
  if (o.stroke) { g.lineWidth = o.stroke; g.strokeStyle = o.strokeColor || 'rgba(0,0,0,0.8)'; g.lineJoin = 'round'; drawStr((ch, x) => g.strokeText(ch, x, by)); }
  drawStr((ch, x) => g.fillText(ch, x, by));
  sp = { c, width, pad, by };
  if (TCACHE.size > 4000) TCACHE.clear();
  TCACHE.set(key, sp);
  return sp;
}
export function text(ctx, s, x, y, o = {}) {
  if (!s) return 0;
  const sp = textSprite(s, o);
  let x0 = x; if (o.align === 'center') x0 = x - sp.width / 2; else if (o.align === 'right') x0 = x - sp.width;
  let y0 = y; if (o.baseline === 'middle') y0 = y + (o.size || 48) * 0.36; else if (o.baseline === 'top') y0 = y + (o.size || 48) * 0.8;
  const a = (o.alpha ?? 1);
  if (a <= 0.002) return sp.width;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.drawImage(sp.c, x0 - sp.pad, y0 - sp.by);
  ctx.restore();
  return sp.width;
}
export function measure(ctx, s, o = {}) { ctx.save(); ctx.font = font(o.weight || 700, o.size || 48, o.fam || FAM.body); const w = ctx.measureText(s).width + (o.tracking || 0) * (o.size || 48) * (s.length - 1); ctx.restore(); return w; }

// Animated headline: words rise in one by one; accent words coloured. p = 0..1 in-progress, q = 0..1 out-progress
export function headline(ctx, words, x, y, t, o = {}) {
  const size = o.size || 120, fam = o.fam || FAM.head, gap = size * 0.28, per = o.per ?? 0.09;
  const ws = words.map(w => typeof w === 'string' ? { w } : w);
  const widths = ws.map(w => measure(ctx, w.w, { size, fam, weight: o.weight || 400, tracking: o.tracking || 0.02 }));
  const total = widths.reduce((a, b) => a + b, 0) + gap * (ws.length - 1);
  let cx = o.align === 'left' ? x : x - total / 2;
  ws.forEach((w, i) => {
    const p = prog(t, (o.t0 || 0) + i * per, (o.t0 || 0) + i * per + 0.45, E.outExpo);
    const out = o.tOut != null ? prog(t, o.tOut, o.tOut + 0.35, E.in) : 0;
    const a = p * (1 - out);
    if (a > 0.001) {
      ctx.save();
      const sc = lerp(1.12, 1, p);
      ctx.translate(cx + widths[i] / 2, y);
      ctx.scale(sc, sc);
      text(ctx, w.w, 0, (1 - p) * size * 0.18 - out * size * 0.1, { size, fam, weight: o.weight || 400, tracking: o.tracking || 0.02, align: 'center', color: w.c || o.color || PAL.text, alpha: a, shadowBlur: size * 0.35 });
      ctx.restore();
    }
    cx += widths[i] + gap;
  });
}

// pill label with optional leader line to an anchor point
export function pill(ctx, s, x, y, o = {}) {
  const size = o.size || 32, padX = size * 0.55, padY = size * 0.32, a = o.alpha ?? 1;
  if (a <= 0.001) return;
  const w = measure(ctx, s, { size, fam: o.fam || FAM.label, weight: o.weight || 700, tracking: o.tracking ?? 0.08 });
  const bw = w + padX * 2, bh = size + padY * 2;
  let bx = x, by = y;
  if (o.anchor === 'center') { bx = x - bw / 2; by = y - bh / 2; } else if (o.anchor === 'right') { bx = x - bw; by = y - bh / 2; } else if (o.anchor === 'left') { by = y - bh / 2; }
  ctx.save(); ctx.globalAlpha *= a;
  if (o.leader) {
    const [lx, ly] = o.leader; ctx.strokeStyle = o.lineColor || 'rgba(244,246,250,0.85)'; ctx.lineWidth = 2;
    const ex = clamp(lx, bx, bx + bw), ey = clamp(ly, by, by + bh);
    ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(lx, ly); ctx.stroke();
    dot(ctx, lx, ly, { r: 6, color: o.dotColor || PAL.text, ring: o.ring });
  }
  ctx.fillStyle = 'rgba(0,0,0,0.22)'; round(ctx, bx - 3, by - 1, bw + 6, bh + 8, (o.radius ?? bh / 2) + 3); ctx.fill();
  ctx.fillStyle = o.bg || 'rgba(8,11,18,0.72)';
  round(ctx, bx, by, bw, bh, o.radius ?? bh / 2); ctx.fill();
  if (o.border) { ctx.strokeStyle = o.border; ctx.lineWidth = 2; round(ctx, bx, by, bw, bh, o.radius ?? bh / 2); ctx.stroke(); }
  text(ctx, s, bx + padX, by + bh / 2 + size * 0.36, { size, fam: o.fam || FAM.label, weight: o.weight || 700, tracking: o.tracking ?? 0.08, color: o.color || PAL.text, shadow: false });
  ctx.restore();
  return { x: bx, y: by, w: bw, h: bh };
}
export function round(ctx, x, y, w, h, r) { r = Math.min(r, w / 2, h / 2); ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
export function dot(ctx, x, y, o = {}) {
  ctx.save(); const r = o.r || 6;
  if (o.ring != null) { const k = ((o.ring % 1) + 1) % 1; ctx.strokeStyle = o.color || PAL.text; ctx.globalAlpha *= (1 - k); ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, r + k * r * 5, 0, Math.PI * 2); ctx.stroke(); ctx.globalAlpha /= Math.max(1e-3, 1 - k); }
  const gg = ctx.createRadialGradient(x, y, 0, x, y, r * 3.2); gg.addColorStop(0, (o.glow || o.color || PAL.text)); gg.addColorStop(0.3, 'rgba(255,255,255,0.25)'); gg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.globalAlpha *= 0.6; ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(x, y, r * 3.2, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha /= 0.6;
  ctx.fillStyle = o.color || PAL.text; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}

// Rolling counter with tabular digits. value displayed = lerp(from, to, eased p). fmt: 'int' | 'comma' | decimals
export function counter(ctx, from, to, p, x, y, o = {}) {
  const v = lerp(from, to, p);
  let s;
  if (o.format) s = o.format(v);
  else { const d = o.decimals || 0; s = v.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); }
  const size = o.size || 140, fam = o.fam || FAM.body, weight = o.weight || 800;
  ctx.save(); ctx.font = font(weight, size, fam);
  const dw = ctx.measureText('0').width;
  const chars = [...(o.prefix || ''), ...s];
  const widths = chars.map(c => /[0-9]/.test(c) ? dw : ctx.measureText(c).width);
  const unitSize = size * 0.42;
  ctx.font = font(o.unitWeight || 700, unitSize, o.unitFam || FAM.label);
  const uw = o.unit ? ctx.measureText(o.unit).width + size * 0.12 : 0;
  const total = widths.reduce((a, b) => a + b, 0) + uw;
  let cx = o.align === 'left' ? x : o.align === 'right' ? x - total : x - total / 2;
  ctx.restore();
  chars.forEach((c, i) => { text(ctx, c, cx + widths[i] / 2, y, { size, fam, weight, align: 'center', color: o.color || PAL.text, alpha: o.alpha ?? 1, shadowBlur: size * 0.3 }); cx += widths[i]; });
  if (o.unit) text(ctx, o.unit, cx + size * 0.12, y, { size: unitSize, fam: o.unitFam || FAM.label, weight: o.unitWeight || 700, color: o.unitColor || PAL.sub, alpha: o.alpha ?? 1, tracking: 0.06 });
  return total;
}

// glowing polyline (array of [x,y]); draw only the first `p` fraction of its length (draw-on)
export function glowPath(ctx, pts, o = {}) {
  if (pts.length < 2) return;
  const p = o.p ?? 1;
  let L = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  const target = L * clamp(p);
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const pass = (lw, col, blur) => {
    ctx.strokeStyle = col; ctx.lineWidth = lw;
    if (o.dash) ctx.setLineDash(o.dash); else ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    let acc = 0;
    for (let i = 1; i < pts.length; i++) {
      if (acc + seg[i - 1] >= target) { const k = (target - acc) / seg[i - 1]; ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)); break; }
      ctx.lineTo(pts[i][0], pts[i][1]); acc += seg[i - 1];
    }
    ctx.stroke();
  };
  const gc = o.glowColor || o.color || PAL.cyan;
  pass((o.width || 4) * 5, gc + '14', 0);
  pass((o.width || 4) * 2.6, gc + '33', 0);
  pass(o.width || 4, o.color || PAL.cyan, 0);
  ctx.restore();
  // head position
  let acc = 0; for (let i = 1; i < pts.length; i++) { if (acc + seg[i - 1] >= target) { const k = (target - acc) / seg[i - 1]; return [lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]; } acc += seg[i - 1]; }
  return pts[pts.length - 1];
}

// image with Ken Burns (from/to rect in normalised coords of the image: [cx, cy, zoom]); framed or full-bleed
export function kenburns(ctx, img, t, x, y, w, h, o = {}) {
  if (!img) return;
  const from = o.from || [0.5, 0.5, 1.0], to = o.to || [0.5, 0.5, 1.12];
  const k = (o.ease || E.inOutSine)(clamp(t));
  const cxn = lerp(from[0], to[0], k), cyn = lerp(from[1], to[1], k), z = lerp(from[2], to[2], k);
  const ar = w / h, iar = img.width / img.height;
  let sw, sh; if (iar > ar) { sh = img.height / z; sw = sh * ar; } else { sw = img.width / z; sh = sw / ar; }
  let sx = cxn * img.width - sw / 2, sy = cyn * img.height - sh / 2;
  sx = clamp(sx, 0, img.width - sw); sy = clamp(sy, 0, img.height - sh);
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  if (o.frame) {
    for (let k = 4; k >= 1; k--) { ctx.fillStyle = `rgba(0,0,0,${0.10})`; round(ctx, x - k * 6, y - k * 4 + 10, w + k * 12, h + k * 10, (o.radius ?? 14) + k * 6); ctx.fill(); }
    round(ctx, x, y, w, h, o.radius ?? 14); ctx.clip();
  }
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  if (o.grade) grade(ctx, x, y, w, h, o.grade);
  ctx.restore();
}
// split-tone grade over a rect: 'teal' | 'sepia' | 'cold'
export function grade(ctx, x, y, w, h, kind) {
  ctx.save();
  if (kind === 'sepia') { ctx.globalCompositeOperation = 'color'; ctx.fillStyle = 'rgba(160,120,70,0.55)'; ctx.fillRect(x, y, w, h); }
  if (kind === 'teal') { ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = 'rgba(20,90,110,0.45)'; ctx.fillRect(x, y, w, h); }
  if (kind === 'cold') { ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = 'rgba(40,80,160,0.5)'; ctx.fillRect(x, y, w, h); }
  ctx.restore();
}

// post: vignette + film grain (grain tiles pre-generated, offset per frame deterministically)
let GRAIN = null;
function makeGrain() {
  const c = document.createElement('canvas'); c.width = c.height = 512; const g = c.getContext('2d');
  const id = g.createImageData(512, 512); const r = rng(1234);
  for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (r() + r() + r() - 1.5) * 70; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0); return c;
}
export function post(ctx, W, H, f, o = {}) {
  ctx.save();
  // vignette
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${o.vignette ?? 0.55})`);
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  // grain
  if ((o.grain ?? 0) > 0) {
    if (!GRAIN) GRAIN = makeGrain();
    const r = rng(f * 7919 + 17); const ox = Math.floor(r() * 512), oy = Math.floor(r() * 512);
    ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = o.grain ?? 0.06;
    for (let y = -oy; y < H; y += 512) for (let x = -ox; x < W; x += 512) ctx.drawImage(GRAIN, x, y);
  }
  ctx.restore();
}

// letterboxed chapter card over the current frame: big index + title
export function chapterCard(ctx, W, H, t, dur, idx, title, o = {}) {
  const a = env(t, 0, dur, 0.4, 0.45);
  if (a <= 0) return;
  ctx.save();
  ctx.fillStyle = `rgba(3,5,10,${0.62 * a})`; ctx.fillRect(0, 0, W, H);
  const p = prog(t, 0.05, 0.8, E.outExpo);
  const lineW = 420 * p;
  ctx.globalAlpha = a;
  ctx.fillStyle = o.accent || PAL.hero; ctx.fillRect(W / 2 - lineW / 2, H / 2 + 26, lineW, 4);
  text(ctx, idx, W / 2, H / 2 - 150, { size: 46, fam: FAM.label, weight: 700, tracking: 0.35, align: 'center', color: o.accent || PAL.hero, alpha: p });
  headline(ctx, title.split(' '), W / 2, H / 2 + 2, t, { size: 132, per: 0.07, t0: 0.12, tOut: dur - 0.45 });
  ctx.restore();
}
