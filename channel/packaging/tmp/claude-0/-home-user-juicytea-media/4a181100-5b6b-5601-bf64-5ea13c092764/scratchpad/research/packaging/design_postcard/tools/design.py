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


def build(n, plate_path, face_path, card_w, cx, cy, angle, text=NAME, shadow=(-14, 16), blur=18, op=0.42,
          contact=0.0, contact_y=None, pgrade=None, face_kw=None, card_kw=None):
    plate = Image.open(plate_path).convert('RGB')
    if plate.size != (FW, FH): plate = plate.resize((FW, FH), Image.LANCZOS)
    pg = dict(warm=0.5, con=1.06, sat=1.04, vig=0.18, vig_bottom=0.12, gamma=0.92)
    pg.update(pgrade or {})
    gam = pg.pop('gamma'); clar = pg.pop('clarity', 60)
    plate = grade(lift(plate, gam), **pg)
    if clar: plate = plate.filter(ImageFilter.UnsharpMask(radius=10, percent=clar, threshold=2))
    face = Image.open(face_path)
    fk = dict(face_fy=0.62, face_zoom=1.25, face_fx=0.55); fk.update(face_kw or {})
    ck = dict(track=0.025); ck.update(card_kw or {})
    card = make_card(face, w=card_w, text=text, cap_px=CAP if text else None, **fk, **ck)
    out, (x0, y0, rc) = place(plate, card, cx, cy, angle, shadow=shadow, blur=blur, opacity=op, contact=contact, contact_y=contact_y)
    full = np.zeros((FH, FW), np.uint8); cm = Image.new('L', (FW, FH), 0); cm.paste(rc.getchannel('A'), (x0, y0)); full = np.asarray(cm)
    bas, wat, cov = basalt_share(plate, full)
    t = save_thumb(out, OUT + f'cand_{n}.jpg')
    a = np.asarray(t).astype(float); l = a @ [0.2126, 0.7152, 0.0722]
    m = dict(cand=n, text=text or '', words=len(text.split()) if text else 0, cap_pct=round(100 * CAP / FH, 1) if text else 0,
             card_w_pct=round(100 * rc.width / FW, 1), card_area_pct=round(100 * cov, 1), basalt_pct=round(100 * bas, 1),
             water_pct=round(100 * wat, 1), luma=round(l.mean(), 1), luma_bottom_half=round(l[360:].mean(), 1),
             p90=round(float(np.percentile(l, 90)), 1), kb=round(os.path.getsize(OUT + f'cand_{n}.jpg') / 1024))
    print(json.dumps(m)); return m


R = D + 'work/r/'
M = []
# 1 PLINTH (launch): card pinned at the old shoreline, left; the summit right; dark drained flank fills the frame below.
M.append(build(1, R + 'PL6.jpg', R + 'face1.jpg', card_w=660, cx=420, cy=300, angle=-3.5, shadow=(-18, 22), blur=20, op=0.5))
# 2 WATERLINE: same camera half drained (-4,300 m): water still clings to the foot of the flank.
M.append(build(2, R + 'WL6.jpg', R + 'face1.jpg', card_w=660, cx=420, cy=300, angle=-3.5, shadow=(-18, 22), blur=20, op=0.5))
# 3 DROP: the card tumbling down the dark flank, well below the old shoreline.
M.append(build(3, R + 'PL6.jpg', R + 'face1.jpg', card_w=660, cx=600, cy=690, angle=-15, shadow=(-50, 56), blur=30, op=0.55))
# 4 BLANK: no lettering; wider view, card standing on the old shoreline at left, the real summit at right.
M.append(build(4, R + 'x2.jpg', R + 'face1.jpg', card_w=620, cx=430, cy=245, angle=-3.5, text=None, contact=0.5, contact_y=452))
json.dump(M, open(OUT + 'metrics.json', 'w'), indent=1)
