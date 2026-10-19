# module-mu-camera

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/mu-camera.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# MU Camera

## Function introduction

Petoi Intelligent Vision Sensor can recognize many objects with a deep-learning algorithm. For example, it can detect color blocks, balls, the human body, and cards. Its detection result can be transmitted through the UART or I2C interface. MU is compact, has low power consumption, processes all algorithms locally, and can be widely used in intelligent toys, AI+STEAM lessons, creators, and other products or fields.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FrTAwT2sHzROsWy1LmAn9%2Fimage.png?alt=media&amp;token=de1d2024-9a14-448a-892d-c676a1b785b5" alt=""><figcaption></figcaption></figure>

## NyBoard

### Hardware setup

After uploading the firmware, switch the dial (left: **down** and **up**; right: **down** and **down**) on the MU Vision Sensor and connect to the mainboard with wire as shown in the following picture:

![Figure 1](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZjKuo5ezz1iWLTGVfZ7C%2FMu%20Camera.jpg?alt=media\&token=32913cc9-2242-431b-8e3b-f4a795b3f92c)

### Software setup

There are two methods to upload the camera mode firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader ](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware)within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Camera**, so press the **Upgrade the Firmware** button. \
  For example, Bittle, NyBoard\_V1\_2, COM5 as follows:<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FvA8nFVfvyJKjxxwryOg1%2Fimage.png?alt=media&amp;token=7069315f-a2bd-4d33-b405-a49ac61ae291" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to upload and modify the source code.&#x20;

1. First, download and install the [MU camera library](https://github.com/mu-opensource/MuVisionSensor3) into your Arduino IDE.&#x20;

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FrwlwHLV03mwtrtqVazop%2FmuLib.png?alt=media\&token=f7721966-efb2-4388-9563-002c9aa93c3a)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FRN0NyFXOV0ct9IOI0AqU%2FaddZipLib.png?alt=media\&token=4803980c-41cf-406c-907c-3aaff81672ec)

2\. Use the latest [OpenCat](https://github.com/PetoiCamp/OpenCathttps://github.com/PetoiCamp/OpenCat) code to finish the setup.&#x20;

Use the latest OpenCat code to finish the setup. For example,  to modify the code for ***Bittle*** as shown below:

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZImh2OWU8yPpoNwriPCR%2Fimage.png?alt=media\&token=79603585-ce0a-4c19-a439-11c7a15b1713)

If you have already uploaded the latest OpenCat code to make Bittle  walk, you only need to uncomment **`#define CAMERA`** At the beginning of OpenCat.ino, then upload the code.&#x20;

If unsure, you need to finish the [upload process for the standard mode](https://docs.petoi.com/arduino-ide/upload-sketch-for-nyboard) (Step 1 to Step 10) to ensure everything is configured correctly, then upload the code in the camera mode.&#x20;

If the camera code is uploaded correctly, Bittle maintains the rest position. Success messages are printed on the [serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor) of Arduino IDE. When the MU Vision Sensor recognizes a target, the two LEDs will turn blue, and Bittle's head can follow the target and swing left and right. The demo code will auto-switch the target between a yellow tennis ball and a human body if it fails to find any object.

<div align="center"><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fvowiq9hpFpHCLjHVvKbR%2FmuInit.png?alt=media&amp;token=b68edc90-9221-40f8-98ea-d7d3021faa1c" alt=""></div>

### Arduino code demo

The demo video is as follows:

{% embed url="<https://www.youtube.com/watch?v=CxGI-MzCGWM>" %}

## BiBoard

### Hardware setup

&#x20;Switch the dial (left: **down** and **up**; right: **down** and **down**) on the MU Vision Sensor and connect to the mainboard with wire

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fb0OjNL8LO3Ccq6j55XPT%2Fimage.png?alt=media&amp;token=e5044336-1ffb-4687-9af9-92281b89dc8c" alt=""><figcaption></figcaption></figure>

#### BiBoard V0

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FdCvqpb4rw6uvgRXYei8A%2Fcamera.jpg?alt=media&amp;token=5b78cb05-0b01-4902-89e9-6d1e0415e9f6" alt=""><figcaption></figcaption></figure>

#### BiBoard V1

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FQBVou3n8lSXFZitWe8vm%2Fimage.png?alt=media&amp;token=88686488-5151-4c5a-8ec3-b2b638c4c26b" alt=""><figcaption></figcaption></figure>

{% hint style="info" %}
If you use the version of Petoi Desktop App <= **V1.2.5**,  you need to connect the camera module to the following Grove socket:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9yT079cMiDNpEqDHDEsW%2Fimage.png?alt=media&amp;token=844dd0de-54dd-46d3-95d3-80617e68dd0e" alt="" data-size="original">
{% endhint %}

Fix the end connected to the camera to the robot's head (included in Bittle's / Bittle X's mouth).

### Software setup

There are two methods to upload the firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.

Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Standard**, so press the **Upgrade the Firmware** button.&#x20;

For example, Bittle, BiBoard\_V0\_2, COM5 as follows:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FaleqWtxk5PSH9bWe9CfF%2Fimage.png?alt=media&amp;token=c92b21ff-992f-4163-a981-86078e26eedd" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

1. First, download and install the [MU camera library](https://github.com/mu-opensource/MuVisionSensor3) into the [Arduino IDE](https://www.arduino.cc/en/software).&#x20;

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FrwlwHLV03mwtrtqVazop%2FmuLib.png?alt=media\&token=f7721966-efb2-4388-9563-002c9aa93c3a)

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FRN0NyFXOV0ct9IOI0AqU%2FaddZipLib.png?alt=media\&token=4803980c-41cf-406c-907c-3aaff81672ec)

2\. Use Arduino IDE to [upload the sketch](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)(***OpenCatEsp32.ino***).&#x20;

Use the latest OpenCatESP32 source code to finish the setup. For example,  to modify the code for ***Bittle*** as shown below:<br>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FGu37FwV2ge9LKHORqrUl%2Fimage.png?alt=media&amp;token=6b0f5ed3-eb4b-4668-8f5a-3e7462718519" alt=""><figcaption></figcaption></figure>

After uploading, there are two methods to ***activate/deactivate*** the camera mode:

* Serial Monitor
  * [Open the serial monitor](/arduino-ide/serial-monitor.md#biboard) and use the serial command "***XC***" to activate the camera mode.
  * Open the serial monitor and use the serial command "***Xc***" to deactivate the camera mode.
* Mobile App
  * Create [a mobile app command](https://docs.petoi.com/mobile-app/controller#create-a-single-command) called "**Activate camera**" and use the code: *`X67`*
  * Create a mobile app command called "**Deactivate camera**" and use the code: *`X99`*

## FAQ

{% hint style="info" %}
If the MU Vision Sensor cannot identify the target object, please press the reset button on the camera and then the reset button on the main board.
{% endhint %}

{% hint style="warning" %}
While the MU Vision Sensor connects with BiBoard if the white LED on the back of the MU Vision Sensor isn't lit up.

Please plug the battery into the BiBoard and long-press the button on the battery to power the BiBoard. Then, click the camera's reset button and the main board's reset button in order.
{% endhint %}

This module also supports the following developing environment:

* MicroPython APIs
* Mixly IDE
* MakeCode IDE

For more details, please refer to [the Technical Support Document](https://morpx-docs.readthedocs.io/en/latest/MUVS3/introduction.html).
