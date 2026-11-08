// Chapter 1 "Only the Top" (s001-s025). Built so far (toolkit demos, end to end): s001-s006.
//   DEMO 1  s001-s003  frame 1 = the NO OCEAN thumbnail (final_ep02_1.jpg) in motion: drained Big Island, thin white line on today's
//                      coast, NO OCEAN block on frame 0 (accent bar wipes on over frames 2-10), tilt down at {most}, coast pulse at
//                      {under}, the dry cap outlined in hero orange at {top} ("only the top"; postcard device when a PD photo exists).
//   DEMO 2  s004-s006  1.6 s flight NW with the sea refilling to 0 m, names on their words with coast rim pulses, SEA LEVEL gauge,
//                      live drain to -400 ft with the counter landing on {ft400}, ONE ISLAND (final_ep02_2.jpg composition):
//                      fused island in hero orange (flood-fill on the production grid), Kaho'olawe dimmed and unlabelled.
// TODO (chapter builder): s007-s025 (Ice Age pass, paper tourist, look-down dive, Penguin Bank, refill, Halape 1975, palm grove).
import { flight, mixState, PLACES, E, PAL, F } from './shared.js';

const FT = 3.28084;
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px;
  const t = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f);
  // ---- beat times (all from Rodney's word timings)
  const tDr = t('drained'), tMost = t('most'), tUnder = t('under'), tCard = t('card'), tTop = t('top');
  const tMaui = t('maui'), tMolo = t('molo'), tLanai = t('lanai'), t400 = t('fourhundred'), tFt = t('ft400'), tOne = t('one');
  const fly0 = K.s1('s003') + 0.03, fly1 = fly0 + 1.6;                         // the flight starts as s003 ends (1.6 s, eased): Maui Nui is in frame by {maui}
  const drain0 = fly1 + 0.95, drain1 = lead('ft400');                          // 0 -> -400 ft, lands on {ft400}
  const L400 = -400 / FT;                                                      // -121.92 m: the counter lands exactly on 400
  const END = K.s0('s007') + 1.2;                                              // demo ends inside s007 (chapter builder continues)
  // optional postcard photo (public-domain photo of a Big Island coast, s003); the beat runs without it
  const PC = '/ep/ep02/img/postcard_bigisland.jpg';
  let postcard = null;
  try { const r = await fetch(PC, { method: 'HEAD' }); if (r.ok) { await api.loadImages([PC]); postcard = kit.makePostcard(api.img(PC), 'HAWAIʻI'); } } catch (e) { /* no photo yet */ }
  // ---- islands from the production grid (sill.py rule: 4-connected land above the level), computed once, lazily
  const BI = { bbox: [-156.15, 18.85, -154.75, 20.35], step: 2 };
  const MN = { bbox: [-157.85, 20.4, -155.9, 21.35], step: 2 };
  const isl = {};
  const getIsl = async () => {
    if (isl.cap) return isl;
    isl.cap = await kit.island(Object.assign({ level: 0, seeds: [PLACES['mauna-loa']] }, BI));
    isl.maui = await kit.island(Object.assign({ level: 0, seeds: [PLACES.maui] }, MN));
    isl.molo = await kit.island(Object.assign({ level: 0, seeds: [PLACES.molokai] }, MN));
    isl.lanai = await kit.island(Object.assign({ level: 0, seeds: [PLACES.lanai] }, MN));
    isl.one = await kit.island(Object.assign({ level: L400, seeds: [PLACES.maui, PLACES.molokai, PLACES.lanai] }, MN));
    isl.kaho = await kit.island(Object.assign({ level: L400, seeds: [PLACES.kahoolawe] }, MN));
    if (isl.one.mask[0] === undefined) throw new Error('island grid');
    // honesty gate: at -400 ft Kaho'olawe must stay separate from the fused island (data saddle -159 m)
    const g = isl.one.g; let touch = 0; for (let k = 0; k < g.nx * g.ny; k++) if (isl.one.mask[k] && isl.kaho.mask[k]) touch++;
    if (touch) api.log(`[ch1] WARNING Kaho'olawe joins the fused island at ${L400.toFixed(0)} m on this grid`);
    isl.capTex = kit.maskTexture(isl.cap.g, { r: isl.cap.mask });
    isl.mnTex = kit.maskTexture(isl.one.g, { r: isl.one.mask, g: isl.kaho.mask });
    api.log(`[ch1] fused island at ${L400.toFixed(1)} m: ${Math.round(isl.one.areaKm2)} km2, ${isl.one.rings.length} rings; Kaho'olawe separate: ${!touch}`);
    return isl;
  };

  // ---- the one continuous camera: thumbnail framing -> tilt down -> flight NW -> ONE ISLAND framing (live push + drift)
  const camFly = flight('noocean', 'mauinui_one', fly0, fly1, { ease: E.inOut, via: { lon: -156.55, lat: 19.75, alt: 34 }, tvia: { tLon: -156.35, tLat: 20.55, tH: -500 } });
  // live hold moves (nothing static over 2 s): push and heading drift accumulate on the thumbnail hold, fade out during the flight
  // (so the flight lands exactly on the ONE ISLAND framing), then start again from the landing
  const zoom = (c, k) => { c.fov = 2 * Math.atan(Math.tan(c.fov * Math.PI / 360) / (1 + k)) * 180 / Math.PI; };
  const cam = (lt) => {
    const c = camFly(lt);
    const pre = 1 - E.inOut(F.clamp((lt - fly0) / (fly1 - fly0))), post = Math.max(0, lt - fly1);
    zoom(c, 0.04 * Math.min(lt, fly0) / 10 * pre + 0.03 * post / 10);                     // 4 % per 10 s on the hold, 3 % after landing
    c.dYaw = -(0.6 * Math.min(lt, fly0) * pre + 0.4 * post);                                // heading drift (deg) to the right
    // s002: 2.5 s eased tilt down along the south flank at {most} (the first "look down"); eases back out during the flight
    c.dPitch = -5 * E.inOut(F.clamp((lt - (tMost - 0.1)) / 2.5)) * (1 - E.inOut(F.clamp((lt - fly0) / 1.2)));
    return c;
  };
  // ---- water level: drained (-9,000 m) -> refills during the flight -> live drain to -400 ft -> hold
  const level = (lt) => {
    if (lt < fly0) return -9000;
    if (lt < fly1) return -9000 + 9000 * (1 - Math.pow(1 - F.clamp((lt - fly0) / (fly1 - fly0)), 2.2));   // ease-out: the sea is visibly rising mid-flight
    return L400 * E.inOutSine(F.clamp((lt - drain0) / (drain1 - drain0)));
  };
  // ---- stage state: the NO OCEAN plate look, blending into the Maui Nui day look during the flight
  const state = (lt) => {
    const p = E.inOut(F.clamp((lt - fly0) / (fly1 - fly0 - 0.6)));
    const st = mixState('noocean', 'mauinui', p);
    st.mlookAmt = 1 - E.inOut(F.clamp((lt - fly0) / 0.9));                    // the thumbnail grade is gone before water shows
    // s002 {under}: the white coast line brightens over 6 frames and back
    const pulse = F.clamp(1 - Math.abs(lt - (tUnder - 0.03)) / 0.2);
    st.set.lineCol = st.set.lineCol.map(v => v * (1 + 0.9 * pulse)); st.set.lineW = st.set.lineW * (1 + 0.8 * pulse);
    st.set.oldLine = lt < fly0 ? 1 : 1 - F.clamp((lt - fly0) / 0.8);          // the old-coast line goes when the sea comes back
    return st;
  };
  // hero masks: the dry cap at {top} (Big Island), then the fused island at {one} with Kaho'olawe dimmed from the landing on
  const mask = (lt) => {
    if (!isl.cap) return null;
    if (lt < fly0 + 0.4) { const a = F.clamp((lt - (lead('top') - 0.1)) / 0.2) * (1 - F.clamp((lt - (tTop + 0.85)) / 0.2)); return a > 0 ? { tex: isl.capTex, bb: isl.cap.g.bb, hero: 0.42 * a } : null; }   // lighter: the cap grade boosts it
    const dim = F.clamp((lt - fly1) / 0.5), hero = 0.58 * F.clamp((lt - lead('one')) / 0.2);
    return { tex: isl.mnTex, bb: isl.one.g.bb, hero, dim: 0.75 * dim };
  };

  scenes.push(kit.terrainShot({
    id: 'ch1-demo', t0: 0, t1: END, region: 'bigisland', cam, level, state, mask,
    async world(ctx, lt, tt, view) {
      await getIsl();
      // s003 postcard (only with a real public-domain photo): drops onto the dry cap at {card}, lifts its hinge at {top}, flutters off
      if (postcard && lt > tCard - 0.6 && lt < fly0 + 0.6) {
        const pd = F.clamp((lt - (tCard - 0.5)) / 0.47), lift = 0.1 * F.clamp((lt - lead('top')) / 0.25), off = F.clamp((lt - (fly0 - 0.2)) / 0.8);
        kit.drawPostcard(ctx, view, postcard, { lon: -155.55 + off * 0.6, lat: 19.6, wKm: 62, rot: 4, hm: 2600 + off * 9000, p: pd, lift: lift + off * 0.8, alpha: 1 - off });
      }
    },
    ui(ctx, lt, tt, view) {
      // DEMO 1: NO OCEAN block on frame 0 (thumbnail text, type-system plate), accent bar wipes on over frames 2-10, out 0.6 s after {drained}
      const outA = F.clamp((lt - (tDr + 0.6)) / (8 / 30));
      if (outA < 1 && !api.Q.nolabel) ui.block(ctx, [{ text: 'NO OCEAN', role: 'title', cap: 150 }], W - px(96), px(96), { anchor: 'right', platePre: true, barP: F.clamp((lt * 30 - 2) / 8), out: outA, bar: PAL.hero });
      // s003 {top}: crisp white outline of the dry cap (the fill is in the terrain, 55 % hero orange)
      const capA = F.clamp((lt - (lead('top') - 0.1)) / 0.2) * (1 - F.clamp((lt - (tTop + 0.85)) / 0.2));
      if (capA > 0 && isl.cap) ui.outline(ctx, view.runs(isl.cap.rings, 0, { every: 2 }), { alpha: capA, p: F.clamp((lt - (lead('top') - 0.1)) / 0.35) });
      // outlines first, text blocks and the gauge on top (text never sits under a line)
      const one = F.clamp((lt - (lead('one') - 0.1)) / (6 / 30));
      const nameTimes = [lead('maui'), lead('molo'), lead('lanai')];
      [['maui', isl.maui], ['molo', isl.molo], ['lanai', isl.lanai]].forEach(([m, I], i) => {
        const a = F.clamp((lt - nameTimes[i]) / 0.1) * (1 - F.clamp((lt - nameTimes[i] - 0.5) / 0.15));
        if (a > 0 && I) ui.outline(ctx, view.runs(I.rings, Math.max(view.level, 0) + 5, { every: 2 }), { alpha: a, width: 6 });
      });
      const oa = F.clamp((lt - lead('one')) / 0.25);
      if (oa > 0 && isl.one) ui.outline(ctx, view.runs(isl.one.rings, L400 + 3, { every: 2 }), { alpha: oa, p: F.clamp((lt - lead('one')) / 0.45), width: 6 });
      // DEMO 2: names on their words (one block), each island's coast pulses white for 0.6 s on its word
      if (lt > nameTimes[0] - 0.05 && one < 1)
        ui.block(ctx, [{ words: ['MAUI', 'MOLOKAʻI', 'LĀNAʻI'], role: 'label', cap: 72 }], W - px(96), px(96),
          { anchor: 'right', textAlign: 'left', p: F.clamp((lt - nameTimes[0] + 0.05) / 0.35), wordTimes: nameTimes, lt, out: one, bar: PAL.hero });
      // s006 {one}: ONE ISLAND headline in the same place; the fused island's outline (white) over its hero-orange fill
      if (one > 0) ui.block(ctx, [{ words: [{ w: 'ONE' }, { w: 'ISLAND', c: PAL.hero }], role: 'headline', cap: 108 }], W - px(96), px(96), { anchor: 'right', p: F.clamp(one * 1.2), bar: PAL.hero });
      // the SEA LEVEL gauge slides in during the flight; hero mode = the -400 FT counter rolling with the real level, landing on {ft400}
      const gp = F.clamp((lt - (fly0 + 0.5)) / 0.6);
      const hp = F.clamp((lt - lead('fourhundred', 6)) / 0.25) * (1 - F.clamp((lt - (lead('one') - 0.3)) / 0.3));
      ui.gauge(ctx, { p: gp, level: view.level, hero: { v: Math.min(0, view.level) * FT, to: -400, p: hp, unit: 'FT' } });
    },
  }));
}
