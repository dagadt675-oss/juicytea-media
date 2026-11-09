"""rend.py OUTDIR name '{overrides}' [name '{...}' ...]: render the NO OCEAN plate (pairs.json cand_1 camera, lift_a base) with overrides, 1920x1080."""
import json, sys, subprocess, os, shutil, tempfile
BASE = {"level": -9000, "tub": 1, "landSat": 1.25, "basalt": [0.036, 0.036, 0.039], "sed": [0.058, 0.055, 0.054], "shot": "plate_ne", "look": "gold",
        "sun": [262, 8], "exposure": 1.7, "landGain": 1.8, "fog": [0.003, 0.0001],
        "cam": {"lon": -155.32, "lat": 18.42, "alt": 26, "tLon": -155.47, "tLat": 19.52, "tH": -2000, "fov": 40}}
out = sys.argv[1]; os.makedirs(out, exist_ok=True); args = sys.argv[2:]
log = {}
lp = os.path.join(out, 'queries.json')
if os.path.exists(lp): log = json.load(open(lp))
for n, o in zip(args[::2], args[1::2]):
    q = dict(BASE); q.update(json.loads(o))
    t = tempfile.mkdtemp(dir=out)
    r = subprocess.run(['node', 'still.cjs', '--page', 'lab_hawaii.html', '--q', json.dumps(q), '--frames', '0', '--w', '1920', '--h', '1080', '--outdir', t],
                       cwd='/home/user/juicytea-media/engine', capture_output=True, text=True)
    shutil.move(os.path.join(t, 'f000000.jpg'), os.path.join(out, n + '.jpg')); shutil.rmtree(t)
    log[n] = q; print(n, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])
json.dump(log, open(lp, 'w'), indent=1)
