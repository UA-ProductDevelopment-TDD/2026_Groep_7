"""Parametrisch ontwerp in mm. Genereert print-STL's en dezelfde CSG als OpenSCAD."""
from pathlib import Path
import numpy as np
import struct, itertools, sys
D=Path(__file__).resolve().parent
# Proefmaten; toleranties per zijde. Magneet en kabel volgens opdracht.
pin=1.65; passing=.45; mond=6.4; onder=2.9; taps=7.; penlengte=16.
px=13.7; pz=13.0; mz=4.35; mag=3.125; magdiepte=4.15
huis=11.2; usb_z=11.4; usb_h=7.; railspel=.40; slag=6.; wand=1.2
plaat=5.35; tape=.8; usb_slag=6.; reces=0.; metalen_neus=7.
top=pz+mond+wand; hoogte=14.75
punten=64
assert px-mond-huis/2>=wand and pz-onder-mz-mag*2**.5>=wand and mz-mag>=wand
assert penlengte-taps-1>usb_slag+reces and penlengte>plaat+tape+usb_slag+reces
assert 10.5-usb_z+hoogte+.2<14.1 and 2*19.3<43
# Primitieven: dezelfde convexe polyeders worden analytisch bemonsterd en als SCAD geschreven.
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
 return Solid(fn,'polyhedron(points=['+','.join(map(vec,pts))+'],faces=['+','.join('['+','.join(map(str,f))+']' for f in ff)+'],convexity=8);')
def cyl(axis,c,h,H,r,R=None):return loft(axis,c,h,H,circ(r),circ(r if R is None else R))
def funnel(s):
 # Onderste halve ellips, bovenaan zelfdragend puntdak met flanken >=45 graden.
 def prof(r,b,roof):
  vals=[(r*np.cos(t),b*np.sin(t)) for t in np.linspace(np.pi,2*np.pi,33)]
  return vals+[(r*.7071,roof-r*.7071),(0,roof),(-r*.7071,roof-r*.7071)]
 a=prof(mond,onder,mond+.01);b=prof(pin+passing,pin+passing,(pin+passing)*2**.5)
 return loft(1,(s*px,pz),-.04,taps,a,b)|loft(1,(s*px,pz),taps-.03,17.4,b)
def magvak(cx):
 # Rond zitvlak, uitsluitend bovenaan een vrijloop van 45 graden.
 dak=[(-mag/2**.5,mag/2**.5),(mag/2**.5,mag/2**.5),(0,mag*2**.5)]
 return cyl(1,(cx,mz),-.05,magdiepte,mag)|loft(1,(cx,mz),-.05,magdiepte,dak)
def slot(axis,x,y,h,H,wide,length):
 return cyl(axis,(x,y),h,H,wide)|cyl(axis,(x,y+length),h,H,wide)|block(x-wide,x+wide,y,y+length,h,H)
def railprof(side,inn,out,upper,h,H):
 # Gelijke doorsnede langs de rail, met 45 graden sluitlip.
 def strook(p):
  q=[(side*x,z) for x,z in p];return loft(1,(0,0),h,H,q)
 return strook([(inn,0),(out,0),(out,1.05),(inn,1.05)]) | strook([(inn,.99),(out,.99),(out,upper),(inn-upper+1,upper)])
def robot():
 # In bedrijfsstand loopt de pen langs +Y; tapezijde ligt op y=0.
 s=block(-19.3,19.3,0,plaat,0,hoogte)-block(-5.8,5.8,-1,4,6.25,20)
 for side in [-1,1]:
  c=(side*px,pz)
  s=s|cyl(1,c,plaat-.05,plaat+penlengte-1,pin)|cyl(1,c,plaat+penlengte-1,plaat+penlengte,pin,pin-.55)
  # Lokaal dikker materiaal voor het blinde magneetgat; naar voren gericht.
  # Vlakke gezamenlijke aanslag voor magneet, tapeplaat en pen.
  s=s-cyl(1,(side*px,mz),wand,magdiepte+wand+.05,mag)
 return s
# Beide magneetparen liggen in dezelfde vlakke aanslag als de pengaten.
def kop(coupon=False):
 stop=magdiepte+wand-plaat
 s=block(-22,22,0,19,0,top)
 s=s-block(-huis/2,huis/2,-1,20,usb_z-usb_h/2,25)
 for side in [-1,1]:
  s=s-funnel(side)
  # Volledig kopvlak teruggenomen onder de pengaten; bossen botsen nergens.
  # Geen verzonken blokinterface: beide contactvlakken zijn vlak.
  s=s-magvak(side*px)
  # Arm binnenrand eindigt exact bij de buitenkant van het pengat.
  near=px+mond; far=near+19
  # Buitenste pinrand volgt de binnenkant van de arm. Vanaf het front loopt de mond taps door.
  arm=[(side*near,0),(side*far,-37),(side*(far+2.4),-37),(side*(near+2.4),.08)]
  s=s|loft(2,(0,0),0,hoogte,arm)
 # Bindersleuven: verticaal langs het huis en door een dwarstunnel eronder.
 for side in [-1,1]:
  lo,hi=sorted([side*5.65,side*7.05]);s=s-block(lo,hi,8.3,11.7,2.1,25)
 # Korte overbrugging van 3,4 mm voor de binder; bovenkant als 45 graden tent.
 def bandgat(y):
  poly=[(y-1.7,2),(y+1.7,2),(y+1.7,3),(y,4.7),(y-1.7,3)]
  # X-extrusie van YZ: wissel X en Y van een Y-extrusie.
  a=loft(1,(0,0),-9,9,poly);return Solid(lambda p:a.fn((p[1],p[0],p[2])),'multmatrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]])'+a.sc)
 s=s-bandgat(10)
 # De staart IS de slede. De railvoet grijpt de schuine buitenranden.
 tail=[(-9,0),(9,0),(9,1),(6.2,3.8),(-6.2,3.8),(-9,1)]
 s=s|loft(1,(0,0),18.92,55,tail)
 s=s|block(-3.6,3.6,18.9,33,0,8)
 for side in [-1,1]:
  lo,hi=sorted([side*3.7,side*5.1]);s=s-block(lo,hi,25.3,28.7,2.1,9)
 s=s-bandgat(27)
 s=s-cyl(2,(4.3,49),-1,6,1.70)
 return s
def basis():
 s=block(-13,13,21,57,-4,0)
 for side in [-1,1]:s=s|railprof(side,9+railspel,13,3.3,21,57)
 # Langgat begrenst de slag met losse pen; onderzijde vlak voor tape.
 return s-slot(2,4.3,43,-5,.1,1.85,slag)
def borgpen():return cyl(2,(0,0),0,2,2.9)|cyl(2,(0,0),1.96,8.8,1.49)
def coupon():
 s=block(-9,9,0,12,0,top)-funnel_local()
 return s-magvak(0)
def funnel_local():
 a=funnel(1);return Solid(lambda p:a.fn((p[0]+px,p[1],p[2])),'translate('+vec([-px,0,0])+')'+a.sc)
def plakmal():
 # Open onderlegger, twee steunbanen en een dwarsverbinding.
 s=block(-20.94,20.94,-36,-33,-1.2,.9)
 for side in [-1,1]:
  for y,Y,half,floor in [(-36,.8,39.483/2+.25,.9),(.77,6.15,19.3+.25,0)]:
   x,X=sorted([side*8,side*(half+1.2)]);s=s|block(x,X,y,Y,-1.2,floor)
   x,X=sorted([side*half,side*(half+1.2)]);s=s|block(x,X,y,Y,-1.2,floor+2.4)
 return s
parts={'plakmal':(plakmal,((-23,23),(-38,8),(-3,5)),.32),'robot':(robot,((-21,21),(-1,23),(-2,16)),.25),'dockkop':(kop,((-43,43),(-39,57),(-2,21)),.34),'railvoet':(basis,((-15,15),(19,59),(-6,5)),.26),'borgpen':(borgpen,((-4,4),(-4,4),(-1,10)),.18),'coupon':(coupon,((-11,11),(-2,14),(-2,21)),.24)}


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
 if name=='robot':t=t[:,:,[0,2,1]];t[:,:,1]*=-1
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



