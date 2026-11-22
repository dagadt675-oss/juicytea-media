#!/bin/bash
# full_render.sh PAR: render every chunk on the Colab GPU (restart-safe), download each finished chunk with md5 check. Log: colab/full.log
S=$SCRATCH; CX=$S/colab/cx.sh; BG=$S/colab/bg.sh; C="$S/colabvenv/bin/colab --auth oauth2"; OUT=$S/colab/out; mkdir -p $OUT
PAR=${1:-2}
$BG "bash /content/vm_render.sh '' $PAR" /content/render_full.log
echo "$(date -u +%T) full render started par=$PAR"
declare -A got; end=$(( $(date +%s) + 5400 ))
while [ $(date +%s) -lt $end ]; do
  list=$($CX "cd /content/out && md5sum c_*.mp4 2>/dev/null" 90 | grep -E '^[0-9a-f]{32}  c_[0-9]+\.mp4$')
  n=0
  while read -r md f; do
    [ -z "$f" ] && continue
    if [ -z "${got[$f]}" ]; then
      for try in 1 2 3; do
        timeout 600 $C download -s mj /content/out/$f $OUT/$f >/dev/null 2>&1
        lm=$(md5sum $OUT/$f 2>/dev/null | cut -d' ' -f1)
        [ "$lm" = "$md" ] && { got[$f]=1; echo "$(date -u +%T) got $f"; break; }
        sleep 5
      done
    fi
    n=$((n+1))
  done <<< "$list"
  done_remote=$($CX "grep -c 'RENDER_DONE' /content/render_full.log 2>/dev/null; grep -E 'FAIL|Error' /content/render_full.log | head -3" 60 | tr '\n' ' ')
  echo "$(date -u +%T) remote chunks $n, downloaded ${#got[@]}, status: $done_remote"
  if [ "${#got[@]}" -ge 68 ]; then echo "$(date -u +%T) FULL_DONE"; break; fi
  echo "$done_remote" | grep -q "^1" && [ "${#got[@]}" -ge "$n" ] && [ "$n" -lt 68 ] && { echo "$(date -u +%T) RENDER ENDED WITH MISSING CHUNKS"; break; }
  sleep 90
done
ls $OUT | wc -l
