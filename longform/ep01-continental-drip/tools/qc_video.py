#!/usr/bin/env python3
"""qc_video.py video.mp4 outdir [--sheet N]
Automated QC for a rendered long-form video:
  - integrated loudness (LUFS), true peak (dBTP), loudness range (ffmpeg ebur128)
  - black frames / near-black stretches (> 0.5 s), frozen/static stretches (> 3.5 s with no visual change)
  - visual change cadence: mean/max seconds between significant changes (scene-score based)
  - silence gaps in audio (> 1.2 s below -45 dBFS)
  - contact sheet of N evenly spaced frames (default 24) + per-minute sheet
Writes outdir/qc.json and sheets; prints a PASS/FAIL summary.
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def main():
    vid, out = sys.argv[1], sys.argv[2]
    n_sheet = int(sys.argv[sys.argv.index('--sheet') + 1]) if '--sheet' in sys.argv else 24
    os.makedirs(out, exist_ok=True)
    dur = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vid]).stdout.strip())
    res = {'duration_s': dur}
    # loudness
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', vid, '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-'])
    tail = r.stderr[r.stderr.rfind('Summary:'):]
    def grab(pat):
        m = re.search(pat, tail); return float(m.group(1)) if m else None
    res['lufs_integrated'] = grab(r'I:\s+(-?[\d.]+) LUFS')
    res['loudness_range_lu'] = grab(r'LRA:\s+(-?[\d.]+) LU')
    res['true_peak_dbtp'] = grab(r'Peak:\s+(-?[\d.]+) dBFS')
    # silence
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', vid, '-af', 'silencedetect=noise=-45dB:d=1.2', '-f', 'null', '-'])
    sil = [(float(a), float(b)) for a, b in re.findall(r'silence_start: (-?[\d.]+).*?silence_end: (-?[\d.]+)', r.stderr, re.S)]
    res['silence_gaps'] = [[round(a, 2), round(b, 2)] for a, b in sil]
    # black frames
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', vid, '-vf', 'blackdetect=d=0.5:pix_th=0.08', '-an', '-f', 'null', '-'])
    res['black_stretches'] = [[float(a), float(b)] for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', r.stderr)]
    # visual change cadence via scene score on a downscaled stream (every frame)
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', vid, '-vf', "scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score", '-an', '-f', 'null', '-'])
    scores = [(float(t), float(s)) for t, s in re.findall(r'pts_time:([\d.]+)[^\n]*\n[^\n]*lavfi.scene_score=([\d.]+)', r.stderr)]
    # a "change" = scene_score > 0.004 accumulated motion; static if consecutive frames are nearly identical
    static, start = [], None
    for t, s in scores:
        if s < 0.0008:
            if start is None: start = t
        else:
            if start is not None and t - start > 3.5: static.append([round(start, 2), round(t, 2)])
            start = None
    if start is not None and scores and scores[-1][0] - start > 3.5: static.append([round(start, 2), round(scores[-1][0], 2)])
    res['static_stretches_over_3_5s'] = static
    cuts = [t for t, s in scores if s > 0.25]
    res['hard_cuts'] = len(cuts)
    gaps = [b - a for a, b in zip([0] + cuts, cuts + [dur])]
    res['mean_s_between_cuts'] = round(sum(gaps) / max(1, len(gaps)), 2)
    res['max_s_between_cuts'] = round(max(gaps) if gaps else dur, 2)
    # contact sheet
    tmp = os.path.join(out, '_f'); os.makedirs(tmp, exist_ok=True)
    times = [dur * (i + 0.5) / n_sheet for i in range(n_sheet)]
    ims = []
    for i, t in enumerate(times):
        fp = os.path.join(tmp, f'{i:03d}.jpg')
        run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', vid, '-frames:v', '1', '-vf', 'scale=480:-2', fp])
        if os.path.exists(fp): ims.append((t, Image.open(fp).convert('RGB')))
    cols = 4; rows = (len(ims) + cols - 1) // cols
    if ims:
        w, h = ims[0][1].size
        sheet = Image.new('RGB', (cols * w, rows * (h + 22)), (15, 15, 15)); d = ImageDraw.Draw(sheet)
        for i, (t, im) in enumerate(ims):
            x, y = (i % cols) * w, (i // cols) * (h + 22); sheet.paste(im, (x, y)); d.text((x + 6, y + h + 4), f'{int(t)//60:02d}:{t%60:05.2f}', fill=(255, 220, 0))
        sheet.save(os.path.join(out, 'sheet.jpg'), quality=85)
    # verdicts
    fails = []
    if res['lufs_integrated'] is not None and not (-15.5 <= res['lufs_integrated'] <= -12.5): fails.append(f"LUFS {res['lufs_integrated']} outside -14±1.5")
    if res['true_peak_dbtp'] is not None and res['true_peak_dbtp'] > -1.0: fails.append(f"true peak {res['true_peak_dbtp']} > -1.0 dBTP")
    if res['black_stretches']: fails.append(f"black stretches {res['black_stretches'][:5]}")
    if res['static_stretches_over_3_5s']: fails.append(f"static stretches {res['static_stretches_over_3_5s'][:8]}")
    inner_sil = [g for g in res['silence_gaps'] if g[0] > 1.0 and g[1] < dur - 3]
    if inner_sil: fails.append(f"silence gaps {inner_sil[:6]}")
    res['fails'] = fails; res['verdict'] = 'PASS' if not fails else 'FAIL'
    json.dump(res, open(os.path.join(out, 'qc.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('silence_gaps',)}, indent=1)[:3000])

if __name__ == '__main__':
    main()
