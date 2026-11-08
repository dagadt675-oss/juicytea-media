import sys, json
sys.path.insert(0, '.')
from compose import *
CFG = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
def cap_font(name, cap_px):
    s = 20
    while True:
        f = font(name, s); b = f.getbbox('H')
        if b[3] - b[1] >= cap_px: return f
        s += 1
log = {}
def save(im, n, note):
    p = f'{D}/cand_{n}.jpg'; im.save(p, quality=92, optimize=True, progressive=True); log[n] = note; print('saved', p)

# 1: IT KEEPS GOING on the dark flank, ending at the waterline
c = CFG.get('c1', {})
im = prep(c.get('plate', 'plateT'), c.get('dbg', 'dbgT'), sky=c.get('sky', True))
cap = int(H * c.get('cap', 0.13))
f = cap_font(c.get('font', 'BarlowCondensed-800'), cap)
im, capm = paste_text(im, c.get('text', 'IT KEEPS\nGOING'), f, c.get('xy', (60, 300)), fill=(255, 255, 255, 255),
                      shadow=(0, 8, 16, 200), shadow_blur=10, shadow_off=(0, 4), spacing=c.get('spacing', 0))
save(im, 1, f'cap {capm}px = {capm/H:.1%}')

# 2: YOU ARE HERE pin on the old beach + tiny paper tourist
c = CFG.get('c2', {})
dbg = c.get('dbg', 'dbgT'); im = prep(c.get('plate', 'plateT'), dbg, sky=c.get('sky', True))
ys = LINES[dbg]['shore']; px = c.get('pin_x', 430); py = ys[px]
P, tip = pin_layer(c.get('pin_r', 30), tuple(c.get('pin_col', (229, 50, 45))))
T, feet = tourist_layer(c.get('tour_h', 22))
tx = px + c.get('tour_dx', 26)
im = put(im, T, (tx - feet[0], ys[tx] - feet[1] + 1), shadow=(1.5, (1, 1), 0.5))
im = put(im, P, (px - tip[0], py - tip[1]), shadow=(4, (3, 4), 0.45))
cap = int(H * c.get('cap', 0.12)); f = cap_font(c.get('font', 'BarlowCondensed-800'), cap)
style = c.get('style', 'map')
if style == 'map':
    kw = dict(fill=tuple(c.get('fill', (16, 30, 44, 255))), halo=(255, 255, 255, 235), halo_w=c.get('halo_w', 7))
else:
    kw = dict(fill=(255, 255, 255, 255), shadow=(0, 8, 16, 220), shadow_blur=10, shadow_off=(0, 4))
im, capm = paste_text(im, c.get('text', 'YOU ARE HERE'), f, c.get('xy', (60, 60)), **kw)
save(im, 2, f'cap {capm}px = {capm/H:.1%}; pin at x={px}, shore y={py}')

# 3: tilted HAWAIʻI postcard sinking at the new waterline
c = CFG.get('c3', {})
dbg = c.get('dbg', 'dbgT'); im = prep(c.get('plate', 'plateT'), dbg, sky=c.get('sky', True))
card = postcard(f"{WK}/r_{c.get('photo', 'pc2')}.jpg", w=c.get('card_w', 540), cap_px=int(H * c.get('cap', 0.12)), word_pos=c.get('word_pos', 'top'), stamp=c.get('stamp', True))
im = sink_card(im, card, tuple(c.get('center', (930, 545))), c.get('angle', 7), c.get('water_y', 640))
save(im, 3, f"card {c.get('card_w', 540)}px = {c.get('card_w', 540)/W:.0%} width")

# 4: the wall, no text, no anchor
c = CFG.get('c4', {})
im = prep(c.get('plate', 'plateW'), c.get('dbg', 'dbgW'), contrast=c.get('contrast', 1.08), sky=c.get('sky', True))
save(im, 4, 'no text')
json.dump(log, open(f'{WK}/make_log.json', 'w'), indent=1)
