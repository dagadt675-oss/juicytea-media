"""Final-step variants for the ep02 arms: reuse design_question/tools/compose.py (crop, masked grade, text),
plus a dawn sky grade (as in design_middrain grade_sky) and optional radial dodges, then text last.
usage: python3 -I finalize.py CFG.json OUTDIR"""
import json, os, sys
import numpy as np
from PIL import Image
PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
sys.path.insert(0, PK + '/design_question/tools')
import compose as C

def sky_grade(im, top, horizon, amt, gamma=1.6):
    a = np.asarray(im).astype(np.float32) / 255.0
    m = C.sky_mask(a).astype(np.float32)
    from PIL import ImageFilter
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
    rows = np.where(m.mean(1) > 0.5)[0]; hz = (rows.max() + 1) if len(rows) else C.H // 3
    t = np.clip(np.arange(C.H, dtype=np.float32) / max(hz, 1), 0, 1) ** gamma
    grad = (np.array(top, np.float32)[None, :] * (1 - t[:, None]) + np.array(horizon, np.float32)[None, :] * t[:, None]) / 255
    grad = np.repeat(grad[:, None, :], C.W, 1)
    # keep the render's own luminance texture, move its colour toward the gradient
    out = a * (1 - amt * m[..., None]) + grad * amt * m[..., None]
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))

def main():
    cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True); log = {}
    for name, c in cfg.items():
        im = C.crop_zoom(Image.open(c['plate']).convert('RGB'), *c.get('crop', [0.5, 0.5, 1.0]))
        mask = C.hero_mask(im, c) if (c.get('wet') or c.get('line_band')) else None
        im = C.grade(im, c.get('grade', {}), mask)
        if 'sky' in c: im = sky_grade(im, **c['sky'])
        for t in c.get('text', []): im, _ = C.draw_text(im, t)
        p = os.path.join(out, name + '.jpg'); im.save(p, quality=92, optimize=True, progressive=True)
        a = np.asarray(im).astype(np.float32); l = (a * [0.2126, 0.7152, 0.0722]).sum(-1)
        log[name] = dict(luma=round(float(l.mean()), 1), p90=round(float(np.percentile(l, 90)), 1), kb=os.path.getsize(p) // 1024)
        print(name, log[name])
    json.dump(log, open(os.path.join(out, 'finalize_log.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
