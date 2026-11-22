#!/usr/bin/env node
// texel_audit.js: texel density of every ep02 terrain shot. For each sampled film frame it measures, at screen points of the terrain
// view, how many screen pixels one colour texel and one height texel of the visible layer cover (the largest singular value of the
// ground-to-screen Jacobian, so slope and foreshortening count: a texel on a cliff face seen front-on is as big as it looks).
//   cd engine && node www/ep/ep02/tools/texel_audit.js [--chapters 1,2,3] [--segs s026,s027|all] [--views all|pali,halape|none]
//      [--www DIR] [--w 1920 --h 1080] [--out audit.json] [--md audit.md] [--tag before] [--closest 0|1] [--step 15]
// Frames: one per narration segment (its middle), each chapter page loaded alone (film.html {"ep":"ep02","only":"chN"}), so a chapter
// another builder is editing cannot break the others. The stage render is skipped (HawaiiStage.render and CineGlobe.render are
// replaced in the page by the measurement), so a frame costs well under a second: cameras, levels and regions are the film's own.
// Closest frames (--closest 1, the default with --segs all): every base shot of the chapter is also scanned every --step frames (and
// its last frame) at the centre and lower-third points only, and its worst frame (largest colour px / 2 or height px / 4) is measured
// in full as an extra row (seg id with ^): the closest point of each camera move, which a segment middle can miss.
// Views: each region's verification camera from data/regions.json (the planned shots of chapters not built yet).
// Points: centre (W/2, H/2), lower third (W/2, 2H/3), and the worst of a 5 x 3 grid over the lower band (y 70-90 %). Sky and water
// points are skipped (water hides the colour texture), and below -6 m only the height counts (the stage draws its seabed there). Colour is judged at its effective resolution: the texel, or the source when
// the texture is finer than its imagery (HLS 30 m, MODIS 250 m; regions.json 'res.colour_src_m' when present).
// Flags: colour > 2 px or height > 4 px at the centre or the lower third. Height is judged on the texel; where the region's meta marks
// ground its source only interpolated (res.height_interp polygons: the Nu'uanu band of the 2020 lidar), the cell also shows the
// source-limited px ('src').
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require(require.resolve('playwright', { paths: [process.cwd(), path.join(__dirname, '../../../..'), '/opt/node-tools/node_modules'] }));
const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const ENGINE = path.resolve(__dirname, '../../../..'), WWW = path.resolve(opt('www', path.join(ENGINE, 'www')));
const W = +opt('w', 1920), H = +opt('h', 1080), FPS = 30, TAG = opt('tag', '');
const CHAPTERS = opt('chapters', '1,2,3,4,5,6').split(',').filter(Boolean).map(Number);
const SEGS = opt('segs', 'all'), VIEWS = opt('views', 'all');
const OUT = opt('out', null), MD = opt('md', null), CLOSEST = +opt('closest', SEGS === 'all' ? 1 : 0), STEP = +opt('step', 15);
const LIM = { col: 2, h: 4 };
const timing = JSON.parse(fs.readFileSync(path.join(WWW, 'ep/ep02/timing.json')));
const IDX = JSON.parse(fs.readFileSync(path.join(WWW, 'ep/ep02/data/regions.json'))).regions;

// ---------- effective resolutions of a layer (m): colour source and finest height source
const LEGACY = { hero: 'bigisland', skirt: 'hawaii_skirt' };
// bigisland's colour is 30 m (HLS) only on the land inside the refined boxes (lab/hawaii/tools/hero_refine.py; the boxes are in
// lab/hawaii/data/meta.json colour_refine.boxes); the rest of the layer stays MODIS 250 m, although regions.json gives the whole layer
// res.colour_src_m 30. Water points are skipped anyway, so the box alone decides.
const REFINE = (() => { try { return Object.values(JSON.parse(fs.readFileSync(path.join(WWW, 'lab/hawaii/data/meta.json'))).colour_refine?.boxes || {}).map(b => b.bbox); }
  catch (e) { console.warn('texel_audit: no colour_refine boxes in lab/hawaii/data/meta.json (' + e.message + '): bigisland colour counted as 250 m'); return []; } })();
function colSrcM(name, lon, lat) {
  const r = IDX[LEGACY[name] || name] || {};
  if ((LEGACY[name] || name) === 'bigisland') return REFINE.some(b => lon >= b[0] && lon <= b[2] && lat >= b[1] && lat <= b[3]) ? 30 : 250;
  if (r.res?.colour_src_m) return r.res.colour_src_m;
  if ((LEGACY[name] || name) === 'bigisland') return 250;       // hawaii_bake.py: 48-day MODIS composite
  if ((LEGACY[name] || name) === 'hawaii_skirt') return 1000;
  const c = r.colour || {};
  if (r.dated && r.dated.focus) { const [fx, fy, rk] = r.dated.focus; if (Math.hypot((lon - fx) * 111.32 * Math.cos(fy * Math.PI / 180), (lat - fy) * 111.32) <= rk) return 30; }
  if (c.hls) { const b = c.hls.bbox; if (!b || (lon >= b[0] && lon <= b[2] && lat >= b[1] && lat <= b[3])) return 30; }
  if (c.modis) return 250;
  return 500;                                                     // Blue Marble NG
}
function inPoly(lon, lat, P) { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j];
  if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) c = !c; } return c; }
function hSrcM(name, lon, lat) {
  const r = IDX[LEGACY[name] || name] || {};
  for (const g of r.res?.height_interp || []) if (g.poly && inPoly(lon, lat, g.poly)) return g.src_m;
  if (r.res?.height_src_m) return r.res.height_src_m;
  if ((LEGACY[name] || name) === 'bigisland') return 70;
  if ((LEGACY[name] || name) === 'hawaii_skirt') return 900;
  let best = 1e9;
  for (const s of r.sources || []) { if (typeof s !== 'object') continue;
    if (s.res_m) best = Math.min(best, s.res_m); else if (s.res_arcsec && (s.cover ?? 1) > 0.05) best = Math.min(best, s.res_arcsec * 30.87); else if (s.px_m) best = Math.min(best, s.px_m); }
  return best < 1e9 ? best : r.px_m || 0;
}

// ---------- in-page measurement (runs in Chromium)
const PAGE_FN = `
window.__texMeasure = function (S, label) {
  const W = S.W, H = S.H, cam = S.cam, eye = cam.position.clone(), V = eye.constructor, KM = 111.32, RE = 6371, D2R = Math.PI / 180;
  const ground = (x, y, maxKm = 400) => {
    const d = new V(x / W * 2 - 1, 1 - y / H * 2, 0.5).unproject(cam).sub(eye).normalize();
    const at = (s) => { const px = eye.x + d.x * s, pz = eye.z + d.z * s, lat = S.c0.lat - pz / KM, lon = S.c0.lon + px / (KM * Math.cos(lat * D2R));
      const gh = Math.max(S.heightAt(lon, lat), S.level), gy = gh * S.vex * 0.001 - (d.x * d.x + d.z * d.z) * s * s / (2 * RE);
      return { above: eye.y + d.y * s - gy, lon, lat, gh }; };
    let s0 = 0, s1 = Math.max(0.002, (cam.near || 0.01) * 0.5);
    while (s1 < maxKm) { const b = at(s1); if (b.above <= 0) { for (let k = 0; k < 36; k++) { const m = (s0 + s1) / 2; if (at(m).above > 0) s0 = m; else s1 = m; } const r = at(s1); return [r.lon, r.lat, r.gh, s1]; }
      s0 = s1; s1 *= 1.05; }
    return null; };
  const layerAt = (lon, lat) => { const L = S.layers; for (let i = 0; i < L.length - 1; i++) { const b = L[i].bbox; if (lon > b[0] && lon < b[2] && lat > b[1] && lat < b[3]) return L[i]; } return L[L.length - 1]; };
  const one = (x, y) => {
    const g = ground(x, y); if (!g) return { x, y, sky: 1 };
    const [lon, lat, gh, dist] = g, l = layerAt(lon, lat), cl = Math.cos(lat * D2R), th = S.heightAt(lon, lat);
    const dm = 0.25, dlo = dm / (111320 * cl), dla = dm / 111320;
    const a = S.project(lon + dlo, lat), b = S.project(lon - dlo, lat), c = S.project(lon, lat + dla), d = S.project(lon, lat - dla);
    if (!a || !b || !c || !d) return { x, y, lon, lat, err: 'proj' };
    const e = [(a[0] - b[0]) / (2 * dm), (a[1] - b[1]) / (2 * dm)], n = [(c[0] - d[0]) / (2 * dm), (c[1] - d[1]) / (2 * dm)];
    const A = e[0] * e[0] + e[1] * e[1], B = e[0] * n[0] + e[1] * n[1], C = n[0] * n[0] + n[1] * n[1];
    const ppm = Math.sqrt((A + C) / 2 + Math.sqrt(((A - C) / 2) ** 2 + B * B));
    const bw = l.bbox[2] - l.bbox[0], bh = l.bbox[3] - l.bbox[1], im = l.col && l.col.image, cw = (im && im.width) || l.hm.W, ch = (im && im.height) || l.hm.H;
    const colM = Math.max(bw / cw * 111320 * cl, bh / ch * 111320), hM = Math.max(bw / l.hm.W * 111320 * cl, bh / l.hm.H * 111320);
    return { x, y, lon: +lon.toFixed(5), lat: +lat.toFixed(5), h: Math.round(th), water: S.level > th + 0.5 ? 1 : 0, layer: l.name, dist: +dist.toFixed(3), ppm, colM, hM };
  };
  const pts = { centre: one(W / 2, H / 2), lower: one(W / 2, H * 2 / 3), band: [] };
  if (!window.__texLight) for (const fy of [0.70, 0.80, 0.90]) for (const fx of [0.1, 0.3, 0.5, 0.7, 0.9]) pts.band.push(one(W * fx, H * fy));
  const camH = S.heightAt(S.cam.position.x / (KM * Math.cos(S.c0.lat * D2R)) + S.c0.lon, S.c0.lat - S.cam.position.z / KM);
  return { label, region: S.region || (S.meta && S.meta.name) || '?', stack: (S.meta && (S.meta.stack || ['bigisland', 'hawaii_skirt'])), level: S.level, fov: cam.fov,
    camAlt: +(eye.y / Math.max(S.vex, 1e-6)).toFixed(4), camAgl: +(eye.y / Math.max(S.vex, 1e-6) - Math.max(camH, S.level) * 0.001).toFixed(4), pts };
};
window.__texPatch = async function () {
  const Hs = await import('/lab/hawaii/hterrain.js'), G = await import('/lab/globe/cineglobe.js');
  window.__AUD = [];
  Hs.HawaiiStage.prototype.render = function (time) { try { window.__AUD.push(window.__texMeasure(this, 'film')); } catch (e) { window.__AUD.push({ err: String(e && e.message || e) }); } return this.R.domElement; };
  G.CineGlobe.prototype.render = function () { return null; };
};
window.__texViews = async function (list) {
  const Hs = await import('/lab/hawaii/hterrain.js'), idx = await (await fetch('/ep/ep02/data/regions.json')).json(), out = [];
  let R = null;
  for (const name of list) {
    const r = idx.regions[name]; if (!r || !r.view || !r.view.cam) continue;
    try {
      const S = new Hs.HawaiiStage(${W}, ${H}, R ? { renderer: R, samples: 0 } : { samples: 0 }); R = S.R;
      await S.loadRegion('/ep/ep02/data', name); S.region = name; S.setLevel(r.view.level ?? 0); S.setCamera(r.view.cam);
      out.push(window.__texMeasure(S, 'view'));
    } catch (e) { out.push({ label: 'view', region: name, err: String(e && e.message || e) }); }
  }
  return out;
};`;

// ---------- static server (as still.cjs) with the page log on stdout
function serve() {
  const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.css': 'text/css', '.geojson': 'application/json', '.webp': 'image/webp', '.svg': 'image/svg+xml' };
  const logs = [];
  const server = http.createServer((req, res) => {
    if (req.method === 'POST') { const ch = []; req.on('data', c => ch.push(c)); req.on('end', () => { logs.push(Buffer.concat(ch).toString()); res.end('ok'); }); return; }
    const u = decodeURIComponent(req.url.split('?')[0]); const p = path.join(WWW, u);
    if (!p.startsWith(WWW) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r({ server, logs, port: server.address().port })));
}

const segMid = (s) => (s.start + s.end) / 2;
async function runPage(browser, port, q, fn) {
  const p = await browser.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  try {
    await p.goto(`http://127.0.0.1:${port}/film.html?q=${encodeURIComponent(JSON.stringify(q))}&w=${W}&h=${H}&fps=${FPS}`);
    await p.waitForFunction(() => window.ready !== undefined, null, { timeout: 180000 }); await p.evaluate(() => window.ready);
    await p.evaluate(PAGE_FN);
    return await fn(p, errs);
  } finally { await p.close(); }
}

(async () => {
  const { server, logs, port } = await serve();
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const rows = [], views = [], notes = [];
  for (const n of CHAPTERS) {
    const t0 = Date.now();
    try {
      await runPage(browser, port, { ep: 'ep02', only: 'ch' + n }, async (p, errs) => {
        const scenes = await p.evaluate(() => window.SCENES);
        const own = scenes.filter(s => s.layer === 0 && s.id !== 'placeholder');
        if (!own.length) { notes.push(`ch${n}: no shots yet (placeholders only)`); return; }
        const a = Math.min(...own.map(s => s.t0)), b = Math.max(...own.map(s => s.t1));
        let segs = timing.segments.filter(s => segMid(s) >= a && segMid(s) < b);
        if (SEGS !== 'all') { const want = new Set(SEGS.split(',')); segs = segs.filter(s => want.has(s.id)); }
        await p.evaluate(() => window.__texPatch());
        const jobs = segs.map(s => ({ id: s.id, f: Math.round(segMid(s) * FPS) }));
        // every base shot gets at least one sample: a shot no segment middle falls in (a short gag) is sampled at its own middle
        if (SEGS === 'all') for (const sh of own) if (!jobs.some(j => j.f / FPS >= sh.t0 && j.f / FPS < sh.t1)) {
          const f = Math.round((sh.t0 + sh.t1) / 2 * FPS), sg = timing.segments.find(s => f / FPS >= s.start && f / FPS < s.end) || timing.segments.filter(s => s.start <= f / FPS).pop();
          jobs.push({ id: (sg ? sg.id : '') + '*', f }); }
        jobs.sort((x, y) => x.f - y.f);
        for (const s of jobs) {
          const f = s.f, t = f / FPS;
          const r = await p.evaluate(async (f) => { window.__AUD = []; await window.renderFrame(f); return window.__AUD; }, f);
          const act = scenes.filter(x => t >= x.t0 && t < x.t1 && x.id !== 'placeholder' && !x.id.startsWith('frame')).map(x => x.id);
          rows.push({ chapter: n, seg: s.id, frame: f, t: +t.toFixed(2), scenes: act, renders: dedupe(r) });
        }
        if (CLOSEST) {   // the worst (closest) frame of every base shot
          const grab = (f) => p.evaluate(async (f) => { window.__AUD = []; await window.renderFrame(f); return window.__AUD; }, f);
          for (const sh of own) {
            const f0 = Math.ceil(sh.t0 * FPS) + 1, f1 = Math.floor(sh.t1 * FPS) - 1; if (f1 < f0) continue;
            const fr = []; for (let f = f0; f <= f1; f += STEP) fr.push(f); if (fr[fr.length - 1] !== f1) fr.push(f1);
            let best = null; await p.evaluate(() => { window.__texLight = 1; });
            for (const f of fr) for (const x of await grab(f)) { enrich(x); const sc = score(x); if (sc > 0 && (!best || sc > best.sc)) best = { f, sc }; }
            await p.evaluate(() => { window.__texLight = 0; });
            if (!best) continue;
            const t = best.f / FPS, sg = timing.segments.find(s => t >= s.start && t < s.end) || timing.segments.filter(s => s.start <= t).pop();
            const act = scenes.filter(x => t >= x.t0 && t < x.t1 && x.id !== 'placeholder' && !x.id.startsWith('frame')).map(x => x.id);
            rows.push({ chapter: n, seg: (sg ? sg.id : '') + '^', closestOf: sh.id, frame: best.f, t: +t.toFixed(2), scenes: act, renders: dedupe(await grab(best.f)) });
          }
          rows.sort((x, y) => x.chapter - y.chapter || x.frame - y.frame);
        }
        const se = logs.filter(l => l.startsWith('SCENE-ERROR')); if (se.length) notes.push(`ch${n}: ${se.length} scene errors (first: ${se[0].slice(0, 160)})`);
        if (errs.length) notes.push(`ch${n}: ${errs.length} page errors (first: ${errs[0].slice(0, 160)})`);
      });
    } catch (e) { notes.push(`ch${n}: page failed: ${String(e.message || e).slice(0, 200)}`); }
    logs.length = 0;
    console.log(`ch${n}: ${rows.filter(r => r.chapter === n).length} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  if (VIEWS !== 'none') {
    const names = VIEWS === 'all' ? Object.keys(IDX).filter(k => IDX[k].view && IDX[k].view.cam) : VIEWS.split(',');
    try { views.push(...await runPage(browser, port, { ep: 'ep02', only: 'none' }, (p) => p.evaluate((l) => window.__texViews(l), names))); }
    catch (e) { notes.push('views: ' + String(e.message || e).slice(0, 200)); }
    console.log(`views: ${views.length}`);
  }
  await browser.close(); server.close();
  for (const r of rows) for (const x of r.renders) enrich(x);
  for (const x of views) enrich(x);
  const res = { tag: TAG, date: new Date().toISOString().slice(0, 16), size: [W, H], limits: LIM, notes, rows, views };
  if (OUT) fs.writeFileSync(OUT, JSON.stringify(res, null, 1));
  if (MD) fs.writeFileSync(MD, markdown(res));
  const fl = rows.filter(r => r.renders.some(x => x.flag)).length;
  console.log(`${rows.length} frames, ${rows.filter(r => r.renders.length).length} with terrain, ${fl} flagged; views ${views.length}, ${views.filter(v => v.flag).length} flagged` + (notes.length ? '\n' + notes.join('\n') : ''));
})().catch(e => { console.error(e); process.exit(1); });

function dedupe(r) { const seen = new Set(), out = []; for (const x of r) { const k = JSON.stringify([x.region, x.pts && x.pts.centre]); if (!seen.has(k)) { seen.add(k); out.push(x); } } return out; }
function enrich(x) {
  if (!x.pts) return;
  if (x.enriched) return; x.enriched = 1;
  const m = (p) => { if (!p || p.sky || p.err) return p; p.colSrcM = colSrcM(p.layer, p.lon, p.lat); p.colEffM = Math.max(p.colM, p.colSrcM); p.hSrcM = hSrcM(p.layer, p.lon, p.lat);
    p.colPx = +(p.ppm * p.colEffM).toFixed(2); p.colTexPx = +(p.ppm * p.colM).toFixed(2); p.hPx = +(p.ppm * p.hM).toFixed(2); p.hEffPx = +(p.ppm * Math.max(p.hM, p.hSrcM)).toFixed(2);
    // det: the detail texturing's strength there (hterrain.js kD: colour px 0.8-2, default detFar 6-16 km, pixel footprint under 16-28 m,
    // not 6-20 m under the water level); cres.png is not read, so where a patch photo was filled from its reference it is higher still
    const ss = (a, b, v) => { const t = Math.min(Math.max((v - a) / (b - a), 0), 1); return t * t * (3 - 2 * t); };
    p.det = +(ss(0.8, 2, p.colPx) * (1 - ss(6, 16, p.dist)) * (1 - ss(16, 28, 1 / p.ppm)) * (1 - ss(6, 20, (x.level ?? 0) - p.h))).toFixed(2);
    p.ppm = +p.ppm.toFixed(4); p.colM = +p.colM.toFixed(2); p.hM = +p.hM.toFixed(2); return p; };
  m(x.pts.centre); m(x.pts.lower); x.pts.band.forEach(m);
  const land = (p) => p && !p.sky && !p.err && !p.water, tex = (p) => land(p) && p.h > -6;   // below -6 m the stage draws its seabed, not the colour map
  const band = x.pts.band.filter(land);
  x.bandMax = band.length ? { colPx: Math.max(0, ...band.filter(tex).map(p => p.colPx)), hPx: Math.max(...band.map(p => p.hPx)) } : null;
  const why = []; let cov = 1;
  for (const k of ['centre', 'lower']) { const p = x.pts[k]; if (!land(p)) continue;
    const over = (tex(p) && p.colPx > LIM.col) || p.hPx > LIM.h; if (over) { p.over = 1; if (!(p.det >= 0.5)) cov = 0; }
    if (tex(p) && p.colPx > LIM.col) why.push(`${k} colour ${p.colPx} px`); if (p.hPx > LIM.h) why.push(`${k} height ${p.hPx} px`); }
  x.flag = why.length ? why.join(', ') : '';
  x.covered = !!(why.length && cov);   // every point over a limit has the detail texturing at half strength or more
}
function score(x) {   // how far over the limits the centre or lower third is (0 = no land there)
  if (!x.pts) return 0; let s = 0;
  for (const k of ['centre', 'lower']) { const p = x.pts[k]; if (!p || p.sky || p.err || p.water) continue;
    s = Math.max(s, p.hPx / LIM.h, p.h > -6 ? p.colPx / LIM.col : 0); }
  return s;
}
function cell(p) { if (!p) return '-'; if (p.sky) return 'sky'; if (p.err) return 'err'; if (p.water) return `water (${p.layer})`;
  return `${p.layer} ${p.dist < 1 ? Math.round(p.dist * 1000) + ' m' : p.dist.toFixed(1) + ' km'}: ${p.h > -6 ? '**' + p.colPx + '**' : 'seabed'} / ${p.hPx}` +
    (p.hEffPx > p.hPx * 1.2 ? ` (src ${p.hEffPx})` : '') + (p.over ? `, det ${p.det}` : ''); }
function markdown(res) {
  const L = [`# ep02 texel audit${res.tag ? ' (' + res.tag + ')' : ''}`, '',
    `${res.date}, ${res.size.join('x')}. Each cell: visible layer, distance from the camera, then **colour px** / height px = screen pixels covered by one colour texel (at its effective resolution: the texel or the imagery, whichever is coarser) and by one height texel, along the least foreshortened direction. Flag: colour > ${res.limits.col} px or height > ${res.limits.h} px at the centre or the lower third (y = 2/3); 'seabed' = ground below -6 m, where the stage draws its own seabed material instead of the colour map (only the height counts). A seg id with * = a shot no segment middle falls in, sampled at its own middle; with ^ = the closest (worst) frame of the shot named, scanned every few frames. 'src' = height px at the source's own resolution where the source is only interpolated. Band max = worst of 15 points over y 70-90 %. 'det' (points over a limit) = estimated strength of the detail texturing there, 0-1 (hterrain.js gate: colour px, the default detFar 6-16 km, footprint, depth under the water level; cres.png not read); flag 'FLAG det' = every point over a limit has det 0.5 or more, so the detail texturing carries it (the texel itself is still that big). Tool: engine/www/ep/ep02/tools/texel_audit.js.`, ''];
  if (res.notes.length) L.push('Notes: ' + res.notes.join('; '), '');
  const ter = res.rows.filter(r => r.renders.length);
  L.push(`## Film frames (one per segment, plus the closest frame of each shot): ${res.rows.length} sampled, ${ter.length} on terrain, ${ter.filter(r => r.renders.some(x => x.flag)).length} flagged, ${ter.filter(r => r.renders.some(x => x.flag) && r.renders.every(x => !x.flag || x.covered)).length} of them carried by the detail texturing`, '',
    '| seg | frame | time | shot | region | centre | lower third | band max col / h | flag |', '|---|---|---|---|---|---|---|---|---|');
  for (const r of ter) for (const x of r.renders) {
    if (!x.pts) { L.push(`| ${r.seg} | ${r.frame} | ${fmtT(r.t)} | ${r.scenes.join(', ')} | err | ${x.err || ''} | | | |`); continue; }
    L.push(`| ${r.seg} | ${r.frame} | ${fmtT(r.t)} | ${r.scenes.join(', ')} | ${x.region} | ${cell(x.pts.centre)} | ${cell(x.pts.lower)} | ${x.bandMax ? x.bandMax.colPx + ' / ' + x.bandMax.hPx : '-'} | ${x.flag ? (x.covered ? 'FLAG det' : 'FLAG') : ''} |`);
  }
  if (res.views.length) {
    L.push('', `## Region verification cameras (regions.json 'view'): ${res.views.length}, ${res.views.filter(v => v.flag).length} flagged`, '',
      '| region | cam agl km | centre | lower third | band max col / h | flag |', '|---|---|---|---|---|---|');
    for (const x of res.views) L.push(x.pts ? `| ${x.region} | ${x.camAgl} | ${cell(x.pts.centre)} | ${cell(x.pts.lower)} | ${x.bandMax ? x.bandMax.colPx + ' / ' + x.bandMax.hPx : '-'} | ${x.flag ? (x.covered ? 'FLAG det' : 'FLAG') : ''} |` : `| ${x.region} | err ${x.err} | | | | |`);
  }
  return L.join('\n') + '\n';
}
function fmtT(t) { const m = Math.floor(t / 60), s = t - m * 60; return `${m}:${s.toFixed(1).padStart(4, '0')}`; }
