// Chapter 1 "Only the Top" (s001-s025, 0.00-93.81 s, no card; base shots to t1x). Every beat is keyed to Rodney's markers (K).
//   s001-s003  frame 1 = the NO OCEAN thumbnail (final_ep02_1.jpg) in motion: drained Big Island, thin white line on today's coast,
//              NO OCEAN in dark ink on the sky; tilt down at {most}, coast pulse at {under}, the USGS postcard lands on the dry cap at
//              {card} (slap 9.12 s), the cap takes the hero fill (exact #FF5A36 at 55 % after the grade, under the card) and outline at
//              {top}; as s003 ends the card flutters off frame right at full opacity.
//   s004-s006  one continuous camera: flight NW while the sea refills, names on their words; the drain starts 0.3 s before "Drop"
//              (mix drain_start 15.21 s, the music stop-down sits mid-drain) and the SEA LEVEL gauge lands on 400 FT on {ft400}
//              (6-frame punch at the hit_body layer, {ft400} + 0.36 s); the outlines merge into the -400 ft contour at {one}.
//   s007       the same camera dives from the ONE ISLAND framing to a low pass north of Lānaʻi, looking ESE across the dry ʻAuʻau
//              Channel floor (the land bridge) to West Maui; three seabirds; LAST ICE AGE grows word by word from "last".
//   s008       GAG (cut on the music dip): on the ʻAuʻau floor (-52 m) 15 m up looking ENE at West Maui, the paper tourist walks left to
//              right among seeded true-size rocks, one hop landing on the paper tap (25.50 s), a clear hat tip with a small bow on
//              {ferry}, walks on as the line ends while his bag scrapes after him (26.88 s).
//   s009-s011  {look}: the camera cranes up to 5 km and turns north over Maui Nui while the sea falls from -400 ft toward -1,000 m
//              (gauge marker only; the -400 ft shore as a cream line); the water turns navy as it falls (no lagoon, no foam rim) with a
//              blue haze on the new surface; over Molokaʻi's north cliffs the slope falls into blue depth on {nobottom}; over the ledge
//              on {ledge}; on {plunge} the camera is tipped about 41-51 degrees down the slope, riding down it.
//   s012-s013  from {plunge} + 0.5 s it pulls back and up, still looking down, then swings west: Penguin Bank (hero fill in exact
//              #FF5A36 at 42 % after the grade, white outline of its top above -60 m, label PENGUIN BANK) framed on {bank} (the camera
//              stops there); the sea rises from "rose"; the fill stays until the water reaches the bank's top (-40 m), so the hero shape
//              goes under on {drowned}; foam only on the waterline.
//   s014-s015  whip-pan (motion blur, 14 sub-frame samples on the fastest frames) to the Big Island's south coast in morning light,
//              steel-blue water (sat 1.03); one yellow down-arrow pulses on {now}; an eased push toward Halapē while the light falls.
//   s016-s023  1975, Halapē (solemn: no gags, no comic sound, no stings), seen from the sea side looking DOWN (pitch 36-46 degrees from
//              0.6-1.25 km) so beach, grove and water fill the frame and the soft hillside stays out of it: s016 the cove (NOVEMBER 1975,
//              HALAPĒ on its pin at {hal}); s017 closer on the camp, the palms shiver with the foreshock (59.3 s), a lantern glows in
//              one tent on {woke}; s018 the quiet cove from the SE, the jolt and a warm dust curtain off the low cliff behind the grove
//              on {hit}; s019 pull-up on {lurch}: the coastal block outlined in white, one short yellow arrow seaward; s020 the block
//              sinks 3.5 m on {drop} (sea level against today's post-1975 grid -3.5 m to 0) and floods among the palms, with a side-on
//              inset in the scene's pre-dawn light (old ground line, a face-on basketball hoop at true scale, one yellow drop arrow, no
//              numbers) that fades before the wave; s021 the surge runs in from the east (frame right) and peaks on "rushed"; first light
//              creeps in over 7 s from the surge; s022 {two}: wide slow drift back, desaturated; s023 {morning}: the USGS photo for 3 s,
//              then the flooded grove from the bench behind it, water behind and between the trunks.
//              Palms are built in 3D at their true positions and projected (they foreshorten with the terrain), trunks mirrored in the
//              flood water; the strip the sea uncovers before the drop is the old beach (sand).
//   s024-s025  up and back to the Big Island's south side, Kīlauea's south flank in the hero fill (exact #FF5A36 at 55 % after the
//              grade; approximate boundary: Koaʻe fault zone and East Rift Zone, the coast from the grid), a short yellow arrow
//              seaward on {yards}; {go}: whip-pan NW (motion blur) that lands on windward Oʻahu's fluted Koʻolau pali, seen from over
//              Kāneʻohe (region pali, sat 1.0) on {did}; the ch2 card rides over it.
// Local helpers (no shared change): spline() C1 camera keys, blurred() sub-frame motion blur for whips, projRings() fills after the
// grade, palms/tents/stars/dust/rocks/surge/inset/coastal block. api.cue lists the picture's own event times under the mix's names.
import { flight, mixState, PLACES, E, PAL, F, MLOOKS, PRESETS, heightGrid, contour, maskTexture, WATER_FILM, MOVE_WATER } from './shared.js';

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
// n: samples, or a function of film time (14 on the fastest 2-3 whip frames: 6 left stair-step copies of the coast at ~20 deg/frame)
function blurred(shot, w0, w1, n = 6, shutter = 0.5) {
  const inner = shot.draw.bind(shot);
  shot.draw = async function (ctx, lt, t, api) {
    if (t < w0 || t > w1 || api.Q.noblur) return inner(ctx, lt, t, api);
    const A = ctx.globalAlpha, dt = shutter / api.FPS, m = api.Q.draft ? 3 : typeof n === 'function' ? n(t) : n;
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
const hex3 = (s) => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
const mixh = (a, b, p) => '#' + mixc(hex3(a), hex3(b), p).map(v => v.toString(16).padStart(2, '0')).join('');

export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const t = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f);
  const ch = K.chapter(1);

  // =========================================================================================== s001-s006 (the foundation demo)
  const tDr = t('drained'), tMost = t('most'), tUnder = t('under'), tCard = t('card'), tTop = t('top');
  const fly0 = K.s1('s003') + 0.03, fly1 = fly0 + 1.6;                         // the flight starts as s003 ends (1.6 s, eased)
  const drain0 = K.s0('s005') - 0.3, drain1 = lead('ft400');                   // 0 -> -400 ft from just before "Drop" (mix drain_start 15.21 s),
                                                                               // lands on {ft400}: the music stop-down (15.77-16.92 s) sits mid-drain
  // fills drawn after the grade in the exact hero orange: project every ring vertex (at hf(lon, lat) m) without cutting the ring
  const projRings = (view, rings, hf) => rings.map(r => r.map(([lon, lat]) => view.project(lon, lat, hf(lon, lat))).filter(Boolean)).filter(r => r.length > 2);
  const L400 = -400 / FT, PB_LEVEL = -60;                                                      // -121.92 m: the gauge lands exactly on 400
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
    // s012: Penguin Bank's flat top = the ground above -60 m around the bank (script: top at about -30 to -60 m). On the 78 m grid the
    // bank already joins West Molokaʻi at -65 m, so -60 m is the deepest level at which it is a table of its own; any land cell (> 0 m)
    // inside the flood fill means it joined Molokaʻi (then the fill would close over the island: warned, never drawn silently)
    isl.pb = await kit.island(Object.assign({ level: PB_LEVEL, seeds: [PLACES['penguin-bank'], [-157.6, 21.0]] }, PBB));
    const gp = isl.pb.g; let molo = 0; for (let k = 0; k < gp.nx * gp.ny; k++) if (isl.pb.mask[k] && gp.h[k] > 0) molo++;
    if (molo) api.log(`[ch1] WARNING Penguin Bank top at ${PB_LEVEL} m joins Molokaʻi (${molo} land cells)`);
    isl.pbTex = kit.maskTexture(gp, { r: isl.pb.mask });
    let nb = 0; for (const v of isl.bridge) if (v > 127) nb++;
    api.log(`[ch1] fused island at ${L400.toFixed(1)} m: ${Math.round(isl.one.areaKm2)} km2, ${isl.one.rings.length} rings; bridge cells ${nb}; Kaho'olawe separate: ${!touch}; Penguin Bank top ${Math.round(isl.pb.areaKm2)} km2 (${isl.pb.rings.length} rings, Molokaʻi land cells in it: ${molo})`);
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
    if (lt < fly0 + 0.4) return null;                                         // the cap fill is drawn after the grade (world), not in the stage
    const dim = F.clamp((lt - fly1) / 0.5), hero = 0.38 * E.inOut(F.clamp((lt - tOne) / 0.35));
    return { tex: isl.mnTex, bb: isl.one.g.bb, hero, dim: 0.75 * dim };
  };
  const oneOut = (lt) => F.clamp((lt - (TA - 0.27)) / 0.27);                   // ONE ISLAND dissolves out over 8 frames before the dive

  scenes.push(ready(kit.terrainShot({
    id: 'ch1-demo', t0: 0, t1: TA, region: REG, stage: STAGE, cam: camD, level: levelD, state: stateD, mask: maskD,
    async world(ctx, lt, tt, view) {
      await getIsl();
      // {top}: the cap's hero fill in the exact #FF5A36 at 55 % after the grade (through the noocean masked look it read maroon), under
      // the card; the coast ring at 0 m covers the cap's screen footprint from this high southern camera (the summit projects inside it)
      const capA = capFill(lt);
      if (capA > 0 && isl.cap) ui.fill(ctx, projRings(view, isl.cap.rings, () => 0), { alpha: capA, fill: 0.55 });
      if (postcard && lt > tCard - 0.05 && lt < fly1) {
        // the drop starts on "postcards" and lands on the paper slap (spot sync 9.12 s = the word's end - 0.03 s); as s003 ends the card
        // flutters off frame right at full opacity (a lift, an eastward drift that speeds up, a flutter roll) until it is out of frame
        const pd = F.clamp((lt - tCard) / (K.Te('card') - 0.03 - tCard)), lift = 0.1 * F.clamp((lt - lead('top')) / 0.25), oe = Math.max(0, lt - (fly0 - 0.2)), off = E.in(F.clamp(oe / 0.9));
        if (off < 1 || oe < 1.2) kit.drawPostcard(ctx, view, postcard, { lon: -155.5 + off * 2.4 + oe * 0.3, lat: 19.62 - off * 0.25, wKm: 72, rot: 4 + 38 * off + 14 * Math.sin(oe * 11) * F.clamp(oe / 0.25),
          hm: 2600 + off * 14000, p: pd, lift: F.clamp(lift + 0.5 * F.clamp(oe / 0.3) + 0.35 * Math.sin(oe * 9)), alpha: 1 });
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
      // the 6-frame lock-in punch on 400 FT at the hit_body layer (spot section 10: {ft400} + 0.36 s), scaled about the plate's left edge
      const pu = (lt - (t('ft400') + 0.36)) * 30, punch = pu > 0 && pu < 6 ? Math.sin(Math.PI * pu / 6) : 0;
      ctx.save(); if (punch > 0) { const cx = px(96), cy = px(96 + 75); ctx.translate(cx, cy); ctx.scale(1 + 0.09 * punch, 1 + 0.09 * punch); ctx.translate(-cx, -cy); }
      ui.gauge(ctx, { p: gp, out: gOut, level: Math.max(view.level, -150), range: 150, to: 492, unit: 'FT', pulse: Math.max(pulse, punch) });
      ctx.restore();
    },
  }), getIsl));

  // =========================================================================================== s007 the dive and the golden pass
  // s007: the golden pass, sun low from the south-southeast (side light; the glint stays outside the frame of the ESE-looking pass).
  // s008-s013 (one continuous shot): a day sun from the east-southeast (side light on the gag, Molokaʻi's north slope and Penguin
  // Bank). The reef flat albedo leans cool so the lit dry floor reads neutral grey, not tan (look book; clone gate tan <= 10 %)
  // (a warmer golden-hour look was tried in round 8: drain-clone distance fell to 10.1-10.6, gate FAIL, so the light stays as is)
  const GOLD = { look: 'warm', sun: [165, 26], water: 'film', level: L400, set: { foamAmt: 1, landSat: 0.9, landGain: 1.0, nearAmt: 0.55, glintAmt: 0.06, waveAmt: 0.7, detail: 1.3,
      reefCol: [0.058, 0.066, 0.082], sedCol: [0.050, 0.051, 0.054] }, post: { exposure: 1.14, contrast: 1.1, sat: 0.95 } };
  const RIDE = { look: 'day', sun: [118, 27], water: 'film', level: L400, set: { foamAmt: 1, landSat: 0.95, landGain: 1.0, nearAmt: 0.55, glintAmt: 0.06, waveAmt: 0.7, detail: 1.3,
      reefCol: [0.060, 0.066, 0.078], sedCol: [0.050, 0.051, 0.054] }, post: { exposure: 1.12, contrast: 1.1, sat: 0.95 } };
  const blend = (a, b, p) => { const s = mixState(a, b, p); s.mlook = null; s.mlookAmt = 0; return s; };
  const tIce = t('ice'), TC = K.s1('s007') - 0.23;                             // cut to the gag on the music dip, under "it really happened"
  const c0 = camD(TA), st0 = stateD(TA);
  // s007: dive from the ONE ISLAND framing over the Kalohi Channel to a low golden pass north of Lānaʻi, looking ESE across the dry
  // ʻAuʻau Channel floor (the land bridge between Lānaʻi and West Maui, script 20.885N 156.758W) with West Maui behind it
  const camB0 = spline([
    Object.assign({ t: TA, stop: true }, pickCam(c0)),
    { t: TA + 1.9, lon: -157.03, lat: 20.965, alt: 4.2, tLon: -156.76, tLat: 20.885, tH: -60, fov: 42, shiftX: 0, shiftY: 0, dYaw: 0, dPitch: 0 },
    { t: TC, lon: -156.892, lat: 20.918, alt: 1.5, tLon: -156.735, tLat: 20.872, tH: -50, fov: 46, shiftX: 0, shiftY: 0, dYaw: 0, dPitch: 0 },
    { t: TC + 0.8, lon: -156.872, lat: 20.912, alt: 1.3, tLon: -156.725, tLat: 20.870, tH: -50, fov: 46, shiftX: 0, shiftY: 0, dYaw: 0, dPitch: 0 },   // still moving at the cut
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
      // whole words on their spoken words from "last" (the plate grows with them: never a mostly empty plate)
      const wt = [K.word('s007', 'last').start - 0.1, lead('ice'), K.word('s007', 'age').start - 0.1];
      const p = F.clamp((T0 - wt[0]) / 0.35), out = F.clamp((T0 - (TC - 0.3)) / 0.27);
      if (p > 0) ui.block(ctx, [{ words: ['LAST', 'ICE', 'AGE'], role: 'headline', cap: 100 }], W / 2, px(96), { anchor: 'center', p, out, bar: PAL.cyan, wordTimes: wt, lt: T0, grow: true });
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
  // s008: the dry ʻAuʻau Channel floor between Lānaʻi and West Maui (78 m grid: flat at about -52 m), the camera 15 m over it looking
  // ENE at West Maui, the walker's goal; Lānaʻi is behind the camera and the Pailolo side never appears in the gag
  const GE = { lon: -156.790, lat: 20.846, floor: -0.0519 }, GHD = 68;        // eye, floor height (km) under it, heading (deg)
  const KX = KM * 1000 * Math.cos(20.85 * D2R), KY = KM * 1000;                 // metres per degree there
  const gF = [Math.sin(GHD * D2R), Math.cos(GHD * D2R)], gR = [Math.cos(GHD * D2R), -Math.sin(GHD * D2R)];
  const gll = (fw, rt) => [GE.lon + (gF[0] * fw + gR[0] * rt) / KX, GE.lat + (gF[1] * fw + gR[1] * rt) / KY];   // metres forward / right -> lon, lat
  const GT = gll(14000, 0);                                                    // the aim point on West Maui's lower slopes
  const tBk = lead('bank') - 0.1;                                              // the bank is framed, filled and outlined on its word
  const camC = spline([
    { t: TC, lon: GE.lon, lat: GE.lat, alt: GE.floor + 0.015, tLon: GT[0], tLat: GT[1], tH: 160, fov: 34, dYaw: 0, dPitch: 0 },
    { t: tLook - 0.05, stop: true, lon: gll(7, 0)[0], lat: gll(7, 0)[1], alt: GE.floor + 0.016, tLon: GT[0], tLat: GT[1], tH: 160, fov: 32.5 },
    // {look}: the crane rises off the floor and turns north over Maui Nui while the sea keeps falling around the new island
    { t: tLook + 1.9, lon: -156.800, lat: 20.905, alt: 5.2, tLon: -156.845, tLat: 21.03, tH: -300, fov: 44 },
    // s010: over Molokaʻi's north cliffs toward Maui Nui's new north shore; on {nobottom} the slope falls away into navy water, no floor
    { t: tNoB, lon: -156.925, lat: 21.135, alt: 2.9, tLon: -156.985, tLat: 21.285, tH: -700, fov: 46 },
    // s011 {ledge}: over the -400 ft shore (the cream line); {plunge}: tipped about 45 degrees down the slope, riding down it
    { t: tLedge, lon: -156.948, lat: 21.200, alt: 1.6, tLon: -156.966, tLat: 21.262, tH: -1000, fov: 48 },
    { t: tPlunge - 0.07, lon: -156.952, lat: 21.236, alt: 1.3, tLon: -156.970, tLat: 21.272, tH: -2600, fov: 54 },     // pitch about 41 deg
    { t: tPlunge + 0.5, lon: -156.956, lat: 21.246, alt: 1.05, tLon: -156.972, tLat: 21.280, tH: -2700, fov: 54 },     // about 42 deg
    // s012: from {plunge} + 0.5 the camera pulls back and up while still looking steeply down (to {plunge} + 1.2), then swings west to
    // Penguin Bank, the flat table off West Molokaʻi, high and dry above the water: framed and filled on {bank}
    { t: tPlunge + 1.2, lon: -157.00, lat: 21.250, alt: 3.0, tLon: -157.04, tLat: 21.262, tH: -2400, fov: 50 },        // about 51 deg
    { t: tBk, stop: true, lon: -157.30, lat: 21.25, alt: 9.0, tLon: -157.60, tLat: 20.99, tH: -60, fov: 38 },
    // s013: while the sea rises and drowns the bank, pull back north-east so West Molokaʻi comes in lower left (the islands part again)
    { t: TW, lon: -157.16, lat: 21.30, alt: 10.5, tLon: -157.45, tLat: 21.03, tH: -60, fov: 42 },
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
  let tDrownW = tDrown; for (let T0 = rise0; T0 < tDrown + 1.5; T0 += 1 / 30) if (levelC(T0) >= -40) { tDrownW = T0; break; }
  const drainP = (T0) => F.clamp((L400 - levelC(T0)) / (1000 + L400));          // 0 at -400 ft, 1 at -1,000 m
  // the deep water of the ride: as the sea falls past -400 ft the film's turquoise gives way to navy (no lagoon, no foam rim at -1,000 m),
  // and a blue haze sits on the new sea surface, so the slope falls into blue depth with no floor; the rise keeps the foam on the
  // waterline only (foamPx 0.3: the default rim reached 30-60 m deep on the bank's steep edge)
  // (the water darkens with depth away from the waterline, the haze lies on the new surface: 'deeper and deeper', not a lagoon)
  const DEEPW = [[0.020, 0.078, 0.155], [0.016, 0.060, 0.135], [0.003, 0.013, 0.045]];
  const RLOOK = (k) => ({ zenith: '#1553b5', horizon: mixh('#9fc4ee', '#86a6d0', k), haze: [mixh('#a5c0e0', '#4f7cb6', k), 0.74], sun: '#fff3e2', glow: ['#ffe6c8', 0.5], sunI: 3.5, skyI: 0.70 });
  const stateC = (T0) => {
    const s = blend(RIDE, RIDE, 0), k = E.inOut(F.clamp(drainP(T0) * 1.6)), lev = levelC(T0), rising = T0 > rise0;
    s.post.exposure = 1.12 + 0.06 * k; s.set.oldLine = 0; s.set.ringH = 30;
    // haze: the scale height shrinks from 6 km to 0.45 km while the column grows from 0.017 to 0.135 (a linear blend of both made a
    // tall, dense whiteout mid-drain)
    const fH = 6.0 * Math.pow(0.075, k), fCol = 0.0168 + 0.118 * k;
    s.look = RLOOK(k); s.fog = [fCol / fH, 0.00012 + 0.00028 * k, fH];
    s.waterCols = WATER_FILM.map((c, i) => c.map((v, j) => v + (DEEPW[i][j] - v) * k));
    s.set.foamAmt = rising ? 0.7 : 1 - k; s.set.foamPx = rising ? 0.3 : 2.5; s.set.edgeGlow = 0.6 * (1 - k); s.set.surfAmt = 0.6 * (1 - k);
    s.set.wRamp = [2 + 3 * k, 12 + 28 * k, 25 + 35 * k, 160 + 540 * k];
    return s;
  };
  // the paper tourist walks left to right (from Lānaʻi's side toward West Maui), one hop landing on the paper tap (spot 25.50 s),
  // tips his hat to camera on {ferry}, walks on when the line ends; the bag scrapes after him in the gap (spot 26.88 s)
  const tHop = K.s0('s008') + 0.16, tWalk = K.Te('ferry') + 0.06;
  const PATH = [gll(127, -46), gll(104, 47)];                                  // 127 m ahead on the left -> 104 m ahead on the right
  const HF = 28;                                                               // his height in metres (paper theatre scale: about 38 % at the hold)
  const walk = (T0) => {                                                       // 0..1 along the path, a stop for the hat tip
    const seg = (a, b, x0, x1, T) => x0 + (x1 - x0) * F.clamp((T - a) / (b - a));
    if (T0 < tHop - 0.4) return seg(TC - 0.6, tHop - 0.4, 0, 0.30, T0);
    if (T0 < tHop) return seg(tHop - 0.4, tHop, 0.30, 0.42, T0);              // the hop (lands on the paper tap)
    if (T0 < tWalk) return 0.42 + 0.02 * E.out(F.clamp((T0 - tHop) / 0.25));
    return seg(tWalk, tLook + 2.5, 0.44, 1.0, T0);
  };
  const C = { tourist: await kit.paper('tourist'), suitcase: await kit.paper('suitcase') };
  const lerpLL = (u) => [PATH[0][0] + (PATH[1][0] - PATH[0][0]) * u, PATH[0][1] + (PATH[1][1] - PATH[0][1]) * u];
  const ppmAt = (view, lon, lat, hm) => { const a = view.project(lon, lat, hm), b = view.project(lon, lat, hm + 10); return a && b ? Math.hypot(a[0] - b[0], a[1] - b[1]) / 10 : 0; };
  // the dry floor at ground level: seeded rock and coral rubble at true size (0.4-2.6 m) so the plain reads as ground, not a void;
  // the walk lane stays clear (local helper: the stage's 78 m floor has no close-range detail, requests/ch1.md item 5)
  const ROCKS = (() => { const r = F.rng(808), a = [];
    for (let k = 0; k < 900 && a.length < 170; k++) { const fw = 20 + Math.pow(r(), 0.75) * 340, rt = (r() - 0.5) * 2 * (22 + fw * 0.78), s = 0.4 + Math.pow(r(), 2.3) * 2.2, kind = r(), seed = r() * 100;
      if (fw > 88 && fw < 145 && Math.abs(rt) < 75) continue;
      const [lon, lat] = gll(fw, rt); a.push({ lon, lat, fw, s, kind, seed, h: null }); }
    return a.sort((p, q) => q.fw - p.fw); })();
  function drawRock(ctx, view, rk, a) {
    if (rk.h == null) rk.h = view.S.heightAt(rk.lon, rk.lat);
    const b = view.project(rk.lon, rk.lat, rk.h); if (!b) return; const ppm = ppmAt(view, rk.lon, rk.lat, rk.h), w = rk.s * ppm * 1.6, h = rk.s * ppm * 0.62;
    if (w < 2 || b[0] < -w || b[0] > W + w || b[1] > H + h) return;
    const coral = rk.kind > 0.75, body = coral ? [146, 142, 134] : [70, 68, 66], lit = coral ? [184, 180, 170] : [120, 116, 110];
    ctx.save(); ctx.globalAlpha *= a;
    ctx.fillStyle = 'rgba(14,16,22,0.30)'; ctx.beginPath(); ctx.ellipse(b[0] - w * 0.42, b[1] + h * 0.08, w * 0.62, h * 0.30, 0, 0, 7); ctx.fill();   // shadow away from the ESE sun
    const P = []; for (let i = 0; i <= 8; i++) { const an = Math.PI * i / 8, rr = 1 + 0.22 * (hash(rk.seed, i) - 0.5); P.push([b[0] + Math.cos(an) * w / 2 * rr, b[1] - Math.sin(an) * h * rr]); }
    ctx.fillStyle = rgba(body, 1); ctx.beginPath(); P.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.quadraticCurveTo(b[0], b[1] + h * 0.16, P[0][0], P[0][1]); ctx.fill();
    ctx.fillStyle = rgba(lit, 0.9); ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]); for (let i = 1; i <= 4; i++) ctx.lineTo(P[i][0], P[i][1]);
    ctx.quadraticCurveTo(b[0] + w * 0.12, b[1] - h * 0.35, P[0][0] - w * 0.05, P[0][1]); ctx.fill();          // the lit (sun) side
    ctx.restore();
  }
  const shotC = kit.terrainShot({
    id: 'ch1-ride', t0: TC, t1: TW, region: REG, stage: STAGE, level: (lt) => levelC(lt + TC), state: (lt) => stateC(lt + TC),
    cam: (lt) => { const c = camC(lt + TC); c.dYaw = (c.dYaw || 0) + whipOutR(lt + TC); c.near = c.alt < 0.5 ? 0.004 : 0.02; c.far = 600; return c; },
    async world(ctx, lt, tt, view) {
      await getIsl();
      const T0 = lt + TC; if (T0 > tLook + 3.2) return;
      const ra = 1 - F.clamp((T0 - tLook) / 0.6);
      if (ra > 0) for (const rk of ROCKS) if (rk.fw > 116) drawRock(ctx, view, rk, ra);
      const u = walk(T0), [lon, lat] = lerpLL(u), hm = view.S.heightAt(lon, lat);
      const ppm = ppmAt(view, lon, lat, hm);
      if (ppm) {
        const hop = T0 > tHop - 0.4 && T0 < tHop ? Math.sin(Math.PI * (T0 - (tHop - 0.4)) / 0.4) * HF * ppm * 0.26 : 0;
        const land = F.clamp(1 - Math.abs(T0 - tHop - 0.05) / 0.12);                // squash on the landing
        const tipA = F.clamp((T0 - (lead('ferry') - 0.12)) / 0.25) * (1 - F.clamp((T0 - (tWalk - 0.2)) / 0.25));
        const walking = T0 < tHop - 0.4 || T0 > tWalk;
        const bob = walking ? Math.abs(Math.sin(T0 * 7.5)) * HF * ppm * 0.025 : 0;
        // the bag first (behind him, trailing), then him
        const bu = Math.max(0, u - 0.07), [blon, blat] = lerpLL(bu), bhm = view.S.heightAt(blon, blat);
        const scrape = T0 > tWalk - 0.02 && T0 < tWalk + 0.8 ? Math.abs(Math.sin((T0 - tWalk) * 31)) * 0.5 : 0;
        kit.drawCutout(ctx, view, C.suitcase, { lon: blon - 0.00003, lat: blat - 0.00004, hm: bhm, hPx: 0.36 * HF * ppm, t: T0, seed: 2, wobble: 0.02, lean: -0.06 - 0.05 * scrape, hop: (walking ? Math.abs(Math.sin(T0 * 7.5 + 1.2)) * 0.012 : 0) * HF * ppm + scrape * 2 });
        // {ferry}: the hat comes up 22 % of his height, tilted 35 degrees, with a small bow (0.1 rad) toward the walk
        kit.drawCutout(ctx, view, C.tourist, { lon, lat, hm, hPx: HF * ppm, t: T0, seed: 1, wobble: 0.02, hop: hop + bob, squash: 0.12 * land + 0.03 * tipA, lean: walking ? 0.05 : 0.1 * tipA,
          parts: { hat: { off: [HF * ppm * 0.05 * tipA, -HF * ppm * 0.22 * tipA], rot: -0.61 * tipA } } });
      }
      if (ra > 0) for (const rk of ROCKS) if (rk.fw <= 116) drawRock(ctx, view, rk, ra);
    },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TC;
      // s009-s011: the -400 ft shore of the one island as a cream line while the sea falls away from it ("the shore becomes a ledge"),
      // on once the crane is up, gone as the camera pulls back to the bank
      const sa = F.clamp((T0 - (tLook + 1.3)) / 0.5) * F.clamp((L400 - 25 - levelC(T0)) / 40) * (1 - F.clamp((T0 - (tPlunge + 1.0)) / 0.5));
      if (sa > 0 && isl.one) ui.line(ctx, view.runs(isl.one.rings, L400, { every: 2 }), { width: 6, color: '#F1E8D6', alpha: sa * 0.95, under: 0.4 });
      // Penguin Bank: the hero fill in the exact #FF5A36 at 42 % (a drained frame: like the ONE ISLAND join, 35-45 % keeps the clone
      // gate's red share under 3 %; at 66 % it read 6 % red) (drawn after the grade, so the low sun cannot turn it maroon), the white
      // outline of its flat top (ground above -60 m), both fading as the rising sea reaches the top; then the label
      // the fill stays until the water reaches the bank's highest cells (about -40 m), so the hero shape goes under on {drowned}
      const pa = F.clamp((T0 - (lead('bank') - 0.1)) / 0.3) * (1 - F.clamp((levelC(T0) + 42) / 14));
      if (pa > 0 && isl.pb) {
        ui.fill(ctx, projRings(view, isl.pb.rings, () => PB_LEVEL), { alpha: pa, fill: 0.42 });
        ui.outline(ctx, view.runs(isl.pb.rings, PB_LEVEL, { every: 2 }), { alpha: pa, width: 6, p: F.clamp((T0 - (lead('bank') - 0.1)) / 0.5) });
      }
      const la = F.clamp((T0 - lead('bank')) / 0.3) * (1 - F.clamp((T0 - (rise0 + 0.3)) / 0.3));
      if (la > 0) { const q = view.project(-157.55, 20.99, -60); if (q) ui.label(ctx, 'PENGUIN BANK', q[0], q[1], { t: tt, p: la, order: ['above', 'above-right', 'above-left'] }); }
      // SEA LEVEL gauge (marker only, no digits; range 1,000 m): in while the sea falls, out while it holds, in again while it rises
      const gin = F.clamp((T0 - (K.s0('s009') - 0.1)) / 0.5) * (1 - F.clamp((T0 - (DR1 + 0.3)) / 0.4)) + F.clamp((T0 - (rise0 - 0.3)) / 0.4) * (1 - F.clamp((T0 - (W0 - 0.35)) / 0.3));
      if (gin > 0) ui.gauge(ctx, { p: 1, alpha: F.clamp(gin), level: Math.max(view.level, -1000), range: 1000, value: false });
    },
  });
  scenes.push(blurred(ready(shotC, getIsl), W0, TW, (tt) => tt > TW - 3.5 / 30 ? 14 : 6));

  // =========================================================================================== s014-s024 the Big Island, 1975
  const tNow = t('now'), tNotA = t('notalways'), tHal = t('hal'), tWoke = t('woke'), tHit = t('hit'), tLurch = t('lurch'), tDrop = t('drop');
  const tFore = K.word('s017', 'earthquake').start - 0.3;                    // the foreshock rumble starts here (spot 59.33 s)
  const tRush = K.word('s021', 'rushed').start, tTwo = t('two'), tMorn = t('morning'), tYards = t('yards'), tGo = t('go'), tDid = t('did');
  const HAL = { lon: -155.2552, lat: 19.2704 };                                // the grove (the 1975 USGS photo; NPS shelter 19.2719, -155.2537)
  // one orbit path around the grove (log distance): the whip landing, the push, the night hold, the lurch pull-up, the drop, the pull back
  const TH1 = K.s0('s015') + 1.78, TQ = K.s0('s024') + 0.8;                                // stage hand-offs: kilauea_sf -> halape, halape -> kilauea_sf
  const G0 = W0 + 5 / 30;                                                      // whip-in starts at the cut
  // round 8: the cove is seen from the sea side, looking DOWN (pitch 36-46 degrees from 0.6-1.25 km), so beach, grove and water fill
  // the frame and the soft 10 m / 30 m hillside behind stays out of it (only the scarp foot shows, as a band, for the {hit} dust)
  const orb = kit.orbitPath([
    { t: G0, lat: 19.300, lon: -155.235, d: 34, tilt: 72, heading: 310, fov: 40 },
    { t: G0 + 0.55, lat: 19.300, lon: -155.235, d: 33, tilt: 72, heading: 350, fov: 40, ease: E.outExpoN },
    { t: K.s1('s014') + 0.2, lat: 19.296, lon: -155.238, d: 30, tilt: 72, heading: 352, fov: 40, ease: E.inOutSine },
    // s015: the push keeps the coast and the cove centred as the light falls, tipping down toward the cove
    { t: K.s0('s015') + 1.9, lat: HAL.lat + 0.0006, lon: HAL.lon + 0.0004, d: 3.2, tilt: 58, heading: 350, fov: 30, ease: E.inOut },
    // s016: the cove in pre-dawn light, a slow push (NOVEMBER 1975, HALAPĒ)
    { t: K.s0('s016') - 0.2, lat: HAL.lat + 0.0004, lon: HAL.lon + 0.0002, d: 0.95, tilt: 44, heading: 345, fov: 24, ease: E.inOut },
    { t: K.s1('s016') - 0.1, lat: HAL.lat + 0.0004, lon: HAL.lon + 0.0001, d: 0.82, tilt: 44, heading: 349, fov: 24, ease: E.inOutSine },
    // s017: closer on the camp (the lantern comes on in one tent on "woke them up")
    { t: K.s0('s017') + 1.3, lat: HAL.lat + 0.0006, lon: HAL.lon + 0.0001, d: 0.72, tilt: 46, heading: 2, fov: 24, ease: E.inOut },
    { t: K.s1('s017'), lat: HAL.lat + 0.0006, lon: HAL.lon + 0.0001, d: 0.68, tilt: 46, heading: 5, fov: 24, ease: E.inOutSine },
    // s018: "more than an hour later": the quiet cove from the south-east, a slow drift, then the jolt and dust off the scarp foot on {hit}
    { t: K.s0('s018') + 1.2, lat: HAL.lat + 0.0007, lon: HAL.lon, d: 0.85, tilt: 47, heading: 330, fov: 26, ease: E.inOut },
    { t: tLurch - 0.1, lat: HAL.lat + 0.0007, lon: HAL.lon, d: 0.82, tilt: 47, heading: 327, fov: 26, ease: E.inOutSine },
    // s019 {lurch}: a quick pull-up over a long stretch of coast (the coastal block outlined, a short seaward arrow)
    { t: tLurch + 1.3, lat: HAL.lat + 0.0012, lon: HAL.lon + 0.002, d: 4.0, tilt: 52, heading: 345, fov: 34, ease: E.inOut },
    { t: K.s0('s020') + 0.2, lat: HAL.lat + 0.0012, lon: HAL.lon + 0.0021, d: 3.8, tilt: 52, heading: 344, fov: 34, ease: E.inOutSine },
    // s020 {drop}: back down to the grove from the south-west (the inset sits top-left)
    { t: tDrop - 0.25, lat: HAL.lat + 0.0003, lon: HAL.lon - 0.0002, d: 0.82, tilt: 46, heading: 15, fov: 24, ease: E.inOut },
    { t: K.s1('s020'), lat: HAL.lat + 0.0003, lon: HAL.lon - 0.0002, d: 0.78, tilt: 46, heading: 19, fov: 24, ease: E.inOutSine },
    // s021: low and close, looking north along the shore: the surge comes in from the east (frame right) on "rushed"
    { t: tRush - 0.55, lat: HAL.lat + 0.0003, lon: HAL.lon, d: 0.62, tilt: 54, heading: 356, fov: 26, ease: E.inOut },
    { t: tTwo, lat: HAL.lat + 0.0003, lon: HAL.lon, d: 0.6, tilt: 54, heading: 353, fov: 26, ease: E.inOutSine },
    // s022 {two}: wide, slow drift back at first light (no text, no gag)
    { t: K.s0('s023'), lat: HAL.lat + 0.0004, lon: HAL.lon, d: 1.25, tilt: 48, heading: 6, fov: 26, ease: E.inOut },
    // after the photo (the swing happens under it): from the bench behind the grove, looking out to sea over the flooded grove, so
    // water shows behind and between the trunks (the USGS photo's 'standing in the sea')
    { t: K.s0('s024') - 0.1, lat: HAL.lat - 0.0005, lon: HAL.lon, d: 0.40, tilt: 73, heading: 195, fov: 24, ease: E.inOutSine },
    // s024: up and back, turning while it looks almost straight down, to the regional oblique of the south flank
    { t: K.s0('s024') + 0.85, lat: 19.285, lon: -155.235, d: 7, tilt: 25, heading: 270, fov: 34, ease: E.inOut },
    { t: K.s0('s024') + 1.9, lat: 19.31, lon: -155.21, d: 42, tilt: 70, heading: 352, fov: 38, ease: E.inOut },
    { t: tGo - 0.12, lat: 19.31, lon: -155.212, d: 39, tilt: 70, heading: 350, fov: 37, ease: E.inOutSine },
  ]);
  // the 6-frame jolt on {hit} and the seaward lurch (seeded, decaying)
  const shake = (T0) => {
    let y = 0, p = 0; const a = (T0 - (lead('hit', 1))) * 30;
    if (a >= 0 && a < 12) { const k = Math.exp(-a / 3.2); y += (hash(Math.floor(a), 1) - 0.5) * 2.2 * k; p += (hash(Math.floor(a), 2) - 0.5) * 1.6 * k; }
    const b = (T0 - (tLurch - 0.05)) * 30; if (b >= 0 && b < 10) { const k = Math.exp(-b / 3); p += -1.3 * k * Math.sin(b * 1.4); }
    const c = (T0 - tFore) * 30; if (c >= 0 && c < 60) { const k = Math.sin(Math.PI * Math.min(1, c / 60)) * Math.exp(-c / 40); y += (hash(Math.floor(c), 3) - 0.5) * 0.5 * k; }
    return [y, p];
  };
  const camH = (T0) => { const c = kit.terrainCamOf(orb(T0)); const [y, p] = shake(T0); c.dYaw = y;                                 // the whip-in pan is in the orbit heading (310 -> 350, decelerating)
    c.dPitch = p; c.near = Math.min(c.near, 0.01); return c; };
  // light: morning (s014) -> pre-dawn blue (s015 push) -> first light (s022-s023) -> morning again for the regional pull back (s024)
  const DAWN = { zenith: '#2f5698', horizon: '#adc0e1', haze: ['#9aaed2', 0.72], sun: '#c9d5f2', glow: ['#ffb48a', 0.22], sunI: 3.3, skyI: 1.6 };
  const FIRST = { zenith: '#3a68b0', horizon: '#e2cab8', haze: ['#cdbfc4', 0.72], sun: '#ffd2a4', glow: ['#ffb582', 0.45], sunI: 3.0, skyI: 0.95 };
  const LG0 = tRush - 2.0;                                                     // first light creeps in over 7 s (unnoticed), done before the photo
  const lightK = (T0) => {                                                     // 0 morning, 1 pre-dawn, 2 first light, 3 morning
    if (T0 < K.s0('s015')) return 0;
    if (T0 < K.s0('s016')) return E.inOut(F.clamp((T0 - K.s0('s015')) / (K.s0('s016') - K.s0('s015') - 0.3)));
    if (T0 < LG0) return 1;
    if (T0 < K.s0('s024')) return 1 + E.inOutSine(F.clamp((T0 - LG0) / 7.0));
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
    // {drop}: back to 0 over 1.5 s; 'rushed': a local surge (up in 0.6 s, peaking on the word: spot sync 75.83 s, down over 1.6 s)
    const pre = -3.5 * E.inOut(F.clamp((T0 - K.s0('s015')) / 2.5)), drop = E.inOut(F.clamp((T0 - (lead('drop', 2))) / 1.5));
    const su = T0 - (tRush - 0.68), surge = su < 0 ? 0 : su < 0.6 ? E.out(su / 0.6) : su < 2.2 ? 1 - E.inOut((su - 0.6) / 1.6) : 0;
    return pre * (1 - drop) + 3.0 * surge;
  };
  const stateH = (T0) => {
    const k = lightK(T0);
    // night: first light keeps the water a muted deep teal (no pool turquoise)
    const night = k <= 1 ? k : k < 2 ? 1 - 0.3 * (k - 1) : 0.7 * (3 - k), WN = [[0.012, 0.080, 0.115], [0.009, 0.048, 0.088], [0.007, 0.034, 0.070]];
    const WD = [[0.030, 0.26, 0.30], [0.024, 0.085, 0.150], [0.022, 0.060, 0.130]];   // by day: steel blue offshore (MOVE_WATER family), no pool teal
    return { look: lookAt(k), sun: [pick3(k, 100, 82, 84, 100), pick3(k, 24, 15, 14, 34)], waterCols: WD.map((c, i) => c.map((v, j) => v + (WN[i][j] - v) * night)), level: levelH(T0),
      set: { foamAmt: 0.6 + 0.6 * F.clamp(1 - Math.abs(T0 - (tRush + 0.6)) / 1.0), waveAmt: 0.45 + 1.8 * F.clamp(1 - Math.abs(T0 - (tFore + 0.9)) / 1.2) + 2.5 * F.clamp(1 - Math.abs(T0 - (tHit + 0.3)) / 1.4),
        glintAmt: 0.06, surfAmt: 0.7, landSat: pick3(k, 1.05, 0.8, 0.85, 1.05), landGain: pick3(k, 1.0, 1.45, 1.25, 1.0), nearAmt: 0.7, landLift: pick3(k, 0.03, 0.06, 0.045, 0.03), shadows: 1 },
      post: { exposure: pick3(k, 1.18, 1.6, 1.38, 1.15), sat: pick3(k, 1.03, 1.0, 1.0, 1.03), contrast: pick3(k, 1.08, 1.05, 1.05, 1.06) } };
  };
  // the strip between today's shore and the pre-1975 waterline (3.5 m lower) was the beach the grove stood on: sand, not dark seabed
  const SAND = [0.30, 0.27, 0.22];
  const stateHd = (T0) => { const st = stateH(T0); st.set.reefCol = SAND; st.set.reefAmt = 1; return st; };
  const gradeH = (T0) => { const d = F.clamp((T0 - (tTwo - 0.1)) / 0.6) * (1 - F.clamp((T0 - (K.s0('s024') - 0.3)) / 0.8)); return { sat: 1 - 0.2 * d }; };

  // ---- the grove, tents, stars, dust: drawn at true positions on the halape stage (lazily placed from the 10 m grid, seeded)
  let GROVE = null;
  const mll = (lon, lat, e, n) => [lon + e / (KM * 1000 * Math.cos(lat * D2R)), lat + n / (KM * 1000)];   // metres east / north -> lon, lat
  const grove = (S) => {
    if (GROVE) return GROVE;
    const r = F.rng(1975), palms = [], tents = [];
    for (let k = 0; k < 9000 && palms.length < 64; k++) {
      const lon = HAL.lon - 0.0012 + r() * 0.0024, lat = HAL.lat - 0.0011 + r() * 0.0019, h = S.heightAt(lon, lat);
      const inWater = h > -2.3 && h < 0.5, beach = h >= 0.5 && h < 3.2 && palms.filter(p => p.h >= 0.5).length < 16;
      if (!(inWater || beach)) continue;
      if (palms.some(p => Math.hypot((p.lon - lon) * 105000, (p.lat - lat) * 111000) < 8)) continue;
      if (Math.hypot((lon - HAL.lon) * 105000, (lat - HAL.lat) * 111000) > 95) continue;
      // coconut palms lean toward the open sea (south +- 60 degrees), 4-17 % of their height
      palms.push({ lon, lat, h, H: 17 + r() * 9, lean: 0.04 + 0.13 * r(), az: Math.PI + (r() - 0.5) * 2.1, seed: r() * 100, fr: 9 + Math.floor(r() * 4) });
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
  // sway (fraction of the height at the top): breeze, foreshock shiver, main-shock whip, lurch, the surge
  const sway = (T0, s) => 0.015 * Math.sin(T0 * 1.1 + s) + 0.05 * F.clamp(1 - Math.abs(T0 - (tFore + 0.9)) / 1.2) * Math.sin(T0 * 19 + s)
    + 0.12 * Math.exp(-Math.max(0, T0 - tHit) * 1.6) * (T0 > tHit - 0.05 ? Math.sin((T0 - tHit) * 24 + s) : 0) + 0.07 * Math.exp(-Math.max(0, T0 - tLurch) * 2) * (T0 > tLurch ? Math.sin((T0 - tLurch) * 16 + s) : 0)
    + 0.05 * F.clamp(1 - Math.abs(T0 - (tRush + 0.2)) / 0.9) * Math.sin(T0 * 11 + s);
  const sunVec = (view) => { const [az, el] = view.sun || [90, 15]; return [Math.sin(az * D2R) * Math.cos(el * D2R), Math.cos(az * D2R) * Math.cos(el * D2R), Math.sin(el * D2R)]; };
  // a coconut palm built in 3D (metres east / north / up around its base) and projected point by point, so it foreshortens with the
  // terrain from any camera (the look-down framings see the crowns from above); fronds shaded by the stage's own sun direction
  function drawPalm(ctx, view, p, T0, tint, level) {
    const P3 = (e, n, z) => { const [lo, la] = mll(p.lon, p.lat, e, n); return view.project(lo, la, p.h + z); };
    const b = P3(0, 0, 0); if (!b) return;
    const ex = P3(1, 0, 0), ny = P3(0, 1, 0); if (!ex || !ny) return;
    const ppm = Math.max(Math.hypot(ex[0] - b[0], ex[1] - b[1]), Math.hypot(ny[0] - b[0], ny[1] - b[1]));
    if (ppm * p.H < 6 || b[0] < -200 || b[0] > W + 200 || b[1] < -300 || b[1] > H + 300) return;
    const sw = sway(T0, p.seed), sa = 1.2;                                     // shake along an east-north-east axis
    const tr = (u) => { const off = p.H * p.lean * Math.pow(u, 1.5); return [Math.sin(p.az) * off + Math.cos(sa) * sw * p.H * u * u, Math.cos(p.az) * off + Math.sin(sa) * sw * p.H * u * u, p.H * u]; };
    const z0 = level > p.h ? level - p.h : 0;                                  // the trunk rises out of the water there
    ctx.save();
    // trunk: a tapered column (0.40 m at the foot, 0.24 m at the crown), lit side lighter
    const C = []; for (let k = 0; k <= 6; k++) { const u = z0 / p.H + (1 - z0 / p.H) * k / 6, [e, n, z] = tr(u), q = P3(e, n, z); if (q) C.push([q, u]); }
    if (C.length < 2) { ctx.restore(); return; }
    const A1 = [], A2 = [];
    C.forEach(([q, u], i) => { const q2 = C[Math.min(C.length - 1, i + 1)][0], q1 = C[Math.max(0, i - 1)][0], dx = q2[0] - q1[0], dy = q2[1] - q1[1], dl = Math.hypot(dx, dy) || 1;
      const w = Math.max(0.7, (0.40 - 0.16 * u) * ppm * 0.5); A1.push([q[0] - dy / dl * w, q[1] + dx / dl * w]); A2.push([q[0] + dy / dl * w, q[1] - dx / dl * w]); });
    ctx.fillStyle = rgba(tint.trunk, 1); ctx.beginPath(); [...A1, ...A2.reverse()].forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill();
    if (z0 > 0) {                                                               // the trunk mirrored in the water (rippled, faint)
      const RF = []; for (let k = 0; k <= 5; k++) { const u = z0 / p.H + 0.45 * k / 5, [e, n, z] = tr(u), q = P3(e + Math.sin(T0 * 3 + k + p.seed) * 0.25, n, 2 * z0 - z); if (q) RF.push(q); }
      if (RF.length > 2) { ctx.strokeStyle = rgba(mixc(tint.trunk, [30, 60, 90], 0.4), 0.32); ctx.lineWidth = Math.max(1, 0.32 * ppm); ctx.lineCap = 'round'; ctx.beginPath(); RF.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
      // a ring of foam where the trunk meets the water
      const ring = []; for (let k = 0; k <= 10; k++) { const a = k / 10 * 6.2832, q = P3(Math.cos(a) * 0.7, Math.sin(a) * 0.7, z0); if (q) ring.push(q); }
      if (ring.length > 4) { ctx.strokeStyle = rgba(tint.foam, 0.6); ctx.lineWidth = Math.max(1, ppm * 0.18); ctx.beginPath(); ring.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
    }
    // crown: pinnate fronds radiating in 3D, rising then drooping; drawn back to front
    const [cx, cy, cz] = tr(1), sv = sunVec(view), camP = view.S.cam.position, fr = [];
    for (let i = 0; i < p.fr; i++) {
      const a = (i / p.fr) * 6.2832 + p.seed + sw * 1.5, L = 4.6 + 1.2 * hash(i, p.seed), rise = 0.32 + 0.12 * hash(p.seed, i), droop = 0.8 + 0.3 * hash(i + 3, p.seed);
      const de = Math.sin(a), dn = Math.cos(a), pe = Math.cos(a), pn = -Math.sin(a);
      const pts = []; for (let k = 0; k <= 6; k++) { const sF = k / 6, rr = L * sF, zz = L * (rise * sF - droop * sF * sF), w = 0.55 * Math.sin(Math.PI * Math.min(1, sF * 1.12));
        const l = P3(cx + de * rr + pe * w, cy + dn * rr + pn * w, cz + zz), r2 = P3(cx + de * rr - pe * w, cy + dn * rr - pn * w, cz + zz); if (l && r2) pts.push([l, r2]); }
      if (pts.length < 3) continue;
      const tip = mll(p.lon, p.lat, cx + de * L, cy + dn * L), tp = view.S.xyz(tip[0], tip[1], p.h + cz), dist = tp.distanceTo(camP);
      const nrm = [de * 0.45, dn * 0.45, 1], nl = Math.hypot(...nrm), lit = F.clamp((nrm[0] * sv[0] + nrm[1] * sv[1] + nrm[2] * sv[2]) / nl);
      fr.push({ pts, dist, lit });
    }
    fr.sort((u, v) => v.dist - u.dist);
    for (const f of fr) { ctx.fillStyle = rgba(mixc(tint.frondD, tint.frondL, 0.25 + 0.75 * f.lit), 1); ctx.beginPath();
      f.pts.forEach(([l], i) => i ? ctx.lineTo(l[0], l[1]) : ctx.moveTo(l[0], l[1])); for (let i = f.pts.length - 1; i >= 0; i--) ctx.lineTo(f.pts[i][1][0], f.pts[i][1][1]); ctx.closePath(); ctx.fill(); }
    const cq = P3(cx, cy, cz); if (cq) { ctx.fillStyle = rgba(mixc(tint.trunk, [20, 20, 20], 0.3), 1); ctx.beginPath(); ctx.arc(cq[0], cq[1], Math.max(1, ppm * 0.45), 0, 7); ctx.fill(); }   // nuts and crown shank
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
      // {woke}: a lantern inside: the canvas lit warm and a halo big enough to read on a phone (core 16 px, glow 90 px at 1080p)
      const gx = (r0[0] + r1[0] + b0[0] + b1[0]) / 4, gy = (r0[1] + r1[1] + b0[1] + b1[1]) / 4, R = Math.max(px(90), Math.hypot(r1[0] - r0[0], r1[1] - r0[1]) * 4);
      quad([r0, r1, b1, b0], `rgba(255,196,118,${0.9 * glow})`); quad([r0, r1, a1, a0], `rgba(230,160,92,${0.7 * glow})`);
      const g = ctx.createRadialGradient(gx, gy, 0, gx, gy, R); g.addColorStop(0, `rgba(255,214,150,${0.92 * glow})`); g.addColorStop(0.18, `rgba(255,190,112,${0.55 * glow})`); g.addColorStop(0.5, `rgba(255,176,96,${0.16 * glow})`); g.addColorStop(1, 'rgba(255,170,90,0)');
      ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(gx, gy, R, 0, 7); ctx.fill();
    }
    ctx.restore();
  }
  const STARS = (() => { const r = F.rng(29), s = []; for (let k = 0; k < 140; k++) s.push([r(), r(), 0.4 + r() * 1.3, r() * 6]); return s; })();
  function drawStars(ctx, view, T0, a) {
    if (a <= 0.01) return; const hz = view.horizonY() * H; if (hz < px(60)) return;
    ctx.save(); for (const [x, y, s, ph] of STARS) { const yy = y * hz * 0.9; if (yy > hz - px(30) || view.ground(x * W, yy, 60)) continue; const tw = 0.65 + 0.35 * Math.sin(T0 * 2.1 + ph);   // sky only (never over the pali)
      ctx.fillStyle = `rgba(235,240,255,${a * tw * (0.35 + 0.65 * (1 - yy / hz))})`; ctx.beginPath(); ctx.arc(x * W, yy, px(s), 0, 7); ctx.fill(); }
    ctx.restore();
  }
  function drawDust(ctx, view, T0, tint) {
    const a0 = T0 - tHit; if (a0 < 0 || a0 > 3.6) return;
    // the low cliff behind the grove (where the ground crosses 16 m going inland), found once
    if (!GROVE.scarp) { GROVE.scarp = []; for (let lon = HAL.lon - 0.0060; lon <= HAL.lon + 0.0040; lon += 0.00022) { for (let lat = 19.2708; lat < 19.2760; lat += 0.00004) if (view.S.heightAt(lon, lat) > 16) { GROVE.scarp.push([lon, lat, view.S.heightAt(lon, lat)]); break; } } }
    // warm, soft puffs shaken off the scarp foot, rising and spreading (alpha 0.35-0.5 at their core, 10-40 m across)
    const env = F.clamp(a0 / 0.15) * Math.exp(-a0 * 0.7);
    GROVE.scarp.forEach(([lon0, lat0, h0], i) => { for (let k = 0; k < 5; k++) {
      if (hash(i, 31 + k) < 0.25) continue;                                        // gaps: the dust comes off in bursts
      const up = 0.00004 + 0.0004 * hash(i, 17 + k), along = (hash(i, 19 + k) - 0.5) * 0.0005, lon = lon0 + along, lat = lat0 + up, hb = view.S.heightAt(lon, lat);
      const ph = hash(i, 7 + k), rise = (2 + 22 * Math.sqrt(a0)) * (0.4 + 0.9 * ph), q = view.project(lon, lat, hb + rise); if (!q || q[0] < -300 || q[0] > W + 300) continue;
      const ppm = ppmAt(view, lon, lat, hb), R = Math.max(px(30), (9 + 28 * Math.sqrt(a0)) * ppm * (0.5 + 1.0 * hash(i, 11 + k))), al = (0.24 + 0.14 * hash(i, 23 + k)) * env;
      const x = q[0] + (hash(i, 13 + k) - 0.5) * R * 0.8 + a0 * ppm * 3 * (hash(i, 29 + k) - 0.3), y = q[1];
      const g = ctx.createRadialGradient(x, y, 0, x, y, R); g.addColorStop(0, rgba(tint.dust, al)); g.addColorStop(0.55, rgba(tint.dust, al * 0.5)); g.addColorStop(1, rgba(tint.dust, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, R, 0, 7); ctx.fill(); } });
  }
  // the scene tint for drawn things (they are drawn after the grade, so they carry the scene's light themselves)
  const tintAt = (T0) => {
    const k = lightK(T0), d = (a, b, c) => k <= 1 ? mixc(a, b, F.clamp(k)) : mixc(b, c, F.clamp(k - 1));
    return { trunk: d([70, 64, 56], [40, 44, 56], [74, 64, 56]), frondD: d([46, 74, 40], [26, 40, 46], [44, 60, 40]), frondL: d([116, 140, 70], [64, 86, 86], [132, 132, 82]),
      foam: [220, 232, 245], tent: d([200, 190, 170], [96, 108, 136], [196, 170, 150]), dust: d([186, 170, 146], [168, 158, 150], [190, 168, 140]) };
  };
  // ---- s019 {lurch}: the coastal block (the low bench between the shore and the scarp foot, ground 0-35 m over about 6 km), outlined,
  // with one short yellow arrow seaward (the true move, metres, is below a pixel at this range)
  let BLOCK = null;
  const getBlock = (S) => {
    if (BLOCK) return BLOCK;
    const bb = [-155.290, 19.258, -155.222, 19.280], g = heightGrid(S, bb, 2), m = new Uint8Array(g.nx * g.ny);
    for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) { const k = j * g.nx + i; m[k] = i > 1 && j > 1 && i < g.nx - 2 && j < g.ny - 2 && g.h[k] > 0.3 && g.h[k] < 35 ? 1 : 0; }
    const rings = contour(g, m, 0, 0.8, 2, 200).sort((a, b) => b.length - a.length).slice(0, 1);
    BLOCK = { rings }; api.log(`[ch1] coastal block: ${rings.length ? rings[0].length : 0} vertices`); return BLOCK;
  };
  const blockA = (T0) => F.clamp((T0 - (lead('lurch') - 0.1)) / 0.3) * (1 - F.clamp((T0 - (K.s0('s020') + 0.9)) / 0.3));
  function drawBlock(ctx, view, T0) {
    const a = blockA(T0); if (a <= 0) return; const B = getBlock(view.S); if (!B.rings.length) return;
    const pr = projRings(view, B.rings, (lon, lat) => Math.max(0, view.S.heightAt(lon, lat)) + 1).map(r => r.concat([r[0]]));   // closed rings
    ui.outline(ctx, pr, { alpha: a, width: 6, p: F.clamp((T0 - (lead('lurch') - 0.1)) / 0.5) });
    const p = F.clamp((T0 - lead('lurch')) / 0.3), q0 = view.project(HAL.lon + 0.004, 19.2716, 15), qs = view.project(HAL.lon + 0.004, 19.2696, 0);
    if (p > 0 && q0 && qs) { const dx = qs[0] - q0[0], dy = qs[1] - q0[1], dl = Math.hypot(dx, dy) || 1, Lp = px(230);   // seaward, 230 px
      ui.arrow(ctx, [q0, [q0[0] + dx / dl * Lp, q0[1] + dy / dl * Lp]], { p, t: T0, width: 15, alpha: a }); }
  }
  // ---- s020 scale inset: a side-on section (old ground line, the block sinking 3.5 m, the sea, a plain basketball hoop at true scale)
  function drawInset(ctx, T0) {
    const a = F.clamp((T0 - (lead('drop') - 0.45)) / (8 / 30)) * (1 - F.clamp((T0 - (K.s0('s021') - 0.05 - 8 / 30)) / (8 / 30)));
    if (a <= 0) return;
    // 41 % of the frame height, top-left (the grove sits centre-right in s020); px per metre m: the window shows -2.1 .. +7.4 m
    const pw = px(640), ph = px(440), x0 = px(96), y0 = px(96), m = ph / 9.5, sea = y0 + ph * (7.4 / 9.5);
    const drop = E.inOut(F.clamp((T0 - (lead('drop', 2))) / 1.5)), g0 = sea - 2.3 * m, g = g0 + 3.5 * m * drop;   // ground +2.3 m -> -1.2 m
    const sc = 0.94 + 0.06 * E.outExpoN(F.clamp((T0 - (lead('drop') - 0.45)) / 0.3));
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(x0 + pw / 2, y0 + ph / 2); ctx.scale(sc, sc); ctx.translate(-(x0 + pw / 2), -(y0 + ph / 2));
    ctx.fillStyle = 'rgba(0,0,0,0.3)'; F.round(ctx, x0 + px(3), y0 + px(7), pw, ph, px(10)); ctx.fill();
    F.round(ctx, x0, y0, pw, ph, px(10)); ctx.save(); ctx.clip();
    // the scene's own pre-dawn light: slate-blue sky, dark steel sea, cool basalt and sand
    const sky = ctx.createLinearGradient(0, y0, 0, y0 + ph); sky.addColorStop(0, '#26385c'); sky.addColorStop(0.75, '#6c7fa6'); sky.addColorStop(1, '#8e98b4'); ctx.fillStyle = sky; ctx.fillRect(x0, y0, pw, ph);
    ctx.fillStyle = '#244a6c'; ctx.fillRect(x0, sea, pw, ph);                                                       // the sea
    const gx1 = x0 + pw * 0.66;
    ctx.fillStyle = '#4c4a52'; ctx.beginPath(); ctx.moveTo(x0, g); ctx.lineTo(gx1, g); ctx.lineTo(gx1 + px(90), y0 + ph + 5); ctx.lineTo(x0, y0 + ph + 5); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#8a8178'; ctx.beginPath(); ctx.moveTo(x0, g); ctx.lineTo(gx1, g); ctx.lineTo(gx1 + px(14), g + px(12)); ctx.lineTo(x0, g + px(12)); ctx.closePath(); ctx.fill();
    // the hoop face-on: pole, backboard 1.8 x 1.05 m with its square, rim 10 ft (3.05 m) up as a ring, net; dark edges so it reads
    const hx = x0 + pw * 0.40, rimY = g - 3.05 * m, bw = 1.8 * m, bh = 1.05 * m, bTop = rimY - 0.85 * m;
    const dk = 'rgba(6,9,15,0.75)', e = px(4);
    ctx.fillStyle = dk; ctx.fillRect(hx - px(10) - e, bTop + bh * 0.5, px(20) + 2 * e, g - (bTop + bh * 0.5) + e);
    ctx.fillStyle = '#E8EBF0'; ctx.fillRect(hx - px(10), bTop + bh * 0.5, px(20), g - (bTop + bh * 0.5));         // pole (behind the board)
    ctx.fillStyle = dk; ctx.fillRect(hx - bw / 2 - e, bTop - e, bw + 2 * e, bh + 2 * e);
    ctx.fillStyle = '#F4F6FA'; ctx.fillRect(hx - bw / 2, bTop, bw, bh);                                           // backboard
    ctx.strokeStyle = '#3a4250'; ctx.lineWidth = px(5); ctx.strokeRect(hx - 0.3 * m, rimY - 0.45 * m, 0.6 * m, 0.45 * m);   // the shooter's square
    // net (white, under the rim) and the rim as an orange ring seen slightly from below
    ctx.strokeStyle = 'rgba(244,246,250,0.95)'; ctx.lineWidth = px(4); ctx.beginPath();
    const rr = 0.23 * m; for (let k = 0; k <= 4; k++) { const xa = hx - rr + 2 * rr * k / 4, xb = hx - rr * 0.6 + 1.2 * rr * k / 4; ctx.moveTo(xa, rimY); ctx.lineTo(xb, rimY + 0.4 * m); }
    ctx.moveTo(hx - rr * 0.8, rimY + 0.2 * m); ctx.lineTo(hx + rr * 0.8, rimY + 0.2 * m); ctx.moveTo(hx - rr * 0.6, rimY + 0.4 * m); ctx.lineTo(hx + rr * 0.6, rimY + 0.4 * m); ctx.stroke();
    ctx.strokeStyle = dk; ctx.lineWidth = px(13); ctx.beginPath(); ctx.ellipse(hx, rimY, rr, rr * 0.28, 0, 0, 7); ctx.stroke();
    ctx.strokeStyle = '#FF8A3C'; ctx.lineWidth = px(7); ctx.beginPath(); ctx.ellipse(hx, rimY, rr, rr * 0.28, 0, 0, 7); ctx.stroke();
    // once the block is below the sea, the water lies over it (and over the foot of the hoop)
    if (g > sea) { ctx.fillStyle = 'rgba(36,74,108,0.8)'; ctx.fillRect(x0, sea, gx1 + px(90) - x0, g - sea + px(12)); }
    ctx.fillStyle = 'rgba(190,210,232,0.9)'; ctx.fillRect(x0, sea - px(3), pw, px(6));                               // the sea surface
    // the old ground line stays where the ground was (white 8 px, dark under-stroke)
    ctx.fillStyle = 'rgba(6,9,15,0.65)'; ctx.fillRect(x0, g0 - px(8), pw, px(16));
    ctx.fillStyle = '#F4F6FA'; ctx.fillRect(x0, g0 - px(4), pw, px(8));
    // the drop: one yellow arrow from the old ground line down to the new ground, beside the hoop (longer than the hoop is tall)
    if (drop > 0.02) { const ax = x0 + pw * 0.14; ui.arrow(ctx, [[ax, g0 + px(6)], [ax, g]], { p: 1, t: T0, width: 15, alpha: F.clamp(drop * 4) }); }
    ctx.restore();
    ctx.strokeStyle = 'rgba(6,9,15,0.8)'; ctx.lineWidth = px(5); F.round(ctx, x0, y0, pw, ph, px(10)); ctx.stroke();
    ctx.restore();
    ui.avoid({ x: x0, y: y0, w: pw, h: ph });
  }
  // s021: the local surge, whitewater running along the shoreline from the east to the west over the drowned beach among the palms:
  // one band (a bright breaking edge and a turbulent body behind it) filled once as a polygon on a third-size canvas at full alpha
  // (soft, noise-broken edges when it is scaled up), then laid over the scene with the band's alpha: no overlapping translucent cards
  let SURGE_CV = null;
  function drawSurge(ctx, view, T0) {
    const u = (T0 - (tRush - 0.8)) / 1.5; if (u < 0 || u > 1.3) return;
    const a = F.clamp(u / 0.1) * (1 - F.clamp((u - 0.9) / 0.4)), lev = view.level;
    const front = HAL.lon + 0.0042 - 0.0080 * F.clamp(u);
    const shoreLat = (lon) => { for (let lat = HAL.lat - 0.0012; lat < HAL.lat + 0.0018; lat += 0.00003) if (view.S.heightAt(lon, lat) > lev + 0.2) return lat; return null; };
    const R0 = [], R1 = [], R2 = [];
    for (let k = 0; k <= 60; k++) { const lon = front + k * 0.00007, la = shoreLat(lon); if (la == null) continue; const f = k / 60;
      const wv = 0.00004 * Math.sin(k * 0.9 + T0 * 3) + 0.00002 * Math.sin(k * 2.3 - T0 * 5);   // a gently wavy seaward edge (no teeth)
      const q0 = view.project(lon, la + 0.00003 * (1 - f), lev + 0.6), q1 = view.project(lon, la - 0.00005 - 0.00002 * (1 - f), lev + 0.5), q2 = view.project(lon, la - 0.00015 - wv - 0.00006 * (1 - f), lev + 0.25);
      if (q0 && q1 && q2) { R0.push([q0, f]); R1.push([q1, f]); R2.push([q2, f]); } }
    if (R0.length < 3) return;
    const S3 = 3, cw = Math.ceil(W / S3), chh = Math.ceil(H / S3);
    if (!SURGE_CV) { SURGE_CV = document.createElement('canvas'); SURGE_CV.width = cw; SURGE_CV.height = chh; }
    const c = SURGE_CV.getContext('2d'); c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, cw, chh); c.setTransform(1 / S3, 0, 0, 1 / S3, 0, 0);
    // the turbulent body (q0 -> q2), fading behind the front: a horizontal gradient from the front (bright) to the tail
    const fx0 = R0[0][0][0], fx1 = R0[R0.length - 1][0][0];
    const gr = c.createLinearGradient(fx0, 0, fx1, 0); gr.addColorStop(0, 'rgba(236,243,250,0)'); gr.addColorStop(0.035, 'rgba(236,243,250,0.62)'); gr.addColorStop(0.14, 'rgba(226,236,246,0.5)'); gr.addColorStop(0.55, 'rgba(214,228,242,0.26)'); gr.addColorStop(1, 'rgba(214,228,242,0)');
    c.fillStyle = gr; c.beginPath(); R0.forEach(([q], i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); for (let i = R2.length - 1; i >= 0; i--) c.lineTo(R2[i][0][0], R2[i][0][1]); c.closePath(); c.fill();
    // the breaking edge on the shore (q0 -> q1), brighter, also as one polygon
    const g2 = c.createLinearGradient(fx0, 0, fx1, 0); g2.addColorStop(0, 'rgba(246,250,253,0)'); g2.addColorStop(0.03, 'rgba(246,250,253,0.85)'); g2.addColorStop(0.3, 'rgba(242,247,252,0.55)'); g2.addColorStop(1, 'rgba(242,247,252,0)');
    c.fillStyle = g2; c.beginPath(); R0.forEach(([q], i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); for (let i = R1.length - 1; i >= 0; i--) c.lineTo(R1[i][0][0], R1[i][0][1]); c.closePath(); c.fill();
    // noise break-up: holes punched into the body along the band (seeded by the sample index, moving with the water)
    c.globalCompositeOperation = 'destination-out';
    for (let i = 1; i < R0.length - 1; i += 1) { const [q, f] = R1[i], [q2] = R2[i], h1 = hash(i, Math.floor(T0 * 8)); if (h1 < 0.35) continue;
      const x = q[0] + (q2[0] - q[0]) * (0.3 + 0.5 * h1), y = q[1] + (q2[1] - q[1]) * (0.3 + 0.5 * h1), rr = Math.max(3, Math.hypot(q2[0] - q[0], q2[1] - q[1]) * (0.15 + 0.2 * hash(i, 5)));
      c.fillStyle = `rgba(0,0,0,${0.35 + 0.4 * f})`; c.beginPath(); c.ellipse(x, y, rr * 1.6, rr * 0.7, 0, 0, 7); c.fill(); }
    c.globalCompositeOperation = 'source-over';
    ctx.save(); ctx.globalAlpha *= a; ctx.imageSmoothingEnabled = true; ctx.drawImage(SURGE_CV, 0, 0, cw, chh, 0, 0, cw * S3, chh * S3); ctx.restore();
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
  scenes.push(blurred(shotK1, G0, G0 + 0.2, (tt) => tt < G0 + 2.5 / 30 ? 14 : 6));
  const halShot = kit.terrainShot({ id: 'ch1-halape', t0: TH1, t1: TQ + 0.5, fadeIn: 0.45, region: 'halape', cam: (lt) => camH(lt + TH1), state: (lt) => stateHd(lt + TH1), grade: (lt) => gradeH(lt + TH1),
    world(ctx, lt, tt, view) {
      const T0 = lt + TH1, G = grove(view.S), tint = tintAt(T0), k = lightK(T0), lev = view.level;
      drawStars(ctx, view, T0, k <= 1 ? F.clamp(k * 1.2 - 0.2) * 0.9 : F.clamp(2 - k) * 0.9);
      const camP = view.S.cam.position, dist = (o) => { const p = view.S.xyz(o.lon, o.lat, o.h); return -Math.hypot(p.x - camP.x, p.z - camP.z); };
      // tents: in from the night, glow on {woke}, gone under the surge
      const tentA = 1 - F.clamp((T0 - (tRush + 0.1)) / 0.5);
      if (tentA > 0) G.tents.slice().sort((a, b) => dist(a) - dist(b)).forEach((tn, i) => drawTent(ctx, view, tn, T0, tint, i === 1 ? F.clamp((T0 - (lead('woke') - 0.1)) / 0.35) * (1 - F.clamp((T0 - (tRush + 0.1)) / 0.4)) * (0.9 + 0.1 * Math.sin(T0 * 9)) : 0, tentA));
      drawSurge(ctx, view, T0);
      G.palms.slice().sort((a, b) => dist(a) - dist(b)).forEach(p => drawPalm(ctx, view, p, T0, tint, lev));
      drawDust(ctx, view, T0, tint);
      drawInset(ctx, T0);
    },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TH1;
      drawBlock(ctx, view, T0);
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
    async world() { await getFlank(); },
    ui(ctx, lt, tt, view) {
      const T0 = lt + TQ, a = flankA(T0); if (a <= 0 || !flank) return;
      // the hero fill in the exact #FF5A36 at 55 % after the grade (a stage fill under this low sun read brick red), then the outline
      ui.fill(ctx, projRings(view, flank.rings, (lon, lat) => Math.max(0, view.S.heightAt(lon, lat))), { alpha: a, fill: 0.55 });
      ui.outline(ctx, view.runs(flank.rings, 0, { every: 3 }), { alpha: a, width: 6 });
      const p = F.clamp((T0 - (lead('yards') - 0.1)) / 0.35);
      if (p > 0) { const q0 = view.project(-155.19, 19.345, 300), q1 = view.project(-155.19, 19.235, 0); if (q0 && q1) ui.arrow(ctx, [q0, q1], { p, t: T0, width: 15, alpha: a }); }
    } });
  scenes.push(blurred(ready(shotK2, getFlank), GW0, TGO, (tt) => tt > TGO - 3.5 / 30 ? 14 : 6));
  // s025 {did}: windward Oʻahu, the green Koʻolau cliffs over Kāneʻohe Bay (region pali, its film light); the whip lands on {did}
  const OAHU = { lon: -157.785, lat: 21.398, alt: 0.9, tLon: -157.818, tLat: 21.377, tH: 560, fov: 44 };   // over Kāneʻohe, the fluted pali across the frame
  const whipInL = (T0) => -55 * (1 - E.outExpoN(F.clamp((T0 - TGO) / (tDid - 0.1 - TGO))));
  const shotO = kit.terrainShot({ id: 'ch1-oahu', t0: TGO, t1: ch.t1x, region: 'pali', state: { look: 'day', sun: [75, 55], water: 'film', set: { foamAmt: 0.25 }, post: { exposure: 1.15, sat: 1.0, contrast: 1.08 } },
    cam: (lt) => { const T0 = lt + TGO, c = Object.assign({}, OAHU); const pz = Math.max(0, T0 - tDid) * 0.004; c.lon -= pz * 0.5; c.lat -= pz; c.dYaw = whipInL(T0); c.near = 0.02; c.far = 500; return c; } });
  scenes.push(blurred(shotO, TGO, TGO + 0.25, (tt) => tt < TGO + 2.5 / 30 ? 14 : 6));
  // picture events for the sound team (cues.cjs): the render's own times under mix_ep02_v1's asset names and gains (spot section 10
  // asks for a frame-exact re-sync); events with no sound in the mix ({one}, the photo, the lantern) are left out
  [[K.Te('card') - 0.03, 'postcard_drop', -10.5], [fly0, 'whoosh_soft', -14], [fly0 + 0.15, 'water_rush_short', -19], [drain0, 'drain_start', -14],
   [drain0 + 0.2, 'tick_counter', -18], [lead('ft400'), 'impact_deep', -10], [t('ft400') + 0.36, 'hit_body', -12.5], [tHop, 'paper_tap', -19.2],
   [tWalk - 0.02, 'suitcase_gravel', -16], [DR0, 'rumble_rise', -16], [tLook, 'whoosh_soft', -17], [lead('nobottom'), 'sonar_ping', -16],
   [tDrownW, 'water_rush_short', -18], [W0, 'whoosh_soft', -13], [tFore, 'rumble_quake', -14], [lead('hit', 1), 'quake_main', -7.6], [lead('hit', 1), 'quake_debris', -12],
   [lead('lurch'), 'tension_groan', -12], [lead('drop', 2), 'ground_drop', -12], [lead('drop', 2) + 1.0, 'water_rush_short', -15], [tRush, 'sea_rush_in', -12],
   [GW0, 'whoosh_big', -14]].forEach(([tc, n, g]) => api.cue(tc, n, g));
  api.log(`[ch1] shots: demo 0-${TA.toFixed(2)}, ice -${TC.toFixed(2)}, ride -${TW.toFixed(2)}, bigisland ${G0.toFixed(2)}-${(TH1 + 0.45).toFixed(2)}, halape -${(TQ + 0.5).toFixed(2)}, flank -${TGO.toFixed(2)}, oahu -${ch.t1x.toFixed(2)}`);
}
