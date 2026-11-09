#!/usr/bin/env python3
"""Round-3 BLIND feed renders: ep02 NO OCEAN fix arms vs the live default, balanced design.

  python3 -I blind_r3.py r3_cands.json

Fixes the round-2 flaws (round2.md section 6):
  * ONE fixed Hawaii host set, in ONE fixed order, for every arm:
      suggested (mobile watch page, compact Up next list, 8 cards): our card + the same 7 hosts, now playing
        RealLifeLore 34Ojnyi9xLw (excluded from the list);
      home (mobile Home feed, full-width cards, 4 cards): our card + the same 3 hosts.
  * Our card's slot is ROTATED (Latin-square style): every arm appears exactly once at Up next slots 2, 5, 7 and
    Home slots 1, 3 (1-based, slot 1 = top card), i.e. 5 feeds per arm. Within a surface the hosts keep their
    relative order; only our card moves.
  * Every arm carries the same launch title and the same meta line ("Myth Juice", "1.2K views", "2d ago").
The image is the full feed as a long phone screenshot (the *_scroll render, scale 1 = true layout size).
File numbers n in feeds/r3_<n>.png follow a seeded shuffle of the jobs, so neither the number nor the write
order reveals the arm. Intermediate renders (whose JSON flags the candidate) go to a temp dir that is deleted;
the key goes to feeds/r3_key.json."""
import json, os, random, shutil, subprocess, sys
from PIL import Image

PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
FEEDSIM = f'{PK}/feedsim/feedsim.py'
HOSTS = f'{PK}/refs/hosts/hosts.json'
HOST_DIR = os.path.dirname(HOSTS)
AVATAR = f'{PK}/feedsim/ours_avatar.jpg'
OUT = f'{PK}/feeds'
TMP = f'{PK}/feedsim/blind/_render_r3'
MASTER_SEED = 2026110803
FEED_SEED = 3  # one feedsim seed for every job (only fixes the pool shuffle, which is pre-compensated below)
ROUND = 'r3'
TITLE = "Why Can't You See Most of Hawaii? (Look Down)"
DURATION = '12:53'
NOW_PLAYING = '34Ojnyi9xLw'  # RealLifeLore, "Why You Can't Travel Between Hawaii's Islands by Boat"

# Fixed host sets (refs/hosts/hosts.json#hawaii).
# Up next: the six most-viewed on-topic long-forms (Hawaii explainers + the Pacific drain episode) and the closest
# same-premise upload (Unseen Works, PACIFIC DRAINED, 4 days old). Dropped: the now-playing video, the 1:49 news clip,
# the off-place drains (Chesapeake, Antarctica) and the smallest Hawaii explainer (Below The Map, 124K).
# The same-premise host is pinned to host index 2, the only position never adjacent to our slots 2, 5, 7
# (playbook section 8: our card sits away from the strongest same-topic host); the other six are in a seeded order.
UPNEXT_PIN = {2: 'YIXnHpSRGP4'}
UPNEXT_REST = ['4-qO0d6r1f0', 'k0tnqPmwWvk', 'biNMRQJXvfs', 'X5O7dd2A4QM', 'N7asoI4KWmE', 'XrMGJPv8n1U']
# Home: the biggest Hawaii video (RealLifeLore), the same-premise drain upload and the brightest Hawaii map card
# (Below The Map, IT'S MOVING). Same-premise host pinned to index 1 (adjacent to our card only at Home slot 3).
HOME_PIN = {1: 'YIXnHpSRGP4'}
HOME_REST = ['34Ojnyi9xLw', 'iGP2VsaRSQ4']

SLOTS = {'suggested': [2, 5, 7], 'home': [1, 3]}  # 1-based
SURF = {'suggested': dict(layout='upnext', n=8, image='upnext_scroll', hosts=7),
        'home': dict(layout='home', n=4, image='home_scroll', hosts=3)}
# 'age' uses YouTube's short form ("2d ago" = 2 days ago) because every host card uses the short form
# ("4d ago", "1y ago"); a long form on our card alone would single it out. Same as round 2.
OURS = dict(channel='Myth Juice', views='1.2K views', age='2d ago', avatar=AVATAR)

CANDS = json.load(open(sys.argv[1]))
HDB = json.load(open(HOSTS))
HAWAII = {i['id']: i for i in HDB['hawaii']}
rng = random.Random(MASTER_SEED)


def order_hosts(pin, rest, m):
    rest = list(rest); rng.shuffle(rest); out = [None] * m
    for k, v in pin.items(): out[k] = v
    it = iter(rest)
    return [o if o is not None else next(it) for o in out]


ORDER = {'suggested': order_hosts(UPNEXT_PIN, UPNEXT_REST, 7), 'home': order_hosts(HOME_PIN, HOME_REST, 3)}
assert NOW_PLAYING not in ORDER['suggested']
for s, ids in ORDER.items():
    assert len(set(ids)) == SURF[s]['hosts'] and all(i in HAWAII for i in ids), (s, ids)


def host_item(hid):
    h = HAWAII[hid]; it = {k: h[k] for k in ('id', 'title', 'channel', 'views', 'age', 'duration', 'view_count') if k in h}
    it['thumb'] = os.path.join(HOST_DIR, h['thumb'])
    if h.get('avatar'): it['avatar'] = os.path.join(HOST_DIR, h['avatar'])
    return it


def pre_permute(ids, layout):
    """feedsim shuffles its pool with random.Random(f'{seed}:{layout}'); feed it the inverse permutation so the
    rendered order is exactly `ids`."""
    perm = list(range(len(ids))); random.Random(f'{FEED_SEED}:{layout}').shuffle(perm)
    inp = [None] * len(ids)
    for k, p in enumerate(perm): inp[p] = ids[k]
    return inp


jobs = []
for ci, c in enumerate(CANDS):
    for sname in ('suggested', 'home'):
        for slot in SLOTS[sname]:
            jobs.append(dict(cand_index=ci + 1, cand=c, surface=sname, slot1=slot, pos=slot - 1))
order = list(range(len(jobs))); rng.shuffle(order)  # file number n -> job, shuffled

os.makedirs(TMP, exist_ok=True)
CHAN = {i['id']: i['channel'] for i in HDB['hawaii']}
key = dict(round=ROUND, created='2026-11-08', master_seed=MASTER_SEED, feedsim_seed=FEED_SEED,
           tool='feedsim/feedsim.py (scale 1, dark mode, JPEG q98 render saved as PNG); driver feedsim/blind/blind_r3.py feedsim/blind/r3_cands.json',
           design=('balanced: one fixed host set and host order per surface for every arm; our card rotated so each arm appears once at '
                   'Up next slots 2, 5, 7 and Home slots 1, 3 (1-based); 4 arms x 5 feeds = 20 feeds'),
           episode='ep02', title=TITLE, ours_duration=DURATION,
           hosts_set='refs/hosts/hosts.json#hawaii',
           now_playing_on_suggested=f'{NOW_PLAYING} ({CHAN[NOW_PLAYING]})',
           host_order={s: [dict(index=k, id=h, channel=CHAN[h], title=HAWAII[h]['title'], views=HAWAII[h]['views'], age=HAWAII[h]['age'])
                           for k, h in enumerate(ids)] for s, ids in ORDER.items()},
           host_choice=('suggested: the six most-viewed on-topic long-forms plus the closest same-premise upload (Unseen Works, PACIFIC DRAINED); '
                        'it is pinned at host index 2, never adjacent to our slots 2/5/7. home: RealLifeLore (biggest Hawaii video), '
                        'Unseen Works PACIFIC DRAINED (same premise, index 1), Below The Map IT\'S MOVING (brightest Hawaii map card). '
                        'Other host positions in a seeded order.'),
           ours_card=dict(channel=OURS['channel'], views=OURS['views'], age=OURS['age'], avatar='feedsim/ours_avatar.jpg',
                          meta_line_home='Myth Juice · 1.2K views · 2d ago',
                          note='same meta line for every arm, the control included; age drawn in the short form the host cards use ("2d ago" = 2 days ago)'),
           surfaces={'suggested': 'mobile watch page, compact Up next list (168x94 thumbs), 8 cards = our card + the 7 fixed hosts (now-playing video excluded), full page as a long screenshot',
                     'home': 'mobile Home feed, full-width 390 pt cards, 4 cards = our card + the 3 fixed hosts, full feed as a long screenshot'},
           position_note='position = 0-based slot of our card (0 = top card); position_1based = the same slot counted from 1 (the slot numbers of the design); rects are [x0,y0,x1,y1] pixel boxes in the PNG',
           candidates=[dict(id=c['id'], control=bool(c.get('control')), title=TITLE, thumb=c['thumb']) for c in CANDS],
           files=[], by_candidate={})
for n, j in enumerate(order, start=1):
    job = jobs[j]; s = SURF[job['surface']]; cand = job['cand']; lay = s['layout']
    ids = pre_permute(ORDER[job['surface']], lay)
    comps = [host_item(h) for h in ids]
    spec = dict(candidate=dict(OURS, id='X', duration=DURATION, thumb=cand['thumb'], title=TITLE),
                competitors=comps, seed=FEED_SEED, n={lay: s['n']})
    if lay == 'upnext':
        spec['competitors'] = [host_item(NOW_PLAYING)] + comps; spec['now_playing'] = NOW_PLAYING
    sp = f'{TMP}/spec_{n}.json'; json.dump(spec, open(sp, 'w'))
    pre = f'{TMP}/f{n}'
    subprocess.run([sys.executable, '-I', FEEDSIM, sp, '--out', pre, '--layouts', lay, '--scale', '1', '--quality', '98',
                    '--seed', str(FEED_SEED), '--pos', f"{lay}={job['pos']}"], check=True, stdout=subprocess.DEVNULL)
    meta = json.load(open(f"{pre}_{s['image']}.json"))
    cards = meta['cards']
    ci = [k for k, c in enumerate(cards) if c.get('tag') == 'candidate' or c.get('id') == 'X']
    assert len(ci) == 1 and ci[0] == job['pos'], (n, ci, job['pos'])
    assert len(cards) == s['n'], (n, len(cards))
    host_ids = [c.get('id') for k, c in enumerate(cards) if k != job['pos']]
    assert host_ids == ORDER[job['surface']], (n, host_ids, ORDER[job['surface']])
    if lay == 'upnext': assert NOW_PLAYING not in host_ids, n
    fn = f'{OUT}/{ROUND}_{n}.png'
    im = Image.open(f"{pre}_{s['image']}.jpg"); im.load()
    Image.frombytes('RGB', im.size, im.convert('RGB').tobytes()).save(fn, optimize=True)  # fresh image: no source metadata
    cr = cards[job['pos']]
    key['files'].append(dict(file=os.path.basename(fn), path=fn, n=n, surface=job['surface'], layout=s['image'], size=list(im.size),
                             candidate_id=cand['id'], control=bool(cand.get('control')),
                             candidate_index_in_request=job['cand_index'], title=TITLE, thumb=cand['thumb'],
                             now_playing=(NOW_PLAYING if lay == 'upnext' else None),
                             position=job['pos'], position_1based=job['slot1'], n_cards=s['n'],
                             candidate_thumb_rect=cr.get('thumb'), candidate_card_rect=cr.get('card'),
                             cards=[dict(slot=k, slot_1based=k + 1, ours=(k == job['pos']), title=(TITLE if k == job['pos'] else c.get('title')),
                                         channel=('Myth Juice' if k == job['pos'] else CHAN.get(c.get('id'))),
                                         id=(None if k == job['pos'] else c.get('id')), thumb_rect=c.get('thumb'), card_rect=c.get('card'))
                                    for k, c in enumerate(cards)]))
    key['by_candidate'].setdefault(cand['id'], {})[f"{job['surface']}_slot{job['slot1']}"] = os.path.basename(fn)
    print(fn, job['surface'], cand['id'], 'slot', job['slot1'])
json.dump(key, open(f'{OUT}/{ROUND}_key.json', 'w'), indent=1, ensure_ascii=False)
shutil.rmtree(TMP)
