#!/bin/bash
# assemble_cut.sh VIDEO_IN(concatenated chunks) SELECT_TXT(from edl.py) AUDIO_WAV OUT_MP4 [CRF]
# Same master as assemble.sh, with the edl.py frame selection (cuts) applied in front of the grade chain, in one encode.
set -e
IN=$1; SEL=$(cat "$2"); AUD=$3; OUT=$4; CRF=${5:-18}
GRADE="eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,format=yuv420p,colorspace=space=bt709:ispace=bt470bg:primaries=bt709:iprimaries=bt709:trc=bt709:itrc=bt709:range=tv:irange=tv,format=yuv420p"
ffmpeg -y -loglevel error -i "$IN" -i "$AUD" -filter_complex "[0:v]${SEL},${GRADE}[v]" -map "[v]" -map 1:a \
  -c:v libx264 -preset slow -crf "$CRF" -profile:v high -level 4.2 -x264-params "aq-mode=3:deblock=-1,-1" -r 30 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
