// Episode 01 orchestrator: loads the modules listed in modules.json (ch1, ch2, ch3, ch4, ch5a, ch5b, ch6). Each exports
//   async function build(api, C) -> array of scenes
// where C = {n, t0, t1, segs: [{id, start, end, text}], T(marker, which), seg(id) -> {start,end}}.
// q.only = N builds only chapter N (for fast per-chapter checks; frames outside it render as plain background).
import * as F from '../../lib/fx.js';
export const scenes = [];
export async function init(api) {
  const timing = api.timing;
  const meta = await api.loadJSON('ep/ep01/modules.json'); // [{id:'ch1', chapter, t0, t1}]
  const only = api.Q.only ? String(api.Q.only) : null;
  for (const ch of meta) {
    if (only && ch.id !== only && ch.id !== 'ch' + only) continue;
    let mod;
    try { mod = await import(`./${ch.id}.js`); } catch (e) { api.log('module ' + ch.id + ' missing: ' + e.message); continue; }
    const segs = timing.segments.filter(s => s.start >= ch.t0 - 0.01 && s.start < ch.t1 - 0.01);
    const C = {
      n: ch.chapter, id: ch.id, t0: ch.t0, t1: ch.t1, segs,
      T: (m, w) => api.T(m, w),
      seg: (id) => timing.segments.find(s => s.id === id),
      words: (id) => timing.words.filter(w => w.seg === id),
    };
    const list = await mod.build(api, C);
    for (const s of list) { s.id = s.id || ch.id; scenes.push(s); }
  }
  // safety net: a neutral background under everything so no frame is ever empty
  scenes.push({ t0: 0, t1: 1e9, layer: -100, id: 'bg', draw: (ctx) => { ctx.fillStyle = '#05070D'; ctx.fillRect(0, 0, api.W, api.H); } });
}
export function post(ctx, t, f, api) { F.post(ctx, api.W, api.H, f, { vignette: 0.42 }); }
