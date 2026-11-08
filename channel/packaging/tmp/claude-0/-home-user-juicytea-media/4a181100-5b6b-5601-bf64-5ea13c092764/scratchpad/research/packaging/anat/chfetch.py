import json,sys,re,time,urllib.request,urllib.parse,statistics
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def v2i(s):
    s=(s or '').replace(',','').upper(); m=re.search(r'(\d[\d.]*)\s*([KMB]?)',s)
    return int(float(m.group(1))*{'K':1e3,'M':1e6,'B':1e9}.get(m.group(2),1)) if m else None
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'}),timeout=30).read().decode('utf-8','replace')
def chan(path):
    html=get('https://www.youtube.com'+path+'/videos')
    m=re.search(r'"content":"([\d.,]+[KMB]?) subscribers?"',html) or re.search(r'"([\d.,]+[KMB]?) subscribers?"',html)
    subs=v2i(m.group(1)) if m else None
    vids=[]
    mm=re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if mm:
        d=json.loads(mm.group(1))
        def walk(o):
            if isinstance(o,dict):
                if 'lockupViewModel' in o:
                    md=o['lockupViewModel'].get('metadata',{}).get('lockupMetadataViewModel',{})
                    parts=[p.get('text',{}).get('content','') for row in md.get('metadata',{}).get('contentMetadataViewModel',{}).get('metadataRows',[]) for p in row.get('metadataParts',[])]
                    if parts: vids.append(v2i(parts[0]))
                    return
                if 'videoRenderer' in o:
                    v=o['videoRenderer']; vids.append(v2i(v.get('viewCountText',{}).get('simpleText',''))); return
                for x in o.values(): walk(x)
            elif isinstance(o,list):
                for x in o: walk(x)
        walk(d)
    vv=[v for v in vids if v is not None]
    return {'subs':subs,'n':len(vv),'med':statistics.median(vv) if vv else None}
out={}
for path in sys.argv[2:]:
    try: out[path]=chan(path)
    except Exception as e: out[path]={'err':str(e)}
    print(path,out[path],file=sys.stderr); time.sleep(1)
json.dump(out,open(sys.argv[1],'w'),indent=0)
