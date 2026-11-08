"""cells.py IMG_A IMG_B: per 16x9 cell and channel (L, a, b as PIL stores them), the mean squared feature difference to the drain clones (A)
and template farms (D) for both images; prints the cells where B lost the most distance vs A."""
import sys, numpy as np
sys.argv = sys.argv; exec(open(__file__.replace('cells.py', 'dist.py')).read().split("if __name__")[0])
def cellsq(p):
    f = feat(load(p)); out = {}
    for k, M in F.items(): out[k[0]] = ((M[:, :432] - f[:432]) ** 2).mean(0).reshape(9, 16, 3)
    return out, f[:432].reshape(9, 16, 3)
a, fa = cellsq(sys.argv[1]); b, fb = cellsq(sys.argv[2])
for k in 'AD':
    print(k, 'total sq', round(a[k].sum(), 1), '->', round(b[k].sum(), 1), ' per channel L,a,b:', a[k].sum((0, 1)).round(1), '->', b[k].sum((0, 1)).round(1))
    dd = (b[k] - a[k]).sum(-1)
    print(' rows (top..bottom) change:', dd.sum(1).round(1))
    print(' cols change:', dd.sum(0).round(1))
np.set_printoptions(linewidth=200)
print('image A a-channel (x255):'); print((fa[..., 1] * 255).astype(int))
print('image B a-channel (x255):'); print((fb[..., 1] * 255).astype(int))
print('image A b-channel (x255):'); print((fa[..., 2] * 255).astype(int))
print('image B b-channel (x255):'); print((fb[..., 2] * 255).astype(int))
