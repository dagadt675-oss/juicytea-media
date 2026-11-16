#!/bin/bash
cd /tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work
OUT=/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/refs/sb
for vid in ZWZWjXTnyEQ TudM_lSW8WA hEsjPdO3YQM iGP2VsaRSQ4 NX1_E9zndps GPxTR2vw_og xiCwRsBn6mQ uKOYckUHWNk a-ZunVN9Tno YIXnHpSRGP4 MvzE0y4rpsk 4d5nTTiCai0; do
  for try in 1 2 3 4 5 6; do
    if [ -f $OUT/${vid}_open.jpg ]; then break; fi
    r=$(python3 -I sb.py $vid 2>&1)
    echo "$(date +%T) $r"
    if echo "$r" | grep -q 429; then sleep 150; else sleep 8; break; fi
  done
done
echo DONE
