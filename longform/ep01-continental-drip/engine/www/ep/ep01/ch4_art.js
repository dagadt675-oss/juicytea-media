// ch4 vector art + procedural effects (all pure functions of time; no Math.random).
import * as F from '../../lib/fx.js';
const { PAL, prog, E, clamp, lerp } = F;

// ---------- deterministic particles ----------
export function particles(seed, n, gen) { const r = F.rng(seed); const out = []; for (let i = 0; i < n; i++) out.push(gen(r, i)); return out; }

// soft blob sprite (cached)
const SPR = {};
export function softSprite(key, color, size = 256, inner = 0) {
  if (SPR[key]) return SPR[key];
  const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d');
  const gr = g.createRadialGradient(size / 2, size / 2, size * inner / 2, size / 2, size / 2, size / 2);
  gr.addColorStop(0, color); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, size, size);
  return (SPR[key] = c);
}

// ---------- war smoke (rolling dark clouds from the left) ----------
const SMOKE = particles(4242, 46, (r, i) => ({ y: r() * 1.25 - 0.12, s: 0.45 + r() * 0.65, sp: 0.75 + r() * 0.6, x0: -0.25 - r() * 1.0, ph: r() * 6.28, front: i % 3 === 0 }));
export function smoke(ctx, W, H, t, t0, amt, o = {}) {
  if (amt <= 0.003) return;
  const spr = softSprite('smoke', 'rgba(26,22,19,0.92)', 256);
  const spr2 = softSprite('smoke2', 'rgba(58,50,44,0.55)', 256);
  ctx.save();
  for (const p of SMOKE) {
    if (o.front != null && p.front !== o.front) continue;
    const lt = t - t0;
    const x = (p.x0 + lt * 0.55 * p.sp) * W + Math.sin(lt * 0.6 + p.ph) * 30;
    const y = p.y * H + Math.cos(lt * 0.5 + p.ph) * 22;
    const s = p.s * H * (1 + lt * 0.08);
    ctx.globalAlpha = amt * 0.85;
    ctx.drawImage(spr, x - s / 2, y - s / 2, s, s);
    ctx.globalAlpha = amt * 0.5;
    ctx.drawImage(spr2, x - s * 0.3 + 40, y - s * 0.35, s * 0.6, s * 0.6);
  }
  ctx.restore();
}

// ---------- snow ----------
const FLAKES = particles(9191, 520, r => ({ x: r(), y: r(), sp: 0.04 + r() * 0.09, sz: 0.8 + r() * r() * 3.2, ph: r() * 6.28, d: r() }));
export function snow(ctx, W, H, t, density = 1, wind = 0.03, alpha = 1) {
  ctx.save(); ctx.fillStyle = '#ffffff';
  const n = Math.floor(FLAKES.length * clamp(density));
  for (let i = 0; i < n; i++) {
    const f = FLAKES[i];
    const y = ((f.y + t * f.sp) % 1) * (H + 40) - 20;
    const x = (((f.x + t * wind * (0.5 + f.d) + Math.sin(t * 0.8 + f.ph) * 0.006) % 1) + 1) % 1 * W;
    ctx.globalAlpha = alpha * (0.35 + 0.65 * f.d);
    ctx.beginPath(); ctx.arc(x, y, f.sz * (0.6 + f.d), 0, 6.283); ctx.fill();
  }
  ctx.restore();
}

// ---------- envelope with heart wax seal ----------
export function envelope(ctx, x, y, w, rot, a = 1) {
  if (a <= 0) return;
  const h = w * 0.62;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, -w / 2 + 10, -h / 2 + 16, w, h, 10); ctx.fill();
  const gr = ctx.createLinearGradient(0, -h / 2, 0, h / 2); gr.addColorStop(0, '#F6EEDC'); gr.addColorStop(1, '#E3D5B6');
  ctx.fillStyle = gr; F.round(ctx, -w / 2, -h / 2, w, h, 8); ctx.fill();
  ctx.strokeStyle = 'rgba(120,96,60,0.55)'; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.moveTo(-w / 2 + 6, -h / 2 + 6); ctx.lineTo(0, h * 0.08); ctx.lineTo(w / 2 - 6, -h / 2 + 6); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-w / 2 + 6, h / 2 - 6); ctx.lineTo(-w * 0.12, -h * 0.02); ctx.moveTo(w / 2 - 6, h / 2 - 6); ctx.lineTo(w * 0.12, -h * 0.02); ctx.stroke();
  // heart seal
  const r = w * 0.085; ctx.translate(0, h * 0.06);
  ctx.fillStyle = '#B3242B'; ctx.beginPath(); ctx.arc(0, 0, r * 1.45, 0, 6.283); ctx.fill();
  ctx.fillStyle = '#E2453F'; ctx.beginPath();
  ctx.moveTo(0, r * 0.75); ctx.bezierCurveTo(-r * 1.3, -r * 0.1, -r * 0.6, -r * 1.05, 0, -r * 0.4); ctx.bezierCurveTo(r * 0.6, -r * 1.05, r * 1.3, -r * 0.1, 0, r * 0.75); ctx.fill();
  ctx.restore();
}

// ---------- hardcover book ----------
export function book(ctx, x, y, w, rot, col, a = 1, o = {}) {
  if (a <= 0) return;
  const h = w * 1.35;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; F.round(ctx, -w / 2 + w * 0.05, -h / 2 + w * 0.07, w, h, w * 0.05); ctx.fill();
  ctx.fillStyle = '#EDE3CC'; F.round(ctx, -w / 2 + w * 0.06, -h / 2 + w * 0.03, w * 0.98, h * 0.97, w * 0.03); ctx.fill(); // pages
  ctx.fillStyle = col; F.round(ctx, -w / 2, -h / 2, w * 0.97, h, w * 0.05); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(-w / 2, -h / 2, w * 0.12, h);
  ctx.fillStyle = o.gold || 'rgba(255,214,120,0.85)';
  ctx.fillRect(-w * 0.25, -h * 0.28, w * 0.6, h * 0.045); ctx.fillRect(-w * 0.18, -h * 0.18, w * 0.46, h * 0.03);
  ctx.strokeStyle = o.gold || 'rgba(255,214,120,0.6)'; ctx.lineWidth = Math.max(1.5, w * 0.012);
  F.round(ctx, -w * 0.36, -h * 0.42, w * 0.78, h * 0.84, w * 0.03); ctx.stroke();
  ctx.restore();
}

// rubber stamp (rotated, double border)
export function rubberStamp(ctx, x, y, lines, color, t, at, o = {}) {
  if (t < at) return;
  const p = prog(t, at, at + 0.16, E.outExpo);
  const sc = lerp(o.from || 2.3, 1, p), a = clamp((t - at) / 0.06);
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.16); ctx.scale(sc, sc); ctx.globalAlpha *= a;
  const w = o.w || 560, h = o.h || 250;
  ctx.strokeStyle = color; ctx.lineWidth = 9; F.round(ctx, -w / 2, -h / 2, w, h, 26); ctx.stroke();
  ctx.lineWidth = 3; F.round(ctx, -w / 2 + 16, -h / 2 + 16, w - 32, h - 32, 16); ctx.stroke();
  ctx.save(); ctx.globalAlpha *= 0.12; ctx.fillStyle = color; F.round(ctx, -w / 2, -h / 2, w, h, 26); ctx.fill(); ctx.restore();
  F.text(ctx, lines[0], 0, -h * 0.17, { size: 44, fam: F.FAM.label, weight: 800, tracking: 0.28, align: 'center', color, shadow: false });
  F.text(ctx, lines[1], 0, h * 0.36, { size: 150, fam: F.FAM.head, weight: 400, tracking: 0.06, align: 'center', color, shadow: false });
  ctx.restore();
}

// ---------- cartoon fingertip (top view, pointing right) ----------
export function finger(ctx, x, y, s, nail, rot = 0, a = 1) {
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.lineJoin = 'round';
  // finger body
  const gr = ctx.createLinearGradient(0, -75, 0, 75); gr.addColorStop(0, '#F3C7A3'); gr.addColorStop(0.55, '#E2A57E'); gr.addColorStop(1, '#C98762');
  ctx.fillStyle = gr; F.round(ctx, -330, -74, 520, 148, 74); ctx.fill();
  ctx.strokeStyle = '#7A4A30'; ctx.lineWidth = 7; F.round(ctx, -330, -74, 520, 148, 74); ctx.stroke();
  // knuckle creases
  ctx.strokeStyle = 'rgba(122,74,48,0.55)'; ctx.lineWidth = 5;
  for (const kx of [-190, -70]) { ctx.beginPath(); ctx.moveTo(kx, -40); ctx.quadraticCurveTo(kx - 14, 0, kx, 40); ctx.stroke(); }
  // free edge (white tip) grows past the fingertip
  const e = 8 + nail * 70;
  ctx.fillStyle = '#FFF7EC'; ctx.strokeStyle = '#7A4A30'; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(150, -46); ctx.lineTo(176 + e - 30, -46); ctx.quadraticCurveTo(176 + e + 6, -40, 176 + e + 6, 0); ctx.quadraticCurveTo(176 + e + 6, 40, 176 + e - 30, 46); ctx.lineTo(150, 46); ctx.closePath(); ctx.fill(); ctx.stroke();
  // nail plate
  const ng = ctx.createLinearGradient(0, -50, 0, 50); ng.addColorStop(0, '#FBDCD3'); ng.addColorStop(1, '#EDB1A6');
  ctx.fillStyle = ng; F.round(ctx, 30, -52, 150, 104, 46); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.beginPath(); ctx.ellipse(52, 0, 18, 38, 0, 0, 6.283); ctx.fill(); // lunula
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; F.round(ctx, 60, -40, 100, 14, 7); ctx.fill(); // gloss
  ctx.restore();
  return 176 + e + 6; // tip x in local units
}

// ---------- cartoon foot (side view, toes pointing left) ----------
export function foot(ctx, x, y, s, nail, rot = 0, a = 1) {
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.lineJoin = 'round';
  const gr = ctx.createLinearGradient(0, -220, 0, 100); gr.addColorStop(0, '#F3C7A3'); gr.addColorStop(0.6, '#E2A57E'); gr.addColorStop(1, '#C27E5A');
  ctx.fillStyle = gr; ctx.strokeStyle = '#7A4A30'; ctx.lineWidth = 7;
  ctx.beginPath();
  ctx.moveTo(250, 90);
  ctx.bezierCurveTo(120, 102, 10, 62, -150, 84);
  ctx.bezierCurveTo(-232, 94, -282, 82, -282, 46);
  ctx.bezierCurveTo(-282, 12, -256, -4, -214, -6);
  ctx.bezierCurveTo(-150, -14, -86, -44, -20, -96);
  ctx.lineTo(52, -230); ctx.lineTo(196, -230);
  ctx.bezierCurveTo(200, -120, 300, -50, 292, 30);
  ctx.bezierCurveTo(288, 74, 276, 90, 250, 90);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  // little toes bumps
  ctx.strokeStyle = 'rgba(122,74,48,0.6)'; ctx.lineWidth = 5;
  for (const [bx, by] of [[-200, 40], [-168, 50], [-140, 58]]) { ctx.beginPath(); ctx.arc(bx, by, 16, Math.PI * 0.9, Math.PI * 1.9); ctx.stroke(); }
  // ankle bone
  ctx.beginPath(); ctx.arc(170, -110, 18, 0.3, 2.6); ctx.stroke();
  // toenail (big toe, top) + growing free edge to the left
  const e = 6 + nail * 46;
  ctx.fillStyle = '#FFF7EC'; ctx.strokeStyle = '#7A4A30'; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(-232, -12); ctx.lineTo(-262 - e + 14, -12); ctx.quadraticCurveTo(-266 - e, -6, -262 - e + 10, 8); ctx.lineTo(-232, 8); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#F2C4B8'; F.round(ctx, -262, -22, 72, 26, 12); ctx.fill(); ctx.stroke();
  ctx.restore();
}

// ---------- needle gauge ----------
export function gauge(ctx, cx, cy, r, val, a = 1, label = 'FORCE') {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.fillStyle = 'rgba(6,9,16,0.78)'; F.round(ctx, cx - r - 50, cy - r - 50, 2 * r + 100, r + 150, 26); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 2; F.round(ctx, cx - r - 50, cy - r - 50, 2 * r + 100, r + 150, 26); ctx.stroke();
  // coloured arc zones
  const zones = [[0, 0.35, '#3A4658'], [0.35, 0.7, '#6C7A8F'], [0.7, 1, PAL.hero]];
  ctx.lineWidth = r * 0.16; ctx.lineCap = 'butt';
  for (const [a0, a1, c] of zones) { ctx.strokeStyle = c; ctx.beginPath(); ctx.arc(cx, cy, r * 0.86, Math.PI + a0 * Math.PI, Math.PI + a1 * Math.PI - 0.01); ctx.stroke(); }
  // ticks
  ctx.strokeStyle = 'rgba(244,246,250,0.8)'; ctx.lineWidth = 3;
  for (let i = 0; i <= 10; i++) { const an = Math.PI + i / 10 * Math.PI, r0 = r * (i % 5 === 0 ? 0.62 : 0.68), r1 = r * 0.74; ctx.beginPath(); ctx.moveTo(cx + Math.cos(an) * r0, cy + Math.sin(an) * r0); ctx.lineTo(cx + Math.cos(an) * r1, cy + Math.sin(an) * r1); ctx.stroke(); }
  // needle
  const an = Math.PI + clamp(val, -0.02, 1.02) * Math.PI;
  ctx.strokeStyle = PAL.yellow; ctx.lineWidth = 9; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx - Math.cos(an) * r * 0.12, cy - Math.sin(an) * r * 0.12); ctx.lineTo(cx + Math.cos(an) * r * 0.8, cy + Math.sin(an) * r * 0.8); ctx.stroke();
  ctx.fillStyle = '#F4F6FA'; ctx.beginPath(); ctx.arc(cx, cy, r * 0.09, 0, 6.283); ctx.fill();
  F.text(ctx, label, cx, cy + r * 0.42, { size: 46, fam: F.FAM.label, weight: 800, tracking: 0.3, align: 'center', color: PAL.text, shadow: false });
  ctx.restore();
}

// ---------- a big bobbing question mark ----------
export function bigQ(ctx, x, y, t, at, size = 300, a = 1, color = PAL.yellow) {
  if (t < at) return;
  const p = prog(t, at, at + 0.45, E.outBack);
  const sc = Math.max(0.01, p), bob = Math.sin((t - at) * 2.4) * 10;
  ctx.save(); ctx.globalAlpha *= a * clamp((t - at) / 0.12); ctx.translate(x, y + bob); ctx.scale(sc, sc); ctx.rotate(Math.sin((t - at) * 1.7) * 0.05);
  F.text(ctx, '?', 0, size * 0.36, { size, fam: F.FAM.head, weight: 400, align: 'center', color, shadowBlur: size * 0.15, stroke: size * 0.035, strokeColor: 'rgba(10,12,18,0.9)' });
  ctx.restore();
}
