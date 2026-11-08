// Minimal film.html-compatible runtime for stand-alone ep02 test pages (payoff_test.html, toolkit_test.html).
// Frames are FILM frames at 30 fps, so timing markers map 1:1 (tools/frames.py prints them). Same scene contract as film.html.
import * as F from '/lib/fx.js';
import { setup, frameStart, frameEnd } from './shared.js';
export function runPage(build) {
  const P = new URLSearchParams(location.search);
  const W = +P.get('w') || 1920, H = +P.get('h') || 1080, FPS = +P.get('fps') || 30, Q = JSON.parse(P.get('q') || '{}');
  const comp = document.createElement('canvas'); comp.width = W; comp.height = H; document.body.appendChild(comp); const cx = comp.getContext('2d');
  const layer = document.createElement('canvas'); layer.width = W; layer.height = H; const la = layer.getContext('2d');
  const imgs = {}, log = (s) => fetch('/log', { method: 'POST', body: String(s) });
  const api = { W, H, FPS, F, Q, log, cues: [], cue(t, name, g = -6) { this.cues.push({ t: +t.toFixed(3), name, gain_db: g }); },
    img: (s) => imgs[s], async loadImages(list) { for (const s of list) imgs[s] = await new Promise((r, j) => { const i = new Image(); i.onload = () => r(i); i.onerror = j; i.src = s.startsWith('/') ? s : '/' + s; }); },
    timing: null, T(m, w = 'start') { const v = api.timing.markers[m]; if (!v) throw new Error('missing marker ' + m); return w === 'end' ? v.end : v.start; } };
  const scenes = []; let kit;
  window.ready = (async () => {
    api.timing = await (await fetch('/ep/ep02/timing.json')).json();
    kit = await setup(api);
    const r = await build(api, kit, scenes);
    scenes.push(frameStart(kit));
    scenes.sort((a, b) => (a.layer || 0) - (b.layer || 0) || a.t0 - b.t0);
    if (r) log(`[test] shot ${r.t0.toFixed(2)}-${r.t1.toFixed(2)} s = frames ${Math.ceil(r.t0 * FPS)}-${Math.floor(r.t1 * FPS)}`);
  })();
  window.renderFrame = async (f) => {
    const t = f / FPS;
    cx.globalAlpha = 1; cx.fillStyle = '#05070D'; cx.fillRect(0, 0, W, H);
    for (const s of scenes) {
      if (t < s.t0 || t >= s.t1) continue;
      const lt = t - s.t0, a = Math.min(1, s.fadeIn ? lt / s.fadeIn : 1, s.fadeOut ? (s.t1 - t) / s.fadeOut : 1);
      if (a < 0.999) { la.setTransform(1, 0, 0, 1, 0, 0); la.clearRect(0, 0, W, H); await s.draw(la, lt, t, api); cx.save(); cx.globalAlpha = Math.max(0, a); cx.drawImage(layer, 0, 0); cx.restore(); }
      else { cx.save(); await s.draw(cx, lt, t, api); cx.restore(); }
    }
    frameEnd(kit, f);
  };
  window.grabBlob = () => new Promise(r => comp.toBlob(r, 'image/jpeg', 0.95));
}
