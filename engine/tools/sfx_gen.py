#!/usr/bin/env python3
"""sfx_gen.py spec.json outdir [--jobs 4] [--only id1,id2] [--dry]
spec.json, either a plain list:
  {"model": "eleven_text_to_sound_v3", "format": "mp3_44100_192", "default_takes": 1, "takes": {"payoff_boom": 2},
   "sfx": [{"id": "drain_start", "prompt": "what it sounds like", "dur": 4.0, "loop": false, "influence": 0.45,
            "variants": 4, "takes": 2}, ...]}
or an episode spot file (spot_sfx.json): every entry of its "assets" with "source": "generate" is used
(gen_prompt -> prompt, length_s -> dur, prompt_influence -> influence, loop, variants); "takes"/"default_takes" may sit
next to "assets" or be passed in a small wrapper {"spot": "path/to/spot_sfx.json", "takes": {...}, "model": ...}.

Generates every SFX with the ElevenLabs Sound Effects API (POST /v1/sound-generation; text, duration_seconds 0.5-30,
prompt_influence 0-1, loop, model_id). Each entry yields variants x takes files named <id>_v<variant>_t<take>_<hash>.mp3,
cached by content hash (prompt, dur, loop, influence, model, format, variant, take), so a re-run only fetches what is
missing and a changed prompt never overwrites an older take. Variants are distinct sounds for round-robin use (no identical
repeat); takes are alternatives of the same variant to pick from (sfx_check.py). Cost: the docs say 40 credits per second
when dur is set; the account counter moved about 11 per second on 2026-11-08 (eleven_text_to_sound_v3, 785 s generated).
Key read from ELEVENLABS_API_KEY (never printed). Writes <outdir>/sfx_done.json with every file per entry."""
import argparse, hashlib, json, os, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API = 'https://api.elevenlabs.io/v1/sound-generation'

def load_spec(path):
    spec = json.load(open(path))
    if 'spot' in spec:  # wrapper around a spot file
        base = json.load(open(os.path.join(os.path.dirname(os.path.abspath(path)), spec['spot'])))
        base.update({k: v for k, v in spec.items() if k != 'spot'}); spec = base
    if 'sfx' not in spec and 'assets' in spec:
        spec['sfx'] = [{'id': k, 'prompt': a['gen_prompt'], 'dur': a.get('length_s'), 'loop': bool(a.get('loop')),
                        'influence': a.get('prompt_influence', 0.3), 'variants': a.get('variants', 1)}
                       for k, a in spec['assets'].items() if a.get('source') == 'generate']
    return spec

def jobs_for(spec):
    model = spec.get('model', 'eleven_text_to_sound_v3'); fmt = spec.get('format', 'mp3_44100_192')
    takes = spec.get('takes', {}); dtakes = spec.get('default_takes', 1)
    out = []
    for s in spec['sfx']:
        nt = s.get('takes', takes.get(s['id'], dtakes))
        dur = None if s.get('dur') is None else round(min(30.0, max(0.5, float(s['dur']))), 2)
        for v in range(s.get('variants', 1)):
            for t in range(nt):
                key = [s['prompt'], dur, bool(s.get('loop')), s.get('influence', 0.3), model, fmt, v, t]
                h = hashlib.sha1(json.dumps(key).encode()).hexdigest()[:10]
                body = {'text': s['prompt'], 'model_id': model, 'loop': bool(s.get('loop')), 'prompt_influence': s.get('influence', 0.3)}
                if dur is not None: body['duration_seconds'] = dur
                out.append({'id': s['id'], 'variant': v, 'take': t, 'dur': dur, 'hash': h, 'body': body, 'fmt': fmt,
                            'name': f"{s['id']}_v{v}_t{t}_{h}.mp3"})
    return out

def fetch(job, outdir, key):
    fn = os.path.join(outdir, job['name'])
    if os.path.exists(fn): return job, fn, 'cached'
    err = None
    for a in range(5):
        try:
            req = urllib.request.Request(f"{API}?output_format={job['fmt']}", json.dumps(job['body']).encode(),
                                         {'xi-api-key': key, 'Content-Type': 'application/json'})
            r = urllib.request.urlopen(req, timeout=300)
            data = r.read()
            if len(data) < 1000 or 'audio' not in r.headers.get('Content-Type', 'audio'): raise RuntimeError(f'not audio ({len(data)} B)')
            tmp = fn + '.part'; open(tmp, 'wb').write(data); os.replace(tmp, fn)
            return job, fn, f'wrote {len(data)} B'
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode('utf-8', 'replace')
            err = f'HTTP {e.code}: {detail}'
            if e.code in (400, 401, 403, 422): break  # not retryable: bad request, auth or validation
        except Exception as e:
            err = f'{type(e).__name__}: {e}'
        time.sleep(5 * (a + 1))
    return job, None, f'FAILED {err}'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('outdir')
    ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--only', default=''); ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    spec = load_spec(a.spec); os.makedirs(a.outdir, exist_ok=True)
    all_jobs = jobs_for(spec)
    jobs = [j for j in all_jobs if not a.only or j['id'] in set(a.only.split(','))]
    secs = sum(j['dur'] or 0 for j in jobs if not os.path.exists(os.path.join(a.outdir, j['name'])))
    print(f"{len(jobs)} files ({len({j['id'] for j in jobs})} sounds); to fetch: {secs:.1f} s of audio, about {secs * 40:.0f} credits", flush=True)
    if a.dry: return
    key = os.environ['ELEVENLABS_API_KEY']
    failed = []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for f in as_completed([ex.submit(fetch, j, a.outdir, key) for j in jobs]):
            job, fn, msg = f.result()
            print(job['name'], msg, flush=True)
            if not fn: failed.append({'id': job['id'], 'variant': job['variant'], 'take': job['take'], 'error': msg})
    done = {}  # every file of the whole spec that exists now (also those of earlier runs), so --only never hides the rest
    for j in all_jobs:
        fn = os.path.join(a.outdir, j['name'])
        if os.path.exists(fn): done.setdefault(j['id'], []).append({'variant': j['variant'], 'take': j['take'], 'dur': j['dur'], 'file': fn})
    json.dump({'model': spec.get('model', 'eleven_text_to_sound_v3'), 'format': spec.get('format', 'mp3_44100_192'), 'files': done, 'failed': failed},
              open(os.path.join(a.outdir, 'sfx_done.json'), 'w'), indent=1)
    print(f"done: {sum(len(v) for v in done.values())} files, failed: {len(failed)}")
    if failed: sys.exit(1)

if __name__ == '__main__':
    main()
