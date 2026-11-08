// PHONE-FIRST TYPE + MAP-GRAPHICS SYSTEM (prototype for ep02).
// Everything is sized by CAP HEIGHT in px at 1080p (scaled by H/1080), never by font size, so one rule fits every family.
// Phone check: a 16:9 player on an upright phone is ~390 px wide = 0.203 x. A 64 px cap -> ~13 px on the phone.
//
//   ROLE       FAMILY                      CAP @1080   % of H   ~ON PHONE   USE
//   number     Anton                       150-190     14-18%   30-38 px    the one big figure of a shot (yellow)
//   headline   Anton                       96-120       9-11%   20-24 px    the idea of the shot, 2-4 words, colour-coded words = legend
//   label      Barlow Condensed 800 caps   64           6%      13 px       place / thing names, ALWAYS on a plate or with a 0.12-cap stroke
//   kicker     Barlow Condensed 800 caps   48 (floor)   4.4%    10 px       connector words, tags ("NEARLY", "MODEL"); never the key fact
//   FLOOR: nothing a viewer must read under 60 px cap; nothing at all under 44 px cap. No grey text: #F4F6FA or a hue.
//
// Lines & shapes (px @1080): meaningful line core 9-12 + dark under-stroke +8; shape outline 5 white + 12 glow + dark under;
// arrows 14 body, head >= 56 long; fills 45-60 % so relief shows through. Hues: hero #FF5A36 (the subject), cyan #3DE3FF
// (water / the other side), yellow #FFD23F (numbers, arrows, counted things). Navy/ink only inside plates & scrims.
import * as F from '../../lib/fx.js';

export const C = {
  text: '#F4F6FA', ink: '#050912', inkA: (a) => `rgba(5,9,18,${a})`, plate: 'rgba(7,12,21,0.86)',
  hero: '#FF5A36', cyan: '#3DE3FF', yellow: '#FFD23F', white: '#FFFFFF', navyTop: '#0D1B30', navyBot: '#04070D',
};
export const CAP = { number: 170, headline: 108, label: 64, kicker: 48 };
export const FLOOR = { must: 60, any: 44 };
export const FAM = { num: 'Anton', head: 'Anton', label: 'Barlow Condensed' };
const WEIGHT = { 'Anton': 400, 'Barlow Condensed': 800, 'Inter': 900, 'Bebas Neue': 400 };

let SC = 1;                          // H / 1080
const RATIO = {};                    // cap-height / font-size per family (measured once)
export async function init(H) {
  SC = H / 1080;
  await Promise.all(['400 100px "Anton"', '800 100px "Barlow Condensed"', '900 100px "Inter"'].map(f => document.fonts.load(f)));
  const m = document.createElement('canvas').getContext('2d');
  for (const fam of ['Anton', 'Barlow Condensed', 'Inter', 'Bebas Neue']) {
    m.font = `${WEIGHT[fam]} 200px "${fam}"`;
    RATIO[fam] = m.measureText('H').actualBoundingBoxAscent / 200;
  }
  return RATIO;
}
export const px = (v) => v * SC;
export const sizeFor = (fam, cap) => cap / (RATIO[fam] || 0.7);

// ---------- QC: every text draw records its cap height; the page logs the smallest per frame ----------
export const QC = { items: [], begin() { this.items = []; }, add(s, cap, a) { if (a > 0.5) this.items.push({ s, cap: Math.round(cap / SC) }); },
  report() { const m = this.items.reduce((a, b) => Math.min(a, b.cap), 1e9); return { min: m === 1e9 ? null : m, n: this.items.length, fail: this.items.filter(i => i.cap < FLOOR.any).map(i => i.s) }; } };

// ---------- core text: cap-sized, cached sprite (F.text), optional dark stroke for unplated text ----------
// o: {fam, cap, color, align, tracking, stroke (true = 0.12*cap), alpha}
export function txt(ctx, s, x, y, o = {}) {
  const fam = o.fam || FAM.label, cap = px(o.cap || CAP.label), size = sizeFor(fam, cap);
  const st = o.stroke === true ? cap * 0.13 : (o.stroke || 0);
  QC.add(s, cap, o.alpha ?? 1);
  return F.text(ctx, s, x, y, { size, fam, weight: WEIGHT[fam] || 700, color: o.color || C.text, align: o.align, tracking: o.tracking ?? (fam === FAM.label ? 0.04 : 0.01),
    alpha: o.alpha ?? 1, stroke: st, strokeColor: o.strokeColor || C.inkA(0.92), shadow: o.shadow ?? true, shadowBlur: cap * 0.35, shadowY: cap * 0.05, shadowColor: 'rgba(0,0,0,0.6)' });
}
export function width(ctx, s, o = {}) {
  const fam = o.fam || FAM.label, cap = px(o.cap || CAP.label);
  return F.measure(ctx, s, { size: sizeFor(fam, cap), fam, weight: WEIGHT[fam] || 700, tracking: o.tracking ?? (fam === FAM.label ? 0.04 : 0.01) });
}

// ---------- headline: stacked lines of coloured words; each word slides up out of a mask (overshoot-free, crisp) ----------
// lines: [{words:[{w, c}], role:'headline'|'kicker'|'number', cap?}], reveal times per word from t0 with `per` spacing.
export function stack(ctx, lines, x, y, lt, o = {}) {
  let cy = y, k = 0; const t0 = o.t0 || 0, per = o.per ?? 0.12, gapK = o.gap ?? 0.42, out = o.tOut != null ? F.prog(lt, o.tOut, o.tOut + 0.3, F.E.in) : 0;
  const boxes = [];
  for (const L of lines) {
    const role = L.role || 'headline', fam = role === 'kicker' || role === 'label' ? FAM.label : FAM.head;
    const cap = L.cap || CAP[role] || CAP.headline, capP = px(cap);
    cy += capP;
    const sp = px(cap) * (fam === FAM.label ? 0.32 : 0.26);
    const ws = L.words.map(w => typeof w === 'string' ? { w } : w);
    const wid = ws.map(w => width(ctx, w.w, { fam, cap, tracking: L.tracking }));
    const tot = wid.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
    let cx = o.align === 'center' ? x - tot / 2 : o.align === 'right' ? x - tot : x;
    boxes.push({ x: cx, y: cy - capP, w: tot, h: capP });
    ws.forEach((w, i) => {
      const p = F.prog(lt, t0 + k * per, t0 + k * per + 0.42, F.E.outExpo); k++;
      const a = p * (1 - out);
      if (a > 0.002) {
        ctx.save();
        ctx.beginPath(); ctx.rect(cx - capP, cy - capP * 1.6, wid[i] + capP * 2, capP * 1.6 + capP * 0.16); ctx.clip(); // mask edge just under the baseline: the word rises out of it
        txt(ctx, w.w, cx, cy + (1 - p) * capP * 1.15, { fam, cap, color: w.c || L.color || C.text, stroke: true, alpha: Math.min(1, a * 1.4), tracking: L.tracking });
        ctx.restore();
      }
      cx += wid[i] + sp;
    });
    cy += capP * (L.lead ?? gapK);
  }
  return { bottom: cy, boxes };
}

// ---------- label plate: rounded rect, coloured accent bar, white caps; optional leader to an anchor ----------
// anchor: 'left'|'center'|'right' (x side) ; y = vertical centre. p = 0..1 build (bar first, then plate wipe, then text)
export function label(ctx, s, x, y, o = {}) {
  const cap = px(o.cap || CAP.label), p = o.p ?? 1; if (p <= 0) return null;
  const tw = width(ctx, s, { cap: o.cap || CAP.label }), padX = cap * 0.5, bar = Math.max(px(9), cap * 0.15), h = cap * 1.95, w = tw + padX * 2 + bar;
  let bx = o.anchor === 'center' ? x - w / 2 : o.anchor === 'right' ? x - w : x, by = y - h / 2;
  const pw = F.prog(p, 0.0, 0.55, F.E.outExpo), pt = F.prog(p, 0.3, 1, F.E.out);
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  if (o.leader) {
    const [lx, ly] = o.leader, ex = F.clamp(lx, bx, bx + w), ey = F.clamp(ly, by, by + h), lp = F.prog(p, 0, 0.6);
    const mx = F.lerp(ex, lx, lp), my = F.lerp(ey, ly, lp);
    ctx.lineCap = 'round';
    ctx.strokeStyle = C.inkA(0.7); ctx.lineWidth = px(9); ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(mx, my); ctx.stroke();
    ctx.strokeStyle = C.text; ctx.lineWidth = px(4); ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(mx, my); ctx.stroke();
    pin(ctx, lx, ly, { p: F.prog(p, 0.4, 0.9, F.E.outBack), color: o.accent || C.text, t: o.t });
  }
  // shadow lip + plate (wipes open from the accent bar)
  const ww = bar + (w - bar) * pw, r = px(10);
  ctx.fillStyle = 'rgba(0,0,0,0.28)'; F.round(ctx, bx + px(2), by + px(6), ww, h, r); ctx.fill();
  ctx.fillStyle = o.bg || C.plate; F.round(ctx, bx, by, ww, h, r); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = px(1.5); F.round(ctx, bx + 0.75, by + 0.75, ww - 1.5, h - 1.5, r); ctx.stroke();
  ctx.save(); F.round(ctx, bx, by, ww, h, r); ctx.clip(); ctx.fillStyle = o.accent || C.hero; ctx.fillRect(bx, by, bar, h); ctx.restore();
  if (pt > 0) { ctx.save(); ctx.beginPath(); ctx.rect(bx, by, ww, h); ctx.clip(); txt(ctx, s, bx + bar + padX - (1 - pt) * cap * 0.4, y + cap / 2, { cap: o.cap || CAP.label, color: o.color || C.text, alpha: pt, shadow: false }); ctx.restore(); }
  ctx.restore();
  return { x: bx, y: by, w, h };
}
// map pin: solid dot with dark ring and a soft pulsing halo
export function pin(ctx, x, y, o = {}) {
  const p = o.p ?? 1; if (p <= 0) return; const r = px(o.r || 11) * p;
  ctx.save();
  if (o.t != null) { const k = (o.t * 0.8) % 1; ctx.globalAlpha *= (1 - k) * 0.8; ctx.strokeStyle = o.color || C.text; ctx.lineWidth = px(3); ctx.beginPath(); ctx.arc(x, y, r * (1.2 + 2.6 * k), 0, 7); ctx.stroke(); ctx.globalAlpha /= Math.max(0.05, (1 - k) * 0.8); }
  ctx.fillStyle = C.inkA(0.85); ctx.beginPath(); ctx.arc(x, y, r + px(4), 0, 7); ctx.fill();
  ctx.fillStyle = o.color || C.text; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
  ctx.restore();
}

// ---------- lines: thick core + dark under-stroke + soft glow, draw-on p (runs = arrays of [x,y]) ----------
function walk(ctx, runs, budget) { ctx.beginPath(); let bud = budget; for (const run of runs) { if (bud <= 0) break; ctx.moveTo(run[0][0], run[0][1]); for (let i = 1; i < run.length; i++) { const d = Math.hypot(run[i][0] - run[i - 1][0], run[i][1] - run[i - 1][1]); if (d > bud) { const k = bud / d; ctx.lineTo(run[i - 1][0] + (run[i][0] - run[i - 1][0]) * k, run[i - 1][1] + (run[i][1] - run[i - 1][1]) * k); bud = 0; break; } ctx.lineTo(run[i][0], run[i][1]); bud -= d; } } }
const runLen = (runs) => runs.reduce((a, run) => { let L = 0; for (let i = 1; i < run.length; i++) L += Math.hypot(run[i][0] - run[i - 1][0], run[i][1] - run[i - 1][1]); return a + L; }, 0);
export function line(ctx, runs, o = {}) {
  const w = px(o.width || 10), budget = runLen(runs) * F.clamp(o.p ?? 1), col = o.color || C.text;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  if (o.dash) ctx.setLineDash(o.dash.map(px));
  const pass = (lw, c) => { ctx.strokeStyle = c; ctx.lineWidth = lw; walk(ctx, runs, budget); ctx.stroke(); };
  pass(w * 3.6, hexA(o.glow || col, 0.10)); pass(w * 2.0, hexA(o.glow || col, 0.22));
  pass(w + px(8), C.inkA(o.under ?? 0.55)); pass(w, col);
  ctx.restore();
}
export function hexA(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }

// shape outline on the globe: project rings, break at the horizon and at pole/seam artefacts, draw like line()
export function projectRuns(globe, ringsArr, o = {}) {
  const runs = [];
  for (const r of ringsArr) {
    let cur = [], lx = null, ly = null, plon = null;
    for (const [lon, lat] of r) {
      const bad = !(lon === lon) || Math.abs(lat) > (o.maxLat ?? 89.5) || (plon !== null && Math.abs(lon - plon) > 90);
      plon = lon;
      const q = bad ? { visible: false } : globe.project(lat, lon, o.h || 0);
      if (!q.visible) { if (cur.length > 1) runs.push(cur); cur = []; lx = null; continue; }
      if (lx !== null && Math.hypot(q.x - lx, q.y - ly) < 1.5) continue;
      cur.push([q.x, q.y]); lx = q.x; ly = q.y;
    }
    if (cur.length > 1) runs.push(cur);
  }
  return runs;
}
export function outline(ctx, runs, o = {}) { line(ctx, runs, Object.assign({ width: 5, color: C.text, under: 0.5 }, o)); }

// ---------- arrow: fat body, big head, dark under-stroke, glow, travelling highlight dashes (reads as motion) ----------
export function arrow(ctx, pts, o = {}) {
  if (pts.length < 2) return;
  const w = px(o.width || 14), p = F.clamp(o.p ?? 1), col = o.color || C.yellow, hl = w * 4.2, hw = w * 4.4;
  const L = runLen([pts]); if (L < 2) return; const target = L * p;
  // tip position + direction at target
  let acc = 0, tip = pts[pts.length - 1], dir = [1, 0];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (acc + d >= target) { const k = (target - acc) / d; tip = [F.lerp(pts[i - 1][0], pts[i][0], k), F.lerp(pts[i - 1][1], pts[i][1], k)]; dir = [(pts[i][0] - pts[i - 1][0]) / d, (pts[i][1] - pts[i - 1][1]) / d]; break; } acc += d; if (i === pts.length - 1) dir = [(pts[i][0] - pts[i - 1][0]) / d, (pts[i][1] - pts[i - 1][1]) / d]; }
  const bodyBudget = Math.max(0, target - hl * 0.55);
  const hs = F.clamp(target / (hl * 1.2));                       // head grows in at the start
  const head = (grow) => { const l = hl * hs + grow, ww = hw * hs + grow * 1.2; const nx = -dir[1], ny = dir[0]; const bx = tip[0] - dir[0] * l, by = tip[1] - dir[1] * l;
    ctx.beginPath(); ctx.moveTo(tip[0] + dir[0] * grow * 0.6, tip[1] + dir[1] * grow * 0.6); ctx.lineTo(bx + nx * ww / 2, by + ny * ww / 2); ctx.quadraticCurveTo(bx + dir[0] * l * 0.18, by + dir[1] * l * 0.18, bx - nx * ww / 2, by - ny * ww / 2); ctx.closePath(); };
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const pass = (lw, c) => { ctx.strokeStyle = c; ctx.lineWidth = lw; walk(ctx, [pts], bodyBudget); ctx.stroke(); };
  pass(w * 3.4, hexA(col, 0.12));
  pass(w + px(10), C.inkA(0.6)); ctx.fillStyle = C.inkA(0.6); head(px(6)); ctx.fill();
  pass(w, col); ctx.fillStyle = col; head(0); ctx.fill();
  // travelling highlight: short bright dashes flowing toward the head
  if (o.t != null) { ctx.save(); ctx.setLineDash([w * 1.2, w * 3.2]); ctx.lineDashOffset = -o.t * w * 9; ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = w * 0.38; walk(ctx, [pts], Math.max(0, bodyBudget - w)); ctx.stroke(); ctx.restore(); }
  ctx.restore();
}

// ---------- odometer number: each digit rolls in its own slot (tabular), crisp stroke ----------
export function slot(ctx, v, x, y, o = {}) {
  const fam = o.fam || FAM.num, cap = px(o.cap || CAP.number), size = sizeFor(fam, cap);
  const n = Math.max(0, v), digits = o.digits || String(Math.floor(Math.max(n, o.to ?? n))).length;
  ctx.save(); ctx.font = `${WEIGHT[fam]} ${size}px "${fam}"`; const dw = ctx.measureText('0').width * 1.02; ctx.restore();
  let cx = o.align === 'right' ? x - dw * digits : o.align === 'center' ? x - dw * digits / 2 : x;
  for (let i = digits - 1; i >= 0; i--) {
    const base = Math.pow(10, i), d = Math.floor(n / base) % 10, rest = n % base, roll = i === 0 ? n % 1 : Math.max(0, rest - (base - 1));
    // window = one glyph (+ its stroke); the outgoing digit fades as it leaves, the incoming one fades in as it arrives
    ctx.save(); ctx.beginPath(); ctx.rect(cx - cap * 0.3, y - cap * 1.1, dw + cap * 0.6, cap * 1.19); ctx.clip();
    const A0 = o.alpha ?? 1, aOut = F.clamp(1 - roll * 1.6), aIn = F.clamp((roll - 0.25) * 1.6);
    if (aOut > 0.002) txt(ctx, String(d), cx + dw / 2, y - roll * cap * 1.3, { fam, cap: o.cap || CAP.number, color: o.color || C.yellow, align: 'center', stroke: true, alpha: A0 * aOut });
    if (roll > 0.001 && aIn > 0.002) txt(ctx, String((d + 1) % 10), cx + dw / 2, y + (1 - roll) * cap * 1.3, { fam, cap: o.cap || CAP.number, color: o.color || C.yellow, align: 'center', stroke: true, alpha: A0 * aIn });
    ctx.restore();
    cx += dw;
  }
  return cx;
}

// ---------- pictogram row: n people, the first k filled (counted), the rest hollow ----------
export function people(ctx, x, y, n, k, o = {}) {
  const h = px(o.h || 84), gap = h * (o.gap ?? 0.66), t = o.p ?? 1;
  // silhouette (unit box: width 0.62h, height h, origin bottom-centre): round head + shoulders with a rounded torso
  const body = (s) => { const hr = 0.17 * h, bw = 0.62 * h, sh = 0.50 * h, r = 0.26 * h;
    ctx.beginPath(); ctx.arc(0, -h + hr + s, hr, 0, 7);
    ctx.moveTo(-bw / 2 + r, -sh); ctx.lineTo(bw / 2 - r, -sh); ctx.quadraticCurveTo(bw / 2, -sh, bw / 2, -sh + r); ctx.lineTo(bw / 2, 0); ctx.lineTo(-bw / 2, 0); ctx.lineTo(-bw / 2, -sh + r); ctx.quadraticCurveTo(-bw / 2, -sh, -bw / 2 + r, -sh); ctx.closePath(); };
  for (let i = 0; i < n; i++) {
    const s = F.E.outBack(F.prog(t, i * 0.06, i * 0.06 + 0.35, F.E.lin)); if (s <= 0.001) continue;
    const cx = x + i * gap + h * 0.31, on = i < k, col = on ? (o.color || C.yellow) : (o.off || C.cyan);
    ctx.save(); ctx.translate(cx, y); ctx.scale(s, s); ctx.lineJoin = 'round';
    ctx.lineWidth = px(8); ctx.strokeStyle = C.inkA(0.8); body(0); ctx.stroke();
    if (on) { ctx.fillStyle = col; body(0); ctx.fill(); }
    else { ctx.fillStyle = C.inkA(0.55); body(0); ctx.fill(); ctx.lineWidth = px(4.5); ctx.strokeStyle = col; body(0); ctx.stroke(); }
    ctx.restore();
  }
  return x + (n - 1) * gap + h * 0.62;
}

// ---------- list / progress tag: square number badge + kicker + pips ----------
export function tag(ctx, word, i, n, x, y, o = {}) {
  const p = o.p ?? 1; if (p <= 0) return;
  const kcap = o.cap || 56, s = px(kcap) * 1.75, a = F.prog(p, 0, 0.4, F.E.out);
  ctx.save(); ctx.globalAlpha *= a * (o.alpha ?? 1);
  const ww = width(ctx, word, { cap: kcap, tracking: 0.1 });
  txt(ctx, word, x, y + s / 2 + px(kcap) / 2, { cap: kcap, tracking: 0.1, stroke: true });
  const bx = x + ww + px(18), sc = F.lerp(0.5, 1, F.E.outBack(F.prog(p, 0.15, 0.6, F.E.lin)));
  ctx.save(); ctx.translate(bx + s / 2, y + s / 2); ctx.scale(sc, sc);
  ctx.fillStyle = C.inkA(0.7); F.round(ctx, -s / 2 - px(4), -s / 2 - px(4), s + px(8), s + px(8), px(14)); ctx.fill();
  ctx.fillStyle = o.color || C.yellow; F.round(ctx, -s / 2, -s / 2, s, s, px(12)); ctx.fill();
  txt(ctx, String(i), 0, px(kcap * 1.1) / 2, { fam: FAM.num, cap: kcap * 1.1, color: C.ink, align: 'center', shadow: false });
  ctx.restore();
  // pips under the row: n segments, the first i filled (where we are in the list)
  const tot = ww + px(18) + s, pg = px(10), pw = (tot - pg * (n - 1)) / n, ph = px(12), py = y + s + px(16);
  for (let k = 0; k < n; k++) { const on = k < i, pk = F.prog(p, 0.3 + k * 0.08, 0.6 + k * 0.08, F.E.out);
    ctx.fillStyle = C.inkA(0.75); F.round(ctx, x + k * (pw + pg) - px(3), py - px(3), pw * pk + px(6), ph + px(6), px(8)); ctx.fill();
    ctx.fillStyle = on ? (o.color || C.yellow) : 'rgba(244,246,250,0.4)'; F.round(ctx, x + k * (pw + pg), py, pw * pk, ph, px(6)); ctx.fill(); }
  ctx.restore();
  return { bottom: py + ph };
}

// ---------- scrims & background ----------
export function scrim(ctx, W, H, side = 'left', o = {}) {
  const ext = (o.extent ?? 0.5), a = o.alpha ?? 0.62;
  let g;
  if (side === 'left') g = ctx.createLinearGradient(0, 0, W * ext, 0);
  else if (side === 'right') g = ctx.createLinearGradient(W, 0, W * (1 - ext), 0);
  else g = ctx.createLinearGradient(0, 0, 0, H * ext);
  g.addColorStop(0, C.inkA(a)); g.addColorStop(0.55, C.inkA(a * 0.45)); g.addColorStop(1, C.inkA(0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
// lift pure-black space to a deep navy gradient (keeps stars and the globe: 'lighten' only raises darker pixels)
export function navySpace(ctx, W, H, cx = W / 2, cy = H / 2) {
  ctx.save(); ctx.globalCompositeOperation = 'lighten';
  const g = ctx.createRadialGradient(cx, cy, H * 0.2, cx, cy, W * 0.85); g.addColorStop(0, '#13284A'); g.addColorStop(0.5, '#0B1830'); g.addColorStop(1, '#060C18');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}
