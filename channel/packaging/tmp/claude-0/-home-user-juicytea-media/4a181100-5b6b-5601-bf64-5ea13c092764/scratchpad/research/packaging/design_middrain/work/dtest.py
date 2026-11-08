import sys, json, numpy as np
sys.path.insert(0,'.')
from compose import *
exec(open('/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work/sim_lib.py').read().split('for p in sys.argv[1:]:')[0])
def dist(im):
    f=feat(im); return {k[:1]:round(float(np.mean([np.linalg.norm(f-F[i]) for i in ids])),3) for k,ids in g.items() if k[0] in 'AD'}
def water_grade(im, dbg, sat=1.0, bright=1.0, hue_shift=0):
    a=np.asarray(im).astype(np.float32); yw=np.array(LINES[dbg]['water'])
    m=np.zeros((H,W),np.float32)
    for x in range(W):
        if yw[x]>=0: m[yw[x]+2:,x]=1
    hsv=np.asarray(im.convert('HSV')).astype(np.float32)
    hsv[...,1]=np.where(m>0,hsv[...,1]*sat,hsv[...,1]).clip(0,255); hsv[...,2]=np.where(m>0,hsv[...,2]*bright,hsv[...,2]).clip(0,255)
    hsv[...,0]=np.where(m>0,(hsv[...,0]+hue_shift)%256,hsv[...,0])
    return Image.fromarray(hsv.astype(np.uint8),'HSV').convert('RGB')
if __name__=='__main__':
    base=Image.open(sys.argv[1]).convert('RGB'); dbg=sys.argv[2]
    print('base',dist(base))
    for kw in [dict(sat=0.8),dict(bright=0.85),dict(sat=0.85,bright=0.85),dict(hue_shift=6),dict(hue_shift=-6),dict(sat=1.15)]:
        print(kw,dist(water_grade(base,dbg,**kw)))
    print('warmsky',dist(grade_sky(base,dbg,top=(120,160,212),horizon=(250,200,150),amt=0.85)))
    print('crop top 8%',dist(base.crop((0,58,W,H)).resize((W,H))))
    print('crop bottom 8%',dist(base.crop((0,0,W,H-58)).resize((W,H))))
