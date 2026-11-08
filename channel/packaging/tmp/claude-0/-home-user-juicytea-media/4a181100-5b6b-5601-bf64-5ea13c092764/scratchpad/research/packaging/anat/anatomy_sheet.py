"""Contact sheet of the 15 exemplars: phone-card tiles (390x219) with captions, plus a compact-card strip (168x94) on YouTube dark-mode background."""
import json
from PIL import Image,ImageDraw,ImageFont
A='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/anat'
T=A+'/../refs/thumbs'; OUT=A+'/../refs/anatomy_sheet.jpg'
m=json.load(open(A+'/merged.json')); c={r['v']['code']:r for r in m.values()}; EX=json.load(open(A+'/exemplars.json'))
fb=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17); fr=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
fh=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26); fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',13)
BG=(15,15,15); W,H,G,CAP,C=390,219,14,58,5
def tile(i,w,h):
    im=Image.open(f'{T}/{i}.jpg').convert('RGB')
    if im.size[0]/im.size[1]<1.6:
        hh=int(im.size[0]*9/16); y=(im.size[1]-hh)//2; im=im.crop((0,y,im.size[0],y+hh))
    return im.resize((w,h),Image.LANCZOS)
def fmt(n):
    return f'{n/1e6:.1f}M' if n>=1e6 else (f'{n/1e3:.0f}K' if n>=1e3 else str(n))
rows=(len(EX)+C-1)//C
top_h=60; grid_h=rows*(H+CAP+G)+G
cw,ch,cg=168,94,10; strip_h=40+2*(ch+cg+18)+10
sheet=Image.new('RGB',(C*W+(C+1)*G, top_h+grid_h+strip_h),BG); d=ImageDraw.Draw(sheet)
d.text((G,14),'Thumbnail anatomy: 15 exemplars (top performers relative to channel size), 2026-11-08',fill=(240,240,240),font=fh)
for n,k in enumerate(EX):
    r=c[k]; x=G+(n%C)*(W+G); y=top_h+G+(n//C)*(H+CAP+G)
    sheet.paste(tile(r['id'],W,H),(x,y))
    d.rectangle((x,y,x+34,y+26),fill=(255,214,0)); d.text((x+5,y+3),str(n+1),fill=(0,0,0),font=fb)
    rel=f"{r['ratio']:.0f}x subs" if r['ratio']>=1 else f"{r['outlier']:.0f}x ch. median"
    d.text((x,y+H+5),f"{r['channel'][:16]}  {fmt(r['views'])} / {fmt(r['subs'])} subs ({rel})",fill=(235,235,235),font=fs)
    v=r['v']; d.text((x,y+H+24),f"{v['words']} words, text {v['txt_h']:.0f}% h, focal {v['focal']}, luma {r['m']['bright']:.0f}",fill=(170,170,170),font=fr)
y0=top_h+grid_h
d.text((G,y0+8),'Same 15 at compact-card size (168x94, YouTube dark mode #0F0F0F): what survives the squint',fill=(240,240,240),font=fb)
per=8
for n,k in enumerate(EX):
    r=c[k]; x=G+(n%per)*(cw+cg+70); y=y0+40+(n//per)*(ch+cg+18)
    sheet.paste(tile(r['id'],cw,ch),(x,y)); d.text((x+cw+6,y+2),str(n+1),fill=(255,214,0),font=fb)
sheet.save(OUT,quality=88); print(OUT,sheet.size)
