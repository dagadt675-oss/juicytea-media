"""Dark-mode feed strip for the S6 test. Usage: python3 feedstrip.py OURS.jpg OUT.jpg
Places OURS among 9 live neighbours at phone-card (390x220) and compact (168x94) sizes."""
import sys,json,numpy as np
from PIL import Image,ImageDraw
B='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/refs/'
N=['YIXnHpSRGP4','ZWZWjXTnyEQ','GPxTR2vw_og','iGP2VsaRSQ4','Awve2w9DXgc','34Ojnyi9xLw','X5O7dd2A4QM','C4gj4cseiJw','4d5nTTiCai0']
def load(p):
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(int); rows=np.where(a.max(axis=(1,2))>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6): im=im.crop((0,rows[0],im.width,rows[-1]+1))
    return im
ours=sys.argv[1]; out=sys.argv[2]
ims=[load(B+i+'.jpg') for i in N]; ims.insert(4,load(ours))
bg=(15,15,15)
# compact column 168x94 (sidebar) x10 and phone cards 390x220 x 4 (around ours)
col=Image.new('RGB',(168+24,10*(94+10)+10),bg)
for k,im in enumerate(ims): col.paste(im.resize((168,94),Image.LANCZOS),(12,10+k*(104)))
ph=Image.new('RGB',(390+24,4*(220+14)+10),bg)
for k,im in enumerate(ims[3:7]): ph.paste(im.resize((390,220),Image.LANCZOS),(12,10+k*234))
S=Image.new('RGB',(col.width+ph.width+20,max(col.height,ph.height)),bg); S.paste(col,(0,0)); S.paste(ph,(col.width+20,0)); S.save(out,quality=90); print(out)
