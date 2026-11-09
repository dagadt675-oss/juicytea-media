// Equal Earth projection matching tex/equal_earth.jpg (3600x1760 px). ee(lon,lat) -> [x,y] in IMAGE pixels.
const A1=1.340264,A2=-0.081106,A3=0.000893,A4=0.003796,M=Math.sqrt(3)/2,S=651.7329707517487,CX=1800.0,CY=880.0;
export const EE_W=3600, EE_H=1760;
export function ee(lon,lat){const l=lon*Math.PI/180,p=lat*Math.PI/180,th=Math.asin(M*Math.sin(p)),t2=th*th,t6=t2*t2*t2;
  const x=l*Math.cos(th)/(M*(A1+3*A2*t2+t6*(7*A3+9*A4*t2))), y=th*(A1+A2*t2+t6*(A3+A4*t2)); return [CX+x*S, CY-y*S];}
// map image -> screen with a view {cx, cy, zoom} in IMAGE px: returns [sx, sy] for a W x H screen
export function eeScreen(lon,lat,view,W,H){const [x,y]=ee(lon,lat); const z=view.zoom*Math.min(W/EE_W,H/EE_H); return [W/2+(x-view.cx)*z, H/2+(y-view.cy)*z];}
export function drawEE(ctx,img,view,W,H){const z=view.zoom*Math.min(W/EE_W,H/EE_H); ctx.drawImage(img, W/2-view.cx*z, H/2-view.cy*z, EE_W*z, EE_H*z);}
