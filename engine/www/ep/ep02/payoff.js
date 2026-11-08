// THE PAYOFF (s168-s172, hero number #7): Mauna Loa about 56,000 ft from its true base, next to Everest on the same base line.
// BlockStage at VE 1.0: Mauna Loa's column runs 17,170 m from its summit down to the true base (USGS: the mass pushed the sea floor
// down by up to 8 km); Everest's block is scaled so its summit is the surveyed 8,849 m and it rises out of the SAME base plane.
// Used by ch6 (call buildPayoff(api, kit, scenes, {t0, t1})) and by the stand-alone test page payoff_test.html.
import { PAL, E, F } from './shared.js';

export function buildPayoff(api, kit, scenes, o = {}) {
  const { K, ui } = kit, W = api.W, px = ui.px;
  const T0 = o.t0 ?? K.s0('s168') - 1.0, T1 = o.t1 ?? K.s1('s172') + 2.2;
  const L = (t) => t - T0;                                        // film time -> shot-local time
  const tLook = K.T('look2'), tBase = K.T('basedent'), t169 = K.s0('s169'), tKick = K.word('s169', 'base').start, t56 = K.lead('tall56');
  const tEv0 = K.s0('s170'), tEv = K.lead('ev3'), tUnder = K.lead('underwater'), tSee = K.T('see');
  const half = 10, gap = 8, xML = -(half + gap / 2), xEV = half + gap / 2, TOP = 17.17, SEA = 12.978;
  // camera keys (block space km: x east, y up, z toward the camera); slow drift keeps every hold alive
  // main framing: Mauna Loa's column on the left (summit ~(0.27, 0.30), base ~0.88), Everest's block on the right under the number block
  const MAIN = { eye: [0, 10.8, 130], target: [0, 10.6, 0], fov: 14 };
  const cam = [
    { t: 0, eye: [-9, 17.6, 70], target: [-11.5, 14.6, 0], fov: 14 },                                        // summit, sea-level line, the drowned flank
    { t: L(tLook - 0.1), eye: [-9.4, 17.2, 71], target: [-11.5, 14.2, 0], fov: 14 },
    { t: L(tBase - 0.1), eye: [-10, 2.6, 76], target: [-11.5, 4.2, 0], fov: 14, ease: E.inOut },              // tips down past the old floor to the dented base
    { t: L(t169 + 0.2), eye: [-10.2, 2.4, 78], target: [-11.5, 4.0, 0], fov: 14 },
    { t: L(t56 + 0.1), eye: [MAIN.eye[0] - 1.2, 10.6, 126], target: [MAIN.target[0] - 1.2, 10.6, 0], fov: 14, ease: E.inOut },   // pull back while the bar climbs
    { t: L(tSee - 0.4), eye: [MAIN.eye[0] + 1.0, 10.9, 131], target: [MAIN.target[0] + 0.4, 10.6, 0], fov: 14, ease: E.inOutSine },  // slow drift: Everest rises in frame
    { t: L(tSee + 1.6), eye: [MAIN.eye[0] + 1.6, 11.6, 146], target: [MAIN.target[0] + 0.6, 11.0, 0], fov: 14, ease: E.inOut },     // eases back: the whole column
    { t: L(T1), eye: [MAIN.eye[0] + 1.8, 11.7, 149], target: [MAIN.target[0] + 0.6, 11.0, 0], fov: 14 },
  ];
  const bar = (t) => E.out(F.clamp((t - (t169 + 0.15)) / (t56 - t169 - 0.15)));      // 0..1, lands on {tall56}
  scenes.push(kit.blockShot({
    id: 'payoff-blocks', t0: T0, t1: T1, blocks: { half, gap }, cam,
    ev: (lt) => E.out(F.clamp((lt - L(tEv0)) / (L(tEv) - L(tEv0)))),
    water: (lt) => 0.6 * E.inOut(F.clamp((lt - L(tUnder - 0.15)) / 0.9)),
    line: 1,
    ui(ctx, lt, t, v) {
      const z = half + 0.05, P = (x, y) => v.p(x, y, z);
      // the dented base line under Mauna Loa glows from {basedent}
      const bA = F.clamp((t - (tBase - 0.15)) / 0.3);
      if (bA > 0) { const a = P(xML - half, 0.02), b = P(xML + half, 0.02); if (a && b) ui.line(ctx, [[a, b]], { color: PAL.yellow, width: 10, alpha: bA, p: F.clamp((t - (tBase - 0.15)) / 0.5) }); }
      // the yellow height bar climbs from the true base to the summit while the counter rolls
      const p = bar(t);
      if (p > 0) {
        const bx = xML + half + 1.8, a = P(bx, 0), b = P(bx, TOP * p);
        if (a && b) { ui.line(ctx, [[a, b]], { color: PAL.yellow, width: 12 });
          const tk = px(26); ui.line(ctx, [[[a[0] - tk, a[1]], [a[0] + tk, a[1]]]], { color: PAL.yellow, width: 10 }); ui.line(ctx, [[[b[0] - tk, b[1]], [b[0] + tk, b[1]]]], { color: PAL.yellow, width: 10 }); }
      }
      // Everest's summit tick on the same base line (halfway up the bar)
      const eA = F.clamp((t - (tEv - 0.1)) / 0.3);
      if (eA > 0 && v.ev.rise > 0.98) { const a = P(xEV - half - 0.6, v.ev.top), b = P(xML + half + 1.8, v.ev.top); if (a && b) ui.line(ctx, [[a, b]], { color: '#FFFFFF', width: 6, alpha: 0.85 * eA, dash: [14, 12] }); }
      // the old sea-level line glows white across both blocks at {underwater}
      const sA = F.clamp((t - (tUnder - 0.1)) / 0.3);
      if (sA > 0) { const a = P(xML - half - 2, SEA), b = P(xEV + half + 2, SEA); if (a && b) ui.line(ctx, [[a, b]], { color: '#FFFFFF', width: 9, alpha: sA, glow: PAL.cyan, p: F.clamp((t - (tUnder - 0.1)) / 0.6) }); }
      // the number block (the one text block): kicker FROM ITS TRUE BASE (mandatory qualifier) + ABOUT 56,000 FT rolling, landing on {tall56}
      const kp = F.clamp((t - (tKick - 0.35)) / 0.4);
      if (kp > 0) {
        const nOpt = { cap: 160, to: 56000, prefix: 'ABOUT', unit: 'FT', prefixCap: 58, unitCap: 100 };
        const m = ui.number(ctx, 0, 0, 0, Object.assign({ measure: true }, nOpt));
        const box = ui.block(ctx, [{ text: 'FROM ITS TRUE BASE', role: 'kicker', cap: 52, qualifier: true }], W - px(96), px(96), { anchor: 'right', p: kp, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow });
        if (box) ui.number(ctx, 56000 * bar(t), box.inner.x, box.inner.y + m.h, Object.assign({ alpha: F.clamp(kp * 2) }, nOpt));
      }
      // MAUNA LOA map label on the summit (held from s165), placed after the block so it avoids it
      const s = P(xML + 2.2, TOP + 0.15);
      if (s) ui.label(ctx, 'MAUNA LOA', s[0], s[1], { dist: 60, accent: PAL.hero, t, side: s[1] > 300 ? 'above' : 'auto' });
    },
  }));
  // sound cues (mix.json): rumble as Everest rises, ticks under the counter, the impact on {tall56}
  api.cue(t169 + 0.15, 'tick_counter', -16); api.cue(t56, 'impact_deep', -8); api.cue(tEv0, 'rumble_quake', -16); api.cue(tUnder, 'shimmer', -18);
  return { t0: T0, t1: T1 };
}
