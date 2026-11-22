"""sheet.py OUT W IMG... : contact sheet, each image downscaled to W px wide (390 = the phone check), labelled with its file name."""
import sys
from PIL import Image, ImageDraw
out, w, ims = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
cols = int(sys.argv[2]) and (3 if w >= 600 else 4)
th = [Image.open(p).convert('RGB') for p in ims]; h = round(w * th[0].height / th[0].width)
rows = (len(th) + cols - 1) // cols; S = Image.new('RGB', (cols * (w + 6), rows * (h + 22)), (20, 20, 20)); d = ImageDraw.Draw(S)
for k, (p, im) in enumerate(zip(ims, th)):
    x, y = (k % cols) * (w + 6), (k // cols) * (h + 22); S.paste(im.resize((w, h), Image.LANCZOS), (x, y + 18)); d.text((x + 2, y + 2), p.split('/')[-1], fill=(230, 230, 230))
S.save(out, quality=90)
