import * as THREE from '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/engine/www/three.module.min.js';
const D2R=Math.PI/180;
const dir=(la,lo)=>new THREE.Vector3(Math.cos(la*D2R)*Math.cos(lo*D2R),Math.sin(la*D2R),-Math.cos(la*D2R)*Math.sin(lo*D2R));
const ll=v=>{const n=v.clone().normalize();return [+(Math.asin(n.y)/D2R).toFixed(1),+(Math.atan2(-n.z,n.x)/D2R).toFixed(1)]};
const qPole=(la,lo,d)=>new THREE.Quaternion().setFromAxisAngle(dir(la,lo),d*D2R);
const pts={natal:[-5.8,-35.2],recife:[-8,-35],sp:[-23.5,-46.6],capehorn:[-56,-67],nyc:[40.7,-74],newfound:[47.5,-52.7],florida:[25,-80.5]};
for (const [name,q] of Object.entries({SAp:qPole(44,-30.6,57),SAm:qPole(44,-30.6,-57),NAp:qPole(66.95,-12.02,75.55),NAm:qPole(66.95,-12.02,-75.55)})){
  console.log(name, Object.entries(pts).map(([k,p])=>k+':'+ll(dir(...p).applyQuaternion(q)).join(',')).join('  '));
}
