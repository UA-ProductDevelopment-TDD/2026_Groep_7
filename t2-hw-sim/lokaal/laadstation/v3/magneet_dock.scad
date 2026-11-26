// V3 � mm. X dwars, Y naar kabel, Z omhoog. STL-keuzes geven printori�ntatie.
part="assemblage"; // robot, dockkop, railvoet, borgpen, coupon, assemblage
pen=1.65; spel=.45; penlengte=16; taps=7; mond=6.4; onder=2.9; // proef: stralen, radiale speling, inloop
px=13.7; pz=13.0; mz=4.35; // proef: penposities en magneethoogte vanaf onderkant plaat
magneet_d=6; magneet_l=4; magspel=.25; lijmruimte=.15; // opgegeven schijven; totale spelingen proef
wand=1.2; rubber_b=10; rubber_h=6; rubber_l=18; metaal=7; papier=.6; // kabel opgegeven, vulruimte proef
usb_z=11.4; usb_h=7; tape=.8; insteek=6; reces=0; // poort en slag fysiek toetsen
railspel=.40; slag=6; // per zijde, respectievelijk afstand tussen centra van uiteinden stopsleuf
bat_b=39.483;bat_l=89.782;bat_h=16.5;poort_x=0;poort_y=10.5; // [uit STL, te meten]
rail_y=14.1;vrije_b=43; led=[0,0,0,0]; // rail uit STL; vrije corridor proef; verboden rechthoek x,z,b,h vanaf plaatmidden en onderrand
plaat_b=38.6; hoogte=14.75; arm_l=37; uitloop=19; rib=2.4; // proef
railstand=0; // 0 achterste nominale stand; -slag voorste stand
stlmap="../../../../shared/bronnen/bittle-model/stl/Bittle & BittleX/"; $fn=64;
e=.03;mr=(magneet_d+magspel)/2; gatdiepte=magneet_l+lijmruimte; plaat=gatdiepte+wand;
W=rubber_b+2*papier; top=pz+mond+wand; r=pen+spel;
assert(px-mond-W/2>=wand && pz-onder-mz-mr*sqrt(2)>=wand && mz-mr>=wand);
assert(penlengte-taps-1>insteek+reces && penlengte>plaat+tape+insteek+reces);
assert(poort_y-usb_z+hoogte+.2<rail_y && plaat_b+2*abs(poort_x)<=vrije_b);
assert(led[2]==0 || led[3]==0 || led[0]>=plaat_b/2 || led[0]+led[2]<=-plaat_b/2 || led[1]>=hoogte || led[1]+led[3]<=0);
assert(railspel>0 && slag>0 && railstand<=0 && railstand>=-slag);
echo("Proefmaten. Meet poort, uitneembaan, hoogte, loopruimte, leds/knop, lijm- en kabelpassing. Schuifkracht, magneetkracht en USB-kracht vereisen een proef.");
module B(x,X,y,Y,z,Z){translate([x,y,z])cube([X-x,Y-y,Z-z]);}
module CY(x,z,y,Y,r,R){translate([x,y,z])rotate([-90,0,0])cylinder(h=Y-y,r1=r,r2=R);}
module XZ(y,Y,p){translate([0,Y,0])rotate([90,0,0])linear_extrude(Y-y)polygon(p);}
function prof(w,b,h)=concat([for(i=[0:32])[w*cos(180+i*180/32),b*sin(180+i*180/32)]],[[w*.7071,h-w*.7071],[0,h],[-w*.7071,h-w*.7071]]);
module trechter(x){translate([x,0,pz]){
 hull(){XZ(-.04,-.039,prof(mond,onder,mond+.01));XZ(taps-.001,taps,prof(r,r,r*sqrt(2)));}
 XZ(taps-e,17.4,prof(r,r,r*sqrt(2)));}}
module maggat(x,y){CY(x,mz,y-.05,y+gatdiepte,mr,mr);}
module dockmag(x){maggat(x,0);translate([x,0,mz])XZ(-.05,gatdiepte,[[-mr/sqrt(2),mr/sqrt(2)],[mr/sqrt(2),mr/sqrt(2)],[0,mr*sqrt(2)]]);}
module robotdeel(){difference(){union(){difference(){B(-plaat_b/2,plaat_b/2,0,plaat,0,hoogte);B(-W/2-.2,W/2+.2,-1,plaat+1,6.25,20);}
 for(s=[-1,1]){CY(s*px,pz,plaat-.05,plaat+penlengte-1,pen,pen);CY(s*px,pz,plaat+penlengte-1,plaat+penlengte,pen,pen-.55);}}
 for(s=[-1,1])translate([s*px,0,0])CY(0,mz,wand,plaat+.05,mr,mr);}}
module bandgat(y){multmatrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]])XZ(-9,9,[[y-1.7,2],[y+1.7,2],[y+1.7,3],[y,4.7],[y-1.7,3]]);}
module kop(){difference(){union(){difference(){B(-22,22,0,19,0,top);B(-W/2,W/2,-1,20,usb_z-usb_h/2,25);
 for(s=[-1,1]){trechter(s*px);dockmag(s*px);}}
 for(s=[-1,1])scale([s,1,1])linear_extrude(hoogte)polygon([[px+mond,0],[px+mond+uitloop,-arm_l],[px+mond+uitloop+rib,-arm_l],[px+mond+rib,.08]]);
 XZ(18.92,55,[[-9,0],[9,0],[9,1],[6.2,3.8],[-6.2,3.8],[-9,1]]);B(-3.6,3.6,18.9,33,0,8);}
 for(s=[-1,1])scale([s,1,1])B(5.65,7.05,8.3,11.7,2.1,25);
 for(s=[-1,1])scale([s,1,1])B(3.7,5.1,25.3,28.7,2.1,9); bandgat(10);bandgat(27);translate([4.3,49,-1])cylinder(h=7,r=1.7);}}
module basis(){difference(){union(){B(-13,13,21,57,-4,0);for(s=[-1,1])scale([s,1,1])XZ(21,57,[[9+railspel,0],[13,0],[13,3.3],[6.7+railspel,3.3],[9+railspel,1]]);}
 hull(){for(y=[49-slag,49])translate([4.3,y,-5])cylinder(h=5.1,r=1.85);}}}
module borgpen(){cylinder(h=2,r=2.9);translate([0,0,1.96])cylinder(h=6.84,r=1.49);}
module coupon(){difference(){B(-9,9,0,12,0,top);trechter(0);dockmag(0);}}
module plakmal(){ B(-20.94,20.94,-36,-33,-1.2,usb_z-poort_y);
 for(s=[-1,1])scale([s,1,1])for(i=[0,1]){a=(i?plaat_b:bat_b)/2+.25; y=i?tape-.03:-36;Y=i?tape+plaat:tape;z=i?0:usb_z-poort_y;
 B(8,a+wand,y,Y,-wand,z); B(a,a+wand,y,Y,-wand,z+2.4);}}
module scene(g){color("lightgray")basis();translate([0,railstand,0]){color("lightseagreen")kop();translate([4.3,49,3.8+2])rotate([180,0,0])borgpen();
 translate([0,-plaat-g,0])color("slategray")robotdeel();
 for(s=[-1,1])for(y=[-g-gatdiepte,lijmruimte])color("orange")CY(s*px,mz,y,y+magneet_l,magneet_d/2,magneet_d/2);
 tip=-(plaat+tape+reces+insteek);color("silver")B(-4.125,4.125,tip,tip+metaal,usb_z-1.2,usb_z+1.2);
 color("gray")B(-rubber_b/2,rubber_b/2,tip+metaal,tip+metaal+rubber_l,usb_z-rubber_h/2,usb_z+rubber_h/2);
 translate([-poort_x,-plaat-g-tape,usb_z-poort_y])rotate([90,0,0])scale([bat_b/39.483,bat_h/16.5,bat_l/89.782])translate([0,12.2084,39.302845])
 for(f=["Case","Lid","Track"])color(f=="Track"?"orange":"lightblue",.35)import(str(stlmap,"Bittle_Battery",f,".stl"));}}
if(part=="assemblage")for(i=[0,1])translate([i*95,0,0])scene(i*10);
else if(part=="plakmal")translate([0,0,wand])plakmal();else if(part=="robot")rotate([90,0,0])robotdeel();else if(part=="dockkop")kop();else if(part=="railvoet")translate([0,0,4])basis();else if(part=="borgpen")borgpen();else if(part=="coupon")coupon();else assert(false);



