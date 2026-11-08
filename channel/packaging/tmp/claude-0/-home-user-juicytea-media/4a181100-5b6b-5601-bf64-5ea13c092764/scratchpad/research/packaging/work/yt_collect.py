#!/usr/bin/env python3
"""Collect YouTube search results with channel ids. Usage: yt_collect.py OUT_JSON q1 q2 ..."""
import json, re, sys, time, urllib.parse, urllib.request, concurrent.futures as cf
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
FILTERS = {'rel': None, 'mid': 'EgIYAg%3D%3D', 'long': 'EgIYAw%3D%3D', 'yr_mid': 'EgQIBRgC', 'yr_long': 'EgQIBRgD'}

def views_to_int(s):
    if not s: return 0
    s = s.replace(',', '').lower()
    m = re.search(r'([\d.]+)\s*([kmb]?)', s)
    if not m: return 0
    return int(float(m.group(1)) * {'k': 1e3, 'm': 1e6, 'b': 1e9}.get(m.group(2), 1))

def len_to_s(s):
    if not s: return 0
    t = 0
    for p in s.split(':'):
        if p.isdigit(): t = t * 60 + int(p)
    return t

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    for i in range(3):
        try:
            return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            err = e; time.sleep(2 + 3 * i)
    raise err

def fetch(q, key):
    sp = FILTERS[key]
    url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(q) + ('&sp=' + sp if sp else '')
    html = get(url)
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m: return []
    data = json.loads(m.group(1)); out = []
    def walk(o):
        if isinstance(o, dict):
            if 'videoRenderer' in o:
                v = o['videoRenderer']
                runs = v.get('ownerText', {}).get('runs', [{}])
                ne = runs[0].get('navigationEndpoint', {}) if runs else {}
                vc = v.get('viewCountText', {})
                vct = vc.get('simpleText') or ''.join(r.get('text', '') for r in vc.get('runs', []))
                out.append({'id': v.get('videoId'),
                    'title': ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', [])),
                    'channel': ''.join(r.get('text', '') for r in runs),
                    'channel_id': ne.get('browseEndpoint', {}).get('browseId', ''),
                    'channel_url': ne.get('browseEndpoint', {}).get('canonicalBaseUrl', ''),
                    'views': views_to_int(vct), 'views_text': vct,
                    'len_s': len_to_s(v.get('lengthText', {}).get('simpleText')),
                    'age': v.get('publishedTimeText', {}).get('simpleText', ''),
                    'query': q, 'filter': key})
                return
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(data)
    return out

if __name__ == '__main__':
    outp = sys.argv[1]; qs = sys.argv[2:]
    jobs = [(q, k) for q in qs for k in FILTERS]
    res = []
    with cf.ThreadPoolExecutor(4) as ex:
        futs = {ex.submit(fetch, q, k): (q, k) for q, k in jobs}
        for f in cf.as_completed(futs):
            q, k = futs[f]
            try:
                r = f.result(); res.extend(r)
                print(f'{len(r):3d} {k:7s} {q}', file=sys.stderr)
            except Exception as e:
                print(f'ERR {k} {q}: {e}', file=sys.stderr)
    json.dump(res, open(outp, 'w'))
    print(len(res), 'rows ->', outp, file=sys.stderr)
