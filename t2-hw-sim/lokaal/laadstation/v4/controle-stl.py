from pathlib import Path
import numpy as np
from shapely.geometry import Point,MultiLineString
from shapely.ops import polygonize
D=Path(__file__).resolve().parent
def load(name):
 return np.frombuffer((D/name).read_bytes()[84:],dtype=[('n','f4',3),('v','f4',(3,3)),('a','u2')])['v'].astype(float)
def section(t,ax,value):
 q=t[(t[:,:,ax].min(1)<value)&(t[:,:,ax].max(1)>value)]
 hits=[[] for _ in q]
 for i in range(3):
  a=q[:,i];b=q[:,(i+1)%3];mask=(a[:,ax]<value)!=(b[:,ax]<value);ix=np.where(mask)[0]
  k=((value-a[ix,ax])/(b[ix,ax]-a[ix,ax]))[:,None]
  for j,p in zip(ix,np.round(np.delete(a[ix]+k*(b[ix]-a[ix]),ax,axis=1),5)):hits[j].append(p)
 return list(polygonize(MultiLineString([seg for seg in hits if len(seg)==2])))
def at(sec,u,v):return min((p for p in sec if p.covers(Point(u,v))),key=lambda p:p.area)
def gap(t,ax,pos,center):
 p=at(section(t,ax,pos),*center);return np.array(p.bounds),p.area
t=load('dockkop.stl');old=load('../v3/dockkop.stl')
for version,mesh,pt in [('v3',old,(13.7,13)),('v4',t,(14,11.75))]:
 q,area=gap(mesh,1,.51,pt);print(version,'trechter op 0,51 mm:',q,round(area,2))
 if version=='v3':a3=area
 else:assert area>2*a3
q,ar=gap(t,1,13.21,(14,11.75));print('v4 eindgat',q,round(q[2]-q[0],3))
for file,ax,d,center in [('robot.stl',1,4.63,(4.3,4.35)),('dockkop.stl',1,6.21,(4.3,4.35)),('railvoet.stl',2,2.13,(0,40)),('railvoet.stl',2,10.23,(4.3,73)),('draaiplaat.stl',2,6.21,(3,40)),('paspen.stl',2,14.23,(0,0))]:
 b,ar=gap(load(file),ax,d,center);print(file,np.round(b[2:]-b[:2],3))
# Railsneden op de uiterste posities en halverwege; vast materiaal van rail
# en slede ligt op overeenkomende hoogte (rail-STL heeft +12,4 in printstand).
rail=load('railvoet.stl')
for shift in [-30,-15,0]:
 area=0
 for y in [28.31,43.31,59.31,66.31]:
  a=section(t,1,y-shift);b=section(rail,1,y)
  from shapely.affinity import translate
  for pa in a:
   for pb in b:
    area+=pa.intersection(translate(pb,yoff=-12.4)).area
 print('railstand',shift,'overlap mm2',round(area,6));assert area<.02
