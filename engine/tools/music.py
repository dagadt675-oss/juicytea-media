#!/usr/bin/env python3
"""music.py cues.json outdir
cues.json: {"global": "style words shared by all cues", "model": "music_v1",
            "plan_global": {"positive": ["style", ...], "negative": ["vocals", ...]},
            "cues": [{"id": "c1", "dur": 95.0, "prompt": "mood for this chapter", "take": 0}, ...]}
Generates one instrumental cue per entry with ElevenLabs Music (prompt-based, force_instrumental), length dur+3 s,
cached by content hash. Key read from ELEVENLABS_API_KEY (never printed).

Composition-plan mode (sound_principles R10: make the music hit the picture): a cue with "plan": true and
"sections": [{"name", "duration_ms", "positive_local_styles", "negative_local_styles"}, ...] is sent as an ElevenLabs
composition plan instead of a prompt (music_v2/v2_5 chunks: text "[name]", duration_ms 3000-120000, positive_styles,
negative_styles), so each section starts where the picture needs it; the last section is stretched by 3 s like dur+3.
The API has no force_instrumental for plans: "instrumental" is added to every chunk and "vocals", "lyrics", "choir" to
its negatives, and the result must still pass a voice check (sfx_check.py music). plan_global styles go to the first
chunk, which sets the genre for the whole cue."""
import hashlib, json, os, sys, time, urllib.request

def plan_for(spec, c):
    pg = spec.get('plan_global', {}); secs = c['sections']; chunks = []
    for i, s in enumerate(secs):
        ms = int(s['duration_ms']) + (3000 if i == len(secs) - 1 else 0)
        pos = (list(pg.get('positive', [])) if i == 0 else []) + list(s.get('positive_local_styles', [])) + ['instrumental']
        neg = list(dict.fromkeys((list(pg.get('negative', [])) if i == 0 else []) + list(s.get('negative_local_styles', [])) + ['vocals', 'lyrics', 'choir']))
        chunks.append({'text': f"[{s['name'][:90]}]", 'duration_ms': min(120000, max(3000, ms)), 'positive_styles': pos[:50],
                       'negative_styles': neg[:50], 'context_adherence': s.get('context_adherence', 'high')})
    return {'chunks': chunks}

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    key = os.environ['ELEVENLABS_API_KEY']
    for c in spec['cues']:
        if c.get('plan'):
            body = {'composition_plan': plan_for(spec, c)}
            if c.get('seed') is not None: body['seed'] = c['seed']
            hkey = [body, spec.get('model'), c.get('take', 0)]
        else:
            prompt = f"{spec.get('global','')}. {c['prompt']}".strip()
            ms = int(min(600, max(10, c['dur'] + 3)) * 1000)
            body = {'prompt': prompt, 'music_length_ms': ms, 'force_instrumental': True}
            hkey = [prompt, ms, spec.get('model'), c.get('take', 0)]
        h = hashlib.sha1(json.dumps(hkey).encode()).hexdigest()[:10]
        fn = os.path.join(out, f"{c['id']}_{h}.mp3")
        if os.path.exists(fn): print('cached', fn); c['file'] = fn; continue
        if spec.get('model'): body['model_id'] = spec['model']
        for a in range(4):
            try:
                req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', json.dumps(body).encode(), {'xi-api-key': key, 'Content-Type': 'application/json'})
                data = urllib.request.urlopen(req, timeout=600).read(); open(fn, 'wb').write(data); break
            except Exception as e:
                err = e; detail = e.read()[:300] if hasattr(e, 'read') else b''
                print('retry', c['id'], e, detail, flush=True); time.sleep(10 * (a + 1))
        else:
            sys.exit(f'music failed for {c["id"]}: {err}')
        c['file'] = fn; print('wrote', fn, len(data), flush=True)
    json.dump(spec, open(os.path.join(out, 'cues_done.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
