# Draaiboek voor de GitHub-manager

> **Layer 3.** Voor wie `main` bewaakt: pull requests nakijken, mergen, de repo schoon houden. De stappen voor teamleden staan in `_config/git-werkwijze.md`; hier staat wat jij daarbovenop doet.
> Achtergrond: `shared/vorige-jaren/README.md`, sectie "Hoe vorig jaar met Git gewerkt werd".

## Wat vorig jaar misging en wat wij ertegen doen

| Vorig jaar | Bij ons |
|---|---|
| Direct op `main` pushen, vaak via de webinterface | `main` beschermd; alleen via pull request |
| PR zonder beschrijving, zonder review, door de indiener zelf gemerged | PR-template (`.github/pull_request_template.md`); een ander dan de indiener keurt goed |
| Commits als "Add files via upload" of dertig keer "Delete ..." | commitboodschap zegt wat en waarom; bestanden in één commit per onderdeel |
| Bijna geen issues, planning in Miro | issues met het label van het team, aan een projectbord gekoppeld |
| 20 tot 60% van het werk in de laatste dagen | een vast wekelijks merge-moment; pull requests klein houden |
| Persoonlijke forks, gedeelde accounts | iedereen heeft schrijfrechten op de teamrepo en commit met een eigen account |
| Versies in bestandsnamen (`_FINAAL`, `rev2`) | versies in git; een mijlpaal krijgt een tag |
| Lege placeholders en binaire bloat | PR-checklist; `.gitignore`; geen zips |

## Eenmalige set-up

Doe dit voor je de teamgenoten toevoegt. Een vinkje betekent: uitgevoerd én nagekeken in GitHub.

1. **Teamleden uitnodigen** met schrijfrechten (Settings → Collaborators). Ze aanvaarden de mail. Noteer hun GitHub-naam in `_config/rollen.md`.
2. **Branch protection of ruleset op `main`** (Settings → Branches of Rules):
   - pull request vereist voor mergen
   - minstens 1 goedkeuring
   - nieuwe pushes maken een goedkeuring ongeldig
   - geen force-push, geen verwijderen van `main`
   Voor een privérepo hangt beschikbaarheid af van het GitHub-abonnement van de eigenaar `[ONBEKEND]`. Lukt het niet, dan blijft het een afspraak en controleer je de commits op `main` zelf.
3. **Labels** aanmaken, met kleur zodat teams op het bord meteen opvallen: `T1 elektronica` (blauw), `T2 hardware` (oranje), `T3 UX-UI` (groen), `concept`, `docs`, en `blokkade`, `vraag`, `robot-nodig`. De T-nummers staan ook in de mapnamen (`t1-elektronica/`, `t2-hw-sim/`, `t3-ux-ui/`). Branchnamen houden hun korte code (`el/`, `hw/`, `sim/`, `ux/`, zie `_config/git-werkwijze.md`).
4. **Projectbord** (Projects, Kanban) met kolommen `Te doen`, `Bezig`, `Review`, `Klaar`. Link het in `README.md`.
5. **Eerste issues** per team uit `<team>/CONTEXT.md` (sectie "Eerste taken") en `concept/CONTEXT.md` aanmaken, met label.
6. **Taal, publiek of privé en Git LFS** vastleggen in `BESLUITEN.md` (open keuzes), en zet genomen beslissingen als regel in de tabel "Genomen".
7. **Repo-instelling**: "Automatically delete head branches" aan, zodat gemergde branches verdwijnen.
8. **Testen met één echte pull request** van een teamlid voor de anderen beginnen.

## Een pull request nakijken

Bekijk dit in volgorde. Wijs niet af op smaak; vraag aan wat in de checklist staat.

1. **Past het in de structuur?** Staat het werk in de map van het juiste team (`<team>/analyse/` of `<team>/prototype/<onderdeel>/`, of `concept/`) en heeft het onderdeel een `README.md`? Staat niets in `shared/bronnen/`?
2. **Bronnen:** heeft elk technisch gegeven een verwijzing naar een bronbestand, of staat het als `[ONBEKEND]`? Pinnummers, spanningen en afmetingen zonder bron gaan terug.
3. **Versie robot:** alleen Bittle X en BiBoard V1? Bij firmware: controleer in de diff dat de regels bovenaan `OpenCatEsp32.ino` niet veranderd zijn (zie `_config/veiligheid-robot.md`).
4. **Veiligheid:** geen sleutels, wachtwoorden of persoonsgegevens; geen hard-coded wifi of IP; geen `.env`.
5. **Grootte:** geen zips; geen bestanden boven 50 MB. CAD-bron en STL staan naast elkaar met een README, geen vijf varianten zonder uitleg welke de goede is.
6. **AI-gebruik** aangegeven in de PR (CLAUDE.md, regel 9).
7. **Logboek:** is er een regel bij?
8. **Test:** staat er hoe het getest is (robot, simulatie, op papier)?

Goedkeuren: Files changed, Review changes, Approve. Mergen: bij voorkeur "Squash and merge" met een leesbare boodschap, branch verwijderen.

Pull requests van jezelf keurt een ander goed: de projectmanager (Wannes), anders een ander teamlid (`_config/git-werkwijze.md`, afspraak 4).

## Elke week

- Eén vast moment (bv. maandagavond) waarop alle open pull requests behandeld worden.
- Kijk naar het projectbord: staat iets te lang op `Bezig`? Vraag het na.
- Kijk of elk team gecommit heeft. Vorig jaar was de bijdrage zeer ongelijk verdeeld. Elk teamlid moet kunnen laten zien wat het deed (individuele reflectie in `oplevering/`).
- Controleer of `LOGBOEK.md` bijgehouden wordt.

## Wanneer iets misgaat

| Probleem | Wat je doet |
|---|---|
| Merge-conflict | `main` in de branch trekken (`git merge origin/main`), conflict oplossen, push. Nooit een branch van een ander herschrijven |
| Per ongeluk op `main` gepusht | niet forceren. Een `git revert` van de commit, en melden in `LOGBOEK.md` |
| Geheim gecommit | het geheim **meteen intrekken** bij de dienst (verwijderen uit de repo volstaat niet: het staat in de geschiedenis) en melden |
| Te groot bestand gecommit | melden aan het team; Git LFS of een gedeelde map. Herschrijven van de geschiedenis alleen in overleg |
| Wie heeft wat gedaan? | `git log --author`, de GitHub-grafieken en het logboek. Dit is wat de rubriek "terugkeren naar oudere versies" bedoelt |

## Wat je niet doet

- Niemands werk herschrijven (geen rebase of force-push op andermans branch).
- Je eigen pull request goedkeuren of mergen zonder tweede paar ogen.
- Een pull request goedkeuren die je niet gelezen hebt, ook al is hij door een AI-agent gemaakt.
