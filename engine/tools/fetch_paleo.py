import json, urllib.request, concurrent.futures as cf, sys
def get(t):
    url = f'https://gws.gplates.org/reconstruct/coastlines/?time={t}&model=MULLER2019&min_area=500'
    for a in range(4):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=120).read())
            polys = []
            for f in d['features']:
                g = f['geometry']
                rings = g['coordinates'] if g['type'] == 'Polygon' else [r for p in g['coordinates'] for r in p]
                for r in rings:
                    rr = [[round(x, 2), round(y, 2)] for x, y in r]
                    if len(rr) >= 4: polys.append(rr)
            json.dump(polys, open(f'coast_{t:03d}.json', 'w'), separators=(',', ':'))
            return t, len(polys)
        except Exception as e:
            err = e
    return t, f'ERR {err}'
times = list(range(1, 200, 2))
with cf.ThreadPoolExecutor(6) as ex:
    for t, n in ex.map(get, times): print(t, n, flush=True)
