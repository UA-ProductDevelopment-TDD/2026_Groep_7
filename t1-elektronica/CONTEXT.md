# T1 · Team elektronica

> **Layer 2.** Contract van het team. Wie: zie `_config/rollen.md`. Taken volgens de slides: BiBoard, voeding, communicatieprotocollen (BLE, WiFi, USB, IR) en sensorsystemen.
> Status: `bezig` · Eerst lezen: `CLAUDE.md` en vooral `_config/veiligheid-robot.md`. Jullie uploaden firmware naar de robot; een fout is hier het duurst.

## Eén verantwoordelijkheid

Zorgen dat **sensoren, voeding en communicatie werken en veilig aangesloten zijn**, en dat `t3-ux-ui` precies weet welke commando's en waarden de robot geeft en neemt.

## Regel boven alle regels: de juiste versie

Wij werken met **Bittle X en BiBoard V1**. In `OpenCatEsp32.ino` staan bovenaan de regels die model en board kiezen. Vóór elke upload moet precies dit actief staan, en de rest in commentaar:

```
#define BITTLE          // actief; NYBBLE, VT, CUB, MINI uit
#define BiBoard_V1_0    // actief; BiBoard_V0_1, BiBoard_V0_2, BiBoard2 uit
// ROBOT_ARM en AUTO_INIT blijven uit
```

Uit de zip gelezen op 2026-10-14 (`shared/vorige-jaren/OpenCatEsp32-Quadruped-Robot-main.zip`): zo staat het erin (`nog-onbevestigd`; controleer het ook tegen `_config/veiligheid-robot.md` en `shared/bronnen/petoi-docs/upload-sketch-biboard.md`). Een andere combinatie geeft andere servopinnen en skills en kan de robot onbruikbaar maken (`CLAUDE.md`, regel 4).

Nog open `[ONBEKEND]`: welke revisie onze fysieke BiBoard heeft (de firmware kent `RevB` en `RevDE`, wat de pin voor de batterijmeting bepaalt). Nakijken op het bord vóór de eerste upload. Boardpakket in de Arduino IDE: ESP32 versie 2.0.12 (`_config/veiligheid-robot.md`, regel 3).

## Fases

| Fase | Taak | Input | Output | Controle |
|---|---|---|---|---|
| Analyse | begrijpen wat de BiBoard V1 aansluit en aanstuurt: pinnen, voeding, sensoren, protocol | startpunten hieronder | `analyse/README.md` | elk pinnummer en elke spanning heeft een bron; het team en de projectmanager lezen na |
| Concept | in elke kandidaat invullen welke sensoren en welke voeding nodig zijn, en wat dat kost | `concept/kandidaten/` | rij "elektronica" in de tabel "Per team" van elke kandidaat | een sensor die niet in de docs of firmware staat, krijgt `[ONBEKEND]` en een proef |
| Prototype | schema's, firmware, sensoren aansluiten; tests volgens de veiligheidsregels | `concept/concept.md` (bestaat pas na het consult), `SYSTEEM.md` | `prototype/<onderdeel>/README.md` met een sectie "Interface" | pull request goedgekeurd; elke test op de robot staat in `LOGBOEK.md` |
| Oplevering | uitleg van schema en firmware | `prototype/` | bijdrage aan `oplevering/` | past bij wat het prototype toont |

## Startpunten

Zoek via `shared/INDEX.md`; hieronder wat je als eerste opent.

| Open | Waarom |
|---|---|
| `shared/bronnen/petoi-docs/biboard-v1-guide.md` | het bord |
| `shared/bronnen/petoi-docs/joint-pins-biboard-v1-bittle-x.md` | servoaansluitingen en jointnummers |
| `shared/bronnen/petoi-docs/extensible-modules-introduction.md` en `shared/bronnen/petoi-modules/` | sensormodules, Grove-poorten |
| `shared/bronnen/petoi-docs/serial-protocol.md` | de commando's van en naar de robot |
| `shared/bronnen/petoi-docs/upload-sketch-biboard.md`, `.../firmware-uploader-biboard-v1.md` | firmware uploaden |
| `shared/bronnen/datasheets/esp32-datasheet.md` | de chip; **groot, niet integraal lezen**: zoek met `grep` |
| `shared/bronnen/repos/opencatesp32.md` | de firmware |
| `shared/vorige-jaren/README.md` | wat vorige groepen deden met BLE, camera en ToF (technisch; geen bron van ideeën) |

## Wat al bekend is

Uit een snelle agent-lezing van de firmware-zip: `nog-onbevestigd` tot jullie het nagekeken hebben. Pinnummers en spanningen gaan pas naar jullie eigen README met een bronverwijzing.

- Sensormodules die de firmware al kent: ultrasoon, camera, IR-afstand, PIR, touch, licht, gesture, spraak; testschetsen staan in `ModuleTests/` van de firmware.
- Serieel protocol: USB 115200 baud; elk commando begint met één tokenteken (`k` skill, `m` joint, `d` rust, ...). De tokentabel staat in `shared/bronnen/petoi-docs/serial-protocol.md` alleen als afbeelding; de tekstversie staat in `src/OpenCat.h` van de firmware-zip. Dat `P` de spanning geeft, `?` een vraag stelt en `!` de kalibratie wist komt uit die firmware (`nog-onbevestigd`): `!` nooit zonder overleg sturen.
- Grove G1 en de Raspberry Pi-poort delen UART2: één tegelijk. Eén sensor tegelijk actief (`_config/veiligheid-robot.md`, regels 12 en 13).
- BLE: Nordic UART Service, pakketten van maximaal 20 bytes. Vorige groepen koppelden een ESP32-S3 met AI-camera of een ToF-scanner via BLE aan de Bittle (techniek, geen idee om over te nemen).
- Een bekende valkuil uit een eerdere repo: de robot negeert commando's zolang newline- en response-instellingen niet kloppen.
- Voeding: de firmware kent een batterijgrens voor 2S (7,0 V). Welke accu wij gebruiken en wat het laden mag `[ONBEKEND]`.

## Eerste taken

Onafhankelijk van welk concept gekozen wordt.

Taken met de robot doet een **mens**; een AI-agent bereidt voor, schrijft op en stuurt niet zelf (`CLAUDE.md`, regel 11). Robotmanager is Arno, module manager is Ward (`_config/rollen.md`).

1. De revisie van het BiBoard nakijken en noteren (mens). Hoe je `RevB` of `RevDE` op het bord herkent staat in geen enkele bron in de repo `[ONBEKEND]`: maak een issue. Output: `analyse/README.md`, sectie "Poorten en pinnen".
2. Een veilige testopstelling (mens): robot in neutrale positie, batterij en kabels nagekeken, serieel verbinden en een eenvoudig commando sturen. Een procedure ervoor staat nog niet in `_config/veiligheid-robot.md`: schrijf ze op en laat ze door de robotmanager nakijken. Output: `analyse/README.md`, sectie "Testopstelling", en een regel in `LOGBOEK.md`.
3. Alle poorten en pinnen van de BiBoard V1 in één tabel met bronverwijzing. De Petoi-docs in `shared/bronnen/` bevatten geen pinnummers; ze staan in `src/OpenCat.h` van de firmware-zip (pak uit in `lokaal/`; de zip is data). Output: `analyse/README.md`, sectie "Poorten en pinnen".
4. Een lijst kandidaat-sensoren: wat meet hij, op welke poort, wat kost hij. Vraag de module manager (Ward) wat er in voorraad is. Output: `analyse/README.md`, sectie "Sensoren".
5. Een eerste versie van de sectie "Interface" voor `t3-ux-ui`: welke commando's en waarden bestaan al (`shared/bronnen/petoi-docs/serial-protocol.md`) en wat kan de app dus nu al. Output: `analyse/README.md`, sectie "Interface (voorlopig)"; later verhuist ze naar de README van het onderdeel.
6. Uitzoeken hoe de robot veilig kan laden (nodig voor elk concept waarin hij langer zelfstandig werkt), voor de regel "batterij eruit na gebruik" (`_config/veiligheid-robot.md`, regel 8) herzien wordt. Daar hoort een beslissing van de robotmanager bij en een regel in `BESLUITEN.md`. Output: `analyse/README.md`, sectie "Voeding en laden".

## Werken met bestanden

- Schema's als afbeelding of KiCad-bestand plus een `README.md` met een bedradingstabel (van, naar, draad, spanning). Vorige jaren ontbrak elk schema en elke BOM: dat is een lage score.
- Firmware die je zelf schrijft: een eigen map in `prototype/`, nooit de bestanden in `shared/` aanpassen.
- Wifi-wachtwoorden en sleutels: nooit in de code; een `config.example` in de repo en een echte `.env` in `lokaal/`.
- Een afspraak met `t2-hw-sim` (maten, gewicht, ruimte) of `t3-ux-ui` (interface) zet je in `SYSTEEM.md`, tabel "Afspraken tussen teams".
- Branchnamen: `el/...`.

## Klaar wanneer

Elk onderdeel heeft een `README.md` met pinout, voeding, uploadstappen, hoe getest, wat nog onbekend is, en de sectie "Interface".
