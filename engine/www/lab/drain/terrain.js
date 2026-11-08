// TerrainStage: real DEM terrain + seafloor with an animatable water level ("drain the sea" hero shots).
// Data comes from terrain_bake.py (hero tile + wide low-res skirt for the horizon). Units: 1 world unit = 1 km.
// Pure function of state: set camera + level + time, call render(); no hidden animation state.
import * as THREE from 'three';

const R_EARTH = 6371.0, KM_DEG = 111.32;

const COMMON = /* glsl */`
uniform vec3 camPos; uniform vec3 sunDir; uniform float horizonDip;
uniform vec3 zenithCol, horizonCol, hazeCol, sunCol, glowCol;
uniform float fogDens, fogH, fogBg;
vec3 skyColor(vec3 d){
  float y = clamp(d.y + horizonDip, 0.0, 1.0);
  vec3 c = mix(horizonCol, zenithCol, pow(y, 0.42));
  float mu = max(dot(d, sunDir), 0.0);
  c += glowCol * (pow(mu, 6.0) * 0.30 + pow(mu, 48.0) * 0.55);
  c = mix(c, hazeCol, exp(-y * 14.0) * 0.55);
  return c;
}
vec3 inscatter(vec3 d){
  float mu = max(dot(d, sunDir), 0.0);
  return hazeCol + glowCol * (pow(mu, 5.0) * 0.35);
}
// height-aware aerial perspective: exponential haze layer of scale height fogH (km) plus a thin uniform term
vec3 aerial(vec3 col, vec3 wp, out float T){
  vec3 v = wp - camPos; float dist = length(v); vec3 d = v / max(dist, 1e-4);
  float y0 = max(camPos.y, 0.0), y1 = max(wp.y, -2.0), dy = y1 - y0;
  float od = abs(dy) < 1e-3 ? fogDens * exp(-y0 / fogH) * dist : fogDens * dist * fogH * (exp(-y0 / fogH) - exp(-y1 / fogH)) / dy;
  od += fogBg * dist;
  T = exp(-od);
  return col * T + inscatter(d) * (1.0 - T);
}
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
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
uniform sampler2D hTex, lightTex, colTex; uniform vec2 texel; uniform vec4 bb; uniform float vex, level, ringH, coastLine, exposedTint, sunI, skyI, dbg, landSat, saltAmt, seaRelief;
varying vec2 vUv; varying vec3 vW;
float Hm(vec2 uv){ return texture2D(hTex, uv).r; }
vec3 seabed(float h, float slope, float cav, vec2 ll){
  float dep = -h;
  vec3 sand = vec3(0.30, 0.225, 0.13), mud = vec3(0.150, 0.118, 0.080), silt = vec3(0.205, 0.170, 0.125), rock = vec3(0.085, 0.068, 0.052);
  vec3 c = mix(sand, mud, smoothstep(60.0, 450.0, dep));
  c = mix(c, silt, smoothstep(700.0, 1600.0, dep));
  float n = fbm(ll * 9.0), n2 = fbm(ll * 41.0 + 3.0);
  float n3 = fbm(vec2(ll.x * 160.0, ll.y * 60.0) + n * 3.0);
  c *= 0.74 + 0.46 * n + 0.18 * (n2 - 0.5) + 0.10 * (n3 - 0.5);
  c *= clamp(1.0 - cav * 1.6, 0.62, 1.22);  // hollows hold darker fine sediment, crests are paler
  c = mix(c, rock, smoothstep(0.10, 0.35, slope) * 0.75);
  return c;
}
void main(){
  vec2 ll = bb.xy + vUv * (bb.zw - bb.xy);
  float lat = radians(ll.y);
  float h = Hm(vUv);
  // finite differences over max(1 texel, pixel footprint): crisp up close, no normal aliasing in the distance
  vec2 fp = max(texel, fwidth(vUv) * 0.75);
  float hl = Hm(vUv - vec2(fp.x, 0.0)), hr = Hm(vUv + vec2(fp.x, 0.0)), hd = Hm(vUv - vec2(0.0, fp.y)), hu = Hm(vUv + vec2(0.0, fp.y));
  float dxk = (bb.z - bb.x) * fp.x * ${KM_DEG} * cos(lat), dyk = (bb.w - bb.y) * fp.y * ${KM_DEG};
  float gx = (hr - hl) * vex * 0.001 / (2.0 * dxk), gy = (hu - hd) * vex * 0.001 / (2.0 * dyk);
  float rk = mix(seaRelief, 1.0, smoothstep(-40.0, 0.0, h));  // optional extra shading relief on the (gentle) seabed only
  vec3 n = normalize(vec3(-gx * rk, 1.0, gy * rk));
  float cav = clamp((hl + hr + hd + hu - 4.0 * h) / max(fp.x * 4096.0, 1.0) / 90.0, -0.25, 0.25);
  float slope = length(vec2(gx, gy)) / vex;  // true (unexaggerated) gradient
  vec4 L = texture2D(lightTex, vUv);
  float shadow = L.r, ao = L.g;
  vec3 land = texture2D(colTex, vUv).rgb; float ll0 = dot(land, vec3(0.2126, 0.7152, 0.0722)); land = max(mix(vec3(ll0), land, landSat), 0.0);
  vec3 alb = mix(seabed(h, slope, cav, ll), land, smoothstep(-6.0, 4.0, h));
  // freshly exposed seabed (was under water at sea level, is now dry): slightly paler crust, plus a dark wet band above the waterline
  float exposed = step(h, -1.0) * step(level, h);
  // dry crust far above the new waterline, darker damp sediment as it gets closer, a dark wet band right at the water
  float above = h - level;
  alb = mix(alb, alb * vec3(1.12, 1.08, 1.03), exposed * exposedTint * smoothstep(80.0, 600.0, above));
  float ring = exposed * (1.0 - smoothstep(0.0, ringH, above));
  float salt = exposed * smoothstep(ringH * 0.8, ringH * 1.4, above) * (1.0 - smoothstep(ringH * 2.5, ringH * 4.5, above)) * (0.65 + 0.35 * fbm(ll * 300.0));
  alb = mix(alb, vec3(0.50, 0.48, 0.43), salt * saltAmt);
  alb *= 1.0 - 0.55 * ring - 0.18 * exposed * (1.0 - smoothstep(ringH, ringH * 5.0, above));
  float ndl = max(dot(n, sunDir), 0.0);
  vec3 sky = mix(hazeCol, zenithCol, 0.55);
  vec3 col = alb * (sunCol * sunI * ndl * shadow + sky * skyI * ao * (0.55 + 0.45 * n.y) + vec3(0.05, 0.04, 0.03) * (1.0 - n.y));
  // wet sheen on the ring
  vec3 v = normalize(camPos - vW); vec3 hv = normalize(v + sunDir);
  col += sunCol * sunI * ring * 0.18 * pow(max(dot(n, hv), 0.0), 40.0) * shadow;
  // former coastline (graphic aid, optional)
  float fw = max(fwidth(h), 1e-3);
  float cl = coastLine * step(level, -25.0) * (1.0 - smoothstep(0.0, fw * 1.6, abs(h + 0.5)));
  col = mix(col, vec3(1.6, 1.45, 1.2), cl * 0.75);
  float T; vec3 colA = aerial(col, vW, T);
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
uniform sampler2D hHero, hSkirt; uniform vec4 bbHero, bbSkirt; uniform float level, time, sunI, dbg;
varying vec3 vW; varying vec2 vLL;
float hAt(vec2 ll){
  vec2 us = (ll - bbSkirt.xy) / (bbSkirt.zw - bbSkirt.xy);
  float hs = texture2D(hSkirt, us).r;
  vec2 uh = (ll - bbHero.xy) / (bbHero.zw - bbHero.xy);
  if (uh.x < 0.0 || uh.y < 0.0 || uh.x > 1.0 || uh.y > 1.0) return hs;
  vec2 e = min(uh, 1.0 - uh); float w = smoothstep(0.0, 0.025, min(e.x, e.y));
  return mix(hs, texture2D(hHero, uh).r, w);
}
void main(){
  float h = hAt(vLL);
  float depth = level - h;
  if (depth <= 0.0) discard;
  if (dbg > 4.5) { gl_FragColor = vec4(fract(vLL.x), fract(vLL.y), clamp(depth / 3000.0, 0.0, 1.0), 1.0); return; }
  vec2 p = vW.xz;
  // km-scale sheen variation (wind slicks) + gentle normals, slowly drifting
  float slick = fbm(p * 0.045 + vec2(time * 0.004, -time * 0.002));
  vec2 g = vec2(fbm(p * 0.6 + vec2(time * 0.03, 0.0)) - fbm(p * 0.6 + vec2(0.37, 0.0) + vec2(time * 0.03, 0.0)),
                fbm(p * 0.6 + vec2(0.0, 0.37) + vec2(0.0, time * 0.02)) - fbm(p * 0.6 + vec2(0.0, time * 0.02)));
  float rough = mix(0.035, 0.11, slick);
  vec3 n = normalize(vec3(g.x * rough * 2.0, 1.0, g.y * rough * 2.0));
  vec3 v = normalize(camPos - vW);
  float fres = 0.02 + 0.98 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
  vec3 refl = skyColor(reflect(-v, n));
  vec3 hv = normalize(v + sunDir); float nh = max(dot(n, hv), 0.0);
  float a2 = rough * rough; float dd = nh * nh * (a2 - 1.0) + 1.0; float spec = a2 / (3.14159 * dd * dd);
  vec3 glint = sunCol * sunI * spec * 0.08 * fres;
  // water body: turquoise over shallow sand, deep navy offshore
  vec3 shallow = vec3(0.020, 0.135, 0.150), mid = vec3(0.008, 0.055, 0.105), deep = vec3(0.003, 0.016, 0.040);
  vec3 body = mix(shallow, mid, smoothstep(4.0, 45.0, depth)); body = mix(body, deep, smoothstep(60.0, 900.0, depth));
  body *= 0.55 + 0.45 * sunI / 3.0 + 0.0;
  float aBody = 1.0 - exp(-depth / 7.0);
  aBody = max(aBody, 0.0);
  float edge = 1.0 - smoothstep(0.0, 2.5, depth);
  body = mix(body, vec3(0.10, 0.22, 0.21), edge * 0.6);
  float alpha = 1.0 - (1.0 - aBody) * (1.0 - fres);
  vec3 prem = body * aBody * (1.0 - fres) + refl * fres + glint;
  float T; vec3 dummy = aerial(vec3(0.0), vW, T);
  vec3 d = normalize(vW - camPos);
  prem = prem * T + inscatter(d) * (1.0 - T) * alpha;
  gl_FragColor = vec4(prem, alpha);
}`;

const SKY_VS = /* glsl */`
varying vec3 vDir; uniform vec3 camPos;
void main(){ vDir = position; vec4 w = vec4(position + camPos, 1.0); gl_Position = projectionMatrix * viewMatrix * w; gl_Position.z = gl_Position.w * 0.99999; }`;
const SKY_FS = /* glsl */`
${COMMON}
varying vec3 vDir;
void main(){ vec3 d = normalize(vDir); gl_FragColor = vec4(skyColor(d), 1.0); }`;

// final pass: exposure, filmic tone curve (ACES fit), split-tone grade, vignette, grain, sRGB encode
const POST_FS = /* glsl */`
uniform sampler2D src; uniform float exposure, vignette, grain, seed, sat; uniform vec2 res; varying vec2 vUv;
vec3 aces(vec3 x){ return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main(){
  vec3 c = texture2D(src, vUv).rgb * exposure;
  c = aces(c);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, sat);
  c += vec3(-0.010, 0.004, 0.014) * (1.0 - smoothstep(0.0, 0.45, l)) + vec3(0.012, 0.004, -0.010) * smoothstep(0.45, 1.0, l);
  vec2 q = vUv - 0.5; q.x *= res.x / res.y;
  c *= 1.0 - vignette * smoothstep(0.35, 1.05, length(q));
  c = pow(max(c, 0.0), vec3(1.0 / 2.2));
  c += (h12(gl_FragCoord.xy + seed * 61.7) - 0.5) * grain;
  gl_FragColor = vec4(c, 1.0);
}`;

async function loadImage(url) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('img ' + url)); i.src = url; }); }
function decodeH16(img, meta) {  // RG 16-bit -> Float32 metres, rows flipped so row 0 = south (matches uv.y = 0 at bbox south)
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
  const px = g.getImageData(0, 0, c.width, c.height).data, W = c.width, H = c.height, out = new Float32Array(W * H);
  for (let r = 0; r < H; r++) { const src = r * W, dst = (H - 1 - r) * W; for (let i = 0; i < W; i++) { const k = (src + i) * 4; out[dst + i] = ((px[k] << 8 | px[k + 1]) / 65535) * meta.hrange + meta.hmin; } }
  return { data: out, W, H };
}
function heightTexture(hm) {
  const half = new Uint16Array(hm.data.length); for (let i = 0; i < half.length; i++) half[i] = THREE.DataUtils.toHalfFloat(hm.data[i]);
  const t = new THREE.DataTexture(half, hm.W, hm.H, THREE.RedFormat, THREE.HalfFloatType);
  t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true; return t;
}
function sampleH(hm, u, v) {  // bilinear, u,v in 0..1 (v from south)
  const x = Math.min(Math.max(u * (hm.W - 1), 0), hm.W - 1.001), y = Math.min(Math.max(v * (hm.H - 1), 0), hm.H - 1.001);
  const i = x | 0, j = y | 0, fx = x - i, fy = y - j, d = hm.data, W = hm.W;
  return d[j * W + i] * (1 - fx) * (1 - fy) + d[j * W + i + 1] * fx * (1 - fy) + d[(j + 1) * W + i] * (1 - fx) * fy + d[(j + 1) * W + i + 1] * fx * fy;
}

export class TerrainStage {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H; this.o = o;
    this.R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.R.setPixelRatio(1); this.R.setSize(W, H, false); this.R.autoClear = true;
    this.rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: o.samples ?? 4, depthBuffer: true });
    this.scene = new THREE.Scene();
    this.cam = new THREE.PerspectiveCamera(o.fov ?? 34, W / H, 2, 6000);
    this.level = 0; this.time = 0;
  }
  async load(dir) {
    const meta = this.meta = await (await fetch(dir + '/meta.json')).json();
    this.vex = meta.vex; this.c0 = { lon: (meta.hero_bbox[0] + meta.hero_bbox[2]) / 2, lat: (meta.hero_bbox[1] + meta.hero_bbox[3]) / 2 };
    const [hI, sI] = await Promise.all([loadImage(dir + '/hero_h16.png'), loadImage(dir + '/skirt_h16.png')]);
    this.hHero = decodeH16(hI, meta); this.hSkirt = decodeH16(sI, meta);
    const TL = new THREE.TextureLoader();
    const tex = async (u, srgb) => { const t = await TL.loadAsync(dir + '/' + u); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; t.minFilter = THREE.LinearMipmapLinearFilter; return t; };
    const [heroCol, heroLight, skCol, skLight] = await Promise.all([tex('hero_color.jpg', true), tex('hero_light.png', false), tex('skirt_color.jpg', true), tex('skirt_light.png', false)]);
    const sunAz = THREE.MathUtils.degToRad(meta.sun_az), sunEl = THREE.MathUtils.degToRad(meta.sun_el);
    const sunDir = new THREE.Vector3(Math.sin(sunAz) * Math.cos(sunEl), Math.sin(sunEl), -Math.cos(sunAz) * Math.cos(sunEl));
    const C = (hex, k = 1) => new THREE.Color(hex).multiplyScalar(k);  // THREE.Color converts sRGB hex to linear
    this.U = {
      camPos: { value: new THREE.Vector3() }, sunDir: { value: sunDir }, horizonDip: { value: 0 },
      zenithCol: { value: C('#2c64a8', 1.0) }, horizonCol: { value: C('#a9c3dc', 1.0) }, hazeCol: { value: C('#aec2d6', 0.80) },
      sunCol: { value: C('#fff1de') }, glowCol: { value: C('#ffe2b8', 0.9) },
      fogDens: { value: this.o.fogDens ?? 0.0062 }, fogH: { value: this.o.fogH ?? 6.0 }, fogBg: { value: this.o.fogBg ?? 0.00030 },
    };
    const hT = heightTexture(this.hHero), sT = heightTexture(this.hSkirt);
    this.hTexHero = hT; this.hTexSkirt = sT;
    const hb = meta.hero_bbox, sb = meta.skirt_bbox;
    const terrMat = (hTex, lightTex, colTex, bb, hm, holeDrop) => new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, {
        hTex: { value: hTex }, lightTex: { value: lightTex }, colTex: { value: colTex }, texel: { value: new THREE.Vector2(1 / hm.W, 1 / hm.H) },
        bb: { value: new THREE.Vector4(...bb) }, hole: { value: new THREE.Vector4(...hb) }, holeDrop: { value: holeDrop },
        vex: { value: this.vex }, level: { value: 0 }, ringH: { value: 45 }, coastLine: { value: 0 }, exposedTint: { value: 1 }, dbg: { value: 0 }, landSat: { value: 1.12 }, saltAmt: { value: 0.55 }, seaRelief: { value: 1.0 }, sunI: { value: 3.0 }, skyI: { value: 0.95 },
      }), vertexShader: TERRAIN_VS, fragmentShader: TERRAIN_FS,
    });
    this.heroMat = terrMat(hT, heroLight, heroCol, hb, this.hHero, 0);
    this.skirtMat = terrMat(sT, skLight, skCol, sb, this.hSkirt, 4.0);
    this.scene.add(new THREE.Mesh(this.grid(hb, this.hHero, this.o.heroGrid || [1400, 700]), this.heroMat));
    this.scene.add(new THREE.Mesh(this.grid(sb, this.hSkirt, this.o.skirtGrid || [720, 400]), this.skirtMat));
    // water: one curved sheet over the whole skirt extent; depth from the height textures per fragment
    this.waterMat = new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, { hHero: { value: hT }, hSkirt: { value: sT }, bbHero: { value: new THREE.Vector4(...hb) }, bbSkirt: { value: new THREE.Vector4(...sb) },
        bb: { value: new THREE.Vector4(...sb) }, level: { value: 0 }, yLevel: { value: 0 }, time: { value: 0 }, sunI: { value: 3.0 }, dbg: { value: 0 } }),
      vertexShader: WATER_VS, fragmentShader: WATER_FS, transparent: true, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
    });
    const water = new THREE.Mesh(this.grid(sb, null, [420, 240]), this.waterMat); water.renderOrder = 2; this.scene.add(water);
    const sky = new THREE.Mesh(new THREE.SphereGeometry(4000, 64, 32), new THREE.ShaderMaterial({ uniforms: this.U, vertexShader: SKY_VS, fragmentShader: SKY_FS, side: THREE.BackSide, depthWrite: false }));
    sky.renderOrder = -1; sky.frustumCulled = false; this.scene.add(sky);
    // post
    this.postMat = new THREE.ShaderMaterial({
      uniforms: { src: { value: this.rt.texture }, exposure: { value: this.o.exposure ?? 0.92 }, vignette: { value: 0.26 }, grain: { value: 0.022 }, seed: { value: 0 }, sat: { value: 1.12 }, res: { value: new THREE.Vector2(this.W, this.H) } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }', fragmentShader: POST_FS, depthTest: false, depthWrite: false,
    });
    this.postScene = new THREE.Scene(); const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.postMat); q.frustumCulled = false; this.postScene.add(q);
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  // world position (km) of lon/lat/height(m): sinusoidal around the hero centre, exaggerated height, no curvature
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
  heightAt(lon, lat) { const hb = this.meta.hero_bbox; return sampleH(this.hHero, (lon - hb[0]) / (hb[2] - hb[0]), (lat - hb[1]) / (hb[3] - hb[1])); }
  // camera: position lon/lat/alt(km), looking at lon/lat/height(m) of a target
  setCamera(c) {
    const p = this.xyz(c.lon, c.lat, 0); p.y = c.alt;
    let t;
    if (c.heading != null) {  // heading: degrees clockwise from north; pitch: degrees, negative looks down
      const hd = THREE.MathUtils.degToRad(c.heading), pt = THREE.MathUtils.degToRad(c.pitch ?? -15);
      t = p.clone().add(new THREE.Vector3(Math.sin(hd) * Math.cos(pt), Math.sin(pt), -Math.cos(hd) * Math.cos(pt)).multiplyScalar(100));
    } else {
      t = this.xyz(c.tLon, c.tLat, c.tH ?? 0); const d = t.clone().sub(p); t.y -= (d.x * d.x + d.z * d.z) / (2 * R_EARTH);
    }
    this.cam.position.copy(p); this.cam.up.set(0, 1, 0); this.cam.lookAt(t);
    if (c.roll) this.cam.rotateZ(THREE.MathUtils.degToRad(c.roll));
    this.cam.fov = c.fov ?? this.cam.fov; this.cam.updateProjectionMatrix(); this.cam.updateMatrixWorld();
    this.U.camPos.value.copy(p); this.U.horizonDip.value = Math.sqrt(2 * Math.max(c.alt, 0.01) / R_EARTH);
  }
  setLevel(m) { this.level = m; for (const M of [this.heroMat, this.skirtMat, this.waterMat]) M.uniforms.level.value = m; this.waterMat.uniforms.yLevel.value = m * this.vex * 0.001; }
  set(k, v) { for (const M of [this.heroMat, this.skirtMat, this.waterMat]) if (M.uniforms[k]) M.uniforms[k].value = v; }
  project(lon, lat, hm) {  // screen px of a ground point (with curvature), or null when behind camera
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
