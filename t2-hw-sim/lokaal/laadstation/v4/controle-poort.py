from pathlib import Path
import numpy as np
src=next((Path(__file__).resolve().parents[4]/'shared').rglob('Bittle_BatteryCase.stl')).parent
def clip(P,ax,side,limit):
 out=[]
 if not len(P):return []
 a=P[-1]
 for b in P:
  va=side*(a[ax]-limit);vb=side*(b[ax]-limit)
  if (va>0)!=(vb>0):out.append(a+(b-a)*va/(va-vb))
  if vb<=0:out.append(b)
  a=b
 return out
for key in ['Case','Lid','Track']:
 t=np.frombuffer((src/('Bittle_Battery'+key+'.stl')).read_bytes()[84:],dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','u2')])['v'].astype(float);t+=[0,12.2084,39.302845]
 cand=t[(t[:,:,0].min(1)<=4.125)&(t[:,:,0].max(1)>=-4.125)&(t[:,:,2].min(1)<=6)&(t[:,:,2].max(1)>=-.1)]
 ranges=[]
 for tri in cand:
  q=tri
  for ax,side,lim in [(0,1,4.125),(0,-1,-4.125),(2,1,6),(2,-1,-.1)]:q=clip(q,ax,side,lim)
  if len(q):h=np.array(q)[:,1];ranges.append((h.min(),h.max()))
 low=max([b for a,b in ranges if b<8.762],default=None);high=min([a for a,b in ranges if a>8.762],default=None)
 hits=[(a,b) for a,b in ranges if a<=9.962 and b>=7.562]
 print(key,'ondergrens',low,'bovengrens',high,'doorsneden driehoeken',len(hits))
 assert not hits
# Doorsneden over de volle tapezone, inclusief beide randen.
t=np.frombuffer((src/'Bittle_BatteryCase.stl').read_bytes()[84:],dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','u2')])['v'].astype(float)
t+=[0,12.2084,39.302845]
for d0,d1 in [(8,20),(24,28)]:
 # Alle driehoekintersecties met het rechthoekige tapegebied controleren.
 residual=[]
 for tri in t[(t[:,:,0].min(1)<=5.5)&(t[:,:,0].max(1)>=-5.5)&(t[:,:,2].min(1)<=d1)&(t[:,:,2].max(1)>=d0)]:
  # buitenste ondervlak: normale naar -Y; voorkom selectie van interne haakjes.
  norm=np.cross(tri[1]-tri[0],tri[2]-tri[0])
  if norm[1]>=0:continue
  q=tri
  for ax,sign,lim in [(0,1,5.5),(0,-1,-5.5),(2,1,d1),(2,-1,-d0)]:q=clip(q,ax,sign,lim)
  if len(q):
   q=np.array(q);height=np.maximum(0,6.04-.26795*q[:,2]);residual.extend(q[:,1]-height)
 print('Tapezone',d0,d1,'minimale verticale afwijking',min(residual))
 for dep in np.linspace(d0,d1,13):
  for x in np.linspace(-5.5,5.5,13):
   a,b,c=t.transpose(1,0,2);u=b-a;v=c-a
   # Gebruik lokale driehoeken rond het punt.
   mask=(t[:,:,0].min(1)<=x)&(t[:,:,0].max(1)>=x)&(t[:,:,2].min(1)<=dep)&(t[:,:,2].max(1)>=dep)
   A=a[mask];U=u[mask];V=v[mask];det=U[:,0]*V[:,2]-U[:,2]*V[:,0];det[abs(det)<1e-14]=np.nan
   i=((x-A[:,0])*V[:,2]-(dep-A[:,2])*V[:,0])/det;j=(U[:,0]*(dep-A[:,2])-U[:,2]*(x-A[:,0]))/det
   y=(A[:,1]+i*U[:,1]+j*V[:,1])[(i>=0)&(j>=0)&(i+j<=1)].min()
   assert abs(y-max(0,6.04-.26795*dep))<.015
print('338 onderzijde-punten binnen 0,015 mm van het schoenprofiel (zonder tapelaag).')
