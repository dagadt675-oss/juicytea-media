// Myth Juice ep02 shot toolkit ("one photoreal Earth"). Every chapter module builds its scenes with these helpers.
// Docs and examples: API.md in this folder. Look book: longform/ep02-hawaii/research/visual/visual_plan.md. Rules: PLAYBOOK*.md.
//
// One page, ONE WebGLRenderer (Hub). Each stage (terrain, blocks, globe) renders WORLD -> its own HDR target -> its own tonemap
// -> hub.rtOut (alpha = class mask) -> the SHARED GRADE pass (same look for every stage) -> canvas -> 2D compositor.
// UI (text, plates, outlines, arrows, numbers, gauge) is drawn on the 2D compositor AFTER the grade: never bloomed or blurred.
// Only stages whose scenes are active at a frame render in that frame; stages are created lazily on first use and cached.
// Pure function of the frame: every uniform a shot can touch is reset from DEFAULTS on every draw (no state leaks between shots).
import * as THREE from 'three';
import * as F from '../../lib/fx.js';
import * as T from '../../lab/type/type.js';
import { HawaiiStage, KM_DEG, R_EARTH, sampleH, LOOKS as LOOKS_T } from '../../lab/hawaii/hterrain.js';
import { BlockStage } from '../../lab/hawaii/blocks.js';
import { CineGlobe, slerpLL } from '../../lab/globe/cineglobe.js';
import * as P from '../../lab/story/story.js';
import { Section } from '../../lab/hawaii/section.js';
export { F, T, P, THREE, Section };

const D2R = Math.PI / 180;
const clamp = F.clamp, lerp = F.lerp;
// ink = dark type straight on the sky, as on both thumbnails (Barlow Condensed 800, rgb 16,22,30, soft white glow: packaging build)
export const PAL = { hero: '#FF5A36', cyan: '#3DE3FF', yellow: '#FFD23F', text: '#F4F6FA', red: '#E8412C', plate: 'rgba(6,9,15,0.86)', ink: '#10161E' };

// ============================================================================================ timing
// K.T('marker') word start (s), K.Te end, K.lead('marker', 3) = 3 frames before the word (highlights land 2-4 frames early),
// K.seg('s004') -> {start, end}, K.f(t) frame index, K.end = film end (last word + 1 s cut + 12 s end screen).
export function makeTime(api) {
  const tm = api.timing || { markers: {}, segments: [] };
  const segs = Object.fromEntries((tm.segments || []).map(s => [s.id, s]));
  const FPS = api.FPS || 30;
  const K = {
    FPS, markers: tm.markers || {}, segments: tm.segments || [],
    T: (m, which = 'start') => { const v = tm.markers?.[m]; if (!v) throw new Error('missing marker ' + m); return which === 'end' ? v.end : v.start; },
    Te: (m) => K.T(m, 'end'),
    lead: (m, frames = 3) => K.T(m) - frames / FPS,
    has: (m) => !!tm.markers?.[m],
    seg: (id) => { const s = segs[id]; if (!s) throw new Error('missing segment ' + id); return s; },
    s0: (id) => K.seg(id).start, s1: (id) => K.seg(id).end,
    f: (t) => Math.round(t * FPS),
    lastWord: (tm.segments || []).reduce((a, s) => Math.max(a, s.end), 0),
    // first word in a segment matching w (case and punctuation ignored): {w, start, end}; K.word('s169', 'base')
    word: (seg, w, nth = 0) => { const n = (x) => x.toLowerCase().replace(/[^a-z0-9ʻāēīōū]/g, ''); const hits = (tm.words || []).filter(x => x.seg === seg && n(x.w) === n(w));
      if (!hits[nth]) throw new Error(`missing word '${w}' in ${seg}`); return hits[nth]; },
  };
  K.end = K.lastWord + 1 + 12;
  // chapter windows: the card sits 0.9 s before the chapter's first voiced segment (PLAYBOOK_craft 7: 0.8-0.9 s voice gap)
  const FIRST = { 1: 's001', 2: 's026', 3: 's049', 4: 's084', 5: 's112', 6: 's150' };
  // XF: the dissolve at every chapter boundary. The incoming chapter's first base shot starts at its t0 with fadeIn XF; the outgoing
  // chapter's last base shot runs to its t1x = t1 + XF (it keeps drawing under the dissolve: no dip to black).
  K.XF = 0.3;
  K.chapter = (n) => {
    const t0 = n === 1 ? 0 : K.s0(FIRST[n]) - 0.9;
    const t1 = n === 6 ? K.end : K.s0(FIRST[n + 1]) - 0.9;
    return { n, t0, t1, t1x: n === 6 ? t1 : t1 + K.XF, card: t0, first: FIRST[n], title: CHAPTER_TITLES[n] };
  };
  return K;
}

// chapter titles: the locked script's chapter list, word for word (the description chapters must match the cards)
export const CHAPTER_TITLES = { 1: 'Only the Top', 2: 'Oʻahu’s Missing Side', 3: 'The Island Stands Up', 4: 'Watch It Grow Old', 5: 'Fought Over a Volcano', 6: 'We Haven’t Hit Bottom' };
// keyframe helpers (ease on the DESTINATION key, PLAYBOOK_production 15). keys: [{t, ...numbers, ease}] in local time.
export const E = Object.assign({}, F.E, { outExpoN: t => t >= 1 ? 1 : (1 - Math.pow(2, -10 * t)) / (1 - Math.pow(2, -10)) });
export function keyAt(keys, lt, fields) {
  if (!Array.isArray(keys)) return keys;
  if (lt <= keys[0].t) return Object.assign({}, keys[0]);
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (lt <= b.t) {
      const p = (b.ease || E.inOut)(clamp((lt - a.t) / Math.max(1e-6, b.t - a.t)));
      const o = Object.assign({}, a);
      for (const k of fields || Object.keys(b)) {
        if (k === 't' || k === 'ease') continue;
        if (typeof b[k] === 'number' && typeof a[k] === 'number') o[k] = lerp(a[k], b[k], p);
        else if (Array.isArray(b[k]) && Array.isArray(a[k])) o[k] = b[k].map((v, j) => lerp(a[k][j], v, p));
        else if (b[k] && typeof b[k] === 'object' && a[k] && typeof a[k] === 'object') o[k] = keyAt([Object.assign({ t: 0 }, a[k]), Object.assign({ t: 1, ease: E.lin }, b[k])], p);
        else if (p >= 0.5) o[k] = b[k];
      }
      return o;
    }
  }
  return Object.assign({}, keys[keys.length - 1]);
}
// value: number | fn(lt) | keys [{t, v, ease}]
export function valAt(v, lt, d = 0) {
  if (v == null) return d;
  if (typeof v === 'function') return v(lt);
  if (Array.isArray(v)) return keyAt(v, lt, ['v']).v;
  return v;
}

// ============================================================================================ the shared grade
// ONE look for every stage (display space, after each stage's own tonemap): navy lift (never pure black), cool shadows,
// slightly warm highlights, vignette, frame-seeded grain. Stage posts run with vignette 0 / grain 0 so nothing is applied twice.
export const GRADE = { exposure: 1.0, contrast: 1.0, sat: 1.0, lift: [0.006, 0.010, 0.022], shadow: [0.97, 1.0, 1.04], high: [1.012, 1.0, 0.985], vignette: 0.2, grain: 0.012 };
// Masked terrain looks (need the stage's class mask: sky 0, water .25, drained seabed .5, today's land 1). 'noocean' is the
// NO OCEAN thumbnail grade (packaging fix_noocean cand_2, build.py) ported to the shader: saturated rainforest green and rust on
// the cap, darker cool slate flank, deeper blue sky top with a warm anti-solar belt. lc radius is in px at 1080p.
export const MLOOKS = {
  noocean: { pulls: [[50, 100, 117, 0.5], [5, 45, 17, 0.171]], vib: 0.417, smax: 0.8, capExp: 1.248, shadow: [0.1, 0.256, 0.515], shadowTint: [0.88, 0.96, 1.2], lc: [18, 0.34],
    flExp: 0.95, flSat: 0.65, flWarm: [0.891, 1.0, 1.021], flBurn: [0.59, 1.0, 0.008], flFar: [0.15, 1.0], fhSat: 0.5, fhWarm: [0.92, 1.0, 1.06],
    skExp: 1.048, skTop: [108, 136, 224], skGrad: [0.609, 1.6], belt: [230, 194, 210], beltP: [0.787, 2.0, 0.2, 0.5] },
  none: null,
};
const GRADE_FS = /* glsl */`
uniform sampler2D src; uniform vec2 res; uniform float seed;
uniform float gExp, gContrast, gSat, gVig, gGrain; uniform vec3 gLift, gShadow, gHigh;
uniform float mAmt, hz; uniform vec4 cP1, cP2; uniform float cVib, cSmax, cExp; uniform vec3 cSh, cShT; uniform vec2 cLC;
uniform float fExp, fSat; uniform vec3 fWarm, fBurn; uniform vec2 fFar; uniform float fhSat; uniform vec3 fhWarm;
uniform float sExp; uniform vec3 sTop; uniform vec2 sGrad; uniform vec3 bCol; uniform vec4 bPar;
varying vec2 vUv;
float lum(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 rgb2hsv(vec3 c){ float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)), d = mx - mn, h = 0.0;
  if (d > 1e-6) { if (mx == c.r) h = mod((c.g - c.b) / d, 6.0); else if (mx == c.g) h = (c.b - c.r) / d + 2.0; else h = (c.r - c.g) / d + 4.0; }
  return vec3(h * 60.0, mx > 1e-6 ? d / mx : 0.0, mx); }
vec3 hsv2rgb(vec3 c){ float h = mod(c.x, 360.0) / 60.0, i = floor(h), f = h - i, v = c.z, s = c.y;
  float p = v * (1.0 - s), q = v * (1.0 - s * f), t = v * (1.0 - s * (1.0 - f));
  if (i < 0.5) return vec3(v, t, p); if (i < 1.5) return vec3(q, v, p); if (i < 2.5) return vec3(p, v, t);
  if (i < 3.5) return vec3(p, q, v); if (i < 4.5) return vec3(t, p, v); return vec3(v, p, q); }
float pullH(float h, vec4 P){ float w = clamp((h - P.x) / 12.0, 0.0, 1.0) * clamp((P.y - h) / 12.0, 0.0, 1.0); return h + (P.z - h) * P.w * w; }
vec3 tone(vec3 a, float ex, vec3 warm, float sat){ a *= ex; a *= warm; float l = lum(a); return vec3(l) + (a - vec3(l)) * sat; }
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main(){
  vec4 s0 = texture2D(src, vUv); vec3 a = s0.rgb, c = a;
  float y = 1.0 - vUv.y, x = vUv.x;
  if (mAmt > 0.001) {
    float A = s0.a;
    // classes: sky 0, water .25, drained seabed and land outside capBB .5 (flank grade), hero-filled .75 (passed through), cap land 1
    float sky = 1.0 - smoothstep(0.06, 0.18, A), cap = smoothstep(0.80, 0.97, A);
    float pass = smoothstep(0.62, 0.72, A) * (1.0 - cap);
    float wat = smoothstep(0.12, 0.2, A) * (1.0 - smoothstep(0.3, 0.42, A)), fl = clamp(1.0 - sky - cap - wat - pass, 0.0, 1.0);
    // cap: hue pulls toward rainforest green and rust, vibrance, saturation cap, cool sky-lit shadows, exposure, local contrast
    vec3 hsv = rgb2hsv(clamp(a, 0.0, 1.0)); hsv.x = pullH(hsv.x, cP1); hsv.x = pullH(hsv.x, cP2);
    hsv.y = clamp(hsv.y + cVib * hsv.y * (1.0 - hsv.y) * 2.0, 0.0, 1.0); hsv.y = min(hsv.y, cSmax);
    vec3 cg = hsv2rgb(hsv);
    float lc0 = lum(cg), w = clamp((cSh.y - lc0) / max(cSh.y - cSh.x, 1e-3), 0.0, 1.0) * cSh.z;
    cg = cg * (1.0 - w) + cg * cShT * w; cg *= cExp;
    if (cLC.y > 0.0) { float lod = log2(max(cLC.x, 1.0) * 1.6); float ls = lum(a), lb = lum(texture2D(src, vUv, lod).rgb);
      float k = clamp(1.0 + cLC.y * (ls - lb) / max(ls, 1e-3), 0.6, 1.6); cg *= 1.0 + (k - 1.0) * cap; }
    // flank: darker, cooler, desaturated; the render's own haze is kept near the horizon; slight burn toward the bottom
    vec3 fg = tone(a, fExp, fWarm, fSat);
    float tb = clamp((y - fBurn.x) / max(fBurn.y - fBurn.x, 1e-3), 0.0, 1.0); fg *= 1.0 - tb * tb * (3.0 - 2.0 * tb) * fBurn.z;
    float tf = clamp((y - hz) / max(fFar.x, 1e-3), 0.0, 1.0); tf = tf * tf * (3.0 - 2.0 * tf); float wf = fFar.y * (1.0 - tf);
    fg = fg * (1.0 - wf) + tone(a, 1.0, fhWarm, fhSat) * wf;
    // sky: exposure, deeper blue toward the top, warm anti-solar belt low on the right; the belt glows faintly on the far floor
    vec3 sg = a * sExp;
    float ts = pow(clamp(y / max(hz, 1e-3), 0.0, 1.0), sGrad.y); sg = sg * (1.0 - sGrad.x * (1.0 - ts)) + sTop * sGrad.x * (1.0 - ts);
    float tbt = pow(clamp(y / max(hz, 1e-3), 0.0, 1.0), bPar.y), xr = pow(clamp((x - bPar.z) / (1.0 - bPar.z), 0.0, 1.0), 0.8);
    float wb = bPar.x * tbt * xr; sg = sg * (1.0 - wb) + bCol * wb;
    float yf = clamp(1.0 - (y - hz) / 0.12, 0.0, 1.0) * step(hz, y); float wfl = bPar.w * yf * xr;
    fg = fg * (1.0 - wfl) + fg * (bCol / max((bCol.r + bCol.g + bCol.b) / 3.0, 1e-3)) * wfl;
    vec3 m = cg * cap + fg * fl + sg * sky + a * (wat + pass);
    c = mix(a, m, mAmt);
  }
  // shared film grade
  c *= gExp;
  float l = lum(c);
  c = mix(c, c * gShadow, (1.0 - smoothstep(0.0, 0.5, l)) * 0.6);
  c = mix(c, c * gHigh, smoothstep(0.5, 1.0, l) * 0.6);
  c = (c - 0.45) * gContrast + 0.45;
  l = lum(c); c = vec3(l) + (c - vec3(l)) * gSat;
  c = c + gLift * (1.0 - c);
  vec2 q = vUv - 0.5; q.x *= res.x / res.y;
  c *= 1.0 - gVig * smoothstep(0.35, 1.05, length(q));
  c += (h12(gl_FragCoord.xy + seed * 61.7) - 0.5) * gGrain;
  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}`;
const FSQ_VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';
class GradePass {
  constructor(W, H) {
    const v3 = (a) => new THREE.Vector3(...a), v4 = (a) => new THREE.Vector4(...a), v2 = (a) => new THREE.Vector2(...a);
    this.u = {
      src: { value: null }, res: { value: v2([W, H]) }, seed: { value: 0 },
      gExp: { value: 1 }, gContrast: { value: 1 }, gSat: { value: 1 }, gVig: { value: 0.2 }, gGrain: { value: 0.012 }, gLift: { value: v3([0, 0, 0]) }, gShadow: { value: v3([1, 1, 1]) }, gHigh: { value: v3([1, 1, 1]) },
      mAmt: { value: 0 }, hz: { value: 0.28 }, cP1: { value: v4([0, 0, 0, 0]) }, cP2: { value: v4([0, 0, 0, 0]) }, cVib: { value: 0 }, cSmax: { value: 1 }, cExp: { value: 1 }, cSh: { value: v3([0, 0, 0]) }, cShT: { value: v3([1, 1, 1]) }, cLC: { value: v2([0, 0]) },
      fExp: { value: 1 }, fSat: { value: 1 }, fWarm: { value: v3([1, 1, 1]) }, fBurn: { value: v3([0, 1, 0]) }, fFar: { value: v2([0.15, 0]) }, fhSat: { value: 1 }, fhWarm: { value: v3([1, 1, 1]) },
      sExp: { value: 1 }, sTop: { value: v3([0, 0, 0]) }, sGrad: { value: v2([0, 1]) }, bCol: { value: v3([0, 0, 0]) }, bPar: { value: v4([0, 1, 0.2, 0]) },
    };
    this.mat = new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: FSQ_VS, fragmentShader: GRADE_FS, depthTest: false, depthWrite: false });
    this.scene = new THREE.Scene(); const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.mat); q.frustumCulled = false; this.scene.add(q);
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  // g: grade overrides (keys of GRADE); m: {look: 'noocean'|object, amt, hz}
  set(g = {}, m = {}, frame = 0) {
    const G = Object.assign({}, GRADE, g), u = this.u;
    u.gExp.value = G.exposure; u.gContrast.value = G.contrast; u.gSat.value = G.sat; u.gVig.value = G.vignette; u.gGrain.value = G.grain;
    u.gLift.value.set(...G.lift); u.gShadow.value.set(...G.shadow); u.gHigh.value.set(...G.high); u.seed.value = (frame * 0.6180339) % 1 * 100;
    const L = typeof m.look === 'string' ? MLOOKS[m.look] : m.look;
    u.mAmt.value = L ? clamp(m.amt ?? 1) : 0; u.hz.value = m.hz ?? 0.28;
    if (L) {
      const pl = L.pulls || []; u.cP1.value.set(...(pl[0] || [0, 0, 0, 0])); u.cP2.value.set(...(pl[1] || [0, 0, 0, 0]));
      u.cVib.value = L.vib ?? 0; u.cSmax.value = L.smax ?? 1; u.cExp.value = L.capExp ?? 1; u.cSh.value.set(...(L.shadow || [0, 0, 0])); u.cShT.value.set(...(L.shadowTint || [1, 1, 1]));
      u.cLC.value.set(L.lc ? L.lc[0] * this.u.res.value.y / 1080 : 0, L.lc ? L.lc[1] : 0);
      u.fExp.value = L.flExp ?? 1; u.fSat.value = L.flSat ?? 1; u.fWarm.value.set(...(L.flWarm || [1, 1, 1])); u.fBurn.value.set(...(L.flBurn || [0, 1, 0]));
      u.fFar.value.set(...(L.flFar || [0.15, 0])); u.fhSat.value = L.fhSat ?? 1; u.fhWarm.value.set(...(L.fhWarm || [1, 1, 1]));
      u.sExp.value = L.skExp ?? 1; u.sTop.value.set(...(L.skTop || [0, 0, 0]).map(v => v / 255)); u.sGrad.value.set(...(L.skGrad || [0, 1]));
      u.bCol.value.set(...(L.belt || [0, 0, 0]).map(v => v / 255)); u.bPar.value.set(...(L.beltP || [0, 1, 0.2, 0]));
    }
  }
  run(R, srcRT) { this.u.src.value = srcRT.texture; R.setRenderTarget(null); R.autoClear = true; R.render(this.scene, this.cam); }
}
// the same grade in JS for 2D world assets (paper cards, photos): applied once at prep time (no vignette, no grain)
export function gradeCanvas(cv, g = {}) {
  const G = Object.assign({}, GRADE, g), cx = cv.getContext('2d', { willReadFrequently: true });
  const im = cx.getImageData(0, 0, cv.width, cv.height), d = im.data;
  const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] === 0) continue;
    let r = d[i] / 255 * G.exposure, gg = d[i + 1] / 255 * G.exposure, b = d[i + 2] / 255 * G.exposure;
    let l = 0.2126 * r + 0.7152 * gg + 0.0722 * b;
    const ws = (1 - ss(0, 0.5, l)) * 0.6, wh = ss(0.5, 1, l) * 0.6;
    r *= (1 - ws + ws * G.shadow[0]) * (1 - wh + wh * G.high[0]); gg *= (1 - ws + ws * G.shadow[1]) * (1 - wh + wh * G.high[1]); b *= (1 - ws + ws * G.shadow[2]) * (1 - wh + wh * G.high[2]);
    r = (r - 0.45) * G.contrast + 0.45; gg = (gg - 0.45) * G.contrast + 0.45; b = (b - 0.45) * G.contrast + 0.45;
    l = 0.2126 * r + 0.7152 * gg + 0.0722 * b; r = l + (r - l) * G.sat; gg = l + (gg - l) * G.sat; b = l + (b - l) * G.sat;
    r = r + G.lift[0] * (1 - r); gg = gg + G.lift[1] * (1 - gg); b = b + G.lift[2] * (1 - b);
    d[i] = clamp(r) * 255; d[i + 1] = clamp(gg) * 255; d[i + 2] = clamp(b) * 255;
  }
  cx.putImageData(im, 0, 0); return cv;
}

// ============================================================================================ the hub: one renderer, lazy stages
export class Hub {
  constructor(api) {
    this.api = api; const W = this.W = api.W, H = this.H = api.H;
    this.R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.R.setPixelRatio(1); this.R.setSize(W, H, false);
    this.rtOut = new THREE.WebGLRenderTarget(W, H, { type: THREE.UnsignedByteType, depthBuffer: false, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter, colorSpace: THREE.NoColorSpace });
    this.grade = new GradePass(W, H);
    this.cache = new Map(); this.perf = {}; this.frame = 0; this.draft = !!api.Q?.draft;
    // Q.perf: sync the GPU after each stage so per-stage times are real (costs a pipeline stall; measurement only)
    if (api.Q?.perf) { const gl = this.R.getContext(), px1 = new Uint8Array(4); this.sync = () => gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px1); }
  }
  // a stage by key, created once with make(renderer) (may be async); concurrent callers share the promise
  stage(key, make) { if (!this.cache.has(key)) this.cache.set(key, Promise.resolve(make(this.R))); return this.cache.get(key); }
  // render one stage into rtOut (renderInto(target)), grade it, draw the result onto ctx
  composite(ctx, key, renderInto, grade = {}, mlook = {}) {
    const t0 = performance.now();                       // measurement only, never drives a pixel
    renderInto(this.rtOut);
    if (this.sync) this.sync();
    const t1 = performance.now();
    this.grade.set(grade, mlook, this.frame);
    this.grade.run(this.R, this.rtOut);
    ctx.drawImage(this.R.domElement, 0, 0);
    if (this.sync) { this.sync(); this.perf['grade+copy'] = (this.perf['grade+copy'] || 0) + performance.now() - t1; }
    this.perf[key] = (this.perf[key] || 0) + t1 - t0;
  }
  // vex is baked into the mesh: a 2x shot uses its own stage (PLAYBOOK_craft 8: 1.0 for height comparisons, 2x at most elsewhere)
  // o: {origin: {lon, lat} (keep a framing identical to another stage), midGrid: [nx, ny] (mesh of the middle layer)}
  terrain(region = 'bigisland', vex = 1, o = {}) {
    if (region === 'hawaii') region = 'bigisland';
    const R = REGIONS[region], idx = this.regionIndex?.[region];
    const stacked = !R && idx && typeof HawaiiStage.prototype.loadRegion === 'function';
    if (!R && !stacked) { if (!this._warned?.[region]) { (this._warned ||= {})[region] = 1; this.api.log(`[hub] region '${region}' not loadable yet, using 'bigisland'`); } return this.terrain('bigisland', vex); }
    return this.stage('terrain:' + region + ':' + vex + ':' + JSON.stringify(o), async (renderer) => {
      const d = this.draft;
      const S = new HawaiiStage(this.W, this.H, { renderer, samples: d ? 0 : 4, vex, origin: o.origin ?? R?.origin ?? idx?.origin, heroGrid: d ? [700, 700] : undefined, skirtGrid: d ? [450, 340] : undefined,
        midGrid: d ? undefined : o.midGrid });
      if (stacked) await S.loadRegion('/ep/ep02/data', region); else await S.load(R.dir);
      S.region = region; return S;
    });
  }
  blocks(o = {}) {
    const key = 'blocks:' + JSON.stringify(o);
    return this.stage(key, async (renderer) => { const S = new BlockStage(this.W, this.H, Object.assign({ renderer, samples: this.draft ? 0 : 4 }, o)); await S.load(o.dir || REGIONS.hawaii.dir); return S; });
  }
  globe() {
    return this.stage('globe', async (renderer) => { const g = new CineGlobe(this.W, this.H, { renderer, ss: this.draft ? 1 : 2 }); await g.init({ day: '/tex/day_8k.jpg', night: '/tex/night_8k.jpg', normal: '/tex/normal_8k.png', clouds: '/lab/globe/clouds_8k.jpg' }); return g; });
  }
}

// ============================================================================================ regions, places, named cameras
// A region = one baked data folder (lab/hawaii/tools/fetch_hawaii.sh; bbox via HB/SB env vars, see API.md).
// 'bigisland' is the legacy lab/hawaii/data bake (hero 4096^2 over the main islands + ETOPO 30" skirt): frame 1 and the thumbnails
// were rendered from it. Other regions (ep/ep02/data/regions.json, baked by lab/hawaii/tools/region_bake.py) load through
// HawaiiStage.loadRegion when the stage supports it; until then terrainShot falls back to 'bigisland' and logs it.
export const REGIONS = {
  bigisland: { dir: '/lab/hawaii/data', origin: { lon: -155.6, lat: 19.6 }, hero: [-158.3, 17.9, -153.8, 21.8], skirt: [-168, 12, -144, 30] },
};
REGIONS.hawaii = REGIONS.bigisland;
// [lon, lat] of named places (summits from the DEM search in blocks.js; islands as in hawaii_bake.py)
export const PLACES = {
  'mauna-loa': [-155.6054, 19.4756], 'mauna-kea': [-155.4681, 19.8207], kilauea: [-155.287, 19.407], hualalai: [-155.864, 19.692], kohala: [-155.716, 20.086],
  halape: [-155.243, 19.272], loihi: [-155.27, 18.92], 'south-point': [-155.681, 18.911], hilo: [-155.09, 19.72],
  maui: [-156.25, 20.71], 'west-maui': [-156.59, 20.89], haleakala: [-156.253, 20.709], molokai: [-156.87, 21.11], lanai: [-156.92, 20.83], kahoolawe: [-156.60, 20.55],
  'penguin-bank': [-157.45, 21.0], 'auau-channel': [-156.758, 20.885], 'pailolo-channel': [-156.78, 21.03], 'kalohi-channel': [-156.93, 20.95],
  oahu: [-157.98, 21.47], pali: [-157.793, 21.367], honolulu: [-157.858, 21.307],
};
// named cameras for HawaiiStage.setCamera (eye lon/lat + alt or agl km; target tLon/tLat/tH m; fov; lens shift)
export const CAMS = {
  // frame 1 = the NO OCEAN thumbnail (final_ep02_1.jpg): fix_noocean d3 plate camera + its 1.321 crop at (0.47, 0.49) as a lens
  noocean: { lon: -155.32, lat: 18.42, alt: 26, tLon: -155.47, tLat: 19.52, tH: -2000, fov: 2 * Math.atan(Math.tan(20 * D2R) / 1.321) / D2R, shiftX: -0.06 * 1.321, shiftY: 0.02 * 1.321 },
  noocean_plate: { lon: -155.32, lat: 18.42, alt: 26, tLon: -155.47, tLat: 19.52, tH: -2000, fov: 40 },
  // ONE ISLAND (final_ep02_2.jpg): its plate (design_question r6 ours_P3_mauinui, recovered by a camera search: eye over the sea
  // north-west of Moloka'i, 10 km up, looking ESE across Maui Nui to the Big Island) + its 1.08 crop at (0.5, 0.55) as a lens
  // (best of 4 searches, land/water/sky layout agreement 0.91 with the plate at 192x108; tools/camsearch.html)
  mauinui_one: { lon: -157.4, lat: 21.25, alt: 11.5, tLon: -156.644, tLat: 20.906, tH: 0, fov: 2 * Math.atan(Math.tan(20 * D2R) / 1.08) / D2R, shiftY: -0.1 * 1.08 },
  mauinui_one_plate: { lon: -157.4, lat: 21.25, alt: 11.5, tLon: -156.644, tLat: 20.906, tH: 0, fov: 40 },
  mauinui_s: { lon: -156.55, lat: 20.15, alt: 30, tLon: -156.65, tLat: 20.90, tH: 0, fov: 34 },
  mauinui_sw: { lon: -157.35, lat: 20.35, alt: 25, tLon: -156.55, tLat: 20.85, tH: 0, fov: 36 },
  bigisland_w: { lon: -156.55, lat: 19.15, alt: 16, tLon: -155.75, tLat: 19.50, tH: 0, fov: 34 },
  bigisland_e: { lon: -154.30, lat: 19.35, alt: 12, tLon: -155.25, tLat: 19.60, tH: -2500, fov: 40 },
};
// stage settings per look (any key can be overridden per shot; everything else is reset to TERRAIN_DEFAULTS each frame)
// the film's seabed albedos (linear): reef flat a warm mid-grey (about RGB 150,138,128 on screen in the ONE ISLAND light), not tan
export const SEABED = { reef: [0.074, 0.066, 0.058] };
// the film's open water (linear shallow, mid, deep): turquoise only in the first metres, a muted steel blue offshore (final_ep02_2.jpg
// far water about RGB 97,153,181), never the saturated navy that reads as a 'blue' clone frame
export const WATER_FILM = [[0.020, 0.40, 0.42], [0.012, 0.16, 0.20], [0.016, 0.092, 0.125]];
export const TERRAIN_DEFAULTS = {
  look: 'gold', sun: [230, 15], water: 'film', level: 0, fog: [0.0028, 0.00012, 6.0],
  set: { foamAmt: 0, tubAmt: 0, oldLine: 0, ringH: 40, tubM: 90, lineW: 2.2, landSat: 1.2, landGain: 1.15, reefAmt: 0.85, detail: 1.0, foamPx: 2.5, foamM: 2.0,
    edgeGlow: 0.6, fresMax: 0.55, seaRelief: 1.0, shadows: 1, dbg: 0, basaltCol: [0.030, 0.032, 0.038], sedCol: [0.046, 0.045, 0.044], reefCol: SEABED.reef,
    tubCol: [0.42, 0.42, 0.40], lineCol: [0.55, 1.6, 1.9], heroAmt: 0, dimAmt: 0,
    // 2026-11-09 review: one depth-coded seabed (reef flat 0 to -150 m, grey sediment, dark slate basalt), turquoise only in the first
    // ~10 m of water and deep blue by ~60 m, wave normals and a surf band; capBB/heroPass/lineFar off unless a shot sets them
    seaMat: 1, nearAmt: 0, landLift: 0, capBB: [-1e4, -1e4, 1e4, 1e4], heroPass: 0, lineFar: [1e5, 2e5],
    wRamp: [2, 12, 25, 160], waveAmt: 1, glintAmt: 0.12, surfAmt: 0.6 },
  post: { exposure: 1.2, sat: 1.2, contrast: 1.1, lift: 0 },
};
export const LINE = { cream: [1.15, 1.1, 1.0], cyan: [0.55, 1.6, 1.9], white: [1.3, 1.32, 1.32] };
export const PRESETS = {
  // NO OCEAN plate d3 (fix_noocean/work/r/queries.json) + the masked thumbnail grade
  // capBB: only the Big Island takes the cap grade (Maui Nui on the horizon stays muted); lineFar: the white rim fades with distance
  noocean: { look: 'gold', sun: [262, 9], level: -9000, fog: [0.003, 0.0001, 6.0], mlook: 'noocean',
    set: { tubAmt: 1, oldLine: 1, lineW: 1.1, lineCol: LINE.white, landSat: 1.6, landGain: 2.7, basaltCol: [0.02, 0.024, 0.034], sedCol: [0.034, 0.04, 0.054], reefCol: [0.05, 0.05, 0.052],
      capBB: [-156.12, 18.8, -154.7, 20.32], lineFar: [190, 245] }, post: { exposure: 1.7 } },
  // Maui Nui at -400 ft: the ONE ISLAND thumbnail light (final_ep02_2.jpg): warm grey shelf, muted far water, darker foreground
  mauinui: { look: 'day', sun: [128, 30], water: 'film', level: -122, set: { foamAmt: 1, landSat: 0.95, landGain: 0.95, nearAmt: 0.6, glintAmt: 0.05, waveAmt: 0.7 }, post: { exposure: 0.96, contrast: 1.12, sat: 1.1 } },
  half: { look: 'gold', sun: [200, 12], level: -2400, set: { foamAmt: 1, tubAmt: 1, oldLine: 1, lineCol: LINE.cream } },
  drained: { look: 'day', sun: [175, 26], level: -9000, set: { tubAmt: 1, oldLine: 1, lineCol: LINE.cream, sedCol: [0.045, 0.045, 0.048] }, post: { exposure: 1.3 } },
  today: { look: 'day', sun: [200, 30], level: 0, set: { foamAmt: 1 } },
  // Everest regions (everest_wide, everest): light from the south (the colour has north-face shadows baked in), -0.7 stop and a lower
  // snow gain (the first everest_wide still measured luma 196 with 6.7 % blown)
  everest: { look: 'day', sun: [165, 34], level: -9000, set: { landGain: 0.8, landSat: 1.0, landLift: 0.07 }, post: { exposure: 0.8 } },
};

// ============================================================================================ terrain helpers (data, masks, contours)
const GRIDS = new Map();
// height grid (m) over a lon/lat bbox from the stage's hero heights, every `step` source cells; row 0 = south
export function heightGrid(S, bbox, step = 2) {
  const key = S.region + ':' + bbox.join(',') + ':' + step; if (GRIDS.has(key)) return GRIDS.get(key);
  // the finest layer that contains the bbox (region stacks: layers finest first; legacy stage: the hero grid)
  const inside = (b) => bbox[0] >= b[0] && bbox[1] >= b[1] && bbox[2] <= b[2] && bbox[3] <= b[3];
  const lay = (S.layers || []).find(l => inside(l.bbox));
  const hb = lay ? lay.bbox : S.meta.hero_bbox, hm = lay ? lay.hm : S.hHero;
  if (!inside(hb)) throw new Error(`heightGrid: bbox ${bbox} is outside every layer of region ${S.region}`);
  const c0 = Math.floor((bbox[0] - hb[0]) / (hb[2] - hb[0]) * (hm.W - 1)), c1 = Math.ceil((bbox[2] - hb[0]) / (hb[2] - hb[0]) * (hm.W - 1));
  const r0 = Math.floor((bbox[1] - hb[1]) / (hb[3] - hb[1]) * (hm.H - 1)), r1 = Math.ceil((bbox[3] - hb[1]) / (hb[3] - hb[1]) * (hm.H - 1));
  const nx = Math.floor((c1 - c0) / step) + 1, ny = Math.floor((r1 - r0) / step) + 1, h = new Float32Array(nx * ny);
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) h[j * nx + i] = hm.data[Math.min(r0 + j * step, hm.H - 1) * hm.W + Math.min(c0 + i * step, hm.W - 1)];
  const bb = [hb[0] + c0 / (hm.W - 1) * (hb[2] - hb[0]), hb[1] + r0 / (hm.H - 1) * (hb[3] - hb[1]), hb[0] + (c0 + (nx - 1) * step) / (hm.W - 1) * (hb[2] - hb[0]), hb[1] + (r0 + (ny - 1) * step) / (hm.H - 1) * (hb[3] - hb[1])];
  const g = { h, nx, ny, bb, ll: (i, j) => [bb[0] + i / (nx - 1) * (bb[2] - bb[0]), bb[1] + j / (ny - 1) * (bb[3] - bb[1])],
    ij: (lon, lat) => [Math.round((lon - bb[0]) / (bb[2] - bb[0]) * (nx - 1)), Math.round((lat - bb[1]) / (bb[3] - bb[1]) * (ny - 1))] };
  GRIDS.set(key, g); return g;
}
// connected land (h > level, 4-connected) containing the seeds -> Uint8 mask on the grid (the sill.py rule, on the production grid)
export function component(g, level, seeds) {
  const { h, nx, ny } = g, m = new Uint8Array(nx * ny), q = new Int32Array(nx * ny); let qh = 0, qt = 0;
  for (const s of seeds) {
    let [i, j] = g.ij(s[0], s[1]); let best = -1;
    for (let r = 0; r < 12 && best < 0; r++) for (let dj = -r; dj <= r; dj++) for (let di = -r; di <= r; di++) {
      const ii = i + di, jj = j + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue; if (h[jj * nx + ii] > level && best < 0) best = jj * nx + ii; }
    if (best >= 0 && !m[best]) { m[best] = 1; q[qt++] = best; }
  }
  while (qh < qt) { const k = q[qh++], i = k % nx, j = (k / nx) | 0;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const ii = i + di, jj = j + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue; const kk = jj * nx + ii; if (!m[kk] && h[kk] > level) { m[kk] = 1; q[qt++] = kk; } } }
  return m;
}
// marching squares on (mask ? h - level : -1): boundary rings in lon/lat at sub-cell precision, simplified (tol in cells), then
// `smooth` Chaikin passes (2 removes the stair-steps of a 78 m grid and stays within a cell of the rendered waterline).
// Only the mask's bounding box is scanned.
export function contour(g, mask, level, tol = 0.6, smooth = 0, minCells = 60) {
  const { h, nx, ny } = g, f = (i, j) => { const k = j * nx + i; return mask[k] ? Math.max(h[k] - level, 1e-3) : -1; };
  let i0 = nx, i1 = -1, j0 = ny, j1 = -1;
  for (let k = 0; k < mask.length; k++) if (mask[k]) { const i = k % nx, j = (k / nx) | 0; if (i < i0) i0 = i; if (i > i1) i1 = i; if (j < j0) j0 = j; if (j > j1) j1 = j; }
  if (i1 < 0) return [];
  i0 = Math.max(0, i0 - 1); j0 = Math.max(0, j0 - 1); i1 = Math.min(nx - 2, i1); j1 = Math.min(ny - 2, j1);
  const pt = (i0, j0, i1, j1) => { const a = f(i0, j0), b = f(i1, j1), t = a / (a - b); return [i0 + (i1 - i0) * t, j0 + (j1 - j0) * t]; };
  const segs = new Map(), key = (p) => p[0].toFixed(3) + ',' + p[1].toFixed(3), add = (a, b) => { const ka = key(a), kb = key(b); (segs.get(ka) || segs.set(ka, []).get(ka)).push([b, kb]); (segs.get(kb) || segs.set(kb, []).get(kb)).push([a, ka]); };
  for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
    const c = (f(i, j) > 0 ? 1 : 0) | (f(i + 1, j) > 0 ? 2 : 0) | (f(i + 1, j + 1) > 0 ? 4 : 0) | (f(i, j + 1) > 0 ? 8 : 0);
    if (c === 0 || c === 15) continue;
    const e = { b: () => pt(i, j, i + 1, j), r: () => pt(i + 1, j, i + 1, j + 1), t: () => pt(i, j + 1, i + 1, j + 1), l: () => pt(i, j, i, j + 1) };
    const S = { 1: ['l', 'b'], 2: ['b', 'r'], 3: ['l', 'r'], 4: ['r', 't'], 6: ['b', 't'], 7: ['l', 't'], 8: ['t', 'l'], 9: ['t', 'b'], 11: ['t', 'r'], 12: ['r', 'l'], 13: ['r', 'b'], 14: ['b', 'l'] }[c];
    if (S) add(e[S[0]](), e[S[1]]()); else { const ctr = (f(i, j) + f(i + 1, j) + f(i + 1, j + 1) + f(i, j + 1)) / 4 > 0;
      if ((c === 5) === ctr) { add(e.l(), e.t()); add(e.b(), e.r()); } else { add(e.l(), e.b()); add(e.t(), e.r()); } }
  }
  // trace chains: open chains first (a shape cut by the grid edge: its ends have one neighbour), then closed rings
  const used = new Set(), rings = [];
  const trace = (k0) => { const ring = []; let k = k0, prev = null;
    for (let guard = 0; guard < 1e6; guard++) {
      used.add(k); const [x, y] = k.split(',').map(Number); ring.push([x, y]);
      const opts = segs.get(k).filter(([p, kk]) => kk !== prev && !used.has(kk)); if (!opts.length) break; prev = k; k = opts[0][1];
    }
    const [ax, ay] = ring[0], [bx, by] = ring[ring.length - 1]; ring.open = Math.hypot(bx - ax, by - ay) > 1.5;
    // drop specks and small holes (a fish pond or a data pit inside an island is not a coast): |area| under minCells cells
    let ar = 0; for (let i = 0; i < ring.length; i++) { const a = ring[i], b = ring[(i + 1) % ring.length]; ar += a[0] * b[1] - b[0] * a[1]; }
    if (ring.length > 8 && (ring.open || Math.abs(ar) / 2 >= minCells)) rings.push(ring); };
  for (const [k0, nb] of segs) if (!used.has(k0) && nb.length === 1) trace(k0);
  for (const [k0] of segs) if (!used.has(k0)) trace(k0);
  const dp = (pts, tl) => { if (pts.length < 3) return pts; let mx = 0, id = 0; const [ax, ay] = pts[0], [bx, by] = pts[pts.length - 1], L = Math.hypot(bx - ax, by - ay) || 1e-9;
    const closed = Math.hypot(bx - ax, by - ay) < 1e-9;              // closed ring: measure from the start point instead of a zero chord
    for (let i = 1; i < pts.length - 1; i++) { const d = closed ? Math.hypot(pts[i][0] - ax, pts[i][1] - ay) : Math.abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / L; if (d > mx) { mx = d; id = i; } }
    return mx > tl ? dp(pts.slice(0, id + 1), tl).slice(0, -1).concat(dp(pts.slice(id), tl)) : [pts[0], pts[pts.length - 1]]; };
  const chaikin = (r, open) => { const o = open ? [r[0]] : []; const n = open ? r.length - 1 : r.length;
    for (let i = 0; i < n; i++) { const a = r[i], b = r[(i + 1) % r.length]; o.push([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]], [0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]); }
    if (open) o.push(r[r.length - 1]); return o; };
  // open chains (cut by the grid edge) stay open: never close them with a straight line across the shape
  return rings.map(r => { let q = r.open ? dp(r, tol) : dp(r.concat([r[0]]), tol).slice(0, -1); for (let k = 0; k < smooth; k++) q = chaikin(q, r.open); if (!r.open) q.push(q[0]); return q.map(([x, y]) => g.ll(x, y)); });
}
// chamfer distance (km) from a mask over the grid (two passes, 3-4 weights)
export function distKm(g, mask) {
  const { nx, ny } = g, D = new Float32Array(nx * ny), BIG = 1e9;
  const cx = (g.bb[2] - g.bb[0]) / (g.nx - 1) * KM_DEG * Math.cos((g.bb[1] + g.bb[3]) / 2 * D2R), cy = (g.bb[3] - g.bb[1]) / (g.ny - 1) * KM_DEG, cd = Math.hypot(cx, cy);
  for (let k = 0; k < D.length; k++) D[k] = mask[k] ? 0 : BIG;
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) { const k = j * nx + i; let v = D[k];
    if (i > 0) v = Math.min(v, D[k - 1] + cx); if (j > 0) { v = Math.min(v, D[k - nx] + cy); if (i > 0) v = Math.min(v, D[k - nx - 1] + cd); if (i < nx - 1) v = Math.min(v, D[k - nx + 1] + cd); } D[k] = v; }
  for (let j = ny - 1; j >= 0; j--) for (let i = nx - 1; i >= 0; i--) { const k = j * nx + i; let v = D[k];
    if (i < nx - 1) v = Math.min(v, D[k + 1] + cx); if (j < ny - 1) { v = Math.min(v, D[k + nx] + cy); if (i < nx - 1) v = Math.min(v, D[k + nx + 1] + cd); if (i > 0) v = Math.min(v, D[k + nx - 1] + cd); } D[k] = v; }
  return D;
}
// land bridges: cells of `joined` (land at the shot's level) that were not land in any of `parts` (today's islands) and lie within
// dKm of at least two different parts; soft weight 0..255 (full in the middle of the bridge, fading toward either shore and outward)
export function bridges(g, joined, parts, dKm = 11) {
  const Ds = parts.map(m => distKm(g, m)), out = new Uint8Array(joined.length); out.soft = true;
  for (let k = 0; k < joined.length; k++) {
    if (!joined[k] || parts.some(m => m[k])) continue;
    const d = Ds.map(D => D[k]).sort((a, b) => a - b);
    if (d[1] > dKm) continue;
    out[k] = Math.round(255 * clamp((dKm - d[1]) / 2.0));
  }
  return out;
}
// island = component + its rings + area (km2), cached by (region, bbox, level, seeds)
const ISL = new Map();
export function island(S, { bbox, level, seeds, step = 2, tol, smooth = 2 }) {
  const key = [S.region, bbox, level, JSON.stringify(seeds), step, tol, smooth].join('|'); if (ISL.has(key)) return ISL.get(key);
  const g = heightGrid(S, bbox, step), mask = component(g, level, seeds), rings = contour(g, mask, level, tol ?? (step === 1 ? 0.7 : 0.6), smooth);
  let n = 0; for (const v of mask) n += v; const cell = ((g.bb[2] - g.bb[0]) / (g.nx - 1) * KM_DEG * Math.cos((g.bb[1] + g.bb[3]) / 2 * D2R)) * ((g.bb[3] - g.bb[1]) / (g.ny - 1) * KM_DEG);
  const o = { g, mask, rings, level, areaKm2: n * cell }; ISL.set(key, o); return o;
}
// RGBA8 mask texture over the grid: channels {r: hero fill, g: dimmed}; soft one-cell edge from bilinear filtering
export function maskTexture(g, ch) {
  const d = new Uint8Array(g.nx * g.ny * 4);
  for (const [c, m] of Object.entries(ch)) { const o = { r: 0, g: 1, b: 2, a: 3 }[c]; for (let k = 0; k < m.length; k++) if (m[k]) d[k * 4 + o] = m.soft ? m[k] : 255; }
  const t = new THREE.DataTexture(d, g.nx, g.ny, THREE.RGBAFormat); t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true; return t;
}

// view for UI on a terrain stage: projection (with optional terrain occlusion), horizon, helpers
function terrainView(S, W, H) {
  const cam = S.cam, eye = cam.position.clone();
  const vis = (lon, lat, hm) => {          // march from the eye toward the point (curved Earth); hidden if the terrain rises above the ray
    const p = S.xyz(lon, lat, hm), dx = p.x - eye.x, dz = p.z - eye.z, L2 = dx * dx + dz * dz, py = p.y - L2 / (2 * R_EARTH);
    for (let k = 1; k < 26; k++) { const s = k / 28, x = eye.x + dx * s, z = eye.z + dz * s, y = eye.y + (py - eye.y) * s;
      const lt = S.c0.lat - z / KM_DEG, ln = S.c0.lon + x / (KM_DEG * Math.cos(lt * D2R));
      const gh = Math.max(S.heightAt(ln, lt), S.level) * S.vex * 0.001 - L2 * s * s / (2 * R_EARTH);
      if (gh > y + 0.03) return false; }
    return true; };
  return {
    S, W, H, level: S.level,
    project: (lon, lat, hm) => S.project(lon, lat, hm),
    visible: vis,
    // project lon/lat rings at height hm (default: the stage level) -> screen runs, split where hidden or off-screen
    runs(rings, hm, o = {}) {
      const out = []; const hh = hm ?? S.level;
      for (const r of rings) { let cur = [];
        for (let i = 0; i < r.length; i++) { const [lon, lat] = r[i]; const q = S.project(lon, lat, hh);
          const ok = q && q[0] > -200 && q[0] < W + 200 && q[1] > -200 && q[1] < H + 200 && (o.occlude === false || (i % (o.every || 1)) || vis(lon, lat, hh));
          if (!ok) { if (cur.length > 1) out.push(cur); cur = []; continue; } cur.push(q); }
        if (cur.length > 1) out.push(cur); }
      return out; },
    // screen y (0..1) of the far horizon, for the masked look's sky gradient
    horizonY() {
      const fwd = new THREE.Vector3(); cam.getWorldDirection(fwd); fwd.y = 0; fwd.normalize();
      const hc = Math.max(eye.y - Math.max(Math.min(S.level, 0), -4800) * S.vex * 0.001, 0.05), dip = Math.sqrt(2 * hc / R_EARTH);
      const p = eye.clone().add(fwd.multiplyScalar(Math.cos(dip) * 1000)).add(new THREE.Vector3(0, -Math.sin(dip) * 1000, 0));
      const q = p.project(cam); return clamp((1 - q.y) / 2, 0.02, 0.98); },
  };
}

// apply a full terrain state (defaults + preset + shot) to the stage: every frame, every uniform
const VEC = (v) => v.length === 2 ? new THREE.Vector2(...v) : v.length === 4 ? new THREE.Vector4(...v) : new THREE.Vector3(...v);
function applyTerrain(S, st) {
  if (typeof st.look === 'string') S.setLook(st.look); else S.setLook('day', st.look);
  S.setSun(...st.sun); S.setLevel(st.level);
  // water: 'film' (WATER_FILM, the default) or a HawaiiStage WATERS name ('turq', 'lagoon', 'ocean'), or waterCols [[shallow], [mid], [deep]]
  const wc = st.waterCols || (st.water === 'film' || !st.water ? WATER_FILM : null);
  if (wc) { S.set('wShallow', VEC(wc[0])); S.set('wMid', VEC(wc[1])); S.set('wDeep', VEC(wc[2])); } else S.setWater(st.water);
  for (const [k, v] of Object.entries(st.set)) S.set(k, Array.isArray(v) ? VEC(v) : v);
  for (const [k, v] of Object.entries(st.post)) S.post(k, v);
  S.post('vignette', 0); S.post('grain', 0); S.post('keepA', 1);
  S.U.fogDens.value = st.fog[0]; S.U.fogBg.value = st.fog[1]; S.U.fogH.value = st.fog[2] ?? 6.0;
}
function mergeState(...parts) {
  const o = { set: {}, post: {} };
  for (const p of parts) { if (!p) continue; for (const k in p) { if (k === 'set' || k === 'post') Object.assign(o[k], p[k]); else o[k] = p[k]; } }
  return o;
}
// blend two terrain states (presets or objects) by p: numbers and arrays lerp, looks blend their sky/sun colours
export function mixState(a, b, p) {
  const A = mergeState(TERRAIN_DEFAULTS, typeof a === 'string' ? PRESETS[a] : a), B = mergeState(TERRAIN_DEFAULTS, typeof b === 'string' ? PRESETS[b] : b);
  const L = (x, y) => typeof x === 'number' && typeof y === 'number' ? lerp(x, y, p) : Array.isArray(x) && Array.isArray(y) && x.length === y.length ? x.map((v, i) => L(v, y[i])) : (p < 0.5 ? x : y);
  const o = { set: {}, post: {} };
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) if (k !== 'set' && k !== 'post') o[k] = L(A[k], B[k]);
  o.mlook = A.mlook || B.mlook;
  for (const g of ['set', 'post']) for (const k of new Set([...Object.keys(A[g]), ...Object.keys(B[g])])) o[g][k] = L(A[g][k], B[g][k]);
  o.look = lookMix(A.look, B.look, p);
  if (A.mlook || B.mlook) o.mlookAmt = lerp(A.mlook ? 1 : 0, B.mlook ? 1 : 0, p);
  return o;
}
function hexMix(a, b, p) { const pa = new THREE.Color(a), pb = new THREE.Color(b); return '#' + pa.lerp(pb, p).getHexString(); }
export function lookMix(a, b, p) {
  if (a === b || p <= 0) return a; if (p >= 1) return b;
  const A = LOOKS_T[a], B = LOOKS_T[b];
  return { zenith: hexMix(A.zenith, B.zenith, p), horizon: hexMix(A.horizon, B.horizon, p), haze: [hexMix(A.haze[0], B.haze[0], p), lerp(A.haze[1], B.haze[1], p)],
    sun: hexMix(A.sun, B.sun, p), glow: [hexMix(A.glow[0], B.glow[0], p), lerp(A.glow[1], B.glow[1], p)], sunI: lerp(A.sunI, B.sunI, p), skyI: lerp(A.skyI, B.skyI, p) };
}
// flight between two named cameras: one eased segment (single velocity peak), eye and target on quadratic Bezier paths through
// optional `via` points ({lon, lat, alt} / {tLon, tLat, tH}), fov and lens shift lerped. Returns fn(lt) for terrainShot.cam.
export function flight(c0, c1, t0, t1, o = {}) {
  const A = typeof c0 === 'string' ? CAMS[c0] : c0, B = typeof c1 === 'string' ? CAMS[c1] : c1, ease = o.ease || E.inOut;
  const q = (a, m, b, p) => (1 - p) * (1 - p) * a + 2 * (1 - p) * p * m + p * p * b;
  const V = o.via || {}, Tv = o.tvia || {};
  return (lt) => {
    const p = ease(clamp((lt - t0) / (t1 - t0))), r = {};
    for (const k of ['lon', 'lat', 'alt']) r[k] = q(A[k], V[k] ?? (A[k] + B[k]) / 2, B[k], p);
    for (const k of ['tLon', 'tLat', 'tH']) r[k] = q(A[k], Tv[k] ?? (A[k] + B[k]) / 2, B[k], p);
    for (const k of ['fov', 'shiftX', 'shiftY', 'roll']) r[k] = lerp(A[k] ?? (k === 'fov' ? 30 : 0), B[k] ?? (k === 'fov' ? 30 : 0), p);
    return r;
  };
}
// camera helpers: push (image scale growth per 10 s) and drift (heading deg/s) keep holds alive (nothing static over 2 s)
function liveCam(c, lt, push = 0, drift = 0) {
  const o = Object.assign({}, c);
  if (push) o.fov = 2 * Math.atan(Math.tan((c.fov ?? 30) * D2R / 2) / (1 + push * lt / 10)) / D2R;
  if (drift && o.tLon != null) {
    const a = drift * lt * D2R, cl = Math.cos(o.lat * D2R), dx = (o.tLon - o.lon) * cl, dy = o.tLat - o.lat;
    o.tLon = o.lon + (dx * Math.cos(a) + dy * Math.sin(a)) / cl; o.tLat = o.lat + (-dx * Math.sin(a) + dy * Math.cos(a));
  }
  return o;
}

// ============================================================================================ SHOTS
// terrainShot: HawaiiStage for a named region with keyframed camera, water level and sun.
// spec: { id, t0, t1, layer=0, fadeIn, fadeOut, region='hawaii', preset: name|object, state: {...overrides},
//   cam: CAMS name | object | keys [{t, cam, ease}],  push (per 10 s), drift (deg/s),
//   level: number | fn(lt) | keys [{t, v, ease}],  sun: [az, el] | fn,  set: fn(lt) -> {uniform: value} (per-frame extras),
//   mlook: {look, amt (number|fn|keys)}, grade: {...GRADE overrides} | fn(lt),
//   mask: fn(lt, S) -> {tex, bb, hero, dim} | null,  world(ctx, lt, t, view) (paper etc.), ui(ctx, lt, t, view) }
export function terrainShot(kit, spec) {
  const pre = typeof spec.preset === 'string' ? PRESETS[spec.preset] : spec.preset;
  return { id: spec.id || 'terrain', t0: spec.t0, t1: spec.t1, layer: spec.layer || 0, fadeIn: spec.fadeIn, fadeOut: spec.fadeOut,
    async draw(ctx, lt, t, api) {
      const S = await kit.hub.terrain(spec.region || 'bigisland', spec.vex || 1, spec.stage || {});
      const st = mergeState(TERRAIN_DEFAULTS, pre, typeof spec.state === 'function' ? spec.state(lt) : spec.state, spec.set ? { set: spec.set(lt, S) } : null);
      if (spec.level != null) st.level = valAt(spec.level, lt);
      if (spec.sun) st.sun = typeof spec.sun === 'function' ? spec.sun(lt) : spec.sun;
      if (spec.exposure != null) st.post.exposure = valAt(spec.exposure, lt);
      applyTerrain(S, st);
      const mk = spec.mask ? spec.mask(lt, S) : null;
      if (mk) { S.setMask(mk.tex, mk.bb); S.set('heroAmt', mk.hero ?? 0); S.set('dimAmt', mk.dim ?? 0); S.set('heroPass', mk.pass ?? 0); } else S.setMask(null);
      // cut-away (lab/hawaii/section.js): every frame either on with its state or off (no leaks between shots on one stage)
      let sec = null;
      if (spec.cut) { sec = await Section.create(S, spec.cut.plane); if (spec.cut.everest) await sec.everest(undefined, spec.cut.everest); }
      for (const x of (S._sections || new Map()).values()) x.group.visible = x === sec;
      if (sec) { sec.set(valAt(spec.cut.state, lt, {})); S.setClip(sec.clip()); } else S.setClip(null);
      let camSpec = spec.cam;
      if (sec && spec.cut.cam) camSpec = (l) => sec.cam(typeof spec.cut.cam === 'function' ? spec.cut.cam(l) : keyAt(spec.cut.cam, l));
      const cm = liveCam(kit.cam(camSpec, lt), lt, valAt(spec.push, lt), valAt(spec.drift, lt)); S.setCamera(cm);
      if (api.Q.dbgCam) api.log('[dbg cam] ' + JSON.stringify(cm));
      if (cm.dPitch || cm.dYaw) { S.cam.rotateY((cm.dYaw || 0) * D2R); S.cam.rotateX((cm.dPitch || 0) * D2R); S.cam.updateMatrixWorld(); }
      const view = terrainView(S, api.W, api.H); view.sec = sec;
      const ml = spec.mlook || (st.mlook ? { look: st.mlook, amt: st.mlookAmt ?? 1 } : null);
      const mlook = ml ? { look: ml.look, amt: valAt(ml.amt ?? 1, lt), hz: view.horizonY() } : {};
      const grade = typeof spec.grade === 'function' ? spec.grade(lt) : spec.grade;
      kit.hub.composite(ctx, 'terrain', (target) => S.render(t, kit.hub.frame, target), grade, mlook);
      if (spec.world) await spec.world(ctx, lt, t, view);
      // xfade(): the incoming shot's UI waits until its dissolve has finished (no ghosted labels over the outgoing shot)
      if (spec.ui && !(this.uiFrom > t)) await spec.ui(ctx, lt, t, view);
    } };
}
// cutawayShot: terrainShot with a section (lab/hawaii/section.js). spec.cut = { plane: {lon, lat, az, side, u0, u1, du, bottomKm, loadU},
//   state: {sag, sagM, alphaKm, oldFloor, crustM, waterTop, waterA, floorLine, trenchTop, trenchA, edgeA, everest: {rise, base}} | fn(lt),
//   everest: {u, width, front, th} | null, cam: keys [{t, u, d, alt, tu, te, tf, fov, ease}] | fn(lt) (section coordinates) }
// view.sec in ui(): sec.project(u, e, f), sec.surf(u), sec.crustTop(u), sec.ev {u, W, base, summit, rise}.
export function cutawayShot(kit, spec) { return terrainShot(kit, Object.assign({ region: 'bigisland', vex: 1, preset: 'drained' }, spec)); }

// blockShot: Mauna Loa vs Everest from the true base (BlockStage, VE 1.0, one base plane). Camera keys in km (x east, y up, z south):
// spec: { cam: keys [{t, eye:[x,y,z], target:[x,y,z], fov}], ev: 0..1 Everest rise (number|fn|keys), water: 0..1 sea volume (to the
//   old sea level), line: 0..1 Mauna Loa's sea-level line, look, sun, grade, ui(ctx, lt, t, view) }. view.p(x, y, z) -> [sx, sy].
export function blockShot(kit, spec) {
  return { id: spec.id || 'blocks', t0: spec.t0, t1: spec.t1, layer: spec.layer || 0, fadeIn: spec.fadeIn, fadeOut: spec.fadeOut,
    async draw(ctx, lt, t, api) {
      const S = await kit.hub.blocks(spec.blocks || { half: 10, gap: 8 });
      if (!S.extra) addBlockExtras(S);
      S.setLook(spec.look || 'day', ...(spec.sun || [228, 30]));
      S.U.seaLine.value = valAt(spec.line, lt, 1); S.guides.visible = false;
      S.postMat.uniforms.vignette.value = 0; S.postMat.uniforms.grain.value = 0; S.postMat.uniforms.keepA.value = 0;
      for (const [k, v] of Object.entries(Object.assign({ exposure: 1.15, sat: 1.15, contrast: 1.08, lift: 0 }, spec.post || {}))) S.postMat.uniforms[k].value = v;
      const ev = clamp(valAt(spec.ev, lt, 1));
      S.evGroup.position.y = -S.topEV * 1.02 * (1 - ev); S.evGroup.visible = ev > 0.0005;
      const wa = clamp(valAt(spec.water, lt, 0)); S.extra.water.visible = wa > 0.002; S.extra.waterU.a.value = wa;
      const c = keyAt(spec.cam, lt);
      S.setCamera({ eye: c.eye, target: c.target, fov: c.fov });
      const cam = S.cam;
      const view = { S, W: api.W, H: api.H,
        p: (x, y, z) => { const v = new THREE.Vector3(x, y, z).project(cam); return v.z > 1 ? null : [(v.x + 1) / 2 * api.W, (1 - v.y) / 2 * api.H]; },
        ml: { x0: S.xML - S.o_half, x1: S.xML + S.o_half, top: S.topML, sea: S.seaY, floor: S.seaY - 5.0 * S.vex },
        ev: { x0: S.xEV - S.o_half, x1: S.xEV + S.o_half, top: S.topEV + S.evGroup.position.y, rise: ev } };
      const grade = typeof spec.grade === 'function' ? spec.grade(lt) : spec.grade;
      kit.hub.composite(ctx, 'blocks', (target) => S.render(kit.hub.frame, target), grade, {});
      if (spec.ui && !(this.uiFrom > t)) await spec.ui(ctx, lt, t, view);
    } };
}
function addBlockExtras(S) {
  const half = S.o.half ?? 14, gap = S.o.gap ?? 10; S.o_half = half;
  // translucent sea volume from the base plane up to Mauna Loa's present sea level, spanning both blocks ("its peak would still be underwater")
  const waterU = { a: { value: 0 }, col: { value: new THREE.Vector3(0.10, 0.55, 0.75) } };
  const geo = new THREE.BoxGeometry(4 * half + gap + 16, S.seaY, 2 * half + 16); geo.translate(0, S.seaY / 2, 0);
  const water = new THREE.Mesh(geo, new THREE.ShaderMaterial({ uniforms: waterU, transparent: true, depthWrite: false,
    vertexShader: 'varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: 'uniform float a; uniform vec3 col; varying vec3 vW; void main(){ gl_FragColor = vec4(col, a * 0.42); }' }));
  water.renderOrder = 3; water.visible = false; S.scene.add(water);
  S.extra = { water, waterU };
}

// cineGlobeShot: CineGlobe with presets. STORY = map-fact globe (clouds 0.25 kept off the subject, haze 0.2, +0.5 stop, no DOF);
// HERO = cinematic oblique (clouds 0.6, DOF 6); ESTABLISH = whole-globe opener. Overlay fills live in the globe texture at 55-66 %;
// outlines and labels go in ui() via view.runs(rings) + kit.ui.outline (crisp, after the grade).
// spec: { preset, keys: [{t, lat, lon, alt, tilt, heading, fov, lookOffset, ease}], subject: [lat, lon], overlay: {canvas, bounds} | null,
//   look: {...earth uniforms} | fn(lt), post: {...CineGlobe post}, sun: {sun:'camera', sunAz, sunEl}, grade, ui }
export const GLOBE_PRESETS = {
  // STORY: +0.5 stop over the first toolkit (its smoke test measured luma 79); frame it so the subject fills a third of the width or
  // more (alt about 0.25-0.32 for the main Hawaiian chain, never the 0.4 of the smoke test that left the Big Island 110 px wide)
  STORY: { state: { clouds: 0.25, sun: 'camera', sunAz: -25, sunEl: 32 }, clear: [5, 16, 0.95], look: { haze: 0.24, exposure: 1.25 * 2.2 * 1.41, oceanTone: 1.0, desat: 0.02, nightAmt: 0, specAmt: 0.6 },
    post: { dof: 0, bloom: 0.12, vignette: 0, grain: 0, ca: 0, lift: [0, 0, 0], shadowTint: [1, 1, 1], highTint: [1, 1, 1], contrast: 1.06, sat: 1.06 } },
  HERO: { state: { clouds: 0.6, sun: 'camera', sunAz: -30, sunEl: 30 }, clear: [4, 12, 0.85], look: { haze: 0.24, exposure: 1.25 * 1.2, nightAmt: 0 },
    post: { dof: 6, bloom: 0.2, vignette: 0, grain: 0, ca: 0, lift: [0, 0, 0], shadowTint: [1, 1, 1], highTint: [1, 1, 1], contrast: 1.12, sat: 1.06 } },
  ESTABLISH: { state: { clouds: 0.6, sun: 'world', sunLat: 10, sunLon: 0 }, clear: null, look: { haze: 0.25, exposure: 1.25 },
    post: { dof: 0, bloom: 0.26, vignette: 0, grain: 0, ca: 0, lift: [0, 0, 0], shadowTint: [1, 1, 1], highTint: [1, 1, 1], contrast: 1.08, sat: 1.08 } },
};
export function cineGlobeShot(kit, spec) {
  const pre = GLOBE_PRESETS[spec.preset || 'STORY'];
  return { id: spec.id || 'globe', t0: spec.t0, t1: spec.t1, layer: spec.layer || 0, fadeIn: spec.fadeIn, fadeOut: spec.fadeOut,
    async draw(ctx, lt, t, api) {
      const g = await kit.hub.globe();
      if (spec.overlay !== undefined && g._owner !== spec.id) { g.setOverlay(spec.overlay ? spec.overlay.canvas : null, spec.overlay?.bounds); g._owner = spec.id; }
      const k = globeKey(spec.keys, lt);
      const subj = spec.subject || [k.lat, k.lon];
      const clear = pre.clear ? [subj[0], subj[1], ...pre.clear] : null;
      g.set(Object.assign({ lookOffset: null, tilt: 0, heading: 0, fov: 30 }, pre.state, spec.sun || {}, k, { clear, cloudOff: 0.04 * t }));
      const look = Object.assign({ dim: 0, desat: 0.04, ovAlpha: 0.6, relief: 0.8, ambient: 0.1, flatBase: 0, ovMul: 0, specAmt: 1, nightAmt: 1 }, pre.look, typeof spec.look === 'function' ? spec.look(lt) : spec.look);
      for (const kk in look) g.look(kk, look[kk]);
      g.post(Object.assign({}, pre.post, spec.post));
      g.starfield(null, spec.stars ?? 1);
      const view = { g, W: api.W, H: api.H, project: (lat, lon, h) => g.project(lat, lon, h),
        runs: (rings, o = {}) => T.projectRuns(g, rings, o) };
      const grade = typeof spec.grade === 'function' ? spec.grade(lt) : spec.grade;
      kit.hub.composite(ctx, 'globe', (target) => g.render(kit.hub.frame, target), grade, {});
      if (spec.ui && !(this.uiFrom > t)) await spec.ui(ctx, lt, t, view);
    } };
}
function globeKey(keys, lt) {
  if (!Array.isArray(keys)) return keys;
  if (lt <= keys[0].t) return Object.assign({}, keys[0]);
  for (let i = 1; i < keys.length; i++) { const a = keys[i - 1], b = keys[i]; if (lt <= b.t) {
    const p = (b.ease || E.inOut)(clamp((lt - a.t) / (b.t - a.t))); const o = keyAt([a, b], lt);
    const [lat, lon] = slerpLL([a.lat, a.lon], [b.lat, b.lon], p); o.lat = lat; o.lon = lon;
    o.alt = Math.exp(lerp(Math.log(a.alt), Math.log(b.alt), p)); return o; } }
  return Object.assign({}, keys[keys.length - 1]);
}

// ============================================================================================ paper (story.js) and the postcard device
// prepPaper(img): story.prepCard + the shared grade baked in (cards are world-layer assets: same grade as the stages)
// (look book U9: warm off-white paper edge of 2-4 px, no blue rim); o.edge px of paper edge on the source image (default 3)
export function prepPaper(img, o = {}) {
  const e = o.edge ?? 3, w = img.width + 2 * e, h = img.height + 2 * e, pc = P.cv(w, h), g = pc.getContext('2d');
  // paper edge: the cut-out's silhouette dilated by e px in warm off-white, the photo on top
  const sil = P.cv(w, h), sg = sil.getContext('2d'); sg.drawImage(img, e, e); sg.globalCompositeOperation = 'source-in'; sg.fillStyle = '#F1E8D6'; sg.fillRect(0, 0, w, h);
  for (let a = 0; a < 16; a++) g.drawImage(sil, Math.round(Math.cos(a / 16 * 6.283) * e), Math.round(Math.sin(a / 16 * 6.283) * e));
  g.drawImage(img, e, e);
  const c = P.prepCard(pc, Object.assign({ light: 'left', rimColor: '#FFE9C8', rimAlpha: 0.35 }, o));
  gradeCanvas(c.img); return c;
}
// image -> perspective quad (corners tl, tr, br, bl in screen px) by affine triangles on an n x n grid (no ctx.filter)
export function drawQuad(ctx, img, q, n = 8, alpha = 1) {
  const W = img.width, H = img.height, at = (u, v) => { const top = [lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u)], bot = [lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u)]; return [lerp(top[0], bot[0], v), lerp(top[1], bot[1], v)]; };
  ctx.save(); ctx.globalAlpha *= alpha;
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const u0 = i / n, u1 = (i + 1) / n, v0 = j / n, v1 = (j + 1) / n;
    for (const tri of [[[u0, v0], [u1, v0], [u0, v1]], [[u1, v0], [u1, v1], [u0, v1]]]) {
      const s = tri.map(([u, v]) => [u * W, v * H]), d = tri.map(([u, v]) => at(u, v));
      const [[x0, y0], [x1, y1], [x2, y2]] = s, [[X0, Y0], [X1, Y1], [X2, Y2]] = d;
      const den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0); if (Math.abs(den) < 1e-9) continue;
      const a = ((X1 - X0) * (y2 - y0) - (X2 - X0) * (y1 - y0)) / den, b = ((X2 - X0) * (x1 - x0) - (X1 - X0) * (x2 - x0)) / den;
      const c = ((Y1 - Y0) * (y2 - y0) - (Y2 - Y0) * (y1 - y0)) / den, dd = ((Y2 - Y0) * (x1 - x0) - (Y1 - Y0) * (x2 - x0)) / den;
      // grow each triangle by ~0.6 px around its centroid to hide hairline seams between triangles
      const cx = (X0 + X1 + X2) / 3, cy = (Y0 + Y1 + Y2) / 3, gr = 0.6;
      ctx.save(); ctx.beginPath();
      for (const [X, Y] of d) { const L = Math.hypot(X - cx, Y - cy) || 1; ctx.lineTo(X + (X - cx) / L * gr, Y + (Y - cy) / L * gr); }
      ctx.closePath(); ctx.clip();
      ctx.transform(a, c, b, dd, X0 - a * x0 - b * y0, Y0 - c * x0 - dd * y0);
      ctx.drawImage(img, 0, 0); ctx.restore();
    }
  }
  ctx.restore();
}
// postcard canvas: off-white card (#F6F1E4), photo inset, place name in big postcard type, warm paper edge
// The title is Anton with the ʻokina as U+2018 (okina()), cap 26 % of the card height, so a card 450 px wide on screen carries a
// 64 px-class title; on screen the card itself must be at least that big when its name has to be read.
export function makePostcard(photo, title, o = {}) {
  const w = o.w || 1200, h = o.h || 800, c = P.cv(w, h), g = c.getContext('2d');
  g.fillStyle = '#F6F1E4'; g.fillRect(0, 0, w, h);
  const m = w * 0.045; const pw = w - 2 * m, ph = h - 2 * m;
  const s = Math.max(pw / photo.width, ph / photo.height), sw = pw / s, sh = ph / s;
  g.drawImage(photo, (photo.width - sw) / 2, (photo.height - sh) / 2, sw, sh, m, m, pw, ph);
  g.strokeStyle = 'rgba(120,90,60,0.35)'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, w - 3, h - 3);
  if (title) { const tt = okina(title), cap = h * 0.26, size = cap / 0.86; g.font = `400 ${size}px "Anton"`; g.textAlign = 'center'; g.lineJoin = 'round';
    const y = h - m - h * 0.07; g.lineWidth = cap * 0.18; g.strokeStyle = 'rgba(5,9,18,0.88)'; g.strokeText(tt, w / 2, y); g.fillStyle = '#FFD23F'; g.fillText(tt, w / 2, y); }
  return gradeCanvas(c);
}
// postcard dropped onto the terrain: lands flat on a lon/lat footprint (centre, width/height km, rotation deg) at height hm,
// p = drop progress 0..1 (falls from above the frame with a slight flutter), lift = hinge lift 0..1 (raises the far edge)
export function drawPostcard(ctx, view, card, o) {
  const { lon, lat } = o, wk = o.wKm, hk = o.hKm ?? wk * card.height / card.width, rot = (o.rot || 0) * D2R;
  const hm = o.hm ?? (view.S?.heightAt ? Math.max(view.S.heightAt(lon, lat), view.level ?? 0) + 25 : 0);   // default: lies on the ground there
  const cl = Math.cos(lat * D2R), p = clamp(o.p ?? 1), lift = clamp(o.lift ?? 0);
  const corner = (sx, sy, up) => { const dx = sx * wk / 2, dy = sy * hk / 2; const ex = dx * Math.cos(rot) - dy * Math.sin(rot), ny = dx * Math.sin(rot) + dy * Math.cos(rot);
    return view.project(lon + ex / (KM_DEG * cl), lat + ny / KM_DEG, hm + up); };
  const fall = (1 - E.out(p)) * (o.dropM ?? 30000), farUp = lift * hk * 1000 * 0.35;
  const q = [corner(-1, 1, fall + farUp), corner(1, 1, fall + farUp), corner(1, -1, fall), corner(-1, -1, fall)];
  if (q.some(v => !v)) return null;
  // soft contact shadow under the card (stronger as it lands)
  const sh = [corner(-1, 1, 0), corner(1, 1, 0), corner(1, -1, 0), corner(-1, -1, 0)];
  if (sh.every(Boolean)) { ctx.save(); ctx.globalAlpha = 0.35 * E.in(p); ctx.fillStyle = 'rgba(0,0,0,1)'; ctx.beginPath(); sh.forEach(([x, y], i) => i ? ctx.lineTo(x + 6, y + 8) : ctx.moveTo(x + 6, y + 8)); ctx.closePath(); ctx.fill(); ctx.restore(); }
  drawQuad(ctx, card, q, 6, o.alpha ?? 1);
  return q;
}
// a paper standee standing on the terrain at lon/lat: hPx = screen height (35-40 % of frame height per the playbook), hinge 0..1,
// hop = lift in px, squash; returns {x, y, top, w, h} (anchor the name plate to the base)
// The standee has a fold-out paper base tab on the ground and two shadows: a soft dark contact shadow right under the base and a
// blurred directional cast shadow of its silhouette along the ground away from the sun (o.shadowDir: screen dx per px of height,
// default 0.55 = sun from the left). No slab.
export function drawStandee(ctx, view, card, o) {
  const b = view.project(o.lon, o.lat, o.hm); if (!b) return null;
  const h = o.hPx, w = h * card.w / card.h, hinge = clamp(o.hinge || 0), sq = o.squash || 0, hop = o.hop || 0, A = o.alpha ?? 1;
  const hs = h * Math.cos(hinge * Math.PI / 2 * 0.96) * (1 - sq), ws = w * (1 + sq * 0.55);
  ctx.save();
  const gl = clamp(1 - hop / (h * 0.9));
  // cast shadow: the silhouette sheared along the ground (flattened to 22 %), blurred by its down-scaled copy
  if (card.sil && gl > 0.01) {
    if (!card.silFade) { const c = P.cv(card.sil.width, card.sil.height), g = c.getContext('2d'); g.drawImage(card.sil, 0, 0); g.globalCompositeOperation = 'destination-in';
      const lg = g.createLinearGradient(0, 0, 0, c.height); lg.addColorStop(0, 'rgba(0,0,0,0)'); lg.addColorStop(1, 'rgba(0,0,0,1)'); g.fillStyle = lg; g.fillRect(0, 0, c.width, c.height); card.silFade = c; }
    const k = o.shadowDir ?? 0.55; ctx.save(); ctx.globalAlpha = 0.26 * gl * A; ctx.translate(b[0], b[1]); ctx.transform(1, 0, k, 0.22, 0, 0);
    ctx.drawImage(card.silFade, -ws / 2, -hs, ws, hs); ctx.restore(); }
  // contact shadow under the base
  const rg = ctx.createRadialGradient(b[0], b[1], 0, b[0], b[1], ws * 0.7);
  rg.addColorStop(0, `rgba(0,0,0,${0.62 * gl * A})`); rg.addColorStop(0.55, `rgba(0,0,0,${0.3 * gl * A})`); rg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.save(); ctx.translate(b[0], b[1]); ctx.scale(1, 0.2); ctx.translate(-b[0], -b[1]); ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(b[0], b[1], ws * 0.7, 0, 7); ctx.fill(); ctx.restore();
  // fold-out base tab (paper, lit from the sky, a darker crease where it meets the card)
  const tb = ws * 0.16, tw2 = ws * 0.46;
  ctx.save(); ctx.globalAlpha *= A; ctx.translate(b[0], b[1] - hop * 0.15);
  ctx.fillStyle = '#E3D9C4'; ctx.beginPath(); ctx.moveTo(-tw2, 0); ctx.lineTo(tw2, 0); ctx.lineTo(tw2 * 1.12, tb * 0.55); ctx.lineTo(-tw2 * 1.12, tb * 0.55); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(60,45,30,0.35)'; ctx.fillRect(-tw2, -1, tw2 * 2, Math.max(2, tb * 0.08)); ctx.restore();
  ctx.translate(b[0], b[1] - hop); ctx.rotate(o.lean || 0); ctx.globalAlpha = A;
  ctx.drawImage(card.img, -ws / 2, -hs, ws, hs);
  ctx.restore();
  return { x: b[0], y: b[1] - hop, top: b[1] - hop - hs, w: ws, h: hs };
}

// ============================================================================================ UI: phone-first type with enforced floors
// Floors (PLAYBOOK_craft 9 / production 16): must-read caps >= 64 px, any text >= 48 px, headline <= 4 words, kicker <= 2 words
// (an explicit `qualifier: true` kicker may hold a mandatory qualifier up to 4 words: logged), one text block per frame,
// <= 10 visible words, must-read text above y = 670 (top 62 %) and below the top 8 %. Violations log '[typeqc] FAIL ...'
// (Q.strict throws). Caps under a floor are raised to the floor, never drawn small.
T.FLOOR.must = 64; T.FLOOR.any = 48;
export const CAP = { number: 170, headline: 108, title: 160, label: 64, kicker: 52, gauge: 112 };
// Anton draws the ʻokina (U+02BB) as a small mid-dot; Anton text uses U+2018 instead (Barlow keeps U+02BB). T.width agrees.
export const okina = (s, fam = T.FAM.head) => (fam === T.FAM.head || fam === T.FAM.num) ? String(s).replace(/ʻ/g, '‘') : String(s);
export function makeUI(api) {
  const W = api.W, H = api.H, sc = H / 1080, px = (v) => v * sc;
  const Q = { blocks: [], labels: [], obst: [], pts: [], words: 0, fails: [], gauge: false };
  const fail = (m) => { Q.fails.push(m); if (api.Q?.strict) throw new Error('[typeqc] ' + m); };
  const floor = (cap, role) => { const f = role === 'kicker' ? T.FLOOR.any : T.FLOOR.must; if (cap < f) { fail(`${role} cap ${cap} < ${f}`); return f; } return cap; };
  const words = (s) => String(s).trim().split(/\s+/).filter(Boolean).length;
  const zone = (box, s, a) => { if (a < 0.5) return; if (box.y + box.h > px(670) + 1) fail(`'${s}' below y=670 (bottom ${Math.round(box.y + box.h)})`); if (box.y < px(86) - 1) fail(`'${s}' in the top 8 % (y ${Math.round(box.y)})`);
    if (box.x < px(96) - 1 || box.x + box.w > W - px(96) + 1) fail(`'${s}' outside the 5 % safe margin`); };
  const inSafe = (b) => b.x >= px(96) - 1 && b.x + b.w <= W - px(96) + 1 && b.y >= px(86) - 1 && b.y + b.h <= px(670) + 1;
  const hit = (a, b, m) => a.x < b.x + b.w + m && a.x + a.w > b.x - m && a.y < b.y + b.h + m && a.y + a.h > b.y - m;
  // free: clear of every text block, label and obstacle (by m px) and of every obstacle point (outlines, pins)
  const free = (b, m = px(12), skip = null) => !Q.blocks.some(x => x !== skip && hit(b, x, m)) && !Q.labels.some(x => hit(b, x, m)) && !Q.obst.some(x => hit(b, x, m))
    && !Q.pts.some(([x, y]) => x > b.x - m && x < b.x + b.w + m && y > b.y - m && y < b.y + b.h + m);
  const famOf = (role) => role === 'headline' || role === 'number' || role === 'title' ? T.FAM.head : T.FAM.label;
  const UI = {
    px, Q, C: T.C, okina,
    begin() { Q.blocks = []; Q.labels = []; Q.obst = []; Q.pts = []; Q.words = 0; Q.fails = []; Q.gauge = false; T.QC.begin(); },
    report(f) {
      if (Q.blocks.length > 1) fail(`${Q.blocks.length} text blocks`);
      if (Q.words > 10) fail(`${Q.words} visible words`);
      const r = T.QC.report(); if (r.fail.length) fail('caps under 48: ' + r.fail.join(', '));
      return { frame: f, minCap: r.min, blocks: Q.blocks.length, labels: Q.labels.length, words: Q.words, fails: Q.fails.slice() };
    },
    // OBSTACLES for the placers (call before block/label): a screen box {x, y, w, h} (a height bar, a subject's projected bbox) or
    // the points of screen runs (outlines, coasts: every `step`-th point)
    avoid(box) { if (box) Q.obst.push(box); return box; },
    avoidRuns(runs, step = 4) { for (const r of runs) for (let i = 0; i < r.length; i += step) Q.pts.push(r[i]); },
    boxOf(pts, pad = 0) { const xs = pts.filter(Boolean).map(p => p[0]), ys = pts.filter(Boolean).map(p => p[1]); if (!xs.length) return null;
      const x = Math.min(...xs) - pad, y = Math.min(...ys) - pad; return { x, y, w: Math.max(...xs) + pad - x, h: Math.max(...ys) + pad - y }; },
    // TEXT BLOCK: lines [{text|words:[{w,c}], role:'headline'|'kicker'|'title'|'label', cap?, qualifier?, color?}], anchored at (x, y) =
    // top-left ('left'), top-right ('right') or top-centre ('center'). o: p 0..1 build (plate wipe, then words rise); out 0..1 exit;
    // bar: accent colour (null = none); barP: accent bar wipe; plate:false = ink type straight on the sky (thumbnail treatment: no
    // plate, no bar, no padding; colour o.color, e.g. PAL.ink); wordTimes: reveal whole words on their spoken words (with grow:true
    // the plate widens with the revealed words); at: [{x, y, anchor}, ...] candidate anchors: the first whose box is inside the safe
    // area and clear of obstacles by o.clear px (default 40) wins (x, y are then ignored). Returns the box (box.inner: number slot).
    block(ctx, lines, x, y, o = {}) {
      const p = o.p ?? 1, out = o.out ?? 0, A = (o.alpha ?? 1) * (1 - E.in(clamp(out)));
      if (p <= 0 || A <= 0.002) return null;
      const L = lines.map(l => { const role = l.role || 'headline', cap = floor(l.cap || CAP[role] || CAP.headline, role === 'kicker' ? 'kicker' : 'must');
        const fam = l.fam === 'label' ? T.FAM.label : l.fam === 'head' ? T.FAM.head : famOf(role);
        const ws = (l.words ? l.words.map(w => typeof w === 'string' ? { w } : w) : String(l.text).split(' ').map(w => ({ w }))).map(w => Object.assign({}, w, { w: okina(w.w, fam) }));
        const n = ws.length; if (role === 'headline' && n > 4) fail(`headline '${ws.map(w => w.w).join(' ')}' has ${n} words`);
        if (role === 'kicker' && n > 2 && !(l.qualifier && n <= 4)) fail(`kicker '${ws.map(w => w.w).join(' ')}' has ${n} words`);
        const sp = px(cap) * (fam === T.FAM.label ? 0.32 : 0.26);
        const wid = ws.map(w => T.width(ctx, w.w, { fam, cap })); const tot = wid.reduce((a, b) => a + b, 0) + sp * (n - 1);
        return { role, cap, ws, fam, sp, wid, tot, n, color: l.color }; });
      const plate = o.plate !== false;
      const padX = plate ? px(o.padX ?? 34) : 0, padY = plate ? px(o.padY ?? 26) : 0, gap = px(o.gap ?? 20), bar = (!plate || o.bar === null) ? 0 : px(8);
      const ex = o.extra || { w: 0, h: 0 };
      const tw = Math.max(ex.w, ...L.map(l => l.tot)), th = L.reduce((a, l) => a + px(l.cap), 0) + gap * (L.length - 1) + (ex.h ? gap + ex.h : 0);
      const w = tw + padX * 2 + bar, h = th + padY * 2;
      const geo = (X, Y, an) => ({ x: an === 'right' ? X - w : an === 'center' ? X - w / 2 : X, y: Y, w, h, anchor: an });
      let g = geo(x, y, o.anchor);
      if (o.at) { const cands = o.at.map(c => geo(c.x, c.y, c.anchor ?? o.anchor)); g = cands.find(c => inSafe(c) && free(c, px(o.clear ?? 40))) || cands[0];
        if (api.Q?.dbgLabel) api.log(`[dbg block] ${cands.map(c => [c.x, c.y].map(Math.round) + ':' + inSafe(c) + ':' + free(c, px(o.clear ?? 40))).join(' ')}`); }
      const bx = g.x, by = g.y, anchor = g.anchor;
      const box = { x: bx, y: by, w, h };
      Q.blocks.push(box); Q.words += L.reduce((a, l) => a + l.n, 0); zone(box, L.map(l => l.ws.map(w => w.w).join(' ')).join(' / '), A);
      if (Q.obst.some(b => hit(box, b, 0))) fail(`block '${L[0].ws.map(w => w.w).join(' ')}' overlaps an obstacle`);
      // per-word reveal progress (wordTimes) and the plate width that follows it (grow)
      let k0 = 0; const prs = L.map(l => l.ws.map((wd, i) => { const t0 = o.wordTimes ? o.wordTimes[k0] : null; k0++;
        return t0 != null ? E.outExpoN(clamp((o.lt - t0) / 0.3)) : o.platePre ? 1 : E.outExpoN(clamp((p - 0.25 - i * 0.08) / 0.5)); }));
      let growW = w, growH = h;
      if (o.grow && o.wordTimes) {
        growW = bar + padX * 2 + Math.max(...L.map((l, li) => l.ws.reduce((a, wd, i) => a + (l.wid[i] + (i ? l.sp : 0)) * E.inOut(clamp(prs[li][i] * 1.6)), 0)));
        // stacked lines: the plate also grows down line by line (never a mostly empty plate)
        if (L.length > 1) growH = padY * 2 + L.reduce((a, l, li) => a + (px(l.cap) + (li ? gap : 0)) * E.inOut(clamp(Math.max(...prs[li]) * 1.6)), 0);
      }
      const pw = o.platePre ? 1 : E.outExpoN(clamp(p / 0.45));
      ctx.save(); ctx.globalAlpha *= A;
      if (plate) {
        const ww = Math.min(bar + (w - bar) * pw, growW), hh = Math.min(h, growH);
        ctx.fillStyle = 'rgba(0,0,0,0.28)'; F.round(ctx, bx + px(2), by + px(6), ww, hh, px(6)); ctx.fill();
        ctx.fillStyle = o.bg || PAL.plate; F.round(ctx, bx, by, ww, hh, px(6)); ctx.fill();
        if (bar) { const bp = clamp(o.barP ?? 1); ctx.save(); F.round(ctx, bx, by, ww, hh, px(6)); ctx.clip(); ctx.fillStyle = o.bar || PAL.hero; ctx.fillRect(bx, by + hh * (1 - bp) / 2, bar, hh * bp); ctx.restore(); }
      }
      let cy = by + padY;
      L.forEach((l, li) => {
        cy += px(l.cap);
        let cx = bx + bar + padX + (anchor === 'right' && o.textAlign !== 'left' ? tw - l.tot : anchor === 'center' ? (tw - l.tot) / 2 : 0);
        l.ws.forEach((wd, i) => {
          const pr = prs[li][i];
          if (pr > 0.002) { ctx.save(); ctx.beginPath(); ctx.rect(bx - (plate ? 0 : px(20)), by - (plate ? 0 : px(20)), w + (plate ? 0 : px(40)), h + (plate ? 0 : px(40))); ctx.clip();
            T.txt(ctx, wd.w, cx, cy + (1 - pr) * px(l.cap) * 0.5, Object.assign({ fam: l.fam, cap: l.cap, color: wd.c || l.color || o.color || PAL.text, alpha: clamp(pr * 1.3), shadow: false },
              o.glow ? { shadow: true, shadowColor: 'rgba(255,255,255,0.43)', shadowBlur: px(16), shadowY: 0 } : {})); ctx.restore(); }
          cx += l.wid[i] + l.sp;
        });
        cy += gap;
      });
      ctx.restore();
      box.inner = { x: bx + bar + padX, y: cy - gap + (ex.h ? gap : 0), w: tw, h: ex.h };   // where an inner number line goes
      return box;
    },
    // MAP LABEL: plate + pin + leader to a screen anchor (a point ON the surface). side 'auto' tries o.order (default above, left,
    // right, below: the label sits above or beside its subject, never on it) and takes the first placement inside the safe area that
    // is clear of text blocks, labels, obstacles (ui.avoid / ui.avoidRuns) and its own pin; fades as its anchor leaves the frame.
    label(ctx, s, ax, ay, o = {}) {
      const p = o.p ?? 1; if (p <= 0 || (o.alpha ?? 1) <= 0.002) return null;
      const cap = floor(o.cap || CAP.label, 'must'), capP = px(cap), d = px(o.dist ?? 70), rise = o.rise ?? capP * 0.4;
      const w = T.width(ctx, s, { cap }) + capP + Math.max(px(9), capP * 0.15), h = capP * 1.95;
      const place = { right: [ax + d, ay - rise - h / 2], left: [ax - d - w, ay - rise - h / 2], above: [ax - w / 2, ay - d - h], below: [ax - w / 2, ay + d],
        'above-left': [ax - d * 0.7 - w, ay - d * 0.7 - h], 'above-right': [ax + d * 0.7, ay - d * 0.7 - h] };
      const pinBox = { x: ax - px(16), y: ay - px(16), w: px(32), h: px(32) };
      const fits = ([x, y]) => { const b = { x, y, w, h }; return inSafe(b) && free(b) && !hit(b, pinBox, px(6)); };
      const order = o.side && o.side !== 'auto' ? [o.side] : (o.order || ['above', 'above-left', 'left', 'above-right', 'right', 'below']);
      // nothing fits: the first placement inside the safe area (overlap is logged by the zone/obstacle checks), never the top 8 %
      const side = order.find(k => fits(place[k])) || order.find(k => inSafe({ x: place[k][0], y: place[k][1], w, h }));
      if (!side) { if (api.Q?.dbgLabel) api.log(`[dbg label] ${s}: no placement inside the safe area, not drawn`); return null; }   // its anchor is at the frame edge
      if (api.Q?.dbgLabel) api.log(`[dbg label] ${s} anchor ${ax.toFixed(0)},${ay.toFixed(0)} side ${side} fits ${order.map(k => k + ':' + fits(place[k])).join(' ')}`);
      const [bx, by] = place[side];
      const inF = Math.min(ax, W - ax, ay, H - ay); const A = (o.alpha ?? 1) * clamp((inF + px(20)) / px(80));
      if (A <= 0.002) return null;
      const an = side.endsWith('left') && side !== 'left' ? 'right' : side === 'left' ? 'right' : side === 'right' || side === 'above-right' ? 'left' : 'center';
      const box = T.label(ctx, s, an === 'right' ? bx + w : an === 'left' ? bx : bx + w / 2, by + h / 2, { cap, p, accent: o.accent || PAL.hero, anchor: an, leader: o.pin === false ? null : [ax, ay], t: o.t, alpha: A });
      if (box) { Q.labels.push(box); Q.words += words(s); zone(box, s, A * p); }
      return box;
    },
    // odometer NUMBER with grouping commas: value (may be fractional while rolling), digits fixed by `to`; prefix word, unit.
    // o.win = {x, y, w, h}: the window digits roll inside (the gauge plate); default a box per digit. o.lead0 = false hides
    // leading zeros (they fade in as the value reaches them). align 'right' keeps the last digit fixed while the value grows.
    number(ctx, v, x, y, o = {}) {
      const cap = floor(o.cap || CAP.number, 'must'), capP = px(cap), fam = T.FAM.num, to = o.to ?? v, digits = String(Math.floor(Math.abs(to))).length;
      const size = T.sizeFor(fam, capP); ctx.save(); ctx.font = `400 ${size}px "${fam}"`; const dw = ctx.measureText('0').width * 1.02, comma = ctx.measureText(',').width * 1.1; ctx.restore();
      const n = Math.max(0, Math.abs(v)), col = o.color || PAL.yellow, A = o.alpha ?? 1;
      const groups = Math.floor((digits - 1) / 3), numW = dw * digits + comma * groups + (o.minus ? dw * 0.62 : 0);
      const ucap = o.unitCap || cap * 0.62, uw = o.unit ? T.width(ctx, o.unit, { fam, cap: ucap }) + px(16) : 0;
      const pcap = o.prefixCap || 64, pw = o.prefix ? T.width(ctx, o.prefix, { fam: T.FAM.label, cap: pcap }) + px(18) : 0;
      const tot = pw + numW + uw; if (o.measure) return { w: tot, h: capP };
      let cx = o.align === 'right' ? x - tot : o.align === 'center' ? x - tot / 2 : x;
      const win = o.win, lead0 = o.lead0 !== false;
      if (o.prefix) { T.txt(ctx, o.prefix, cx, y, { fam: T.FAM.label, cap: pcap, color: o.prefixColor || PAL.text, stroke: !win, alpha: A }); cx += pw; Q.words += words(o.prefix); }
      if (o.minus) {
        // with hidden leading zeros the minus sits just left of the first visible digit (slides as digits fade in)
        let hid = 0; if (o.lead0 === false) for (let i = digits - 1; i > 0; i--) { const base = Math.pow(10, i); hid += 1 - clamp((n - base * 0.92) / (base * 0.08)) ; if (n >= base) break; }
        const mx = cx + hid * dw + (hid >= 3 ? comma : 0);
        const ma = A * clamp(o.minusA ?? 1); ctx.save(); ctx.globalAlpha *= ma; if (!win) { ctx.fillStyle = 'rgba(5,9,18,0.92)'; const mw = dw * 0.5, mh = capP * 0.11 + px(6); ctx.fillRect(mx + dw * 0.04 - px(3), y - capP * 0.5 - mh / 2, mw + px(6), mh); }
        ctx.fillStyle = col; ctx.fillRect(mx + dw * 0.04, y - capP * 0.5 - capP * 0.055, dw * 0.5, capP * 0.11); ctx.restore(); cx += dw * 0.62; }
      for (let i = digits - 1; i >= 0; i--) {
        const base = Math.pow(10, i), d = Math.floor(n / base) % 10, rest = n % base, roll = i === 0 ? n % 1 : Math.max(0, rest - (base - 1));
        const la = lead0 || i === 0 ? 1 : clamp((n - base * 0.92) / (base * 0.08));
        if (la > 0.002) {
          ctx.save(); ctx.beginPath(); if (win) ctx.rect(win.x, win.y, win.w, win.h); else ctx.rect(cx - capP * 0.3, y - capP * 1.1, dw + capP * 0.6, capP * 1.19); ctx.clip();
          const aOut = clamp(1 - roll * 1.6), aIn = clamp((roll - 0.25) * 1.6), st = !win;
          if (aOut > 0.002) T.txt(ctx, String(d), cx + dw / 2, y - roll * capP * 1.3, { fam, cap, color: col, align: 'center', stroke: st, alpha: A * aOut * la });
          if (roll > 0.001 && aIn > 0.002) T.txt(ctx, String((d + 1) % 10), cx + dw / 2, y + (1 - roll) * capP * 1.3, { fam, cap, color: col, align: 'center', stroke: st, alpha: A * aIn * la });
          ctx.restore();
        }
        cx += dw;
        if (i > 0 && i % 3 === 0) { const ca = lead0 ? 1 : clamp((n - base * 0.92) / (base * 0.08)); if (ca > 0.002) T.txt(ctx, ',', cx + px(2), y, { fam, cap, color: col, stroke: !win, alpha: A * ca }); cx += comma; }
      }
      if (o.unit) { T.txt(ctx, o.unit, cx + px(16), y, { fam, cap: ucap, color: col, stroke: !win, alpha: A }); Q.words += words(o.unit); }
      Q.words += 1;
      return { x: o.align === 'right' ? x - tot : o.align === 'center' ? x - tot / 2 : x, y: y - capP, w: tot, h: capP };
    },
    // persistent SEA LEVEL gauge, fixed top-left, plate 150 px (13.9 % of the height): accent bar, a 64 px water column whose surface
    // marker follows the level on the shot's own linear range (range m: 150 for Maui Nui, so -122 m drops it 81 %), the title, and the
    // current value in the plate (Anton cap 112, yellow, the plate is the odometer window). o: p slide-in 0..1, out fade-out 0..1 (fade it
    // out whenever no level is changing), level (m), range (m), unit 'FT' (default) or 'M', to (max shown value, fixes the digit count),
    // value (false: no digits), pulse 0..1 (a hero-number moment: yellow rim). Returns the plate box.
    gauge(ctx, o = {}) {
      const p = o.p ?? 1, A0 = (o.alpha ?? 1) * (1 - E.in(clamp(o.out ?? 0))); if (p <= 0 || A0 <= 0.002) return null;
      const title = o.title || 'SEA LEVEL', cap = floor(o.cap || 64, 'must'), ncap = floor(o.ncap || CAP.gauge, 'must'), unit = o.unit || 'FT';
      const k = unit === 'FT' ? 3.28084 : 1, lv = o.level ?? 0, val = Math.max(0, -lv * k), to = o.to ?? Math.max(10, Math.round((o.range ?? 6000) * k));
      const h = px(o.h ?? 150), colW = px(64), tw = T.width(ctx, title, { cap });
      const nOpt = { cap: ncap, to, unit, unitCap: 72, lead0: false, minus: true };
      const nm = o.value === false ? { w: 0 } : UI.number(ctx, 0, 0, 0, Object.assign({ measure: true }, nOpt));
      const w = px(8) + px(24) + colW + px(28) + tw + (o.value === false ? 0 : px(30) + nm.w) + px(32);
      const x = px(96) - (1 - E.outExpoN(p)) * (w + px(120)), y = px(96);
      ctx.save(); ctx.globalAlpha *= A0 * clamp(p * 2);
      ctx.fillStyle = 'rgba(0,0,0,0.28)'; F.round(ctx, x + px(2), y + px(6), w, h, px(6)); ctx.fill();
      ctx.fillStyle = PAL.plate; F.round(ctx, x, y, w, h, px(6)); ctx.fill();
      if (o.pulse > 0) { ctx.save(); ctx.globalAlpha *= clamp(o.pulse); ctx.strokeStyle = PAL.yellow; ctx.lineWidth = px(5); F.round(ctx, x - px(2), y - px(2), w + px(4), h + px(4), px(8)); ctx.stroke(); ctx.restore(); }
      ctx.fillStyle = PAL.cyan; ctx.fillRect(x, y, px(8), h);
      // water column: today's sea level is the top tick; the marker drops with the level (linear over the shot's range)
      const cx0 = x + px(32), cy0 = y + px(22), ch = h - px(44), f = o.scale === 'sqrt' ? Math.sqrt(clamp(-lv / (o.range ?? 6000))) : clamp(-lv / (o.range ?? 6000));
      ctx.fillStyle = 'rgba(244,246,250,0.16)'; ctx.fillRect(cx0, cy0, colW, ch);
      const sy = cy0 + ch * f; ctx.fillStyle = PAL.cyan; ctx.fillRect(cx0, sy, colW, cy0 + ch - sy);
      ctx.fillStyle = PAL.text; ctx.fillRect(cx0 - px(8), cy0 - px(3), colW + px(16), px(6));      // today's level tick
      ctx.fillStyle = '#FFFFFF'; ctx.fillRect(cx0 - px(5), sy - px(5), colW + px(10), px(10));        // live surface marker
      const tx = cx0 + colW + px(28);
      T.txt(ctx, title, tx, y + h / 2 + px(cap) / 2, { cap, color: PAL.text, shadow: false });
      if (o.value !== false) {
        const win = { x: tx + tw + px(14), y: y + px(4), w: nm.w + px(30), h: h - px(8) };
        UI.number(ctx, val, x + w - px(32), y + h / 2 + px(ncap) / 2, Object.assign({ align: 'right', win, minusA: clamp(val / 3) }, nOpt));
        Q.words -= 0;   // number() counts the value and its unit
      }
      ctx.restore();
      Q.gauge = true; Q.words += words(title);
      const box = { x, y, w, h }; zone(box, 'gauge', A0 * clamp(p * 2) * (p > 0.95 ? 1 : 0));
      return box;
    },
    // crisp lines (UI layer): outline of a shape (5-6 px white + under-stroke + glow), meaningful line (9-12 px), arrow (type.js spec)
    outline(ctx, runs, o = {}) { T.outline(ctx, runs, Object.assign({ width: 6 }, o)); },
    line(ctx, runs, o = {}) { T.line(ctx, runs, Object.assign({ width: 10 }, o)); },
    arrow: T.arrow, pin: T.pin,
    // hero fill in screen space (when the shape is not on a stage that can fill it): 55-66 % hero orange
    fill(ctx, runs, o = {}) { ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1) * (o.fill ?? 0.58); ctx.fillStyle = o.color || PAL.hero; ctx.beginPath();
      for (const r of runs) r.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.fill('evenodd'); ctx.restore(); },
  };
  return UI;
}

// ============================================================================================ transitions
// xfade(a, b, dur): b fades in over dur while a keeps drawing underneath until b's fade ends (no dip to black: PLAYBOOK_craft 7).
// The incoming shot's own UI starts only when its dissolve has finished (b.uiFrom); a scale jump (globe to terrain) should use
// one continuous move instead (look book S14: log-altitude zoom over 3-5 s) or a match-cut at the same lon/lat/heading.
export function xfade(a, b, dur = 0.5) { b.fadeIn = dur; b.uiFrom = b.t0 + dur; a.t1 = Math.max(a.t1, b.t0 + dur); return [a, b]; }
// seq(shots, {fade}): consecutive shots, each b.t0 = previous t1 (as given), crossfaded by `fade` s (0 = hard cut)
export function seq(shots, o = {}) { for (let i = 1; i < shots.length; i++) if (o.fade) xfade(shots[i - 1], shots[i], o.fade); return shots; }
// whip(c0, c1, p): camera blend for a whip-pan (6-8 frames); use as a camera key ease: E.inOutExpo
export const WHIP = E.inOutExpo;

// chapter card (chapters 2-6; edit.js adds them): drawn last (layer 90) on a near-opaque plate over the incoming chapter's moving
// first shot, 0.26 s dissolve in, 1.1 s hold, 0.26 s dissolve out (PLAYBOOK_craft 8). It is the frame's one text block while it shows.
export function chapterCard(kit, n) {
  const ch = kit.K.chapter(n), ui = kit.ui, W = kit.W, H = kit.H, D = 0.26 + 1.1 + 0.26;
  return { id: 'card-' + n, t0: ch.card, t1: ch.card + D, layer: 90, draw(ctx, lt) {
    const a = clamp(lt / 0.26) * (1 - clamp((lt - 0.26 - 1.1) / 0.26));
    ui.block(ctx, [{ text: String(ch.title).toUpperCase(), role: 'headline', cap: 104 }], W / 2, ui.px(300), { anchor: 'center', platePre: true, alpha: a, bg: 'rgba(6,9,15,0.92)', bar: PAL.hero });
  } };
}
// ============================================================================================ kit = everything a chapter needs
export async function setup(api) {
  await T.init(api.H);
  // load the latin-ext and spacing-modifier subsets too (ʻokina U+02BB, kahakō vowels, U+2212) before any text is drawn
  await Promise.all(['400 100px "Anton"', '800 100px "Barlow Condensed"'].map(f => document.fonts.load(f, 'ĀāĒēĪīŌōŪūʻ−ABC0123456789')));
  const hub = new Hub(api);
  try { const r = await fetch('/ep/ep02/data/regions.json'); if (r.ok) { const j = await r.json(); hub.regionIndex = Array.isArray(j.regions) ? Object.fromEntries(j.regions.map(x => [x.name, x])) : (j.regions || {}); } } catch (e) { /* no index yet */ }
  const K = makeTime(api);
  const ui = makeUI(api);
  const kit = { api, hub, K, ui, W: api.W, H: api.H, F, T, P, E, PAL, CAMS, PLACES, PRESETS, REGIONS, SEABED, Section, okina,
    // camera: CAMS name | object | keys [{t, cam: name|object, ease}] (use the same height mode, alt or agl, in every key of a move)
    cam(c, lt) { const Z = { shiftX: 0, shiftY: 0, roll: 0 }; const R = (x) => Object.assign({}, Z, typeof x === 'string' ? CAMS[x] : x);
      if (typeof c === 'function') return R(c(lt));
      if (Array.isArray(c)) return keyAt(c.map(k => Object.assign(R(k.cam), { t: k.t, ease: k.ease })), lt); return R(c); },
    terrainShot: (s) => terrainShot(kit, s), cutawayShot: (s) => cutawayShot(kit, s), blockShot: (s) => blockShot(kit, s), cineGlobeShot: (s) => cineGlobeShot(kit, s),
    island: async (o) => island(await hub.terrain(o.region || 'bigisland', o.vex || 1, o.stage || {}), o),
    // land-bridge weights: new land of `joined` within dKm of two of `parts` (today's islands), on the same grid (see bridges())
    bridges: (joined, parts, dKm) => bridges(joined.g, joined.mask, parts.map(p => p.mask), dKm),
    maskTexture, makePostcard, drawPostcard, drawStandee, drawQuad, prepPaper, gradeCanvas, flight, mixState, keyAt, valAt, xfade, seq,
    perfLog: [],
  };
  return kit;
}
// frame hooks for edit.js: a layer -1000 scene resets per-frame QC; post() logs QC + per-stage timings
export function frameStart(kit) { return { id: 'frame-start', t0: 0, t1: 1e9, layer: -1000, draw: (ctx, lt, t) => { kit.hub.frame = Math.round(t * kit.api.FPS); kit.hub.perf = {}; kit.ui.begin(); kit._t0 = performance.now(); } }; }
export function frameEnd(kit, f) {
  const r = kit.ui.report(f), ms = performance.now() - (kit._t0 || performance.now());
  const perf = Object.entries(kit.hub.perf).map(([k, v]) => `${k}=${v.toFixed(0)}`).join(' ');
  if (r.fails.length) kit.api.log(`[typeqc] FAIL f=${f} ${r.fails.join(' | ')}`);
  if (kit.api.Q?.qc) kit.api.log(`[typeqc] f=${f} minCap=${r.minCap} blocks=${r.blocks} labels=${r.labels} words=${r.words}`);
  kit.api.log(`[perf] f=${f} total=${ms.toFixed(0)}ms ${perf}`);
}
