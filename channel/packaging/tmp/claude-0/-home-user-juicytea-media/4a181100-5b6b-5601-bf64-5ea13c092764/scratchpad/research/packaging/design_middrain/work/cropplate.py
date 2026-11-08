import sys
from PIL import Image
src, dst, x0, y0, s = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
for pre, rs in (('r_', Image.LANCZOS), ('r_dbg', Image.NEAREST)):
    im = Image.open(f'{pre}{src}.jpg'); w, h = im.size
    c = im.crop((int(x0 * w), int(y0 * h), int((x0 + s) * w), int((y0 + s) * h))).resize((w, h), rs)
    c.save(f'{pre}{dst}.jpg', quality=95)
