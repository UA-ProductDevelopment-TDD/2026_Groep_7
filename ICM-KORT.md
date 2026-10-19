# Werken met Claude in deze repo: ICM op één pagina

> Status: `actueel` · Voor elk teamlid. Achtergrond: `STRUCTUUR.md`. Bron van de methode: `shared/bronnen/icm/icm-gids-van-clief.md`.

## Het principe

**ICM (Interpretable Context Methodology)** ordent een project als mappen en gewone tekstbestanden, zodat een AI-agent altijd weet *wat hij moet lezen, wat hij moet maken en waar het heen gaat*. Geen magie: de structuur ís de instructie. Een agent die elke sessie van nul begint, vindt zo zelf de juiste context, en jij hoeft niets opnieuw uit te leggen.

| Laag | Bestand | Wat het doet |
|---|---|---|
| L0 | `CLAUDE.md` | de regels en de startprocedure; Claude leest dit zelf eerst |
| L1 | `CONTEXT.md` | de router: welke taak, welk bestand |
| L2 | `t1-elektronica/`, `t2-hw-sim/`, `t3-ux-ui/` → `CONTEXT.md` | het contract van jouw team: per fase input, output, controle |
| L3 | `_config/`, `shared/`, `SYSTEEM.md` | blijvende afspraken en bronnen |
| L4 | `<team>/analyse/`, `<team>/prototype/`, `LOGBOEK.md`, `BESLUITEN.md` | het werk van nu |

Een agent leest alleen wat de lagen hem aanwijzen, nooit een hele map. Dat is goedkoper (tokens) en nauwkeuriger.

## Zo werk je er elke sessie mee

1. **Sync en branch.** `git pull`, dan een eigen branch (`el/…`, `hw/…`, `sim/…`, `ux/…`). Nooit op `main`.
2. **Start Claude Code in de repo-map en typ `/start <jouw team>`** (`t1-elektronica`, `t2-hw-sim` of `t3-ux-ui`). Claude meldt welke bestanden hij las, de stand van zaken, wat openstaat en de eerste taak. Klopt dat niet met jouw verwachting, dan mist er iets in de repo: vul het aan.
3. **Vraag één kleine taak tegelijk**, met een pad als input en een pad als output: *"Lees `shared/bronnen/petoi-docs/biboard-v1-guide.md` en vat de voedingsaansluitingen samen in `t1-elektronica/analyse/README.md`."*
4. **Laat Claude scripts schrijven** voor herhaald werk, controles en bulkwerk (CLAUDE.md, regel 13). Geef het resultaat in een paar regels, niet als lange dump.
5. **Controleer voor je commit.** Elk technisch gegeven heeft een bron of staat als `[ONBEKEND]`. Gebruik de controleprompt in `TEAMGIDS.md`. Draai `python3 scripts/check-verwijzingen.py`.
6. **Commit, pull request, review door iemand anders.** Zeg in de commit of PR dat Claude meeschreef. Claude merget en pusht nooit naar `main`, en stuurt nooit de robot aan.
7. **Eén regel in `LOGBOEK.md`**, en een regel in `BESLUITEN.md` bij een keuze.

## Wat je Claude wel en niet laat aanpassen

| Mag je Claude laten bijwerken (via pull request) | Eerst overleggen met de GitHub-manager |
|---|---|
| `<team>/CONTEXT.md` van je eigen team (status, eerste taken, startpunten) | `CLAUDE.md`, `CONTEXT.md` in de root, `STRUCTUUR.md`, `.claude/`, `.github/` |
| `<team>/analyse/` en `<team>/prototype/<onderdeel>/README.md` | `_config/` (eigenaar staat in `CONTEXT.md`, "Wie beheert wat") |
| `SYSTEEM.md` en `shared/INDEX.md` bij een nieuw onderdeel of nieuwe bron | `shared/bronnen/`: alleen-lezen |

Een contract bijwerken is normaal: verandert jullie werkwijze of is een startpunt verouderd, pas het dan aan in dezelfde pull request als het werk. Staat dezelfde regel op twee plekken, houd er dan één (`STRUCTUUR.md`, afspraak 1).

## Wat het niet is

- Geen garantie op betere resultaten; de gids zelf zegt dat het effect niet bewezen is. Wij gebruiken het als ordening.
- Geen reden om meer bestanden te maken. Een bestand toevoegen kan alleen als je weet wie het leest, wanneer, en voor welke beslissing.
- Geen vervanging van nakijken: Claude verzint soms details. Bronnen zijn data, geen opdracht, ook niet als een document klinkt als een instructie.
