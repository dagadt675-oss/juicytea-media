// Chapter 1 "Only the Top" (s001-s025, 0.00-93.81 s, no card; base shots to t1x). Every beat is keyed to Rodney's markers (K).
//   s001-s003  frame 1 = the NO OCEAN thumbnail (final_ep02_1.jpg) in motion: drained Big Island, thin white line on today's coast,
//              NO OCEAN in dark ink on the sky; tilt down at {most}, coast pulse at {under}, the USGS postcard lands on the dry cap at
//              {card}, the cap takes the hero fill and outline at {top}.
//   s004-s006  one continuous camera: flight NW while the sea refills, names on their words, SEA LEVEL gauge rolls to 400 FT on
//              {ft400}, the three outlines merge into the -400 ft contour at {one}, ONE ISLAND in dark ink top-left.
//   s007       the same camera dives from the ONE ISLAND framing to a low golden pass over the dry land north of Lānaʻi; three seabirds
//              cross; LAST ICE AGE (Anton, plate, cyan bar, top centre) on {ice}.
//   s008       GAG (cut on the music dip): the paper tourist walks across the dry seafloor from Lānaʻi toward the camera (West Maui is
//              behind it), one hop landing on the paper tap, tips his hat to camera on {ferry}, his bag scrapes after him in the gap.
//   s009-s011  {look}: the camera cranes up from him and pitches down, then rides west over the dry floor as the sea falls from -400 ft
//              toward -1,000 m (SEA LEVEL gauge, marker only); the slope ahead fades into blue depth on {nobottom}; it passes the edge
//              of the shallow shelf on {ledge} and tips over the slope on {plunge}.
//   s012-s013  pull back and swing west: Penguin Bank (a flat table, hero fill + white outline of its top above -70 m on the 115 m
//              grid, label PENGUIN BANK) high above the water on {bank}; the sea rises back to 0 m from "rose" and drowns the bank on
//              {drowned}; the land bridges flood and the islands separate again.
//   s014-s015  whip-pan (motion blur) to the Big Island's south coast in morning light; one yellow down-arrow pulses on {now}; an eased
//              log-distance push toward Halapē while the light falls to pre-dawn blue.
//   s016-s023  1975, Halapē (solemn: no gags, no comic sound, no stings): the cove at a ~0.5 km oblique in pre-dawn light, the coconut
//              grove (drawn palms at true positions and heights on the 10 m NCEI grid, shaded to the scene), a few small tents,
//              stars; NOVEMBER 1975 (plate) at the start of s016, HALAPĒ label on its pin at {hal}; {woke}: palms shiver, the water
//              ripples, a lantern glows in one tent; {hit}: 6-frame camera jolt, dust off the scarp behind the grove; {lurch}: quick
//              pull-up along the coast; {drop}: the coastal block sinks 3.5 m (the sea level relative to today's post-1975 grid goes
//              from -3.5 m to 0) and the sea floods in among the palms, which stay standing (about 1-2 m of water), with a side-on
//              scale inset (old ground line, new ground, a plain basketball hoop at true scale, no numbers) that fades before the
//              wave; 'rushed': a local surge from the east over the dropped shore (the tents go under); {two}: hold on the flooded
//              grove at first light, desaturated; {morning}: the USGS public-domain photo (img/ch1/halape_1975.jpg) for 3 s, then
//              back to the render of the same grove.
//   s024-s025  pull back to the Big Island's south side, Kīlauea's south flank in the hero fill (approximate boundary: Koaʻe fault
//              zone and East Rift Zone, the coast from the grid), a short yellow arrow seaward on {yards}; {go}: whip-pan NW (motion
//              blur) that lands on windward Oʻahu's green cliffs (region pali) on {did}; the ch2 card rides over it.
// Local helpers (no shared change): spline() C1 camera keys, blurred() sub-frame motion blur for whips, palms/tents/stars/dust/inset.
import { flight, mixState, PLACES, E, PAL, F, MLOOKS, PRESETS, heightGrid, contour, maskTexture } from './shared.js';

const FT = 3.28084, D2R = Math.PI / 180, KM = 111.32;
// one stage for s001-s013: Maui Nui (78 m) inside the legacy Big Island bake (frame 1 = the thumbnail plate), legacy origin and mesh
export const CH1_STAGE = { origin: { lon: -155.6, lat: 19.6 }, midGrid: [1500, 1500] };

// ---------------------------------------------------------------------------------------------------------------- local helpers
// C1 Hermite spline through camera keys [{t, lon, lat, alt, tLon, tLat, tH, fov, ...numbers, stop}]: one velocity curve with no
// stops at inner keys (unless `stop`), zero velocity at both ends; missing fields carry over from the previous key
function spline(keys) {
  const K = keys.map(k => Object.assign({}, k));
  const flds = [...new Set(K.flatMap(k => Object.keys(k)))].filter(f => !['t', 'stop'].includes(f));
  for (let i = 0; i < K.length; i++) for (const f of flds) if (K[i][f] == null) K[i][f] = i ? K[i - 1][f] : 0;
  const n = K.length, tan = {};
  for (const f of flds) tan[f] = K.map((k, i) => { if (k.stop || i === 0 || i === n - 1) return 0; const a = K[i - 1], b = K[i + 1];
    const s0 = (k[f] - a[f]) / (k.t - a.t), s1 = (b[f] - k[f]) / (b.t - k.t); return (s0 * (b.t - k.t) + s1 * (k.t - a.t)) / (b.t - a.t); });
  return (lt) => {
    const o = {};
    if (lt <= K[0].t) { for (const f of flds) o[f] = K[0][f]; return o; }
    if (lt >= K[n - 1].t) { for (const f of flds) o[f] = K[n - 1][f]; return o; }
    let i = 0; while (lt > K[i + 1].t) i++;
    const a = K[i], b = K[i + 1], dt = b.t - a.t, u = (lt - a.t) / dt, u2 = u * u, u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
    for (const f of flds) o[f] = h00 * a[f] + h10 * dt * tan[f][i] + h01 * b[f] + h11 * dt * tan[f][i + 1];
    return o;
  };
}
// scalar spline: keys [{t, v, stop}]
const vspline = (keys) => { const s = spline(keys); return (lt) => s(lt).v; };
// sub-frame motion blur (a 180-degree shutter, n renders averaged) for whip-pan frames inside [w0, w1] (film time); UI is off there
function blurred(shot, w0, w1, n = 6, shutter = 0.5) {
  const inner = shot.draw.bind(shot);
  shot.draw = async function (ctx, lt, t, api) {
    if (t < w0 || t > w1 || api.Q.noblur) return inner(ctx, lt, t, api);
    const A = ctx.globalAlpha, dt = shutter / api.FPS, m = api.Q.draft ? 3 : n;
    for (let k = 0; k < m; k++) { const o = (k / (m - 1) - 0.5) * dt; ctx.save(); ctx.globalAlpha = A / (k + 1); await inner(ctx, lt + o, t + o, api); ctx.restore(); }
  };
  return shot;
}
// await a lazy data step before a shot draws (its mask() runs before world(), so a single still must not miss the data)
function ready(shot, fn) { const d = shot.draw.bind(shot); shot.draw = async function (ctx, lt, t, api) { await fn(); return d(ctx, lt, t, api); }; return shot; }
// seeded hash noise (pure function of its inputs)
const hash = (a, b = 0) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };
const wob = (t, s) => Math.sin(t * 2.3 + s * 6.1) * 0.6 + Math.sin(t * 3.7 + s * 2.9) * 0.4;
// point-in-polygon (lon/lat)
const inPoly = (x, y, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
// lerp between two colours given as [r, g, b]
const mixc = (a, b, p) => a.map((v, i) => Math.round(v + (b[i] - v) * p));
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const t = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f);
  const ch = K.chapter(1);

  // =========================================================================================== s001-s006 (the foundation demo)
  const tDr = t('drained'), tMost = t('most'), tUnder = t('under'), tCard = t('card'), tTop = t('top');
  const fly0 = K.s1('s003') + 0.03, fly1 = fly0 + 1.6;                         // the flight starts as s003 ends (1.6 s, eased)
  const drain0 = fly1 + 0.95, drain1 = lead('ft400');                          // 0 -> -400 ft, lands on {ft400}
  const L400 = -400 / FT;                                                      // -121.92 m: the gauge lands exactly on 400
  const tOne = lead('one');                                                    // ONE ISLAND lands 3 frames before the word
  const TA = tOne + 2.4;                                                       // hand-off to the s007 dive (ONE ISLAND readable 2.1 s)
  const REG = 'mauinui', STAGE = CH1_STAGE;
  const PC = '/ep/ep02/img/postcard_bigisland.jpg';
  let postcard = null;
  try { const r = await fetch(PC, { method: 'HEAD' }); if (r.ok) { await api.loadImages([PC]); postcard = kit.makePostcard(api.img(PC), 'HAWAIʻI'); } } catch (e) { /* fallback below */ }
  const BI = { bbox: [-156.15, 18.85, -154.75, 20.35], step: 1, region: REG, stage: STAGE };
  const MN = { bbox: [-157.75, 20.4, -155.9, 21.35], step: 1, region: REG, stage: STAGE };
  const PBB = { bbox: [-158.05, 20.72, -157.18, 21.22], step: 1, region: REG, stage: STAGE };         // Penguin Bank on the 115 m layer
  const isl = {};
  const getIsl = async () => {
    if (isl.cap) return isl;
    isl.cap = await kit.island(Object.assign({ level: 0, seeds: [PLACES['mauna-loa']] }, BI));
    isl.maui = await kit.island(Object.assign({ level: 0, seeds: [PLACES.maui, PLACES['west-maui']] }, MN));
    isl.molo = await kit.island(Object.assign({ level: 0, seeds: [PLACES.molokai] }, MN));
    isl.lanai = await kit.island(Object.assign({ level: 0, seeds: [PLACES.lanai] }, MN));
    isl.one = await kit.island(Object.assign({ level: L400, seeds: [PLACES.maui, PLACES.molokai, PLACES.lanai] }, MN));
    isl.kaho = await kit.island(Object.assign({ level: L400, seeds: [PLACES.kahoolawe] }, MN));
    const g = isl.one.g; let touch = 0; for (let k = 0; k < g.nx * g.ny; k++) if (isl.one.mask[k] && isl.kaho.mask[k]) touch++;
    if (touch) api.log(`[ch1] WARNING Kaho'olawe joins the fused island at ${L400.toFixed(0)} m on this grid`);
    isl.bridge = kit.bridges(isl.one, [isl.maui, isl.molo, isl.lanai], 11);
    isl.capTex = kit.maskTexture(isl.cap.g, { r: isl.cap.mask });
    isl.mnTex = kit.maskTexture(isl.one.g, { r: isl.bridge, g: isl.kaho.mask });
    // s012: Penguin Bank's flat top = the land above -70 m around the bank (on this grid it joins Molokaʻi only at -80 m)
    isl.pb = await kit.island(Object.assign({ level: -70, seeds: [PLACES['penguin-bank'], [-157.6, 21.0]] }, PBB));
    const gp = isl.pb.g; let molo = false; { const [i, j] = gp.ij(-157.1, 21.13); molo = !!isl.pb.mask[j * gp.nx + i]; }
    if (molo) api.log('[ch1] WARNING Penguin Bank top at -70 m touches Molokaʻi on the 115 m grid');
    isl.pbTex = kit.maskTexture(gp, { r: isl.pb.mask });
    let nb = 0; for (const v of isl.bridge) if (v > 127) nb++;
    api.log(`[ch1] fused island at ${L400.toFixed(1)} m: ${Math.round(isl.one.areaKm2)} km2, ${isl.one.rings.length} rings; bridge cells ${nb}; Kaho'olawe separate: ${!touch}; Penguin Bank top ${Math.round(isl.pb.areaKm2)} km2 (${isl.pb.rings.length} rings, Molokaʻi in it: ${molo})`);
    return isl;
  };
  const camFly = flight('noocean', 'mauinui_one', fly0, fly1, { ease: E.inOut, via: { lon: -156.55, lat: 19.75, alt: 34 }, tvia: { tLon: -156.35, tLat: 20.55, tH: -500 } });
  const zoom = (c, k) => { c.fov = 2 * Math.atan(Math.tan(c.fov * Math.PI / 360) / (1 + k)) * 180 / Math.PI; };
  const tilt = (lt) => E.inOut(F.clamp((lt - (tMost - 0.1)) / 2.5)) * (1 - E.inOut(F.clamp((lt - fly0) / 1.2)));
  const camD = (lt) => {
    const c = camFly(lt);
    const pre = 1 - E.inOut(F.clamp((lt - fly0) / (fly1 - fly0))), post = Math.max(0, lt - fly1);
    zoom(c, 0.04 * Math.min(lt, fly0) / 10 * pre + 0.03 * post / 10);
    c.dYaw = -(0.6 * Math.min(lt, fly0) * pre + 0.4 * post);
    c.dPitch = -5 * tilt(lt);
    return c;
  };
  const levelD = (lt) => {
    if (lt < fly0) return -9000;
    if (lt < fly1) return -9000 * Math.pow(1 - F.clamp((lt - fly0) / (fly1 - fly0)), 5);
    return L400 * E.inOutSine(F.clamp((lt - drain0) / (drain1 - drain0)));
  };
  const capFill = (lt) => F.clamp((lt - (lead('top') - 0.1)) / 0.2) * (1 - F.clamp((lt - (tTop + 0.85)) / 0.2));
  const stateD = (lt) => {
    const p = E.inOut(F.clamp((lt - fly0) / (fly1 - fly0 - 0.6)));
    const st = mixState('noocean', 'mauinui', p);
    st.mlookAmt = 1 - E.inOut(F.clamp((lt - fly0) / 0.9));
    const k = tilt(lt) * (lt < fly0 ? 1 : 0);
    if (k > 0) {
      st.set.sedCol = st.set.sedCol.map((v, i) => v * (1 + 0.85 * k) + [0.006, 0.004, 0][i] * k); st.set.basaltCol = st.set.basaltCol.map(v => v * (1 + 0.7 * k));
      st.set.nearAmt = Math.max(st.set.nearAmt || 0, k);
      st.mlook = Object.assign({}, MLOOKS.noocean, { flExp: 0.95 + 0.3 * k, flSat: 0.65 + 0.1 * k, flBurn: [0.59, 1.0, 0.008 * (1 - k)] });
    }
    const pulse = F.clamp(1 - Math.abs(lt - (tUnder - 0.03)) / 0.2);
    st.set.lineCol = st.set.lineCol.map(v => v * (1 + 0.9 * pulse)); st.set.lineW = st.set.lineW * (1 + 0.8 * pulse);
    st.set.oldLine = lt < fly0 ? 1 : 1 - F.clamp((lt - fly0) / 0.8);
    return st;
  };
  const maskD = (lt) => {
    if (!isl.cap) return null;
    if (lt < fly0 + 0.4) { const a = capFill(lt); return a > 0 ? { tex: isl.capTex, bb: isl.cap.g.bb, hero: 0.55 * a, pass: a } : null; }
    const dim = F.clamp((lt - fly1) / 0.5), hero = 0.38 * E.inOut(F.clamp((lt - tOne) / 0.35));
    return { tex: isl.mnTex, bb: isl.one.g.bb, hero, dim: 0.75 * dim };
  };
  const oneOut = (lt) => F.clamp((lt - (TA - 0.27)) / 0.27);                   // ONE ISLAND dissolves out over 8 frames before the dive

  scenes.push(ready(kit.terrainShot({
    id: 'ch1-demo', t0: 0, t1: TA, region: REG, stage: STAGE, cam: camD, level: levelD, state: stateD, mask: maskD,
    async world(ctx, lt, tt, view) {
      await getIsl();
      if (postcard && lt > tCard - 0.6 && lt < fly0 + 0.6) {
        const pd = F.clamp((lt - (tCard - 0.5)) / 0.47), lift = 0.1 * F.clamp((lt - lead('top')) / 0.25), off = F.clamp((lt - (fly0 - 0.2)) / 0.8);
        kit.drawPostcard(ctx, view, postcard, { lon: -155.5 + off * 0.6, lat: 19.62, wKm: 72, rot: 4, hm: 2600 + off * 9000, p: pd, lift: lift + off * 0.8, alpha: 1 - off });
      }
    },
    ui(ctx, lt, tt, view) {
      const capA = capFill(lt);
      if (capA > 0 && isl.cap) ui.outline(ctx, view.runs(isl.cap.rings, 0, { every: 2 }), { alpha: capA, p: F.clamp((lt - (lead('top') - 0.1)) / 0.35) });
      if (!postcard && lt > tCard - 0.1 && lt < fly0) { const q = view.project(...PLACES['mauna-loa']); if (q) ui.label(ctx, 'HAWAIʻI', q[0], q[1], { t: tt, p: F.clamp((lt - (lead('card') - 0.1)) / 0.3) }); }
      const merge = F.clamp((lt - tOne) / (6 / 30));
      [['maui', isl.maui], ['molo', isl.molo], ['lanai', isl.lanai]].forEach(([m, I]) => {
        const a = F.clamp((lt - lead(m)) / 0.12) * (1 - merge);
        if (a > 0 && I) ui.outline(ctx, view.runs(I.rings, 0, { every: 2 }), { alpha: a, width: 6, p: F.clamp((lt - lead(m)) / 0.5) });
      });
      if (merge > 0 && isl.one) ui.outline(ctx, view.runs(isl.one.rings, L400, { every: 2 }), { alpha: merge, width: 6, p: F.clamp((lt - tOne) / 0.5) });
      const outA = F.clamp((lt - (tDr + 0.6)) / (8 / 30));
      if (outA < 1 && !api.Q.nolabel) ui.block(ctx, [{ text: 'NO OCEAN', role: 'title', fam: 'label', cap: 162 }], W - px(96), px(96), { anchor: 'right', plate: false, color: PAL.ink, glow: true, platePre: true, out: outA });
      const nameTimes = [lead('maui'), lead('molo'), lead('lanai')];
      const nOut = F.clamp((lt - (tOne - 0.2)) / 0.2);
      if (lt > nameTimes[0] - 0.05 && nOut < 1)
        ui.block(ctx, [{ words: ['MAUI'], role: 'label', cap: 68 }, { words: ['MOLOKAʻI'], role: 'label', cap: 68 }, { words: ['LĀNAʻI'], role: 'label', cap: 68 }], W - px(96), px(96),
          { anchor: 'right', textAlign: 'left', p: 1, wordTimes: nameTimes, lt, grow: true, out: nOut, bar: PAL.hero, gap: 30 });
      const oneP = F.clamp((lt - tOne) / 0.3);
      if (oneP > 0 && oneOut(lt) < 1) ui.block(ctx, [{ text: 'ONE ISLAND', role: 'headline', fam: 'label', cap: 130 }], px(96), px(96), { anchor: 'left', plate: false, color: PAL.ink, glow: true, p: oneP, out: oneOut(lt) });
      const gp = F.clamp((lt - (fly1 - 0.05)) / 0.6), gOut = F.clamp((lt - (tOne - 0.4)) / 0.3);
      const pulse = F.clamp((lt - lead('ft400', 4)) / 0.15) * (1 - F.clamp((lt - (lead('ft400') + 1.0)) / 0.4));
      ui.gauge(ctx, { p: gp, out: gOut, level: Math.max(view.level, -150), range: 150, to: 492, unit: 'FT', pulse });
    },
  }), getIsl));
  api.cue(lead('ft400'), 'impact_short', -12); api.cue(tOne, 'impact_deep', -9); api.cue(drain0, 'riser_tension', -14);

  // =========================================================================================== s007 the dive and the golden pass
  // the Maui Nui golden-hour light for s007-s013: low sun from the south (side light on every camera of this stretch)
  const GOLD = { look: 'warm', sun: [160, 24], water: 'film', level: L400, set: { foamAmt: 1, landSat: 1.0, landGain: 1.0, nearAmt: 0.55, glintAmt: 0.08, waveAmt: 0.7, detail: 1.3,
      reefCol: [0.085, 0.074, 0.062] }, post: { exposure: 1.12, contrast: 1.1, sat: 1.08 } };
  const blend = (a, b, p) => { const s = mixState(a, b, p); s.mlook = null; s.mlookAmt = 0; return s; };
  const tIce = t('ice'), TC = K.s1('s007') - 0.23;                             // cut to the gag on the music dip, under "it really happened"
  const c0 = camD(TA), st0 = stateD(TA);
  const camB0 = spline([
    Object.assign({ t: TA, stop: true }, pickCam(c0)),
    { t: TA + 1.75, lon: -157.16, lat: 21.05, alt: 2.6, tLon: -156.90, tLat: 20.95, tH: -150, fov: 44, shiftX: 0, shiftY: 0, dYaw: 0, dPitch: 0 },
    { t: TC, lon: -157.07, lat: 21.012, alt: 1.5, tLon: -156.84, tLat: 20.925, tH: -120, fov: 46, shiftX: 0, shiftY: 0, dYaw: 0, dPitch: 0 },
  ]);
  function pickCam(c) { return { lon: c.lon, lat: c.lat, alt: c.alt, tLon: c.tLon, tLat: c.tLat, tH: c.tH, fov: c.fov, shiftX: c.shiftX || 0, shiftY: c.shiftY || 0, dYaw: c.dYaw || 0, dPitch: c.dPitch || 0 }; }
  const birds = [{ y0: 0.66, y1: 0.58, t0: tIce - 0.9, d: 2.0, s: 110, seed: 1 }, { y0: 0.74, y1: 0.67, t0: tIce - 0.65, d: 2.2, s: 92, seed: 2 }, { y0: 0.62, y1: 0.57, t0: tIce - 0.3, d: 2.0, s: 78, seed: 3 }];
  scenes.push(ready(kit.terrainShot({
    id: 'ch1-ice', t0: TA, t1: TC, region: REG, stage: STAGE, cam: (lt) => Object.assign(camB0(lt + TA), { near: 0.05, far: 900 }), level: L400,
    state: (lt) => blend(st0, GOLD, E.inOut(F.clamp(lt / 1.6))),
    mask: (lt) => { const f = E.inOut(F.clamp(lt / 0.7)); return isl.mnTex && f < 1 ? { tex: isl.mnTex, bb: isl.one.g.bb, hero: 0.38 * (1 - f), dim: 0.75 * (1 - f) } : null; },
    world(ctx, lt) {
      const T0 = lt + TA;                                                       // three seabirds crossing the dry floor (true-scale silhouettes)
      for (const b of birds) { const u = (T0 - b.t0) / b.d; if (u < 0 || u > 1) continue; drawBird(ctx, W * (1.06 - 1.16 * u), H * (b.y0 + (b.y1 - b.y0) * u) + 6 * Math.sin(T0 * 2 + b.seed), px(b.s), T0 * 5.2 + b.seed); }
    },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TA, f = F.clamp(lt / 0.45);   // (isl is ready: the demo shot ran it)
      if (f < 1 && isl.one) ui.outline(ctx, view.runs(isl.one.rings, L400, { every: 2 }), { alpha: 1 - f, width: 6 });
      const p = F.clamp((T0 - lead('ice')) / 0.35), out = F.clamp((T0 - (TC - 0.3)) / 0.27);
      if (p > 0) ui.block(ctx, [{ text: 'LAST ICE AGE', role: 'headline', cap: 100 }], W / 2, px(96), { anchor: 'center', p, out, bar: PAL.cyan });
    },
  }), getIsl));
  function drawBird(ctx, x, y, span, ph) {                                     // a gliding seabird: dark body, wings flapping
    const f = Math.sin(ph * 6.2832 * 0.55), s = span / 2, up = f * s * 0.32;
    ctx.save(); ctx.translate(x, y); ctx.fillStyle = 'rgba(28,32,38,0.86)'; ctx.beginPath();
    ctx.moveTo(-s, -up); ctx.quadraticCurveTo(-s * 0.45, -s * 0.18 - up * 0.4, -s * 0.08, 0); ctx.lineTo(s * 0.08, 0);
    ctx.quadraticCurveTo(s * 0.45, -s * 0.18 - up * 0.4, s, -up); ctx.quadraticCurveTo(s * 0.45, -s * 0.02 - up * 0.2, s * 0.06, s * 0.1);
    ctx.lineTo(-s * 0.06, s * 0.1); ctx.quadraticCurveTo(-s * 0.45, -s * 0.02 - up * 0.2, -s, -up); ctx.fill();
    ctx.beginPath(); ctx.ellipse(-s * 0.02, s * 0.04, s * 0.22, s * 0.07, 0, 0, 7); ctx.fill(); ctx.restore();
  }

  // =========================================================================================== s008-s013 gag, look down, ride, Penguin Bank
  const tFerry = t('ferry'), tLook = t('look'), tNoB = t('nobottom'), tLedge = t('ledge'), tPlunge = t('plunge'), tBank = t('bank'), tDrown = t('drowned');
  const TW = K.s0('s014') - 0.11;                                              // the whip cut (whoosh 45.56)
  const W0 = TW - 5 / 30;                                                      // whip-out starts 5 frames before the cut
  // floor heights (mauinui 78 m grid) under the gag: the dry seafloor north of Lānaʻi at about -70 m
  const GE = { lon: -156.905, lat: 20.9445, floor: -0.0553 };                 // the gag camera (15 m over the floor), looking N at Molokaʻi
  const camC = spline([
    { t: TC, lon: GE.lon, lat: GE.lat, alt: GE.floor + 0.015, tLon: -156.893, tLat: 21.08, tH: 120, fov: 34, dYaw: 0, dPitch: 0 },
    { t: tLook - 0.05, stop: true, lon: GE.lon, lat: GE.lat + 0.00008, alt: GE.floor + 0.015, tLon: -156.893, tLat: 21.08, tH: 120, fov: 32.5 },
    { t: tLook + 1.1, stop: true, lon: GE.lon, lat: 20.9423, alt: GE.floor + 0.30, tLon: -156.90477, tLat: 20.94548, tH: -59, fov: 40 },
    { t: tLook + 2.6, lon: -156.925, lat: 20.9455, alt: 0.95, tLon: -156.958, tLat: 20.948, tH: -60, fov: 44 },
    { t: tNoB, lon: -156.972, lat: 20.950, alt: 1.5, tLon: -157.13, tLat: 20.945, tH: -700, fov: 46 },
    { t: tLedge, lon: -157.022, lat: 20.951, alt: 1.2, tLon: -157.12, tLat: 20.945, tH: -620, fov: 46 },
    { t: tPlunge, lon: -157.058, lat: 20.950, alt: 0.9, tLon: -157.10, tLat: 20.946, tH: -520, fov: 47 },
    { t: tPlunge + 1.2, lon: -157.093, lat: 20.947, alt: 0.25, tLon: -157.123, tLat: 20.944, tH: -720, fov: 48 },
    { t: tBank + 0.9, stop: true, lon: -157.02, lat: 20.95, alt: 10.0, tLon: -157.48, tLat: 20.99, tH: -200, fov: 44 },
    { t: TW, lon: -157.03, lat: 20.951, alt: 9.6, tLon: -157.47, tLat: 20.99, tH: -200, fov: 42 },
  ]);
  // whip-out: the view pans right (clockwise) faster and faster over the last 5 frames (dYaw negative = right)
  const whipOutR = (lt) => -50 * Math.pow(F.clamp((lt - W0) / (TW - W0)), 2.2);
  const rise0 = K.word('s013', 'rose').start - 0.15;
  const DR0 = K.word('s009', 'draining.').start + 0.15, DR1 = DR0 + 6.6;      // the drain resumes on "draining" (-400 ft -> -1,000 m in 6.6 s)
  const levelC = (T0) => {
    if (T0 < DR0) return L400;
    if (T0 < rise0) return L400 + (-1000 - L400) * E.inOutSine(F.clamp((T0 - DR0) / (DR1 - DR0)));
    return vspline([{ t: rise0, v: -1000, stop: true }, { t: rise0 + 1.15, v: -175 }, { t: tDrown + 0.02, v: -52 }, { t: tDrown + 0.95, v: 0, stop: true }])(T0);
  };
  const drainP = (T0) => F.clamp((L400 - levelC(T0)) / (1000 + L400));          // 0 at -400 ft, 1 at -1,000 m
  const stateC = (T0) => {
    const s = blend(GOLD, GOLD, 0), k = drainP(T0), hi = F.clamp((T0 - (tPlunge + 0.6)) / 1.6);
    s.set.sedCol = s.set.sedCol.map((v, i) => v * (1 + 0.7 * k) + [0.005, 0.004, 0][i] * k); s.set.basaltCol = s.set.basaltCol.map(v => v * (1 + 0.8 * k));
    s.sun = [160, 24 + 14 * E.inOut(hi)]; s.post.exposure = 1.12 + 0.1 * k;
    s.set.oldLine = 0; s.set.ringH = 30;
    return s;
  };
  // the paper tourist: world path on the dry floor (walks from the Lānaʻi side toward the camera and to the right)
  const tHop = K.s0('s008') + 0.16, PATH = [[-156.905326, 20.945653], [-156.904530, 20.945408]];   // start (125 m ahead, left), end (105 m ahead, right)
  const HF = 28;                                                               // his height in metres (paper theatre scale: about 38 % at the hold)
  const walk = (T0) => {                                                       // 0..1 along the path, a stop for the hat tip
    const seg = (a, b, x0, x1, T) => x0 + (x1 - x0) * F.clamp((T - a) / (b - a));
    if (T0 < tHop - 0.4) return seg(TC - 0.6, tHop - 0.4, 0, 0.30, T0);
    if (T0 < tHop) return seg(tHop - 0.4, tHop, 0.30, 0.42, T0);              // the hop (lands on the paper tap)
    if (T0 < tFerry + 0.75) return 0.42 + 0.02 * E.out(F.clamp((T0 - tHop) / 0.25));
    return seg(tFerry + 0.75, tLook + 2.5, 0.44, 1.0, T0);
  };
  const C = { tourist: await kit.paper('tourist'), suitcase: await kit.paper('suitcase') };
  const lerpLL = (u) => [PATH[0][0] + (PATH[1][0] - PATH[0][0]) * u, PATH[0][1] + (PATH[1][1] - PATH[0][1]) * u];
  const ppmAt = (view, lon, lat, hm) => { const a = view.project(lon, lat, hm), b = view.project(lon, lat, hm + 10); return a && b ? Math.hypot(a[0] - b[0], a[1] - b[1]) / 10 : 0; };
  const shotC = kit.terrainShot({
    id: 'ch1-ride', t0: TC, t1: TW, region: REG, stage: STAGE, level: (lt) => levelC(lt + TC), state: (lt) => stateC(lt + TC),
    cam: (lt) => { const c = camC(lt + TC); c.dYaw = (c.dYaw || 0) + whipOutR(lt + TC); c.near = c.alt < 0.5 ? 0.004 : 0.02; c.far = 600; return c; },
    mask: (lt) => { const T0 = lt + TC, a = F.clamp((T0 - (lead('bank') - 0.1)) / 0.35) * (1 - F.clamp((levelC(T0) + 110) / 45)); return a > 0 && isl.pbTex ? { tex: isl.pbTex, bb: isl.pb.g.bb, hero: 0.62 * a } : null; },
    async world(ctx, lt, tt, view) {
      await getIsl();
      const T0 = lt + TC; if (T0 > tLook + 3.2) return;
      const u = walk(T0), [lon, lat] = lerpLL(u), hm = view.S.heightAt(lon, lat);
      const ppm = ppmAt(view, lon, lat, hm); if (!ppm) return;
      const hop = T0 > tHop - 0.4 && T0 < tHop ? Math.sin(Math.PI * (T0 - (tHop - 0.4)) / 0.4) * HF * ppm * 0.26 : 0;
      const land = F.clamp(1 - Math.abs(T0 - tHop - 0.05) / 0.12);                // squash on the landing
      const tipA = F.clamp((T0 - (lead('ferry') - 0.12)) / 0.25) * (1 - F.clamp((T0 - (tFerry + 0.55)) / 0.25));
      const walking = T0 < tHop - 0.4 || T0 > tFerry + 0.75;
      const bob = walking ? Math.abs(Math.sin(T0 * 7.5)) * HF * ppm * 0.025 : 0;
      // the bag first (behind him, trailing), then him
      const bu = Math.max(0, u - 0.07), [blon, blat] = lerpLL(bu), bhm = view.S.heightAt(blon, blat);
      const scrape = T0 > tFerry + 0.75 && T0 < tFerry + 1.6 ? Math.abs(Math.sin(T0 * 31)) * 0.5 : 0;
      kit.drawCutout(ctx, view, C.suitcase, { lon: blon - 0.00003, lat: blat - 0.00004, hm: bhm, hPx: 0.36 * HF * ppm, t: T0, seed: 2, wobble: 0.02, lean: -0.06 - 0.05 * scrape, hop: (walking ? Math.abs(Math.sin(T0 * 7.5 + 1.2)) * 0.012 : 0) * HF * ppm + scrape * 2 });
      kit.drawCutout(ctx, view, C.tourist, { lon, lat, hm, hPx: HF * ppm, t: T0, seed: 1, wobble: 0.02, hop: hop + bob, squash: 0.12 * land, lean: walking ? 0.05 : -0.04 * tipA,
        parts: { hat: { off: [px(18) * tipA, -HF * ppm * 0.10 * tipA], rot: -0.55 * tipA } } });
    },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TC;
      // s010-s011: the -400 ft shore of the one island stays as a cream line while the water drops away from it ("the shore becomes a
      // ledge"); it goes when the camera pulls back to the bank
      const sa = F.clamp((L400 - 25 - levelC(T0)) / 40) * (1 - F.clamp((T0 - (tPlunge + 1.0)) / 0.5));
      if (sa > 0 && isl.one) ui.line(ctx, view.runs(isl.one.rings, L400, { every: 2 }), { width: 6, color: '#F1E8D6', alpha: sa * 0.95, under: 0.4 });
      // Penguin Bank: white outline of its flat top (fades as the sea rises past -110 m), then the label
      const pa = F.clamp((T0 - (lead('bank') - 0.1)) / 0.3) * (1 - F.clamp((levelC(T0) + 110) / 40));
      if (pa > 0 && isl.pb) ui.outline(ctx, view.runs(isl.pb.rings, -70, { every: 2 }), { alpha: pa, width: 6, p: F.clamp((T0 - (lead('bank') - 0.1)) / 0.5) });
      const la = F.clamp((T0 - lead('bank')) / 0.3) * (1 - F.clamp((T0 - (rise0 + 0.3)) / 0.3));
      if (la > 0) { const q = view.project(-157.55, 20.99, -60); if (q) ui.label(ctx, 'PENGUIN BANK', q[0], q[1], { t: tt, p: la, order: ['above', 'above-right', 'above-left'] }); }
      // SEA LEVEL gauge (marker only, no digits; range 1,000 m): in while the sea falls, out while it holds, in again while it rises
      const gin = F.clamp((T0 - (K.s0('s009') - 0.1)) / 0.5) * (1 - F.clamp((T0 - (DR1 + 0.3)) / 0.4)) + F.clamp((T0 - (rise0 - 0.3)) / 0.4) * (1 - F.clamp((T0 - (W0 - 0.35)) / 0.3));
      if (gin > 0) ui.gauge(ctx, { p: 1, alpha: F.clamp(gin), level: Math.max(view.level, -1000), range: 1000, value: false });
    },
  });
  scenes.push(blurred(ready(shotC, getIsl), W0, TW));

  // =========================================================================================== s014-s024 the Big Island, 1975
  const tNow = t('now'), tNotA = t('notalways'), tHal = t('hal'), tWoke = t('woke'), tHit = t('hit'), tLurch = t('lurch'), tDrop = t('drop');
  const tRush = K.word('s021', 'rushed').start, tTwo = t('two'), tMorn = t('morning'), tYards = t('yards'), tGo = t('go'), tDid = t('did');
  const HAL = { lon: -155.2552, lat: 19.2704 };                                // the grove (the 1975 USGS photo; NPS shelter 19.2719, -155.2537)
  // one orbit path around the grove (log distance): the whip landing, the push, the night hold, the lurch pull-up, the drop, the pull back
  const TH1 = K.s0('s015') + 1.78, TQ = K.s0('s024') + 0.8;                                // stage hand-offs: kilauea_sf -> halape, halape -> kilauea_sf
  const G0 = W0 + 5 / 30;                                                      // whip-in starts at the cut
  const orb = kit.orbitPath([
    { t: G0, lat: 19.300, lon: -155.235, d: 34, tilt: 72, heading: 310, fov: 40 },
    { t: G0 + 0.55, lat: 19.300, lon: -155.235, d: 33, tilt: 72, heading: 350, fov: 40, ease: E.outExpoN },
    { t: K.s1('s014') + 0.2, lat: 19.296, lon: -155.238, d: 30, tilt: 72, heading: 352, fov: 40, ease: E.inOutSine },
    { t: K.s0('s016') - 0.2, lat: HAL.lat + 0.0004, lon: HAL.lon + 0.0002, d: 0.70, tilt: 79, heading: 17, fov: 28, ease: E.inOut },
    { t: K.s0('s017') + 1.6, lat: HAL.lat + 0.0005, lon: HAL.lon + 0.0001, d: 0.44, tilt: 80, heading: 26, fov: 25, ease: E.inOut },
    { t: K.s0('s018') + 1.4, lat: HAL.lat + 0.0004, lon: HAL.lon, d: 0.62, tilt: 79, heading: 21, fov: 28, ease: E.inOut },
    { t: tLurch - 0.1, lat: HAL.lat + 0.0004, lon: HAL.lon, d: 0.60, tilt: 79, heading: 23, fov: 28, ease: E.inOutSine },
    { t: tLurch + 1.3, lat: HAL.lat + 0.003, lon: HAL.lon + 0.008, d: 4.2, tilt: 70, heading: 14, fov: 36, ease: E.inOut },
    { t: K.s0('s020') + 0.2, lat: HAL.lat + 0.003, lon: HAL.lon + 0.0082, d: 4.0, tilt: 70, heading: 13, fov: 36, ease: E.inOutSine },
    { t: tDrop - 0.25, lat: HAL.lat + 0.0004, lon: HAL.lon, d: 0.68, tilt: 79, heading: 27, fov: 28, ease: E.inOut },
    { t: tTwo, lat: HAL.lat + 0.0004, lon: HAL.lon, d: 0.64, tilt: 79, heading: 31, fov: 28, ease: E.inOutSine },
    { t: K.s0('s024') - 0.1, lat: HAL.lat + 0.0004, lon: HAL.lon - 0.0002, d: 0.80, tilt: 78, heading: 37, fov: 29, ease: E.inOutSine },
    { t: K.s0('s024') + 1.7, lat: 19.31, lon: -155.21, d: 42, tilt: 70, heading: 352, fov: 38, ease: E.inOut },
    { t: tGo - 0.12, lat: 19.31, lon: -155.212, d: 39, tilt: 70, heading: 350, fov: 37, ease: E.inOutSine },
  ]);
  // the 6-frame jolt on {hit} and the seaward lurch (seeded, decaying)
  const shake = (T0) => {
    let y = 0, p = 0; const a = (T0 - (lead('hit', 1))) * 30;
    if (a >= 0 && a < 12) { const k = Math.exp(-a / 3.2); y += (hash(Math.floor(a), 1) - 0.5) * 2.2 * k; p += (hash(Math.floor(a), 2) - 0.5) * 1.6 * k; }
    const b = (T0 - (tLurch - 0.05)) * 30; if (b >= 0 && b < 10) { const k = Math.exp(-b / 3); p += -1.3 * k * Math.sin(b * 1.4); }
    const c = (T0 - (lead('woke', 2))) * 30; if (c >= 0 && c < 26) { const k = Math.exp(-c / 9); y += (hash(Math.floor(c), 3) - 0.5) * 0.35 * k; }
    return [y, p];
  };
  const camH = (T0) => { const c = kit.terrainCamOf(orb(T0)); const [y, p] = shake(T0); c.dYaw = y;                                 // the whip-in pan is in the orbit heading (310 -> 350, decelerating)
    c.dPitch = p; c.near = Math.min(c.near, 0.01); return c; };
  // light: morning (s014) -> pre-dawn blue (s015 push) -> first light (s022-s023) -> morning again for the regional pull back (s024)
  const DAWN = { zenith: '#2f5698', horizon: '#adc0e1', haze: ['#9aaed2', 0.72], sun: '#c9d5f2', glow: ['#ffb48a', 0.22], sunI: 3.3, skyI: 1.6 };
  const FIRST = { zenith: '#3a68b0', horizon: '#e2cab8', haze: ['#cdbfc4', 0.72], sun: '#ffd2a4', glow: ['#ffb582', 0.45], sunI: 3.0, skyI: 0.95 };
  const lightK = (T0) => {                                                     // 0 morning, 1 pre-dawn, 2 first light, 3 morning
    if (T0 < K.s0('s015')) return 0;
    if (T0 < K.s0('s016')) return E.inOut(F.clamp((T0 - K.s0('s015')) / (K.s0('s016') - K.s0('s015') - 0.3)));
    if (T0 < tTwo - 0.6) return 1;
    if (T0 < K.s0('s024')) return 1 + E.inOut(F.clamp((T0 - (tTwo - 0.6)) / 2.2));
    return 2 + E.inOut(F.clamp((T0 - K.s0('s024')) / 1.6));
  };
  const lookAt = (k) => {
    const day = { zenith: '#1553b5', horizon: '#9fc4ee', haze: ['#a5c0e0', 0.74], sun: '#fff3e2', glow: ['#ffe6c8', 0.5], sunI: 3.5, skyI: 0.70 };
    const A = k < 1 ? day : k < 2 ? DAWN : FIRST, B = k < 1 ? DAWN : k < 2 ? FIRST : day, p = k - Math.floor(Math.min(k, 2.999));
    const hx = (a, b) => '#' + mixc(hex(a), hex(b), p).map(v => v.toString(16).padStart(2, '0')).join('');
    return { zenith: hx(A.zenith, B.zenith), horizon: hx(A.horizon, B.horizon), haze: [hx(A.haze[0], B.haze[0]), A.haze[1] + (B.haze[1] - A.haze[1]) * p], sun: hx(A.sun, B.sun),
      glow: [hx(A.glow[0], B.glow[0]), A.glow[1] + (B.glow[1] - A.glow[1]) * p], sunI: A.sunI + (B.sunI - A.sunI) * p, skyI: A.skyI + (B.skyI - A.skyI) * p };
  };
  function hex(s) { return [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16)); }
  const pick3 = (k, a, b, c, d) => k < 1 ? a + (b - a) * k : k < 2 ? b + (c - b) * (k - 1) : c + (d - c) * (k - 2);
  const levelH = (T0) => {                                                     // relative sea level on today's (post-1975) grid
    // today (s014) 0 m; the push back to 1975 (s015) lowers the sea 3.5 m against today's grid (the block had not dropped yet);
    // {drop}: back to 0 over 1.5 s; 'rushed': a local surge (up in 0.6 s, landing on the word, down over 1.6 s)
    const pre = -3.5 * E.inOut(F.clamp((T0 - K.s0('s015')) / 2.5)), drop = E.inOut(F.clamp((T0 - (lead('drop', 2))) / 1.5));
    const su = T0 - (tRush - 0.45), surge = su < 0 ? 0 : su < 0.6 ? E.out(su / 0.6) : su < 2.2 ? 1 - E.inOut((su - 0.6) / 1.6) : 0;
    return pre * (1 - drop) + 3.0 * surge;
  };
  const stateH = (T0) => {
    const k = lightK(T0);
    const night = k <= 1 ? k : k < 2 ? 1 - 0.6 * (k - 1) : 0.4 * (3 - k), WN = [[0.008, 0.095, 0.135], [0.005, 0.052, 0.092], [0.005, 0.036, 0.072]];
    return { look: lookAt(k), sun: [pick3(k, 100, 82, 84, 100), pick3(k, 24, 15, 14, 34)], waterCols: [[0.020, 0.40, 0.42], [0.012, 0.16, 0.20], [0.016, 0.092, 0.125]].map((c, i) => c.map((v, j) => v + (WN[i][j] - v) * night)), level: levelH(T0),
      set: { foamAmt: 0.6 + 1.4 * F.clamp(1 - Math.abs(T0 - (tRush + 0.3)) / 1.2), waveAmt: 0.8 + 1.8 * F.clamp(1 - Math.abs(T0 - (tWoke + 0.2)) / 0.9) + 2.5 * F.clamp(1 - Math.abs(T0 - (tHit + 0.3)) / 1.4),
        glintAmt: 0.06, surfAmt: 0.7, landSat: pick3(k, 1.05, 0.8, 0.85, 1.05), landGain: pick3(k, 1.0, 1.45, 1.25, 1.0), nearAmt: 0.7, landLift: pick3(k, 0.03, 0.06, 0.045, 0.03), shadows: 1 },
      post: { exposure: pick3(k, 1.18, 1.6, 1.38, 1.15), sat: pick3(k, 1.15, 1.0, 1.0, 1.05), contrast: pick3(k, 1.08, 1.05, 1.05, 1.06) } };
  };
  const gradeH = (T0) => { const d = F.clamp((T0 - (tTwo - 0.1)) / 0.6) * (1 - F.clamp((T0 - (K.s0('s024') - 0.3)) / 0.8)); return { sat: 1 - 0.2 * d }; };

  // ---- the grove, tents, stars, dust: drawn at true positions on the halape stage (lazily placed from the 10 m grid, seeded)
  let GROVE = null;
  const grove = (S) => {
    if (GROVE) return GROVE;
    const r = F.rng(1975), palms = [], tents = [];
    for (let k = 0; k < 9000 && palms.length < 64; k++) {
      const lon = HAL.lon - 0.0012 + r() * 0.0024, lat = HAL.lat - 0.0011 + r() * 0.0019, h = S.heightAt(lon, lat);
      const inWater = h > -2.3 && h < 0.5, beach = h >= 0.5 && h < 3.2 && palms.filter(p => p.h >= 0.5).length < 16;
      if (!(inWater || beach)) continue;
      if (palms.some(p => Math.hypot((p.lon - lon) * 105000, (p.lat - lat) * 111000) < 8)) continue;
      if (Math.hypot((lon - HAL.lon) * 105000, (lat - HAL.lat) * 111000) > 95) continue;
      palms.push({ lon, lat, h, H: 17 + r() * 9, lean: (r() - 0.5) * 0.5, seed: r() * 100, fr: 8 + Math.floor(r() * 4) });
    }
    for (let k = 0; k < 3000 && tents.length < 4; k++) {
      const lon = HAL.lon - 0.0010 + r() * 0.0022, lat = HAL.lat + 0.0001 + r() * 0.0009, h = S.heightAt(lon, lat);
      if (h < 1.2 || h > 6 || tents.length >= 4) continue;
      if (tents.some(p => Math.hypot((p.lon - lon) * 105000, (p.lat - lat) * 111000) < 18)) continue;
      tents.push({ lon, lat, h, rot: r() * 3.14, col: [[214, 160, 92], [176, 168, 118], [196, 120, 80], [150, 160, 120]][tents.length] });
    }
    const dust = []; for (let k = 0; k < 70; k++) { const lon = HAL.lon - 0.0045 + r() * 0.0085, lat = 19.2726 + r() * 0.0012; dust.push({ lon, lat, h: S.heightAt(lon, lat), s: r(), d: r() }); }
    GROVE = { palms, tents, dust };
    api.log(`[ch1] Halapē grove: ${palms.length} palms (${palms.filter(p => p.h < 0.4).length} on ground that is under water after the drop), ${tents.length} tents`);
    return GROVE;
  };
  const sway = (T0, s) => 0.03 * Math.sin(T0 * 1.1 + s) + 0.09 * F.clamp(1 - Math.abs(T0 - (tWoke + 0.4)) / 1.2) * Math.sin(T0 * 19 + s)
    + 0.22 * Math.exp(-Math.max(0, T0 - tHit) * 1.6) * (T0 > tHit - 0.05 ? Math.sin((T0 - tHit) * 24 + s) : 0) + 0.12 * Math.exp(-Math.max(0, T0 - tLurch) * 2) * (T0 > tLurch ? Math.sin((T0 - tLurch) * 16 + s) : 0)
    + 0.10 * F.clamp(1 - Math.abs(T0 - (tRush + 0.2)) / 0.9) * Math.sin(T0 * 11 + s);
  function drawPalm(ctx, view, p, T0, tint, level) {
    const b = view.project(p.lon, p.lat, p.h), top = view.project(p.lon, p.lat, p.h + p.H); if (!b || !top) return;
    const Hp = Math.hypot(top[0] - b[0], top[1] - b[1]); if (Hp < 3) return;
    const wl = level > p.h ? view.project(p.lon, p.lat, level) : null;        // the trunk rises out of the water there
    const sw = sway(T0, p.seed), lx = (p.lean + sw) * Hp * 0.35, tx = top[0] + lx, ty = top[1] + Math.abs(lx) * 0.08;
    const cx = b[0] + lx * 0.25, cy = b[1] - Hp * 0.55;
    ctx.save();
    const y0 = wl ? wl[1] : b[1], x0 = wl ? wl[0] : b[0];
    // the trunk: a tapered, slightly curved column (base wider, a lit side and a shade side)
    const q = (u) => [(1 - u) * (1 - u) * x0 + 2 * (1 - u) * u * cx + u * u * tx, (1 - u) * (1 - u) * y0 + 2 * (1 - u) * u * cy + u * u * ty];
    const wB = Math.max(1.6, Hp * 0.05), wT = Math.max(1.0, Hp * 0.028), L1 = [], L2 = [];
    for (let k = 0; k <= 6; k++) { const u = k / 6, [x, y] = q(u), [x2, y2] = q(Math.min(1, u + 0.01)), dl = Math.hypot(x2 - x, y2 - y) || 1, nx = -(y2 - y) / dl, ny = (x2 - x) / dl, w = (wB + (wT - wB) * u) / 2;
      L1.push([x + nx * w, y + ny * w]); L2.push([x - nx * w, y - ny * w]); }
    ctx.fillStyle = rgba(tint.trunk, 1); ctx.beginPath(); [...L1, ...L2.reverse()].forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill();
    if (wl) { ctx.strokeStyle = rgba(tint.foam, 0.55); ctx.lineWidth = Math.max(1, Hp * 0.014); ctx.beginPath(); ctx.ellipse(x0, y0, Hp * 0.08, Hp * 0.02, 0, 0, 7); ctx.stroke(); }
    // the crown: pinnate fronds (tapered leaf shapes drooping from the crown), back fronds darker, a few dead fronds hanging
    const L = Hp * 0.40, fr = [];
    for (let i = 0; i < p.fr; i++) { const a = (i / p.fr) * 6.2832 + p.seed + sw * 2.0; fr.push({ a, dx: Math.cos(a), dz: Math.sin(a) }); }
    fr.sort((u, v) => u.dz - v.dz);                                          // back fronds first
    for (const f of fr) {
      const len = L * (0.85 + 0.15 * hash(f.a, p.seed)), droop = 0.30 + 0.30 * (1 - Math.abs(f.dx)) + 0.15 * hash(p.seed, f.a);
      const ex = tx + f.dx * len, ey = ty + len * droop - f.dz * len * 0.18, mx = tx + f.dx * len * 0.55, my = ty - len * 0.20 + f.dz * len * 0.06;
      const P = (u) => [(1 - u) * (1 - u) * tx + 2 * (1 - u) * u * mx + u * u * ex, (1 - u) * (1 - u) * ty + 2 * (1 - u) * u * my + u * u * ey];
      const wmax = Math.max(1.2, Hp * 0.055), A = [], B = [];
      for (let k = 0; k <= 7; k++) { const u = k / 7, [x, y] = P(u), [x2, y2] = P(Math.min(1, u + 0.02)), dl = Math.hypot(x2 - x, y2 - y) || 1, nx = -(y2 - y) / dl, ny = (x2 - x) / dl, w = wmax * Math.sin(Math.PI * Math.min(1, u * 1.15)) * 0.5;
        A.push([x + nx * w, y + ny * w]); B.push([x - nx * w, y - ny * w]); }
      const lit = F.clamp(0.5 + 0.5 * f.dx * 0.8 - 0.25 * f.dz);
      ctx.fillStyle = rgba(mixc(tint.frondD, tint.frondL, lit), 1); ctx.beginPath(); [...A, ...B.reverse()].forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle = rgba(mixc(tint.trunk, [20, 20, 20], 0.3), 1); ctx.beginPath(); ctx.arc(tx, ty + Hp * 0.01, Math.max(1.2, Hp * 0.03), 0, 7); ctx.fill();   // coconuts / crown shank
    ctx.restore();
  }
  function drawTent(ctx, view, tn, T0, tint, glow, alpha) {
    const c = Math.cos(tn.rot), s = Math.sin(tn.rot), m = (dx, dy, z) => view.project(tn.lon + (dx * c - dy * s) / (KM * 1000 * Math.cos(tn.lat * D2R)), tn.lat + (dx * s + dy * c) / (KM * 1000), tn.h + z);
    const r0 = m(-1.6, 0, 1.7), r1 = m(1.6, 0, 1.7), a0 = m(-1.6, -1.1, 0), a1 = m(1.6, -1.1, 0), b0 = m(-1.6, 1.1, 0), b1 = m(1.6, 1.1, 0);
    if (![r0, r1, a0, a1, b0, b1].every(Boolean)) return;
    ctx.save(); ctx.globalAlpha *= alpha;
    const quad = (q, col) => { ctx.fillStyle = col; ctx.beginPath(); q.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill(); };
    const L = mixc(tn.col, tint.tent, 0.55), Dk = mixc(L, [10, 14, 24], 0.45);
    quad([r0, r1, a1, a0], rgba(Dk, 1)); quad([r0, r1, b1, b0], rgba(L, 1));
    if (glow > 0) {
      const gx = (r0[0] + r1[0] + b0[0] + b1[0]) / 4, gy = (r0[1] + r1[1] + b0[1] + b1[1]) / 4, R = Math.max(px(34), Math.hypot(r1[0] - r0[0], r1[1] - r0[1]) * 2.6);
      quad([r0, r1, b1, b0], `rgba(255,190,110,${0.75 * glow})`);
      const g = ctx.createRadialGradient(gx, gy, 0, gx, gy, R); g.addColorStop(0, `rgba(255,196,120,${0.55 * glow})`); g.addColorStop(1, 'rgba(255,170,90,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(gx, gy, R, 0, 7); ctx.fill();
    }
    ctx.restore();
  }
  const STARS = (() => { const r = F.rng(29), s = []; for (let k = 0; k < 140; k++) s.push([r(), r(), 0.4 + r() * 1.3, r() * 6]); return s; })();
  function drawStars(ctx, view, T0, a) {
    if (a <= 0.01) return; const hz = view.horizonY() * H;
    ctx.save(); for (const [x, y, s, ph] of STARS) { const yy = y * hz * 0.9; if (yy > hz - px(30) || view.ground(x * W, yy, 60)) continue; const tw = 0.65 + 0.35 * Math.sin(T0 * 2.1 + ph);   // sky only (never over the pali)
      ctx.fillStyle = `rgba(235,240,255,${a * tw * (0.35 + 0.65 * (1 - yy / hz))})`; ctx.beginPath(); ctx.arc(x * W, yy, px(s), 0, 7); ctx.fill(); }
    ctx.restore();
  }
  function drawDust(ctx, view, T0, tint) {
    const a0 = T0 - tHit; if (a0 < 0 || a0 > 3.6) return;
    // a band of dust shaken off the scarp face behind the grove (where the cliff crosses 45 m), rising and thinning; plus small puffs
    if (!GROVE.scarp) { GROVE.scarp = []; for (let lon = HAL.lon - 0.0075; lon <= HAL.lon + 0.0035; lon += 0.0004) { for (let lat = 19.2718; lat < 19.2760; lat += 0.00005) if (view.S.heightAt(lon, lat) > 45) { GROVE.scarp.push([lon, lat]); break; } } }
    const env = F.clamp(a0 / 0.18) * Math.exp(-a0 * 0.75), rise = 6 + 26 * Math.sqrt(a0);
    const pts = GROVE.scarp.map(([lon, lat], i) => view.project(lon, lat, 45 + rise * (0.8 + 0.4 * hash(i, 7)))).filter(Boolean);
    if (pts.length > 2) {
      const ppm = ppmAt(view, GROVE.scarp[GROVE.scarp.length >> 1][0], GROVE.scarp[GROVE.scarp.length >> 1][1], 45), w0 = (10 + 22 * Math.sqrt(a0)) * ppm;
      ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      for (const [k, al] of [[3.2, 0.11], [2.2, 0.15], [1.4, 0.19], [0.8, 0.17]]) {
        ctx.strokeStyle = rgba(tint.dust, al * env); ctx.lineWidth = w0 * k; ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
      ctx.restore();
    }
    for (const d of GROVE.dust) {
      const a = a0 - d.d * 0.3; if (a < 0) continue;
      const q = view.project(d.lon, d.lat, d.h + 2 + a * (6 + 10 * d.s)); if (!q) continue;   // shaken loose, rising and spreading
      const ppm = ppmAt(view, d.lon, d.lat, d.h), R = (3 + 9 * Math.sqrt(a)) * ppm * (0.7 + 0.6 * d.s), al = 0.22 * Math.exp(-a * 0.9) * F.clamp(a / 0.1);
      const x = q[0] + a * 4 * ppm * (d.s - 0.4), y = q[1];
      const g = ctx.createRadialGradient(x, y, 0, x, y, R); g.addColorStop(0, rgba(tint.dust, al)); g.addColorStop(1, rgba(tint.dust, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, R, 0, 7); ctx.fill();
    }
  }
  // the scene tint for drawn things (they are drawn after the grade, so they carry the scene's light themselves)
  const tintAt = (T0) => {
    const k = lightK(T0), d = (a, b, c) => k <= 1 ? mixc(a, b, F.clamp(k)) : mixc(b, c, F.clamp(k - 1));
    return { trunk: d([70, 64, 56], [34, 38, 50], [70, 60, 52]), frondD: d([46, 74, 40], [22, 34, 40], [44, 58, 38]), frondL: d([116, 140, 70], [46, 64, 66], [128, 128, 78]),
      foam: [220, 232, 245], tent: d([200, 190, 170], [92, 104, 132], [196, 170, 150]), dust: d([170, 160, 140], [150, 146, 150], [176, 156, 134]) };
  };
  // ---- s020 scale inset: a side-on section (old ground line, the block sinking 3.5 m, the sea, a plain basketball hoop at true scale)
  function drawInset(ctx, T0) {
    const a = F.clamp((T0 - (lead('drop') - 0.45)) / (8 / 30)) * (1 - F.clamp((T0 - (K.s0('s021') - 0.05 - 8 / 30)) / (8 / 30)));
    if (a <= 0) return;
    const pw = px(560), ph = px(380), x0 = W - px(96) - pw, y0 = px(96), m = ph / 9.0, sea = y0 + ph * (7.1 / 9.0);   // m: px per metre (-1.9 .. +7.1 m)
    const drop = E.inOut(F.clamp((T0 - (lead('drop', 2))) / 1.5)), g0 = sea - 2.3 * m, g = g0 + 3.5 * m * drop;   // ground: +2.3 m -> -1.2 m
    const sc = 0.92 + 0.08 * E.outExpoN(F.clamp((T0 - (lead('drop') - 0.45)) / 0.3));
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(x0 + pw / 2, y0 + ph / 2); ctx.scale(sc, sc); ctx.translate(-(x0 + pw / 2), -(y0 + ph / 2));
    F.round(ctx, x0, y0, pw, ph, px(10)); ctx.save(); ctx.clip();
    const sky = ctx.createLinearGradient(0, y0, 0, y0 + ph); sky.addColorStop(0, '#2c4a7c'); sky.addColorStop(1, '#7e95bf'); ctx.fillStyle = sky; ctx.fillRect(x0, y0, pw, ph);
    // the sea (right, and over the block once it is below sea level)
    ctx.fillStyle = 'rgba(38,92,128,0.92)'; ctx.fillRect(x0, sea, pw, ph);
    // the ground block: a basalt slab with a beach edge on its right
    const gx1 = x0 + pw * 0.72;
    ctx.fillStyle = '#3a3532'; ctx.beginPath(); ctx.moveTo(x0, g); ctx.lineTo(gx1, g); ctx.lineTo(gx1 + px(70), y0 + ph + 5); ctx.lineTo(x0, y0 + ph + 5); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#5a5047'; ctx.fillRect(x0, g, gx1 - x0, px(8));
    // water over the sunken block
    if (g > sea) { ctx.fillStyle = 'rgba(52,118,156,0.82)'; ctx.fillRect(x0, sea, gx1 + px(70) - x0, g - sea); }
    ctx.fillStyle = 'rgba(210,235,250,0.85)'; ctx.fillRect(x0, sea - px(3), pw, px(5));
    // the hoop: pole, arm, backboard, rim at 10 ft (3.05 m) above the ground it stands on
    const hx = x0 + pw * 0.30, rimY = g - 3.05 * m, col = '#F4F6FA';
    ctx.fillStyle = 'rgba(6,9,15,0.55)'; ctx.fillRect(hx - px(9), rimY - 0.6 * m - px(4), px(18), g - rimY + 0.6 * m + px(4));      // dark edge so the white reads on the sky
    ctx.fillStyle = col; ctx.fillRect(hx - px(6), rimY - 0.6 * m, px(12), g - rimY + 0.6 * m);                                     // pole
    ctx.fillRect(hx, rimY - 0.55 * m, 0.62 * m, px(10));                                                                          // arm
    ctx.fillRect(hx + 0.62 * m, rimY - 0.95 * m, px(12), 1.22 * m);                                                               // backboard (edge-on)
    ctx.fillStyle = '#FF8A3C'; ctx.fillRect(hx + 0.62 * m + px(12), rimY - px(5), 0.46 * m, px(10));                            // rim, 10 ft up
    ctx.strokeStyle = 'rgba(244,246,250,0.8)'; ctx.lineWidth = px(3); ctx.beginPath();                                            // net
    ctx.moveTo(hx + 0.62 * m + px(14), rimY + px(5)); ctx.lineTo(hx + 0.70 * m + px(12), rimY + 0.4 * m); ctx.lineTo(hx + 1.0 * m + px(12), rimY + 0.4 * m); ctx.lineTo(hx + 1.08 * m + px(12), rimY + px(5)); ctx.stroke();
    if (g > sea) { ctx.fillStyle = 'rgba(52,118,156,0.5)'; ctx.fillRect(x0, sea, gx1 + px(70) - x0, g - sea); ctx.fillStyle = 'rgba(210,235,250,0.85)'; ctx.fillRect(x0, sea - px(3), pw, px(5)); }
    // the old ground line stays where the ground was (white, 6 px, under-stroke)
    ctx.fillStyle = 'rgba(6,9,15,0.6)'; ctx.fillRect(x0, g0 - px(7), pw, px(14));
    ctx.fillStyle = '#F4F6FA'; ctx.fillRect(x0, g0 - px(3), pw, px(6));
    ctx.restore();
    ctx.strokeStyle = 'rgba(6,9,15,0.75)'; ctx.lineWidth = px(4); F.round(ctx, x0, y0, pw, ph, px(10)); ctx.stroke();
    ctx.restore();
    ui.avoid({ x: x0, y: y0, w: pw, h: ph });
  }

  // ---- s014-s015 kilauea_sf (regional), s015-s024 halape (10 m), s024-s025 kilauea_sf again
  const nowArrow = (ctx, view, T0) => {
    const p = F.clamp((T0 - (lead('now') - 0.12)) / 0.3), out = F.clamp((T0 - (tNow + 1.5)) / 0.3); if (p <= 0 || out >= 1) return;
    const q = view.project(-155.2545, 19.2715, 2); if (!q) return;
    const pulse = 1 + 0.12 * Math.sin(F.clamp((T0 - tNow) / 0.5) * Math.PI), Lh = px(170) * pulse;
    ui.arrow(ctx, [[q[0] + px(70), q[1] - Lh - px(20)], [q[0] + px(70), q[1] - px(18)]], { p, t: T0, width: 15, alpha: 1 - out });
  };
  const stateK = (T0) => Object.assign(stateH(T0), {});
  const shotK1 = kit.terrainShot({ id: 'ch1-bigisland', t0: G0, t1: TH1 + 0.45, region: 'kilauea_sf', cam: (lt) => camH(lt + G0), state: (lt) => stateK(lt + G0), grade: (lt) => gradeH(lt + G0),
    ui(ctx, lt, tt, view) { nowArrow(ctx, view, lt + G0); } });
  scenes.push(blurred(shotK1, G0, G0 + 0.2));
  const halShot = kit.terrainShot({ id: 'ch1-halape', t0: TH1, t1: TQ + 0.5, fadeIn: 0.45, region: 'halape', cam: (lt) => camH(lt + TH1), state: (lt) => stateH(lt + TH1), grade: (lt) => gradeH(lt + TH1),
    world(ctx, lt, tt, view) {
      const T0 = lt + TH1, G = grove(view.S), tint = tintAt(T0), k = lightK(T0), lev = view.level;
      drawStars(ctx, view, T0, k <= 1 ? F.clamp(k * 1.2 - 0.2) * 0.9 : F.clamp(2 - k) * 0.9);
      const camP = view.S.cam.position, dist = (o) => { const p = view.S.xyz(o.lon, o.lat, o.h); return -Math.hypot(p.x - camP.x, p.z - camP.z); };
      // tents: in from the night, glow on {woke}, gone under the surge
      const tentA = 1 - F.clamp((T0 - (tRush + 0.1)) / 0.5);
      if (tentA > 0) G.tents.slice().sort((a, b) => dist(a) - dist(b)).forEach((tn, i) => drawTent(ctx, view, tn, T0, tint, i === 1 ? F.clamp((T0 - (lead('woke') - 0.1)) / 0.35) * (1 - F.clamp((T0 - (tRush + 0.1)) / 0.4)) * (0.9 + 0.1 * Math.sin(T0 * 9)) : 0, tentA));
      G.palms.slice().sort((a, b) => dist(a) - dist(b)).forEach(p => drawPalm(ctx, view, p, T0, tint, lev));
      drawDust(ctx, view, T0, tint);
      drawInset(ctx, T0);
    },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TH1;
      // NOVEMBER 1975 at the start of s016 (2.1 s), then HALAPĒ on its pin at {hal} (2.2 s)
      const s16 = K.s0('s016'), np = F.clamp((T0 - (s16 - 0.15)) / 0.35), nout = F.clamp((T0 - (s16 + 1.95)) / 0.27);
      if (np > 0 && nout < 1) ui.block(ctx, [{ text: 'NOVEMBER 1975', role: 'label', cap: 66 }], px(96), px(96), { anchor: 'left', p: np, out: nout, bar: PAL.yellow });
      const hp = F.clamp((T0 - (lead('hal') - 0.05)) / 0.3), hout = F.clamp((T0 - (tHal + 2.25)) / 0.27);
      if (hp > 0 && hout < 1) { const q = view.project(-155.2544, 19.2711, 3); if (q) ui.label(ctx, 'HALAPĒ', q[0], q[1], { t: tt, p: hp, alpha: 1 - hout, order: ['above', 'above-left', 'above-right'] }); }
    } });
  scenes.push(halShot);
  // s023: the USGS public-domain photo of the drowned grove, full-bleed, Ken Burns 2 %, 3 s, in on {morning}
  const PH = '/ep/ep02/img/ch1/halape_1975.jpg'; let photo = null;
  try { await api.loadImages([PH]); const im = api.img(PH), c = document.createElement('canvas'); c.width = im.width; c.height = im.height; c.getContext('2d').drawImage(im, 0, 0); photo = kit.gradeCanvas(c); } catch (e) { api.log('[ch1] halape photo missing: ' + e.message); }
  const PH0 = lead('morning', 4), PH1 = PH0 + 3.0;
  if (photo) scenes.push({ id: 'ch1-photo1975', t0: PH0, t1: PH1, layer: 1, fadeIn: 8 / 30, fadeOut: 8 / 30, draw(ctx, lt) {
    const k = 1.0 + 0.02 * (lt / 3), w = W * k, h = w * photo.height / photo.width, x = (W - w) / 2 - W * 0.006 * (lt / 3), y = (H - h) / 2;
    ctx.drawImage(photo, x, y, w, h);
  } });
  // s024-s025: the regional pull back on kilauea_sf; Kīlauea's south flank in the hero fill; the seaward arrow on {yards}
  const FLANK = [[-155.47, 19.17], [-155.43, 19.25], [-155.37, 19.31], [-155.315, 19.365], [-155.27, 19.372], [-155.22, 19.360], [-155.17, 19.368], [-155.12, 19.383], [-155.06, 19.398],
    [-155.00, 19.418], [-154.95, 19.445], [-154.90, 19.475], [-154.84, 19.505], [-154.78, 19.48], [-154.80, 19.30], [-155.10, 19.12], [-155.40, 19.08]];
  let flank = null;
  const getFlank = async () => {
    if (flank) return flank;
    const S = await kit.hub.terrain('kilauea_sf', 1, {}), bb = [-155.58, 19.10, -154.86, 19.49], g = heightGrid(S, bb, 2);
    const m = new Uint8Array(g.nx * g.ny);
    for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) { const [lon, lat] = g.ll(i, j), k = j * g.nx + i; if (g.h[k] > 0 && inPoly(lon, lat, FLANK)) m[k] = 1; }
    let n = 0; for (const v of m) n += v;
    flank = { g, mask: m, tex: maskTexture(g, { r: m }), rings: contour(g, m, 0, 0.8, 2, 200) };
    api.log(`[ch1] south flank fill: ${n} cells, ${flank.rings.length} rings (boundary approximate: Koaʻe fault zone and East Rift Zone)`);
    return flank;
  };
  const flankA = (T0) => F.clamp((T0 - (K.s0('s024') + 0.9)) / 0.6) * (1 - F.clamp((T0 - (tGo - 0.45)) / 0.3));
  const TGO = tGo - 0.06;                                                      // the whip-out cut (whoosh 91.64 starts it)
  const GW0 = TGO - 5 / 30;
  const whipOutL = (T0) => 50 * Math.pow(F.clamp((T0 - GW0) / (TGO - GW0)), 2.2);
  const shotK2 = kit.terrainShot({ id: 'ch1-flank', t0: TQ, t1: TGO, fadeIn: 0.5, region: 'kilauea_sf', state: (lt) => stateH(lt + TQ), grade: (lt) => gradeH(lt + TQ),
    cam: (lt) => { const c = camH(lt + TQ); c.dYaw += whipOutL(lt + TQ); return c; },
    mask: (lt) => { const a = flankA(lt + TQ); return a > 0 && flank ? { tex: flank.tex, bb: flank.g.bb, hero: 0.55 * a } : null; },
    async world() { await getFlank(); },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TQ, a = flankA(T0); if (a <= 0 || !flank) return;
      ui.outline(ctx, view.runs(flank.rings, 0, { every: 3 }), { alpha: a, width: 6 });
      const p = F.clamp((T0 - (lead('yards') - 0.1)) / 0.35);
      if (p > 0) { const q0 = view.project(-155.19, 19.345, 300), q1 = view.project(-155.19, 19.235, 0); if (q0 && q1) ui.arrow(ctx, [q0, q1], { p, t: T0, width: 15, alpha: a }); }
    } });
  scenes.push(blurred(ready(shotK2, getFlank), GW0, TGO));
  // s025 {did}: windward Oʻahu, the green Koʻolau cliffs over Kāneʻohe Bay (region pali, its film light); the whip lands on {did}
  const OAHU = { lon: -157.772, lat: 21.398, alt: 0.55, tLon: -157.806, tLat: 21.356, tH: 560, fov: 46 };
  const whipInL = (T0) => -55 * (1 - E.outExpoN(F.clamp((T0 - TGO) / (tDid - 0.1 - TGO))));
  const shotO = kit.terrainShot({ id: 'ch1-oahu', t0: TGO, t1: ch.t1x, region: 'pali', state: { look: 'day', sun: [75, 55], water: 'film', set: { foamAmt: 0.25 }, post: { exposure: 1.15, sat: 1.1, contrast: 1.08 } },
    cam: (lt) => { const T0 = lt + TGO, c = Object.assign({}, OAHU); const pz = Math.max(0, T0 - tDid) * 0.004; c.lon -= pz * 0.5; c.lat -= pz; c.dYaw = whipInL(T0); c.near = 0.02; c.far = 500; return c; } });
  scenes.push(blurred(shotO, TGO, TGO + 0.25));
  api.log(`[ch1] shots: demo 0-${TA.toFixed(2)}, ice -${TC.toFixed(2)}, ride -${TW.toFixed(2)}, bigisland ${G0.toFixed(2)}-${(TH1 + 0.45).toFixed(2)}, halape -${(TQ + 0.5).toFixed(2)}, flank -${TGO.toFixed(2)}, oahu -${ch.t1x.toFixed(2)}`);
}
