// Earth that morphs into a tetrahedron (the 1875 "tetrahedral hypothesis" visual) — for a Stage.
import * as THREE from '../three.module.min.js';
import { llDir } from './cutaway.js';

// vertices: 4 lat/lon pairs (one at the south pole + three at ~19.47°N for a regular tetrahedron)
export async function tetraEarth(stage, o = {}) {
  const R = o.radius || 3;
  const verts = (o.vertices || [[-90, 0], [19.47, -75], [19.47, 45], [19.47, 165]]).map(([a, b]) => llDir(a, b));
  // face normals (outward) and inradius for the tetrahedron with circumradius 1
  const faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]].map(([i, j, k]) => {
    const A = verts[i], B = verts[j], C = verts[k];
    const n = new THREE.Vector3().subVectors(B, A).cross(new THREE.Vector3().subVectors(C, A)).normalize();
    if (n.dot(A) < 0) n.negate();
    return { n, h: n.dot(A) };
  });
  const geo = new THREE.SphereGeometry(R, 192, 96);
  const base = geo.attributes.position.array.slice();
  const target = new Float32Array(base.length);
  const d = new THREE.Vector3();
  for (let i = 0; i < base.length; i += 3) {
    d.set(base[i], base[i + 1], base[i + 2]).normalize();
    let t = Infinity;
    for (const f of faces) { const c = f.n.dot(d); if (c > 1e-6) t = Math.min(t, f.h / c); }
    const s = R * t * (o.tetraScale || 1.55); // scale so the tetra roughly matches the globe's apparent size
    target[i] = d.x * s; target[i + 1] = d.y * s; target[i + 2] = d.z * s;
  }
  const tex = await new Promise(r => new THREE.TextureLoader().load(o.map || 'tex/day_8k.jpg', t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; r(t); }));
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.85, flatShading: false });
  const mesh = new THREE.Mesh(geo, mat); mesh.castShadow = true;
  // wireframe edges of the tetrahedron (glowing), revealed with k
  const eg = new THREE.BufferGeometry();
  const ev = []; const scale = R * (o.tetraScale || 1.55) * 1.002;
  [[0, 1], [0, 2], [0, 3], [1, 2], [2, 3], [3, 1]].forEach(([i, j]) => { ev.push(...verts[i].clone().multiplyScalar(scale).toArray(), ...verts[j].clone().multiplyScalar(scale).toArray()); });
  eg.setAttribute('position', new THREE.Float32BufferAttribute(ev, 3));
  const edges = new THREE.LineSegments(eg, new THREE.LineBasicMaterial({ color: o.edgeColor || 0xffd23f, transparent: true, opacity: 0 }));
  const grp = new THREE.Group(); grp.add(mesh); grp.add(edges); stage.add(grp);
  grp.userData.set = (k, edgeAlpha = 0) => {
    const p = geo.attributes.position.array;
    for (let i = 0; i < p.length; i++) p[i] = base[i] + (target[i] - base[i]) * k;
    geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
    edges.material.opacity = edgeAlpha;
  };
  return grp;
}
