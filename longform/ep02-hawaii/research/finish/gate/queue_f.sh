#!/bin/bash
# queue3.sh JOBFILE: like queue2.sh (TREE<TAB>QJSON<TAB>FRAMES<TAB>OUTDIR[<TAB>PAGE]), plus (2026-11-16 13:25):
# - waits until MemAvailable >= 5 GB before each render (shared 15 GB box, 8192 px Big Island colour);
# - after a render, a still that is black (mean < 4) or a log with 'Target crashed' / missing stills -> the job is re-run (max 2 retries).
S=/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/closeup/r3/shader; W=/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/ep02/finish/gate
others() { [ "$(pgrep -fc "^node still.cjs")" -ge 2 ]; }   # allow one other run's render (memory guard below)
memok() { awk '/MemAvailable/ { exit !($2 >= 5*1024*1024) }' /proc/meminfo; }
while IFS=$'\t' read -r tree q frames out page; do
  [ -z "$tree" ] && continue; case "$tree" in \#*) continue;; esac
  [ -f "$out/perf.json" ] && continue
  for try in 0 1 2; do
    n=0; while others; do [ $((n % 12)) -eq 0 ] && echo "$(date -u +%H:%M:%S) waiting for another still.cjs ($out)" >> $W/queue.log; n=$((n+1)); sleep 10; done
    n=0; until memok; do [ $((n % 12)) -eq 0 ] && echo "$(date -u +%H:%M:%S) waiting for memory ($out)" >> $W/queue.log; n=$((n+1)); sleep 10; done
    python3 -I $S/tools/render.py "$tree" "$q" "$frames" "$out" ${page:+--page $page} > /dev/null 2>&1
    bad=$(python3 -I - "$out" "$frames" <<'PY'
import sys, os, numpy as np
from PIL import Image
d, fr = sys.argv[1], sys.argv[2]
want = sorted(set('f%06d.jpg' % int(float(f)) for f in fr.split(',')))
log = open(d + '/log.txt', errors='replace').read() if os.path.exists(d + '/log.txt') else ''
bad = []
if 'Target crashed' in log or 'crashed' in log.lower(): bad.append('crash')
for w in want:
    p = os.path.join(d, w)
    if not os.path.exists(p): bad.append('missing ' + w); continue
    if np.asarray(Image.open(p).convert('L')).mean() < 4: bad.append('black ' + w)
print(' '.join(bad))
PY
)
    [ -z "$bad" ] && break
    echo "$(date -u +%H:%M:%S) RETRY $out ($bad)" >> $W/queue.log; mv "$out" "$out.bad$try"
  done
  err=$(grep -ciE 'error|exception|uncaught|failed' "$out/log.txt" 2>/dev/null)
  echo "$(date -u +%H:%M:%S) $out $(python3 -c "import json;d=json.load(open('$out/perf.json'));print('gpu',d['gpu_cpu_s'],'wall',d['wall_s'],'rc',d['rc'])" 2>/dev/null) errlines=$err" >> $W/queue.log
done < "$1"
echo "$(date -u +%H:%M:%S) DONE $1" >> $W/queue.log
