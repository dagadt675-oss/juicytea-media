"""NO OCEAN chroma fix. usage: python3 -I build.py CFG.json OUTDIR [names...]
Per variant: crop the engine plate, split it into cap (land above today's sea level, from the wet render with the same camera),
sky and drained flank; give the cap chroma (vibrance, hue pull toward rainforest green and rust-red, local contrast),
make the flank darker and cooler, optionally strengthen the thin surf line on the old coast, then set the label."""
import json, os, sys, subprocess
import numpy as np
from PIL import Image, ImageFilter
PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
sys.path.insert(0, PK + '/design_question/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C
from metrics import m as metrics

def rgb2hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn; v = mx; s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; dd = np.maximum(d, 1e-6)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
    return np.where(d > 1e-6, h, 0), s, v

def hsv2rgb(h, s, v):
    h = (h % 360) / 60; i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.zeros(h.shape + (3,), np.float32)
    for k, (R, G, B) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        mk = i == k; out[mk, 0] = R[mk]; out[mk, 1] = G[mk]; out[mk, 2] = B[mk]
    return out

def pull(h, lo, hi, target, k):
    """move hues inside [lo, hi] toward target by fraction k, with soft edges (12 deg)."""
    w = np.clip((h - lo) / 12, 0, 1) * np.clip((hi - h) / 12, 0, 1)
    return h + (target - h) * k * w

def cap_grade(a, g):
    h, s, v = rgb2hsv(np.clip(a, 0, 1))
    for lo, hi, tgt, k in g.get('pulls', []): h = pull(h, lo, hi, tgt, k)
    vib = g.get('vibrance', 0); s = np.clip(s + vib * s * (1 - s) * 2, 0, 1)
    if 'sat' in g: s = np.clip(s * g['sat'], 0, 1)
    if 'smax' in g: s = np.minimum(s, g['smax'])
    out = hsv2rgb(h, s, v)
    if 'shadow_tint' in g:                         # sky-lit shadows go cool: [lum_lo, lum_hi, amount, [r, g, b]]
        lo, hi, amt, tint = g['shadow_tint']; l = (out * [0.2126, 0.7152, 0.0722]).sum(-1)
        w = (np.clip((hi - l) / max(hi - lo, 1e-3), 0, 1) * amt)[..., None]
        out = out * (1 - w) + out * np.array(tint, np.float32) * w
    if 'exposure' in g: out = out * g['exposure']
    if 'gamma' in g: out = np.clip(out, 0, 1) ** (1 / g['gamma'])
    return out

def local_contrast(a, radius, amt, mask):
    import scipy.ndimage as ndi
    l = (a * [0.2126, 0.7152, 0.0722]).sum(-1).astype(np.float32)
    lb = ndi.gaussian_filter(l, radius)
    k = np.clip(1 + amt * (l - lb) / np.maximum(l, 1e-3), 0.6, 1.6)
    return a * (1 + (k - 1) * mask[..., 0])[..., None]

def soft(mask_bool, blur):
    return np.asarray(Image.fromarray((mask_bool * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255

def build(c, outp):
    im = C.crop_zoom(Image.open(c['plate']).convert('RGB'), *c['crop'])
    a = np.asarray(im).astype(np.float32) / 255
    hero = C.hero_mask(im, c)                         # HxWx1, 0..1
    sky = soft(C.sky_mask(a), 2)[..., None] * (1 - hero)
    flank = np.clip(1 - hero - sky, 0, 1)
    capg = cap_grade(a.copy(), c.get('cap', {}))
    if c.get('cap', {}).get('lc'): capg = local_contrast(capg, *c['cap']['lc'], hero)
    fl = C.tone(a.copy(), c.get('flank', {}))
    if 'flank_burn' in c:                              # darken the flank more toward the bottom of the frame
        y0, y1, amt = c['flank_burn']; fl = fl * (1 - C.vgrad(y0, y1)[..., None] * amt)
    sk = C.tone(a.copy(), c.get('sky', {}))
    if 'flank_far' in c:                               # keep the render's own aerial haze on the far floor: the flank grade fades in below the horizon
        rows = np.where((sky[..., 0] > 0.5).mean(1) > 0.5)[0]; hz0 = (rows.max() + 1) if len(rows) else C.H // 4
        ff = c['flank_far']; t = np.clip((np.arange(C.H, dtype=np.float32) - hz0) / (ff[0] * C.H), 0, 1); t = t * t * (3 - 2 * t)
        keep = ff[1] if len(ff) > 1 else 1.0
        w = (keep * (1 - t))[:, None, None]
        fl = fl * (1 - w) + C.tone(a.copy(), c.get('flank_haze', {})) * w
    if 'sky_grad' in c:                                # deeper blue at the top of the sky, fading to the render's own pale horizon
        sg = c['sky_grad']; rows = np.where((sky[..., 0] > 0.5).mean(1) > 0.5)[0]; hz = (rows.max() + 1) if len(rows) else C.H // 4
        t = np.clip(np.arange(C.H, dtype=np.float32) / max(hz, 1), 0, 1) ** sg.get('gamma', 1.6)
        top = np.array(sg['top'], np.float32) / 255
        sk = sk * (1 - sg['amt'] * (1 - t)[:, None, None]) + top[None, None, :] * sg['amt'] * (1 - t)[:, None, None]
    if 'belt' in c:                                    # anti-solar glow low on the eastern (right) horizon: sun is in the west, camera looks north
        bt = c['belt']; rows = np.where((sky[..., 0] > 0.5).mean(1) > 0.5)[0]; hz = (rows.max() + 1) if len(rows) else C.H // 4
        t = np.clip(np.arange(C.H, dtype=np.float32) / max(hz, 1), 0, 1) ** bt.get('gamma', 3.0)
        xr = np.clip((np.arange(C.W, dtype=np.float32) / C.W - bt.get('x0', 0.2)) / (1 - bt.get('x0', 0.2)), 0, 1) ** 0.8
        w = (bt['amt'] * t[:, None] * xr[None, :])[..., None]
        col = np.array(bt['col'], np.float32) / 255
        sk = sk * (1 - w) + col * w
        if bt.get('floor'):                            # the same glow faintly on the far drained floor near the horizon
            yf = np.clip(1 - (np.arange(C.H, dtype=np.float32) - hz) / (bt.get('floor_h', 0.12) * C.H), 0, 1) * (np.arange(C.H) >= hz)
            wf = (bt['floor'] * yf[:, None] * xr[None, :])[..., None]
            fl = fl * (1 - wf) + fl * (col / col.mean()) * wf
    out = capg * hero + fl * flank + sk * sky
    if c.get('surf'):                                  # thin bright line on the old coast, outer edge of the cap mask
        sp = c['surf']; hb = hero[..., 0] > 0.5
        dil = np.asarray(Image.fromarray((hb * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(sp.get('w', 3)))) > 128
        edge = dil & ~hb
        ys = np.where(edge.any(1))[0]
        if sp.get('ymin'): edge[:int(sp['ymin'] * C.H)] = False   # keep the far shore (often blurred into haze) untouched
        core = soft(edge, sp.get('core_blur', 0.6))[..., None]; glow = soft(edge, sp.get('glow_blur', 4))[..., None]
        col = np.array(sp.get('col', [1, 1, 1]), np.float32)
        out = out * (1 - core * sp.get('core', 0.9)) + col * core * sp.get('core', 0.9)
        out = out + col * glow * sp.get('glow', 0.25)
    g = c.get('global', {})
    if 'contrast' in g: out = (out - 0.45) * g['contrast'] + 0.45
    if 'exposure' in g: out = out * g['exposure']
    res = Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
    texts = []
    for t in c.get('text', []): res, info = C.draw_text(res, t); texts.append(info)
    q = 92
    while True:
        res.save(outp, quality=q, optimize=True, progressive=True)
        if os.path.getsize(outp) < 1_900_000 or q <= 70: break
        q -= 4
    hm = hero[..., 0] > 0.5; fm = flank[..., 0] > 0.5
    r = np.asarray(res).astype(np.float32); l = (r * [0.2126, 0.7152, 0.0722]).sum(-1); ch = r.max(-1) - r.min(-1)
    info = metrics(outp)
    info.update(cap_luma=round(float(l[hm].mean()), 1), cap_chroma=round(float(ch[hm].mean()), 1), flank_luma=round(float(l[fm].mean()), 1),
                flank_chroma=round(float(ch[fm].mean()), 1), cap_share=round(float(hm.mean()), 3), kb=os.path.getsize(outp) // 1024,
                flank_bminusr=round(float((r[..., 2] - r[..., 0])[fm].mean()), 1), text=texts)
    return info

def gate(p):
    import re
    o = subprocess.run(['python3', '-I', 'gate.py', os.path.abspath(p)], cwd=PK + '/../niche/work', capture_output=True, text=True).stdout.strip()
    A = float(re.search(r'A_drai=([\d.]+)', o).group(1)); D = float(re.search(r'D_temp=([\d.]+)', o).group(1))
    st = o.split('|')[1].strip()
    return dict(A=A, D=D, stats=st, gate_py=o.split('GATE')[-1].strip(), bar='PASS' if (A >= 11.71 and D >= 11.43 and 'PASS' in o) else 'FAIL')

if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    names = sys.argv[3:] or [k for k in cfg if not k.startswith('_')]
    logp = os.path.join(out, 'build_log.json'); log = json.load(open(logp)) if os.path.exists(logp) else {}
    for n in names:
        p = os.path.join(out, n + '.jpg'); info = build(cfg[n], p); info['gate'] = gate(p); log[n] = info
        G = info['gate']; print(f"{n}: A={G['A']} D={G['D']} {G['bar']} | {G['stats']} | luma={info['luma']} p90={info['p90']} colorful={info['colorful']} c168={info['colorful168']} cap_luma={info['cap_luma']} cap_chroma={info['cap_chroma']} flank_luma={info['flank_luma']} flank_b-r={info['flank_bminusr']} cap_share={info['cap_share']} kb={info['kb']}")
    json.dump(log, open(logp, 'w'), indent=1)
