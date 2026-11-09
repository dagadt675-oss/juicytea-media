// Chapter 1 "Only the Top" (s001-s025). Built so far (toolkit demos, end to end): s001-s006. TODO (chapter builder): s007-s025.
//   DEMO 1  s001-s003  frame 1 = the NO OCEAN thumbnail (final_ep02_1.jpg) in motion: drained Big Island, thin white line on today's
//                      coast, NO OCEAN in dark ink straight on the sky (the thumbnail's own treatment: Barlow Condensed 800, soft white glow) on frame 0, out 0.6 s after
//                      {drained}; tilt down at {most} (the seabed brightens as it fills the frame), coast pulse at {under}, the postcard
//                      (USGS public-domain photo of Pohoiki, img/postcard_bigisland.jpg) lands on the dry cap at {card}, the cap takes the
//                      hero fill and outline at {top} (the cap grade steps aside inside the fill, so it reads #FF5A36).
//   DEMO 2  s004-s006  one continuous camera: 1.6 s flight NW while the sea refills; region 'mauinui' (78 m) is the finest layer of
//                      the same stage, so the landing, the drain and every outline come from the 78 m grid; names revealed on their
//                      words in a stacked block (top-right) with each island's 0 m outline staying on from its word; the SEA LEVEL gauge
//                      (top-left, value in the plate, range 150 m) rolls to 400 FT on {ft400} and fades out before {one}; at {one} the
//                      three outlines merge into the -400 ft contour (marching squares on the 78 m grid, 2 Chaikin passes, the level the
//                      water uses), the new land bridges take a 38 % hero fill, ONE ISLAND in the same dark ink top-left (final_ep02_2.jpg).
import { flight, mixState, PLACES, E, PAL, F, MLOOKS } from './shared.js';

const FT = 3.28084;
// one stage for the whole demo: Maui Nui (78 m) inside the legacy Big Island bake (frame 1 = the thumbnail plate), legacy origin and mesh
export const CH1_STAGE = { origin: { lon: -155.6, lat: 19.6 }, midGrid: [1500, 1500] };
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, px = ui.px;
  const t = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f);
  // ---- beat times (all from Rodney's word timings)
  const tDr = t('drained'), tMost = t('most'), tUnder = t('under'), tCard = t('card'), tTop = t('top');
  const fly0 = K.s1('s003') + 0.03, fly1 = fly0 + 1.6;                         // the flight starts as s003 ends (1.6 s, eased)
  const drain0 = fly1 + 0.95, drain1 = lead('ft400');                          // 0 -> -400 ft, lands on {ft400}
  const L400 = -400 / FT;                                                      // -121.92 m: the gauge lands exactly on 400
  const tOne = lead('one');                                                    // ONE ISLAND lands 3 frames before the word
  const END = K.s0('s007') + 1.2;                                              // demo ends inside s007 (chapter builder continues)
  const REG = 'mauinui', STAGE = CH1_STAGE;
  // s003 postcard: a real public-domain photo (USGS, Pohoiki black sand beach; licence line in engine/ASSETS.md)
  const PC = '/ep/ep02/img/postcard_bigisland.jpg';
  let postcard = null;
  try { const r = await fetch(PC, { method: 'HEAD' }); if (r.ok) { await api.loadImages([PC]); postcard = kit.makePostcard(api.img(PC), 'HAWAIʻI'); } } catch (e) { /* fallback below */ }
  // ---- islands on the production grids (sill.py rule: 4-connected land above the level), computed once, lazily
  const BI = { bbox: [-156.15, 18.85, -154.75, 20.35], step: 1, region: REG, stage: STAGE };          // bigisland layer (115 m)
  const MN = { bbox: [-157.75, 20.4, -155.9, 21.35], step: 1, region: REG, stage: STAGE };            // the whole mauinui layer (78 m)
  const isl = {};
  const getIsl = async () => {
    if (isl.cap) return isl;
    isl.cap = await kit.island(Object.assign({ level: 0, seeds: [PLACES['mauna-loa']] }, BI));
    isl.maui = await kit.island(Object.assign({ level: 0, seeds: [PLACES.maui, PLACES['west-maui']] }, MN));
    isl.molo = await kit.island(Object.assign({ level: 0, seeds: [PLACES.molokai] }, MN));
    isl.lanai = await kit.island(Object.assign({ level: 0, seeds: [PLACES.lanai] }, MN));
    isl.one = await kit.island(Object.assign({ level: L400, seeds: [PLACES.maui, PLACES.molokai, PLACES.lanai] }, MN));
    isl.kaho = await kit.island(Object.assign({ level: L400, seeds: [PLACES.kahoolawe] }, MN));
    // honesty gate: at -400 ft Kaho'olawe must stay separate from the fused island (saddle -159 m on this grid)
    const g = isl.one.g; let touch = 0; for (let k = 0; k < g.nx * g.ny; k++) if (isl.one.mask[k] && isl.kaho.mask[k]) touch++;
    if (touch) api.log(`[ch1] WARNING Kaho'olawe joins the fused island at ${L400.toFixed(0)} m on this grid`);
    // hero fill only on the new land bridges (land at -400 ft within 11 km of two of today's islands): the islands keep their colours
    isl.bridge = kit.bridges(isl.one, [isl.maui, isl.molo, isl.lanai], 11);
    isl.capTex = kit.maskTexture(isl.cap.g, { r: isl.cap.mask });
    isl.mnTex = kit.maskTexture(isl.one.g, { r: isl.bridge, g: isl.kaho.mask });
    if (api.Q.dbgIsl) for (const [k, I] of Object.entries({ one: isl.one, maui: isl.maui })) api.log(`[dbg isl] ${k} ` + I.rings.map(r => `${r.length}pts lon ${Math.min(...r.map(p => p[0])).toFixed(2)}..${Math.max(...r.map(p => p[0])).toFixed(2)} lat ${Math.min(...r.map(p => p[1])).toFixed(2)}..${Math.max(...r.map(p => p[1])).toFixed(2)}`).join(' | '));
    let nb = 0; for (const v of isl.bridge) if (v > 127) nb++;
    api.log(`[ch1] fused island at ${L400.toFixed(1)} m: ${Math.round(isl.one.areaKm2)} km2, ${isl.one.rings.length} rings; bridge cells ${nb}; Kaho'olawe separate: ${!touch}`);
    return isl;
  };

  // ---- the one continuous camera: thumbnail framing -> tilt down -> flight NW -> ONE ISLAND framing (live push + drift)
  const camFly = flight('noocean', 'mauinui_one', fly0, fly1, { ease: E.inOut, via: { lon: -156.55, lat: 19.75, alt: 34 }, tvia: { tLon: -156.35, tLat: 20.55, tH: -500 } });
  // hold moves (nothing static over 2 s) accumulate on the thumbnail hold, fade out during the flight (so it lands exactly on the
  // ONE ISLAND framing), then start again from the landing
  const zoom = (c, k) => { c.fov = 2 * Math.atan(Math.tan(c.fov * Math.PI / 360) / (1 + k)) * 180 / Math.PI; };
  const tilt = (lt) => E.inOut(F.clamp((lt - (tMost - 0.1)) / 2.5)) * (1 - E.inOut(F.clamp((lt - fly0) / 1.2)));
  const cam = (lt) => {
    const c = camFly(lt);
    const pre = 1 - E.inOut(F.clamp((lt - fly0) / (fly1 - fly0))), post = Math.max(0, lt - fly1);
    zoom(c, 0.04 * Math.min(lt, fly0) / 10 * pre + 0.03 * post / 10);                     // 4 % per 10 s on the hold, 3 % after landing
    c.dYaw = -(0.6 * Math.min(lt, fly0) * pre + 0.4 * post);                                // heading drift (deg) to the right
    c.dPitch = -5 * tilt(lt);                                                                // s002: 2.5 s eased tilt down at {most}
    return c;
  };
  // ---- water level: drained (-9,000 m) -> refills during the flight -> live drain to -400 ft -> hold
  const level = (lt) => {
    if (lt < fly0) return -9000;
    if (lt < fly1) return -9000 * Math.pow(1 - F.clamp((lt - fly0) / (fly1 - fly0)), 5);   // the sea rises mid-flight and covers Maui Nui's shelf before it fills the frame (no dry basin)
    return L400 * E.inOutSine(F.clamp((lt - drain0) / (drain1 - drain0)));
  };
  // ---- stage state: the NO OCEAN plate look, blending into the Maui Nui day look during the flight
  const capFill = (lt) => F.clamp((lt - (lead('top') - 0.1)) / 0.2) * (1 - F.clamp((lt - (tTop + 0.85)) / 0.2));
  const state = (lt) => {
    const p = E.inOut(F.clamp((lt - fly0) / (fly1 - fly0 - 0.6)));
    const st = mixState('noocean', 'mauinui', p);
    st.mlookAmt = 1 - E.inOut(F.clamp((lt - fly0) / 0.9));                    // the thumbnail grade is gone before water shows
    // the look-down (s002-s003): as the tilt fills the frame with seabed, lift its mid-tones and bring in the near-field detail
    // (frame 0 stays the thumbnail plate; the tilt frames hold luma 85+ instead of 76-82)
    const k = tilt(lt) * (lt < fly0 ? 1 : 0);
    if (k > 0) {
      st.set.sedCol = st.set.sedCol.map((v, i) => v * (1 + 0.85 * k) + [0.006, 0.004, 0][i] * k); st.set.basaltCol = st.set.basaltCol.map(v => v * (1 + 0.7 * k));
      st.set.nearAmt = Math.max(st.set.nearAmt || 0, k);
      st.mlook = Object.assign({}, MLOOKS.noocean, { flExp: 0.95 + 0.3 * k, flSat: 0.65 + 0.1 * k, flBurn: [0.59, 1.0, 0.008 * (1 - k)] });
    }
    // s002 {under}: the white coast line brightens over 6 frames and back
    const pulse = F.clamp(1 - Math.abs(lt - (tUnder - 0.03)) / 0.2);
    st.set.lineCol = st.set.lineCol.map(v => v * (1 + 0.9 * pulse)); st.set.lineW = st.set.lineW * (1 + 0.8 * pulse);
    st.set.oldLine = lt < fly0 ? 1 : 1 - F.clamp((lt - fly0) / 0.8);          // the old-coast line goes when the sea comes back
    return st;
  };
  // hero masks: the dry cap at {top} (Big Island; pass = the cap grade steps aside inside the fill), then from the landing on the
  // Maui Nui mask: Kaho'olawe dimmed (G) and, from {one}, the land bridges at 38 % (R)
  const mask = (lt) => {
    if (!isl.cap) return null;
    if (lt < fly0 + 0.4) { const a = capFill(lt); return a > 0 ? { tex: isl.capTex, bb: isl.cap.g.bb, hero: 0.55 * a, pass: a } : null; }
    const dim = F.clamp((lt - fly1) / 0.5), hero = 0.38 * E.inOut(F.clamp((lt - tOne) / 0.35));
    return { tex: isl.mnTex, bb: isl.one.g.bb, hero, dim: 0.75 * dim };
  };

  scenes.push(kit.terrainShot({
    id: 'ch1-demo', t0: 0, t1: END, region: REG, stage: STAGE, cam, level, state, mask,
    async world(ctx, lt, tt, view) {
      await getIsl();
      // s003 postcard: drops onto the dry cap at {card}, lifts its hinge at {top}, flutters off as the flight starts
      if (postcard && lt > tCard - 0.6 && lt < fly0 + 0.6) {
        const pd = F.clamp((lt - (tCard - 0.5)) / 0.47), lift = 0.1 * F.clamp((lt - lead('top')) / 0.25), off = F.clamp((lt - (fly0 - 0.2)) / 0.8);
        kit.drawPostcard(ctx, view, postcard, { lon: -155.5 + off * 0.6, lat: 19.62, wKm: 72, rot: 4, hm: 2600 + off * 9000, p: pd, lift: lift + off * 0.8, alpha: 1 - off });
      }
    },
    ui(ctx, lt, tt, view) {
      // outlines and lines first, then the text block, then labels (PLAYBOOK_craft 9)
      // s003 {top}: crisp white outline of the dry cap (the 55 % fill is in the terrain)
      const capA = capFill(lt);
      if (capA > 0 && isl.cap) ui.outline(ctx, view.runs(isl.cap.rings, 0, { every: 2 }), { alpha: capA, p: F.clamp((lt - (lead('top') - 0.1)) / 0.35) });
      // fallback event on {card} when no photo is present: the HAWAIʻI map label on the summit cap
      if (!postcard && lt > tCard - 0.1 && lt < fly0) { const q = view.project(...PLACES['mauna-loa']); if (q) ui.label(ctx, 'HAWAIʻI', q[0], q[1], { t: tt, p: F.clamp((lt - (lead('card') - 0.1)) / 0.3) }); }
      // s004-s006: each island's 0 m outline draws on at its word and stays through {one}; at {one} they give way to the fused contour
      const merge = F.clamp((lt - tOne) / (6 / 30));
      const names = [['maui', isl.maui], ['molo', isl.molo], ['lanai', isl.lanai]];
      names.forEach(([m, I]) => {
        const a = F.clamp((lt - lead(m)) / 0.12) * (1 - merge);
        if (a > 0 && I) ui.outline(ctx, view.runs(I.rings, 0, { every: 2 }), { alpha: a, width: 6, p: F.clamp((lt - lead(m)) / 0.5) });
      });
      if (merge > 0 && isl.one) ui.outline(ctx, view.runs(isl.one.rings, L400, { every: 2 }), { alpha: merge, width: 6, p: F.clamp((lt - tOne) / 0.5) });
      // DEMO 1: NO OCEAN on frame 0 in the thumbnail's own treatment (dark ink on the sky, no plate), out 0.6 s after {drained}
      const outA = F.clamp((lt - (tDr + 0.6)) / (8 / 30));
      if (outA < 1 && !api.Q.nolabel) ui.block(ctx, [{ text: 'NO OCEAN', role: 'title', fam: 'label', cap: 162 }], W - px(96), px(96), { anchor: 'right', plate: false, color: PAL.ink, glow: true, platePre: true, out: outA });
      // DEMO 2: names revealed whole on their words in one stacked block (top-right, over the sky); the plate grows with each name
      const nameTimes = [lead('maui'), lead('molo'), lead('lanai')];
      const nOut = F.clamp((lt - (tOne - 0.2)) / 0.2);
      if (lt > nameTimes[0] - 0.05 && nOut < 1)
        ui.block(ctx, [{ words: ['MAUI'], role: 'label', cap: 68 }, { words: ['MOLOKAʻI'], role: 'label', cap: 68 }, { words: ['LĀNAʻI'], role: 'label', cap: 68 }], W - px(96), px(96),
          { anchor: 'right', textAlign: 'left', p: 1, wordTimes: nameTimes, lt, grow: true, out: nOut, bar: PAL.hero, gap: 30 });
      // s006 {one}: ONE ISLAND in the thumbnail's slot and treatment (top-left, dark Anton ink on the sky, no coloured word)
      const oneP = F.clamp((lt - tOne) / 0.3);
      if (oneP > 0) ui.block(ctx, [{ text: 'ONE ISLAND', role: 'headline', fam: 'label', cap: 130 }], px(96), px(96), { anchor: 'left', plate: false, color: PAL.ink, glow: true, p: oneP });
      // the SEA LEVEL gauge (top-left): in as the sea reaches today's level at the end of the flight, rolls with the live level to
      // 400 FT on {ft400} (yellow rim on the hero number), out before {one} (no level changes from s006 to s009)
      const gp = F.clamp((lt - (fly1 - 0.05)) / 0.6), gOut = F.clamp((lt - (tOne - 0.4)) / 0.3);
      const pulse = F.clamp((lt - lead('ft400', 4)) / 0.15) * (1 - F.clamp((lt - (lead('ft400') + 1.0)) / 0.4));
      ui.gauge(ctx, { p: gp, out: gOut, level: Math.max(view.level, -150), range: 150, to: 492, unit: 'FT', pulse });
    },
  }));
  api.cue(lead('ft400'), 'impact_short', -12); api.cue(tOne, 'impact_deep', -9); api.cue(drain0, 'riser_tension', -14);
}
