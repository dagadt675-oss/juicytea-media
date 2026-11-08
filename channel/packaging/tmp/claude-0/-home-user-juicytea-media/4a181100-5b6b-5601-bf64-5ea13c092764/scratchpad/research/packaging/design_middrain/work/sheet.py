import sys
from PIL import Image, ImageDraw, ImageFont
out=sys.argv[1]; files=sys.argv[2:]; cols=2; w=640; h=360
rows=(len(files)+cols-1)//cols
S=Image.new('RGB',(cols*w+(cols+1)*6,rows*(h+22)+6),(20,20,20)); d=ImageDraw.Draw(S)
for k,f in enumerate(files):
    im=Image.open(f).convert('RGB').resize((w,h)); x=6+(k%cols)*(w+6); y=6+(k//cols)*(h+22)
    S.paste(im,(x,y+16)); d.text((x,y),f.split('/')[-1],fill=(230,230,230))
S.save(out,quality=88)
