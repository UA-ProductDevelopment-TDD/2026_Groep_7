# Prompt: stijlsysteem en eerste dashboard (voor Codex, Claude Code of een ander agent-model)

> Gebruik: open de agent in de root van de repo (`2026_Groep_7`), plak het blok hieronder. Eerst alleen fase A en B laten doen, bekijken, dan pas C. Maak een branch `ux/stijlsysteem`.
> Gemaakt met Claude Code; de agent die dit uitvoert meldt zijn AI-gebruik in de commit.

```
Je bent een senior product designer en front-end engineer. Je bouwt het stijlsysteem en een eerste klikbaar dashboard voor een studentenproject. Werk in kleine stappen, leg elke keuze kort uit, en verzin niets: ontbreekt een gegeven, schrijf [ONBEKEND].

## Context (lees eerst, in deze volgorde, en niets anders blind)
1. CLAUDE.md en CONTEXT.md (repo-regels; belangrijk: niemand pusht op main, branch ux/..., geen sleutels in code, geen node_modules in Git, bestandsnamen kleine letters met koppeltekens, README per onderdeel).
2. t3-ux-ui/CONTEXT.md (contract van ons team: gebruiker kan de robot bedienen, begrijpen en vertrouwen; testmodus eerst; altijd een zichtbare stop-knop).
3. t3-ux-ui/analyse/onderzoek-synthese.md (wat een vos afschrikt, wat kippen stresseert, markt, bestaande oplossingen). Elke ontwerpkeuze die hierop steunt, citeert het bron-id of de URL uit dat bestand. Gebruik t3-ux-ui/analyse/bronnen/INDEX.md om een bron te vinden; lees grote bronbestanden gericht, niet integraal.
4. t3-ux-ui/analyse/bronnen/dashboard-architectuur-samenvatting.txt (voorbeelden en referenties voor dashboards).
5. _config/veiligheid-robot.md (robotveiligheid: de UI stuurt nooit kalibratie of firmware-opdrachten).

## Het product
Bittle X (Petoi quadruped robothond) patrouilleert 's nachts een vaste ronde rond een kippenhok in Vlaanderen op ruw terrein (gras, modder). Hij herkent vos, kip of mens (ESP32-S3-camera met IR-verlichting), meet afstand tot de omheining (VL53L0X ToF), schakelt over op afschrikmodus (speaker/buzzer en leds) en keert terug naar een dock om te laden (Qi plus magneetkabel).
Toestandsmachine (uit het simulatievoorstel van het team): patrouille -> detectie -> afschrikmodus -> terug naar dock -> laden.
Meetwaarden die de simulatie en later de robot leveren: afwijking van de route, aantal valpartijen, dekking van het hok per ronde, tijd tot herkenning van de vos, valse alarmen, dockingsucces, energieverbruik per ronde.
Gebruiker: kippenhouder of kleine boerderij; geen technische achtergrond, vaak op een telefoon, 's nachts, half wakker, na een melding.
Dashboard volgens ons plan: livebeeld, meldingen, patrouillezones; afschrikmodus en gevoeligheid instellen; melding bij gedetecteerde vos; handmatig ingrijpen en noodstop.

## Visie op de stijl
- Kalm in rust, duidelijk bij alarm. Twee toestanden: "kalm" (alles goed) en "alarm" (vos gedetecteerd), herkenbaar zonder te lezen.
- Glass-stijl: doorschijnende panelen (backdrop-blur) over een achtergrond die een live camerabeeld is, in de prototypefase een stilstaand foto of gegenereerd beeld van een kippenhok bij nacht. Eis: tekstcontrast voldoet aan WCAG AA ook boven een wisselend nachtbeeld (gebruik een donkere scrim of voldoende opaque panelen waar nodig; test dit).
- Eén duidelijke accentkleur en één alarmkleur. Nachtmodus is de standaard; daglicht is een tweede thema.
- Grote tikdoelen (min. 44 px) en een noodstop die altijd zichtbaar is, op elke pagina, op dezelfde plek.
- Geen generieke "AI-look": geen willekeurige gradients, geen stapels identieke kaarten, geen emoji als iconen. Een vaste spacing-schaal (8 px-basis), maximaal 2 lettertypen, maximaal 8 componenten.
- Taal van de interface: Nederlands (Vlaams), korte zinnen, geen jargon (geen "ToF", "BLE" in de hoofdweergave).

## Fase A: stijlsysteem (eerst, nog geen schermen)
Lever in t3-ux-ui/prototype/stijlsysteem/:
- tokens.css (CSS-variabelen: kleur licht/nacht, typografie, spacing, radius, blur, schaduw, motion) en tokens.json met dezelfde waarden.
- stijlgids.html: één statische pagina die tokens en componenten toont (kaart/paneel, statusbadge, meldingsrij, zonekaart, live-tegel, noodknop, gevoeligheidsschuif, tijdlijn), in kalm en alarm, in nacht en dag. Geen framework, geen build-stap.
- README.md: keuzes met motivatie en bron-id, contrastmetingen (tabel: combinatie, verhouding, geslaagd), en wat bewust niet is gedaan.
Toon moodboardlinks of referenties alleen als je ze echt in de bronnen vindt (met licentie); anders [ONBEKEND].

## Fase B: eerste dashboard (klikbaar, testmodus)
Lever in t3-ux-ui/prototype/dashboard/ (statische HTML, CSS en JS zonder build; of Vite als je dat motiveert in de README):
- Schermen: 1) Overzicht (livebeeld als achtergrond, status, batterij, volgende ronde, laatste melding), 2) Melding (snapshot, tijdstip, wat hij herkende, knoppen: "bekijk live", "start afschrikken", "negeer"), 3) Zones en route (kaart van hok en omheiding, patrouillezones aan/uit), 4) Instellingen (afschrikmodus, gevoeligheid, nachtschema), 5) Handmatig (richtingsknoppen, noodstop, terug naar dock).
- Testmodus: een mock-datastroom (mock.js) die de toestandsmachine doorloopt en de meetwaarden hierboven simuleert; schakelaar "Testmodus" zichtbaar. Geen verbinding met een echte robot, geen sleutels. Maak een .env.example als er configuratie is.
- Noodstop doet in de mock "alles stoppen" en toont de bevestiging; echte commando's blijven [ONBEKEND] tot SYSTEEM.md ze vastlegt.
- Toegankelijk: toetsenbord, focusstijlen, aria-labels, reduced-motion respecteren.
- Toon bij elke afschrikinstelling in de UI geen onbewezen belofte; gebruik de bron (bv. gewenning) om willekeur/afwisseling als optie te rechtvaardigen, met een korte uitleg in de README.

## Fase C: opties voor verder (alleen voorstellen, niets bouwen)
Geef max. 8 opties met per optie: wat het toevoegt, inspanning (S/M/L), risico, en welke bron of welk team nodig is. Denk aan: live beeld via ESP32-camerastream, WebSocket of MQTT-koppeling met de simulatie van t2-hw-sim, Bittle Link als referentie, meldingen via push, historiek en statistiek per ronde, weergave van de simulatiemetingen, tweede taal, instelbare "karakter"-stijl van Bittle (afstemmen met Joren).

## Werkwijze en grenzen
- Branch ux/stijlsysteem; commit per fase; vermeld AI-gebruik in elke commit.
- Raak alleen t3-ux-ui/prototype/ en t3-ux-ui/analyse/README.md aan. Niet t1-elektronica, t2-hw-sim of shared/bronnen.
- Stuur nooit iets naar een robot. Geen externe diensten, geen CDN-afhankelijkheden zonder ze te noemen (liever lokaal).
- Controleer je werk: open de pagina's, test mobiel (375 px) en desktop, meet contrast, noteer fouten in de README.
- Eindig met: gelezen bestanden, aangemaakte bestanden, wat nog [ONBEKEND] is, wat je niet kon testen, volgende stap.
```

## Waar de agent zelf moet zoeken (kort)

| Wat | Waar |
|---|---|
| Afschrik- en kipgedrag | `t3-ux-ui/analyse/onderzoek-synthese.md`, daarna bron via `bronnen/INDEX.md` |
| Dashboardvoorbeelden | `bronnen/dashboard-architectuur-samenvatting.txt` |
| Systeemgrenzen en commando's | `SYSTEEM.md`, `_config/veiligheid-robot.md` |
| Simulatiemetingen en toestanden | document van Wannes (staat nog niet in de repo: vraag het hem; zet het in `t2-hw-sim/`) |
