// Globe: NASA Blue Marble / Black Marble Earth with atmosphere, regional hi-res patches,
// highlight overlays and a geodetic camera (lat, lon, alt [Earth radii], tilt, heading, fov).
// Coordinate convention (matches THREE.SphereGeometry UVs): dir(lat,lon) = (cos φ cos λ, sin φ, -cos φ sin λ).
import * as THREE from '../../three.module.min.js';

const D2R = Math.PI / 180;
export function dirOf(lat, lon, r = 1) {
  const a = lat * D2R, b = lon * D2R;
  return new THREE.Vector3(Math.cos(a) * Math.cos(b) * r, Math.sin(a) * r, -Math.cos(a) * Math.sin(b) * r);
}
export function latLonOf(v) {
  const n = v.clone().normalize();
  return [Math.asin(n.y) / D2R, Math.atan2(-n.z, n.x) / D2R];
}
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

const EARTH_VS = `
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
void main(){ vUv=uv; vN=normalize(mat3(modelMatrix)*normal); vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;

const EARTH_FS = `
uniform sampler2D dayTex; uniform sampler2D nightTex; uniform sampler2D nrmTex; uniform float relief;
uniform sampler2D patchTex; uniform vec4 patchB; uniform float patchOn;
uniform sampler2D ovTex; uniform vec4 ovB; uniform float ovOn; uniform float ovAlpha;
uniform vec3 sunDir; uniform vec3 camPos;
uniform float dim; uniform float desat; uniform float nightAmt; uniform float exposure; uniform float ambient;
uniform vec3 tint; uniform float specAmt; uniform float rimAmt; uniform float flatBase; uniform vec3 flatColor; uniform float ovMul;
varying vec2 vUv; varying vec3 vN; varying vec3 vW;
const float PI = 3.14159265;
vec2 ll(vec3 p){ vec3 n=normalize(p); return vec2(atan(-n.z, n.x)*180.0/PI, asin(clamp(n.y,-1.0,1.0))*180.0/PI); }
void main(){
  vec3 n0=normalize(vN); vec3 v=normalize(camPos-vW);
  vec2 g = vec2(0.0);
  if (patchOn > 0.5 || ovOn > 0.5) g = ll(vW);
  vec3 n = n0;
  if (relief > 0.0) {
    vec3 tn = texture2D(nrmTex, vUv).xyz * 2.0 - 1.0;
    vec3 east = normalize(vec3(n0.z, 0.0, -n0.x) + vec3(1e-6));
    vec3 north = cross(n0, east);
    n = normalize(mix(n0, normalize(tn.x*east + tn.y*north + tn.z*n0), relief));
  }
  vec3 day = texture2D(dayTex, vUv).rgb;
  if (patchOn > 0.5) {
    vec2 q = vec2((g.x-patchB.x)/(patchB.z-patchB.x), (patchB.w-g.y)/(patchB.w-patchB.y));
    if (q.x>0.0 && q.x<1.0 && q.y>0.0 && q.y<1.0) {
      float e = smoothstep(0.0,0.04,q.x)*smoothstep(0.0,0.04,1.0-q.x)*smoothstep(0.0,0.04,q.y)*smoothstep(0.0,0.04,1.0-q.y);
      day = mix(day, texture2D(patchTex, vec2(q.x, 1.0 - q.y)).rgb, e);
    }
  }
  float lum = dot(day, vec3(0.299,0.587,0.114));
  float water = smoothstep(0.03,0.16, day.b - max(day.r, day.g*0.9));
  day = mix(day, vec3(lum), desat);
  // flat base (e.g. paleo maps): replace imagery with a uniform ocean colour; land then comes from the overlay
  day = mix(day, flatColor, flatBase);
  water = mix(water, 1.0, flatBase);
  float d = dot(n, sunDir);
  float d0 = dot(n0, sunDir);
  float lit = smoothstep(-0.10, 0.30, d0);
  vec3 col = day * (ambient + exposure*max(d, 0.0));
  vec3 h = normalize(sunDir + v);
  col += vec3(1.0,0.93,0.82) * pow(max(dot(n,h),0.0), 70.0) * water * specAmt * lit;
  vec3 night = texture2D(nightTex, vUv).rgb;
  col += night * vec3(1.0,0.76,0.42) * 1.7 * (1.0 - lit) * nightAmt;
  float term = exp(-pow(d0*5.0, 2.0));
  col += vec3(0.30,0.10,0.02) * term * 0.22;
  col *= (1.0 - dim);
  if (ovOn > 0.5) {
    vec2 q = vec2((g.x-ovB.x)/(ovB.z-ovB.x), (ovB.w-g.y)/(ovB.w-ovB.y));
    // explicit, seam-corrected gradients: atan() wraps at +-180 deg, and the raw derivative there picks the 1x1 mip
    // (a dashed line along the date line on every overlay globe facing the Pacific)
    vec2 qdx = dFdx(q), qdy = dFdy(q); float wrapU = 360.0 / (ovB.z - ovB.x);
    if (abs(qdx.x) > 0.5 * wrapU) qdx.x -= sign(qdx.x) * wrapU;
    if (abs(qdy.x) > 0.5 * wrapU) qdy.x -= sign(qdy.x) * wrapU;
    if (q.x>0.0 && q.x<1.0 && q.y>0.0 && q.y<1.0) {
      vec4 o = textureGrad(ovTex, vec2(q.x, 1.0 - q.y), vec2(qdx.x, -qdx.y), vec2(qdy.x, -qdy.y));
      vec3 oc = mix(o.rgb * (0.55 + 0.6*max(lit,0.35)), o.rgb * (ambient + exposure*max(d,0.0)) * 1.15, ovMul);
      col = mix(col, oc, o.a * ovAlpha);
    }
  }
  float fres = pow(1.0 - max(dot(n, v), 0.0), 3.0);
  col = mix(col, vec3(0.32,0.58,1.0) * (0.15 + 0.85*lit), fres * rimAmt);
  col *= tint;
  gl_FragColor = vec4(col, 1.0);
}`;

const ATMO_VS = `varying vec3 vN; varying vec3 vW;
void main(){ vN=normalize(mat3(modelMatrix)*normal); vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`;
const ATMO_FS = `uniform vec3 sunDir; uniform float strength; uniform vec3 camPos; varying vec3 vN; varying vec3 vW;
void main(){
  vec3 dir = normalize(vW - camPos);
  // closest approach of the view ray to the planet centre (unit radius planet)
  float tc = -dot(camPos, dir);
  vec3 cpt = camPos + dir * max(tc, 0.0);
  float h = length(cpt);
  float above = max(h - 1.0, 0.0);
  float i = (exp(-above / 0.010) * 0.95 + exp(-above / 0.040) * 0.28) * (1.0 - smoothstep(0.045, 0.075, above));
  // sun side of the limb is brighter; slight warm tint near terminator
  float lit = smoothstep(-0.30, 0.50, dot(normalize(cpt), sunDir));
  vec3 c = mix(vec3(0.95,0.45,0.18), vec3(0.36,0.62,1.0), smoothstep(-0.1, 0.4, dot(normalize(cpt), sunDir)));
  gl_FragColor = vec4(c * i * (0.06 + 1.1*lit) * strength, 1.0);
}`;

export class Globe {
  constructor(W, H) {
    this.W = W; this.H = H;
    this.renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.renderer.setClearColor(0x04060B, 1);
    this.renderer.autoClear = false;
    this.renderer.setPixelRatio(1); this.renderer.setSize(W, H, false);
    this.renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // all shading done in display (sRGB) space
    this.canvas = this.renderer.domElement;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(34, W / H, 0.001, 200);
    this.sunDir = new THREE.Vector3(1, 0.3, 0.4).normalize();
    this.state = { lat: 20, lon: 0, alt: 3, tilt: 0, heading: 0, fov: 34, sun: 'camera', sunAz: -35, sunEl: 28 };
  }
  _tex(url) {
    return new Promise((res, rej) => new THREE.TextureLoader().load(url, t => {
      t.colorSpace = THREE.NoColorSpace; t.anisotropy = 2; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; res(t);
    }, undefined, rej));
  }
  async init({ day = 'tex/day_8k.jpg', night = 'tex/night_8k.jpg', normal = 'tex/normal_4k.png', segments = 256 } = {}) {
    const [d, n, nm] = await Promise.all([this._tex(day), this._tex(night), this._tex(normal)]);
    nm.anisotropy = 1;
    const blank = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1); blank.needsUpdate = true;
    this.u = {
      dayTex: { value: d }, nightTex: { value: n }, nrmTex: { value: nm }, relief: { value: 0.8 },
      patchTex: { value: blank }, patchB: { value: new THREE.Vector4(0, 0, 1, 1) }, patchOn: { value: 0 },
      ovTex: { value: blank }, ovB: { value: new THREE.Vector4(-180, -90, 180, 90) }, ovOn: { value: 0 }, ovAlpha: { value: 1 },
      sunDir: { value: this.sunDir }, camPos: { value: this.camera.position },
      dim: { value: 0 }, desat: { value: 0.12 }, nightAmt: { value: 1 }, exposure: { value: 1.25 }, ambient: { value: 0.10 },
      tint: { value: new THREE.Vector3(1, 1, 1) }, specAmt: { value: 0.5 }, rimAmt: { value: 0.35 }, flatBase: { value: 0 }, flatColor: { value: new THREE.Vector3(0.035, 0.09, 0.19) }, ovMul: { value: 0 },
    };
    this.earth = new THREE.Mesh(new THREE.SphereGeometry(1, segments, segments / 2), new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: EARTH_VS, fragmentShader: EARTH_FS }));
    this.scene.add(this.earth);
    this.atmoU = { sunDir: { value: this.sunDir }, strength: { value: 1 }, camPos: { value: this.camera.position } };
    this.atmo = new THREE.Mesh(new THREE.SphereGeometry(1.08, 160, 80), new THREE.ShaderMaterial({
      uniforms: this.atmoU, vertexShader: ATMO_VS, fragmentShader: ATMO_FS, side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    }));
    this.scene.add(this.atmo);
    const r = rng(11), N = 7000, pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      const u = r() * 2 - 1, th = r() * Math.PI * 2, s = Math.sqrt(1 - u * u);
      pos.set([90 * s * Math.cos(th), 90 * u, 90 * s * Math.sin(th)], i * 3);
      const b = Math.pow(r(), 7) * 0.95 + 0.06, w = r();
      col.set([b * (0.85 + 0.15 * w), b * 0.92, b * (0.95 + 0.1 * (1 - w))], i * 3);
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    this.stars = new THREE.Points(g, new THREE.PointsMaterial({ size: 1.7, sizeAttenuation: false, vertexColors: true, transparent: true, opacity: 1, depthWrite: false }));
    this.stars.visible = false;
    // starfield background: full-screen quad sampling a frame-sized star canvas, scrolled for parallax
    const sc = document.createElement('canvas'); sc.width = this.W; sc.height = this.H; const sg = sc.getContext('2d');
    sg.fillStyle = '#04060B'; sg.fillRect(0, 0, sc.width, sc.height);
    const rr = rng(77);
    for (let i = 0; i < 1500; i++) {
      const x = rr() * sc.width, y = rr() * sc.height, b = Math.pow(rr(), 6) * 0.95 + 0.05, sz = b > 0.6 ? 1.6 : b > 0.3 ? 1.2 : 0.8, w = rr();
      sg.fillStyle = `rgba(${Math.round(230 + 25 * w)},${Math.round(232 + 10 * w)},255,${b})`; sg.beginPath(); sg.arc(x, y, sz, 0, Math.PI * 2); sg.fill();
    }
    const st = new THREE.CanvasTexture(sc); st.wrapS = st.wrapT = THREE.RepeatWrapping; st.colorSpace = THREE.NoColorSpace; st.minFilter = THREE.LinearFilter; st.generateMipmaps = false;
    this.bgU = { tex: { value: st }, off: { value: new THREE.Vector2(0, 0) }, alpha: { value: 1 } };
    this.bgScene = new THREE.Scene(); this.bgCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.bgScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({ uniforms: this.bgU, depthTest: false, depthWrite: false,
      vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }',
      fragmentShader: 'uniform sampler2D tex; uniform vec2 off; uniform float alpha; varying vec2 vUv; void main(){ vec3 c = texture2D(tex, vUv + off).rgb; gl_FragColor = vec4(mix(vec3(0.0157,0.0235,0.043), c, alpha), 1.0); }' })));
    this.set({});
    this.renderer.render(this.scene, this.camera);
  }
  // hi-res regional texture (equirectangular crop) with bounds [lon0, lat0, lon1, lat1]
  async setPatch(url, b) {
    if (!url) { this.u.patchOn.value = 0; return; }
    const t = await this._tex(url); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    if (this.u.patchTex.value && this.u.patchTex.value.dispose) this.u.patchTex.value.dispose();
    this.u.patchTex.value = t; this.u.patchB.value.set(b[0], b[1], b[2], b[3]); this.u.patchOn.value = 1;
  }
  // overlay from an image URL (RGBA PNG, equirectangular over bounds b)
  async setOverlayURL(url, b = [-180, -90, 180, 90]) {
    const t = await this._tex(url); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    if (this.u.ovTex.value && this.u.ovTex.value.dispose) this.u.ovTex.value.dispose();
    this.u.ovTex.value = t; this.u.ovB.value.set(b[0], b[1], b[2], b[3]); this.u.ovOn.value = 1;
  }
  // re-upload the current overlay canvas (after redrawing it in place)
  refreshOverlay() { if (this.u.ovTex.value && this.u.ovTex.value.isCanvasTexture) this.u.ovTex.value.needsUpdate = true; }
  // overlay from a canvas (equirectangular over bounds b); draw highlights there (fills + glow)
  setOverlay(canvas, b = [-180, -90, 180, 90]) {
    if (!canvas) { this.u.ovOn.value = 0; return; }
    const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.NoColorSpace; t.minFilter = THREE.LinearMipmapLinearFilter; t.anisotropy = 2;
    if (this.u.ovTex.value && this.u.ovTex.value.dispose) this.u.ovTex.value.dispose();
    this.u.ovTex.value = t; this.u.ovB.value.set(b[0], b[1], b[2], b[3]); this.u.ovOn.value = 1;
  }
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
    // optional screen offset of the target point: look slightly away so the target sits at (ox, oy) in NDC-ish units
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
      // key light relative to camera: azimuth (deg, + = right) / elevation (deg, + = up), mostly from behind the camera
      const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
      const cup = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 1);
      const back = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 2); // points from target toward camera
      const az = (S.sunAz ?? -35) * D2R, el = (S.sunEl ?? 28) * D2R;
      this.sunDir.copy(back.multiplyScalar(Math.cos(el) * Math.cos(az)).add(right.multiplyScalar(Math.cos(el) * Math.sin(az))).add(cup.multiplyScalar(Math.sin(el)))).normalize();
    }
    this.u.camPos.value.copy(cam.position);
    this.atmoU.camPos.value.copy(cam.position);
    // stars fade when close to the ground (sky would be bright)
    this.starAlpha = Math.min(1, Math.max(0, (S.alt - 0.02) / 0.15));
  }
  look(k, v) { this.u[k].value = v; }
  // draw a cached starfield (2x frame size) offset by camera yaw/pitch for parallax, then the globe on top
  starfield(ctx, alpha = 1) { this.starMul = alpha; }
  render() {
    const S = this.state;
    this.bgU.off.value.set(((S.lon * 6 + (S.heading || 0) * 4) / this.W) % 1, ((S.lat * 4 + (S.tilt || 0) * 6) / this.H) % 1);
    this.bgU.alpha.value = (this.starAlpha ?? 1) * (this.starMul ?? 1);
    this.renderer.clear();
    this.renderer.render(this.bgScene, this.bgCam);
    this.renderer.clearDepth();
    this.renderer.render(this.scene, this.camera);
    return this.canvas;
  }
  // project lat/lon(/height in Earth radii) to screen px; visible=false if behind the globe
  project(lat, lon, hgt = 0) {
    const p = dirOf(lat, lon, 1 + hgt);
    const cp = this.camera.position;
    const toCam = cp.clone().sub(p);
    // occlusion by the sphere: ray from p toward camera hits the unit sphere?
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
  // screen-space radius of the globe disc (px) and its center, useful for halos
  disc() {
    const c = new THREE.Vector3(0, 0, 0).project(this.camera);
    const d = this.camera.position.length();
    const ang = Math.asin(Math.min(1, 1 / d));
    const f = this.H / 2 / Math.tan(this.camera.fov * D2R / 2);
    return { x: (c.x + 1) / 2 * this.W, y: (1 - c.y) / 2 * this.H, r: Math.tan(ang) * f };
  }
}

// great-circle interpolation between two lat/lon points (t in 0..1)
export function slerpLL(a, b, t) {
  const A = dirOf(a[0], a[1]), B = dirOf(b[0], b[1]);
  const om = Math.acos(Math.min(1, Math.max(-1, A.dot(B))));
  if (om < 1e-6) return [a[0], a[1]];
  const s = Math.sin(om);
  const P = A.multiplyScalar(Math.sin((1 - t) * om) / s).add(B.multiplyScalar(Math.sin(t * om) / s));
  return latLonOf(P);
}
export function gcDist(a, b) { const A = dirOf(a[0], a[1]), B = dirOf(b[0], b[1]); return Math.acos(Math.min(1, Math.max(-1, A.dot(B)))); }
