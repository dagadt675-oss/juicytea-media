"""sweep.py CFG.json BASE OUTDIR 'json-patch' ...: build variants of BASE with dict patches, print A/D (in-process copy of gate.py's feat) and colour metrics."""
import json, sys, copy, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as Bd
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist.py')).read().split("if __name__")[0])
def stats(im):
    hsv = np.asarray(im.resize((320, 180)).convert('HSV')).astype(float) / 255
    H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    return dict(tan=round(((H >= 15) & (H <= 50) & (S > 0.12) & (S < 0.55) & (V > 0.45)).mean() * 100, 1), red=round((((H < 15) | (H > 340)) & (S > 0.55) & (V > 0.45)).mean() * 100, 1),
                blue=round(((H >= 200) & (H < 250) & (S > 0.35)).mean() * 100, 1))
def deep(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep(a[k], v)
        else: a[k] = v
cfg = json.load(open(sys.argv[1])); base = cfg[sys.argv[2]]; out = sys.argv[3]; os.makedirs(out, exist_ok=True)
for i, patch in enumerate(sys.argv[4:]):
    c = copy.deepcopy(base); deep(c, json.loads(patch)); p = os.path.join(out, f's{i}.jpg')
    info = Bd.build(c, p); f = feat(load(p))
    A = np.mean(np.linalg.norm(F['A_drain_clones'] - f, axis=1)); D = np.mean(np.linalg.norm(F['D_template_farms'] - f, axis=1))
    st = stats(Image.open(p).convert('RGB'))
    ok = A >= 11.71 and D >= 11.43 and st['tan'] <= 10 and st['red'] <= 3 and st['blue'] <= 45
    print(f"s{i} A={A:.2f} D={D:.2f} {'OK ' if ok else 'no '} {st} luma={info['luma']} col={info['colorful']} c168={info['colorful168']} cap={info['cap_luma']}/{info['cap_chroma']} flank={info['flank_luma']} | {patch}")
