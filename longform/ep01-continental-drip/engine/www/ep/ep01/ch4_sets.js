// ch4 2.5D "sets" drawn with a tiny pinhole projection on the 2D canvas:
//  - corridor of university doors (s060)  - magnetic seafloor block (s067-s068)
import * as F from '../../lib/fx.js';
import { particles, softSprite } from './ch4_art.js';
const { PAL, prog, E, clamp, lerp } = F;

// ---------- generic look-at camera ----------
function camera(pos, target, fov, W, H) {
  const f = [target[0] - pos[0], target[1] - pos[1], target[2] - pos[2]]; const fl = Math.hypot(...f); f[0] /= fl; f[1] /= fl; f[2] /= fl;
  let r = [f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0]; // f x up(0,1,0)
  r = [-f[2], 0, f[0]]; const rl = Math.hypot(...r) || 1; r[0] /= rl; r[2] /= rl;
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  const foc = H / 2 / Math.tan(fov * Math.PI / 360);
  return {
    depth(p) { return (p[0] - pos[0]) * f[0] + (p[1] - pos[1]) * f[1] + (p[2] - pos[2]) * f[2]; },
    proj(p) {
      const v = [p[0] - pos[0], p[1] - pos[1], p[2] - pos[2]];
      const zc = v[0] * f[0] + v[1] * f[1] + v[2] * f[2], xc = v[0] * r[0] + v[1] * r[1] + v[2] * r[2], yc = v[0] * u[0] + v[1] * u[1] + v[2] * u[2];
      return [W / 2 + foc * xc / zc, H / 2 - foc * yc / zc, zc];
    },
    foc,
  };
}
// fill a 3D polygon with near-plane clipping
function poly3(ctx, cam, pts, near = 0.06) {
  const out = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length], da = cam.depth(a), db = cam.depth(b);
    if (da >= near) out.push(a);
    if ((da >= near) !== (db >= near)) { const k = (da - near) / (da - db); out.push([a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]); }
  }
  if (out.length < 3) return false;
  ctx.beginPath(); out.forEach((p, i) => { const q = cam.proj(p); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.closePath();
  return true;
}
function line3(ctx, cam, a, b, near = 0.06) {
  let da = cam.depth(a), db = cam.depth(b);
  if (da < near && db < near) return;
  if (da < near) { const k = (near - da) / (db - da); a = [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]; }
  if (db < near) { const k = (near - db) / (da - db); b = [b[0] + (a[0] - b[0]) * k, b[1] + (a[1] - b[1]) * k, b[2] + (a[2] - b[2]) * k]; }
  const p = cam.proj(a), q = cam.proj(b); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]);
}
const hex = (c) => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
const mix = (a, b, k) => { const A = hex(a), B = hex(b); return `rgb(${Math.round(lerp(A[0], B[0], k))},${Math.round(lerp(A[1], B[1], k))},${Math.round(lerp(A[2], B[2], k))})`; };

// =====================================================================================
// CORRIDOR: three German doors slam shut, the far (Austrian) door opens onto warm light.
// o = {t0, slams:[t,t,t], open, pushAt, pushEnd}
// =====================================================================================
export function corridor(ctx, W, H, t, o) {
  const XW = 2.2, YH = 3.8, ZN = 5, ZF = -18;
  // camera dolly + push through the far door
  let cz = lerp(3.4, 0.4, prog(t, o.t0, o.pushAt, E.inOut));
  cz = lerp(cz, -16.9, prog(t, o.pushAt, o.pushEnd, E.in));
  let sx = 0, sy = 0;
  for (const ts of o.slams) if (t > ts) { const k = t - ts; sy += 0.05 * Math.exp(-k * 9) * Math.sin(k * 70); sx += 0.025 * Math.exp(-k * 9) * Math.cos(k * 55); }
  const cam = camera([sx, 1.55 + sy, cz], [sx * 0.5, 1.5 + sy, cz - 10], 64, W, H);
  // background
  ctx.fillStyle = '#07080B'; ctx.fillRect(0, 0, W, H);
  const fogC = '#0A0B0F';
  const shade = (base, z) => mix(base, fogC, clamp(1 - Math.exp(-Math.max(0, cz - z) / 8.5)));
  // far wall + door
  const openP = prog(t, o.open, o.open + 0.55, E.out);
  // warm light behind the far door
  ctx.save();
  if (poly3(ctx, cam, [[-0.9, 0, ZF - 0.01], [0.9, 0, ZF - 0.01], [0.9, 2.9, ZF - 0.01], [-0.9, 2.9, ZF - 0.01]])) {
    const c = cam.proj([0, 1.4, ZF]); const rr = cam.foc * 2.2 / Math.max(0.3, cam.depth([0, 1.4, ZF]));
    const gr = ctx.createRadialGradient(c[0], c[1], 0, c[0], c[1], rr); gr.addColorStop(0, '#FFF1D0'); gr.addColorStop(0.5, '#FFC46E'); gr.addColorStop(1, '#C8652A');
    ctx.fillStyle = openP > 0 ? gr : '#100C08'; ctx.fill();
  }
  ctx.restore();
  // far wall with hole for the door (even-odd)
  {
    const pts = [[-XW, 0, ZF], [XW, 0, ZF], [XW, YH, ZF], [-XW, YH, ZF]];
    const hole = [[-0.9, 0, ZF], [-0.9, 2.9, ZF], [0.9, 2.9, ZF], [0.9, 0, ZF]];
    if (cam.depth([0, 0, ZF]) > 0.1) {
      ctx.beginPath(); [pts, hole].forEach(P => P.forEach((p, i) => { const q = cam.proj(p); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }));
      ctx.fillStyle = shade('#4A4239', ZF); ctx.fill('evenodd');
      // trim
      ctx.beginPath(); line3(ctx, cam, [-1.05, 0, ZF + 0.01], [-1.05, 3.05, ZF + 0.01]); line3(ctx, cam, [-1.05, 3.05, ZF + 0.01], [1.05, 3.05, ZF + 0.01]); line3(ctx, cam, [1.05, 3.05, ZF + 0.01], [1.05, 0, ZF + 0.01]);
      ctx.strokeStyle = shade('#9C8E7A', ZF); ctx.lineWidth = Math.max(2, cam.foc * 0.12 / cam.depth([0, 0, ZF])); ctx.stroke();
      // Austrian flag (red-white-red)
      [['#ED2939', 3.55, 3.4], ['#F4F4F4', 3.4, 3.25], ['#ED2939', 3.25, 3.1]].forEach(([c, y0, y1]) => { if (poly3(ctx, cam, [[-0.5, y1, ZF + 0.02], [0.5, y1, ZF + 0.02], [0.5, y0, ZF + 0.02], [-0.5, y0, ZF + 0.02]])) { ctx.fillStyle = shade(c, ZF + 6); ctx.fill(); } });
    }
    // far double door leaves swinging away from us
    const be = openP * 1.75;
    for (const sgn of [-1, 1]) {
      const hx = sgn * 0.9, ex = hx - sgn * 0.9 * Math.cos(be), ez = ZF - 0.9 * Math.sin(be);
      if (poly3(ctx, cam, [[hx, 0, ZF], [ex, 0, ez], [ex, 2.9, ez], [hx, 2.9, ZF]])) { ctx.fillStyle = shade(openP > 0 ? '#7A4E2C' : '#6A4426', ZF); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 2; ctx.stroke(); }
    }
  }
  // corridor surfaces in depth strips (far -> near)
  for (let z = ZF; z < ZN; z += 1) {
    const z1 = z + 1, zm = z + 0.5;
    if (poly3(ctx, cam, [[-XW, 0, z], [XW, 0, z], [XW, 0, z1], [-XW, 0, z1]])) { ctx.fillStyle = shade((Math.floor(z) & 1) ? '#2E2823' : '#352E28', zm); ctx.fill(); }
    if (poly3(ctx, cam, [[-XW, YH, z], [XW, YH, z], [XW, YH, z1], [-XW, YH, z1]])) { ctx.fillStyle = shade('#1B1712', zm); ctx.fill(); }
    if (poly3(ctx, cam, [[-XW, 0, z], [-XW, YH, z], [-XW, YH, z1], [-XW, 0, z1]])) { ctx.fillStyle = shade('#4C443B', zm); ctx.fill(); }
    if (poly3(ctx, cam, [[XW, 0, z], [XW, YH, z], [XW, YH, z1], [XW, 0, z1]])) { ctx.fillStyle = shade('#463E36', zm); ctx.fill(); }
  }
  // floor tile lines + wainscot line
  ctx.beginPath();
  for (let x = -XW + 0.55; x < XW; x += 0.55) line3(ctx, cam, [x, 0.001, ZF], [x, 0.001, ZN]);
  for (const s of [-1, 1]) line3(ctx, cam, [s * XW, 1.0, ZF], [s * XW, 1.0, ZN]);
  ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 2; ctx.stroke();
  // warm light spill on the floor from the far door
  if (openP > 0) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    if (poly3(ctx, cam, [[-0.9, 0.002, ZF], [0.9, 0.002, ZF], [2.0, 0.002, ZF + 9], [-2.0, 0.002, ZF + 9]])) {
      const a = cam.proj([0, 0, ZF]), b = cam.proj([0, 0, ZF + 9]);
      const gr = ctx.createLinearGradient(a[0], a[1], b[0], b[1]); gr.addColorStop(0, `rgba(255,190,110,${0.45 * openP})`); gr.addColorStop(1, 'rgba(255,170,90,0)');
      ctx.fillStyle = gr; ctx.fill();
    }
    ctx.restore();
  }
  // side doors (German flags): [side, zc, slamTime]
  const doors = [[-1, -3.0, o.slams[0]], [1, -6.6, o.slams[1]], [-1, -10.2, o.slams[2]]];
  const sorted = doors.slice().sort((a, b) => a[1] - b[1]); // far first
  for (const [s, zc, ts] of sorted) {
    const X = s * XW, X1 = s * (XW - 0.002);
    // stone frame
    if (poly3(ctx, cam, [[X1, 0, zc - 0.78], [X1, 2.75, zc - 0.78], [X1, 2.75, zc + 0.78], [X1, 0, zc + 0.78]])) { ctx.fillStyle = shade('#9A8C78', zc); ctx.fill(); }
    // interior (warm while open)
    const closed = prog(t, ts - 0.2, ts, E.in);
    if (poly3(ctx, cam, [[s * (XW - 0.004), 0, zc - 0.62], [s * (XW - 0.004), 2.5, zc - 0.62], [s * (XW - 0.004), 2.5, zc + 0.62], [s * (XW - 0.004), 0, zc + 0.62]])) { ctx.fillStyle = mix(shade('#8A5A2A', zc), '#0B0907', closed); ctx.fill(); }
    // German flag (black-red-gold)
    [['#111111', 3.35, 3.2], ['#DD0000', 3.2, 3.05], ['#FFCE00', 3.05, 2.9]].forEach(([c, y0, y1]) => { if (poly3(ctx, cam, [[X1 * 0.999, y1, zc - 0.4], [X1 * 0.999, y0, zc - 0.4], [X1 * 0.999, y0, zc + 0.4], [X1 * 0.999, y1, zc + 0.4]])) { ctx.fillStyle = shade(c, zc + 3); ctx.fill(); } });
    // leaf: hinge on the near edge, swings into the corridor, slams at ts with a small bounce
    let ang = 1.15 * (1 - prog(t, ts - 0.22, ts, E.in));
    if (t > ts) ang = -0.06 * Math.exp(-(t - ts) * 10) * Math.sin((t - ts) * 40);
    const hz = zc + 0.62, ex = X - s * 1.24 * Math.sin(Math.max(0, ang)), ez = hz - 1.24 * Math.cos(ang);
    if (poly3(ctx, cam, [[X1, 0, hz], [ex, 0, ez], [ex, 2.5, ez], [X1, 2.5, hz]])) { ctx.fillStyle = shade('#6E4628', zc + 1); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 2; ctx.stroke(); }
    // dust puff
    if (t > ts && t < ts + 1.2) {
      const k = (t - ts) / 1.2; const spr = softSprite('dust', 'rgba(200,185,160,0.55)', 128);
      ctx.save(); ctx.globalAlpha = 0.6 * (1 - k);
      for (let i = 0; i < 6; i++) { const p = cam.proj([X - s * (0.2 + k * 0.6 + i * 0.05), 0.15 + i * 0.06, zc + (i - 2.5) * 0.25]); const r = cam.foc * (0.25 + k * 0.5) / Math.max(0.5, p[2]); ctx.drawImage(spr, p[0] - r, p[1] - r, 2 * r, 2 * r); }
      ctx.restore();
    }
  }
  // ceiling lamps
  const lamp = softSprite('lamp', 'rgba(255,214,150,0.9)', 128);
  for (const z of [-1.5, -6, -10.5, -15]) {
    const d = cam.depth([0, 3.6, z]); if (d < 0.3) continue;
    const p = cam.proj([0, 3.55, z]); const r = cam.foc * 0.6 / d;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.55 * (1 - clamp((d - 4) / 22)); ctx.drawImage(lamp, p[0] - r, p[1] - r * 0.6, 2 * r, 1.2 * r); ctx.restore();
  }
  // warm flash as we push through the far door
  const fl = prog(t, o.pushEnd - 0.4, o.pushEnd, E.in);
  if (fl > 0) { ctx.fillStyle = `rgba(255,236,206,${fl})`; ctx.fillRect(0, 0, W, H); }
}

// =====================================================================================
// SEAFLOOR BLOCK with magnetic stripes mirrored about a spreading ridge.
// s = {cam:{pos,target,fov}, rightReveal (0..1), flip (0..1), shift (units), ridgeGlow (0..1), arrows (0..1), spreadArrows (0..1)}
// =====================================================================================
const L = 7.2, DZ = 9;
const BOUNDS = [0.42, 0.95, 1.08, 1.62, 1.74, 2.25, 2.95, 3.12, 3.32, 3.95, 4.6, 5.0, 5.55, 6.15, 6.6, 7.4, 8.2, 9.0];
const NEW0 = 0.2, NEWW = 0.34;
const hgt = (x) => 0.36 * Math.exp(-((x / 1.05) ** 2)) - 0.08 * Math.exp(-((x / 0.16) ** 2)) - 0.05 * Math.min(Math.abs(x), 5) / 5;
// stripe intervals in distance-from-ridge d for a given spreading shift: [{a, b, n (normal?)}]
function stripes(shift) {
  const cuts = [];
  for (let j = 0; NEW0 + j * NEWW < shift; j++) cuts.push({ d: shift - (NEW0 + j * NEWW), k: 'new' });
  const out = []; let a = 0;
  // new crust: polarity depends on creation shift u = shift - d
  const polAt = (d) => {
    if (d >= shift) { const d0 = d - shift; let i = 0; while (i < BOUNDS.length && BOUNDS[i] <= d0) i++; return i % 2 === 0; }
    const u = shift - d; if (u < NEW0) return true; return Math.floor((u - NEW0) / NEWW) % 2 === 1;
  };
  const edges = [0, ...cuts.map(c => c.d), ...BOUNDS.map(b => b + shift)].filter(d => d >= 0 && d <= L + 0.01).sort((x, y) => x - y);
  edges.push(L);
  for (let i = 0; i < edges.length - 1; i++) { const a0 = edges[i], b0 = edges[i + 1]; if (b0 - a0 < 1e-4) continue; out.push({ a: a0, b: b0, n: polAt((a0 + b0) / 2) }); }
  return out;
}
const MSNOW = particles(777, 140, r => ({ x: r(), y: r(), sp: 0.01 + r() * 0.03, s: 0.6 + r() * 1.8, ph: r() * 6.28 }));

export function seafloor(ctx, W, H, t, s) {
  // deep water background
  const bg = ctx.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#0B2238'); bg.addColorStop(0.55, '#06121F'); bg.addColorStop(1, '#03070D');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  // god rays
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 5; i++) {
    const x = W * (0.15 + i * 0.19) + Math.sin(t * 0.13 + i) * 60; const gr = ctx.createLinearGradient(x, 0, x + 140, H * 0.8);
    gr.addColorStop(0, 'rgba(90,170,220,0.07)'); gr.addColorStop(1, 'rgba(90,170,220,0)'); ctx.fillStyle = gr;
    ctx.beginPath(); ctx.moveTo(x - 50, 0); ctx.lineTo(x + 60, 0); ctx.lineTo(x + 330, H); ctx.lineTo(x + 120, H); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
  const cam = camera(s.cam.pos, s.cam.target, s.cam.fov || 38, W, H);
  const NZ = 6; // z subdivisions for nicer perspective
  const NORM = '#EEF1F5', REV = '#1A2433', BASE = '#2A3646';
  // top surface patch between x0..x1 (x0<x1) from z=0..-DZ
  const surf = (x0, x1, col, map) => {
    const n = Math.max(2, Math.ceil((x1 - x0) / 0.25));
    const front = [], back = [];
    for (let i = 0; i <= n; i++) { const x = lerp(x0, x1, i / n); front.push(map(x, 0)); back.push(map(x, -DZ)); }
    if (poly3(ctx, cam, [...front, ...back.reverse()])) { ctx.fillStyle = col; ctx.fill(); }
  };
  const flat = (x, z) => [x, hgt(x), z];
  // base surface
  surf(-L, L, BASE, flat);
  // subtle cross-hatch on base so it reads as terrain
  ctx.beginPath(); for (let z = 0; z >= -DZ; z -= 1.5) { const pts = []; for (let x = -L; x <= L + 0.01; x += 0.4) pts.push(cam.proj([x, hgt(x) + 0.002, z])); pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); }
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 1.5; ctx.stroke();
  const st = stripes(s.shift || 0);
  // right side stripes (reveal wipe outward from the ridge)
  const rr = (s.rightReveal ?? 0) * L;
  for (const q of st) { if (q.a >= rr) break; surf(q.a, Math.min(q.b, rr), q.n ? NORM : REV, (x, z) => [x, hgt(x) + 0.004, z]); }
  // left side: a mirrored 'page' flipping over the ridge axis
  const fp = s.flip ?? 0;
  if (fp > 0) {
    const th = Math.PI * (1 - fp);
    const map = (d, z) => [-d * Math.cos(th), hgt(d) + 0.006 + d * Math.sin(th) * 0.92, z];
    for (const q of st) surf(q.a, q.b, q.n ? (th > 1.57 ? '#CDD3DB' : NORM) : REV, map);
  }
  // compass needles: polarity arrows (north = away from camera)
  if ((s.arrows || 0) > 0) {
    ctx.save(); ctx.globalAlpha = s.arrows; ctx.strokeStyle = PAL.yellow; ctx.fillStyle = PAL.yellow; ctx.lineWidth = 4; ctx.lineCap = 'round';
    for (const q of st) {
      const w = q.b - q.a; if (w < 0.3 || q.a > rr) continue;
      for (const sg of fp >= 1 ? [1, -1] : [1]) {
        const xm = sg * (q.a + q.b) / 2, zA = q.n ? -2.2 : -3.6, zB = q.n ? -3.6 : -2.2;
        const a = cam.proj([xm, hgt(xm) + 0.01, zA]), b = cam.proj([xm, hgt(xm) + 0.01, zB]);
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
        const ang = Math.atan2(b[1] - a[1], b[0] - a[0]), hl = 14;
        ctx.beginPath(); ctx.moveTo(b[0] + Math.cos(ang) * 6, b[1] + Math.sin(ang) * 6); ctx.lineTo(b[0] - Math.cos(ang - 0.5) * hl, b[1] - Math.sin(ang - 0.5) * hl); ctx.lineTo(b[0] - Math.cos(ang + 0.5) * hl, b[1] - Math.sin(ang + 0.5) * hl); ctx.closePath(); ctx.fill();
      }
    }
    ctx.restore();
  }
  // ridge glow along the crest
  const rg = s.ridgeGlow ?? 0.5;
  {
    const pts = []; for (let z = 0; z >= -DZ; z -= 0.5) pts.push(cam.proj([0, hgt(0) + 0.01, z]));
    const p2 = pts.map(p => [p[0], p[1]]);
    F.glowPath(ctx, p2, { color: '#FF8A3D', width: 3 + 5 * rg, alpha: 0.5 + 0.5 * rg });
  }
  // spreading arrows (white chevrons moving outward)
  if ((s.spreadArrows || 0) > 0) {
    ctx.save(); ctx.globalAlpha = s.spreadArrows; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const sg of [-1, 1]) for (const z of [-1.2, -5.5]) {
      const x0 = sg * (0.6 + ((t * 0.5) % 1) * 0.5), x1 = x0 + sg * 1.0;
      const a = cam.proj([x0, hgt(x0) + 0.05, z]), b = cam.proj([x1, hgt(x1) + 0.05, z]);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
      ctx.beginPath(); ctx.moveTo(b[0] - Math.cos(ang - 0.6) * 22, b[1] - Math.sin(ang - 0.6) * 22); ctx.lineTo(b[0], b[1]); ctx.lineTo(b[0] - Math.cos(ang + 0.6) * 22, b[1] - Math.sin(ang + 0.6) * 22); ctx.stroke();
    }
    ctx.restore();
  }
  // front cross-section (z = 0)
  {
    const yB = -2.4;
    const top = []; for (let x = -L; x <= L + 0.001; x += 0.2) top.push([x, hgt(x), 0]);
    // mantle
    if (poly3(ctx, cam, [...top, [L, yB, 0], [-L, yB, 0]])) {
      const a = cam.proj([0, 0, 0]), b = cam.proj([0, yB, 0]);
      const gr = ctx.createLinearGradient(0, a[1], 0, b[1]); gr.addColorStop(0, '#3A1D14'); gr.addColorStop(1, '#6E2A12'); ctx.fillStyle = gr; ctx.fill();
    }
    // magma chamber glow under the ridge
    const c = cam.proj([0, -0.75, 0]); const rr2 = cam.foc * 1.5 / c[2];
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const mg = ctx.createRadialGradient(c[0], c[1], 0, c[0], c[1], rr2); mg.addColorStop(0, `rgba(255,150,60,${0.55 + 0.35 * rg})`); mg.addColorStop(1, 'rgba(255,90,30,0)');
    ctx.fillStyle = mg; ctx.fillRect(c[0] - rr2, c[1] - rr2, 2 * rr2, 2 * rr2);
    ctx.restore();
    // lower crust band
    const lower = top.map(p => [p[0], p[1] - 0.32, 0]);
    const lower2 = top.map(p => [p[0], p[1] - 0.75, 0]);
    if (poly3(ctx, cam, [...lower, ...lower2.slice().reverse()])) { ctx.fillStyle = '#2B2622'; ctx.fill(); }
    // upper crust base band, then polarity dikes mirrored on top
    { const tp = [], bt = []; for (let x = -L; x <= L + 0.001; x += 0.2) { tp.push([x, hgt(x), 0]); bt.push([x, hgt(x) - 0.32, 0]); } if (poly3(ctx, cam, [...tp, ...bt.reverse()])) { ctx.fillStyle = '#3A4350'; ctx.fill(); } }
    for (const q of st) {
      for (const sg of [1, -1]) {
        if (sg === 1 && q.a >= rr) continue; if (sg === -1 && fp < 1) continue;
        const a0 = sg === 1 ? q.a : -Math.min(q.b, L), a1 = sg === 1 ? Math.min(q.b, rr) : -q.a;
        const n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / 0.2)); const tp = [], bt = [];
        for (let i = 0; i <= n; i++) { const x = lerp(a0, a1, i / n); tp.push([x, hgt(x), 0]); bt.push([x, hgt(x) - 0.32, 0]); }
        if (poly3(ctx, cam, [...tp, ...bt.reverse()])) { ctx.fillStyle = q.n ? '#C9CFD8' : '#141C27'; ctx.fill(); }
      }
    }
    // upwelling arrows under the ridge
    ctx.save(); ctx.strokeStyle = 'rgba(255,200,120,0.85)'; ctx.lineWidth = 5; ctx.lineCap = 'round';
    for (const sg of [-1, 1]) {
      const k = (t * 0.35) % 1;
      const pts = []; for (let i = 0; i <= 12; i++) { const u = i / 12; const x = sg * (0.15 + u * 1.6), y = -2.1 + 1.25 * Math.sin(u * Math.PI / 2) ; pts.push(cam.proj([x * 1.0, y, 0.001])); }
      F.glowPath(ctx, pts.map(p => [p[0], p[1]]), { color: '#FFB060', width: 4, p: 0.25 + 0.75 * k, alpha: 0.75 * (1 - k * 0.6) });
    }
    ctx.restore();
    // block outline
    ctx.beginPath(); line3(ctx, cam, [-L, hgt(-L), 0], [-L, yB, 0]); line3(ctx, cam, [L, hgt(L), 0], [L, yB, 0]); line3(ctx, cam, [-L, yB, 0], [L, yB, 0]);
    ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.lineWidth = 2; ctx.stroke();
  }
  // far fog
  {
    const a = cam.proj([0, 0, -DZ]); const b = cam.proj([0, 0, -DZ * 0.45]);
    const gr = ctx.createLinearGradient(0, a[1] - 40, 0, b[1]); gr.addColorStop(0, 'rgba(6,18,31,1)'); gr.addColorStop(1, 'rgba(6,18,31,0)');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, Math.max(0, b[1]));
  }
  // marine snow
  ctx.save(); ctx.fillStyle = '#BFE6FF';
  for (const m of MSNOW) { const y = ((m.y - t * m.sp) % 1 + 1) % 1 * H, x = (m.x + Math.sin(t * 0.3 + m.ph) * 0.01) * W; ctx.globalAlpha = 0.25; ctx.beginPath(); ctx.arc(x, y, m.s, 0, 6.283); ctx.fill(); }
  ctx.restore();
}
