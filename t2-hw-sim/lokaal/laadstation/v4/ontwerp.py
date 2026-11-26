"""V4 · mm. Bouw vanuit deze map met python ontwerp.py. NumPy vereist."""
from pathlib import Path
import numpy as np
import sys,struct,itertools
D=Path(__file__).resolve().parent
punten=64
class Solid:
 def __init__(self,fn,sc): self.fn=fn;self.sc=sc
 def __or__(a,b):return Solid(lambda p:np.minimum(a.fn(p),b.fn(p)),'union(){'+a.sc+b.sc+'}')
 def __sub__(a,b):return Solid(lambda p:np.maximum(a.fn(p),-b.fn(p)),'difference(){'+a.sc+b.sc+'}')
def vec(v):return '['+','.join(str(round(float(k),6)) for k in v)+']'
def block(x,X,y,Y,z,Z):
 def fn(p):
  a,b,c=p;return np.maximum(np.maximum(np.maximum(x-a,a-X),np.maximum(y-b,b-Y)),np.maximum(z-c,c-Z))
 return Solid(fn,'translate('+vec([x,y,z])+')cube('+vec([X-x,Y-y,Z-z])+');')
def circ(r):return [(r*np.cos(t),r*np.sin(t)) for t in np.arange(punten)*2*np.pi/punten]
def loft(axis,center,h,H,poly,poly2=None):
 # Doorsneden in XZ (langs Y) of XY (langs Z), convex en linksom.
 if poly2 is None:poly2=poly
 u,v=center
 A=np.array(poly);B=np.array(poly2);N=len(A); A+=np.zeros_like(A)
 def xyz(a,b,c):return [a+u,c,b+v] if axis==1 else [a+u,b+v,c]
 pts=np.array([xyz(a,b,c) for ar,c in [(A,h),(B,H)] for a,b in ar])
 faces=[list(range(N)),list(range(N,2*N))]
 for i in range(N):faces.extend([[i,(i+1)%N,(i+1)%N+N],[i,(i+1)%N+N,i+N]])
 mid=pts.mean(0);planes=[];ff=[]
 for f in faces:
  a,b,c=pts[f[:3]];n=np.cross(b-a,c-a);ln=np.linalg.norm(n)
  if ln<1e-9:continue
  n=n/ln
  if n@(mid-a)>0:n=-n;f=f[::-1]
  ff.append(f[::-1]);planes.append([*n,-n@a])
 # Het convexe omhulsel van twee doorsneden gebruikt de steunlijnen
 # van beide profielen, ook als de verbindende vierhoeken niet vlak zijn.
 planes=[]
 for ar in (A,B):
  for edge in np.roll(ar,-1,axis=0)-ar:
   n=np.array([edge[1],-edge[0]]);n=n/np.linalg.norm(n)
   for direction in (n,-n):
    a,b=direction;la=(A@direction).max();lb=(B@direction).max()
    slope=(lb-la)/(H-h);d=slope*h-la-a*u-b*v
    planes.append([a,-slope,b,d] if axis==1 else [a,b,-slope,d])
 planes.extend([[0,-1,0,h],[0,1,0,-H]] if axis==1 else [[0,0,-1,h],[0,0,1,-H]])
 planes=np.unique(np.round(planes,9),axis=0)
 def fn(p):
  x,y,z=p;res=-1e6
  for a,b,c,d in planes:res=np.maximum(res,a*x+b*y+c*z+d)
  return res
 def lamina(poly,pos,th):
  coords="["+",".join(vec(pt) for pt in poly)+"]"
  tr=vec([u,pos+th,v]) if axis==1 else vec([u,v,pos])
  rot="rotate([90,0,0])" if axis==1 else ""
  return "translate("+tr+")"+rot+f"linear_extrude({th})polygon("+coords+");"
 return Solid(fn,"hull(){"+lamina(A,h,.001)+lamina(B,H-.001,.001)+"}")
def cyl(axis,c,h,H,r,R=None):
 R=r if R is None else R
 def fn(p):
  x,y,z=p;v,u=(z,y) if axis==1 else (y,z)
  return np.maximum(np.hypot(x-c[0],v-c[1])-(r+(R-r)*np.clip((u-h)/(H-h),0,1)),np.maximum(h-u,u-H))
 rot="rotate([-90,0,0])" if axis==1 else ""
 start=[c[0],h,c[1]] if axis==1 else [*c,h]
 return Solid(fn,"translate("+vec(start)+")"+rot+f"cylinder(h={H-h},r1={r},r2={R});")
def slot(axis,x,y,h,H,wide,length):
 return cyl(axis,(x,y),h,H,wide)|cyl(axis,(x,y+length),h,H,wide)|block(x-wide,x+wide,y,y+length,h,H)
def railprof(side,inn,out,upper,h,H):
 # Gelijke doorsnede langs de rail, met 45 graden sluitlip.
 def strook(p):
  q=[(side*x,z) for x,z in p];return loft(1,(0,0),h,H,q)
 return strook([(inn,0),(out,0),(out,1.05),(inn,1.05)]) | strook([(inn,.99),(out,.99),(out,upper),(inn-upper+1,upper)])
# Ontwerpmaten in mm. Model-as Y wijst van batterij naar kabel; Z is omhoog.
wand=1.2; tape=.8; plaat=9.35; mag=3.125; magdiepte=8.15
px=14.; pz=11.75; mx=4.3; mz=4.35; pin=2.4; sp=.45; lengte=22.
taps=11.; mouth=12.9; mouth_x=19.85; onder=7.2
usb=13.5; huis=11.2; H=usb+mouth+1.25
reis=30.; pivot_y=40.; pivot_r=6.; pivot_sp=.35
batbreed=39.483; batlengte=89.782; bathoogte=16.5; poorthoogte=8.762 # uit STL, te meten
batbodem=usb-poorthoogte
def yz(poly,x,X):
 a=loft(1,(0,0),x,X,poly)
 return Solid(lambda p:a.fn((p[1],p[0],p[2])),'multmatrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]])'+a.sc)
def dak(r):return [(-r/2**.5,r/2**.5),(r/2**.5,r/2**.5),(0,r*2**.5)]
def rondgat(x,z,y,Y,r):return cyl(1,(x,z),y,Y,r)|loft(1,(x,z),y,Y,dak(r))
def profiel(r,b,h):
 return [(r*np.cos(t),b*np.sin(t)) for t in np.linspace(np.pi,2*np.pi,33)]+[(r*.7071,h-r*.7071),(0,h),(-r*.7071,h-r*.7071)]
def trechter(side):
 a=[(x+side*(mouth_x-px),z) for x,z in profiel(mouth,onder,mouth+.01)]
 b=profiel(pin+sp,pin+sp,(pin+sp)*2**.5)
 return loft(1,(side*px,pz),-.05,taps,a,b)|loft(1,(side*px,pz),taps-.03,lengte+1.5,b)
def robot():
 s=block(-18.8,18.8,0,plaat,0,16.8)-block(-5.95,5.95,-1,plaat+1,usb-3.8,19)
 for sign in [-1,1]:
  s=s-rondgat(sign*mx,mz,wand,plaat+.1,mag)
  s=s-rondgat(sign*px,pz,plaat-6.45,plaat+.1,2.62)
  s=s-cyl(1,(sign*px,pz),plaat-1.2,plaat+.02,2.62,3.43)
 # Centraal vlak 11 mm breed, vrij van de randdetails in de batterijmesh.
 # Werkelijke hoogte = max(0, 6.040 - 0.26795*d) vanaf laagste kastpunt.
 flat=batbodem-tape; front=batbodem+6.04-tape/np.cos(np.deg2rad(15))
 s=s|block(-5.5,5.5,-28,.15,0,flat)
 s=s|yz([(-22.55,0),(.15,0),(.15,front+.04),(-22.55,flat-.01)],-5.5,5.5)
 return s
def paspen():
 # Print verticaal; de conische schouder centreert in de robotplaat.
 return cyl(2,(0,0),0,5.12,2.38)|cyl(2,(0,0),5.08,6.1,2.38,3.2)|cyl(2,(0,0),6.07,8.55,3.2,pin)|cyl(2,(0,0),8.5,6.1+lengte-1,pin)|cyl(2,(0,0),6.1+lengte-1.02,6.1+lengte,pin,1.65)
def bandgat(y):
 return yz([(y-1.7,2),(y+1.7,2),(y+1.7,3),(y,4.7),(y-1.7,3)],-9,9)
def kop():
 w=20.5;h=pz+(pin+sp)*2**.5+1.5
 rect=lambda a,b:[(-a,0),(a,0),(a,b),(-a,b)]
 s=loft(1,(0,0),0,taps,rect(34.15,H),rect(w,h))|block(-w,w,taps-.03,25,0,h)
 s=s-block(-huis/2,huis/2,-1,26,usb-3.5,H+1)
 for sign in [-1,1]:
  s=s-trechter(sign)-rondgat(sign*mx,mz,-.05,magdiepte,mag)
  # Binder vlak achter beide magneetkamers. Huis eindigt op 9,65 mm bij nominale slag.
  lo,hi=sorted([sign*5.65,sign*7.05]);s=s-block(lo,hi,9.55,12.95,2.1,H+1)-block(lo,hi,5.8,12.95,10.0,H+1)
 s=s-bandgat(11.25)
 tail=[(-9,0),(9,0),(9,1),(6.2,3.8),(-6.2,3.8),(-9,1)]
 s=s|loft(1,(0,0),24.9,98,tail)|block(-3.6,3.6,24.8,43,0,usb-2.8)
 for sign in [-1,1]:
  lo,hi=sorted([sign*3.7,sign*5.1]);s=s-block(lo,hi,32.3,35.7,2.1,13)
 return s-bandgat(34)-cyl(2,(4.3,90),-1,6,1.7)
def basis():
 s=block(-13,13,27,99,-12.4,0)
 for side in [-1,1]:s=s|railprof(side,9.4,13,3.3,27,99)
 return s-slot(2,4.3,90-reis,-3.9,.3,1.85,reis)-cyl(2,(0,pivot_y),-13,.2,pivot_r+pivot_sp)-cyl(2,(0,pivot_y),-4.5,.2,8.3)
def draaiplaat():
 # Open draaipenverbinding. Uitnemen door recht omhoog te tillen.
 return (cyl(2,(0,pivot_y),0,3.2,18)|cyl(2,(0,pivot_y),3.17,11.5,pivot_r))-cyl(2,(0,pivot_y),1.4,12,1.30)
def borgpen():return cyl(2,(0,0),0,2,2.9)|cyl(2,(0,0),1.96,8.8,1.49)
def mal():
 # Referentie op het breedste kastgebied, met midden vrij voor het tapeschoentje.
 s=block(-21.3,21.3,-52,-48,-1,batbodem)
 # Achterste kastvlak en voorste plaatvlak fixeren de langspositie.
 end=-batlengte-.12
 s=s|block(-18,18,end-1.6,end,-1,batbodem+14.1)
 s=s|block(-20.5,20.5,plaat+.12,plaat+1.72,-1,2.2)
 for sign in [-1,1]:
  def L(a,b,y,Y,z,Z):
   lo,hi=sorted([sign*a,sign*b]);return block(lo,hi,y,Y,z,Z)
  s=s|L(9,21.3,-52,plaat,-1,0)|L(19.99,21.3,-52,-24,-1,batbodem+14.1)
  s=s|L(19.05,20.5,0,plaat+.3,-1,4)|L(9,12,end-.1,-51.9,-1,.8)
 return s
def qrhouder():
 # Los, plaatsbaar op eigen voet buiten het bewegingsvolume. Kaart van boven.
 s=block(-19,19,-5,7,0,2)|block(-18,18,0,4.8,1.9,34)
 return s-block(-16.1,16.1,1.5,3.25,3.2,35)-block(-14.8,14.8,-.1,2,4.5,35)
def coupon():
 s=block(0,34.15,0,13,0,H)
 return s-trechter(1)-rondgat(mx,mz,-.1,magdiepte,mag)
def kaartje():return block(-15.8,15.8,0,32,0,1.2)
parts={
 'qrkaartje':(kaartje,((-17,17),(-2,34),(-2,3)),.33),
 'robot':(robot,((-20,20),(-30,11),(-2,19)),.27),
 'paspen':(paspen,((-5,5),(-5,5),(-1,30)),.22),
 'dockkop':(kop,((-36,36),(-2,100),(-2,30)),.42),
 'railvoet':(basis,((-15,15),(25,101),(-14,5)),.32),
 'draaiplaat':(draaiplaat,((-20,20),(20,60),(-2,13)),.32),
 'borgpen':(borgpen,((-4,4),(-4,4),(-1,10)),.18),
 'plakmal':(mal,((-23,23),(-94,13),(-3,21)),.34),
 'qrhouder':(qrhouder,((-21,21),(-7,9),(-2,36)),.32),
 'coupon':(coupon,((-2,36),(-2,15),(-2,30)),.32)}
def mesh(name,obj,bounds,h):
 axes=[np.arange(lo-.71832*h,hi+1.8*h,h) for lo,hi in bounds];x,y=np.meshgrid(*axes[:2],indexing='ij')
 corners=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
 faces=[];prev=obj.fn((x,y,axes[2][0]))
 for k,z in enumerate(axes[2][1:]):
  cur=obj.fn((x,y,z));vals=np.stack([(cur if l else prev)[i:i+x.shape[0]-1,j:j+y.shape[1]-1] for i,j,l in corners],axis=-1);prev=cur
  ix,iy=np.where((vals.min(2)<0)&(vals.max(2)>=0))
  if not len(ix):continue
  base=np.stack((axes[0][ix],axes[1][iy],np.full(len(ix),axes[2][k])),axis=-1);vs=vals[ix,iy]
  for ids in ([0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]):
   pts=corners[ids];f=vs[:,ids];codes=(f<0)@[1,2,4,8]
   for code in np.unique(codes):
    if code in (0,15):continue
    mask=codes==code;inside=[i for i in range(4) if code>>i&1];outside=[i for i in range(4) if i not in inside];edges=list(itertools.product(inside,outside))
    if len(edges)==4:edges[2],edges[3]=edges[3],edges[2]
    poly=[]
    for i,j in edges:
     frac=f[mask,i]/(f[mask,i]-f[mask,j]);poly.append(base[mask]+h*(pts[i]+frac[:,None]*(pts[j]-pts[i])))
    for j in range(1,len(poly)-1):
     tri=np.stack((poly[0],poly[j],poly[j+1]),axis=1)
     if np.dot(np.cross(tri[0,1]-tri[0,0],tri[0,2]-tri[0,0]),pts[outside[0]]-pts[inside[0]])<0:tri=tri[:,[0,2,1]]
     faces.append(tri)
 t=np.concatenate(faces)
 if False:t=t[:,:,[0,2,1]];t[:,:,1]*=-1
 t[:,:,2]-=t[:,:,2].min()
 t=t.astype('f4');norm=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);l=np.linalg.norm(norm,axis=1)
 t=t[l>0];norm=norm[l>0]/l[l>0,None]
 dt=[('n','<f4',3),('t','<f4',(3,3)),('a','<u2')];rec=np.zeros(len(t),dtype=dt);rec['t']=t;rec['n']=norm
 p=D/(name+'.stl');p.write_bytes(bytes(80)+struct.pack('<I',len(t))+rec.tobytes())
 t=np.frombuffer(p.read_bytes()[84:],dtype=dt)['t'];vs,idx=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);idx=idx.reshape(-1,3)
 edges=np.vstack([idx[:,[0,1]],idx[:,[1,2]],idx[:,[2,0]]]);key=edges[:,0]*len(vs)+edges[:,1]
 assert np.array_equal(np.sort(key),np.sort(edges[:,1]*len(vs)+edges[:,0])) and len(np.unique(key))==len(key),name
 parent=np.arange(len(vs))
 while True:
  old=parent.copy();small=old[idx].min(1)
  for i in range(3):np.minimum.at(parent,old[idx[:,i]],small)
  parent=parent[parent]
  if np.array_equal(parent,old):break
 assert len(np.unique(parent))==1,name
 vol=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum(dtype=float)/6000;assert vol>0
 print(name,'mm',np.ptp(vs,axis=0),'cm3',round(vol,3),'gesloten verbonden mesh',flush=True)
if __name__=='__main__':
 for key in sys.argv[1:] or parts:
  make,bounds,h=parts[key];mesh(key,make(),bounds,h)





