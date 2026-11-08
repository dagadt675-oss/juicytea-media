#!/usr/bin/env python3
"""Fetch host-video metadata, thumbnails and channel avatars for the feed simulator.

Usage:
  python3 -I fetch_hosts.py SETNAME ID[::search query] [...]   # add/refresh a set in hosts.json
  (metadata comes from the search-results renderer: the query defaults to the title known from probes/ or the
   niche idx.json, then the bare id; watch pages answer HTTP 429 from the sandbox)
  python3 -I fetch_hosts.py --channel @handle OUT.jpg    # save a channel avatar (our own channel)

Writes (never committed; refs/ is for other channels' images):
  research/packaging/refs/hosts/<videoId>.jpg            maxresdefault (fallback hqdefault, bars trimmed later)
  research/packaging/refs/hosts/avatars/<channelId>.jpg  channel avatar (88 px)
  research/packaging/refs/hosts/hosts.json               {set: [ {id, thumb, title, channel, views, age, duration,
                                                          avatar, publish_date, view_count, length_s, fetched}, ...]}
Views/age strings are formatted the way YouTube shows them (floored: 3,644,064 -> "3.6M views"; 1 year ago).
"""
import json, os, re, sys, time, urllib.parse, urllib.request, datetime as dt

ROOT = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
HOSTS = ROOT + '/refs/hosts'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
TODAY = dt.date(2026, 11, 8)


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9',
                                               'Cookie': 'CONSENT=YES+1; PREF=hl=en&gl=US'})
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
    return b if binary else b.decode('utf-8', 'replace')


def jsvar(html, name):
    m = re.search(r'(?:var\s+)?' + re.escape(name) + r'\s*=\s*(\{.*?\});\s*(?:var\s|</script>)', html, re.S)
    return json.loads(m.group(1)) if m else {}


def walk(o, key):
    if isinstance(o, dict):
        if key in o:
            yield o[key]
        for v in o.values():
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def fmt_views(n):
    n = int(n)
    if n < 1000:
        return f'{n} view' + ('' if n == 1 else 's')
    def fl(x):  # floor to one decimal, drop .0
        s = f'{int(x * 10) / 10:.1f}'
        return s[:-2] if s.endswith('.0') else s
    if n < 10_000: return fl(n / 1e3) + 'K views'
    if n < 1_000_000: return f'{n // 1000}K views'
    if n < 10_000_000: return fl(n / 1e6) + 'M views'
    if n < 1_000_000_000: return f'{n // 1_000_000}M views'
    return fl(n / 1e9) + 'B views'


def fmt_age(publish, today=TODAY):
    d = (today - publish).days
    def u(n, w): return f'{n} {w}' + ('' if n == 1 else 's') + ' ago'
    if d < 1: return '12 hours ago'
    if d < 7: return u(d, 'day')
    if d < 30: return u(d // 7, 'week')
    if d < 365: return u(max(1, d // 30), 'month')
    return u(d // 365, 'year')


def fmt_dur(s):
    s = int(s); h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'


def save_thumb(vid):
    out = f'{HOSTS}/{vid}.jpg'
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        return out
    for q in ('maxresdefault', 'hq720', 'sddefault', 'hqdefault'):
        try:
            b = get(f'https://i.ytimg.com/vi/{vid}/{q}.jpg', binary=True)
            if len(b) > 5000:
                open(out, 'wb').write(b); return out
        except Exception:
            pass
    return None


def save_avatar(url, cid):
    os.makedirs(HOSTS + '/avatars', exist_ok=True)
    out = f'{HOSTS}/avatars/{cid}.jpg'
    if os.path.exists(out):
        return out
    url = re.sub(r'=s\d+-', '=s88-', url)
    try:
        open(out, 'wb').write(get(url, binary=True)); return out
    except Exception:
        return None


def titles_lookup():
    """Known titles (from this folder's probe JSONs and the niche index) to use as search queries."""
    t = {}
    for f in [ROOT + '/feedsim/probes/' + x for x in os.listdir(ROOT + '/feedsim/probes') if x.endswith('.json')]:
        try:
            for q in json.load(open(f)):
                for v in q.get('top', []):
                    if v.get('id'): t[v['id']] = (v.get('title', '') + ' ' + v.get('channel', '')).strip()
        except Exception:
            pass
    try:
        idx = json.load(open(ROOT + '/../niche/work/idx.json'))
        for k, v in idx.items():
            t.setdefault(k, (v.get('title', '') + ' ' + v.get('channel', '')).strip())
    except Exception:
        pass
    return t


def search_renderers(q):
    html = get('https://www.youtube.com/results?search_query=' + urllib.parse.quote(q) + '&hl=en&gl=US')
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    return list(walk(json.loads(m.group(1)), 'videoRenderer')) if m else []


def txt(o):
    return o.get('simpleText') or ''.join(r.get('text', '') for r in o.get('runs', [])) if o else ''


def fetch(vid, query=None):
    """Watch pages answer 429 from this sandbox, so read the search-results renderer for the video."""
    v = None
    for q in [query, vid] if query else [vid]:
        for r in search_renderers(q):
            if r.get('videoId') == vid:
                v = r; break
        if v: break
        time.sleep(0.5)
    if not v:
        raise RuntimeError('not found in search results')
    owner = (v.get('ownerText') or {}).get('runs', [{}])[0]
    cid = owner.get('navigationEndpoint', {}).get('browseEndpoint', {}).get('browseId', '')
    av = (v.get('channelThumbnailSupportedRenderers', {}).get('channelThumbnailWithLinkRenderer', {})
          .get('thumbnail', {}).get('thumbnails') or [{}])[-1].get('url', '')
    vc = re.sub(r'[^0-9]', '', txt(v.get('viewCountText', {})))
    ln = txt(v.get('lengthText', {}))
    secs = 0
    for part in ln.split(':'):
        secs = secs * 60 + int(part) if part.isdigit() else secs
    age = txt(v.get('publishedTimeText', {})).replace('\u00a0', ' ').replace('\xa0', ' ')
    age = re.sub(r'\bmin\b', 'minutes', re.sub(r'\bhr\b', 'hours', age))
    if age.startswith('Streamed '): age = age[9:]
    rec = dict(id=vid, title=txt(v.get('title', {})), channel=owner.get('text', ''), channel_id=cid,
               view_count=int(vc or 0), length_s=secs, age=age, fetched=str(TODAY))
    rec['views'] = fmt_views(rec['view_count'])
    rec['duration'] = ln or fmt_dur(secs)
    t = save_thumb(vid); rec['thumb'] = os.path.relpath(t, HOSTS) if t else None
    a = save_avatar(av, cid) if av and cid else None
    rec['avatar'] = os.path.relpath(a, HOSTS) if a else None
    return rec


def main():
    os.makedirs(HOSTS, exist_ok=True)
    if sys.argv[1] == '--channel':
        html = get(f'https://www.youtube.com/{sys.argv[2]}?hl=en')
        m = re.search(r'"avatar":\{"thumbnails":\[\{"url":"([^"]+)"', html) or \
            re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not m:
            sys.exit('no avatar found')
        url = re.sub(r'=s\d+-', '=s176-', m.group(1))
        open(sys.argv[3], 'wb').write(get(url, binary=True)); print(sys.argv[3], url); return
    setname, ids = sys.argv[1], sys.argv[2:]
    path = HOSTS + '/hosts.json'
    db = json.load(open(path)) if os.path.exists(path) else {}
    out = []; tl = titles_lookup()
    for vid in ids:
        vid, _, q = vid.partition('::')
        try:
            r = fetch(vid, q or tl.get(vid))
        except Exception as e:
            print('FAIL', vid, e); continue
        out.append(r)
        print(f"{vid} | {r['views']:>12} | {r['age']:>13} | {r['duration']:>8} | {r['channel'][:24]:24} | {r['title'][:70]} | thumb={bool(r['thumb'])} av={bool(r['avatar'])}")
        time.sleep(0.4)
    db[setname] = out
    json.dump(db, open(path, 'w'), indent=1, ensure_ascii=False)
    print('wrote', path, setname, len(out))


if __name__ == '__main__':
    main()
