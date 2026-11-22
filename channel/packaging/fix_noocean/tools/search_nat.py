"""search.py OUTDIR N SEED: random search over the grade knobs (sensible ranges only); logs A, D, gate shares, luma, colourfulness to OUTDIR/search.jsonl."""
import json, sys, os, random
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as Bd
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist.py')).read().split("if __name__")[0])
R = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/fix_noocean/work/r/'
WET = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_question/work/r6/ours_P1_ridge_wet.jpg'
TXT = {"s": "NO OCEAN", "cap": 0.155, "x": 0.955, "y": 0.035, "anchor": "r", "fill": [16, 22, 30], "shadow": [255, 255, 255, 110], "shadow_off": [0, 0], "blur": 8}
def stats(im):
    hsv = np.asarray(im.resize((320, 180)).convert('HSV')).astype(float) / 255
    H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    return dict(tan=round(float(((H >= 15) & (H <= 50) & (S > 0.12) & (S < 0.55) & (V > 0.45)).mean()) * 100, 1), red=round(float((((H < 15) | (H > 340)) & (S > 0.55) & (V > 0.45)).mean()) * 100, 1),
                blue=round(float(((H >= 200) & (H < 250) & (S > 0.35)).mean()) * 100, 1))
def sample(rng):
    u = rng.uniform
    c = {"plate": R + rng.choice(['d1', 'd2', 'd3']) + '.jpg', "wet": WET,
            "crop": [0.47, round(u(0.49, 0.53), 3), round(u(1.18, 1.34), 3)],
            "cap": {"pulls": [[50, 100, round(u(105, 125)), round(u(0.3, 0.6), 2)], [5, 45, round(u(12, 17)), round(u(0.2, 0.5), 2)]],
                    "vibrance": round(u(0.1, 0.35), 2), "smax": round(u(0.65, 0.78), 2), "exposure": round(u(1.0, 1.25), 2),
                    "shadow_tint": [0.1, round(u(0.25, 0.4), 2), round(u(0.0, 0.7), 2), [0.88, 0.96, 1.2]], "lc": [12, round(u(0.2, 0.5), 2)]},
            "flank": {"exposure": round(u(0.72, 0.95), 2), "sat": round(u(0.3, 0.6), 2), "warm": [round(u(0.82, 0.92), 2), 1.0, round(u(1.0, 1.08), 2)]},
            "flank_burn": [round(u(0.5, 0.65), 2), 1.0, round(u(0.0, 0.5), 2)],
            "sky": {"exposure": round(u(1.0, 1.05), 3)}, "text": [TXT]}
    if rng.random() < 0.5: c["sky_grad"] = {"top": [round(u(70, 110)), round(u(130, 160)), round(u(200, 230))], "amt": round(u(0.3, 0.7), 2), "gamma": 1.6}
    return c
out = sys.argv[1]; n = int(sys.argv[2]); rng = random.Random(int(sys.argv[3])); os.makedirs(out, exist_ok=True)
tmp = os.path.join(out, '_tmp.jpg')
with open(os.path.join(out, 'search.jsonl'), 'a') as fo:
    for i in range(n):
        c = sample(rng); info = Bd.build(c, tmp); f = feat(load(tmp)); st = stats(Image.open(tmp).convert('RGB'))
        A = float(np.mean(np.linalg.norm(F['A_drain_clones'] - f, axis=1))); D = float(np.mean(np.linalg.norm(F['D_template_farms'] - f, axis=1)))
        rec = dict(A=round(A, 3), D=round(D, 3), **st, luma=info['luma'], col=info['colorful'], cap_luma=info['cap_luma'], cap_chroma=info['cap_chroma'], flank=info['flank_luma'], cfg=c)
        fo.write(json.dumps(rec) + '\n'); fo.flush()
        ok = A >= 11.71 and D >= 11.43 and st['tan'] <= 10 and st['red'] <= 3 and st['blue'] <= 45
        print(i, 'OK ' if ok else 'no ', round(A, 2), round(D, 2), st, info['luma'], info['colorful'], flush=True)
