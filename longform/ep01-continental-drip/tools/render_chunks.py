#!/usr/bin/env python3
"""render_chunks.py --ep ep01 --frames N --out final_video.mp4 [--chunk 450] [--par 3] [--w 1920 --h 1080] [--only 3,7] [--force 3]
Restart-safe renderer: splits [0, N) into chunks of --chunk frames, renders each chunk with engine/render.cjs into
chunks/<ep>/c_00012.mp4 (atomic rename when done), skips chunks that already exist, runs --par chunks in parallel,
then concatenates (stream copy) into --out. Re-run the same command after any interruption to continue.
"""
import argparse, os, subprocess, sys, time, concurrent.futures as cf
ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ep', default='ep01'); ap.add_argument('--frames', type=int, required=True)
    ap.add_argument('--chunk', type=int, default=450); ap.add_argument('--par', type=int, default=3)
    ap.add_argument('--out', required=True); ap.add_argument('--w', type=int, default=1920); ap.add_argument('--h', type=int, default=1080)
    ap.add_argument('--crf', default='12'); ap.add_argument('--only', default=''); ap.add_argument('--force', default='')
    ap.add_argument('--dir', default=None); ap.add_argument('--reverse', action='store_true')
    a = ap.parse_args()
    cdir = a.dir or os.path.join(ENGINE, 'chunks', f'{a.ep}_{a.w}x{a.h}')
    os.makedirs(cdir, exist_ok=True)
    n = (a.frames + a.chunk - 1) // a.chunk
    only = {int(x) for x in a.only.split(',') if x}
    force = {int(x) for x in a.force.split(',') if x}
    for i in force:
        p = os.path.join(cdir, f'c_{i:05d}.mp4')
        if os.path.exists(p): os.remove(p)
    todo = [i for i in range(n) if (not only or i in only) and not os.path.exists(os.path.join(cdir, f'c_{i:05d}.mp4'))]
    if a.reverse: todo = todo[::-1]
    print(f'{n} chunks, {len(todo)} to render -> {cdir}', flush=True)
    q = f'{{"ep":"{a.ep}"}}'
    def job(i):
        s = i * a.chunk; k = min(a.chunk, a.frames - s)
        tmp = os.path.join(cdir, f'tmp_{i:05d}.mp4'); fin = os.path.join(cdir, f'c_{i:05d}.mp4')
        # several renderers may share one chunk dir: skip chunks finished meanwhile or being written by another process
        if os.path.exists(fin): return i, 'skip (already done)'
        lock = os.path.join(cdir, f'lock_{i:05d}')
        for busy in (tmp, lock):
            if os.path.exists(busy) and time.time() - os.path.getmtime(busy) < 150: return i, 'skip (in progress elsewhere)'
        t0 = time.time()
        r = subprocess.run(['node', os.path.join(ENGINE, 'render.cjs'), '--page', 'film.html', '--q', q, '--start', str(s), '--frames', str(k),
                            '--w', str(a.w), '--h', str(a.h), '--crf', a.crf, '--out', tmp], capture_output=True, text=True)
        if r.returncode == 3: return i, 'skip (' + r.stdout.strip()[-80:] + ')'
        if r.returncode != 0 or not os.path.exists(tmp):
            return i, f'FAIL {r.stdout[-400:]} {r.stderr[-800:]}'
        # verify frame count
        cnt = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', tmp], capture_output=True, text=True).stdout.strip()
        if cnt != str(k):
            return i, f'FAIL frame count {cnt} != {k}'
        os.replace(tmp, fin)
        return i, f'ok {k} frames in {time.time() - t0:.0f}s'
    with cf.ThreadPoolExecutor(a.par) as ex:
        for i, msg in ex.map(job, todo):
            print(f'chunk {i}: {msg}', flush=True)
    missing = [i for i in range(n) if not os.path.exists(os.path.join(cdir, f'c_{i:05d}.mp4'))]
    if missing:
        print('missing chunks:', missing); sys.exit(1)
    lst = os.path.join(cdir, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.join(cdir, f'c_{i:05d}.mp4')}'\n" for i in range(n)))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', a.out], check=True)
    print('concatenated ->', a.out)

if __name__ == '__main__':
    main()
