# Landlicht — bewaard visueel uitgangspunt

Status: door Jolan visueel beoordeeld en aanvaard als voorlopig uitgangspunt op 2026-11-01. Gemaakt met Codex (AI). Backend, camera en robot zijn niet gekoppeld. De huidige vormgeving blijft behouden.

## Openen
Open `index.html` in Chrome of Edge. Geen installatie nodig. Bij wijzigingen: Ctrl+F5. Een lokale webserver is voor de volgende fase aanbevolen; zie `../../analyse/dashboard-lokaal-of-cloud.md`.

## Bestanden
- `index.html`: toepassing en dialoog.
- `dashboard.css`: Landlicht-vormgeving en schermformaten.
- `dashboard.js`: vijf pagina's, editor, demotaken, browseropslag.
- `map-engine.js`: gedetailleerde canvasplattegrond en zachte strook die binnen 120 seconden vervaagt.
- `core.js`: gegevensmodel, validatie en eenvoudige obstakelplanning.

## Huidige functies
Overzicht, Mijn kippenhok, Patrouilles, In de buurt en Activiteit. Objecten plaatsen, slepen, dupliceren, verwijderen, draaien en afmetingen wijzigen. Routes en verboden zones tekenen; punten verslepen na selectie. Ongedaan maken/opnieuw, kaart exporteren en importeren. Eiertelling handmatig aanpassen. Lokale demonstraties van patrouille, controlebezoek en terugkeer naar dock.

Kaart en telling worden in browser-localStorage bewaard. Dit is gekoppeld aan browser/profiel/oorsprong en kan worden gewist. Exporteer je eigen kaart als JSON voor een zelfstandige kopie. Browserdata zitten niet in Git. Wisselen van file:// naar localhost kan een afzonderlijke opslag opleveren: exporteer/importeer dan.

## Grenzen en controle
- Alle sensorwaarden en buurtwaarnemingen zijn demo. Een controlebezoek bewijst geen ei- of waterdetectie. De strook is positiehistoriek, geen gevalideerde cameradekking.
- Kaartafmetingen zijn illustratieve coördinaten, geen gekalibreerde meters. Eenvoudige planner is geen hardwarebesturing of fysische simulatie.
- De koppeling met PyBullet/Bittle Studio, het echte cameramodel, transportprotocol en lokalisatie zijn nog [ONBEKEND].
- JavaScript-syntax, validatie van startdata en een vrije demo-dockroute gecontroleerd op 2026-11-01. Geen volledige regressie-, browser- of robottest. Browserautomatisering werd geblokkeerd door onzekere URL-herkenning; Jolan heeft het ontwerp zelf bekeken.

## Bewaarde feedback
Positief: algemeen kwaliteitsniveau, Mijn kippenhok, overzicht en activiteit. Later: logo, minder zachte vormgeving, betere routevoorbeelden op Patrouilles. Buurtkaart later vervangen door inzoombare Vlaamse kaart; meldingsbron nog te kiezen. Nu geen verdere visuele herwerking.

## Context en vervolg
Gelezen: AGENTS.md, root- en team-CONTEXT.md, systeemafspraken, logboek, besluiten, Git-werkwijze, shared/INDEX.md, gerichte delen van vorige-jaren/README.md en Petoi Python API. Bittle Studio is gereedschap van de begeleiders; geen code gekopieerd.

Volgende stap ter bespreking: lokale startknop, FastAPI + SQLite en een simulatoradapter. Eerst bevestigbare testgegevens en verbindingsverlies, daarna integratie door elektronica/simulatie. Zie de architectuurnotitie. Nog geen hosting, hardwareverbinding of externe publicatie.
