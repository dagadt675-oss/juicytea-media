"""Extra contrast metrics (pop, compact-card contrast, bright island, centre-minus-edge). Run after metrics2.py."""
import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
A='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/anat'
T=A+'/../refs/thumbs'; m=json.load(open(A+'/merged.json'))
def load(p):
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(int); rows=np.where(a.max(axis=(1,2))>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6): im=im.crop((0,rows[0],im.width,rows[-1]+1))
    return im
for i,r in m.items():
    im=load(f'{T}/{i}.jpg').resize((320,180),Image.LANCZOS)
    a=np.asarray(im).astype(float)/255; L=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    med=np.median(L); r['m']['pop']=round(float((np.percentile(L,98)-med)*255),1)
    r['m']['sm_contrast']=round(float(np.asarray(im.resize((168,94),Image.LANCZOS).convert('L')).astype(float).std()),1)
    mask=L>min(0.95,med+0.3); lbl,n=ndi.label(mask)
    r['m']['bright_island']=round(float(ndi.sum(mask,lbl,range(1,n+1)).max()/L.size*100) if n else 0.0,1)
    h,w=L.shape; r['m']['centre_minus_edge']=round(float((L[h//4:3*h//4,w//4:3*w//4].mean()-np.concatenate([L[:h//6].ravel(),L[-h//6:].ravel()]).mean())*255),1)
json.dump(m,open(A+'/merged.json','w'),indent=0)
