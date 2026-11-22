"""Arm 3 for ep02 (YOU ARE HERE pin on the old shore, mid-drain plate), rebuilt with design_middrain/work/compose.py
helpers but written to final_work/out2 so the tested design_middrain/cand_2.jpg stays untouched.
usage: python3 -I pin_arm.py NAME pin_r cap label_y tour_h [label_cx]"""
import sys, os
WK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_middrain/work'
OUT = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/final_work/out2'
sys.path.insert(0, WK); os.chdir(WK)
from compose import *
name, pin_r, cap, ly, tour_h = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
lcx = int(sys.argv[6]) if len(sys.argv) > 6 else 800
def cap_font(nm, cap_px):
    s = 20
    while True:
        f = font(nm, s); b = f.getbbox('H')
        if b[3] - b[1] >= cap_px: return f
        s += 1
dbg = 'dbgPL1c'; im = prep('PL1c', dbg, sky=True)
ys = LINES[dbg]['shore']; px = 800; py = ys[px]
Pn, tip = pin_layer(pin_r, (229, 50, 45))
T, feet = tourist_layer(tour_h)
tx = px + int(pin_r * 0.9)
im = put(im, T, (tx - feet[0], ys[tx] - feet[1] + 1), shadow=(1.5, (1, 1), 0.5))
im = put(im, Pn, (px - tip[0], py - tip[1]), shadow=(4, (3, 4), 0.45))
f = cap_font('BarlowCondensed-800', int(H * cap))
w = f.getlength('YOU ARE HERE')
im, capm = paste_text(im, 'YOU ARE HERE', f, (int(lcx - w / 2), ly), fill=(16, 30, 44, 255), halo=(255, 255, 255, 235), halo_w=8)
os.makedirs(OUT, exist_ok=True); p = f'{OUT}/{name}.jpg'; im.save(p, quality=92, optimize=True, progressive=True)
print(p, f'cap {capm}px = {capm / H:.1%}; pin r {pin_r} at x={px}, shore y={py}; label x {lcx - w / 2:.0f}-{lcx + w / 2:.0f}')
