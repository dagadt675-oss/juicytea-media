#!/bin/bash
# assemble.sh VIDEO_IN(concatenated chunks) AUDIO_WAV OUT_MP4
# Final master: subtle film grain + gentle teal/orange grade + sharpen, x264 high quality, AAC 320k, faststart.
set -e
IN=$1; AUD=$2; OUT=$3
ffmpeg -y -loglevel error -i "$IN" -i "$AUD" -map 0:v -map 1:a \
  -vf "eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,noise=alls=5:allf=t+u,format=yuv420p" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.2 -x264-params "aq-mode=3:deblock=-1,-1" \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
