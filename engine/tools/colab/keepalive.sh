#!/bin/bash
# touch the Colab session every 4 min (an idle client lets Colab reclaim the VM); stops when colab/STOP_KA exists
C="$SCRATCH/colabvenv/bin/colab --auth oauth2"
while [ ! -f $SCRATCH/colab/STOP_KA ]; do
  r=$(timeout 100 $C exec -s mj --timeout 60 --env "CMD=nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; uptime | sed 's/.*load/load/'" --env T=60 -f $SCRATCH/colab/run_fg.py 2>&1 | tail -2 | tr '\n' ' ')
  echo "$(date -u +%T) $r" >> $SCRATCH/colab/keepalive.log
  sleep 240
done
