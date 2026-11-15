// HawaiiStage: real DEM terrain + seafloor around the Hawaiian Islands with an animatable water level, for thumbnail-grade hero stills.
// Forked from lab/drain/terrain.js (TerrainStage) so lab_drain.html keeps working. Units: 1 world unit = 1 km. Pure function of state.
// Differences from TerrainStage:
//  - sun shadows are ray-marched in the shader over the height textures (any sun az/el, any vertical exaggeration, no bake per light);
//  - seabed material: dark basalt flanks, dark brown pelagic sediment on gentle slopes, a little cream reef only on the shallow shelf
//    (never the pale tan "drained basin" ramp of the clone channels);
//  - old-shoreline devices: a pale "bathtub ring" band just below the former sea level and/or one luminous waterline on the 0 m contour;
//  - water: turquoise palette option, a screen-space foam rim at the waterline and a luminous shallow edge;
//  - grade: exposure, contrast, saturation, warm/cool split, vignette; haze is height-aware relative to the drained floor.
// Production options (ep02 toolkit, engine/www/ep/ep02/shared.js; all default off, so lab_hawaii.html renders as before):
//  - o.renderer: share one WebGLRenderer between stages; render(time, seed, target) can draw the final pass into a render target;
//  - the scene target's alpha carries a class mask (sky 0, water 0.25, drained seabed 0.5, today's land 1) for masked grades;
//    post('keepA', 1) passes it through to the output target;
//  - setMask(texture, bbox): R = hero fill (heroAmt, heroCol), G = dimmed and desaturated (dimAmt); camera shiftX (lens shift);
//  - decoded heights and textures are cached per URL, so several stages on one page load the data once.
//  - (2026-11-09, all default off) clipN: a vertical cut plane (terrain and water discarded on one side, for cut-aways; see
//    lab/hawaii/section.js); capBB: land outside this lon/lat box is classed 0.5 (graded like the flank, not the cap);
//    heroPass: hero-filled pixels are classed 0.75 (the shared grade passes them through, so the fill keeps its colour);
//    lineFar: the old-coast line and bathtub ring fade out between these distances (km); seaMat 1: one depth-coded seabed
//    (reef flat 0 to -150 m, grey sediment, dark slate basalt deep and on steep flanks); nearAmt: near-field seabed detail;
//    water wRamp (shallow->mid->deep depths in m), waveAmt (wave normals), glintAmt, surfAmt (broken surf band offshore).
//  - (2026-11-09, close-up quality; o.crisp loads what it needs, uniforms default off) crisp: bicubic B-spline normals from float32
//    heights (texelFetch; no bilinear creases, no half-float terraces), B-spline AO and Catmull-Rom colour where texels are magnified;
//    colSharp: texture-space unsharp mask of the colour at about 3 texels; detAmt: tiling procedural detail (detailTextures(): canopy,
//    rock, soil; world metres from a 4 km camera anchor, mipmapped and anisotropic) chosen per pixel from the colour, slope and height,
//    faded in where the colour map is magnified (cMag) within detFar km, each octave faded out once the imagery resolves its scale
//    (colRes: the colour's source resolution, res.colour_src_m); detail normals lit by the stage sun and a little detail AO;
//    hazeFar (U): extra aerial haze beyond the close-up zone.
// Any region: loadRegion(root, name) (or load() on a region folder) reads <root>/regions.json (lab/hawaii/tools/region_bake.py) and
// stacks 1-3 nested layers, finest first; the legacy two-layer folder renders pixel-identically to before (lab/hawaii/README.md, Regions).
import * as THREE from 'three';

export const R_EARTH = 6371.0, KM_DEG = 111.32;

const COMMON = /* glsl */`
uniform vec3 camPos; uniform vec3 sunDir; uniform float horizonDip;
uniform vec3 zenithCol, horizonCol, hazeCol, sunCol, glowCol;
uniform float fogDens, fogH, fogBg, fogBase; uniform vec3 hazeFar;
vec3 skyColor(vec3 d){
  float y = clamp(d.y + horizonDip, 0.0, 1.0);
  vec3 c = mix(horizonCol, zenithCol, pow(y, 0.45));
  float mu = max(dot(d, sunDir), 0.0);
  c += glowCol * (pow(mu, 5.0) * 0.35 + pow(mu, 64.0) * 0.8);
  c = mix(c, hazeCol, exp(-y * 16.0) * 0.45);
  return c;
}
vec3 inscatter(vec3 d){
  float mu = max(dot(d, sunDir), 0.0);
  return hazeCol + glowCol * (pow(mu, 5.0) * 0.40);
}
vec3 aerial(vec3 col, vec3 wp, out float T){
  vec3 v = wp - camPos; float dist = length(v); vec3 d = v / max(dist, 1e-4);
  float y0 = max(camPos.y - fogBase, 0.0), y1 = max(wp.y - fogBase, 0.0), dy = y1 - y0;
  float od = abs(dy) < 1e-3 ? fogDens * exp(-y0 / fogH) * dist : fogDens * dist * fogH * (exp(-y0 / fogH) - exp(-y1 / fogH)) / dy;
  od += fogBg * dist;
  T = exp(-od);
  // hazeFar (x, y km, z amount; default off): extra aerial haze that sets in beyond the close-up zone, so far ground whose colour
  // map is coarser than the screen reads as distance, not as a soft texture, next to crisp near ground
  if (hazeFar.z > 0.0) T *= 1.0 - hazeFar.z * smoothstep(hazeFar.x, hazeFar.y, dist);
  return col * T + inscatter(d) * (1.0 - T);
}
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s; }
// noise at frequency f (cycles per degree) faded to its mean where one cycle spans fewer than ~4 pixels (pf = pixel footprint in degrees)
float fbmL(vec2 ll, float f, float pf){ return mix(0.47, fbm(ll * f), 1.0 - smoothstep(0.12, 0.45, f * pf)); }
`;

// height lookup across the nested grids (hero inside its bbox, then the optional mid layer, wide skirt elsewhere; with two layers
// mid = skirt) + sun visibility by ray-marching toward the sun
const HEIGHT = /* glsl */`
uniform sampler2D hHero, hMid, hSkirt; uniform vec4 bbHero, bbMid, bbSkirt; uniform float vex, sunEl, penumbra;
float hAt(vec2 ll){
  vec2 uh = (ll - bbHero.xy) / (bbHero.zw - bbHero.xy);
  if (uh.x > 0.0 && uh.y > 0.0 && uh.x < 1.0 && uh.y < 1.0) return texture2D(hHero, uh).r;
  vec2 um = (ll - bbMid.xy) / (bbMid.zw - bbMid.xy);
  if (um.x > 0.0 && um.y > 0.0 && um.x < 1.0 && um.y < 1.0) return texture2D(hMid, um).r;
  return texture2D(hSkirt, (ll - bbSkirt.xy) / (bbSkirt.zw - bbSkirt.xy)).r;
}
float sunVis(vec2 ll, float h0){
  vec2 hd = normalize(vec2(sunDir.x, -sunDir.z) + 1e-6);
  vec2 dir = vec2(hd.x / (${KM_DEG} * cos(radians(ll.y))), hd.y / ${KM_DEG});
  float best = -1.0, s = 0.18;
  for (int i = 0; i < 38; i++) {
    float dz = (hAt(ll + dir * s) - h0) * vex * 0.001 - s * s / ${(2 * R_EARTH).toFixed(1)};
    best = max(best, dz / s); s *= 1.2;
  }
  return clamp((sunEl - atan(best)) / penumbra + 0.5, 0.0, 1.0);
}
`;

const TERRAIN_VS = /* glsl */`
uniform vec3 camPos; uniform vec4 hole; uniform float holeDrop; uniform vec4 bb; uniform vec2 detAnchor;
varying vec2 vUv; varying vec3 vW; varying vec2 vD;
void main(){
  vUv = uv; vec3 p = position;
  // detail-texture coordinates: metres from an anchor snapped to 4 km near the camera (exact in float32, a whole number of tiles of
  // every detail octave, so the pattern never moves when the anchor steps), kept small for float precision anywhere on a stage
  vD = (position.xz - detAnchor) * 1000.0;
  vec2 ll = bb.xy + uv * (bb.zw - bb.xy);
  if (holeDrop > 0.0 && ll.x > hole.x && ll.x < hole.z && ll.y > hole.y && ll.y < hole.w) p.y -= holeDrop;
  vec2 d = p.xz - camPos.xz; p.y -= dot(d, d) / (2.0 * ${R_EARTH.toFixed(1)});
  vW = p;
  gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;

const TERRAIN_FS = /* glsl */`
${COMMON}
${HEIGHT}
uniform sampler2D hTex, aoTex, colTex; uniform vec2 texel; uniform vec4 bb;
uniform float level, ringH, sunI, skyI, dbg, landSat, landGain, seaRelief, shadows;
uniform vec3 basaltCol, sedCol, reefCol, tubCol, lineCol;
uniform float reefAmt, tubM, tubAmt, oldLine, lineW, detail;
uniform sampler2D maskTex; uniform vec4 maskBB; uniform float maskOn, heroAmt, dimAmt; uniform vec3 heroCol;
uniform vec4 clipN, capBB; uniform float heroPass, seaMat, nearAmt, landLift; uniform vec2 lineFar;
uniform sampler2D hTexF, dVeg, dRock, dSoil; uniform float crisp, colBias, colSharp, detAmt, detRel, colRes; uniform vec2 detFar;
varying vec2 vUv; varying vec3 vW; varying vec2 vD;
float Hm(vec2 uv){ return texture2D(hTex, uv).r; }
// ---- close-up quality (crisp, detAmt; all off by default, the ep02 toolkit turns them on) ----
// B-spline bicubic height with its analytic gradient from a 4x4 texelFetch of the float32 heights: (h, dh/di, dh/dj) in metres per
// texel. C2 heights, C1 normals: no bilinear grid creases or half-float terraces in the shading of a magnified DEM.
vec3 hGradB(vec2 uv){
  ivec2 sz = textureSize(hTexF, 0); vec2 st = uv * vec2(sz) - 0.5, i = floor(st), f = st - i, f2 = f * f, f3 = f2 * f, g = 1.0 - f;
  vec4 wx = vec4(g.x * g.x * g.x, 3.0 * f3.x - 6.0 * f2.x + 4.0, -3.0 * f3.x + 3.0 * f2.x + 3.0 * f.x + 1.0, f3.x) / 6.0;
  vec4 wy = vec4(g.y * g.y * g.y, 3.0 * f3.y - 6.0 * f2.y + 4.0, -3.0 * f3.y + 3.0 * f2.y + 3.0 * f.y + 1.0, f3.y) / 6.0;
  vec4 dx = vec4(-0.5 * g.x * g.x, 1.5 * f2.x - 2.0 * f.x, -1.5 * f2.x + f.x + 0.5, 0.5 * f2.x);
  vec4 dy = vec4(-0.5 * g.y * g.y, 1.5 * f2.y - 2.0 * f.y, -1.5 * f2.y + f.y + 0.5, 0.5 * f2.y);
  vec3 r = vec3(0.0); ivec2 b = ivec2(i) - 1, mx = sz - 1;
  for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++) {
    float v = texelFetch(hTexF, clamp(b + ivec2(x, y), ivec2(0), mx), 0).r;
    r += v * vec3(wx[x] * wy[y], dx[x] * wy[y], wx[x] * dy[y]);
  }
  return r;
}
// Catmull-Rom bicubic colour in 9 bilinear taps (sharper than bilinear, no texel grid); for magnified colour texels only
vec3 texCR(sampler2D t, vec2 uv){
  vec2 sz = vec2(textureSize(t, 0)), sp = uv * sz, t1 = floor(sp - 0.5) + 0.5, f = sp - t1;
  vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f)), w1 = 1.0 + f * f * (-2.5 + 1.5 * f), w2 = f * (0.5 + f * (2.0 - 1.5 * f)), w3 = f * f * (-0.5 + 0.5 * f);
  vec2 w12 = w1 + w2, a = (t1 - 1.0) / sz, c = (t1 + 2.0) / sz, m = (t1 + w2 / w12) / sz;
  vec3 r = (textureLod(t, vec2(a.x, a.y), 0.0).rgb * w0.x + textureLod(t, vec2(m.x, a.y), 0.0).rgb * w12.x + textureLod(t, vec2(c.x, a.y), 0.0).rgb * w3.x) * w0.y
         + (textureLod(t, vec2(a.x, m.y), 0.0).rgb * w0.x + textureLod(t, vec2(m.x, m.y), 0.0).rgb * w12.x + textureLod(t, vec2(c.x, m.y), 0.0).rgb * w3.x) * w12.y
         + (textureLod(t, vec2(a.x, c.y), 0.0).rgb * w0.x + textureLod(t, vec2(m.x, c.y), 0.0).rgb * w12.x + textureLod(t, vec2(c.x, c.y), 0.0).rgb * w3.x) * w3.y;
  return max(r, 0.0);
}
// B-spline bicubic of one channel in 4 bilinear taps (smooth, for the AO of a magnified DEM)
float texBS(sampler2D t, vec2 uv){
  vec2 sz = vec2(textureSize(t, 0)), st = uv * sz - 0.5, i = floor(st), f = st - i, g = 1.0 - f;
  vec2 w0 = g * g * g / 6.0, w1 = (3.0 * f * f * f - 6.0 * f * f + 4.0) / 6.0, w2 = (-3.0 * f * f * f + 3.0 * f * f + 3.0 * f + 1.0) / 6.0, w3 = f * f * f / 6.0;
  vec2 g0 = w0 + w1, g1 = w2 + w3, h0 = (i - 0.5 + w1 / g0) / sz, h1 = (i + 1.5 + w3 / g1) / sz;
  return g0.y * (g0.x * textureLod(t, h0, 0.0).r + g1.x * textureLod(t, vec2(h1.x, h0.y), 0.0).r)
       + g1.y * (g0.x * textureLod(t, vec2(h0.x, h1.y), 0.0).r + g1.x * textureLod(t, h1, 0.0).r);
}
// one octave of a tiling detail texture (detailTextures(): R height, GB slope, A tint/crack) at p metres, tile T m, turned 90 degrees
// (r) and offset (o) to break up the octaves: (h - 0.5, dh/dx, dh/dz per metre, a - 0.5). Mipmapped and anisotropic: no shimmer.
// weight of a detail octave whose features are F metres where the colour map resolves res metres: none once the imagery shows them
float octW(float F, float res){ return 1.0 - smoothstep(1.2, 3.0, F / res); }
vec4 dTap(sampler2D t, vec2 p, float T, float r, vec2 o){
  vec4 s = texture2D(t, (r > 0.5 ? vec2(p.y, -p.x) : p) / T + o);
  vec2 g = (s.gb - 0.5) * 128.0 / T;
  return vec4(s.r - 0.5, r > 0.5 ? vec2(-g.y, g.x) : g, s.a - 0.5);
}
vec3 seabed(float h, float slope, float cav, vec2 ll, float pf){
  float dep = -h;
  float n = fbm(ll * 6.0), n2 = fbmL(ll + 3.0, 33.0, pf), n3 = fbmL(ll + n * 0.02, 170.0, pf);
  // sediment ponds on gentle slopes (abyssal plain, moat), bare basalt on the flanks and slide blocks
  float rocky = smoothstep(0.035, 0.11, slope + (n2 - 0.5) * 0.05);
  vec3 c;
  if (seaMat > 0.5) {
    // one depth-coded seabed for every shot: reef flat 0 to -150 m, grey sediment (olive-brown drapes), dark slate basalt
    // deep and on steep flanks (the NO OCEAN look), so the shelf of the ONE ISLAND shot and the drained massif read as one world
    float deep = smoothstep(700.0, 2600.0, dep + (n - 0.5) * 500.0);
    vec3 sed = sedCol * mix(vec3(1.0), vec3(1.10, 1.04, 0.84), smoothstep(0.35, 0.75, n2));
    c = mix(sed, basaltCol, max(rocky, deep));
    float shelf = (1.0 - smoothstep(115.0, 170.0, dep + (n2 - 0.5) * 40.0)) * (1.0 - 0.65 * smoothstep(0.06, 0.16, slope));
    c = mix(c, reefCol * (0.9 + 0.2 * n2), shelf * reefAmt);
  } else {
    c = mix(sedCol, basaltCol, rocky);
    // shallow carbonate shelf (cream reef), only where it is both shallow and gentle
    float shelf = (1.0 - smoothstep(70.0, 190.0, dep)) * (1.0 - smoothstep(0.03, 0.10, slope));
    c = mix(c, reefCol, shelf * reefAmt);
  }
  c *= 0.85 + 0.28 * n + 0.14 * (n2 - 0.5) + 0.12 * (n3 - 0.5) * detail;
  c *= clamp(1.0 - cav * 1.5, 0.66, 1.25);
  return c;
}
void main(){
  if (clipN.w > 0.5 && dot(vW.xz, clipN.xy) + clipN.z > 0.0) discard;
  vec2 ll = bb.xy + vUv * (bb.zw - bb.xy);
  float lat = radians(ll.y);
  float h = Hm(vUv);
  vec2 fp = max(texel, fwidth(vUv) * 0.75);
  float pf = max(fwidth(ll.x), fwidth(ll.y));
  float hl = Hm(vUv - vec2(fp.x, 0.0)), hr = Hm(vUv + vec2(fp.x, 0.0)), hd = Hm(vUv - vec2(0.0, fp.y)), hu = Hm(vUv + vec2(0.0, fp.y));
  float dxk = (bb.z - bb.x) * fp.x * ${KM_DEG} * cos(lat), dyk = (bb.w - bb.y) * fp.y * ${KM_DEG};
  float gx = (hr - hl) * vex * 0.001 / (2.0 * dxk), gy = (hu - hd) * vex * 0.001 / (2.0 * dyk);
  // crisp: where a height texel spans more than about a pixel, the gradient of the bicubic surface (smooth normals, no texel grid)
  vec2 tpx = texel / max(fwidth(vUv), vec2(1e-9));
  float kB = crisp * smoothstep(0.75, 1.5, min(tpx.x, tpx.y));
  if (kB > 0.0) {
    vec3 hg = hGradB(vUv); float ex = (bb.z - bb.x) * texel.x * ${KM_DEG} * cos(lat), ey = (bb.w - bb.y) * texel.y * ${KM_DEG};
    gx = mix(gx, hg.y * vex * 0.001 / ex, kB); gy = mix(gy, hg.z * vex * 0.001 / ey, kB);
  }
  float rk = mix(seaRelief, 1.0, smoothstep(-40.0, 0.0, h));
  // procedural micro-relief on the seabed (sonar grids are 100-450 m; this keeps close flanks from looking like plastic)
  float sub = 1.0 - smoothstep(-30.0, 10.0, h);
  vec2 q = ll * 180.0; float e = 0.37;
  vec2 dn = vec2(fbm(q + vec2(e, 0.0)) - fbm(q - vec2(e, 0.0)), fbm(q + vec2(0.0, e)) - fbm(q - vec2(0.0, e))) * 0.16 * detail * sub * (1.0 - smoothstep(0.12, 0.45, 180.0 * pf));
  float slope = length(vec2(gx, gy)) / vex;
  // gullies and lava ribs on steep submarine flanks: ridged noise stretched along the fall line (about 0.7 km apart, km long)
  vec2 fall = vec2(gx, gy) / (length(vec2(gx, gy)) + 1e-6), perp = vec2(-fall.y, fall.x);
  vec2 km = vec2(ll.x * ${KM_DEG} * cos(lat), ll.y * ${KM_DEG});
  float acr = dot(km, perp), alo = dot(km, fall), gf = 1.4;
  float steep = smoothstep(0.05, 0.16, slope) * sub * (1.0 - smoothstep(0.12, 0.45, gf * pf * ${KM_DEG})) * detail;
  float rid = 1.0 - abs(2.0 * fbm(vec2(acr * gf, alo * gf * 0.12)) - 1.0);
  float rid2 = 1.0 - abs(2.0 * fbm(vec2((acr + 0.06) * gf, alo * gf * 0.12)) - 1.0);
  vec2 pg = perp * (rid2 - rid) / 0.06 * 0.09 * steep;
  // near-field detail (nearAmt): ~150 m and ~45 m basalt relief, faded by the pixel footprint (look book U6)
  vec2 dn2 = vec2(0.0); float nearV = 0.5;
  if (nearAmt > 0.001) {
    vec2 q2 = ll * 760.0; float e2 = 0.31;
    float fade2 = (1.0 - smoothstep(0.12, 0.45, 760.0 * pf)) * sub, fade3 = (1.0 - smoothstep(0.12, 0.45, 2600.0 * pf)) * sub;
    dn2 = vec2(fbm(q2 + vec2(e2, 0.0)) - fbm(q2 - vec2(e2, 0.0)), fbm(q2 + vec2(0.0, e2)) - fbm(q2 - vec2(0.0, e2))) * 0.22 * fade2;
    vec2 q3 = ll * 2600.0 + 7.3;
    dn2 += vec2(vnoise(q3 + vec2(e2, 0.0)) - vnoise(q3 - vec2(e2, 0.0)), vnoise(q3 + vec2(0.0, e2)) - vnoise(q3 - vec2(0.0, e2))) * 0.10 * fade3;
    dn2 *= nearAmt; nearV = mix(0.5, fbmL(ll + 11.0, 760.0, pf), nearAmt * sub);
  }
  vec3 n = normalize(vec3(-gx * rk + dn.x + dn2.x - pg.x, 1.0, gy * rk - dn.y - dn2.y + pg.y));
  float cav = clamp((hl + hr + hd + hu - 4.0 * h) / max(fp.x * 4096.0, 1.0) / 90.0, -0.25, 0.25);
  float ao = texture2D(aoTex, vUv).r;
  if (kB > 0.0) ao = mix(ao, texBS(aoTex, vUv), kB);
  float shadow = shadows > 0.5 ? sunVis(ll, h) : 1.0;
  vec3 land = colBias != 0.0 ? texture2D(colTex, vUv, colBias).rgb : texture2D(colTex, vUv).rgb;
  // colour texels per screen pixel (cMag > 1: the colour map is magnified and soft); crisp: Catmull-Rom instead of bilinear there
  vec2 cpx = 1.0 / (vec2(textureSize(colTex, 0)) * max(fwidth(vUv), vec2(1e-9)));
  // cMag uses the more magnified axis: at grazing angles the map is minified along the view but still soft across it
  float cMag = max(cpx.x, cpx.y), kC = crisp * smoothstep(1.0, 2.0, min(cpx.x, cpx.y));
  float fadeD = 1.0 - smoothstep(detFar.x, detFar.y, length(vW - camPos));
  if (kC > 0.0) {
    land = mix(land, texCR(colTex, vUv), kC);
    // colSharp: unsharp mask in texture space at about 3 texels (the 30 m satellite pixels baked into a 10 m grid), limited to
    // +-30 % of the colour so a bright patch never gets a dark rim; stable in motion (it moves with the ground, not the screen)
    float kS = colSharp * kC * fadeD;
    if (kS > 0.0) { vec3 bl = textureLod(colTex, vUv, 1.6).rgb; land = max(land + clamp((land - bl) * kS, -0.3 * land, 0.3 * land), 0.0); }
  }
  float l0 = dot(land, vec3(0.2126, 0.7152, 0.0722)); land = max(mix(vec3(l0), land, landSat), 0.0) * landGain * (0.86 + 0.20 * fbmL(ll, 520.0, pf) + 0.10 * (fbmL(ll, 2100.0, pf) - 0.5));
  // landLift: baked-in topographic shadow (black texels in a satellite composite) lifted to a rock grey; real shade comes from the sun
  if (landLift > 0.0) { float ld = dot(land, vec3(0.2126, 0.7152, 0.0722)); land = mix(land, max(land, vec3(landLift) * vec3(1.0, 0.97, 0.92)), 1.0 - smoothstep(landLift * 0.4, landLift * 1.4, ld)); }
  vec3 alb = mix(seabed(h, slope, cav, ll, pf) * mix(1.0, 0.70 + 0.55 * rid, steep) * (0.82 + 0.36 * nearV), land, smoothstep(-6.0, 4.0, h));
  // detail texturing (detAmt): where the colour map is magnified (cMag > 1) and the camera is close (detFar, km), tiling high-frequency
  // detail in world metres: forest canopy, rock / lava, fine soil and sand, chosen per pixel from the colour (excess green, brightness),
  // the slope and the height; albedo modulated about 1 (the colour map's mean is kept, so far views do not change) and detail normals
  // lit by the stage sun, with a little detail AO
  float kD = detAmt * smoothstep(1.0, 3.0, cMag) * fadeD;
  if (kD > 0.002) {
    float onL = smoothstep(-6.0, 4.0, h), s3 = land.r + land.g + land.b + 1e-4, lL = dot(land, vec3(0.2126, 0.7152, 0.0722));
    float exg = (2.0 * land.g - land.r - land.b) / s3, chr = (max(land.r, max(land.g, land.b)) - min(land.r, min(land.g, land.b))) / (max(land.r, max(land.g, land.b)) + 1e-4);
    // vegetation = green dominant (not just excess green, which also takes yellow-ochre cinder and dry grass)
    float gdm = (land.g - max(land.r, land.b)) / s3;
    float wV = smoothstep(0.02, 0.10, gdm) * smoothstep(0.02, 0.10, exg) * (1.0 - smoothstep(1.4, 2.2, slope));
    float wS = (1.0 - wV) * smoothstep(0.09, 0.2, lL) * (1.0 - smoothstep(6.0, 20.0, h)) * (1.0 - smoothstep(0.08, 0.25, slope));
    float rkL = max(smoothstep(0.3, 0.75, slope), 1.0 - smoothstep(0.025, 0.07, lL));
    float snow = smoothstep(0.28, 0.5, lL) * (1.0 - smoothstep(0.08, 0.2, chr));
    vec3 W = vec3(wV, (1.0 - wV - wS) * rkL, (1.0 - wV - wS) * (1.0 - rkL) + wS);
    float rkS = 0.5 * smoothstep(0.035, 0.11, slope);
    W = mix(vec3(0.0, rkS, 1.0 - rkS), W, onL);
    float amp = kD * (1.0 - 0.75 * snow) * mix(0.5, 1.0, onL);
    // the colour map's real resolution (m): its texel, or the coarser source imagery baked into it (colRes: HLS 30 m, NAIP 0.6 m)
    float res = max(colRes, (bb.z - bb.x) * ${(KM_DEG * 1000).toFixed(1)} * cos(lat) / float(textureSize(colTex, 0).x));
    vec3 mod3 = vec3(1.0); vec2 G = vec2(0.0); float Hd = 0.0;
    if (W.x > 0.01) {   // canopy: crowns about 6 m (62.5 m tile), clumps about 25 m, leaves and shrubs about 1.5 m
      vec4 a = dTap(dVeg, vD, 62.5, 0.0, vec2(0.0)), b = dTap(dVeg, vD, 250.0, 1.0, vec2(0.37, 0.71)), c = dTap(dVeg, vD, 15.625, 1.0, vec2(0.13, 0.52));
      a *= octW(6.0, res); b *= octW(25.0, res); c *= octW(1.5, res);
      a *= 0.45 + 1.1 * clamp(b.x + 0.5, 0.0, 1.0);   // rougher canopy in the clumps, smoother between them (no even 'moss')
      float hv = a.x + 0.8 * b.x + 0.25 * c.x;
      vec3 m = vec3(clamp(1.0 + 1.0 * hv, 0.3, 1.45)) * (1.0 + a.w * vec3(0.26, 0.14, -0.34) + b.w * vec3(0.18, 0.10, -0.16));
      mod3 += W.x * (m - 1.0); G += W.x * (2.8 * a.yz + 7.0 * b.yz + 0.35 * c.yz); Hd += W.x * hv;
    }
    if (W.y > 0.01) {   // rock and lava: ridged blocks about 3 m (31.25 m tile), outcrops about 12 m, cracks and grit
      vec4 a = dTap(dRock, vD, 31.25, 0.0, vec2(0.0)), b = dTap(dRock, vD, 125.0, 1.0, vec2(0.61, 0.23)), c = dTap(dRock, vD, 7.8125, 1.0, vec2(0.29, 0.83));
      a *= octW(5.0, res); b *= octW(20.0, res); c *= octW(1.2, res);
      float hr2 = a.x + 0.6 * b.x + 0.4 * c.x;
      vec3 m = vec3(clamp(1.0 + 0.8 * hr2 + 0.35 * a.w, 0.4, 1.5));
      mod3 += W.y * (m - 1.0); G += W.y * (1.6 * a.yz + 4.5 * b.yz + 0.3 * c.yz); Hd += W.y * hr2;
    }
    if (W.z > 0.01) {   // soil, grass, sand: fine relief about 1 m (10 m tile), 4 m swells, pebbles and grit
      vec4 a = dTap(dSoil, vD, 10.0, 0.0, vec2(0.0)), b = dTap(dSoil, vD, 40.0, 1.0, vec2(0.47, 0.19)), c = dTap(dSoil, vD, 2.5, 1.0, vec2(0.71, 0.37));
      vec4 e = dTap(dSoil, vD, 160.0, 1.0, vec2(0.83, 0.61));   // patches about 30-80 m: fields, scrub, yards (mid distance)
      a *= octW(2.0, res); b *= octW(8.0, res); c *= octW(0.5, res); e *= octW(32.0, res);
      float hs = a.x + 0.7 * b.x + 0.4 * c.x;
      vec3 m = vec3(clamp(1.0 + 0.5 * hs + 0.3 * a.w + 0.55 * e.w + 0.3 * e.x, 0.55, 1.45)) * (1.0 + e.x * vec3(-0.10, 0.06, -0.05));
      mod3 += W.z * (m - 1.0); G += W.z * (0.35 * a.yz + 0.9 * b.yz + 0.08 * c.yz + 1.2 * e.yz); Hd += W.z * hs * 0.5;
    }
    alb *= mix(vec3(1.0), mod3, amp);
    n = normalize(n / max(n.y, 0.08) - vec3(G.x, 0.0, G.y) * vex * detRel * amp);
    ao *= clamp(1.0 + 0.8 * Hd * amp, 0.55, 1.15);
  }
  float exposed = step(h, -1.0) * step(level, h);
  float above = h - level;
  // bathtub ring: pale mineral crust in a band just below the former sea level, broken up by noise
  float camD = length(vW - camPos), farK = 1.0 - smoothstep(lineFar.x, lineFar.y, camD);
  float tb = exposed * (1.0 - smoothstep(tubM * 0.35, tubM, -h)) * smoothstep(0.25, 0.6, fbmL(ll, 420.0, pf) + 0.25 * (1.0 + h / tubM));
  alb = mix(alb, tubCol, tb * tubAmt * farK);
  // dark wet band right above the new waterline
  float ring = exposed * (1.0 - smoothstep(0.0, ringH, above));
  alb *= 1.0 - 0.5 * ring;
  float heroW = 0.0;
  if (maskOn > 0.5) {
    vec2 mq = (ll - maskBB.xy) / (maskBB.zw - maskBB.xy);
    vec4 mk = (mq.x > 0.0 && mq.y > 0.0 && mq.x < 1.0 && mq.y < 1.0) ? texture2D(maskTex, mq) : vec4(0.0);
    float ml = dot(alb, vec3(0.2126, 0.7152, 0.0722));
    alb = mix(alb, mix(vec3(ml), alb, 0.3) * 0.62, mk.g * dimAmt);
    alb = mix(alb, heroCol * (0.55 + 0.9 * ml / (ml + 0.08)), mk.r * heroAmt);
    heroW = mk.r * heroPass;
  }
  float ndl = max(dot(n, sunDir), 0.0);
  vec3 sky = mix(hazeCol, zenithCol, 0.55);
  vec3 col = alb * (sunCol * sunI * ndl * shadow + sky * skyI * ao * (0.55 + 0.45 * n.y) + vec3(0.05, 0.04, 0.03) * (1.0 - n.y));
  vec3 v = normalize(camPos - vW); vec3 hv = normalize(v + sunDir);
  col += sunCol * sunI * ring * 0.16 * pow(max(dot(n, hv), 0.0), 40.0) * shadow;
  // one luminous line on the former coastline (0 m contour), constant width in pixels
  float fw = max(fwidth(h), 1e-3);
  float dl = abs(h + 0.5) / fw;
  float cl = oldLine * farK * step(level, -25.0) * (1.0 - smoothstep(lineW * 0.5, lineW * 0.5 + 1.0, dl));
  float glow = oldLine * farK * step(level, -25.0) * exp(-dl / (lineW * 1.6)) * 0.35;
  float T; vec3 colA = aerial(col, vW, T);
  colA = mix(colA, lineCol, clamp(cl, 0.0, 1.0)) + lineCol * glow * T;
  if (dbg > 0.5) { vec3 o = dbg < 1.5 ? vec3(0.5 + h / 8000.0, 0.5 + h / 8000.0, h < 0.0 ? 1.0 : 0.0) : dbg < 2.5 ? vec3(T) : dbg < 3.5 ? alb : vec3(shadow, ao, 0.0); gl_FragColor = vec4(o * 0.6, 1.0); return; }
  // alpha = class: drained seabed 0.5, today's land 1 (0.5 outside capBB), hero-filled 0.75 (heroPass: the shared grade leaves it)
  float inCap = step(capBB.x, ll.x) * step(ll.x, capBB.z) * step(capBB.y, ll.y) * step(ll.y, capBB.w);
  float cls = mix(0.5, mix(0.5, 1.0, inCap), smoothstep(-2.0, 2.0, h));
  gl_FragColor = vec4(colA, mix(cls, 0.75, clamp(heroW, 0.0, 1.0)));
}`;

const WATER_VS = /* glsl */`
uniform vec3 camPos; uniform float yLevel; uniform vec4 bb;
varying vec3 vW; varying vec2 vLL;
void main(){
  vLL = bb.xy + uv * (bb.zw - bb.xy);
  vec3 p = position; p.y = yLevel;
  vec2 d = p.xz - camPos.xz; p.y -= dot(d, d) / (2.0 * ${R_EARTH.toFixed(1)});
  vW = p; gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;

const WATER_FS = /* glsl */`
${COMMON}
${HEIGHT}
uniform float level, time, sunI, dbg, foamAmt, foamPx, foamM, edgeGlow, fresMax, waveAmt, glintAmt, surfAmt;
uniform vec3 wShallow, wMid, wDeep; uniform vec4 wRamp, clipN;
varying vec3 vW; varying vec2 vLL;
float hBlend(vec2 ll){
  vec2 us = (ll - bbSkirt.xy) / (bbSkirt.zw - bbSkirt.xy);
  float hs = texture2D(hSkirt, us).r;
  vec2 um = (ll - bbMid.xy) / (bbMid.zw - bbMid.xy);
  if (um.x > 0.0 && um.y > 0.0 && um.x < 1.0 && um.y < 1.0 && bbMid != bbSkirt) {
    vec2 em = min(um, 1.0 - um); hs = mix(hs, texture2D(hMid, um).r, smoothstep(0.0, 0.025, min(em.x, em.y)));
  }
  vec2 uh = (ll - bbHero.xy) / (bbHero.zw - bbHero.xy);
  if (uh.x < 0.0 || uh.y < 0.0 || uh.x > 1.0 || uh.y > 1.0) return hs;
  vec2 e = min(uh, 1.0 - uh); float w = smoothstep(0.0, 0.025, min(e.x, e.y));
  return mix(hs, texture2D(hHero, uh).r, w);
}
void main(){
  if (clipN.w > 0.5 && dot(vW.xz, clipN.xy) + clipN.z > 0.0) discard;
  float h = hBlend(vLL);
  float depth = level - h;
  if (depth <= 0.0) discard;
  vec2 p = vW.xz;
  float slick = fbm(p * 0.045 + vec2(time * 0.004, -time * 0.002));
  vec2 g = vec2(fbm(p * 0.6 + vec2(time * 0.03, 0.0)) - fbm(p * 0.6 + vec2(0.37, 0.0) + vec2(time * 0.03, 0.0)),
                fbm(p * 0.6 + vec2(0.0, 0.37) + vec2(0.0, time * 0.02)) - fbm(p * 0.6 + vec2(0.0, time * 0.02)));
  float rough = mix(0.035, 0.11, slick);
  vec3 n = normalize(vec3(g.x * rough * 2.0, 1.0, g.y * rough * 2.0));
  if (waveAmt > 0.001) {   // wind waves: two crossing swell trains + chop, faded by the pixel footprint (no shimmer far away)
    float pw = max(fwidth(p.x), fwidth(p.y));
    vec2 w1 = vec2(0.82, 0.57), w2 = vec2(-0.37, 0.93);
    // swell about 150 m and 100 m long (real ocean scale), chop about 40 m: sub-pixel far away, so only the near water carries them
    float k1 = 42.0, k2 = 63.0, f1 = 1.0 - smoothstep(0.05, 0.25, k1 * pw / 6.283), f2 = 1.0 - smoothstep(0.05, 0.25, k2 * pw / 6.283);
    vec2 sl = w1 * cos(dot(p, w1) * k1 - time * 2.6) * 0.5 * f1 + w2 * cos(dot(p, w2) * k2 + time * 3.1) * 0.35 * f2;
    float f3 = 1.0 - smoothstep(0.05, 0.25, 150.0 * pw / 6.283);
    vec2 ch = vec2(fbm(p * 150.0 + time * 0.8) - 0.5, fbm(p * 150.0 + 9.1 - time * 0.6) - 0.5) * f3;
    n = normalize(n + vec3(sl.x + ch.x * 0.6, 0.0, sl.y + ch.y * 0.6) * 0.06 * waveAmt);
  }
  vec3 v = normalize(camPos - vW);
  float fres = 0.02 + fresMax * pow(1.0 - max(dot(n, v), 0.0), 5.0);
  vec3 refl = skyColor(reflect(-v, n)) * mix(vec3(1.0), wShallow * 2.2 + 0.25, 0.35);
  vec3 hv = normalize(v + sunDir); float nh = max(dot(n, hv), 0.0);
  float a2 = rough * rough; float dd = nh * nh * (a2 - 1.0) + 1.0; float spec = a2 / (3.14159 * dd * dd);
  vec3 glint = sunCol * sunI * spec * glintAmt * fres;
  vec3 body = mix(wShallow, wMid, smoothstep(wRamp.x, wRamp.y, depth)); body = mix(body, wDeep, smoothstep(wRamp.z, wRamp.w, depth));
  body *= 0.55 + 0.45 * sunI / 3.0;
  // foam rim + luminous shallow edge, sized in screen pixels via the depth derivative
  float fwD = max(fwidth(depth), 0.05);
  float fr = foamPx * fwD + foamM;
  float pf = max(fwidth(vLL.x), fwidth(vLL.y));
  float fn = fbmL(vLL, 2400.0, pf) * 0.7 + fbmL(vLL, 300.0, pf) * 0.6;
  float foam = foamAmt * (1.0 - smoothstep(fr * (0.35 + 0.5 * fn), fr * (0.7 + 0.6 * fn), depth));
  float edge = edgeGlow * (1.0 - smoothstep(fr, fr * 3.0, depth));
  // broken surf band a little offshore (surfAmt): white water where the bottom shoals, in streaks along the swell
  // (in metres of depth, faded where one metre of depth spans more than a pixel row: no streaks at grazing angles)
  if (surfAmt > 0.001) { float sb = smoothstep(1.5, 3.0, depth) * (1.0 - smoothstep(5.0, 9.0, depth)) * (1.0 - smoothstep(0.6, 2.0, fwD));
    foam = max(foam, surfAmt * sb * smoothstep(0.45, 0.8, fbmL(vLL + time * 0.0004, 1500.0, pf) * 0.8 + fn * 0.4)); }
  body = mix(body, wShallow * 1.9, edge * 0.7);
  float aBody = 1.0 - exp(-depth / 7.0);
  float alpha = 1.0 - (1.0 - aBody) * (1.0 - fres);
  vec3 prem = body * aBody * (1.0 - fres) + refl * fres + glint;
  float lit = max(dot(vec3(0.0, 1.0, 0.0), sunDir), 0.15);
  vec3 foamC = vec3(0.92, 0.96, 0.98) * (sunCol * sunI * lit * 0.32 + mix(hazeCol, zenithCol, 0.5) * 0.45);
  prem = mix(prem, foamC, clamp(foam, 0.0, 1.0)); alpha = max(alpha, clamp(foam, 0.0, 1.0));
  float T; vec3 dummy = aerial(vec3(0.0), vW, T);
  vec3 d = normalize(vW - camPos);
  prem = prem * T + inscatter(d) * (1.0 - T) * alpha;
  if (dbg > 4.5) { gl_FragColor = vec4(fract(vLL.x), fract(vLL.y), clamp(depth / 3000.0, 0.0, 1.0), 1.0); return; }
  gl_FragColor = vec4(prem, alpha);
}`;

const SKY_VS = /* glsl */`
varying vec3 vDir; uniform vec3 camPos;
void main(){ vDir = position; vec4 w = vec4(position + camPos, 1.0); gl_Position = projectionMatrix * viewMatrix * w; gl_Position.z = gl_Position.w * 0.99999; }`;
const SKY_FS = /* glsl */`
${COMMON}
varying vec3 vDir;
void main(){ vec3 d = normalize(vDir); gl_FragColor = vec4(skyColor(d), 0.0); }`;   // alpha = class: sky 0

// final pass: exposure, ACES fit, saturation, split-tone, gamma, contrast around mid-grey, vignette, grain
export const POST_FS = /* glsl */`
uniform sampler2D src; uniform float exposure, vignette, grain, seed, sat, contrast, lift, keepA; uniform vec2 res; varying vec2 vUv;
vec3 aces(vec3 x){ return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main(){
  vec4 s0 = texture2D(src, vUv); vec3 c = s0.rgb * exposure;
  c = aces(c);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = max(mix(vec3(l), c, sat), 0.0);
  c += vec3(-0.008, 0.002, 0.012) * (1.0 - smoothstep(0.0, 0.45, l)) + vec3(0.012, 0.004, -0.010) * smoothstep(0.45, 1.0, l);
  c = pow(max(c, 0.0), vec3(1.0 / 2.2));
  c = clamp((c - 0.5) * contrast + 0.5 + lift, 0.0, 1.0);
  vec2 q = vUv - 0.5; q.x *= res.x / res.y;
  c *= 1.0 - vignette * smoothstep(0.35, 1.05, length(q));
  c += (h12(gl_FragCoord.xy + seed * 61.7) - 0.5) * grain;
  gl_FragColor = vec4(c, keepA > 0.5 ? s0.a : 1.0);
}`;
export const POST_VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }';

export async function loadImage(url) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('img ' + url)); i.src = url; }); }
// per-page caches: several stages (terrain, blocks) share decoded heights, textures and meta
const CACHE = new Map();
export function cached(key, fn) { if (!CACHE.has(key)) CACHE.set(key, fn()); return CACHE.get(key); }
export const loadMeta = (dir) => cached('meta:' + dir, async () => (await fetch(dir + '/meta.json')).json());
export const loadH16 = (url, meta) => cached('h16:' + url, async () => decodeH16(await loadImage(url), meta));
export const loadTex = (url, srgb) => cached('tex:' + url + ':' + !!srgb, async () => { const t = await new THREE.TextureLoader().loadAsync(url); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; t.minFilter = THREE.LinearMipmapLinearFilter; return t; });
export function decodeH16(img, meta) {  // RG 16-bit -> Float32 metres, rows flipped so row 0 = south
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
  const px = g.getImageData(0, 0, c.width, c.height).data, W = c.width, H = c.height, out = new Float32Array(W * H);
  for (let r = 0; r < H; r++) { const src = r * W, dst = (H - 1 - r) * W; for (let i = 0; i < W; i++) { const k = (src + i) * 4; out[dst + i] = ((px[k] << 8 | px[k + 1]) / 65535) * meta.hrange + meta.hmin; } }
  return { data: out, W, H };
}
export function heightTexture(hm) {
  const half = new Uint16Array(hm.data.length); for (let i = 0; i < half.length; i++) half[i] = THREE.DataUtils.toHalfFloat(hm.data[i]);
  const t = new THREE.DataTexture(half, hm.W, hm.H, THREE.RedFormat, THREE.HalfFloatType);
  t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true; return t;
}
// float32 heights for the crisp path's texelFetch (no filtering needed): half floats step 0.25-4 m at 256-8,000 m, which shows as
// terraces in the shading of a magnified 10 m DEM. One per decoded grid (WeakMap on the cached grid object).
const HF32 = new WeakMap();
export function heightTexture32(hm) {
  if (!HF32.has(hm)) {
    const t = new THREE.DataTexture(hm.data, hm.W, hm.H, THREE.RedFormat, THREE.FloatType);
    t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true;
    HF32.set(hm, t);
  }
  return HF32.get(hm);
}
// Tiling detail textures for close-up terrain (procedural, generated here: no image files, no licences). Each N x N RGBA8, periodic,
// mipmapped, anisotropic: R = height (mean 0.5), G/B = slope dh/du, dh/dv in tile units (0.5 + s / 128), A = a tint or crack channel
// (mean 0.5). veg: tropical canopy (two sizes of crowns as domes with gaps, leaf noise; A = per-crown tint); rock: ridged blocks,
// cracks along cell edges, grit (A = crack); soil: fbm swells, pebbles (A = colour noise). Deterministic (fixed seeds).
let DETAIL = null;
export function detailTextures(R, N = 512) {
  if (DETAIL) return DETAIL;
  const H = (x, y, s) => { let h = Math.imul(x, 0x27d4eb2d) ^ Math.imul(y + 0x9e37, 0x165667b1) ^ Math.imul(s + 0x51ed, 0x5bd1e995);
    h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d); h = Math.imul(h ^ (h >>> 12), 0x297a2d39); h ^= h >>> 15; return (h >>> 0) / 4294967296; };
  const wrap = (i, P) => ((i % P) + P) % P;
  // periodic gradient noise (period P cells), about 0..1
  const gn = (x, y, P, s) => { const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (i, j, dx, dy) => { const a = H(wrap(i, P), wrap(j, P), s) * 6.2831853; return Math.cos(a) * dx + Math.sin(a) * dy; };
    const u = fx * fx * fx * (fx * (fx * 6 - 15) + 10), v = fy * fy * fy * (fy * (fy * 6 - 15) + 10);
    const a = g(xi, yi, fx, fy), b = g(xi + 1, yi, fx - 1, fy), c = g(xi, yi + 1, fx, fy - 1), d = g(xi + 1, yi + 1, fx - 1, fy - 1);
    return 0.5 + 0.7 * (a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v); };
  const fbm = (x, y, P, oct, s, ridge = false) => { let a = 1, t = 0, n = 0, f = 1;
    for (let k = 0; k < oct; k++) { let v = gn(x * f, y * f, P * f, s + k * 101); if (ridge) { v = 1 - Math.abs(2 * v - 1); v *= v; } t += a * v; n += a; f *= 2; a *= 0.5; } return t / n; };
  // periodic Worley over G cells, one jittered point per cell: calls fn(dist in cells, cell hash seed) for the 3x3 neighbours
  const cells = (x, y, G, s, fn) => { const cx = Math.floor(x), cy = Math.floor(y);
    for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) { const ii = wrap(cx + i, G), jj = wrap(cy + j, G);
      const px = cx + i + 0.15 + 0.7 * H(ii, jj, s), py = cy + j + 0.15 + 0.7 * H(ii, jj, s + 7); fn(Math.hypot(x - px, y - py), ii * 977 + jj * 131 + s); } };
  const make = (fill) => {
    const h = new Float32Array(N * N), a = new Float32Array(N * N);
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const r = fill((i + 0.5) / N, (j + 0.5) / N); h[j * N + i] = r[0]; a[j * N + i] = r[1]; }
    const mean = (v) => v.reduce((s, x) => s + x, 0) / v.length, mh = mean(h), ma = mean(a);
    const d = new Uint8Array(N * N * 4), at = (x, y) => h[wrap(y, N) * N + wrap(x, N)];
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const k = j * N + i, sx = (at(i + 1, j) - at(i - 1, j)) * N / 2, sy = (at(i, j + 1) - at(i, j - 1)) * N / 2;
      const q = (v) => Math.max(0, Math.min(255, Math.round(v * 255)));
      d[k * 4] = q(h[k] - mh + 0.5); d[k * 4 + 1] = q(0.5 + sx / 128); d[k * 4 + 2] = q(0.5 + sy / 128); d[k * 4 + 3] = q(a[k] - ma + 0.5); }
    const t = new THREE.DataTexture(d, N, N, THREE.RGBAFormat, THREE.UnsignedByteType);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
    t.anisotropy = R ? R.capabilities.getMaxAnisotropy() : 8; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true; return t;
  };
  const veg = make((u, v) => {   // emergent crowns (5 per tile, 45 % present), 9 main and 18 small crowns per tile, as domes of varied
    let best = 0, id = 0.5;       // size and height; gaps fall to a low, noisy understory
    const crown = (G, s, hk, p = 1) => cells(u * G, v * G, G, s, (d, c) => { if (H(c, 13, s) > p) return;
      const r = 0.36 + 0.42 * H(c, 3, s), hf = hk * (0.6 + 0.4 * H(c, 5, s)), x = d / r;
      if (x < 1) { const dome = hf * Math.pow(1 - x * x, 0.55); if (dome > best) { best = dome; id = H(c, 9, s); } } });
    crown(5, 7, 1.15, 0.45); crown(9, 11, 1.0); crown(18, 23, 0.74);
    const leaf = fbm(u * 24, v * 24, 24, 3, 41), under = 0.06 + 0.12 * fbm(u * 6, v * 6, 6, 3, 43);
    return [Math.max(best, under) + 0.12 * (leaf - 0.5) * (best > under ? 1 : 0.5), id];
  });
  const rock = make((u, v) => {   // ridged blocks + grit; thin cracks on domain-warped Worley edges (curved, broken), mostly in A
    const wu = u + 0.035 * (fbm(u * 4, v * 4, 4, 3, 51) - 0.5), wv = v + 0.035 * (fbm(u * 4 + 7.3, v * 4, 4, 3, 53) - 0.5);
    let f1 = 9, f2 = 9; cells(wu * 7, wv * 7, 7, 61, (d) => { if (d < f1) { f2 = f1; f1 = d; } else if (d < f2) f2 = d; });
    const crack = (1 - Math.min(1, Math.max(0, (f2 - f1 - 0.015) / 0.05))) * Math.min(1, Math.max(0, (fbm(u * 8, v * 8, 8, 3, 57) - 0.38) * 4));
    const rid = fbm(u * 4, v * 4, 4, 5, 63, true), base = fbm(u * 3, v * 3, 3, 5, 67), grit = fbm(u * 64, v * 64, 64, 2, 71);
    return [0.5 * rid + 0.4 * base + 0.1 * grit - 0.06 * crack, 1 - crack];
  });
  const soil = make((u, v) => {   // fbm swells + sparse pebbles
    let peb = 0; cells(u * 22, v * 22, 22, 83, (d, c) => { if (H(c, 1, 83) < 0.35) { const x = d / 0.28; if (x < 1) peb = Math.max(peb, Math.sqrt(1 - x * x)); } });
    return [0.75 * fbm(u * 5, v * 5, 5, 6, 89) + 0.25 * peb, fbm(u * 3, v * 3, 3, 4, 97)];
  });
  DETAIL = { veg, rock, soil };
  return DETAIL;
}
export function sampleH(hm, u, v) {  // bilinear, u,v in 0..1 (v from south)
  const x = Math.min(Math.max(u * (hm.W - 1), 0), hm.W - 1.001), y = Math.min(Math.max(v * (hm.H - 1), 0), hm.H - 1.001);
  const i = x | 0, j = y | 0, fx = x - i, fy = y - j, d = hm.data, W = hm.W;
  return d[j * W + i] * (1 - fx) * (1 - fy) + d[j * W + i + 1] * fx * (1 - fy) + d[(j + 1) * W + i] * (1 - fx) * fy + d[(j + 1) * W + i + 1] * fx * fy;
}
export const C = (hex, k = 1) => new THREE.Color(hex).multiplyScalar(k);  // sRGB hex -> linear
const V3 = (a) => new THREE.Vector3(...a);

// looks: sky, haze and sun colours (sRGB hex), intensities
export const LOOKS = {
  gold: { zenith: '#1b58bd', horizon: '#a9c9ee', haze: ['#a6bfdd', 0.70], sun: '#ffc68c', glow: ['#ffae66', 0.40], sunI: 3.6, skyI: 0.62 },
  day: { zenith: '#1553b5', horizon: '#9fc4ee', haze: ['#a5c0e0', 0.74], sun: '#fff3e2', glow: ['#ffe6c8', 0.5], sunI: 3.5, skyI: 0.70 },
  warm: { zenith: '#1e5fbf', horizon: '#b9d0ea', haze: ['#adc3dd', 0.72], sun: '#ffd6a8', glow: ['#ffbc7c', 0.40], sunI: 3.6, skyI: 0.64 },
};
export const WATERS = {  // linear RGB: shallow, mid, deep
  turq: [[0.020, 0.40, 0.42], [0.006, 0.17, 0.25], [0.002, 0.060, 0.125]],
  lagoon: [[0.020, 0.42, 0.40], [0.005, 0.19, 0.22], [0.002, 0.085, 0.12]],
  ocean: [[0.020, 0.22, 0.26], [0.006, 0.090, 0.16], [0.003, 0.035, 0.085]],
};

export class HawaiiStage {
  constructor(W, H, o = {}) {
    this.W = W; this.H = H; this.o = o;
    if (o.renderer) this.R = o.renderer;
    else { this.R = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, alpha: false }); this.R.setPixelRatio(1); this.R.setSize(W, H, false); }
    this.R.autoClear = true;
    this.rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: o.samples ?? 4, depthBuffer: true });
    this.scene = new THREE.Scene();
    this.cam = new THREE.PerspectiveCamera(o.fov ?? 30, W / H, 0.5, 9000);
    this.level = 0; this.time = 0;
  }
  // legacy folder (hero_* + skirt_*: lab/hawaii/data), or a region folder baked by region_bake.py (then its stack from ../regions.json)
  async load(dir) {
    const meta = await loadMeta(dir);
    if (meta.files && meta.name) return this.loadRegion(dir.replace(/\/[^/]+\/?$/, ''), meta.name);
    this.meta = meta;
    this.vex = this.o.vex ?? meta.vex ?? 1.0;
    this.c0 = this.o.origin ?? { lon: -155.6, lat: 19.6 };
    [this.hHero, this.hSkirt] = await Promise.all([loadH16(dir + '/hero_h16.png', meta), loadH16(dir + '/skirt_h16.png', meta)]);
    const tex = (u, srgb) => loadTex(dir + '/' + u, srgb);
    const [heroCol, heroAO, skCol, skAO] = await Promise.all([tex('hero_color.jpg', true), tex('hero_ao.png', false), tex('skirt_color.jpg', true), tex('skirt_ao.png', false)]);
    const hT = await cached('htex:' + dir + '/hero', async () => heightTexture(this.hHero)), sT = await cached('htex:' + dir + '/skirt', async () => heightTexture(this.hSkirt));
    return this.build([{ name: 'hero', bbox: meta.hero_bbox, hm: this.hHero, hT, col: heroCol, ao: heroAO, grid: this.o.heroGrid || [1500, 1500], colRes: 250 },
      { name: 'skirt', bbox: meta.skirt_bbox, hm: this.hSkirt, hT: sT, col: skCol, ao: skAO, grid: this.o.skirtGrid || [900, 680], colRes: 1000 }]);
  }
  // any region of an episode's regions.json (e.g. root 'ep/ep02/data', name 'midway'): its 'stack' = 1-3 nested layers, finest first,
  // each inside the next (o.stack overrides it). meta.hero_bbox / hHero = the finest layer, meta.skirt_bbox / hSkirt = the outermost.
  async loadRegion(root, name) {
    const idx = await cached('regions:' + root, async () => (await fetch(root + '/regions.json')).json());
    const R = idx.regions[name]; if (!R) throw new Error('unknown region ' + name);
    const stack = (this.o.stack || R.stack || [name]).slice(0, 3), big = [1500, 1000, 900];
    const L = await Promise.all(stack.map(async (n, i) => {
      const r = idx.regions[n]; if (!r) throw new Error('unknown region ' + n);
      const d = r.dir, hm = await loadH16(d + '/' + r.files.h16, { hmin: r.hmin ?? -8000, hrange: r.hrange ?? 17000 });
      const [col, ao, hT] = await Promise.all([loadTex(d + '/' + r.files.color, true), loadTex(d + '/' + r.files.ao, false), cached('htex:' + d + '/' + r.files.h16, async () => heightTexture(hm))]);
      const k = Math.min(1, big[i] / Math.max(...r.wh));  // mesh: at most 1500 / 1000 / 900 vertices on the long side, never more than the texels
      const g = (i === 0 ? this.o.heroGrid : i === stack.length - 1 ? this.o.skirtGrid : this.o.midGrid) || [Math.max(2, Math.round(r.wh[0] * k)), Math.max(2, Math.round(r.wh[1] * k))];
      // colRes: the real resolution of the colour (m), as texel_audit.js reads it: res.colour_src_m (detail_bake.py), else HLS 30 m,
      // MODIS 250 m, Blue Marble 500 m (the legacy Big Island hero and skirt: MODIS 250 m, 1000 m)
      const c = r.colour || {}, colRes = r.res?.colour_src_m ?? (n === 'bigisland' ? 250 : n === 'hawaii_skirt' ? 1000 : c.hls ? 30 : c.modis ? 250 : 500);
      return { name: n, bbox: r.bbox, hm, hT, col, ao, grid: g, colRes };
    }));
    for (let i = 1; i < L.length; i++) { const a = L[i - 1].bbox, b = L[i].bbox; if (a[0] < b[0] || a[1] < b[1] || a[2] > b[2] || a[3] > b[3]) console.error(`region stack: ${L[i - 1].name} is not inside ${L[i].name}`); }
    const hb = L[0].bbox;
    this.meta = { name, region: R, stack, layers: L.map(l => ({ name: l.name, bbox: l.bbox })), hero_bbox: hb, skirt_bbox: L[L.length - 1].bbox, hmin: -8000, hrange: 17000, vex: 1.0 };
    this.hHero = L[0].hm; this.hSkirt = L[L.length - 1].hm;
    this.vex = this.o.vex ?? 1.0;
    this.c0 = this.o.origin ?? R.origin ?? { lon: (hb[0] + hb[2]) / 2, lat: (hb[1] + hb[3]) / 2 };
    return this.build(L);
  }
  // layers finest first (1-3): { name, bbox, hm (decoded heights), hT (height texture), col, ao (textures), grid: [nx, ny] mesh vertices }
  build(L) {
    this.layers = L;
    const hero = L[0], mid = L[Math.min(1, L.length - 1)], skirt = L[L.length - 1];
    this.U = {
      camPos: { value: new THREE.Vector3() }, sunDir: { value: new THREE.Vector3(0, 1, 0) }, horizonDip: { value: 0 },
      zenithCol: { value: C('#2c64a8') }, horizonCol: { value: C('#a9c3dc') }, hazeCol: { value: C('#aec2d6', 0.8) },
      sunCol: { value: C('#fff1de') }, glowCol: { value: C('#ffe2b8', 0.9) },
      fogDens: { value: this.o.fogDens ?? 0.0028 }, fogH: { value: this.o.fogH ?? 6.0 }, fogBg: { value: this.o.fogBg ?? 0.00012 }, fogBase: { value: 0 },
      sunEl: { value: 0.4 }, penumbra: { value: THREE.MathUtils.degToRad(1.4) }, vex: { value: this.vex },
      detAnchor: { value: new THREE.Vector2() }, hazeFar: { value: new THREE.Vector3(0, 0, 0) },
    };
    // o.crisp (the ep02 toolkit sets it): float32 heights for the bicubic normals, the detail textures, anisotropic filtering at the
    // GPU's maximum on the colour and AO maps. The look itself is switched by the uniforms crisp / detAmt / colBias (default 0).
    const crisp = !!this.o.crisp, det = crisp ? detailTextures(this.R) : null;
    if (crisp) { const mA = this.R.capabilities.getMaxAnisotropy(); for (const l of L) for (const t of [l.col, l.ao]) if (t && t.anisotropy !== mA) { t.anisotropy = mA; t.needsUpdate = true; } }
    const hb = hero.bbox, sb = skirt.bbox;
    const HU = { hHero: { value: hero.hT }, hMid: { value: mid.hT }, hSkirt: { value: skirt.hT },
      bbHero: { value: new THREE.Vector4(...hb) }, bbMid: { value: new THREE.Vector4(...mid.bbox) }, bbSkirt: { value: new THREE.Vector4(...sb) } };
    const blank = new THREE.DataTexture(new Uint8Array([0, 0, 0, 0]), 1, 1); blank.needsUpdate = true;
    this.clipU = { value: new THREE.Vector4(0, 0, 0, 0) };   // (nx, nz, d, on): discard where dot(xz, n) + d > 0 (shared by terrain and water)
    this.maskU = { tex: { value: blank }, bb: { value: new THREE.Vector4(0, 0, 1, 1) }, on: { value: 0 }, heroAmt: { value: 0 }, dimAmt: { value: 0 }, heroCol: { value: C('#FF5A36', 0.17) } };
    const terrMat = (hTex, aoTex, colTex, bb, hm, holeDrop, hole = hb) => new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, HU, {
        hTex: { value: hTex }, aoTex: { value: aoTex }, colTex: { value: colTex }, texel: { value: new THREE.Vector2(1 / hm.W, 1 / hm.H) },
        bb: { value: new THREE.Vector4(...bb) }, hole: { value: new THREE.Vector4(...hole) }, holeDrop: { value: holeDrop },
        level: { value: 0 }, ringH: { value: 40 }, dbg: { value: 0 }, landSat: { value: 1.2 }, landGain: { value: 1.15 }, seaRelief: { value: 1.0 },
        sunI: { value: 3.2 }, skyI: { value: 0.9 }, shadows: { value: 1 },
        basaltCol: { value: V3([0.033, 0.034, 0.038]) }, sedCol: { value: V3([0.066, 0.062, 0.060]) }, reefCol: { value: V3([0.16, 0.165, 0.155]) },
        tubCol: { value: V3([0.42, 0.42, 0.40]) }, lineCol: { value: V3([0.55, 1.6, 1.9]) },
        reefAmt: { value: 0.45 }, tubM: { value: 90 }, tubAmt: { value: 0 }, oldLine: { value: 0 }, lineW: { value: 2.2 }, detail: { value: 1.0 },
        maskTex: this.maskU.tex, maskBB: this.maskU.bb, maskOn: this.maskU.on, heroAmt: this.maskU.heroAmt, dimAmt: this.maskU.dimAmt, heroCol: this.maskU.heroCol,
        clipN: this.clipU, capBB: { value: new THREE.Vector4(-1e4, -1e4, 1e4, 1e4) }, heroPass: { value: 0 }, seaMat: { value: 0 }, nearAmt: { value: 0 }, landLift: { value: 0 }, lineFar: { value: new THREE.Vector2(1e5, 2e5) },
        hTexF: { value: crisp ? heightTexture32(hm) : hTex }, dVeg: { value: det ? det.veg : blank }, dRock: { value: det ? det.rock : blank }, dSoil: { value: det ? det.soil : blank },
        crisp: { value: 0 }, colBias: { value: 0 }, colSharp: { value: 0 }, colRes: { value: 0 }, detAmt: { value: 0 }, detRel: { value: 1 }, detFar: { value: new THREE.Vector2(6, 16) },
      }), vertexShader: TERRAIN_VS, fragmentShader: TERRAIN_FS,
    });
    // one mesh per layer; each coarser layer drops out of sight inside the next finer layer's bbox
    this.mats = L.map((l, i) => terrMat(l.hT, l.ao, l.col, l.bbox, l.hm, i ? 4.0 + 6.0 * this.vex : 0, i ? L[i - 1].bbox : hb));
    L.forEach((l, i) => { this.mats[i].uniforms.colRes.value = l.colRes || 0; });   // the source resolution of each layer's colour (m)
    this.heroMat = this.mats[0]; this.skirtMat = this.mats[L.length - 1];
    L.forEach((l, i) => this.scene.add(new THREE.Mesh(this.grid(l.bbox, l.hm, l.grid), this.mats[i])));
    this.waterMat = new THREE.ShaderMaterial({
      uniforms: Object.assign({}, this.U, HU, {
        bb: { value: new THREE.Vector4(...sb) }, level: { value: 0 }, yLevel: { value: 0 }, time: { value: 0 }, sunI: { value: 3.2 }, dbg: { value: 0 },
        foamAmt: { value: 0 }, foamPx: { value: 2.5 }, foamM: { value: 2.0 }, edgeGlow: { value: 0.6 }, fresMax: { value: 0.55 },
        wRamp: { value: new THREE.Vector4(6, 120, 150, 900) }, waveAmt: { value: 0 }, glintAmt: { value: 0.08 }, surfAmt: { value: 0 }, clipN: this.clipU,
        wShallow: { value: V3(WATERS.turq[0]) }, wMid: { value: V3(WATERS.turq[1]) }, wDeep: { value: V3(WATERS.turq[2]) },
      }),
      vertexShader: WATER_VS, fragmentShader: WATER_FS, transparent: true, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      blendSrcAlpha: THREE.ConstantAlphaFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor, blendAlpha: 0.25,   // alpha = class: water 0.25
    });
    const water = new THREE.Mesh(this.grid(sb, null, [600, 450]), this.waterMat); water.renderOrder = 2; this.scene.add(water);
    const sky = new THREE.Mesh(new THREE.SphereGeometry(6000, 64, 32), new THREE.ShaderMaterial({ uniforms: this.U, vertexShader: SKY_VS, fragmentShader: SKY_FS, side: THREE.BackSide, depthWrite: false }));
    sky.renderOrder = -1; sky.frustumCulled = false; this.scene.add(sky);
    this.postMat = new THREE.ShaderMaterial({
      uniforms: { src: { value: this.rt.texture }, exposure: { value: 1.2 }, vignette: { value: 0.20 }, grain: { value: 0.012 }, seed: { value: 0 }, sat: { value: 1.2 }, contrast: { value: 1.1 }, lift: { value: 0 }, keepA: { value: 0 }, res: { value: new THREE.Vector2(this.W, this.H) } },
      vertexShader: POST_VS, fragmentShader: POST_FS, depthTest: false, depthWrite: false,
    });
    this.postScene = new THREE.Scene(); const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.postMat); q.frustumCulled = false; this.postScene.add(q);
    this.postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }
  xyz(lon, lat, hm = 0) { return new THREE.Vector3((lon - this.c0.lon) * KM_DEG * Math.cos(lat * Math.PI / 180), hm * this.vex * 0.001, -(lat - this.c0.lat) * KM_DEG); }
  grid(bb, hm, [nx, ny]) {
    const pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2);
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const u = i / (nx - 1), v = j / (ny - 1), lon = bb[0] + u * (bb[2] - bb[0]), lat = bb[1] + v * (bb[3] - bb[1]), k = j * nx + i;
      const p = this.xyz(lon, lat, hm ? sampleH(hm, u, v) : 0); pos[k * 3] = p.x; pos[k * 3 + 1] = p.y; pos[k * 3 + 2] = p.z; uv[k * 2] = u; uv[k * 2 + 1] = v;
    }
    const idx = new Uint32Array((nx - 1) * (ny - 1) * 6); let n = 0;
    for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1; idx[n++] = a; idx[n++] = b; idx[n++] = c; idx[n++] = b; idx[n++] = d; idx[n++] = c; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5); return g;
  }
  heightAt(lon, lat) {  // metres from the finest layer that contains the point (the outermost layer clamps)
    const L = this.layers;
    for (let i = 0; i < L.length - 1; i++) { const b = L[i].bbox; if (lon > b[0] && lon < b[2] && lat > b[1] && lat < b[3]) return sampleH(L[i].hm, (lon - b[0]) / (b[2] - b[0]), (lat - b[1]) / (b[3] - b[1])); }
    const s = L[L.length - 1].bbox; return sampleH(L[L.length - 1].hm, (lon - s[0]) / (s[2] - s[0]), (lat - s[1]) / (s[3] - s[1]));
  }
  // camera: lon/lat + alt (km above sea level, may be negative in drained shots) or agl (km above the ground/water under the camera);
  // aim with heading/pitch (deg) or a target tLon/tLat/tH (m; default = ground height there)
  setCamera(c) {
    const p = this.xyz(c.lon, c.lat, 0);
    const gnd = Math.max(this.heightAt(c.lon, c.lat), this.level) * this.vex * 0.001;
    p.y = c.agl != null ? gnd + c.agl : c.alt;
    let t;
    if (c.tLon == null) {
      const hd = THREE.MathUtils.degToRad(c.heading ?? 0), pt = THREE.MathUtils.degToRad(c.pitch ?? -15);
      t = p.clone().add(new THREE.Vector3(Math.sin(hd) * Math.cos(pt), Math.sin(pt), -Math.cos(hd) * Math.cos(pt)).multiplyScalar(100));
    } else {
      t = this.xyz(c.tLon, c.tLat, c.tH ?? Math.max(this.heightAt(c.tLon, c.tLat), this.level)); const d = t.clone().sub(p); t.y -= (d.x * d.x + d.z * d.z) / (2 * R_EARTH);
    }
    this.cam.position.copy(p); this.cam.up.set(0, 1, 0); this.cam.lookAt(t);
    if (c.roll) this.cam.rotateZ(THREE.MathUtils.degToRad(c.roll));
    this.cam.fov = c.fov ?? this.cam.fov;
    this.cam.near = c.near ?? this.o.near ?? 0.5; this.cam.far = c.far ?? this.o.far ?? 9000;  // km; ground cameras (agl < 0.5) need near ~0.005-0.02 and a smaller far
    this.cam.updateProjectionMatrix();
    if (c.shiftY || c.shiftX) { this.cam.projectionMatrix.elements[9] += c.shiftY || 0; this.cam.projectionMatrix.elements[8] += c.shiftX || 0; this.cam.projectionMatrixInverse.copy(this.cam.projectionMatrix).invert(); }  // lens shift (keeps verticals straight)
    this.cam.updateMatrixWorld();
    this.U.detAnchor.value.set(Math.round(p.x / 4) * 4, Math.round(p.z / 4) * 4);   // km, a multiple of 4 (see TERRAIN_VS)
    this.U.camPos.value.copy(p); this.U.horizonDip.value = Math.sqrt(2 * Math.max(p.y - gnd, 0.01) / R_EARTH);
    this.camGround = gnd;
  }
  setSun(az, el) {
    const A = THREE.MathUtils.degToRad(az), E = THREE.MathUtils.degToRad(el);
    this.U.sunDir.value.set(Math.sin(A) * Math.cos(E), Math.sin(E), -Math.cos(A) * Math.cos(E)); this.U.sunEl.value = E;
  }
  setLook(name, o = {}) {
    const L = Object.assign({}, LOOKS[name] || LOOKS.day, o);
    this.U.zenithCol.value = C(L.zenith); this.U.horizonCol.value = C(L.horizon); this.U.hazeCol.value = C(L.haze[0], L.haze[1]);
    this.U.sunCol.value = C(L.sun); this.U.glowCol.value = C(L.glow[0], L.glow[1]);
    this.set('sunI', L.sunI); this.set('skyI', L.skyI);
  }
  setWater(name) { const w = WATERS[name] || WATERS.turq; this.set('wShallow', V3(w[0])); this.set('wMid', V3(w[1])); this.set('wDeep', V3(w[2])); }
  setLevel(m) {
    this.level = m; for (const M of [...this.mats, this.waterMat]) M.uniforms.level.value = m; this.waterMat.uniforms.yLevel.value = m * this.vex * 0.001;
    this.U.fogBase.value = Math.max(Math.min(m, 0), -5500) * this.vex * 0.001;  // haze sits on the new floor (water surface or drained seabed)
  }
  set(k, v) { for (const M of [...this.mats, this.waterMat]) if (M.uniforms[k]) M.uniforms[k].value = v; }
  // highlight mask over a lon/lat bbox: R = hero fill, G = dimmed (texture: THREE.DataTexture RGBA8, row 0 = south). null switches it off.
  setMask(tex, bb) { if (!tex) { this.maskU.on.value = 0; return; } this.maskU.tex.value = tex; this.maskU.bb.value.set(...bb); this.maskU.on.value = 1; }
  post(k, v) { this.postMat.uniforms[k].value = v; }
  // vertical cut plane through lon/lat with horizontal normal (world x east, z south): discard where dot(p - A, n) > 0. null = off.
  setClip(c) { if (!c) { this.clipU.value.set(0, 0, 0, 0); return; } const A = this.xyz(c.lon, c.lat, 0); this.clipU.value.set(c.nx, c.nz, -(A.x * c.nx + A.z * c.nz), 1); }
  project(lon, lat, hm) {
    const p = this.xyz(lon, lat, hm ?? Math.max(this.heightAt(lon, lat), this.level)); const d = p.clone().sub(this.cam.position); p.y -= (d.x * d.x + d.z * d.z) / (2 * R_EARTH);
    const q = p.project(this.cam); if (q.z > 1) return null; return [(q.x + 1) / 2 * this.W, (1 - q.y) / 2 * this.H];
  }
  render(time = 0, seed = 0, target = null) {
    this.waterMat.uniforms.time.value = time; this.postMat.uniforms.seed.value = seed;
    this.R.autoClear = true; this.R.setClearColor(0x000000, 0);
    this.R.setRenderTarget(this.rt); this.R.render(this.scene, this.cam);
    this.R.setRenderTarget(target); this.R.render(this.postScene, this.postCam);
    return this.R.domElement;
  }
}
