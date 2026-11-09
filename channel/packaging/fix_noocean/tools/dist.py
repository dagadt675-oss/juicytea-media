"""dist.py IMG [...]: A (drain clones) and D (template farms) mean feature distance, split into the LAB-grid part and the hue-histogram part
(same feat() as niche/work/sim_lib.py), plus the hue histogram of the image and the cluster means."""
import json, sys, numpy as np
from PIL import Image
B = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche'
g = json.load(open(B + '/work/groups.json'))
def load(p):
    im = Image.open(p).convert('RGB'); a = np.asarray(im).astype(int); rows = np.where(a.max(axis=(1, 2)) > 20)[0]
    if len(rows) and (rows[0] > 5 or rows[-1] < a.shape[0] - 6): im = im.crop((0, rows[0], im.width, rows[-1] + 1))
    return im
def feat(im):
    s = np.asarray(im.resize((16, 9), Image.BOX).convert('LAB')).astype(float).ravel() / 255
    hsv = np.asarray(im.resize((160, 90)).convert('HSV')).astype(float) / 255
    H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]; m = S > 0.25
    hh, _ = np.histogram(H[m], bins=12, range=(0, 360)); hh = hh / (m.size)
    return np.concatenate([s, hh * 3])
F = {k: np.array([feat(load(f'{B}/refs/{i}.jpg')) for i in ids]) for k, ids in g.items() if k[0] in 'AD'}
def d(p):
    f = feat(load(p)); out = {}
    for k, M in F.items():
        out[k[0]] = round(float(np.mean(np.linalg.norm(M - f, axis=1))), 2)
        out[k[0] + '_grid'] = round(float(np.mean(np.linalg.norm(M[:, :432] - f[:432], axis=1))), 2)
        out[k[0] + '_hue'] = round(float(np.mean(np.linalg.norm(M[:, 432:] - f[432:], axis=1))), 2)
    out['hue'] = [round(x, 2) for x in f[432:]]
    return out
if __name__ == '__main__':
    for k, M in F.items(): print(k, 'mean hue hist', [round(x, 2) for x in M[:, 432:].mean(0)])
    for p in sys.argv[1:]: print(p.split('/')[-1], d(p))
