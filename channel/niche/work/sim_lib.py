import json,sys,numpy as np
from PIL import Image
B='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche'
g=json.load(open(B+'/work/groups.json'))
def load(p):
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(int); rows=np.where(a.max(axis=(1,2))>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6): im=im.crop((0,rows[0],im.width,rows[-1]+1))
    return im
def feat(im):
    s=np.asarray(im.resize((16,9),Image.BOX).convert('LAB')).astype(float).ravel()/255
    hsv=np.asarray(im.resize((160,90)).convert('HSV')).astype(float)/255
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]; m=S>0.25
    hh,_=np.histogram(H[m],bins=12,range=(0,360)); hh=hh/(m.size)
    return np.concatenate([s,hh*3])
def stats(im):
    hsv=np.asarray(im.resize((320,180)).convert('HSV')).astype(float)/255
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    return dict(tan=((H>=15)&(H<=50)&(S>0.12)&(S<0.55)&(V>0.45)).mean(),red=(((H<15)|(H>340))&(S>0.55)&(V>0.45)).mean(),
        blue=((H>=200)&(H<250)&(S>0.35)).mean(),cyan=((H>165)&(H<200)&(S>0.35)&(V>0.5)).mean(),white=((S<0.12)&(V>0.85)).mean(),
        brightsat=((V>0.6)&((S>0.45)|(V>0.85))).mean())
F={i:feat(load(f'{B}/refs/{i}.jpg')) for v in g.values() for i in v}
for p in sys.argv[1:]:
    im=load(p); f=feat(im); st=stats(im)
    dist={k:float(np.mean([np.linalg.norm(f-F[i]) for i in ids])) for k,ids in g.items()}
    ok=st['tan']<=.10 and st['red']<=.03 and st['blue']<=.45 and dist['A_drain_clones']>=11.0 and dist['D_template_farms']>=11.0
    print(p.split('/')[-1],'|',' '.join(f'{k}={100*v:.0f}%' for k,v in st.items()),'|',' '.join(f'{k[:6]}={v:.2f}' for k,v in sorted(dist.items(),key=lambda kv:kv[1])),'| GATE','PASS' if ok else 'FAIL')
