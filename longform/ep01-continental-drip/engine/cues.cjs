#!/usr/bin/env node
// Dump sound cues + scene list from the film page: node cues.cjs --q '{"ep":"ep01"}' --out cues.json
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const argv = process.argv.slice(2); const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const Q = opt('q', '{}'), OUT = opt('out', 'cues.json'); const WWW = path.join(__dirname, 'www');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.css': 'text/css', '.geojson': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => { const u = decodeURIComponent(req.url.split('?')[0]); const p = path.join(WWW, u); if (req.method === 'POST') { let s = ''; req.on('data', c => s += c); req.on('end', () => { console.log('[page]', s); res.end('ok'); }); return; } if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res); });
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('[pageerror]', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('[console]', m.text()); });
  await p.goto(`http://127.0.0.1:${server.address().port}/film.html?q=${encodeURIComponent(Q)}&w=1920&h=1080&fps=30`);
  await p.waitForFunction(() => window.ready !== undefined, null, { timeout: 180000 }); await p.evaluate(() => window.ready);
  const r = await p.evaluate(() => ({ cues: window.CUES, scenes: window.SCENES }));
  fs.writeFileSync(OUT, JSON.stringify(r, null, 1)); console.log('cues', r.cues.length, 'scenes', r.scenes.length, '->', OUT);
  await b.close(); server.close();
})();
