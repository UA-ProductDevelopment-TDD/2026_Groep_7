from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent
def reader(name):
 dt=[('normal','<f4',3),('triangle','<f4',(3,3)),('attr','<u2')]
 return np.frombuffer((D/(name+'.stl')).read_bytes()[84:],dtype=dt)['triangle'].astype(float)
def ray(t,y,z):
 # Snede langs X. Selecteer alleen driehoeken die het meetpunt omvatten.
 a,b,c=t.transpose(1,0,2);u=b-a;v=c-a;den=u[:,1]*v[:,2]-u[:,2]*v[:,1]
 den[abs(den)<1e-12]=np.nan;Y=y-a[:,1];Z=z-a[:,2]
 i=(Y*v[:,2]-Z*v[:,1])/den;j=(u[:,1]*Z-u[:,2]*Y)/den;m=(i>=0)&(j>=0)&(i+j<=1)
 return np.unique(np.round((a[:,0]+i*u[:,0]+j*v[:,0])[m],6))
def small(t):
 lo=t.min(1);hi=t.max(1)
 def query(y,z):return ray(t[(lo[:,1]<=y)&(hi[:,1]>=y)&(lo[:,2]<=z)&(hi[:,2]>=z)],y,z)
 return query
head=small(reader('dockkop'));rail=small(reader('railvoet'));rob=small(reader('robot'))
for y in (.45,3.5,7.5):
 a=head(y,13.0); section=a[(a>6)&(a<21)]; print('pengat',y,section,round(section[-1]-section[0],3));assert len(section)==2 and abs(section.ptp() if hasattr(section,'ptp') else np.ptp(section))>4.1
for name,row in [('magneet dock',head(2,4.35)),('magneet robot',rob(-4.35,3.5)),('pen robot',rob(-13.0,12)),('kabelgoot',head(4.5,11.4)),('mond',head(-36,13.0))]:print(name,np.round(row,3))
for d in [-6,-3,0]:
 vals=[]
 for y in [23.2,27.2,34.4,42.2,48.8]:
  for z in [.21,.83,1.37,2.18,2.99,3.12]:
   h=head(y-d,z);b=rail(y,z+4)
   if not len(h):continue
   gap=b[b>0].min()-h.max()
   assert gap>.3,(y,z,gap);vals.append(gap)
 print('railstand',d,'kleinste gemeten zijspeling',round(min(vals),3))
def width_near(values,c,r):
 a=values[(values>c-r)&(values<c+r)];assert len(a)==2,(values,c,r);return float(a[1]-a[0])
for center in (-13.7,13.7):
 shaft=width_near(rob(-13,12),center,2.5)
 bore=width_near(head(7.5,13),center,2.5)
 assert .38<(bore-shaft)/2<.52
 for values in [head(2,4.35),rob(-4.35,3.5)]:assert 6.15<width_near(values,center,3.6)<6.30
print('Beide penassen, eindpassingen en alle vier magneetzittingen akkoord.')
# Past de onderste brede sledestrook onder de lippen?
tail=head(35,.65);lip=rail(35,4+3.13)
assert tail.max()-lip[lip>0].min()>1.3
print('Geometrische borging tegen optillen:',round(tail.max()-lip[lip>0].min(),2),'mm overlap per zijde')
vertical=small(reader('dockkop')[:,:,[2,1,0]])
for y in [.45,3.5,7.5]:
 z=vertical(y,13.7);print('Verticale snede op diepte',y,np.round(z,2))

