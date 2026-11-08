import json,sys,numpy as np
from PIL import Image
A='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/anat'
P=A+'/..'; N=P+'/../niche'
exec(open(A+'/metrics_lib.py').read())
exec(open(N+'/work/sim_lib.py').read()) if False else None
# gate features (copied logic from niche/work/gate.py)
g=json.load(open(N+'/work/groups.json'))
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
def gstats(im):
    hsv=np.asarray(im.resize((320,180)).convert('HSV')).astype(float)/255
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    return dict(tan=((H>=15)&(H<=50)&(S>0.12)&(S<0.55)&(V>0.45)).mean(),red=(((H<15)|(H>340))&(S>0.55)&(V>0.45)).mean(),
        blue=((H>=200)&(H<250)&(S>0.35)).mean())
F={i:feat(load(f'{N}/refs/{i}.jpg')) for v in g.values() for i in v}
m=json.load(open(A+'/merged.json'))
for i,r in m.items():
    p=f'{P}/refs/thumbs/{i}.jpg'
    try:
        r['m']=metrics(p)
        im=load(p); f=feat(im); st=gstats(im)
        r['m'].update({k:round(100*v,1) for k,v in st.items()})
        for k in ('A_drain_clones','D_template_farms','F_craft_baseline'):
            r['m']['d_'+k[0]]=round(float(np.mean([np.linalg.norm(f-F[j]) for j in g[k] if j!=i])),2)
        r['m']['gate']=bool(st['tan']<=.10 and st['red']<=.03 and st['blue']<=.45 and r['m']['d_A']>=11 and r['m']['d_D']>=11)
    except Exception as e:
        print('ERR',i,e)
json.dump(m,open(A+'/merged.json','w'),indent=0)
print(json.dumps(next(iter(m.values()))['m']))
