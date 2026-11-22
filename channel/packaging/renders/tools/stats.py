# stats.py renders_dir : per 1920 render: mean luma, near-black %, sky / water / terrain shares, niche gate colour shares + verdict -> stats.json
import sys, json, glob, os, subprocess, numpy as np
from PIL import Image
R = sys.argv[1]; out = {}
G = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work/gate.py'
fs = sorted(glob.glob(R + '/ours_hawaii_*_1920.jpg'))
gate = subprocess.run(['python3', G] + fs, capture_output=True, text=True).stdout.strip().splitlines()
gl = {l.split(' |')[0].strip(): l for l in gate if '|' in l}
for f in fs:
    im = Image.open(f).convert('RGB').resize((480, 270), Image.BOX); a = np.asarray(im).astype(float) / 255
    l = a @ [0.2126, 0.7152, 0.0722]
    hsv = np.asarray(im.convert('HSV')).astype(float) / 255; H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    skyish = (a[..., 2] > a[..., 0] + 0.05) & (V > 0.55) & (S < 0.5)
    sky = np.zeros_like(skyish)
    for c in range(skyish.shape[1]):
        col = skyish[:, c]; n = np.argmin(col) if not col.all() else len(col); sky[:n, c] = True
    water = ~sky & (H > 170) & (H < 225) & (S > 0.35)
    name = os.path.basename(f)[len('ours_hawaii_'):-len('_1920.jpg')]
    g = gl.get(os.path.basename(f), '')
    out[name] = dict(luma=round(float(l.mean() * 255)), near_black=round(float((l < 18 / 255).mean() * 100), 1), sky=round(float(sky.mean() * 100)),
                     water=round(float(water.mean() * 100)), terrain=round(float((~sky & ~water).mean() * 100)),
                     gate=g.split('| GATE')[-1].strip() if g else '?', colours=g.split('|')[1].strip() if g else '', dist=g.split('|')[2].strip() if g else '')
json.dump(out, open(R + '/stats.json', 'w'), indent=1)
for k, v in out.items(): print(k, v)
