# Dashboard: lokaal of cloud?

Onderzocht 2026-11-01 met Codex. Architectuurvoorstel, geen teambesluit. Visuele basis blijft bewaard in `../prototype/stijlverkenning/`.

## Advies
Begin lokaal: huidig dashboard + Python/FastAPI + SQLite + een verwisselbare simulator/robotadapter. Geen React-herschrijving nodig om dit interactief te maken: het huidige JavaScript reageert al op gebeurtenissen. React kan later helpen bij onderhoud, maar bepaalt niet waar de app draait.

| Optie | Wat draait waar? | Geschikt voor | Nadeel/kosten |
|---|---|---|---|
| Lokaal, aanbevolen | Browser + server + database op laptop | Practicum, offline demo, simulatie en directe robotkoppeling | Laptop moet aanblijven; bestaande hardware en stroom nodig |
| Vercel + Supabase | Online dashboard, accounts, opslag en updates | Meerdere gebruikers en kijken buitenshuis | Gratis quota/voorwaarden, internet en afzonderlijke robotbrug/video-oplossing |
| Hybride, later | Lokale besturing; selectieve cloudsync | Lokale werking met online geschiedenis/meldingen | Meer componenten en authenticatie |
| Dashboard direct op ESP32 | Webbestanden en firmware op module | Kleine ingebouwde bediening | Past niet vanzelf bij deze editor, opslag en simulator; geheugen/firmwarecapaciteit onbekend |

Geen hostingabonnement nodig voor de lokale optie. Een bestaande laptop volstaat voor de UI-server; zware simulatie/beeldherkenning moet afzonderlijk worden getest. Wifi binnen hetzelfde netwerk is geen internetverbinding. Zonder externe kaarttegels kan de lokale UI offline werken nadat afhankelijkheden zijn geïnstalleerd.

## Lokale architectuur en gebruikersflow

```text
Start-dashboard (Windows-startbestand, later te bouwen)
  └─ lokale Python-server opent dashboard in browser
      ├─ SQLite: terrein, routes, eieren, gebeurtenissen
      ├─ WebSocket: status, positie, bevestiging van acties
      ├─ video-endpoint: lokale camerastream doorgeven
      └─ verwisselbare adapter
          ├─ mock: ontwikkel- en foutscenario's
          ├─ PyBullet: koppeling door simulatie-team
          └─ robot: koppeling door elektronicateam
```

FastAPI ondersteunt WebSockets [1]. SQLite schrijft naar een lokaal bestand en vereist geen aparte databaseserver [2]. Ontwerp: server levert zowel UI als API vanaf dezelfde oorsprong; dit vermijdt veel cross-origin-problemen. Eerst alleen localhost. Telefoontoegang op hetzelfde wifi-netwerk is een aparte stap met bewuste LAN-configuratie, toegangsbescherming en firewallinstelling. Zet robotbesturing niet zomaar publiek op internet.

Een Windows-launcher kan de omgeving controleren, de lokale server starten en de browser openen. Eerst eenmalig dependencies installeren; daarna één startbestand. Later eventueel verpakken als desktopprogramma. Dat hoeft geen nieuwe UI te betekenen.

Bittle Studio gebruikt volgens de repo-analyse FastAPI + PyBullet + three.js en launchers per besturingssysteem [3]. Het patroon past dus bij het practicum. Niet hetzelfde als onze huidige animatie: die is een functionele mock, geen gevalideerde fysische robot-simulatie. Studio-code is GPL-3.0 volgens die analyse; we hoeven geen code over te nemen.

## Livebeeld
Espressif publiceert JPEG-capture en een HTTP-JPEG-streamvoorbeeld [4]. Voor de eerste proef is een lokale MJPEG-stream vaak eenvoudiger dan een volledige videoclouddienst. Voorstel: ESP32-camera levert beelden, de lokale server geeft die onder zijn eigen adres door, dashboard toont de stream. Begin met een videobestand of testbeeld; voeg pas daarna een echte bron toe.

Dit is geen bewijs dat de geplande cameramodule deze firmware, resolutie, framerate of gelijktijdige detectie ondersteunt: model, geheugen, streamformaat, prestaties en voeding blijven [ONBEKEND] tot elektronica ze bevestigt. Gebruik niet blind een algemeen ESP32-CAM-pinout. Bittle X/BiBoard V1 is het uitgangspunt; camera en BiBoard zijn aparte componenten.

Supabase Realtime is bedoeld voor gegevensupdates, niet voor het doorsturen van ieder videoframe. Cloudvideo vergt een geschikte streamingverbinding; eventueel WebRTC met relay, wat extra complexiteit/verkeer kan geven. Bereken kosten pas na een gemeten bitrate. Geen garantie dat continu cloudvideo gratis blijft.

## Vercel en Supabase: actuele grenzen
- Vercel Hobby is bedoeld voor persoonlijk, niet-commercieel gebruik; teamgebruik/toelaatbaarheid dus checken [5]. De directe Hobby-koppeling met Git-repositories van organisaties is niet ondersteund volgens de huidige limietenpagina [6]. Onze repo zit in UA-ProductDevelopment-TDD. Geen persoonlijke fork als sluiproute: dat botst met onze repo-afspraken.
- Vercel ondersteunt inmiddels WebSockets op alle plannen, maar verbindingen eindigen bij de maximale Function-duur; reconnects en externe duurzame staat blijven nodig [7]. Oud advies dat Vercel helemaal geen WebSockets ondersteunt is achterhaald. Een cloudfunction krijgt daarmee nog geen toegang tot een robot op een lokaal wifi-netwerk: een expliciet geauthenticeerde verbinding/brug blijft nodig.
- Supabase Free: 500 MB database, 1 GB bestandsopslag, 5 GB egress plus 5 GB cached egress, 2 miljoen Realtime-berichten/maand en 200 piekverbindingen. Maximaal twee actieve gratis projecten; pauzering na een week inactiviteit [8]. Dit kan een klein prototype dragen, geen belofte voor onbeperkt streamen of 24/7 beschikbaarheid.

Beoordeling: nuttig als latere online laag, niet nodig voor onze volgende stap. GitHub blijft ook bij een volledig lokaal programma de broncode en versiegeschiedenis beheren.

## Contract tussen teams (voorstel, nog overeenkomen)
UX/UI definieert gewenste scherminformatie en testscenario's. Elektronica levert transport en echte meetwaarden. Simulatie levert robot-/omgevingsgedrag. Nodige afspraken:
- status en positie: tijdstip, bron (mock/simulatie/robot), geldigheid, coördinatenstelsel en eenheden;
- batterij, deur, eiertelling: waarde of onbekend, meettijd en herkomst; handmatige telling apart houden;
- acties: uniek ID, aangevraagd/geaccepteerd/uitgevoerd/mislukt; een klik is geen uitvoering;
- camera: streamadres, formaat en beschikbaarheid;
- verbindingsverlies: zichtbaar onbekend/offline; robotzijdige stop/timeout is verantwoordelijkheid elektronica. Webknop is geen gegarandeerde fysieke noodstop;
- mapping: kaartversie, schaal, oriëntatie, oorsprong en lokalisatiekwaliteit. Huidige schermcoördinaten zijn geen meters.

Concrete pinnen, seriële commando's, endpointnamen en vervaltijden hier bewust niet ingevuld. Eerst afspreken in SYSTEEM.md met de verantwoordelijke teams.

## Eerstvolgende bouwstappen
1. Huidige stijl behouden. Launcher en lokale server toevoegen, databasebestanden buiten Git.
2. Huidige gegevens/toestanden losmaken van schermcode; één mockadapter met dezelfde interface als later de echte adapter.
3. Tests: herstart bewaart kaart; offline wordt zichtbaar; acties krijgen een bevestiging; onbereikbaar doel faalt netjes; stop wordt niet zomaar als uitgevoerd aangenomen.
4. Videobestand/testbeeld, daarna lokale stream door elektronica. Geen robotcommando's door AI uitvoeren.
5. Simulatie-team sluit zijn omgeving aan; mens test de fysieke koppeling.
6. Pas bij behoefte aan toegang buitenshuis cloudsync, accounts en hosting kiezen.

## Buurtkaart, later
Leaflet is een open-source kaartbibliotheek voor zoomen en markers [9]. Begin met Vlaanderen, daarna gemeente/dorpsniveau. Kaarttegels en waarnemingen zijn afzonderlijke bronnen. OpenStreetMap vereist bronvermelding en naleving van het tegelbeleid; publieke standaardtegels zijn geen onbeperkte offline-downloadvoorziening [10]. Buurtapps leveren niet automatisch een toegankelijke API. Eerst markers met gemarkeerde testdata, daarna een toegelaten meldingsbron. De huidige pagina blijft voorlopig ongewijzigd.

## Bronnen
[1] FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
[2] Python/SQLite: https://docs.python.org/3/library/sqlite3.html
[3] Interne analyse: `../../shared/vorige-jaren/README.md`, sectie Bittle_Studio. Alleen gerichte analyse gelezen, zip niet opnieuw onderzocht. Aanvullend: `../../shared/bronnen/petoi-docs/python-api.md`.
[4] Espressif camera-driver en voorbeelden: https://github.com/espressif/esp32-camera/blob/master/README.md
[5] Vercel Hobby: https://vercel.com/docs/plans/hobby
[6] Vercel Git-organisatiebeperking: https://vercel.com/docs/limits#connecting-a-project-to-a-git-repository
[7] Actuele WebSocket-documentatie: https://vercel.com/docs/functions/websockets
[8] Supabase Free en quota: https://supabase.com/pricing
[9] Leaflet: https://leafletjs.com/
[10] OSM-tegelbeleid: https://operations.osmfoundation.org/policies/tiles/

Bronnen geraadpleegd op 2026-11-01. Cloudprijzen en voorwaarden opnieuw checken bij daadwerkelijke implementatie. Geen cloudaccount, deployment of robotverbinding gemaakt.
