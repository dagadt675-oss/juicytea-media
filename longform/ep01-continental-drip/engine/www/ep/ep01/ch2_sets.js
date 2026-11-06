// ch2 3D sets on ONE shared stage ('ch2_main') to keep the WebGL context count low:
// floe diorama (gag 3), tiny planet (gags 4a/4b), cut-away Earth (drills), tetra-in-globe (1875), plus actors
// that are composited onto 2D scenes (profile panel, Pacific pour, Kenney mini on the flat map).
import * as F from '../../lib/fx.js';
import { Actor, tinyPlanet, THREE } from '../../lib/actors.js';
import { cutawayEarth, llDir, drillDir } from '../../lib/cutaway.js';
import { tetraEarth } from '../../lib/morph.js';
const { prog, E, clamp, lerp } = F;
const UP = new THREE.Vector3(0, 1, 0);

export async function makeSets(api) {
  const st = await api.newStage('ch2_main', { shadowExtent: 5, hemi: 1.2, key: 2.6, rim: 1.8, exposure: 1.05 });
  const hemi = st.scene.children.find(o => o.isHemisphereLight);
  const rim = st.scene.children.find(o => o.isDirectionalLight && o !== st.key);
  const rnd = F.rng(4242);

  // ---------- floe diorama ----------
  const floeSet = new THREE.Group(); st.add(floeSet);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(90, 90), new THREE.MeshStandardMaterial({ color: 0x0b2844, roughness: 0.18, metalness: 0.45 }));
  water.rotation.x = -Math.PI / 2; water.receiveShadow = true; floeSet.add(water);
  const floeGeo = (rad, n) => {
    const sh = new THREE.Shape();
    for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, r = rad * (0.78 + 0.32 * rnd()); const x = Math.cos(a) * r, y = Math.sin(a) * r * 0.8; i ? sh.lineTo(x, y) : sh.moveTo(x, y); }
    sh.closePath();
    const g = new THREE.ExtrudeGeometry(sh, { depth: 0.3, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.07, bevelSegments: 2 });
    g.rotateX(-Math.PI / 2); g.translate(0, -0.24, 0); return g;
  };
  const iceMat = new THREE.MeshStandardMaterial({ color: 0xeef6ff, roughness: 0.75, metalness: 0 });
  const floe1 = new THREE.Group(); floeSet.add(floe1);
  const f1 = new THREE.Mesh(floeGeo(1.45, 10), iceMat); f1.castShadow = true; f1.receiveShadow = true; floe1.add(f1);
  // striped pole
  const sc = document.createElement('canvas'); sc.width = 64; sc.height = 512; const sg = sc.getContext('2d');
  sg.fillStyle = '#ffffff'; sg.fillRect(0, 0, 64, 512); sg.fillStyle = '#d42a2a';
  for (let y = -64; y < 512; y += 64) { sg.beginPath(); sg.moveTo(0, y); sg.lineTo(64, y + 24); sg.lineTo(64, y + 56); sg.lineTo(0, y + 32); sg.closePath(); sg.fill(); }
  const stex = new THREE.CanvasTexture(sc); stex.colorSpace = THREE.SRGBColorSpace;
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.055, 1.7, 20), new THREE.MeshStandardMaterial({ map: stex, roughness: 0.4 }));
  pole.position.set(0.78, 0.9, -0.35); pole.castShadow = true; floe1.add(pole);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.11, 20, 12), new THREE.MeshStandardMaterial({ color: 0xffd23f, roughness: 0.25, metalness: 0.6, emissive: 0x332200 }));
  knob.position.set(0.78, 1.78, -0.35); floe1.add(knob);
  // second floe with a tiny workshop
  const floe2 = new THREE.Group(); floeSet.add(floe2);
  const f2 = new THREE.Mesh(floeGeo(1.1, 9), iceMat); f2.castShadow = true; f2.receiveShadow = true; floe2.add(f2);
  const cabin = new THREE.Group(); floe2.add(cabin);
  const wall = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.62, 0.72), new THREE.MeshStandardMaterial({ color: 0xb3352b, roughness: 0.7 })); wall.position.y = 0.37; wall.castShadow = true; cabin.add(wall);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(0.78, 0.46, 4), new THREE.MeshStandardMaterial({ color: 0xf4f8fc, roughness: 0.8 })); roof.rotation.y = Math.PI / 4; roof.position.y = 0.91; roof.castShadow = true; cabin.add(roof);
  const chim = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.36, 0.14), new THREE.MeshStandardMaterial({ color: 0x5a3a28 })); chim.position.set(0.24, 1.02, -0.08); cabin.add(chim);
  const win = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.2), new THREE.MeshBasicMaterial({ color: 0xffd27a })); win.position.set(-0.22, 0.42, 0.362); cabin.add(win);
  const door = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.4), new THREE.MeshStandardMaterial({ color: 0x3a2015 })); door.position.set(0.2, 0.26, 0.362); cabin.add(door);
  const smokeMat = []; const smoke = [];
  for (let i = 0; i < 8; i++) { const m = new THREE.MeshBasicMaterial({ color: 0xdfe6ee, transparent: true, opacity: 0.5, depthWrite: false }); const s = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), m); cabin.add(s); smoke.push(s); smokeMat.push(m); }
  cabin.rotation.y = 0.5;
  // ripples around floes
  const ripMat = new THREE.MeshBasicMaterial({ color: 0xbfe6ff, transparent: true, opacity: 0.18, depthWrite: false });
  const rip1 = new THREE.Mesh(new THREE.RingGeometry(1.0, 1.06, 64), ripMat); rip1.rotation.x = -Math.PI / 2; rip1.position.y = 0.01; floeSet.add(rip1);
  const rip2 = new THREE.Mesh(new THREE.RingGeometry(1.0, 1.06, 64), ripMat.clone()); rip2.rotation.x = -Math.PI / 2; rip2.position.y = 0.01; floeSet.add(rip2);
  const heroF = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });
  floe1.add(heroF.root); heroF.root.position.set(-0.1, 0.06, 0.2);

  // ---------- tiny planet ----------
  const planet = await tinyPlanet(st, { radius: 3 }); planet.position.set(0, -3, 0);
  const heroP = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });

  // ---------- cut-away Earth ----------
  const ce = await cutawayEarth(st, { radius: 3, map: 'ep/ep01/img/ch2_day4k.jpg' });
  const heroD = await Actor.create(st, 'models/adventurer.glb', { scale: 0.2 });

  // ---------- tetra-in-globe ----------
  const te = await tetraEarth(st, { radius: 2.2, map: 'ep/ep01/img/ch2_day4k.jpg' });
  te.userData.set(0, 0);
  const teMesh = te.children[0];

  // ---------- composite actors ----------
  const heroC = await Actor.create(st, 'models/adventurer.glb', { scale: 0.55 });
  const mini = await Actor.create(st, 'models/mini_male_a.glb', { scale: 1 });
  const bb = new THREE.Box3().setFromObject(mini.root); const mh = Math.max(0.01, bb.max.y - bb.min.y); mini.root.scale.setScalar(1 / mh);

  const all = { floeSet, planet, ce, te, heroF: heroF.root, heroP: heroP.root, heroD: heroD.root, heroC: heroC.root, mini: mini.root };
  function only(...keys) { for (const k in all) all[k].visible = keys.includes(k); }
  function lights(o = {}) {
    st.key.intensity = o.key ?? 2.6; hemi.intensity = o.hemi ?? 1.2; rim.intensity = o.rim ?? 1.8;
    st.key.position.set(...(o.keyPos || [5, 9, 6])); rim.position.set(...(o.rimPos || [-6, 4, -7]));
    st.renderer.toneMappingExposure = o.exposure ?? 1.05;
    st.renderer.shadowMap.enabled = o.shadows ?? true;
  }

  const S = {
    st, THREE, heroF, heroP, heroD, heroC, mini, planet, ce, te, llDir, UP,
    // ---- gag 3: floe diorama ----
    floe(ctx, t, lt, o = {}) {
      only('floeSet', 'heroF'); lights({ key: 2.4, hemi: 0.9, rim: 2.6, keyPos: [4, 6, 7], rimPos: [-5, 3.5, -6], exposure: 1.1 });
      floe1.position.y = 0.035 * Math.sin(t * 1.7); floe1.rotation.x = 0.03 * Math.sin(t * 1.3); floe1.rotation.z = 0.035 * Math.sin(t * 1.1 + 1);
      const drift = o.cabinX ?? -2.7;
      floe2.position.set(drift, 0.04 * Math.sin(t * 1.5 + 2), -1.9); floe2.rotation.x = 0.04 * Math.sin(t * 1.2 + 0.5); floe2.rotation.z = 0.05 * Math.sin(t * 1.4 + 2);
      smoke.forEach((s, i) => { const ph = (t * 0.32 + i / smoke.length) % 1; s.position.set(0.24 + ph * 0.55, 1.22 + ph * 1.5, -0.08 - ph * 0.2); s.scale.setScalar(0.07 + ph * 0.24); smokeMat[i].opacity = 0.55 * (1 - ph) * clamp(ph * 6); });
      const rp = (t * 0.45) % 1; rip1.scale.setScalar(1.3 + rp * 1.4); rip1.material.opacity = 0.22 * (1 - rp); rip1.position.set(floe1.position.x, 0.01, floe1.position.z);
      const rp2 = (t * 0.45 + 0.5) % 1; rip2.scale.setScalar(1.0 + rp2 * 1.2); rip2.material.opacity = 0.2 * (1 - rp2); rip2.position.set(floe2.position.x, 0.01, floe2.position.z);
      heroF.root.rotation.y = o.heroRy ?? -0.5;
      const cam = o.cam || [1.7, 0.62, 4.7], tgt = o.target || [-0.55, 0.72, -0.4];
      st.lookFrom(cam, tgt, o.fov || 31);
      ctx.drawImage(st.render(t), 0, 0);
    },
    // ---- tiny planet: put (lat, lon) on top; spin (rad) about the vertical ----
    planet(ctx, t, o = {}) {
      only('planet', 'heroP'); lights({ key: 2.7, hemi: 1.1, rim: 2.4, keyPos: [4, 7, 6], rimPos: [-6, 3, -6] });
      const q = new THREE.Quaternion().setFromUnitVectors(llDir(o.lat, o.lon), UP);
      const qs = new THREE.Quaternion().setFromAxisAngle(UP, o.spin || 0);
      planet.quaternion.copy(qs.multiply(q));
      if (o.hero) { heroP.path = null; heroP.root.position.set(...o.hero.pos); heroP.root.rotation.set(o.hero.rx || 0, o.hero.ry || 0, o.hero.rz || 0); }
      const a = o.camAng ?? 0.35, dist = o.dist ?? 5.0, h = o.camH ?? 0.9;
      st.lookFrom([Math.sin(a) * dist, h, Math.cos(a) * dist], o.target || [0, 0.55, 0], o.fov || 30);
      ctx.drawImage(st.render(t), 0, 0);
    },
    // ---- cut-away Earth with (lat, lon) on top and a drill grown to p ----
    cutaway(ctx, t, o = {}) {
      only('ce', ...(o.rider ? ['heroD'] : [])); lights({ key: 2.4, hemi: 1.3, rim: 1.6, keyPos: [6, 8, 5] });
      const q = new THREE.Quaternion().setFromUnitVectors(llDir(o.lat, o.lon), UP);
      const qs = new THREE.Quaternion().setFromAxisAngle(UP, o.spin || 0);
      ce.userData.shell.quaternion.copy(qs.multiply(q));
      const d = drillDir(ce, UP, Math.max(0.001, o.p || 0), { width: 0.045 });
      ce.userData.drill.visible = (o.p || 0) > 0.002;
      if (o.rider) {
        heroD.path = null; const e = d.end; heroD.root.position.set(e.x + 0.16, e.y + 0.05, e.z + 0.16); heroD.root.rotation.set(Math.PI, o.riderRy ?? 0.8, 0);
      }
      st.lookFrom(o.cam || [6, 3.5, 6], o.target || [0, 0.3, 0], o.fov || 32);
      ctx.drawImage(st.render(t), 0, 0);
      return { end: d.end, top: new THREE.Vector3(0, 3, 0), bottom: new THREE.Vector3(0, -3, 0) };
    },
    // ---- tetra-in-globe ----
    tetra(ctx, t, o = {}) {
      only('te'); lights({ key: 2.5, hemi: 1.0, rim: 2.2, keyPos: [5, 6, 7], rimPos: [-6, 3, -5], exposure: 1.05, shadows: false });
      te.rotation.set(o.rx || 0.25, o.ry || 0, 0);
      const xr = o.xray || 0; const m = teMesh.material;
      // toggling 'transparent' changes the compiled shader (OPAQUE define): flag a recompile, or the look depends on where the chunk started
      const wantT = xr > 0.001;
      if (m.transparent !== wantT) { m.transparent = wantT; m.needsUpdate = true; }
      if (wantT) { m.opacity = 1 - 0.55 * xr; m.depthWrite = xr < 0.5; } else { m.opacity = 1; m.depthWrite = true; }
      te.userData.set(o.k || 0, o.edge ?? 0);
      st.lookFrom(o.cam || [0, 0.6, 8.4], o.target || [0, 0, 0], o.fov || 32);
      ctx.drawImage(st.render(t), 0, 0);
      te.updateMatrixWorld(true);
      // tetra vertices in world space (same construction as lib/morph.js, tetraScale 1.55)
      const R = 2.2 * 1.55;
      const V = [[-90, 0], [19.47, -75], [19.47, 45], [19.47, 165]].map(([a, b]) => llDir(a, b).multiplyScalar(R).applyMatrix4(te.matrixWorld));
      return { V, R: 2.2, cam: st.camera.position.clone() };
    },
    // ---- an actor rendered alone and composited with its feet at (x, y), h px tall ----
    comp(ctx, t, which, x, y, h, o = {}) {
      const act = which === 'mini' ? mini : heroC; only(which === 'mini' ? 'mini' : 'heroC');
      lights({ key: 2.6, hemi: 1.2, rim: 3.0, keyPos: [4, 6, 6], rimPos: [-5, 4, -6], shadows: false });
      act.path = null; act.root.position.set(0, 0, 0); act.root.rotation.set(o.rx || 0, o.ry ?? 0.35, o.rz || 0);
      st.lookFrom([0, o.camY ?? 0.42, 4.2], [0, 0.5, 0], 30);
      const cv = st.render(t);
      const foot = st.project(new THREE.Vector3(0, 0, 0)), head = st.project(new THREE.Vector3(0, 1, 0));
      const ph = foot.y - head.y, k = h / ph;
      const sx = foot.x - ph * 1.0, sy = head.y - ph * 0.55, sw = ph * 2.0, sh = ph * 1.75;
      ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
      if (o.clipY != null) { ctx.beginPath(); ctx.rect(0, 0, api.W, o.clipY); ctx.clip(); }
      ctx.drawImage(cv, sx, sy, sw, sh, x - ph * 1.0 * k, y - ph * 1.55 * k, sw * k, sh * k);
      ctx.restore();
      return { headY: y - h };
    },
    project(v) { return st.project(v); },
  };
  return S;
}
