#!/usr/bin/env python3
"""asr_clip.py T0 T1 [--wav PATH] [--model small.en] [--spec OUT.png]
Transcribes one stretch of audio (default: the narration stem audio/vo/vo_proc.wav) with faster-whisper and prints every
heard word with its absolute time and confidence. --spec also writes a spectrogram + waveform image of the stretch
(ffmpeg showspectrumpic / showwavespic) so clipped word tails, clicks or masking can be seen."""
import os, subprocess, sys
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
def main():
    t0, t1 = float(sys.argv[1]), float(sys.argv[2])
    wav = arg('--wav', os.path.join(BASE, 'audio', 'vo', 'vo_proc.wav')); model = arg('--model', 'small.en'); spec = arg('--spec', None)
    pcm = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', wav, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                                       capture_output=True, check=True).stdout, np.float32)
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=2)
    segs, _ = m.transcribe(pcm, language='en', word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    for s in segs:
        for w in s.words:
            print('%8.2f-%8.2f  p=%.2f  %s' % (t0 + w.start, t0 + w.end, w.probability, w.word))
    if spec:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t0), '-t', str(t1 - t0), '-i', wav, '-filter_complex',
                        '[0:a]aformat=channel_layouts=mono,asplit[a][b];[a]showspectrumpic=s=1400x360:legend=0:fscale=lin[s];'
                        '[b]showwavespic=s=1400x200:split_channels=0[w];[s][w]vstack=inputs=2:shortest=0', spec], check=False)
        print('image', spec)

if __name__ == '__main__':
    main()
