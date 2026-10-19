# Veilig werken met de robot

> **Layer 3.** Beheerd door de robotmanager. Lees dit voor je de robot aanzet, kalibreert of firmware uploadt.
> Bron per regel tussen haakjes: `slides` = practicumslides 2026-2027 V0.1 · `docs` = bestand in `shared/bronnen/` · `[mondeling, niet bevestigd]` = alleen uit de mondelinge uitleg, nog te controleren.

## Juiste versie

1. Dit team werkt met de **Bittle X** en de **BiBoard V1** (slides). De Petoi-docs bevatten ook pagina's voor NyBoard, BiBoard V0 en andere robots; gebruik die niet.
2. Een firmware van de verkeerde versie uploaden zet de robot in een kapotte toestand die volledig herstel vraagt. Vorig jaar gebeurde dat met een verkeerd gekozen board `[mondeling, niet bevestigd]`.
3. De Arduino IDE heeft het ESP32-boardpakket **versie 2.0.12** nodig; versie 2.0.13 en hoger kan het board laten falen bij opstarten (docs: `petoi-docs/upload-sketch-biboard.md`).

## Firmware

4. Twee wegen (slides): **Petoi Desktop App, Firmware Uploader** om terug te gaan naar een robot die werkt; **Arduino IDE met de OpenCatEsp32-broncode** voor alles wat je zelf programmeert.
5. Sluit eerst de seriële monitor voor je uploadt (slides).
6. De Firmware Uploader-pagina voor BiBoard V1 verwijst voor uploadopties en factory reset naar de pagina van BiBoard V0 (docs: `petoi-docs/firmware-uploader-biboard-v1.md`). Laat dat bevestigen bij de begeleiders voor iemand uploadt (`BESLUITEN.md`, open keuze 17).

## Opstarten en batterij

7. Zet de robot in een **neutrale startpositie** voor je hem aanzet. Bij een verkeerde startpositie kunnen servo's de verkeerde kant op draaien en zichzelf beschadigen, vooral na een firmware-update `[mondeling, niet bevestigd]`.
8. **Batterij uithalen na gebruik, niet onbeheerd opladen** `[mondeling, niet bevestigd]`.

## Aansluiten

9. Servokabel: bruin/zwart = GND (−), rood = +, geel/oranje = signaal (S) (slides). Verkeerd om insteken kan de chip doen doorbranden (docs: `petoi-docs/joint-pins-biboard-v1-bittle-x.md`).
10. Jointnummers: 0 = hoofd (pan), 8-11 = schouders, 12-15 = knieën; 1-7 zijn voorbehouden voor andere Petoi-robots (slides).
11. Connectoren zijn moeilijk verkeerd in te steken, maar met te veel kracht lukt het toch `[mondeling, niet bevestigd]`.
12. Grove G1 en de Raspberry Pi-poort delen UART2: gebruik er maar één tegelijk (slides).
13. Eén sensor tegelijk: een sensor aanzetten zet de vorige uit. Stuur `X?` om te zien wat aan staat (slides).

## Kalibratie

14. Servo's kalibreren met de Joint Calibrator (docs: `petoi-docs/joint-calibrator-bittle-x.md`). Nodig na elke servovervanging of firmware-update `[mondeling, niet bevestigd]`.
15. De IMU wordt gekalibreerd tijdens de firmware-upload (slides). Leg de robot daarvoor volledig plat `[mondeling, niet bevestigd]`. De V1-pagina van de Firmware Uploader beschrijft de stap niet zelf, ze verwijst naar de V0-pagina (zie regel 6).

## Spraak

16. De spraakmodule kan uitgezet worden zodat de robot tijdens het werken niet op omgevingsgeluid reageert `[mondeling, niet bevestigd]`. Hoe: zie `petoi-docs/voice-command-module.md`.
