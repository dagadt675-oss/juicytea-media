import json, numpy as np, sys
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
P='/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
def otsu(x):
    h,b=np.histogram(x,bins=64); h=h.astype(float); w=np.cumsum(h); m=np.cumsum(h*b[:-1])
    mt=m[-1]; wt=w[-1]; best=0; t=b[0]
    for i in range(1,63):
        if w[i]==0 or wt-w[i]==0: continue
        mb=m[i]/w[i]; mf=(mt-m[i])/(wt-w[i]); v=w[i]*(wt-w[i])*(mb-mf)**2
        if v>best: best=v; t=b[i]
    return t
def metrics(path):
    im=Image.open(path).convert('RGB')
    # crop letterbox bars (hqdefault 4:3 with black bars)
    a=np.asarray(im).astype(float)
    rowmax=a.max(axis=(1,2)); rows=np.where(rowmax>20)[0]
    if len(rows) and (rows[0]>5 or rows[-1]<a.shape[0]-6):
        im=im.crop((0,rows[0],im.width,rows[-1]+1))
    im=im.resize((320,180),Image.LANCZOS)
    a=np.asarray(im).astype(float)/255.0
    r,g,b=a[...,0],a[...,1],a[...,2]
    luma=0.299*r+0.587*g+0.114*b
    hsv=np.asarray(im.convert('HSV')).astype(float)/255.0
    H,S,V=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    rg=r-g; yb=0.5*(r+g)-b
    colourful=np.sqrt(rg.std()**2+yb.std()**2)+0.3*np.sqrt(rg.mean()**2+yb.mean()**2)
    dark=(luma<0.2).mean()
    brightsat=((V>0.6)&((S>0.45)|(V>0.85))).mean()
    navy=((H>190)&(H<260)&(V<0.45)&(S>0.25)).mean()
    warm=(((H<50)|(H>330))&(S>0.45)&(V>0.4)).mean()
    cyan=((H>165)&(H<205)&(S>0.35)&(V>0.5)).mean()
    gx=ndi.sobel(luma,1); gy=ndi.sobel(luma,0); mag=np.hypot(gx,gy)
    edges=(mag>0.5).mean()
    # focal subject: colour distinctiveness from border colour, Otsu, largest blob bbox
    lab=np.asarray(im.convert('LAB')).astype(float)
    border=np.concatenate([lab[:8].reshape(-1,3),lab[-8:].reshape(-1,3),lab[:,:8].reshape(-1,3),lab[:,-8:].reshape(-1,3)])
    bm=np.median(border,axis=0)
    d=np.sqrt(((lab-bm)**2).sum(-1)); d=ndi.gaussian_filter(d,3)
    t=otsu(d.ravel()); mask=d>t
    mask=ndi.binary_opening(mask,iterations=2)
    lbl,n=ndi.label(mask)
    if n:
        sizes=ndi.sum(mask,lbl,range(1,n+1)); k=int(np.argmax(sizes))+1
        ys,xs=np.where(lbl==k); bbox=(xs.max()-xs.min()+1)*(ys.max()-ys.min()+1)/(320*180); blob=sizes[k-1]/(320*180)
    else: bbox=blob=0.0
    # spectral residual saliency
    sm=np.asarray(im.convert('L').resize((128,72))).astype(float)
    F=np.fft.fft2(sm); A=np.log(np.abs(F)+1e-9); Ph=np.angle(F)
    SR=A-ndi.uniform_filter(A,3); sal=np.abs(np.fft.ifft2(np.exp(SR+1j*Ph)))**2; sal=ndi.gaussian_filter(sal,2.5)
    salm=sal>3*sal.mean(); salfrac=salm.mean()
    return dict(bright=round(luma.mean()*255,1),sat=round(S.mean()*100,1),colourful=round(colourful*255,1),
        dark=round(dark*100,1),brightsat=round(brightsat*100,1),navy=round(navy*100,1),warm=round(warm*100,1),cyan=round(cyan*100,1),
        contrast=round(luma.std()*255,1),edges=round(edges*100,1),focal_bbox=round(bbox*100,1),focal_blob=round(blob*100,1),sal=round(salfrac*100,1),
        size=Image.open(path).size)
ds=json.load(open(P+'/data/dataset.json'))
for r in ds:
    r['m']=metrics(P+'/refs/thumbs/%s.jpg'%r['id'])
json.dump(ds,open(P+'/data/dataset.json','w'),indent=0)
print(json.dumps(ds[0]['m']))
