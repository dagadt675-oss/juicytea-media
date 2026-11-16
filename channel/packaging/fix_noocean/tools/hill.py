"""hill.py START.json OUTDIR N SEED [zoom_lo zoom_hi] [luma_floor]: hill-climb the grade knobs from START to raise colourfulness while the gate bar holds
(A >= 11.73, D >= 11.45, tan <= 10, red <= 3, blue <= 45; a small margin over 11.71 / 11.43) and mean luma stays >= luma_floor. Natural ranges are clamped."""
import json, sys, os, random, copy
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as Bd
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist.py')).read().split("if __name__")[0])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search.py')).read().split("def sample")[0].split("exec(open")[0].split("import build as Bd")[1]) if False else None
def stats(im):
    hsv = np.asarray(im.resize((320, 180)).convert('HSV')).astype(float) / 255
    H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    return dict(tan=float(((H >= 15) & (H <= 50) & (S > 0.12) & (S < 0.55) & (V > 0.45)).mean()) * 100, red=float((((H < 15) | (H > 340)) & (S > 0.55) & (V > 0.45)).mean()) * 100,
                blue=float(((H >= 200) & (H < 250) & (S > 0.35)).mean()) * 100)
# (path, lo, hi, sigma)
KN = [(('crop', 2), 1.18, 1.36, 0.02), (('crop', 1), 0.49, 0.53, 0.006), (('cap', 'pulls', 0, 2), 105, 135, 3), (('cap', 'pulls', 0, 3), 0.25, 0.7, 0.05),
      (('cap', 'pulls', 1, 2), 11, 18, 1), (('cap', 'pulls', 1, 3), 0.15, 0.6, 0.05), (('cap', 'vibrance'), 0.05, 0.45, 0.04), (('cap', 'smax'), 0.62, 0.8, 0.02),
      (('cap', 'exposure'), 1.0, 1.3, 0.03), (('cap', 'shadow_tint', 1), 0.2, 0.42, 0.02), (('cap', 'shadow_tint', 2), 0.0, 0.8, 0.08), (('cap', 'lc', 1), 0.15, 0.55, 0.05),
      (('flank', 'exposure'), 0.7, 0.95, 0.025), (('flank', 'sat'), 0.25, 0.65, 0.04), (('flank', 'warm', 0), 0.8, 0.94, 0.012), (('flank', 'warm', 2), 1.0, 1.1, 0.01),
      (('flank_burn', 2), 0.0, 0.55, 0.05), (('sky', 'exposure'), 1.0, 1.06, 0.01), (('sky_grad', 'amt'), 0.0, 0.75, 0.06)]
def get(c, p):
    for k in p: c = c[k]
    return c
def put(c, p, v):
    for k in p[:-1]: c = c[k]
    c[p[-1]] = v
def evaluate(c, tmp):
    info = Bd.build(c, tmp); f = feat(load(tmp)); st = stats(Image.open(tmp).convert('RGB'))
    A = float(np.mean(np.linalg.norm(F['A_drain_clones'] - f, axis=1))); D = float(np.mean(np.linalg.norm(F['D_template_farms'] - f, axis=1)))
    return A, D, st, info
start = json.load(open(sys.argv[1])); out = sys.argv[2]; N = int(sys.argv[3]); rng = random.Random(int(sys.argv[4]))
zlo, zhi = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (1.18, 1.36); lfloor = float(sys.argv[7]) if len(sys.argv) > 7 else 95
os.makedirs(out, exist_ok=True); tmp = os.path.join(out, '_tmp.jpg')
if 'sky_grad' not in start: start['sky_grad'] = {"top": [90, 145, 215], "amt": 0.0, "gamma": 1.6}
def score(A, D, st, info):
    ok = A >= 11.73 and D >= 11.45 and st['tan'] <= 10 and st['red'] <= 3 and st['blue'] <= 45 and info['luma'] >= lfloor
    return (info['colorful'] if ok else -100 + min(A - 11.73, 0) * 50 + min(D - 11.45, 0) * 50 + min(info['luma'] - lfloor, 0)), ok
cur = copy.deepcopy(start); A, D, st, info = evaluate(cur, tmp); best, ok = score(A, D, st, info)
print('start', round(A, 3), round(D, 3), ok, info['luma'], info['colorful'], flush=True)
with open(os.path.join(out, 'hill.jsonl'), 'a') as fo:
    for i in range(N):
        cand = copy.deepcopy(cur)
        for p, lo, hi, sg in rng.sample(KN, rng.randint(1, 4)):
            if p[0] == 'crop' and p[1] == 2: lo, hi = zlo, zhi
            v = float(np.clip(get(cand, p) + rng.gauss(0, sg), lo, hi)); put(cand, p, round(v, 3) if not isinstance(get(cand, p), int) else int(round(v)))
        A, D, st, info = evaluate(cand, tmp); s, ok = score(A, D, st, info)
        if s > best:
            best, cur = s, cand
            fo.write(json.dumps(dict(i=i, A=A, D=D, **st, luma=info['luma'], col=info['colorful'], c168=info['colorful168'], cap=info['cap_luma'], capC=info['cap_chroma'], flank=info['flank_luma'], cfg=cand)) + '\n'); fo.flush()
            print(i, 'NEW', round(A, 3), round(D, 3), ok, {k: round(v, 1) for k, v in st.items()}, 'luma', info['luma'], 'col', info['colorful'], 'cap', info['cap_luma'], info['cap_chroma'], flush=True)
json.dump(cur, open(os.path.join(out, 'best.json'), 'w'), indent=1)
