#!/usr/bin/env python3
"""assemble_edl.py VIDEO_IN(concatenated chunks) RANGES_JSON(edl.py) AUDIO_WAV OUT_MP4 [CRF] [--xfade J:N,J:N] [--test]
The master as assemble.sh makes it (grade, BT.709, x264 slow, AAC 320k), with the picture taken from the edl.py ranges in
output order. Each range is its own frame-accurate input (-ss/-to half a frame inside the boundaries) feeding one concat.
--xfade J:N  dissolves N frames (even) over join J (1-based: the join between range J and range J+1) without moving the
             timeline: range J holds its last frame N/2 frames longer, range J+1 starts with its first frame held N/2
             frames, and the two overlap in an xfade of N frames (so a shot never shows cut material from the other side).
--test       320x180, ultrafast, no grade: a quick structural check (frame count, joins) in a few minutes."""
import json, subprocess, sys

GRADE = ('eq=contrast=1.04:saturation=1.06,colorbalance=rs=-0.02:bs=0.03:rh=0.03:bh=-0.02,unsharp=5:5:0.35:5:5:0.0,format=yuv420p,'
         'colorspace=space=bt709:ispace=bt470bg:primaries=bt709:iprimaries=bt709:trc=bt709:itrc=bt709:range=tv:irange=tv,format=yuv420p')
FPS = 30
def main():
    vid, rj, aud, out = sys.argv[1:5]
    rest = sys.argv[5:]; crf = rest[0] if rest and not rest[0].startswith('--') else '18'
    xf = {}
    if '--xfade' in rest:
        for item in rest[rest.index('--xfade') + 1].split(','):
            j, n = item.split(':'); xf[int(j)] = int(n)
    test = '--test' in rest
    R = json.load(open(rj))
    inputs, labels = [], []   # labels: per range, the stream label of its finished picture
    fc = []
    def add_input(args): inputs.append(args); return len(inputs) - 1
    def ss(f): return '%.4f' % ((f - 0.5) / FPS)
    scale = ',scale=320:180' if test else ''
    for i, r in enumerate(R):
        k, m, h = r['k'], r['m'], r.get('hold_until')
        pre = xf.get(i, 0) // 2        # join i is between range i-1 and range i (1-based J = i)
        post = xf.get(i + 1, 0) // 2   # join i+1 is between range i and range i+1
        subs = []
        if h and h > k:   # the moved piece: hold its own first shot frame until the shot starts (pre-hold merges into it)
            n_hold = (h - k) + pre
            a = add_input(['-ss', ss(h), '-i', vid]); fc.append(f'[{a}:v]trim=end_frame=1,loop=loop={n_hold - 1}:size=1:start=0,setpts=N/{FPS}/TB{scale}[s{a}]'); subs.append(f'[s{a}]')
            k = h
        elif pre:
            a = add_input(['-ss', ss(k), '-i', vid]); fc.append(f'[{a}:v]trim=end_frame=1,loop=loop={pre - 1}:size=1:start=0,setpts=N/{FPS}/TB{scale}[s{a}]'); subs.append(f'[s{a}]')
        a = add_input(['-ss', ss(k), '-to', ss(m), '-i', vid]); fc.append(f'[{a}:v]setpts=PTS-STARTPTS{scale}[s{a}]'); subs.append(f'[s{a}]')
        if post:
            a = add_input(['-ss', ss(m - 1), '-i', vid]); fc.append(f'[{a}:v]trim=end_frame=1,loop=loop={post - 1}:size=1:start=0,setpts=N/{FPS}/TB{scale}[s{a}]'); subs.append(f'[s{a}]')
        if len(subs) > 1: fc.append(''.join(subs) + f'concat=n={len(subs)}:v=1:a=0[p{i}]'); labels.append(f'[p{i}]')
        else: labels.append(subs[0])
        r['_len'] = (m - k) + ((h - r['k']) if (h and h > r['k']) else 0) + pre + post
    # chain the ranges: concat at plain joins, xfade at dissolve joins (offset in the accumulated output timeline)
    acc, acc_len = labels[0], R[0]['_len']
    for i in range(1, len(R)):
        n = xf.get(i, 0)
        if n:
            fc.append(f'{acc}{labels[i]}xfade=transition=fade:duration={n / FPS:.6f}:offset={(acc_len - n) / FPS:.6f}[x{i}]')
            acc = f'[x{i}]'; acc_len += R[i]['_len'] - n
        else:
            fc.append(f'{acc}{labels[i]}concat=n=2:v=1:a=0[x{i}]'); acc = f'[x{i}]'; acc_len += R[i]['_len']
    fc.append(f'{acc}{"format=yuv420p" if test else GRADE}[v]')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    for a in inputs: cmd += a
    cmd += ['-i', aud, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', f'{len(inputs)}:a', '-r', str(FPS)]
    if test: cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-c:a', 'aac', '-b:a', '96k', '-shortest', out]
    else: cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-profile:v', 'high', '-level', '4.2', '-x264-params', 'aq-mode=3:deblock=-1,-1',
                  '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', '-shortest', out]
    expected = sum(r['m'] - r['k'] for r in R)
    print('inputs', len(inputs), 'expected frames', expected, 'accumulated', acc_len, 'xfade', xf, flush=True)
    subprocess.run(cmd, check=True)
    print(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames:format=duration,size',
                          '-of', 'default=nw=1', out], capture_output=True, text=True).stdout)

if __name__ == '__main__':
    main()
