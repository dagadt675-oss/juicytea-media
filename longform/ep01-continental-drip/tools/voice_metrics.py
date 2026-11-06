import sys, numpy as np, librosa, warnings
warnings.filterwarnings('ignore')
from faster_whisper import WhisperModel
ref = "right now about two miles beneath your feet there is something no human being has ever seen not once we have photographed the far side of the moon we have landed on mars but this place we have only ever heard it".split()
m = WhisperModel('base.en', device='cpu', compute_type='int8')
print(f"{'voice':10} {'dur':>5} {'wps':>5} {'f0med':>6} {'f0sd_st':>7} {'rmsDR':>6} {'sil%':>5} {'wer':>5} {'bright':>6}")
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=22050)
    dur = len(y) / sr
    f0, vf, vp = librosa.pyin(y, fmin=55, fmax=300, sr=sr, frame_length=1024)
    f0v = f0[~np.isnan(f0)]
    st = 12 * np.log2(f0v / np.median(f0v))
    rms = librosa.feature.rms(y=y)[0]; rdb = 20*np.log10(rms+1e-6)
    speech = rdb > (rdb.max() - 35)
    dr = np.percentile(rdb[speech], 95) - np.percentile(rdb[speech], 20)
    sil = 1 - speech.mean()
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0][speech].mean()
    segs, _ = m.transcribe(y if sr == 16000 else librosa.resample(y, orig_sr=sr, target_sr=16000), beam_size=5)
    hyp = ' '.join(s.text for s in segs).lower()
    hyp = ''.join(ch if ch.isalnum() or ch == ' ' else ' ' for ch in hyp).split()
    # simple WER via edit distance
    d = np.zeros((len(ref)+1, len(hyp)+1), int); d[:,0] = range(len(ref)+1); d[0,:] = range(len(hyp)+1)
    for i in range(1, len(ref)+1):
        for j in range(1, len(hyp)+1):
            d[i,j] = min(d[i-1,j]+1, d[i,j-1]+1, d[i-1,j-1] + (ref[i-1] != hyp[j-1]))
    wer = d[-1,-1] / len(ref)
    print(f"{f.split('/')[-1][:-4]:10} {dur:5.1f} {43/dur:5.2f} {np.median(f0v):6.1f} {st.std():7.2f} {dr:6.1f} {sil*100:5.1f} {wer:5.2f} {cent:6.0f}")
