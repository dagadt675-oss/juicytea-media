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
  for (const aa of ['0', '1']) {
    const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
    await p.goto(`http://127.0.0.1:${server.address().port}/globe_test2.html?w=1920&h=1080&fps=30&aa=${aa}`);
    await p.waitForFunction(() => window.ready !== undefined); await p.evaluate(() => window.ready);
    const r = await p.evaluate(async () => {
      const T = { renderGrabRaw: 0, renderJpeg: 0, postJpeg: 0, jpegKB: 0 }; const n = 8;
      for (let f = 0; f < n; f++) {
        let t = performance.now(); await window.renderFrame(f); window.grab(); T.renderGrabRaw += performance.now() - t;
        t = performance.now(); await window.renderFrame(f); const b = await window.grabJpeg(); T.renderJpeg += performance.now() - t;
        t = performance.now(); await fetch('/frame', { method: 'POST', body: b }); T.postJpeg += performance.now() - t; T.jpegKB += b.size / 1024;
      }
      for (const k in T) T[k] = (T[k] / n).toFixed(0); return T;
    });
    console.log('aa=' + aa, JSON.stringify(r)); await p.close();
  }
  await b.close(); server.close();
})();
