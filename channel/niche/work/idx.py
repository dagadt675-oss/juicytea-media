import json,glob,sys
idx={}
files=glob.glob('comp/*.json')+glob.glob('research/niche_*/*.json')+glob.glob('research/packaging/data/*.json')
for f in files:
    try: d=json.load(open(f))
    except Exception: continue
    if isinstance(d,dict): d=list(d.values())
    if not isinstance(d,list): continue
    for r in d:
        if isinstance(r,dict) and r.get('id') and r.get('title'):
            idx.setdefault(r['id'],{k:r.get(k) for k in ('title','channel','views','len_s','age','handle')})
json.dump(idx,open('research/niche/work/idx.json','w'))
print(len(idx))
