#!/usr/bin/env python3
"""tts.py segments.json outdir [--voice ID] [--model eleven_v4] [--force id1,id2] [--only id1,id2]
segments.json: {"voice": "...", "model": "...", "settings": {...}, "segments": [{"id": "s01", "text": "...", "pause": 0.45, "speed": 1.0}, ...]}
Text may contain markers {m:name} placed right before a word; they are stripped for synthesis and resolved to word times.
Each segment -> outdir/seg/<id>.mp3 + <id>.json (alignment). Cached by content hash (text+voice+model+settings).
Then assembles outdir/vo.wav (48 kHz mono) trimming each take to [first char - 60 ms, last char + 90 ms] and inserting the pauses,
and writes outdir/timing.json: {duration, segments:[{id,start,end}], words:[{w,start,end,seg}], markers:{name:{start,end,word}}}.
The ElevenLabs key is read from ELEVENLABS_API_KEY (never printed)."""
import base64, hashlib, json, os, re, subprocess, sys, time, urllib.request
import numpy as np, soundfile as sf

def key():
    k = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if not k: sys.exit('ELEVENLABS_API_KEY not set')
    return k

MARK = re.compile(r'\{m:([A-Za-z0-9_\-]+)\}')

def strip_markers(text):
    marks, out, i = [], [], 0
    for m in MARK.finditer(text):
        out.append(text[i:m.start()]); marks.append((m.group(1), sum(len(x) for x in out))); i = m.end()
    out.append(text[i:])
    clean = ''.join(out)
    # collapse double spaces created by marker removal
    return clean, marks

def synth(text, prev, nxt, voice, model, settings, speed, out_mp3):
    body = {'text': text, 'model_id': model}
    if prev: body['previous_text'] = prev
    if nxt: body['next_text'] = nxt
    vs = dict(settings or {})
    if speed: vs['speed'] = float(speed)
    if vs: body['voice_settings'] = vs
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_192'
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), {'xi-api-key': key(), 'Content-Type': 'application/json'})
            d = json.loads(urllib.request.urlopen(req, timeout=300).read())
            open(out_mp3, 'wb').write(base64.b64decode(d['audio_base64']))
            return d.get('alignment') or d.get('normalized_alignment')
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    raise RuntimeError(f'TTS failed: {err}')

def load_wav(mp3, sr=48000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def words_from_alignment(al, offset, t_shift):
    chars, st, en = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
    words, cur, cs, ce, ci0 = [], '', None, None, None
    for i, c in enumerate(chars):
        if c.isspace():
            if cur: words.append({'w': cur, 'start': cs - t_shift + offset, 'end': ce - t_shift + offset, 'c0': ci0, 'c1': i}); cur = ''
            continue
        if not cur: cs, ci0 = st[i], i
        cur += c; ce = en[i]
    if cur: words.append({'w': cur, 'start': cs - t_shift + offset, 'end': ce - t_shift + offset, 'c0': ci0, 'c1': len(chars)})
    return words

def main():
    spec_path, outdir = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    def opt(k, d=None):
        return args[args.index(k) + 1] if k in args else d
    spec = json.load(open(spec_path))
    voice = opt('--voice', spec.get('voice', 'nPczCjzI2devNBz1zQrb'))
    model = opt('--model', spec.get('model', 'eleven_v4'))
    settings = spec.get('settings', {})
    force = set((opt('--force', '') or '').split(',')) - {''}
    only = set((opt('--only', '') or '').split(',')) - {''}
    segs = spec['segments']
    os.makedirs(os.path.join(outdir, 'seg'), exist_ok=True)
    SR = 48000
    cleaned = [strip_markers(s['text']) for s in segs]
    for i, s in enumerate(segs):
        if only and s['id'] not in only: continue
        text = cleaned[i][0]
        prev = cleaned[i - 1][0] if i > 0 and not s.get('fresh') else ''
        nxt = cleaned[i + 1][0] if i + 1 < len(segs) else ''
        h = hashlib.sha1(json.dumps([text, voice, model, settings, s.get('speed'), s.get('take', 0)]).encode()).hexdigest()[:12]
        mp3 = os.path.join(outdir, 'seg', f"{s['id']}.mp3"); meta = mp3[:-4] + '.json'
        if os.path.exists(meta) and json.load(open(meta)).get('hash') == h and s['id'] not in force:
            continue
        al = synth(text, prev[-600:], nxt[:300], voice, model, settings, s.get('speed'), mp3)
        json.dump({'hash': h, 'text': text, 'alignment': al}, open(meta, 'w'))
        print('synth', s['id'], len(text), 'chars', flush=True)
    # assemble
    track, t = [], 0.0
    allw, segt, markers = [], [], {}
    lead = float(spec.get('lead_in', 0.0))
    if lead > 0: track.append(np.zeros(int(lead * SR), np.float32)); t = lead
    for i, s in enumerate(segs):
        mp3 = os.path.join(outdir, 'seg', f"{s['id']}.mp3"); meta = json.load(open(mp3[:-4] + '.json'))
        al = meta['alignment']; y = load_wav(mp3, SR)
        st = al['character_start_times_seconds']; en = al['character_end_times_seconds']
        nonsp = [k for k, c in enumerate(al['characters']) if not c.isspace()]
        a = max(0.0, st[nonsp[0]] - 0.06); b = min(len(y) / SR, en[nonsp[-1]] + 0.09)
        clip = y[int(a * SR):int(b * SR)]
        # 8 ms fades to avoid clicks
        fl = int(0.008 * SR); clip[:fl] *= np.linspace(0, 1, fl); clip[-fl:] *= np.linspace(1, 0, fl)
        ws = words_from_alignment(al, t, a)
        for w in ws: w['seg'] = s['id']
        # markers: char offset in clean text -> word containing/after it
        for name, ci in cleaned[i][1]:
            cand = [w for w in ws if w['c1'] > ci]
            if cand: markers[name] = {'start': round(cand[0]['start'], 3), 'end': round(cand[0]['end'], 3), 'word': cand[0]['w'], 'seg': s['id']}
        segt.append({'id': s['id'], 'start': round(t, 3), 'end': round(t + len(clip) / SR, 3)})
        allw += ws
        track.append(clip); t += len(clip) / SR
        pause = float(s.get('pause', 0.35))
        track.append(np.zeros(int(pause * SR), np.float32)); t += pause
    vo = np.concatenate(track)
    sf.write(os.path.join(outdir, 'vo.wav'), vo, SR, subtype='PCM_24')
    for w in allw: w.pop('c0', None); w.pop('c1', None); w['start'] = round(w['start'], 3); w['end'] = round(w['end'], 3)
    json.dump({'duration': round(t, 3), 'segments': segt, 'words': allw, 'markers': markers}, open(os.path.join(outdir, 'timing.json'), 'w'), indent=0)
    nwords = len(allw); speech = sum(w['end'] - w['start'] for w in allw)
    print(f'vo.wav {t:.1f} s, {nwords} words, {nwords / t * 60:.0f} wpm overall, {len(markers)} markers')

if __name__ == '__main__':
    main()
