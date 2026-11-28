# Bittle Platform

Eén eenvoudige pagina om met de echte Bittle te werken: de omgeving in kaart brengen, het camerabeeld bekijken, de robot besturen met een 3D-robot die meebeweegt, en beenbewegingen opnemen en bewaren. De sensoren, de natuurkundige simulatie en de rest van Bittle Studio zitten er bewust niet in.

**Klaar:** kaart, camerabeeld via USB, besturen via Bluetooth of USB, 3D-robot, bewegingen opnemen, motor-indeling, en **rondom scannen**: de robot draait op de plek en zet wat de camera ziet en wat de afstandssensor meet op de kaart.
**Later:** de echte afstandssensor (lidar of ultrasoon) uitlezen, de camera via wifi met de XIAO ESP32-S3, en eventueel de robot een verkenningsronde laten lopen.

## Starten

| | Windows | Mac | Linux |
|---|---|---|---|
| Starten | `launchers/windows/Start Bittle Platform.cmd` | `launchers/mac/Start Bittle Platform.command` | `launchers/linux/start-platform.sh` |

Het platform opent op http://127.0.0.1:8790. Gebruik **Chrome of Edge**: Bluetooth vanuit een webpagina werkt alleen daar. Laat het zwarte venster open; Ctrl+C stopt het platform.

**Meekijken vanaf een andere computer:** start met `app/platform_launcher.py --lan` (of `app/platform_server.py --lan`). Teamgenoten op hetzelfde wifi-netwerk openen dan `http://<ip-adres-van-deze-laptop>:8790` en zien de kaart en het camerabeeld. Wijzigen (opslaan, camera verbinden) kan alleen op de laptop zelf, en de robot besturen ook, want Bluetooth zit daar.

## De pagina

- **Kaart van de omgeving** (links): een bovenaanzicht in meters. Teken muren, omheining, het hok, een huisje, obstakels, zones, het dock, markers en tekst; zet de robot op zijn plek. Een foto of schets van het erf kan als achtergrond: upload hem, klik twee punten waarvan je de afstand kent en geef die afstand, dan klopt de schaal. Kaarten worden bewaard in `platform-data/maps/`. Sneltoetsen (als de kaart aangeklikt is): V W F C H O Z D M T R kiezen een gereedschap, Delete wist, Ctrl+Z maakt ongedaan, Ctrl+S bewaart, pijltjes schuiven 5 cm.
- **Camera**: het live beeld van de Grove Vision AI V2, met kaders rond wat het AI-model op het bordje herkent (nu een gezichtsmodel van SenseCraft).
- **3D-robot**: de Bittle (of de krabpoten) in de houding van dit moment. Hij loopt niet rond: het lichaam blijft staan en de poten bewegen.
- **Besturen**: rijden (pijltjes of W A S D, spatie = stop), houdingen, motoren aan/uit, en een schuif per gewricht.
- **Scannen**: rondom scannen vanaf de plek waar de robot op de kaart staat (zie hieronder).
- **Bewegingen**: houdingen opnemen en afspelen, bewaren onder een naam (in `platform-data/motions/`).
- **Motoren**: welke servo bij welk gewricht hoort, de draairichting en het nulpunt, per model.
- **Logboek**: alles wat naar de robot gaat en terugkomt, en een vak om zelf Petoi-commando's te sturen.

## De robot verbinden

Klik in de bovenbalk op **Bluetooth** en kies de Bittle in het venster van de browser (hij heet meestal "Bittle…" of "Petoi…"). Met een USB-kabel: **USB** en kies zijn COM-poort. **Test** werkt zonder robot: alles wat zou vertrekken, staat dan in het logboek.

**Robot volgt de 3D-robot** (bovenaan, standaard aan): elke houding van de 3D-robot (schuiven, afgespeelde bewegingen) gaat ook naar de echte robot, tot 20 keer per seconde. De knoppen voor rijden en houdingen sturen altijd het Petoi-commando; de robot voert dat zelf uit en de 3D-robot speelt hetzelfde mee.

## Een beenbeweging aanleren

1. Verbind de robot en open **Bewegingen**.
2. Zet de eerste houding: met de schuiven onder **Besturen**, of met **Live meelezen**. Dan worden de servo's slap en beweeg je de poten met de hand; de 3D-robot doet mee.
3. Klik **+ Houding toevoegen**. Herhaal voor elke houding.
4. Pas per houding de tijd aan (seconden om naar die houding te gaan), verplaats of vervang houdingen.
5. **Afspelen** toont de beweging op de 3D-robot en, met "Robot volgt" aan, op de echte robot. **Herhalen** laat ze doorlopen tot Stop.
6. Geef een naam en klik **Opslaan**.

## Rondom scannen

De camera en de afstandssensor zitten op het hoofd. De robot kijkt rondom en zet elke foto en meting meteen op de kaart.

**Twee manieren** (kies bij Instellingen → Scannen):
- **Nek-scan** (standaard, snel): de robot staat stil en zwaait zijn hoofd van rechts (−90°) naar links (+90°) in stapjes van 15°, met bij elke stand een foto en afstand: één zwaai duurt ongeveer 3,5 s. Daarna draait het lijf ongeveer 136° naar links, het hoofd zwaait opnieuw, en zo verder tot de camera het beginbeeld terugziet (meestal 3 zwaaien). De nekhoek is bekend, dus elke foto staat meteen goed op de kaart; de beelden zelf verfijnen de richting en meten hoeveel het lijf echt draaide. Let op: de nekas van Bittle staat 30° schuin (Petoi's eigen model), dus een nek van 90° kijkt maar ongeveer 74° opzij en wat omhoog; het platform rekent dat mee.
- **Lijf-scan**: de hele robot draait telkens een stapje (standaard 15°), staat stil en neemt een foto. Trager, maar werkt ook als de camera niet op het hoofd zit.

**Zo doe je een scan**
1. Bewaar de kaart (een scan hoort bij een bewaarde kaart) en zet de robot erop met het gereedschap **Robot**: klik zijn plek en sleep in de richting waarin hij kijkt.
2. Verbind de camera en de robot. Open **Scannen** en klik **Scan hier**. Tijdens een nek-scan volgt de echte robot altijd, ook als "Robot volgt de 3D-robot" uit staat; de 3D-robot zwaait mee.
3. Is de robot niet verbonden, of staat "Lijf draaien" op "Met de hand", dan draai je hem (of alleen de camera) zelf en klik je **Volgende foto**. Een nek-scan heeft de verbonden robot nodig voor het hoofd.
4. Zodra de camera het beginbeeld terugziet, is de scan rond. Het platform maakt dan de rondom-foto en zet alles op de kaart. Aan het eind staat hoeveel stappen en seconden de scan duurde.

**Hoe het platform weet hoeveel de robot draaide.** Bittle draait nooit precies wat je vraagt. Daarom vergelijkt het platform elke foto met de vorige: bij draaien schuift het beeld opzij, en uit die verschuiving volgt de hoek. Ziet een foto te weinig (een kale muur), dan telt de gevraagde draai. Als de cirkel rond is, vergelijkt het platform het laatste beeld met het eerste en verdeelt het de opgestapelde fout over alle stappen. Tegelijk meet het zo de echte kijkhoek van de camera; met **Gebruik deze kijkhoek** neem je die over. In proeven met nagemaakte camerabeelden zat elke richting daarna binnen 0,5° van de werkelijkheid, voor lenzen van 45° tot 80°.

**Wat er op de kaart komt**
- **Kijkrichtingen** (paarse streepjes) vanaf de scanplek, één per foto, en de **rondom-foto** in het tabblad. Van links naar rechts in de rondom-foto is rechtsom draaien.
- **Herkende dingen**, als gekleurde punten met hun naam en zekerheid. De afstand volgt uit waar het ding de grond raakt in het beeld, met de hoogte en kanteling van de camera uit de instellingen. Zie je zijn onderkant niet, dan schat het platform de afstand uit de grootte van bekende dingen (persoon, kip, vos). Wat het herkent, hangt af van het AI-model op het bordje (nu gezichten); voor kippen of een vos moet er een ander model op, bijvoorbeeld een eigen model uit SenseCraft AI.
- **Het vloerbeeld**: de grond tot 1,2 m rond de robot, van bovenaf gezien.
- **Gemeten afstanden** (oranje punten) en de **omtrek** die ze vormen, als er een afstandssensor gekozen is. Met **Muren maken van de omtrek** worden het muren op de kaart; controleer ze en bewaar de kaart.

**De omgeving in 3D.** In het 3D-venster staan de foto's van de scans op de huidige kaart rond de robot, al tijdens het scannen: elke foto staat in de richting waarin de camera keek, op de afstand die de sensor mat. Het deel van een foto dat de grond toont, buigt naar de vloer; de rest staat recht als een wand. Naast elkaar liggende foto's tonen elk hun eigen strook, zodat ze samen een ring vormen. Foto's zonder meting staan doorschijnend op de gemiddelde afstand van de scan. Herkende dingen zijn oranje bollen. Met **Omgeving** zet je het aan of uit; met **Overzicht** zoom je uit (**Dichtbij** gaat terug). De robot blijft in het midden; draait hij tijdens een scan, dan draait de omgeving om hem heen.
Met de SRF05 is elke foto een vlakke wand (één afstand per foto). De code werkt al met een raster van afstanden per foto: met een 8×8 ToF-sensor (VL53L5CX) krijgt elke foto straks de vorm van wat ze toont.

**Instellingen** (onderaan in Scannen):
- Hoogte, kanteling, kijkhoek van de camera en hoe ver ze vóór het midden van de robot zit.
- Scanmanier (nek of lijf); voor de nek: hoe ver (standaard 90°), de nekstap (15°) en de wachttijd na een nekstap (0,1 s; verhoog die als de foto's wazig zijn).
- Hoe het lijf draait: Petoi's draaien op de plaats (kvtL), met de hand, of een eigen opgenomen beweging (handig voor de krabpoten).
- Stapgrootte en wachttijd van het lijf. Houd de stap onder ongeveer een derde van de kijkhoek, anders overlappen de foto's te weinig.
- De afstandssensor.

### De afstandssensor

Bij elke stap bewaart de scan de gemeten afstand, en de kaart toont die als punten en omtrek. Kies de sensor bij **Instellingen** in de Scannen-tab:

- **SRF05 op de camera (XIAO)**: de ultrasone sensor op de XIAO van de camera (zie "Via wifi" hieronder). De camera moet verbonden zijn, via USB of wifi. Bij elke stap neemt het platform een halve seconde metingen (ongeveer 7) terwijl de robot stilstaat en houdt de middelste; als de meeste metingen geen echo geven, staat er in die richting niets binnen bereik (4 m). Wat de camera recht voor de sensor herkent (binnen ±15°), krijgt die gemeten afstand in plaats van een schatting uit het beeld, behalve als het beeld een heel andere afstand geeft (dan kwam de echo van iets anders). In de lijst van herkende dingen staat "(gemeten)" of "(geschat)". Zet bij **Vóór het midden** en **Richting** waar de sensor op de robot zit.
- **Nagebootste sensor**: meet wat op de kaart getekend is (muren, omheining, hok, huisje, obstakels). Daarmee probeer je alles uit zonder robot.
- **Andere sensoren** (later): een nieuwe bron in `app/bittle_platform/distance.py`; de rest van de scan blijft hetzelfde.
  - Ultrasoon (zoals de HC-SR04 of Petoi's Grove-sensor) geeft één afstand per stap in een brede bundel. Gaas en stro kaatsen het geluid soms slecht terug.
  - Een lidar met één straal (TF-Luna, VL53L1X) is smaller en nauwkeuriger.
  - Een draaiende 2D-lidar (RPLIDAR, LD06) meet zelf honderden afstanden rondom.

## Motor-indeling (vooral voor de krabpoten)

De 3D-robot werkt met gewrichtshoeken; de robot met servohoeken: **servo = gewrichtshoek × richting + nulpunt**. Bij de standaard Bittle klopt de indeling al (0 = nek, 8-11 = schouders, 12-15 = knieën, de rechterpoten draaien omgekeerd). Bij de krabpoten zijn de voorste onderbenen omgekeerd gemonteerd, dus:

1. Kies bovenaan het model **Krabpoten** en open **Motoren**.
2. Klik **Test** bij een gewricht: alleen die servo beweegt even heen en terug. Beweegt de verkeerde poot, kies een ander servonummer.
3. Draait de poot de andere kant op dan de 3D-robot, keer de richting om (+/−).
4. Zet de robot in de nulstand (Besturen → Nulstand) en pas het nulpunt aan tot de echte poot staat zoals de 3D-poot.
5. **Opslaan**. De indeling staat in `platform-data/motor-layout.json`.

De ingebouwde Petoi-vaardigheden (wandelen, zitten…) zijn gemaakt voor de standaardpoten. Voor de krabpoten neem je beter eigen bewegingen op.

## De camera

De camera bestaat uit twee delen die bij elkaar horen:

- **Seeed Grove Vision AI V2**: het bordje met de AI-chip (Himax WiseEye2). Het herkent zelf wat de camera ziet, met een model van SenseCraft AI. Met USB-C aan de laptop verschijnt het als een COM-poort (USB-chip CH343).
- **Raspberry Pi-camera 1.3** (OV5647): de camera zelf, met een lintkabel. Die gaat in de lintkabel-aansluiting van de Grove Vision AI V2: klepje open, lint er helemaal in met de metalen contacten naar de contacten van de aansluiting, klepje dicht.

In het platform: kies de poort (die met "Vision AI" erbij), een beeldgrootte (240×240 is het vlotst) en klik **Verbind**. Zonder aangesloten camera meldt het platform dat het bordje antwoordt maar de camera niet; steek je de camera daarna in, dan start het beeld vanzelf.

### Via wifi (XIAO ESP32S3 Sense)

De **XIAO ESP32S3 Sense** zit op de achterkant van de Grove Vision AI V2 en maakt de camera draadloos. Hij geeft het AI-protocol van het bordje ongewijzigd door over wifi (TCP-poort 3333): beeld, herkende kaders en modelnaam komen dus precies zo binnen als via USB, en scannen en herkennen werken hetzelfde. Zonder Vision AI V2 op de pinnen geeft hij het beeld van zijn eigen Sense-camera (zonder AI).

**Eerste keer (of op een nieuwe plek):**

1. Zet de camera aan. Kent de XIAO nog geen bereikbaar netwerk, dan maakt hij na ±20 s de hotspot **Bittle-Camera**.
2. Verbind je telefoon of laptop met **Bittle-Camera**. De instelpagina opent vanzelf (anders: surf naar `192.168.4.1`).
3. Kies **Configure WiFi**, kies je **2,4 GHz**-netwerk (5 GHz werkt niet) en typ het wachtwoord. De XIAO onthoudt het.
4. Na het opslaan verbindt hij met dat netwerk en gaat het oranje lampje aan. Zijn statuspagina staat op `http://bittle-camera.local` (of het IP-adres dat de router hem gaf).

Wordt de instelpagina 5 minuten niet gebruikt, dan herstart de XIAO en probeert hij opnieuw. Wifi vergeten: knop op de statuspagina, of houd de **BOOT**-knop van de XIAO 5 s ingedrukt.

**In het platform:** kies bij de camera **📶 Wifi-camera (XIAO)**, laat het adres op `bittle-camera.local` (of typ het IP-adres) en klik **Verbind**. De laptop moet op hetzelfde wifi-netwerk zitten. Zonder wifi kan het ook met een USB-kabel aan de USB-C van de XIAO: kies dan zijn COM-poort ("XIAO op de Vision AI").

**Afstandssensor SRF05 op de camera:** de XIAO zoekt bij het opstarten zelf waar hij zit: Trigger/Echo op de pads **MTMS/MTDI** (achterkant, GPIO42/41) of op **D2/D1**. Voeding op VUSB (5V) en GND, MODE los, en Echo via een spanningsdeler (1 kΩ naar de pin, 2 kΩ van de pin naar GND), want de SRF05 geeft 5 V. Hij meet ongeveer 14 keer per seconde; het platform toont de afstand linksboven in het camerabeeld (📏). De metingen komen als extra regels `{"type": 1, "name": "DISTANCE", "data": {"cm": …}}` mee in dezelfde verbinding als het beeld.

**Batterij:** het zekerst is een kleine powerbank aan de USB-C van de XIAO: dan krijgen beide bordjes 5 V. Een LiPo van 3,7 V aan de BAT+/BAT−-pads onderaan de XIAO (die laadt hem op via USB-C) voedt de XIAO zelf, maar op batterij zit er geen 5 V op de 5V-pin; test dus eerst of de Grove Vision AI V2 dan nog opstart (statuspagina: "Grove Vision AI V2 gevonden"). Lukt dat niet, zet dan een kleine 5 V-boost tussen de LiPo en de 5V-pin.

**Firmware:** `firmware/bittle-camera/bittle-camera.ino` (Arduino, bibliotheek WiFiManager). Opnieuw bouwen en flashen (XIAO met zijn eigen USB-C aan de laptop):

```bash
arduino-cli compile -b esp32:esp32:XIAO_ESP32S3:PSRAM=opi --output-dir firmware/bittle-camera/build firmware/bittle-camera
```

```bash
arduino-cli upload -p COM5 -b esp32:esp32:XIAO_ESP32S3:PSRAM=opi --input-dir firmware/bittle-camera/build firmware/bittle-camera
```

`arduino-cli` staat in `%LOCALAPPDATA%\Programs\arduino-cli`. Seeed heeft zelf een vergelijkbaar voorbeeld (`camera_web_server` in de bibliotheek Seeed_Arduino_SSCMA) met een eigen webpagina; deze firmware gebruikt hetzelfde idee (XIAO praat met het bordje via de UART-pinnen D6/D7), maar geeft de gegevens door aan het platform in plaats van aan een eigen pagina.

## Wat het platform (nog) niet doet

- De 3D-robot heeft geen natuurkunde: hij valt niet en loopt niet rond, hij toont alleen de houding.
- De robot op de kaart zet je met de hand (gereedschap Robot). Waar hij staat, bepaalt het platform niet zelf; alleen hoeveel hij draait tijdens een scan.
- Eén camera meet geen afstanden: zonder afstandssensor krijgen alleen herkende dingen een geschatte plek, en teken je muren zelf (de rondom-foto helpt).
- De kaders van de camera komen van het model op het bordje; dat model kies of train je in SenseCraft AI.
- Bluetooth werkt alleen in Chrome of Edge, en alleen op de computer waarop het platform draait.

## Voor ontwikkelaars

- Server: `app/platform_server.py` (FastAPI, poort 8790). Opslag: `app/bittle_platform/storage.py`; camera: `app/bittle_platform/camera.py` (Seeed SSCMA AT-protocol, 921600 baud over USB, of `wifi://host[:3333]` via de XIAO); 3D-modellen: `app/bittle_platform/models.py`; scannen: `app/bittle_platform/scan.py` (cilinderprojectie en fasecorrelatie met numpy, Pillow voor JPEG); afstandssensor: `app/bittle_platform/distance.py` (hier komt de echte sensor bij).
- Gegevens: `platform-data/` (kaarten, bewegingen, scans met hun foto's, motor-indeling, instellingen).
- Pagina: `app/web/platform/` (gewone ES-modules, three.js); de 3D-omgeving staat in `environment.js` en leest per foto `steps[].view` uit de scan-API (camerapositie, richting, kanteling, kijkhoek en `depth`: een raster in meters langs de kijkrichting). De verbinding met de robot hergebruikt `app/web/bittle-link/link.js`.
- Tests:

```bash
.venv/Scripts/python.exe -m unittest discover -s app/tests -t app -p "test_platform*.py" -v
```
