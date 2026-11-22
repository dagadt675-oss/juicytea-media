import urllib.request,re,json,sys,time,html
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def get(u):
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9','Cookie':'CONSENT=YES+1'})
    return urllib.request.urlopen(req,timeout=40).read().decode('utf-8','replace')
for vid in sys.argv[1:]:
    try:
        h=get('https://www.youtube.com/watch?v='+vid)
        m=re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\});(?:var |</script>)',h)
        p=json.loads(m.group(1))
        tr=p.get('captions',{}).get('playerCaptionsTracklistRenderer',{}).get('captionTracks',[])
        t=[x for x in tr if x.get('languageCode','').startswith('en')] or tr
        if not t: print(vid,'NO CAPTIONS'); continue
        x=get(t[0]['baseUrl']+'&fmt=json3')
        if not x.strip(): print(vid,'empty caption body'); continue
        j=json.loads(x)
        out=[]
        for e in j.get('events',[]):
            st=e.get('tStartMs',0)/1000
            if st>45: break
            s=''.join(sg.get('utf8','') for sg in e.get('segs',[]) or [])
            if s.strip(): out.append(f'{st:5.1f} {s.strip()}')
        json.dump({'vid':vid,'title':p['videoDetails']['title'],'lines':out},open(f'tx/{vid}.json','w'))
        print('==',vid,p['videoDetails']['title'],'|',p['videoDetails'].get('author'))
        print('\n'.join(out[:40]))
    except Exception as e:
        print(vid,'ERR',e)
    time.sleep(4)
