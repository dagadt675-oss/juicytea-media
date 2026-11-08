import json,sys,re,collections
W=sys.argv[1]
rows=[]
for f in sys.argv[2:]: rows+=json.load(open(f))
by={}
for r in rows:
    if r['id'] not in by: by[r['id']]=dict(r, queries=[r['query']])
    elif r['query'] not in by[r['id']]['queries']: by[r['id']]['queries'].append(r['query'])
u=list(by.values())
def months(age):
    m=re.match(r'(?:Streamed )?(\d+)\s*(\w+)',age or '')
    if not m: return None
    n=int(m.group(1)); unit=m.group(2)
    f={'s':1/2.6e6,'m':None,'h':1/730,'d':1/30.4,'w':7/30.4,'mo':1,'y':12}
    if unit.startswith('mo'): return n
    if unit.startswith('min'): return n/43800
    u0=unit[0]
    return n*{'s':1/2.6e6,'h':1/730,'d':1/30.4,'w':7/30.4,'y':12}.get(u0,0) or None
EXC=re.compile(r"relax|ambient|asmr|white noise|sleep music|meditat|calming|\bmusic\b|lofi|lo-fi|drone footage|4k drone|scenic|itinerar|things to do|vlog|hotel|resort|airbnb|cost of living|real estate|moving to|minecraft|roblox|\bgta\b|fortnite|\blive\b|livestream|news|cnn|\bfox\b|sermon|prophecy|\bbible\b|jesus|god's|trailer|full movie|movie|official video|lyrics|song|cooking|recipe|food tour|surf|snorkel|scuba|fishing|cruise|budget|travel guide|travel tips|best beaches|walking tour|tour\b|#shorts|podcast|episode \d+ \|", re.I)
TOPIC=re.compile(r"hawai|island|ocean|\bsea\b|seas\b|volcan|everest|mountain|\bmap|geograph|continent|earth|drain|without|water|\bice\b|trench|underwater|\blost\b|sunken|sank|atlantis|doggerland|zealandia|sundaland|beringia|countr|border|\bland|world|planet|lake|river|\bbay\b|mediterranean|pacific|atlantic|deep|tallest|biggest|largest|forbidden|remote|abandon|isolated|hidden|mystery|myster|places|place\b|mauna|kilauea|eruption|seafloor|sea floor|bottom|abyss|glacier|antarctic|arctic|greenland|tsunami|earthquake|plate|tectonic|magma|crater|caldera|summit|peak", re.I)
keep=[];drop=collections.Counter()
for r in u:
    t=r['title']
    if not (240<=r['len_s']<=4*3600): drop['len']+=1; continue
    asc=sum(1 for c in t if ord(c)<128)/max(1,len(t))
    if asc<0.95: drop['nonascii']+=1; continue
    if EXC.search(t): drop['exc']+=1; continue
    if not TOPIC.search(t): drop['topic']+=1; continue
    mo=months(r['age'])
    r['age_months']=round(mo,3) if mo else None
    if mo is None or mo<0.25: drop['age']+=1; continue
    if r['views']<1000: drop['views']+=1; continue
    keep.append(r)
print(drop, len(keep), 'channels', len(set(r['channel_id'] for r in keep)), file=sys.stderr)
json.dump(keep,open(W+'/raw/filtered.json','w'))
