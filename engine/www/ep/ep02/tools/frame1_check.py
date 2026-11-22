"""frame1_check.py OURS REF [--mask-label]: SSIM (gray, gaussian 1.5) at 320x180 + colour stats (luma, colourfulness, per-region)."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
def ssim(a, b):
    a = a.astype(np.float64); b = b.astype(np.float64); C1, C2 = (0.01*255)**2, (0.03*255)**2
    f = lambda x: ndimage.gaussian_filter(x, 1.5)
    ma, mb = f(a), f(b); va = f(a*a)-ma*ma; vb = f(b*b)-mb*mb; cov = f(a*b)-ma*mb
    return (((2*ma*mb+C1)*(2*cov+C2))/((ma*ma+mb*mb+C1)*(va+vb+C2)))
def colorful(a):
    rg = a[...,0]-a[...,1]; yb = 0.5*(a[...,0]+a[...,1])-a[...,2]
    return np.sqrt(rg.std()**2+yb.std()**2) + 0.3*np.sqrt(rg.mean()**2+yb.mean()**2)
o = Image.open(sys.argv[1]).convert('RGB').resize((320, 180), Image.LANCZOS); r = Image.open(sys.argv[2]).convert('RGB').resize((320, 180), Image.LANCZOS)
O = np.asarray(o).astype(float); R = np.asarray(r).astype(float)
S = ssim(np.asarray(o.convert('L')), np.asarray(r.convert('L')))
m = np.ones(S.shape, bool)
if '--mask-label' in sys.argv: m[:60, 140:] = False      # the NO OCEAN text block region (top right) excluded
lum = lambda A: (A*[0.2126,0.7152,0.0722]).sum(-1)
print(f'SSIM320={S[m].mean():.3f} (full {S.mean():.3f})  luma ours={lum(O).mean():.1f} ref={lum(R).mean():.1f}  colourful ours={colorful(O):.1f} ref={colorful(R):.1f}  MAE={np.abs(O-R)[m].mean():.1f}')
for name, ys in [('top third', slice(0, 60)), ('middle', slice(60, 120)), ('bottom', slice(120, 180))]:
    print(f'  {name}: ours rgb={O[ys].reshape(-1,3).mean(0).round(0)} ref rgb={R[ys].reshape(-1,3).mean(0).round(0)} ssim={S[ys].mean():.3f}')
