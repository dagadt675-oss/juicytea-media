#!/bin/bash
# upload the engine bundle to the Colab VM (session mj); log: colab/upload.log
C="$SCRATCH/colabvenv/bin/colab --auth oauth2"
mask() { sed -E 's#(token|code|access_token|refresh_token)=[^& ]+#\1=***#g'; }
up() { echo "$(date -u +%T) upload $1 -> $2"; timeout 3600 $C upload -s mj "$1" "$2" 2>&1 | mask | tail -2; }
up $SCRATCH/colab/vm_setup.sh /content/vm_setup.sh
up $SCRATCH/colab/vm_render.sh /content/vm_render.sh
up $SCRATCH/colab/bundle/mj/engine/render.cjs /content/render.cjs
up $SCRATCH/colab/bundle/mj/tools/render_chunks.py /content/render_chunks.py
up $SCRATCH/colab/engine_www.tar /content/engine_www.tar
echo "$(date -u +%T) UPLOAD_DONE"
