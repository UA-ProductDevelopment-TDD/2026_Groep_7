# Analyse Elektronica

> Status: `bezig` · Werkdocument van team `t1-elektronica` voor de analysefase. Vul in terwijl je leest en test; een deel dat je niet kunt bevestigen, blijft `[ONBEKEND]`.
> Contract: `../CONTEXT.md`. Een technisch gegeven zonder bron hoort hier niet (`CLAUDE.md`, regel 3).

## Vragen om te beantwoorden

- Welke poorten en pinnen heeft de BiBoard V1 vrij, en waarvoor zijn ze bedoeld?
- Wat is de voeding: spanning, stroom, capaciteit, laden?
- Welke sensoren ondersteunt de firmware, op welke poort, en welke werken tegelijk?
- Welke communicatie bestaat (USB, BLE, wifi, IR) en welke commando's zijn er al?
- Hoe upload je firmware veilig, en wat is het herstel als het misgaat?

## Wat we gelezen en getest hebben

| Bron of test | Wat het opleverde | Datum | Wie | Regel in `LOGBOEK.md` |
|---|---|---|---|---|

## Poorten en pinnen

Eén tabel: poort of pin, functie, bron. Pinnummers staan in `src/OpenCat.h` van de firmware-zip; de revisie van het bord: `[ONBEKEND]`.

## Sensoren

Kandidaat-sensoren: wat meet hij, op welke poort, wat kost hij.

## Voeding en laden

Spanning, stroom, capaciteit, laden; wat de veiligheidsregels toelaten.

## Testopstelling

Hoe jullie veilig serieel verbinden, stap voor stap, nagekeken door de robotmanager.

## Interface (voorlopig)

Welke commando's en waarden `t3-ux-ui` mag sturen en lezen.

## Wat de robot kan

Per bevinding een bronverwijzing of een testbeschrijving.

## Grenzen

Wat de robot of de onderdelen niet kunnen, met bron.

## Kansen voor upgrades

Genummerde lijst. Dit is de input voor `concept/`: elke kans verwijst naar iets uit dit document.

## Open vragen

Wat we nog niet weten en wie het uitzoekt.
