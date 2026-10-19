# opencatesp32

| | |
|---|---|
| Link in de slides | github.com/PetoiCamp/OpenCatEsp32 |
| Opgehaald van | https://github.com/PetoiCamp/OpenCatEsp32 |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | git clone zonder bestandsinhoud; README + volledige bestandenlijst, geen CAD- of codebestanden overgenomen |

---

Branch `main`, laatste commit `84dd6eff307eb2f4af6f9cbdf72f04e7d71beecf 2026-09-08`. Bestanden: 2169.

## README (README.md)

# OpenCatESP32 — OpenCat Framework on ESP32/BiBoard

🚀 **[Quaddle](https://www.kickstarter.com/projects/petoi/quaddle-open-source-desktop-robot-kit/?ref=cbcwga&utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-hero-banner) — Petoi's newest OpenCat-lineage quadruped — goes live on Kickstarter Sept 2, 2026.** [Get notified →](https://www.kickstarter.com/projects/petoi/quaddle-open-source-desktop-robot-kit/?ref=cbcwga&utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-hero-banner) (details below)

OpenCatESP32 runs the OpenCat quadruped robotics framework on [BiBoard](https://www.petoi.com/products/biboard-esp32-development-board-for-quadruped-robot?utm_source=github&utm_medium=code&utm_campaign=github-opencat) — an ESP32-based development board designed for multi-degree-of-freedom legged robots with up to 12 servos. Developed by [Petoi](https://www.petoi.com?utm_source=github&utm_medium=code&utm_campaign=github-opencat), the maker of futuristic programmable robotic pets.

This is the codebase for current-generation Petoi hardware. If you're on the older NyBoard (ATmega328P), see the main [OpenCat repo](https://github.com/PetoiCamp/OpenCat).

[![BittleESP32](https://github.com/PetoiCamp/NonCodeFiles/blob/master/gif/BiBoard.gif?raw=true)](https://www.youtube.com/watch?v=GTgps_H990w)

[![BittleGap](https://github.com/PetoiCamp/NonCodeFiles/blob/master/gif/gap.gif?raw=true)](https://youtu.be/1qhNRSQTcG4)

*Click either GIF to watch the demo.*

---

## Quaddle mini robot dog — launching on Kickstarter Sept 2, 2026
![](https://github.com/PetoiCamp/NonCodeFiles/blob/master/gif/quaddleCover.gif?raw=true)

[Quaddle](https://www.kickstarter.com/projects/petoi/quaddle-open-source-desktop-robot-kit/?ref=cbcwga&utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-quaddle-section) is Petoi's newest quadruped, **going live on Kickstarter Sept 2, 2026** — a mini desk robot built on the same OpenCat lineage as Bittle and Nybble.

- Full quadruped running on just **4 servos** instead of the usual 8–12, which forces genuinely different gait-design and leg-coordination solutions to still get all four legs walking, running, and balancing
- Position-feedback servos — readable, not just drivable — which is what makes **Puppet Mode** possible: hand-guide the legs and record a motion directly, no code required
- 3D-printable shells and mounts for customization
- Same open platform this repo already supports for gait research, reinforcement learning (RL), and sim2real work — a hands-on physical AI platform, not a toy version of the idea
- Try it in the [online simulator](https://www.petoi.com/pages/quaddle-robot-dog-simulator?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-quaddle-simulator) before it ships

**Source code is not yet public.** It's an upgraded version of the OpenCat project, and its ESP32-S3 code structure is closer to this repo than to the main NyBoard-based [OpenCat repo](https://github.com/PetoiCamp/OpenCat-Quadruped-Robot). We plan to open source it before Quaddle delivery.

- Watch this repo and [r/petoi](https://www.reddit.com/r/Petoi/) for the open-source announcement
- [Get notified on Kickstarter](https://www.kickstarter.com/projects/petoi/quaddle-open-source-desktop-robot-kit/?ref=cbcwga&utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-notify-link) when it goes live
- Check out the [Quaddle Hugging Face page](https://huggingface.co/petoi/quaddle)

---

## About the Project

Inspired by Boston Dynamics' Spot, [Dr. Rongzhong Li](https://www.linkedin.com/in/rongzhongli/) started OpenCat in his dorm at Wake Forest University in 2016. The goal was straightforward: make agile quadruped robots affordable and hackable enough for researchers, educators, and makers — not just well-funded labs.

Since then:
- **30,000+ robots shipped**, cumulative across all channels
- **60+ countries**
- **$1M+ raised** across two prior Kickstarter and Indiegogo campaigns
- **20+ academic papers** cite the platform — see [Research Spotlight](https://www.petoi.com/pages/robotics-research-and-academic-applications?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- One of the most-starred open-source quadruped robot projects on GitHub

---

## Hardware

BiBoard is the control board for:

- 🐶 [Bittle X — mini robot dog & AI robotics kit with voice control](https://www.petoi.com/products/petoi-robot-dog-bittle-x-voice-controlled?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
  - [Also available on Amazon](https://www.amazon.com/dp/B0FNT6TSVT?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-amazon-buy-link)
  - [Try the simulator](https://www.petoi.com/pages/bittle-x-robot-dog-simulator?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-bittle-x-simulator)
- 🐱 [Nybble Q — mini robot cat & AI robotics kit](https://www.petoi.com/products/petoi-nybble-q-robot-cat?utm_source=github&utm_medium=code&utm_campaign=github-opencat)

The older [Bittle](https://www.petoi.com/collections/robots/products/petoi-bittle-robot-dog?utm_source=github&utm_medium=code&utm_campaign=github-opencat) and [Nybble](https://www.petoi.com/collections/robots/products/petoi-nybble-robot-cat?utm_source=github&utm_medium=code&utm_campaign=github-opencat) (NyBoard) are discontinued. BiBoard is the current platform.

---

## Why BiBoard Over NyBoard?

The ATmega328P (NyBoard) gets the job done for locomotion. BiBoard is for when your **robotics programming** needs more headroom:

- **ESP32 dual-core @ 240 MHz** — handle real-time servo coordination and a perception pipeline simultaneously
- **Wi-Fi + Bluetooth built in** — wireless control and data streaming without a dongle
- **Up to 12 servos** — full 12-DOF configurations
- **Arduino IDE compatible** — same workflow, more horsepower
- **Open source** — hardware and software both forkable

If you're building an open source robot dog for research, running ROS, deploying a vision model, or just want room to experiment — BiBoard is the right foundation.

---

## Board Configuration

**Arduino IDE settings (ESP32 Dev Module):**

| Setting | Value |
|---|---|
| Upload Speed | 921600 |
| CPU Frequency | 240 MHz (WiFi/BT) |
| Flash Frequency | 80 MHz |
| Flash Mode | QIO |
| Flash Size | 4 MB |
| Partition Scheme | Default 4MB with spiffs |
| Core Debug Level | None |
| PSRAM | Disabled |

Full setup: [Upload Sketch for BiBoard](https://guide.petoi.com/arduino-ide/upload-sketch-for-biboard)

---

## What People Have Built

- [AI and computer vision applications](https://www.petoi.com/blogs/blog/tagged/showcase+ai?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [Raspberry Pi robotics projects](https://www.petoi.com/blogs/blog/tagged/raspberry-pi?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [NVIDIA Isaac simulations and reinforcement learning](https://www.youtube.com/playlist?list=PLHMFXft_rV6MWNGyofDzRhpatxZuUZMdg)
- [SLAM with ROS using Bittle and Raspberry Pi](https://www.youtube.com/watch?v=uXpQUIF_Jyk&list=PLHMFXft_rV6MWNGyofDzRhpatxZuUZMdg&index=6)
- [Research Spotlight](https://www.petoi.com/pages/robotics-research-and-academic-applications?utm_source=github&utm_medium=code&utm_campaign=github-opencat) — academic and research use

---

## Education

OpenCat shows up in **AI robotics education** across K-12 programs, community colleges, university labs, and maker spaces — hands-on **physical AI** teaching that goes beyond screen-based coding exercises:

- [Robotics education showcases](https://www.petoi.com/blogs/blog/tagged/showcase+education?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [STEM & robotics curriculum resources](https://www.petoi.com/pages/resources-curriculum-stem-coding-robot?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [Robotics competitions](https://www.petoi.com/blogs/blog/robot-competitions-with-petoi?utm_source=github&utm_medium=code&utm_campaign=github-opencat)

---

## Community & Discussion

- [r/OpenCat](https://www.reddit.com/r/OpenCat/) — firmware code, framework hacking, extending and porting OpenCat
- [r/Petoi](https://www.reddit.com/r/Petoi/) — hardware Q&A, builds, quadruped coding, RL experiments, curriculum, 3D-printed parts, general discussion
- [Facebook Group](https://www.facebook.com/groups/385050523510952) — community discussion and builds

---

## Resources

- [Petoi Guides](https://guide.petoi.com/)
- [AI reinforcement learning with Petoi](https://www.petoi.com/blogs/blog/petoi-robot-ai-reinforcing-learning?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [FinoBot — AI robot dog with Raspberry Pi and ROS2](https://www.petoi.com/blogs/blog/finobot-ai-robot-dog-bittle-x-follows-someone?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [Robotics research with Bittle adapting to different surfaces at Haverford College](https://www.petoi.com/blogs/blog/robotics-research-with-bittle-robot-dog-at-haverford-college?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [Advanced tutorials by the community](https://www.youtube.com/playlist?list=PLHMFXft_rV6MWNGyofDzRhpatxZuUZMdg)
- [All kits and accessories](https://www.petoi.com/store?utm_source=github&utm_medium=code&utm_campaign=github-opencat)
- [FAQ](https://www.petoi.com/pages/faq?utm_source=github&utm_medium=code&utm_campaign=github-opencat)

Follow the project:

- [YouTube](https://www.youtube.com/@petoicamp?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-youtube-follow)
- [Twitter](https://twitter.com/petoicamp?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-twitter-follow)
- [Instagram](https://www.instagram.com/petoicamp/?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-instagram-follow)
- [Facebook](https://www.facebook.com/PetoiCamp/?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-facebook-follow)
- [LinkedIn](https://www.linkedin.com/company/petoi/?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-linkedin-follow)
- [TikTok](https://www.tiktok.com/@petoicamp/?utm_source=github&utm_medium=code&utm_campaign=github-opencat&utm_content=esp32-readme-tiktok-follow)

## Bestandenlijst

```
.gitattributes
.gitignore
ChangeLog.md
ESP32config/ESP32Configuration.jpg
LICENSE
Log/ASYNC_UPGRADE_GUIDE.md
Log/GAIT_CONTROL_IMPLEMENTATION.md
Log/GESTURE_STACK_OVERFLOW_FIX.md
Log/HOW_TO_INCREASE_STACK_SIZE.md
ModuleTests/AnalogInput/AnalogInput.ino
ModuleTests/ESP8266WiFiController/ESP8266WiFiController.ino
ModuleTests/ESP8266WiFiController/actionpage.h
ModuleTests/ESP8266WiFiController/calibrationpage.h
ModuleTests/ESP8266WiFiController/commons.h
ModuleTests/ESP8266WiFiController/mainpage.h
ModuleTests/moduleTests.ino
ModuleTests/setBluetoothParameter/setBluetoothParameter.ino
ModuleTests/testBLE_uart/testBLE_uart.ino
ModuleTests/testBT_SPP/testBT_SPP.ino
ModuleTests/testBackTouch/testBackTouch.ino
ModuleTests/testBuzzer/testBuzzer.ino
ModuleTests/testDoubleCores/testDoubleCores.ino
ModuleTests/testDoubleInfraredDistance/testDoubleInfraredDistance.ino
ModuleTests/testDoubleTouch/testDoubleTouch.ino
ModuleTests/testFlashEEPROM/testFlashEEPROM.ino
ModuleTests/testGesture/src/Arduino_APDS9960.cpp
ModuleTests/testGesture/src/Arduino_APDS9960.h
ModuleTests/testGesture/testGesture.ino
ModuleTests/testGroveUltrasonic/testGroveUltrasonic.ino
ModuleTests/testGroveUltrasonic/testRGBLedUlrasonicESP32/RgbUltrasonic.h
ModuleTests/testGroveUltrasonic/testRGBLedUlrasonicESP32/testRGBLedUlrasonicESP32.ino
ModuleTests/testI2cDevice/testI2cDevice.ino
ModuleTests/testI2cEEPROM/testI2cEEPROM.ino
ModuleTests/testIRquality/testInfraredRec/testInfraredRec.ino
ModuleTests/testIRquality/testInfraredSend/testInfraredSend.ino
ModuleTests/testInfraredRemote/testInfraredRemote.ino
ModuleTests/testMP3/PetoiESP32MP3.cpp
ModuleTests/testMP3/PetoiESP32MP3.h
ModuleTests/testMP3/data/1-10.mp3
ModuleTests/testMP3/data/bark.mp3
ModuleTests/testMP3/data/lowbattery_16b_32k.mp3
ModuleTests/testMP3/data/lowbattery_24b_192k.mp3
ModuleTests/testMP3/data/pno-cs.mp3
ModuleTests/testMP3/data/viola16_48kbps.mp3
ModuleTests/testMP3/data/viola24pcm_441k_192kbps.mp3
ModuleTests/testMP3/dog-barking-short-sound-effect.mp3
ModuleTests/testMP3/testMP3.ino
ModuleTests/testMPU6050/testMPU6050.ino
ModuleTests/testMPU6050NoInterrupt/testMPU6050NoInterrupt.ino
ModuleTests/testMacro/testMacro.ino
ModuleTests/testMpuNoInterruptClass/testMpuNoInterruptClass.ino
ModuleTests/testNvsEsp32/testNvsEsp32.ino
ModuleTests/testOLED/SSD1315.cpp
ModuleTests/testOLED/SSD1315.h
ModuleTests/testOLED/logo1.bmp
ModuleTests/testOLED/logo2.bmp
ModuleTests/testOLED/testOLED.ino
ModuleTests/testPCA9685/testPCA9685.ino
ModuleTests/testRandom/testRandom.ino
ModuleTests/testSLSensor/SoundAndLightBehavior.csv
ModuleTests/testSLSensor/testSLSensor.ino
ModuleTests/testSerialComm/testSerialComm.ino
ModuleTests/testSerialToSerialBT_SSP/testSerialToSerialBT_SSP.ino
ModuleTests/testServo/genericServoTest/Readme.md
ModuleTests/testServo/genericServoTest/genericServoTest.ino
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/.github/ISSUE_TEMPLATE.md
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/.github/PULL_REQUEST_TEMPLATE.md
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/.github/workflows/githubci.yml
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/.gitignore
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/Adafruit_PWMServoDriver.cpp
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/Adafruit_PWMServoDriver.h
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/README.md
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/keywords.txt
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/library.properties
ModuleTests/testServo/genericServoTest/src/Adafruit-PWM-Servo-Driver-Library/license.txt
ModuleTests/testServo/genericServoTest/src/espServo.h
ModuleTests/testServo/genericServoTest/src/pcaServo.h
ModuleTests/testServo/genericServoTest/src/servo.h
ModuleTests/testServo/genericServoTest/src/src.ino
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32PWM.cpp
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32PWM.h
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32Servo.cpp
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32Servo.h
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32Tone.cpp
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/ESP32Tone.h
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/analogWrite.cpp
ModuleTests/testServo/genericServoTest/temp/PetoiESP32Servo/analogWrite.h
ModuleTests/testServo/testESP32ServoCalibrated/ESP32PWM.cpp
ModuleTests/testServo/testESP32ServoCalibrated/ESP32PWM.h
ModuleTests/testServo/testESP32ServoCalibrated/ESP32Servo.cpp
ModuleTests/testServo/testESP32ServoCalibrated/ESP32Servo.h
ModuleTests/testServo/testESP32ServoCalibrated/ESP32Tone.cpp
ModuleTests/testServo/testESP32ServoCalibrated/ESP32Tone.h
ModuleTests/testServo/testESP32ServoCalibrated/analogWrite.cpp
ModuleTests/testServo/testESP32ServoCalibrated/analogWrite.h
ModuleTests/testServo/testESP32ServoCalibrated/testESP32ServoCalibrated.ino
ModuleTests/testServo/testESP32ServoSimple/testESP32ServoSimple.ino
ModuleTests/testServo/testESP32ServoSimpleWalk/testESP32ServoSimpleWalk.ino
ModuleTests/testTwoAnalogRaw/testTwoAnalogRaw.ino
ModuleTests/testUltrasonicWithTrigAndEcho/testUltrasonicWithTrigAndEcho.ino
ModuleTests/testVoiceCommander/testVoiceCommander.ino
ModuleTests/testVoltageReading/testVoltageReading.ino
ModuleTests/test_Loudness_Light/test_Loudness_Light.ino
ModuleTests/test_Touch_Reflection_PIR/test_Touch_Reflection_PIR.ino
OpenCatEsp32.ino
PetoiWebCodingBlocks/.gitignore
PetoiWebCodingBlocks/Arduino/http_server/http_server.ino
"PetoiWebCodingBlocks/Doc/\351\215\221\350\212\245\346\232\237\347\200\271\347\202\265\345\271\207.xlsx"
PetoiWebCodingBlocks/assets/logo.svg
PetoiWebCodingBlocks/blocks/communication.js
PetoiWebCodingBlocks/blocks/generators.js
PetoiWebCodingBlocks/communication.pptx
PetoiWebCodingBlocks/i18n/i18gen.js
PetoiWebCodingBlocks/js/petoi_async_client.js
PetoiWebCodingBlocks/js/timeout_config.js
PetoiWebCodingBlocks/js/toolbox.js
PetoiWebCodingBlocks/lang/translations.js
PetoiWebCodingBlocks/log/Features.md
PetoiWebCodingBlocks/log/Update Summary (English).md
PetoiWebCodingBlocks/log/Update Summary.md
PetoiWebCodingBlocks/main.html
PetoiWebCodingBlocks/node_modules/.package-lock.json
PetoiWebCodingBlocks/node_modules/agent-base/LICENSE
PetoiWebCodingBlocks/node_modules/agent-base/README.md
PetoiWebCodingBlocks/node_modules/agent-base/dist/helpers.d.ts
PetoiWebCodingBlocks/node_modules/agent-base/dist/helpers.d.ts.map
PetoiWebCodingBlocks/node_modules/agent-base/dist/helpers.js
PetoiWebCodingBlocks/node_modules/agent-base/dist/helpers.js.map
PetoiWebCodingBlocks/node_modules/agent-base/dist/index.d.ts
PetoiWebCodingBlocks/node_modules/agent-base/dist/index.d.ts.map
PetoiWebCodingBlocks/node_modules/agent-base/dist/index.js
PetoiWebCodingBlocks/node_modules/agent-base/dist/index.js.map
PetoiWebCodingBlocks/node_modules/agent-base/package.json
PetoiWebCodingBlocks/node_modules/asynckit/LICENSE
PetoiWebCodingBlocks/node_modules/asynckit/README.md
PetoiWebCodingBlocks/node_modules/asynckit/bench.js
PetoiWebCodingBlocks/node_modules/asynckit/index.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/abort.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/async.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/defer.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/iterate.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/readable_asynckit.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/readable_parallel.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/readable_serial.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/readable_serial_ordered.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/state.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/streamify.js
PetoiWebCodingBlocks/node_modules/asynckit/lib/terminator.js
PetoiWebCodingBlocks/node_modules/asynckit/package.json
PetoiWebCodingBlocks/node_modules/asynckit/parallel.js
PetoiWebCodingBlocks/node_modules/asynckit/serial.js
PetoiWebCodingBlocks/node_modules/asynckit/serialOrdered.js
PetoiWebCodingBlocks/node_modules/asynckit/stream.js
PetoiWebCodingBlocks/node_modules/atob-lite/.npmignore
PetoiWebCodingBlocks/node_modules/atob-lite/LICENSE.md
PetoiWebCodingBlocks/node_modules/atob-lite/README.md
PetoiWebCodingBlocks/node_modules/atob-lite/atob-browser.js
PetoiWebCodingBlocks/node_modules/atob-lite/atob-node.js
PetoiWebCodingBlocks/node_modules/atob-lite/package.json
PetoiWebCodingBlocks/node_modules/blockly/README.md
PetoiWebCodingBlocks/node_modules/blockly/blockly.min.js
PetoiWebCodingBlocks/node_modules/blockly/blockly.mjs
PetoiWebCodingBlocks/node_modules/blockly/blockly_compressed.js
PetoiWebCodingBlocks/node_modules/blockly/blockly_compressed.js.map
PetoiWebCodingBlocks/node_modules/blockly/blocks.d.ts
PetoiWebCodingBlocks/node_modules/blockly/blocks.js
PetoiWebCodingBlocks/node_modules/blockly/blocks.mjs
PetoiWebCodingBlocks/node_modules/blockly/blocks_compressed.js
PetoiWebCodingBlocks/node_modules/blockly/blocks_compressed.js.map
PetoiWebCodingBlocks/node_modules/blockly/core-node.js
PetoiWebCodingBlocks/node_modules/blockly/core.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core.js
PetoiWebCodingBlocks/node_modules/blockly/core/any_aliases.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/block.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/block_animations.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/block_svg.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/blockly.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/blockly_options.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/blocks.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/browser_events.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bubbles.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bubbles/bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bubbles/mini_workspace_bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bubbles/text_bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bubbles/textinput_bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/bump_objects.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/clipboard.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/clipboard/block_paster.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/clipboard/registry.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/clipboard/workspace_comment_paster.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/comments.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/comments/comment_view.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/comments/rendered_workspace_comment.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/comments/workspace_comment.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/common.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/component_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/config.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/connection_checker.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/connection_db.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/connection_type.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/contextmenu.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/contextmenu_items.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/contextmenu_registry.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/css.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/delete_area.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dialog.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/drag_target.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dragging.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dragging/block_drag_strategy.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dragging/bubble_drag_strategy.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dragging/comment_drag_strategy.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dragging/dragger.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/dropdowndiv.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_abstract.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_change.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_create.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_delete.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_drag.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_field_intermediate_change.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_block_move.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_bubble_open.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_click.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_change.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_collapse.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_create.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_delete.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_comment_move.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_marker_move.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_selected.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_theme_change.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_toolbox_item_select.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_trashcan_open.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_ui_base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_var_base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_var_create.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_var_delete.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_var_rename.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/events_viewport.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/utils.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/events/workspace_events.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/extensions.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_checkbox.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_dropdown.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_image.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_label.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_label_serializable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_number.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_registry.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_textinput.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/field_variable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/flyout_base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/flyout_button.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/flyout_horizontal.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/flyout_metrics_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/flyout_vertical.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/generator.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/gesture.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/grid.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/icons.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inject.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/align.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/dummy_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/end_row_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/input_types.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/statement_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/inputs/value_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/insertion_marker_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/insertion_marker_previewer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_ast_node_location.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_ast_node_location_svg.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_ast_node_location_with_block.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_autohideable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_bounded_element.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_collapsible_toolbox_item.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_comment_icon.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_component.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_connection_checker.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_connection_previewer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_contextmenu.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_copyable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_deletable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_delete_area.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_drag_target.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_draggable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_dragger.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_flyout.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_has_bubble.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_icon.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_keyboard_accessible.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_legacy_procedure_blocks.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_metrics_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_movable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_observable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_parameter_model.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_paster.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_positionable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_procedure_block.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_procedure_map.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_procedure_model.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_registrable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_rendered_element.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_selectable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_selectable_toolbox_item.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_serializable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_serializer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_styleable.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_toolbox.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_toolbox_item.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/interfaces/i_variable_backed_parameter_model.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/internal_constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/keyboard_nav/ast_node.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/keyboard_nav/basic_cursor.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/keyboard_nav/cursor.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/keyboard_nav/marker.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/keyboard_nav/tab_navigate_cursor.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/layer_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/layers.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/main.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/marker_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/menu.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/menuitem.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/metrics_manager.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/msg.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/names.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/observable_procedure_map.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/options.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/positionable_helpers.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/procedures.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/registry.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/render_management.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/rendered_connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/block_rendering.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/drawer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/i_path_object.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/info.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/marker_svg.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/path_object.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/common/renderer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/drawer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/geras.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/highlight_constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/highlighter.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/info.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/measurables/inline_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/measurables/statement_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/path_object.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/geras/renderer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/base.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/bottom_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/external_value_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/field.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/hat.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/icon.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/in_row_spacer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/inline_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/input_connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/input_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/jagged_edge.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/next_connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/output_connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/previous_connection.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/round_corner.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/spacer_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/square_corner.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/statement_input.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/top_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/measurables/types.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/thrasos/info.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/thrasos/renderer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/thrasos/thrasos.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/constants.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/drawer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/info.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/marker_svg.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/measurables/bottom_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/measurables/inputs.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/measurables/row_elements.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/measurables/top_row.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/path_object.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/renderer.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/renderers/zelos/zelos.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/scrollbar.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/scrollbar_pair.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/serialization.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/serialization/blocks.d.ts
PetoiWebCodingBlocks/node_modules/blockly/core/serialization/exceptions.d.ts
... en nog 1769 bestanden
```
