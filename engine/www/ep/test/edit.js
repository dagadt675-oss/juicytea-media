import * as F from '../../lib/fx.js';
import { globeShot, photoShot, statShot, barsShot, textShot } from '../../lib/shots.js';
import { loadGeo, findFeature, rings, fillEquirect, makeCanvas, centroid } from '../../lib/geo.js';
export const scenes = [];
export async function init(api) {
  await api.globe();
  await api.loadImages(['ep/test/apollo.jpg']);
  const fc = await loadGeo('ne_50m_admin_0_countries');
  const GRL = findFeature(fc, 'Greenland'), DRC = findFeature(fc, 'Democratic Republic of the Congo');
  const b = [-75, 58, -10, 84]; const ov = makeCanvas(2048, 1024); fillEquirect(ov, b, [GRL], { color: '#FF5A36', alpha: 0.75, glow: 24 });
  scenes.push(textShot({ t0: 0, t1: 2.2, words: ['THE', 'MAP', 'IS', '*LYING'], bg: (ctx, lt, api) => api.drawGlobe(ctx, { lat: 30, lon: -40, alt: 2.8 }, { relief: 0 }), dim: 0.3 }));
  scenes.push(globeShot({ t0: 2.2, t1: 8, keys: [{ t: 0, lat: 30, lon: -40, alt: 2.8 }, { t: 3, lat: 50, lon: -35, alt: 1.2, tilt: 15 }], overlay: { canvas: ov, bounds: b },
    look: lt => ({ ovAlpha: F.prog(lt, 2.4, 3.2), dim: 0.3 * F.prog(lt, 2.4, 3.2) }),
    outlines: [{ rings: rings(GRL), t: 2.6, d: 1.2 }],
    labels: [{ t: 3.2, text: 'GREENLAND', lat: 72, lon: -40, dx: 160, dy: -40, ring: true }],
    moves: [{ t: 4.2, d: 1.6, rings: rings(DRC), from: centroid(rings(DRC)), to: [62, -45], color: '#FFD23F' }] }));
  scenes.push(photoShot({ t0: 8, t1: 11, src: 'ep/test/apollo.jpg', framed: true, blurBg: true, credit: 'NASA / APOLLO 17', caption: 'DEC 7, 1972' }));
  scenes.push(statShot({ t0: 11, t1: 14, kicker: 'AREA', value: 836330, unit: 'SQ MI', sub: 'Greenland, true size', bg: (ctx, lt, api) => api.drawGlobe(ctx, { lat: 70, lon: -40, alt: 1.4 }, { relief: 0.8 }) }));
  scenes.push(barsShot({ t0: 14, t1: 18, title: 'TRUE SIZE', unit: 'K SQ MI', items: [{ label: 'AFRICA', value: 11700 }, { label: 'GREENLAND', value: 836 }, { label: 'MEXICO', value: 761 }], hl: 1 }));
}
