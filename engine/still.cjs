#!/usr/bin/env node
// Render specific frames of a page to JPEG files: node still.cjs --page film.html --frames 0,90,300 --outdir stills [--w 1920 --h 1080] [--q '{}']
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const PAGE = opt('page', 'film.html'), W = +opt('w', 1920), H = +opt('h', 1080), FPS = +opt('fps', 30);
const OUTDIR = path.resolve(opt('outdir', 'stills')); const Q = opt('q', '{}');
const WWW = path.resolve(opt('www', path.join(__dirname, 'www')));
const frames = opt('frames', '0').split(',').map(Number);
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.css': 'text/css', '.geojson': 'application/json', '.webp': 'image/webp', '.svg': 'image/svg+xml' };
fs.mkdirSync(OUTDIR, { recursive: true });
const server = http.createServer((req, res) => {
  if (req.method === 'POST') { const ch = []; req.on('data', c => ch.push(c)); req.on('end', () => {
    const u = new URL(req.url, 'http://x'); if (u.pathname === '/log') { console.log('[page]', Buffer.concat(ch).toString()); res.end('ok'); return; }
    fs.writeFileSync(path.join(OUTDIR, u.searchParams.get('name')), Buffer.concat(ch)); res.end('ok'); }); return; }
  const u = decodeURIComponent(req.url.split('?')[0]); const p = path.join(WWW, u);
  if (!p.startsWith(WWW) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  p.on('console', m => { if (m.type() === 'error' || m.text().startsWith('[dbg]')) console.log('[console]', m.type(), m.text()); });
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto(`http://127.0.0.1:${server.address().port}/${PAGE}?q=${encodeURIComponent(Q)}&w=${W}&h=${H}&fps=${FPS}`);
  await p.waitForFunction(() => window.ready !== undefined, null, { timeout: 180000 }); await p.evaluate(() => window.ready);
  const t0 = Date.now();
  await p.evaluate(async (frames) => {
    for (const f of frames) { await window.renderFrame(f); const bl = await window.grabBlob(); await fetch('/save?name=' + 'f' + String(f).padStart(6, '0') + '.jpg', { method: 'POST', body: bl }); }
  }, frames);
  console.log(`saved ${frames.length} stills in ${((Date.now() - t0) / 1000).toFixed(1)} s -> ${OUTDIR}`);
  await b.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
