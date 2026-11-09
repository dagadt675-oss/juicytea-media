// Section: a terrain cut-away for HawaiiStage (ep02 payoff, s162-s172). A vertical plane through a point (lon/lat) at an azimuth;
// the stage's terrain and water are discarded on the camera side (stage.setClip), and a section wall along the plane shows the
// inside of the Earth at true scale (VE = the stage's vex; use 1.0 for any height comparison):
//   - the volcanic pile from the surface down to the top of the oceanic crust: layered basalt that drapes the surface near the top,
//     with a few oxidised flow tops, darker and cooler below the old sea floor (the part pushed down into the dent);
//   - the top of the oceanic crust sags under the load (schematic flexure w(r) = w0 e^(-r/a) (cos(r/a) + sin(r/a)) after the USGS
//     description: the sea floor pushed down by up to about 8 km under Mauna Loa); crust 6.5 km thick (pillow basalt, sheeted dikes,
//     gabbro), the Moho as a faint pale line, then the mantle;
//   - the old ocean in cross-section (waterA): translucent water above the surface (outside the rock only), between waterBot (e.g. the
//     old sea floor: never water inside the dent) and waterTop;
//   - an optional thin 'old sea floor' line across the dent (floorLine) and the trench water strip (trenchA, below trenchTop).
// Everest (optional): a thin slab of its real profile (lab/hawaii/data everest_h16.png, scaled so the summit is 8,849 m above its
// base), standing a little in front of the section on the same base line, rising out of that line (rise 0..1), same section shader
// in limestone tones with snow on top.
// All geometry is built once per plane; set(state) every frame (pure function of the frame). Units: km (world), m (elevations).
import * as THREE from 'three';
import { R_EARTH, KM_DEG, loadMeta, loadH16, sampleH } from './hterrain.js';

const COMMON = /* glsl */`
uniform vec3 camPos, sunDir, sunCol, zenithCol, hazeCol, glowCol; uniform float sunI, skyI, fogDens, fogBg, fogH, fogBase, fogK;
vec3 aerial(vec3 col, vec3 wp, out float T){
  vec3 v = wp - camPos; float dist = length(v); vec3 d = v / max(dist, 1e-4);
  float y0 = max(camPos.y - fogBase, 0.0), y1 = max(wp.y - fogBase, 0.0), dy = y1 - y0;
  float od = abs(dy) < 1e-3 ? fogDens * exp(-y0 / fogH) * dist : fogDens * dist * fogH * (exp(-y0 / fogH) - exp(-y1 / fogH)) / dy;
  od += fogBg * dist; T = exp(-od * fogK);
  float mu = max(dot(d, sunDir), 0.0);
  return col * T + (hazeCol + glowCol * pow(mu, 5.0) * 0.4) * (1.0 - T);
}
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
`;
const WALL_VS = /* glsl */`
uniform vec3 camPos; uniform float vex, eOff;
attribute float aU, aS, aE; varying float vU, vS, vE, vR; varying vec3 vW;
void main(){
  vU = aU; vS = aS; vE = aE + eOff; vR = aE;
  vec3 p = position; p.y += eOff * vex * 0.001;
  vec2 d = p.xz - camPos.xz; p.y -= dot(d, d) / (2.0 * ${R_EARTH.toFixed(1)});
  vW = p; gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;
// mat 0 = the Earth section; mat 1 = Everest's slab (front face 1, top ribbon 2 via aS < -1e5 flag in vS)
const WALL_FS = /* glsl */`
${COMMON}
uniform float mat, sag, sagM, alphaKm, loadU, oldFloor, crustM, waterTop, waterBot, waterA, floorLine, trenchTop, trenchA, baseClip, edgeA;
uniform vec3 faceN, waterCol; uniform float lit;
varying float vU, vS, vE, vR; varying vec3 vW;
float flex(float r){ float x = r / alphaKm; return exp(-x) * (cos(x) + sin(x)); }
float crustTop(float u){ return oldFloor - sag * sagM * flex(abs(u - loadU)); }
float line(float d, float w){ float fw = max(fwidth(d), 1e-3); return 1.0 - smoothstep(w * 0.5, w * 0.5 + 1.0, abs(d) / fw); }
vec3 shade(vec3 alb, vec3 n){
  float ndl = max(dot(n, sunDir), 0.0);
  return alb * (sunCol * sunI * (0.25 + 0.75 * ndl) * lit + mix(hazeCol, zenithCol, 0.5) * skyI * 0.9);
}
void main(){
  float e = vE, u = vU;
  vec3 col; float a = 1.0;
  if (mat < 0.5) {
    if (e > vS) {
      // above the cut surface: the old ocean in cross-section (outside the rock only), and the trench strip
      float wa = (e < waterTop && e > waterBot ? waterA : 0.0);
      float ta = (e < trenchTop ? trenchA : 0.0);
      a = max(wa * 0.55, ta * 0.85); if (a < 0.003) discard;
      vec3 wc = mix(waterCol, waterCol * 0.45, smoothstep(0.0, 5000.0, waterTop - e));
      col = mix(wc, vec3(0.25, 0.85, 1.0), ta / max(a, 1e-3) * 0.6);
      col += vec3(0.6, 0.9, 1.0) * line(e - min(waterTop, 1e9), 2.0) * wa * 0.5;
      float T; col = aerial(col, vW, T);
      gl_FragColor = vec4(col * a, a); return;
    }
    float ct = crustTop(u), d = vS - e;
    vec3 alb;
    float n1 = fbm(vec2(u * 0.35, e * 0.0012)), n2 = fbm(vec2(u * 3.0, e * 0.012) + 3.1), n3 = fbm(vec2(u * 0.08, e * 0.0003) + 9.0);
    if (e > ct) {
      // volcanic pile: thin lava flows (dark seam at each flow base, now and then an oxidised red-brown top) that drape the surface
      // near the top and flatten with depth; flow packages of different thickness and tone; darker and cooler below the old sea floor
      float s = e - vS * exp(-max(d, 0.0) / 4500.0) + (fbm(vec2(u * 0.05, e * 0.0003)) - 0.5) * 260.0;
      float pid = floor(s / 1100.0), hp = hash(vec2(pid, 3.1)), th = mix(110.0, 240.0, hp);
      float b = fract(s / th), fid = floor(s / th);
      float seam = 1.0 - smoothstep(0.0, 0.09, b);
      alb = mix(vec3(0.092, 0.080, 0.066), vec3(0.070, 0.063, 0.056), hash(vec2(pid, 7.7))) * (0.92 + 0.16 * hash(vec2(fid, 1.3)));
      alb *= (0.90 + 0.14 * (n3 - 0.5)) * (1.0 - 0.38 * seam);
      float ox = smoothstep(0.86, 0.97, b) * step(0.82, hash(vec2(fid, 5.9)));
      alb = mix(alb, vec3(0.115, 0.064, 0.046), ox * 0.6);
      float deep = smoothstep(oldFloor + 300.0, oldFloor - 300.0, e);
      alb = mix(alb, alb * vec3(0.66, 0.70, 0.80), deep);
    } else if (e > ct - crustM) {
      // oceanic crust: pillow basalt, sheeted dikes (vertical grain), gabbro; a darker blue-slate than the pile
      float dc = ct - e;
      vec3 slate = vec3(0.038, 0.044, 0.055);
      float pil = fbm(vec2(u * 4.0, e * 0.006)), dik = fbm(vec2(u * 3.0, e * 0.0005)), gab = fbm(vec2(u * 1.2, e * 0.0012) + 7.0);
      float g = dc < 1500.0 ? 0.86 + 0.24 * pil : dc < 3200.0 ? 0.88 + 0.16 * dik : 0.88 + 0.18 * gab;
      alb = slate * g * mix(1.0, 0.86, smoothstep(0.0, crustM, dc));
    } else {
      // mantle (peridotite): dark olive green-brown, slowly warmer with depth
      float dm = ct - crustM - e;
      alb = mix(vec3(0.046, 0.050, 0.034), vec3(0.060, 0.046, 0.032), smoothstep(0.0, 12000.0, dm)) * (0.9 + 0.2 * n1);
    }
    // depth falloff toward the bottom of the section (soft, like ambient occlusion in a deep cut)
    alb *= mix(1.0, 0.72, smoothstep(-8000.0, -30000.0, e));
    col = shade(alb, faceN);
    // lines in the rock: the crust top (the sag) as a dark seam, the Moho faint and pale, the old sea floor (floorLine) white
    col = mix(col, col * 0.45, line(e - ct, 2.2) * 0.8);
    col = mix(col, vec3(0.55, 0.52, 0.48), line(e - (ct - crustM), 1.6) * 0.35);
    float inDent = smoothstep(oldFloor - 40.0, oldFloor - 400.0, ct);
    col = mix(col, vec3(0.92, 0.95, 1.0), line(e - oldFloor, 2.2) * floorLine * inDent * step(ct, e + 1.0) * 0.85);
    // freshly cut top edge: a thin bright rim where the section meets the surface
    col += vec3(0.30, 0.29, 0.27) * edgeA * line(d, 2.4) * step(0.0, d);
  } else {
    // Everest's slab: limestone and granite bands, snow on top; rises out of the base line (discard below it)
    if (e < baseClip) discard;
    bool top = vS < -1e5;
    vec3 alb;
    if (top) { float pe = -vS - 2e5; alb = mix(vec3(0.13, 0.115, 0.10), vec3(0.82, 0.84, 0.88), smoothstep(5600.0, 6400.0, pe + (fbm(vec2(u * 3.0, pe * 0.01)) - 0.5) * 900.0)); }
    else {
      // Everest's rock: pale limestone and granite (warm light grey), clearly not the basalt behind it
      float s = e + (fbm(vec2(u * 0.3, e * 0.0008)) - 0.5) * 400.0, b = fract(s / 700.0);
      alb = vec3(0.122, 0.110, 0.095) * (0.88 + 0.16 * smoothstep(0.1, 0.3, b) * (1.0 - smoothstep(0.75, 0.95, b)) + 0.12 * (fbm(vec2(u * 2.0, e * 0.004)) - 0.5));
      // snow and ice on the cut face just under the summit ridge (vS = the profile top at this column, vR = height above its base)
      float sn = smoothstep(5600.0, 6300.0, vR + (fbm(vec2(u * 2.0, vR * 0.004)) - 0.5) * 700.0) * (1.0 - smoothstep(120.0, 420.0, vS - vR));
      alb = mix(alb, vec3(0.80, 0.82, 0.86), sn);
    }
    col = shade(alb, top ? vec3(0.0, 1.0, 0.0) : faceN);
  }
  float T; col = aerial(col, vW, T);
  gl_FragColor = vec4(col, 1.0);
}`;

export class Section {
  // o: {lon, lat (a point on the plane), az (deg, direction along the plane; 90 = east-west), side (+1: camera on the right of az,
  //     i.e. south for an E-W plane), u0, u1 (km along the plane from the point), du (km column step), bottomKm, loadU (km: load centre)}
  static async create(S, o) {
    const key = JSON.stringify(o); S._sections ||= new Map();
    if (S._sections.has(key)) return S._sections.get(key);
    const sec = new Section(S, o); S._sections.set(key, sec); await sec.build(); return sec;
  }
  constructor(S, o) { this.S = S; this.o = Object.assign({ az: 90, side: 1, u0: -200, u1: 200, du: 0.25, bottomKm: 34, loadU: 0, waterTopMax: 0 }, o); }
  // world frame of the plane (x east, z south, km): straight in world space, so the wall and the clip plane agree exactly
  frame() {
    const S = this.S, o = this.o, A = S.xyz(o.lon, o.lat, 0), az = o.az * Math.PI / 180;
    const along = new THREE.Vector2(Math.sin(az), Math.cos(az));              // (east, north)
    const al = new THREE.Vector2(along.x, -along.y).normalize();               // world (x, z)
    const nw = new THREE.Vector2(-al.y, al.x).multiplyScalar(o.side >= 0 ? 1 : -1);   // side +1: right of the direction of travel
    // for az = 90 (east): al = (1, 0), nw = (0, 1) = south (+z)
    return { A, al, nw };
  }
  w2ll(x, z) { const S = this.S, lat = S.c0.lat - z / KM_DEG; return [S.c0.lon + x / (KM_DEG * Math.cos(lat * Math.PI / 180)), lat]; }
  // world point of section coordinates: u km along, e m elevation, f km toward the camera side
  world(u, e, f = 0) { const { A, al, nw } = this.F; return new THREE.Vector3(A.x + al.x * u + nw.x * f, e * this.S.vex * 0.001, A.z + al.y * u + nw.y * f); }
  ll(u, f = 0) { const p = this.world(u, 0, f); return this.w2ll(p.x, p.z); }
  surf(u) { const [lon, lat] = this.ll(u); return this.S.heightAt(lon, lat); }
  flex(r) { const x = r / this.st.alphaKm; return Math.exp(-x) * (Math.cos(x) + Math.sin(x)); }
  crustTop(u) { const s = this.st; return s.oldFloor - s.sag * s.sagM * this.flex(Math.abs(u - s.loadU)); }
  async build() {
    const S = this.S, o = this.o; this.F = this.frame();
    const U = S.U;
    this.u = { mat: { value: 0 }, sag: { value: 1 }, sagM: { value: 8000 }, alphaKm: { value: 90 }, loadU: { value: o.loadU }, oldFloor: { value: -5000 }, crustM: { value: 6500 },
      waterTop: { value: 0 }, waterBot: { value: -1e9 }, waterA: { value: 0 }, floorLine: { value: 0 }, trenchTop: { value: -1e9 }, trenchA: { value: 0 }, baseClip: { value: -1e9 }, edgeA: { value: 1 },
      fogK: { value: 0.3 }, faceN: { value: new THREE.Vector3(this.F.nw.x, 0, this.F.nw.y) }, waterCol: { value: new THREE.Vector3(0.03, 0.30, 0.42) }, lit: { value: 0.38 }, eOff: { value: 0 } };
    const shared = { camPos: U.camPos, sunDir: U.sunDir, sunCol: U.sunCol, zenithCol: U.zenithCol, hazeCol: U.hazeCol, glowCol: U.glowCol, sunI: S.heroMat.uniforms.sunI, skyI: S.heroMat.uniforms.skyI,
      fogDens: U.fogDens, fogBg: U.fogBg, fogH: U.fogH, fogBase: U.fogBase, vex: U.vex };
    const mk = (u) => new THREE.ShaderMaterial({ uniforms: Object.assign({}, shared, u), vertexShader: WALL_VS, fragmentShader: WALL_FS, transparent: true, depthWrite: true,
      side: THREE.DoubleSide, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor });
    this.mat = mk(this.u);
    // wall: one column every du km, top = max(surface + 30 m, the highest water top), bottom = -bottomKm
    const n = Math.round((o.u1 - o.u0) / o.du) + 1, pos = new Float32Array(n * 2 * 3), aU = new Float32Array(n * 2), aS = new Float32Array(n * 2), aE = new Float32Array(n * 2), idx = [];
    this.prof = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const u = o.u0 + i * o.du, s = this.surf(u); this.prof[i] = s;
      const top = Math.max(s + 30, o.waterTopMax), bot = -o.bottomKm * 1000;
      for (const [k, e] of [[0, top], [1, bot]]) { const p = this.world(u, e), j = i * 2 + k; pos.set([p.x, p.y, p.z], j * 3); aU[j] = u; aS[j] = s; aE[j] = e; }
      if (i < n - 1) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aU', new THREE.BufferAttribute(aU, 1)); g.setAttribute('aS', new THREE.BufferAttribute(aS, 1)); g.setAttribute('aE', new THREE.BufferAttribute(aE, 1)); g.setIndex(idx);
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5);
    this.wall = new THREE.Mesh(g, this.mat); this.wall.renderOrder = 3; this.wall.frustumCulled = false;
    this.group = new THREE.Group(); this.group.add(this.wall); this.group.visible = false; S.scene.add(this.group);
    this.st = { sag: 1, sagM: 8000, alphaKm: 90, loadU: o.loadU, oldFloor: -5000, crustM: 6500 };
  }
  // Everest slab: u centre (km along the plane), width (km of real profile), f front offset and th thickness (km toward the camera)
  async everest(dir = '/lab/hawaii/data', o = {}) {
    if (this.ev) return this.ev;
    const meta = await loadMeta(dir), hm = await loadH16(dir + '/everest_h16.png', meta), eb = meta.everest_bbox;
    const at = (lon, lat) => sampleH(hm, (lon - eb[0]) / (eb[2] - eb[0]), (lat - eb[1]) / (eb[3] - eb[1]));
    let best = -1e9, sl = 86.925, st = 27.988;      // the DEM maximum near the surveyed summit
    for (let j = -30; j <= 30; j++) for (let i = -30; i <= 30; i++) { const v = at(86.925 + i * 0.0005, 27.988 + j * 0.0005); if (v > best) { best = v; sl = 86.925 + i * 0.0005; st = 27.988 + j * 0.0005; } }
    const scale = 8849 / best, W = o.width ?? 22, n = 220, kmLon = KM_DEG * Math.cos(st * Math.PI / 180);
    const prof = []; for (let i = 0; i < n; i++) { const x = -W / 2 + W * i / (n - 1); prof.push(Math.max(0, at(sl + x / kmLon, st) * scale)); }
    this.evProf = { prof, W, n, scale };
    const u = Object.assign({}, this.u, { mat: { value: 1 }, eOff: { value: 0 }, baseClip: { value: -1e9 } });
    this.evMat = new THREE.ShaderMaterial({ uniforms: Object.assign({}, this.mat.uniforms, u), vertexShader: WALL_VS, fragmentShader: WALL_FS, side: THREE.DoubleSide });
    const uc = o.u ?? 22, f = o.front ?? 1.0, th = o.th ?? 1.2;
    const P = [], AU = [], AS = [], AE = [], I = []; let k = 0;
    const push = (uu, e, ff, s) => { const p = this.world(uu, e, ff); P.push(p.x, p.y, p.z); AU.push(uu); AS.push(s); AE.push(e); return k++; };
    for (let i = 0; i < n - 1; i++) {                       // front face (at f + th) and top ribbon
      const ua = -W / 2 + W * i / (n - 1), ub = -W / 2 + W * (i + 1) / (n - 1), ea = prof[i], eB = prof[i + 1];
      const a0 = push(uc + ua, 0, f + th, ea), a1 = push(uc + ua, ea, f + th, ea), b0 = push(uc + ub, 0, f + th, eB), b1 = push(uc + ub, eB, f + th, eB); I.push(a0, a1, b0, b0, a1, b1);
      const c0 = push(uc + ua, ea, f + th, -2e5 - ea), c1 = push(uc + ua, ea, f, -2e5 - ea), d0 = push(uc + ub, eB, f + th, -2e5 - eB), d1 = push(uc + ub, eB, f, -2e5 - eB); I.push(c0, c1, d0, d0, c1, d1);
    }
    for (const [i, s] of [[0, -1], [n - 1, 1]]) { const uu = uc - W / 2 + W * i / (n - 1), e = prof[i];   // end caps
      const a = push(uu, 0, f, 0), b = push(uu, e, f, 0), c = push(uu, 0, f + th, 0), d = push(uu, e, f + th, 0); I.push(a, b, c, c, b, d); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
    for (const [nm, arr] of [['aU', AU], ['aS', AS], ['aE', AE]]) g.setAttribute(nm, new THREE.Float32BufferAttribute(arr, 1)); g.setIndex(I);
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5);
    this.evMesh = new THREE.Mesh(g, this.evMat); this.evMesh.renderOrder = 4; this.evMesh.frustumCulled = false; this.group.add(this.evMesh);
    this.ev = { u: uc, W, f, th, summit: 8849, prof, scale };
    return this.ev;
  }
  // state every frame: {sag 0..1, sagM, alphaKm, oldFloor, crustM, waterTop, waterA, floorLine, trenchTop, trenchA, edgeA,
  //   everest: {rise 0..1, base (m)}}
  set(s = {}) {
    const u = this.u, st = this.st;
    for (const k of ['sag', 'sagM', 'alphaKm', 'oldFloor', 'crustM']) st[k] = s[k] ?? { sag: 1, sagM: 8000, alphaKm: 90, oldFloor: -5000, crustM: 6500 }[k];
    st.loadU = this.o.loadU;
    for (const k of ['sag', 'sagM', 'alphaKm', 'oldFloor', 'crustM']) u[k].value = st[k];
    u.waterTop.value = s.waterTop ?? 0; u.waterBot.value = s.waterBot ?? -1e9; u.waterA.value = s.waterA ?? 0; u.floorLine.value = s.floorLine ?? 0;
    u.trenchTop.value = s.trenchTop ?? -1e9; u.trenchA.value = s.trenchA ?? 0; u.edgeA.value = s.edgeA ?? 1; u.fogK.value = s.fogK ?? 0.3;
    if (this.evMesh) {
      const ev = s.everest || {}, rise = Math.max(0, Math.min(1, ev.rise ?? 0)), base = ev.base ?? (this.crustTop(this.o.loadU));
      this.evMesh.visible = rise > 0.0005;
      this.evMat.uniforms.eOff.value = base - this.ev.summit * 1.02 * (1 - rise); this.evMat.uniforms.baseClip.value = base;
      this.ev.base = base; this.ev.rise = rise;
    }
  }
  // screen point of section coordinates (u km, e m, f km toward the camera), with the stage's camera-relative curvature
  project(u, e, f = 0) {
    const S = this.S, p = this.world(u, e, f), c = S.cam.position, dx = p.x - c.x, dz = p.z - c.z; p.y -= (dx * dx + dz * dz) / (2 * R_EARTH);
    const q = p.project(S.cam); if (q.z > 1) return null; return [(q.x + 1) / 2 * S.W, (1 - q.y) / 2 * S.H];
  }
  // a HawaiiStage camera from section coordinates: eye at (u, d km toward the camera side, alt km), looking at (tu, te m, tf km)
  cam(c) {
    const e = this.world(c.u, 0, c.d), t = this.world(c.tu ?? c.u, 0, c.tf ?? 0);
    const [lon, lat] = this.w2ll(e.x, e.z), [tLon, tLat] = this.w2ll(t.x, t.z);
    return { lon, lat, alt: c.alt, tLon, tLat, tH: c.te ?? 0, fov: c.fov ?? 30, roll: c.roll || 0, shiftX: c.shiftX || 0, shiftY: c.shiftY || 0, near: c.near, far: c.far };
  }
  // clip spec for HawaiiStage.setClip (terrain and water removed on the camera side)
  clip() { const [lon, lat] = this.w2ll(this.F.A.x, this.F.A.z); return { lon, lat, nx: this.F.nw.x, nz: this.F.nw.y }; }
}
