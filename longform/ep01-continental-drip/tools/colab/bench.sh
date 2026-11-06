#!/bin/bash
# bench.sh: after the parts arrive, lay out /content/mj, unpack the assets, render chunk 10 on the GPU, download it. Log: colab/bench.log
S=$SCRATCH; CX=$S/colab/cx.sh; BG=$S/colab/bg.sh
until grep -q PARTS_DONE $S/colab/upload_parts.log; do sleep 15; done
tail -3 $S/colab/upload_parts.log | cut -c1-120
$CX "mkdir -p /content/mj/engine /content/mj/tools /content/out && mv -f /content/render.cjs /content/mj/engine/ && mv -f /content/render_chunks.py /content/mj/tools/ && cd /content/mj/engine && tar -xf /content/engine_www.tar && du -sh www && ls www | head -20 && rm -rf /content/parts && df -h /content | tail -1" 600
$CX "cd /content/mj/engine && ls node_modules | head -3 && node -e \"console.log(require('playwright/package.json').version)\"" 60
$BG "bash /content/vm_render.sh 10 1" /content/render.log
echo "$(date -u +%T) benchmark render of chunk 10 started"
end=$(( $(date +%s) + 1800 ))
while [ $(date +%s) -lt $end ]; do
  out=$($CX "tail -2 /content/render.log; ls /content/out" 60)
  echo "$(date -u +%T) $(echo "$out" | tr '\n' ' ' | cut -c1-200)"
  echo "$out" | grep -q "RENDER_DONE\|FAIL\|Error" && break
  sleep 60
done
$CX "grep -E 'GPU renderer|rendered|chunk 10|FAIL|Error|exit' /content/render.log | head; ls -la /content/out" 60
mkdir -p $S/colab/out; timeout 600 $S/colabvenv/bin/colab --auth oauth2 download -s mj /content/out/c_00010.mp4 $S/colab/out/c_00010.mp4 2>&1 | tail -1
ls -la $S/colab/out/; ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $S/colab/out/c_00010.mp4
echo "$(date -u +%T) BENCH_DONE"
