import json,sys,numpy as np
from PIL import Image,ImageDraw,ImageFont
B='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche'
g=json.load(open(B+'/work/groups.json')); idx=json.load(open(B+'/work/idx.json'))
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
except: F=ImageFont.load_default()
def load(i):
    im=Image.open(f'{B}/refs/{i}.jpg').convert('RGB')
    a=np.asarray(im).astype(int); rows=np.where(a.max(axis=(1,2))>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6): im=im.crop((0,rows[0],im.width,rows[-1]+1))
    return im.resize((384,216),Image.LANCZOS)
def fmt(v):
    v=v or 0
    return f'{v/1e6:.1f}M' if v>=1e6 else f'{v/1e3:.0f}K' if v>=1e3 else str(v)
for name,ids in g.items():
    cols=4; W,H=384,216+40
    rows=(len(ids)+cols-1)//cols
    sh=Image.new('RGB',(cols*W,rows*H),(15,15,15)); d=ImageDraw.Draw(sh)
    for k,i in enumerate(ids):
        x,y=(k%cols)*W,(k//cols)*H
        sh.paste(load(i),(x,y))
        m=idx.get(i,{})
        d.text((x+4,y+218),f"{k+1}. {fmt(m.get('views'))} | {(m.get('channel') or '')[:22]} | {m.get('age') or ''}",fill=(255,230,120),font=F)
        d.text((x+4,y+234),(m.get('title') or '')[:52],fill=(230,230,230),font=F)
    sh.save(f'{B}/work/sheet_{name}.jpg',quality=85)
    print(name,sh.size)
