# CONTEXT.md — routering

> **Layer 1.** Lees dit na `CLAUDE.md`. Het zegt waar een taak thuishoort en welk bestand je opent. Spring gericht; lees niet alles. Dit is de enige router: andere bestanden verwijzen hiernaar.

## Eerst: in welk team zit je?

| Je zit in | Open | Je werkt in |
|---|---|---|
| T1 · `t1-elektronica` | `t1-elektronica/CONTEXT.md` | `t1-elektronica/` |
| T2 · `t2-hw-sim` (hardware en simulatie) | `t2-hw-sim/CONTEXT.md` | `t2-hw-sim/` |
| T3 · `t3-ux-ui` | `t3-ux-ui/CONTEXT.md` | `t3-ux-ui/` |
| je werkt aan het concept (alle teams) | `concept/CONTEXT.md` | `concept/` |
| je beheert de repo (GitHub-manager) | `_config/git-master.md` | |

## Waar gaat wat heen

| Wat je in handen hebt | Waar het heen gaat |
|---|---|
| Analyse van de robot of een onderdeel | `<team>/analyse/README.md` |
| CAD, STL, schema, firmware, app-code, simulatie | `<team>/prototype/<onderdeel>/` met een `README.md` |
| Een conceptidee | `concept/kandidaten/<naam>.md`, volgens `concept/sjabloon-kandidaat.md` |
| Een afspraak tussen teams (commando's, maten, pinout) | `SYSTEEM.md`, tabel "Afspraken tussen teams" |
| Een beslissing, of een open keuze | `BESLUITEN.md` |
| Wat er vandaag gebeurde | `LOGBOEK.md` |
| Presentatie, filmpje, individuele reflectie | `oplevering/` |
| Een officiële doc of link van de begeleiders of Petoi | `shared/bronnen/` + een regel in `shared/bronnen/links.md` + een regel in `shared/INDEX.md` |
| Een afspraak die voor het hele project geldt | `_config/` |
| Grote of lokale bestanden, een eigen `.env`, proefjes | `<team>/lokaal/` (komt niet in git) |
| Een script dat het hele team kan hergebruiken | `scripts/` (CLAUDE.md, regel 13) |
| Een taak die iemand moet doen | GitHub Issues, met het label van het team |

## Wat je leest voor welke taak

| Taak | Lees dit, en niet meer |
|---|---|
| Je eerste dag | `TEAMGIDS.md`, `_config/veiligheid-robot.md`, dan het contract van je team |
| Wanneer moet wat af | `_config/opdracht.md`, sectie Planning |
| Iets opzoeken over de robot of de elektronica | `shared/INDEX.md`, dan het ene bestand dat je nodig hebt |
| Wat past waarop (onderdelen en interfaces) | `SYSTEEM.md` |
| Firmware uploaden | `_config/veiligheid-robot.md`, dan `shared/bronnen/petoi-docs/upload-sketch-biboard.md` |
| Wat deden vorige jaren | `shared/vorige-jaren/README.md` |
| Hoe werk ik met Claude in deze repo (1 pagina) | `ICM-KORT.md` |
| Hoe is de repo opgebouwd, en waarom | `STRUCTUUR.md`; de volledige gids: `shared/bronnen/icm/icm-gids-van-clief.md` (via de sectiekaart in `shared/INDEX.md`) |
| Pull requests nakijken | `_config/git-master.md` |
| Stand van zaken | `LOGBOEK.md`, `BESLUITEN.md`, het projectbord op GitHub |

## Wie beheert wat

| Bestand of map | Beheerder |
|---|---|
| `_config/opdracht.md`, `_config/rollen.md` | projectmanager |
| `_config/git-werkwijze.md`, `_config/git-master.md`, `STRUCTUUR.md`, `TEAMGIDS.md`, `ICM-KORT.md`, `scripts/`, `CONTEXT.md`, `CLAUDE.md`, `README.md`, `.github/`, `.claude/` | GitHub-manager |
| `BESLUITEN.md` | GitHub-manager bewaakt; iedereen stelt voor via een pull request |
| `oplevering/` | het hele team |
| `_config/veiligheid-robot.md` | robotmanager |
| `SYSTEEM.md` | projectmanager, met de teams |
| `<team>/` | het team zelf |
| `concept/` | het hele team |
| `shared/bronnen/` | niemand (alleen-lezen; aanvullen mag via de regel hierboven) |
| `shared/vorige-jaren/README.md`, `shared/INDEX.md` | GitHub-manager |
| `LOGBOEK.md` | iedereen |

Rollen die nog niet verdeeld zijn: `_config/rollen.md`.
