// ch3 small 3D dioramas: Green's bent card in water (s046), the 1918 kids' classroom (s052), cut-away Earth (s054).
import { stageBg, ripples, glowSprite, cv, F, PAL, E, prog, clamp, lerp } from './ch3_lib.js';
const D2R = Math.PI / 180;

// ---------- s046: bent card dipped in water ----------
export async function makeCardRig(api, A) {
  const { THREE } = await import('../../lib/actors.js');
  const W = api.W, H = api.H;
  const st = await api.newStage('ch3card', { shadowExtent: 4, hemi: 1.05, key: 2.3, rim: 2.0, exposure: 1.0 });
  st.renderer.localClippingEnabled = true;
  const water = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: 0x1b93b8, transparent: true, opacity: 0.62, roughness: 0.16, metalness: 0.08, depthWrite: false }));
  water.rotation.x = -Math.PI / 2; water.receiveShadow = true; water.renderOrder = 2; st.add(water);
  const bed = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: 0x062a3c, roughness: 1 }));
  bed.rotation.x = -Math.PI / 2; bed.position.y = -0.9; bed.receiveShadow = true; st.add(bed);
  const pDry = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), pWet = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
  const white = new THREE.Color(0xf6f2e8), hero = new THREE.Color(0xff5a36);
  const dryMat = new THREE.MeshStandardMaterial({ color: white.clone(), roughness: 0.55, side: THREE.DoubleSide, clippingPlanes: [pDry] });
  const wetMat = new THREE.MeshStandardMaterial({ color: 0xcfe4ea, roughness: 0.5, side: THREE.DoubleSide, clippingPlanes: [pWet] });
  const card = new THREE.Group();
  const HL = 1.3, WD = 1.0, ANG = 7.5 * D2R, PITCH = -5 * D2R;
  const halves = [];
  for (const sgn of [1, -1]) {
    const hg = new THREE.Group(); hg.rotation.x = sgn * ANG; card.add(hg); halves.push({ sgn, hg });
    for (const mat of [dryMat, wetMat]) {
      const g = new THREE.PlaneGeometry(2 * HL, WD); g.rotateX(-Math.PI / 2); g.translate(0, 0, sgn * WD / 2);
      const m = new THREE.Mesh(g, mat); m.castShadow = true; m.receiveShadow = true; hg.add(m);
    }
  }
  // fold line
  const fold = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 2 * HL, 6), new THREE.MeshStandardMaterial({ color: 0x8a8a84, clippingPlanes: [pDry] }));
  fold.rotation.z = Math.PI / 2; card.add(fold);
  card.rotation.z = PITCH; st.add(card);
  // ridge height (y of the fold's centre) over time: hangs dry, lowers, nose touches, settles with the tip at x = +0.45
  const yFinal = 0.55 * Math.sin(-PITCH);
  const y0Of = (t) => lerp(0.95, yFinal, E.inOut(clamp((t - A.card - 0.05) / (A.water + 0.02 - A.card - 0.05)))) + 0.012 * Math.sin(t * 2.4);
  // nose-touch time (lowest corner reaches y = 0)
  const lowCorner = (y0) => y0 - HL * Math.sin(-PITCH) - WD * Math.sin(ANG) * Math.cos(PITCH);
  let tTouch = A.water; for (let t = A.card; t < A.water; t += 1 / 60) { if (lowCorner(y0Of(t)) <= 0) { tTouch = t; break; } }
  const vtmp = new THREE.Vector3();
  const waterline = () => {
    // per half: world y is affine in (x, u) -> solve y = 0
    const lines = [];
    card.updateMatrixWorld(true);
    for (const { sgn, hg } of halves) {
      const P = (x, u) => vtmp.set(x, 0, sgn * u * WD).applyMatrix4(hg.matrixWorld).clone();
      const a = P(-HL, 0), b = P(HL, 0), c = P(-HL, 1);
      const ya = a.y, bx = (b.y - a.y) / (2 * HL), cu = c.y - a.y;
      const pts = [];
      for (let i = 0; i <= 40; i++) { const x = -HL + 2 * HL * i / 40; const u = -(ya + bx * (x + HL)) / cu; if (u >= 0 && u <= 1) pts.push(P(x, u)); }
      lines.push(pts);
    }
    return lines;
  };
  return {
    st,
    draw(ctx, t) {
      stageBg(ctx, W, H, { c0: '#0f3550', c1: '#02060b', y: 0.35, stars: false });
      card.position.y = y0Of(t);
      card.rotation.y = 0.04 * Math.sin(t * 0.7);
      const tint = prog(t, A.water - 0.05, A.water + 0.5);
      dryMat.color.copy(white).lerp(hero, 0.88 * tint);
      const orb = (t - A.card) * 2.2;
      const az = (58 + orb) * D2R, el = 46 * D2R, d = 5.2;
      st.lookFrom([Math.sin(az) * Math.cos(el) * d + 0.15, Math.sin(el) * d, Math.cos(az) * Math.cos(el) * d], [0.25, 0.05, 0], 34);
      ctx.drawImage(st.render(t), 0, 0);
      // white waterline + ripples from the dipped nose
      if (t > tTouch) {
        const lines = waterline();
        for (const pts of lines) if (pts.length > 1) F.glowPath(ctx, pts.map(p => { const q = st.project(p); return [q.x, q.y]; }), { color: '#ffffff', width: 4, p: 1, alpha: prog(t, tTouch, tTouch + 0.25) });
        const nose = st.project(vtmp.set(HL, 0, 0).applyMatrix4(card.matrixWorld).setY(0));
        ripples(ctx, nose.x, nose.y, t - tTouch, { r: 260, flat: 0.55, n: 3 });
      }
      return { tTouch };
    },
  };
}

// ---------- s052: 1918 children's page, Kenney minis at a chalkboard ----------
export async function makeKidsRig(api, A) {
  const { Actor, THREE } = await import('../../lib/actors.js');
  const W = api.W, H = api.H;
  const st = await api.newStage('ch3kids', { shadowExtent: 4, hemi: 1.35, key: 2.1, rim: 1.7, exposure: 1.0, keyColor: 0xffe6c0 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.ShadowMaterial({ opacity: 0.3 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; st.add(floor);
  const tints = [[1, 0.86, 0.8], [1, 1, 1], [0.82, 0.92, 1.05]];
  const kids = [];
  for (let i = 0; i < 3; i++) {
    const k = await Actor.create(st, 'models/mini_male_a.glb', { scale: 1.6, idle: 'sit' });
    k.root.traverse(m => { if (m.isMesh && m.material) m.material.color.setRGB(...tints[i]); });
    kids.push(k);
  }
  const X = [-1.45, 0, 1.45];
  kids[0].play(A.pyramid + 0.1, 'emote-yes', { fade: 0.2 }); kids[0].play(A.pyramid + 1.4, 'sit', { fade: 0.3 });
  kids[2].play(A.pyramid + 0.25, 'emote-yes', { fade: 0.2 }); kids[2].play(A.pyramid + 1.5, 'sit', { fade: 0.3 });
  kids[1].play(A.tight - 0.25, 'idle', { fade: 0.15 });
  kids[1].play(A.tight + 0.05, 'emote-no', { fade: 0.15 });
  return {
    st, kids,
    drawKids(ctx, t) {
      kids.forEach((k, i) => {
        const p = E.outBack(clamp((t - A.mag + 0.06 - i * 0.09) / 0.45));
        k.root.scale.setScalar(1.6 * Math.max(0.001, p));
        let ry = Math.PI + (i - 1) * -0.18;
        if (i === 1) ry = lerp(Math.PI, 0.12, E.inOut(clamp((t - A.tight + 0.3) / 0.4)));
        k.root.rotation.y = ry;
        k.root.position.set(X[i], 0, i === 1 ? 0.35 : 0);
      });
      const sway = Math.sin(t * 0.5) * 0.15;
      st.lookFrom([sway, 1.75, 5.2], [0, 0.55, -0.6], 30);
      ctx.drawImage(st.render(t), 0, 0);
    },
  };
}

// ---------- s054: cut-away Earth with radioactive "heater" specks ----------
export async function makeCutRig(api, A) {
  const { THREE } = await import('../../lib/actors.js');
  const { cutawayEarth } = await import('../../lib/cutaway.js');
  const W = api.W, H = api.H;
  const st = await api.newStage('ch3cut', { shadowExtent: 4, hemi: 1.0, key: 2.4, rim: 1.8, exposure: 1.05, shadows: false });
  const ce = await cutawayEarth(st, { radius: 3, map: 'ep/ep01/img/ch3_day_4k.jpg' });
  // specks on the two cut faces (z=0, x>=0) and (x=0, z>=0), mostly in crust+mantle
  const r = F.rng(31337), specks = [];
  for (let i = 0; i < 150; i++) {
    const rr = 3 * (0.57 + 0.41 * Math.sqrt(r())), th = (r() - 0.5) * Math.PI * 0.98, face = r() < 0.5;
    const v = face ? new THREE.Vector3(rr * Math.cos(th), rr * Math.sin(th), 0.01) : new THREE.Vector3(0.01, rr * Math.sin(th), rr * Math.cos(th));
    specks.push({ v, ph: r() * 6.28, w: 2 + r() * 5, s: 0.6 + r() * 0.8, d: r() });
  }
  const spr = glowSprite('rgba(255,150,40,0.95)');
  return {
    st,
    draw(ctx, t) {
      stageBg(ctx, W, H, { c0: '#1b2440', c1: '#04060c', y: 0.5, drift: t * 3 });
      const az = (38 + (t - A.cut0) * 2.0) * D2R, d = 8.6;
      st.lookFrom([Math.sin(az) * d, 3.6, Math.cos(az) * d], [0, 0.15, 0], 32);
      ctx.drawImage(st.render(t), 0, 0);
      const on = prog(t, A.rad - 0.15, A.rad + 1.3, E.out);
      if (on > 0) {
        const c = st.project(new THREE.Vector3(0, 0, 0));
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const pulse = 0.75 + 0.25 * Math.sin(t * 2.2);
        const g = ctx.createRadialGradient(c.x, c.y, 10, c.x, c.y, 520);
        g.addColorStop(0, `rgba(255,120,30,${0.32 * on * pulse})`); g.addColorStop(1, 'rgba(255,80,0,0)');
        ctx.fillStyle = g; ctx.fillRect(c.x - 520, c.y - 520, 1040, 1040);
        for (const s of specks) {
          const a = clamp((on * 1.25 - s.d * 0.4) * 2) * (0.55 + 0.45 * Math.sin(t * s.w + s.ph));
          if (a <= 0.02) continue;
          const q = st.project(s.v); const sz = 34 * s.s;
          ctx.globalAlpha = a; ctx.drawImage(spr, q.x - sz / 2, q.y - sz / 2, sz, sz);
        }
        ctx.restore();
      }
    },
  };
}
