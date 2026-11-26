# Laadstation v3 · dunne kop op één langsrail

De vaste railvoet wordt op jullie eigen voet bevestigd. De dockkop schuift naar en van de robot. Eén losse borgpen loopt mee in een langgat en begrenst de beweging. Schuif de kop voor de eerste proef naar achteren. De armen vangen een zijdelingse fout op, de twee trechtergaten corrigeren de resterende afwijking en de magneten kunnen de vrij schuivende kop het laatste stuk aantrekken. Een terugstelveer is niet voorzien.

## Printbestanden

| Bestand | Functie | Oriëntatie bij import op 100% |
|---|---|---|
| robot.stl | Tapeplaat met twee pennen en twee ronde magneetkamers | Tapezijde op het bed; pennen omhoog |
| dockkop.stl | Geleidearmen, trechters, twee magneetkamers, USB-goot en slede in één print | Vlakke onderzijde op het bed |
| railvoet.stl | Korte rail om op eigen voet te bevestigen | Vlakke onderzijde op het bed |
| borgpen.stl | Uitneembare slagbegrenzing | Brede kop op het bed; omkeren bij montage |
| coupon.stl | Eén doorsnede van de functionele voorkant met hetzelfde pengat en magneetvak | Zelfde ligging als dockkop |
| plakmal.stl | Los hulpmiddel voor de positie van de tapeplaat | Open zijde boven |

Start met de coupon en de robotplaat, in PETG, laag 0,2 mm, nozzle 0,4 mm, drie omtrekken. Als uitgangspunt 20% vulling. Laat de slicer de dunne pennen zoveel mogelijk met gesloten omtrekken vullen. Controleer de laagpreview met supports uit. De dockgaten hebben schuine daken; het ronde magneetvak in de kop heeft bovenaan een kleine driehoekige vrijloop met 45° flanken. De schijf rust op de ronde onderhelft. De onderste lippen van de rail en de schuine vlakken aan de slede zijn bereikbaar voor ontbramen. De eerste-laagrand mag de schuifpassing niet blokkeren.

## Afmetingen en digitale controles

| Interface | Ontwerpwaarden in mm |
|---|---|
| Pen en gat | Pen Ø3,30, 16 lang, hartafstand 27,40. De opening loopt in 7 mm van 12,80 naar 4,20 mm breed. Nominale radiale speling 0,45. De bodem en het dak van de inloop hellen naar de eindboring. |
| Magneet | Vier schijven Ø6 × 4. Elke kamer is nominaal Ø6,25 × 4,15 diep. De magneetassen liggen 8,65 mm recht onder de penassen. Tussen de punt van de vrijloop en de onderzijde van de trechtermond blijft nominaal 1,33 mm kunststof. Onder de magneet blijft 1,225 mm. |
| Kabel | Open U-goot 11,20 breed voor huis 10 × 6 × 18. Vul de goot met papieren stroken tot het stekkerhart klopt. Twee afzonderlijke binderbanen voor huis en mantel; de achterste loopt binnen de railflanken. |
| Kop en plaat | Robotplaat 38,60 × 14,75 mm; 5,35 mm dik voor de magneet en 1,20 mm achterwand. De armen zijn even hoog als de plaat. Bij de twee trechterdaken is de kop plaatselijk 20,60 mm hoog. |
| Rail | Montageplaat 26 × 36 mm. Zijspeling nominaal 0,40 per zijde, gemeten op horizontale snede. Schuine lippen houden de slede tegen bij optillen. Langgat 3,70 breed voor een pen van Ø2,98; nominale hartslag 6 mm, theoretische uiterste slag inclusief spel 6,72 mm. De borgpen blijft ongeveer 1 mm boven de onderzijde van de montageplaat. |
| Inloop | Bij 37 mm tussen de contactvlakken begint de grove geleiding. Bij 16 mm bereiken de pentoppen de fijne trechters. Bij circa 8 mm zit de volle pendiameter in de eindboring, bij de aangenomen slag van 6 mm bereikt de USB-tip de poortmond bij 6 mm. Gesloten blijft 1,40 mm axiale ruimte achter de pennen. |

De STL’s zijn numeriek uit de geometrie opgebouwd en na export opnieuw ingelezen. Elke STL moet één verbonden oppervlak hebben met positief volume en precies twee tegengesteld gerichte driehoeken per rand. Bij de rail is de ruimte tussen slede en lippen op drie standen en op meerdere doorsneden gecontroleerd. Schuifwrijving, fysieke overhangkwaliteit, houdkracht en gecombineerde vangst bij ±15 mm en ±10° vragen een echte proef.

## Montage en proef

1. Pas een losse magneet en een pen van de robotplaat in de coupon. De magneet moet zonder kracht tot op de vlakke bodem gaan. Controleer de pen ook met lichte hoogteafwijking.
2. Schuif de staart van de dockkop vanaf het open uiteinde tussen de raillippen. Breng het gat in de staart boven het langgat en steek de borgpen er van boven los in, kop boven. Beweeg over de volledige slag en controleer dat de lippen de kop vasthouden. Bevestig de railvoet op jullie eigen drager met twee vlakke tapestroken naast het langgat. Stel de rail evenwijdig aan de laadpoort en op de gemeten hoogte.
3. Plaats de magneten vanaf de contactzijde. Kies op de robotplaat links en rechts een omgekeerde pool naar voren. Laat elk dockmagneetje op zijn eigen tegenmagneet klikken, markeer het raakvlak, en plaats dit gemarkeerde vlak naar buiten in het dock. Borg met weinig geschikte lijm, zonder verhitting. Houd de magneten vlak of iets verzonken zodat de kunststof vlakken de eindaanslag vormen. Met de opgegeven dieptes kan elke schijf circa 0,15 mm terugliggen.
4. Leg de uitgenomen batterij en de plaat in de plakmal. Controleer de poort visueel: de echte batterij kan afwijken van de referentie-STL. Gebruik VHB op de vlakke draagstroken waar de kast werkelijk raakt. Controleer uitneembaan, poten, knop en leds. Test eerst zonder USB-kabel en met de hand.
5. Leg de kabel van boven in de goot. Stel de diepte spanningsloos met de echte batterij af. Bij volledige insteek moeten de contactvlakken juist samenkomen. Gebruik een smalle kabelbinder door de voorste twee sleuven rond het huis, en een tweede door de achterste sleuven rond de mantel. Richt de sluitkoppen omhoog. Geef de kabel achter de slede een losse bocht en herhaal de schuifproef mét kabel.
6. Probeer daarna kleine inloopfouten voordat je de uiterste zijdelingse en hoekafwijkingen test. Noteer of de magneten de laatste afstand met aangesloten kabel overbruggen, of de stekker volledig zit en of het dock bij loskomen vrij blijft bewegen. Automatisch koppelen en loslopen zijn nog niet aangetoond.

## Nog te meten

De kastreferentie meet circa 39,48 × 89,78 × 14,10 mm, 16,50 mm met deksel. De echte poortpositie, poortdiepte, insteekslag, kastvorm, tapecontact, VHB-dikte en vrije zone voor poten/knop/leds zijn nog onzeker. Het ontwerp neemt een poorthart op 10,5 mm vanaf de kastbodem aan. Met die aanname ligt de bovenzijde van het robotdeel 0,25 mm onder de laagste referentiehoogte van de houder. Die kleine marge is een reden om de mal eerst droog te passen en de montagehoogte te meten. De mal veronderstelt ook 0,8 mm samengedrukte tape.

Open magneet_dock.scad voor de parametrische constructie en de gesloten assemblage plus 10 mm tussenstand. De assemblage haalt de batterij, het deksel en de track uit het bestaande relatieve bronpad in de repo. De STL’s zijn zelfstandig te gebruiken. Zij zijn via Python geëxporteerd; een afzonderlijke OpenSCAD-render en een fysieke proef staan open.
## Meetresultaten van de geleverde STL’s

- Beide pennen meten circa Ø3,29 mm. Eén pengat meet horizontaal 12,14 / 8,43 / 4,16 mm op respectievelijk 0,45 / 3,50 / 7,50 mm achter de mond. De gemeten eindspeling per zijde is circa 0,43 mm. Op dezelfde drie diepten is de verticale vrije opening 8,84 / 7,00 / 4,89 mm. Het puntdak verklaart het verschil met de breedte.
- De vier magneetkamers meten op halve diepte circa 6,23–6,24 mm breed. De centrale kabeldoorgang meet 11,20 mm. De brede ingang meet 77,17 mm tussen de armen op 1 mm van de voorrand.
- Bij 0, 3 en 6 mm verplaatsing is de kleinste horizontale zijspeling in de bemonsterde raildoorsneden 0,39 mm. De bovenlippen overlappen de brede onderrand van de slede met circa 1,72 mm per kant. De kop kan daarmee alleen langs de rail uitgeschoven worden wanneer de borgpen is uitgenomen.
- Gewichtsraming uit gesloten meshvolumes bij 1,27 g/cm³ voor massief PETG: robotdeel 3,38 g, dockkop 23,15 g, railvoet 5,91 g, borgpen 0,13 g. De slicer kan lager uitkomen bij gedeeltelijke vulling. Magneten, kabel, tape en binders apart wegen.
