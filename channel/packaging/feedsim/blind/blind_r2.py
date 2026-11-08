#!/usr/bin/env python3
"""Round-2 BLIND feed renders (same method as blind_r1.py, now episode-aware).

  python3 -I blind_r2.py r2_cands.json

Each candidate is rendered in 2 feeds:
  * suggested: mobile watch page, compact Up next list ('upnext' layout), candidate + 7 hosts of ITS episode
    (ep02 -> refs/hosts/hosts.json#hawaii, now playing RealLifeLore 34Ojnyi9xLw;
     ep01 -> refs/hosts/hosts.json#ep01,   now playing Atlas Pro VKq0pr4rbRs), the now-playing video excluded;
  * home: mobile Home feed ('home' layout), candidate + 3 hosts of its episode.
The image is the full feed as a long phone screenshot (the *_scroll render, scale 1 = true layout size).
Our card: "Myth Juice", "1.2K views", "2d ago" for every candidate, the control included.
Slots are seeded random draws WITHOUT replacement inside each (episode, surface) group, so a viewer who sees
several feeds of one episode cannot learn 'our' slot. File numbers n in feeds/r2_<n>.png follow a seeded shuffle
of the jobs, so neither the number nor the file order reveals the candidate or the slot. Intermediate renders
(whose JSON flags the candidate) go to a temp dir that is deleted; the key goes to feeds/r2_key.json."""
import json, os, random, shutil, subprocess, sys
from PIL import Image

PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
FEEDSIM = f'{PK}/feedsim/feedsim.py'
HOSTS = f'{PK}/refs/hosts/hosts.json'
AVATAR = f'{PK}/feedsim/ours_avatar.jpg'
OUT = f'{PK}/feeds'
TMP = f'{PK}/feedsim/blind/_render_r2'
MASTER_SEED = 2026110802
ROUND = 'r2'

CANDS = json.load(open(sys.argv[1]))
HDB = json.load(open(HOSTS))
CHAN = {i['id']: i['channel'] for v in HDB.values() for i in v}
# 'age' uses YouTube's short form ("2d ago" = "2 days ago") because every host card uses the short form
# ("4d ago", "1y ago"); a long form on our card alone would give it away.
OURS = dict(channel='Myth Juice', views='1.2K views', age='2d ago', avatar=AVATAR)
EP = {'ep02': dict(hosts='hawaii', now_playing='34Ojnyi9xLw', duration='12:53'),
      'ep01': dict(hosts='ep01', now_playing='VKq0pr4rbRs', duration='15:34')}
SURF = {'suggested': dict(layout='upnext', n=8, image='upnext_scroll', hosts=7),
        'home': dict(layout='home', n=4, image='home_scroll', hosts=3)}

rng = random.Random(MASTER_SEED)
slots = {}
for ep in EP:
    group = [c for c in CANDS if c['ep'] == ep]
    for sname, s in SURF.items():
        assert len(group) <= s['n'], (ep, sname)
        draw = rng.sample(range(s['n']), len(group))
        for c, p in zip(group, draw): slots[(c['id'], sname)] = p
jobs = []
for ci, c in enumerate(CANDS):
    for sname in ('suggested', 'home'):
        jobs.append(dict(cand_index=ci + 1, cand=c, surface=sname, pos=slots[(c['id'], sname)], seed=rng.randrange(1, 10 ** 6)))
order = list(range(len(jobs))); rng.shuffle(order)  # file number n -> job, shuffled

os.makedirs(TMP, exist_ok=True)
key = dict(round=ROUND, created='2026-11-08', master_seed=MASTER_SEED,
           tool='feedsim/feedsim.py (scale 1, dark mode, JPEG q98 render saved as PNG); driver feedsim/blind/blind_r2.py feedsim/blind/r2_cands.json',
           episodes={ep: dict(hosts_set=f"refs/hosts/hosts.json#{v['hosts']}", now_playing_on_suggested=f"{v['now_playing']} ({CHAN[v['now_playing']]})",
                              ours_duration=v['duration']) for ep, v in EP.items()},
           ours_card=dict(channel=OURS['channel'], views=OURS['views'], age=OURS['age'], avatar='feedsim/ours_avatar.jpg',
                          note='same meta line for every candidate, the control included; age drawn in the short form the host cards use ("2d ago" = 2 days ago)'),
           surfaces={'suggested': 'mobile watch page, compact Up next list (168x94 thumbs), 8 cards = candidate + 7 hosts of its episode (now-playing video excluded), full page as a long screenshot',
                     'home': 'mobile Home feed, full-width 390 pt cards, 4 cards = candidate + 3 hosts of its episode, full feed as a long screenshot'},
           position_note='position = 0-based slot of our card in the list (0 = top card); position_1based = the same slot counted from 1; rects are [x0,y0,x1,y1] pixel boxes in the PNG',
           slot_rule='seeded draws without replacement within each (episode, surface) group',
           candidates=[dict(id=c['id'], ep=c['ep'], control=bool(c.get('control')), title=c['title'], thumb=c['thumb']) for c in CANDS],
           files=[])
for n, j in enumerate(order, start=1):
    job = jobs[j]; s = SURF[job['surface']]; cand = job['cand']; ep = EP[cand['ep']]
    spec = dict(candidate=dict(OURS, id='X', duration=ep['duration'], thumb=cand['thumb'], title=cand['title']),
                hosts=f"{HOSTS}#{ep['hosts']}", now_playing=ep['now_playing'], seed=job['seed'], n={s['layout']: s['n']})
    sp = f'{TMP}/spec_{n}.json'; json.dump(spec, open(sp, 'w'))
    pre = f'{TMP}/f{n}'
    subprocess.run([sys.executable, '-I', FEEDSIM, sp, '--out', pre, '--layouts', s['layout'], '--scale', '1', '--quality', '98',
                    '--seed', str(job['seed']), '--pos', f"{s['layout']}={job['pos']}"], check=True, stdout=subprocess.DEVNULL)
    meta = json.load(open(f"{pre}_{s['image']}.json"))
    cards = meta['cards']
    ci = [k for k, c in enumerate(cards) if c.get('tag') == 'candidate' or c.get('id') == 'X']
    assert len(ci) == 1 and ci[0] == job['pos'], (n, ci, job['pos'])
    assert len(cards) == s['n'], (n, len(cards))
    host_ids = [c.get('id') for k, c in enumerate(cards) if k != job['pos']]
    assert all(h in {i['id'] for i in HDB[ep['hosts']]} for h in host_ids), (n, host_ids)
    if s['layout'] == 'upnext': assert ep['now_playing'] not in host_ids, n
    fn = f'{OUT}/{ROUND}_{n}.png'
    im = Image.open(f"{pre}_{s['image']}.jpg"); im.load()
    Image.frombytes('RGB', im.size, im.convert('RGB').tobytes()).save(fn, optimize=True)  # fresh image: no source metadata
    cr = cards[job['pos']]
    key['files'].append(dict(file=os.path.basename(fn), path=fn, n=n, surface=job['surface'], layout=s['image'], size=list(im.size),
                             candidate_id=cand['id'], ep=cand['ep'], control=bool(cand.get('control')),
                             candidate_index_in_request=job['cand_index'], title=cand['title'], thumb=cand['thumb'],
                             hosts_set=ep['hosts'], now_playing=(ep['now_playing'] if s['layout'] == 'upnext' else None),
                             position=job['pos'], position_1based=job['pos'] + 1, n_cards=s['n'], seed=job['seed'],
                             candidate_thumb_rect=cr.get('thumb'), candidate_card_rect=cr.get('card'),
                             cards=[dict(slot=k, ours=(k == job['pos']), title=(cand['title'] if k == job['pos'] else c.get('title')),
                                         channel=('Myth Juice' if k == job['pos'] else CHAN.get(c.get('id'))),
                                         id=(None if k == job['pos'] else c.get('id')), thumb_rect=c.get('thumb'), card_rect=c.get('card'))
                                    for k, c in enumerate(cards)]))
    print(fn, job['surface'], cand['id'], 'pos', job['pos'])
json.dump(key, open(f'{OUT}/{ROUND}_key.json', 'w'), indent=1)
shutil.rmtree(TMP)
