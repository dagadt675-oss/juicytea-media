// Story mode "Archive in the World": real public-domain people as paper cut-outs living INSIDE the photoreal Earth scene.
// Everything is a pure function of time. Cheap on software canvas: all heavy work (cut-out, paper edge, grade,
// silhouette, rim) is done once in prepCard(); per frame we only blit and transform.
import * as F from './fx.js';
const D2R = Math.PI / 180;
export function cv(w, h) { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; }

// ---------- one-time card preparation ----------
// img: RGBA paper cut-out (tools/card.py). light: 'left' | 'right' (key-light side, matches the scene sun).
// Returns {img: shaded card, sil: soft black silhouette (for shadows), w, h}
export function prepCard(img, o = {}) {
  const w = img.width, h = img.height, light = o.light || 'left';
  const c = cv(w, h), g = c.getContext('2d');
  g.drawImage(img, 0, 0);
  // directional shading: key side a touch warmer/brighter, far side cooler/darker (same light as the globe)
  g.globalCompositeOperation = 'source-atop';
  const lg = g.createLinearGradient(light === 'left' ? 0 : w, 0, light === 'left' ? w : 0, h * 0.4);
  lg.addColorStop(0, 'rgba(255,214,160,0.16)'); lg.addColorStop(0.55, 'rgba(0,0,0,0)'); lg.addColorStop(1, 'rgba(10,30,60,0.30)');
  g.fillStyle = lg; g.fillRect(0, 0, w, h);
  // bottom falls off slightly (grounding)
  const bg = g.createLinearGradient(0, h * 0.6, 0, h); bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(1, 'rgba(5,10,20,0.28)');
  g.fillStyle = bg; g.fillRect(0, 0, w, h);
  // rim light on the far edge (sky / globe bounce): silhouette minus a shifted silhouette
  if (o.rim !== false) {
    const r = cv(w, h), rg = r.getContext('2d');
    rg.drawImage(img, 0, 0); rg.globalCompositeOperation = 'source-in'; rg.fillStyle = o.rimColor || '#9FDcff'; rg.fillRect(0, 0, w, h);
    rg.globalCompositeOperation = 'destination-out';
    const k = o.rimPx || Math.round(w * 0.012), dx = light === 'left' ? -k : k;
    rg.drawImage(img, dx, Math.round(k * 0.4));
    g.globalCompositeOperation = 'source-atop'; g.globalAlpha = o.rimAlpha ?? 0.9; g.drawImage(r, 0, 0);
    // the key side gets a thin warm edge too
    const r2 = cv(w, h), r2g = r2.getContext('2d');
    r2g.drawImage(img, 0, 0); r2g.globalCompositeOperation = 'source-in'; r2g.fillStyle = '#FFE2B0'; r2g.fillRect(0, 0, w, h);
    r2g.globalCompositeOperation = 'destination-out'; r2g.drawImage(img, -dx * 0.6, Math.round(k * 0.3));
    g.globalAlpha = 0.45; g.drawImage(r2, 0, 0);
    g.globalAlpha = 1;
  }
  g.globalCompositeOperation = 'source-over';
  // soft silhouette for drop/cast shadows (blur by down/up-scaling: no ctx.filter on big areas)
  const s = 0.06, sm = cv(w * s, h * s), smg = sm.getContext('2d');
  smg.imageSmoothingQuality = 'high'; smg.drawImage(img, 0, 0, sm.width, sm.height);
  smg.globalCompositeOperation = 'source-in'; smg.fillStyle = '#000'; smg.fillRect(0, 0, sm.width, sm.height);
  const sil = cv(w * 0.25, h * 0.25), sg = sil.getContext('2d'); sg.imageSmoothingQuality = 'high'; sg.drawImage(sm, 0, 0, sil.width, sil.height);
  return { img: c, sil, w, h };
}

// ---------- layers ----------
// collage card in screen space: (x, yBottom) = bottom-centre, hgt in px, rot radians, with a soft drop shadow
export function drawCard(ctx, card, x, yb, hgt, o = {}) {
  const s = hgt / card.h, w = card.w * s;
  ctx.save();
  ctx.translate(x, yb); ctx.rotate(o.rot || 0);
  if (o.shadow !== false) {
    ctx.save(); ctx.globalAlpha = (o.alpha ?? 1) * (o.shadowAlpha ?? 0.55);
    const sx = o.shadowDx ?? hgt * 0.022, sy = o.shadowDy ?? hgt * 0.016, grow = 1.02;
    ctx.drawImage(card.sil, -w / 2 * grow + sx, -hgt * grow + sy, w * grow, hgt * grow);
    ctx.restore();
  }
  ctx.globalAlpha = o.alpha ?? 1;
  ctx.drawImage(card.img, -w / 2, -hgt, w, hgt);
  ctx.restore();
  return { w, h: hgt };
}

// paper standee standing ON the globe at lat/lon. h = card height in Earth radii.
// hinge: 0 = upright, 1 = lying flat (pop-up book fold, falls away from camera). squash: + = squashed, - = stretched.
// lift: extra height above ground (Earth radii) for hops. lean: radians.
export function standee(ctx, g, card, o) {
  const { lat, lon } = o, h = o.h, lift = o.lift || 0, hinge = F.clamp(o.hinge || 0), sq = o.squash || 0;
  const b0 = g.project(lat, lon, 0), b = g.project(lat, lon, lift);
  const up = g.project(lat, lon, lift + h);
  const phi = hinge * Math.PI / 2 * 0.96;
  const tip = g.project(lat + (h * Math.sin(phi)) / D2R, lon, lift + h * Math.cos(phi));
  const vx = tip.x - b.x, vy = tip.y - b.y, hs = Math.hypot(vx, vy) * (1 - sq);
  const hUp = Math.hypot(up.x - b.x, up.y - b.y);
  const ws = hUp * card.w / card.h * (1 + sq * 0.55);
  const ang = Math.atan2(vx, -vy) + (o.lean || 0);
  const A = o.alpha ?? 1;
  // ground shadows (on the terrain, below the card): contact AO + cast shadow from the key light
  const gl = F.clamp(1 - lift / (h * 0.9));          // shadow fades while airborne
  ctx.save();
  if (o.shadow !== false) {
    // cast shadow: silhouette mapped onto the ground, falling back-right (sun from front-left)
    const hd = h / D2R, cl = Math.cos(lat * D2R);
    const sLat = lat + hd * (o.shLat ?? 0.55) * Math.cos(phi), sLon = lon + hd * (o.shLon ?? 0.95) * Math.cos(phi) / cl;
    const st = g.project(sLat, sLon, 0);
    const ux = (st.x - b0.x), uy = (st.y - b0.y);
    // affine: card x-axis -> screen horizontal (ws), card y (up, 0..h) -> shadow direction
    ctx.save(); ctx.globalAlpha = A * (o.shAlpha ?? 0.42) * gl;
    ctx.setTransform(ws / card.w, 0, -ux / card.h, -uy / card.h, b0.x, b0.y);
    ctx.drawImage(card.sil, -card.w / 2, -card.h * 0.02 - card.h, card.w, card.h);
    ctx.restore();
    // contact shadow / ambient occlusion
    const rx = ws * 0.62 * (0.6 + 0.4 * gl), ry = rx * 0.16;
    const rg = ctx.createRadialGradient(b0.x, b0.y, 0, b0.x, b0.y, rx);
    rg.addColorStop(0, `rgba(0,0,0,${0.55 * A * gl})`); rg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.save(); ctx.translate(b0.x, b0.y); ctx.scale(1, ry / rx); ctx.translate(-b0.x, -b0.y);
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(b0.x, b0.y, rx, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  ctx.translate(b.x, b.y); ctx.rotate(ang); ctx.globalAlpha = A;
  ctx.drawImage(card.img, -ws / 2, -hs, ws, hs);
  ctx.restore();
  return { x: b.x, y: b.y, top: b.y - hs, w: ws, h: hs };
}

// drifting dust motes and out-of-focus bokeh (deterministic). rect = [x, y, w, h]
export function dust(ctx, t, o = {}) {
  const r = F.rng(o.seed || 7), n = o.n || 40, [X, Y, Wd, Hd] = o.rect || [0, 0, 1920, 1080];
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < n; i++) {
    const big = r() < (o.bokeh ?? 0.18);
    const x0 = r(), y0 = r(), sp = 0.4 + r(), ph = r() * 6.28, sz = big ? 10 + r() * 26 : 1.2 + r() * 3.2;
    const x = X + ((x0 * Wd + t * (o.vx ?? 14) * sp + Math.sin(t * 0.7 + ph) * 12) % Wd + Wd) % Wd;
    const y = Y + ((y0 * Hd - t * (o.vy ?? 9) * sp + Math.cos(t * 0.5 + ph) * 8) % Hd + Hd) % Hd;
    const tw = 0.6 + 0.4 * Math.sin(t * (1.5 + r() * 2) + ph);
    const a = (big ? 0.07 : 0.55) * tw * (o.alpha ?? 1);
    const gr = ctx.createRadialGradient(x, y, 0, x, y, sz);
    gr.addColorStop(0, `rgba(${o.rgb || '255,226,180'},${a})`); gr.addColorStop(big ? 0.75 : 0.35, `rgba(${o.rgb || '255,226,180'},${a * (big ? 0.8 : 0.5)})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gr; ctx.fillRect(x - sz, y - sz, sz * 2, sz * 2);
  }
  ctx.restore();
}

// warm light leak (screen blend radial)
export function leak(ctx, x, y, r, rgb, a) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(0.45, `rgba(${rgb},${a * 0.35})`); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.restore();
}

// tilt-shift depth of field on whatever is already on ctx: blurred copy masked to the top/bottom bands
let TS = null;
export function tiltShift(ctx, W, H, o = {}) {
  if (!TS) TS = { a: cv(W / 2, H / 2), b: cv(W / 4, H / 4), c: cv(W / 8, H / 8), full: cv(W, H) };
  const { a, b, c, full } = TS;
  for (const [dst, src] of [[a, ctx.canvas], [b, a], [c, b]]) { const g = dst.getContext('2d'); g.imageSmoothingQuality = 'high'; g.clearRect(0, 0, dst.width, dst.height); g.drawImage(src, 0, 0, dst.width, dst.height); }
  const fg = full.getContext('2d'); fg.globalCompositeOperation = 'source-over'; fg.clearRect(0, 0, W, H); fg.imageSmoothingQuality = 'high';
  fg.drawImage(c, 0, 0, W, H);
  fg.globalCompositeOperation = 'destination-in';
  const top = o.top ?? 0.34, bot = o.bottom ?? 0.1, s = o.strength ?? 1;
  const gr = fg.createLinearGradient(0, 0, 0, H);
  gr.addColorStop(0, `rgba(0,0,0,${s})`); gr.addColorStop(top, 'rgba(0,0,0,0)'); gr.addColorStop(1 - bot, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(0,0,0,${s * 0.9})`);
  fg.fillStyle = gr; fg.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalCompositeOperation = 'source-over'; ctx.drawImage(full, 0, 0); ctx.restore();
}

// shared "story" grade on the WORLD layer (before UI): warm highlights from the key side, teal shadows, lifted blacks
export function grade(ctx, W, H, o = {}) {
  ctx.save();
  ctx.globalCompositeOperation = 'soft-light';
  const g = ctx.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, `rgba(255,196,140,${o.warm ?? 0.22})`); g.addColorStop(1, `rgba(20,90,110,${o.teal ?? 0.22})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'lighten'; ctx.fillStyle = o.floor || 'rgb(9,16,30)'; ctx.fillRect(0, 0, W, H); // lifted blacks: deep navy, never pure black
  ctx.globalCompositeOperation = 'source-over';
  const vg = ctx.createRadialGradient(W / 2, H * 0.52, H * 0.42, W / 2, H * 0.52, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(3,6,12,${o.vignette ?? 0.38})`);
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// thick, phone-readable arrow along screen points (draw-on p 0..1) with dark under-stroke and a big head
export function arrow(ctx, pts, p, o = {}) {
  if (p <= 0 || pts.length < 2) return;
  let L = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let want = L * F.clamp(p), out = [pts[0]];
  for (let i = 1; i < pts.length && want > 0; i++) { const d = seg[i - 1]; if (want >= d) { out.push(pts[i]); want -= d; } else { const k = want / d; out.push([pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k]); want = 0; } }
  const w = o.width || 14, head = o.head || 48, col = o.color || F.PAL.yellow;
  const [hx, hy] = out[out.length - 1], [px, py] = out.length > 1 ? out[out.length - 2] : pts[0];
  const ang = Math.atan2(hy - py, hx - px);
  const shaft = out.slice(); shaft[shaft.length - 1] = [hx - Math.cos(ang) * head * 0.6, hy - Math.sin(ang) * head * 0.6];
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const path = (pp) => { ctx.beginPath(); pp.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); };
  const headPath = (grow) => { ctx.beginPath(); ctx.moveTo(hx + Math.cos(ang) * grow, hy + Math.sin(ang) * grow); ctx.lineTo(hx - Math.cos(ang - 0.5) * (head + grow), hy - Math.sin(ang - 0.5) * (head + grow)); ctx.lineTo(hx - Math.cos(ang + 0.5) * (head + grow), hy - Math.sin(ang + 0.5) * (head + grow)); ctx.closePath(); };
  ctx.strokeStyle = 'rgba(5,10,20,0.75)'; ctx.lineWidth = w + 10; path(shaft); ctx.stroke(); headPath(6); ctx.fillStyle = 'rgba(5,10,20,0.75)'; ctx.fill();
  ctx.strokeStyle = col; ctx.lineWidth = w; path(shaft); ctx.stroke(); headPath(0); ctx.fillStyle = col; ctx.fill();
  ctx.restore();
}

// big two-colour Bebas lines that rise in word by word. lines: [[{w, c}], ...]
export function bigLines(ctx, lines, x, y, lt, o = {}) {
  const size = o.size || 130, lh = size * (o.lh ?? 0.92), per = o.per ?? 0.07, t0 = o.t0 ?? 0;
  let k = 0;
  lines.forEach((words, li) => {
    let cx = x;
    for (const wd of words) {
      const p = F.prog(lt, t0 + k * per, t0 + k * per + 0.32, F.E.outBack); k++;
      const a = F.clamp(p * 1.4);
      F.text(ctx, wd.w, cx, y + li * lh + (1 - p) * size * 0.35, { size, fam: F.FAM.head, weight: 400, color: wd.c || F.PAL.text, alpha: a * (o.alpha ?? 1), tracking: 0.01, stroke: 0, baseline: 'top', shadowBlur: size * 0.18, shadowColor: 'rgba(0,0,0,0.75)' });
      cx += F.measure(ctx, wd.w, { size, fam: F.FAM.head, weight: 400, tracking: 0.01 }) + size * 0.24;
    }
  });
}

// readable plate behind a text block (crisp rounded rect, 80% navy, accent bar)
export function plate(ctx, x, y, w, h, o = {}) {
  ctx.save(); ctx.globalAlpha *= o.alpha ?? 1;
  ctx.fillStyle = o.bg || 'rgba(8,14,26,0.82)'; F.round(ctx, x, y, w, h, o.r ?? 12); ctx.fill();
  if (o.bar !== false) { ctx.fillStyle = o.bar || F.PAL.hero; ctx.fillRect(x, y + 10, 8, h - 20); }
  ctx.restore();
}

// replace starry black above the horizon with an atmospheric sky (deep blue to haze at the limb).
// The limb is found per screen column by ray-casting the camera against the unit sphere, so the sky follows the curve.
import * as THREE from '../../three.module.min.js';
function limbY(g, x, W, H) {
  const cam = g.camera, o = cam.position, v = new THREE.Vector3();
  const hit = (y) => { v.set(x / W * 2 - 1, 1 - y / H * 2, 0.5).unproject(cam).sub(o).normalize(); const b = o.dot(v), c = o.lengthSq() - 1; return b * b - c > 0 && -b > 0; };
  if (hit(0)) return 0; if (!hit(H)) return H;
  let lo = 0, hi = H; for (let i = 0; i < 18; i++) { const m = (lo + hi) / 2; if (hit(m)) hi = m; else lo = m; } return hi;
}
export function sky(ctx, g, W, H, o = {}) {
  const N = 16, pts = []; let ymax = 0;
  for (let i = 0; i <= N; i++) { const x = W * i / N, y = limbY(g, x, W, H); pts.push([x, y]); ymax = Math.max(ymax, y); }
  if (ymax <= 1) return;
  const ymin = Math.min(...pts.map(p => p[1]));
  ctx.save(); ctx.globalCompositeOperation = 'lighten';
  ctx.beginPath(); ctx.moveTo(0, 0); for (const [x, y] of pts) ctx.lineTo(x, y + 2); ctx.lineTo(W, 0); ctx.closePath();
  const gr = ctx.createLinearGradient(0, 0, 0, ymax + 2);
  gr.addColorStop(0, o.top || 'rgb(12,28,56)'); gr.addColorStop(Math.max(0.05, ymin / (ymax + 2)) * 0.8, o.mid || 'rgb(34,78,132)'); gr.addColorStop(1, o.hor || 'rgb(130,180,222)');
  ctx.fillStyle = gr; ctx.fill();
  ctx.restore();
}
