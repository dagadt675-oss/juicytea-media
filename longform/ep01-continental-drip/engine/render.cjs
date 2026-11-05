#!/usr/bin/env node
// Deterministic frame renderer. Serves ./www (or --www), loads a page exposing
//   window.ready (Promise), async window.renderFrame(f), async window.grabBlob() -> JPEG Blob
// and streams frames into ffmpeg (image2pipe mjpeg -> x264 intermediate).
// Parallel: --jobs J splits [start, start+frames) into J contiguous segments rendered by J browsers, then concatenates.
// Usage: node render.cjs --page film.html --fps 30 --start 0 --frames 900 --out out.mp4 [--jobs 3] [--w 1920 --h 1080] [--crf 12] [--q '{...}']
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
const { chromium } = require('playwright');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const PAGE = opt('page', 'film.html');
const FPS = +opt('fps', 30), START = +opt('start', 0), N = +opt('frames', 90);
const W = +opt('w', 1920), H = +opt('h', 1080), CRF = opt('crf', '12');
const OUT = path.resolve(opt('out', 'out.mp4'));
const Q = opt('q', '{}');
const WWW = path.resolve(opt('www', path.join(__dirname, 'www')));
const JOBS = Math.max(1, +opt('jobs', 1));
const PRESET = opt('preset', 'veryfast');

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.css': 'text/css', '.bin': 'application/octet-stream', '.geojson': 'application/json' };

function startServer(sinks) {
  const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url.startsWith('/frame')) {
      const job = +(new URL(req.url, 'http://x').searchParams.get('job') || 0);
      const chunks = []; let len = 0;
      req.on('data', c => { chunks.push(c); len += c.length; });
      req.on('end', () => {
        const buf = Buffer.concat(chunks, len);
        const ff = sinks[job];
        ff.count++;
        if (ff.proc.stdin.write(buf)) { res.writeHead(200); res.end('ok'); }
        else ff.proc.stdin.once('drain', () => { res.writeHead(200); res.end('ok'); });
      });
      return;
    }
    if (req.method === 'POST' && req.url.startsWith('/log')) {
      let s = ''; req.on('data', c => s += c); req.on('end', () => { console.log('[page]', s); res.end('ok'); }); return;
    }
    const u = decodeURIComponent(req.url.split('?')[0]);
    const p = path.join(WWW, u === '/' ? PAGE : u);
    if (!p.startsWith(WWW) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

function ffSink(out) {
  const proc = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', PRESET, '-crf', CRF, '-pix_fmt', 'yuv420p', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  return { proc, count: 0, done: new Promise(r => proc.on('close', r)) };
}

async function runJob(browser, port, job, start, n) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error' || m.text().startsWith('[dbg]')) console.log(`[j${job}]`, m.type(), m.text()); });
  page.on('pageerror', e => console.log(`[j${job} pageerror]`, e.message));
  const url = `http://127.0.0.1:${port}/${PAGE}?q=${encodeURIComponent(Q)}&w=${W}&h=${H}&fps=${FPS}`;
  await page.goto(url);
  await page.waitForFunction(() => window.ready !== undefined, null, { timeout: 180000 });
  await page.evaluate(() => window.ready);
  await page.evaluate(async ({ start, n, job }) => {
    for (let f = start; f < start + n; f++) {
      await window.renderFrame(f);
      const b = await window.grabBlob();
      const r = await fetch('/frame?job=' + job, { method: 'POST', body: b });
      if (!r.ok) throw new Error('frame post failed');
      if ((f - start) % 150 === 0) fetch('/log', { method: 'POST', body: `job ${job} frame ${f}` });
    }
  }, { start, n, job });
  await page.close();
}

(async () => {
  const t0 = Date.now();
  const segs = [];
  const per = Math.ceil(N / JOBS);
  for (let j = 0; j < JOBS; j++) { const s = START + j * per; const n = Math.min(per, START + N - s); if (n > 0) segs.push({ s, n, out: JOBS === 1 ? OUT : OUT.replace(/\.mp4$/, `.part${j}.mp4`) }); }
  const sinks = segs.map(sg => ffSink(sg.out));
  const server = await startServer(sinks);
  const port = server.address().port;
  const browsers = await Promise.all(segs.map(() => chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-vsync', '--js-flags=--max-old-space-size=4096'] })));
  await Promise.all(segs.map((sg, j) => runJob(browsers[j], port, j, sg.s, sg.n)));
  await Promise.all(browsers.map(b => b.close()));
  sinks.forEach(s => s.proc.stdin.end());
  await Promise.all(sinks.map(s => s.done));
  server.close();
  if (segs.length > 1) {
    const list = OUT + '.concat.txt';
    fs.writeFileSync(list, segs.map(sg => `file '${sg.out}'`).join('\n'));
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', OUT]);
    segs.forEach(sg => fs.unlinkSync(sg.out)); fs.unlinkSync(list);
  }
  const total = sinks.reduce((a, s) => a + s.count, 0);
  const dt = (Date.now() - t0) / 1000;
  console.log(`rendered ${total} frames in ${dt.toFixed(1)} s = ${(dt / Math.max(1, total) * 1000).toFixed(0)} ms/frame -> ${OUT}`);
})().catch(e => { console.error(e); process.exit(1); });
