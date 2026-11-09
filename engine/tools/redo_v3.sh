#!/bin/bash
# redo_v3.sh "<chunk list>" MIX_WAV
# Re-render the listed 450-frame chunks with the current code (forward + reverse runner, 2 jobs each, cooperating through
# chunk locks), check every frame count, keep the replaced chunks in chunks/old_v2, swap the new ones in, concatenate,
# assemble the graded BT.709 master with MIX_WAV, then QC it and re-run the temporal glitch scan on it.
# Progress and results go to engine/redo_v3.log.
S=$SCRATCH
CD=$S/engine/chunks/ep01_1920x1080; RD=$S/engine/chunks/redo3; OLD=$S/engine/chunks/old_v2; LOG=$S/engine/redo_v3.log
LIST=$1; MIX=$2
mkdir -p $RD $OLD
echo "start $(date -u) chunks: $LIST" >> $LOG
cd $S/engine
$S/venv/bin/python $S/tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par 2 --only "$LIST" --dir $RD --out $RD/unused.mp4 > $S/engine/render_v3F.log 2>&1 &
sleep 40
$S/venv/bin/python $S/tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par 2 --only "$LIST" --reverse --dir $RD --out $RD/unused.mp4 > $S/engine/render_v3R.log 2>&1 &
wait
echo "render done $(date -u)" >> $LOG
python3 - "$LIST" "$CD" "$RD" "$OLD" >> $LOG 2>&1 <<'PY'
import os, subprocess, sys
lst = [int(x) for x in sys.argv[1].split(',') if x]; cd, rd, old = sys.argv[2:5]
def frames(p): return subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip()
miss = [i for i in lst if not os.path.exists(f'{rd}/c_{i:05d}.mp4')]
if miss: print('REDO MISSING', miss); sys.exit(1)
bad = [i for i in lst if frames(f'{rd}/c_{i:05d}.mp4') != ('179' if i == 67 else '450')]
if bad: print('BAD FRAMES', bad); sys.exit(1)
for i in lst:
    if not os.path.exists(f'{old}/c_{i:05d}.mp4'): os.replace(f'{cd}/c_{i:05d}.mp4', f'{old}/c_{i:05d}.mp4')
    os.replace(f'{rd}/c_{i:05d}.mp4', f'{cd}/c_{i:05d}.mp4')
bad = [i for i in range(68) if frames(f'{cd}/c_{i:05d}.mp4') != ('179' if i == 67 else '450')]
print('swapped', len(lst), 'chunks; bad main chunks:', bad); sys.exit(1 if bad else 0)
PY
[ $? -ne 0 ] && { echo "STOP: chunk check failed" >> $LOG; exit 1; }
( for i in $(seq 0 67); do echo "file '$CD/c_$(printf %05d $i).mp4'"; done ) > $CD/list_v3.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $CD/list_v3.txt -c copy $S/engine/video_full_v3.mp4 && echo "concat ok $(date -u)" >> $LOG
[ -f $S/deliver/ep01/video_final.mp4 ] && [ ! -f $S/deliver/ep01/video_final_v2.mp4 ] && mv $S/deliver/ep01/video_final.mp4 $S/deliver/ep01/video_final_v2.mp4
$S/tools/assemble.sh $S/engine/video_full_v3.mp4 $MIX $S/deliver/ep01/video_final.mp4 18 >> $LOG 2>&1 && echo "assemble ok $(date -u)" >> $LOG
$S/venv/bin/python $S/tools/qc_video.py $S/deliver/ep01/video_final.mp4 $S/research/qc_v3 --sheet 48 >> $LOG 2>&1; echo "qc exit $? $(date -u)" >> $LOG
$S/venv/bin/python $S/tools/temporal_scan.py $S/deliver/ep01/video_final.mp4 $S/review6/temporal_v3.json >> $LOG 2>&1; echo "scan exit $? $(date -u)" >> $LOG
echo "ALL DONE $(date -u)" >> $LOG
