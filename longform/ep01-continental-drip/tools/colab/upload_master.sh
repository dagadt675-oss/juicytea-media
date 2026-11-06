#!/bin/bash
# upload_master.sh: the 806 MB v3 master to the Colab CPU session 'up' in 40 MB parts, reassembled and md5-checked there
C="$SCRATCH/colabvenv/bin/colab --auth oauth2"; P=$SCRATCH/colab/parts_master; T=$SCRATCH/deliver/ep01/video_final.mp4
mask() { sed -E 's#(token|code|access_token|refresh_token)=[^& ]+#\1=***#g'; }
mkdir -p $P; cd $P && [ -f m_aa ] || split -b 40m $T m_
LM=$(md5sum $T | cut -d' ' -f1); echo "local md5 $LM; parts: $(ls m_* | wc -l)"
$C exec -s up --timeout 60 --env "CMD=mkdir -p /content/parts /content/mythjuice; ls /content/parts | wc -l" --env T=60 -f $SCRATCH/colab/run_fg.py 2>&1 | mask | tail -1
for f in m_*; do
  for try in 1 2 3 4; do
    out=$(timeout 900 $C upload -s up $P/$f /content/parts/$f 2>&1 | mask | tail -1)
    echo "$(date -u +%T) $f try $try: $(echo $out | cut -c1-40)"
    echo "$out" | grep -q "Uploaded" && break; sleep 10
  done
done
$C exec -s up --timeout 600 --env "CMD=cd /content/parts && cat m_* > /content/mythjuice/myth_juice_ep01_v3_master_1080p.mp4 && rm -f m_* && md5sum /content/mythjuice/*.mp4 && ls -la /content/mythjuice" --env T=600 -f $SCRATCH/colab/run_fg.py 2>&1 | mask | tail -4
echo "$(date -u +%T) MASTER_PARTS_DONE (expected md5 $LM)"
