import json, statistics, re, glob
R='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research'
P=R+'/packaging'; N=R+'/niche'
ds={r['id']:r for r in json.load(open(P+'/data/dataset.json'))}
g=json.load(open(N+'/work/groups.json'))
grp={i:k for k,v in g.items() for i in v}
idx=json.load(open(N+'/work/idx.json'))
filt={r['id']:r for r in json.load(open(P+'/work/raw/filtered.json'))}
chid=json.load(open(P+'/work/raw/channels.json'))
nch=json.load(open(N+'/comp_data/chans.json'))
known=json.load(open(P+'/data/chsubs_known.json'))
def v2i(s):
    s=(s or '').replace(',','').upper(); m=re.search(r'(\d[\d.]*)\s*([KMB]?)',s)
    return int(float(m.group(1))*{'K':1e3,'M':1e6,'B':1e9}.get(m.group(2),1)) if m else None
# name -> channel_id / handle maps
name2cid={}; 
for r in filt.values(): name2cid.setdefault(r['channel'],r['channel_id'])
name2h={}
for h,c in nch.items(): name2h.setdefault(c.get('name'),h)
for i,r in idx.items():
    if r.get('handle'): name2h.setdefault(r['channel'],r['handle'])
def nmed(c):
    vv=[v['views'] for v in c.get('videos',[]) if isinstance(v.get('views'),(int,float))]
    return statistics.median(vv) if vv else None
out={}
ids=list(dict.fromkeys(list(ds)+list(grp)))
for i in ids:
    base=ds.get(i) or {}
    ir=idx.get(i,{})
    row={'id':i,'title':base.get('title') or ir.get('title'),'channel':base.get('channel') or ir.get('channel'),
         'views':base.get('views') or ir.get('views'),'len_s':base.get('len_s') or ir.get('len_s'),'age':base.get('age') or ir.get('age'),
         'group':grp.get(i),'src':('niche' if i in grp else '')+('+pack' if i in ds else '')}
    ch=row['channel']; subs=None; med=None; how=None
    fr=filt.get(i); cid=fr['channel_id'] if fr else name2cid.get(ch)
    if cid and cid in chid and chid[cid].get('subs'):
        subs=chid[cid]['subs']; med=chid[cid].get('median_recent_views'); how='chpage-id'
    h=ir.get('handle') or name2h.get(ch)
    if h and h in nch:
        if not subs and nch[h].get('subs'): subs=nch[h]['subs']; how='chpage-handle'
        if not med: med=nmed(nch[h])
    if not subs and base.get('subs'): subs=base['subs']; how=base.get('subs_src')
    if not subs and ch in known['chsubs']: subs=known['chsubs'][ch]; how='known'
    if not med and ch in known.get('chmed',{}): med=known['chmed'][ch]
    if not med and base.get('chmed'): med=base['chmed']
    row.update(subs=subs,chmed=med,subs_how=how,cid=cid,handle=h)
    out[i]=row
json.dump(out,open(P+'/anat/merged.json','w'),indent=0)
miss=[r for r in out.values() if not r['subs']]
print('total',len(out),'with subs',len(out)-len(miss),'with med',sum(1 for r in out.values() if r['chmed']))
for r in miss: print('MISS',r['id'],r['channel'],r['group'],r['views'],'|',(r['title'] or '')[:60], r['cid'], r['handle'])
# extra channel pages fetched 2026-11-08
ex=json.load(open(P+'/anat/raw/ch_extra.json'))
for r in out.values():
    h=r.get('handle')
    if h in ex and 'err' not in ex[h]:
        if not r['subs'] and ex[h]['subs']: r['subs']=ex[h]['subs']; r['subs_how']='chpage-fetch'
        if not r['chmed'] and ex[h]['med']: r['chmed']=ex[h]['med']
def agedays(a):
    m=re.search(r'(\d+)\s*(\w+)',a or '')
    if not m: return None
    n,u=int(m.group(1)),m.group(2)
    if u.startswith('mo'): return n*30.4
    return n*{'s':1/86400,'m':1/1440,'h':1/24,'d':1,'w':7,'y':365}.get(u[0],0)
for r in out.values():
    r['age_d']=agedays(r['age'])
    r['ratio']=r['views']/r['subs'] if r['subs'] and r['views'] is not None else None
    r['outlier']=r['views']/r['chmed'] if r['chmed'] and r['views'] is not None else None
json.dump(out,open(P+'/anat/merged.json','w'),indent=0)
print('after extra: with subs',sum(1 for r in out.values() if r['subs']))
# fresh probe additions (probe_c, 2026-11-08)
add=json.load(open(P+'/anat/raw/add_rows.json')); cha=json.load(open(P+'/anat/raw/ch_add.json'))
for i,r in add.items():
    c=cha.get(r['curl'],{})
    row={'id':i,'title':r['title'],'channel':r['channel'],'views':r['views'],'len_s':r['len_s'],'age':r['age'],'group':None,'src':'probe_c:'+r['q'],
         'subs':c.get('subs'),'chmed':c.get('med'),'subs_how':'chpage-fetch','cid':r['cid'],'handle':r['curl']}
    row['age_d']=agedays(row['age']); row['ratio']=row['views']/row['subs'] if row['subs'] else None
    row['outlier']=row['views']/row['chmed'] if row['chmed'] else None
    out[i]=row
json.dump(out,open(P+'/anat/merged.json','w'),indent=0)
print('final total',len(out),'with subs',sum(1 for r in out.values() if r['subs']))
