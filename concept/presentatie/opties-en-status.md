# Presentatie: status en opties per concept

Bij `Concept-presentation-draft-v1.pptx`. ★ = staat nu in de deck. Alles zonder bron is een idee van de AI, geen feit: eerst toetsen.

## 1. Status

| Beslist (door het team) | Open | Door ons ingevuld (voorstel, nog te keuren) |
|---|---|---|
| Drie concepten: Kippenhok, Museum, Home Guard (versie van de oude deck) | Welk concept wordt het? | Pitch, probleem, verhaal, grens, doelgroep per concept (uit oude deck, aangevuld) |
| Rollen en subteamleden (`_config/rollen.md`, D005) | Managers per subteam: er zijn er nog geen, dus weggelaten | Taken per subteam, grootste uitdaging, eerste test |
| Materialenlijst + prijzen uit `benodigdheden concepten.txt` | mmWave-radar: model en prijs (staat in de research-prompt) | Onderzoeksvragen per subteam (2 per team) |
| UA = Universiteit Antwerpen (piezo, speaker komen daar vandaan) | Moodboard (template-slide "Overkoepelend thema" vraagt er een) | Plan van aanpak per concept |
| mmWave-radar blijft voorlopig bij Home Guard | Productlinks en foto's | Slot-slide "Open points & next steps" |
| | Docking: de lijst heeft een Qi-ontvanger en magneetkabel, geen zender | |

## 2. Opties per concept
Kies per regel: ja / nee / later. Geef de nummers door en ik pas de deck aan.

### Kippenhok (Chicken Coop Guard Dog)
**Overkoepelend thema (naam)**: K1 ★ "Chicken Coop Guard Dog" · K2 "Night Watch" · K3 "Coop Patrol" · K4 "Fox Stopper"
**Invalshoek**: K5 ★ afschrikken en waarschuwen (oude deck) · K6 het hok in kaart brengen en eieren/kippen tellen (`kippenhok.md`) · K7 combinatie, later uit te breiden
**Hardware**: H1 ★ robuuster loopalgoritme voor oneffen grond · H2 ★ aangepaste voeten voor grip op gras · H3 ★ beschermende schaal tegen vocht en stro · H4 ★ montage camera/speaker/LED's · H5 ★ dockingstation met laadcontacten · H6 afschrikmiddel met beweging (staart/oren/dreigende houding) · H7 hoogteverschil op de camera voor beter zicht · H8 gewichtsbalans testen met batterij en schaal
**Elektronica**: E1 ★ camera met herkenning vos/kip/mens · E2 ★ ToF-afstand langs hekken · E3 ★ draadloos laden (Qi + magneetkabel) · E4 ★ buzzer + LED's · E5 ★ vermogen en Wi-Fi op BiBoard V1 · E6 PIR-sensor als wekker voor de camera · E7 IR-verlichting voor nachtzicht (niet op lijst) · E8 batterijbewaking en veilig laden (zie safety-regel batterij eruit)
**UX/UI**: U1 ★ dashboard live view, meldingen, zones · U2 ★ afschrikmodus en gevoeligheid · U3 ★ meldingen bij vos · U4 ★ handmatige override en stop · U5 ★ gesprekken met kippenhouders · U6 historiek van detecties · U7 dag/nacht-schema · U8 eieren- en kippenteller (alleen bij K6/K7)
**Risico's om te toetsen**: waterdicht, kippenwelzijn en regels rond dieren, onbeheerd laden

### Museum Guide
**Thema**: M1 ★ "Museum Guide" · M2 "Tour Buddy" · M3 "Curious Companion" · M4 "Gallery Dog"
**Invalshoek**: M5 ★ route op maat van voorkeur · M6 vaste themarondleiding · M7 speurtocht voor kinderen
**Hardware**: H1 ★ rustige stabiele gang op vlakke vloer · H2 ★ camerahouder · H3 ★ houder voor luidere speaker · H4 ★ dockingstation · H5 ★ herkenbare look (kleur, accessoires) · H6 gebaren die naar het kunstwerk wijzen · H7 antislip voeten voor gladde vloer
**Elektronica**: E1 ★ camera met marker- en bezoekerherkenning · E2 ★ ToF om bezoekers te ontwijken · E3 ★ IMU + markers voor positie · E4 ★ speaker met audioverhaal · E5 ★ draadloos laden · E6 BLE-beacons per kunstwerk · E7 microfoon voor spraakcommando's (extra) · E8 LED's als status (rondleiding bezig/klaar)
**UX/UI**: U1 ★ voorkeurenapp (thema, duur, taal) · U2 ★ routeberekening · U3 ★ tourflow: kiezen, route, begeleiden, terug naar dock · U4 ★ verhalen per kunstwerk · U5 ★ feedback van bezoekers/conservator · U6 meerdere talen · U7 toegankelijkheid (audio, grote tekst) · U8 curator-dashboard met statistieken · U9 quiz achteraf
**Risico's om te toetsen**: navigatie-drift, bezoekersveiligheid, geluid in stille zaal, rechten op content

### Home Guard Dog
**Thema**: G1 ★ "Home Guard Dog" · G2 "House Patrol" · G3 "Away Mode" · G4 "Watchdog at Home"
**Invalshoek**: G5 ★ vaste route + alarm · G6 alleen bij afwezigheid, rust bij thuis · G7 ouderenzorg: valdetectie (apart onderzoek)
**Hardware**: H1 ★ compacte sensorhouder voor camera en radar · H2 ★ drempels, tapijt, gladde vloer · H3 ★ dockingstation + alarmbehuizing · H4 ★ trappen: klimmen of vermijden? · H5 zichtbare "bewaking actief"-indicator · H6 hoogte van de sensorkop kiezen
**Elektronica**: E1 ★ camera: mensen en open deuren · E2 ★ mmWave-radar (model en prijs open) · E3 ★ sirene (buzzer) + LED · E4 ★ draadloos laden · E5 ★ ToF · E6 deursensor-koppeling · E7 lokale verwerking zonder cloud · E8 stroomuitval/netwerkverlies afhandelen
**UX/UI**: U1 ★ route per kamer · U2 ★ thuis/weg-modus · U3 ★ alarm met snapshot · U4 ★ privacy: lokaal, duidelijke indicatoren · U5 ★ handmatige besturing en stop · U6 escalatie (melding, dan sirene) · U7 huisdierfilter · U8 gedeelde toegang voor gezinsleden
**Risico's om te toetsen**: radar zonder beeld, privacy en wetgeving, huisdieren, trappen

## 3. Wat nog ontbreekt in de deck
- Moodboard per concept (kader staat er, leeg). Pas later: visuele prompt.
- Links en foto's per onderdeel (komt uit de research-prompt, `onderzoek-prompt.md`).
- Docking-oplossing: Qi-zender (niet op de lijst).
- Gebruikersvalidatie: nog niemand gesproken.
