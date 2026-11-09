#!/usr/bin/env python3
"""Blind find-it / pick-one feeds built on feedsim.py (same renderer, same geometry).

  python3 -I blind.py specs/r1_blind.json

For every candidate x surface it renders one full-scroll mobile page as PNG named <round>_<n>.png in out_dir,
with n shuffled so that neither the file name nor the file order reveals which candidate it holds or where.
The key (candidate, slot, card order, candidate rectangles, seeds) goes to <round>_key.json next to the feeds.

Design of a round:
  * one host SET per surface, drawn once with the round seed, shared by every candidate (like-for-like);
  * per feed, the host order is reshuffled and our slot is drawn at random; on a surface the candidates get
    distinct slots (sampled without replacement), so a viewer who sees several feeds cannot learn 'our' slot;
  * our social proof is the same small-channel line for every candidate, in YouTube's short form like the hosts.
"""
import json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feedsim  # noqa: E402

LAYOUT_PAGE = {'upnext': 'upnext_scroll', 'home': 'home_scroll'}


def main(spec_path):
    sp = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    rnd, seed = sp['round'], sp['seed']
    out_dir = os.path.normpath(os.path.join(base, sp['out_dir'])); os.makedirs(out_dir, exist_ok=True)
    # reuse feedsim's spec loader for hosts / now playing / path normalisation
    fs_spec = {'hosts': sp['hosts'], 'now_playing': sp['now_playing'],
               'candidates': [dict(sp['ours'], **c) for c in sp['candidates']]}
    tmp = os.path.join(base, f'.{rnd}_fs_spec.json'); json.dump(fs_spec, open(tmp, 'w'))
    try:
        _, cands, hosts, npi = feedsim.load_spec(tmp)
    finally:
        os.remove(tmp)
    for c in cands: c.pop('badge', None)  # the desktop-only 'New' chip is not drawn on mobile anyway

    jobs, host_sets = [], {}
    for sf in sp['surfaces']:
        pool = [h for h in hosts if h is not npi] if sf['layout'] == 'upnext' else list(hosts)
        r = random.Random(f'{rnd}:{seed}:hostset:{sf["name"]}')
        chosen = r.sample(pool, sf['hosts']); host_sets[sf['name']] = chosen
        n = sf['hosts'] + 1
        slots = random.Random(f'{rnd}:{seed}:slots:{sf["name"]}').sample(range(n), len(cands))
        for cand, slot in zip(cands, slots):
            jobs.append(dict(surface=sf, cand=cand, slot=slot, n=n, feed_seed=f'{rnd}:{seed}:{sf["name"]}:{cand["id"]}'))
    random.Random(f'{rnd}:{seed}:fileorder').shuffle(jobs)

    key = {'round': rnd, 'note': sp.get('note', ''), 'seed': seed, 'scale': sp.get('scale', 1), 'spec': os.path.abspath(spec_path),
           'generator': os.path.abspath(__file__),
           'positions_are': '0-based slot from the top of the list/feed; position_1based is the same slot counted from 1',
           'ours_meta': sp['ours'], 'now_playing_on_suggested': {'id': npi.get('id'), 'channel': npi.get('channel'), 'title': npi.get('title')},
           'surfaces': {sf['name']: dict(layout=LAYOUT_PAGE[sf['layout']], n_cards=sf['hosts'] + 1, desc=sf.get('desc', ''),
                                         hosts=[dict(id=h.get('id'), channel=h.get('channel'), title=h.get('title'), views=h.get('views'), age=h.get('age'))
                                                for h in host_sets[sf['name']]]) for sf in sp['surfaces']},
           'files': []}
    for k, j in enumerate(jobs, 1):
        sf, cand = j['surface'], j['cand']
        rng = random.Random(j['feed_seed'])
        order = list(host_sets[sf['name']]); rng.shuffle(order)
        c = feedsim.Ctx(sp.get('scale', 1), sp.get('style'))
        if sf['layout'] == 'upnext':
            out = feedsim.render_upnext(c, cand, order, npi, j['n'], j['slot'], rng)
        else:
            out = feedsim.render_home(c, cand, order, j['n'], j['slot'], rng)
        im, rects = out[LAYOUT_PAGE[sf['layout']]]
        fn = os.path.join(out_dir, f'{rnd}_{k}.png'); im.save(fn, optimize=True)
        cr = next(r for r in rects if r['tag'] == 'candidate')
        key['files'].append(dict(
            file=fn, n=k, surface=sf['name'], layout=LAYOUT_PAGE[sf['layout']], size=list(im.size),
            candidate=cand['id'], title=cand['title'], thumb=cand['thumb'],
            position=j['slot'], position_1based=j['slot'] + 1, of=j['n'],
            order_top_to_bottom=[('OURS ' + cand['id']) if r['tag'] == 'candidate' else f"{r['id']} | {r['title']}" for r in rects],
            candidate_thumb_rect=cr['thumb'], candidate_card_rect=cr['card'], feed_seed=j['feed_seed']))
        print(fn, im.size)
    kp = os.path.join(out_dir, f'{rnd}_key.json'); json.dump(key, open(kp, 'w'), indent=1); print(kp)


if __name__ == '__main__':
    main(sys.argv[1])
