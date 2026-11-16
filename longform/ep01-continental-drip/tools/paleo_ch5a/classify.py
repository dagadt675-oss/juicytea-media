import json, numpy as np
from scipy.spatial import cKDTree
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/engine/www/paleo/'
tr=json.load(open(P+'tracks.json'))
def V(lonlat):
    a=np.asarray(lonlat,float); lon=np.radians(a[...,0]); lat=np.radians(a[...,1])
    return np.stack([np.cos(lat)*np.cos(lon), np.sin(lat), -np.cos(lat)*np.sin(lon)],-1)
def frame(p1,p2):
    e1=p1/np.linalg.norm(p1); e2=np.cross(p1,p2); e2/=np.linalg.norm(e2); e3=np.cross(e1,e2); return np.stack([e1,e2,e3],1)
pairs={'africa':('africa_c','cape_agulhas'),'samerica':('samerica_c','cape_horn'),'india':('india_c','kanyakumari'),'australia':('australia_c','tasmania_s'),'antarctica':('antarctica_c','south_pole')}
def R(c,T):
    a,b=pairs[c]; E=frame(V(tr[a][0]),V(tr[b][0])); F=frame(V(tr[a][T]),V(tr[b][T])); return F@E.T
coast={}
def load(T):
    if T not in coast: coast[T]=json.load(open(P+'coast_%03d.json'%T))
    return coast[T]
c0=load(0)
print('n polys',len(c0))
Ts=[10,60,120,170]
trees={}
for T in Ts:
    polys=load(T); pts=[];idx=[]
    for i,p in enumerate(polys):
        pts.extend(p); idx.extend([i]*len(p))
    trees[T]=(cKDTree(V(pts)), np.array(idx))
member={}
for i,p in enumerate(c0):
    pv=V(p)
    samp=pv[np.linspace(0,len(pv)-1,min(len(pv),8)).astype(int)]
    best=None
    for c in pairs:
        ok=True
        for T in Ts:
            q=samp@R(c,T).T
            d,_=trees[T][0].query(q)
            if np.median(d)>np.radians(0.3): ok=False;break
        if ok: best=c;break
    if best: member.setdefault(best,[]).append(i)
for c,l in member.items():
    nv=sum(len(c0[i]) for i in l)
    print(c,len(l),nv, sorted([len(c0[i]) for i in l])[-5:])
json.dump(member,open('member.json','w'))
