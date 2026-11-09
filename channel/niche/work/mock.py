from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance,ImageOps
import numpy as np
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/visual/proto_drain/'
O='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work/'
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; FS='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
W,H=1280,720
half=Image.open(P+'after_half_1920.jpg').convert('RGB').resize((W,H))
dr=Image.open(P+'after_drained_1920.jpg').convert('RGB').resize((W,H))
full=Image.open(P+'after_full_1920.jpg').convert('RGB').resize((W,H))
# M1: clone-style "SEA LEVEL" (as currently planned): half-drained + black box + yellow dashed line
m1=half.copy(); d=ImageDraw.Draw(m1)
for x in range(0,W,40): d.line([(x,300),(x+24,300)],fill=(255,210,63),width=10)
f=ImageFont.truetype(FB,150); t='SEA LEVEL'; bb=d.textbbox((0,0),t,font=f)
d.rectangle([W-(bb[2]-bb[0])-80,140,W-20,140+(bb[3]-bb[1])+50],fill=(0,0,0)); d.text((W-(bb[2]-bb[0])-50,150),t,font=f,fill=(255,255,255))
m1.save(O+'mock_M1_sealevel_clonestyle.jpg',quality=90)
# M2: postcard signature: warm/dark graded terrain + off-white postcard card tilted, real-photo view inside, "GREETINGS FROM" + place
g=ImageEnhance.Color(dr).enhance(0.35); g=ImageEnhance.Brightness(g).enhance(0.62)
a=np.asarray(g).astype(float); a[...,0]*=1.18; a[...,1]*=1.02; a[...,2]*=0.80   # warm basalt grade (stand-in)
# golden rim light gradient from left
xs=np.linspace(1.35,0.85,W)[None,:,None]; a=np.clip(a*xs,0,255); g=Image.fromarray(a.astype(np.uint8))
# sky band top 22% pale dawn
sky=Image.new('RGB',(W,int(H*0.22)),(0,0,0)); sd=ImageDraw.Draw(sky)
for y in range(sky.height):
    k=y/sky.height; sd.line([(0,y),(W,y)],fill=(int(250-40*k),int(214-30*k),int(170-10*k)))
g.paste(sky,(0,0))
# cyan waterline glow under card
gd=ImageDraw.Draw(g); gd.line([(0,int(H*0.22)),(W,int(H*0.22))],fill=(61,227,255),width=8)
card_w,card_h=560,370
card=Image.new('RGB',(card_w,card_h),(246,240,226))
photo=full.crop((200,60,200+1020,60+600)).resize((card_w-36,card_h-36))
card.paste(photo,(18,18)); cd=ImageDraw.Draw(card)
f1=ImageFont.truetype(FB,30); f2=ImageFont.truetype(FS,120)
cd.text((34,26),'GREETINGS FROM',font=f1,fill=(255,255,255),stroke_width=4,stroke_fill=(20,20,20))
cd.text((30,190),'HAWAII',font=f2,fill=(255,210,63),stroke_width=6,stroke_fill=(30,20,10))
# stamp
cd.rectangle([card_w-110,22,card_w-30,112],fill=(255,90,54),outline=(255,255,255),width=5); cd.ellipse([card_w-92,40,card_w-48,94],fill=(255,210,63))
card=card.rotate(-4,expand=True,resample=Image.BICUBIC,fillcolor=(0,0,0,0))
mask=Image.new('L',card.size,0); md=ImageDraw.Draw(mask); 
base=Image.new('L',(card_w,card_h),255).rotate(-4,expand=True,resample=Image.BICUBIC); 
sh=Image.new('RGBA',card.size,(0,0,0,0)); 
g=g.convert('RGBA'); shadow=Image.new('RGBA',g.size,(0,0,0,0)); s2=Image.new('RGBA',card.size,(0,0,0,150)); shadow.paste(s2,(70+14,20+18),base); shadow=shadow.filter(ImageFilter.GaussianBlur(12))
g=Image.alpha_composite(g,shadow); g.paste(card,(70,20),base)
m2=g.convert('RGB'); m2.save(O+'mock_M2_postcard.jpg',quality=90)
print('ok')
