#!/usr/bin/env python3
"""Competition probe: YouTube search with filters + channel handle capture.
Usage: python3 probe2.py OUTJSON MODE "q1" "q2" ...
MODE: rel (relevance), year_views (last-year upload, sort by views), year_long (last-year, >20min, by views)
"""
import json, re, sys, time, base64, urllib.parse, urllib.request

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

def vint(s):
    if not s: return 0
    s = s.replace(',', '').lower()
    m = re.search(r'([\d.]+)\s*([kmb]?)', s)
    if not m: return 0
    return int(float(m.group(1)) * {'k': 1e3, 'm': 1e6, 'b': 1e9}.get(m.group(2), 1))

def lens(s):
    if not s: return 0
    t = 0
    for p in s.split(':'):
        if p.isdigit(): t = t * 60 + int(p)
    return t

def sp_for(mode):
    # protobuf: field1 sort (3=view count); field2 filters {1: upload date (5=this year), 2: type (1=video), 3: duration}
    if mode == 'rel': return None
    filt = bytes([0x08, 0x05, 0x10, 0x01])
    if mode == 'year_mid': filt += bytes([0x18, 0x03])
    if mode == 'year_long': filt += bytes([0x18, 0x02])
    msg = bytes([0x08, 0x03, 0x12, len(filt)]) + filt
    return urllib.parse.quote(base64.b64encode(msg).decode())

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
                runs = v.get('ownerText', {}).get('runs', [])
                handle = ''
                if runs:
                    be = runs[0].get('navigationEndpoint', {}).get('browseEndpoint', {})
                    handle = be.get('canonicalBaseUrl', '') or be.get('browseId', '')
                out.append({'id': v.get('videoId'), 'q': q,
                            'title': ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', [])),
                            'channel': ''.join(r.get('text', '') for r in runs), 'handle': handle,
                            'views': vint(v.get('viewCountText', {}).get('simpleText') or ''.join(r.get('text', '') for r in v.get('viewCountText', {}).get('runs', []))),
                            'len_s': lens(v.get('lengthText', {}).get('simpleText')),
                            'age': v.get('publishedTimeText', {}).get('simpleText', '')})
                return
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(data)
    return out

if __name__ == '__main__':
    outp, mode, qs = sys.argv[1], sys.argv[2], sys.argv[3:]
    try: allr = json.load(open(outp))
    except Exception: allr = []
    for q in qs:
        try:
            r = fetch(q, sp_for(mode))
        except Exception as e:
            print('ERR', q, e); r = []
        for x in r: x['mode'] = mode
        allr += r
        print(f'{mode} | {q}: {len(r)} results; >=100K long(>=6m): {sum(1 for x in r if x["views"]>=1e5 and x["len_s"]>=360)}')
        time.sleep(0.6)
    json.dump(allr, open(outp, 'w'))
