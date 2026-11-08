// BlockStage: Mauna Loa vs Everest at the same scale, as two cut-out terrain blocks standing on one base line (no text).
// Mauna Loa block: real DEM top (ETOPO 2022 + AWS Terrain Tiles), its column runs from the summit down to its true base,
// 17,170 m (about 56,000 ft) below the summit (USGS Volcano Watch: the mass pushed the sea floor down as much as 8 km).
// Wall bands: above sea level / under water down to the old sea floor (5,000 m) / pushed into the crust; one luminous waterline at 0 m.
// Everest block: AWS Terrain Tiles (SRTM) top, scaled so the summit is the surveyed 8,849 m (29,032 ft), column from sea level.
// Both blocks share the footprint size, the base plane y = 0 and the vertical scale (vex, default 1 = true scale). 1 unit = 1 km.
import * as THREE from 'three';
import { decodeH16, sampleH, loadImage, POST_FS, POST_VS, C, LOOKS, KM_DEG } from './hterrain.js';

const VS = /* glsl */`
attribute float elev; attribute float wall;
varying vec3 vW; varying vec3 vN; varying float vElev; varying float vWall; varying vec2 vUv;
void main(){ vUv = uv; vElev = elev; vWall = wall; vN = normalize(normal); vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const FS = /* glsl */`
uniform vec3 sunDir, sunCol, skyCol, camPos, hazeCol, lineCol; uniform float sunI, skyI, isEv, fogDens, seaLine, guide1, guide2, vex, baseM;
uniform sampler2D colTex; uniform float hasTex;
varying vec3 vW; varying vec3 vN; varying float vElev; varying float vWall; varying vec2 vUv;
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
void main(){
  vec3 n = normalize(vN);
  vec3 alb;
  float e = vElev;
  if (vWall > 0.5) {
    // cut face: horizontal lava / rock layering, coloured by depth band
    float along = vW.x + vW.z;
    float strata = fbm(vec2(along * 0.35, vW.y * 6.0)) * 0.5 + fbm(vec2(along * 2.0, vW.y * 30.0)) * 0.5;
    if (isEv > 0.5) {
      alb = mix(vec3(0.062, 0.062, 0.066), vec3(0.050, 0.052, 0.058), smoothstep(3000.0, 7000.0, e));
    } else {
      vec3 above = vec3(0.046, 0.042, 0.040), under = vec3(0.022, 0.050, 0.085), root = vec3(0.030, 0.021, 0.025);
      alb = e > 0.0 ? above : (e > -5000.0 ? under : root);
    }
    alb *= 0.72 + 0.56 * strata;
  } else if (hasTex > 0.5) {
    vec3 land = texture2D(colTex, vUv).rgb; float l0 = dot(land, vec3(0.2126, 0.7152, 0.0722)); alb = max(mix(vec3(l0), land, 1.2), 0.0) * 1.15;
    alb *= 0.86 + 0.28 * fbm(vW.xz * 1.7);
  } else {
    // Everest top: snow and ice above ~5,600 m on gentler slopes, grey rock on steep faces, brown moraine lower down
    float slope = sqrt(max(1.0 - n.y * n.y, 0.0)) / max(n.y, 0.05) / vex;
    float nz = fbm(vW.xz * 2.2);
    float snow = smoothstep(5200.0, 6000.0, e + nz * 600.0) * (1.0 - smoothstep(0.75, 1.15, slope + nz * 0.2));
    vec3 rock = mix(vec3(0.10, 0.092, 0.085), vec3(0.075, 0.070, 0.068), nz);
    vec3 low = vec3(0.11, 0.095, 0.075);
    alb = mix(mix(low, rock, smoothstep(4600.0, 5400.0, e)), vec3(0.78, 0.80, 0.84), snow);
  }
  float ndl = max(dot(n, sunDir), 0.0);
  vec3 col = alb * (sunCol * sunI * ndl + skyCol * skyI * (0.55 + 0.45 * n.y));
  // luminous waterline at present sea level on Mauna Loa's cut faces; optional guide lines at the two summit heights
  float fw = max(fwidth(e), 1e-3);
  if (isEv < 0.5 && vWall > 0.5) {
    float dl = abs(e) / fw; col = mix(col, lineCol, seaLine * (1.0 - smoothstep(1.2, 2.4, dl))); col += lineCol * seaLine * exp(-dl / 4.0) * 0.25;
    float d5 = abs(e + 5000.0) / fw; col = mix(col, vec3(0.9, 0.85, 0.8) * 0.5, 0.6 * seaLine * (1.0 - smoothstep(0.8, 1.6, d5)));
  }
  float dist = length(vW - camPos); float T = exp(-fogDens * dist);
  col = col * T + hazeCol * (1.0 - T);
  gl_FragColor = vec4(col, 1.0);
}`;
const FLOOR_FS = /* glsl */`
uniform vec3 camPos, hazeCol, floorCol, sunCol, sunDir; uniform float fogDens, sunI; uniform vec4 fpA, fpB; varying vec3 vW;
float boxD(vec2 p, vec4 b){ vec2 c = (b.xy + b.zw) * 0.5, h = (b.zw - b.xy) * 0.5; vec2 d = abs(p - c) - h; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }
void main(){
  float dA = boxD(vW.xz, fpA), dB = boxD(vW.xz, fpB);
  float occ = 1.0 - 0.55 * exp(-max(min(dA, dB), 0.0) / 6.0);
  vec3 col = floorCol * (sunCol * sunI * max(sunDir.y, 0.0) * 0.55 + vec3(0.55, 0.62, 0.72) * 0.6) * occ;
  float dist = length(vW - camPos); float T = exp(-fogDens * dist);
  gl_FragColor = vec4(col * T + hazeCol * (1.0 - T), 1.0);
}`;
const SKY_FS = /* glsl */`
uniform vec3 zen, hor; varying vec3 vDir;
void main(){ vec3 d = normalize(vDir); float y = clamp(d.y, 0.0, 1.0); gl_FragColor = vec4(mix(hor, zen, pow(y, 0.5)), 1.0); }`;
const SKY_VS = /* glsl */`varying vec3 vDir; uniform vec3 camPos;
void main(){ vDir = position; vec4 w = vec4(position + camPos, 1.0); gl_Position = projectionMatrix * viewMatrix * w; gl_Position.z = gl_Position.w * 0.99999; }`;
const GUIDE_FS = /* glsl */`uniform vec3 col; uniform float a; void main(){ gl_FragColor = vec4(col * a, a); }`;

export class BlockStage {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H; this.o = o; this.vex = o.vex ?? 1.0;
    this.R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.R.setPixelRatio(1); this.R.setSize(W, H, false);
    this.rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: o.samples ?? 4, depthBuffer: true });
    this.scene = new THREE.Scene(); this.cam = new THREE.PerspectiveCamera(30, W / H, 0.5, 5000);
  }
  async load(dir) {
    const meta = this.meta = await (await fetch(dir + '/meta.json')).json();
    const [hI, eI] = await Promise.all([loadImage(dir + '/hero_h16.png'), loadImage(dir + '/everest_h16.png')]);
    const hero = decodeH16(hI, meta), ev = decodeH16(eI, meta);
    const colTex = await new THREE.TextureLoader().loadAsync(dir + '/hero_color.jpg'); colTex.colorSpace = THREE.SRGBColorSpace; colTex.anisotropy = 8;
    const half = this.o.half ?? 14, gap = this.o.gap ?? 10, N = this.o.n ?? 360;
    const hb = meta.hero_bbox, eb = meta.everest_bbox;
    // summit positions = DEM maxima near the named peaks
    const peak = (hm, bb, lon, lat, r) => { let best = -1e9, bl = lon, bt = lat; for (let j = -r; j <= r; j++) for (let i = -r; i <= r; i++) {
      const lo = lon + i * 0.0005, la = lat + j * 0.0005, v = sampleH(hm, (lo - bb[0]) / (bb[2] - bb[0]), (la - bb[1]) / (bb[3] - bb[1])); if (v > best) { best = v; bl = lo; bt = la; } } return { h: best, lon: bl, lat: bt }; };
    const ml = peak(hero, hb, -155.6054, 19.4756, 30), es = peak(ev, eb, 86.925, 27.988, 30);
    this.facts = { mlDem: ml.h, evDem: es.h };
    const ML_TOTAL = 17170, EV = 8849;
    this.mlBase = ml.h - ML_TOTAL;  // true base: the column is 17,170 m from the DEM summit
    const evScale = EV / es.h;      // Everest relief scaled so the DEM summit is the surveyed 8,849 m (DEM grid smooths the peak)
    this.U = {
      sunDir: { value: new THREE.Vector3() }, sunCol: { value: new THREE.Color() }, skyCol: { value: new THREE.Color() }, camPos: { value: new THREE.Vector3() },
      hazeCol: { value: new THREE.Color() }, lineCol: { value: new THREE.Vector3(0.55, 1.6, 1.9) }, sunI: { value: 3.3 }, skyI: { value: 0.7 }, fogDens: { value: 0.0005 },
      seaLine: { value: 1 }, vex: { value: this.vex },
    };
    const mk = (fn, cx, isEv, base) => {
      // top grid
      const pos = [], uv = [], el = [], wl = [], idx = [];
      const hAt = (i, j) => fn(i / (N - 1), j / (N - 1));
      const yOf = (e) => (e - base) * 0.001 * this.vex;
      for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
        const u = i / (N - 1), v = j / (N - 1), e = hAt(i, j).e;
        pos.push(cx - half + u * 2 * half, yOf(e), half - v * 2 * half); uv.push(...hAt(i, j).uv); el.push(e); wl.push(0);
      }
      for (let j = 0; j < N - 1; j++) for (let i = 0; i < N - 1; i++) { const a = j * N + i, b = a + 1, c = a + N, d = c + 1; idx.push(a, b, c, b, d, c); }
      const top = new THREE.BufferGeometry();
      top.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); top.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      top.setAttribute('elev', new THREE.Float32BufferAttribute(el, 1)); top.setAttribute('wall', new THREE.Float32BufferAttribute(wl, 1)); top.setIndex(idx); top.computeVertexNormals();
      // walls: 4 strips from the top edge down to the base line, flat normals
      const wp = [], ev2 = [], wn = [], wu = [], wi = []; let k = 0;
      const edges = [[(t) => [t, 0], [0, 0, 1]], [(t) => [N - 1, t], [1, 0, 0]], [(t) => [N - 1 - t, N - 1], [0, 0, -1]], [(t) => [0, N - 1 - t], [-1, 0, 0]]];
      for (const [f, nrm] of edges) for (let t = 0; t < N; t++) {
        const [i, j] = f(t), e = hAt(i, j).e, x = cx - half + i / (N - 1) * 2 * half, z = half - j / (N - 1) * 2 * half;
        wp.push(x, yOf(e), z, x, 0, z); ev2.push(e, base); wn.push(...nrm, ...nrm); wu.push(0, 0, 0, 0);
        if (t < N - 1) { const a = k, b = k + 1, c = k + 2, d = k + 3; wi.push(a, b, c, c, b, d); } k += 2;
      }
      const wg = new THREE.BufferGeometry();
      wg.setAttribute('position', new THREE.Float32BufferAttribute(wp, 3)); wg.setAttribute('normal', new THREE.Float32BufferAttribute(wn, 3));
      wg.setAttribute('uv', new THREE.Float32BufferAttribute(wu, 2)); wg.setAttribute('elev', new THREE.Float32BufferAttribute(ev2, 1));
      wg.setAttribute('wall', new THREE.Float32BufferAttribute(new Array(wp.length / 3).fill(1), 1)); wg.setIndex(wi);
      const mat = new THREE.ShaderMaterial({ uniforms: Object.assign({}, this.U, { isEv: { value: isEv }, colTex: { value: colTex }, hasTex: { value: isEv ? 0 : 1 }, baseM: { value: base } }), vertexShader: VS, fragmentShader: FS, side: THREE.DoubleSide });
      const g = new THREE.Group(); g.add(new THREE.Mesh(top, mat)); g.add(new THREE.Mesh(wg, mat)); return g;
    };
    const kmLon = (lat) => KM_DEG * Math.cos(lat * Math.PI / 180);
    const mlFn = (u, v) => { const lon = ml.lon + (u * 2 - 1) * half / kmLon(ml.lat), lat = ml.lat + (v * 2 - 1) * half / KM_DEG;
      const uu = (lon - hb[0]) / (hb[2] - hb[0]), vv = (lat - hb[1]) / (hb[3] - hb[1]); return { e: sampleH(hero, uu, vv), uv: [uu, vv] }; };
    const evFn = (u, v) => { const lon = es.lon + (u * 2 - 1) * half / kmLon(es.lat), lat = es.lat + (v * 2 - 1) * half / KM_DEG;
      return { e: sampleH(ev, (lon - eb[0]) / (eb[2] - eb[0]), (lat - eb[1]) / (eb[3] - eb[1])) * evScale, uv: [0, 0] }; };
    this.xML = -(half + gap / 2); this.xEV = half + gap / 2;
    this.scene.add(mk(mlFn, this.xML, 0, this.mlBase));
    this.scene.add(mk(evFn, this.xEV, 1, 0));
    this.topML = ML_TOTAL * 0.001 * this.vex; this.topEV = EV * 0.001 * this.vex; this.seaY = -this.mlBase * 0.001 * this.vex;
    // floor
    this.floorMat = new THREE.ShaderMaterial({ uniforms: Object.assign({}, this.U, { floorCol: { value: new THREE.Vector3(0.05, 0.06, 0.075) },
      fpA: { value: new THREE.Vector4(this.xML - half, -half, this.xML + half, half) }, fpB: { value: new THREE.Vector4(this.xEV - half, -half, this.xEV + half, half) } }),
      vertexShader: 'varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }', fragmentShader: FLOOR_FS });
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000), this.floorMat); fl.rotation.x = -Math.PI / 2; fl.position.y = -0.01; this.scene.add(fl);
    this.skyU = { zen: { value: new THREE.Color() }, hor: { value: new THREE.Color() }, camPos: this.U.camPos };
    const sky = new THREE.Mesh(new THREE.SphereGeometry(3000, 48, 24), new THREE.ShaderMaterial({ uniforms: this.skyU, vertexShader: SKY_VS, fragmentShader: SKY_FS, side: THREE.BackSide, depthWrite: false }));
    sky.renderOrder = -1; sky.frustumCulled = false; this.scene.add(sky);
    // optional guide lines at the two summit heights (thin translucent bars spanning both blocks)
    this.guides = new THREE.Group(); this.scene.add(this.guides); this.guides.visible = false;
    for (const y of [this.topML, this.topEV]) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(4 * half + gap + 10, 0.06 * this.vex + 0.04, 0.06), new THREE.ShaderMaterial({ uniforms: { col: { value: new THREE.Vector3(1, 1, 1) }, a: { value: 0.75 } }, fragmentShader: GUIDE_FS, vertexShader: 'void main(){ gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }', transparent: true, depthWrite: false, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor }));
      m.position.set(0, y, 0); this.guides.add(m);
    }
    this.postMat = new THREE.ShaderMaterial({ uniforms: { src: { value: this.rt.texture }, exposure: { value: 1.15 }, vignette: { value: 0.18 }, grain: { value: 0.01 }, seed: { value: 0 }, sat: { value: 1.15 }, contrast: { value: 1.08 }, lift: { value: 0 }, res: { value: new THREE.Vector2(this.W, this.H) } },
      vertexShader: POST_VS, fragmentShader: POST_FS, depthTest: false, depthWrite: false });
    this.postScene = new THREE.Scene(); const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.postMat); q.frustumCulled = false; this.postScene.add(q);
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  setLook(name, sunAz, sunEl) {
    const L = LOOKS[name] || LOOKS.day, A = THREE.MathUtils.degToRad(sunAz), E = THREE.MathUtils.degToRad(sunEl);
    this.U.sunDir.value.set(Math.sin(A) * Math.cos(E), Math.sin(E), -Math.cos(A) * Math.cos(E));
    this.U.sunCol.value = C(L.sun); this.U.skyCol.value = C(L.zenith).lerp(C(L.horizon), 0.5); this.U.hazeCol.value = C(L.haze[0], L.haze[1]);
    this.U.sunI.value = L.sunI; this.U.skyI.value = L.skyI; this.skyU.zen.value = C(L.zenith); this.skyU.hor.value = C(L.horizon);
  }
  // camera in block space: eye [x,y,z] km and target [x,y,z] km (x east, y up, z south); default frames both blocks from the south-east
  setCamera(c) {
    this.cam.position.set(...c.eye); this.cam.lookAt(new THREE.Vector3(...c.target)); this.cam.fov = c.fov ?? 30; this.cam.updateProjectionMatrix(); this.cam.updateMatrixWorld();
    this.U.camPos.value.copy(this.cam.position);
  }
  render(seed = 0) {
    this.postMat.uniforms.seed.value = seed;
    this.R.setRenderTarget(this.rt); this.R.render(this.scene, this.cam);
    this.R.setRenderTarget(null); this.R.render(this.postScene, this.postCam); return this.R.domElement;
  }
}
