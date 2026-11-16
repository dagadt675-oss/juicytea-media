#!/usr/bin/env python3
"""Round-1 BLIND feed renders: each candidate pair in 2 feeds (mobile Suggested list = 'upnext' layout with 7
hawaii hosts; mobile Home = 'home' layout with 3 hosts). Output files feeds/r1_<n>.png are numbered in a seeded
shuffled order so the number reveals neither the candidate nor the slot; the key goes to feeds/r1_key.json.
The image is the full feed as a long phone screenshot (the *_scroll render, scale 1 = true layout size) so every
host card is in the stimulus. Intermediate renders (whose JSON flags the candidate) go to a temp dir and are deleted."""
import json, os, random, shutil, subprocess, sys
from PIL import Image

PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
FEEDSIM = f'{PK}/feedsim/feedsim.py'
HOSTS = f'{PK}/refs/hosts/hosts.json'
AVATAR = f'{PK}/feedsim/ours_avatar.jpg'
OUT = f'{PK}/feeds'
TMP = f'{PK}/feedsim/blind/_render'
MASTER_SEED = 20261108

PAIRS = json.load(open(sys.argv[1]))
CHAN = {i['id']: i['channel'] for v in json.load(open(HOSTS)).values() for i in v}
OURS = dict(channel='Myth Juice', views='1.2K views', age='2d ago', duration='12:53', avatar=AVATAR)
# 'age' uses YouTube's short form ("2d ago") because every host card uses it; a long form on ours alone would give it away.
SURF = {'suggested': dict(layout='upnext', n=8, image='upnext_scroll', hosts=7),
        'home': dict(layout='home', n=4, image='home_scroll', hosts=3)}

rng = random.Random(MASTER_SEED)
# balanced, seeded candidate slots: home 4 slots x3, suggested 8 slots + 4 extra
slots = {'home': [k % 4 for k in range(len(PAIRS))], 'suggested': [k % 8 for k in range(len(PAIRS))]}
for v in slots.values(): rng.shuffle(v)
jobs = []
for ci, p in enumerate(PAIRS):
    src = os.path.basename(os.path.dirname(p['thumb']))
    for sname in ('suggested', 'home'):
        jobs.append(dict(cand_index=ci + 1, cand_id=p['id'], design_set=src, label=f"{src}/{p['id']}",
                         title=p['title'], thumb=p['thumb'], surface=sname, pos=slots[sname][ci],
                         seed=rng.randrange(1, 10 ** 6)))
order = list(range(len(jobs))); rng.shuffle(order)  # file number n -> job, shuffled

os.makedirs(TMP, exist_ok=True)
key = dict(round='r1', created='2026-11-08', master_seed=MASTER_SEED, tool='feedsim/feedsim.py (scale 1, dark mode, JPEG q98 render saved as PNG); driver feedsim/blind/blind_r1.py feedsim/blind/r1_pairs.json',
           hosts_set='refs/hosts/hosts.json#hawaii', now_playing='34Ojnyi9xLw (RealLifeLore) on the Suggested surface',
           ours_card=OURS | dict(avatar='feedsim/ours_avatar.jpg'),
           surfaces={'suggested': 'mobile watch page, compact Up next list (168x94 thumbs), 8 cards = candidate + 7 hosts, full page as a long screenshot',
                     'home': 'mobile Home feed, full-width 390 pt cards, 4 cards = candidate + 3 hosts, full feed as a long screenshot'},
           position_note='position = 0-based slot of our card in the list (0 = top card); card_rects are pixel boxes in the PNG',
           files=[])
for n, j in enumerate(order, start=1):
    job = jobs[j]; s = SURF[job['surface']]
    spec = dict(candidate=dict(OURS, id='X', thumb=job['thumb'], title=job['title']), hosts=HOSTS + '#hawaii',
                now_playing='34Ojnyi9xLw', seed=job['seed'], n={s['layout']: s['n']})
    sp = f'{TMP}/spec_{n}.json'; json.dump(spec, open(sp, 'w'))
    pre = f'{TMP}/f{n}'
    subprocess.run([sys.executable, '-I', FEEDSIM, sp, '--out', pre, '--layouts', s['layout'], '--scale', '1', '--quality', '98',
                    '--seed', str(job['seed']), '--pos', f"{s['layout']}={job['pos']}"], check=True, stdout=subprocess.DEVNULL)
    meta = json.load(open(f"{pre}_{s['image']}.json"))
    cards = meta['cards']
    ci = [k for k, c in enumerate(cards) if c.get('tag') == 'candidate' or c.get('id') == 'X']
    assert len(ci) == 1 and ci[0] == job['pos'], (n, ci, job['pos'])
    assert len(cards) == s['n'], (n, len(cards))
    fn = f'{OUT}/r1_{n}.png'
    Image.open(f"{pre}_{s['image']}.jpg").save(fn, optimize=True)
    key['files'].append(dict(file=os.path.basename(fn), path=fn, surface=job['surface'], layout=s['image'],
                             candidate_label=job['label'], candidate_id=job['cand_id'], design_set=job['design_set'],
                             candidate_index_in_request=job['cand_index'], title=job['title'], thumb=job['thumb'],
                             position=job['pos'], n_cards=s['n'], seed=job['seed'],
                             cards=[dict(slot=k, ours=(k == job['pos']), title=c.get('title'), channel=('Myth Juice' if k == job['pos'] else CHAN.get(c.get('id'))),
                                         id=(None if k == job['pos'] else c.get('id')), thumb_rect=c.get('thumb'), card_rect=c.get('card'))
                                    for k, c in enumerate(cards)]))
    print(fn, job['surface'], job['label'], 'pos', job['pos'])
json.dump(key, open(f'{OUT}/r1_key.json', 'w'), indent=1)
shutil.rmtree(TMP)
