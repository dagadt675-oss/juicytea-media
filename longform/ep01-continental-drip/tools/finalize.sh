#!/bin/bash
# finalize.sh "<redo chunk list>": after the redo batch, swap the re-rendered chunks in, concat, assemble with the final mix, QC.
S=$SCRATCH
CD=$S/engine/chunks/ep01_1920x1080; RD=$S/engine/chunks/redo; LOG=$S/engine/finalize.log
while pgrep -f "start_redo.sh" >/dev/null || pgrep -f "render_chunks.py.*chunks/redo" >/dev/null; do sleep 30; done
echo "redo done $(date -u)" >> $LOG
python3 - "$1" "$CD" "$RD" >> $LOG 2>&1 <<'PY'
import os, subprocess, sys
lst = [int(x) for x in sys.argv[1].split(',') if x]; cd, rd = sys.argv[2], sys.argv[3]
def frames(p): return subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip()
miss = [i for i in lst if not os.path.exists(f'{rd}/c_{i:05d}.mp4')]
if miss: print('REDO MISSING', miss); sys.exit(1)
for i in lst:
    n = '179' if i == 67 else '450'; f = frames(f'{rd}/c_{i:05d}.mp4')
    if f != n: print('BAD FRAMES', i, f); sys.exit(1)
for i in lst: os.replace(f'{rd}/c_{i:05d}.mp4', f'{cd}/c_{i:05d}.mp4')
bad = [i for i in range(68) if frames(f'{cd}/c_{i:05d}.mp4') != ('179' if i == 67 else '450')]
print('swapped', len(lst), 'chunks; bad main chunks:', bad); sys.exit(1 if bad else 0)
PY
[ $? -ne 0 ] && { echo "STOP: chunk check failed" >> $LOG; exit 1; }
( for i in $(seq 0 67); do echo "file '$CD/c_$(printf %05d $i).mp4'"; done ) > $CD/list_v2.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $CD/list_v2.txt -c copy $S/engine/video_full_v2.mp4 && echo "concat ok $(date -u)" >> $LOG
while [ ! -f $S/audio/mix_v2.wav ] || ! grep -q "mix exit 0" $S/audio/mix_v2.log 2>/dev/null; do sleep 20; done
nice -n 5 $S/tools/assemble.sh $S/engine/video_full_v2.mp4 $S/audio/mix_v2.wav $S/deliver/ep01/video_final.mp4 18 >> $LOG 2>&1 && echo "assemble ok $(date -u)" >> $LOG
nice -n 5 $S/venv/bin/python $S/tools/qc_video.py $S/deliver/ep01/video_final.mp4 $S/research/qc_final --sheet 48 >> $LOG 2>&1; echo "qc exit $? $(date -u)" >> $LOG
