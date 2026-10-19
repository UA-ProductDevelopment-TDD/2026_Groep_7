# Git-werkwijze

> **Layer 3.** Hoe het team samenwerkt in deze repo. Beheerd door de GitHub-manager.
> De elf stappen komen uit de practicumslides 2026-2027 V0.1 ("Git, step by step"). Wat daarna volgt (branchnamen, commitformaat, beschermde `main`) is een voorstel voor het team, geen eis van de docenten.

## De elf stappen uit de slides

| # | Stap | Wie | In VS Code | Commando |
|---|---|---|---|---|
| 0 | Kick-off: afspreken wie wat doet voor iemand code schrijft | hele team | — | — |
| 1 | Repository aanmaken | GitHub-manager | github.com → + → New repository | `gh repo create team-bittle` |
| 2 | Team uitnodigen | GitHub-manager | alleen via de website; teamleden aanvaarden de mail | — |
| 3 | Iedereen een kopie | iedereen | Source Control → Clone Repository | `git clone <url>` |
| 4 | Vertrekken van de laatste versie | teamlid | Sync Changes (of ··· → Pull) | `git pull` |
| 5 | Een branch als veilig zijspoor | teamlid | branchnaam linksonder → Create new branch | `git branch feature/leg-sensor` en `git switch feature/leg-sensor` |
| 6 | Snapshots bewaren | teamlid | bestand stagen met +, boodschap typen, Commit | `git add .` en `git commit -m "Leg sensor"` |
| 7 | Werk uploaden | teamlid | Publish Branch (later Sync Changes) | `git push origin feature/leg-sensor` |
| 8 | Pull request: "please check my work" | teamlid | Create Pull Request-icoon | `gh pr create` |
| 9 | Review | GitHub-manager | github.com → Files changed → Review changes → Approve | `gh pr review --approve` |
| 10 | Mergen in `main` | GitHub-manager | github.com → Merge pull request → Delete branch | `gh pr merge --delete-branch` |
| 11 | Iedereen de nieuwe `main` | iedereen | naar `main` wisselen, Sync Changes | `git switch main` en `git pull` |

Het team gebruikt **GitKraken** (`BESLUITEN.md`, D006); de stappen zijn overal dezelfde: clone, pull, branch, stage, commit, push, pull request. De kolom "In VS Code" blijft als alternatief staan. `gh` is de GitHub CLI; wie die niet heeft, doet dezelfde stap via de website of VS Code.

## Voorstel: afspraken

1. **Branchnamen:** `<subteam>/<korte-omschrijving>`, met als code `hw`, `el`, `ux`, `sim`, `concept` (een conceptkandidaat) of `docs`. Bijvoorbeeld `el/ultrasoon-sensor`. Dat is de vorm `feature/leg-sensor` uit de slides, met het subteam in plaats van `feature`, zodat je op GitHub meteen ziet van wie een branch is.
2. **Commitboodschap:** kort en in de gebiedende wijs, wat en waarom: `voeg afstandssensor toe aan G1 — voor obstakeldetectie`.
3. **`main` is beschermd.** In GitHub: Settings → Branches → branch protection rule op `main`, met "Require a pull request before merging". Dan kan niemand per ongeluk rechtstreeks pushen. Of dit beschikbaar is voor een privérepo hangt af van het GitHub-abonnement van de eigenaar; kijk het na bij het aanmaken. Lukt het niet, dan geldt de regel als afspraak.
4. **Wie reviewt de GitHub-manager?** Op GitHub kan niemand zijn eigen pull request goedkeuren. Pull requests van de GitHub-manager reviewt een ander teamlid: bij voorkeur de projectmanager (Wannes; `BESLUITEN.md`, D005), anders elk ander teamlid.
5. **Klein en vaak.** Eén pull request per afgerond onderdeel, niet één per week.
6. **Issues voor taken.** Elke taak een issue met het label van het subteam; het project board (Kanban) toont de stand.
7. **Eigen branch, eigen account.** Iedereen werkt met een eigen GitHub-account in de teamrepo zelf, geen persoonlijke forks en geen gedeeld account. Dan zie je later wie wat deed (individuele reflectie, rubriek).
8. **Geen webinterface-commits als "Add files via upload".** Dat was vorig jaar de gewoonte en maakt de geschiedenis onleesbaar. Gebruik GitKraken, VS Code of `git` en geef elke commit een boodschap uit afspraak 2. Voor een kleine tekstwijziging mag de webeditor, op een branch en met een echte boodschap.
9. **Elke week mergen, niet vlak voor de deadline.** Vorig jaar viel 20 tot 60% van de commits in de laatste dagen. De GitHub-manager houdt een vast merge-moment (`_config/git-master.md`).
10. **Geen versies in bestandsnamen.** Versies zitten in git; een mijlpaal krijgt een tag.
11. **Zeg het als een AI-agent meewerkte.** In de commit of pull request, bijvoorbeeld: `schrijf URDF-lader — met Claude Code`. Het PR-sjabloon heeft een vakje.
12. **Grote bestanden.** STL en STEP kunnen groot worden. GitHub waarschuwt vanaf 50 MB en weigert bestanden boven 100 MB; beslis als team of jullie Git LFS gebruiken (`BESLUITEN.md`, open keuze 9).

## Voor de GitHub-manager

Set-up, reviewen en mergen: `_config/git-master.md`.

## Hulp

Alle Git- en GitHub-links uit de slides staan in `shared/bronnen/links.md` onder "Git en GitHub".
