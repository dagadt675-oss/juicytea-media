#!/bin/bash
# finalize_v3.sh: after the round-6 re-render, build the tightened v3 master and the upload copy, then QC it.
#  1 wait for every chunk runner; 2 check the redo set (450 frames each, 179 for chunk 67); 3 swap it in (old chunks kept in
#  chunks/old_v2); 4 concat; 5 edl.py (cuts + move) on mix_v3; 6 mix; 7 captions; 8 graded master; 9 QC + glitch re-scan;
#  10 upload copy under 500 MiB (2-pass from the master, audio copied). Log: engine/finalize_v3.log
S=$SCRATCH
CD=$S/engine/chunks/ep01_1920x1080; RD=$S/engine/chunks/redo3; OLD=$S/engine/chunks/old_v2; LOG=$S/engine/finalize_v3.log
E=$S/review6/edl_v3; D=$S/deliver/ep01; PY=$S/venv/bin/python
SET="0,1,2,3,4,9,10,11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28,29,30,31,$(seq -s, 33 67)"
log() { echo "$(date -u +%T) $*" >> $LOG; }
log "waiting for chunk runners"
while pgrep -f "render_chunks.py" >/dev/null; do sleep 30; done
log "runners done"
python3 - "$SET" "$CD" "$RD" "$OLD" >> $LOG 2>&1 <<'PYEOF'
import os, subprocess, sys
lst = [int(x) for x in sys.argv[1].split(',') if x]; cd, rd, old = sys.argv[2:5]
os.makedirs(old, exist_ok=True)
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
PYEOF
[ $? -ne 0 ] && { log "STOP: chunk check failed"; exit 1; }
( for i in $(seq 0 67); do echo "file '$CD/c_$(printf %05d $i).mp4'"; done ) > $CD/list_v3.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $CD/list_v3.txt -c copy $S/engine/video_full_v3.mp4 && log "concat ok" || { log "STOP: concat failed"; exit 1; }
$PY $S/tools/edl.py $S/review6/edl_v3/edl.json $E --mix $S/audio/mix_v3.json >> $LOG 2>&1 && log "edl ok" || { log "STOP: edl failed"; exit 1; }
$PY $S/tools/mix.py $E/mix_cut.json $E/mix_cut.wav >> $LOG 2>&1 && log "mix ok" || { log "STOP: mix failed"; exit 1; }
python3 $S/tools/make_srt.py $E/timing_cut.json $E/captions_en.srt >> $LOG 2>&1 && log "captions ok"
[ -f $D/video_final.mp4 ] && [ ! -f $D/video_final_v2.mp4 ] && mv $D/video_final.mp4 $D/video_final_v2.mp4
$PY $S/tools/assemble_edl.py $S/engine/video_full_v3.mp4 $E/ranges.json $E/mix_cut.wav $D/video_final.mp4 18 >> $LOG 2>&1 && log "master ok" || { log "STOP: master failed"; exit 1; }
# upload copy (needs only the master) in parallel with the checks
( cd $D && ffmpeg -y -loglevel error -i video_final.mp4 -map 0:v -c:v libx264 -preset slow -b:v 3900k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 \
    -x264-params aq-mode=3 -pass 1 -passlogfile x264v3 -an -f null /dev/null && \
  ffmpeg -y -loglevel error -i video_final.mp4 -map 0:v -map 0:a -c:v libx264 -preset slow -b:v 3900k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 \
    -x264-params aq-mode=3 -pass 2 -passlogfile x264v3 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a copy -movflags +faststart myth_juice_ep01_upload.mp4 && \
  rm -f x264v3* && echo "$(date -u +%T) upload ok $(stat -c %s myth_juice_ep01_upload.mp4) bytes" >> $LOG || echo "$(date -u +%T) STOP: upload encode failed" >> $LOG ) &
$PY $S/tools/qc_video.py $D/video_final.mp4 $S/research/qc_v3 --sheet 48 >> $LOG 2>&1; log "qc exit $?"
$PY $S/tools/temporal_scan.py $D/video_final.mp4 $S/review6/temporal_v3.json >> $LOG 2>&1; log "scan exit $?"
wait
log "ALL DONE"
