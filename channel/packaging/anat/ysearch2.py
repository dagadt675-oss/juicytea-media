"""Search probe that also records channel url/id. Usage: ysearch2.py OUT.json "q1" "q2" ..."""
import json,re,sys,time,urllib.parse,urllib.request
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def v2i(s):
    s=(s or '').replace(',','').lower(); m=re.search(r'([\d.]+)\s*([kmb]?)',s)
    return int(float(m.group(1))*{'k':1e3,'m':1e6,'b':1e9}.get(m.group(2),1)) if m else 0
def l2s(s):
    t=0
    for p in (s or '').split(':'):
        if p.isdigit(): t=t*60+int(p)
    return t
def fetch(q):
    url='https://www.youtube.com/results?search_query='+urllib.parse.quote(q)
    html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'}),timeout=40).read().decode('utf-8','replace')
    m=re.search(r'var ytInitialData = (\{.*?\});</script>',html)
    if not m: return []
    out=[]
    def walk(o):
        if isinstance(o,dict):
            if 'videoRenderer' in o:
                v=o['videoRenderer']; ow=v.get('ownerText',{}).get('runs',[{}])[0]
                be=ow.get('navigationEndpoint',{}).get('browseEndpoint',{})
                out.append({'id':v.get('videoId'),'title':''.join(r.get('text','') for r in v.get('title',{}).get('runs',[])),
                    'channel':ow.get('text',''),'cid':be.get('browseId'),'curl':be.get('canonicalBaseUrl'),
                    'views':v2i(v.get('viewCountText',{}).get('simpleText') or ''.join(r.get('text','') for r in v.get('viewCountText',{}).get('runs',[]))),
                    'len_s':l2s(v.get('lengthText',{}).get('simpleText')),'age':v.get('publishedTimeText',{}).get('simpleText','')})
                return
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(json.loads(m.group(1)))
    return out
res={}
for q in sys.argv[2:]:
    try: res[q]=fetch(q)
    except Exception as e: res[q]={'err':str(e)}
    print(q,len(res[q]),file=sys.stderr); time.sleep(1)
json.dump(res,open(sys.argv[1],'w'),indent=0)
