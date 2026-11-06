#!/bin/bash
# vm_render.sh "<chunk list or empty for all>" [PAR]: render 450-frame chunks of ep01 on the Colab GPU into /content/out
# (restart-safe: finished chunks are skipped). Log: /content/render.log. Then tar + md5 the chunks for download.
export GPU=1 __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
ONLY=${1:-}; PAR=${2:-3}
cd /content/mj/engine
echo "== render start $(date -u +%T) only='$ONLY' par=$PAR"
python3 /content/mj/tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par $PAR ${ONLY:+--only $ONLY} --dir /content/out --out /content/out/unused.mp4
echo "== render exit $? $(date -u +%T)"
cd /content/out && ls c_*.mp4 2>/dev/null | wc -l | xargs echo "chunks done:"
echo RENDER_DONE
