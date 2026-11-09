"""luma.py IMG...: mean luma (Rec.709), top/bottom half luma, near-black share (luma < 18), blown share (> 250), at 480x270."""
import sys, numpy as np
from PIL import Image
for p in sys.argv[1:]:
    a = np.asarray(Image.open(p).convert('RGB').resize((480, 270), Image.BOX)).astype(float)
    L = a @ [0.2126, 0.7152, 0.0722]
    print(f"{p.split('/')[-1]}: luma {L.mean():.1f}  top {L[:135].mean():.1f}  bottom {L[135:].mean():.1f}  nearblack {100*(L<18).mean():.1f}%  blown {100*(L>250).mean():.1f}%")
