// Bittle X laadstation | mm | X dwars, Y omhoog, Z naar kabel.
part="assemblage"; // robot, dock, coupon, testpen, plakmal of assemblage
bat_b=39.483; bat_l=89.782; bat_h=16.5; // [uit STL, te meten]
poort_x=0; poort_y=10.5; opening_b=9.5; opening_h=7; // [uit STL, te meten]
reces=0; slag=6; tape=.8; vloer=36; // proef: poortreces, insteekslag, samengedrukte tape en laadhoogte
rail_y=14.1; lijf_b=43; lijf_min=-1; lijf_max=15; // rail uit STL, overige vrije ruimte te meten
led=[0,0,0,0]; // proef: verboden rechthoek [x,y,b,h] vanaf poorthart; nul = onbekend
md=6; mt=4; vakspel=.25; huid=.6; // magneten uit opdracht, totale vakspeling en lipdikte uit pasproef
metaal=7; hb=10; hh=6; hl=18; // opgegeven kabel
papier=.5; kabel_d=4; band=3; // proef: per kant, manteldiameter, binderbreedte
px=14; py=-1.7; pr=4.65; lengte=16; neus=1; // proef: penhart, buitenradius, lengte, afschuining
passing=.45; flare=1.8; inloop=4; eindgap=.45; // proef: radiale speling, mondverbreding, trechterdiepte, axiale vrije ruimte
wand=1.2; plaat=2.4; voet=2.4; rib=2.4; // proef met minimumwand 1,2
aanloop=42; keel=18; zij=15; gier=10; grofspeling=1; // simulatiedoel en proefmaten
coupons=[.3,.45,.6]; mal_l=24; mal_spel=.25; // proef
stlmap="../../../../shared/bronnen/bittle-model/stl/Bittle & BittleX/";
$fn=80; e=.02;
vak=(md+vakspel)/2; W=hb+2*papier; H=hh+2*papier;
breed=px+pr+wand; laag=py-pr-wand; hoog=py+pr; bodem=-max(opening_h,H)/2-.2;
keelW=max(bat_b/2,breed)+grofspeling; mondW=keelW+zij+(lengte+plaat)*sin(gier);
r=pr+passing; top=py+(r+flare)*sqrt(2)+wand; front=lengte+eindgap;
achter=front+huid+mt+vakspel+wand; tip=plaat+tape+reces+slag; sch=metaal-tip;
step=2*(pr+max(coupons)+flare)+2*wand;
assert(pr-vak>=wand && pr-.45-vak+huid>=wand && huid>0);
assert(px-r-flare-W/2>=wand && px-r-W/2-wand>=wand);
assert(lengte>tip && lengte-inloop-neus-px*sin(gier)>slag+reces);
assert(poort_y+hoog+.2<=min(rail_y,lijf_max) && poort_y+laag>=lijf_min && abs(poort_x)+breed<=lijf_b/2);
assert(led[2]==0 || led[3]==0 || led[0]>=breed || led[0]+led[2]<=-breed || led[1]>=hoog || led[1]+led[3]<=laag);
assert(inloop>=flare && plaat>=wand && slag<=metaal && eindgap>0 && sch+hl>band);
echo("TE METEN: lijf, track, uitneembaan, vlakke tapezones, poort, kabel, loophoogte, led/knop, printpassing, magneetkracht. Proefwaarden zijn ongevalideerd.");
module B(x,X,y,Y,z,Z){translate([x,y,z]) cube([X-x,Y-y,Z-z]);}
module dak(r){hull(){circle(r);polygon([[-r/sqrt(2),r/sqrt(2)],[0,r*sqrt(2)],[r/sqrt(2),r/sqrt(2)]]);}}
module koker(r,R,z,Z){translate([0,0,z]) linear_extrude(height=Z-z,scale=R/r) dak(r);}
module pin(){cylinder(h=lengte-neus,r=pr);translate([0,0,lengte-neus]) cylinder(h=neus,r1=pr,r2=pr-.45);}
module laadgat(){translate([0,0,-e]) cylinder(h=plaat+lengte-huid+e,r=vak);
 translate([0,0,plaat+lengte-huid-e]) cylinder(h=huid+2*e,r1=vak,r2=vak-huid);}
module robot(){difference(){union(){difference(){B(-breed,breed,laag,hoog,0,plaat);B(-max(W+.4,opening_b)/2,max(W+.4,opening_b)/2,bodem,hoog+e,-e,plaat+e);}
 for(s=[-1,1]) translate([s*px,py,plaat-e]) pin();}
 for(s=[-1,1]) translate([s*px,py,0]) laadgat();}}
module boorgang(sp){a=pr+sp;koker(a+flare,a,-e,inloop);koker(a,a,inloop-e,front);
 koker(vak-huid,vak,front-e,front+huid);koker(vak,vak,front+huid-e,achter+e);}
module goot(z,Z){difference(){B(-W/2-wand,W/2+wand,-H/2-wand,H/2,z,Z);B(-W/2,W/2,-H/2,H,z-e,Z+e);}}
module dock(){difference(){union(){
 for(s=[-1,1]) scale([s,1,1]){
 B(W/2,keelW+rib,-vloer,top,0,achter);
 B(keelW,keelW+rib,-vloer,hoog,-keel,.1);
 hull(){B(keelW,keelW+rib,-vloer,hoog,-keel,-keel+e);B(mondW,mondW+rib,-vloer,hoog,-aanloop,-aanloop+rib);}
 }
 B(-keelW-rib,keelW+rib,-vloer,-vloer+voet,0,achter+10);
 B(-W/2-wand,W/2+wand,-vloer,-H/2,0,sch+hl);
 goot(0,sch+hl);
 B(-kabel_d/2-wand,kabel_d/2+wand,-vloer,-kabel_d/2,sch+hl-e,achter+10);
 }
 for(s=[-1,1]) translate([s*px,py,0]) boorgang(passing);
 for(c=[(sch+hl)/2,achter+6]){
 for(s=[-1,1]) scale([s,1,1]) B(W/2,W/2+wand,-9,top+e,c-band/2,c+band/2);
 translate([0,-9,c]) rotate([0,90,0]) linear_extrude(height=W+2*wand,center=true) polygon([[-band/2,-wand],[band/2,-wand],[band/2,0],[0,band/2],[-band/2,0]]);
 }
 translate([0,-vloer,-29]) rotate([0,90,0]) linear_extrude(height=2*(mondW+rib+1),center=true) polygon([[-10,-e],[10,-e],[0,10]]);
}}
module coupon(){difference(){B(-step/2,(len(coupons)-.5)*step,-10.5,py+(pr+max(coupons)+flare)*sqrt(2)+wand,0,achter);
 for(i=[0:len(coupons)-1]) translate([i*step,py,0]) boorgang(coupons[i]);}
 translate([-step/2-W/2-wand+e,-10.5+H/2+wand,0]) goot(0,8);}
module testpen(){difference(){union(){cylinder(h=plaat,r=pr+wand);translate([0,0,plaat-e]) pin();}laadgat();}}
module plakmal(){for(i=[0,1]){h=(i==0?bat_b/2:breed)+mal_spel; xc=i==0?0:poort_x; y=i==0?-poort_y:laag;
 z=i==0?-mal_l:0; Z=i==0?e:plaat;
 B(xc-h-wand,xc+h+wand,-poort_y-wand,y,z,Z);
 for(s=[-1,1]) translate([xc,0,0]) scale([s,1,1]) B(h,h+wand,y-e,y+2*wand,z,Z);}}
module scene(g){dock();translate([0,0,-plaat-g])robot();
 color("silver",.5)B(-4.125,4.125,-1.2,1.2,-tip,sch);color("gray",.5)B(-hb/2,hb/2,-hh/2,hh/2,sch,sch+hl);
 for(s=[-1,1]) for(z=[lengte-g-huid-mt,front+huid]) color("red",.7) translate([s*px,py,z]) cylinder(h=mt,r=md/2);
 translate([-poort_x,-poort_y,-plaat-g-tape])scale([bat_b/39.483,bat_h/16.5,-bat_l/89.782])translate([0,12.2084,39.302845])
 for(f=["Case","Lid","Track"])color(f=="Track"?"orange":"lightblue",.3)import(str(stlmap,"Bittle_Battery",f,".stl"));}
if(part=="robot")robot();else if(part=="testpen")testpen();else if(part=="dock")translate([0,0,vloer])rotate([90,0,0])dock();
else if(part=="coupon")translate([0,0,10.5])rotate([90,0,0])coupon();else if(part=="plakmal")translate([0,0,poort_y+wand])rotate([90,0,0])plakmal();
else if(part=="assemblage")for(i=[0,1])translate([i*(2*mondW+20),0,0])scene(i*10);else assert(false);

