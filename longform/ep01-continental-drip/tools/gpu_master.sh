#!/bin/bash
# gpu_master.sh: after finalize_v3b, build the same v3 master from the Colab GPU chunks (for comparison / optional delivery)
S=$SCRATCH; E=$S/review6/edl_v3; G=$S/colab/out; LOG=$S/engine/gpu_master.log
while ! grep -qE "[0-9] ALL DONE$|STOP:" $S/engine/finalize_v3b.log; do sleep 60; done
( for i in $(seq 0 67); do echo "file '$G/c_$(printf %05d $i).mp4'"; done ) > $G/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $G/list.txt -c copy $S/engine/video_full_v3gpu.mp4 && echo "$(date -u +%T) gpu concat ok" >> $LOG
nice -n 5 $S/venv/bin/python $S/tools/assemble_edl.py $S/engine/video_full_v3gpu.mp4 $E/ranges.json $E/mix_cut.wav $S/deliver/ep01/video_final_gpu.mp4 18 --xfade "$(cat $E/XFADE_OK)" >> $LOG 2>&1 && echo "$(date -u +%T) gpu master ok" >> $LOG || echo "$(date -u +%T) STOP: gpu master failed" >> $LOG
echo "$(date -u +%T) GPU_MASTER_DONE" >> $LOG
