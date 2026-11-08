import numpy as np
from scipy import ndimage as nd
h=np.load('h.npy'); W=4096; lon0,lat0,lon1,lat1=-158.3,17.9,-153.8,21.8
dx=(lon1-lon0)/W*111.32*np.cos(np.radians(19.6)); dy=(lat1-lat0)/W*111.32
print('cell km',dx,dy)
# restrict to Big Island region
i0,i1=int((lat1-20.4)/(lat1-lat0)*W),int((lat1-18.7)/(lat1-lat0)*W)
j0,j1=int((-156.3-lon0)/(lon1-lon0)*W),int((-154.6-lon0)/(lon1-lon0)*W)
sub=h[i0:i1,j0:j1]
deep=sub<-2000
dist,ind=nd.distance_transform_edt(~deep,sampling=(dy,dx),return_indices=True)
# coastline cells: land cells adjacent to sea
land=sub>0
coast=land & ~nd.binary_erosion(land)
ci,cj=np.nonzero(coast)
d=dist[ci,cj]
# only Big Island coast: exclude Maui (lat>20.3)
lat=lat1-(ci+i0+0.5)/W*(lat1-lat0); lon=lon0+(cj+j0+0.5)/W*(lon1-lon0)
m=(lat<20.3)
order=np.argsort(d[m])
for k in order[:5]:
    pass
# bin by bearing around island center
c=(-155.5,19.6)
ang=np.degrees(np.arctan2((lat[m]-c[1]),(lon[m]-c[0])*np.cos(np.radians(19.6))))
bins=np.arange(-180,181,15)
for b0 in bins[:-1]:
    s=(ang>=b0)&(ang<b0+15)
    if s.sum()==0: continue
    dd=d[m][s]; k=np.argmin(dd)
    print(f"bearing {b0:5d}..{b0+15:4d}: coast pts {s.sum():4d}  median dist to -2000: {np.median(dd):5.1f} km  min {dd[k]:4.1f} at {lon[m][s][k]:.3f},{lat[m][s][k]:.3f}")
