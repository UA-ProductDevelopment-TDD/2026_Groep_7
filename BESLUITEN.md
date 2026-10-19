# Besluiten

> Een besluit is een ander soort bestand dan bewijs: bewijs zegt wat bekend is, een besluit zegt wat iemand kiest (ICM-gids §11.5). Zo kan een latere teamgenoot of agent zien dat iets bewust is weggelaten en niet toevallig vergeten. Vervangt `setup/vragenlijst.md`.
> Nieuwe besluiten bovenaan. Elk besluit heeft een herzieningsvoorwaarde.

## Genomen

| ID | Datum | Besluit | Beslisser | Reden | Herzien wanneer |
|---|---|---|---|---|---|
| D007 | 2026-10-19 | Wij zijn **team 7**. De officiële repo is `UA-ProductDevelopment-TDD/2026_Groep_7` (https://github.com/UA-ProductDevelopment-TDD/2026_Groep_7). De inhoud van deze repo verhuist daarheen | Jolan (GitHub-manager), uit de gegevens van de docenten | de repo van de organisatie is degene die beoordeeld wordt | als de docenten een andere repo aanwijzen |
| D006 | 2026-10-19 | Git-programma van het team: **GitKraken** | Jolan (GitHub-manager) | afgesproken voor het team; zelfde stappen als in `_config/git-werkwijze.md` | bij problemen met GitKraken of een andere eis van de begeleiders |
| D005 | 2026-10-19 | Rollenlijst "Teamstructuur" met zes rollen: project Wannes, GitHub Jolan, robot Arno, module Ward, simulation/test Joren, presentatie Ben. Geen technical manager. Pull requests van de GitHub-manager reviewt bij voorkeur de projectmanager. `SYSTEEM.md` valt onder de projectmanager. Teaminfo: GroveKit nr. 8; Bittle-nummer, teamnummer, teamnaam en repo-link `[ONBEKEND]` | Jolan, uit de teaminfo van de docenten | bevestigd door de GitHub-manager | als de docenten de lijst wijzigen of het team rollen wil ruilen |
| D004 | 2026-10-19 | Teams krijgen een T-nummer: T1 `t1-elektronica`, T2 `t2-hw-sim`, T3 `t3-ux-ui` (mapnamen en GitHub-labels). Token-efficiënt werken met scripts is regel 13 in `CLAUDE.md`. `ICM-KORT.md` is de uitleg op één pagina | Jolan (GitHub-manager) | teams en werkwijze zijn zo op GitHub en voor Claude meteen herkenbaar en goedkoper om te lezen | bij een andere teamverdeling |
| D003 | 2026-10-15 | Het kippenhok is **één kandidaat** (`concept/kandidaten/kippenhok.md`), onze eigen invulling. Er komen minstens twee andere kandidaten bij voor het consult | Jolan (GitHub-manager), namens het team | de opdracht vraagt een keuze uit concepten; het concept is nog volop in ontwikkeling | na het consult met de begeleiders |
| D002 | 2026-10-15 | Repo-opbouw: een map per team als basis, met contract (`CONTEXT.md`) per team; gezamenlijke conceptfase en systeemkaart apart; fases als contract in plaats van als mappen. Zie `STRUCTUUR.md` | Jolan | bij de herziening bleek de fase-opzet te verspreid voor parallel werkende teams | als de teamleden na het toevoegen een probleem melden |
| D001 | 2026-10-14 | Drie teams: `t2-hw-sim` (Wannes, Arno), `t1-elektronica` (Ben, Ward), `t3-ux-ui` (Joren, Jolan) | Jolan | verdeling bij de start van de opdracht | bij wijziging van de verdeling |

## Open

Beslissen met het team zodra de teamleden zijn toegevoegd. Elke beslissing die genomen wordt, verhuist naar de tabel hierboven met een ID.

| # | Keuze | Opties of context | Wie beslist |
|---|---|---|---|
| 1 | Een eigen teamnaam (optioneel) | wij zijn team 7 (D007) | team |
| 4 | Gekozen robot | Bittle X is het uitgangspunt van deze repo; de opdracht noemt ook de Sesame Robot. Bevestigen | team |
| 5 | Inhoud overzetten naar `2026_Groep_7` | de GitHub-manager stuurt de mappen op; daarna controleren of alles er staat en deze repo archiveren of verwijzen. Daarna: wie beheert de rechten op de organisatie-repo, en kan `main` daar beschermd worden `[ONBEKEND]` | GitHub-manager met begeleiders |
| 6 | Publiek of privé | de repo's van de organisatie zijn publiek. Bij publiek: beslissen of `shared/bronnen/` meegaat (zie `shared/README.md`) en niets met sleutels of persoonsgegevens in de geschiedenis | team |
| 7 | Taal van de repo | nu Nederlands | team |
| 8 | CAD-pakket van `t2-hw-sim` | SolidWorks, Fusion of ander | `t2-hw-sim` |
| 9 | Git LFS voor grote CAD-bestanden | ja of nee. Zonder LFS: geen bestanden boven 50 MB | team |
| 10 | Waar staan video en grote bestanden buiten Git | een gedeelde map; in de repo komt alleen de link | team |
| 11 | Kanaal voor teamcommunicatie | | team |
| 12 | Licentie van onze eigen code en CAD | de URDF en Bittle_Studio zijn GPL-3.0, Petoi OpenCat is MIT; kiezen voor we code overnemen | team |
| 13 | De zips in `shared/vorige-jaren/` | 35 MB, zitten al in de geschiedenis van `main`. Houden, of later weghalen en alleen de links bewaren | GitHub-manager |
| 14 | Claude Code lokaal | wie heeft het geïnstalleerd en met welk abonnement; zie `TEAMGIDS.md` | team |
| 15 | Top 3 per team of voor het hele team | de slides spreken van "top 3 concepten per subteam"; wij gaan uit van drie kandidaten voor het hele team. Navragen bij de begeleiders | projectmanager |
| 16 | Waterdicht: droge schuur of echt buiten | alleen relevant als het kippenhok in de top 3 komt | team |
| 17 | Wat geldt voor uploadopties en factory reset van de Firmware Uploader voor BiBoard V1 | `_config/veiligheid-robot.md`, regel 6, vraagt dit te laten bevestigen voor iemand uploadt; de workshop is geweest maar het resultaat staat nergens `[ONBEKEND]` | robotmanager (rol nog niet toegewezen) |
| 19 | Welke Bittle en welk nummer | de teaminfo noemt "Bittle 3 #" zonder nummer; de repo gaat uit van Bittle X met BiBoard V1. Bevestigen bij de robotmanager (Arno) voor een upload | robotmanager |
