// Chapter 4 "Watch It Grow Old" (s084-s111), window K.chapter(4) (315.55-435.89 s, last shot to t1x). Built 2026-11-15.
// Every beat is keyed to Rodney's markers (K.T / K.lead / K.word); the chapter card (315.55-317.17) is the orchestrator's.
// Base layer 0 is one continuous ride on one camera path (PATH) with stage hand-offs where its distance crosses a threshold:
//   s084-s085  opens on ch3's last camera over the Big Island; {old} it lifts off at regional oblique; {notseen} a 1 s insert glance
//              down the drained south flank into the dark of the Hawaiian Deep (the loop re-planted, no text), then the swing to the
//              south coast. The AGE gauge (local helper, top-left plate, yellow marker on a slim bar from NOW) slides in at 317.03.
//   s086-s088  {coast} the cliffs at the end of Chain of Craters Road (holei stage, surf on black lava); s087 the two dated NPS photos
//              (before 2022, after 2026) in one wipe that lands on {arch}, HŌLEI SEA ARCH on the lintel, no cause shown; {cent} waves
//              wash through where the arch stood (foam puffs at the waterline), slow pull back and away.
//   s089-s090  flight NW to Maui (Haleakalā fills the frame), MAUI, age marker slides; Oʻahu's windward side, OʻAHU, a pin pulses on
//              Honolulu; GAG (appearance 3 of 4): back at the Pali Lookout, the paper tourist now holds his hat on with both hands
//              behind the paper wall; the gust (wind_gust) lifts the hat and nearly him, he lands, the hat stays; rise over the cliff.
//   s091-s092  flight to Kauaʻi, KAUAʻI; {canyons} the drop into Waimea Canyon under a rain squall, water threads down the gullies
//              (steepest-descent lines on the real grid); {lower} fast flight NW past Niʻihau.
//   s093-s099  Nihoa fills the frame, NIHOA; {seven} hero number ABOUT / 7 MILLION YEARS (age marker lands, impact punch); {rock} pull
//              wide; {outhere2} quick pull-out over the open NW chain; s096-s099 slow push into the valleys, late light, no outlines
//              (no published site map), no gags, no SFX (burials); {nobody} seabird specks, pull away.
//   s100-s108  flight to Lalo, LALO through {lalo}; s101 the lone pinnacle, hero fill + waterline outline on {tooth}, LA PÉROUSE
//              PINNACLE; s102 East Island BEFORE (Landsat 9 July 2018 stage), EAST ISLAND; s103 the paper monk seal on paper_tap, the pup on
//              {pups}; {left} head lift; s105 pull wide, a procedural storm spiral (CCW, eye just west, eastern eyewall over the lagoon)
//              passes SSW to NNE on {shoals}; back down to an empty beach; {away} a wave front washes the AFTER stage (13 Oct 2018) over
//              it; GAG in the gap: the seal surfaces where its beach was, bobs, looks left, looks right (paper turn), grunts, blinks;
//              {sandback} the before outline regrows to 0.7 scale (about half the area, bare sand); {seals} it flops on, two more haul out.
//   s109-s111  flight to Pūhāhonu: two paper basalt rocks (the stage grid has no pinnacles there) with foam rings, the label; the
//              flight NW over open water past the reefs, the age marker slides to the end; arrival on a moving Midway oblique (ch5).
// Local helpers only (no shared change): camOf/orbit/chainPath/route/farWater (ch3), fromEye + the paper wall (ch2), the AGE gauge, the
// hands-on-hat tourist card (the kit tourist with repainted belly and raised paper arms as a part), paper rocks, the storm tiles.
import { PAL, E, F, MOVE_WATER, WATER_FILM, heightGrid } from './shared.js';

const D2R = Math.PI / 180, KM = 111.32;
const ARCH = [-155.0979, 19.2945], HALEA = [-156.253, 20.709], HNL = [-157.858, 21.307], LOOKOUT = [-157.7936, 21.3667];
const KAU = [-159.53, 22.07], NIH = [-161.921, 23.059], LALO_C = [-166.22, 23.76], LAPER = [-166.261, 23.7689], EASTI = [-166.2104, 23.7876];
const GARD = [-167.9996, 24.9988], MIDW = [-177.37, 28.22];
// ---------------------------------------------------------------------------------------------------------------- geo helpers (ch3)
const offLL = (ll, km, brg) => { const cl = Math.cos(ll[1] * D2R); return [ll[0] + km * Math.sin(brg * D2R) / (KM * cl), ll[1] + km * Math.cos(brg * D2R) / KM]; };
const brgOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return (Math.atan2((b[0] - a[0]) * cl, b[1] - a[1]) / D2R + 360) % 360; };
const kmOf = (a, b) => { const cl = Math.cos((a[1] + b[1]) / 2 * D2R); return Math.hypot((b[0] - a[0]) * cl * KM, (b[1] - a[1]) * KM); };
function camOf(c) {
  const e = offLL([c.lon, c.lat], c.d * Math.sin(c.tilt * D2R), c.heading + 180);
  return { lon: e[0], lat: e[1], alt: (c.h || 0) / 1000 + c.d * Math.cos(c.tilt * D2R), tLon: c.lon, tLat: c.lat, tH: c.h || 0, fov: c.fov,
    near: F.clamp(c.d * 0.003, 0.004, 2), far: F.clamp(c.d * 300, 400, 9000) };
}
function orbit(t, eye, alt, tgt, h, fov, ease) { const dh = kmOf(eye, tgt), dv = alt - h / 1000;
  return { t, lon: tgt[0], lat: tgt[1], h, d: Math.hypot(dh, dv), tilt: Math.atan2(dh, dv) / D2R, heading: brgOf(eye, tgt), fov, ease }; }
// orbit key from an eye (lon/lat, alt km), a heading, a pitch below the horizon and a target distance (ch2)
function fromEye(t, eye, alt, heading, pitch, d, fov, ease) {
  const T = offLL(eye, d * Math.cos(pitch * D2R), heading);
  return { t, lon: T[0], lat: T[1], h: (alt - d * Math.sin(pitch * D2R)) * 1000, d, tilt: 90 - pitch, heading, fov, ease };
}
function monotone(keys) {
  const n = keys.length, x = keys.map(k => k[0]), y = keys.map(k => k[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
  m[0] = 0; m[n - 1] = 0;
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : 3 * (x[i + 1] - x[i - 1]) / ((2 * x[i + 1] - x[i] - x[i - 1]) / d[i - 1] + (x[i + 1] + x[i] - 2 * x[i - 1]) / d[i]);
  return (t) => { if (t <= x[0]) return y[0]; if (t >= x[n - 1]) return y[n - 1];
    let i = 0; while (t > x[i + 1]) i++; const h = x[i + 1] - x[i], s = (t - x[i]) / h, s2 = s * s, s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * y[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * y[i + 1] + (s3 - s2) * h * m[i + 1]; };
}
function chainPath(keys) {
  const hd = [keys[0].heading];
  for (let i = 1; i < keys.length; i++) hd.push(hd[i - 1] + ((((keys[i].heading - keys[i - 1].heading) % 360) + 540) % 360 - 180));
  const ch = (f) => monotone(keys.map((k, i) => [k.t, f(k, i)]));
  const C = { lon: ch(k => k.lon), lat: ch(k => k.lat), ld: ch(k => Math.log(k.d)), tilt: ch(k => k.tilt), hd: ch((k, i) => hd[i]), fov: ch(k => k.fov), h: ch(k => k.h || 0) };
  return (t) => ({ lon: C.lon(t), lat: C.lat(t), d: Math.exp(C.ld(t)), tilt: C.tilt(t), heading: C.hd(t), fov: C.fov(t), h: C.h(t) });
}
const route = (...segs) => (t) => { for (const [a, b, f] of segs) if (t <= b) return f(Math.max(t, a)); const L = segs[segs.length - 1]; return L[2](L[1]); };
function farWater(d) {
  const k = E.inOut(F.clamp((Math.log(d) - Math.log(25)) / (Math.log(500) - Math.log(25))));
  return k > 0 ? WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], k))) : null;
}
function blurred(shot, w0, w1, n = 6, shutter = 0.5) {
  const inner = shot.draw.bind(shot);
  shot.draw = async function (ctx, lt, t, api) {
    if (t < w0 || t > w1 || api.Q.noblur) return inner(ctx, lt, t, api);
    const A = ctx.globalAlpha, dt = shutter / api.FPS, m = api.Q.draft ? 3 : n;
    for (let k = 0; k < m; k++) { const o = (k / (m - 1) - 0.5) * dt; ctx.save(); ctx.globalAlpha = A / (k + 1); await inner(ctx, lt + o, t + o, api); ctx.restore(); }
  };
  return shot;
}
function ready(shot, fn) { const d = shot.draw.bind(shot); shot.draw = async function (ctx, lt, t, api) { await fn(); return d(ctx, lt, t, api); }; return shot; }
const hash = (a, b = 0) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };
const loadImg = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('cannot load ' + src)); i.src = src; });
const centroid = (r) => { let a = 0, x = 0, y = 0; for (let i = 0; i < r.length - 1; i++) { const [x0, y0] = r[i], [x1, y1] = r[i + 1], c = x0 * y1 - x1 * y0; a += c; x += (x0 + x1) * c; y += (y0 + y1) * c; } return Math.abs(a) < 1e-14 ? r[0] : [x / (3 * a), y / (3 * a)]; };

// ---------------------------------------------------------------------------------------------------------------- paper cards
// the Pali lookout wall (ch2's card, same seed: the same wall)
function wallCard(kit) {
  const w = 2400, h = 300, c = kit.P.cv(w, h), g = c.getContext('2d'), R = F.rng(11);
  g.fillStyle = '#8f897d'; g.fillRect(0, 0, w, h);
  for (let row = 0, y = 26; y < h + 20; row++) {
    const rh = 52 + R() * 26; let x = -R() * 90 - (row % 2) * 40;
    while (x < w + 40) {
      const sw = 90 + R() * 120, cx = x + sw / 2, cy = y + rh / 2, n = 9, pts = [];
      for (let k = 0; k < n; k++) { const a = k / n * Math.PI * 2, rr = 0.86 + R() * 0.16; pts.push([cx + Math.cos(a) * sw * 0.47 * rr, cy + Math.sin(a) * rh * 0.45 * rr]); }
      const tn = 58 + R() * 40, warm = R() * 10;
      const path = () => { g.beginPath(); pts.forEach(([px_, py_], i) => i ? g.lineTo(px_, py_) : g.moveTo(px_, py_)); g.closePath(); };
      path(); g.fillStyle = `rgb(${Math.round(tn + 8 + warm)},${Math.round(tn + 4)},${Math.round(tn)})`; g.fill();
      g.save(); path(); g.clip();
      const lg = g.createLinearGradient(0, cy - rh / 2, 0, cy + rh / 2); lg.addColorStop(0, 'rgba(255,246,225,0.22)'); lg.addColorStop(0.45, 'rgba(255,246,225,0)'); lg.addColorStop(1, 'rgba(0,0,0,0.30)');
      g.fillStyle = lg; g.fillRect(cx - sw, cy - rh, sw * 2, rh * 2);
      for (let k = 0; k < 6; k++) { g.fillStyle = `rgba(${R() < 0.5 ? '255,250,240' : '0,0,0'},0.07)`; g.beginPath(); g.arc(cx + (R() - 0.5) * sw * 0.7, cy + (R() - 0.5) * rh * 0.6, 4 + R() * 10, 0, 7); g.fill(); }
      g.restore();
      x += sw * (0.92 + R() * 0.1);
    }
    y += rh * 0.93;
  }
  g.fillStyle = '#b3ab9c'; g.fillRect(0, 0, w, 24); g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(0, 22, w, 7);
  return kit.prepPaper(c, { edge: 5 });
}
// aloha print on a canvas region (red cloth, pale five-petal flowers with red centres), used for the repaint and the sleeves
function aloha(g, R, x0, y0, w, h, n) {
  for (let i = 0; i < n; i++) { const x = x0 + R() * w, y = y0 + R() * h, r = 7 + R() * 5, a0 = R() * 6.28;
    g.fillStyle = 'rgba(232,170,140,0.92)'; for (let k = 0; k < 5; k++) { const a = a0 + k * 1.2566; g.beginPath(); g.arc(x + Math.cos(a) * r * 0.8, y + Math.sin(a) * r * 0.8, r * 0.62, 0, 7); g.fill(); }
    g.fillStyle = 'rgba(214,72,52,0.9)'; g.beginPath(); g.arc(x, y, r * 0.32, 0, 7); g.fill(); }
}
// the kit tourist holding his hat on with both hands: his crossed hands on the belly repainted as shirt (clipped to the photo's own
// silhouette), and raised paper arms (sleeves in the same red aloha print, hands gripping the brim) as a part drawn over the hat
async function touristHold(kit, TOUR) {
  const img = await loadImg('/ep/ep02/img/paper/tourist.png'), w = img.width, h = img.height, R = F.rng(5);
  const c = kit.P.cv(w, h), g = c.getContext('2d'); g.drawImage(img, 0, 0);
  g.save(); g.globalCompositeOperation = 'source-atop';
  const sh = g.createLinearGradient(0, 255, 0, 330); sh.addColorStop(0, '#C8301F'); sh.addColorStop(1, '#B02818');
  g.fillStyle = sh; g.beginPath(); g.ellipse(130, 292, 56, 40, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(70,74,82,0.85)'; g.fillRect(118, 250, 18, 26);                       // the tie runs on under the arms' old place
  aloha(g, R, 84, 262, 92, 56, 7); g.restore();
  const OX = 110, OY = 24, a = kit.P.cv(w + 2 * OX, 230), ag = a.getContext('2d'); ag.translate(OX, OY); ag.lineCap = 'round'; ag.lineJoin = 'round';
  const elbow = (S, Hh, L1, L2, side) => { const dx = Hh[0] - S[0], dy = Hh[1] - S[1], d = Math.hypot(dx, dy), ux = dx / d, uy = dy / d;
    const aa = (L1 * L1 - L2 * L2 + d * d) / (2 * d), hh = Math.sqrt(Math.max(0, L1 * L1 - aa * aa)); return [S[0] + aa * ux - side * uy * hh, S[1] + aa * uy + side * ux * hh]; };
  for (const [S, Hh, side] of [[[26, 152], [46, 50], -1], [[212, 152], [192, 50], 1]]) {     // elbows out wide (side picks the outer solution)
    const El = elbow(S, Hh, 112, 116, side), Wr = [F.lerp(El[0], Hh[0], 0.86), F.lerp(El[1], Hh[1], 0.86)];
    ag.strokeStyle = '#8E2014'; ag.lineWidth = 40; ag.beginPath(); ag.moveTo(...S); ag.lineTo(...El); ag.lineTo(...Wr); ag.stroke();
    ag.strokeStyle = '#C8301F'; ag.lineWidth = 34; ag.beginPath(); ag.moveTo(...S); ag.lineTo(...El); ag.lineTo(...Wr); ag.stroke();
    ag.save(); ag.beginPath(); ag.lineWidth = 34; ag.moveTo(...S); ag.lineTo(...El); ag.lineTo(...Wr); ag.strokeStyle = '#000'; ag.globalCompositeOperation = 'source-atop';
    const bx = Math.min(S[0], El[0], Wr[0]) - 20, by = Math.min(S[1], El[1], Wr[1]) - 20; aloha(ag, R, bx, by, Math.abs(El[0] - S[0]) + 40, Math.abs(S[1] - Wr[1]) + 40, 9); ag.restore();
    ag.fillStyle = 'rgba(255,240,220,0.18)'; ag.beginPath(); ag.arc(El[0], El[1], 12, 0, 7); ag.fill();
    ag.strokeStyle = '#E6D9C2'; ag.lineWidth = 8; ag.beginPath(); ag.moveTo(Wr[0] - 15, Wr[1] + 4); ag.lineTo(Wr[0] + 15, Wr[1] - 2); ag.stroke();   // shirt cuff
    ag.fillStyle = '#B58466'; ag.beginPath(); ag.ellipse(Hh[0], Hh[1], 17, 20, 0, 0, 7); ag.fill();                                                   // the hand on the brim
    ag.fillStyle = '#C99476'; for (let k = 0; k < 4; k++) { ag.beginPath(); ag.ellipse(Hh[0] - side * 6 + k * side * 0 + (k - 1.5) * 7, Hh[1] - 16, 4.5, 7, 0, 0, 7); ag.fill(); }
    ag.fillStyle = 'rgba(80,50,35,0.35)'; ag.beginPath(); ag.ellipse(Hh[0], Hh[1] + 9, 13, 6, 0, 0, 7); ag.fill();
  }
  const body = kit.prepPaper(c, { edge: 3, edgeColor: '#F1E8D6' }), arms = kit.prepPaper(a, { edge: 3, edgeColor: '#F1E8D6' });
  return Object.assign(body, { name: 'tourist_hold', parts: { hat: TOUR.parts.hat, arms: Object.assign(arms, { at: [-OX, -OY] }) }, meta: TOUR.meta, base: true, sink: 0, tilt: 0 });
}
// a basalt pinnacle as a paper card: ragged sides, a narrow broken top whitened by seabird guano, darker wet foot
function rockCard(kit, seed, w, h, top) {
  const c = kit.P.cv(w, h), g = c.getContext('2d'), R = F.rng(seed), n = 16, L = [], Rt = [];
  for (let i = 0; i <= n; i++) { const v = i / n, half = w * (0.48 - (0.48 - top) * Math.pow(v, 0.85)) * (0.86 + 0.22 * R()); L.push([w / 2 - half + w * 0.05 * Math.sin(v * 5 + seed), h * (1 - v) + (i === n ? R() * h * 0.04 : 0)]); }
  for (let i = n; i >= 0; i--) { const v = i / n, half = w * (0.48 - (0.48 - top) * Math.pow(v, 0.85)) * (0.86 + 0.22 * R()); Rt.push([w / 2 + half + w * 0.05 * Math.sin(v * 5 + seed), h * (1 - v) + (i === n ? R() * h * 0.06 : 0)]); }
  const pts = L.concat(Rt); g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.closePath();
  const lg = g.createLinearGradient(0, 0, w, 0); lg.addColorStop(0, '#5a524b'); lg.addColorStop(0.55, '#3f3a36'); lg.addColorStop(1, '#2b2826'); g.fillStyle = lg; g.fill();
  g.save(); g.clip();
  for (let k = 0; k < 26; k++) { g.strokeStyle = `rgba(${R() < 0.5 ? '255,245,230' : '0,0,0'},${0.06 + R() * 0.08})`; g.lineWidth = 2 + R() * 5; const x = R() * w; g.beginPath(); g.moveTo(x, R() * h * 0.3); g.lineTo(x + (R() - 0.5) * w * 0.2, h * (0.5 + R() * 0.5)); g.stroke(); }
  for (let k = 0; k < 40; k++) { g.fillStyle = `rgba(236,232,222,${0.55 + R() * 0.4})`; const y = h * Math.pow(R(), 1.8) * 0.32, x = w * 0.5 + (R() - 0.5) * w * (0.2 + y / h * 1.4); g.beginPath(); g.ellipse(x, y, 3 + R() * 9, 2 + R() * 5, 0, 0, 7); g.fill(); }
  for (let k = 0; k < 10; k++) { g.strokeStyle = 'rgba(232,228,218,0.5)'; g.lineWidth = 1.5 + R() * 2.5; const x = w * (0.3 + R() * 0.4), y = h * 0.1 + R() * h * 0.15; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - 0.5) * 8, y + h * (0.1 + R() * 0.25)); g.stroke(); }
  const wg = g.createLinearGradient(0, h * 0.8, 0, h); wg.addColorStop(0, 'rgba(0,0,0,0)'); wg.addColorStop(1, 'rgba(8,10,12,0.55)'); g.fillStyle = wg; g.fillRect(0, h * 0.8, w, h * 0.2);
  g.restore();
  return kit.prepPaper(c, { edge: 4 });
}
// a hurricane cloud disc (north up, east right): three log-spiral bands turning counter-clockwise inward (northern hemisphere) with
// finer streets inside them, a dense central overcast, a bright eyewall around a clear eye. The tiles are OPAQUE, premultiplied on
// black (overlapping tile edges are then idempotent: no seams), and the whole disc is laid onto the frame with a screen blend.
function stormTiles(kit, N = 1024, TN = 12) {
  const c = kit.P.cv(N, N), g = c.getContext('2d'), im = g.createImageData(N, N), d = im.data;
  const vn = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, s = (a) => a * a * (3 - 2 * a);
    const h00 = hash(xi, yi), h10 = hash(xi + 1, yi), h01 = hash(xi, yi + 1), h11 = hash(xi + 1, yi + 1);
    return F.lerp(F.lerp(h00, h10, s(xf)), F.lerp(h01, h11, s(xf)), s(yf)); };
  const fbm = (x, y) => vn(x, y) * 0.5 + vn(x * 2.1, y * 2.1) * 0.27 + vn(x * 4.3, y * 4.3) * 0.15 + vn(x * 8.7, y * 8.7) * 0.08;
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const x = (i + 0.5) / N * 2 - 1, y = 1 - (j + 0.5) / N * 2, r = Math.hypot(x, y), ph = Math.atan2(y, x);
    const w1 = fbm(x * 3 + 11, y * 3 + 5), w2 = fbm(x * 9 + 2, y * 9 + 8), w3 = fbm(x * 24 + 4, y * 24 + 1);
    const sp = ph + 2.4 * Math.log(Math.max(r, 0.02)) + (w1 - 0.5) * 1.8;
    const arm = 0.5 + 0.5 * Math.cos(3 * sp), fine = 0.5 + 0.5 * Math.cos(11 * sp + w2 * 4);
    const cdo = 1 - F.clamp((r - 0.19 - 0.07 * (w1 - 0.5)) / 0.15);
    const band = Math.pow(arm, 1.25) * (0.6 + 0.4 * fine) * F.clamp(1 - (r - 0.25) / 0.68);
    const wall = Math.exp(-Math.pow((r - 0.058) / 0.022, 2)), eye = F.clamp((r - 0.03 - 0.012 * (w2 - 0.5)) / 0.022);
    let den = (Math.max(cdo * (0.85 + 0.2 * w2), band * (0.6 + 0.8 * w2)) + 0.25 * wall) * eye * F.clamp((0.98 - r) / 0.16);
    den = F.clamp(den * (0.7 + 0.6 * w3));
    const sh = F.clamp((168 + 84 * den + 26 * (w3 - 0.5) + 14 * wall) / 255), a = F.clamp(den * 1.2) * 0.95, k = (j * N + i) * 4;
    d[k] = 255 * sh * a; d[k + 1] = 255 * Math.min(1, sh * 1.01) * a; d[k + 2] = 255 * Math.min(1, sh * 1.03) * a; d[k + 3] = 255;
  }
  g.putImageData(im, 0, 0);
  const ts = N / TN, tiles = [];
  for (let b = 0; b < TN; b++) for (let a = 0; a < TN; a++) { const t = kit.P.cv(ts + 2, ts + 2), tg = t.getContext('2d'); tg.fillStyle = '#000'; tg.fillRect(0, 0, ts + 2, ts + 2);
    tg.drawImage(c, a * ts - 1, b * ts - 1, ts + 2, ts + 2, 0, 0, ts + 2, ts + 2);
    tiles.push({ img: t, u0: (a * ts - 1) / N, v0: (b * ts - 1) / N, u1: ((a + 1) * ts + 1) / N, v1: ((b + 1) * ts + 1) / N }); }
  return tiles;
}

// ---------------------------------------------------------------------------------------------------------------- build
export async function build(api, kit, scenes) {
  const { K, ui } = kit, W = api.W, H = api.H, px = ui.px, TY = kit.T;
  const ch = K.chapter(4), T = (m) => K.T(m), lead = (m, f = 3) => K.lead(m, f), s0 = (s) => K.s0(s), s1 = (s) => K.s1(s);
  const pr = (t, a, b, e = E.inOut) => e(F.clamp((t - a) / Math.max(1e-6, b - a)));
  const env = (t, a, b, fi = 0.3, fo = 0.3) => F.clamp(Math.min((t - a) / fi, (b - t) / fo));
  const dbg = !!api.Q.ch4dbg, XF = 0.45, dummy = kit.P.cv(4, 4).getContext('2d');
  const wd = (seg, w) => K.word(seg, w).start, tRain = wd('s091', 'rain'), tHur = wd('s105', 'hurricane'), tSlid = wd('s090', 'slid'), tSea = wd('s090', 'sea');
  const TODAY_SET = { foamAmt: 0.6, foamPx: 0, foamM: 2 };
  const DEEPW = WATER_FILM.map((c, j) => c.map((v, q) => F.lerp(v, MOVE_WATER[j][q], 0.75)));
  const gh = (v, lon, lat) => Math.max(v.S.heightAt(lon, lat), v.level ?? 0);
  const gp = (v, ll, off = 30) => v.project(ll[0], ll[1], gh(v, ll[0], ll[1]) + off);
  const druns = (v, pts, off = 40, every = 3, flat = null) => {
    const out = []; let cur = [];
    for (let i = 0; i < pts.length; i++) { const [lo, la] = pts[i], hm = (flat ?? gh(v, lo, la)) + off, q = v.project(lo, la, hm);
      const ok = q && q[0] > -400 && q[0] < W + 400 && q[1] > -400 && q[1] < H + 400 && (i % every || v.visible(lo, la, hm));
      if (!ok) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); }
    if (cur.length > 1) out.push(cur); return out; };
  const heroBright = (S) => { const u = S.maskU?.heroCol; if (!u) return; if (!S._heroDef) S._heroDef = u.value.clone(); u.value.setRGB(0.34, 0.068, 0.018); };
  const heroReset = (S) => { const u = S.maskU?.heroCol; if (u && S._heroDef) u.value.copy(S._heroDef); };
  const camDist = (view, lon, lat, hm) => view.S.xyz(lon, lat, hm).distanceTo(view.S.cam.position);
  const ON = (view, q, m = 0) => q && q[0] > -m && q[0] < W + m && q[1] > -m && q[1] < H + m;

  // ================================================================ sun, water, exposure (film time)
  const SUNK = [[ch.t0, 210, 38], [T('old') + 0.9, 210, 38], [T('notseen') + 0.85, 128, 30], [T('cent') + 0.2, 128, 30], [T('maui2') - 0.9, 160, 34], [s0('s090'), 160, 34],
    [T('oahu2'), 100, 42], [T('hnl') + 1.15, 100, 42], [tSlid, 75, 55], [tSea + 0.25, 120, 42],
    [T('kauai') - 0.05, 190, 36], [tRain + 0.2, 200, 34], [T('canyons') + 0.05, 225, 30], [s1('s092') - 1.3, 225, 30], [T('nihoa') - 0.15, 215, 32], [s0('s097') - 0.2, 215, 30],
    [s0('s098') - 0.1, 230, 24], [T('dead') - 0.55, 255, 14], [s0('s099'), 250, 18], [T('ffs') - 0.2, 210, 35], [s0('s109'), 210, 35], [T('pokes') - 0.2, 210, 30], [s0('s110') + 0.6, 210, 30], [T('onlyreef') - 0.4, 200, 38]];
  const sunAz = monotone(SUNK.map(k => [k[0], k[1]])), sunEl = monotone(SUNK.map(k => [k[0], k[2]]));
  const SUN = (t) => [sunAz(t), sunEl(t)];
  // Lalo's lagoon and white sand measured luma 133-150 (film range 85-130): trimmed from s101 to the s109 flight and again over Gardner
  const LALO_DIM = (t) => Math.max(0.08 * env(t, s0('s101') - 0.5, s0('s105') + 0.4, 0.8, 0.6), 0.08 * env(t, T('away') - 0.5, s0('s109') + 0.35, 0.5, 0.45),
    0.16 * env(t, T('pokes') - 1.6, s0('s110') + 1.25, 0.6, 0.6));   // not over the storm's high ocean (12348 was 69 dimmed); measured: 0.12 -> luma x0.87
  // the windward pull-out under the high sun (r7 10459 137, 10480 144) and Nihoa's turquoise sea (10874-11518: 133-139) were over 130 as well;
  // at 0.1 the middle of the pull-out (r8motr 10468-10476) still measured 131-133, so 0.135 there
  const HI_DIM = (t) => 0.135 * env(t, tSlid - 0.4, s0('s091') + 0.15, 0.5, 0.5) + 0.08 * env(t, T('nihoa') - 1.2, T('nobody') + 0.5, 1.0, 0.5);
  const EXPO = (t) => 1 + 0.22 * env(t, s0('s098') - 0.3, T('nobody') + 0.5, 1.2, 1.2) + 0.08 * env(t, T('canyons') - 0.2, s1('s091') + 0.2, 0.5, 0.6) - LALO_DIM(t) - HI_DIM(t);
  const FOAM = (t) => (t > T('coast') - 1.5 && t < T('cent') + 2.0) ? 1 : 0.6;
  // the shot state: today, the film water blending to navy from far up, the chapter's sun (o: set extras, water name, sun override)
  const stAt = (c, t, o = {}) => { const st = { sun: o.sun || SUN(t), set: Object.assign({}, TODAY_SET, { foamAmt: o.foam ?? FOAM(t) }, o.set || {}) };
    const wc = farWater(c.d); if (wc) st.waterCols = wc; else if (o.waterCols) st.waterCols = o.waterCols; else if (o.water) st.water = o.water;
    const ex = EXPO(t); if (Math.abs(ex - 1) > 1e-3) st.post = { exposure: ex }; return st; };

  // ================================================================ camera: one ride (route of flights; each eases at its own ends)
  const tA0 = K.chapter(3).t1x, tCoast = T('coast') + 0.05, tCent = T('cent') + 0.04, tMauiE = s0('s090') - 0.13, tPg = T('hnl') + 1.1;
  const A1 = [
    { t: tA0, lon: -155.55, lat: 19.62, h: 0, d: 240, tilt: 50, heading: 24, fov: 38 },                 // ch3's last camera
    { t: T('old') - 0.1, lon: -155.50, lat: 19.57, h: 0, d: 205, tilt: 50, heading: 21, fov: 38 },
    { t: T('old') + 1.43, lon: -155.32, lat: 19.42, h: 0, d: 265, tilt: 43, heading: 6, fov: 38 },      // {old}: lift off, regional
    { t: T('notseen') - 0.22, lon: -155.16, lat: 19.33, h: 0, d: 95, tilt: 52, heading: 345, fov: 39 },
    { t: T('notseen') + 1.03, lon: -155.108, lat: 19.302, h: 0, d: 16, tilt: 68, heading: 300, fov: 40 },
    // {coast}: the cliffs at Hōlei seen ALONG the coast from offshore (eye 1.4 km at bearing 102, 270 m up, over the sea): the cliff
    // line and its surf run diagonally through the frame, sea left, the lava plain right (was: looking inland across a tan slope)
    { t: tCoast, lon: ARCH[0], lat: ARCH[1], h: 0, d: 1.4, tilt: 79, heading: 282, fov: 40 },
  ];
  const A2 = [A1[5],
    { t: s0('s087') + 0.27, lon: ARCH[0], lat: ARCH[1], h: 0, d: 1.3, tilt: 79.3, heading: 279, fov: 40 },
    { t: s0('s088') - 0.04, lon: ARCH[0], lat: ARCH[1], h: 0, d: 1.2, tilt: 79.6, heading: 276, fov: 40 },
    { t: tCent, lon: ARCH[0], lat: ARCH[1], h: 0, d: 1.1, tilt: 80, heading: 274, fov: 40 }];
  const A3 = [A2[3],
    { t: s0('s089') - 0.04, lon: -155.104, lat: 19.300, h: 0, d: 5, tilt: 72, heading: 295, fov: 40 },   // slow pull back and away
    { t: T('maui2') - 1.32, lon: -155.70, lat: 20.00, h: 0, d: 150, tilt: 48, heading: 318, fov: 38 },
    { t: T('maui2') - 0.1, lon: -156.24, lat: 20.70, h: 1200, d: 58, tilt: 64, heading: 320, fov: 38 },  // Haleakalā fills the frame
    { t: tMauiE, lon: -156.255, lat: 20.715, h: 1200, d: 52, tilt: 65, heading: 322, fov: 38 }];
  const B = [A3[4],
    { t: s0('s090') + 0.72, lon: -156.95, lat: 21.08, h: 400, d: 140, tilt: 52, heading: 292, fov: 38 },
    { t: T('oahu2') - 0.02, lon: -157.79, lat: 21.42, h: 300, d: 42, tilt: 63, heading: 245, fov: 40 },   // windward Oʻahu, the Koʻolau
    { t: tPg + 0.3, lon: -157.81, lat: 21.41, h: 300, d: 37, tilt: 63.5, heading: 238, fov: 40 }];
  const pathB = chainPath(B);
  // the Pali callback (ch2's settled framing and push), then the rise over the cliff and on to Kauaʻi in one flight
  const tGu = 346.24 - 346.24 + (T('hnl') + 1.49);                                                       // the mix's wind_gust (x105)
  const tRise = tGu + 1.96, tKau = T('kauai') - 0.05, tCanH = tRain + 0.31, tCan = T('canyons') + 0.05, tNi0 = s1('s092') - 1.24;
  const PK = [fromEye(tPg, offLL(LOOKOUT, 0.84, 223), 0.79, 57, 14, 2.5, 48), fromEye(tRise, offLL(LOOKOUT, 0.75, 223.5), 0.745, 58.5, 15, 2.5, 47),
    fromEye(tRise + 1.3, offLL(LOOKOUT, 2.5, 40), 6, 15, 24, 18, 46),
    { t: tKau - 0.8, lon: -158.6, lat: 21.85, h: 0, d: 160, tilt: 48, heading: 300, fov: 40 },
    { t: tKau, lon: -159.50, lat: 22.06, h: 600, d: 70, tilt: 58, heading: 322, fov: 42 },                 // {kauai}
    { t: tCanH, lon: -159.57, lat: 22.05, h: 600, d: 62, tilt: 59, heading: 326, fov: 42 }];
  const CN = [PK[5], orbit(tCan, [-159.655, 21.955], 2.4, [-159.66, 22.06], 600, 45),                  // {canyons}: down into the walls
    orbit(tNi0, [-159.657, 21.975], 2.2, [-159.662, 22.07], 600, 44)];
  const tNih = T('nihoa') - 0.1, tSeven = lead('seven'), tOut0 = T('outhere2') - 0.2, tOut1 = tOut0 + 1.1, tLived1 = T('lived') + 1.0;
  const NF = [CN[2], { t: tNi0 + 0.95, lon: -160.9, lat: 22.6, h: 0, d: 150, tilt: 56, heading: 312, fov: 40 },   // past Niʻihau, Nihoa ahead in frame
    { t: tNih - 0.42, lon: NIH[0], lat: NIH[1], h: 40, d: 14, tilt: 70, heading: 328, fov: 39 },          // target locked on Nihoa: a centred push-in
    { t: tNih, lon: NIH[0], lat: NIH[1], h: 80, d: 2.8, tilt: 76, heading: 335, fov: 38 }];
  const NH = [NF[3],
    { t: T('seven') - 0.1, lon: NIH[0], lat: NIH[1], h: 80, d: 2.65, tilt: 76, heading: 338, fov: 38 },
    { t: T('rock') - 0.1, lon: NIH[0], lat: NIH[1], h: 80, d: 2.5, tilt: 76.5, heading: 341, fov: 38 },
    { t: T('rock') + 1.0, lon: NIH[0], lat: NIH[1], h: 60, d: 9, tilt: 70, heading: 336, fov: 38 },       // {rock}: how little is left
    { t: tOut0, lon: NIH[0], lat: NIH[1], h: 60, d: 9.8, tilt: 70, heading: 332, fov: 38 },
    { t: tOut1, lon: offLL(NIH, 4, 315)[0], lat: offLL(NIH, 4, 315)[1], h: 0, d: 48, tilt: 60, heading: 318, fov: 40 },   // {outhere2}: Nihoa a sliver in the open chain
    { t: tLived1, lon: NIH[0], lat: NIH[1] + 0.001, h: 90, d: 2.4, tilt: 74, heading: 355, fov: 38 },     // {lived}: into the valleys
    { t: lead('shrine'), lon: NIH[0], lat: NIH[1] + 0.001, h: 90, d: 2.15, tilt: 74, heading: 4, fov: 38 },
    { t: s0('s099'), lon: NIH[0] + 0.001, lat: NIH[1] + 0.001, h: 90, d: 2.0, tilt: 73, heading: 22, fov: 38 },   // late light drift
    { t: T('nobody') + 0.1, lon: NIH[0], lat: NIH[1], h: 60, d: 7.5, tilt: 69, heading: 28, fov: 38 },    // {nobody}: pull away
    { t: s1('s099') + 0.0, lon: NIH[0], lat: NIH[1], h: 60, d: 8.5, tilt: 68, heading: 30, fov: 38 }];
  const tLa0 = s1('s099'), tLaA = tLa0 + 0.75, tLa1 = T('ffs') - 0.85, tD0 = s0('s101') - 0.05, tD1 = tD0 + 2.0, tE0 = T('tooth') + 1.37;
  const LA = [NH[10],
    { t: tLaA, lon: -165.5, lat: 23.62, h: 0, d: 160, tilt: 56, heading: 25, fov: 40 },                   // past Mokumanamana's bank, Lalo ahead
    orbit(tLa1, [-166.37, 23.58], 14, [-166.22, 23.77], 0, 40),                                            // {ffs}: the lagoon at Lalo
    orbit(tD0, [-166.36, 23.59], 13.4, [-166.22, 23.77], 0, 40)];
  const pinEye = (b, dd, alt) => offLL(LAPER, dd, b);
  const LD = [LA[3], orbit(tD0 + 1.0, pinEye(236, 2.2), 0.9, LAPER, 14, 38),                                 // the pinnacle centred early, then down to it
    orbit(tD1, pinEye(236, 0.34), 0.05, LAPER, 14, 38), orbit(tE0, pinEye(224, 0.30), 0.046, LAPER, 14, 38)];   // s101 the tooth
  const tE1 = T('east') - 0.1, tS0 = s0('s105'), tS1 = tS0 + 1.5, tS2 = s1('s105'), tS3 = tS2 + 1.55, tGa0 = s0('s109');
  const tTap = s0('s103') + 0.15, tAway = T('away'), tFr0 = tAway - 0.1, tFr1 = tAway + 0.7, tSurf = s1('s106') + 0.35, tGrunt = tSurf + 1.1, tFlop = T('seals') + 0.02;
  const EI = { c: EASTI.slice(), ring: null, done: false, brg: 100, half: 0.22 };      // East Island: centroid and ring from the 2018 BEFORE stage (filled lazily)
  // the seal spots and the cameras that frame them share one fixed copy of that outline's centroid, long axis and half-length (as
  // logged from lalo_2018_before: -166.2094, 23.7869, 125 deg, 0.248 km), so the async ring can never move a seal off its camera
  const EIC = [-166.2094, 23.7869], EIBRG = 125, EIHALF = 0.248, eiFix = (u, v = 0) => offLL(offLL(EIC, u, EIBRG), v, EIBRG + 90);
  const SPOT = { sp: eiFix(-0.12 * EIHALF), pup: eiFix(0.42 * EIHALF, 0.008), sand: eiFix(0, -0.004), s2: eiFix(0.42 * EIHALF, 0.01), s3: eiFix(0.1 * EIHALF, -0.03) };   // s3 on the wide far part of the regrown bar, behind the hero's back (in the regrown outline, checked in sim)
  SPOT.water = offLL(SPOT.sand, 0.06, 260);       // the gag: in the water just off the old beach's edge, a short flop from the regrown sand
  // a seal camera: target a km right of and b km beyond the spot P along the view, so the seal sits lower left at 35-45 % of frame height
  const SC = (t, P, a, b, d, tilt, hd) => { const g = offLL(offLL(P, b, hd), a, hd + 90); return { t, lon: g[0], lat: g[1], h: 0, d, tilt, heading: hd, fov: 40 }; };
  const ES = [LD[3],
    { t: tE0 + 0.9, lon: -166.236, lat: 23.778, h: 0, d: 4, tilt: 60, heading: 48, fov: 40 },
    { t: tE1, lon: EIC[0], lat: EIC[1], h: 0, d: 0.74, tilt: 66, heading: 50, fov: 40 },                  // {east}: the island fills the frame
    SC(tTap + 0.35, SPOT.sp, 0.03, 0.08, 0.33, 66, 42),                                                   // s103: down to the seal (38 % of frame height), the pup's spot right
    SC(s0('s104'), SPOT.sp, 0.03, 0.08, 0.312, 66.5, 46),
    SC(T('left') + 0.4, SPOT.sp, 0.028, 0.08, 0.288, 67, 48),                                              // {left}: slow push
    SC(tS0, SPOT.sp, 0.028, 0.08, 0.28, 67, 49)];
  const SS = [ES[6],
    { t: tS1, lon: -166.25, lat: 23.77, h: 0, d: 230, tilt: 40, heading: 20, fov: 42 },                    // s105: wide over the shoals
    { t: tS2, lon: -166.24, lat: 23.775, h: 0, d: 215, tilt: 41, heading: 22, fov: 42 },
    { t: tS3, lon: EIC[0], lat: EIC[1], h: 0, d: 0.68, tilt: 64, heading: 30, fov: 40 },                   // back down: an empty beach
    { t: tFr1 - 0.25, lon: EIC[0], lat: EIC[1], h: 0, d: 0.6, tilt: 62, heading: 22, fov: 40 },            // {away}: the wipe, the island centred
    SC(tSurf - 0.08, SPOT.water, 0.04, 0.06, 0.27, 54, 22),                                                // the gag: the seal surfaces lower left (41 %), the old beach behind
    SC(s0('s107'), SPOT.water, 0.04, 0.06, 0.265, 54, 24),
    SC(T('sandback'), SPOT.water, 0.04, 0.06, 0.28, 54.5, 25),                                             // {sandback}: the sand regrows behind and right of it
    SC(tFlop - 0.3, SPOT.water, 0.04, 0.06, 0.285, 55, 26),                                                // {seals}: one frame holds the flop and the haul-out
    SC(tGa0, SPOT.water, 0.04, 0.06, 0.27, 55.5, 28)];
  // every zoom-in locks its target on the subject one key before arrival (a centred push-in), every exit rises with the target held,
  // then travels: the subject never slides out of frame while the distance collapses (r2-r5: empty-sea frames at 12805-12950, 13003-13030)
  const tGa1 = tGa0 + 1.37, tGa2 = T('pokes') - 0.1, tEnd0 = s0('s110') - 0.1, tEnd1 = tEnd0 + 1.9, tAt = T('atall') - 0.4;
  const GMID = offLL(GARD, 0.05, 235);
  const GA = [SS[SS.length - 1], { t: tGa0 + 0.6, lon: EASTI[0], lat: EASTI[1], h: 0, d: 7, tilt: 62, heading: 30, fov: 40 },    // rise off East Island, the atoll held
    { t: tGa1, lon: -167.4, lat: 24.55, h: 0, d: 150, tilt: 68, heading: 318, fov: 40 },                   // mid-flight, Pūhāhonu ahead in frame
    { t: tGa2 - 0.53, lon: GMID[0], lat: GMID[1], h: 22, d: 6, tilt: 79, heading: 350, fov: 38 },          // target locked on the rocks: a centred push-in
    { t: tGa2, lon: GMID[0], lat: GMID[1], h: 22, d: 0.5, tilt: 85.5, heading: 6, fov: 38 },               // {pokes}: two rocks in open sea, low
    { t: tEnd0, lon: GMID[0], lat: GMID[1], h: 22, d: 0.48, tilt: 85.5, heading: 10, fov: 38 }];
  const EN = [GA[5], { t: tEnd0 + 0.75, lon: GMID[0], lat: GMID[1], h: 22, d: 2.4, tilt: 79, heading: 340, fov: 40 },   // s110: rise, the rocks held, then recede below
    { t: tEnd1, lon: -171.3, lat: 25.85, h: 0, d: 230, tilt: 55, heading: 298, fov: 40 },                  // NW over open water, Laysan's pale ring passes
    { t: tAt, lon: MIDW[0], lat: MIDW[1], h: 0, d: 110, tilt: 57, heading: 322, fov: 42 },                 // {atall}: Midway's reef ring ahead, centred
    { t: T('onlyreef'), lon: MIDW[0], lat: MIDW[1], h: 0, d: 18, tilt: 59, heading: 28, fov: 42 },        // {onlyreef}: a ring of reef
    { t: ch.t1x + 0.6, lon: MIDW[0], lat: MIDW[1] + 0.002, h: 0, d: 15.2, tilt: 60.5, heading: 31, fov: 42 }];
  // ch5 opens on this flight with ch4's original keys (its EN, verbatim): from {onlyreef} on the camera runs on that path, so the
  // dissolve 435.89-436.19 shows one identical camera (the two paths meet on the {onlyreef} key; slopes there differ by under 0.3 deg/s)
  const EN_CH5 = chainPath([{ t: tEnd0, lon: GMID[0], lat: GMID[1], h: 22, d: 0.48, tilt: 85.5, heading: 10, fov: 38 },
    { t: tEnd1, lon: -171.6, lat: 26.0, h: 0, d: 600, tilt: 42, heading: 300, fov: 40 }, EN[4], EN[5]]);
  const PATH = route([tA0, tCoast, chainPath(A1)], [tCoast, tCent, chainPath(A2)], [tCent, tMauiE, chainPath(A3)], [tMauiE, tPg, pathB],
    [tPg, tCanH, chainPath(PK)], [tCanH, tNi0, chainPath(CN)], [tNi0, tNih, chainPath(NF)], [tNih, tLa0, chainPath(NH)], [tLa0, tD0, chainPath(LA)],
    [tD0, tE0, chainPath(LD)], [tE0, tS0, chainPath(ES)], [tS0, tGa0, chainPath(SS)], [tGa0, tEnd0, chainPath(GA)], [tEnd0, T('onlyreef'), chainPath(EN)],
    [T('onlyreef'), ch.t1x + 0.6, EN_CH5]);
  const cross = (path, a, b, D) => { const up = path(b).d > path(a).d; let lo = a, hi = b; for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if ((path(m).d > D) === up) hi = m; else lo = m; } return (lo + hi) / 2; };
  const tH1 = cross(PATH, A1[3].t, A1[4].t, 60), tH2 = cross(PATH, A1[4].t, A1[5].t, 6), tH3 = cross(PATH, A3[1].t, A3[2].t, 6), tH4 = cross(PATH, A3[1].t, A3[2].t, 90);
  const tH5 = cross(pathB, B[1].t, B[2].t, 100), tH6 = cross(PATH, tRise, PK[2].t, 8), tH7 = cross(PATH, PK[2].t, PK[3].t, 100), tH8 = cross(PATH, PK[3].t, PK[4].t, 85);
  const tH9 = cross(PATH, CN[2].t, NF[1].t, 25), tH10 = NF[1].t - 0.2, tH11 = tLaA - 0.2, tH12 = cross(PATH, ES[1].t, ES[2].t, 3), tH13 = tGa1 - 0.2, tH14 = tEnd1 - 0.2;
  if (dbg) api.log(`[ch4] hand-offs ${[tH1, tH2, tH3, tH4, tH5, tH6, tH7, tH8, tH9, tH10, tH11, tH12, tH13, tH14].map(x => x.toFixed(2)).join(' ')}`);

  // ================================================================ the AGE gauge (local: same corner and plate as ui.gauge)
  const AGEK = [[ch.t0, 0], [T('maui2') - 0.4, 0], [T('maui2') + 0.2, 1.5], [T('oahu2') - 0.33, 1.5], [T('oahu2') + 0.27, 3.5], [T('kauai') - 0.42, 3.5], [T('kauai') + 0.18, 5],
    [T('lower') - 0.6, 5], [T('lower') + 1.5, 6.4], [T('seven') - 0.55, 6.4], [T('seven') + 0.1, 7.2], [T('ffs') - 1.4, 7.2], [T('ffs') + 0.05, 12], [tGa0 + 0.6, 12], [T('pokes') - 0.2, 12.6],
    [T('atall') - 0.4, 12.6], [T('atall') + 0.2, 14]];
  const ageAt = monotone(AGEK), AGE_MAX = 14;
  const GWIN = [[ch.t0 + 1.48, T('old') + 1.33], [T('maui2') - 0.77, T('hnl') + 0.65], [T('kauai') - 0.85, T('kauai') + 2.25], [T('lower') - 0.63, T('rock') + 0.4],
    [T('ffs') - 1.63, T('ffs') + 2.17], [tGa0 + 0.17, T('pokes') + 1.07], [T('atall') - 0.83, ch.t1 - 0.3]];
  const gAlpha = (t) => Math.max(0, ...GWIN.map(([a, b]) => env(t, a, b, 0.35, 0.45)));
  const gSlide = (t) => F.clamp((t - GWIN[0][0]) / 0.5);
  const TRW = px(440), gGeo = (ctx, t) => {
    const A = gAlpha(t); if (A <= 0.002) return null;
    const p = gSlide(t), h = px(150), tw = TY.width(ctx, 'AGE', { cap: 64 }), w = px(8) + px(28) + tw + px(64) + TRW + px(46) + px(30);
    const x = px(96) - (1 - E.outExpoN(p)) * (w + px(120)), y = px(96), tx = x + px(36), trX = tx + tw + px(64), trY = y + px(56);
    return { A: A * F.clamp(p * 2), x, y, w, h, tx, trX, trY };
  };
  const avoidGauge = (t) => { const g = gGeo(dummy, t); if (g) ui.avoid({ x: g.x, y: g.y, w: g.w, h: g.h }); };
  scenes.push({ id: 'ch4-age', t0: ch.t0 + 1.4, t1: ch.t1, layer: 60, draw(ctx, lt, t) {
    const g = gGeo(ctx, t); if (!g) return; const { A, x, y, w, h, tx, trX, trY } = g;
    ctx.save(); ctx.globalAlpha *= A;
    ctx.fillStyle = 'rgba(0,0,0,0.28)'; F.round(ctx, x + px(2), y + px(6), w, h, px(6)); ctx.fill();
    ctx.fillStyle = PAL.plate; F.round(ctx, x, y, w, h, px(6)); ctx.fill();
    ctx.fillStyle = PAL.yellow; ctx.fillRect(x, y, px(8), h);
    TY.txt(ctx, 'AGE', tx, y + h / 2 + px(64) / 2, { cap: 64, color: PAL.text, shadow: false });
    ctx.fillStyle = 'rgba(244,246,250,0.22)'; F.round(ctx, trX, trY - px(5), TRW, px(10), px(5)); ctx.fill();
    const cx = trX + TRW + px(22); ctx.strokeStyle = 'rgba(244,246,250,0.75)'; ctx.lineWidth = px(5); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(cx - px(8), trY - px(12)); ctx.lineTo(cx + px(5), trY); ctx.lineTo(cx - px(8), trY + px(12)); ctx.stroke();       // older, onward
    const f = F.clamp(ageAt(t) / AGE_MAX), mx = trX + f * TRW;
    if (mx - trX > px(2)) { ctx.fillStyle = PAL.yellow; F.round(ctx, trX, trY - px(5), mx - trX, px(10), px(5)); ctx.fill(); }
    ctx.fillStyle = PAL.text; ctx.fillRect(trX - px(3), trY - px(17), px(6), px(34));                                                             // NOW tick
    ctx.fillStyle = PAL.ink; ctx.beginPath(); ctx.arc(mx, trY, px(19), 0, 7); ctx.fill();
    ctx.fillStyle = PAL.yellow; ctx.beginPath(); ctx.arc(mx, trY, px(14), 0, 7); ctx.fill();
    TY.txt(ctx, 'NOW', trX - px(3), y + h - px(20), { cap: 50, color: PAL.text, shadow: false });                                              // under the NOW tick
    ctx.restore();
    ui.Q.gauge = true; ui.Q.words += 2; ui.avoid({ x, y, w, h });
  } });
  [[ch.t0 + 1.48, 'age_slide', -16.1], [T('maui2') - 0.4, 'age_slide', -20], [T('oahu2') - 0.33, 'age_slide', -19.2], [T('kauai') - 0.42, 'age_slide', -20],
    [T('seven') - 0.55, 'age_slide', -14.1], [T('atall') - 0.4, 'age_slide', -20]].forEach(c => api.cue(...c));

  // label helper: in on t0 (0.3 s), out by t1; the gauge plate is an obstacle
  const lab = (ctx, s, q, t, t0, t1, o = {}) => { if (!q) return null; const a = F.clamp((t1 - t) / 0.35); if (t < t0 || a <= 0) return null;
    return ui.label(ctx, s, q[0], q[1], Object.assign({ t, p: F.clamp((t - t0) / 0.3), alpha: a, order: ['above', 'above-right', 'above-left', 'right', 'left'] }, o)); };

  // ================================================================ PART A: the Big Island's own coast (bigisland, kilauea_sf, holei)
  const camAt = (t) => camOf(PATH(t));
  const leg = (id, region, t0, t1, o = {}) => { const s = kit.terrainShot(Object.assign({ id, t0, t1, fadeIn: o.fadeIn ?? XF, region, preset: 'today',
    cam: (lt) => (o.cam || camAt)(t0 + lt), state: (lt) => stAt((o.path || PATH)(t0 + lt), t0 + lt, o.st ? o.st(t0 + lt) : {}) }, o.spec || {}));
    if (o.fadeIn !== K.XF) s.uiFrom = t0 + (o.fadeIn ?? XF); scenes.push(o.wrap ? o.wrap(s) : s); return s; };
  // s086-s088 at Hōlei: surf washing against the cliff foot from {coast} on (stronger through {cent}, where the arch stood); the waterline
  // found on the grid at 13 points along 1.2 km of coast. Repeating bursts (two per point, staggered) so the wash keeps moving.
  const WL = { pts: null };
  const waterline = (S) => { if (WL.pts) return WL.pts; const pts = [];
    for (let b = -0.6; b < 0.61; b += 0.1) { const s = offLL(ARCH, b, 68), wet = S.heightAt(s[0], s[1]) < 0.3;      // walk to the waterline (seaward 158 from land, landward from water)
      for (let k = 1; k <= 80; k++) { const q = offLL(s, k * 0.004, wet ? 338 : 158); if ((S.heightAt(q[0], q[1]) < 0.3) !== wet) { pts.push(wet ? offLL(q, 0.004, 158) : q); break; } } }
    return (WL.pts = pts); };
  const foamPuffs = (ctx, t, view) => { const a = env(t, T('coast') - 0.6, s0('s089') + 0.2, 0.4, 0.9) * (0.55 + 0.45 * env(t, T('cent') - 0.6, T('cent') + 2.2, 0.3, 0.9)); if (a <= 0.01) return;
    const pts = waterline(view.S); ctx.save();
    pts.forEach((ll, i) => { const q = view.project(ll[0], ll[1], 1), e = view.project(ll[0] + 0.0004, ll[1], 1); if (!q || !e) return;
      const base = Math.max(px(34), Math.hypot(e[0] - q[0], e[1] - q[1]) * 2.0);
      for (let k = 0; k < 2; k++) { const u = (((t - T('coast')) / 1.25 + i * 0.29 + k * 0.5) % 1 + 1) % 1, r = base * (0.5 + 1.3 * E.out(u)), al = a * Math.pow(1 - u, 1.3) * 0.8;
        const g = ctx.createRadialGradient(q[0], q[1], 0, q[0], q[1], r); g.addColorStop(0, `rgba(250,252,255,${al})`); g.addColorStop(0.55, `rgba(240,246,250,${0.45 * al})`); g.addColorStop(1, 'rgba(240,246,250,0)');
        ctx.save(); ctx.translate(q[0], q[1]); ctx.scale(1, 0.38); ctx.translate(-q[0], -q[1]); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(q[0], q[1], r, 0, 7); ctx.fill(); ctx.restore(); } });
    ctx.restore(); };
  // Hōlei: the sea is deep right off the cliffs (the photos show navy water); the grid's coarse shelf there gave a turquoise lagoon
  const HOLEI_SEA = [[0.008, 0.11, 0.18], [0.005, 0.06, 0.12], [0.003, 0.035, 0.085]];
  leg('ch4-lift', 'bigisland', ch.t0, tH1 + XF, { fadeIn: K.XF });
  leg('ch4-coast', 'kilauea_sf', tH1, tH2 + XF);
  leg('ch4-holei', 'holei', tH2, tH3 + XF, { st: () => ({ waterCols: HOLEI_SEA }), spec: { world(ctx, lt, t, view) { foamPuffs(ctx, t, view); } } });
  leg('ch4-leave', 'kilauea_sf', tH3, tH4 + XF);
  api.cue(T('cent') - 0.62, 'wave_wash', -20); api.cue(s0('s089'), 'whoosh_big', -16);
  // {notseen}: the glance (1 s) down the drained south flank into the dark of the Hawaiian Deep, no text; it covers the first hand-off
  const tGl0 = T('notseen') - 0.12, tGl1 = T('notseen') + 0.98;
  scenes.push(kit.terrainShot({ id: 'ch4-glance', t0: tGl0, t1: tGl1, layer: 1, fadeIn: 0.12, fadeOut: 0.16, region: 'bigisland', preset: 'drained',
    cam: (lt) => camOf({ lon: -155.20, lat: 19.00, h: -4500, d: 38 - 3.5 * lt, tilt: 70, heading: 345 - 2 * lt, fov: 40 }),       // up the drowned flank to today's coast
    state: () => ({ level: -9000, waterCols: DEEPW, sun: [200, 30], set: { tubAmt: 0.4, oldLine: 1, lineCol: [1.15, 1.1, 1.0], foamAmt: 0 } }) }));
  api.cue(T('notseen') - 0.3, 'amb_deep_pressure', -18);
  // s087: the two dated NPS photos in one wipe that lands on {arch}; HŌLEI SEA ARCH on the standing arch's lintel
  const tPh0 = s0('s087') + 0.12, tWipe1 = lead('arch'), tWipe0 = tWipe1 - 0.8, tPh1 = s1('s087') - 0.45;
  const PH = {};
  const coverCrop = (img, s, fx, fy) => { const w = Math.round(W * s), h = Math.round(H * s), c = kit.P.cv(w, h), g = c.getContext('2d'), k = Math.max(w / img.width, h / img.height);
    const dw = img.width * k, dh = img.height * k; g.drawImage(img, F.clamp(w / 2 - fx * dw, w - dw, 0), F.clamp(h / 2 - fy * dh, h - dh, 0), dw, dh); return kit.gradeCanvas(c) || c; };
  try { PH.a = coverCrop(await loadImg('/ep/ep02/img/ch4/holei_2022_before.jpg'), 1.12, 0.42, 0.52); PH.b = coverCrop(await loadImg('/ep/ep02/img/ch4/holei_2026_after.jpg'), 1.12, 0.5, 0.5); }
  catch (e) { api.log('[ch4] Hōlei photos missing: ' + e.message); }
  const kb = (ctx, cv, s, fx, fy) => { const dw = W * s, dh = H * s; ctx.drawImage(cv, fx * W * (1 - s), fy * H * (1 - s), dw, dh); };
  if (PH.a && PH.b) scenes.push({ id: 'ch4-holei-photos', t0: tPh0, t1: tPh1, layer: 1, draw(ctx, lt, t) {
    const A = env(t, tPh0, tPh1, 0.25, 0.3); if (A <= 0) return;
    const sa = F.lerp(1.0, 1.07, pr(t, tPh0, tWipe1, E.linear || (x => x))), sb = F.lerp(1.0, 1.05, pr(t, tWipe0, tPh1, x => x));
    ctx.save(); ctx.globalAlpha *= A;
    const wx = F.lerp(W * 1.15, -W * 0.15, pr(t, tWipe0, tWipe1, E.inOutSine)), fe = W * 0.14;
    if (wx > -fe) kb(ctx, PH.a, sa, 0.40, 0.48);
    if (wx < W + fe) { const c = PH.wc || (PH.wc = kit.P.cv(W, H)), g = c.getContext('2d'); g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, W, H); kb(g, PH.b, sb, 0.5, 0.5);
      g.globalCompositeOperation = 'destination-in'; const lg = g.createLinearGradient(wx - fe, 0, wx + fe, 0); lg.addColorStop(0, 'rgba(0,0,0,0)'); lg.addColorStop(1, 'rgba(0,0,0,1)');
      g.fillStyle = lg; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; ctx.drawImage(c, 0, 0); }
    ctx.restore();
    // the label on the lintel of the standing arch (before photo coordinates, through its Ken Burns), out as the wipe starts
    const la = env(t, tPh0 + 0.25, tWipe0 + 0.1, 0.3, 0.3);
    if (la > 0) { const lx = 0.40 * W * (1 - sa) + 0.385 * W * sa, ly = 0.48 * H * (1 - sa) + 0.335 * H * sa;    // the lintel (before photo frame coords)
      ui.label(ctx, 'HŌLEI SEA ARCH', lx, ly, { t, p: F.clamp((t - (tPh0 + 0.25)) / 0.3), alpha: A * F.clamp((tWipe0 + 0.1 - t) / 0.3), order: ['above', 'above-right', 'above-left'] }); }
  } });

  // ================================================================ PART B: Maui, Oʻahu, the Pali callback, Kauaʻi (mauinui ... waimea)
  // the blur windows never overlap a label (each blur sample draws the label again: ghosts, and ui.label then finds no free slot)
  leg('ch4-maui', 'mauinui', tH4, tH5 + XF, { wrap: (s) => blurred(s, s0('s090') + 0.36, B[2].t - 0.2, 5, 0.45),
    spec: { ui(ctx, lt, t, view) { avoidGauge(t);
      lab(ctx, 'MAUI', view.visible(HALEA[0], HALEA[1], 3100) ? view.project(HALEA[0], HALEA[1], 3150) : null, t, lead('maui2'), s0('s090') + 0.35); } } });
  const oahuUI = (ctx, lt, t, view) => { avoidGauge(t);
    const pa = env(t, T('hnl') - 0.1, tPg + 0.15, 0.2, 0.3), hq = view.project(HNL[0], HNL[1], 40);
    if (pa > 0 && hq && view.visible(HNL[0], HNL[1], 40)) { ui.avoid({ x: hq[0] - px(34), y: hq[1] - px(34), w: px(68), h: px(68) }); ctx.save(); ctx.globalAlpha *= pa; ui.pin(ctx, hq[0], hq[1], { r: 15, t: t - T('hnl'), color: PAL.text, p: 1 }); ctx.restore(); }
    lab(ctx, 'OʻAHU', gp(view, [-157.80, 21.40], 120), t, lead('oahu2'), T('hnl') + 0.55, { order: ['above', 'above-left', 'above-right', 'left', 'right'] }); };
  leg('ch4-oahu', 'oahu_nuuanu', tH5, tPg + 0.2, { cam: (t) => camOf(pathB(t)), path: pathB, spec: { ui: oahuUI } });
  // the Pali callback (tourist appearance 3 of 4): ch2's lookout framing; he stands behind the paper wall holding his hat on with both
  // hands; the gust (x105) leans him in, yanks the hat up (the arms stretch with it) and lifts him onto his toes; he lands, the hat stays
  const card = { wall: wallCard(kit) };
  try { const TOUR = await kit.paper('tourist'); card.tour = await touristHold(kit, TOUR); } catch (e) { api.log('[ch4] tourist card: ' + e.message); }
  const DREF = 1.004, gust = (t) => pr(t, tGu - 0.05, tGu + 0.35) * (1 - pr(t, tGu + 1.45, tGu + 2.05));
  const yank = (t) => { const u = (t - (tGu + 0.62)) / 0.62; return u > 0 && u < 1 ? Math.sin(Math.PI * u) * (1 - 0.25 * u) : 0; };
  const fold = (t) => pr(t, tRise + 0.15, tRise + 0.55, E.in);
  const wallAt = (view, t) => { const fo = fold(t); if (fo >= 1) return null;
    const S = view.S, cam = S.cam.position, hL = gh(view, ...LOOKOUT), W0 = offLL(LOOKOUT, 0.04, 42), E1 = offLL(W0, 0.17, 312), E2 = offLL(W0, 0.30, 132);
    const end = (ll) => { const q = view.project(ll[0], ll[1], hL); if (!q) return null; const k = DREF / S.xyz(ll[0], ll[1], hL).distanceTo(cam); return [q, 0.40 * H * 0.36 * F.clamp(k, 0, 1.6) * (1 - fo)]; };
    const A = end(E1), Bq = end(E2); if (!A || !Bq) return null;
    return { A, B: Bq, quad: [[A[0][0], A[0][1] - A[1]], [Bq[0][0], Bq[0][1] - Bq[1]], Bq[0], A[0]] }; };
  const paliShot = kit.terrainShot({ id: 'ch4-pali', t0: tPg, t1: tH6 + XF, fadeIn: 0.2, region: 'pali', preset: 'today',
    cam: (lt) => camAt(tPg + lt),
    state: (lt) => { const t = tPg + lt, c = PATH(t), q = pr(t, tRise, tRise + 1.0);
      const st = { sun: t < tSlid ? [75, 55] : SUN(t), set: { foamAmt: 0.25 * (1 - q), waveAmt: F.lerp(1, 0.4, q), glintAmt: F.lerp(0.12, 0.05, q) } }; const wc = farWater(c.d); if (wc) st.waterCols = wc;
      const ex = EXPO(t); if (Math.abs(ex - 1) > 1e-3) st.post = { exposure: ex }; return st; },
    world(ctx, lt, t, view) {
      const S = view.S, hL = gh(view, ...LOOKOUT), b = view.project(LOOKOUT[0], LOOKOUT[1], hL); if (!b) return;
      const s = F.clamp(DREF / camDist(view, LOOKOUT[0], LOOKOUT[1], hL), 0, 1.4), hPx = H * 0.36 * s, fo = fold(t);
      const wall = wallAt(view, t);
      if (wall) { const { A, B: Bq } = wall;
        ctx.save(); ctx.globalAlpha = 0.3; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.moveTo(A[0][0], A[0][1] - 2); ctx.lineTo(Bq[0][0], Bq[0][1] - 2);
        ctx.lineTo(Bq[0][0] + Bq[1] * 0.25, Bq[0][1] + Bq[1] * 0.09); ctx.lineTo(A[0][0] + A[1] * 0.25, A[0][1] + A[1] * 0.09); ctx.closePath(); ctx.fill(); ctx.restore();
        kit.drawQuad(ctx, card.wall.img, wall.quad, 10, 1);
        ctx.save(); ctx.fillStyle = '#E9E0CC'; ctx.fillRect(Bq[0][0] - 3, Bq[0][1] - Bq[1], Math.max(5, Bq[1] * 0.05), Bq[1]); ctx.restore(); }
      const TOUR = card.tour; if (!TOUR) return;
      const gu = gust(t), yk = yank(t), land = (() => { const u = (t - (tGu + 1.24)) / 0.22; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; })();
      const lift = s * (4 * gu * Math.abs(Math.sin(t * 21)) + 30 * yk), hop = s * 22 * Math.pow(yk, 1.5);
      const brim = { rot: gu * (0.06 * Math.sin(t * 29) + 0.035 * Math.sin(t * 47 + 1.3)), off: [gu * 1.5 * s * Math.sin(t * 37), -lift] };
      kit.drawCutout(ctx, view, TOUR, { lon: LOOKOUT[0], lat: LOOKOUT[1], hPx, hinge: fo, alpha: F.clamp((t - tPg) / 0.2), lean: 0.05 + 0.3 * gu - 0.1 * yk, wobble: 0.015 + 0.025 * gu, t, seed: 3, hop, squash: 0.07 * land,
        parts: { hat: brim, arms: { off: [brim.off[0] * 0.6, -lift * 0.92] } } });
    } });
  scenes.push(paliShot); api.cue(tGu, 'wind_gust', -20);
  // the rise over the cliff (oahu_nuuanu), the channel (main_chain), Kauaʻi and Waimea Canyon (waimea): rain squall and water threads
  leg('ch4-oahu-up', 'oahu_nuuanu', tH6, tH7 + XF);
  leg('ch4-channel', 'main_chain', tH7, tH8 + XF, { wrap: (s) => blurred(s, tH7, tH8 + XF, 5, 0.45) });
  const RAIN = Array.from({ length: 170 }, (_, i) => [hash(i, 1), hash(i, 2), 0.5 + hash(i, 3), 0.6 + 0.8 * hash(i, 4)]);
  const rainA = (t) => Math.max(0.38 * env(t, T('kauai') + 0.3, tNi0, 0.8, 0.4), env(t, tRain - 0.15, tNi0, 0.6, 0.4));
  const rain = (ctx, t) => { const a = rainA(t); if (a <= 0) return;
    ctx.save(); const vg = ctx.createLinearGradient(0, 0, 0, H * 0.75); vg.addColorStop(0, `rgba(58,66,80,${0.32 * a})`); vg.addColorStop(1, 'rgba(58,66,80,0)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
    const sw = F.clamp((t - (tRain - 0.2)) / 1.4), sx = F.lerp(W * 1.2, -W * 0.4, sw);                                           // the squall front sweeps over the rim
    if (sw > 0 && sw < 1) { const g = ctx.createLinearGradient(sx - W * 0.3, 0, sx + W * 0.3, 0); g.addColorStop(0, 'rgba(150,160,175,0)'); g.addColorStop(0.5, `rgba(150,160,175,${0.28 * a})`); g.addColorStop(1, 'rgba(150,160,175,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
    ctx.lineCap = 'round';
    for (const [x0, y0, sp, ln] of RAIN) { const L = px(46) * ln, y = ((y0 + t * 1.9 * sp) % 1.15) * H - L, x = ((x0 - t * 0.13 * sp) % 1 + 1) % 1 * W;
      ctx.strokeStyle = `rgba(222,230,242,${0.32 * a * (0.5 + 0.5 * sp)})`; ctx.lineWidth = px(2.2); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - L * 0.18, y + L); ctx.stroke(); }
    ctx.restore(); };
  // water threads: steepest-descent lines from rim seeds down the gullies (computed once on the waimea grid)
  const THR = { lines: null };
  const threads = (S) => { if (THR.lines) return THR.lines; THR.lines = [];
    try { const g = heightGrid(S, [-159.70, 21.99, -159.62, 22.10], 2), at = (i, j) => g.h[j * g.nx + i], R = F.rng(23);
      const ll = (i, j) => [g.bb[0] + i / (g.nx - 1) * (g.bb[2] - g.bb[0]), g.bb[1] + j / (g.ny - 1) * (g.bb[3] - g.bb[1])];
      for (let s = 0; s < 400 && THR.lines.length < 26; s++) { let i = 2 + Math.floor(R() * (g.nx - 4)), j = 2 + Math.floor(R() * (g.ny - 4)); const h0 = at(i, j);
        if (h0 < 650 || h0 > 1050) continue; const line = [ll(i, j)];
        for (let k = 0; k < 300; k++) { let bi = i, bj = j, bh = at(i, j); for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) { const ni = i + di, nj = j + dj; if (ni < 0 || nj < 0 || ni >= g.nx || nj >= g.ny) continue; if (at(ni, nj) < bh) { bh = at(ni, nj); bi = ni; bj = nj; } }
          if (bi === i && bj === j) break; i = bi; j = bj; if (k % 2) line.push(ll(i, j)); }
        if (line.length > 12 && h0 - at(i, j) > 260) THR.lines.push({ pts: line, d: R() * 0.6 }); } } catch (e) { api.log('[ch4] threads: ' + e.message); }
    return THR.lines; };
  const drawThreads = (ctx, t, view) => { const a = env(t, T('canyons') + 0.3, tNi0 + 0.1, 0.4, 0.3); if (a <= 0) return;
    ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const L of threads(view.S)) { const p = pr(t, T('canyons') + 0.3 + L.d, T('canyons') + 1.6 + L.d, E.out), n = Math.max(2, Math.floor(L.pts.length * p));
      const q = []; for (let k = 0; k < n; k++) { const [lo, la] = L.pts[k], r = view.project(lo, la, view.S.heightAt(lo, la) + 4); if (r) q.push(r); }
      if (q.length < 2) continue; ctx.strokeStyle = `rgba(20,30,40,${0.35 * a})`; ctx.lineWidth = px(5); ctx.beginPath(); q.forEach((r, k) => k ? ctx.lineTo(...r) : ctx.moveTo(...r)); ctx.stroke();
      ctx.strokeStyle = `rgba(226,240,250,${0.85 * a})`; ctx.lineWidth = px(2.6); ctx.stroke(); }
    ctx.restore(); };
  leg('ch4-kauai', 'waimea', tH8, tH9 + XF, { spec: {
    world(ctx, lt, t, view) { drawThreads(ctx, t, view); rain(ctx, t); },
    ui(ctx, lt, t, view) { avoidGauge(t); lab(ctx, 'KAUAʻI', gp(view, KAU, 150), t, lead('kauai'), T('kauai') + 2.15); } } });

  // ================================================================ PART C: Nihoa (main_chain -> nihoa)
  leg('ch4-nw', 'main_chain', tH9, tH10 + XF, { wrap: (s) => blurred(s, tH9, tH10 + XF, 5, 0.45) });
  api.cue(T('lower') - 0.23, 'whoosh_big', -15);
  const BIRDS = Array.from({ length: 9 }, (_, i) => [hash(i, 7), 0.12 + 0.4 * hash(i, 8), 0.6 + 0.8 * hash(i, 9), hash(i, 10) * 6.28]);
  const nihoaShot = leg('ch4-nihoa', 'nihoa', tH10, tH11 + XF, { spec: {
    world(ctx, lt, t, view) {   // {nobody}: seabird specks drifting over the empty rock (no other marks on Nihoa: there are burials)
      const a = env(t, s0('s099') + 0.2, tLa0 + 0.3, 0.6, 0.5); if (a <= 0) return;
      ctx.save(); ctx.strokeStyle = `rgba(36,38,44,${0.8 * a})`; ctx.lineWidth = px(2.4); ctx.lineCap = 'round';
      for (const [x0, y0, sp, ph] of BIRDS) { const x = ((x0 + (t - s0('s099')) * 0.035 * sp) % 1) * W, y = y0 * H + 6 * Math.sin(t * 1.3 + ph), fl = Math.sin(t * 9 * sp + ph), s = px(7 + 4 * sp);
        ctx.beginPath(); ctx.moveTo(x - s, y - s * 0.3 * fl); ctx.quadraticCurveTo(x - s * 0.4, y - s * 0.45, x, y); ctx.quadraticCurveTo(x + s * 0.4, y - s * 0.45, x + s, y - s * 0.3 * fl); ctx.stroke(); }
      ctx.restore(); },
    ui(ctx, lt, t, view) { avoidGauge(t);
      lab(ctx, 'NIHOA', gp(view, [NIH[0] - 0.004, NIH[1] + 0.0015], 60), t, lead('nihoa'), T('seven') + 0.35, { order: ['above-left', 'left', 'above', 'below', 'above-right'] });   // left side: above-right ran under the right-anchored 7 MILLION YEARS block (r7t2 10926)
      // HERO NUMBER #4: ABOUT / 7 MILLION YEARS lands with the age marker on {seven} (punch on the impact), out before s095
      const kp = F.clamp((t - (tSeven - 0.05)) / 0.35), kout = pr(t, s1('s094') - 0.75, s1('s094') - 0.3);
      if (kp > 0 && kout < 1) {
        const nOpt = { cap: 150, to: 7, unit: 'MILLION YEARS', unitCap: 84 }, m = ui.number(dummy, 7, 0, 0, Object.assign({ measure: true }, nOpt));
        const punch = 1 + 0.07 * Math.sin(F.clamp((t - (T('seven') - 0.08)) / 0.2) * Math.PI);
        const nq = gp(view, NIH, 40); if (nq) ui.avoid({ x: nq[0] - px(160), y: nq[1] - px(70), w: px(320), h: px(140) });
        ctx.save();
        const box = ui.block(ctx, [{ text: 'ABOUT', role: 'kicker', cap: 52, qualifier: true }], W - px(96), px(96), { anchor: 'right', p: kp, out: kout, extra: { w: m.w, h: m.h + px(10) }, bar: PAL.yellow, clear: 24,
          at: [{ x: W - px(96), y: px(96), anchor: 'right' }, { x: W - px(96), y: px(300), anchor: 'right' }, { x: W / 2, y: px(470), anchor: 'center' }] });
        if (box) { ctx.translate(box.x + box.w / 2, box.y + box.h / 2); ctx.scale(punch, punch); ctx.translate(-(box.x + box.w / 2), -(box.y + box.h / 2));
          ui.number(ctx, 7, box.inner.x, box.inner.y + m.h, Object.assign({ alpha: F.clamp(kp * 2) * (1 - E.in(kout)) }, nOpt)); }
        ctx.restore(); }
    } } });
  api.cue(T('seven') - 0.08, 'impact_short', -14); api.cue(T('outhere2') - 0.17, 'whoosh_soft', -18);

  // ================================================================ PART D: Lalo (laperouse, lalo_2018_before / _after)
  const LP = {};
  const lapMask = (S) => { if (!LP.m) { try { const g = heightGrid(S, [-166.2655, 23.7655, -166.2565, 23.7725], 1), m = new Uint8Array(g.nx * g.ny);
      for (let k = 0; k < m.length; k++) m[k] = g.h[k] > 2 ? 1 : 0; LP.m = { tex: kit.maskTexture(g, { r: m }), bb: g.bb }; } catch (e) { api.log('[ch4] pinnacle mask: ' + e.message); LP.m = { none: true }; } } return LP.m.none ? null : LP.m; };
  const lapRing = async () => { if (!LP.done) { LP.done = 1; try { const r = await kit.island({ region: 'laperouse', bbox: [-166.2655, 23.7655, -166.2565, 23.7725], level: 2, seeds: [LAPER], step: 1 }); LP.rings = r.rings; }
    catch (e) { api.log('[ch4] pinnacle ring: ' + e.message); LP.rings = []; } } };
  const laloShot = kit.terrainShot({ id: 'ch4-lalo', t0: tH11, t1: tH12 + XF, fadeIn: XF, region: 'laperouse', preset: 'today',
    cam: (lt) => camAt(tH11 + lt), state: (lt) => stAt(PATH(tH11 + lt), tH11 + lt, { foam: 0.35, water: 'ocean' }),
    mask: (lt, S) => { const t = tH11 + lt, a = env(t, lead('tooth') - 0.05, tE0 + 0.6, 0.3, 0.5); if (a <= 0) return null; const m = lapMask(S); if (!m) return null; heroBright(S); return { tex: m.tex, bb: m.bb, hero: 0.5 * a }; },
    world(ctx, lt, t, view) { heroReset(view.S); },
    ui(ctx, lt, t, view) { avoidGauge(t);
      lab(ctx, 'LALO', view.project(LALO_C[0], LALO_C[1], 30), t, lead('ffs'), T('lalo') + 1.0, { order: ['above', 'above-left', 'above-right'] });
      const oa = env(t, lead('tooth') - 0.05, tE0 + 0.5, 0.3, 0.4);
      if (oa > 0 && LP.rings?.length) for (const r of LP.rings) ui.line(ctx, druns(view, r, 0, 1, 2), { color: PAL.hero, width: 8, alpha: oa, p: pr(t, lead('tooth') - 0.05, lead('tooth') + 0.55) });
      lab(ctx, 'LA PÉROUSE PINNACLE', view.project(LAPER[0], LAPER[1], 40), t, lead('tooth') + 0.1, tE0 + 0.2, { order: ['above', 'above-right', 'above-left', 'right', 'left'], dist: 90 });
    } });
  laloShot.uiFrom = tH11 + XF; scenes.push(blurred(ready(laloShot, lapRing), tH11, tLa1 - 0.3, 5, 0.45));
  // East Island: the BEFORE outline (lalo_2018_before, level 0) for the seal's spot and the regrowth; robust seed (the highest cell nearby)
  const eiPrep = async () => { if (EI.done) return; EI.done = true;
    try { const S = await kit.hub.terrain('lalo_2018_before', 1, {}); const bb = [-166.225, 23.776, -166.196, 23.799], g = heightGrid(S, bb, 1);
      let bk = 0; for (let k = 1; k < g.h.length; k++) if (g.h[k] > g.h[bk]) bk = k;
      const seed = [g.bb[0] + (bk % g.nx) / (g.nx - 1) * (g.bb[2] - g.bb[0]), g.bb[1] + Math.floor(bk / g.nx) / (g.ny - 1) * (g.bb[3] - g.bb[1])];
      const r = await kit.island({ region: 'lalo_2018_before', bbox: bb, level: 0.3, seeds: [seed], step: 1 });
      EI.ring = r.rings.sort((a, b) => b.length - a.length)[0] || null; if (EI.ring) EI.c = centroid(EI.ring);
      if (EI.ring) { const c = EI.c, cl = Math.cos(c[1] * D2R), P = EI.ring.map(q => [(q[0] - c[0]) * KM * cl, (q[1] - c[1]) * KM]); let sxx = 0, syy = 0, sxy = 0;   // the long axis
        for (const [x, y] of P) { sxx += x * x; syy += y * y; sxy += x * y; } const th = 0.5 * Math.atan2(2 * sxy, sxx - syy);
        EI.brg = (90 - th / D2R + 360) % 360; EI.half = Math.max(0.05, ...P.map(([x, y]) => Math.abs(x * Math.cos(th) + y * Math.sin(th)))); } if (dbg) api.log(`[ch4] East Island ${EI.c.map(v => v.toFixed(4))} area ${r.areaKm2?.toFixed?.(3)} km2, ${EI.ring?.length} pts, axis ${EI.brg.toFixed(0)} deg, half ${EI.half.toFixed(3)} km`);
    } catch (e) { api.log('[ch4] East Island ring: ' + e.message); } };
  const SEAL = {}; try { SEAL.a = await kit.paper('seal'); SEAL.p = await kit.paper('seal_pup'); } catch (e) { api.log('[ch4] seal cut-outs: ' + e.message); }
  // seal sizes are world-fixed (EDREF / distance) and the cameras come close: an adult at 0.25-0.3 km reads 35-45 % of frame height (PLAYBOOK_craft: figures 35-40 % or more)
  const EDREF = 0.62, SW = 0.24, sealScale = (view, ll) => F.clamp(EDREF / camDist(view, ll[0], ll[1], 0.5), 0, 3.5);
  // a lighter, tighter contact shadow for the big seals on white sand (the kit's full-width one read as a grey smear at 40 % height, r7t)
  const SOFT = { contact: false, shadowA: 0.12 };
  const softContact = (ctx, view, ll, hm, wPx, a = 1) => { const b0 = view.project(ll[0], ll[1], hm); if (!b0 || a <= 0.01) return; const r = wPx * 0.4, b = [b0[0], b0[1] + wPx * (SEAL.a ? SEAL.a.h / SEAL.a.w : 0.41) * 0.1];   // under the belly (the cut's sink)
    const g = ctx.createRadialGradient(b[0], b[1], 0, b[0], b[1], r); g.addColorStop(0, `rgba(40,34,28,${0.34 * a})`); g.addColorStop(0.6, `rgba(40,34,28,${0.14 * a})`); g.addColorStop(1, 'rgba(40,34,28,0)');
    ctx.save(); ctx.translate(b[0], b[1]); ctx.scale(1, 0.13); ctx.translate(-b[0], -b[1]); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(b[0], b[1], r, 0, 7); ctx.fill(); ctx.restore(); };
  // dbg: the measured screen height of each seal as drawn (fraction of H; vis = the part above the waterline for a swimming one)
  const sealLog = (tag, t, r, wl) => { if (dbg && r) api.log(`[ch4] seal f=${Math.round(t * 30)} ${tag} h=${(r.h / H).toFixed(3)}${wl != null ? ` vis=${(Math.max(0, wl - r.top) / H).toFixed(3)}` : ''} x=${(r.x / W).toFixed(2)}`); return r; };
  // s103-s104 on the sand: the seal pops up on paper_tap, the pup shuffles in on {pups}, {left} the head lifts toward the camera; both
  // shrink with distance as the camera pulls wide for the storm and are gone before it comes back (nobody is on the beach at {away})
  // the gust at s105: both fold flat and fade as the camera starts to rise (gone before they could read small)
  const sealsBefore = (ctx, t, view) => {
    if (!SEAL.a || t < tTap || t > tS0 + 0.35) return; const fa = 1 - pr(t, tS0 - 0.05, tS0 + 0.3), fold = pr(t, tS0 - 0.2, tS0 + 0.15, E.inSine);
    const sp = SPOT.sp, s = sealScale(view, sp), pp = SPOT.pup;   // the pup along the sand, clear of the adult
    const pupT = F.clamp((t - (lead('pups') - 0.1)) / 0.9), lift = pr(t, lead('left') - 0.05, lead('left') + 0.45, E.outBack);
    if (pupT > 0 && SEAL.p) { const shuffle = Math.abs(Math.sin(pupT * Math.PI * 4)) * (1 - pupT);
      sealLog('pup', t, kit.drawCutout(ctx, view, SEAL.p, { lon: pp[0], lat: pp[1], hm: 0.6, wPx: W * 0.12 * sealScale(view, pp), alpha: fa * F.clamp(pupT * 4), hinge: fold, hop: px(8) * shuffle * s, squash: 0.05 * shuffle, lean: 0.02 * Math.sin(t * 9) * (1 - pupT), t, seed: 5, wobble: 0.01 })); }
    softContact(ctx, view, sp, 0.6, W * SW * s, fa * (1 - fold) * F.clamp((t - tTap) / 0.3));
    sealLog('adult', t, kit.drawCutout(ctx, view, SEAL.a, { ...SOFT, lon: sp[0], lat: sp[1], hm: 0.6, wPx: W * SW * s, ...(t < tTap + 0.6 ? { pop: F.clamp((t - tTap) / 0.45) } : { hinge: fold }), alpha: fa, lean: -0.11 * lift, turn: 0.1 * lift, t, seed: 2, wobble: 0.006 }));
  };
  // the storm (s105): tiles of the cloud disc laid on a plane 8 km up, centre on a 22.5 deg track, closest (just west of the atoll) on {shoals}
  const STORM = { tiles: null }, SR = 300, tCl = T('shoals'), sV = 110;
  const stormC = (t) => offLL([-166.445, 23.75], sV * (t - tCl), 22.5);
  const drawStorm = (ctx, t, view) => { const a = env(t, tHur - 1.1, tS2 + 0.9, 0.5, 0.8); if (a <= 0) return;
    const tiles = STORM.tiles || (STORM.tiles = stormTiles(kit)), C = stormC(t), th = 0.35 * (t - tCl);
    const P = (u, v) => { const x = (u * 2 - 1) * SR, y = (1 - v * 2) * SR, xr = x * Math.cos(th) - y * Math.sin(th), yr = x * Math.sin(th) + y * Math.cos(th);
      const ll = [C[0] + xr / (KM * Math.cos(C[1] * D2R)), C[1] + yr / KM]; return view.project(ll[0], ll[1], 8000); };
    const cv = STORM.cv || (STORM.cv = kit.P.cv(W, H)), g = cv.getContext('2d'); let n = 0;
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    for (const tl of tiles) { const q = [P(tl.u0, tl.v0), P(tl.u1, tl.v0), P(tl.u1, tl.v1), P(tl.u0, tl.v1)]; if (q.some(p => !p)) continue;
      const xs = q.map(p => p[0]), ys = q.map(p => p[1]); if (Math.max(...xs) < 0 || Math.min(...xs) > W || Math.max(...ys) < 0 || Math.min(...ys) > H) continue;
      if (Math.max(...xs) - Math.min(...xs) > W * 3) continue; kit.drawQuad(g, tl.img, q, 2, 1); n++; }
    if (!n) return; ctx.save(); ctx.globalAlpha *= a * 0.55; ctx.globalCompositeOperation = 'screen'; ctx.drawImage(cv, 0, 0); ctx.restore(); };   // 0.55: the eye frame read luma 153 at full strength (film max 130)
  const eastState = (t) => stAt(PATH(t), t, { foam: 0.35, water: 'ocean' });
  const eastShot = leg('ch4-east', 'lalo_2018_before', tH12, tH13 + XF, { st: () => ({ foam: 0.35, water: 'ocean' }), spec: {
    world(ctx, lt, t, view) { sealsBefore(ctx, t, view); drawStorm(ctx, t, view); },
    ui(ctx, lt, t, view) { avoidGauge(t);
      if (t < tS0 && SEAL.a && t > tTap) { const sp = SPOT.sp, q = view.project(sp[0], sp[1], 0.6), w = W * SW * sealScale(view, sp); if (q) ui.avoid({ x: q[0] - w / 2, y: q[1] - w * 0.45, w, h: w * 0.48 }); }
      lab(ctx, 'EAST ISLAND', view.project(EI.c[0], EI.c[1], 3), t, lead('east'), tTap + 0.1, { order: ['above', 'above-left', 'above-right'] }); } } });
  scenes.splice(scenes.indexOf(eastShot), 1, ready(eastShot, eiPrep));
  api.cue(tTap, 'paper_tap', -22); api.cue(tHur - 0.9, 'storm_pass', -14);
  // {away}: the AFTER stage (13 Oct 2018) with the same camera and light, revealed behind a wave front that washes over the sand (the two
  // stages differ only inside the island's focus circle, so the reveal is full-frame); then the gag and the regrowth on top of it
  const AFT = kit.terrainShot({ id: 'ch4-east-after', t0: tFr0, t1: tH13 + XF, region: 'lalo_2018_after', preset: 'today',
    cam: (lt) => camAt(tFr0 + lt), state: (lt) => eastState(tFr0 + lt), world(ctx, lt, t, view) { AFT.view = view; } });
  const OFF = {}, tRg0 = s0('s107') - 0.2, tRg1 = T('sandback') + 1.3;
  const ringScreen = (view, k) => { if (!EI.ring) return null; const c = EI.c, pts = [];
    for (const p of EI.ring) { const q = view.project(c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k, 0.4); if (!q) return null; pts.push(q); } return pts; };
  const polyFill = (g, pts) => { g.beginPath(); pts.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.closePath(); g.fill(); };
  const sealSpots = () => SPOT;
  // a seal in the water: drawn on a scratch canvas and cut at its waterline (dy px below the base point), a foam ring where it breaks the surface
  const wetSeal = (ctx, view, cut, o, wl) => { const c = OFF.s || (OFF.s = kit.P.cv(W, H)), g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H);
    const r = kit.drawCutout(g, view, cut, Object.assign({ shadow: false, contact: false }, o)); if (!r) return null;
    g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000'; g.fillRect(0, wl, W, H - wl); g.globalCompositeOperation = 'source-over';
    ctx.drawImage(c, 0, 0);
    foam(ctx, r.x, wl, r.w * 0.62, o.t, 1); return r; };
  // where a body breaks the surface: a soft white wash on the waterline and two ripples that spread and fade (k: strength 0..1)
  const foam = (ctx, x, y, fw, t, k) => { if (k <= 0.01) return; ctx.save();
    const g = ctx.createRadialGradient(x, y, 0, x, y, fw * 0.55); g.addColorStop(0, `rgba(240,248,250,${0.42 * k})`); g.addColorStop(0.7, `rgba(240,248,250,${0.18 * k})`); g.addColorStop(1, 'rgba(240,248,250,0)');
    ctx.translate(x, y); ctx.scale(1, 0.12); ctx.translate(-x, -y); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, fw * 0.55, 0, 7); ctx.fill(); ctx.restore();
    ctx.save(); ctx.lineWidth = px(2.5);
    for (let i = 0; i < 2; i++) { const u = ((t * 0.7 + i * 0.5) % 1 + 1) % 1; ctx.strokeStyle = `rgba(240,248,250,${0.5 * (1 - u) * k})`;
      ctx.beginPath(); ctx.ellipse(x, y, fw * (0.5 + 0.3 * u), fw * (0.06 + 0.035 * u), 0, -0.15, Math.PI + 0.15, false); ctx.stroke(); }   // the front arc only (the back one is behind the body)
    ctx.restore(); };
  scenes.push(ready({ id: 'ch4-east-after', t0: tFr0, t1: tH13 + XF, layer: 1, fadeOut: XF, async draw(ctx, lt, t, api) {
    const c = OFF.a || (OFF.a = kit.P.cv(W, H)), g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, W, H);
    await AFT.draw(g, t - tFr0, t, api); const view = AFT.view; if (!view) return;
    const wx = F.lerp(W * 1.1, -W * 0.25, pr(t, tFr0, tFr1, E.inOutSine)), fe = W * 0.12;
    g.globalCompositeOperation = 'destination-in'; const lg = g.createLinearGradient(wx - fe, 0, wx + fe, 0); lg.addColorStop(0, 'rgba(0,0,0,0)'); lg.addColorStop(1, 'rgba(0,0,0,1)'); g.fillStyle = lg; g.fillRect(0, 0, W, H);
    const k = 0.7 * pr(t, tRg0, tRg1, E.inOutSine);                                                    // {sandback}: the regrown sand shows the BEFORE stage
    if (k > 0.02) { const pts = ringScreen(view, k); if (pts) { g.globalCompositeOperation = 'destination-out'; g.fillStyle = 'rgba(0,0,0,0.3)';
      for (const f of [1.03, 1.015, 1.0, 0.985]) { const cx = pts.reduce((a, q) => a + q[0], 0) / pts.length, cy = pts.reduce((a, q) => a + q[1], 0) / pts.length; polyFill(g, pts.map(q => [cx + (q[0] - cx) * f, cy + (q[1] - cy) * f])); } } }
    g.globalCompositeOperation = 'source-over'; ctx.drawImage(c, 0, 0);
    // the wave front's foam over the old sand
    const fa = env(t, tFr0, tFr1 + 0.2, 0.15, 0.35); const isl = ringScreen(view, 1.15);
    // soft foam puffs along a wavy front, only where the front crosses the old island; no clip (a clipped straight band read as a white
    // rectangle on the 390 px sheet, r7 12532)
    if (fa > 0 && isl) { const ys = isl.map(q => q[1]), y0 = Math.min(...ys), y1 = Math.max(...ys), st = px(8), r = px(30);
      const inside = (x, y) => { let c = false; for (let i = 0, j = isl.length - 1; i < isl.length; j = i++) { const a = isl[i], b = isl[j];
        if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
      ctx.save();
      for (let y = y0; y <= y1; y += st) { const x = wx - px(20) + px(18) * Math.sin(y * 0.045 / px(1) + t * 5) + px(8) * Math.sin(y * 0.11 / px(1) - t * 3.1); if (!inside(x, y)) continue;
        const g2 = ctx.createRadialGradient(x, y, 0, x, y, r); g2.addColorStop(0, `rgba(250,252,255,${0.5 * fa})`); g2.addColorStop(0.5, `rgba(250,252,255,${0.22 * fa})`); g2.addColorStop(1, 'rgba(250,252,255,0)');
        ctx.fillStyle = g2; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); }
      ctx.restore(); }
    if (!SEAL.a) return;
    // GAG in the gap: the seal surfaces where its beach was, bobs, looks left, looks right (paper turn), grunts, blinks; it waits while
    // the sand comes back, flops onto it on {seals} (landing squash), and two more haul out beside it
    const S = sealSpots(), sw = view.project(S.water[0], S.water[1], 0), ss = view.project(S.sand[0], S.sand[1], 0.6); if (!sw || !ss) return;
    const hopT = E.inOut(F.clamp((t - (tFlop - 0.3)) / 0.3)), sc = F.lerp(sealScale(view, S.water), sealScale(view, S.sand), hopT), wP = W * SW * sc, bob = Math.sin((t - tSurf) * 4.2) * px(6) * sc;   // the hop shrinks it to the sand's distance
    const turnK = (t) => pr(t, tSurf + 0.62, tSurf + 0.86) - pr(t, tGrunt + 0.28, tGrunt + 0.5);
    const gr = (() => { const u = (t - tGrunt) / 0.32; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; })();
    if (t >= tSurf - 0.05 && t < tFlop) {
      const up = E.outBack(F.clamp((t - (tSurf - 0.05)) / 0.35)), hopU = F.clamp((t - (tFlop - 0.3)) / 0.3), hs = wP * SEAL.a.h / SEAL.a.w, arc = Math.sin(Math.PI * Math.min(1, hopU)) * hs * 0.45;
      const bx = F.lerp(sw[0], ss[0], E.inOut(hopU)), by = F.lerp(sw[1], ss[1], E.inOut(hopU)) - arc;
      const o = { x: bx, y: by + hs * (1 - up) * 0.9 + hs * 0.12 * (1 - hopU) + bob * (1 - hopU), wPx: wP, turn: turnK(t), squash: 0.09 * gr - 0.06 * Math.sin(Math.PI * hopU), lean: -0.05 * gr - 0.12 * Math.sin(Math.PI * hopU), t, seed: 2, wobble: 0.008 };
      // in the water: cut at the waterline with foam; airborne (the hop to the sand): whole, the splash left behind on the water
      if (hopU > 0) foam(ctx, sw[0], sw[1], W * SW * sealScale(view, S.water) * 0.62, t, 1 - hopU);
      const r = hopU <= 0 ? sealLog('swim', t, wetSeal(ctx, view, SEAL.a, o, sw[1]), sw[1]) : hopU < 1 ? sealLog('hop', t, kit.drawCutout(ctx, view, SEAL.a, Object.assign({ shadow: false, contact: false }, o)))
        : sealLog('landed', t, kit.drawCutout(ctx, view, SEAL.a, { lon: S.sand[0], lat: S.sand[1], hm: 0.6, wPx: wP, squash: o.squash, lean: o.lean, t, seed: 2, wobble: 0.004 }));
      const tb = tGrunt + 0.75; if (r && t > tb && t < tb + 0.16 && Math.abs(o.turn) < 0.05) {                      // the blink: lids over both eyes
        const kk = r.h / SEAL.a.h, rot = (o.lean || 0) + (SEAL.a.tilt || 0), cs = Math.cos(rot), sn = Math.sin(rot);
        ctx.save(); ctx.fillStyle = '#6a625b'; for (const [ex, ey] of [[23, 23], [69, 23]]) { const lx = -r.w / 2 + ex * kk, ly = -r.h + ey * kk;
          ctx.beginPath(); ctx.ellipse(r.x + cs * lx - sn * ly, r.y + sn * lx + cs * ly, 10 * kk, 8 * kk * Math.sin(Math.PI * (t - tb) / 0.16), rot, 0, 7); ctx.fill(); } ctx.restore(); }
    }
    if (t >= tFlop) {                                                                                      // landed on the seal_flop cue: the squash starts there
      const land = (() => { const u = (t - tFlop) / 0.25; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; })(), g2 = (() => { const u = (t - (s1('s108') + 0.19)) / 0.3; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; })();
      // the hero has no cast shadow: with the card's sink its base line runs below the tail, and the faint shadow showed there as a hard-edged grey band on the sand (r7t2 12750)
      // two more haul out: s3 behind the hero (from the far water, facing right: its head over the hero's tail end), s2 in front right (from the
      // near water off the bar's end); drawn far to near by screen depth (base y), the hero between them; card heights about 0.42 H (hero), 0.38-0.40 (s2, s3)
      const hero = () => (softContact(ctx, view, S.sand, 0.6, W * SW * sealScale(view, S.sand)), sealLog('hero', t, kit.drawCutout(ctx, view, SEAL.a, { ...SOFT, shadow: false, lon: S.sand[0], lat: S.sand[1], hm: 0.6, wPx: W * SW * sealScale(view, S.sand), squash: 0.12 * land + 0.07 * g2, lean: -0.06 * g2, t, seed: 2, wobble: 0.004 })));
      // each comes out of the water (s2 off the bar's near end, s3 off its far side) with three humps (a paper bounce), world-placed so its size follows its depth
      // the waterline cut sits at the belly line (0.14 h above the base: seal.png's belly with PAPER sink 0.12), so a seal still in the water never hovers over it (r7mot 12763-12766)
      // s2 humps in dry from fully off-frame right: its water lies past the frame edge, and a waterline cut over the visible sand bar read as sunk into the sand (r7t2 12750-12760)
      const ext = [[S.s3, 0.97, tFlop + 0.75, 9, EIBRG - 90, 0.09], [S.s2, 0.9, tFlop + 0.35, 7, EIBRG, 0.13]].map(([ll, sz, t0, seed, out, dist]) => {
        const u = F.clamp((t - t0) / 0.8), p = offLL(ll, dist * (1 - E.out(u)), out); const q = view.project(p[0], p[1], 0.4); return { p, sz, u, seed, dd: q ? q[1] : -1e9 }; });
      const dh = ss[1]; let drawn = false;
      for (const { p, sz, u, seed, dd } of ext.sort((a, b) => a.dd - b.dd)) { if (!drawn && dd > dh) { hero(); drawn = true; }
        if (u <= 0) continue; const w2 = W * SW * sz * sealScale(view, p), h2 = w2 * SEAL.a.h / SEAL.a.w, bump = Math.abs(Math.sin(Math.PI * 3 * u)) * (1 - u);
        const oo = { wPx: w2, alpha: F.clamp(u * 40), squash: -0.05 * bump, flip: seed === 9, t, seed, wobble: 0.004 + 0.01 * (1 - u) };
        if (u < 0.4 && seed === 9) { const q = view.project(p[0], p[1], 0.4); if (q) sealLog('s' + seed, t, wetSeal(ctx, view, SEAL.a, Object.assign(oo, { x: q[0], y: q[1] + h2 * (0.2 * (1 - u / 0.4) + 0.65 * (1 - E.outBack(F.clamp(u / 0.18)))) }), q[1] - 0.14 * h2), q[1]); }   // still in the water off the bar's end: rises through the waterline (no alpha ghost)
        else { softContact(ctx, view, p, 0.4, w2, oo.alpha); sealLog('s' + seed, t, kit.drawCutout(ctx, view, SEAL.a, Object.assign(oo, SOFT, { lon: p[0], lat: p[1], hm: 0.4, hop: h2 * 0.12 * bump }))); } }
      if (!drawn) hero();
    }
  } }, eiPrep));
  api.cue(tAway, 'sand_wash', -16); api.cue(tSurf - 0.12, 'seal_surface', -18); api.cue(tGrunt, 'monk_seal_grunt', -18); api.cue(tFlop, 'seal_flop', -19); api.cue(s1('s108') + 0.19, 'monk_seal_grunt', -20);

  // ================================================================ PART E: Pūhāhonu, the open chain, Midway (gardner -> midway)
  const ROCKS = [{ ll: GARD, hm: 52, card: rockCard(kit, 31, 760, 520, 0.2), wf: 0.62 }, { ll: offLL(GARD, 0.11, 228), hm: 18, card: rockCard(kit, 47, 420, 330, 0.22), wf: 0.85 }];
  const drawRocks = (ctx, t, view) => {
    for (const R of ROCKS.slice().sort((a, b) => camDist(view, b.ll[0], b.ll[1], 0) - camDist(view, a.ll[0], a.ll[1], 0))) {
      const b = view.project(R.ll[0], R.ll[1], 0), tp = view.project(R.ll[0], R.ll[1], R.hm); if (!b || !tp) continue;
      const hPx = Math.hypot(tp[0] - b[0], tp[1] - b[1]); if (hPx < 2) continue; const wPx = hPx * R.card.w / R.card.h;
      ctx.save(); for (let k = 0; k < 2; k++) { const u = ((t * 0.55 + k * 0.5) % 1); ctx.strokeStyle = `rgba(246,250,252,${0.7 * (1 - u)})`; ctx.lineWidth = Math.max(1.5, px(3.5) * (1 - u));
        ctx.beginPath(); ctx.ellipse(b[0], b[1], wPx * (0.55 + 0.5 * u), wPx * (0.09 + 0.08 * u), 0, 0, 7); ctx.stroke(); } ctx.restore();
      kit.drawCutout(ctx, view, R.card, { x: b[0], y: b[1], hPx, base: false, shadow: false, contact: true, t, seed: 4, wobble: 0.003 });
      R.top = [tp[0], tp[1]];
    } };
  leg('ch4-gardner', 'gardner', tH13, tH14 + XF, { st: () => ({ water: 'turq' }), wrap: (s) => blurred(blurred(s, tH13, tGa2 - 0.6, 5, 0.45), tEnd0 + 0.62, tH14 + XF, 5, 0.45), spec: {
    world(ctx, lt, t, view) { if (t > tGa1 - 0.4) drawRocks(ctx, t, view); },
    ui(ctx, lt, t, view) { avoidGauge(t); const r = ROCKS[0]; if (t > tGa2 - 0.2 && r.top) { const pts = [r.top, view.project(r.ll[0], r.ll[1], 0), ROCKS[1].top].filter(Boolean); if (pts.length > 1) ui.avoid(ui.boxOf(pts, px(20)));
      lab(ctx, 'PŪHĀHONU (GARDNER PINNACLES)', r.top, t, lead('pokes'), tEnd0 + 0.6, { order: ['above', 'above-right', 'above-left', 'right', 'left'], dist: 40 }); } } } });
  api.cue(s0('s109'), 'whoosh_soft', -19);
  leg('ch4-midway', 'midway', tH14, ch.t1x, { st: (t) => ({ water: 'lagoon', foam: 0.3 }), wrap: (s) => blurred(s, tH14, T('onlyreef') - 0.6, 5, 0.45) });

  // ================================================================ layer-0 contiguity check (gaps would show navy placeholders)
  const base = scenes.filter(s => (s.layer || 0) === 0 && s.t0 < ch.t1x && s.t1 > ch.t0 && /^ch4-/.test(s.id)).sort((a, b) => a.t0 - b.t0);
  let cov = ch.t0, gaps = []; for (const s of base) { if (s.t0 > cov + 1e-3) gaps.push(`${cov.toFixed(2)}-${s.t0.toFixed(2)}`); cov = Math.max(cov, s.t1); }
  if (cov < ch.t1x - 1e-3) gaps.push(`${cov.toFixed(2)}-${ch.t1x.toFixed(2)}`);
  api.log(`[ch4] ${base.length} base shots ${ch.t0.toFixed(2)}-${ch.t1x.toFixed(2)}${gaps.length ? ' GAPS ' + gaps.join(', ') : ', contiguous'}`);
}
