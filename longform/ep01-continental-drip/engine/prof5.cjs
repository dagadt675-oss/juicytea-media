const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const WWW = path.join(__dirname, 'www');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.css':'text/css', '.woff2':'font/woff2', '.geojson':'application/json' };
const server = http.createServer((req, res) => { const p = path.join(WWW, decodeURIComponent(req.url.split('?')[0])); if (!fs.existsSync(p)) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res); });
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto(`http://127.0.0.1:${server.address().port}/bench2d.html`);
  await p.waitForFunction(() => window.ready !== undefined); await p.evaluate(() => window.ready);
  console.log(JSON.stringify(await p.evaluate(() => window.bench()))); await b.close(); server.close();
})();
