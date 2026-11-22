// ch6: 2D orthographic Gondwana (rigid present-day outlines rotated with paleo/tracks.json point pairs) and
// paleo coastline stills for the filmstrip. Simplified reconstructions (two tracked points per plate).
import * as F from '../../lib/fx.js';
import { loadGeo, rings } from '../../lib/geo.js';
import { v3, frameOf, rotFrames, applyR, orthoView, orthoDisc, orthoShade, orthoFillV } from './ch6_lib.js';
const { PAL, clamp } = F;

const PAIRS = { SA: ['samerica_c', 'cape_horn'], AF: ['africa_c', 'cape_agulhas'], IN: ['india_c', 'kanyakumari'], AU: ['australia_c', 'tasmania_s'], AN: ['antarctica_c', 'south_pole'], MG: ['madagascar_s', 'africa_c'] };
const ARABIA = new Set(['Saudi Arabia', 'Yemen', 'Oman', 'United Arab Emirates', 'Qatar', 'Kuwait', 'Jordan', 'Israel', 'Palestine']);
const INDIA = new Set(['India', 'Sri Lanka', 'Bangladesh', 'Nepal', 'Bhutan']);
const AUS = new Set(['Australia', 'Papua New Guinea', 'New Zealand']);
export const GCOL = { SA: PAL.hero, AF: PAL.hero, IN: PAL.hero, MG: '#d8c39a', AU: '#d8c39a', AN: '#eef3f8' };

export async function createGond(api) {
  const tracks = await api.loadJSON('paleo/tracks.json');
  const C = await loadGeo('ne_110m_admin_0_countries');
  const groups = { SA: [], AF: [], IN: [], AU: [], AN: [], MG: [] };
  for (const f of C.features) {
    const P = f.properties, name = P.ADMIN || P.NAME, cont = P.CONTINENT;
    let gk = null;
    if (cont === 'South America') gk = 'SA';
    else if (name === 'Madagascar') gk = 'MG';
    else if (cont === 'Africa' || ARABIA.has(name)) gk = 'AF';
    else if (INDIA.has(name)) gk = 'IN';
    else if (AUS.has(name)) gk = 'AU';
    else if (cont === 'Antarctica') gk = 'AN';
    if (!gk) continue;
    for (const r of rings(f)) if (r.length > 3) groups[gk].push(r.map(([lo, la]) => v3(la, lo)));
  }
  const at = (name, T) => {
    const tr = tracks[name]; T = clamp(T, 0, 200);
    const i = Math.min(199, Math.floor(T)), f = T - i, a = tr[i], b = tr[i + 1];
    let dl = b[0] - a[0]; if (dl > 180) dl -= 360; if (dl < -180) dl += 360;
    return v3(a[1] + (b[1] - a[1]) * f, a[0] + dl * f);
  };
  const E0 = {}; for (const k in PAIRS) E0[k] = frameOf(at(PAIRS[k][0], 0), at(PAIRS[k][1], 0));
  const rot = (k, T) => rotFrames(E0[k], frameOf(at(PAIRS[k][0], T), at(PAIRS[k][1], T)));
  const G = {
    groups, rot, at,
    // rotated rings of group k at time T (Ma), optional extra rotation matrix X applied after
    ringsAt(k, T, X) { const R = rot(k, T); return groups[k].map(r => r.map(p => { const q = applyR(R, p); return X ? applyR(X, q) : q; })); },
    // point on plate k (present lat/lon) at T
    ptAt(k, lat, lon, T) { return applyR(rot(k, T), v3(lat, lon)); },
    // draw the disc + all groups; per-group T (object) or single T
    draw(ctx, V, Tk, o = {}) {
      orthoDisc(ctx, V, o.disc || {});
      for (const k of ['AN', 'AU', 'IN', 'MG', 'SA', 'AF']) {
        const T = typeof Tk === 'number' ? Tk : Tk[k];
        const col = (o.colors && o.colors[k]) || GCOL[k];
        orthoFillV(ctx, V, this.ringsAt(k, T, o.extra && o.extra[k]), { color: col, alpha: (o.alpha && o.alpha[k]) ?? 1, stroke: 'rgba(255,255,255,0.35)', lw: 1.2 });
      }
      orthoShade(ctx, V);
    },
  };
  return G;
}

// paleo coastline still (all land cream) on an ortho disc; polys = [[lon,lat],...]
export function drawPaleoPolys(ctx, V, polys, o = {}) {
  orthoDisc(ctx, V, o.disc || {});
  const RV = polys.map(r => r.map(([lo, la]) => v3(la, lo)));
  orthoFillV(ctx, V, RV, { color: o.land || '#d8c39a', stroke: 'rgba(255,255,255,0.4)', lw: 1.4 });
  orthoShade(ctx, V);
}
export { orthoView };
