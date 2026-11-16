const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const WWW = path.join(__dirname, 'www');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.woff2': 'font/woff2', '.css': 'text/css', '.geojson': 'application/json' };
const server = http.createServer((req, res) => {
  if (req.method === 'POST') { req.on('data', () => {}); req.on('end', () => res.end('ok')); return; }
  const p = path.join(WWW, decodeURIComponent(req.url.split('?')[0]));
  if (!fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto(`http://127.0.0.1:${server.address().port}/demo.html?w=1920&h=1080&fps=30`);
  await p.waitForFunction(() => window.ready !== undefined); await p.evaluate(() => window.ready);
  const r = await p.evaluate(async () => {
    const out = {};
    for (const f of [60, 200, 260]) {
      let t = performance.now(); await window.renderFrame(f); const b = await window.grabBlob(); out['f' + f] = Math.round(performance.now() - t);
    }
    // isolate post cost
    const c = document.querySelector('canvas'); const ctx = c.getContext('2d');
    const F = await import('./lib/fx.js');
    let t = performance.now(); for (let i = 0; i < 5; i++) F.post(ctx, 1920, 1080, i); await new Promise(r => c.toBlob(r, 'image/jpeg', 0.95)); out.post5 = Math.round(performance.now() - t);
    t = performance.now(); for (let i = 0; i < 5; i++) await new Promise(r => c.toBlob(r, 'image/jpeg', 0.95)); out.blob5 = Math.round(performance.now() - t);
    return out;
  });
  console.log(JSON.stringify(r)); await b.close(); server.close();
})();
