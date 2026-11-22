// Cut-away Earth for a Stage: textured globe with a quarter wedge removed, layered cross-section faces,
// optional drill line through the centre. Uses three.js clipping planes (stage.renderer.localClippingEnabled).
import * as THREE from '../three.module.min.js';

export const LAYERS = [ // outer radius (fraction of Earth radius), colour, emissive
  { r: 1.000, c: 0x7a5a3a, e: 0x000000, name: 'CRUST' },
  { r: 0.990, c: 0xc2552a, e: 0x3a0c00, name: 'MANTLE' },
  { r: 0.546, c: 0xf0a020, e: 0x803000, name: 'OUTER CORE' },
  { r: 0.192, c: 0xfff0b0, e: 0xffc040, name: 'INNER CORE' },
];

function halfDisc(r0, r1, mat, seg = 96) {
  // half annulus in local XY plane spanning angles -90..+90 deg (x >= 0)
  const g = new THREE.RingGeometry(Math.max(r0, 1e-4), r1, seg, 1, -Math.PI / 2, Math.PI);
  return new THREE.Mesh(g, mat);
}

export async function cutawayEarth(stage, o = {}) {
  const R = o.radius || 3;
  stage.renderer.localClippingEnabled = true;
  const grp = new THREE.Group();
  const planes = [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0), new THREE.Plane(new THREE.Vector3(0, 0, -1), 0)];
  const tex = await new Promise(r => new THREE.TextureLoader().load(o.map || 'tex/day_8k.jpg', t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; r(t); }));
  const shell = new THREE.Mesh(new THREE.SphereGeometry(R, 192, 96), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9, clippingPlanes: planes, clipIntersection: true, side: THREE.FrontSide }));
  grp.add(shell);
  // inner surfaces of each layer boundary (seen through the wedge) — back faces of clipped spheres
  LAYERS.forEach((L, i) => {
    const inner = new THREE.Mesh(new THREE.SphereGeometry(R * L.r * 0.999, 128, 64), new THREE.MeshStandardMaterial({ color: L.c, emissive: L.e, emissiveIntensity: 0.8, roughness: 0.7, clippingPlanes: planes, clipIntersection: true, side: THREE.BackSide }));
    grp.add(inner);
  });
  // cross-section faces on the two cut planes
  const faces = new THREE.Group();
  LAYERS.forEach((L, i) => {
    const r1 = R * L.r, r0 = i + 1 < LAYERS.length ? R * LAYERS[i + 1].r : 0;
    const mat = new THREE.MeshStandardMaterial({ color: L.c, emissive: L.e, emissiveIntensity: i >= 2 ? 1.2 : 0.5, roughness: 0.75, side: THREE.DoubleSide });
    // face on plane z=0 for x>0  (XY plane, x>=0)
    const a = halfDisc(r0, r1, mat); faces.add(a);
    // face on plane x=0 for z>0  (YZ plane, z>=0): rotate the XY half-disc about Y by -90deg so +x -> +z
    const b = halfDisc(r0, r1, mat); b.rotation.y = -Math.PI / 2; faces.add(b);
  });
  grp.add(faces);
  grp.userData = { R, planes, faces, shell };
  stage.add(grp);
  return grp;
}

// unit direction for lat/lon in the same convention as globe.js
export function llDir(lat, lon) { const a = lat * Math.PI / 180, b = lon * Math.PI / 180; return new THREE.Vector3(Math.cos(a) * Math.cos(b), Math.sin(a), -Math.cos(a) * Math.sin(b)); }

// glowing drill tube from a surface point through the centre, grown to fraction p (0..1 of the diameter)
export function drill(grp, lat, lon, p, o = {}) {
  return drillDir(grp, llDir(lat, lon), p, o);
}
// drill along a world/group-space unit direction
export function drillDir(grp, d, p, o = {}) {
  const R = grp.userData.R;
  if (!grp.userData.drill) {
    const mat = new THREE.MeshBasicMaterial({ color: o.color || 0x3de3ff, transparent: true, opacity: 0.95 });
    const m = new THREE.Mesh(new THREE.CylinderGeometry(o.width || 0.035, o.width || 0.035, 1, 16), mat);
    grp.add(m); grp.userData.drill = m;
  }
  const m = grp.userData.drill;
  const a = d.clone().multiplyScalar(R * 1.02), b = d.clone().multiplyScalar(-R * 1.02);
  const end = a.clone().lerp(b, Math.max(0.001, p));
  m.position.copy(a.clone().add(end).multiplyScalar(0.5));
  m.scale.set(1, a.distanceTo(end), 1);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), end.clone().sub(a).normalize());
  return { a, end };
}
