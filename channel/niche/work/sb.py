import urllib.request,re,json,sys,time,io
from PIL import Image
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
OUT='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/refs/sb'
import os; os.makedirs(OUT,exist_ok=True)
def get(u,binary=False):
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9','Cookie':'CONSENT=YES+1'})
    d=urllib.request.urlopen(req,timeout=40).read()
    return d if binary else d.decode('utf-8','replace')
for vid in sys.argv[1:]:
    try:
        h=get('https://www.youtube.com/watch?v='+vid)
        m=re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\});(?:var |</script>)',h)
        p=json.loads(m.group(1))
        spec=p.get('storyboards',{}).get('playerStoryboardSpecRenderer',{}).get('spec')
        dur=int(p['videoDetails'].get('lengthSeconds',0))
        if not spec: print(vid,'no spec'); continue
        parts=spec.split('|'); base=parts[0]; levels=parts[1:]
        L=len(levels)-1
        w,hh,cnt,cols,rows,interval,name,sigh=levels[L].split('#')
        w,hh,cnt,cols,rows,interval=map(int,(w,hh,cnt,cols,rows,interval))
        if interval==0: interval=int(dur*1000/cnt) if cnt else 0
        url=base.replace('$L',str(L)).replace('$N',name)+'&sigh='+sigh
        frames=[]
        per=cols*rows; need=[i for i in range(cnt) if i*interval/1000<=32]
        sheets=sorted(set(i//per for i in need))
        for s in sheets:
            img=Image.open(io.BytesIO(get(url.replace('M$M','M%d'%s),True))).convert('RGB')
            for i in need:
                if i//per!=s: continue
                k=i%per; x=(k%cols)*w; y=(k//cols)*hh
                frames.append((i*interval/1000,img.crop((x,y,x+w,y+hh))))
        # compose strip
        n=len(frames); C=8; R=(n+C-1)//C
        sh=Image.new('RGB',(C*w,R*(hh+14)),(10,10,10))
        from PIL import ImageDraw; d=ImageDraw.Draw(sh)
        for j,(t,f) in enumerate(frames):
            x=(j%C)*w; y=(j//C)*(hh+14); sh.paste(f,(x,y)); d.text((x+2,y+hh),f'{t:.1f}s',fill=(255,220,0))
        sh.save(f'{OUT}/{vid}_open.jpg',quality=88)
        print(vid,p['videoDetails']['author'],'|',p['videoDetails']['title'][:60],'| level',L,w,'x',hh,'interval ms',interval,'frames',n)
    except Exception as e:
        print(vid,'ERR',repr(e)[:200])
    time.sleep(3)
