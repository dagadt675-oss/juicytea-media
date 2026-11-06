#!/usr/bin/env python3
"""assemble_edl.py VIDEO_IN(concatenated chunks) RANGES_JSON(edl.py) AUDIO_WAV OUT_MP4 [CRF]
The master as assemble.sh makes it (grade, BT.709, x264 slow, AAC 320k), with the picture taken from the edl.py ranges in
output order. Each range is its own frame-accurate input (-ss/-to half a frame inside the boundaries), so the concat filter
pulls one range at a time and nothing is buffered."""
import json, subprocess, sys

GRADE = ('eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,format=yuv420p,'
         'colorspace=space=bt709:ispace=bt470bg:primaries=bt709:iprimaries=bt709:trc=bt709:itrc=bt709:range=tv:irange=tv,format=yuv420p')
def main():
    vid, rj, aud, out = sys.argv[1:5]; crf = sys.argv[5] if len(sys.argv) > 5 else '18'
    R = json.load(open(rj))
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    parts = []   # (input args, filter for that input)
    for r in R:
        k, m, h = r['k'], r['m'], r.get('hold_until')
        if h and h > k:   # hold the piece's own first frame until its shot starts (keeps sound and picture in sync)
            parts.append((['-ss', '%.4f' % ((h - 0.5) / 30), '-i', vid], 'trim=end_frame=1,loop=loop=%d:size=1:start=0,setpts=N/30/TB' % (h - k - 1)))
            k = h
        parts.append((['-ss', '%.4f' % ((k - 0.5) / 30), '-to', '%.4f' % ((m - 0.5) / 30), '-i', vid], 'setpts=PTS-STARTPTS'))
    for a, _ in parts: cmd += a
    cmd += ['-i', aud]
    fc = ''.join('[%d:v]%s[v%d];' % (i, f, i) for i, (_, f) in enumerate(parts))
    fc += ''.join('[v%d]' % i for i in range(len(parts))) + 'concat=n=%d:v=1:a=0[c];[c]%s[v]' % (len(parts), GRADE)
    cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '%d:a' % len(parts), '-r', '30',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-profile:v', 'high', '-level', '4.2', '-x264-params', 'aq-mode=3:deblock=-1,-1',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', '-shortest', out]
    subprocess.run(cmd, check=True)
    print(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames:format=duration,size',
                          '-of', 'default=nw=1', out], capture_output=True, text=True).stdout)
    print('expected frames', sum(r['m'] - r['k'] for r in R))

if __name__ == '__main__':
    main()
