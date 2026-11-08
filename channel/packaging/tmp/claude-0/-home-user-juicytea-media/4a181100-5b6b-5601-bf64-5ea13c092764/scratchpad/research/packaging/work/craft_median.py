"""Median feature distance of the craft baseline to the clone clusters (reference bar for the gate).
Uses the same features as niche/work/sim_lib.py. Leave-one-out within a group."""
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
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]; m=S>0.25
    hh,_=np.histogram(H[m],bins=12,range=(0,360)); hh=hh/(m.size)
    return np.concatenate([s,hh*3])
F={i:feat(load(f'{B}/refs/{i}.jpg')) for v in g.values() for i in v}
print('groups',{k:len(v) for k,v in g.items()})
for src in g:
    for tgt in ['A_drain_clones','D_template_farms']:
        d=[np.mean([np.linalg.norm(F[i]-F[j]) for j in g[tgt] if j!=i]) for i in g[src]]
        print(f'{src:22s} -> {tgt:18s} median {np.median(d):5.2f}  p25 {np.percentile(d,25):5.2f}  p75 {np.percentile(d,75):5.2f}')
