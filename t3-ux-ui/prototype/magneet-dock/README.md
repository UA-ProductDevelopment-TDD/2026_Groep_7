# Magneet-dock v0

Een eerste, zelfgemaakte versie van een laaddock voor de Bittle X: twee 3D-geprinte delen die de robot met magneten en trechters uitlijnen, zodat een gewone USB-C-kabel in de laadpoort van de batterij komt. Bedoeld als test in afwachting van de gekochte magnetische USB-C-kabel (Kuulaa, zie `concept/presentatie/onderzoek-prompt.md`).

Wie: een lid van t3-ux-ui dat aan het laden werkt. Opgesteld met Claude (AI), 2026-11-15.

## Bestanden

| Bestand | Wat |
|---|---|
| `concept-schets-v0.svg` | eerste schets. **Verouderd:** de pennen staan daar boven elkaar en de magneten in de pennen. Het ontwerp in de prompt heeft de pennen naast elkaar, op het robotdeel, en de trechters in het dock. |
| `prompt-3d-model.md` | de prompt voor een ander AI-model dat het OpenSCAD-model en de STL's maakt |

## Ontwerp in het kort

De prompt geeft bewust geen ontwerpmaten, alleen principes. Het andere model kiest de maten en verantwoordt ze.
- **Robotdeel:** zo klein mogelijk, met tape op de batterij, positioneert zichzelf, met **twee pennen naast elkaar** naast de poort en magneten Ø6×4.
- **Dockdeel:** brede trechters (vangen ±15 mm en ±10° op), nauwe trechtergaten voor de pennen, een stekkerhouder met ruimte voor opvulpapier, en trekontlasting voor de kabel.
- **Testcoupon** om eerst de toleranties te kiezen.
- Vaste gegevens in de prompt: de batterij-STL's, de kabel (stekker 7 mm, behuizing 10 × 6 × 18) en de magneten Ø6 × 4.

## Wat we gecontroleerd hebben

**3D-model van de batterij** (gecontroleerd op 2026-11-15, met een wegwerpscript dat doorsneden van de STL's maakt):
- `shared/bronnen/bittle-model/` is Petoi's NonCodeFiles, met in `stl/Bittle & BittleX/` de onderdelen die Petoi voor de Bittle én de Bittle X aanbiedt. Een volledig CAD-model van de robot zit er niet in. De README van Petoi verwijst daarvoor naar hun ROS-model.
- `Bittle_BatteryCase.stl`: 39,5 × 89,8 × 14,1 mm. Met `Bittle_BatteryLid.stl` erop is het geheel ongeveer 16,5 mm hoog. Eén uiteinde is vol (wand ~3,5 mm). Het andere uiteinde is dunner (~8 mm hoog, met een schuine onderkant) en heeft in het midden een **opening van ~9,5 × ~7 mm**: waarschijnlijk voor de laadpoort.
- `Bittle_BatteryTrack.stl` (72 × 97 × 14,6 mm) is de houder in het lijf.
- **Niet bevestigd dat dit de batterij van onze Bittle X is.** De map geldt voor Bittle én Bittle X, maar het gaat om printbare behuizingen. Het deksel toont geen gaten voor de knop of de leds die Petoi bij de Bittle X-batterij beschrijft (`shared/bronnen/petoi/assembly-frame.md`). Vergelijk met de echte batterij: de buitenmaat en waar de poort zit.
- De oudere `battery.obj` uit het URDF (33 × 72 × 13,7 mm) wijkt flink af van de STL. Die gebruiken we niet.

**Laden volgens Petoi** (`shared/bronnen/petoi/bittle-x-technische-specs.md`, `shared/bronnen/petoi-docs/mobile-app-introduction.md`): 7,4 V 1000 mAh, laden met USB 5 V 1 A in ca. 1,5 uur, laadpoort "op één uiteinde van de batterij". Gewicht 269-353 g.

**Kan hij lopen terwijl hij laadt, en zich zo in- of uitpluggen?**
- Of de robot mag werken terwijl de batterij laadt, staat nergens in onze bronnen: `[ONBEKEND]`. Te vragen aan de begeleiders of Petoi, of door een mens te testen volgens `_config/veiligheid-robot.md`.
- Krachten (schatting, niet gemeten). Volgens de USB Type-C-specificatie vraagt een stekker 5-20 N om in te steken en 8-20 N om uit te trekken (niet in `shared/bronnen`). Een robot van ~0,3 kg duwt of trekt door te wandelen hooguit ~1,5-2,8 N. **Met een gewone USB-C-stekker zal hij zich dus waarschijnlijk niet zelf insteken of lostrekken.** De magneten (Ø6×4) helpen pas op de laatste millimeters.
- Daarom is v0 een testopstelling: uitlijnen en vasthouden, en insteken eerst met de hand testen. Mogelijke volgende stappen:
  1. **de gekochte magneetkabel**, die bijna geen insteekkracht vraagt; de geprinte uitlijning blijft bruikbaar,
  2. **een verende stekkerslede** in het dock,
  3. **een afzetrand** om los te komen,
  4. **de magneten zelf als laadcontact** (+ en −, zoals een magneetkabel). Dat is een elektrische aanpassing: alleen na nakijken door t1-elektronica.

## Te meten (een mens, met schuifmaat en foto's)

1. De plaats van de USB-C-poort op de batterij: welk uiteinde (kop of staart), de hoogte boven de onderkant, de verschuiving opzij en hoe diep ze verzonken zit.
2. De werkelijke maten van de batterij (breedte, hoogte) en de plaats van de knop en de leds.
3. De hoogte van het poortmidden boven de vloer als de robot stilstaat.
4. De vrije ruimte tussen de poten aan dat uiteinde (de trechtermond is ~65 mm breed).
5. De kabel zodra hij er is: de stekker en de behuizing.
6. Insteek- en uittrekkracht: duw de stekker met de hand in de batterij terwijl die op een keukenweegschaal ligt, en lees de piek af.

## Openstaand

- **Veiligheid:** regel 8 in `_config/veiligheid-robot.md` zegt "niet onbeheerd opladen". Automatisch laden vraagt een beslissing van de robotmanager en een regel in `BESLUITEN.md`, ook als taak van t1-elektronica (`t1-elektronica/CONTEXT.md`, taak 6).
- `shared/bronnen/bittle-model/` is **~348 MB** (vooral GIF's). Dat is te groot voor git. Volgens `CONTEXT.md` horen grote bestanden in `<team>/lokaal/`. Hou alleen de nodige STL's bij, of zet de map in `.gitignore`. Een bron in `shared/bronnen/` krijgt ook een regel in `links.md` en `INDEX.md` (GitHub-manager).
- De keuze "magneetkabel boven Qi" nog als regel in `BESLUITEN.md` zetten (via een pull request).
- De schets bijwerken naar het ontwerp in de prompt, als dat nodig is voor de presentatie.
