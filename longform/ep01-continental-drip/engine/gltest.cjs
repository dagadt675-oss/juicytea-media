const { chromium } = require('playwright');
(async()=>{
const b = await chromium.launch({ args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
await p.setContent(`<canvas id=c width=1920 height=1080></canvas><script>
const gl=document.getElementById('c').getContext('webgl2');
window.info = gl ? gl.getParameter(gl.VERSION)+' | '+(gl.getExtension('WEBGL_debug_renderer_info')? gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL):'') : 'no webgl2';
</script>`);
console.log(await p.evaluate(() => window.info));
await b.close();})();
