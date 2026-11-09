import json,re,statistics as st
db=json.load(open('chans.json'))
def days(a):
    m=re.search(r'(\d+)\s*(second|minute|hour|day|week|month|year|h\b|d\b|w\b|mo\b|y\b)',a or '')
    if not m: return None
    n=int(m.group(1)); u=m.group(2)
    return n*{'second':0,'minute':0,'hour':0,'h':0,'day':1,'d':1,'week':7,'w':7,'month':30,'mo':30,'year':365,'y':365}[u]
def chstats(h):
    c=db.get(h) or {}
    vs=[v for v in c.get('videos',[]) if days(v['age']) is not None]
    n30=sum(1 for v in vs if days(v['age'])<=30)
    settled=[v['views'] for v in vs if 7<=days(v['age'])<=90]
    med=st.median(settled) if settled else None
    allmed=st.median([v['views'] for v in vs]) if vs else None
    return {'subs':c.get('subs'),'n30':n30,'n_fetched':len(vs),'med_settled':med,'med_all':allmed,'name':c.get('name')}
def tier(s):
    if s is None: return '?'
    return '<10K' if s<1e4 else '10-100K' if s<1e5 else '100K-1M' if s<1e6 else '1M+'
