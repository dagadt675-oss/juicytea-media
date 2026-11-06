#!/usr/bin/env python3
"""assemble_edl.py VIDEO_IN(concatenated chunks) RANGES_JSON(edl.py) AUDIO_WAV OUT_MP4 [CRF] [--xfade J:N,J:N] [--test]
The master as assemble.sh makes it (grade, BT.709, x264 slow, AAC 320k), with the picture taken from the edl.py ranges in
output order. Each range is its own input (seek half a frame before its first frame, then an exact frame-count trim) feeding one concat.
--xfade J:N  dissolves N frames (even) over join J (1-based: the join between range J and range J+1) without moving the
             timeline: range J clones its last frame N/2 frames longer, range J+1 starts with N/2 clones of its first
             frame, and the two overlap in an xfade of N frames (so a shot never shows cut material from the other side).
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
    test = '--test' in rest; noshort = '--noshortest' in rest; noaudio = '--noaudio' in rest
    R = json.load(open(rj))
    # the EDL may ask for one frame past the end of the source (mix duration rounded up): clamp to the real frame count
    nb = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', vid], capture_output=True, text=True).stdout.strip() or 0)
    if nb:
        for r in R:
            if r['m'] > nb: print('range end clamped', r['m'], '->', nb); r['m'] = nb
    inputs, labels = [], []   # labels: per range, the stream label of its finished picture
    fc = []
    def add_input(args): inputs.append(args); return len(inputs) - 1
    def ss(f): return '%.4f' % ((f - 0.5) / FPS)
    scale = ',scale=320:180' if test else ''
    for i, r in enumerate(R):
        k, m, h = r['k'], r['m'], r.get('hold_until')
        pre = xf.get(i, 0) // 2        # join i is between range i-1 and range i (1-based J = i)
        post = xf.get(i + 1, 0) // 2   # join i+1 is between range i and range i+1
        k0 = h if (h and h > k) else k
        # holds are clones of the first/last frame of the same stream (tpad), so no second seek can bring in a foreign frame
        start = (k0 - k) + pre
        # seek to the first frame, then cut the exact frame count in the graph (an input -to rounds and can let one more frame through)
        a = add_input(['-ss', ss(k0), '-i', vid])
        f = f'[{a}:v]trim=end_frame={m - k0},setpts=PTS-STARTPTS'
        if start: f += f',tpad=start_mode=clone:start={start}'
        if post: f += f',tpad=stop_mode=clone:stop={post}'
        fc.append(f + f'{scale},settb=1/30,setpts=N[p{i}]'); labels.append(f'[p{i}]')   # exact integer frame stamps in one timebase: concat and xfade then never round a frame away
        r['_len'] = (m - k0) + start + post
    # chain the ranges: concat at plain joins, xfade at dissolve joins (offset in the accumulated output timeline)
    acc, acc_len = labels[0], R[0]['_len']
    for i in range(1, len(R)):
        n = xf.get(i, 0)
        if n:
            fc.append(f'{acc}{labels[i]}xfade=transition=fade:duration={n / FPS:.6f}:offset={(acc_len - n) / FPS:.6f},settb=1/30,setpts=N[x{i}]')
            acc = f'[x{i}]'; acc_len += R[i]['_len'] - n
        else:
            fc.append(f'{acc}{labels[i]}concat=n=2:v=1:a=0,settb=1/30,setpts=N[x{i}]'); acc = f'[x{i}]'; acc_len += R[i]['_len']   # concat re-stamps to 1/1e6; back to exact 1/30 for the next xfade
    fc.append(f'{acc}{"format=yuv420p" if test else GRADE}[v]')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    for a in inputs: cmd += a
    if noaudio: cmd += ['-filter_complex', ';'.join(fc), '-map', '[v]', '-r', str(FPS)]
    else: cmd += ['-i', aud, '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', f'{len(inputs)}:a', '-r', str(FPS)]
    sh = [] if (noshort or noaudio) else ['-shortest']
    if test: cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28'] + ([] if noaudio else ['-c:a', 'aac', '-b:a', '96k']) + sh + [out]
    else: cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-profile:v', 'high', '-level', '4.2', '-x264-params', 'aq-mode=3:deblock=-1,-1',
                  '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart'] + sh + [out]
    expected = sum(r['m'] - r['k'] for r in R)
    print('inputs', len(inputs), 'expected frames', expected, 'accumulated', acc_len, 'xfade', xf, flush=True)
    subprocess.run(cmd, check=True)
    print(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames:format=duration,size',
                          '-of', 'default=nw=1', out], capture_output=True, text=True).stdout)

if __name__ == '__main__':
    main()
