// ch6 helper: "future Earth" renderer — today's continents (Blue Marble texture, clipped by Natural Earth plate masks)
// rigidly rotated on the sphere (true plate motion = rotation about Earth's centre) over a flat ocean globe.
// Rendered with the shared Globe's own WebGL renderer right after the globe pass (same context → texture and depth reuse).
// Everything is a pure function of the plate quaternions you pass in (deterministic).
import * as THREE from '../../three.module.min.js';
import { loadGeo, rings } from '../../lib/geo.js';

const D2R = Math.PI / 180;
export const PLATES = ['NA', 'SA', 'AF', 'EU', 'AU', 'AN'];
export function dir(lat, lon) { const a = lat * D2R, b = lon * D2R; return new THREE.Vector3(Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)); }
export function ll(v) { const n = v.clone().normalize(); return [Math.asin(Math.max(-1, Math.min(1, n.y))) / D2R, Math.atan2(-n.z, n.x) / D2R]; }
// rotation about an Euler pole (deg); positive = counter-clockwise seen from outside above the pole
export function qPole(lat, lon, deg) { return new THREE.Quaternion().setFromAxisAngle(dir(lat, lon), deg * D2R); }
// rotation that carries point `from` to `to` along the great circle, then spins `spin` deg about `to`
export function qMove(from, to, spin = 0) {
  const q = new THREE.Quaternion().setFromUnitVectors(dir(from[0], from[1]), dir(to[0], to[1]));
  if (spin) q.premultiply(new THREE.Quaternion().setFromAxisAngle(dir(to[0], to[1]), spin * D2R));
  return q;
}
export function rotLL(q, lat, lon) { return ll(dir(lat, lon).applyQuaternion(q)); }

// ---- plate assignment of Natural Earth polygons ----
const MULTI = new Set(['France', 'Netherlands', 'United Kingdom', 'United States of America', 'Spain', 'Portugal', 'Norway', 'Denmark', 'Chile', 'Ecuador', 'Russia', 'Yemen', 'Australia', 'New Zealand']);
function polyCentroid(r) { let x = 0, y = 0, z = 0; for (const [lo, la] of r) { const v = dir(la, lo); x += v.x; y += v.y; z += v.z; } return ll(new THREE.Vector3(x, y, z)); }
function ringArea(r) { let a = 0; for (let i = 0, j = r.length - 1; i < r.length; j = i++) a += (r[j][0] + r[i][0]) * (r[j][1] - r[i][1]); return Math.abs(a / 2); }
function byLocation(la, lo) {
  if (la < -60) return 'AN';
  if (lo < -168 && la > 55) return 'EU';                     // Chukotka east of the dateline
  if (lo > 170 && la > 50 && la < 56) return 'NA';            // Aleutians
  if (lo < -150 && la < 30) return null;                     // Hawaii (Pacific plate) — leave out
  if (la > 62.8 && la < 66.8 && lo > -25 && lo < -13) return 'EU';   // Iceland
  if (la > 59 && lo > -75 && lo < -10) return 'NA';                    // Greenland
  if (lo > -170 && lo < -25) {                                         // the Americas
    if (la > 12.2 || (lo < -77.3 && la > 7.0)) return 'NA';
    return 'SA';
  }
  if (la < 37.5 && lo > -26 && lo < 52 && !(lo > 34.5 && la > 12.4)) return 'AF';
  if (lo > 110 && la < -9 && la > -50) return 'AU';
  if (la > -12) return 'EU';
  return null;
}
function plateOf(f, la, lo) {
  const P = f.properties, name = P.ADMIN || P.NAME;
  // western New Guinea (and Aru/Tanimbar) ride the Australian plate, not Eurasia: otherwise Papua lands on Australia in Aurica
  if (name === 'Indonesia' && lo > 130.5 && la < -0.5) return 'AU';
  if (MULTI.has(name)) return byLocation(la, lo);
  const c = P.CONTINENT;
  if (c === 'North America') return 'NA';
  if (c === 'South America') return (la > 12.2) ? 'NA' : 'SA';
  if (c === 'Africa') return 'AF';
  if (c === 'Europe' || c === 'Asia') return 'EU';
  if (c === 'Antarctica') return 'AN';
  if (c === 'Oceania') return (lo > 110 && la < -0.5 && la > -50 && lo < 180) ? 'AU' : null;
  return null;
}

const VS = `varying vec3 vW; void main(){ vec4 w = modelMatrix*vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix*viewMatrix*w; }`;
const FS = `
uniform sampler2D dayTex; uniform sampler2D maskA; uniform sampler2D maskB; uniform sampler2D heatTex;
uniform mat3 rot[6]; uniform vec3 capC[6]; uniform float capR[6]; uniform vec4 tint[6];
uniform vec3 sunDir; uniform vec3 camPos; uniform float exposure; uniform float ambient; uniform float desat; uniform float heatAmt; uniform float alpha; uniform float dim; uniform vec4 heatPal;
varying vec3 vW;
const float PI = 3.14159265;
void main(){
  vec3 p = normalize(vW);
  vec3 col = vec3(0.0); float cov = 0.0;
  float lod = log2(max(max(length(dFdx(p)), length(dFdy(p))) * 1303.8, 1e-4));
  for (int i = 0; i < 6; i++) {
    if (dot(p, capC[i]) < capR[i]) continue;
    vec3 q = rot[i] * p;
    float u = atan(-q.z, q.x) / (2.0*PI) + 0.5; float v = asin(clamp(q.y,-1.0,1.0)) / PI + 0.5;
    vec4 ma = texture2D(maskA, vec2(u, v)); vec4 mb = texture2D(maskB, vec2(u, v));
    float m = i == 0 ? ma.r : i == 1 ? ma.g : i == 2 ? ma.b : i == 3 ? mb.r : i == 4 ? mb.g : mb.b;
    if (m < 0.003) continue;
    vec3 c = textureLod(dayTex, vec2(u, v), max(lod, 0.0)).rgb;
    float lum = dot(c, vec3(0.299,0.587,0.114));
    c = mix(c, vec3(lum), desat);
    c = mix(c, tint[i].rgb * (0.35 + 0.9*lum), tint[i].a);
    float k = m * (1.0 - cov);
    col += c * k; cov += k;
  }
  if (cov < 0.003) discard;
  col /= max(cov, 1e-4);
  if (heatAmt > 0.001) {
    float u = atan(-p.z, p.x) / (2.0*PI) + 0.5; float v = asin(clamp(p.y,-1.0,1.0)) / PI + 0.5;
    float h = texture2D(heatTex, vec2(u, v)).r;
    vec3 cool = vec3(0.27, 0.88, 0.54), warm = vec3(1.0, 0.36, 0.21), hot = vec3(0.50, 0.03, 0.03);
    vec3 hc = h < heatPal.x ? cool : mix(warm, hot, smoothstep(heatPal.y, heatPal.z, h));
    float lumc = dot(col, vec3(0.299,0.587,0.114));
    col = mix(col, hc * (0.55 + 0.7*lumc), heatAmt * 0.88);
  }
  vec3 v = normalize(camPos - vW);
  float d = dot(p, sunDir);
  vec3 lit = col * (ambient + exposure * max(d, 0.0));
  float fres = pow(1.0 - max(dot(p, v), 0.0), 3.0);
  lit = mix(lit, vec3(0.32,0.58,1.0) * (0.15 + 0.85*smoothstep(-0.1,0.3,d)), fres * 0.35);
  lit *= (1.0 - dim);
  gl_FragColor = vec4(lit * cov * alpha, cov * alpha);
}`;

export async function createFuture(api) {
  const g = api.g;
  const C = await loadGeo('ne_50m_admin_0_countries');
  const W = 4096, H = 2048;
  const cvA = document.createElement('canvas'); cvA.width = W; cvA.height = H;
  const cvB = document.createElement('canvas'); cvB.width = W; cvB.height = H;
  const gA = cvA.getContext('2d'), gB = cvB.getContext('2d');
  for (const gg of [gA, gB]) { gg.fillStyle = '#000'; gg.fillRect(0, 0, W, H); gg.globalCompositeOperation = 'lighter'; }
  const X = lo => (lo + 180) / 360 * W, Y = la => (90 - la) / 180 * H;
  const chan = { NA: [gA, '#ff0000'], SA: [gA, '#00ff00'], AF: [gA, '#0000ff'], EU: [gB, '#ff0000'], AU: [gB, '#00ff00'], AN: [gB, '#0000ff'] };
  const caps = {}; for (const p of PLATES) caps[p] = { x: 0, y: 0, z: 0, pts: [] };
  const plateRings = {}; for (const p of PLATES) plateRings[p] = [];
  for (const f of C.features) {
    const g0 = f.geometry; if (!g0) continue;
    const polys = g0.type === 'Polygon' ? [g0.coordinates] : g0.type === 'MultiPolygon' ? g0.coordinates : [];
    for (const poly of polys) {
      const outer = poly[0]; if (!outer || outer.length < 4) continue;
      const [la, lo] = polyCentroid(outer);
      const pl = plateOf(f, la, lo); if (!pl) continue;
      if (ringArea(outer) < 0.02 && pl !== 'AN') continue;   // specks
      const [gg, col] = chan[pl];
      gg.fillStyle = col; gg.beginPath();
      for (const r of poly) { r.forEach(([x, y], i) => i ? gg.lineTo(X(x), Y(y)) : gg.moveTo(X(x), Y(y))); gg.closePath(); }
      gg.fill('evenodd');
      plateRings[pl].push(outer);
      const cp = caps[pl]; const step = Math.max(1, Math.floor(outer.length / 60));
      for (let i = 0; i < outer.length; i += step) { const v = dir(outer[i][1], outer[i][0]); cp.x += v.x; cp.y += v.y; cp.z += v.z; cp.pts.push(v); }
    }
  }
  // bounding caps (centre + cos radius) per plate
  const capC0 = {}, capCos = {};
  for (const p of PLATES) {
    const cp = caps[p]; let c = new THREE.Vector3(cp.x, cp.y, cp.z);
    if (p === 'AN' || c.lengthSq() < 1e-9) c = new THREE.Vector3(0, -1, 0);
    c.normalize();
    let mind = 1; for (const v of cp.pts) mind = Math.min(mind, c.dot(v));
    const ang = Math.acos(Math.max(-1, Math.min(1, mind))) + 3 * D2R;
    capC0[p] = c; capCos[p] = Math.cos(Math.min(Math.PI, ang));
  }
  const mkTex = (cv) => { const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.NoColorSpace; t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = false; t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.ClampToEdgeWrapping; return t; };
  const heatCv = document.createElement('canvas'); heatCv.width = 512; heatCv.height = 256;
  const heatTex = mkTex(heatCv);
  const U = {
    dayTex: { value: g.u.dayTex.value }, maskA: { value: mkTex(cvA) }, maskB: { value: mkTex(cvB) }, heatTex: { value: heatTex },
    rot: { value: PLATES.map(() => new THREE.Matrix3()) }, capC: { value: PLATES.map(p => capC0[p].clone()) }, capR: { value: PLATES.map(p => capCos[p]) },
    tint: { value: PLATES.map(() => new THREE.Vector4(1, 0.35, 0.2, 0)) },
    sunDir: { value: g.sunDir }, camPos: { value: g.camera.position }, exposure: { value: 1.25 }, ambient: { value: 0.12 }, desat: { value: 0.15 },
    heatAmt: { value: 0 }, alpha: { value: 1 }, dim: { value: 0 }, heatPal: { value: new THREE.Vector4(0.3, 0.45, 0.95, 0) },
  };
  const mat = new THREE.ShaderMaterial({ uniforms: U, vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, depthTest: true,
    blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1.0012, 192, 96), mat);
  const scene = new THREE.Scene(); scene.add(mesh);
  // mask pixel lookup (for the heat-map precompute)
  let maskData = null;
  const maskAt = (p, la, lo) => {
    if (!maskData) maskData = { A: gA.getImageData(0, 0, W, H).data, B: gB.getImageData(0, 0, W, H).data };
    const x = Math.min(W - 1, Math.max(0, Math.floor((lo + 180) / 360 * W))), y = Math.min(H - 1, Math.max(0, Math.floor((90 - la) / 180 * H)));
    const i = (y * W + x) * 4; const k = { NA: ['A', 0], SA: ['A', 1], AF: ['A', 2], EU: ['B', 0], AU: ['B', 1], AN: ['B', 2] }[p];
    return maskData[k[0]][i + k[1]] / 255;
  };
  // coastline runs per plate (for crisp 2D outlines of moving plates)
  const coast = {}; for (const p of PLATES) coast[p] = [];
  const CL = await loadGeo('ne_50m_coastline');
  for (const f of CL.features) {
    for (const line of rings(f)) {
      let cur = null, curP = null, last = null;
      for (const pt of line) {
        const pl = byLocation(pt[1], pt[0]) || (pt[1] < -60 ? 'AN' : null);
        if (pl !== curP) { if (cur && cur.length > 2) coast[curP].push(cur); cur = pl ? [pt] : null; curP = pl; last = pt; continue; }
        if (!cur) continue;
        if (Math.hypot(pt[0] - last[0], pt[1] - last[1]) < 0.3) continue;
        cur.push(pt); last = pt;
      }
      if (cur && cur.length > 2) coast[curP].push(cur);
    }
  }
  for (const p of PLATES) coast[p] = coast[p].filter(r => { let L = 0; for (let i = 1; i < r.length; i++) L += Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1]); return L > 3; });
  const F = {
    plateRings, U, coast,
    q: Object.fromEntries(PLATES.map(p => [p, new THREE.Quaternion()])),
    // set plate quaternions: {NA: q, ...} (missing = identity)
    setPose(pose) {
      PLATES.forEach((p, i) => {
        const q = (pose && pose[p]) || new THREE.Quaternion();
        F.q[p] = q;
        const m4 = new THREE.Matrix4().makeRotationFromQuaternion(q.clone().invert());
        U.rot.value[i].setFromMatrix4(m4);
        U.capC.value[i].copy(capC0[p]).applyQuaternion(q);
      });
    },
    setTint(t) { PLATES.forEach((p, i) => { const v = t && t[p]; if (v) U.tint.value[i].set(v[0], v[1], v[2], v[3]); else U.tint.value[i].w = 0; }); },
    // draw globe (flat ocean) + moved continents onto ctx with the globe camera state
    draw(ctx, state, o = {}) {
      g.set(Object.assign({ sun: 'camera', lookOffset: null, tilt: 0, heading: 0, fov: 34 }, state));
      const look = Object.assign({ dim: 0, desat: 0, ovAlpha: 0, relief: 0, nightAmt: 0, exposure: 1.25, flatBase: 1, ovMul: 0, ambient: 0.12 }, o.look || {});
      for (const k in look) g.look(k, look[k]);
      const ovOn = g.u.ovOn.value, patchOn = g.u.patchOn.value;
      g.u.ovOn.value = 0; g.u.patchOn.value = 0;
      g.starfield(ctx, o.starAlpha ?? 1);
      const cv = g.render();
      U.sunDir.value = g.sunDir; U.camPos.value = g.camera.position;
      U.heatAmt.value = o.heat || 0; U.alpha.value = o.alpha ?? 1; U.dim.value = o.dim || 0; U.desat.value = o.desat ?? 0.15;
      g.renderer.render(scene, g.camera);
      g.u.ovOn.value = ovOn; g.u.patchOn.value = patchOn;
      ctx.drawImage(cv, 0, 0);
    },
    // heat map of the current pose: blurred land mask in world coordinates (computed once per pose)
    buildHeat(blurPx = 9) {
      const w = heatCv.width, h = heatCv.height; const land = new Float32Array(w * h);
      const inv = PLATES.map(p => F.q[p].clone().invert());
      for (let y = 0; y < h; y++) {
        const la = 90 - (y + 0.5) / h * 180;
        for (let x = 0; x < w; x++) {
          const lo = -180 + (x + 0.5) / w * 360; const v = dir(la, lo);
          let m = 0;
          PLATES.forEach((p, i) => { if (p === 'AN' || m >= 1) return; const q = ll(v.clone().applyQuaternion(inv[i])); m = Math.max(m, maskAt(p, q[0], q[1])); });
          land[y * w + x] = m > 0.5 ? 1 : 0;
        }
      }
      // separable box blur x3 (wraps in longitude)
      let a = land, b = new Float32Array(w * h);
      const r = blurPx;
      for (let pass = 0; pass < 3; pass++) {
        for (let y = 0; y < h; y++) { let s = 0; for (let k = -r; k <= r; k++) s += a[y * w + ((k + w) % w)]; for (let x = 0; x < w; x++) { b[y * w + x] = s / (2 * r + 1); s += a[y * w + ((x + r + 1) % w)] - a[y * w + ((x - r + w) % w)]; } }
        [a, b] = [b, a];
        for (let x = 0; x < w; x++) { let s = 0; for (let k = -r; k <= r; k++) s += a[Math.min(h - 1, Math.max(0, k)) * w + x]; for (let y = 0; y < h; y++) { b[y * w + x] = s / (2 * r + 1); s += a[Math.min(h - 1, y + r + 1) * w + x] - a[Math.max(0, y - r) * w + x]; } }
        [a, b] = [b, a];
      }
      const id = heatCv.getContext('2d').createImageData(w, h);
      let nl = 0, ncool = 0;
      for (let i = 0; i < w * h; i++) {
        const hv = land[i] ? Math.max(0, Math.min(1, (a[i] - 0.5) * 2)) : 0;
        if (land[i]) { nl++; if (hv < 0.3) ncool++; }
        id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = Math.round(hv * 255); id.data[i * 4 + 3] = 255;
      }
      heatCv.getContext('2d').putImageData(id, 0, 0); heatTex.needsUpdate = true;
      return { coolShare: ncool / Math.max(1, nl) };
    },
  };
  F.setPose({});
  return F;
}

// interpolate a pose: each plate {q, t0, t1, ease}; lt local time
export function poseAt(spec, lt, easeDefault) {
  const out = {};
  for (const p in spec) {
    const s = spec[p];
    const k = Math.max(0, Math.min(1, (lt - s.t0) / Math.max(1e-6, s.t1 - s.t0)));
    const e = (s.ease || easeDefault || (x => x))(k);
    out[p] = new THREE.Quaternion().slerp(s.q, e);   // identity → q
  }
  return out;
}
export { THREE };
