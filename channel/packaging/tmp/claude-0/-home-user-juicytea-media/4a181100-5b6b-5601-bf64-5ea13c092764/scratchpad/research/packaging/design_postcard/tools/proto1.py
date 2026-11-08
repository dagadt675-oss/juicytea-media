import sys
sys.path.insert(0, '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_postcard/tools')
from card import *
D = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_postcard/'
plate = Image.open(D + 'work/r/P1.jpg').convert('RGB')   # 1920x1080
plate = grade(plate, warm=0.6, con=1.08, sat=1.05, vig=0.25, vig_bottom=0.25)
face = Image.open(D + 'work/r/face1.jpg')
# frame is 1920x1080 here; final 1280x720 => factor 1.5. cap 13.5% of 720 = 97 px final = 146 px here
card = make_card(face, w=700, text='HAWAI' + OKINA + 'I', cap_px=146, face_fy=0.62, face_zoom=1.25, face_fx=0.55)
out, _ = place(plate, card, cx=430, cy=300, angle=4.5, shadow=(-16, 18), blur=18, opacity=0.5)
save_thumb(out, D + 'work/proto1.jpg')
