// CineGlobe: cinematic drop-in replacement for lib/globe.js `Globe` (same public API: init, set, look, setPatch,
// setOverlay, setOverlayURL, refreshOverlay, render, project, disc, starfield, canvas, u, camera).
// What is different:
//   - all shading in LINEAR HDR (textures decoded from sRGB), rendered at ss x resolution (default 2x supersampling)
//   - sunlight reddened by the air it crosses (Kasten-Young air mass) -> physically shaped warm terminator band
//   - aerial perspective over the disc (blue haze growing toward the limb) matched to the limb scattering shell
//   - real cloud layer (VIIRS NOAA-20 + Suomi-NPP, 2025-09-20) with relief shading, cast shadows and drift
//   - GGX ocean sun glint with Fresnel (sharp core + soft halo), relief damped over water (no bathymetry streaks)
//   - city lights as HDR emitters (they bloom), detail-enhanced albedo, 8k relief normals
//   - post chain on the WORLD layer only: dual-filter bloom, analytic depth-of-field (exact ray/sphere depth),
//     filmic tonemap, grade (navy blacks, cool shadows, warm highlights), lens CA, vignette, film grain.
//   UI (labels, outlines, arcs) is drawn by the caller AFTER render(), so text stays crisp and is never bloomed.
//
// USE IN film.html (production):
//   import { CineGlobe } from './lab/globe/cineglobe.js';      (move to lib/ when adopted; asset lab/globe/clouds_8k.jpg -> tex/)
//   api.globe():  globe = new CineGlobe(W, H, { ss: Q.draft ? 1 : 2 }); await globe.init();
//   api.drawGlobe(ctx, state, look, t): ... ctx.drawImage(globe.render(Math.round(t * FPS)), 0, 0);   // frame index seeds the grain
//   EDIT.post: no vignette/grain on top (CineGlobe already applies them to the world layer) -> post = () => {}
//   Do NOT pass ep01's LOOK0 (specAmt .5 / desat .12 were tuned for the old shader); pass only what a shot changes.
// Extra camera-state keys (globeShot keys / sun objects):
//   clouds: 0..1 cloud amount (0.6-0.8 for story shots)      cloudOff: deg of cloud drift (e.g. 0.04 * t)
//   cloudsLow: override the automatic cloud fade on low shots  clear: [lat, lon, innerDeg, outerDeg, amount] clouds part over the subject
//   focus: [lat, lon] DOF focus point (default: the look-at target)   (clear: null switches the clear zone off)
// Extra look keys: haze (aerial perspective, .2-.4), detail (albedo local contrast), oceanTone, waterRelief, cityI, cloudGamma,
//   cloudShadow, ovGain, atmo (limb strength), cloudBump.  Lens / grade per shot: globe.post({ dof, exposure, bloom, vignette, grain,
//   contrast, sat, lift, shadowTint, highTint, ca, sharpen, tm }) - see CINE_DEFAULTS. dof 6-8 on low oblique shots, 0 on whole-globe shots.
import * as THREE from '../../three.module.min.js';
import { dirOf } from '../../lib/globe.js';
export { dirOf, latLonOf, slerpLL, gcDist } from '../../lib/globe.js';

const D2R = Math.PI / 180;
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ---------------------------------------------------------------- shared atmosphere model (exaggerated, art-directable)
const ATMO_COMMON = `
const float PI = 3.14159265;
const vec3 BETA = vec3(0.17, 0.40, 1.0);          // Rayleigh ~ lambda^-4 for 680/550/440 nm, normalised to blue
uniform float tauZ; uniform float tauM; uniform float sunI; uniform vec3 sunCol;
uniform vec3 clearDir; uniform vec2 clearCos; uniform float clearAmt;
float clearMul(vec3 p){ return 1.0 - clearAmt * smoothstep(clearCos.x, clearCos.y, dot(normalize(p), clearDir)); }
float airmass(float mu){ float m = clamp(mu, 0.0, 1.0); float deg = degrees(acos(m)); return 1.0 / (m + 0.15 * pow(max(93.885 - deg, 0.6), -1.253)); }
vec3 tauOf(float m){ return (BETA * tauZ + tauM) * m; }
// sunlight reaching a point whose local sun cosine is mu (normalised so noon light is neutral)
vec3 sunTrans(float mu){ return exp(-tauOf(airmass(mu) - 1.0)); }
float phaseR(float c){ return 0.75 * (1.0 + c * c); }
float phaseM(float c, float g){ float g2 = g * g; return (1.0 - g2) / pow(1.0 + g2 - 2.0 * g * c, 1.5) * 0.25; }
vec3 srgb2lin(vec3 c){ return pow(max(c, 0.0), vec3(2.2)); }
`;

const EARTH_VS = `
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
void main(){ vUv=uv; vN=normalize(mat3(modelMatrix)*normal); vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;

const EARTH_FS = ATMO_COMMON + `
uniform sampler2D dayTex; uniform sampler2D nightTex; uniform sampler2D nrmTex; uniform sampler2D cloudTex; uniform float relief;
uniform sampler2D patchTex; uniform vec4 patchB; uniform float patchOn;
uniform sampler2D ovTex; uniform vec4 ovB; uniform float ovOn; uniform float ovAlpha;
uniform vec3 sunDir; uniform vec3 camPos;
uniform float dim; uniform float desat; uniform float nightAmt; uniform float exposure; uniform float ambient;
uniform vec3 tint; uniform float specAmt; uniform float rimAmt; uniform float flatBase; uniform vec3 flatColor; uniform float ovMul;
uniform float detail; uniform float haze; uniform float waterRelief; uniform float oceanTone; uniform float cloudAmt; uniform float cloudGamma;
uniform float cloudShadow; uniform float cloudOff; uniform float cloudH; uniform float cityI; uniform float ovGain;
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
vec2 ll(vec3 p){ vec3 n=normalize(p); return vec2(atan(-n.z, n.x)*180.0/PI, asin(clamp(n.y,-1.0,1.0))*180.0/PI); }
float cloudA(vec2 g, vec3 p){ float a = textureLod(cloudTex, vec2(fract((g.x + 180.0 + cloudOff) / 360.0), (g.y + 90.0) / 180.0), 1.5).r; return pow(a, cloudGamma) * cloudAmt * clearMul(p); }
float D_ggx(float ndh, float r){ float a = r*r; float a2 = a*a; float d = ndh*ndh*(a2-1.0)+1.0; return a2 / (PI*d*d); }
void main(){
  vec3 n0=normalize(vN); vec3 v=normalize(camPos-vW);
  vec2 g = ll(vW);
  // albedo (sRGB texture), local-contrast boost against a blurred mip: crisper relief and coastlines
  vec3 day = texture2D(dayTex, vUv).rgb;
  vec3 dayB = texture2D(dayTex, vUv, 2.0).rgb;
  day = clamp(day + detail * (day - dayB), 0.0, 1.0);
  if (patchOn > 0.5) {
    vec2 q = vec2((g.x-patchB.x)/(patchB.z-patchB.x), (patchB.w-g.y)/(patchB.w-patchB.y));
    if (q.x>0.0 && q.x<1.0 && q.y>0.0 && q.y<1.0) {
      float e = smoothstep(0.0,0.04,q.x)*smoothstep(0.0,0.04,1.0-q.x)*smoothstep(0.0,0.04,q.y)*smoothstep(0.0,0.04,1.0-q.y);
      vec2 pq = vec2(q.x, 1.0 - q.y);
      vec3 pc = texture2D(patchTex, pq).rgb; vec3 pb = texture2D(patchTex, pq, 2.0).rgb;
      day = mix(day, clamp(pc + detail * (pc - pb), 0.0, 1.0), e);
    }
  }
  float water = smoothstep(0.03,0.16, day.b - max(day.r, day.g*0.9));
  float lum = dot(day, vec3(0.299,0.587,0.114));
  day = mix(day, vec3(lum), desat);
  day = mix(day, flatColor, flatBase);
  water = mix(water, 1.0, flatBase);
  vec3 alb = srgb2lin(day);
  alb *= mix(1.0, oceanTone, water);                       // deeper, richer open ocean
  // relief normal (damped over water: the bathymetry relief reads as streaks)
  vec3 n = n0;
  float rel = relief * mix(1.0, waterRelief, water);
  if (rel > 0.0) {
    vec3 tn = texture2D(nrmTex, vUv).xyz * 2.0 - 1.0;
    vec3 east = normalize(vec3(n0.z, 0.0, -n0.x) + vec3(1e-6));
    vec3 north = cross(n0, east);
    n = normalize(mix(n0, normalize(tn.x*east + tn.y*north + tn.z*n0), rel));
  }
  float mu = dot(n0, sunDir);
  float muV = max(dot(n0, v), 0.0);
  float dl = max(dot(n, sunDir), 0.0);
  float sunVis = smoothstep(-0.015, 0.035, mu);
  vec3 Tsun = sunTrans(mu);
  float SI = sunI * exposure / 1.25;
  // cloud shadow: cloud alpha where the ray toward the sun crosses the cloud shell
  vec3 pc = normalize(vW) + sunDir * (cloudH / max(mu, 0.12));
  float csh = cloudA(ll(pc), pc) * cloudShadow * smoothstep(0.0, 0.15, mu);
  vec3 E = sunCol * SI * Tsun * sunVis * (1.0 - csh);
  // sky (ambient) light: blue, survives into twilight; a faint floor keeps the night side readable
  vec3 sky = vec3(0.30, 0.45, 0.80) * SI * 0.10 * smoothstep(-0.10, 0.30, mu) + vec3(0.22, 0.30, 0.55) * ambient * 0.35;   // faint navy night fill: land shapes still read at night
  vec3 col = alb * (E * dl + sky);
  // ocean sun glint: GGX (sharp core + soft halo) with Schlick Fresnel, on the smooth sphere normal
  vec3 h = normalize(sunDir + v);
  float ndh = max(dot(normalize(mix(n0, n, 0.15)), h), 0.0); float vdh = max(dot(v, h), 0.0);
  float F = 0.02 + 0.98 * pow(1.0 - vdh, 5.0);
  float nl = max(mu, 0.0), nv = max(muV, 0.05);
  float k = 0.05; float G = (nl / (nl*(1.0-k)+k)) * (nv / (nv*(1.0-k)+k));
  float spec = (0.85 * D_ggx(ndh, 0.36) + 0.15 * D_ggx(ndh, 0.20)) * F * G / (4.0 * nv);
  col += E * 2.2 * (1.0 - exp(-spec / 2.2)) * water * specAmt * smoothstep(0.03, 0.22, mu);   // no blob at grazing sun     // soft-clipped: a sheen, never a disc
  // city lights: HDR emitters on the night side, dimmed under clouds handled by the cloud shell
  vec3 night = srgb2lin(texture2D(nightTex, vUv).rgb);
  float nm = 1.0 - smoothstep(-0.10, 0.05, mu);
  col += pow(night, vec3(1.15)) * vec3(1.0, 0.72, 0.40) * cityI * nm * nightAmt;
  col *= (1.0 - dim);
  // highlight overlay (house style): lit by the sun, but with a floor so it always reads
  float ovCov = 0.0;
  if (ovOn > 0.5) {
    vec2 q = vec2((g.x-ovB.x)/(ovB.z-ovB.x), (ovB.w-g.y)/(ovB.w-ovB.y));
    vec2 qdx = dFdx(q), qdy = dFdy(q); float wrapU = 360.0 / (ovB.z - ovB.x);
    if (abs(qdx.x) > 0.5 * wrapU) qdx.x -= sign(qdx.x) * wrapU;
    if (abs(qdy.x) > 0.5 * wrapU) qdy.x -= sign(qdy.x) * wrapU;
    if (q.x>0.0 && q.x<1.0 && q.y>0.0 && q.y<1.0) {
      vec4 o = textureGrad(ovTex, vec2(q.x, 1.0 - q.y), vec2(qdx.x, -qdx.y), vec2(qdy.x, -qdy.y));
      float lightF = mix(0.62 + 0.38 * smoothstep(-0.1, 0.5, mu), (dl * sunVis + 0.08) * 1.1, ovMul);
      vec3 oc = srgb2lin(o.rgb) * ovGain * lightF;
      col = mix(col, oc, o.a * ovAlpha);
      ovCov = o.a * ovAlpha;
    }
  }
  // aerial perspective: extinction + in-scatter along the view path (same model as the limb shell)
  vec3 tv = tauOf(airmass(muV)) * haze * (1.0 - 0.75 * ovCov);
  vec3 ext = exp(-tv);
  float c = dot(-v, sunDir);
  vec3 airLight = sunCol * SI * sunTrans(max(mu, 0.0)) * smoothstep(-0.12, 0.12, mu);
  vec3 ins = airLight * (1.0 - ext) * (phaseR(c) * 0.55 + phaseM(c, 0.70) * 0.9 * tauM / (tauZ * 0.4 + tauM));
  col = col * ext + ins * rimAmt / 0.35;
  col *= tint;
  gl_FragColor = vec4(col, 1.0);
}`;

const CLOUD_FS = ATMO_COMMON + `
uniform sampler2D cloudTex; uniform vec3 sunDir; uniform vec3 camPos; uniform float cloudAmt; uniform float cloudGamma; uniform float cloudOff;
uniform float exposure; uniform float haze; uniform float dim; uniform float bump; uniform float rimAmt; uniform float fadeLow;
uniform sampler2D ovTex; uniform vec4 ovB; uniform float ovOn; uniform float ovAlpha; uniform float ovClear;
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
float cA(vec2 uv){ return pow(texture2D(cloudTex, uv).r, cloudGamma); }
void main(){
  vec2 uv = vec2(fract(vUv.x + cloudOff / 360.0), vUv.y);
  float a = cA(uv) * cloudAmt * clearMul(vW);
  if (ovOn > 0.5 && ovAlpha > 0.0) {
    vec3 nn = normalize(vW); vec2 g = vec2(atan(-nn.z, nn.x)*180.0/PI, asin(clamp(nn.y,-1.0,1.0))*180.0/PI);
    vec2 q = vec2((g.x-ovB.x)/(ovB.z-ovB.x), (ovB.w-g.y)/(ovB.w-ovB.y));
    if (q.x>0.0 && q.x<1.0 && q.y>0.0 && q.y<1.0) a *= 1.0 - ovClear * ovAlpha * smoothstep(0.0, 0.5, textureLod(ovTex, vec2(q.x, 1.0 - q.y), 3.0).a);
  }
  if (a < 0.004) discard;
  vec3 n0 = normalize(vN); vec3 v = normalize(camPos - vW);
  // pseudo relief from the alpha gradient: lit flanks / shaded flanks on thick cloud
  vec2 px = vec2(1.0 / 8192.0, 1.0 / 4096.0) * 2.5;
  float ax = cA(uv + vec2(px.x, 0.0)) - cA(uv - vec2(px.x, 0.0));
  float ay = cA(uv + vec2(0.0, px.y)) - cA(uv - vec2(0.0, px.y));
  vec3 east = normalize(vec3(n0.z, 0.0, -n0.x) + vec3(1e-6)); vec3 north = cross(n0, east);
  vec3 nb = normalize(n0 - bump * (ax * east + ay * north));
  float mu = dot(n0, sunDir);
  float SI = sunI * exposure / 1.25;
  float wrap = clamp(dot(nb, sunDir) * 0.6 + 0.4, 0.0, 1.0);
  vec3 E = sunCol * SI * sunTrans(mu) * smoothstep(-0.06, 0.06, mu);
  vec3 sky = vec3(0.32, 0.45, 0.78) * SI * 0.12 * smoothstep(-0.10, 0.30, mu);
  float alb = mix(0.48, 0.86, smoothstep(0.1, 0.9, a));     // thick cloud is brighter
  vec3 col = alb * (E * wrap + sky);
  float muV = max(dot(n0, v), 0.0);
  vec3 tv = tauOf(airmass(muV)) * haze * 0.55; vec3 ext = exp(-tv);
  float c = dot(-v, sunDir);
  vec3 ins = sunCol * SI * sunTrans(max(mu, 0.0)) * smoothstep(-0.12, 0.12, mu) * (1.0 - ext) * phaseR(c) * 0.55;
  col = (col * ext + ins * rimAmt / 0.35) * (1.0 - dim);
  a *= smoothstep(0.0, 0.10, muV) * fadeLow;
  gl_FragColor = vec4(col, a);
}`;

const ATMO_VS = `varying vec3 vW; void main(){ vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;
// limb shell: closest approach of the view ray, tangent column density, sunlight at that point (reddened, shadowed)
const ATMO_FS = ATMO_COMMON + `
uniform vec3 sunDir; uniform vec3 camPos; uniform float strength; uniform float Hs; uniform float exposure; varying vec3 vW;
void main(){
  vec3 dir = normalize(vW - camPos);
  float tc = -dot(camPos, dir);
  vec3 cpt = camPos + dir * max(tc, 0.0);
  float h = max(length(cpt) - 1.0, 0.0);
  float fade = 1.0 - smoothstep(0.045, 0.072, h);
  float dens = exp(-h / Hs) + 0.10 * exp(-h / (Hs * 3.5));
  vec3 tl = tauOf(24.0) * dens;                               // tangent ray ~ 36 air masses at the surface
  float mu = dot(normalize(cpt), sunDir);
  float shadowMu = -sqrt(max(2.0 * h * 0.14, 0.0));
  float lit = smoothstep(shadowMu - 0.02, shadowMu + 0.16, mu);
  vec3 Ts = exp(-tauOf(max(airmass(max(mu, 0.0)) - 1.0, 0.0)) * exp(-h / (3.0 * Hs)));
  float SI = sunI * exposure / 1.25;
  float c = dot(dir, sunDir);
  vec3 col = sunCol * SI * Ts * lit * (1.0 - exp(-tl)) * (phaseR(c) * 0.55 + phaseM(c, 0.76) * 0.35);
  gl_FragColor = vec4(col * strength * fade, 1.0);
}`;

const FS_VS = 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }';

const BG_FS = `uniform sampler2D tex; uniform vec2 off; uniform float alpha; uniform vec3 top; uniform vec3 bot; uniform float starI; varying vec2 vUv;
void main(){ vec3 s = pow(texture2D(tex, vUv + off).rgb, vec3(2.2));
  vec3 base = mix(bot, top, smoothstep(0.0, 1.0, vUv.y));
  gl_FragColor = vec4(base + s * starI * alpha, 1.0); }`;

const COPY_FS = 'uniform sampler2D t; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(t, vUv).rgb, 1.0); }';
const PRE_FS = `uniform sampler2D t; uniform vec2 px; uniform float thr; varying vec2 vUv;
vec3 f(vec3 c){ float b = max(c.r, max(c.g, c.b)); float k = 0.5 * thr; float s = clamp(b - thr + k, 0.0, 2.0 * k); s = s * s / (4.0 * k + 1e-4); return c * max(s, b - thr) / max(b, 1e-4); }
void main(){ vec3 c = f(texture2D(t, vUv + px * vec2(-1.0,-1.0)).rgb) + f(texture2D(t, vUv + px * vec2(1.0,-1.0)).rgb)
  + f(texture2D(t, vUv + px * vec2(-1.0,1.0)).rgb) + f(texture2D(t, vUv + px * vec2(1.0,1.0)).rgb);
  gl_FragColor = vec4(min(c * 0.25, vec3(40.0)), 1.0); }`;
const DOWN_FS = `uniform sampler2D t; uniform vec2 px; varying vec2 vUv;
void main(){ vec3 c = texture2D(t, vUv).rgb * 4.0 + texture2D(t, vUv + px * vec2(-1.0,-1.0)).rgb + texture2D(t, vUv + px * vec2(1.0,-1.0)).rgb
  + texture2D(t, vUv + px * vec2(-1.0,1.0)).rgb + texture2D(t, vUv + px * vec2(1.0,1.0)).rgb; gl_FragColor = vec4(c / 8.0, 1.0); }`;
const UP_FS = `uniform sampler2D t; uniform vec2 px; uniform float w; varying vec2 vUv;
void main(){ vec3 c = texture2D(t, vUv + px * vec2(-2.0, 0.0)).rgb + texture2D(t, vUv + px * vec2(2.0, 0.0)).rgb
  + texture2D(t, vUv + px * vec2(0.0,-2.0)).rgb + texture2D(t, vUv + px * vec2(0.0, 2.0)).rgb
  + 2.0 * (texture2D(t, vUv + px * vec2(-1.0,-1.0)).rgb + texture2D(t, vUv + px * vec2(1.0,-1.0)).rgb
  + texture2D(t, vUv + px * vec2(-1.0, 1.0)).rgb + texture2D(t, vUv + px * vec2(1.0, 1.0)).rgb); gl_FragColor = vec4(c / 12.0 * w, 1.0); }`;

// final: DOF (exact sphere depth) + bloom + exposure + filmic tonemap + grade + CA + vignette + grain
const FINAL_FS = `uniform sampler2D tHDR; uniform sampler2D tBloom; uniform vec2 res; uniform float exposure; uniform float bloom;
uniform float vig; uniform float grain; uniform float ca; uniform float seed; uniform float sharpen; uniform float dof; uniform float focus; uniform float maxCoc;
uniform mat4 invProj; uniform mat4 camWorld; uniform vec3 camPos; uniform vec3 lift; uniform vec3 shadowTint; uniform vec3 highTint;
uniform float contrast; uniform float sat; uniform float tmMode; varying vec2 vUv;
float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + seed) * 43758.5453); }
float depthAt(vec2 uv){ vec4 p = invProj * vec4(uv * 2.0 - 1.0, 1.0, 1.0); vec3 d = normalize((camWorld * vec4(p.xyz / p.w, 0.0)).xyz);
  float b = dot(camPos, d); float c = dot(camPos, camPos) - 1.0; float h = b*b - c; if (h < 0.0) return 1e4; return -b - sqrt(h); }
float cocAt(vec2 uv){ return clamp(dof * abs(1.0 - focus / depthAt(uv)), 0.0, maxCoc); }
vec3 rrt(vec3 v){ vec3 a = v * (v + 0.0245786) - 0.000090537; vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081; return a / b; }
vec3 aces(vec3 c){
  const mat3 IM = mat3(vec3(0.59719, 0.07600, 0.02840), vec3(0.35458, 0.90834, 0.13383), vec3(0.04823, 0.01566, 0.83777));
  const mat3 OM = mat3(vec3(1.60475, -0.10208, -0.00327), vec3(-0.53108, 1.10813, -0.07276), vec3(-0.07367, -0.00605, 1.07602));
  return clamp(OM * rrt(IM * (c / 0.6)), 0.0, 1.0); }
// hue-preserving variant: tone-map the max channel, keep ratios, roll the overflow toward white
vec3 tmHue(vec3 c){ float m = max(c.r, max(c.g, c.b)); if (m < 1e-5) return c; float t = rrt(vec3(m / 0.6)).x / 1.0; vec3 o = c * (t / m);
  float over = max(m / 0.6 - 1.2, 0.0); return clamp(mix(o, vec3(max(o.r, max(o.g, o.b))), 1.0 - exp(-over * 0.25)), 0.0, 1.0); }
vec3 fetchCA(vec2 uv, vec2 off){ return vec3(texture2D(tHDR, uv + off).r, texture2D(tHDR, uv).g, texture2D(tHDR, uv - off).b); }
void main(){
  vec2 uv = vUv; vec2 cc = uv - 0.5; float r2 = dot(cc, cc);
  vec2 off = cc * r2 * ca * 4.0 / res;
  vec3 col;
  float coc = dof > 0.0 ? cocAt(uv) : 0.0;
  if (coc < 0.6) {
    vec3 c0 = fetchCA(uv, off);
    vec3 nb = (texture2D(tHDR, uv + vec2(1.0, 0.0) / res).rgb + texture2D(tHDR, uv - vec2(1.0, 0.0) / res).rgb
             + texture2D(tHDR, uv + vec2(0.0, 1.0) / res).rgb + texture2D(tHDR, uv - vec2(0.0, 1.0) / res).rgb) * 0.25;
    col = max(c0 + sharpen * (1.0 - coc / 0.6) * clamp(c0 - nb, -0.25, 0.25), 0.0);
  } else {
    vec3 acc = fetchCA(uv, off); float wsum = 1.0;
    for (int i = 0; i < 28; i++) {
      float fi = float(i) + 0.5; float r = sqrt(fi / 28.0) * coc; float a = fi * 2.39996323;
      vec2 o = vec2(cos(a), sin(a)) * r / res;
      float sc = cocAt(uv + o);
      float w = smoothstep(r - 1.0, r + 0.5, max(sc, coc * 0.35));    // samples sharper than their distance do not bleed in
      acc += texture2D(tHDR, uv + o).rgb * w; wsum += w;
    }
    col = acc / wsum;
  }
  col += texture2D(tBloom, uv).rgb * bloom;
  col *= exposure;
  vec3 d = tmMode > 0.5 ? tmHue(col) : aces(col);
  d = pow(d, vec3(1.0 / 2.2));
  // grade in display space
  float l = dot(d, vec3(0.2126, 0.7152, 0.0722));
  d = mix(d, d * shadowTint, (1.0 - smoothstep(0.0, 0.5, l)) * 0.6);
  d = mix(d, d * highTint, smoothstep(0.5, 1.0, l) * 0.6);
  d = (d - 0.5) * contrast + 0.5;
  l = dot(d, vec3(0.2126, 0.7152, 0.0722));
  d = mix(vec3(l), d, sat);
  d = d + lift * (1.0 - d);                                   // navy blacks instead of crushed black
  d *= 1.0 - vig * smoothstep(0.10, 0.80, r2 * 2.2);
  float gn = hash(uv * res) + hash(uv * res + 17.3) - 1.0;
  d += gn * grain * (0.35 + 0.65 * (1.0 - abs(l * 2.0 - 1.0)));
  gl_FragColor = vec4(clamp(d, 0.0, 1.0), 1.0);
}`;

class Pass {
  constructor(frag, uniforms, o = {}) {
    this.u = uniforms;
    this.mat = new THREE.ShaderMaterial({ uniforms, vertexShader: FS_VS, fragmentShader: frag, depthTest: false, depthWrite: false, blending: o.blending ?? THREE.NoBlending, transparent: !!o.blending });
    this.scene = new THREE.Scene(); this.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.mat));
  }
  run(r, cam, target) { r.setRenderTarget(target); r.render(this.scene, cam); }
}

export const CINE_DEFAULTS = {
  ss: 2,              // supersampling factor (1 = draft)
  exposure: 1.0, bloom: 0.20, bloomThr: 0.95, vignette: 0.30, grain: 0.022, ca: 1.0, sharpen: 0.35,
  dof: 0, maxCoc: 6,  // dof = circle of confusion in px per unit of |1 - focus/depth|; 0 = off
  contrast: 1.08, sat: 1.08, lift: [0.010, 0.016, 0.034], shadowTint: [0.94, 1.0, 1.07], highTint: [1.015, 1.0, 0.98], tm: 0,
  spaceTop: [0.0026, 0.0040, 0.0105], spaceBot: [0.0009, 0.0013, 0.0032], starI: 1.25,
};

export class CineGlobe {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H; this.cine = Object.assign({}, CINE_DEFAULTS, o);
    this.renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.renderer.setClearColor(0x000000, 1); this.renderer.autoClear = false;
    this.renderer.setPixelRatio(1); this.renderer.setSize(W, H, false);
    this.renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
    this.canvas = this.renderer.domElement;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(34, W / H, 0.001, 200);
    this.sunDir = new THREE.Vector3(1, 0.3, 0.4).normalize();
    this.state = { lat: 20, lon: 0, alt: 3, tilt: 0, heading: 0, fov: 34, sun: 'camera', sunAz: -35, sunEl: 28 };
    this.focusDist = 1;
  }
  _tex(url, srgbMip = true) {
    return new Promise((res, rej) => new THREE.TextureLoader().load(url, t => {
      t.colorSpace = THREE.NoColorSpace; t.anisotropy = 8; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; res(t);
    }, undefined, rej));
  }
  async init({ day = 'tex/day_8k.jpg', night = 'tex/night_8k.jpg', normal = 'tex/normal_8k.png', clouds = 'lab/globe/clouds_8k.jpg', segments = 384 } = {}) {
    const C = this.cine;
    const [d, n, nm, cl] = await Promise.all([this._tex(day), this._tex(night), this._tex(normal), this._tex(clouds)]);
    nm.anisotropy = 4; cl.wrapS = THREE.RepeatWrapping;
    const blank = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1); blank.needsUpdate = true;
    const common = { tauZ: { value: 0.25 }, tauM: { value: 0.035 }, sunI: { value: 1.55 }, sunCol: { value: new THREE.Vector3(1.0, 0.985, 0.96) },
      clearDir: { value: new THREE.Vector3(1, 0, 0) }, clearCos: { value: new THREE.Vector2(0.99, 0.995) }, clearAmt: { value: 0 } };
    this.common = common;
    this.u = Object.assign({
      dayTex: { value: d }, nightTex: { value: n }, nrmTex: { value: nm }, cloudTex: { value: cl }, relief: { value: 0.8 },
      patchTex: { value: blank }, patchB: { value: new THREE.Vector4(0, 0, 1, 1) }, patchOn: { value: 0 },
      ovTex: { value: blank }, ovB: { value: new THREE.Vector4(-180, -90, 180, 90) }, ovOn: { value: 0 }, ovAlpha: { value: 1 },
      sunDir: { value: this.sunDir }, camPos: { value: this.camera.position },
      dim: { value: 0 }, desat: { value: 0.04 }, nightAmt: { value: 1 }, exposure: { value: 1.25 }, ambient: { value: 0.10 },
      tint: { value: new THREE.Vector3(1, 1, 1) }, specAmt: { value: 1.0 }, rimAmt: { value: 0.35 }, flatBase: { value: 0 }, flatColor: { value: new THREE.Vector3(0.035, 0.09, 0.19) }, ovMul: { value: 0 },
      detail: { value: 0.55 }, haze: { value: 0.32 }, waterRelief: { value: 0.18 }, oceanTone: { value: 0.80 },
      cloudAmt: { value: 0.82 }, cloudGamma: { value: 2.15 }, cloudShadow: { value: 0.55 }, cloudOff: { value: 0 }, cloudH: { value: 0.0045 }, cityI: { value: 2.6 }, ovGain: { value: 1.0 },
    }, common);
    this.earth = new THREE.Mesh(new THREE.SphereGeometry(1, segments, segments / 2), new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: EARTH_VS, fragmentShader: EARTH_FS }));
    this.scene.add(this.earth);
    this.cloudU = Object.assign({ cloudTex: { value: cl }, sunDir: { value: this.sunDir }, camPos: { value: this.camera.position }, cloudAmt: this.u.cloudAmt, cloudGamma: this.u.cloudGamma,
      cloudOff: this.u.cloudOff, exposure: this.u.exposure, haze: this.u.haze, dim: this.u.dim, rimAmt: this.u.rimAmt, bump: { value: 1.6 }, fadeLow: { value: 1 },
      ovTex: this.u.ovTex, ovB: this.u.ovB, ovOn: this.u.ovOn, ovAlpha: this.u.ovAlpha, ovClear: { value: 0.9 } }, common);
    this.clouds = new THREE.Mesh(new THREE.SphereGeometry(1.0045, segments, segments / 2), new THREE.ShaderMaterial({ uniforms: this.cloudU, vertexShader: EARTH_VS, fragmentShader: CLOUD_FS, transparent: true, depthWrite: false }));
    this.clouds.renderOrder = 1; this.scene.add(this.clouds);
    this.atmoU = Object.assign({ sunDir: { value: this.sunDir }, camPos: { value: this.camera.position }, strength: { value: 1.25 }, Hs: { value: 0.0085 }, exposure: this.u.exposure }, common);
    this.atmo = new THREE.Mesh(new THREE.SphereGeometry(1.075, 192, 96), new THREE.ShaderMaterial({
      uniforms: this.atmoU, vertexShader: ATMO_VS, fragmentShader: ATMO_FS, side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    }));
    this.atmo.renderOrder = 2; this.scene.add(this.atmo);
    // starfield: frame-sized canvas sampled by a full-screen quad (parallax offset), on a deep-navy gradient
    const sc = document.createElement('canvas'); sc.width = this.W; sc.height = this.H; const sg = sc.getContext('2d');
    sg.fillStyle = '#000'; sg.fillRect(0, 0, sc.width, sc.height);
    const rr = rng(77);
    for (let i = 0; i < 1700; i++) {
      const x = rr() * sc.width, y = rr() * sc.height, b = Math.pow(rr(), 6) * 0.95 + 0.05, sz = b > 0.6 ? 1.5 : b > 0.3 ? 1.1 : 0.75, w = rr();
      sg.fillStyle = `rgba(${Math.round(225 + 30 * w)},${Math.round(230 + 12 * w)},255,${b})`; sg.beginPath(); sg.arc(x, y, sz, 0, Math.PI * 2); sg.fill();
    }
    const st = new THREE.CanvasTexture(sc); st.wrapS = st.wrapT = THREE.RepeatWrapping; st.colorSpace = THREE.NoColorSpace; st.minFilter = THREE.LinearFilter; st.generateMipmaps = false;
    this.bgU = { tex: { value: st }, off: { value: new THREE.Vector2(0, 0) }, alpha: { value: 1 }, top: { value: new THREE.Vector3(...C.spaceTop) }, bot: { value: new THREE.Vector3(...C.spaceBot) }, starI: { value: C.starI } };
    this.bgScene = new THREE.Scene(); this.fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.bgScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({ uniforms: this.bgU, depthTest: false, depthWrite: false, vertexShader: FS_VS, fragmentShader: BG_FS })));
    // render targets
    const W = this.W, H = this.H, ss = C.ss;
    const rt = (w, h, depth = false) => new THREE.WebGLRenderTarget(Math.max(1, Math.round(w)), Math.max(1, Math.round(h)), { type: THREE.HalfFloatType, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: depth, generateMipmaps: false, colorSpace: THREE.NoColorSpace });
    this.rtScene = rt(W * ss, H * ss, true);
    this.rtHDR = ss > 1 ? rt(W, H) : this.rtScene;
    this.bl = []; for (let i = 1; i <= 6; i++) this.bl.push(rt(W / 2 ** i, H / 2 ** i));
    this.pCopy = new Pass(COPY_FS, { t: { value: null } });
    this.pPre = new Pass(PRE_FS, { t: { value: null }, px: { value: new THREE.Vector2() }, thr: { value: C.bloomThr } });
    this.pDown = new Pass(DOWN_FS, { t: { value: null }, px: { value: new THREE.Vector2() } });
    this.pUp = new Pass(UP_FS, { t: { value: null }, px: { value: new THREE.Vector2() }, w: { value: 1 } }, { blending: THREE.AdditiveBlending });
    this.fu = {
      tHDR: { value: this.rtHDR.texture }, tBloom: { value: this.bl[0].texture }, res: { value: new THREE.Vector2(W, H) }, exposure: { value: C.exposure }, bloom: { value: C.bloom },
      vig: { value: C.vignette }, grain: { value: C.grain }, ca: { value: C.ca }, seed: { value: 0 }, sharpen: { value: C.sharpen }, dof: { value: C.dof }, focus: { value: 1 }, maxCoc: { value: C.maxCoc },
      invProj: { value: new THREE.Matrix4() }, camWorld: { value: new THREE.Matrix4() }, camPos: { value: new THREE.Vector3() },
      lift: { value: new THREE.Vector3(...C.lift) }, shadowTint: { value: new THREE.Vector3(...C.shadowTint) }, highTint: { value: new THREE.Vector3(...C.highTint) },
      contrast: { value: C.contrast }, sat: { value: C.sat }, tmMode: { value: C.tm },
    };
    this.pFinal = new Pass(FINAL_FS, this.fu);
    this.set({});
  }
  // post / lens settings per shot: g.post({dof: 12, bloom: 0.3, exposure: 1.1, ...}) (keys of CINE_DEFAULTS)
  post(o = {}) {
    const C = Object.assign(this.cine, o), f = this.fu;
    f.exposure.value = C.exposure; f.bloom.value = C.bloom; f.vig.value = C.vignette; f.grain.value = C.grain; f.ca.value = C.ca; f.sharpen.value = C.sharpen;
    f.dof.value = C.dof; f.maxCoc.value = C.maxCoc; f.contrast.value = C.contrast; f.sat.value = C.sat; f.tmMode.value = C.tm;
    f.lift.value.set(...C.lift); f.shadowTint.value.set(...C.shadowTint); f.highTint.value.set(...C.highTint);
    this.pPre.u.thr.value = C.bloomThr; this.bgU.starI.value = C.starI;
  }
  async setPatch(url, b) {
    if (!url) { this.u.patchOn.value = 0; return; }
    const t = await this._tex(url); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    if (this.u.patchTex.value && this.u.patchTex.value.dispose) this.u.patchTex.value.dispose();
    this.u.patchTex.value = t; this.u.patchB.value.set(b[0], b[1], b[2], b[3]); this.u.patchOn.value = 1;
  }
  async setOverlayURL(url, b = [-180, -90, 180, 90]) {
    const t = await this._tex(url); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    if (this.u.ovTex.value && this.u.ovTex.value.dispose) this.u.ovTex.value.dispose();
    this.u.ovTex.value = t; this.u.ovB.value.set(b[0], b[1], b[2], b[3]); this.u.ovOn.value = 1;
  }
  refreshOverlay() { if (this.u.ovTex.value && this.u.ovTex.value.isCanvasTexture) this.u.ovTex.value.needsUpdate = true; }
  setOverlay(canvas, b = [-180, -90, 180, 90]) {
    if (!canvas) { this.u.ovOn.value = 0; return; }
    const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.NoColorSpace; t.minFilter = THREE.LinearMipmapLinearFilter; t.anisotropy = 4;
    if (this.u.ovTex.value && this.u.ovTex.value.dispose) this.u.ovTex.value.dispose();
    this.u.ovTex.value = t; this.u.ovB.value.set(b[0], b[1], b[2], b[3]); this.u.ovOn.value = 1;
  }
  // camera: identical convention to Globe.set (lat, lon, alt, tilt, heading, fov, lookOffset, sun modes)
  set(s) {
    Object.assign(this.state, s);
    const S = this.state, cam = this.camera;
    const P = dirOf(S.lat, S.lon, 1);
    const up = P.clone().normalize();
    let north = new THREE.Vector3(0, 1, 0).sub(up.clone().multiplyScalar(up.y));
    if (north.lengthSq() < 1e-8) north = new THREE.Vector3(1, 0, 0); north.normalize();
    const east = new THREE.Vector3().crossVectors(north, up).normalize();
    const h = (S.heading || 0) * D2R, t = (S.tilt || 0) * D2R;
    const fwd = north.clone().multiplyScalar(Math.cos(h)).add(east.clone().multiplyScalar(Math.sin(h)));
    const camPos = P.clone().add(up.clone().multiplyScalar(Math.cos(t) * S.alt)).add(fwd.clone().multiplyScalar(-Math.sin(t) * S.alt));
    cam.position.copy(camPos);
    cam.up.copy(fwd.clone().multiplyScalar(Math.cos(t)).add(up.clone().multiplyScalar(Math.sin(t))).normalize());
    const look = P.clone();
    if (S.lookOffset) { look.add(east.clone().multiplyScalar(S.lookOffset[0] * S.alt)).add(fwd.clone().multiplyScalar(S.lookOffset[1] * S.alt)); }
    cam.lookAt(look);
    cam.fov = S.fov || 34; cam.near = Math.max(0.0005, S.alt * 0.05); cam.far = 200; cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    if (S.sun === 'world') {
      this.sunDir.copy(dirOf(S.sunLat ?? 10, S.sunLon ?? 0, 1));
    } else {
      const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
      const cup = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 1);
      const back = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 2);
      const az = (S.sunAz ?? -35) * D2R, el = (S.sunEl ?? 28) * D2R;
      this.sunDir.copy(back.multiplyScalar(Math.cos(el) * Math.cos(az)).add(right.multiplyScalar(Math.cos(el) * Math.sin(az))).add(cup.multiplyScalar(Math.sin(el)))).normalize();
    }
    this.u.camPos.value.copy(cam.position);
    this.focusDist = S.focus ? cam.position.distanceTo(dirOf(S.focus[0], S.focus[1], 1)) : cam.position.distanceTo(P);
    this.starAlpha = Math.min(1, Math.max(0, (S.alt - 0.02) / 0.15));
    if (S.clouds !== undefined) this.u.cloudAmt.value = S.clouds;
    if (S.cloudOff !== undefined) this.u.cloudOff.value = S.cloudOff;
    // clouds part over the subject: clear: [lat, lon, innerDeg, outerDeg, amount]
    if (S.clear) { const c = S.clear; this.common.clearDir.value.copy(dirOf(c[0], c[1], 1)); this.common.clearCos.value.set(Math.cos((c[3] ?? c[2] * 2) * D2R), Math.cos(c[2] * D2R)); this.common.clearAmt.value = c[4] ?? 1; }
    else if (S.clear === null) this.common.clearAmt.value = 0;
  }
  // look keys: every earth uniform (ep01 names), plus 'atmo' (limb shell strength) and 'cloudBump'
  look(k, v) { if (k === 'atmo') this.atmoU.strength.value = v; else if (k === 'cloudBump') this.cloudU.bump.value = v; else if (this.u[k]) this.u[k].value = v; }
  starfield(ctx, alpha = 1) { this.starMul = alpha; }
  render(frame = 0) {
    const S = this.state, r = this.renderer, cam = this.fsCam, W = this.W, H = this.H;
    this.bgU.off.value.set(((S.lon * 6 + (S.heading || 0) * 4) / W) % 1, ((S.lat * 4 + (S.tilt || 0) * 6) / H) % 1);
    this.bgU.alpha.value = (this.starAlpha ?? 1) * (this.starMul ?? 1);
    // clouds fade out on low, close shots unless a shot asks for them (texture is ~5 km/px)
    this.cloudU.fadeLow.value = S.cloudsLow ?? Math.min(1, Math.max(0.25, (S.alt - 0.15) / 0.6));
    // 1) scene -> HDR target (ss x)
    r.setRenderTarget(this.rtScene); r.clear();
    r.render(this.bgScene, cam);
    r.clearDepth();
    r.render(this.scene, this.camera);
    // 2) resolve supersampling (bilinear tap at 2x2 block centres = box filter)
    if (this.rtHDR !== this.rtScene) { this.pCopy.u.t.value = this.rtScene.texture; this.pCopy.run(r, cam, this.rtHDR); }
    // 3) bloom: prefilter -> 5 downs -> additive tent ups
    const bl = this.bl;
    this.pPre.u.t.value = this.rtHDR.texture; this.pPre.u.px.value.set(0.5 / W, 0.5 / H); this.pPre.run(r, cam, bl[0]);
    for (let i = 1; i < bl.length; i++) { this.pDown.u.t.value = bl[i - 1].texture; this.pDown.u.px.value.set(1 / bl[i - 1].width, 1 / bl[i - 1].height); this.pDown.run(r, cam, bl[i]); }
    for (let i = bl.length - 1; i > 0; i--) { this.pUp.u.t.value = bl[i].texture; this.pUp.u.px.value.set(0.5 / bl[i].width, 0.5 / bl[i].height); this.pUp.u.w.value = 1; this.pUp.run(r, cam, bl[i - 1]); }
    // 4) final composite to the canvas
    const f = this.fu, c = this.camera;
    f.invProj.value.copy(c.projectionMatrixInverse); f.camWorld.value.copy(c.matrixWorld); f.camPos.value.copy(c.position);
    f.focus.value = this.focusDist; f.seed.value = (frame * 0.6180339) % 1 * 100.0;
    this.pFinal.run(r, cam, null);
    return this.canvas;
  }
  project(lat, lon, hgt = 0) {
    const p = dirOf(lat, lon, 1 + hgt);
    const cp = this.camera.position;
    const toCam = cp.clone().sub(p);
    const dir = toCam.clone().normalize();
    const b = p.dot(dir), c = p.lengthSq() - 0.9999;
    const disc = b * b - c;
    let visible = true;
    if (disc > 0) { const tHit = -b - Math.sqrt(disc); if (tHit > 1e-5) visible = false; }
    if (hgt <= 0 && p.clone().normalize().dot(dir) < 0) visible = false;
    const v = p.clone().project(this.camera);
    if (v.z > 1) visible = false;
    return { x: (v.x + 1) / 2 * this.W, y: (1 - v.y) / 2 * this.H, visible, facing: p.clone().normalize().dot(dir) };
  }
  disc() {
    const c = new THREE.Vector3(0, 0, 0).project(this.camera);
    const d = this.camera.position.length();
    const ang = Math.asin(Math.min(1, 1 / d));
    const f = this.H / 2 / Math.tan(this.camera.fov * D2R / 2);
    return { x: (c.x + 1) / 2 * this.W, y: (1 - c.y) / 2 * this.H, r: Math.tan(ang) * f };
  }
}
