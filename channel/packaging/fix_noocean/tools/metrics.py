"""metrics.py IMG [...]: mean luma, p90, Hasler-Susstrunk colourfulness at full size and at 168x94, mean chroma (Lab) of the top-25% most chromatic pixels."""
import sys, numpy as np
from PIL import Image
def hs(a):
    r,g,b=a[...,0],a[...,1],a[...,2]; rg=r-g; yb=0.5*(r+g)-b
    return float(np.sqrt(rg.std()**2+yb.std()**2)+0.3*np.sqrt(rg.mean()**2+yb.mean()**2))
def m(p):
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(np.float32)
    l=(a*[0.2126,0.7152,0.0722]).sum(-1)
    s=np.asarray(im.resize((168,94),Image.LANCZOS)).astype(np.float32)
    sm=np.asarray(im.resize((320,180),Image.BOX)).astype(np.float32); C=sm.max(-1)-sm.min(-1)
    return dict(luma=round(float(l.mean()),1),p90=round(float(np.percentile(l,90)),1),sd=round(float(l.std()),1),colorful=round(hs(a),1),colorful168=round(hs(s),1),
                chroma_top25=round(float(np.sort(C.ravel())[-C.size//4:].mean()),1))
if __name__=='__main__':
    for p in sys.argv[1:]: print(p.split('/')[-1], m(p))
