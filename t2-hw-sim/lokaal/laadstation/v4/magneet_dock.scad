// Laadstation v4. Eenheden mm. X links/rechts, +Y vanaf robot naar kabel, Z omhoog.
part="assemblage"; // robot, paspen (2x), dockkop, railvoet, draaiplaat, borgpen, coupon, plakmal, qrhouder, qrkaartje
railstand=0; draaihoek=0; opening=10; toon_batterij=true; // illustratieve standen
batbreed=39.483;batlengte=89.782;bathoogte=16.5;poorthoogte=8.762; // [uit STL, te meten] hoogte centraal in vrije kast+dekselopening
vrije_rail=14.10;vrije_breedte=40; // laagste track uit STL; beschikbare beenruimte proef
led=[0,0,0,0]; // verboden vlak op onderzijde [xmin,diepte,b,l]; nul = onbekend
tape=.8;helling=15;schuin_begin=6.04;schoenlengte=28;schoen_b=11; // tape proef; helling en ondersnede [uit STL, te meten]
pen=2.4;sp=.45;lengte=22;px=14;pz=11.75; // proefmaten, pinhart tov kopmidden en printbed
taps=11;mond=12.9;mond_x=19.85;onder=7.2; // halve breedte en onderhoogte van asymmetrische ingang
wand=1.2;md=6;ml=4;stapel=2;magspel=.25;lijm=.15;mx=4.3;mz=4.35; // opgegeven schijven; pasvorm, positie en lijm proef
usb=13.5;huis=11.2;usbslag=6; // proefhoogte en doorgang voor opgegeven huis 10x6x18 en neus 7
rail_l=72;rail_y=27;railbodem=12.4;railspel=.4;reis=30;pin_y=90; // proef, lengte en slag
pivot_y=40;pivot_r=6;pivot_sp=.35; // draaipen achter de kop
stlmap="../../../../shared/bronnen/bittle-model/stl/Bittle & BittleX/";$fn=96;
mag=(md+magspel)/2;magdiepte=ml*stapel+lijm;plaat=magdiepte+wand;batbodem=usb-poorthoogte;H=usb+mond+1.25;
assert(lengte>plaat+usbslag && lengte-taps-1-px*sin(10)>usbslag);
assert(mond_x-mond-huis/2>=wand && 2*mx-2*mag>=wand && usb-3.5-mz-mag*sqrt(2)>=wand);
assert(16.8-pz-2.62*sqrt(2)>=wand && 16.8-batbodem+.2<vrije_rail && 37.6<=vrije_breedte);
assert(railstand<=0 && railstand>=-reis && opening>=0 && pin_y-reis>pivot_y+8.3+1.85+wand);
assert(led[2]==0 || led[3]==0 || led[0]>schoen_b/2 || led[0]+led[2]<-schoen_b/2 || led[1]>schoenlengte || led[1]+led[3]<0);
echo("Proefmaten: echte laadbus, kastvorm, tape, knop/led, beenbaan, grondspeling, kracht en kabelvrijloop meten.");
module B(x,X,y,Y,z,Z){translate([x,y,z])cube([X-x,Y-y,Z-z]);}
module CY(x,z,y,Y,r,R){translate([x,y,z])rotate([-90,0,0])cylinder(h=Y-y,r1=r,r2=R);}
module CZ(x,y,z,Z,r,R){translate([x,y,z])cylinder(h=Z-z,r1=r,r2=R);}
module XZ(y,Y,p){translate([0,Y,0])rotate([90,0,0])linear_extrude(Y-y)polygon(p);}
module YZ(x,X,p){multmatrix([[0,1,0,0],[1,0,0,0],[0,0,1,0],[0,0,0,1]])XZ(x,X,p);}
module rondgat(x,z,y,Y,r){CY(x,z,y,Y,r,r);translate([x,0,z])XZ(y,Y,[[-r/sqrt(2),r/sqrt(2)],[r/sqrt(2),r/sqrt(2)],[0,r*sqrt(2)]]);}
function prof(r,b,h)=concat([for(i=[0:32])[r*cos(180+i*180/32),b*sin(180+i*180/32)]],[[r*.7071,h-r*.7071],[0,h],[-r*.7071,h-r*.7071]]);
module trechter(s){r=pen+sp;hull(){translate([s*mond_x,0,pz])XZ(-.05,-.049,prof(mond,onder,mond+.01));translate([s*px,0,pz])XZ(taps-.001,taps,prof(r,r,r*sqrt(2)));}
 translate([s*px,0,pz])XZ(taps-.03,lengte+1.5,prof(r,r,r*sqrt(2)));}
module robot(){difference(){B(-18.8,18.8,0,plaat,0,16.8);B(-5.95,5.95,-1,plaat+1,usb-3.8,19);
 for(s=[-1,1]){rondgat(s*mx,mz,wand,plaat+.1,mag);rondgat(s*px,pz,plaat-6.45,plaat+.1,2.62);CY(s*px,pz,plaat-1.2,plaat+.02,2.62,3.43);}}
 f=batbodem-tape;v=batbodem+schuin_begin-tape/cos(helling);overgang=schuin_begin/tan(helling);
 B(-schoen_b/2,schoen_b/2,-schoenlengte,.15,0,f);YZ(-schoen_b/2,schoen_b/2,[[-overgang,0],[.15,0],[.15,v+.04],[-overgang,f-.01]]);}
module paspen(){CZ(0,0,0,5.12,2.38,2.38);CZ(0,0,5.08,6.1,2.38,3.2);CZ(0,0,6.07,8.55,3.2,pen);CZ(0,0,8.5,6.1+lengte-1,pen,pen);CZ(0,0,6.1+lengte-1.02,6.1+lengte,pen,1.65);}
module bandgat(y){YZ(-9,9,[[y-1.7,2],[y+1.7,2],[y+1.7,3],[y,4.7],[y-1.7,3]]);}
module dockkop(){h=pz+(pen+sp)*sqrt(2)+1.5;
 difference(){union(){difference(){union(){hull(){B(-34.15,34.15,0,.001,0,H);B(-20.5,20.5,taps-.001,taps,0,h);}B(-20.5,20.5,taps-.03,25,0,h);}
 B(-huis/2,huis/2,-1,26,usb-3.5,H+1);for(s=[-1,1]){trechter(s);rondgat(s*mx,mz,-.05,magdiepte,mag);}}
 XZ(24.9,rail_y+rail_l-1,[[-9,0],[9,0],[9,1],[6.2,3.8],[-6.2,3.8],[-9,1]]);B(-3.6,3.6,24.8,43,0,usb-2.8);}
 for(s=[-1,1])scale([s,1,1]){B(5.65,7.05,9.55,12.95,2.1,H+1);B(5.65,7.05,5.8,12.95,10,H+1);B(3.7,5.1,32.3,35.7,2.1,13);}
 bandgat(11.25);bandgat(34);CZ(4.3,pin_y,-1,6,1.7,1.7);}}
module railvoet(){e=rail_y+rail_l;difference(){union(){B(-13,13,rail_y,e,-railbodem,0);for(s=[-1,1])scale([s,1,1])XZ(rail_y,e,[[9+railspel,0],[13,0],[13,3.3],[6.7+railspel,3.3],[9+railspel,1]]);}
 hull(){for(y=[pin_y-reis,pin_y])CZ(4.3,y,-3.9,.3,1.85,1.85);}
 CZ(0,pivot_y,-railbodem-.6,.2,pivot_r+pivot_sp,pivot_r+pivot_sp);CZ(0,pivot_y,-4.5,.2,8.3,8.3);}}
module draaiplaat(){difference(){union(){CZ(0,pivot_y,0,3.2,18,18);CZ(0,pivot_y,3.17,3.2+railbodem-4.1,pivot_r,pivot_r);}CZ(0,pivot_y,1.4,3.2+railbodem,1.3,1.3);}}
module borgpen(){CZ(0,0,0,2,2.9,2.9);CZ(0,0,1.96,8.8,1.49,1.49);}
module plakmal(){e=-batlengte-.12;B(-21.3,21.3,-52,-48,-1,batbodem);B(-18,18,e-1.6,e,-1,batbodem+14.1);B(-20.5,20.5,plaat+.12,plaat+1.72,-1,2.2);
 for(s=[-1,1])scale([s,1,1]){B(9,21.3,-52,plaat,-1,0);B(batbreed/2+.25,21.3,-52,-24,-1,batbodem+14.1);B(19.05,20.5,0,plaat+.3,-1,4);B(9,12,e-.1,-51.9,-1,.8);}}
module coupon(){difference(){B(0,34.15,0,13,0,H);trechter(1);rondgat(mx,mz,-.1,magdiepte,mag);}}
module qrhouder(){difference(){union(){B(-19,19,-5,7,0,2);B(-18,18,0,4.8,1.9,34);}B(-16.1,16.1,1.5,3.25,3.2,35);B(-14.8,14.8,-.1,2,4.5,35);}}
module qrkaartje(){B(-15.8,15.8,0,32,0,1.2);}
module scene(){
 translate([0,0,-railbodem-3.2])draaiplaat();
 translate([0,pivot_y,0])rotate([0,0,draaihoek])translate([0,-pivot_y,0]){
 color("lightgrey")railvoet();
 translate([0,railstand,0]){
 color("seagreen")dockkop(); color("orange")translate([4.3,pin_y,5.8])rotate([180,0,0])borgpen();
 translate([0,-opening-plaat,0]){color("wheat")robot();
 for(s=[-1,1]) color("peru")translate([s*px,plaat-6.1,pz])rotate([-90,0,0])paspen();
 if(toon_batterij)translate([0,0,batbodem])rotate([90,0,0])translate([0,12.2084,39.302845])for(f=["Case","Lid","Track"])color(f=="Track"?"orange":"lightblue",.32)import(str(stlmap,"Bittle_Battery",f,".stl"));}
 for(s=[-1,1])for(j=[0,1])for(yy=[.15+4*j,-opening-magdiepte+4*j])color("silver")translate([s*mx,yy,mz])rotate([-90,0,0])cylinder(h=4,r=3);
 // Gebruikersmaten USB-omhulling, nominale insteekslag 6 mm
 color("gray",.6)translate([-4.125,-plaat-usbslag,usb-1.2])cube([8.25,7,2.4]);color("black",.45)translate([-5,-plaat-usbslag+7,usb-3])cube([10,18,6]);
 } } }

if(part=="assemblage")scene();else if(part=="robot")robot();else if(part=="dockkop")dockkop();else if(part=="railvoet")translate([0,0,railbodem])railvoet();else if(part=="draaiplaat")draaiplaat();else if(part=="paspen")paspen();else if(part=="borgpen")borgpen();else if(part=="plakmal")translate([0,0,1])plakmal();else if(part=="coupon")coupon();else if(part=="qrhouder")qrhouder();else if(part=="qrkaartje")qrkaartje();else assert(false);

