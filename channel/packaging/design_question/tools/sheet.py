import sys, os
from PIL import Image, ImageDraw
# usage: sheet.py out.jpg cols img1 img2 ...
out, cols = sys.argv[1], int(sys.argv[2]); ims = sys.argv[3:]
W, H = 480, 270; rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (cols * W, rows * (H + 18)), (15, 15, 15)); d = ImageDraw.Draw(sh)
for i, p in enumerate(ims):
    x, y = (i % cols) * W, (i // cols) * (H + 18)
    sh.paste(Image.open(p).convert('RGB').resize((W, H)), (x, y + 18)); d.text((x + 4, y + 3), os.path.basename(p), fill=(230, 230, 230))
sh.save(out, quality=82)
