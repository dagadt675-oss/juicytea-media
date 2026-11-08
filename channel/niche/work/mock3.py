from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import numpy as np
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/proto_drain/'
O='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work/'
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FS='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
W,H=1280,720
dr=Image.open(P+'after_drained_1920.jpg').convert('RGB').resize((W,H))
full=Image.open(P+'after_full_1920.jpg').convert('RGB').resize((W,H))
# basalt grade: luminance only, dark, cool-neutral, with warm low-sun rim from left
L=np.asarray(dr.convert('L')).astype(float)/255
L=(L-L.min())/(L.max()-L.min()+1e-6)
contrast=np.clip((L-0.35)*1.9+0.35,0,1)**1.2
rim=np.linspace(1.0,0.55,W)[None,:]
base=np.stack([contrast*0.42*255*rim+18, contrast*0.40*255*rim+18, contrast*0.40*255*rim+22],-1)
# warm highlights on the brightest ridges (sunrise key)
hl=np.clip((contrast-0.6)/0.4,0,1)[...,None]*np.array([255,150,60])[None,None,:]*0.55*rim[...,None]
img=np.clip(base+hl,0,255).astype(np.uint8); g=Image.fromarray(img)
# sky: pale clear blue to white (top 20%)
sky=Image.new('RGB',(W,int(H*0.2))); sd=ImageDraw.Draw(sky)
for y in range(sky.height):
    k=y/sky.height; sd.line([(0,y),(W,y)],fill=(int(200+40*k),int(228+20*k),int(248+5*k)))
g.paste(sky,(0,0))
gd=ImageDraw.Draw(g)
for w,c in [(26,(30,120,140)),(14,(61,227,255)),(5,(220,255,255))]: gd.line([(0,int(H*0.2)),(W,int(H*0.2))],fill=c,width=w)
# postcard
cw,ch=500,330
card=Image.new('RGB',(cw,ch),(247,242,230))
photo=full.crop((260,40,260+1000,40+620)).resize((cw-32,ch-32)); card.paste(photo,(16,16))
cd=ImageDraw.Draw(card)
cd.text((30,24),'GREETINGS FROM',font=ImageFont.truetype(FB,26),fill=(255,255,255),stroke_width=4,stroke_fill=(15,15,15))
cd.text((26,160),'HAWAII',font=ImageFont.truetype(FS,104),fill=(255,210,63),stroke_width=6,stroke_fill=(25,15,5))
cd.rectangle([cw-96,20,cw-26,96],fill=(255,90,54),outline=(255,255,255),width=5); cd.ellipse([cw-80,36,cw-42,80],fill=(255,210,63))
m=Image.new('L',(cw,ch),255)
card=card.rotate(-4,expand=True,resample=Image.BICUBIC); m=m.rotate(-4,expand=True,resample=Image.BICUBIC)
g=g.convert('RGBA'); shadow=Image.new('RGBA',g.size,(0,0,0,0)); shadow.paste(Image.new('RGBA',card.size,(0,0,0,170)),(400+16,8+20),m); shadow=shadow.filter(ImageFilter.GaussianBlur(14))
g=Image.alpha_composite(g,shadow); g.paste(card,(400,8),m)
g.convert('RGB').save(O+'mock_M3_postcard_basalt.jpg',quality=90); print('ok')
