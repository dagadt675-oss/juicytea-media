import numpy as np
from PIL import Image
im=np.array(Image.open('/home/user/juicytea-media/engine/www/lab/hawaii/data/hero_h16.png').convert('RGBA')).astype(np.uint32) if False else None
im=Image.open('/home/user/juicytea-media/engine/www/lab/hawaii/data/hero_h16.png'); print(im.mode, im.size)
a=np.array(im)
print(a.shape,a.dtype)
if a.ndim==3:
    h=((a[...,0].astype(np.float64)*256+a[...,1])/65535)*17000-8000
else:
    h=a.astype(np.float64)/65535*17000-8000
np.save('h.npy',h.astype(np.float32))
W=4096; lon0,lat0,lon1,lat1=-158.3,17.9,-153.8,21.8
# PNG row 0 = north
def ll(i,j): return lon0+(j+0.5)/W*(lon1-lon0), lat1-(i+0.5)/W*(lat1-lat0)
def ij(lon,lat): return int((lat1-lat)/(lat1-lat0)*W), int((lon-lon0)/(lon1-lon0)*W)
for name,(lo,la) in {'MaunaKea':(-155.468,19.821),'MaunaLoa':(-155.608,19.475),'Kilauea':(-155.287,19.421),'Hilo':(-155.09,19.72)}.items():
    i,j=ij(lo,la); print(name,h[i,j])
