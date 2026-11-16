// THE PAYOFF (s168-s172, hero number #7): Mauna Loa about 56,000 ft from its true base, Everest on the same base line.
// A terrain cut-away on the drained Big Island (cutawayShot, lab/hawaii/section.js), VE 1.0, the shared sky and grade:
//   - an east-west plane through Mauna Loa's summit; the half toward the camera (south) is removed, the drained terrain continues
//     beyond the cut. (The script asks for a north-south slice; along the meridian the data shows no trench at either rim, while the
//     east-west section meets the Hawaiian Deep about 125 km east of the summit, so the trench at the rim of the sag is real.)
//   - the section: layered basalt, darker below the old sea floor; the crust and Moho sag under the load (schematic flexure, 7.97 km
//     under the summit so the dented base is exactly 17,170 m below the DEM summit: about 56,000 ft, USGS); the old sea floor line
//     across the dent; the trench water strip at the rim.
//   - the yellow bar runs beside the summit column from the dented base to the summit and lands with the counter on {tall56};
//     Everest's slab (its real profile, summit 8,849 m) rises out of the same base line on {ev3}; at {underwater} the old sea-level
//     line glows and the old ocean shows as a translucent slab between the old sea floor and sea level, outside the rock only.
// Used by ch6 (buildPayoff(api, kit, scenes, {t0, t1})) and by the stand-alone test page payoff_test.html.
import { PAL, E, F } from './shared.js';

export const ML = { lon: -155.6054, lat: 19.4756, summit: 4204, total: 17170 };      // DEM summit (USGS survey 4,169 m), column (USGS)
// the plane and the section state ch6 shares for s162-s172 (the cut opens at {slice}, the sag deepens at {bent})
export const CUT_PLANE = { lon: ML.lon, lat: ML.lat, az: 90, side: 1, u0: -210, u1: 185, du: 0.25, bottomKm: 36, loadU: 0, waterTopMax: 0 };
export const SECTION = { sagM: ML.total - ML.summit - 5000, alphaKm: 90, oldFloor: -5000, crustM: 6500, trenchTop: -5470 };
export const EVEREST = { u: 21, width: 16, front: 0.15, th: 0.6 };

export function buildPayoff(api, kit, scenes, o = {}) {
  const { K, ui } = kit, W = api.W, px = ui.px;
  const T0 = o.t0 ?? K.s0('s168') - 1.0, T1 = o.t1 ?? K.s1('s172') + 2.2;
  const L = (t) => t - T0;                                        // film time -> shot-local time
  const tLook = K.T('look2'), tBase = K.T('basedent'), t169 = K.s0('s169'), tKick = K.word('s169', 'base').start, t56 = K.lead('tall56');
  const tEv0 = K.s0('s170'), tEv = K.lead('ev3'), tUnder = K.lead('underwater'), tSee = K.T('see');
  const BASE = ML.summit - ML.total;                              // -12,966 m: the dented true base under the summit
  const uBar = -4.0;                                              // the bar runs just west of the summit column, on the face (the label goes above)
  // camera keys in section coordinates: eye u (km east of the summit), d (km toward the camera, south), alt (km); target tu, te (m)
  const MAIN = { u: 8, d: 62, alt: 11, tu: 8, te: -2000, fov: 25.5 };
  const cam = [
    { t: 0, u: -14, d: 40, alt: 7.5, tu: 14, te: -1200, fov: 26 },                                         // summit, flank, the old floor line
    { t: L(tLook - 0.1), u: -13, d: 41, alt: 7.2, tu: 13, te: -1500, fov: 26 },
    { t: L(tBase - 0.1), u: 0, d: 64, alt: -6, tu: 2, te: -10500, fov: 28, ease: E.inOut },                 // tips down through the cut to the dented base
    { t: L(t169 + 0.2), u: 0.4, d: 64, alt: -6.1, tu: 2.4, te: -10400, fov: 28 },
    { t: L(t56 + 0.1), ...MAIN, ease: E.inOut },                                                            // pulls back while the bar climbs
    { t: L(tSee - 0.4), ...MAIN, u: 9, tu: 9, d: 63.5, ease: E.inOutSine },                                 // slow drift: Everest rises in frame
    { t: L(tSee + 1.6), u: 10, d: 76, alt: 13, tu: 10, te: -1800, fov: 25.5, ease: E.inOut },               // eases back: the whole cut-away
    { t: L(T1), u: 10.4, d: 78, alt: 13.3, tu: 10.4, te: -1800, fov: 25.5 },
  ];
  const bar = (t) => E.out(F.clamp((t - (t169 + 0.15)) / (t56 - t169 - 0.15)));      // 0..1, lands on {tall56}
  const ev = (t) => E.out(F.clamp((t - tEv0) / (tEv - tEv0)));
  const under = (t) => E.inOut(F.clamp((t - (tUnder - 0.15)) / 0.9));
  scenes.push(kit.cutawayShot({
    id: 'payoff-cut', t0: T0, t1: T1, region: 'bigisland', vex: 1, preset: 'drained',
    state: { sun: [200, 24], look: 'day' },
    cut: { plane: CUT_PLANE, everest: EVEREST, cam,
      state: (lt) => { const t = lt + T0; return Object.assign({}, SECTION, { sag: 1, floorLine: 1, trenchA: 0.85, edgeA: 1,
        waterTop: 0, waterA: 0.55 * under(t), waterBot: SECTION.oldFloor, everest: { rise: ev(t), base: BASE } }); } },
    level: -5470,                                                 // the trench strip: the last water in the Hawaiian Deep (east rim)
    ui(ctx, lt, t, v) {
      const S = v.sec; if (!S) return;
      const P = (u, e, f = 0.05) => S.project(u, e, f);
      // the dented base line under Mauna Loa (on since s165): yellow along the top of the bent crust, glows from {basedent}
      const glow = F.clamp((t - (tBase - 0.15)) / 0.3) * (1 - 0.6 * F.clamp((t - (tBase + 1.2)) / 0.6));
      const runs = (pts) => { const out = []; let cur = []; for (const q of pts) { if (!q) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); } if (cur.length > 1) out.push(cur); return out; };
      // once Everest rises on the flat base level, the dent east of the bar steps back (one clear base line under both mountains)
      const evOn = F.clamp(((S.ev ? S.ev.rise : 0) - 0.05) * 4);
      const dentW = [], dentE = []; for (let u = -70; u <= uBar; u += 1.0) dentW.push(P(u, S.crustTop(u))); for (let u = uBar; u <= 70; u += 1.0) dentE.push(P(u, S.crustTop(u)));
      ui.line(ctx, runs(dentW), { color: PAL.yellow, width: 9 + 3 * glow, alpha: 0.85 + 0.15 * glow });
      ui.line(ctx, runs(dentE), { color: PAL.yellow, width: 9 + 3 * glow, alpha: (0.85 + 0.15 * glow) * (1 - 0.75 * evOn) });
      // the old sea-level line glows white across the section at {underwater} (faint before)
      const sA = F.clamp((t - (tUnder - 0.1)) / 0.3);
      const sea = []; for (let u = -60; u <= 90; u += 5) sea.push(P(u, 0));
      ui.line(ctx, runs(sea), { color: '#FFFFFF', width: 6 + 3 * sA, alpha: 0.35 + 0.65 * sA, glow: PAL.cyan, p: 1 });
      // the yellow height bar beside the summit column: from the dented base to the summit, climbing while the counter rolls
      const p = bar(t), a0 = P(uBar, BASE, 0.3), top = P(uBar, ML.summit, 0.3);
      let barBox = null;
      if (p > 0 && a0 && top) {
        const b = [a0[0] + (top[0] - a0[0]) * p, a0[1] + (top[1] - a0[1]) * p], tk = px(30);
        ui.line(ctx, [[a0, b]], { color: PAL.yellow, width: 12 });
        ui.line(ctx, [[[a0[0] - tk, a0[1]], [a0[0] + tk, a0[1]]]], { color: PAL.yellow, width: 10 });
        ui.line(ctx, [[[b[0] - tk, b[1]], [b[0] + tk, b[1]]]], { color: PAL.yellow, width: 10 });
      }
      if (a0 && top) barBox = ui.avoid(ui.boxOf([a0, top], px(36)));                      // the whole bar (incl. its top tick) stays clear
      // Everest on the same base line: the base extends under its slab, a solid white tick at its summit reaches the bar
      const er = S.ev ? S.ev.rise : 0;
      if (er > 0.02 && S.ev) {
        const eA = F.clamp((t - (tEv - 0.2)) / 0.3);
        const b0 = P(uBar, BASE, 0.3), b1 = P(EVEREST.u + EVEREST.width / 2 + 0.6, BASE, EVEREST.front + EVEREST.th);
        if (b0 && b1) ui.line(ctx, [[b0, b1]], { color: PAL.yellow, width: 9, alpha: F.clamp(er * 3), p: F.clamp(er * 1.5) });
        const evTop = BASE + 8849, s0 = P(EVEREST.u - 0.6, evTop, EVEREST.front + EVEREST.th), s1 = P(uBar, evTop, 0.3);
        if (eA > 0 && er > 0.98 && s0 && s1) ui.line(ctx, [[s0, s1]], { color: '#FFFFFF', width: 6, alpha: eA, p: eA });
      }
      // the number block (the one text block): kicker FROM ITS TRUE BASE (mandatory qualifier, logged exception) + ABOUT 56,000 FT,
      // placed in the sky clear of the bar (40 px) and of the summit: top-right, else top-centre, else top-left
      const kp = F.clamp((t - (tKick - 0.35)) / 0.4);
      const sum = P(0, ML.summit, 0);
      if (sum) ui.avoid({ x: sum[0] - px(40), y: sum[1] - px(30), w: px(80), h: px(60) });
      if (kp > 0) {
        const nOpt = { cap: 160, to: 56000, prefix: 'ABOUT', unit: 'FT', prefixCap: 58, unitCap: 100 };
        const m = ui.number(ctx, 0, 0, 0, Object.assign({ measure: true }, nOpt));
        const box = ui.block(ctx, [{ text: 'FROM ITS TRUE BASE', role: 'kicker', cap: 52, qualifier: true }], W - px(96), px(96),
          { anchor: 'right', p: kp, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow, clear: 40,
            at: [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W * 0.62, y: px(96), anchor: 'center' }, { x: px(96), y: px(96), anchor: 'left' }] });
        if (box) ui.number(ctx, 56000 * bar(t), box.inner.x, box.inner.y + m.h, Object.assign({ alpha: F.clamp(kp * 2) }, nOpt));
      }
      // MAUNA LOA map label anchored on the summit surface (held from s165), above or beside it, clear of the block and the bar
      if (sum) ui.label(ctx, 'MAUNA LOA', sum[0], sum[1], { dist: 60, accent: PAL.hero, t, order: ['above', 'above-left', 'left', 'above-right', 'right'] });
    },
  }));
  // sound cues (mix.json): rumble as Everest rises, ticks under the counter, the impact on {tall56}
  api.cue(t169 + 0.15, 'tick_counter', -16); api.cue(t56, 'impact_deep', -8); api.cue(tEv0, 'rumble_quake', -16); api.cue(tUnder, 'shimmer', -18);
  return { t0: T0, t1: T1 };
}
