# Wat vorige jaren deden — analyse van de repo's

> Status: `actueel` · Datum: 2026-10-14 · Bron: de zips in deze map (zes repo's plus de OpenCat-firmware), snel doorgelezen door AI-agents (CLAUDE.md, regel 9: AI-gebruik is transparant).
> De GitHub-organisatie `UA-ProductDevelopment-TDD` is publiek bekeken (alleen lezen, uitgelogd). Daar staan 16 repo's: `2025_Groep_1` tot `_5` (gearchiveerd), `2026_Groep_1` tot `_7` (actief, dit jaar), en vier gereedschapsrepo's. `Bittle_Studio`, `Bittle_URDF` en `Bittle_AI_voice` zijn dus geen groepswerk van vorig jaar, maar gereedschap dat de begeleiders in september-oktober 2026 plaatsten; de studentenrepo's zijn `2025_Groep_*` en `2026_Groep_*`.
> Dit is een **snelle** lezing van opbouw en flow, geen review. Wat er niet in stond, staat als `[ONBEKEND]`. Geen enkele zip bevatte een `.git`-map: de commit-, branch- en pull-requestgeschiedenis is dus niet te zien. Controleer dat op GitHub (zie `_config/git-master.md`).

## Waarvoor dit dient

Om te leren **hoe** vorige groepen georganiseerd waren en wat technisch lukte of misging. Niet om een conceptidee over te nemen: ons concept komt uit onze eigen analyse (`CLAUDE.md`, regel 12; `concept/CONTEXT.md`). Waar hieronder "wat we overnemen" staat, gaat het om structuur, werkwijze en techniek.

## In één blik

| Repo | Wat | Omvang | Docs | Wat nemen we mee |
|---|---|---|---|---|
| `2025_Groep_1` | Bittle als performer op een podium: dansjes, camera die skills triggert | 48 bestanden, 4,4 MB | één README met links; alle "Algemeen"-mappen leeg | BLE + AI-camera als patroon; skills als `.md` |
| `2025_Groep_2` | "RobotDawg": Bittle met browser-HUD, radar (3x ToF), AI-camera, schietmechanisme | 49 bestanden, 11 MB | sterke root-README; 2 van 3 submap-docs leeg | root-README met architectuur, protocol, configuratie, "Getting Started" |
| `2026_Groep_5` | leeg sjabloon: `UI TEAM`, `HARDWARE TEAM`, `SOFTWARE TEAM`, `LOGBOEK`, elk één regel | 5 bestanden | geen | alleen het idee: map per team + gedeeld logboek |
| `Bittle_AI_voice` | "Bittle Commander": spraak naar OpenAI Realtime naar robot via Web Bluetooth/Serial | ca. 1000 regels JS, geen dependencies | goede README, eerlijk over wat niet getest is | veiligheidsmodel rond AI-acties, testmodus, tests, CI |
| `Bittle_Studio` | motion-studio: keyframes, PyBullet-simulatie, aparte robotconsole "Bittle Link" | 99 bestanden, 41 MB (38 MB meshes) | README en developer-guide goed | `link.js`, pack-formaat, serial monitor, Test mode, stop-knop |
| `Bittle_URDF` | URDF van de Bittle X voor simulatie | 27 bestanden, 39 MB | README (met fouten) | het model zelf: startpunt voor het simulatie-werk |
| `OpenCatEsp32` | firmware van Petoi (upstream) | 2164 bestanden | MIT | de versiekeuze in `OpenCatEsp32.ino`; pinnen en sensormodules |

## Opbouw en flow per repo

### 2025_Groep_1 — podium en dans

- **Opbouw:** drie mappen per werkgroep (`Behavior team`, `Lijntje`, `Podium team`), geen map per fase. De rollen HW / ELA / UX-UI staan alleen in de README.
- **Flow:** niet af te lezen. Waarschijnlijk zat het denkwerk in een Miro-bord en een presentatie buiten de repo `[ONBEKEND]`; de PowerPoint in de repo is een bestand van 13 bytes.
- **Techniek:** een XIAO ESP32S3 met Seeed AI-camera verbindt via BLE (Nordic UART) met de Bittle X en stuurt een Petoi-skill als de detectiescore boven 80 komt. Dansen zijn Petoi-skill-exports als `.md`.
- **Wat misging:** lege placeholders, geen README per map, CAD-varianten (`TRAP`, `TRAP 2/3/4`, `TRAP_NIEUW`) zonder aanduiding welke de definitieve is, 4 MB CAD-binaries in git, geen logboek.

### 2025_Groep_2 — RobotDawg

- **Opbouw:** `ELA/`, `Hardware/`, `UI:UX/`, en een root-README met systeemoverzicht. Revisies als `rev1`, `rev2` naast elkaar in plaats van in de git-geschiedenis (18 bijna-identieke HTML-bestanden, tot `_FINAAL`).
- **Flow:** eerst losse testpagina's (`test2`, `AItest_1-4`), daarna integratie in één browserpagina. Subteams koppelen via één protocol (BLE-UART) dat in de README staat.
- **Techniek:** Web Bluetooth naar twee BLE-apparaten, scanner met 3x VL53L0X ToF op een servo, XIAO ESP32-S3 met Grove Vision AI v2, aangepaste STL-delen.
- **Sterk:** de README: architectuur, protocol, waar je IP en UUID aanpast, genummerde "Getting Started".
- **Wat misging:** `HW.md` en `AI_vision.md` zijn placeholders, een `:` in de mapnaam `UI:UX` (breekt op Windows), bestanden zonder extensie, een hard-coded IP, een ontbrekende camera-sketch (README niet reproduceerbaar), geen BOM, schema of testverslag.

### 2026_Groep_5 — leeg sjabloon

Vijf bestanden met elk alleen `# 2026_Groep_5`. Het is de kale startstructuur (GitHub Classroom of een eerste commit; herkomst `[ONBEKEND]`). Het laat zien wat het sjabloon van de begeleiders vraagt: een map per team plus een logboek. Spaties en hoofdletters in mapnamen (`UI TEAM`) vermijden we.

### Bittle_AI_voice — spraakbesturing

- **Architectuur:** microfoon of tekst, dan een WebRTC-verbinding met OpenAI Realtime, dan function calls ("acties", "gebaren", "scènes"), dan lokale validatie, dan OpenCat-commando's naar de robot via BLE (20 bytes per pakket) of USB (115200 baud).
- **Veiligheid:** elke AI-aanroep gaat langs een whitelist met limieten op hoek en duur; geen kalibratie of firmware-reset via de AI; stopknop; sessielimiet. Er is een testmodus zonder hardware.
- **Dev-workflow:** één GitHub Actions-bestand (test, bouw, deploy naar GitHub Pages bij een push op `main`). Geen CLAUDE.md, geen issue- of PR-templates, geen CODEOWNERS.
- **Zwak:** de live flow is volgens de README zelf niet getest met een echte sleutel; de API-sleutel zit in de browser (BYOK); audio gaat naar een betaalde externe dienst; de robot geeft geen bevestiging dat een beweging uitgevoerd is.

### Bittle_Studio — motion-studio en robotconsole

- **Opbouw:** `app/` (Python FastAPI + PyBullet + three.js), `app/web/bittle-link/` (de losse robotconsole, vanilla JS, geen build), `launchers/` per besturingssysteem, `saved-motions/`, `docs/developer-guide.md`, `robot-models/bittle/` (38 MB meshes).
- **Flow voor de gebruiker:** simuleren, bewegingen ontwerpen, naar de robot sturen. Dockbare panelen, donker thema met één accentkleur (`#c0e581`), een serial monitor die elk commando uitlegt, Test mode zonder robot, een stop-knop (`Esc`), verplichte "Verified" per servo bij setup.
- **Licentie:** GPL-3.0, het robotmodel heeft een eigen licentie en bron (`SOURCE.md`). Overleg voor je code letterlijk overneemt.
- **Zwak voor ons:** geen sensoren, geen telling, geen navigatie, geen dashboard met telemetrie. Het is een motion-studio, geen toepassing.

### Bittle_URDF — het simulatiemodel

Gecontroleerd in de bron: `urdf/bittle.urdf` heeft 12 joints, waarvan 8 `revolute` (4 schouders, 4 knieën) en 4 `fixed` (batterij, cover, IMU, hoofdbord). **Er zijn geen joints voor kop of staart**: het model beweegt 8 DOF, terwijl de firmware voor Bittle 9 DOF noemt (`#define BITTLE // 1 on head + 8 on leg`). De README verwijst naar `urdf/bittle_x.urdf` en `simulation/test_bittle.py`; **beide bestaan niet** in de zip. Alle gewrichten hebben dezelfde `effort` en `velocity` (waarschijnlijk niet gemeten `[ONBEKEND]`). De PyBullet-jointindex is niet het servonummer van de robot; een mapping ontbreekt. Het gewicht komt door fijne OBJ-meshes (`base_frame.obj` 13 MB).

### OpenCatEsp32 — de versiekeuze

Gecontroleerd in `OpenCatEsp32.ino`: de bestandskop staat nu correct voor ons: `#define BITTLE` actief (`NYBBLE`, `VT`, `CUB`, `MINI` uit), `#define BiBoard_V1_0` actief (`BiBoard_V0_1`, `BiBoard_V0_2`, `BiBoard2` uit), `ROBOT_ARM` uit, `AUTO_INIT` uit. Elke andere combinatie geeft andere servopinnen en andere skills, en kan de robot onbruikbaar maken (zie `_config/veiligheid-robot.md`). Voor wie de details wil: pinnen staan in `src/OpenCat.h`, de skills in `src/InstinctBittleESP.h`, en `ModuleTests/` bevat testschetsen per module.

Volgens de agent-analyse, nog te controleren in de bron `nog-onbevestigd`:

- `RevDE` is gekozen (`RevB` uit); dat bepaalt de pin voor de batterijmeting. Welke revisie onze fysieke BiBoard heeft is `[ONBEKEND]`: eerst nakijken.
- Het token `!` wist de kalibratie en `AUTO_INIT` doet dat zonder vraag: laat die staan.
- Sensormodules in de firmware die voor een concept met sensoren relevant zijn: ultrasoon, camera (Mu), IR-afstand, PIR, touch, licht, gesture, spraak. Een weer- of kippensensor is er niet.
- Deze zip mist `Applications/`, `serialMaster/`, `pyUI/` en `docs/`.

## Hoe vorig jaar met Git gewerkt werd

Bron: publieke pagina's van de organisatie, uitgelogd bekeken; instellingen als branch protection zijn zo niet te zien `[ONBEKEND]`. Een samenvattende webtool is gebruikt, dus aantallen zijn indicatief `nog-onbevestigd`.

| Onderdeel | Wat we zagen |
|---|---|
| Pull requests | vrijwel geen: 5 in de vijf 2025-repo's samen, 0 in de gereedschapsrepo's en in de 2026-repo's die we bekeken. Geen enkele had een beschrijving, een review, een label of een assignee |
| Goedkeuring | een PR werd door de indiener zelf gemerged; in één geval merged een andere persoon dezelfde dag, ook zonder review |
| Branches | bijna alleen `main`; een enkele branch uit de webeditor of een persoonlijke fork |
| Commits | direct op `main`, vaak via de webinterface: "Add files via upload", dertig losse "Delete ..."-commits, geen conventie, geen verwijzing naar issues |
| Issues en borden | één of twee per repo, geen projectbord; planning stond in Miro |
| Ritme | pieken vlak voor de deadline: 20 tot 60% van de commits in de laatste dagen (9-14 jan 2026) |
| Bijdragen | zeer ongelijk verdeeld; soms een gedeeld account, wat individuele bijdragen onzichtbaar maakt |
| CI | alleen in de gereedschapsrepo's (`pages.yml`, tests) |

De rubriek van het vak zegt dat te weinig GitHub-informatie ondermaats is en dat terugkeren naar oudere versies aanvaardbaar is (`_config/opdracht.md`). Vorig jaar haalde dus niemand de versiegeschiedenis echt uit. Wat wij daaruit halen staat in `_config/git-master.md`.

## Wat we over alle repo's heen zien

**Wat goed werkte**

1. Een root-README die architectuur, protocol, configuratie en opstartstappen geeft (Groep 2, Studio).
2. Eén gedeeld protocol als koppeling tussen de teams: BLE-UART met OpenCat-tekstcommando's (Groep 1, Groep 2, AI_voice, Studio gebruiken allemaal dezelfde route).
3. Een testmodus zonder robot, en een stop-knop (Studio, AI_voice).
4. Kleine testpagina's eerst, dan integratie (Groep 2).
5. Skills en bewegingen als tekstbestanden die je kunt diffen (Groep 1, Studio).

**Wat telkens misging**

1. Lege placeholder-bestanden en lege mappen. Zie `_config/opdracht.md`: "geen of beperkte informatie op GitHub" is ondermaats.
2. Geen logboek, geen testverslag, geen BOM, geen schema's.
3. Versiegeschiedenis in bestandsnamen (`rev2/joysticks2_33.html`, `TRAP_NIEUW`) in plaats van in git.
4. Binaire bloat: CAD, STL, OBJ en zips in git.
5. Naamgeving: spaties, `:`, hoofdletters, een mix van Nederlands en Engels, bestanden zonder extensie.
6. Niemand schreef de interface tussen de teams op (maten, pinout, commando's).
7. Geen simulatie in de twee 2025-repo's; geen enkele repo ging over een dier of een binnen- of buitenruimte met een vaste taak voor de robot `nog-onbevestigd`.
8. Geen enkele repo had issues-templates, PR-templates of een CLAUDE.md.

## Wat wij ervan overnemen

| Uit | Wat | Waar het bij ons terechtkomt |
|---|---|---|
| Groep 2 | README met architectuur, configuratie, "Getting Started" | verplichte `README.md` per onderdeel in `prototype/` (`STRUCTUUR.md`, "Afspraken") |
| Groep 2, Groep 1 | koppeling via één protocol | `SYSTEEM.md`, tabel "Afspraken tussen teams" |
| Groep 5 | map per team, gedeeld logboek | de drie teammappen en `LOGBOEK.md` |
| AI_voice | AI mag alleen gevalideerde acties doen, testmodus, tests, CI | veiligheidsregel voor AI-code in `CLAUDE.md`; idee voor `t3-ux-ui` |
| Studio | Test mode, stop-knop, pack-formaat, serial monitor | `t3-ux-ui/CONTEXT.md` |
| Groep 1, Groep 2 | BLE + AI-camera, ToF voor afstand | `t1-elektronica/CONTEXT.md` |
| OpenCat | de versiekeuze controleren voor elke upload | `_config/veiligheid-robot.md` (al aanwezig) en `t1-elektronica/CONTEXT.md` |
| URDF | bestaand model als vertrekpunt | `t2-hw-sim/CONTEXT.md` |
| alle | geen placeholders, geen binaire bloat, één taal, kleine letters | `_config/git-werkwijze.md`, `.gitignore`, PR-template |

## Wat we bewust niet overnemen

- Het concept van Groep 2 (schietmechanisme) en de dans-/podiumopzet van Groep 1: ze zijn hun concept; ons concept komt uit onze eigen analyse (`CLAUDE.md`, regel 12).
- Revisies in bestandsnamen. Versies horen in git (branches en commits); wil je een mijlpaal vastzetten, gebruik een tag.
- De OpenAI-sleutel in de browser. Als `t3-ux-ui` spraak of AI-besturing wil, kiest het team zelf hoe de sleutel veilig blijft (CLAUDE.md, regel 8).
- Code letterlijk uit Studio of de URDF (GPL-3.0) zonder eerst als team te beslissen welke licentie wij kiezen.
