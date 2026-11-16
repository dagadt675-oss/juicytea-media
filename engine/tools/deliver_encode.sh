#!/bin/bash
# deliver_encode.sh VIDEO_IN AUDIO_WAV OUT_MP4 [VIDEO_KBPS] [PRESET]: same grade/BT.709 chain as assemble.sh, 2-pass x264 sized for a 500 MiB upload limit
set -e
IN=$1; AUD=$2; OUT=$3; VB=${4:-3700}; PR=${5:-slow}
VF="eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,format=yuv420p,colorspace=space=bt709:ispace=bt470bg:primaries=bt709:iprimaries=bt709:trc=bt709:itrc=bt709:range=tv:irange=tv,format=yuv420p"
X="aq-mode=3:deblock=-1,-1"
cd "$(dirname "$OUT")"
ffmpeg -y -loglevel error -i "$IN" -map 0:v -vf "$VF" -c:v libx264 -preset $PR -b:v ${VB}k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 -x264-params "$X" -pass 1 -passlogfile x264pass -an -f null /dev/null
ffmpeg -y -loglevel error -i "$IN" -i "$AUD" -map 0:v -map 1:a -vf "$VF" -c:v libx264 -preset $PR -b:v ${VB}k -maxrate 7000k -bufsize 14000k -profile:v high -level 4.2 -x264-params "$X" -pass 2 -passlogfile x264pass \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$OUT"
rm -f x264pass*
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$OUT"
