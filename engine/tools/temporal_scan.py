#!/usr/bin/env python3
"""temporal_scan.py VIDEO OUT_JSON [--chunk 450]
Decodes every frame at 256x144 (gray) and looks for motion glitches a contact sheet cannot show:
  - cuts:    global frame difference far above its local median (hard cuts, intended or not)
  - flashes: frame n differs from both neighbours while n-1 and n+1 match each other (1-frame glitch)
  - pops:    one 16x16 block jumps far above its local history without a global cut (element appears/vanishes in 1 frame)
  - seams:   the frame pair at every chunk boundary (n = k*chunk) compared with the motion around it
             (a chunk re-rendered with newer code next to an older chunk shows up as a jump exactly there)
Differences are mean absolute luma differences (0-255)."""
import json, subprocess, sys
import numpy as np

W, H, BS = 256, 144, 16

def main():
    vid, outp = sys.argv[1], sys.argv[2]
    chunk = int(sys.argv[sys.argv.index('--chunk') + 1]) if '--chunk' in sys.argv else 450
    fps = 30.0
    cmd = ['ffmpeg', '-v', 'error', '-i', vid, '-map', '0:v', '-vf', f'scale={W}:{H}:flags=area,format=gray', '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 64)
    fs = W * H
    gd, bmax, bidx, d2 = [], [], [], []   # global diff n vs n-1, max block diff, its block index, diff n+1 vs n-1
    prev2 = prev = None
    n = 0
    while True:
        buf = p.stdout.read(fs)
        if len(buf) < fs: break
        f = np.frombuffer(buf, np.uint8).reshape(H, W).astype(np.int16)
        if prev is None:
            gd.append(0.0); bmax.append(0.0); bidx.append(-1)
        else:
            a = np.abs(f - prev)
            gd.append(float(a.mean()))
            b = a.reshape(H // BS, BS, W // BS, BS).mean(axis=(1, 3))
            k = int(b.argmax()); bmax.append(float(b.flat[k])); bidx.append(k)
        if prev2 is not None:
            d2.append(float(np.abs(f - prev2).mean()))   # d2[i] = |F[i+2]-F[i]|
        prev2, prev = prev, f
        n += 1
    p.wait()
    gd = np.array(gd); bmax = np.array(bmax); d2 = np.array(d2)
    N = len(gd)
    np.savez_compressed(outp.rsplit('.', 1)[0] + '_raw.npz', gd=gd, bmax=bmax, bidx=np.array(bidx), d2=d2)

    def locmed(x, i, r=15):
        lo, hi = max(1, i - r), min(N, i + r + 1)
        s = np.concatenate([x[lo:i], x[i + 1:hi]])
        return float(np.median(s)) if len(s) else 0.0

    tc = lambda i: round(i / fps, 3)
    cuts, flashes, pops, seams = [], [], [], []
    for i in range(1, N):
        m = locmed(gd, i)
        if gd[i] > max(10.0, 6 * m + 2):
            cuts.append({'frame': i, 't': tc(i), 'diff': round(gd[i], 2), 'local_median': round(m, 2)})
    for i in range(1, N - 1):
        # flash: F[i] far from F[i-1] and F[i+1], but F[i+1] close to F[i-1]
        a, b, c = gd[i], gd[i + 1], d2[i - 1]
        if a > 3.0 and b > 3.0 and c < 0.35 * min(a, b):
            flashes.append({'frame': i, 't': tc(i), 'in': round(a, 2), 'out': round(b, 2), 'across': round(c, 2)})
    cutset = {c['frame'] for c in cuts}
    for i in range(1, N):
        if i in cutset: continue
        m = locmed(bmax, i)
        if bmax[i] > max(40.0, 5 * m + 15) and gd[i] < 8:
            k = bidx[i]; by, bx = divmod(k, W // BS)
            # block position as a fraction of the frame (x, y of the block centre)
            pops.append({'frame': i, 't': tc(i), 'block_diff': round(bmax[i], 1), 'local_median': round(m, 1),
                         'where_xy': [round((bx + 0.5) * BS / W, 2), round((by + 0.5) * BS / H, 2)], 'global': round(gd[i], 2)})
    for k in range(1, N // chunk + 1):
        i = k * chunk
        if i >= N: break
        m = locmed(gd, i, 8); mb = locmed(bmax, i, 8)
        seams.append({'frame': i, 't': tc(i), 'chunk_from': k - 1, 'chunk_to': k, 'diff': round(gd[i], 2), 'local_median': round(m, 2),
                      'ratio': round(gd[i] / (m + 0.05), 1), 'block_diff': round(bmax[i], 1), 'block_local_median': round(mb, 1),
                      'cut_here': i in cutset})
    # abrupt motion stops/starts inside a shot (camera or element halts or launches with no easing)
    stops = []
    for i in range(4, N - 4):
        if i in cutset or (i + 1) in cutset or (i - 1) in cutset: continue
        before, after = gd[i - 3:i].mean(), gd[i:i + 3].mean()
        if before > 1.2 and after < 0.12 * before and min(gd[i - 3:i]) > 0.5:
            stops.append({'frame': i, 't': tc(i), 'kind': 'stop', 'motion_before': round(before, 2), 'motion_after': round(after, 2)})
        elif after > 1.2 and before < 0.12 * after and min(gd[i:i + 3]) > 0.5:
            stops.append({'frame': i, 't': tc(i), 'kind': 'start', 'motion_before': round(before, 2), 'motion_after': round(after, 2)})
    # judder: repeated (duplicate) frames in the middle of motion
    judder = []
    for i in range(1, N - 1):
        if gd[i] < 0.03 and gd[i - 1] > 0.6 and gd[i + 1] > 0.6:
            judder.append(i)
    jud_runs = []
    for i in judder:
        if jud_runs and i - jud_runs[-1]['last'] <= 15: jud_runs[-1]['last'] = i; jud_runs[-1]['count'] += 1
        else: jud_runs.append({'first': i, 'last': i, 'count': 1})
    jud = [{'t0': tc(r['first']), 't1': tc(r['last']), 'dup_frames': r['count']} for r in jud_runs]
    sus_seams = [s for s in seams if (s['ratio'] > 3 and s['diff'] > 0.6) or (s['block_diff'] > 3 * s['block_local_median'] + 10)]
    out = {'frames': N, 'fps': fps, 'abrupt_motion': stops, 'judder': jud, 'cuts': cuts, 'flashes': flashes, 'pops': pops, 'seams_all': seams, 'seams_suspicious': sus_seams,
           'global_diff_per_second': [round(float(gd[int(s * fps):int((s + 1) * fps)].mean()), 2) for s in range(int(N / fps))]}
    json.dump(out, open(outp, 'w'), indent=1)
    print(f'frames {N}; cuts {len(cuts)}; flashes {len(flashes)}; pops {len(pops)}; abrupt motion {len(stops)}; judder runs {len(jud)}; suspicious seams {len(sus_seams)}/{len(seams)}')

if __name__ == '__main__':
    main()
