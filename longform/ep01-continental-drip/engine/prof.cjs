const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const WWW = path.join(__dirname, 'www');
const server = http.createServer((req, res) => {
  if (req.method === 'POST') { req.on('data', () => {}); req.on('end', () => res.end('ok')); return; }
  const p = path.join(WWW, decodeURIComponent(req.url.split('?')[0]));
  if (!fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': p.endsWith('.html') ? 'text/html' : p.endsWith('.js') ? 'text/javascript' : 'image/jpeg' });
  fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto(`http://127.0.0.1:${server.address().port}/globe_test.html?w=1920&h=1080&fps=30`);
  await p.waitForFunction(() => window.ready !== undefined); await p.evaluate(() => window.ready);
  const r = await p.evaluate(async () => {
    const T = { render: 0, grab: 0, post: 0 }; const n = 10;
    for (let f = 0; f < n; f++) {
      let t = performance.now(); await window.renderFrame(f); T.render += performance.now() - t;
      t = performance.now(); const px = window.grab(); T.grab += performance.now() - t;
      t = performance.now(); await fetch('/frame', { method: 'POST', body: px }); T.post += performance.now() - t;
    }
    for (const k in T) T[k] = (T[k] / n).toFixed(0); return T;
  });
  console.log(JSON.stringify(r)); await b.close(); server.close();
})();
