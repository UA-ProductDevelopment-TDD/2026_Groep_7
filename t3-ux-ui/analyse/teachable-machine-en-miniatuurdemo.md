# Teachable Machine en miniatuurdemo

8 november 2026. Met Codex opgesteld; voorstel, geen teambesluit. Aanvulling op `camera-en-grijper-uitvoerplan.md`. Geen hardware verbonden of dashboardcode gewijzigd.

## Nieuwe gebruikersinformatie

- Demonstratie waarschijnlijk met vos- en kipknuffel, eieren en kartonnen kippenhok. Objecten nog te verzamelen. Geen validatie op echte dieren veronderstellen.
- Petoi-arm is waarschijnlijk uitleenbaar; beschikbaarheid en geschiktheid voor eieren nog te controleren.
- Lama-behuizing in ontwikkeling bij collega.
- Laptop volgens gebruiker: i7-11800H, 48 GB RAM, NVIDIA T600 Laptop GPU met 4 GB, Intel UHD; 411 van 477 GB opslag gebruikt, dus ongeveer 66 GB vrij.
- Camera nog onbekend. Start software met webcam, afbeeldingen en videobestand; netwerkcamera later via eigen ontvanger aansluiten.

## Advies

Begin voor de eerste miniatuurdemo met Teachable Machine (TM) voor scèneclassificatie en een los verwisselbare herkenningslaag. Kies later objectdetectie als meerdere dieren tegelijk of afzonderlijke eieren gelokaliseerd moeten worden. Eenzelfde gegevensmodel kan beide ondersteunen, maar een classificatie krijgt geen verzonnen objectkader, afstand of telling.

TM-export kan lokaal gebruikt worden. Voorkeursroute: TensorFlow.js-export, inclusief modelstructuur, gewichtbestand(en) en metadata/klassen. Bewaar ook het trainingsproject en de oorspronkelijke beelden; gewichten alleen bewaren de trainingsverzameling niet. De JavaScriptbibliotheken en modellen moeten lokaal geleverd worden voor een werkelijk offline demo; de voorbeeldcode gebruikt externe CDN-links. Versies vastzetten en zonder internet testen.

De inferentie draait in de browser op de laptop; Python/FastAPI levert de app en ontvangt resultaten. TM accepteert een afbeelding, video of canvas. Een toekomstige ESP32-stream wordt eerst naar zo'n uniform beeld omgezet. Classificatie in de browser is afhankelijk van een actieve pagina: bij sluiten, pauzeren of achtergrondvertraging moeten resultaten verlopen. Geen blijvende hardwareactie baseren op een oude classificatie.

## Dataplan voor Jolan

1. Bouw eerst een eenvoudige versie van het hok en verzamel de uiteindelijke knuffels. Begin desnoods met een geleende webcam; de eindcamera blijft nodig voor hertesten en aanvullende training.
2. Kies bijvoorbeeld vier scèneklassen: leeg/achtergrond, alleen vos, alleen kip, vos en kip samen. Die laatste klasse voorkomt niet alle ambiguïteit: TM is hiermee nog steeds een scèneclassifier.
3. Maak per klasse meerdere afzonderlijke opnames: wissel positie, afstand, hoek, belichting en achtergrond. Gebruik voor alle klassen vergelijkbare achtergronden. Laat de hand die een knuffel vasthoudt niet onbedoeld het kenmerk van de vos worden.
4. Praktisch startvoorstel: 3–5 opnamesessies per klasse, samen ongeveer 100–300 gevarieerde beelden per klasse. Dit is geen vereiste of nauwkeurigheidsgarantie. Variatie en aparte testopnames zijn belangrijker dan aantallen bijna gelijke frames.
5. Houd één volledige sessie per klasse buiten TM-training. Test ook lege scènes, halve dieren en onbekende voorwerpen. Een lage score of onduidelijke combinatie wordt 'onzeker'; een hoge score sluit een fout niet uit.
6. Train een Standard image model op https://teachablemachine.withgoogle.com/ . Exporteer via TensorFlow.js → Download. Bewaar project, export en testbeelden apart.
7. Geef de modelbestanden, namen en betekenis van de klassen, testbeelden en testresultaten terug. Deel geen model alleen via een gehoste link als offline gebruik het doel is.

Eieren: voor een zeer vaste opstelling zijn scèneklassen '0/1/2/3 eieren' als beperkte proef mogelijk, maar dat is geen algemene teller. Voor vrije posities en overlap is een objectdetector of segmentatiemodel beter. Daarvoor teken je kaders of maskers rond ieder zichtbaar ei. Verborgen eieren blijven onbekend.

## Wat nu gebouwd kan worden

1. Bestaande app-start en tests controleren; ontbrekende dashboard-README aanvullen.
2. Een herkenningswerkblad met keuze webcam/afbeelding/video, livebeeld, start/stop en bronstatus.
3. Lokale TM-modelimport en foutmelding bij ontbrekende of onverenigbare bestanden.
4. Klassen en scores tonen, met echte classificatie expliciet gescheiden van gesimuleerde gegevens.
5. Instelbare bevestiging over meerdere beelden, waarschuwing bij onzekere uitkomst en vervallen van oude resultaten.
6. Proefmelding in dashboard met beeld en tijdstip; geen echte robot- of alarmactie.
7. Opnames en testresultaten lokaal bewaren met instelbare limiet.
8. Aansluitpunten voor netwerkcamera en objectdetector; pas na modelidentificatie de echte netwerkontvanger afwerken.

Dit is een bouwvolgorde, geen claim dat deze functies al bestaan. Na cameraswitch blijven resolutie, uitsnede, kleur, spiegeling, vertraging en modelkwaliteit te testen; 'alleen IP invullen' kan niet worden gegarandeerd.

## Laptopbeoordeling

Naar verwachting ruim geschikt voor dashboard, TM en één compacte herkenningsstroom. Nog geen benchmark. De 4 GB GPU-geheugen begrenst grotere modellen en trainingsbatches; 48 GB systeem-RAM vervangt GPU-geheugen niet. Begin zonder een grote CUDA/TensorFlow-installatie. Browserinferentie heeft die Python-installatie niet nodig. Python TensorFlow-GPU op moderne versies vraagt op Windows een andere route zoals WSL2; niet nodig voor dit eerste voorstel.

Circa 66 GB vrije opslag is voldoende om klein te starten, maar beperk videobewaring en voorkom dubbele datasets/omgevingen. Concrete snelheids- en geheugenclaims volgen pas na test.

## Toegevoegde Bittle Studio

Gericht gelezen in `t3-ux-ui/vb-studio/Bittle_Studio-master/Bittle_Studio-master/`: README, LICENSE, `docs/coop-simulation.md` (gerichte passages) en `app/coop/examples/external_detector.py`.

Deze kopie bevat naast Studio/Bittle Link een Coop-simulator en een HTTP-hub. Het externe detectorvoorbeeld haalt camerabeelden op en publiceert `label`, `confidence`, `bbox` via `detections/external`. De voorbeeldfunctie gebruikt kleurvlakken. Dat bewijst de koppeling als codevoorbeeld, niet herkenning van echte knuffels; niets hiervan is in deze sessie gestart of getest.

TM-classificatie levert geen bbox en past daarom niet rechtstreeks in deze objectdetectie-interface. Ontwerp een aparte classificatiegebeurtenis voor het dashboard; gebruik voor de bestaande simulatorinterface later een detector met echte kaders. Geen volledig beeldkader verzinnen als locatie van een vos.

Studio documenteert BLE en seriële bediening, een monitor en testmodus. Bruikbaar als referentie voor een afzonderlijke technische pagina en robotadapter. Letterlijke code-overname vraagt aandacht voor de aanwezige GPL-3.0-licentie. De voorbeeldstudio blijft ongewijzigd. Simulatorcijfers niet presenteren als gemeten hardwareprestaties.

## Wachten op bevestiging

Werkelijke camera-aansluiting, firmware/pinout/voeding; nauwkeurigheid op de eindcamera; grijperbereik en grijpkracht; echte robotacties; navigatie en metrische kaart. Ultrasoon/ToF kan obstakels signaleren, maar een kaart vereist ook betrouwbare pose en meetrichting. Markers en een vooraf gemaakte miniatuurkaart zijn een realistischer eerste integratie dan vrije SLAM.

## Internetbronnen

- Google TM-bibliotheek en lokale bestanden: https://github.com/googlecreativelab/teachablemachine-community/blob/master/libraries/image/README.md
- Officieel JS-exportvoorbeeld en ondersteunde beeldinvoer: https://github.com/googlecreativelab/teachablemachine-community/blob/master/snippets/markdown/image/tensorflowjs/javascript.md
- TensorFlow-installatie en Windows-beperkingen: https://www.tensorflow.org/install/pip

Alleen dit T3-analysebestand toegevoegd. Geen software geïnstalleerd, modellen getraind, code gekopieerd, robot aangestuurd of gedeelde projectdocumenten aangepast.
