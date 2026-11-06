// ch3: the tetrahedral Earth rig (Green's 1875 "shrinking Earth -> tetrahedron") with the Explorer.
// Everything is a pure function of absolute time t; anchors (marker times) are passed in A.
import { keyAt, stageBg, inwardArrows, questionMark, glowSprite, F, PAL, E, prog, clamp, lerp } from './ch3_lib.js';

const D2R = Math.PI / 180;

export async function makeTetraRig(api, A) {
  const { Actor, THREE } = await import('../../lib/actors.js');
  const { tetraEarth } = await import('../../lib/morph.js');
  const W = api.W, H = api.H;
  const st = await api.newStage('ch3tetra', { shadowExtent: 4.6, hemi: 0.95, key: 2.5, rim: 2.8, exposure: 1.05 });
  // fill light that follows the camera: the faces turned away from the key light rendered pitch black
  if (!st.head) { st.head = new THREE.DirectionalLight(0xffffff, 1.1); st.add(st.head); st.add(st.head.target); }
  const R = 2.2, TS = 1.55;
  const te = await tetraEarth(st, { radius: R, map: 'ep/ep01/img/ch3_day_4k.jpg' });
  const mesh = te.children[0]; mesh.receiveShadow = true;
  te.children[1].visible = false; // 1-px GL lines are invisible in software GL; replaced by tubes below
  const llv = (lat, lon) => new THREE.Vector3(Math.cos(lat * D2R) * Math.cos(lon * D2R), Math.sin(lat * D2R), -Math.cos(lat * D2R) * Math.sin(lon * D2R));
  const verts = [[-90, 0], [19.47, -75], [19.47, 45], [19.47, 165]].map(([a, b]) => llv(a, b));
  const faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]].map(([i, j, k]) => {
    const Av = verts[i], B = verts[j], Cv = verts[k];
    const n = new THREE.Vector3().subVectors(B, Av).cross(new THREE.Vector3().subVectors(Cv, Av)).normalize();
    if (n.dot(Av) < 0) n.negate();
    return { n, h: n.dot(Av), idx: [i, j, k] };
  });
  const tOf = (d) => { let t = Infinity; for (const f of faces) { const c = f.n.dot(d); if (c > 1e-6) t = Math.min(t, f.h / c); } return t; };
  const rad = (d, k) => R * ((1 - k) + k * TS * tOf(d));

  // glowing edge tubes + corner balls (depth-tested, so hidden parts stay hidden)
  const edgeMat = new THREE.MeshBasicMaterial({ color: 0xffd23f, transparent: true, opacity: 0, depthWrite: false });
  const tubes = [];
  const VS = R * TS * 1.004;
  [[0, 1], [0, 2], [0, 3], [1, 2], [2, 3], [3, 1]].forEach(([i, j]) => {
    const a = verts[i].clone().multiplyScalar(VS), b = verts[j].clone().multiplyScalar(VS);
    const len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, len, 10, 1, true), edgeMat);
    m.position.copy(a.clone().add(b).multiplyScalar(0.5));
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    te.add(m); tubes.push(m);
  });
  verts.forEach(v => { const s = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 8), edgeMat); s.position.copy(v.clone().multiplyScalar(VS)); te.add(s); tubes.push(s); });

  // the Explorer lives in the planet's frame
  const hero = await Actor.create(st, 'models/adventurer.glb', { scale: 0.75 });
  te.add(hero.root);
  const ROLL0 = A.tet + 0.42, ROLL1 = A.pyr4 - 0.04;
  // exactly one roll over the path, ending upright at ROLL1 (at speed 1.15 the looping 1.33 s clip wrapped at 383.60 and
  // the idle crossfade cut a second roll off upside down)
  const rollDur = hero.clips.Roll ? hero.clips.Roll.duration : 1.333;
  hero.play(A.cool - 0.2, 'Idle_Neutral', { fade: 0.4 });
  hero.play(ROLL0, 'Roll', { fade: 0.12, speed: rollDur / (ROLL1 - ROLL0), once: true });
  hero.play(ROLL1, 'Idle_Neutral', { fade: 0.25 });
  hero.play(A.stall + 0.3, 'HitRecieve_2', { fade: 0.08, once: true });
  hero.play(A.stall + 1.25, 'Idle_Neutral', { fade: 0.35 });

  const UP = new THREE.Vector3(0, 1, 0);
  const top = new THREE.Vector3(0, 1, 0);
  const vPerch = verts[1].clone().multiplyScalar(R * TS * 0.86).add(new THREE.Vector3(0, R * TS / 3, 0).multiplyScalar(0.14));
  const dPerch = vPerch.clone().normalize();
  // tilt axis: toward the Americas corner (horizontal direction of vertex 1)
  const cH = new THREE.Vector3(verts[1].x, 0, verts[1].z).normalize();
  const tiltAxis = new THREE.Vector3().crossVectors(UP, cH).normalize();
  const qAlign = new THREE.Quaternion().setFromUnitVectors(dPerch, UP);
  const qI = new THREE.Quaternion();

  // ---- time functions ----
  const kOf = (t) => {
    if (t < A.tet) return 0;
    if (t < A.stall + 0.08) return E.inOut(clamp((t - A.tet) / 3.0));
    return 1 - E.outBack(clamp((t - A.stall - 0.08) / 1.0));
  };
  const edgeOf = (t) => {
    if (t < A.tet) return 0;
    const on = clamp((kOf(t) - 0.55) / 0.35);
    const off = t < A.stall + 0.08 ? 1 : clamp((kOf(t) - 0.7) / 0.3); // the cage leaves with the flat faces
    return 0.92 * on * off;
  };
  const flareOf = (t) => Math.max(0, 1 - Math.abs(t - (A.pyr4 + 0.12)) / 0.55) * (t > A.pyr4 - 0.4 ? 1 : 0);
  const scaleOf = (t) => {
    const shrink = lerp(1, 0.94, prog(t, A.cool + 0.6, A.tet + 0.2));
    return t < A.stall + 0.08 ? shrink : lerp(0.94, 1, E.outBack(clamp((t - A.stall - 0.08) / 1.0)));
  };
  const tiltOf = (t) => 25 * prog(t, A.tet, A.tet + 1.1) * (1 - prog(t, A.pyr4 + 1.4, A.pred - 0.2));
  const alignOf = (t) => prog(t, A.stall + 0.25, A.stall + 1.3, E.inOut);
  // hero placement in planet coords: direction, radius, surface normal, facing mode
  const heroLocal = (t, k) => {
    if (t < ROLL0) return { d: top.clone(), r: rad(top, k), n: top.clone(), face: 'cam' };
    if (t < ROLL1) {
      const s = E.inOut(clamp((t - ROLL0) / (ROLL1 - ROLL0)));
      const d = top.clone().lerp(dPerch, s).normalize();
      const n = d.clone().lerp(UP, clamp(k)).normalize();
      return { d, r: rad(d, k), n, face: 'path' };
    }
    const d = dPerch.clone();
    let r = rad(d, Math.max(k, -0.2));
    let n = d.clone().lerp(UP, clamp(k)).normalize();
    if (t >= A.stall) {
      // corner vanishes: hang for a beat (cartoon), then drop onto the reforming ball
      const rHang = rad(d, 1);
      const fall = E.in(clamp((t - A.stall - 0.3) / 0.32));
      r = lerp(rHang, rad(d, k), fall);
      n = UP.clone().lerp(d, fall).normalize();
    }
    return { d, r, n, face: 'cam' };
  };
  const yawOf = (t) => {
    let y = 28;
    if (t > A.stall + 1.3) y += 55 * Math.sin((t - A.stall - 1.3) * 2.6) * prog(t, A.stall + 1.3, A.stall + 1.7);
    return y;
  };

  // ---- camera rig (spherical around a target; 'hero' targets the Explorer) ----
  const CAM = [
    { t: A.pyr2 + 1.2, az: 26, el: 5, dist: 6.0, ty: 0, hero: 1, fov: 30 },
    { t: A.cool - 0.2, az: 36, el: 6, dist: 5.8, hero: 1 },
    { t: A.cool + 1.2, az: 42, el: 13, dist: 13.2, hero: 0, tx: 0, ty: 0.9, tz: 0 },
    { t: A.tet, az: 46, el: 12, dist: 12.8, hero: 0, tx: 0, ty: 0.8, tz: 0 },
    { t: A.tet + 1.6, az: 34, el: 9, dist: 8.6, hero: 0.7 },
    { t: A.pyr4 + 0.1, az: 30, el: 6, dist: 6.4, hero: 1 },
    { t: A.pyr4 + 1.4, az: 26, el: 5, dist: 6.0, hero: 1 },
    { t: A.pred - 0.3, az: 40, el: 16, dist: 13.6, hero: 0, tx: 0, ty: 0, tz: 0 },
    { t: A.pred + 1.2, az: 44, el: 17, dist: 13.4, hero: 0 },
    { t: A.L1 - 0.1, az: 44, el: 17, dist: 13.4, hero: 0 },
    { t: A.c1 - 0.15, az: 16, el: 30, dist: 12.6, hero: 0, ty: 0.5 },
    { t: A.L2 - 0.1, az: 12, el: 30, dist: 12.6, hero: 0, ty: 0.5 },
    { t: A.c2 - 0.15, az: 96, el: -18, dist: 12.4, hero: 0, ty: -0.6 },
    { t: A.L3 - 0.1, az: 90, el: -18, dist: 12.4, hero: 0, ty: -0.6 },
    { t: A.c3 - 0.15, az: 15, el: 86, dist: 12.0, hero: 0, ty: 0 },
    { t: A.L4 - 0.1, az: 25, el: 86, dist: 12.0, hero: 0, ty: 0 },
    { t: A.c4 - 0.15, az: 15, el: -86, dist: 11.6, hero: 0, ty: 0 },
    { t: A.L5 - 0.1, az: 5, el: -86, dist: 11.6, hero: 0, ty: 0 },
    { t: A.c5 - 0.15, az: -78, el: 9, dist: 12.4, hero: 0, ty: 0.2 },
    { t: A.c5 + 0.6, az: -80, el: 9, dist: 12.4, hero: 0, ty: 0.2 },
    { t: A.c5 + 2.3, az: 30, el: 17, dist: 14.0, hero: 0, ty: 0 },
    { t: A.main, az: 36, el: 18, dist: 13.6, hero: 0, ty: 0 },
    // s053 / s054 (frozen mid-turn, 1 deg/s drift)
    { t: A.s053, az: 18, el: 11, dist: 13.2, hero: 0, ty: -0.4 },
    { t: A.how - 0.1, az: 26, el: 11, dist: 13.2, hero: 0, ty: -0.4, ease: E.lin },
    { t: A.measure, az: 32, el: 11, dist: 12.8, hero: 0, ty: -0.4, ease: E.lin },
    // s055 (stall -> back to a ball; push in on the Explorer)
    { t: A.s055, az: 26, el: 10, dist: 13.2, hero: 0, ty: -0.4 },
    { t: A.stall + 0.2, az: 28, el: 10, dist: 13.0, hero: 0, ty: -0.4, ease: E.lin },
    { t: A.stall + 1.4, az: 30, el: 8, dist: 6.6, hero: 1 },
    { t: A.real - 1.2, az: 38, el: 6, dist: 6.2, hero: 1 },
  ];
  for (const c of CAM) { for (const [k, v] of [['tx', 0], ['ty', 0], ['tz', 0], ['hero', 0], ['fov', 30]]) if (c[k] === undefined) c[k] = v; }
  const camState = (t) => keyAt(CAM, t);

  let lastK = null;
  const tmp = new THREE.Vector3();
  const pose = (t) => {
    const k = kOf(t);
    if (lastK === null || Math.abs(k - lastK) > 1e-5) { te.userData.set(k, 0); lastK = k; }
    const e = edgeOf(t), fl = flareOf(t);
    edgeMat.opacity = Math.min(1, e + fl * 0.4); tubes.forEach(m => { m.visible = edgeMat.opacity > 0.01; const s = 1 + 1.6 * fl; if (m.geometry.type === 'CylinderGeometry') m.scale.set(s, 1, s); else m.scale.setScalar(1 + 1.2 * fl); });
    // planet orientation: tilt toward camera during the roll, later align the Explorer's spot to the top
    const qt = new THREE.Quaternion().setFromAxisAngle(tiltAxis, tiltOf(t) * D2R);
    const qa = qI.clone().slerp(qAlign, alignOf(t));
    te.quaternion.copy(qa.premultiply(qt));
    te.scale.setScalar(scaleOf(t));
    const h = heroLocal(t, k);
    hero.root.position.copy(h.d.clone().multiplyScalar(h.r));
    te.updateMatrixWorld(true);
    const heroW = hero.root.getWorldPosition(new THREE.Vector3());
    const upW = h.n.clone().applyQuaternion(te.quaternion).normalize();
    // camera
    const c = camState(t);
    const drift = (t >= A.s053 && t < A.measure) ? 0 : 0;
    const tg = new THREE.Vector3(c.tx || 0, c.ty || 0, c.tz || 0).lerp(heroW.clone().addScaledVector(upW, 0.62), clamp(c.hero || 0));
    const az = (c.az + drift) * D2R, el = c.el * D2R;
    const cp = tg.clone().add(new THREE.Vector3(Math.cos(el) * Math.sin(az), Math.sin(el), Math.cos(el) * Math.cos(az)).multiplyScalar(c.dist));
    st.camera.up.set(0, 1, 0);
    st.lookFrom(cp.toArray(), tg.toArray(), c.fov || 30);
    st.head.position.copy(cp); st.head.target.position.copy(tg); st.head.target.updateMatrixWorld();
    // hero orientation in planet coords
    const camL = te.worldToLocal(cp.clone());
    const posL = hero.root.position.clone();
    const up = h.n.clone();
    const faceQ = (fwd, yaw) => {
      fwd.addScaledVector(up, -fwd.dot(up));
      if (fwd.lengthSq() < 1e-8) fwd.set(0, 0, 1); fwd.normalize();
      if (yaw) fwd.applyAxisAngle(up, yaw * D2R);
      const x = new THREE.Vector3().crossVectors(up, fwd).normalize();
      return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, up, fwd));
    };
    // 'path' faces the direction of travel (top -> perch); the old dPerch - posL swung back toward the axis near the end
    const travelQ = () => faceQ(dPerch.clone().sub(top), 0);
    if (h.face === 'path') hero.root.quaternion.copy(travelQ());
    else {
      const qc = faceQ(camL.clone().sub(posL), yawOf(t));
      // after the roll he turns from the travel direction to the camera over 0.3 s (it used to snap in one frame)
      const turn = prog(t, ROLL1, ROLL1 + 0.3);
      hero.root.quaternion.copy(t >= ROLL1 && turn < 1 ? travelQ().slerp(qc, turn) : qc);
    }
    return { k, cp, tg, heroW };
  };
  // projected helpers
  const proj = (v) => st.project(v);
  const centerPx = () => proj(te.getWorldPosition(tmp.set(0, 0, 0)));
  const radiusPx = (cp, rWorld) => { const d = cp.length(); return rWorld / d * (H / 2) / Math.tan(st.camera.fov * D2R / 2); };

  return {
    st, te, hero, verts, faces, R, TS, THREE,
    // draw the stage (background + 3D) at absolute time t. o: {offX (px, shifts subject right), bg}
    draw(ctx, t, o = {}) {
      stageBg(ctx, W, H, { c0: o.c0 || '#142a50', c1: '#03050a', drift: t * 4, y: 0.55 });
      const P = pose(t);
      if (o.offX) st.camera.setViewOffset(W, H, -o.offX, 0, W, H); else st.camera.clearViewOffset();
      ctx.drawImage(st.render(t), 0, 0);
      // corner flare glows (visible corners only)
      const fl = flareOf(t);
      if (fl > 0.01) {
        const spr = glowSprite('rgba(255,210,63,0.9)');
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        verts.forEach(v => {
          const w = te.localToWorld(v.clone().multiplyScalar(R * TS));
          const toCam = P.cp.clone().sub(w).normalize();
          const nW = v.clone().applyQuaternion(te.quaternion);
          if (nW.dot(toCam) < -0.15) return;
          const q = proj(w); const s = 150 * fl;
          ctx.globalAlpha = fl; ctx.drawImage(spr, q.x - s / 2, q.y - s / 2, s, s);
        });
        ctx.restore();
      }
      P.center = centerPx(); P.rpx = radiusPx(P.cp.clone().sub(te.getWorldPosition(new THREE.Vector3())), (P.k > 0.5 ? 2.5 : 2.2) * te.scale.x);
      return P;
    },
    // world position of a corner / face centre (for 2D overlays)
    cornerW(i) { return te.localToWorld(verts[i].clone().multiplyScalar(R * TS)); },
    faceCenterW(fi) { const f = faces[fi]; return te.localToWorld(f.n.clone().multiplyScalar(f.h * R * TS)); },
    faceNormalW(fi) { return faces[fi].n.clone().applyQuaternion(te.quaternion); },
    proj,
  };
}
