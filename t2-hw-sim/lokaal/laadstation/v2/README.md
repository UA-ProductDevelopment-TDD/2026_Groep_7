# Laadstation · magneten in de penassen

T3 UX/UI en T2 hardware · ontwerp en numerieke mesh-export met Codex. Alle vijf STL’s staan in mm in printstand. Gebruik de onderdelen uit dezelfde export. In het bewerkbare OpenSCAD-bestand toont `part="assemblage"` de gesloten stand en een stand op 10 mm afstand, met de vier magneten, batterij, houder en spookstekker.

## Onderdelen en passing

Vier schijfmagneten Ø6 × 4 mm. Elke holle pen bevat één magneet tegen de binnenrand van zijn punt. De tweede schijf zit daar recht tegenover, achter de bodem van het trechtergat. De vlakke robotplaat draagt de pennen en de tape. In de gesloten stand raakt de plaat het dock en houdt die aanslag de penpunten 0,45 mm vrij van de gatbodem. Er is geen tweede klikverbinding.

| Maat | Waarde en functie |
|---|---|
| Pennen | Ø9,30 mm, hartafstand 28 mm. De doorlopende laadboring van Ø6,25 mm laat bij de schacht 1,53 mm kunststof rondom over. De achterkant blijft bereikbaar tot het robotdeel op de batterij zit. |
| Trechtergaten | Nominale horizontale mondbreedte 13,8 mm, taps over 4 mm tot 10,2 mm. Daarachter 0,45 mm radiale speling per pen. De 45°-dakpunt maakt het bovendeel van het gat hoger dan de horizontale breedte. |
| Inloop | Afstand tot de aanslag: bij 42 mm bereiken de zijkanten de brede ingang, bij 18 mm begint de parallelle keel, bij 16 mm komen de pentoppen in de gaten, bij circa 11 mm loopt de volle pendiameter in de eindpassing. Bij aangenomen reces 0 raakt de metalen stekker de poortmond bij 6 mm. Contact met de zijgeleiders hangt af van de startpositie. |
| Grofgeleiding | Ingang circa 78,1 mm vrij; berekend op zijdelingse fout ±15 mm en gier ±10°. De dynamische vangst en contact met lopende poten vereisen een proef. |
| Magneetafstand | Nominaal 0,45 mm eindspeling plus twee axiale lippen van 0,60 mm. De werkelijke afstand hangt ook af van waar de schijven op de schuine lippen zitten. Verander `huid` of `eindgap` en regenereer beide delen om de aantrekking te regelen. |
| Kabel | Metalen neus 7 mm, kunststof huis opgegeven als 10 × 6 × 18 mm. Open goot 11 × 7 mm met papieren vulstroken en twee binders voor fixatie en trekontlasting. |
| Gewicht | Berekend uit de geëxporteerde volumes bij 1,27 g/cm³ massief PETG: robotdeel 2,35 g, dock 63,53 g. Exclusief vier magneten, tape en kabel. De slicer geeft het gewicht bij gekozen vulling. |

## Controle

De drie batterij-STL’s geven 39,48 × 89,78 × 14,10 mm voor de kast en 16,50 mm totaal met deksel. Op het dunne uiteinde ligt centraal een opening van circa 9,5 × 7 mm. Op STL-Y = −4 mm ligt het oppervlak bij X = 12 mm slechts 0,14 mm terug en bij X = 16 mm al 3,65 mm. Gebruik vooral de binnenste vlakke draagstroken en controleer hun contactafdruk. Met de gekozen poorthoogte ligt het robotdeel 0,65 mm onder de laagste Y van de houder. Dit betreft de vaste STL-positie. De uitneembaan, poten, echte batterij en positie van leds/knop moeten worden gemeten. De vrije lijfbreedte en laadhoogte zijn proefwaarden.

De meshes zijn rechtstreeks met NumPy gegenereerd en na export gecontroleerd op een gesloten oppervlak met consistent gerichte randen. Dwarsdoorsneden door het dock op 0,45 / 2 / 5 mm achter de mond meten respectievelijk 13,40 / 12,00 / 10,20 mm breed. Zowel de penboring als de magneetkamer achter het gat meten bij hun midden circa 6,24 mm breed. De vernauwingen aan de penpunt en de bodem zijn kleiner dan de schijfdiameter. De kleinste nominale dam tussen de trechtermond en de kabelgoot is 1,60 mm. Numerieke mesh-export rondt scherpe overgangen lokaal af. OpenSCAD-render, slicercontrole en fysieke proeven staan open.

## Printen en monteren

1. Print eerst **coupon.stl** en **testpen.stl** met PETG, nozzle 0,4 mm, laag 0,2 mm en drie omtrekken. Gebruik de geleverde oriëntatie, bekijk de laagpreview met support uit. Houd de trechteropeningen voor je en de kabelgoot links: de gaten hebben van links naar rechts 0,30 / 0,45 / 0,60 mm nominale radiale speling. Het middelste komt overeen met het dock. Probeer ook het invoeren van een schijf in de losse pen en achter in de coupon.
2. Print **robot.stl** met de tapezijde op het bed en de pennen recht omhoog. Print **dock.stl** op zijn voet, **plakmal.stl** plat. Verwijder bramen en meet de doorgangen. Houd aansluitvlak, kabelgoot en magneetzittingen vrij van strings.
3. Werk met de batterij uitgenomen. **Monteer de twee penmagneten vóór het tapen.** Schuif elke schijf vanaf de vlakke achterzijde van de robotplaat door de holle pen tot aan de vernauwing. Gebruik een stomp niet-magnetisch staafje. Zet de schijf met een kleine hoeveelheid geschikte lijm aan de omtrek vast en laat uitharden. Links en rechts moeten tegengestelde polen naar voren wijzen. Gebruik geen warmte.
4. Laat de twee dockmagneten elk tegen hun eigen pentip klikken en markeer op elke schijf het vlak dat naar de pen wijst. Neem ze af en schuif ze vanaf de **kabelzijde** in de achterste ronde openingen van het dock, met de gemarkeerde kant naar de trechter. Druk ze tegen hun zitting, pas eerst droog en borg ze met lijm. Het testpenmagneetje kan voor de droogproef een van de vier losse magneten zijn.
5. Controleer eerst de volledige koppeling op tafel, zonder kabel. Plaats korte stukken VHB op de vlakke draagstroken aan beide kanten van de poort. Gebruik de plakmal en controleer poortcentrum, vrije leds en knop, spoor en poten voordat je de tape aandrukt. Meet de werkelijke laadhoogte op de vloer.
6. Stel de losse kabel voor de eerste pasproef spanningsloos af. Vul onder en naast het huis op met papier en stel de diepte in zodat de vlakke aanslagen contact maken bij volledige insteek. Borg huis en mantel elk met een kabelbinder. Test met de hand op recht in- en uitnemen. Meet daarna benodigde kracht, houdkracht en weerstand tegen verschuiven van de voet. Automatisch laden en loslopen zijn nog niet aangetoond. De open kabelgoot blijft bereikbaar voor vervolgwerk met een verende houder.
