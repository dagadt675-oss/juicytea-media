#!/bin/bash
# qa_sheet.sh MODULE STEP_S OUTDIR  -> renders stills every STEP_S seconds across the module and builds labelled sheets
S=/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad
M=$1; STEP=$2; OUT=$3
cd $S/engine
FR=$(python3 -c "
import json
m=[x for x in json.load(open('www/ep/ep01/modules.json')) if x['id']=='$M'][0]
t=m['t0']+0.5; fr=[]
while t<m['t1']-0.2: fr.append(str(int(t*30))); t+=$STEP
print(','.join(fr))")
rm -rf $OUT; node still.cjs --page film.html --q "{\"ep\":\"ep01\",\"only\":\"$M\"}" --frames $FR --outdir $OUT 2>&1 | grep -E "saved|error|pageerror" | grep -v 404
$S/venv/bin/python - "$OUT" <<'PY'
import sys, glob
from PIL import Image, ImageDraw
out=sys.argv[1]; fs=sorted(glob.glob(out+'/f*.jpg'))
cols=6; per=36
for si in range(0,len(fs),per):
    chunk=fs[si:si+per]; rows=(len(chunk)+cols-1)//cols
    s=Image.new('RGB',(cols*320,rows*196),(15,15,15)); d=ImageDraw.Draw(s)
    for i,f in enumerate(chunk):
        im=Image.open(f).resize((320,180)); x,y=(i%cols)*320,(i//cols)*196; s.paste(im,(x,y))
        fr=int(f.split('/f')[-1][:-4]); t=fr/30; d.text((x+4,y+182),f'{int(t)//60}:{t%60:05.2f}',fill=(255,220,0))
    s.save(f'{out}/sheet_{si//per}.jpg',quality=82)
print('sheets', (len(fs)+per-1)//per)
PY
