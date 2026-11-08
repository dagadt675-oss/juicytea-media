// HawaiiStage: real DEM terrain + seafloor around the Hawaiian Islands with an animatable water level, for thumbnail-grade hero stills.
// Forked from lab/drain/terrain.js (TerrainStage) so lab_drain.html keeps working. Units: 1 world unit = 1 km. Pure function of state.
// Differences from TerrainStage:
//  - sun shadows are ray-marched in the shader over the height textures (any sun az/el, any vertical exaggeration, no bake per light);
//  - seabed material: dark basalt flanks, dark brown pelagic sediment on gentle slopes, a little cream reef only on the shallow shelf
//    (never the pale tan "drained basin" ramp of the clone channels);
//  - old-shoreline devices: a pale "bathtub ring" band just below the former sea level and/or one luminous waterline on the 0 m contour;
//  - water: turquoise palette option, a screen-space foam rim at the waterline and a luminous shallow edge;
//  - grade: exposure, contrast, saturation, warm/cool split, vignette; haze is height-aware relative to the drained floor.
import * as THREE from 'three';

export const R_EARTH = 6371.0, KM_DEG = 111.32;

const COMMON = /* glsl */`
uniform vec3 camPos; uniform vec3 sunDir; uniform float horizonDip;
uniform vec3 zenithCol, horizonCol, hazeCol, sunCol, glowCol;
uniform float fogDens, fogH, fogBg, fogBase;
vec3 skyColor(vec3 d){
  float y = clamp(d.y + horizonDip, 0.0, 1.0);
  vec3 c = mix(horizonCol, zenithCol, pow(y, 0.45));
  float mu = max(dot(d, sunDir), 0.0);
  c += glowCol * (pow(mu, 5.0) * 0.35 + pow(mu, 64.0) * 0.8);
  c = mix(c, hazeCol, exp(-y * 16.0) * 0.45);
  return c;
}
vec3 inscatter(vec3 d){
  float mu = max(dot(d, sunDir), 0.0);
  return hazeCol + glowCol * (pow(mu, 5.0) * 0.40);
}
vec3 aerial(vec3 col, vec3 wp, out float T){
  vec3 v = wp - camPos; float dist = length(v); vec3 d = v / max(dist, 1e-4);
  float y0 = max(camPos.y - fogBase, 0.0), y1 = max(wp.y - fogBase, 0.0), dy = y1 - y0;
  float od = abs(dy) < 1e-3 ? fogDens * exp(-y0 / fogH) * dist : fogDens * dist * fogH * (exp(-y0 / fogH) - exp(-y1 / fogH)) / dy;
  od += fogBg * dist;
  T = exp(-od);
  return col * T + inscatter(d) * (1.0 - T);
}
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
// noise at frequency f (cycles per degree) faded to its mean where one cycle spans fewer than ~4 pixels (pf = pixel footprint in degrees)
float fbmL(vec2 ll, float f, float pf){ return mix(0.47, fbm(ll * f), 1.0 - smoothstep(0.12, 0.45, f * pf)); }
`;

// height lookup across both grids (hero inside its bbox, wide skirt elsewhere) + sun visibility by ray-marching toward the sun
const HEIGHT = /* glsl */`
uniform sampler2D hHero, hSkirt; uniform vec4 bbHero, bbSkirt; uniform float vex, sunEl, penumbra;
float hAt(vec2 ll){
  vec2 uh = (ll - bbHero.xy) / (bbHero.zw - bbHero.xy);
  if (uh.x > 0.0 && uh.y > 0.0 && uh.x < 1.0 && uh.y < 1.0) return texture2D(hHero, uh).r;
  return texture2D(hSkirt, (ll - bbSkirt.xy) / (bbSkirt.zw - bbSkirt.xy)).r;
}
float sunVis(vec2 ll, float h0){
  vec2 hd = normalize(vec2(sunDir.x, -sunDir.z) + 1e-6);
  vec2 dir = vec2(hd.x / (${KM_DEG} * cos(radians(ll.y))), hd.y / ${KM_DEG});
  float best = -1.0, s = 0.18;
  for (int i = 0; i < 38; i++) {
    float dz = (hAt(ll + dir * s) - h0) * vex * 0.001 - s * s / ${(2 * R_EARTH).toFixed(1)};
    best = max(best, dz / s); s *= 1.2;
  }
  return clamp((sunEl - atan(best)) / penumbra + 0.5, 0.0, 1.0);
}
`;

const TERRAIN_VS = /* glsl */`
uniform vec3 camPos; uniform vec4 hole; uniform float holeDrop; uniform vec4 bb;
varying vec2 vUv; varying vec3 vW;
void main(){
  vUv = uv; vec3 p = position;
  vec2 ll = bb.xy + uv * (bb.zw - bb.xy);
  if (holeDrop > 0.0 && ll.x > hole.x && ll.x < hole.z && ll.y > hole.y && ll.y < hole.w) p.y -= holeDrop;
  vec2 d = p.xz - camPos.xz; p.y -= dot(d, d) / (2.0 * ${R_EARTH.toFixed(1)});
  vW = p;
  gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;

const TERRAIN_FS = /* glsl */`
${COMMON}
${HEIGHT}
uniform sampler2D hTex, aoTex, colTex; uniform vec2 texel; uniform vec4 bb;
uniform float level, ringH, sunI, skyI, dbg, landSat, landGain, seaRelief, shadows;
uniform vec3 basaltCol, sedCol, reefCol, tubCol, lineCol;
uniform float reefAmt, tubM, tubAmt, oldLine, lineW, detail;
varying vec2 vUv; varying vec3 vW;
float Hm(vec2 uv){ return texture2D(hTex, uv).r; }
vec3 seabed(float h, float slope, float cav, vec2 ll, float pf){
  float dep = -h;
  float n = fbm(ll * 6.0), n2 = fbmL(ll + 3.0, 33.0, pf), n3 = fbmL(ll + n * 0.02, 170.0, pf);
  // sediment ponds on gentle slopes (abyssal plain, moat), bare basalt on the flanks and slide blocks
  float rocky = smoothstep(0.035, 0.11, slope + (n2 - 0.5) * 0.05);
  vec3 c = mix(sedCol, basaltCol, rocky);
  // shallow carbonate shelf (cream reef), only where it is both shallow and gentle
  float shelf = (1.0 - smoothstep(70.0, 190.0, dep)) * (1.0 - smoothstep(0.03, 0.10, slope));
  c = mix(c, reefCol, shelf * reefAmt);
  c *= 0.85 + 0.28 * n + 0.14 * (n2 - 0.5) + 0.12 * (n3 - 0.5) * detail;
  c *= clamp(1.0 - cav * 1.5, 0.66, 1.25);
  return c;
}
void main(){
  vec2 ll = bb.xy + vUv * (bb.zw - bb.xy);
  float lat = radians(ll.y);
  float h = Hm(vUv);
  vec2 fp = max(texel, fwidth(vUv) * 0.75);
  float pf = max(fwidth(ll.x), fwidth(ll.y));
  float hl = Hm(vUv - vec2(fp.x, 0.0)), hr = Hm(vUv + vec2(fp.x, 0.0)), hd = Hm(vUv - vec2(0.0, fp.y)), hu = Hm(vUv + vec2(0.0, fp.y));
  float dxk = (bb.z - bb.x) * fp.x * ${KM_DEG} * cos(lat), dyk = (bb.w - bb.y) * fp.y * ${KM_DEG};
  float gx = (hr - hl) * vex * 0.001 / (2.0 * dxk), gy = (hu - hd) * vex * 0.001 / (2.0 * dyk);
  float rk = mix(seaRelief, 1.0, smoothstep(-40.0, 0.0, h));
  // procedural micro-relief on the seabed (sonar grids are 100-450 m; this keeps close flanks from looking like plastic)
  float sub = 1.0 - smoothstep(-30.0, 10.0, h);
  vec2 q = ll * 180.0; float e = 0.37;
  vec2 dn = vec2(fbm(q + vec2(e, 0.0)) - fbm(q - vec2(e, 0.0)), fbm(q + vec2(0.0, e)) - fbm(q - vec2(0.0, e))) * 0.16 * detail * sub * (1.0 - smoothstep(0.12, 0.45, 180.0 * pf));
  float slope = length(vec2(gx, gy)) / vex;
  // gullies and lava ribs on steep submarine flanks: ridged noise stretched along the fall line (about 0.7 km apart, km long)
  vec2 fall = vec2(gx, gy) / (length(vec2(gx, gy)) + 1e-6), perp = vec2(-fall.y, fall.x);
  vec2 km = vec2(ll.x * ${KM_DEG} * cos(lat), ll.y * ${KM_DEG});
  float acr = dot(km, perp), alo = dot(km, fall), gf = 1.4;
  float steep = smoothstep(0.05, 0.16, slope) * sub * (1.0 - smoothstep(0.12, 0.45, gf * pf * ${KM_DEG})) * detail;
  float rid = 1.0 - abs(2.0 * fbm(vec2(acr * gf, alo * gf * 0.12)) - 1.0);
  float rid2 = 1.0 - abs(2.0 * fbm(vec2((acr + 0.06) * gf, alo * gf * 0.12)) - 1.0);
  vec2 pg = perp * (rid2 - rid) / 0.06 * 0.09 * steep;
  vec3 n = normalize(vec3(-gx * rk + dn.x - pg.x, 1.0, gy * rk - dn.y + pg.y));
  float cav = clamp((hl + hr + hd + hu - 4.0 * h) / max(fp.x * 4096.0, 1.0) / 90.0, -0.25, 0.25);
  float ao = texture2D(aoTex, vUv).r;
  float shadow = shadows > 0.5 ? sunVis(ll, h) : 1.0;
  vec3 land = texture2D(colTex, vUv).rgb; float l0 = dot(land, vec3(0.2126, 0.7152, 0.0722)); land = max(mix(vec3(l0), land, landSat), 0.0) * landGain * (0.86 + 0.20 * fbmL(ll, 520.0, pf) + 0.10 * (fbmL(ll, 2100.0, pf) - 0.5));
  vec3 alb = mix(seabed(h, slope, cav, ll, pf) * mix(1.0, 0.70 + 0.55 * rid, steep), land, smoothstep(-6.0, 4.0, h));
  float exposed = step(h, -1.0) * step(level, h);
  float above = h - level;
  // bathtub ring: pale mineral crust in a band just below the former sea level, broken up by noise
  float tb = exposed * (1.0 - smoothstep(tubM * 0.35, tubM, -h)) * smoothstep(0.25, 0.6, fbmL(ll, 420.0, pf) + 0.25 * (1.0 + h / tubM));
  alb = mix(alb, tubCol, tb * tubAmt);
  // dark wet band right above the new waterline
  float ring = exposed * (1.0 - smoothstep(0.0, ringH, above));
  alb *= 1.0 - 0.5 * ring;
  float ndl = max(dot(n, sunDir), 0.0);
  vec3 sky = mix(hazeCol, zenithCol, 0.55);
  vec3 col = alb * (sunCol * sunI * ndl * shadow + sky * skyI * ao * (0.55 + 0.45 * n.y) + vec3(0.05, 0.04, 0.03) * (1.0 - n.y));
  vec3 v = normalize(camPos - vW); vec3 hv = normalize(v + sunDir);
  col += sunCol * sunI * ring * 0.16 * pow(max(dot(n, hv), 0.0), 40.0) * shadow;
  // one luminous line on the former coastline (0 m contour), constant width in pixels
  float fw = max(fwidth(h), 1e-3);
  float dl = abs(h + 0.5) / fw;
  float cl = oldLine * step(level, -25.0) * (1.0 - smoothstep(lineW * 0.5, lineW * 0.5 + 1.0, dl));
  float glow = oldLine * step(level, -25.0) * exp(-dl / (lineW * 1.6)) * 0.35;
  float T; vec3 colA = aerial(col, vW, T);
  colA = mix(colA, lineCol, clamp(cl, 0.0, 1.0)) + lineCol * glow * T;
  if (dbg > 0.5) { vec3 o = dbg < 1.5 ? vec3(0.5 + h / 8000.0, 0.5 + h / 8000.0, h < 0.0 ? 1.0 : 0.0) : dbg < 2.5 ? vec3(T) : dbg < 3.5 ? alb : vec3(shadow, ao, 0.0); gl_FragColor = vec4(o * 0.6, 1.0); return; }
  gl_FragColor = vec4(colA, 1.0);
}`;

const WATER_VS = /* glsl */`
uniform vec3 camPos; uniform float yLevel; uniform vec4 bb;
varying vec3 vW; varying vec2 vLL;
void main(){
  vLL = bb.xy + uv * (bb.zw - bb.xy);
  vec3 p = position; p.y = yLevel;
  vec2 d = p.xz - camPos.xz; p.y -= dot(d, d) / (2.0 * ${R_EARTH.toFixed(1)});
  vW = p; gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;

const WATER_FS = /* glsl */`
${COMMON}
${HEIGHT}
uniform float level, time, sunI, dbg, foamAmt, foamPx, foamM, edgeGlow, fresMax;
uniform vec3 wShallow, wMid, wDeep;
varying vec3 vW; varying vec2 vLL;
float hBlend(vec2 ll){
  vec2 us = (ll - bbSkirt.xy) / (bbSkirt.zw - bbSkirt.xy);
  float hs = texture2D(hSkirt, us).r;
  vec2 uh = (ll - bbHero.xy) / (bbHero.zw - bbHero.xy);
  if (uh.x < 0.0 || uh.y < 0.0 || uh.x > 1.0 || uh.y > 1.0) return hs;
  vec2 e = min(uh, 1.0 - uh); float w = smoothstep(0.0, 0.025, min(e.x, e.y));
  return mix(hs, texture2D(hHero, uh).r, w);
}
void main(){
  float h = hBlend(vLL);
  float depth = level - h;
  if (depth <= 0.0) discard;
  vec2 p = vW.xz;
  float slick = fbm(p * 0.045 + vec2(time * 0.004, -time * 0.002));
  vec2 g = vec2(fbm(p * 0.6 + vec2(time * 0.03, 0.0)) - fbm(p * 0.6 + vec2(0.37, 0.0) + vec2(time * 0.03, 0.0)),
                fbm(p * 0.6 + vec2(0.0, 0.37) + vec2(0.0, time * 0.02)) - fbm(p * 0.6 + vec2(0.0, time * 0.02)));
  float rough = mix(0.035, 0.11, slick);
  vec3 n = normalize(vec3(g.x * rough * 2.0, 1.0, g.y * rough * 2.0));
  vec3 v = normalize(camPos - vW);
  float fres = 0.02 + fresMax * pow(1.0 - max(dot(n, v), 0.0), 5.0);
  vec3 refl = skyColor(reflect(-v, n)) * mix(vec3(1.0), wShallow * 2.2 + 0.25, 0.35);
  vec3 hv = normalize(v + sunDir); float nh = max(dot(n, hv), 0.0);
  float a2 = rough * rough; float dd = nh * nh * (a2 - 1.0) + 1.0; float spec = a2 / (3.14159 * dd * dd);
  vec3 glint = sunCol * sunI * spec * 0.08 * fres;
  vec3 body = mix(wShallow, wMid, smoothstep(6.0, 120.0, depth)); body = mix(body, wDeep, smoothstep(150.0, 900.0, depth));
  body *= 0.55 + 0.45 * sunI / 3.0;
  // foam rim + luminous shallow edge, sized in screen pixels via the depth derivative
  float fwD = max(fwidth(depth), 0.05);
  float fr = foamPx * fwD + foamM;
  float pf = max(fwidth(vLL.x), fwidth(vLL.y));
  float fn = fbmL(vLL, 2400.0, pf) * 0.7 + fbmL(vLL, 300.0, pf) * 0.6;
  float foam = foamAmt * (1.0 - smoothstep(fr * (0.35 + 0.5 * fn), fr * (0.7 + 0.6 * fn), depth));
  float edge = edgeGlow * (1.0 - smoothstep(fr, fr * 3.0, depth));
  body = mix(body, wShallow * 1.9, edge * 0.7);
  float aBody = 1.0 - exp(-depth / 7.0);
  float alpha = 1.0 - (1.0 - aBody) * (1.0 - fres);
  vec3 prem = body * aBody * (1.0 - fres) + refl * fres + glint;
  float lit = max(dot(vec3(0.0, 1.0, 0.0), sunDir), 0.15);
  vec3 foamC = vec3(0.92, 0.96, 0.98) * (sunCol * sunI * lit * 0.32 + mix(hazeCol, zenithCol, 0.5) * 0.45);
  prem = mix(prem, foamC, clamp(foam, 0.0, 1.0)); alpha = max(alpha, clamp(foam, 0.0, 1.0));
  float T; vec3 dummy = aerial(vec3(0.0), vW, T);
  vec3 d = normalize(vW - camPos);
  prem = prem * T + inscatter(d) * (1.0 - T) * alpha;
  if (dbg > 4.5) { gl_FragColor = vec4(fract(vLL.x), fract(vLL.y), clamp(depth / 3000.0, 0.0, 1.0), 1.0); return; }
  gl_FragColor = vec4(prem, alpha);
}`;

const SKY_VS = /* glsl */`
varying vec3 vDir; uniform vec3 camPos;
void main(){ vDir = position; vec4 w = vec4(position + camPos, 1.0); gl_Position = projectionMatrix * viewMatrix * w; gl_Position.z = gl_Position.w * 0.99999; }`;
const SKY_FS = /* glsl */`
${COMMON}
varying vec3 vDir;
void main(){ vec3 d = normalize(vDir); gl_FragColor = vec4(skyColor(d), 1.0); }`;

// final pass: exposure, ACES fit, saturation, split-tone, gamma, contrast around mid-grey, vignette, grain
export const POST_FS = /* glsl */`
uniform sampler2D src; uniform float exposure, vignette, grain, seed, sat, contrast, lift; uniform vec2 res; varying vec2 vUv;
vec3 aces(vec3 x){ return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main(){
  vec3 c = texture2D(src, vUv).rgb * exposure;
  c = aces(c);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = max(mix(vec3(l), c, sat), 0.0);
  c += vec3(-0.008, 0.002, 0.012) * (1.0 - smoothstep(0.0, 0.45, l)) + vec3(0.012, 0.004, -0.010) * smoothstep(0.45, 1.0, l);
  c = pow(max(c, 0.0), vec3(1.0 / 2.2));
  c = clamp((c - 0.5) * contrast + 0.5 + lift, 0.0, 1.0);
  vec2 q = vUv - 0.5; q.x *= res.x / res.y;
  c *= 1.0 - vignette * smoothstep(0.35, 1.05, length(q));
  c += (h12(gl_FragCoord.xy + seed * 61.7) - 0.5) * grain;
  gl_FragColor = vec4(c, 1.0);
}`;
export const POST_VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';

export async function loadImage(url) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('img ' + url)); i.src = url; }); }
export function decodeH16(img, meta) {  // RG 16-bit -> Float32 metres, rows flipped so row 0 = south
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
  const px = g.getImageData(0, 0, c.width, c.height).data, W = c.width, H = c.height, out = new Float32Array(W * H);
  for (let r = 0; r < H; r++) { const src = r * W, dst = (H - 1 - r) * W; for (let i = 0; i < W; i++) { const k = (src + i) * 4; out[dst + i] = ((px[k] << 8 | px[k + 1]) / 65535) * meta.hrange + meta.hmin; } }
  return { data: out, W, H };
}
export function heightTexture(hm) {
  const half = new Uint16Array(hm.data.length); for (let i = 0; i < half.length; i++) half[i] = THREE.DataUtils.toHalfFloat(hm.data[i]);
  const t = new THREE.DataTexture(half, hm.W, hm.H, THREE.RedFormat, THREE.HalfFloatType);
  t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true; return t;
}
export function sampleH(hm, u, v) {  // bilinear, u,v in 0..1 (v from south)
  const x = Math.min(Math.max(u * (hm.W - 1), 0), hm.W - 1.001), y = Math.min(Math.max(v * (hm.H - 1), 0), hm.H - 1.001);
  const i = x | 0, j = y | 0, fx = x - i, fy = y - j, d = hm.data, W = hm.W;
  return d[j * W + i] * (1 - fx) * (1 - fy) + d[j * W + i + 1] * fx * (1 - fy) + d[(j + 1) * W + i] * (1 - fx) * fy + d[(j + 1) * W + i + 1] * fx * fy;
}
export const C = (hex, k = 1) => new THREE.Color(hex).multiplyScalar(k);  // sRGB hex -> linear
const V3 = (a) => new THREE.Vector3(...a);

// looks: sky, haze and sun colours (sRGB hex), intensities
export const LOOKS = {
  gold: { zenith: '#1b58bd', horizon: '#a9c9ee', haze: ['#a6bfdd', 0.70], sun: '#ffc68c', glow: ['#ffae66', 0.40], sunI: 3.6, skyI: 0.62 },
  day: { zenith: '#1553b5', horizon: '#9fc4ee', haze: ['#a5c0e0', 0.74], sun: '#fff3e2', glow: ['#ffe6c8', 0.5], sunI: 3.5, skyI: 0.70 },
  warm: { zenith: '#1e5fbf', horizon: '#b9d0ea', haze: ['#adc3dd', 0.72], sun: '#ffd6a8', glow: ['#ffbc7c', 0.40], sunI: 3.6, skyI: 0.64 },
};
export const WATERS = {  // linear RGB: shallow, mid, deep
  turq: [[0.020, 0.40, 0.42], [0.006, 0.17, 0.25], [0.002, 0.060, 0.125]],
  lagoon: [[0.020, 0.42, 0.40], [0.005, 0.19, 0.22], [0.002, 0.085, 0.12]],
  ocean: [[0.020, 0.22, 0.26], [0.006, 0.090, 0.16], [0.003, 0.035, 0.085]],
};

export class HawaiiStage {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H; this.o = o;
    this.R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.R.setPixelRatio(1); this.R.setSize(W, H, false); this.R.autoClear = true;
    this.rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: o.samples ?? 4, depthBuffer: true });
    this.scene = new THREE.Scene();
    this.cam = new THREE.PerspectiveCamera(o.fov ?? 30, W / H, 0.5, 9000);
    this.level = 0; this.time = 0;
  }
  async load(dir) {
    const meta = this.meta = await (await fetch(dir + '/meta.json')).json();
    this.vex = this.o.vex ?? meta.vex ?? 1.0;
    this.c0 = this.o.origin ?? { lon: -155.6, lat: 19.6 };
    const [hI, sI] = await Promise.all([loadImage(dir + '/hero_h16.png'), loadImage(dir + '/skirt_h16.png')]);
    this.hHero = decodeH16(hI, meta); this.hSkirt = decodeH16(sI, meta);
    const TL = new THREE.TextureLoader();
    const tex = async (u, srgb) => { const t = await TL.loadAsync(dir + '/' + u); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; t.minFilter = THREE.LinearMipmapLinearFilter; return t; };
    const [heroCol, heroAO, skCol, skAO] = await Promise.all([tex('hero_color.jpg', true), tex('hero_ao.png', false), tex('skirt_color.jpg', true), tex('skirt_ao.png', false)]);
    this.U = {
      camPos: { value: new THREE.Vector3() }, sunDir: { value: new THREE.Vector3(0, 1, 0) }, horizonDip: { value: 0 },
      zenithCol: { value: C('#2c64a8') }, horizonCol: { value: C('#a9c3dc') }, hazeCol: { value: C('#aec2d6', 0.8) },
      sunCol: { value: C('#fff1de') }, glowCol: { value: C('#ffe2b8', 0.9) },
      fogDens: { value: this.o.fogDens ?? 0.0028 }, fogH: { value: this.o.fogH ?? 6.0 }, fogBg: { value: this.o.fogBg ?? 0.00012 }, fogBase: { value: 0 },
      sunEl: { value: 0.4 }, penumbra: { value: THREE.MathUtils.degToRad(1.4) }, vex: { value: this.vex },
    };
    const hT = heightTexture(this.hHero), sT = heightTexture(this.hSkirt);
    const hb = meta.hero_bbox, sb = meta.skirt_bbox;
    const HU = { hHero: { value: hT }, hSkirt: { value: sT }, bbHero: { value: new THREE.Vector4(...hb) }, bbSkirt: { value: new THREE.Vector4(...sb) } };
    const terrMat = (hTex, aoTex, colTex, bb, hm, holeDrop) => new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, HU, {
        hTex: { value: hTex }, aoTex: { value: aoTex }, colTex: { value: colTex }, texel: { value: new THREE.Vector2(1 / hm.W, 1 / hm.H) },
        bb: { value: new THREE.Vector4(...bb) }, hole: { value: new THREE.Vector4(...hb) }, holeDrop: { value: holeDrop },
        level: { value: 0 }, ringH: { value: 40 }, dbg: { value: 0 }, landSat: { value: 1.2 }, landGain: { value: 1.15 }, seaRelief: { value: 1.0 },
        sunI: { value: 3.2 }, skyI: { value: 0.9 }, shadows: { value: 1 },
        basaltCol: { value: V3([0.033, 0.034, 0.038]) }, sedCol: { value: V3([0.066, 0.062, 0.060]) }, reefCol: { value: V3([0.16, 0.165, 0.155]) },
        tubCol: { value: V3([0.42, 0.42, 0.40]) }, lineCol: { value: V3([0.55, 1.6, 1.9]) },
        reefAmt: { value: 0.45 }, tubM: { value: 90 }, tubAmt: { value: 0 }, oldLine: { value: 0 }, lineW: { value: 2.2 }, detail: { value: 1.0 },
      }), vertexShader: TERRAIN_VS, fragmentShader: TERRAIN_FS,
    });
    this.heroMat = terrMat(hT, heroAO, heroCol, hb, this.hHero, 0);
    this.skirtMat = terrMat(sT, skAO, skCol, sb, this.hSkirt, 4.0 + 6.0 * this.vex);
    this.scene.add(new THREE.Mesh(this.grid(hb, this.hHero, this.o.heroGrid || [1500, 1500]), this.heroMat));
    this.scene.add(new THREE.Mesh(this.grid(sb, this.hSkirt, this.o.skirtGrid || [900, 680]), this.skirtMat));
    this.waterMat = new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, HU, {
        bb: { value: new THREE.Vector4(...sb) }, level: { value: 0 }, yLevel: { value: 0 }, time: { value: 0 }, sunI: { value: 3.2 }, dbg: { value: 0 },
        foamAmt: { value: 0 }, foamPx: { value: 2.5 }, foamM: { value: 2.0 }, edgeGlow: { value: 0.6 }, fresMax: { value: 0.55 },
        wShallow: { value: V3(WATERS.turq[0]) }, wMid: { value: V3(WATERS.turq[1]) }, wDeep: { value: V3(WATERS.turq[2]) },
      }),
      vertexShader: WATER_VS, fragmentShader: WATER_FS, transparent: true, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
    });
    const water = new THREE.Mesh(this.grid(sb, null, [600, 450]), this.waterMat); water.renderOrder = 2; this.scene.add(water);
    const sky = new THREE.Mesh(new THREE.SphereGeometry(6000, 64, 32), new THREE.ShaderMaterial({ uniforms: this.U, vertexShader: SKY_VS, fragmentShader: SKY_FS, side: THREE.BackSide, depthWrite: false }));
    sky.renderOrder = -1; sky.frustumCulled = false; this.scene.add(sky);
    this.postMat = new THREE.ShaderMaterial({
      uniforms: { src: { value: this.rt.texture }, exposure: { value: 1.2 }, vignette: { value: 0.20 }, grain: { value: 0.012 }, seed: { value: 0 }, sat: { value: 1.2 }, contrast: { value: 1.1 }, lift: { value: 0 }, res: { value: new THREE.Vector2(this.W, this.H) } },
      vertexShader: POST_VS, fragmentShader: POST_FS, depthTest: false, depthWrite: false,
    });
    this.postScene = new THREE.Scene(); const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.postMat); q.frustumCulled = false; this.postScene.add(q);
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  xyz(lon, lat, hm = 0) { return new THREE.Vector3((lon - this.c0.lon) * KM_DEG * Math.cos(lat * Math.PI / 180), hm * this.vex * 0.001, -(lat - this.c0.lat) * KM_DEG); }
  grid(bb, hm, [nx, ny]) {
    const pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2);
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const u = i / (nx - 1), v = j / (ny - 1), lon = bb[0] + u * (bb[2] - bb[0]), lat = bb[1] + v * (bb[3] - bb[1]), k = j * nx + i;
      const p = this.xyz(lon, lat, hm ? sampleH(hm, u, v) : 0); pos[k * 3] = p.x; pos[k * 3 + 1] = p.y; pos[k * 3 + 2] = p.z; uv[k * 2] = u; uv[k * 2 + 1] = v;
    }
    const idx = new Uint32Array((nx - 1) * (ny - 1) * 6); let n = 0;
    for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1; idx[n++] = a; idx[n++] = b; idx[n++] = c; idx[n++] = b; idx[n++] = d; idx[n++] = c; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5); return g;
  }
  heightAt(lon, lat) {
    const hb = this.meta.hero_bbox, sb = this.meta.skirt_bbox;
    if (lon > hb[0] && lon < hb[2] && lat > hb[1] && lat < hb[3]) return sampleH(this.hHero, (lon - hb[0]) / (hb[2] - hb[0]), (lat - hb[1]) / (hb[3] - hb[1]));
    return sampleH(this.hSkirt, (lon - sb[0]) / (sb[2] - sb[0]), (lat - sb[1]) / (sb[3] - sb[1]));
  }
  // camera: lon/lat + alt (km above sea level, may be negative in drained shots) or agl (km above the ground/water under the camera);
  // aim with heading/pitch (deg) or a target tLon/tLat/tH (m; default = ground height there)
  setCamera(c) {
    const p = this.xyz(c.lon, c.lat, 0);
    const gnd = Math.max(this.heightAt(c.lon, c.lat), this.level) * this.vex * 0.001;
    p.y = c.agl != null ? gnd + c.agl : c.alt;
    let t;
    if (c.tLon == null) {
      const hd = THREE.MathUtils.degToRad(c.heading ?? 0), pt = THREE.MathUtils.degToRad(c.pitch ?? -15);
      t = p.clone().add(new THREE.Vector3(Math.sin(hd) * Math.cos(pt), Math.sin(pt), -Math.cos(hd) * Math.cos(pt)).multiplyScalar(100));
    } else {
      t = this.xyz(c.tLon, c.tLat, c.tH ?? Math.max(this.heightAt(c.tLon, c.tLat), this.level)); const d = t.clone().sub(p); t.y -= (d.x * d.x + d.z * d.z) / (2 * R_EARTH);
    }
    this.cam.position.copy(p); this.cam.up.set(0, 1, 0); this.cam.lookAt(t);
    if (c.roll) this.cam.rotateZ(THREE.MathUtils.degToRad(c.roll));
    this.cam.fov = c.fov ?? this.cam.fov; this.cam.updateProjectionMatrix();
    if (c.shiftY) { this.cam.projectionMatrix.elements[9] += c.shiftY; this.cam.projectionMatrixInverse.copy(this.cam.projectionMatrix).invert(); }  // vertical lens shift (keeps verticals straight)
    this.cam.updateMatrixWorld();
    this.U.camPos.value.copy(p); this.U.horizonDip.value = Math.sqrt(2 * Math.max(p.y - gnd, 0.01) / R_EARTH);
    this.camGround = gnd;
  }
  setSun(az, el) {
    const A = THREE.MathUtils.degToRad(az), E = THREE.MathUtils.degToRad(el);
    this.U.sunDir.value.set(Math.sin(A) * Math.cos(E), Math.sin(E), -Math.cos(A) * Math.cos(E)); this.U.sunEl.value = E;
  }
  setLook(name, o = {}) {
    const L = Object.assign({}, LOOKS[name] || LOOKS.day, o);
    this.U.zenithCol.value = C(L.zenith); this.U.horizonCol.value = C(L.horizon); this.U.hazeCol.value = C(L.haze[0], L.haze[1]);
    this.U.sunCol.value = C(L.sun); this.U.glowCol.value = C(L.glow[0], L.glow[1]);
    this.set('sunI', L.sunI); this.set('skyI', L.skyI);
  }
  setWater(name) { const w = WATERS[name] || WATERS.turq; this.set('wShallow', V3(w[0])); this.set('wMid', V3(w[1])); this.set('wDeep', V3(w[2])); }
  setLevel(m) {
    this.level = m; for (const M of [this.heroMat, this.skirtMat, this.waterMat]) M.uniforms.level.value = m; this.waterMat.uniforms.yLevel.value = m * this.vex * 0.001;
    this.U.fogBase.value = Math.max(Math.min(m, 0), -5500) * this.vex * 0.001;  // haze sits on the new floor (water surface or drained seabed)
  }
  set(k, v) { for (const M of [this.heroMat, this.skirtMat, this.waterMat]) if (M.uniforms[k]) M.uniforms[k].value = v; }
  post(k, v) { this.postMat.uniforms[k].value = v; }
  project(lon, lat, hm) {
    const p = this.xyz(lon, lat, hm ?? Math.max(this.heightAt(lon, lat), this.level)); const d = p.clone().sub(this.cam.position); p.y -= (d.x * d.x + d.z * d.z) / (2 * R_EARTH);
    const q = p.project(this.cam); if (q.z > 1) return null; return [(q.x + 1) / 2 * this.W, (1 - q.y) / 2 * this.H];
  }
  render(time = 0, seed = 0) {
    this.waterMat.uniforms.time.value = time; this.postMat.uniforms.seed.value = seed;
    this.R.setRenderTarget(this.rt); this.R.render(this.scene, this.cam);
    this.R.setRenderTarget(null); this.R.render(this.postScene, this.postCam);
    return this.R.domElement;
  }
}
