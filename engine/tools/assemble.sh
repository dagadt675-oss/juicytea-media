#!/bin/bash
# assemble.sh VIDEO_IN(concatenated chunks) AUDIO_WAV OUT_MP4 [CRF]
# Final master for upload: gentle grade (contrast/saturation, teal-orange balance) + light sharpen, x264 high, AAC 320k, faststart.
# Chunks come out of the JPEG pipe as BT.601 (bt470bg) YCbCr; the master is converted (matrix only) and tagged BT.709 for HD players.
# No synthetic grain: it costs a lot of bitrate and YouTube's re-encode turns it into mush.
set -e
IN=$1; AUD=$2; OUT=$3; CRF=${4:-18}
ffmpeg -y -loglevel error -i "$IN" -i "$AUD" -map 0:v -map 1:a \
  -vf "eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,format=yuv420p,colorspace=space=bt709:ispace=bt470bg:primaries=bt709:iprimaries=bt709:trc=bt709:itrc=bt709:range=tv:irange=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf "$CRF" -profile:v high -level 4.2 -x264-params "aq-mode=3:deblock=-1,-1" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
