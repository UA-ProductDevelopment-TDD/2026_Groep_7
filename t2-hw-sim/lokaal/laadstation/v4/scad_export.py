"""V4 uit de generator: afmetingen wijzigen in ontwerp.py en opnieuw genereren."""
from ontwerp import *
def schrijf():
 toptekst="""// Laadstation v4, mm. Geometrie gegenereerd uit ontwerp.py.
// Wijzig voor nieuwe productiematen de Nederlandse parametersectie in die bron.
part="assemblage"; // robot, paspen (2x), dockkop, railvoet, draaiplaat, borgpen, coupon, plakmal, qrhouder
railstand=0; // 0 tot -30 mm
draaihoek=0; // graden t.o.v. eigen voet
opening=10; // mm tussen robot- en dockcontactvlak
toon_batterij=true;
stlmap="../../../../shared/bronnen/bittle-model/stl/Bittle & BittleX/";
$fn=96;
assert(railstand<=0 && railstand>=-30);assert(opening>=0);
echo("STL-gebaseerde pasproef. Echte poort, tape, vrije beenbaan, draaibereik met kabel en kracht nog meten.");
"""
 mod=''.join('module '+k+'(){'+f().sc+'}\n' for k,(f,_,__) in parts.items())
 asm=f"""
module scene(){{
 translate([0,0,-15.6])draaiplaat();
 translate([0,40,0])rotate([0,0,draaihoek])translate([0,-40,0]){{
 color("lightgrey")basisweergave();
 translate([0,railstand,0]){{
 color("seagreen")dockkop(); color("orange")translate([4.3,90,5.8])rotate([180,0,0])borgpen();
 translate([0,-opening-{plaat},0]){{color("wheat")robot();
 for(s=[-1,1]) color("peru")translate([s*{px},{plaat}-6.1,{pz}])rotate([-90,0,0])paspen();
 if(toon_batterij)translate([0,0,{batbodem}])rotate([90,0,0])translate([0,12.2084,39.302845])for(f=["Case","Lid","Track"])color(f=="Track"?"orange":"lightblue",.32)import(str(stlmap,"Bittle_Battery",f,".stl"));}}
 for(s=[-1,1])for(j=[0,1])for(yy=[.15+4*j,-opening-8.15+4*j])color("silver")translate([s*{mx},yy,{mz}])rotate([-90,0,0])cylinder(h=4,r=3);
 // Gebruikersmaten USB-omhulling, nominale insteekslag 6 mm
 color("gray",.6)translate([-4.125,-15.35,{usb}-1.2])cube([8.25,7,2.4]);color("black",.45)translate([-5,-8.35,{usb}-3])cube([10,18,6]);
 }} }} }}
module basisweergave(){{railvoet();}}
"""
 choices='if(part=="assemblage")scene();'+''.join(f'else if(part=="{k}")translate([0,0,{12.4 if k=="railvoet" else 1 if k=="plakmal" else 0}]){k}();' for k in parts)+'else assert(false,"Onbekend onderdeel");'
 (D/'magneet_dock.scad').write_text(toptekst+mod+asm+choices,encoding='utf8')
if __name__=='__main__':schrijf()
