#!/bin/bash
# vm_setup.sh : one-time setup of a Colab GPU VM for the Myth Juice film engine (headless Chromium + three.js on the NVIDIA GPU).
# Layout on the VM: /content/mj/engine/{render.cjs,www/,node_modules/}, /content/mj/tools/render_chunks.py, chunks -> /content/out.
# Run as root: bash /content/vm_setup.sh > /content/setup.log 2>&1. Idempotent.
set -u; cd /content
echo "== start $(date -u +%T)"
mkdir -p /content/mj/engine /content/mj/tools /content/out
# 1 assets (uploaded as /content/engine_www.tar) -> /content/mj/engine/www
if [ -f /content/engine_www.tar ] && [ ! -d /content/mj/engine/www ]; then
  tar -xf /content/engine_www.tar -C /content/mj/engine && echo "www unpacked: $(du -sh /content/mj/engine/www | cut -f1)"
fi
ls /content/mj/engine/render.cjs /content/mj/tools/render_chunks.py 2>&1
# 2 node + playwright (same version as the box: 1.63.0) + its Chromium build with system libraries
node --version; npm --version; python3 --version
cd /content/mj/engine && { [ -d node_modules/playwright ] || npm install --silent --no-audit --no-fund playwright@1.63.0; }
npx --yes playwright@1.63.0 install --with-deps chromium > /content/pw_install.log 2>&1 && echo "playwright chromium installed" || { echo "PLAYWRIGHT INSTALL FAILED"; tail -5 /content/pw_install.log; }
# 3 NVIDIA EGL for Chromium/ANGLE (the Colab image has the driver but no EGL vendor ICD registered)
mkdir -p /usr/share/glvnd/egl_vendor.d
cat > /usr/share/glvnd/egl_vendor.d/10_nvidia.json <<'J'
{"file_format_version":"1.0.0","ICD":{"library_path":"/usr/lib64-nvidia/libEGL_nvidia.so.0"}}
J
ls -la /usr/lib64-nvidia/libEGL_nvidia.so.0 2>/dev/null || { echo "libEGL_nvidia not at the expected path:"; ls /usr/lib64-nvidia 2>/dev/null | head -5; find / -name 'libEGL_nvidia.so*' 2>/dev/null | head -3; }
apt-get install -y -qq libegl1 libgl1 libgles2 ffmpeg > /dev/null 2>&1 || true
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1 | head -2
ffmpeg -version 2>/dev/null | head -1
# 4 WebGL renderer check: must say NVIDIA, otherwise Chromium fell back to software and a render would take hours
export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
cat > /content/mj/engine/glcheck.cjs <<'JS'
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--no-sandbox', '--use-gl=angle', '--use-angle=gl-egl', '--ignore-gpu-blocklist', '--enable-gpu', '--disable-gpu-vsync'] });
  const p = await b.newPage();
  const r = await p.evaluate(() => { const c = document.createElement('canvas'); const g = c.getContext('webgl2') || c.getContext('webgl'); if (!g) return 'no-webgl'; const e = g.getExtension('WEBGL_debug_renderer_info'); return String(e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER)); });
  console.log('WEBGL_RENDERER', r); await b.close();
})().catch(e => { console.log('GLCHECK_ERROR', e.message); process.exit(1); });
JS
cd /content/mj/engine && node glcheck.cjs
echo "== setup done $(date -u +%T)"
