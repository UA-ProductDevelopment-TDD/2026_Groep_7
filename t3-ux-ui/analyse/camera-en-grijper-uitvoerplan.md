# Camera, lokale herkenning en grijper: uitvoerplan

Datum: 7 november 2026. Opgesteld met Codex voor T3 UX/UI. Onderzoeksadvies, geen teambesluit. Geen hardware getest of firmware gewijzigd. Bittle X met BiBoard V1 blijft het uitgangspunt; de lama is de geplande behuizing volgens Jolan, nog geen gecontroleerd mechanisch ontwerp. Met “Bitalino” interpreteren we hier de Bittle uit de projectcontext; controleer het fysieke label.

## 1. Uitkomst van de aanvullende broncontrole

De zipbestanden zijn rechtstreeks en zonder uitvoering van hun code onderzocht. Tekst uit de lokale PowerPoint is uitgelezen; afbeeldingen in die presentatie zijn niet visueel geïdentificeerd. Afwezigheid in deze zoekactie bewijst niet dat de school een onderdeel niet heeft.

| Bewijs | Vindplaats | Conclusie en grens |
|---|---|---|
| XIAO ESP32-S3 met Grove Vision AI v2 | `shared/vorige-jaren/2025_Groep_2-main.zip`, intern `2025_Groep_2-main/README.md`, regels 77–80 | Expliciet gedocumenteerde combinatie bij vorige groep; niet bevestigd als huidige kitinhoud |
| Werkelijke ontvangstcode voor camerabeelden | Zelfde zip, `ELA/AI vision/camera_test_2.html`, regels 86–142 | HTTP-opdrachten; HTTP-stream op poort 8080, pad `/stream/result`; JSON-regels met `data.image` als base64-JPEG en `data.boxes` |
| README noemt MJPEG, code gebruikt bovengenoemd formaat | Zelfde bronnen | Protocol niet uit README alleen afleiden. Firmwareversie en daadwerkelijk antwoord controleren |
| Geen camera-/vision-`.ino` gevonden in Groep 2 | Namen van alle `.ino`-bestanden in de zip gecontroleerd | Browsercode is onvoldoende om de camera reproduceerbaar te flashen |
| XIAO ESP32S3 als BLE-client naar Bittle | `2025_Groep_1-main.zip`, `Lijntje/FinaleCodeAIVisionBLE.ino`, regel 2 | Ondersteunt het patroon met aparte ESP32; identificeert niet op zichzelf de camerasensor |
| DFRobot DFR1154 expliciet genoemd | `concept/presentatie/Concept-presentatie-v2-NL.pptx`, slide 10; ook 16 en 22; `materials.json` | Begroot onderdeel; de presentatie labelt de buzzer als UA-onderdeel, niet de camera. Geen voorraadbewijs |
| ESP32-S3-camera en herkenning op module voorgesteld | Zelfde presentatie, slide 7 | Oud architectuurvoorstel. Lokale laptopherkenning is de nu onderzochte route |
| Mu-camera gekoppeld aan lesmateriaal | `shared/bronnen/links.md`, regel 56 | De verwijzing is expliciet als afgeleid/vermoedelijk gemarkeerd; geen harde kitinventaris |
| GroveKit nr. 8 | `SYSTEEM.md` | Kitnummer bekend; gedetailleerde inhoud ontbreekt |

De gerichte tekstscan van Groep 5 leverde geen aanvullende camera-identificatie op. Er is geen bevestigde grijperinventaris gevonden. De lokale samenvatting van de practicumslides bevat geen volledige onderdelenlijst. Een nieuwere presentatie of schoolinventaris buiten deze checkout is niet gecontroleerd.

**Werkhypothese:** vraag bij school eerst naar Grove Vision AI V2 + XIAO ESP32-S3, omdat hiervan concrete projectcode bestaat. Controleer daarna DFR1154. Koop niets op basis van deze hypothese.

## 2. Eerst verzamelen: één pakket waarmee we verder kunnen

Doe deze inventaris bij uitgeschakelde hardware. Noteer onbekenden als `[ONBEKEND]`; maak geen pinout op basis van kabelkleur of een gelijkende stekker.

| Te verzamelen | Hoe | Waarom nodig |
|---|---|---|
| Camera en alle gekoppelde printjes | Scherpe foto boven- en onderkant, plus één overzichtsfoto met kabels | Visionmodule, ESP32 en camerasensor kunnen drie verschillende onderdelen zijn |
| Opschriften | Letterlijk merk, model, revisie en sensorlabel overnemen | V2, Sense en bordrevisie kunnen andere software vereisen |
| Inventarisbewijs | Foto van kitlijst of antwoord van modulebeheerder | Onderscheid beschikbaar, uitleenbaar en alleen voorgesteld |
| Bestaande werking | Vraag wie laatst beeld zag, in welke app en met welke firmware | Een werkende configuratie behouden bespaart herstelwerk |
| USB en voeding | Connector, gebruikte voeding en eventuele adapter fotograferen | Elektronica kan juiste spanning en stroomvoorziening bevestigen |
| Camera-adres | Alleen als al bekend: lokale URL en firmwareversie | Bepaalt ontvanger en protocol |
| Grijper | Foto, model, servo-opschrift en meegeleverde onderdelen | Bepaalt mechaniek, aansturing en voeding |
| Laptop | Windows Instellingen → Systeem → Info: CPU en RAM; Taakbeheer → Prestaties: GPU-model en GPU-geheugen | Modelkeuze en eventuele versnelling |
| Demonstratieobjecten | Foto van vos, kip en ei naast liniaal | Echt dier, speelgoed en print vragen andere trainingsbeelden |
| Lama-opbouw | Schets van camera, nek, grijper en batterij | Zichtveld, stabiliteit en bereik afstemmen |

Geen wifiwachtwoorden, API-sleutels, studentennummers of apparaatsleutels in het verslag of Git opnemen. Voor de laptop volstaan componentnamen; een volledig systeemrapport is niet nodig.

Vraag modulebeheerder en begeleider concreet:

1. Hebben we dezelfde Grove Vision AI V2 en XIAO ESP32-S3 als Groep 2 van vorig jaar? Welke sensor zit eraan?
2. Is DFR1154 aanwezig, besteld of alleen ooit voorgesteld?
3. Is er een uitgeleende grijper: Petoi-arm, M5Stack Catch U102, servogrijper of iets anders?
4. Is de werkende camerafirmware van vorig jaar nog beschikbaar, met bijbehorende versies en installatie-instructies?
5. Welk lokaal 2,4GHz-netwerk mogen we gebruiken waarop laptop en camera elkaar kunnen bereiken?

Klaar voor de volgende stap: camera/ESP32 identificeerbaar, juiste voedingsroute door elektronica bevestigd, duidelijk of bestaande firmware behouden kan blijven.

## 3. Route kiezen op basis van wat daadwerkelijk aanwezig is

### A. Grove Vision AI V2 met XIAO ESP32-S3

Gebruik de officiële Seeed-handleiding [S1] als referentie. Die beschrijft Grove Vision AI V2 met XIAO ESP32S3 Sense, een HTTP-server en 2,4GHz-wifi. Controleer of jullie precieze bord overeenkomt. De AI-chip van de Grove-module en de ESP32 zijn verschillende componenten.

Eerst bestaande webinterface proberen; niet meteen flashen. Vraag de modulebeheerder naar de huidige netwerkconfiguratie. Noteer het werkelijke adres; IP-adressen uit vorig jaar niet kopiëren.

Als de pagina beeld toont, controleer via browserontwikkeltools → Network welk verzoek de beelden draagt. De oude Groep 2-code gebruikt een HTTP-response met JSON-regels en base64-afbeeldingen, **geen WebSocket in dit specifieke testbestand**. De README noemt dit MJPEG, maar de getoonde implementatie is anders. Het nieuwe dashboard moet het werkelijk aanwezige formaat ondersteunen.

De oude code activeert ook sensor/inferentie via een `/command`-endpoint. Voer die opdrachten niet blind uit: protocol en firmware moeten overeenkomen. Het ontvangen van `boxes` betekent dat een model op de module detecties heeft gemaakt; het zegt niet dat dit model vos, kip of ei kent. Voor laptopherkenning hebben we vooral bruikbare volledige beelden nodig.

Als firmware ontbreekt: elektronica kiest het bij het bord passende officiële voorbeeld, bewaart de bestaande configuratie waar mogelijk en legt versies vast. De Seeed-handleiding noemt versiegevoelige instellingen [S1]. Pas de Arduino-installatie voor het BiBoard niet zomaar aan om de camera werkend te krijgen; gebruik aparte projectconfiguraties. De lokale robotveiligheidsregels hebben betrekking op het BiBoard en zijn geen universele cameraboardinstructie.

### B. DFRobot DFR1154

Gebruik DFRobot-documentatie en voorbeelden [S2, S3]. Start bij `5.3 CameraWebServer`. DFRobot heeft daarnaast OpenCV- en YOLO-voorbeelden: nuttige technische referenties, geen bewijs van herkenning van onze doelobjecten.

Laat elektronica het model, passende bordinstellingen en voeding controleren. Bij bestaande firmware: eerst de webpagina en het beeld aantonen. Bij nieuwe firmware: een mens uploadt alleen naar het bevestigde camerabord. Noteer daarna IP, poort, streamroute en firmwareversie uit het eigen voorbeeld; geen generieke ESP32-pinout overnemen.

### C. XIAO ESP32-S3 Sense met rechtstreeks aangesloten camera

Een XIAO met eigen camera-uitbreiding is niet automatisch Grove Vision AI V2. Vraag welke fysieke sensor aan welk bord gekoppeld is. Kies pas daarna de bijbehorende Seeed-cameragids en firmware. De identificatie bepaalt of we rechtstreeks JPEG-frames ontvangen of via een afzonderlijke visionmodule werken.

### D. Mu-camera of alleen detectieresultaten beschikbaar

Controleer of volledige beelden toegankelijk zijn. Alleen coördinaten of labels zijn onvoldoende om op de laptop een eigen beeldmodel te draaien. Als volledige beelden niet beschikbaar zijn: gebruik voorlopig een bestaande webcam of opgenomen bestand voor de software, en zoek binnen school naar een uitleenbare streamingcamera. Koop geen nieuwe module zonder deze check.

## 4. Eerste werkende wifi-proef

Doel: aantonen dat camera → laptop werkt, zonder lopen, grijpen of alarm. Uitvoering met elektronica; voor hardwarehandelingen gelden `_config/veiligheid-robot.md` en de juiste fabrikantdocumentatie.

1. Begin op tafel met de cameramodule volgens bevestigde voedingsinstructies. De robot hoeft voor deze proef niet te bewegen.
2. Gebruik een toegestaan lokaal 2,4GHz-netwerk. Een geschikte router of hotspot kan dienen; verifieer de frequentie en dat apparaten onderling bereikbaar zijn. Een gastnetwerk kan dat verhinderen.
3. Verbind laptop en camera met dat netwerk. Internettoegang alleen is geen bewijs dat ze elkaar kunnen bereiken.
4. Verkrijg het camera-IP uit de bestaande interface, routerlijst of bij het voorbeeld horende monitor. Geen poortscan nodig.
5. Open de exacte lokale camera-URL in de browser. Noteer of de pagina en het beeld afzonderlijk werken.
6. Houd een hand of testobject voor de camera. Controleer dat het beeld daadwerkelijk verandert en niet een bewaarde foto is.
7. Laat vijf minuten lopen. Noteer uitval, bevriezen, herstarten en de aangeboden resolutie. Vijf minuten is onze voorgestelde eerste testduur, geen productspecificatie.
8. Laat een stopwatch of bewegend object filmen en film desgewenst tegelijkertijd het laptopscherm. Schat de vertraging; benoem meetonnauwkeurigheid. Zonder cameraklok meet je niet zomaar exacte opnamevertraging uit een server-tijdstempel.
9. Beëindig en herstel de verbinding op een door elektronica afgesproken manier. Controleer of beeld vanzelf terugkomt en of een ander IP is toegewezen.
10. Herhaal pas daarna op de geplande werkafstand en met de lama-behuizing voorlopig rondom de camera.

Teruggeven: cameramodel, voeding bevestigd ja/nee, firmware, URL, protocol indien bekend, resolutie, vijfminutenresultaat, geschatte vertraging, herstelgedrag en één representatief beeld. Stuur geen wachtwoorden.

### Als iets niet werkt

| Waarneming | Eerst controleren | Wat teruggeven |
|---|---|---|
| Geen nieuw USB-apparaat | Datakabel, juiste poort, voeding; niet willekeurig drivers installeren | Bordlabel en exacte melding in Apparaatbeheer |
| Geen camera-IP | Juiste netwerkband, geldige configuratie, antenne en voeding door elektronica | Laatste relevante logregels zonder geheimen |
| Camera-IP bekend, pagina niet bereikbaar | Werkelijk huidig IP, zelfde lokaal netwerk, gastisolatie | Exacte URL en browserfout |
| Pagina wel, beeld niet | Streamknop, protocol, sensorverbinding, firmware-/modelstatus | Network-status en foutmelding |
| Browserbeeld wel, Python later niet | MJPEG versus JSON/base64 versus RTSP, eventuele activatiestap | Response-type en klein geschoond voorbeeld zonder beeldpayload |
| Beeld loopt steeds verder achter | Buffering, te hoge resolutie, te trage herkenning | Verschil met en zonder herkenning |
| Module herstart | Voeding, aansluitingen, geheugen of firmware | Herstartlog en omstandigheden; geen spanning gokken |

## 5. Laptop en dashboard voorbereiden

De lokale dashboardcode staat in `../prototype/dashboard/`. FastAPI, SQLite en een testadapter bestaan; `/api/camera/frame` maakt nu een SVG-testbeeld. Er is nog geen echte camera- of grijperkoppeling. De map wordt op het moment van controle door Git als niet bijgehouden gemeld. De ontbrekende README en reproduceerbare startcontrole moeten bij de implementatiestap worden afgewerkt.

Beoogde bouwvolgorde:

1. Bestaande app en tests controleren zonder robot. Projectopslag, startprocedure en foutmeldingen vastleggen.
2. Eén bron toevoegen: eerst videobestand/webcam indien beschikbaar, daarna de bevestigde netwerkcamera.
3. Camera-ontvangst in een aparte taak uitvoeren. Eén cameraverbinding delen tussen livebeeld en herkenning.
4. Alleen het nieuwste bruikbare beeld bewaren voor inferentie. Geen oplopende wachtrij.
5. Een apart herkenningsproces toevoegen, zodat een langzaam model de stopknop en interface niet blokkeert.
6. Beeld en detecties koppelen met hetzelfde beeldnummer. Rotatie, schaling en uitsnijden registreren voordat kaders worden getekend.
7. Verbindingsstatus en leeftijd van het laatst ontvangen beeld tonen. Bij storing: resultaat onbekend, niet nul.
8. Detecties en proefmeldingen toevoegen; hardwareacties blijven uit totdat hun interface is afgesproken en getest.

Voorstel gegevens per detectie: bron, beeldnummer, ontvangsttijd, optionele echte opnametijd, modelversie, klasse, score en kadercoördinaten. Ontvangsttijd niet als opnametijd presenteren. Voor eiertelling ook nest/meetpositie, tijdstip en handmatige correctie bewaren. Scores zijn modeluitkomsten, geen gegarandeerde kansen.

Software kan na installatie lokaal werken. Gratis/open-source betekent niet automatisch dat ieder model en iedere dataset dezelfde licentie heeft. YOLO11n is een praktische startkandidaat [S7]; YOLOX Nano/Tiny een alternatief [S8]. Vergelijk pas prestaties op de eigen laptop. Geen FPS-garantie vooraf.

## 6. Herkenning trainen en beoordelen

Begin met één taak: vosmelding óf eieren op een vaste plek. Voor een snelle demonstratie is een stilstaande opname eenvoudiger te beoordelen dan herkenning tijdens lopen.

1. Kies exact wat telt als doelobject: speelgoedvos of echte vos, echte eieren of namaakeieren. Leg dit vast.
2. Neem korte, afzonderlijke sessies op: verschillende afstanden, kijkrichtingen, lichtomstandigheden en achtergronden. Voeg lege scènes en verwarrende objecten toe.
3. Selecteer gevarieerde beelden; duizenden bijna identieke videoframes zijn geen gevarieerde dataset.
4. Label alle zichtbare doelobjecten consequent. Noteer hoe gedeeltelijk zichtbare objecten behandeld worden.
5. Houd hele opnamesessies buiten de training voor validatie en test. Voorkom dat vrijwel hetzelfde beeld in beide zit.
6. Train een klein model met onze klassen. Standaard COCO bevat niet afzonderlijk vos, kip en ei [S9].
7. Meet zowel gemiste doelen als valse meldingen. Test ook zonder doelobject in beeld.
8. Vergelijk CPU en beschikbare GPU op identieke testbeelden. Noteer rekentijd én de totale zichtbare vertraging.
9. Test opnieuw na montage in de lama; montagehoek en trillingen veranderen de beelden.

Voorgestelde eerste evaluatie, nog af te spreken met het team: tien aparte passages met een vosobject, tien zonder; tien stilstaande nestscènes met handmatig bekende aantallen; vijf minuten continue livefeed. Rapporteer ruwe aantallen, geen algemene betrouwbaarheidsclaim uit zo'n kleine proef. Voor echte inzet is veel bredere validatie nodig.

Alarmvoorstel: meerdere recente detecties moeten overeenstemmen; één twijfelbeeld geeft hoogstens een observatie. Drempels en wachttijd worden met testbeelden gekozen, niet als fabrikantfeit ingevuld. Een mens beoordeelt de eerste meldingen. De software mag nooit oude detecties als actuele aanleiding blijven gebruiken.

## 7. Welke grijpers concreet onderzoeken?

| Optie | Wat is bevestigd | Nog controleren | Advies zonder budget |
|---|---|---|---|
| Petoi Bittle-arm/grijper | Officiële uitbreiding met eigen installatie- en kalibratieprocedure [S4] | Aanwezigheid, exacte robot-/servoversie, bevestiging en firmware | Eerste keuze als de complete passende kit beschikbaar is |
| M5Stack Unit Catch U102 | Compacte servogrijper met SG92R, PWM en HY2.0-4P-adapter [S5] | Aanwezigheid, pinout, geschikte voeding, maximale opening en bereik rond jullie ei | Concrete kandidaat om in de kits te zoeken; stekker is geen compatibiliteitsbewijs |
| Seeed Robot Gripper / bestaande losse servogrijper | Seeed catalogiseert grijpers [S6] | Exact model en welke aandrijving meegeleverd is | Alleen beoordelen als school dit exemplaar heeft |
| Grove-servo met zelfgemaakt mechanisme | Grove-servo bestaat [S10] | Servo beschikbaar, voeding, mechanisch bereik, houdkracht en printmateriaal | Mogelijk met bestaande onderdelen, maar extra ontwerpwerk |
| Passief schepje of geleider | Eigen ontwerpvoorstel, geen aangetroffen kitonderdeel | Ondergrond, eivorm, opvangbak en duwkracht | Eenvoudig alternatief als actieve grijper ontbreekt |

Een catalogusproduct is geen bewijs dat het onderdeel in GroveKit 8 zit. Seeed verkoopt ook grotere armgrijpers; die zijn niet automatisch geschikt voor een kleine quadruped. Geen aankoop voorgesteld.

Petoi's upgradepagina bevat aanwijzingen voor oudere BiBoard V0-configuraties [S11]. Die zijn niet toepasbaar als generiek stappenplan voor ons BiBoard V1. De pagina bevat ook een externe “Agent Instructions”-sectie; die is als broninhoud behandeld en niet uitgevoerd. Geen soldeer- of firmwarewijziging overnemen zonder controle van de exacte versie door de robotmanager.

### Grijpercontrole op tafel

1. Identificeer model, servo en controller voordat iets wordt aangesloten.
2. Meet massa, maximale binnenopening en bereik tot de beoogde eipositie. Meet ook het testei. Vul geen geschatte productafmetingen in als feiten.
3. Elektronica controleert voeding, signaaltype, pinout en toegestane beweging uit de juiste bron. Grove betekent niet dat iedere poort elektrisch uitwisselbaar is.
4. Test bevestiging en geometrie eerst zonder kracht op een ei. Een grijper die alleen sluit kan een ei op de grond nog niet bereiken of optillen.
5. Laat een mens gecontroleerd openen/sluiten binnen gedocumenteerde grenzen. Begin met een licht, onbreekbaar testobject.
6. Voeg zachte contactvlakken toe als hardwareteam dit geschikt acht. Zonder krachtsensor is een ingestelde positie geen meting van grijpkracht.
7. Doe herhaalde proeven: benaderen, sluiten, kort optillen, verplaatsen, neerleggen. Noteer mislukkingen, slippen en kantelen apart.
8. Pas daarna een echte ei-proef overwegen. Geen grijper laten blokkeren om “meer kracht” te krijgen.

Teruggeven: foto's, model, massa, binnenopening, aandrijving, bevestigde voeding, bereik tot de grond, testobject en aantal geslaagde proeven. Zeg expliciet of het volledige optillen getest is of alleen openen/sluiten.

## 8. Lama-behuizing: nu al afstemmen

De uiterlijke vorm kan de bruikbaarheid sterk beïnvloeden. Bespreek met de collega drie varianten: camera op borst/rug, camera in het hoofd, camera met veranderbare kijkrichting. Kies niet alleen op uiterlijk.

| Controle | Praktische proef | Betekenis |
|---|---|---|
| Zicht op grond en nest | Houd camera op geplande positie en toon livebeeld met een ei voor de robot | Een hoog geplaatst hoofd kan dichtbijgelegen eieren missen |
| Beweging van de nek | Film tijdens handmatig nabootsen van de verwachte beweging | Lange nek kan beeldtrilling en wisselende oriëntatie vergroten |
| Camera en grijper tegelijk | Maak een zijaanzicht en bovenaanzicht van hun bereik | Snuit, bek of grijper mag het doel niet afdekken |
| Beeldoriëntatie | Controleer tekst of marker in het beeld | Rotatie/spiegeling moet ook op detectiekaders worden toegepast |
| Netwerk en toegang | Test met kap erop en eraf; houd USB en reset bereikbaar | Behuizing kan signaal en onderhoud beïnvloeden |
| Gewicht en balans | Laat hardwareteam massa en zwaartepunt vergelijken met en zonder opbouw | Lange nek en arm kunnen stabiliteit verminderen |

Voor de eerste demonstratie zou ik een vaste cameramontage kiezen en de robot laten stoppen voor een nestcontrole. Als de camera beweegt, moet navigatie haar actuele oriëntatie kennen. Een kalibratie van vóór de definitieve montage blijft niet vanzelf geldig.

## 9. Werkverdeling en afspreekpunten

Voorstel: Jolan/T3 beheert laptopontvangst, herkenning en dashboard; elektronica bevestigt camerabord, voeding, firmware en protocol; hardware verzorgt lama, montage en grijpermechaniek; robotmanager begeleidt alle robotproeven. Leg eigenaarschap expliciet vast met het team.

Levering van elektronica aan T3: model + firmwareversie + werkelijk werkende URL + streamformaat + opstartvolgorde + herstelgedrag. Levering van T3 aan elektronica: benodigde beeldkwaliteit, gewenste statusvelden en lijst met afzonderlijk te bevestigen acties. Een detectie is geen commando en een verstuurd commando is geen bewijs van uitvoering.

Routeplanning komt pas na aantoonbare beeldontvangst. Voor de miniatuur: bekende kaart, herkenbare vaste markers en afstandsmeting onderzoeken; objectdetectie alleen levert geen betrouwbare afstand of beloopbaarheidskaart. OpenCV biedt marker- en kalibratietechniek [S12].

## 10. Invulformulier om terug te sturen

Kopieer dit en vul alleen in wat bekend is:

```text
INVENTARIS
Camera/visionmodule merk + model + revisie:
ESP32-bord (inclusief Sense ja/nee):
Camerasensorlabel:
Foto's overzicht / bovenkant / onderkant:
Aanwezig of alleen voorgesteld? Bevestigd door:
Bestaande firmware en wie die heeft:
Voeding gecontroleerd door elektronica:

LAPTOP EN NETWERK
Windows-versie:
CPU / RAM / GPU / GPU-geheugen:
Netwerksoort en 2,4GHz beschikbaar:
Camera-URL (zonder wachtwoord):
Webpagina bereikbaar / veranderend livebeeld zichtbaar:
Protocol of Network-screenshot:
Resolutie / vijf minuten stabiel / geschatte vertraging:
Gedrag na verbinding herstellen:
Exacte foutmelding indien van toepassing:

GRIJPER EN LAMA
Grijper merk/model + servo:
Foto / massa / binnenopening / bereik tot grond:
Voeding en pinout bevestigd:
Openen/sluiten getest of ook optillen:
Testobject en resultaten:
Geplande camera- en grijperpositie op lama:

DEMONSTRATIE
Echte dieren/eieren of miniaturen:
Eerste prioriteit: vosmelding / eieren tellen:
Beschikbare testbeelden:
Wat nog ontbreekt:
```

Met alleen identificatiefoto's en laptopgegevens kan het vervolg al gericht voorbereid worden. Met een werkende URL en bekend streamformaat kan de echte camera-adapter gebouwd worden. Grijpergegevens hoeven dat werk niet op te houden.

## 11. Bronnen en audit

Internetbronnen geraadpleegd 7 november 2026:

- S1: https://wiki.seeedstudio.com/grove_vision_ai_v2_webcamera/
- S2: https://wiki.dfrobot.com/dfr1154/
- S3: https://github.com/DFRobot/DFR1154_Examples
- S4: https://docs.petoi.com/extensible-modules/robot-arm
- S5: https://docs.m5stack.com/en/unit/Catch
- S6: https://www.seeedstudio.com/tag/Gripper.html
- S7: https://docs.ultralytics.com/models/yolo11/ en https://www.ultralytics.com/license
- S8: https://github.com/Megvii-BaseDetection/YOLOX
- S9: https://docs.ultralytics.com/datasets/detect/coco/
- S10: https://wiki.seeedstudio.com/Grove-Servo/
- S11: https://docs.petoi.com/extensible-modules/robot-arm/upgrade-your-older-bittle-bittle-x-for-the-robotics-arm-gripper
- S12: https://docs.opencv.org/4.5.0/d9/d6d/tutorial_table_of_content_aruco.html

Aanvullend lokaal gelezen of gericht doorzocht: `_config/opdracht.md`, `_config/veiligheid-robot.md`, `t3-ux-ui/CONTEXT.md`, `shared/bronnen/links.md`, `shared/bronnen/petoi-docs/extensible-modules-introduction.md`, de drie genoemde studentenarchieven en de PowerPoint. Dit bouwt voort op de vorige controle van `CONTEXT.md`, `SYSTEEM.md`, `BESLUITEN.md`, `LOGBOEK.md`, `shared/INDEX.md`, de vorige chat en dashboardcode.

Het wegwerpscript `t3-ux-ui/lokaal/zoek-camera-bronnen.py` zoekt tekst in de geselecteerde archieven en PowerPoint zonder bestanden uit te voeren. De lokale uitvoer staat in `camera-broncontrole.json`. Deze zoekhulpen zijn geen productcode en horen niet als broninventaris van school te worden geïnterpreteerd. Alleen T3-bestanden zijn toegevoegd; dashboardcode en gedeelde documenten zijn niet gewijzigd. Geen robotproef uitgevoerd, geen teambesluit genomen, geen commit of push.
