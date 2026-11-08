import json, glob, os
R='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research'
P=R+'/packaging/data'
chsubs={}; byid={}; chmed={}
for r in json.load(open(R+'/bench-packaging/all_rows2.json')):
    if r.get('subs'): chsubs[r['ch']]=r['subs']
    if r.get('chmed'): chmed[r['ch']]=r['chmed']
    byid[r['id']]=r
for f in glob.glob(R+'/bench-packaging/meta*.txt')+[P+'/meta.txt']:
    for l in open(f):
        p=l.rstrip('\n').split('|')
        if len(p)<8: continue
        if f.endswith('packaging/data/meta.txt'):
            vid,subs,views,date,dur,ch=p[0],p[1],p[2],p[3],p[4],p[5]
        else:
            vid,ch,_,subs,date,views,dur=p[:7]
        try: chsubs[ch]=int(subs)
        except: pass
for f in glob.glob(R+'/bench-packaging/ch/*.json'):
    d=json.load(open(f))
    if d.get('channel_follower_count'): chsubs[d['channel']]=d['channel_follower_count']
json.dump({'chsubs':chsubs,'chmed':chmed},open(P+'/chsubs_known.json','w'),indent=0)
cands=json.load(open(P+'/cands.json'))
ids=[l.strip() for l in open(P+'/ids_sel.list') if l.strip()]
miss=set()
for i in ids:
    c=cands[i]['channel']
    if c not in chsubs: miss.add(c)
print(len(chsubs),'channels known; missing',len(miss))
print(sorted(miss))
