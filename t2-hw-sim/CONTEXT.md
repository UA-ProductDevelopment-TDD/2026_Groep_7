# T2 · Team hardware en simulatie

> **Layer 2.** Contract van het team. Wie: zie `_config/rollen.md`. Taken volgens de slides: robotontwerp, sensor- en motorpositionering, lasercut- en 3D-printonderdelen (hardware), en de digital twin: een virtuele robot en omgeving om concepten en animaties veilig te testen (simulatie).
> Status: `bezig` · Eerst lezen: `CLAUDE.md` en `_config/veiligheid-robot.md`.

## Eén verantwoordelijkheid

Zorgen dat wat de teams bedenken **fysiek past en in simulatie getest is** voor het op de robot gaat. Twee sporen: *hardware* (CAD, behuizingen, houders, prints) en *simulatie* (virtuele Bittle en omgeving). Verdeel ze zelf en leg het vast in een issue. Ze raken elkaar: een behuizing is pas goed als de simulatie toont dat de robot er nog mee loopt.

## Fases

| Fase | Taak | Input | Output | Controle |
|---|---|---|---|---|
| Analyse | begrijpen wat de robot fysiek en virtueel is en wat de grenzen zijn | startpunten hieronder | `analyse/README.md` | elke maat, massa of limiet heeft een bron of staat als `[ONBEKEND]`; het team en de projectmanager lezen na |
| Concept | in elke kandidaat invullen wat het betekent voor ontwerp en simulatie | `concept/kandidaten/` | rij "t2-hw-sim" in de tabel "Per team" van elke kandidaat | geen bewering over wat past zonder bron of proef |
| Prototype | bouwen en testen, in simulatie eerst | `concept/concept.md` (bestaat pas na het consult), `SYSTEEM.md` | `prototype/<onderdeel>/README.md` en bestanden | pull request goedgekeurd; test staat in `LOGBOEK.md` |
| Oplevering | beeld en film van het werk | `prototype/` | bijdrage aan `oplevering/` | past bij wat het prototype toont |

## Startpunten

Zoek via `shared/INDEX.md`; hieronder wat je als eerste opent.

| Spoor | Open | Waarom |
|---|---|---|
| Hardware | `shared/bronnen/petoi/bittle-x-technische-specs.md` | afmetingen en gewicht; let op de kanttekening in `shared/bronnen/links.md` over de CPU |
| Hardware | `shared/bronnen/petoi/assembly-frame.md`, `shared/bronnen/repos/noncodefiles-stl.md` | het frame en de bestaande STL-bestanden |
| Hardware | `shared/bronnen/petoi/blog-3d-geprinte-accessoires.md` | wat anderen printten |
| Simulatie | `shared/vorige-jaren/Bittle_URDF-main.zip` | het URDF zelf met de meshes; pak uit in `lokaal/`, nooit in een gevolgde map |
| Simulatie | `shared/bronnen/repos/bittle-urdf-ua-tdd.md`, `.../bittle-urdf-aiwintermuteai.md` | de README van het model (met fouten, zie hieronder) |
| Simulatie | `shared/bronnen/simulatie/pybullet-bullet3.md` | de simulator |
| Simulatie | `shared/bronnen/simulatie/sw-urdf-exporter.md`, `.../fusion2urdf.md` | CAD naar URDF, voor eigen onderdelen |
| Simulatie | `shared/bronnen/petoi/bittle-x-simulator.md` | wat Petoi zelf biedt |
| Beide | `shared/vorige-jaren/README.md`, secties `Bittle_URDF` en `2025_Groep_1` | wat vorig jaar wel en niet lukte (technisch; geen bron van ideeën) |

## Wat al bekend is over het URDF-model

Uit de zip gelezen op 2026-10-14; niet op een robot nagekeken, dus `nog-onbevestigd` (`SYSTEEM.md`).

- `urdf/bittle.urdf` heeft 12 joints: 8 `revolute` (schouders en knieën) en 4 `fixed`. **Geen kop of staart.** De firmware kent bij Bittle 9 DOF; hoe jullie het ontbrekende hoofdgewricht behandelen (weglaten of toevoegen) is nog `[ONBEKEND]`: maak er een issue van.
- De README van die repo noemt `urdf/bittle_x.urdf` en `simulation/test_bittle.py`; die bestaan niet in de zip. Het echte bestand is `bittle.urdf`.
- De index van een joint in PyBullet is niet het servonummer van de robot (zie `SYSTEEM.md`, rij Gewrichten). Een mapping stellen jullie op en laten jullie controleren door `t1-elektronica`.
- Massa's, inertie en servokoppel zijn niet gecontroleerd `[ONBEKEND]`. De simulatie bewijst dus pas iets over het echte gedrag nadat jullie dat gemeten hebben.
- Licentie GPL-3.0: beslis als team wat jullie met afgeleide bestanden doen (`BESLUITEN.md`, open keuze 12).

## Eerste taken

Onafhankelijk van welk concept gekozen wordt. Taken met de robot doet een mens (`CLAUDE.md`, regel 11).

1. Het URDF laden in PyBullet, alle joints uitlezen en één joint bewegen. Pak de zip uit naar `lokaal/urdf/` en werk met een venv in `lokaal/venv/`. Python-versie en of `pip install pybullet` op jouw computer lukt: `[ONBEKEND]`, noteer wat werkte in `analyse/README.md`. Zonder scherm kun je PyBullet headless starten (`p.DIRECT`). Het script komt in `prototype/sim-urdf-test/` met een `README.md`; de bevindingen (joints, limieten, wat ontbreekt) komen in `analyse/README.md`. Let op: de README van het model noemt verkeerde bestandsnamen (zie hierboven); het pad in de meshes is relatief, dus verplaats mappen niet.
2. De mapping tussen PyBullet-joint en servonummer opstellen. Zoek eerst in `shared/bronnen/petoi-docs/` en in de firmware (`shared/bronnen/petoi-docs/serial-protocol.md`, de OpenCat-zip) welk nummer bij welke schouder of knie hoort; staat het er niet, schrijf `[ONBEKEND]`. Zet de mapping in `prototype/joint-mapping/mapping.md` en open een issue met het label `el`, zodat `t1-elektronica` ze controleert in de pull request.
3. Samen met de robotmanager meten hoe groot en hoe zwaar de echte Bittle X is, met batterij en zonder.
4. Een eenvoudige testomgeving in simulatie: vlakke ondergrond en één obstakel. Aannames als `[ONBEKEND]` markeren.
5. Kiezen welk CAD-pakket en of Git LFS (`BESLUITEN.md`, open keuzes 8 en 9).

## Werken met bestanden

- CAD-bron (SolidWorks of Fusion) blijft in `lokaal/` zolang ze groot of nog werkversie is. Wat gedeeld wordt: een export (STEP en STL) plus een `README.md` met materiaal, maten, printinstellingen en welke versie de definitieve is. Versies zitten in Git; geen `TRAP_NIEUW` naast `TRAP 2`.
- Bestanden boven 50 MB niet committen (`_config/git-werkwijze.md`).
- Simulatiecode: scripts met een `README.md` die zegt hoe je het draait (Python-versie, installatie, startcommando) en wat het aantoont.
- Een afwijking van de afspraken met `t1-elektronica` (maten, ruimte) zet je in `SYSTEEM.md`, tabel "Afspraken tussen teams".
- Branchnamen: `hw/...` en `sim/...`.

## Op de robot werken

Voor je de robot aanraakt: neutrale startpositie, juiste firmware, batterij eruit na gebruik: `_config/veiligheid-robot.md`. Vraag de robot aan de robotmanager en schrijf elke sessie in `LOGBOEK.md`.

## Klaar wanneer

Elk onderdeel heeft een `README.md` met wat het is, hoe je het gebruikt of print, hoe het getest is en wat nog onbekend is. Zonder dat telt het niet (`CLAUDE.md`, regel 6).
