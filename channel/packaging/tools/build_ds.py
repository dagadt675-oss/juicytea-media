import json
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/data'
R='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research'
k=json.load(open(P+'/chsubs_known.json')); chsubs=k['chsubs']; chmed=k['chmed']
manual={'Contour Atlas':1400,'Earth Tipping':1500,'Unseen Works':2910,'Spinosnack':603000,'Super Freaky Science!':8800,
 'HiddenHistory-02':2200,'Submerged History':1100,'Before Humanity':2600,'Signal & Nonsense':2800,'Earthyphus':1500,
 'Documentary Overload':44500,'Paper Skylines':7600}
src={}
for c,v in manual.items(): chsubs.setdefault(c,v); src[c]='context.md'
# yt-dlp rows (exact per video)
ytd={}
for l in open(P+'/meta.txt'):
    p=l.rstrip('\n').split('|')
    ytd[p[0]]={'subs':int(p[1]),'views':int(p[2]),'date':p[3],'dur':int(p[4])}
byid={r['id']:r for r in json.load(open(R+'/bench-packaging/all_rows2.json'))}
cands=json.load(open(P+'/cands.json'))
ids=[l.strip() for l in open(P+'/ids_sel.list') if l.strip()]
ds=[]
for i in ids:
    c=cands[i]; ch=c['channel']
    row={'id':i,'title':c['title'],'channel':ch,'views':c['views'],'len_s':c['len_s'],'age':c['age']}
    if i in ytd: row.update(subs=ytd[i]['subs'],views=ytd[i]['views'],date=ytd[i]['date'],subs_src='yt-dlp')
    elif i in byid and byid[i].get('subs'): row.update(subs=byid[i]['subs'],date=byid[i].get('date'),subs_src='bench')
    elif ch in chsubs: row.update(subs=chsubs[ch],subs_src=src.get(ch,'bench-channel'))
    else: row['subs']=None
    if ch in chmed: row['chmed']=chmed[ch]
    if row['subs']: row['ratio']=row['views']/row['subs']
    ds.append(row)
json.dump(ds,open(P+'/dataset.json','w'),indent=0)
kn=[r for r in ds if r.get('subs')]
print('total',len(ds),'with subs',len(kn))
import statistics
rs=sorted(r['ratio'] for r in kn); print('ratio quantiles', [round(rs[int(q*(len(rs)-1))],2) for q in (0,.25,.5,.75,.9,1)])
print('>=20:',sum(x>=20 for x in rs),' >=10:',sum(x>=10 for x in rs),' <3:',sum(x<3 for x in rs))
