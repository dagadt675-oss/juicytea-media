# sill.py etopo15.tif : level (m) at which the Atlantic seed and the Mediterranean seed stop being connected by water (h < level)
import sys, numpy as np
from collections import deque
from PIL import Image
h = np.asarray(Image.open(sys.argv[1])).astype(np.float32); H, W = h.shape; bb = [-9, 34, -1, 38]
def rc(lon, lat): return int((bb[3] - lat) / (bb[3] - bb[1]) * (H - 1)), int((lon - bb[0]) / (bb[2] - bb[0]) * (W - 1))
A, M = rc(-7.5, 35.8), rc(-4.0, 36.0)
def conn(L):
    wet = h < L; seen = np.zeros_like(wet); q = deque([A]); seen[A] = True
    while q:
        r, c = q.popleft()
        if (r, c) == M: return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and wet[rr, cc] and not seen[rr, cc]: seen[rr, cc] = True; q.append((rr, cc))
    return False
lo, hi = -1000.0, 0.0  # conn(hi) True, conn(lo) False
print('seeds depth', h[A], h[M], 'conn0', conn(0.0), 'conn-1000', conn(-1000.0))
while hi - lo > 1: mid = (lo + hi) / 2; (hi, lo) = (mid, lo) if conn(mid) else (hi, mid)
print('sill level ~ %.0f m (connected above, closed below)' % lo)
