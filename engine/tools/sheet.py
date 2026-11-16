# usage: python sheet.py DIR OUT.jpg [cols] [width]
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
tw = int(sys.argv[4]) if len(sys.argv) > 4 else 480
fs = sorted(glob.glob(os.path.join(d, 'f*.jpg')))
th = tw * 9 // 16
rows = (len(fs) + cols - 1) // cols
sh = Image.new('RGB', (cols * tw, rows * (th + 22)), (20, 20, 20))
dr = ImageDraw.Draw(sh)
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
except Exception: font = ImageFont.load_default()
for i, f in enumerate(fs):
    im = Image.open(f).resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 22)
    sh.paste(im, (x, y))
    fr = int(os.path.basename(f)[1:7]); t = fr / 30
    dr.text((x + 4, y + th + 3), f'f{fr} t={t:.2f} ({int(t//60)}:{t%60:05.2f})', fill=(255, 220, 80), font=font)
sh.save(out, quality=88)
print(out, len(fs))
