#!/bin/bash
# finalize_v3b.sh: after finalize_v3.sh (ALL DONE) and once review6/edl_v3/XFADE_OK exists, build the final master with the
# dissolve joins, re-scan it, and encode the upload copy (< 500 MiB). The no-dissolve master is kept as video_final_nodissolve.mp4.
S=$SCRATCH
E=$S/review6/edl_v3; D=$S/deliver/ep01; PY=$S/venv/bin/python; LOG=$S/engine/finalize_v3b.log
log() { echo "$(date -u +%T) $*" >> $LOG; }
log "waiting for finalize_v3 ALL DONE and XFADE_OK"
while ! grep -q "ALL DONE" $S/engine/finalize_v3.log 2>/dev/null || [ ! -f $E/XFADE_OK ]; do sleep 20; done
XF=$(cat $E/XFADE_OK)
[ -f $D/video_final.mp4 ] && [ ! -f $D/video_final_nodissolve.mp4 ] && mv $D/video_final.mp4 $D/video_final_nodissolve.mp4
log "master with dissolves: $XF"
$PY $S/tools/assemble_edl.py $S/engine/video_full_v3.mp4 $E/ranges.json $E/mix_cut.wav $D/video_final.mp4 18 --xfade "$XF" >> $LOG 2>&1 && log "master ok" || { log "STOP: master failed"; exit 1; }
( cd $D && rm -f myth_juice_ep01_upload.mp4 && ffmpeg -y -loglevel error -i video_final.mp4 -map 0:v -c:v libx264 -preset slow -b:v 3900k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 \
    -x264-params aq-mode=3 -pass 1 -passlogfile x264v3b -an -f null /dev/null && \
  ffmpeg -y -loglevel error -i video_final.mp4 -map 0:v -map 0:a -c:v libx264 -preset slow -b:v 3900k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 \
    -x264-params aq-mode=3 -pass 2 -passlogfile x264v3b -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a copy -movflags +faststart myth_juice_ep01_upload.mp4 && \
  rm -f x264v3b* && echo "$(date -u +%T) upload ok $(stat -c %s myth_juice_ep01_upload.mp4) bytes" >> $LOG || echo "$(date -u +%T) STOP: upload encode failed" >> $LOG ) &
$PY $S/tools/temporal_scan.py $D/video_final.mp4 $S/review6/temporal_v3b.json >> $LOG 2>&1; log "scan exit $?"
$PY $S/tools/qc_video.py $D/video_final.mp4 $S/research/qc_v3b --sheet 48 >> $LOG 2>&1; log "qc exit $?"
wait
log "ALL DONE"
