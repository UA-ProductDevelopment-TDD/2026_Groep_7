# Prompt: materials research (paste into a web-enabled AI)

Copy everything below the line. Save the answer as `materials-research.json` in this folder and give it to Claude Code ("merge materials-research.json into materials.json and rebuild the deck").

---

You are helping a university student team (University of Antwerp, product development) that upgrades a Petoi Bittle X robot dog (BiBoard V1, ESP32). Research the parts below on the live web. Buy in Belgium/EU if possible (Amazon.nl/.de/.com.be, DFRobot, Kiwi Electronics, Tinytronics, Conrad, Mouser).

Rules:
- Use only prices and links you actually opened. If you cannot verify something, write null and say why in "notes". Never invent a URL or price.
- Prices in EUR incl. VAT, price for ONE unit/pack as sold, plus "units_in_pack".
- Return ONLY one JSON object, no commentary, matching the schema below.
- Per item give the best option and at most 2 alternatives. Give a direct product image URL (jpg/png) if available.
- Check compatibility notes: voltage/logic level (3.3 V vs 5 V), size/weight for mounting on a Bittle X back (max about 150 g extra), interface (I2C, UART, USB, PWM), and whether it works with ESP32 / BiBoard V1.

Items (id: description):
1. cam: DFRobot ESP32-S3 AI Camera Module (on-device vision)
2. tof: GERUI VL53L0X ToF laser range finder, 6-pack
3. mag: Kuulaa USB-C magnetic charging cable 3A with Type-C adapter
4. qi: USB Type-C universal Qi wireless charging receiver (thin, for the robot)
5. qi_tx: a Qi wireless charging transmitter pad suitable for a dock (NOT in the list yet, please add)
6. piezo: piezo disc / active buzzer, 3.3 V compatible
7. speaker: small speaker with amplifier (e.g. MAX98357A I2S module + 3 W speaker), clear voice, fits on a robot dog
8. mmwave: mmWave presence radar for the Home Guard concept (movement detection behind thin walls, e.g. plasterboard). Do NOT only check the examples DFRobot SEN0395, Seeed MR24HPC1, LD2410C: research what exists. Give the 3 best options in "alternatives" with price, detection range, whether it works through walls, interface (UART/I2C/GPIO), supply voltage, size and weight.
9. leds (optional suggestion, not on the team list): addressable LED strip or ring (WS2812B), for the deterrent mode
10. ir_cam (optional suggestion, not on the team list): night vision: IR illuminator or ESP32 camera with IR-cut, for the Chicken Coop concept

Items 5, 9 and 10 are optional suggestions; keep them clearly separate so the team can ignore them.

Schema:

```json
{
  "researched_on": "YYYY-MM-DD",
  "items": {
    "<id>": {
      "name": "exact product name",
      "supplier": "shop name",
      "url": "https://... (opened and checked)",
      "image_url": "https://... or null",
      "price_eur": 0.00,
      "units_in_pack": 1,
      "in_stock": true,
      "delivery_days": 0,
      "specs": ["key spec 1", "key spec 2"],
      "compatibility": "works with ESP32/BiBoard V1? voltage, interface, weight",
      "alternatives": [{"name": "", "url": "", "price_eur": 0.00}],
      "notes": "what you could not verify"
    }
  }
}
```
