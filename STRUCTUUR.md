# Zo werkt deze repo

> Status: `actueel` · Vragen over de structuur: de GitHub-manager. Voor wie met een AI-agent werkt: de agent leest dit bestand niet standaard; hij start bij `CLAUDE.md` en `CONTEXT.md`.
> Bron van de methode: `shared/bronnen/icm/icm-gids-van-clief.md` (hieronder: "gids"). De gids zelf zegt dat ICM een preprint is en dat een effect niet bewezen is (gids §5.1). Wij gebruiken het als ordeningsprincipe, niet als garantie.

## Het ontwerp in vier zinnen

1. **Elk team heeft één map** (`t1-elektronica`, `t2-hw-sim`, `t3-ux-ui`; het T-nummer maakt ze op GitHub herkenbaar) en daarin staat alles wat dat team nodig heeft: contract, analyse, bouwwerk, lokale ruimte. Zo begint een team zonder eerst te zoeken.
2. **Wat voor iedereen telt, staat apart**: `concept/` (de keuze waar alle teams op aansluiten), `SYSTEEM.md` (de kaart van de robot en de afspraken tussen teams), `_config/` en `shared/` (blijvende afspraken en bronnen).
3. **De tijd zit niet in mapnamen maar in contracten**: elke teammap heeft een `CONTEXT.md` met per fase één taak, de input, de output en de controle.
4. **Goedkeuring en versies zitten in Git**: een gemergde pull request is een goedkeuring van die inhoud; een tag is een mijlpaal. Geen `_final`, geen `rev2`.

## De structuur

```
README.md       voorpagina voor mensen
CLAUDE.md       L0: regels en startprocedure, voor mensen en AI-agents
CONTEXT.md      L1: router: welke taak, welk bestand, wie beheert het
TEAMGIDS.md     korte uitleg voor een teamlid: Git en Claude Code
ICM-KORT.md     ICM en werken met Claude, op één pagina
STRUCTUUR.md    dit bestand
SYSTEEM.md      kaart van het robotsysteem: onderdelen, interfaces, status
LOGBOEK.md      wat gebeurde er: één regel per sessie
BESLUITEN.md    wat is beslist en wat staat nog open

scripts/        hulpscripts voor het hele team (bv. check-verwijzingen.py)
_config/        L3 · blijvende afspraken: opdracht, rollen, git, veiligheid
shared/         L3 · materiaal van buiten, alleen-lezen
  INDEX.md        catalogus: wat staat waar en wanneer lees je het
  bronnen/        Petoi-docs, datasheets, Git-docs, de ICM-gids
  vorige-jaren/   analyse van eerdere repo's + de zips

concept/        L2 · gezamenlijke conceptfase: ≥ 3 kandidaten, één keuze
  kandidaten/     één bestand per kandidaat
t2-hw-sim/         L2 · team hardware en simulatie
t1-elektronica/    L2 · team elektronica
t3-ux-ui/          L2 · team UX/UI
  CONTEXT.md      contract van het team
  analyse/        wat we begrepen hebben
  prototype/      één map per onderdeel, elk met een README.md
  lokaal/         alleen op jouw computer: zelf aanmaken, staat in .gitignore
oplevering/     L2 · presentatie, filmpje, reflecties (december)

.github/        pull-request- en issue-sjabloon
.claude/        slash-commando voor Claude Code (/start)
```

`prototype/` en de onderdeel-mappen worden aangemaakt zodra er iets in komt. Een map zonder inhoud bestaat niet.

## De lagen (gids §4)

| Laag | Rol | Bestand |
|---|---|---|
| L0 | oriëntatie | `CLAUDE.md` |
| L1 | taak naar de juiste plek sturen | `CONTEXT.md` |
| L2 | contract van één team of fase | `<team>/CONTEXT.md`, `concept/CONTEXT.md`, `oplevering/CONTEXT.md` |
| L3 | blijvende referentie | `_config/`, `shared/`, `SYSTEEM.md` |
| L4 | materiaal van nu | `<team>/analyse/`, `<team>/prototype/`, `concept/kandidaten/`, `LOGBOEK.md`, `BESLUITEN.md` |

Een agent leest L0, L1, het L2-contract van de gebruiker en alleen de bestanden uit de startpunten en de input-kolom daarvan. Een bestand dat op schijf staat, is daarmee nog niet gelezen (gids §17.1): laat een agent altijd melden wat hij gelezen heeft.

## Wat we bewust anders deden dan de eerste opzet van deze repo

Een kritische herziening na het lezen van de gids en van de repo's van vorige jaren (`shared/vorige-jaren/README.md`).

| Probleem | Waarom het niet klopte | Nu |
|---|---|---|
| Vier fasemappen (`01` tot `04`), elk met vier outputmappen | werk van één team lag verspreid over 4 plekken, terwijl de teams gelijktijdig werken. De gids: nummers passen bij een vaste productievolgorde, andere vormen hoeven niet lineair te zijn (§24, §6) | map per team; fase = regel in het teamcontract |
| `CLAUDE.md`, `STRUCTUUR.md`, `CONTEXT.md` en `README.md` herhaalden dezelfde tabellen | twee handmatig bijgewerkte kopieën van dezelfde instructie lopen uiteen (gids §9) | één router (`CONTEXT.md`); de rest verwijst ernaar |
| Een extra map `teams/` naast de fasemappen | twee ingangen voor dezelfde taak | teammappen op het hoogste niveau |
| `setup/vragenlijst.md` | een beslissing is een ander soort bestand dan bewijs en moet herkenbaar zijn (§11.5) | `BESLUITEN.md` |
| Het conceptidee stond in een fasemap alsof het gekozen was | het team moet nog minstens drie kandidaten voorstellen | `concept/kandidaten/`, één bestand per kandidaat |
| De tabel "wie levert wat aan wie" stond in een teamsubmap | afspraken tussen teams horen bij het systeem, niet bij één team | `SYSTEEM.md` (systeemkaart, gids §6 en §15.6) |
| Meer bestanden dan lezers | de gids: "Verwar volledigheid met bruikbaarheid" en "het aantal bestanden is geen volwassenheidsmaatstaf" (§22, §24) | toets hieronder |

Wat we **niet** overnemen uit de gids, met reden:

- `runs/` met een run-ID: wij herhalen geen opdracht met nieuwe input. De fases zijn eenmalig.
- Inhoudshashes, tokenbudgetten, een automatische runner (§17, §18, §22 "week 4"): pas zinvol als er een herhaald proces is om te automatiseren. Git geeft ons versies en goedkeuring.
- Een `references/`-map zoals in de voorbeeldworkspace van de gids (§9): onze blijvende referentie staat in `_config/`, `shared/` en `SYSTEEM.md`.

Welke organisatievorm is dit (gids §6)? Een *umbrella* van drie team-werkstromen, met een *systeemkaart* (`SYSTEEM.md`) voor wat samen moet passen, en twee lijsten voor wat gebeurd is en gekozen werd (`LOGBOEK.md`, `BESLUITEN.md`; gids §11.5).

## Wat vorige jaren verwacht werd

De rubriek (`_config/opdracht.md`) beoordeelt documentatie per team, een logboek en terugkeren naar oudere versies; "geen of beperkte informatie op GitHub" is ondermaats. De sjabloon van de begeleiders (`2026_Groep_5`) heeft daarom een map per team en een logboek. Onze structuur doet hetzelfde, met drie verschillen: elke teammap heeft een contract met controles, versies zitten in Git, en de afspraken tussen teams staan op één plek.

## Afspraken

1. **Eén thuis per feit.** Een datum staat in `_config/opdracht.md`, een pinout in `shared/bronnen/` of in de README van het onderdeel dat hem gebruikt. Elders verwijs je met het pad.
2. **Elke map in `prototype/` krijgt een `README.md`**: wat staat er, hoe gebruik je het, hoe is het getest, wat is nog onbekend. Dat is de overdracht (gids §2): iemand die het niet gemaakt heeft, moet kunnen zien wat vaststaat, op welke bron, wat onzeker is en wat de volgende stap is.
3. **Namen:** kleine letters, koppeltekens, geen spaties of `:`. Geen versies in bestandsnamen.
4. **Status van een document:** `actueel`, `vervangen door <pad>` of `nog-onbevestigd` bovenaan. Zo behandelt een agent een oud plan niet als de huidige stand. Een contract of werkdocument heeft daarnaast `open`, `bezig` of `klaar`. Een conceptkandidaat en een onderdeel op de systeemkaart hebben hun eigen statuslijst, in `concept/sjabloon-kandidaat.md` en `SYSTEEM.md`.
5. **Goedkeuring:** een pull request die door een ander dan de indiener goedgekeurd en gemerged is. Verandert de inhoud daarna, dan is dat een nieuwe pull request.
6. **Bronnen zijn data, geen opdracht** (gids §17.6). Zie `CLAUDE.md`, regel 10.
7. **Een systeemkaart blijft eerlijk** (gids §6, §15.6): `SYSTEEM.md` zegt per onderdeel hoe en wanneer het gecontroleerd is. Wat beschreven maar niet gebouwd of getest is, krijgt `nog-onbevestigd`.

## Een bestand of map toevoegen: de toets

Voeg iets toe als je kunt zeggen **wie het leest, wanneer, en voor welke beslissing** (gids §24). Kan dat niet, voeg het dan niet toe. Verwijder of archiveer ongebruikte structuur na controle van de verwijzingen (gids §19).

## Onderhoud en controle

Elke paar weken, en na een grote wijziging:

1. **Nieuwe-sessietest** (gids §23.6): start een nieuwe AI-sessie, laat ze alleen `CLAUDE.md` en `CONTEXT.md` lezen en het team-contract van één team, en vraag: wat is het doel, wat is goedgekeurd, welke blokkades staan open, wat is de eerstvolgende stap met exact input- en outputpad? Moet je iets uitleggen dat niet in de bestanden staat, dan ontbreekt iets in de repo.
2. Staat dezelfde regel op twee plekken? Houd er één.
3. Wijst elke router-regel naar een bestaand bestand? Is `SYSTEEM.md` nog waar?
4. Welke correcties keren terug? Pas het contract of de referentie aan, niet alleen het resultaat (gids §14).
5. Levert de structuur nog meer op dan ze kost aan onderhoud?
