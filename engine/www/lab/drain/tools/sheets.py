# sheets.py OUTDIR : phone versions, compare.jpg, sequence.jpg, luma metrics for the drain lab
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
O = sys.argv[1]
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f_big, f_mid, f_small = ImageFont.truetype(B, 30), ImageFont.truetype(B, 22), ImageFont.truetype(R, 18)
src = {'before': f'{O}/before/f000000.jpg', 'after_full': f'{O}/final/f000000.jpg', 'after_half': f'{O}/final/f000240.jpg', 'after_drained': f'{O}/final/f000450.jpg'}
im = {k: Image.open(v).convert('RGB') for k, v in src.items()}
ph = {}
for k, v in im.items():
    v.save(f'{O}/{k}_1920.jpg', quality=90); ph[k] = v.resize((390, 219), Image.LANCZOS); ph[k].save(f'{O}/{k}_phone390.jpg', quality=92)
def metrics(img):
    a = np.asarray(img.resize((96, 54), Image.BOX)).astype(float); l = a @ [0.2126, 0.7152, 0.0722]
    return l.mean(), (l < 18).mean() * 100
with open(f'{O}/metrics.txt', 'w') as fh:
    for k, v in im.items():
        m, b = metrics(v); fh.write(f'{k}: mean luma {m:.0f}/255, near-black {b:.1f}%\n')
print(open(f'{O}/metrics.txt').read())
BG = (14, 18, 26); TX = (244, 246, 250); SUB = (160, 172, 188); OR = (255, 120, 80)
def head(d, x, y, t, s, f=f_big, c=TX): d.text((x, y), t, font=f, fill=c); d.text((x, y + 38), s, font=f_small, fill=SUB)
# compare.jpg : left before, right after; row 1 full size (scaled 960), row 2 phone 390 px at 1:1 and 2x, row 3 the live drain on one camera
W = 1960; S = Image.new('RGB', (W, 1700), BG); d = ImageDraw.Draw(S)
d.text((20, 14), 'DRAIN / 3D TERRAIN HERO SHOT  -  Strait of Gibraltar, same place, same heading', font=f_big, fill=TX)
head(d, 20, 64, 'BEFORE: ep01 engine (globe.js), closest tilted regional camera + 500 m patch', 'flat textured sphere, blue bathymetry paint, no water surface, 34 px label (ep01 rule)', f_mid)
head(d, 1000, 64, 'AFTER: lab_drain.html, real ETOPO/SRTM terrain + seafloor mesh, live water', 'baked soft sun shadows + AO, height haze, curved horizon, HDR grade, phone-floor UI', f_mid, OR)
S.paste(im['before'].resize((960, 540), Image.LANCZOS), (20, 128)); S.paste(im['after_full'].resize((960, 540), Image.LANCZOS), (980, 128))
y2 = 690; d.text((20, y2), 'PHONE SIZE: 390 x 219 px (upright phone), shown 1:1 and 2x', font=f_mid, fill=TX)
for i, k in enumerate(['before', 'after_full']):
    x0 = 20 + i * 960
    S.paste(ph[k], (x0, y2 + 40)); S.paste(ph[k].resize((780, 438), Image.BILINEAR).crop((0, 0, 520, 438)), (x0 + 410, y2 + 40))
    d.text((x0, y2 + 268), '1:1', font=f_small, fill=SUB); d.text((x0 + 410, y2 + 484), '2x (left part)', font=f_small, fill=SUB)
y3 = 1220; d.text((20, y3), 'AFTER ONLY: one camera, sea level lowered live (0 m, -350 m where the strait closes, -1,100 m)', font=f_mid, fill=OR)
for i, k in enumerate(['after_full', 'after_half', 'after_drained']):
    S.paste(im[k].resize((632, 356), Image.LANCZOS), (20 + i * 643, y3 + 40))
d.text((20, y3 + 410), 'Before cannot show this at all: ep01 had no terrain mesh and no water level.', font=f_small, fill=SUB)
S.save(f'{O}/compare.jpg', quality=88)
# sequence.jpg : the three water levels, full size (scaled) + phone size
Q = Image.new('RGB', (1940, 940), BG); d = ImageDraw.Draw(Q)
d.text((20, 12), 'Water level sequence (same camera, pure function of time): full / half / drained', font=f_mid, fill=TX)
for i, (k, t) in enumerate([('after_full', '0 m (frame 0)'), ('after_half', '-350 m, strait dry (frame 240)'), ('after_drained', '-1,100 m (frame 450)')]):
    x = 20 + i * 640; Q.paste(im[k].resize((620, 349), Image.LANCZOS), (x, 50)); d.text((x, 405), t, font=f_small, fill=SUB)
    Q.paste(ph[k], (x, 440)); Q.paste(ph[k].resize((620, 348), Image.BILINEAR).crop((0, 0, 620, 260)), (x, 670))
d.text((20, 912), 'Row 2: phone 1:1.  Row 3: phone enlarged (top part).', font=f_small, fill=SUB)
Q.save(f'{O}/sequence.jpg', quality=88)
