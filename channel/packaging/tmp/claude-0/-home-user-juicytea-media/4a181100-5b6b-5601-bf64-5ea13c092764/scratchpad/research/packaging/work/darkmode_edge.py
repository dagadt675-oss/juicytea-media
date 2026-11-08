"""Dark-mode separation check: share of the outer border band (8% of each side) with luma < 35,
i.e. pixels that melt into YouTube's dark-mode page (#0F0F0F). Usage: python3 -I darkmode_edge.py img.jpg [...]
With --calibrate: prints the distribution over refs/thumbs split by anat/top_flags.json."""
import sys,json,glob,os,numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
def load(p):
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(int); rows=np.where(a.max(axis=(1,2))>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6): im=im.crop((0,rows[0],im.width,rows[-1]+1))
    return im.resize((320,180))
def edge_dark(p):
    a=np.asarray(load(p)).astype(float); L=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    by,bx=int(180*.08),int(320*.08); m=np.zeros(L.shape,bool); m[:by]=m[-by:]=True; m[:,:bx]=m[:,-bx:]=True
    return float((L[m]<35).mean()), float(L.mean())
if sys.argv[1:2]==['--calibrate']:
    fl=json.load(open(P+'/anat/top_flags.json')); r={True:[],False:[]}
    for i,t in fl.items():
        f=P+f'/refs/thumbs/{i}.jpg'
        if os.path.exists(f): r[t].append(edge_dark(f)[0])
    for t in (True,False):
        v=np.array(r[t]); print('top' if t else 'rest',len(v),'median %.2f p75 %.2f p90 %.2f share>0.5: %.0f%%'%(np.median(v),np.percentile(v,75),np.percentile(v,90),100*(v>0.5).mean()))
else:
    for p in sys.argv[1:]:
        e,l=edge_dark(p); print(os.path.basename(p),'edge_dark=%.2f mean_luma=%.0f'%(e,l),'PASS' if e<=0.5 else 'FAIL')
