// Shot factories: each returns a scene {t0, t1, fadeIn, fadeOut, layer, draw(ctx, lt, t, api)}.
// Everything is a pure function of time -> deterministic frames.
import * as F from './fx.js';
import { slerpLL } from './globe.js';
import { strokeProjected, rings, fillProjected, gcLine, projectPath, moveRings } from './geo.js';
const { PAL, E, prog, env, clamp, lerp } = F;

// ---- camera keyframes for the globe ----
// keys: [{t, lat, lon, alt, tilt?, heading?, fov?, ease?}] (t relative to shot start). drift: deg/s heading drift for life.
export function camAt(keys, lt, drift = 0) {
  if (lt <= keys[0].t) return withDrift(keys[0], lt, drift);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (lt <= b.t) {
      const k = (b.ease || E.inOut)(clamp((lt - a.t) / Math.max(1e-6, b.t - a.t)));
      const ll = slerpLL([a.lat, a.lon], [b.lat, b.lon], k);
      return withDrift({
        lat: ll[0], lon: ll[1],
        alt: Math.exp(lerp(Math.log(a.alt), Math.log(b.alt), k)),
        tilt: lerp(a.tilt || 0, b.tilt || 0, k), heading: lerp(a.heading || 0, b.heading || 0, k), fov: lerp(a.fov || 34, b.fov || 34, k),
        sunAz: lerp(a.sunAz ?? -35, b.sunAz ?? -35, k), sunEl: lerp(a.sunEl ?? 28, b.sunEl ?? 28, k),
      }, lt, drift);
    }
  }
  return withDrift(keys[keys.length - 1], lt, drift);
}
function withDrift(s, lt, drift) {
  // gentle life: slow heading drift + tiny altitude breathing so no frame is ever static
  return Object.assign({}, s, { heading: (s.heading || 0) + drift * lt, alt: s.alt * (1 + 0.006 * Math.sin(lt * 0.7)) });
}

// ---- globe shot ----
// o: {t0, t1, keys, drift, look: {dim, desat, ...} | (lt)=>look, overlay: {canvas, bounds} , outlines: [{rings, t, d, color, width, glow}],
//     labels: [{t, d?, text, lat, lon, dx, dy, anchor}], arcs: [{t, d, from, to, lift, color, width, dash}], markers: [{t, lat, lon, color}],
//     moves: [{t, d, rings, from, to, color}], extra(ctx, lt, api)}
export function globeShot(o) {
  return {
    t0: o.t0, t1: o.t1, fadeIn: o.fadeIn ?? 0, fadeOut: o.fadeOut ?? 0, layer: o.layer || 0, id: o.id,
    async draw(ctx, lt, t, api) {
      const g = api.g;
      if (o.overlay !== undefined && api._ovOwner !== o) { // install this shot's overlay once
        if (o.overlay) g.setOverlay(o.overlay.canvas, o.overlay.bounds); else g.setOverlay(null);
        api._ovOwner = o;
      }
      if (o.patch !== undefined && api._patchOwner !== o) { await g.setPatch(o.patch ? o.patch.url : null, o.patch ? o.patch.bounds : null); api._patchOwner = o; }
      if (o.pre) await o.pre(lt, api);   // update overlays/patches BEFORE the globe renders (no 1-frame lag)
      const cam = camAt(o.keys, lt, o.drift ?? 0.25);
      const look = Object.assign({ dim: 0, desat: 0.12, ovAlpha: 0, relief: 0.8, nightAmt: 1, exposure: 1.25 }, typeof o.look === 'function' ? o.look(lt) : (o.look || {}));
      api.drawGlobe(ctx, Object.assign({}, cam, o.sun || {}), look);
      for (const m of o.moves || []) {
        const p = prog(lt, m.t, m.t + (m.d || 2), E.inOut);
        if (lt < m.t - 0.01) continue;
        const R = moveRings(m.rings, m.from, m.to, p, m.spin || 0);
        fillProjected(ctx, g, R, { color: m.color || PAL.yellow, alpha: (m.alpha ?? 0.55) * prog(lt, m.t - 0.3, m.t + 0.2) });
        strokeProjected(ctx, g, R, { color: m.stroke || '#ffffff', width: 2 });
      }
      for (const ol of o.outlines || []) {
        if (lt < ol.t) continue;
        strokeProjected(ctx, g, ol.rings, { p: prog(lt, ol.t, ol.t + (ol.d ?? 1.4), E.out), color: ol.color || '#ffffff', width: ol.width || 2.2, glow: ol.glow, dash: ol.dash, alpha: ol.alpha });
      }
      for (const a of o.arcs || []) {
        if (lt < a.t) continue;
        const pts = projectPath(g, gcLine(a.from, a.to, a.n || 90, a.lift ?? 0.03));
        const head = F.glowPath(ctx, pts, { p: prog(lt, a.t, a.t + (a.d || 1.5), E.inOut), color: a.color || PAL.cyan, width: a.width || 3.5, dash: a.dash });
        if (a.headDot && head) F.dot(ctx, head[0], head[1], { r: 6, color: a.color || PAL.cyan });
      }
      for (const m of o.markers || []) {
        if (lt < m.t) continue;
        const q = g.project(m.lat, m.lon); if (!q.visible) continue;
        F.dot(ctx, q.x, q.y, { r: m.r || 7, color: m.color || PAL.hero, ring: ((lt - m.t) * 0.7) % 1 });
      }
      for (const L of o.labels || []) {
        if (lt < L.t || (L.d && lt > L.t + L.d)) continue;
        const q = g.project(L.lat, L.lon); if (!q.visible && !L.screen) continue;
        const a = L.d ? env(lt, L.t, L.t + L.d, 0.3, 0.3) : prog(lt, L.t, L.t + 0.35);
        const x = L.screen ? L.screen[0] : q.x + (L.dx ?? 120), y = L.screen ? L.screen[1] : q.y + (L.dy ?? -90);
        F.pill(ctx, L.text, x, y, { anchor: L.anchor || 'left', leader: L.noLeader ? null : [q.x, q.y], ring: L.ring ? ((lt - L.t) * 0.8) % 1 : null, alpha: a, size: L.size || 32, color: L.color, border: L.border });
      }
      if (o.extra) await o.extra(ctx, lt, api, cam);
    },
  };
}

// ---- photo / image shot with Ken Burns, optional caption & credit ----
export function photoShot(o) {
  return {
    t0: o.t0, t1: o.t1, fadeIn: o.fadeIn ?? 0.35, fadeOut: o.fadeOut ?? 0, layer: o.layer || 0, id: o.id,
    draw(ctx, lt, t, api) {
      const img = api.img(o.src); const dur = o.t1 - o.t0;
      ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, api.W, api.H);
      if (o.blurBg && img) { // blurred full-bleed backdrop behind a framed photo
        ctx.save(); ctx.filter = 'blur(24px) brightness(0.45)'; F.kenburns(ctx, img, lt / dur, -40, -40, api.W + 80, api.H + 80, { from: [0.5, 0.5, 1.1], to: [0.5, 0.5, 1.2] }); ctx.restore();
      }
      if (o.framed) {
        const w = o.w || 1280, h = o.h || 720, x = (api.W - w) / 2 + (o.dx || 0), y = (api.H - h) / 2 + (o.dy || 0);
        F.kenburns(ctx, img, lt / dur, x, y, w, h, { from: o.from, to: o.to, frame: true, grade: o.grade });
      } else F.kenburns(ctx, img, lt / dur, 0, 0, api.W, api.H, { from: o.from || [0.5, 0.5, 1.0], to: o.to || [0.5, 0.5, 1.14], grade: o.grade });
      if (o.credit) F.text(ctx, o.credit, api.W - 36, api.H - 30, { size: 20, fam: F.FAM.label, weight: 500, color: 'rgba(244,246,250,0.65)', align: 'right', tracking: 0.06, shadowBlur: 6 });
      if (o.caption) F.pill(ctx, o.caption, 80, api.H - 120, { anchor: 'left', size: 30, alpha: prog(lt, 0.4, 0.8) * (o.captionOut ? 1 - prog(lt, o.captionOut, o.captionOut + 0.3) : 1) });
      if (o.extra) o.extra(ctx, lt, api);
    },
  };
}

// ---- big statistic card over a (dimmed) background drawer ----
export function statShot(o) {
  return {
    t0: o.t0, t1: o.t1, fadeIn: o.fadeIn ?? 0.3, fadeOut: o.fadeOut ?? 0.3, layer: o.layer || 0, id: o.id,
    async draw(ctx, lt, t, api) {
      if (o.bg) await o.bg(ctx, lt, api); else { ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, api.W, api.H); }
      const W = api.W, H = api.H;
      if (o.dimBg !== false) { ctx.fillStyle = `rgba(3,5,10,${0.55 * prog(lt, 0, 0.5)})`; ctx.fillRect(0, 0, W, H); }
      const p = prog(lt, o.rollAt ?? 0.25, (o.rollAt ?? 0.25) + (o.roll ?? 1.2), E.outExpo);
      if (o.kicker) F.text(ctx, o.kicker, W / 2, H / 2 - 150, { size: 40, fam: F.FAM.label, weight: 700, tracking: 0.3, align: 'center', color: o.accent || PAL.hero, alpha: prog(lt, 0.05, 0.4) });
      if (o.value != null) F.counter(ctx, o.from ?? 0, o.value, p, W / 2, H / 2 + 60, { size: o.size || 220, unit: o.unit, decimals: o.decimals, prefix: o.prefix, format: o.format, color: o.color, alpha: prog(lt, 0.1, 0.4) });
      if (o.big) F.headline(ctx, o.big.split(' ').map(w => w.startsWith('*') ? { w: w.slice(1), c: o.accent || PAL.hero } : w), W / 2, H / 2 + 60, lt, { size: o.size || 200, t0: 0.15 });
      if (o.sub) F.text(ctx, o.sub, W / 2, H / 2 + 150, { size: 44, fam: F.FAM.body, weight: 600, align: 'center', color: PAL.sub, alpha: prog(lt, (o.rollAt ?? 0.25) + 0.6, (o.rollAt ?? 0.25) + 1.0) });
    },
  };
}

// ---- horizontal comparison bars (animated), e.g. heights/areas ----
export function barsShot(o) {
  return {
    t0: o.t0, t1: o.t1, fadeIn: o.fadeIn ?? 0.3, fadeOut: o.fadeOut ?? 0.3, layer: o.layer || 0, id: o.id,
    async draw(ctx, lt, t, api) {
      const W = api.W, H = api.H;
      if (o.bg) await o.bg(ctx, lt, api); else { ctx.fillStyle = '#070A12'; ctx.fillRect(0, 0, W, H); }
      ctx.fillStyle = 'rgba(3,5,10,0.55)'; ctx.fillRect(0, 0, W, H);
      if (o.title) F.text(ctx, o.title, 160, 170, { size: 64, fam: F.FAM.head, tracking: 0.04, alpha: prog(lt, 0, 0.4) });
      const max = Math.max(...o.items.map(i => i.value));
      const top = 260, rowH = Math.min(140, (H - top - 120) / o.items.length), bw = W - 160 - 520;
      o.items.forEach((it, i) => {
        const t0 = (o.stagger ?? 0.35) * i + 0.3 + (it.at || 0);
        const p = prog(lt, t0, t0 + 1.1, E.outExpo);
        const y = top + i * rowH;
        F.text(ctx, it.label, 160, y + rowH * 0.42, { size: 38, fam: F.FAM.label, weight: 700, tracking: 0.06, alpha: prog(lt, t0 - 0.2, t0 + 0.2) });
        ctx.fillStyle = 'rgba(255,255,255,0.07)'; F.round(ctx, 160, y + rowH * 0.52, bw, rowH * 0.28, 8); ctx.fill();
        ctx.fillStyle = it.color || (i === o.hl ? PAL.hero : PAL.cyan); F.round(ctx, 160, y + rowH * 0.52, Math.max(2, bw * it.value / max * p), rowH * 0.28, 8); ctx.fill();
        F.counter(ctx, 0, it.value, p, 160 + bw + 30, y + rowH * 0.80, { size: 54, align: 'left', unit: it.unit || o.unit, decimals: it.decimals || 0, alpha: prog(lt, t0, t0 + 0.3) });
      });
    },
  };
}

// ---- title / text card on a background drawer ----
export function textShot(o) {
  return {
    t0: o.t0, t1: o.t1, fadeIn: o.fadeIn ?? 0.25, fadeOut: o.fadeOut ?? 0.25, layer: o.layer || 0, id: o.id,
    async draw(ctx, lt, t, api) {
      if (o.bg) await o.bg(ctx, lt, api);
      if (o.dim) { ctx.fillStyle = `rgba(3,5,10,${o.dim})`; ctx.fillRect(0, 0, api.W, api.H); }
      const words = o.words.map(w => typeof w === 'string' ? (w.startsWith('*') ? { w: w.slice(1), c: o.accent || PAL.hero } : { w }) : w);
      F.headline(ctx, words, o.x ?? api.W / 2, o.y ?? api.H / 2 + 40, lt, { size: o.size || 150, t0: o.in ?? 0.1, per: o.per ?? 0.08, tOut: o.out != null ? o.out : (o.t1 - o.t0) - 0.4, align: o.align });
      if (o.sub) F.text(ctx, o.sub, o.x ?? api.W / 2, (o.y ?? api.H / 2 + 40) + 90, { size: 40, fam: F.FAM.label, weight: 700, tracking: 0.2, align: o.align === 'left' ? 'left' : 'center', color: PAL.sub, alpha: prog(lt, 0.5, 0.9) });
    },
  };
}

// ---- overlay-only scene (lower thirds, captions, counters drawn on top of whatever is below; use layer > 0) ----
export function overlay(o) { return { t0: o.t0, t1: o.t1, layer: o.layer ?? 5, fadeIn: 0, fadeOut: 0, id: o.id, draw: o.draw }; }
