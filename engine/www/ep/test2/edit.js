import * as F from '../../lib/fx.js';
import { globeShot, textShot } from '../../lib/shots.js';
import { region, allRings, WorldOverlay, dripArrow, planetGag, PaleoOverlay, trackAt, yearsChip } from '../../lib/beats.js';
import { strokeProjected } from '../../lib/geo.js';
export const scenes = [];
export async function init(api) {
  await api.globe();
  const names = ['south america', 'africa', 'india', 'greenland', 'florida', 'baja', 'kamchatka'];
  const R = {}; for (const n of names) R[n] = await region(n);
  const tips = { 'south america': [-55.9, -67.3], africa: [-34.8, 20.0], india: [8.1, 77.5], greenland: [59.8, -43.9], florida: [25.1, -80.9], baja: [22.9, -109.9], kamchatka: [50.9, 156.7] };
  const ov = new WorldOverlay();
  const at = names.map((n, i) => 1.0 + i * 0.55);
  scenes.push(globeShot({ t0: 0, t1: 6, keys: [{ t: 0, lat: 18, lon: -40, alt: 2.9 }, { t: 6, lat: 10, lon: 40, alt: 2.7 }], drift: 0,
    look: lt => { const layers = names.filter((n, i) => lt >= at[i]).map(n => ({ key: n, features: R[n], color: '#FF5A36', alpha: 0.85 })); ov.set(layers, api.g); return { ovAlpha: 1, dim: 0.25 * F.prog(lt, 0.8, 1.5) }; },
    extra: (ctx, lt) => { names.forEach((n, i) => { if (lt < at[i]) return; const q = api.g.project(...tips[n]); if (!q.visible) return; dripArrow(ctx, q.x, q.y + 6, F.prog(lt, at[i], at[i] + 0.6), { len: 70 }); }); },
  }));
  const gag = await planetGag(api, 'gag', { clips: [[6, 'Walk'], [8.2, 'HitRecieve', { once: true, fade: 0.15 }], [9.0, 'Death', { once: true, fade: 0.2 }]] });
  scenes.push({ t0: 6, t1: 10.5, draw: (ctx, lt, t) => gag.draw(ctx, t, { planetRot: [Math.min(lt, 2.2) * 0.25, 0.5, 0], camAng: 0.3 - lt * 0.05 }) });
  const pal = new PaleoOverlay(api); const tracks = await api.loadJSON('paleo/tracks.json');
  scenes.push(globeShot({ t0: 10.5, t1: 16, keys: [{ t: 0, lat: -45, lon: 20, alt: 2.6 }, { t: 5.5, lat: -60, lon: 10, alt: 2.2 }], drift: 0,
    look: () => ({ flatBase: 1, ovAlpha: 1, ovMul: 1, nightAmt: 0, relief: 0 }),
    pre: async (lt) => { await pal.draw(F.prog(lt, 0.3, 5.0, F.E.inOut) * 160); },
    extra: async (ctx, lt) => { const T = F.prog(lt, 0.3, 5.0, F.E.inOut) * 160; yearsChip(ctx, api.W, T);
      for (const n of ['cape_horn', 'cape_agulhas', 'kanyakumari', 'tasmania_s']) { const p = trackAt(tracks, n, T); if (!p) continue; const q = api.g.project(p[0], p[1]); if (q.visible) F.dot(ctx, q.x, q.y, { r: 8, color: '#FF5A36', ring: (lt * 0.8) % 1 }); } },
  }));
}
