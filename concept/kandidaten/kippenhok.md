# Kandidaat: kippenhok-robot

Status: `idee` (eerste schets, nog niet getoetst)
Voorgesteld door: team 01 (via JolanDijkmans) · Datum: 2026-10-14
Dit is **onze eigen invulling** en één van minstens drie kandidaten (`../CONTEXT.md`). Het is geen gekozen concept.

## In één zin
Een Bittle X die rondwandelt in en rond een kippenhok, het hok eerst in kaart brengt en taken uitvoert zoals eieren en kippen tellen, laden bij een laadstation en een deur sluiten.

## Voor wie en welk probleem
Iemand met kippen die elke dag het hok moet controleren, de kippen moet tellen en 's avonds de deur moet sluiten. Of dat een echt probleem is voor een echte gebruiker is nog niet getoetst `[ONBEKEND]`: eerst gesprekken met mensen met kippen.

## Wat doet de robot
- Het hok in kaart brengen: bij de start afwandelen en vastleggen waar ruimte is en wat er staat.
- Een vaste rondgang of controleronde lopen.
- Eieren tellen in de nesten.
- Kippen tellen bij het sluiten van het hok.
- Zelf terug naar een laadstation gaan.
- Een deur sluiten, via een systeem waarvoor de robot sensor of trigger is.

Open: welke sensoren en welke kaart; hoe nauwkeurig een Bittle zijn positie kan schatten; of camerabeelden eieren en kippen betrouwbaar herkennen; of de robot de deur zelf kan sluiten of een apart mechanisme aanstuurt; hoe kippen op een robot reageren. Alles hiervan is `[ONBEKEND]`.

## Wat is nieuw (innovativiteit) en waarom koopt iemand het (verkoopbaarheid)
Nog uit te zoeken: wat bestaande systemen (automatische hokdeuren, hokcamera's) al doen, en wat een lopende robot daarbovenop biedt. Verschil met een vorige groep: geen enkele repo in `shared/vorige-jaren/README.md` ging over dieren of een hok `nog-onbevestigd`.

## Per team
| Team | Wat betekent het voor ons | Eerste vraag |
|---|---|---|
| t2-hw-sim | een beschermende behuizing, een proefhok in simulatie | wat weegt een beschermende schaal en loopt de robot er nog stabiel mee? |
| t1-elektronica | sensoren voor kaart, afstand, eieren en kippen; autonoom laden | welke sensoren, en wat kan de BiBoard V1 aan? |
| t3-ux-ui | gebruiker: iemand met kippen · ziet telling, route, meldingen, batterij · kan handmatig ingrijpen en stoppen | hoe voelt een robot in een hok, voor de gebruiker en voor de kippen? |

## Grootste risico en goedkoopste test
**Rem op het hele idee: waterdicht.** Een hok is een omgeving met vocht, stof, mest en stro. Of de Bittle X daartegen bestand is, is niet bevestigd `[ONBEKEND]` (`shared/bronnen/petoi/bittle-x-technische-specs.md`). Elektronica en servo's zijn kwetsbaar; een beschermende behuizing moet licht genoeg zijn om nog te lopen. Eerst bepalen: droge schuur of echt buiten (`BESLUITEN.md`, open keuze 16).

Test: een proefhok op papier en in simulatie, en de echte robot een korte route laten lopen op stro of zand, door een mens, onder toezicht en volgens `_config/veiligheid-robot.md`.

## Wat we nog niet weten
- Of dit een echt probleem is voor een echte gebruiker.
- Hoe de robot veilig en onbeheerd laadt, tegenover de regel "batterij eruit na gebruik" (`_config/veiligheid-robot.md`, regel 8).
- Kippenwelzijn en regelgeving rond dieren en robots.

## Bronnen
- Sensoren die de firmware kent: `SYSTEEM.md`, tabel "Wat erbij kan"; `shared/INDEX.md`, groep "Petoi-modules".
