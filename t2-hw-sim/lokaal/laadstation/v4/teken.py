import xml.etree.ElementTree as E, numpy as np
from pathlib import Path
from ontwerp import profiel
R=E.Element('svg',xmlns='http://www.w3.org/2000/svg',viewBox='0 0 1280 1100',width='1280',height='1100')
E.SubElement(R,'title').text='Laadstation v4 — maten, langsrail, draaipunt en plakpositie'
def el(tag,**kw):return E.SubElement(R,tag,{k.replace('_','-'):str(v) for k,v in kw.items()})
def rect(x,y,w,h,c,rr=0):el('rect',x=x,y=y,width=w,height=h,rx=rr,fill=c)
def txt(x,y,v,size=17,b=False):el('text',x=x,y=y,fill='#173d48',font_family='Arial, sans-serif',font_size=size,font_weight=700 if b else 400).text=v
def line(x,y,X,Y,c='#224955',w=1.7):el('line',x1=x,y1=y,x2=X,y2=Y,stroke=c,stroke_width=w)
def path(ps,c,stroke='#24515b',w=1.2):el('polygon',points=' '.join(f'{x:.2f},{y:.2f}' for x,y in ps),fill=c,stroke=stroke,stroke_width=w)
def dim(x,X,y,label):
 line(x,y,X,y);line(x,y-5,x,y+5);line(X,y-5,X,y+5);txt((x+X)/2-len(label)*3.8,y-9,label,15)
A='#7cc2b3';B='#bfd1dc';C='#eeb66b';dark='#204852'
rect(0,0,1280,1100,'#f1f5f4');txt(36,57,'Laadstation v4',42,True);txt(36,90,'Montagematen in mm   /   batterijreferentie met deksel   /   nominale CAD-maten tenzij anders vermeld',20)
rect(24,112,586,431,'white',12);txt(44,151,'01   Dockkop van voren',24,True)
f=lambda x,z:(310+x*7,415-z*7)
# Straight contact face. Upper central slot is open.
path([f(x,z) for x,z in [(-34.15,0),(34.15,0),(34.15,27.65), (5.6,27.65),(5.6,10),(-5.6,10),(-5.6,27.65),(-34.15,27.65)]],A)
for sign in [-1,1]:
 path([f(x+sign*19.85,z+11.75) for x,z in profiel(12.9,7.2,12.91)],'white')
 path([f(x+sign*14,z+11.75) for x,z in profiel(2.85,2.85,2.85*2**.5)],'#dbe7e8')
 x,y=f(sign*4.3,4.35);el('circle',cx=x,cy=y,r=3.125*7,fill=C,stroke=dark)
dim(f(-34.15,0)[0],f(34.15,0)[0],456,'68,30 kopvlak')
dim(f(6.95,0)[0],f(32.75,0)[0],208,'25,80 mond')
txt(48,494,'Pen Ø4,80  ·  hartafstand 28,00  ·  eindboring 5,70 breed',17)
txt(48,520,'Oranje: vier kamers over beide delen, Ø6,25 × 8,15 diep.',16)
rect(624,112,632,431,'white',12);txt(646,151,'02   Langsrail en draaiing',24,True)
# Top view along horizontal
xx=lambda y:695+(y-22)*6.3
cy=330
el('circle',cx=xx(40),cy=cy,r=18*6.3,fill='#e6ecee',stroke='#9dabb2')
rect(xx(27),cy-13*6.3,72*6.3,26*6.3,B,3)
for s in [-1,1]:rect(xx(27),cy+(9.3 if s==1 else -13)*6.3,72*6.3,3.7*6.3,'#728e9b')
el('circle',cx=xx(40),cy=cy,r=6.35*6.3,fill='#f5f7f6',stroke=dark)
el('circle',cx=xx(40),cy=cy,r=6*6.3,fill=C,stroke=dark)
rect(xx(60)-1.85*6.3,cy+4.3*6.3-1.85*6.3,33.7*6.3,3.7*6.3,'white',11)
el('circle',cx=xx(90),cy=cy+4.3*6.3,r=1.49*6.3,fill=dark)
dim(xx(27),xx(99),203,'72,00 raillengte');dim(xx(60),xx(90),450,'30,00 slag')
txt(646,493,'Spil Ø12,00 in Ø12,70  ·  sleuf 33,70 × 3,70',17)
txt(646,520,'Vaste schijf Ø36 onder de rail; de hele rail draait mee.',16)
rect(24,558,1232,440,'white',12);txt(44,597,'03   Tapeschoen onder de geassembleerde batterij',24,True)
# Use intersections of original STL triangles with central section x = 0.31.
root=next((Path(__file__).resolve().parents[4]/'shared').rglob('Bittle_BatteryCase.stl')).parent
fx=lambda d:560-5.2*d
fy=lambda h:849-5.2*h
for key,col in [('Case','#476977'),('Lid','#7799a6')]:
 t=np.frombuffer((root/('Bittle_Battery'+key+'.stl')).read_bytes()[84:],dtype=[('n','f4',3),('v','f4',(3,3)),('u','u2')])['v'].astype(float);q=t[(t[:,:,0].min(1)<.31)&(t[:,:,0].max(1)>.31)]
 for tri in q:
  hits=[]
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   if (a[0]<.31)!=(b[0]<.31):
    pt=a+(b-a)*(.31-a[0])/(b[0]-a[0]);hits.append((fx(pt[2]+39.302845),fy(pt[1]+12.2084)))
  if len(hits)==2:line(*hits[0],*hits[1],col,1.8)
path([(fx(d),fy(h)) for d,h in [(28,-4.738),(-9.35,-4.738),(-9.35,4.96),(0,4.96),(0,5.21),(22.55,-.8),(28,-.8)]],C)
for d0,d1 in [(8,20),(24,28)]:
 def ht(d):return max(0,6.04-.26795*d)
 path([(fx(d),fy(ht(d)-k)) for d,k in [(d0,0),(d1,0),(d1,.8),(d0,.8)]],dark)
line(fx(-10),fy(8.762),fx(6),fy(8.762),'#c76438',2.7)
dim(fx(89.782),fx(0),717,'89,78 kast');dim(fx(28),fx(0),924,'28,00 schoen')
txt(61,958,'Doorsnede uit de kast- en deksel-STL bij X = 0,31 mm.',16)
txt(673,660,'Plakken ten opzichte van de poortzijde',20,True)
for i,s in enumerate(['1. Leg de gesloten batterij in de mal, met het','    poorteinde tegen het robotdeel. De achterste','    aanslag bepaalt de positie in lengterichting.','2. Plak centraal op de twee contactstroken:','    8–20 mm achter het kopvlak op de helling,','    24–28 mm achter het kopvlak op het vlak.','3. Pas een spanningsloze stekker vóór aandrukken.','    As uit de vrije STL-opening: 8,76 mm boven','    de vlakke kastbodem; werkelijke laadbus nameten.']):
 txt(672,697+i*27,s,17)
txt(42,1044,'Passing is digitaal gecontroleerd. Het echte poorthart, beenbereik, de kabelbocht en de krachten vragen een fysieke proef.',18)
# Front outline high point matches nominal H=25.90, not 26 significant at this scale.
E.ElementTree(R).write('maattekening.svg',encoding='utf-8',xml_declaration=True);E.parse('maattekening.svg')

