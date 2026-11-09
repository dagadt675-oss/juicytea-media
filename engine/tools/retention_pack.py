#!/usr/bin/env python3
"""retention_pack.py PACK_DIR TEMPORAL_JSON AUDIO_JSON TIMING_JSON SPEC_JSON MODULES_JSON MIX_JSON OUT_DIR
Material for the retention/fatigue panel (they cannot play the film, so they get the closest substitute):
  overview_NN.jpg  one frame every 4 s for the whole film, 6x5 per sheet, labelled
  script.md        every narration line with its time, chapter headers, chapter titles from the description
  pacing.md        per 30 s: words per minute, hard cuts, pops, abrupt motion, mean motion energy, music cue, chapter
Uses the context frames review_pack.py already extracted (PACK_DIR/_frames384, every 15th frame)."""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30.0
def mmss(t): return '%d:%02d' % (int(t) // 60, int(t) % 60)

def main():
    pack, tj, aj, timj, specj, modj, mixj, out = sys.argv[1:9]
    os.makedirs(out, exist_ok=True)
    T = json.load(open(tj)); A = json.load(open(aj)); TM = json.load(open(timj)); SP = json.load(open(specj)); MOD = json.load(open(modj)); MX = json.load(open(mixj))
    gd = np.load(tj.rsplit('.', 1)[0] + '_raw.npz')['gd']; N = len(gd)
    try: fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    except Exception: fnt = ImageFont.load_default()
    frames = list(range(0, N, 120))
    W, H, LB = 320, 180, 20
    for k in range(0, len(frames), 30):
        part = frames[k:k + 30]; rows = (len(part) + 5) // 6
        sh = Image.new('RGB', (6 * W, rows * (H + LB)), (20, 20, 20)); d = ImageDraw.Draw(sh)
        for j, f in enumerate(part):
            x, y = (j % 6) * W, (j // 6) * (H + LB)
            im = Image.open(os.path.join(pack, '_frames384', '%06d.jpg' % f)).resize((W, H))
            sh.paste(im, (x, y + LB)); d.text((x + 5, y + 1), mmss(f / FPS), fill=(255, 230, 80), font=fnt)
        sh.save(os.path.join(out, 'overview_%02d.jpg' % (k // 30 + 1)), quality=85)
    text = {s['id']: re.sub(r'\{[^}]*\}', '', s['text']) for s in SP['segments']}
    chap_titles = [(0, 'Why do the continents point south?'), (175, "What's on Earth's other side?"), (233, 'Can you dig to China?'),
                   (358, 'Is Earth secretly a pyramid?'), (481, 'Continental drift: why did geologists laugh at Wegener?'),
                   (604, 'Running the clock backwards'), (875, 'Where is the drip going next?')]
    with open(os.path.join(out, 'script.md'), 'w') as fh:
        fh.write('# Narration with times (16:51 total)\n\n')
        ci = 0
        for s in TM['segments']:
            while ci < len(chap_titles) and s['start'] >= chap_titles[ci][0] - 0.5:
                fh.write('\n## %s  %s\n\n' % (mmss(chap_titles[ci][0]), chap_titles[ci][1])); ci += 1
            fh.write('- [%s] %s\n' % (mmss(s['start']), text.get(s['id'], '')))
    words = TM['words']
    cue = lambda t: next((m['file'].rsplit('/', 1)[-1].split('_')[1] for m in MX['music'] if m['start'] <= t < m['end']), '-')
    mod = lambda t: next((m['id'] for m in MOD if m['t0'] <= t < m['t1']), '-')
    with open(os.path.join(out, 'pacing.md'), 'w') as fh:
        fh.write('Per 30 s window. wpm = narration words per minute; cuts = hard picture changes; pops = elements appearing/vanishing in one frame; '
                 'abrupt = motion starting or stopping with no easing; motion = mean frame difference (0-255; under ~0.3 is a near-still picture); '
                 'still_s = seconds in the window with motion under 0.15.\n\n| window | chapter module | music cue | wpm | cuts | pops | abrupt | motion | still_s |\n|---|---|---|---|---|---|---|---|---|\n')
        for s0 in range(0, int(N / FPS), 30):
            a, b = int(s0 * FPS), min(N, int((s0 + 30) * FPS))
            nw = sum(1 for w in words if s0 <= w['start'] < s0 + 30)
            c = sum(1 for x in T['cuts'] if s0 <= x['t'] < s0 + 30); p = sum(1 for x in T['pops'] if s0 <= x['t'] < s0 + 30)
            ab = sum(1 for x in T.get('abrupt_motion', []) if s0 <= x['t'] < s0 + 30)
            still = sum(1 for sec in range(s0, min(s0 + 30, int(N / FPS))) if gd[int(sec * FPS):int((sec + 1) * FPS)].mean() < 0.15)
            fh.write('| %s-%s | %s | %s | %d | %d | %d | %d | %.2f | %d |\n' % (mmss(s0), mmss(s0 + 30), mod(s0 + 15), cue(s0 + 15), nw * 2 * 30 / max(1, min(30, N / FPS - s0)), c, p, ab, gd[a:b].mean(), still))
        fh.write('\nNarration pauses over 1.2 s: %s\n' % json.dumps(A['narration_pauses_over_1_2s']))
    print('ok', len(frames), 'overview frames')

if __name__ == '__main__':
    main()
