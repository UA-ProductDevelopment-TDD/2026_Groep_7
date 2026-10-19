# extensible-modules-introduction

| | |
|---|---|
| Link in de slides | https://docs.petoi.com/extensible-modules/introduction |
| Opgehaald van | https://docs.petoi.com/extensible-modules/introduction.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Introduction

The head of Bittle is designed as a clip to hold extensible modules. We compiled a sensor pack with some popular modules, but its contents may change. Thanks to the rich content of the Arduino and Raspberry Pi communities, you can also wire other add-ons.&#x20;

{% hint style="info" %}
How to use these sensors via the example functions already implemented in the firmware：

For **NyBoard**, you need to [upload the firmware](https://docs.petoi.com/upload-firmware#nyboard) in a different mode.

For **BiBoard**, you can use the serial commands to [switch modes](https://docs.petoi.com/extensible-modules/pages/8ajuxMEplUPiNYi4SRyi#id-2.8-swith-mode-via-the-serial-commands)**.**
{% endhint %}

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FngH8Ow8CqrC3AJIaGYbH%2FDoubleLight_New.png?alt=media\&token=f56a1de4-5eff-479b-afda-559ef0aff3d1)[Light sensor](https://docs.petoi.com/extensive-modules/light-sensor)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3iZNJGg7IEWmLuE0bHXc%2FDoubleTouch_New.png?alt=media\&token=9760a8d7-e446-4ff4-a1e7-1bfe4ae1cef0)[Touch sensor](https://docs.petoi.com/extensive-modules/touch-sensor)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FeGCa7dTjK2h5U5TYMYj9%2FGesture_New.png?alt=media\&token=fcd86171-f894-4db0-91ac-3451ac333412)[Gesture sensor](https://docs.petoi.com/extensive-modules/gesture-sensor)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FjQi0R9BPHx9MQh0FmUIA%2FPIR_New.png?alt=media\&token=d0ffcfa1-3de1-4ee4-8067-9691ec63b39a)[PIR motion sensor](https://docs.petoi.com/extensive-modules/pir-motion-sensor)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FeaaZIAat5GJ8b9KW9rvh%2FIRdistance_New.png?alt=media\&token=582a4d17-e46a-4fd7-b7e7-98c3d55444c1)[IR distance sensor](https://docs.petoi.com/extensible-modules/ir-distance-sensor)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FDmHaxjwLiaWcf8Tlb820%2FVisionSensor.jpg?alt=media\&token=a6badd18-af43-44b3-a0e8-aa3c07c3e2f7)   [MU vision sensor](https://docs.petoi.com/extensive-modules/mu-camera)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F7Y6hs6A9BOL86zZHNfHy%2Fvoice05.jpg?alt=media\&token=d784b87a-6a33-4fe1-8c31-57a79dc11ec1)[Voice command module](https://docs.petoi.com/extensible-modules/voice-command-module) (Built-in on Bittle X)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FmNZ3WkybbeL7gReEDNns%2FUltra_01.jpg?alt=media\&token=364d3455-1215-42d9-97ff-a5068412881f)[Ultrasonic sensor](https://docs.petoi.com/extensive-modules/ultrasonic-sensor) (Built-in on Nybble)

You can also purchase the following third-party sensors (such as Seeed studio):

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F6nd02Hl2BzJ1uTBcjg9b%2Fextensible-modules.jpg?alt=media\&token=20f202c4-c1e8-4991-bb66-a35804880e44)

The loudness and light level modules can generate [analog readings](https://github.com/PetoiCamp/OpenCat/tree/main/ModuleTests/test_Loudness_Light) for the corresponding signals and should be connected to the analog Grove socket.&#x20;

&#x20;<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FfB8z7DNr3xyZP3jcfTRw%2Fsound-sensor.png?alt=media&amp;token=f5bbc3d2-e229-4878-a292-446c88a1cefe" alt="" data-size="original">[Grove - Sound Sensor/ Noise Detector](https://www.seeedstudio.com/Grove-Loudness-Sensor.html)

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FAssk52XduTk3LFIR85RL%2Flight-sensor.png?alt=media&amp;token=e5c951be-29fe-400e-8bb0-1a256e66522a" alt="" data-size="original">[Grove - Light Sensor v1.2 - LS06-S phototransistor](https://www.seeedstudio.com/Grove-Light-Sensor-v1-2-LS06-S-phototransistor.html)

The touch, reflection, and PIR sensors can generate digital 1 or 0 as a switch signal. So, they should be connected to the digital Grove socket. We use the fourth socket with D6 and D7 in the demo code.

&#x20;<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F35YiXIRj91mvCoOvCs2V%2Ftouch-sensor.png?alt=media&amp;token=deddf5db-4630-4c97-a783-4bada7ae1c6d" alt="" data-size="original">[Grove - Touch Sensor](https://www.seeedstudio.com/Grove-Touch-Sensor.html)

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FjJEvoYh5DwYRZQcd1W7N%2Freflection-sensor.png?alt=media&amp;token=7851e769-553f-4880-b101-9f928a29cab2" alt="" data-size="original">[Grove - Infrared Reflective Sensor v1.2](https://www.seeedstudio.com/Grove-Infrared-Reflective-Sensor-v1-2.html)

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXwg8SF4HCEPvWxjCZUWi%2FPIR-motion-sensor.png?alt=media&amp;token=3c21dbea-b01c-41ba-9280-724eac60cae9" alt="" data-size="original">[Grove - mini PIR motion sensor](https://www.seeedstudio.com/Grove-mini-PIR-motion-sensor-p-2930.html)

The [intelligent camera](https://github.com/PetoiCamp/BallTracking), [gesture](https://github.com/PetoiCamp/OpenCat/tree/main/ModuleTests/testGesture), and [OLED](https://github.com/PetoiCamp/OpenCat/tree/main/ModuleTests/testOLED) module should be connected to the I2C Grove socket.&#x20;

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FQr94aM9SiDdy1TgWBRjE%2Fgesture-sensor.png?alt=media&amp;token=f0ab202f-fe11-4f32-a42a-b2ed977950fa" alt="" data-size="original">[Grove - Gesture Sensor for Arduino (PAJ7620U2)](https://www.seeedstudio.com/Grove-Gesture-PAJ7620U2.html)

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9EJOaQ4VTXPyoRdHuCAN%2FOLED.png?alt=media&amp;token=36c3b5e3-5e05-4fc1-91a2-b44f71b16f2d" alt="" data-size="original">[Grove - OLED Display 0.96" (SSD1315)](https://www.seeedstudio.com/Grove-OLED-Display-0-96-SSD1315-p-4294.html)
