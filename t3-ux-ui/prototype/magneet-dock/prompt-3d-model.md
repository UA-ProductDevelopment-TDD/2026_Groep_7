# Prompt voor een ander AI-model: magneet-dock v0 voor de Bittle X

> Kopieer alles onder de lijn naar het andere model. Voeg als bijlage toe, uit `shared/bronnen/bittle-model/stl/Bittle & BittleX/`:
> - `Bittle_BatteryCase.stl` en `Bittle_BatteryLid.stl` (de batterij),
> - `Bittle_BatteryTrack.stl` (de houder in het lijf waar de batterij in schuift).
>
> Voeg ook foto's van de echte batterij toe (vooral van het uiteinde met de laadpoort) zodra je ze hebt.
>
> Geschreven met Claude (AI) op 2026-11-15. Waarom de keuzes zo zijn: `README.md` in deze map.

---

## Rol en doel

Je bent een mechanisch ontwerper met ervaring in FDM-3D-printen. Ontwerp een **parametrisch, printklaar** magnetisch dockingsysteem in **OpenSCAD**, waarmee een Petoi Bittle X-robothond (269-353 g volgens Petoi) zijn batterij laadt via een gewone **USB-C-kabel**. De laadpoort zit volgens Petoi "op één uiteinde van de batterij".

Het systeem bestaat uit twee delen die in elkaar klikken:
- een **robotdeel**, klein en licht, dat met **dubbelzijdige tape** op de batterij geplakt wordt, rond de laadpoort;
- een **dockdeel**, dat de USB-C-kabel vasthoudt en op de vloer staat.

Werking: de robot loopt het dock in. Brede trechters vangen hem op en zetten hem recht. **Twee pennen naast elkaar** (horizontaal, links en rechts van de poort) vallen in **twee trechtergaten** en lijnen hem nauwkeurig uit. Magneten trekken de twee delen tegen elkaar, en de stekker zit dan recht in de poort.

## Ontwerpprincipes

1. **Minimaal.** Zo weinig mogelijk materiaal en zo klein mogelijk, vooral het robotdeel: dat loopt mee en mag het lijf, de poten, de knop en de leds van de batterij niet hinderen. Het dockdeel mag groter zijn, maar ook zonder overbodig materiaal.
2. **Eenvoudig te bevestigen met tape.** Het robotdeel heeft een vlak plakvlak voor dubbelzijdige foamtape (VHB) en positioneert zichzelf op de batterij (bijvoorbeeld met lipjes langs de rand of een aanslag tegen het uiteinde), zodat het bij het plakken vanzelf juist zit. De batterij moet uitneembaar blijven.
3. **Eerst uitlijnen, dan insteken.** De pennen moeten al in hun gat zitten voordat de stekker de batterij raakt. De pennen zijn dus langer dan het stuk stekker dat uitsteekt.
4. **Ruime vangst, nauwe eindpositie.** De trechters zijn breed (ze vangen minstens ±15 mm opzij en ±10° scheefstand op; dat is de vangzone waarmee onze simulatie werkt). De pennen zitten in hun gat met weinig speling.
5. **Stevig genoeg.** De verbinding moet het wandelen van de robot en het herhaald in- en uitklikken aankunnen. De kabel krijgt trekontlasting, zodat trekkrachten niet op de stekker of de poort komen.
6. **Magneten eenvoudig te monteren.** Bijvoorbeeld een sleuf waar de magneet in schuift, achter een dun wandje, zodat hij er bij het aantrekken niet uit getrokken kan worden. Vastzetten met een druppel lijm, zonder hitte (neodymium verliest zijn kracht boven ca. 80 °C).
7. **Printbaar zonder support** in een opgegeven oriëntatie: FDM, nozzle 0,4 mm, laag 0,2 mm, overhang ≤ 45°.

## Gegevens

### Batterij: gebruik de STL's, en lees de opmerkingen hieronder

- Batterijmaten en vorm: haal ze uit `Bittle_BatteryCase.stl` en `Bittle_BatteryLid.stl`. Wat wij eruit gemeten hebben (controleer het zelf):
  - de behuizing is ongeveer 39,5 × 89,8 × 14,1 mm, met het deksel ongeveer 16,5 mm hoog;
  - één uiteinde is vol en dik;
  - het andere uiteinde is dunner, met een schuine onderkant, en heeft in het midden een **opening van ongeveer 9,5 mm breed en 7 mm hoog**. Dat is waarschijnlijk de plaats van de laadpoort, maar dat is niet bevestigd.
- **Opgelet:** deze STL's komen uit Petoi's map `Bittle & BittleX` (3D-printbare onderdelen). Het is niet bevestigd dat de batterij van onze Bittle X precies deze vorm heeft. Volgens Petoi heeft de Bittle X-batterij ook een knop en leds, waarvan de plaats niet gekend is. Maak daarom alle maten die met de batterij te maken hebben **parameters**: de buitenmaat, de plaats van de poort, de diepte van de poort en een vrije zone voor de knop en de leds. Neem de STL-waarden als standaard en markeer ze als `[uit STL, te meten]`.
- `Bittle_BatteryTrack.stl` toont waar de batterij in het lijf schuift. Het robotdeel mag niet botsen met die houder of met het lijf.

### USB-C-kabel (opgegeven door de gebruiker; de kabel is er nog niet, dus ontwerp ruim)

- Metalen stekker: 7 mm lang (doorsnede volgens de USB-C-norm).
- Kunststof behuizing achter de stekker: 10 mm breed, 6 mm dik, 18 mm lang.
- Laat rond de behuizing ruimte om op te vullen met papier, zodat dezelfde houder ook voor een iets andere kabel werkt.

### Magneten (opgegeven door de gebruiker)

- Schijfmagneet **Ø6 × 4 mm**, neodymium. Er zijn er minstens 6. Gebruik er zoveel als nodig is voor een goede houdkracht (verdeeld over de twee delen, in tegengestelde paren) en zeg hoeveel.
- Zorg dat de magneten maar op één manier aantrekken (polariteit links en rechts omgekeerd). Leg in de montagestappen uit hoe de gebruiker de polariteit juist krijgt.

## Krachten: wees eerlijk, beloof niet te veel

- Een USB-C-stekker vraagt volgens de USB Type-C-specificatie ongeveer **5-20 N** om in te steken en **8-20 N** om uit te trekken. Die waarden zijn nog niet nagekeken in onze bronnen.
- De robot duwt of trekt door te wandelen naar schatting hooguit **1,5-3 N**. Dat is niet gemeten.
- Automatisch insteken en vooral lostrekken door te wandelen is dus **niet gegarandeerd**. v0 moet zeker **uitlijnen en vasthouden**. Insteken wordt eerst met de hand getest. Een verende stekkerhouder of een flexibele trechter aan de kant van de lader, en een afzetrand om los te komen, zijn een volgende stap: bouw ze niet, maar houd er ruimte voor.
- Maak de houdkracht van de magneten instelbaar, bijvoorbeeld met de dikte van het wandje voor de magneet.

## Harde regels

- **Verzin geen maten.** Wat niet in deze prompt of in de STL's staat, wordt een parameter met een redelijke standaardwaarde, een commentaar met de herkomst, en een `echo()`-waarschuwing als het onzeker is.
- Één `.scad`-bestand, alle parameters bovenaan met Nederlands commentaar, één module per onderdeel, en een keuze `part = "robot" | "dock" | "coupon" | "assemblage"`.
- Minimale wanddikte 1,2 mm, behalve een bewust dun magneetwandje.
- Voeg `assert()`-controles toe voor de kritische punten:
  - de pennen zitten in hun gat voordat de stekker de batterij raakt,
  - de wanden tussen de gaten, de stekkerhouder en de magneetsleuven zijn dik genoeg,
  - het robotdeel botst niet met het lijf of de batterijhouder.

## Op te leveren

1. `magneet_dock.scad`, parametrisch.
2. STL's in printoriëntatie: het robotdeel, het dockdeel (eventueel in 2 stukken, bijvoorbeeld kop en voet, als dat de print eenvoudiger maakt) en een **testcoupon**. De coupon is een klein blokje met een paar gaten met verschillende speling, een korte pen, een magneetsleuf en een stuk van de stekkerhouder, zodat de gebruiker eerst de juiste toleranties kiest. Kun je OpenSCAD niet uitvoeren, zeg dat dan en lever alleen de `.scad`.
3. Een `assemblage`-weergave met de batterij-STL en een spookstekker: gesloten, en ook op 10 mm afstand.
4. Een kort verslag:
   - de gekozen maten en waarom,
   - de **insteekvolgorde** (bij welke afstand de trechters, de pennen en de stekker elk iets raken),
   - de uitkomst van de controles,
   - het gewicht per onderdeel,
   - printinstellingen (PETG aanbevolen) en de printoriëntatie,
   - de montagestappen (tape, magneten, kabel),
   - alles wat nog gemeten moet worden.
