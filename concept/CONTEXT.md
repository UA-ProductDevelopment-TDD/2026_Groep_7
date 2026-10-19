# concept — van kandidaten naar één concept

> **Layer 2.** Contract van de gezamenlijke conceptfase. Alle teams werken hier samen. Data en mijlpalen: `_config/opdracht.md`, sectie Planning.
> Status: `bezig`

## Eén verantwoordelijkheid

Een gekozen concept opleveren dat elk team kan uitwerken, na een eerlijke afweging van **minstens drie eigen kandidaten**. Daarbij hoort per kandidaat wat het per team betekent.

## Stand

| Kandidaat | Bestand | Status | Van wie |
|---|---|---|---|
| A. Kippenhok-robot | `kandidaten/kippenhok.md` | `idee`: eerste schets, nog te toetsen | voorstel van het team bij de start |
| B. | | nog te bedenken | |
| C. | | nog te bedenken | |

Het kippenhok is **onze invulling**, één van de kandidaten, geen gekozen concept. Zolang er geen `concept.md` is, werkt geen team aan één bepaald concept; het werkt aan wat voor elk concept nodig is (zie de eerste taken in de teamcontracten).

## Regels voor kandidaten

1. **Eigen idee.** Een kandidaat komt uit een eigen probleem of gebruiker, niet uit het werk van een vorige groep. `shared/vorige-jaren/README.md` is er om te zien wat technisch lukte en om te vermijden dat we iets herdoen. Een kandidaat die lijkt op een vorige groep, benoemt het verschil.
2. **Eén bestand per kandidaat**, volgens `sjabloon-kandidaat.md`. Daarin staat ook wat het per team (`t2-hw-sim`, `t1-elektronica`, `t3-ux-ui`) betekent en wat we nog niet weten.
3. **Technische beweringen met bron** (`CLAUDE.md`, regel 3). Weet je niet of de Bittle X het kan, schrijf `[ONBEKEND]` en bedenk een kleine proef om het te weten.
4. **Eerlijk over risico.** Elke kandidaat noemt zijn grootste risico en de goedkoopste manier om dat te testen.

## Inputs

| Bron | Plek | Deel | Waarom |
|---|---|---|---|
| Analyses van de teams | `t2-hw-sim/analyse/`, `t1-elektronica/analyse/`, `t3-ux-ui/analyse/` | secties "kansen" en "grenzen" | wat kan de robot, wat niet |
| Opdracht | `_config/opdracht.md` | Opdracht, Evaluatie | mogelijke upgrades en de criteria verkoopbaarheid en innovativiteit |
| Rollen | `_config/rollen.md` | Overkoepelend thema | wat het concept moet bevatten |
| Systeem | `SYSTEEM.md` | onderdelen en status | wat al bestaat |
| Vorige jaren | `shared/vorige-jaren/README.md` | "Wat misging", techniekdelen | wat al geprobeerd werd |

## Process

1. Elk teamlid mag kandidaten voorstellen; zet ze in `kandidaten/` op een eigen branch `concept/<naam>`. Een kandidaat hoeft nog niet af te zijn. De indiener past in dezelfde pull request de tabel "Stand" hierboven aan.
2. Elk team vult in elke kandidaat zijn rij in de tabel "Per team" in: wat betekent het voor ons en wat is de eerste vraag. De indiener vult zijn eigen rij; de andere rijen blijven `[ONBEKEND]` tot dat team eraan toe is.
3. Het team kiest een top 3 voor het consult (of per team, zie `BESLUITEN.md`, open keuze 15). Leg de afweging vast in `BESLUITEN.md`, met de reden en wat ervoor moet gebeuren om het besluit te herzien.
4. Na het consult kiest het team met de begeleiders één concept en werkt het uit tot `concept.md` (naam, verhaal, doelgroep, moodboard, upgrades per team).
5. Splits het gekozen concept in taken per team, als GitHub Issues.

## Outputs

| Artefact | Plek | Formaat |
|---|---|---|
| Kandidaten | `kandidaten/<naam>.md` | markdown, volgens het sjabloon |
| Top 3 en reden | `BESLUITEN.md` | een besluitregel |
| Gekozen concept | `concept.md` | markdown: naam, verhaal, doelgroep, upgrades per team |
| Moodboard | `concept/`, gelinkt vanuit `concept.md` | afbeelding |

## Controle

- Staat bij elke kandidaat voor wie het is en wat de robot erbij doet?
- Heeft elk team zijn rij ingevuld, of staat er `[ONBEKEND]` met een vraag?
- Is elke beweging over de Bittle X ofwel bewezen met een bron ofwel gemarkeerd?
- Is het besluit vastgelegd met reden en herzieningsvoorwaarde?
- Menselijke beoordeling: het team en de begeleiders. Een agent mag voorstellen en samenvatten, niet kiezen.
- Een pull request voor een kandidaat keurt een ander teamlid dan de indiener goed; de GitHub-manager merget (`_config/git-werkwijze.md`, afspraak 4).
