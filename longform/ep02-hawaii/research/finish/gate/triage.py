"""triage.py A_DIR B_DIR TAG: diffcrop sheet per common still (cmp/TAG_fNNNNNN.jpg) + GPU per still (perf.json frames_gpu)."""
import sys, os, json, subprocess, glob
F = os.path.dirname(os.path.abspath(__file__))
a, b, tag = sys.argv[1:4]
def gpu(d):
    try: fg = json.load(open(os.path.join(d, 'perf.json')))['frames_gpu']
    except Exception: return {}
    out = {}
    for e in fg: out.setdefault(e['file'], []).append(e['gpu_step'])
    return out
ga, gb = gpu(a), gpu(b)
for p in sorted(glob.glob(os.path.join(a, 'f*.jpg'))):
    n = os.path.basename(p); q = os.path.join(b, n)
    if not os.path.exists(q): print(n, 'missing in B'); continue
    out = os.path.join(F, 'cmp', f'{tag}_{n}')
    r = subprocess.run([sys.executable, '-I', os.path.join(F, 'diffcrop.py'), p, q, out, '--label', 'live,r3'], capture_output=True, text=True)
    print(n, 'GPU live', ga.get(n), 'r3', gb.get(n)); print('  ' + r.stdout.strip().replace('\n', '\n  ') + (r.stderr[-300:] if r.returncode else ''))
