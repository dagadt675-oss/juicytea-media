#!/usr/bin/env python3
"""Fetch channel subs + recent uploads. Usage: python3 chan.py OUTJSON handle1 handle2 ...
handle: '/@Name' or '/channel/UC..' or '@Name'"""
import json, re, sys, time, urllib.request
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

def vint(s):
    if not s: return 0
    s = s.replace(',', '').lower().replace('thousand', 'k').replace('million', 'm').replace('billion', 'b')
    m = re.search(r'([\d.]+)\s*([kmb]?)', s)
    if not m: return 0
    return int(float(m.group(1)) * {'k': 1e3, 'm': 1e6, 'b': 1e9}.get(m.group(2), 1))

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9', 'Cookie': 'CONSENT=YES+1'})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')

def texts(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('content', 'simpleText', 'text') and isinstance(v, str): acc.append(v)
            else: texts(v, acc)
    elif isinstance(o, list):
        for x in o: texts(x, acc)
    return acc

def chan(h):
    h = h if h.startswith('/') else '/' + h
    html = get('https://www.youtube.com' + h + '/videos')
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m: return {'handle': h, 'error': 'noData'}
    d = json.loads(m.group(1))
    hdr = d.get('header', {})
    t = texts(hdr, [])
    subs = next((vint(x) for x in t if 'subscriber' in x.lower()), None)
    nvid = next((vint(x) for x in t if re.search(r'\bvideos?\b', x.lower())), None)
    name = d.get('metadata', {}).get('channelMetadataRenderer', {}).get('title', '')
    vids = []
    def walk(o):
        if isinstance(o, dict):
            if 'videoRenderer' in o:
                v = o['videoRenderer']
                vids.append({'title': ''.join(r.get('text', '') for r in v.get('title', {}).get('runs', [])),
                             'views': vint(v.get('viewCountText', {}).get('simpleText', '')),
                             'age': v.get('publishedTimeText', {}).get('simpleText', ''),
                             'len': v.get('lengthText', {}).get('simpleText', '')})
                return
            if 'lockupViewModel' in o:
                lv = o['lockupViewModel']
                lm = lv.get('metadata', {}).get('lockupMetadataViewModel', {})
                title = lm.get('title', {}).get('content', '')
                parts = []
                for row in lm.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', []):
                    for pt in row.get('metadataParts', []):
                        parts.append((pt.get('text', {}).get('content', ''), pt.get('accessibilityLabel', '')))
                views = next((vint(a) for c, a in parts if 'view' in a.lower()), 0)
                if not views: views = next((vint(c) for c, a in parts if 'view' in c.lower()), 0)
                age = next((c for c, a in parts if 'ago' in c.lower() or 'ago' in a.lower()), '')
                ln = next((x for x in texts(lv.get('contentImage', {}), []) if re.fullmatch(r'\d+:\d+(:\d+)?', x)), '')
                vids.append({'title': title, 'views': views, 'age': age, 'len': ln})
                return
            for x in o.values(): walk(x)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(d.get('contents', {}))
    return {'handle': h, 'name': name, 'subs': subs, 'nvideos': nvid, 'videos': vids}

if __name__ == '__main__':
    outp = sys.argv[1]
    try: db = json.load(open(outp))
    except Exception: db = {}
    for h in sys.argv[2:]:
        if h in db and db[h].get('videos'): continue
        try:
            r = chan(h)
        except Exception as e:
            r = {'handle': h, 'error': str(e)}
        db[h] = r
        vs = r.get('videos', [])
        print(f"{h[:30]:<30} {str(r.get('name',''))[:24]:<24} subs={r.get('subs')} n={r.get('nvideos')} got={len(vs)} " + ' | '.join(f"{v['views']:,}/{v['age']}" for v in vs[:6]))
        time.sleep(0.7)
    json.dump(db, open(outp, 'w'))
