import json, random
from PIL import Image, ImageDraw, ImageFont
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
ds=json.load(open(P+'/data/dataset.json'))
extra={'X5O7dd2A4QM','uKOYckUHWNk','cJn_2dwF1ug','ypSbAOKsjnk','iGP2VsaRSQ4','XrMGJPv8n1U','6Y-mnIvFxiA','ExXDVpDpgLk','tQqMyEJr0w4','DPY6_01_3UI','0XxZ7AO496k','t84VKEOdnQE','SNBWtEMiJf8','zGOHcPHskc4'}
sel=[r for r in ds if r.get('subs') or r['id'] in extra]
random.Random(7).shuffle(sel)
for n,r in enumerate(sel,1): r['code']=n
codes={r['id']:r['code'] for r in sel}
for r in ds: r['code']=codes.get(r['id'])
json.dump(ds,open(P+'/data/dataset.json','w'),indent=0)
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22)
except: font=ImageFont.load_default()
W,H=400,225; C,Rw=4,4
for s in range(0,len(sel),C*Rw):
    chunk=sel[s:s+C*Rw]
    sheet=Image.new('RGB',(C*W+(C+1)*6,Rw*H+(Rw+1)*6),(24,24,24))
    for k,r in enumerate(chunk):
        im=Image.open(P+'/refs/thumbs/%s.jpg'%r['id']).convert('RGB')
        if im.size[0]/im.size[1]<1.5:  # 4:3 hq with bars -> crop centre 16:9
            h=int(im.size[0]*9/16); y=(im.size[1]-h)//2; im=im.crop((0,y,im.size[0],y+h))
        im=im.resize((W,H),Image.LANCZOS)
        x=6+(k%C)*(W+6); y=6+(k//C)*(H+6); sheet.paste(im,(x,y))
        d=ImageDraw.Draw(sheet); d.rectangle((x,y,x+44,y+28),fill=(255,0,255)); d.text((x+4,y+2),str(r['code']),fill='white',font=font)
    sheet.save(P+'/refs/inspect_%02d.jpg'%(s//(C*Rw)+1),quality=85)
print(len(sel))
