#!/usr/bin/env python3
"""YouTube search supply probe (no API key).
Usage: python3 ytsearch.py "query one" ["query two" ...] [--json]
For each query prints the top results (videos + shorts): title, channel, views, length, age.
Then a supply summary: number of long-form (>=6 min) results with >=100K views whose title
shares >=50% of the query's content words, the max views of such a result, and the best Short's views.
"""
import json, re, sys, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
STOP = set('the a an of in on at to is are was were why how what who which that this these those and or for with from by it its be as do does did you your we our they their can could would will not no yes if then than into over under about there here'.split())

def views_to_int(s):
    if not s: return 0
    s = s.replace(',', '').lower()
    m = re.search(r'([\d.]+)\s*([kmb]?)', s)
    if not m: return 0
    n = float(m.group(1)); mult = {'k': 1e3, 'm': 1e6, 'b': 1e9}.get(m.group(2), 1)
    return int(n * mult)

def len_to_s(s):
    if not s: return 0
    parts = [int(p) for p in s.split(':') if p.isdigit()]
    t = 0
    for p in parts: t = t * 60 + p
    return t

def fetch(q, sp=None):
    url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(q) + ('&sp=' + sp if sp else '')
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    html = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m: return []
    data = json.loads(m.group(1))
    out = []
    def walk(o):
        if isinstance(o, dict):
            if 'videoRenderer' in o:
                v = o['videoRenderer']
                out.append({'type': 'video', 'id': v.get('videoId'),
                            'title': ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', [])),
                            'channel': ''.join(r.get('text', '') for r in v.get('ownerText', {}).get('runs', [])),
                            'views': views_to_int(v.get('viewCountText', {}).get('simpleText') or ''.join(r.get('text','') for r in v.get('viewCountText', {}).get('runs', []))),
                            'len_s': len_to_s(v.get('lengthText', {}).get('simpleText')),
                            'age': v.get('publishedTimeText', {}).get('simpleText', '')})
                return
            if 'shortsLockupViewModel' in o:
                v = o['shortsLockupViewModel']
                out.append({'type': 'short', 'id': v.get('onTap', {}).get('innertubeCommand', {}).get('reelWatchEndpoint', {}).get('videoId'),
                            'title': v.get('overlayMetadata', {}).get('primaryText', {}).get('content', ''),
                            'channel': '', 'views': views_to_int(v.get('overlayMetadata', {}).get('secondaryText', {}).get('content', '')),
                            'len_s': 0, 'age': ''})
                return
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(data)
    return out

def words(s):
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP and len(w) > 2]

def probe(q):
    res = fetch(q)
    try:
        res_long = fetch(q, 'EgIYAg%253D%253D')  # duration filter: 4-20 min
    except Exception:
        res_long = []
    seen = set(); allr = []
    for r in res + res_long:
        if r['id'] in seen: continue
        seen.add(r['id']); allr.append(r)
    qw = set(words(q))
    def overlap(t):
        tw = set(words(t))
        return len(qw & tw) / max(1, len(qw))
    long_hits = [r for r in allr if r['type'] == 'video' and r['len_s'] >= 360 and overlap(r['title']) >= 0.5]
    big_long = [r for r in long_hits if r['views'] >= 100_000]
    shorts = [r for r in allr if r['type'] == 'short' or (r['type'] == 'video' and 0 < r['len_s'] <= 70)]
    summary = {'query': q, 'n_results': len(allr),
               'longform_matching': len(long_hits), 'longform_matching_100k': len(big_long),
               'max_longform_matching_views': max([r['views'] for r in long_hits], default=0),
               'best_short_views': max([r['views'] for r in shorts], default=0),
               'top_any_views': max([r['views'] for r in allr], default=0)}
    return summary, sorted(allr, key=lambda r: -r['views'])[:25]

if __name__ == '__main__':
    qs = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv
    allout = []
    for q in qs:
        try:
            s, top = probe(q)
        except Exception as e:
            s, top = {'query': q, 'error': str(e)}, []
        allout.append({'summary': s, 'top': top})
        if not as_json:
            print('=' * 100); print('QUERY:', q); print('SUMMARY:', json.dumps(s))
            for r in top:
                print(f"  [{r['type'][0]}] {r['views']:>11,}  {r['len_s']//60:>3}m{r['len_s']%60:02d}s  {r['age']:<14} {r['channel'][:22]:<22} | {r['title'][:90]}")
    if as_json: print(json.dumps(allout, indent=1))
