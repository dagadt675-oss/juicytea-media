#!/usr/bin/env python3
"""asr_check.py VO_WAV TIMING_JSON OUT_JSON [MODEL] [THREADS]
Transcribes the narration stem with faster-whisper (word timestamps) and aligns the heard words with the script words
(timing.json) to list where the voice may not say what the script says: substitutions, dropped or extra words,
and words the recogniser heard with low confidence. Proper nouns and spelled-out numbers produce expected
mismatches; each mismatch carries both versions and times so a reviewer can judge it."""
import json, re, sys, difflib, subprocess
import numpy as np
from faster_whisper import WhisperModel

def norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))

def main():
    wav, timing, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    model_name = sys.argv[4] if len(sys.argv) > 4 else 'small.en'
    threads = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    model = WhisperModel(model_name, device='cpu', compute_type='int8', cpu_threads=threads)
    # decode with ffmpeg to 16 kHz mono float32 (avoids the PyAV API mismatch in faster-whisper's own decoder)
    pcm = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    segs, info = model.transcribe(pcm, language='en', word_timestamps=True, beam_size=5, condition_on_previous_text=False, vad_filter=False)
    heard = []
    for s in segs:
        for w in s.words:
            heard.append({'w': w.word.strip(), 'n': norm(w.word), 't0': round(w.start, 2), 't1': round(w.end, 2), 'p': round(w.probability, 3)})
    T = json.load(open(timing))['words']
    script = [{'w': x.get('word', x.get('w')), 'n': norm(x.get('word', x.get('w', ''))), 't0': x['start'], 't1': x['end']} for x in T]
    script = [x for x in script if x['n']]
    heard = [x for x in heard if x['n']]
    sm = difflib.SequenceMatcher(a=[x['n'] for x in script], b=[x['n'] for x in heard], autojunk=False)
    diffs = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == 'equal': continue
        sa, hb = script[a0:a1], heard[b0:b1]
        t = sa[0]['t0'] if sa else (hb[0]['t0'] if hb else None)
        diffs.append({'op': op, 't': t, 'script': ' '.join(x['w'] for x in sa), 'heard': ' '.join(x['w'] for x in hb),
                      'heard_conf': [x['p'] for x in hb]})
    lowconf = [x for x in heard if x['p'] < 0.45]
    out = {'model': model_name, 'script_words': len(script), 'heard_words': len(heard), 'match_ratio': round(sm.ratio(), 4),
           'diffs': diffs, 'low_confidence_words': lowconf, 'transcript': ' '.join(x['w'] for x in heard)}
    json.dump(out, open(outp, 'w'), indent=1)
    print(f'{model_name}: script {len(script)} words, heard {len(heard)}, ratio {sm.ratio():.3f}, diffs {len(diffs)}, low-confidence {len(lowconf)}')

if __name__ == '__main__':
    main()
