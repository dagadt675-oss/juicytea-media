#!/usr/bin/env python3
"""music.py cues.json outdir
cues.json: {"global": "style words shared by all cues", "model": "music_v1",
            "cues": [{"id": "c1", "dur": 95.0, "prompt": "mood for this chapter", "take": 0}, ...]}
Generates one instrumental cue per entry with ElevenLabs Music (prompt-based, force_instrumental), length dur+3 s,
cached by content hash. Key read from ELEVENLABS_API_KEY (never printed)."""
import hashlib, json, os, sys, time, urllib.request

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    key = os.environ['ELEVENLABS_API_KEY']
    for c in spec['cues']:
        prompt = f"{spec.get('global','')}. {c['prompt']}".strip()
        ms = int(min(600, max(10, c['dur'] + 3)) * 1000)
        h = hashlib.sha1(json.dumps([prompt, ms, spec.get('model'), c.get('take', 0)]).encode()).hexdigest()[:10]
        fn = os.path.join(out, f"{c['id']}_{h}.mp3")
        if os.path.exists(fn): print('cached', fn); c['file'] = fn; continue
        body = {'prompt': prompt, 'music_length_ms': ms, 'force_instrumental': True}
        if spec.get('model'): body['model_id'] = spec['model']
        for a in range(4):
            try:
                req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', json.dumps(body).encode(), {'xi-api-key': key, 'Content-Type': 'application/json'})
                data = urllib.request.urlopen(req, timeout=600).read(); open(fn, 'wb').write(data); break
            except Exception as e:
                err = e; print('retry', c['id'], e, flush=True); time.sleep(10 * (a + 1))
        else:
            sys.exit(f'music failed for {c["id"]}: {err}')
        c['file'] = fn; print('wrote', fn, len(data), flush=True)
    json.dump(spec, open(os.path.join(out, 'cues_done.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
