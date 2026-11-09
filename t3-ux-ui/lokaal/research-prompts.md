# Research-prompts T3 UX/UI (kippenhok-waakhond)

Gebruik: kopieer het blok "Gedeelde regels" vooraan elke prompt. Model-tip per prompt staat erbij.
Wegwerpbestand (`lokaal/`), niet voor de repo.

## Gedeelde regels (voor elke prompt plakken)

```
Context: studentenproject (UAntwerpen). Een robothond (Petoi Bittle X) patrouilleert 's nachts rond een kippenhok en schrikt vossen af. Focus: Vlaanderen/Belgie, daarna NL/Noordwest-Europa, pas daarna rest van de wereld.
Regels:
- Elke bewering heeft een bron met werkende URL. Geen bron = schrijf "ONBEKEND". Verzin geen cijfers.
- Geef bij elk cijfer: waarde, eenheid, regio, jaar, en of het een meting, schatting of mening is.
- Onderscheid peer-reviewed, officiele instantie, bedrijf/webshop, forum/blog. Zeg welke het zwakst is.
- Tegenstrijdige bronnen: toon beide, kies er geen.
- Afbeeldingen: geef alleen directe afbeeldings-URL's (of de pagina waar ze staan) met licentie; zeg of hergebruik mag. Geen afbeeldingen verzinnen.
- Maximaal 300 woorden samenvatting, geen inleiding, geen herhaling, geen algemeenheden.
Uitvoerformaat (exact):
1. "## Samenvatting" (max 300 woorden, bullets)
2. "## Bevindingen" als markdown-tabel: id | bewering | waarde | eenheid | regio | jaar | bronsoort | bron_titel | bron_url | zekerheid(hoog/middel/laag)
3. "## Afbeeldingen" als tabel: id | wat het toont | image_url | pagina_url | licentie
4. "## Hiaten" (wat je niet vond, welke zoektermen je probeerde)
5. Sluit af met een ```json blok met dezelfde bevindingen als lijst van objecten (zelfde kolomnamen) zodat ik het kan inlezen.
```

---

## P1 · Wat schrikt een vos af? (Elicit / Consensus / Scite: papers)

```
Onderzoek wat de rode vos (Vulpes vulpes) afschrikt of juist niet, met focus op kippenhokken en vee.
Zoek: peer-reviewed studies en rapporten over (a) licht (flits, bewegingsgestuurd, rood/wit/UV), (b) geluid (ultrasoon, alarm, menselijke stem, hondengeblaf, roofdiergeluiden), (c) geur/smaak (menselijke geur, urine van roofdieren, repellents), (d) beweging/aanwezigheid (vogelverschrikker, robot, drone, hond), (e) gewenning: na hoeveel dagen/nachten werkt een afschrikmiddel niet meer, en wat vertraagt gewenning (variatie, willekeur, combinatie).
Geef per afschrikmiddel: effect (sterk/zwak/geen), studiedesign, steekproef, duur, gewenningsdata, en wat het betekent voor een mobiele robot met camera, speaker en led.
Eindig met een rangschikking van de 5 meest belovende prikkels voor een robot, met bewijsniveau.
Zoektermen om te starten: "red fox deterrent livestock", "fox habituation deterrent", "predator deterrent poultry", "nonlethal predator control fox", "fladry fox", "motion-activated deterrent fox".
```

## P2 · Kippen: wat vinden ze eng, en wat niet? (Elicit / Consensus)

```
Onderzoek het gedrag en de stressreacties van hennen (Gallus gallus domesticus) op prikkels, met het oog op een robot die rond het hok loopt.
Zoek: (a) wat veroorzaakt paniek/angstreacties (geluid in dB en frequentie, plotse beweging, schaduw van roofvogel, felle of flitsend licht, onbekende objecten, robots/drones), (b) wat ze als normaal ervaren (mens, vaste routine, trage beweging, bepaalde kleuren/geluiden), (c) invloed van stress op leggen (eierproductie, sterfte, verstikking door samendringen), (d) gewenning aan robots of voertuigen in stallen (bestaande studies met robots in pluimveehuizen), (e) nachtgedrag: slaaphouding, hoe gevoelig voor licht/geluid 's nachts, wat verstoort slaap.
Geef concrete drempelwaarden (dB, lux, snelheid, afstand) waar de bron ze geeft, anders ONBEKEND.
Eindig met "ontwerpregels voor de robot": 5 do's en 5 don'ts, elk met bron.
Zoektermen: "laying hens fear response robot", "poultry house robot welfare", "hen stress noise dB", "chicken fear drone", "hen night disturbance light", "tonic immobility predator".
```

## P3 · Predatie en schade in Vlaanderen (algemeen model met web: Deep Research / Claude / OpenAI)

```
Breng predatie en andere verliezen in kleine kippenhouderijen in kaart, met voorrang op Vlaanderen en Belgie.
Zoek cijfers en bronnen over: (a) aantal en aandeel kippen gedood of meegenomen door vos, marter (steenmarter), roofvogels, hond/kat, (b) andere verliesoorzaken: ratten en muizen (eieren, voer, ziekte), wezel/bunzing, ziekten, (c) seizoenspatroon: wanneer vossen het meest op kippen jagen (jongen grootbrengen, winter) en op welk uur van de nacht, (d) verschil per predator: vos vs steenmarter vs bunzing vs rat (hoe ze binnenkomen, wat ze doen, sporen), (e) aantal vossen/marters in Vlaanderen (trend), meldingen bij Natuur en Bos, INBO, Departement Omgeving, jagers- en pluimveeorganisaties, (f) wettelijke context: wat mag een hobbyhouder in Vlaanderen doen tegen vossen (afschrikken, vangen, schieten)?
Start bij: INBO, Agentschap Natuur en Bos, Departement Landbouw en Visserij, Statbel, Natuurpunt, Hubertus Vereniging Vlaanderen, Vlaamse hobbypluimvee-organisaties, Boerenbond; ga daarna naar NL (Sovon, Zoogdiervereniging, WUR) en UK (Game & Wildlife Conservation Trust).
Als er geen Vlaamse cijfers zijn: zeg dat expliciet en geef het dichtstbijzijnde vergelijkbare cijfer met regio.
Voeg een tabel "Problemen op een rij" toe: probleem | oorzaak | frequentie/ernst | bron | kan een robot dit oplossen? (ja/deels/nee).
```

## P4 · Marktcontext kippenhokken en kippenhouders (algemeen model met web)

```
Geef een marktbeeld van kippenhokken voor hobby- en kleine houders in Belgie/Vlaanderen.
Zoek: (a) aantal huishoudens/hobbyhouders met kippen en gemiddeld aantal kippen per houder (Statbel, Departement Landbouw, Sanitel/FAVV-registratie, pluimveeorganisaties, enquetes), (b) types hokken (houten hok op poten, kippenren met omheining, mobiel hok/kippentractor, ingegraven gaas, volledig overdekte ren, automatische poortjes) met prijsbereik, typische afmetingen, marktaandeel indien bekend, en populaire webshops/merken in BE/NL, (c) eierproductie: gemiddelde eieren per kip per jaar, welke maanden de piek en het dal zijn (daglicht), (d) hoeveel houders zelf bouwen (indien cijfers), (e) wat houders zeggen dat hun grootste problemen zijn (forums, enquetes, Reddit, Facebook-groepen: citeer max 1 korte zin en geef de link), (f) wat ze willen uitgeven aan bescherming.
Geef bij schattingen zonder bron expliciet "ONBEKEND" en geef een redelijke bandbreedte pas als aparte rij gemarkeerd als "eigen schatting".
Voeg een tabel "Hoktypes" toe: type | typische prijs | kwetsbaarheid voor vos/marter/rat | past een Bittle-ronde erbij? | bron | foto-URL.
```

## P5 · Bestaande oplossingen tegen vossen (algemeen model met web)

```
Inventariseer bestaande oplossingen om kippen 's nachts te beschermen tegen vos en marter, en vergelijk ze.
Categorieen: automatische hokpoortjes (lichtsensor/timer; bv. merken in BE/NL/DE/UK), elektrische omheining/schrikdraad, ingegraven gaas/rok, volledig overdekte ren, licht- en geluidsafschrikkers (bv. Nite Guard, ultrasoon, bewegingsgestuurde sirene, vossenverschrikkers), camerabewaking met melding (wildcamera's, slimme camera's), robot/drone-oplossingen, hond/lama/ezel als bewaker, en de "ik breng ze zelf binnen"-aanpak.
Per oplossing: werking, prijs (aankoop + jaarlijks), onderhoud, bewezen effect (met bron of "geen bewijs"), zwakke punten (gewenning, storm, stroomuitval, marter die toch binnenraakt), en of het een robot overbodig maakt of aanvult.
Concreet: wat is de goedkoopste combinatie die vossen echt tegenhoudt, en wat blijft er over waar een robot echt meerwaarde heeft? Wees eerlijk als het antwoord "niets" is.
Geef productfoto-URL's met licentie, en prijslinks van BE/NL-webshops.
Voeg tabel toe: oplossing | prijs | bewijs | zwakte | aanvulling door robot (ja/nee/deels) | bron | afbeelding.
```

## P6 · Dashboard-voorbeelden en stijlsysteem (algemeen model met web + GitHub)

```
Zoek referenties om een dashboard/app voor een bewakingsrobot (livebeeld, meldingen, patrouillezones, modus, noodstop) te ontwerpen, en stel een vast stijlsysteem voor.
Zoek: (a) apps voor huis- en hokbewaking (Ring, Arlo, Nest, Reolink, Eufy, Frigate, Home Assistant-dashboards), robotbesturing (Petoi-app, Spot/Boston Dynamics, Unitree, Roborock/robotstofzuigers, ROS-webinterfaces zoals Foxglove, Rerun, Webviz), en landbouw/agri-interfaces (precision-farming dashboards, melkrobot-apps, FarmBot, John Deere Operations Center) met screenshots (URL + licentie), (b) wat werkt: welke 5 schermen/elementen komen overal terug en in welke volgorde, welke info boven de vouw, hoe worden meldingen en nooduitschakeling getoond, (c) de trend "glass UI" (doorschijnende panelen over een live-camerabeeld of foto): voorbeelden, leesbaarheid/contrast-eisen (WCAG), valkuilen in donkere nachtbeelden, (d) concrete GitHub-repositories met open-source dashboards of UI-kits die we kunnen bestuderen of hergebruiken (met licentie, laatste commit, sterren; liefst Frigate, Home Assistant-kaarten, Foxglove, shadcn/ui, Tremor, Tailwind-glass-voorbeelden), (e) reverse-engineeringvoorbeelden van interfaces voor thuisgebruik (hoe leer je een bestaande app na te bouwen: schermen in kaart brengen, componenten isoleren; wat is legaal).
Eindig met een voorstel voor een compact stijlsysteem: kleurtokens (licht + donker/nacht), typografie, 8 basiscomponenten (kaart, statusbadge, meldingsrij, zonekaart, live-tegel, grote noodknop, schuif voor gevoeligheid, tijdlijn), icoonset, en regels voor 'kalm' versus 'alarm' state. Geef elke keuze met referentie en korte motivatie.
Geef 15 screenshot-/moodboardlinks met licentie, gesorteerd per thema.
```

## P7 · AI-gestuurd interface bouwen (algemeen model met web + GitHub)

```
Onderzoek hoe je met een AI-codeermodel (Claude Code, Cursor, v0, Lovable, Bolt) een mooie en consistente interface bouwt, voor een studententeam dat in Git samenwerkt.
Zoek: (a) bewezen werkwijzen: design tokens en een DESIGN.md/CLAUDE.md met stijlregels, componentenbibliotheek eerst, schermen laten bouwen vanuit een referentiebeeld, kleine iteraties, (b) vaakgemaakte fouten ("AI-look": generieke gradients, te veel kaarten, inconsistente spacing) en hoe je ze voorkomt, (c) repositories met voorbeelden van goede AI-gebouwde dashboards en stijlgidsen (URL, licentie, tech), (d) hoe je een prototype laat werken zonder robot: mock-datastroom/testmodus, WebSocket- of MQTT-simulatie, (e) minimale techstack voor een snel, offline-bruikbaar dashboard in de browser (statische HTML + JS vs. framework), met voor- en nadelen.
Geef een stappenplan van maximaal 10 stappen om van moodboard naar werkend dashboard te gaan, met per stap het te geven prompttype.
```

---

## Volgorde

1. P3 en P1 (context + onderbouwing van het probleem), tegelijk.
2. P5, P4.
3. P2 (robotregels, voor het ontwerp van de afschrikmodus).
4. P6 en P7 (stijl; los van de rest).

## Verwerken

Resultaten (markdown + json-blok) opslaan als `t3-ux-ui/analyse/bronnen/p<nr>-<onderwerp>.md`. Een script kan de json-blokken samenvoegen tot een CSV voor slides. Zeg het als je dat script wilt.
