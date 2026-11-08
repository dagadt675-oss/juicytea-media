// Myth Juice ep02 "Why Can't You See Most of Hawaii? (Look Down)": the orchestrator in the film.html contract.
// Render: node still.cjs --page film.html --q '{"ep":"ep02"}' --frames 0,90 --outdir DIR   (Q.only: "ch1".."ch6", Q.draft, Q.qc, Q.strict, Q.dev)
// Each chapter module chN.js exports build(api, kit, scenes) and pushes its scenes with the shared toolkit (shared.js, API.md).
// Base shots (layer 0) must cover every frame: uncovered stretches get a placeholder (navy gradient, logged) until a chapter fills them.
import { setup, frameStart, frameEnd } from './shared.js';
import * as F from '../../lib/fx.js';
export const scenes = [];
let KIT = null;
export async function init(api) {
  const kit = KIT = await setup(api);
  const only = api.Q.only;
  for (let n = 1; n <= 6; n++) {
    if (only && only !== 'ch' + n) continue;
    const mod = await import(`./ch${n}.js`);
    const before = scenes.length;
    await mod.build(api, kit, scenes);
    for (const s of scenes.slice(before)) s.chapter = n;
  }
  // placeholders for every uncovered stretch of the base layer (0 .. film end)
  const base = scenes.filter(s => (s.layer || 0) === 0).map(s => [s.t0, s.t1]).sort((a, b) => a[0] - b[0]);
  const gaps = []; let cur = 0;
  for (const [a, b] of base) { if (a > cur + 1e-6) gaps.push([cur, a]); cur = Math.max(cur, b); }
  if (cur < kit.K.end) gaps.push([cur, kit.K.end]);
  for (const [a, b] of gaps) scenes.push(placeholder(a, b, api));
  if (gaps.length) api.log(`[edit] ${gaps.length} uncovered stretches use placeholders: ${gaps.slice(0, 6).map(g => g.map(v => v.toFixed(1)).join('-')).join(', ')}${gaps.length > 6 ? ' ...' : ''}`);
  scenes.push(frameStart(kit));
}
// no vignette or grain on top: the shared grade already ran on every stage; log type QC and per-stage timings
export function post(ctx, t, f, api) { if (KIT) frameEnd(KIT, f); }
function placeholder(t0, t1, api) {
  return { id: 'placeholder', t0, t1, layer: 0, draw(ctx, lt, t) {
    const g = ctx.createLinearGradient(0, 0, 0, api.H); g.addColorStop(0, '#0B1D28'); g.addColorStop(1, '#05070D');
    ctx.fillStyle = g; ctx.fillRect(0, 0, api.W, api.H);
    if (api.Q.dev) F.text(ctx, `PLACEHOLDER ${t.toFixed(1)} s`, api.W / 2, api.H / 2, { size: 60, fam: 'Barlow Condensed', weight: 800, align: 'center', color: '#3DE3FF' });
  } };
}
