import numpy as np, json, sys
from PIL import Image
def lines(dbg):
    a=np.array(Image.open(dbg).convert('RGB')).astype(int); H,W,_=a.shape
    R,G,B=a[...,0],a[...,1],a[...,2]
    land=(B<90)&(R>120)&(G>120)          # yellow: h>0
    water=(R<60)&(G>120)&(B>150)          # cyan water (dbg doesn't recolour water)
    ys=np.full(W,-1); yw=np.full(W,-1)
    for x in range(W):
        l=np.nonzero(land[:,x])[0]
        if len(l): ys[x]=l.max()
        w=np.nonzero(water[:,x])[0]
        if len(w): yw[x]=w.min()
    return ys,yw
if __name__=='__main__':
    out={}
    for n in sys.argv[1:]:
        ys,yw=lines(f'r_{n}.jpg'); out[n]={'shore':ys.tolist(),'water':yw.tolist()}
        print(n,'shore y at x=0,320,640,960,1279:',[int(ys[x]) for x in (0,320,640,960,1279)],' water:',[int(yw[x]) for x in (0,320,640,960,1279)])
    json.dump(out,open('lines.json','w'))
