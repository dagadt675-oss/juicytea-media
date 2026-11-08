import json,numpy as np
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
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    m=S>0.25
    hh,_=np.histogram(H[m],bins=12,range=(0,360)); hh=hh/ (m.size)
    return np.concatenate([s, hh*3])
def stats(im):
    hsv=np.asarray(im.resize((320,180)).convert('HSV')).astype(float)/255
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    tan=((H>=15)&(H<=50)&(S>0.12)&(S<0.55)&(V>0.45)).mean()
    red=(((H<15)|(H>340))&(S>0.55)&(V>0.45)).mean()
    cyan=((H>165)&(H<200)&(S>0.35)&(V>0.5)).mean()
    blue=((H>=200)&(H<250)&(S>0.35)).mean()
    white=((S<0.12)&(V>0.85)).mean()
    black=(V<0.12).mean()
    yellow=((H>=45)&(H<65)&(S>0.55)&(V>0.6)).mean()
    green=((H>=70)&(H<160)&(S>0.25)&(V>0.25)).mean()
    return dict(bright=V.mean(),sat=S.mean(),tan=tan,red=red,cyan=cyan,blue=blue,white=white,black=black,yellow=yellow,green=green)
F={};ST={}
for k,ids in g.items():
    for i in ids:
        im=load(f'{B}/refs/{i}.jpg'); F[i]=feat(im); ST[i]=stats(im)
own={'ep01_B':'/home/user/juicytea-media/longform/ep01-continental-drip/release/thumb_B_pointing_at_what.jpg','ep01_A':'/home/user/juicytea-media/longform/ep01-continental-drip/release/thumb_A_cant_unsee_it.jpg'}
for k,p in own.items(): im=load(p); F[k]=feat(im); ST[k]=stats(im)
def d(a,b): return float(np.linalg.norm(F[a]-F[b]))
print('Within-group mean pairwise distance (lower = more alike):')
for k,ids in g.items():
    ds=[d(a,b) for x,a in enumerate(ids) for b in ids[x+1:]]
    print(f'  {k:22} n={len(ids):2} mean={np.mean(ds):.2f} median={np.median(ds):.2f}')
allids=[i for v in g.values() for i in v]
ds=[d(a,b) for x,a in enumerate(allids) for b in allids[x+1:]]
print(f'  ALL n={len(allids)} mean={np.mean(ds):.2f}')
# first-mover clones only (template thumbs)
cl=['ZWZWjXTnyEQ','grkuCssX_hI','cGdf7hBUd2A','GPxTR2vw_og','BUXMgKYyNLE','Jf8FZHuk4EU','PU28UaJ0Vg4','Exwm1PEM8GQ','rnJ_Xyo1Jz0','PN8J8YO99b4','hil1ohlY15U','LLba4kwJnjE','dUjgdkWErek','bSQn6TZ1bsQ','Gb3SMJb9h9Q','g3kKI35lMEM','fnOA_AQh4jI','X_cR9oz1Ew8']
ds=[d(a,b) for x,a in enumerate(cl) for b in cl[x+1:]]
print(f'  black-box drain template only n={len(cl)} mean={np.mean(ds):.2f}')
print('Group colour stats (mean % of pixels):')
for k,ids in g.items():
    keys=['bright','sat','tan','red','cyan','blue','white','black','yellow','green']
    print('  ',k.ljust(22),' '.join(f"{kk}={100*np.mean([ST[i][kk] for i in ids]):.0f}" for kk in keys))
for k in own: print('  ',k.ljust(22),' '.join(f"{kk}={100*ST[k][kk]:.0f}" for kk in ['bright','sat','tan','red','cyan','blue','white','black','yellow','green']))
print('Nearest group centroid for own thumbs (mean distance to group members):')
for k in own:
    print(' ',k, sorted([(round(np.mean([d(k,i) for i in ids]),2),gk) for gk,ids in g.items()]))
json.dump({k:v for k,v in ST.items()},open(B+'/work/colour_stats.json','w'))
