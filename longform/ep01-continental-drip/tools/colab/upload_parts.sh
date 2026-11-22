#!/bin/bash
# upload_parts.sh: the 343 MB asset tar in 40 MB parts (the Colab upload endpoint returned 500 for the whole file), md5-verified on the VM
C="$SCRATCH/colabvenv/bin/colab --auth oauth2"; P=$SCRATCH/colab/parts; T=$SCRATCH/colab/engine_www.tar
mask() { sed -E 's#(token|code|access_token|refresh_token)=[^& ]+#\1=***#g'; }
mkdir -p $P; cd $P && [ -f p_aa ] || split -b 40m $T p_
LM=$(md5sum $T | cut -d' ' -f1); echo "local md5 $LM; parts: $(ls p_* | wc -l)"
$C exec -s mj --timeout 60 --env "CMD=mkdir -p /content/parts; ls /content/parts | wc -l" --env T=60 -f $SCRATCH/colab/run_fg.py 2>&1 | mask | tail -1
for f in p_*; do
  for try in 1 2 3 4; do
    out=$(timeout 900 $C upload -s mj $P/$f /content/parts/$f 2>&1 | mask | tail -1)
    echo "$(date -u +%T) $f try $try: $out"
    echo "$out" | grep -q "Uploaded" && break; sleep 10
  done
done
$C exec -s mj --timeout 300 --env "CMD=cd /content/parts && cat p_* > /content/engine_www.tar && md5sum /content/engine_www.tar && ls -la /content/engine_www.tar" --env T=300 -f $SCRATCH/colab/run_fg.py 2>&1 | mask | tail -3
echo "$(date -u +%T) PARTS_DONE (expected md5 $LM)"
