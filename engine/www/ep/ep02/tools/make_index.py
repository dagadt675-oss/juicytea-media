#!/usr/bin/env python3
"""make_index.py: write engine/www/ep/ep02/data/regions.json from regions_spec.json plus each baked region's meta.json.
regions.json is what HawaiiStage.loadRegion('ep/ep02/data', name) and lab_region.html read: per region the data folder (absolute
from the web root), files, bbox, size, pixel size, nesting stack, verification camera, purpose (script segments), sources, colour
dates, sea-level facts measured on the baked grid, data gaps and sizes. Legacy regions (bigisland, hawaii_skirt) point at
lab/hawaii/data and take their facts from its meta.json. Run after any bake (rebuild_regions.sh does)."""
import json, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); WWW = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(HERE, '..', 'data')
spec = json.load(open(os.path.join(HERE, 'regions_spec.json')))
out = dict(about='ep02 terrain/seafloor regions for HawaiiStage.loadRegion(root, name) (engine/www/lab/hawaii/hterrain.js). Heights: RG 16-bit PNG, '
                 'h = v / 65535 * hrange + hmin, row 0 = north. stack = layers finest first, each inside the next. Facts are measured on the '
                 'baked grid (not survey values): use them to stage shots, check every narrated number against the fact ledger.',
           generated=time.strftime('%Y-%m-%d %H:%M'), root='ep/ep02/data',
           rebuild='bash engine/www/ep/ep02/tools/rebuild_regions.sh [DL_DIR] [name,name]', regions={})
missing = []
for R in spec['regions']:
    n = R['name']
    e = {k: R[k] for k in ('bbox', 'wh', 'stack', 'purpose', 'view', 'gaps') if k in R}
    if R.get('legacy'):
        e.update(dir='/' + R['dir'], files=R['files'], hmin=-8000.0, hrange=17000.0, rebuild=R.get('rebuild'))
        lm = os.path.join(WWW, R['dir'], 'meta.json')
        if os.path.exists(lm) and n == 'bigisland':
            m = json.load(open(lm)); e['facts'] = m.get('facts', {}); e['sources'] = ['ETOPO 2022 15"', 'Terrarium z11 (land)', 'GIBS MODIS 250 m composite']
        hp = os.path.join(WWW, R['dir'], R['files']['h16'])
        if R.get('facts') and os.path.exists(hp):  # the same measurements as region_bake.py, on the legacy grid
            import sys, numpy as np
            from PIL import Image
            sys.path.insert(0, os.path.join(WWW, 'lab', 'hawaii', 'tools')); import region_bake as rb
            a = np.asarray(Image.open(hp)).astype(np.float32); h = (a[..., 0] * 256 + a[..., 1]) / 65535 * 17000.0 - 8000.0
            px = ((e['bbox'][2] - e['bbox'][0]) / e['wh'][0] * 111320 * 0.94 + (e['bbox'][3] - e['bbox'][1]) / e['wh'][1] * 111320) / 2
            e.setdefault('facts', {})['grid'] = rb.facts(h, e['bbox'], R['facts'], px)
        e['px_m'] = round((e['bbox'][2] - e['bbox'][0]) / e['wh'][0] * 111320 * 0.94, 1)
        e['bytes'] = {k: os.path.getsize(os.path.join(WWW, R['dir'], f)) for k, f in R['files'].items() if os.path.exists(os.path.join(WWW, R['dir'], f))}
    else:
        mp = os.path.join(DATA, n, 'meta.json')
        if not os.path.exists(mp): missing.append(n); continue
        m = json.load(open(mp))
        e.update(dir=f'/ep/ep02/data/{n}', files=m['files'], hmin=m['hmin'], hrange=m['hrange'], px_m=m['px_m'], sources=m['sources'],
                 colour={k: (v if k != 'modis' else f'{len(v)} MODIS Terra/Aqua days') for k, v in m.get('colour', {}).items()},
                 facts=m['facts'], bytes=m['bytes'], bake_s=m.get('bake_s'), baked=m.get('baked'))
        e['bbox'], e['wh'] = m['bbox'], m['wh']
    out['regions'][n] = e
json.dump(out, open(os.path.join(DATA, 'regions.json'), 'w'), indent=1, ensure_ascii=False)
tot = sum(sum(e.get('bytes', {}).values()) for k, e in out['regions'].items() if not k in ('bigisland', 'hawaii_skirt'))
print(f'regions.json: {len(out["regions"])} regions, ep02 baked data {tot / 1e6:.1f} MB' + (f'; not baked yet: {missing}' if missing else ''))
