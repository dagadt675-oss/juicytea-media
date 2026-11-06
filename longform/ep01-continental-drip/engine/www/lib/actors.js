// Animated 3D characters (CC0 Quaternius / Kenney rigs) in small "diorama" scenes, rendered deterministically.
// A Stage owns its own WebGL renderer + scene + camera + lights; Actors play clip timelines evaluated at absolute time.
import * as THREE from '../three.module.min.js';
import { GLTFLoader } from '../jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from '../jsm/utils/SkeletonUtils.js';

const loader = new GLTFLoader();
const cache = {};
export function loadGLB(url) { return cache[url] || (cache[url] = new Promise((res, rej) => loader.load(url, res, undefined, rej))); }
const D2R = Math.PI / 180;

export class Stage {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H;
    this.renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: true, premultipliedAlpha: true });
    this.renderer.setPixelRatio(1); this.renderer.setSize(W, H, false);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping; this.renderer.toneMappingExposure = o.exposure ?? 1.05;
    this.renderer.shadowMap.enabled = o.shadows ?? true; this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setClearColor(0x000000, 0);
    this.canvas = this.renderer.domElement;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(o.fov || 32, W / H, 0.05, 500);
    const hemi = new THREE.HemisphereLight(o.sky || 0xbfd8ff, o.ground || 0x30261c, o.hemi ?? 1.1); this.scene.add(hemi);
    const key = new THREE.DirectionalLight(o.keyColor || 0xfff1dc, o.key ?? 2.6); key.position.set(5, 9, 6); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); key.shadow.camera.near = 0.5; key.shadow.camera.far = 40;
    const s = o.shadowExtent || 6; Object.assign(key.shadow.camera, { left: -s, right: s, top: s, bottom: -s }); key.shadow.bias = -0.0005; key.shadow.radius = 4;
    this.scene.add(key); this.key = key;
    const rim = new THREE.DirectionalLight(o.rimColor || 0x7fb4ff, o.rim ?? 1.4); rim.position.set(-6, 4, -7); this.scene.add(rim);
    this.actors = [];
  }
  add(obj) { this.scene.add(obj); return obj; }
  lookFrom(pos, target, fov) { this.camera.position.set(...pos); this.camera.lookAt(new THREE.Vector3(...target)); if (fov) { this.camera.fov = fov; } this.camera.updateProjectionMatrix(); }
  render(t) { for (const a of this.actors) a.update(t); this.renderer.render(this.scene, this.camera); return this.canvas; }
  project(v) { const p = v.clone().project(this.camera); return { x: (p.x + 1) / 2 * this.W, y: (1 - p.y) / 2 * this.H }; }
}

export class Actor {
  // url: glb; o: {scale, clipPrefix}
  static async create(stage, url, o = {}) {
    const g = await loadGLB(url);
    const a = new Actor();
    a.root = SkeletonUtils.clone(g.scene);
    a.root.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = false; m.frustumCulled = false; if (m.material) { m.material = m.material.clone(); m.material.side = THREE.FrontSide; } } });
    a.root.scale.setScalar(o.scale || 1);
    a.mixer = new THREE.AnimationMixer(a.root);
    a.clips = {};
    for (const c of g.animations) { const short = c.name.split('|').pop(); a.clips[short] = c; }
    a.actions = {};
    a.timeline = [{ t: -1e9, clip: o.idle || Object.keys(a.clips).find(k => /^idle$/i.test(k)) || Object.keys(a.clips)[0], fade: 0 }];
    a.path = null; // [{t, x, y, z, ry}]
    stage.add(a.root); stage.actors.push(a);
    return a;
  }
  action(name) {
    if (!this.actions[name]) { const c = this.clips[name]; if (!c) throw new Error('no clip ' + name + ' in ' + Object.keys(this.clips).join(',')); const ac = this.mixer.clipAction(c); ac.play(); ac.enabled = true; ac.setEffectiveWeight(0); this.actions[name] = ac; }
    return this.actions[name];
  }
  // schedule: play clip from absolute time t (seconds), crossfading over `fade`; once:true clamps at last frame
  play(t, clip, o = {}) { this.timeline.push({ t, clip, fade: o.fade ?? 0.25, once: !!o.once, speed: o.speed ?? 1 }); this.timeline.sort((a, b) => a.t - b.t); return this; }
  moveAlong(keys) { this.path = keys; return this; }
  update(t) {
    // find current and previous entries
    let i = 0; while (i + 1 < this.timeline.length && this.timeline[i + 1].t <= t) i++;
    const cur = this.timeline[i], prev = i > 0 ? this.timeline[i - 1] : null;
    for (const k in this.actions) this.actions[k].setEffectiveWeight(0);
    const setA = (e, w) => {
      const ac = this.action(e.clip); const dur = ac.getClip().duration;
      let lt = Math.max(0, (t - e.t) * (e.speed || 1));
      if (e.once) lt = Math.min(lt, dur - 1e-3); else lt = lt % dur;
      ac.time = lt; ac.setEffectiveWeight(w);
    };
    const k = cur.fade > 0 ? Math.min(1, (t - cur.t) / cur.fade) : 1;
    if (prev && k < 1) {
      // previous clip keeps running at its time t
      setA(prev, 1 - k);
    }
    setA(cur, k);
    this.mixer.update(0);
    if (this.path) {
      const P = this.path; let j = 0; while (j + 1 < P.length && P[j + 1].t <= t) j++;
      const a = P[j], b = P[Math.min(j + 1, P.length - 1)];
      const u = b.t > a.t ? Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))) : 0;
      const e = b.ease ? b.ease(u) : u;
      this.root.position.set(a.x + (b.x - a.x) * e, (a.y || 0) + ((b.y || 0) - (a.y || 0)) * e, a.z + (b.z - a.z) * e);
      const ry = (a.ry || 0) + ((b.ry || 0) - (a.ry || 0)) * e; this.root.rotation.y = ry * D2R;
    }
  }
}

// tiny planet using the Earth textures (day map) — a stylised sphere the actor can stand on
export async function tinyPlanet(stage, o = {}) {
  const tex = await new Promise(r => new THREE.TextureLoader().load(o.map || 'tex/day_8k.jpg', t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; r(t); }));
  const m = new THREE.Mesh(new THREE.SphereGeometry(o.radius || 3, 160, 80), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.85, metalness: 0 }));
  m.receiveShadow = true; stage.add(m);
  // atmosphere rim
  const glow = new THREE.Mesh(new THREE.SphereGeometry((o.radius || 3) * 1.035, 96, 48), new THREE.ShaderMaterial({
    uniforms: {}, transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
    vertexShader: 'varying vec3 vN; varying vec3 vV; void main(){ vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }',
    fragmentShader: 'varying vec3 vN; varying vec3 vV; void main(){ float i=pow(1.0-abs(dot(vN,vV)),2.5); gl_FragColor=vec4(vec3(0.35,0.6,1.0)*i*1.2, i); }',
  }));
  m.add(glow);
  return m;
}
export { THREE };
