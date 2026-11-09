#!/usr/bin/env python3
"""sb2sheet.py storyboard.mhtml out.jpg [duration_s]
Turns a yt-dlp storyboard (-f sb0, mhtml) into one contact-sheet JPEG (frames in order, each labelled mm:ss).
Use: yt-dlp -f sb0 -o 'sb_%(id)s.%(ext)s' URL ; python sb2sheet.py sb_ID.mhtml sheet_ID.jpg DURATION"""
import base64, email, io, sys
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
dur = float(sys.argv[3]) if len(sys.argv) > 3 else 0
msg = email.message_from_bytes(open(src, 'rb').read())
mosaics = []
for part in msg.walk():
    if part.get_content_type().startswith('image/'):
        mosaics.append(Image.open(io.BytesIO(part.get_payload(decode=True))).convert('RGB'))
frames = []
for m in mosaics:
    # storyboard mosaics are grids of equal tiles; sb0 is usually 160x90 tiles (or 5x5 of 160x90)
    tw, th = 160, 90
    if m.width % tw: tw = m.width // 5
    if m.height % th: th = m.height // 5
    for r in range(m.height // th):
        for c in range(m.width // tw):
            tile = m.crop((c*tw, r*th, (c+1)*tw, (r+1)*th))
            if tile.getextrema()[0][1] < 8: continue  # skip black padding tiles
            frames.append(tile)
n = len(frames)
cols = 10
rows = (n + cols - 1) // cols
tw, th = frames[0].size if frames else (160, 90)
sheet = Image.new('RGB', (cols*tw, rows*(th+14)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(frames):
    x, y = (i % cols)*tw, (i // cols)*(th+14)
    sheet.paste(f, (x, y))
    t = dur * i / max(1, n) if dur else i
    d.text((x+3, y+th+1), f'{int(t)//60:02d}:{int(t)%60:02d}', fill=(255, 255, 0))
sheet.save(out, quality=85)
print(out, n, 'frames', sheet.size)
