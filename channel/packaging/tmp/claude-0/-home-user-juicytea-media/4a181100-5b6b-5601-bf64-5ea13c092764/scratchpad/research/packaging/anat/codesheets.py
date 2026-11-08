"""Blind coding sheets: shuffled, numbered tiles at phone-card width (380px) with a 10% height ruler. No titles/views shown."""
import json,random
from PIL import Image,ImageDraw,ImageFont
A='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/anat'
T=A+'/../refs/thumbs'
m=json.load(open(A+'/merged.json'))
ids=sorted(m); random.Random(11).shuffle(ids)
codes={i:n+1 for n,i in enumerate(ids)}
json.dump(codes,open(A+'/blind_codes.json','w'))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
W,H,C,R,G=380,214,4,4,8
def tile(i):
    im=Image.open(f'{T}/{i}.jpg').convert('RGB')
    if im.size[0]/im.size[1]<1.6:
        h=int(im.size[0]*9/16); y=(im.size[1]-h)//2; im=im.crop((0,y,im.size[0],y+h))
    return im.resize((W,H),Image.LANCZOS)
for s in range(0,len(ids),C*R):
    ch=ids[s:s+C*R]
    sh=Image.new('RGB',(C*W+(C+1)*G+14,R*H+(R+1)*G),(30,30,30)); d=ImageDraw.Draw(sh)
    for k,i in enumerate(ch):
        x=G+14+(k%C)*(W+G); y=G+(k//C)*(H+G); sh.paste(tile(i),(x,y))
        for t in range(1,10):  # ruler ticks every 10% of height, left of tile
            yy=y+int(H*t/10); d.line((x-12,yy,x-2,yy),fill=(255,255,0) if t%5==0 else (170,170,170),width=2)
        d.rectangle((x,y,x+40,y+22),fill=(255,0,255)); d.text((x+3,y+1),str(codes[i]),fill='white',font=font)
    sh.save(f'{A}/code_{s//(C*R)+1:02d}.jpg',quality=88)
print(len(ids),'tiles', (len(ids)+15)//16,'sheets')
