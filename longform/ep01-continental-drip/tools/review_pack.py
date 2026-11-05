#!/usr/bin/env python3
"""review_pack.py VIDEO TEMPORAL_JSON AUDIO_JSON TIMING_JSON SPEC_JSON MODULES_JSON OUTDIR
Builds the material for the animation review agents, one folder per segment (OUTDIR/segNN/):
  sheet_KK.jpg   context frames every 15th frame (2 per second), 4x4 per sheet, 480x270, labelled mm:ss.ss / frame
  ev_XXX.jpg     one image per detected event: four consecutive frames (2x2, 640x360) around it, the changed block boxed
  motion.png     motion-energy plot (global frame difference per frame) with every event marked
  README.md      time range, chapter code files, narration lines with times, the events table, audio flags in range
Events come from temporal_scan.py (cuts, flashes, pops, chunk seams, abrupt stops/starts, judder)."""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30.0
def font(sz, bold=True):
    try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), sz)
    except Exception: return ImageFont.load_default()
def mmss(t): return '%d:%05.2f' % (int(t) // 60, t - 60 * (int(t) // 60))

def extract(video, frames, size, outdir):
    """Decode only the listed frame numbers (one pass, select filter) to outdir/NNNNNN.jpg."""
    frames = sorted(set(int(f) for f in frames if f >= 0))
    os.makedirs(outdir, exist_ok=True)
    todo = [f for f in frames if not os.path.exists(os.path.join(outdir, '%06d.jpg' % f))]
    if not todo: return
    tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    # select by ranges to keep the expression short
    rng, s = [], todo[0]; p = s
    for f in todo[1:]:
        if f == p + 1: p = f; continue
        rng.append((s, p)); s = p = f
    rng.append((s, p))
    for k in range(0, len(rng), 1200):
        part = rng[k:k + 1200]
        expr = '+'.join('between(n\\,%d\\,%d)' % (a, b) for a, b in part)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', f"select='{expr}',scale={size[0]}:{size[1]}:flags=area", '-vsync', '0', '-q:v', '3',
                        os.path.join(tmp, 'x_%06d.jpg')], check=True)
        got = sorted(os.listdir(tmp)); want = [f for a, b in part for f in range(a, b + 1)]
        for name, f in zip(got, want): os.replace(os.path.join(tmp, name), os.path.join(outdir, '%06d.jpg' % f))
        for name in os.listdir(tmp): os.remove(os.path.join(tmp, name))
    os.rmdir(tmp)

def main():
    video, tj, aj, timj, specj, modj, out = sys.argv[1:8]
    T = json.load(open(tj)); A = json.load(open(aj)); TM = json.load(open(timj)); SP = json.load(open(specj)); MOD = json.load(open(modj))
    raw = np.load(tj.rsplit('.', 1)[0] + '_raw.npz'); gd = raw['gd']; N = len(gd)
    text = {s['id']: re.sub(r'\{[^}]*\}', '', s['text']) for s in SP['segments']}
    lines = [(s['start'], s['end'], s['id'], text.get(s['id'], '')) for s in TM['segments']]
    # segments: split long chapters at the narration line nearest their middle
    segs = []
    for m in MOD:
        t0, t1 = m['t0'], m['t1']
        if t1 - t0 > 140:
            mid = (t0 + t1) / 2
            cut = min((l[0] for l in lines if t0 + 30 < l[0] < t1 - 30), key=lambda x: abs(x - mid))
            cut = round(cut - 0.15, 2)
            segs += [(m['id'], t0, cut), (m['id'], cut, t1)]
        else: segs.append((m['id'], t0, t1))
    segs[-1] = (segs[-1][0], segs[-1][1], N / FPS)
    # events
    ev = []
    for c in T['cuts']: ev.append(('cut', c['frame'], c))
    for c in T['flashes']: ev.append(('flash', c['frame'], c))
    for c in T['pops']: ev.append(('pop', c['frame'], c))
    for c in T['seams_suspicious']: ev.append(('seam', c['frame'], c))
    for c in T.get('abrupt_motion', []): ev.append(('motion_' + c['kind'], c['frame'], c))
    for c in T.get('judder', []): ev.append(('judder', int(round(c['t0'] * FPS)), c))
    ev.sort(key=lambda e: e[1])
    # merge events closer than 4 frames into one strip
    groups = []
    for e in ev:
        if groups and e[1] - groups[-1][-1][1] <= 3: groups[-1].append(e)
        else: groups.append([e])
    need = set()
    for g in groups:
        f = g[0][1]
        for k in range(f - 2, f + 2): need.add(min(max(k, 0), N - 1))
    ctx = list(range(0, N, 15))
    fdir = os.path.join(out, '_frames400'); cdir = os.path.join(out, '_frames384')
    extract(video, sorted(need), (400, 225), fdir)
    extract(video, ctx, (384, 216), cdir)
    F14, F18, F22 = font(14), font(18), font(22)
    index = []
    for si, (mid, t0, t1) in enumerate(segs, 1):
        sd = os.path.join(out, 'seg%02d' % si); os.makedirs(sd, exist_ok=True)
        # context sheets
        fr = [f for f in ctx if t0 * FPS <= f < t1 * FPS]
        sheets = []
        for k in range(0, len(fr), 20):
            part = fr[k:k + 20]; W, H, LB = 384, 216, 20
            sh = Image.new('RGB', (5 * W, 4 * (H + LB)), (20, 20, 20)); d = ImageDraw.Draw(sh)
            for j, f in enumerate(part):
                x, y = (j % 5) * W, (j // 5) * (H + LB)
                sh.paste(Image.open(os.path.join(cdir, '%06d.jpg' % f)), (x, y + LB))
                d.text((x + 5, y + 1), '%s  f%d' % (mmss(f / FPS), f), fill=(255, 230, 80), font=F14)
            p = os.path.join(sd, 'sheet_%02d.jpg' % (k // 20 + 1)); sh.save(p, quality=85); sheets.append(p)
        # event filmstrips: 4 consecutive frames per event in a row, 4 events per image
        rows = []
        segg = [g for g in groups if t0 * FPS <= g[0][1] < t1 * FPS]
        W, H, LB, HD = 400, 225, 20, 26
        for k in range(0, len(segg), 4):
            part = segg[k:k + 4]
            im = Image.new('RGB', (4 * W, len(part) * (H + LB + HD)), (20, 20, 20)); d = ImageDraw.Draw(im)
            for r, g in enumerate(part):
                f = g[0][1]; eid = k + r + 1; y0 = r * (H + LB + HD)
                kinds = '+'.join(sorted(set(e[0] for e in g)))
                d.text((6, y0 + 3), 'E%d  %s  at %s (frame %d)' % (eid, kinds.upper(), mmss(f / FPS), f), fill=(255, 120, 90), font=F18)
                for j, fk in enumerate(range(f - 2, f + 2)):
                    kk = min(max(fk, 0), N - 1); x = j * W
                    fimg = Image.open(os.path.join(fdir, '%06d.jpg' % kk)).convert('RGB')
                    if fk == f:
                        dd = ImageDraw.Draw(fimg); dd.rectangle([1, 1, W - 2, H - 2], outline=(255, 60, 60), width=2)
                        for e in g:
                            if e[0] == 'pop':
                                bx, by = e[2]['where_xy']
                                dd.rectangle([bx * W - 18, by * H - 18, bx * W + 18, by * H + 18], outline=(255, 0, 200), width=2)
                    im.paste(fimg, (x, y0 + HD + LB))
                    d.text((x + 5, y0 + HD + 1), '%s f%d%s' % (mmss(kk / FPS), kk, ' (event)' if fk == f else ''), fill=(255, 230, 80), font=F14)
                info = '; '.join('%s %s' % (e[0], json.dumps({kk: vv for kk, vv in e[2].items() if kk not in ('frame',)})) for e in g)
                rows.append(('events_%02d.jpg' % (k // 4 + 1), eid, f, kinds, info))
            im.save(os.path.join(sd, 'events_%02d.jpg' % (k // 4 + 1)), quality=85)
        # motion plot
        a, b = int(t0 * FPS), min(N, int(t1 * FPS))
        PW, PH, M = 1900, 420, 40
        pl = Image.new('RGB', (PW, PH), (250, 250, 250)); d = ImageDraw.Draw(pl)
        y = np.clip(gd[a:b], 0, 20); xs = M + (np.arange(len(y)) / max(1, len(y) - 1)) * (PW - 2 * M); ys = PH - M - y / 20 * (PH - 2 * M)
        for t in range(int(np.ceil(t0)), int(t1) + 1):
            X = M + (t * FPS - a) / max(1, b - a - 1) * (PW - 2 * M)
            d.line([(X, M), (X, PH - M)], fill=(225, 225, 225) if t % 5 else (190, 190, 190))
            if t % 5 == 0: d.text((X - 18, PH - M + 6), mmss(t)[:-3], fill=(60, 60, 60), font=F14)
        col = {'cut': (200, 0, 0), 'flash': (255, 0, 200), 'pop': (0, 120, 255), 'seam': (255, 140, 0), 'judder': (0, 160, 0)}
        for _, _e, f, kinds, _i in rows:
            X = M + (f - a) / max(1, b - a - 1) * (PW - 2 * M); c = col.get(kinds.split('+')[0], (120, 0, 160))
            d.line([(X, M), (X, M + 18)], fill=c, width=3)
        d.line(list(zip(xs.tolist(), ys.tolist())), fill=(30, 30, 30), width=1)
        d.text((M, 8), 'motion energy (mean |frame difference|, clipped at 20) %s - %s.  marks: red cut, magenta flash, blue pop, orange chunk seam, green judder, purple abrupt stop/start' % (mmss(t0), mmss(t1)), fill=(0, 0, 0), font=F14)
        pl.save(os.path.join(sd, 'motion.png'))
        # audio flags in range
        af = []
        for c in A['vo_cuts']:
            if c['kind'] == 'offset' and t0 <= c['t'] < t1: af.append('voice tail cut abruptly at %s (level %s dB -> %s dB within 16 ms)' % (mmss(c['t']), c['before_db'], c['after_db']))
        for m in A['masking']:
            if t0 <= m['t0'] < t1: af.append('music/SFX within 8 dB of the voice %s-%s (worst margin %s dB)' % (mmss(m['t0']), mmss(m['t1']), m['min_margin_db']))
        with open(os.path.join(sd, 'README.md'), 'w') as fh:
            fh.write('# Segment %02d: %s - %s (module %s, file engine/www/ep/ep01/%s*.js)\n\n' % (si, mmss(t0), mmss(t1), mid, mid))
            fh.write('Frame n is shown at time n/30 s. Video: deliver/ep01/video_final.mp4 (1920x1080, 30 fps).\n\n## Narration\n\n')
            for l in lines:
                if l[1] > t0 and l[0] < t1: fh.write('- [%s - %s] %s\n' % (mmss(l[0]), mmss(l[1]), l[3]))
            fh.write('\n## Context sheets (every 15th frame)\n\n' + '\n'.join('- ' + os.path.basename(p) for p in sheets) + '\n')
            fh.write('\n## Detected events (%d; each filmstrip row shows frames f-2, f-1, f, f+1; the event frame f is outlined red, a changed block magenta)\n\n| event | image | time | frame | kind | detector data |\n|---|---|---|---|---|---|\n' % len(rows))
            for img, eid, f, kinds, info in rows: fh.write('| E%d | %s | %s | %d | %s | %s |\n' % (eid, img, mmss(f / FPS), f, kinds, info.replace('|', '/')))
            fh.write('\n## Audio flags in this range\n\n' + ('\n'.join('- ' + x for x in af) if af else '- none') + '\n')
        index.append({'seg': si, 'module': mid, 't0': round(t0, 2), 't1': round(t1, 2), 'dir': sd, 'sheets': len(sheets), 'events': len(rows)})
    json.dump(index, open(os.path.join(out, 'index.json'), 'w'), indent=1)
    for x in index: print(x)

if __name__ == '__main__':
    main()
