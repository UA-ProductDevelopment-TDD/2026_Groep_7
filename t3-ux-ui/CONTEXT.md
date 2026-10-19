# T3 · Team UX/UI

> **Layer 2.** Contract van het team. Wie: zie `_config/rollen.md`. Taken volgens de slides: dashboard of app voor datavisualisatie, programmeerbare scenario's en gebruikersinteractie.
> Status: `bezig` · Een teamlid kan ook GitHub-manager zijn; dat staat los van dit team (`_config/git-master.md`).

## Eén verantwoordelijkheid

Zorgen dat een **gebruiker de robot kan bedienen, begrijpen en vertrouwen**, met een app of dashboard dat eerst in een testmodus werkt en pas daarna met de robot.

## Fases

| Fase | Taak | Input | Output | Controle |
|---|---|---|---|---|
| Analyse | begrijpen hoe de Bittle nu bediend wordt en wat daar wringt | startpunten hieronder | `analyse/README.md` | elke bevinding met schermafbeelding of bron; het team en de projectmanager lezen na |
| Concept | in elke kandidaat invullen wie de gebruiker is, wat die ziet en wat die kan sturen | `concept/kandidaten/` | rij "t3-ux-ui" in de tabel "Per team" van elke kandidaat (gebruiker, wat die ziet, wat die kan sturen) | een bewering over gebruikers zonder gesprek of bron krijgt `[ONBEKEND]` |
| Prototype | app of dashboard bouwen en testen, eerst tegen een testmodus of simulatie, dan tegen de robot | `concept/concept.md` (bestaat pas na het consult), `SYSTEEM.md` | `prototype/<onderdeel>/README.md` en code | pull request goedgekeurd; elke test op de robot staat in `LOGBOEK.md` |
| Oplevering | schermen en demo | `prototype/` | bijdrage aan `oplevering/` | past bij wat het prototype toont |

## Startpunten

Zoek via `shared/INDEX.md`; hieronder wat je als eerste opent.

| Open | Waarom |
|---|---|
| `shared/bronnen/petoi-docs/desktop-app-introduction.md`, `.../mobile-app-introduction.md` | wat Petoi's eigen apps doen |
| `shared/bronnen/petoi-docs/skill-composer.md`, `.../petoi-coding-blocks.md` | bewegingen maken en programmeren |
| `shared/bronnen/petoi-docs/python-api.md`, `.../serial-protocol.md` | hoe een app de robot aanstuurt |
| `shared/bronnen/petoi-docs/voice-command-module.md` | spraak |
| `shared/vorige-jaren/README.md`, secties `Bittle_Studio`, `Bittle_AI_voice`, `2025_Groep_2` | drie bedieningen: wat ze goed deden en waar het misging (techniek en werkwijze; geen bron van ideeën) |

## Wat er te leren valt uit bestaande bedieningen

Uit de agent-analyse; `nog-onbevestigd` tot jullie het zelf geprobeerd hebben.

- **Bittle Link (in Bittle_Studio):** een losse webconsole die rechtstreeks via Web Bluetooth of Web Serial met de robot praat (alleen Chrome of Edge). Goede gewoonten: een testmodus zonder robot, een serial monitor die elk commando in gewone taal uitlegt, een stop-knop op `Esc`, een verplichte controle per servo bij setup. Licentie GPL-3.0: overleg met het team voor je code letterlijk overneemt.
- **Bittle_AI_voice:** spraak naar AI naar robot. Het patroon dat de moeite waard is: de AI mag alleen een beperkte, gevalideerde set acties aanroepen (whitelist, limieten op hoek en duur) met altijd een stop-knop. Nadelen: sleutel in de browser, audio naar een betaalde dienst, geen bevestiging dat een beweging uitgevoerd is.
- **RobotDawg (2025_Groep_2):** alles op één HUD-pagina met een statusbalk voor de BLE-verbinding. Tientallen kopieën van dezelfde HTML-pagina naast elkaar zijn precies wat we niet doen.
- **Wat geen enkele repo had:** een dashboard met telemetrie, meldingen of bediening door iemand die geen techniek kent.

## Eerste taken

Onafhankelijk van welk concept gekozen wordt.

Taken met de robot doet een **mens**; een AI-agent bereidt voor en schrijft op (`CLAUDE.md`, regel 11). De robotmanager is Arno (`_config/rollen.md`).

1. De Petoi Desktop App en de mobiele app zelf uitproberen met de robot erbij (mens); noteer wat verwarrend is, met een schermafbeelding. Output: `analyse/README.md`, sectie "Bestaande bediening".
2. Bittle Link uit `shared/vorige-jaren/Bittle_Studio-master.zip` draaien in testmodus (zonder robot; pak uit in `lokaal/`) en beschrijven welke schermen en commando's er zijn. Output: `analyse/README.md`, sectie "Bestaande bediening".
3. Een manier bedenken om gebruikers te leren kennen voor elke kandidaat: wie, waar, hoe vaak, welke taak. Eerst aannames, gemarkeerd als `[ONBEKEND]`, daarna toetsen met echte mensen. Output: `analyse/README.md`, sectie "Gebruikers (aannames)".
4. Met `t1-elektronica` afspreken welke commando's en waarden de app mag sturen en lezen. Output: `SYSTEEM.md`, tabel "Afspraken tussen teams".
5. Een testmodus kiezen waartegen jullie kunnen werken zonder robot (eigen mock of die van Bittle Link). Output: `analyse/README.md`, sectie "Testmodus".

## Werken met bestanden

- Schermontwerpen als afbeelding (of een link naar het Figma- of Miro-bord in de README) plus uitleg in `prototype/<onderdeel>/README.md`.
- Code: een eigen map in `prototype/`, met een `README.md` die zegt hoe je het installeert, start en test. Geen `node_modules` of build-map in Git (`.gitignore` regelt dat). Geen sleutels in de code: een `.env.example` in de repo.
- Bestandsnamen in kleine letters met koppeltekens, zonder spaties of `:`. Versies zitten in Git, niet in `v2-definitief.html`.
- Een app die de robot bestuurt: altijd een zichtbare stop-knop en een testmodus (`_config/veiligheid-robot.md`). Geen opdrachten die kalibreren of firmware wissen.
- Branchnamen: `ux/...`.

## Vibecoden met Claude Code

Wie met een AI-agent codeert, werkt in kleine stappen, leest wat er geschreven wordt, laat het testen en meldt het in de pull request (`CLAUDE.md`, regel 9). Praktisch: `TEAMGIDS.md`, sectie "Werken met Claude Code". De AI stuurt nooit zelf naar de robot (`CLAUDE.md`, regel 11).

## Klaar wanneer

Elk onderdeel heeft een `README.md` met installatie, gebruik, een schermafbeelding, hoe getest (testmodus, simulatie, robot) en wat nog onbekend is.
