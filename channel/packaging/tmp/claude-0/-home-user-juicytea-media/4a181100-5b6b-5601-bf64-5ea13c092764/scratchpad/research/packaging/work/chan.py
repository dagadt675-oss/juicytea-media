import json,sys,re,time,os,urllib.request,concurrent.futures as cf,statistics
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
W=sys.argv[1]; inp=sys.argv[2]; outp=W+'/raw/channels.json'
db=json.load(open(outp)) if os.path.exists(outp) else {}
ids=sorted(set(r['channel_id'] for r in json.load(open(inp)) if r['channel_id'])-set(db))
print('todo',len(ids),file=sys.stderr)
def v2i(s):
    s=(s or '').replace(',','').upper()
    m=re.search(r'(\d[\d.]*)\s*([KMB]?)',s)
    return int(float(m.group(1))*{'K':1e3,'M':1e6,'B':1e9}.get(m.group(2),1)) if m else None
def one(cid):
    url=f'https://www.youtube.com/channel/{cid}/videos'
    html=None
    for i in range(3):
        try:
            html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'}),timeout=30).read().decode('utf-8','replace'); break
        except Exception as e:
            time.sleep(2+2*i)
    if html is None: return cid,{'err':1}
    m=re.search(r'"content":"([\d.,]+[KMB]?) subscribers?"',html)
    subs=v2i(m.group(1)) if m else None
    vids=[]
    mm=re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if mm:
        d=json.loads(mm.group(1))
        def walk(o):
            if isinstance(o,dict):
                if 'lockupViewModel' in o:
                    lv=o['lockupViewModel']; md=lv.get('metadata',{}).get('lockupMetadataViewModel',{})
                    t=md.get('title',{}).get('content','')
                    parts=[p.get('text',{}).get('content','') for row in md.get('metadata',{}).get('contentMetadataViewModel',{}).get('metadataRows',[]) for p in row.get('metadataParts',[])]
                    s=json.dumps(lv.get('contentImage',{}))
                    ln=re.findall(r'"text": "(\d+:\d+(?::\d+)?)"',s)
                    vids.append({'id':lv.get('contentId'),'title':t,'views':v2i(parts[0]) if parts else None,'age':parts[1] if len(parts)>1 else '','len':ln[0] if ln else ''})
                    return
                for x in o.values(): walk(x)
            elif isinstance(o,list):
                for x in o: walk(x)
        walk(d)
    vv=[v['views'] for v in vids if v['views'] is not None]
    return cid,{'subs':subs,'n_recent':len(vv),'median_recent_views':statistics.median(vv) if vv else None,'recent':vids}
n=0
with cf.ThreadPoolExecutor(6) as ex:
    for cid,res in ex.map(one,ids):
        db[cid]=res; n+=1
        if n%100==0:
            json.dump(db,open(outp,'w')); print(n,file=sys.stderr)
json.dump(db,open(outp,'w')); print('done',len(db),file=sys.stderr)
