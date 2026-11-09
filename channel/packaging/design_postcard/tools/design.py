"""Build the four postcard-signature candidates. python3 design.py [ver]  -> work/<ver>/cand_<n>.jpg (+ metrics json)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card import *
D = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_postcard/'
VER = sys.argv[1] if len(sys.argv) > 1 else 'v1'
OUT = D + 'work/' + VER + '/'; os.makedirs(OUT, exist_ok=True)
NAME = 'HAWAI' + OKINA + 'I'
FW, FH = 1920, 1080            # compose space; final 1280x720 (x 2/3)
CAP = 0.125 * 720 * 1.5        # cap height of the place name, compose px (12.5% of frame height)


def lift(im, g=0.9):
    a = np.asarray(im).astype(np.float32) / 255
    return Image.fromarray((255 * a ** g).clip(0, 255).astype(np.uint8))


def terrain_mask(plate):
    """True where the plate is terrain or water (not sky): per column, sky = top run of bright, blue-ish pixels."""
    a = np.asarray(plate.convert('RGB')).astype(int)
    l = a @ [0.2126, 0.7152, 0.0722]
    sky = (a[..., 2] > a[..., 0] + 8) & (l > 150)
    m = np.ones(sky.shape, bool)
    for x in range(sky.shape[1]):
        col = sky[:, x]; k = np.argmax(~col) if (~col).any() else len(col)
        m[:k, x] = False
    return m


def basalt_share(plate, card_alpha_full):
    a = np.asarray(plate.convert('RGB')).astype(int)
    terr = terrain_mask(plate)
    hsv = np.asarray(plate.convert('HSV')).astype(float) / 255
    water = (hsv[..., 1] > 0.35) & (hsv[..., 2] > 0.45) & (hsv[..., 0] * 360 > 160) & (hsv[..., 0] * 360 < 250)
    green = (hsv[..., 0] * 360 > 60) & (hsv[..., 0] * 360 < 160) & (hsv[..., 1] > 0.25)
    covered = card_alpha_full > 128
    bas = terr & ~water & ~green & ~covered
    return float(bas.mean()), float((terr & water & ~covered).mean()), float(covered.mean())


def depth_grade(plate, top=1.12, bottom=0.62, cool=0.10, warm_top=0.06):
    """Light falls off with depth below the old shoreline: lift + warm the upper flank, darken + cool toward the frame bottom."""
    m = terrain_mask(plate)
    ys = np.array([np.argmax(m[:, x]) if m[:, x].any() else plate.height for x in range(plate.width)])
    ys = np.minimum.accumulate(np.minimum.accumulate(ys)[::-1])[::-1] * 0 + np.median(ys)
    a = np.asarray(plate).astype(np.float32); H = a.shape[0]
    yy = np.arange(H)[:, None].astype(np.float32)
    t = np.clip((yy - ys[None, :]) / (H - ys[None, :]), 0, 1)
    g = (top * (1 - t) + bottom * t) * m + (1 - m)
    a = a * g[..., None]
    a[..., 0] -= (cool * 255 * 0.25) * (t * m); a[..., 2] += (cool * 255 * 0.10) * (t * m)
    a[..., 0] += (warm_top * 255 * 0.3) * ((1 - t) ** 3 * m); a[..., 1] += (warm_top * 255 * 0.12) * ((1 - t) ** 3 * m)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def build(n, plate_path, face_path, card_w, cx, cy, angle, text=NAME, shadow=(-14, 16), blur=18, op=0.42,
          contact=0.0, contact_y=None, pgrade=None, face_kw=None, card_kw=None, depth=None, cap=None):
    CAPX = CAP if cap is None else cap * 720 * 1.5
    plate = Image.open(plate_path).convert('RGB')
    if plate.size != (FW, FH): plate = plate.resize((FW, FH), Image.LANCZOS)
    pg = dict(warm=0.5, con=1.06, sat=1.04, vig=0.18, vig_bottom=0.12, gamma=0.92)
    pg.update(pgrade or {})
    gam = pg.pop('gamma'); clar = pg.pop('clarity', 60)
    plate = grade(lift(plate, gam), **pg)
    if clar:
        sharp = plate.filter(ImageFilter.UnsharpMask(radius=6, percent=clar, threshold=3))
        mk = Image.fromarray((terrain_mask(plate) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(4))
        plate = Image.composite(sharp, plate, mk)
    if depth is not None: plate = depth_grade(plate, **depth)
    face = Image.open(face_path)
    fk = dict(face_fy=0.75, face_zoom=1.45, face_fx=0.5, face_sat=1.25, face_con=1.08); fk.update(face_kw or {})
    ck = dict(track=0.025); ck.update(card_kw or {})
    card = make_card(face, w=card_w, text=text, cap_px=CAPX if text else None, **fk, **ck)
    out, (x0, y0, rc) = place(plate, card, cx, cy, angle, shadow=shadow, blur=blur, opacity=op, contact=contact, contact_y=contact_y)
    full = np.zeros((FH, FW), np.uint8); cm = Image.new('L', (FW, FH), 0); cm.paste(rc.getchannel('A'), (x0, y0)); full = np.asarray(cm)
    bas, wat, cov = basalt_share(plate, full)
    t = save_thumb(out, OUT + f'cand_{n}.jpg')
    a = np.asarray(t).astype(float); l = a @ [0.2126, 0.7152, 0.0722]
    m = dict(cand=n, text=text or '', words=len(text.split()) if text else 0, cap_pct=round(100 * CAPX / FH, 1) if text else 0,
             card_w_pct=round(100 * rc.width / FW, 1), card_area_pct=round(100 * cov, 1), basalt_pct=round(100 * bas, 1),
             water_pct=round(100 * wat, 1), luma=round(l.mean(), 1), luma_bottom_half=round(l[360:].mean(), 1),
             p90=round(float(np.percentile(l, 90)), 1), kb=round(os.path.getsize(OUT + f'cand_{n}.jpg') / 1024))
    print(json.dumps(m)); return m


R = D + 'work/r/ours_r_'
M = []
DP = dict(top=1.3, bottom=0.55, cool=0.10, warm_top=0.10)
PG = dict(sat=1.10)
CK = dict(track=0.025, stamp_w=0.15)
SH = dict(shadow=(-22, 26), blur=24, op=0.6)
# 1 PLINTH (launch): card pinned at the old shoreline, left; the summit right; dark drained flank fills the frame below.
M.append(build(1, R + 'PL6.jpg', R + 'face1.jpg', card_w=720, cx=425, cy=312, angle=-3.5, depth=DP, cap=0.14, pgrade=PG, card_kw=CK, **SH))
# 2 WATERLINE: same camera half drained (-4,300 m): water still clings to the foot of the flank.
M.append(build(2, R + 'WL6.jpg', R + 'face1.jpg', card_w=720, cx=425, cy=312, angle=-3.5, depth=dict(DP, bottom=0.85), cap=0.14, pgrade=PG, card_kw=CK, **SH))
# 3 DROP: the card tumbling down the dark flank, well below the old shoreline.
M.append(build(3, R + 'PL6.jpg', R + 'face1.jpg', card_w=720, cx=610, cy=700, angle=-15, shadow=(-50, 56), blur=30, op=0.6, depth=DP, cap=0.14, pgrade=PG, card_kw=CK))
# 4 BLANK: no lettering; wider view, card standing on the old shoreline at left, the real summit at right.
M.append(build(4, R + 'x2.jpg', R + 'face1.jpg', card_w=610, cx=440, cy=240, angle=-3.5, text=None, contact=0.5, contact_y=446, depth=DP, pgrade=PG,
               card_kw=dict(CK, border=0.06), face_kw=dict(face_fy=0.7, face_zoom=1.3), shadow=(-16, 20), blur=20, op=0.45))
json.dump(M, open(OUT + 'metrics.json', 'w'), indent=1)
