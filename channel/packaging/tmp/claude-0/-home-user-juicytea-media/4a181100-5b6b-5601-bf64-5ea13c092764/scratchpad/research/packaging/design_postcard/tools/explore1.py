import sys, os
sys.argv = [sys.argv[0], 'x1']
exec(open(os.path.dirname(os.path.abspath(__file__)) + '/design.py').read().split("R = D + 'work/r/ours_r_'")[0])
R = D + 'work/r/ours_r_'
DP = dict(top=1.12, bottom=0.55, cool=0.10, warm_top=0.08)
V = [('a', 'PL6.jpg', dict(card_w=660, cx=420, cy=300, angle=-3.5), dict(DP, bottom=0.65)),
     ('b', 'PL6.jpg', dict(card_w=720, cx=440, cy=310, angle=-3.5), DP),
     ('c', 'PL6.jpg', dict(card_w=660, cx=420, cy=380, angle=-4.5), DP),
     ('d', 'PL4.jpg', dict(card_w=660, cx=1500, cy=300, angle=3.5), DP),
     ('e', 'PL6.jpg', dict(card_w=660, cx=420, cy=300, angle=-3.5), dict(DP, bottom=0.45, cool=0.18)),
     ('f', 'PL6.jpg', dict(card_w=660, cx=380, cy=300, angle=-3.5), dict(DP, top=1.25, bottom=0.6))]
for k, p, kw, dp in V:
    build('1' + k, R + p, R + 'face1.jpg', shadow=(-18, 22), blur=20, op=0.5, depth=dp, **kw)
