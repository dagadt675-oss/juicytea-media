import json,re,numpy as np
from scipy.stats import mannwhitneyu, fisher_exact
A='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/anat'
m=json.load(open(A+'/merged.json')); codes=json.load(open(A+'/blind_codes.json')); inv={v:k for k,v in codes.items()}
FL='BACFSXMNDRGIKPWT'
for l in open(A+'/vcodes.txt'):
    if not re.match(r'^\d',l): continue
    c,w,h,f,foc,note=l.rstrip('\n').split('|',5)
    r=m[inv[int(c)]]; r['v']={'code':int(c),'words':int(w),'txt_h':float(h),'flags':f,'focal':foc,'note':note}
    for ch in FL: r['v'][ch]=int(ch in f)
    r['v']['nflags']=sum(r['v'][x] for x in 'ACCSXDRIG' if x!='C')+r['v']['C']  # graphic devices count: A,C,S,X,D,R,I,G
    r['v']['devices']=sum(r['v'][x] for x in 'ACDRIS')
    r['v']['cluttered']=int(r['v']['words']>=8 or r['v']['devices']>=3)
json.dump(m,open(A+'/merged.json','w'),indent=0)
E=[r for r in m.values() if r.get('subs') and r.get('age_d') and r['age_d']>=7 and (r.get('len_s') or 0)>=240]
rat=np.array([r['ratio'] for r in E]); t67=np.percentile(rat,66.7)
print('eligible',len(E),'ratio p66.7',round(t67,1))
def split(rows,key,thr):
    top=[r for r in rows if r[key] is not None and r[key]>=thr]; rest=[r for r in rows if r[key] is not None and r[key]<thr]; return top,rest
CONT=[('bright','m','Mean brightness (luma 0-255)'),('sat','m','Mean saturation (HSV S, %)'),('colourful','m','Colourfulness (Hasler-Susstrunk)'),
 ('dark','m','Dark pixels (luma<20%), % of frame'),('brightsat','m','Bright or saturated pixels, %'),('navy','m','Navy pixels, %'),('tan','m','Tan pixels, %'),('red','m','Saturated red pixels, %'),
 ('contrast','m','Luma std dev (contrast)'),('edges','m','Edge density (clutter), %'),('focal_blob','m','Focal blob area (computed), %'),('focal_bbox','m','Focal bbox area (computed), %'),('d_A','m','Feature distance to drain clones'),
 ('words','v','Words of text'),('txt_h','v','Tallest text line, % of height'),('devices','v','Graphic devices (arrow/ring/depth/region/inset/split)')]
BIN=[('B','caption box/banner'),('A','arrow'),('C','circle/ring'),('F','face (incl. cartoon)'),('S','before/after or left/right split'),('X','scale comparison'),('M','map or globe'),('N','numeral in text'),('D','depth/height label'),('R','red/orange highlighted region'),('G','grid/collage'),('I','inset picture'),('K','channel logo/brand'),('W','waterline over/under view'),('T','tan drained basin'),('P','postcard/paper frame')]
def get(r,k,src): return r[src].get(k)
def report(top,rest,label):
    out={'label':label,'n_top':len(top),'n_rest':len(rest),'cont':[],'bin':[],'extra':{}}
    for k,src,name in CONT:
        a=np.array([get(r,k,src) for r in top],float); b=np.array([get(r,k,src) for r in rest],float)
        p=mannwhitneyu(a,b).pvalue
        out['cont'].append((name,float(np.median(a)),float(np.median(b)),float(a.mean()),float(b.mean()),float(p)))
    for k,name in BIN:
        a=sum(r['v'][k] for r in top); b=sum(r['v'][k] for r in rest)
        p=fisher_exact([[a,len(top)-a],[b,len(rest)-b]]).pvalue
        out['bin'].append((name,100*a/len(top),100*b/len(rest),float(p)))
    for nm,fn in [('words 0',lambda r:r['v']['words']==0),('words 1-3',lambda r:1<=r['v']['words']<=3),('words 4-6',lambda r:4<=r['v']['words']<=6),('words 7+',lambda r:r['v']['words']>=7),
                  ('txt_h>=12%',lambda r:r['v']['txt_h']>=12),('txt_h>=15%',lambda r:r['v']['txt_h']>=15),('focal L (>=50%)',lambda r:r['v']['focal']=='L'),('focal S (<25%)',lambda r:r['v']['focal']=='S'),
                  ('0-1 devices',lambda r:r['v']['devices']<=1),('3+ devices',lambda r:r['v']['devices']>=3),('clone kit (box+arrow+depth)',lambda r:r['v']['B'] and r['v']['A'] and r['v']['D']),
                  ('passes gate.py',lambda r:r['m']['gate']),('legible text (1-4 words, line>=10%)',lambda r:1<=r['v']['words']<=4 and r['v']['txt_h']>=10),('no text',lambda r:r['v']['words']==0),('navy>=25%',lambda r:r['m']['navy']>=25),('dark>=40%',lambda r:r['m']['dark']>=40)]:
        a=sum(1 for r in top if fn(r)); b=sum(1 for r in rest if fn(r))
        out['extra'][nm]=(100*a/len(top),100*b/len(rest),float(fisher_exact([[a,len(top)-a],[b,len(rest)-b]]).pvalue))
    return out
res={}
TOP=lambda r: r['views']>=100000 and r['ratio']>=10
top=[r for r in E if TOP(r)]; rest=[r for r in E if not TOP(r)]
res['primary']=report(top,rest,'TOP = >=100K views AND views >= 10x subscribers; REST = all other eligible')
small=[r for r in E if r['subs']<100000]
res['small']=report([r for r in small if TOP(r)],[r for r in small if not TOP(r)],'channels under 100K subs only')
Eo=[r for r in E if r.get('outlier')]; oth=5.0
T3=lambda r: r['views']>=100000 and r['outlier']>=oth
res['outlier']=report([r for r in Eo if T3(r)],[r for r in Eo if not T3(r)],'TOP = >=100K views AND >=5x the channel median (outlier score)')
noclone=[r for r in E if r['group'] not in ('A_drain_clones','B_without_ice_water','D_template_farms','E_sleep_docs')]
res['noclone']=report([r for r in noclone if TOP(r)],[r for r in noclone if not TOP(r)],'excluding clone/template/sleep-doc groups')
oth=float(oth); t67=20.0
for r in E: r['top']=bool(TOP(r))
json.dump({r['id']:r['top'] for r in E},open(A+'/top_flags.json','w'))
res['meta']={'E':len(E),'t67':float(t67),'oth':float(oth),'n_small':len(small),'all':len(m),'with_subs':sum(1 for r in m.values() if r.get('subs'))}
json.dump(res,open(A+'/analysis.json','w'),indent=1)
for key in ('primary','small','outlier','noclone'):
    o=res[key]; print('\n==',o['label'],'top',o['n_top'],'rest',o['n_rest'])
    for n,a,b,ma,mb,p in o['cont']: print(f'  {n:55s} med {a:7.1f} vs {b:7.1f} | mean {ma:6.1f} vs {mb:6.1f} p={p:.3f}')
    for n,a,b,p in o['bin']: print(f'  {n:40s} {a:5.0f}% vs {b:5.0f}% p={p:.3f}')
    for n,(a,b,p) in o['extra'].items(): print(f'  {n:40s} {a:5.0f}% vs {b:5.0f}% p={p:.3f}')
