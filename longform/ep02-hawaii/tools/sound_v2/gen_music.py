#!/usr/bin/env python3
"""gen_music.py CUES_JSON OUTDIR CUE_ID [CUE_ID ...]: generate selected cues exactly the way engine/tools/music.py does (same body,
same plan_for, same content-hash file name, model, mp3_44100_192), but one attempt per cue (no retry loop that could re-request
and re-bill), with a budget guard on SECONDS REQUESTED (13.7 credits/s; the account counter lags), and merging into
OUTDIR/cues_done.json instead of overwriting it. Key only from ELEVENLABS_API_KEY (never printed).
Budget file: OUTDIR/budget.json {"limit_credits": N, "rate": 13.7, "spent": [{"id", "s", "credits", "status"}]}."""
import hashlib, json, os, sys, time, urllib.request
sys.path.insert(0, '/home/user/juicytea-media/engine/tools')
from music import plan_for  # noqa: E402

RATE = 13.7


def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; want = sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    bpath = os.path.join(out, 'budget.json')
    bud = json.load(open(bpath)) if os.path.exists(bpath) else {'limit_credits': 9500, 'rate': RATE, 'spent': []}
    dpath = os.path.join(out, 'cues_done.json')
    done = json.load(open(dpath)) if os.path.exists(dpath) else {k: v for k, v in spec.items() if k != 'cues'} | {'cues': []}
    key = os.environ['ELEVENLABS_API_KEY']
    for c in [c for c in spec['cues'] if c['id'] in want]:
        if c.get('plan'):
            body = {'composition_plan': plan_for(spec, c)}
            if c.get('seed') is not None: body['seed'] = c['seed']
            hkey = [body, spec.get('model'), c.get('take', 0)]
            secs = sum(ch['duration_ms'] for ch in body['composition_plan']['chunks']) / 1000
        else:
            prompt = f"{spec.get('global', '')}. {c['prompt']}".strip()
            ms = int(min(600, max(10, c['dur'] + 3)) * 1000)
            body = {'prompt': prompt, 'music_length_ms': ms, 'force_instrumental': True}
            hkey = [prompt, ms, spec.get('model'), c.get('take', 0)]
            secs = ms / 1000
        h = hashlib.sha1(json.dumps(hkey).encode()).hexdigest()[:10]
        fn = os.path.join(out, f"{c['id']}_{h}.mp3")
        if os.path.exists(fn):
            print('cached', fn)
        else:
            cost = secs * RATE
            used = sum(x['credits'] for x in bud['spent'])
            if used + cost > bud['limit_credits']:
                print(f"BUDGET STOP {c['id']}: {used:.0f} + {cost:.0f} > {bud['limit_credits']}"); continue
            if spec.get('model'): body['model_id'] = spec['model']
            t0 = time.time()
            try:
                req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', json.dumps(body).encode(),
                                             {'xi-api-key': key, 'Content-Type': 'application/json'})
                data = urllib.request.urlopen(req, timeout=600).read(); open(fn, 'wb').write(data)
                bud['spent'].append({'id': c['id'], 's': round(secs, 2), 'credits': round(cost, 1), 'status': 'ok', 'file': fn,
                                     'wall_s': round(time.time() - t0, 1)})
                print('wrote', fn, len(data), f'{secs:.1f} s ~{cost:.0f} credits', flush=True)
            except Exception as e:
                detail = e.read()[:300] if hasattr(e, 'read') else b''
                bud['spent'].append({'id': c['id'], 's': round(secs, 2), 'credits': round(cost, 1), 'status': f'failed: {e} {detail!r}'[:300]})
                print('FAILED (counted as spent, not retried)', c['id'], e, detail, flush=True)
                json.dump(bud, open(bpath, 'w'), indent=1); continue
            json.dump(bud, open(bpath, 'w'), indent=1)
        c = dict(c); c['file'] = fn
        done['cues'] = [x for x in done['cues'] if x['id'] != c['id']] + [c]
        json.dump(done, open(dpath, 'w'), indent=1)
    print('budget used (by seconds):', round(sum(x['credits'] for x in bud['spent'])), 'of', bud['limit_credits'])


if __name__ == '__main__':
    main()
