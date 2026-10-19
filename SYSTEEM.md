# SYSTEEM — kaart van het robotsysteem

> **Layer 3.** Beheerd door de projectmanager, met de teams. Status: `actueel`.
> Dit is een kaart, geen specificatie: ze verwijst naar de bron en zegt hoe en wanneer iets gecontroleerd is. Wijkt de kaart af van een bron of van de werkelijkheid, dan is de kaart fout: pas ze aan. Waarom zo: `STRUCTUUR.md`, "Afspraken", punt 7.

## Labels

| Label | Betekent |
|---|---|
| `bron` | staat zo in een bron in `shared/bronnen/` (pad erbij) |
| `gecontroleerd` | iemand van het team heeft het zelf nagekeken of gemeten (wie, datum) |
| `nog-onbevestigd` | uit een snelle lezing of een agent-analyse; nog niet nagekeken |
| `[ONBEKEND]` | weten we niet |

## Het platform (uitgangspunt van deze repo)

| Onderdeel | Wat | Label | Bron |
|---|---|---|---|
| Robot | Petoi Bittle X (uitgangspunt van deze repo; de opdracht noemt ook de Sesame Robot, zie `BESLUITEN.md`, open keuze 4) | `bron` | `_config/opdracht.md` |
| Exemplaar | GroveKit nr. 8; Bittle-nummer `[ONBEKEND]` (de teaminfo noemt "Bittle 3 #" zonder nummer) | `nog-onbevestigd` | teaminfo docenten, zie `BESLUITEN.md`, D005 |
| Bord | BiBoard V1: ESP32-U4WDH, 4 MB flash, wifi en Bluetooth LE, 12 servo-PWM, zes-assige bewegingssensor, Grove (UART2, I2C, 4 analoog), Raspberry Pi-poort, ingangsspanning 7 tot 9 V, baud 115200 | `bron` | `shared/bronnen/petoi-docs/biboard-v1-guide.md` |
| Firmware | Petoi OpenCat voor ESP32; model en board kies je bovenaan `OpenCatEsp32.ino`; de juiste instelling voor ons staat in `t1-elektronica/CONTEXT.md` | `nog-onbevestigd` (uit de zip gelezen) | `shared/vorige-jaren/OpenCatEsp32-Quadruped-Robot-main.zip`, `_config/veiligheid-robot.md` |
| Gewrichten | 0 = hoofd (pan), 8-11 = schouders, 12-15 = knieën; welke schouder of knie welk nummer heeft `[ONBEKEND]`. Het jointnummer staat los van de PWM-pin op het bord | `nog-onbevestigd` (nummers uit de slides) | `_config/veiligheid-robot.md`, regel 10; de pagina `shared/bronnen/petoi-docs/joint-pins-biboard-v1-bittle-x.md` bevat alleen een bedradingsafbeelding en de waarschuwing over de pinnen |
| Besturing | seriële tekstcommando's, elk met één tokenteken vooraan (`ksit`, `m0 30`, `d`); USB 115200 baud. Vorige groepen stuurden dezelfde commando's via Bluetooth LE | `bron` voor serieel; `nog-onbevestigd` voor BLE | `shared/bronnen/petoi-docs/serial-protocol.md` |
| Apps van Petoi | Desktop App, mobiele app, Skill Composer, Python API, Blockly-blokken | `bron` | `shared/INDEX.md`, groep "Petoi-docs" |

## Wat erbij kan (modules)

Petoi beschrijft deze modules voor het hoofd van de Bittle. Welke wij gebruiken, volgt uit het gekozen concept.

| Module | Bron |
|---|---|
| ultrasoon-afstandssensor | `shared/bronnen/petoi-modules/module-ultrasonic-sensor.md` |
| camera (Mu) | `.../module-mu-camera.md` |
| dubbele IR-afstandssensor | `.../module-ir-distance-sensor-double-infrared-reflection-sensor.md` |
| PIR-bewegingssensor | `.../module-pir-motion-sensor.md` |
| aanraaksensor | `.../module-touch-sensor.md` |
| lichtsensor | `.../module-light-sensor.md` |
| gebarensensor | `.../module-gesture-sensor.md` |
| spraakmodule | `shared/bronnen/petoi-docs/voice-command-module.md` |

Zie ook: één sensor tegelijk actief; Grove G1 en de Raspberry Pi-poort delen UART2 (`_config/veiligheid-robot.md`, regels 12 en 13).

## Wat wij bouwen of aanpassen

Wordt ingevuld door de teams zodra er iets is. Eén rij per onderdeel. Geen rij zonder pad.

Nog niets: de eerste rij komt bij het eerste onderdeel.

| Onderdeel | Team | Status | Waar | Gecontroleerd |
|---|---|---|---|---|

Status: `idee`, `analyse`, `in bouw`, `getest`, `herzien nodig`. `herzien nodig` zet je als iets waar het onderdeel van afhangt, wijzigt (gids §18.3).

## Simulatie

| Onderdeel | Wat | Label | Bron |
|---|---|---|---|
| URDF-model | `urdf/bittle.urdf`: 12 joints, 8 `revolute` (schouders en knieën) en 4 `fixed`; geen kop of staart; PyBullet-index is niet het servonummer | `nog-onbevestigd` (gecontroleerd in de zip, niet op een robot) | `shared/vorige-jaren/Bittle_URDF-main.zip`, `shared/vorige-jaren/README.md` |
| Simulator | PyBullet, de keuze van het vak | `bron` | `shared/bronnen/simulatie/pybullet-bullet3.md` |

## Afspraken tussen teams

Hier staat wat het ene team aan het andere moet leveren of van het andere mag verwachten. Een afspraak zonder inhoud is `[ONBEKEND]`. Elke wijziging krijgt een regel in `LOGBOEK.md` en, als ze iets beslist, in `BESLUITEN.md`.

| Van | Naar | Wat | Waar vastgelegd | Status |
|---|---|---|---|---|
| `t1-elektronica` | `t2-hw-sim` | afmetingen en gewicht van sensoren, bord, accu en laadpoort | `t1-elektronica/prototype/<onderdeel>/README.md` | `[ONBEKEND]` |
| `t2-hw-sim` | `t1-elektronica` | beschikbare ruimte en bevestigingspunten | `t2-hw-sim/prototype/<onderdeel>/README.md` | `[ONBEKEND]` |
| `t1-elektronica` | `t3-ux-ui` | welke commando's en sensorwaarden de robot geeft en neemt, via BLE of USB | `t1-elektronica/prototype/<onderdeel>/README.md`, sectie "Interface" | `[ONBEKEND]` |
| `t3-ux-ui` | `t1-elektronica` | wat de gebruiker moet zien of kunnen sturen, met prioriteit | `t3-ux-ui/prototype/<onderdeel>/README.md` | `[ONBEKEND]` |
| `t2-hw-sim` | `t3-ux-ui` | een testomgeving (simulatie) om de app zonder robot te proberen | `t2-hw-sim/prototype/<onderdeel>/README.md` | `[ONBEKEND]` |
| `t3-ux-ui` | `t2-hw-sim` | de scenario's die in simulatie getest moeten worden | `concept/concept.md` (bestaat pas na het consult) en issues | `[ONBEKEND]` |
