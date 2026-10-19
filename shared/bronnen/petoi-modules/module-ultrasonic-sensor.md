# module-ultrasonic-sensor

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/ultrasonic-sensor.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Ultrasonic Sensor

## Function introduction

Petoi RGB Ultrasonic Sensor is a new module that integrates RGB LED and ultrasonic ranging. Only one GPIO is needed to operate the ultrasonic transceiver. While the ultrasonic probe measures the distance, the other GPIO pin can drive RGB LEDs with various light effects.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fl8BHZGeI1GKkvs4Ewkp8%2FUltra_01.jpg?alt=media&amp;token=8a7015f2-7578-4b2c-9bc4-bfb65caf3644" alt=""><figcaption></figcaption></figure>

{% hint style="info" %}
The previous one:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3TWvP8tjgOy51cTvJ4ql%2F%E8%B6%85%E5%A3%B0%E6%B3%A2%E4%BC%A0%E6%84%9F%E5%99%A801.jpg?alt=media&amp;token=44214fce-262b-4e25-a5da-b11c45358aa3" alt="" data-size="original">
{% endhint %}

## NyBoard

### Hardware setup

Connecting to the NyBoard with wire as shown in the following picture:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FD2HwN5zUBNcoRYIlqNKt%2FUltraConnect_01.jpg?alt=media&amp;token=e72dd6fc-ec6e-4868-866a-e5625b06a61f" alt=""><figcaption></figcaption></figure>

{% hint style="info" %}
The previous one:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FkmdIjWPLXJXRjpLkOIGW%2FUltrasonic_Sensor.jpeg?alt=media&amp;token=d5221650-1ced-4842-902e-676fede0fbd5" alt="" data-size="original">
{% endhint %}

Attach the ultrasonic sensor to [Nybble's eye](https://youtu.be/g7_ODr_3DTc).

{% embed url="<https://youtu.be/kV2UYbpfGic>" %}

### Software setup

There are two methods to upload the ultrasonic mode firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Ultrasonic**, so press the **Upgrade the Firmware** button. \
  For example, Nybble, NyBoard\_V1\_2, COM5 as follows:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F2e7b2t80CsYebShoyhbk%2Fimage.png?alt=media&amp;token=58b6d34e-314d-4684-8d73-a090dcbca9bb" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to upload and modify the source code.&#x20;

Use the latest OpenCat code to finish the setup. For example,  to modify the code for ***Nybble*** as shown below:

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FNxVFIMsyv5DiV1Exauri%2Fimage.png?alt=media\&token=81225404-aa5b-48ae-bba3-bb8deb08f867)

If you have already uploaded the latest OpenCat code to make Nybble walk, you only need to uncomment the **`#define ULTRASONIC`** at the beginning of OpenCat.ino, then upload the code.&#x20;

If you are unsure, you need to finish the [upload process for the standard mode](https://docs.petoi.com/arduino-ide/upload-sketch-for-nyboard) (Step 1 to Step 10) to ensure everything is configured correctly, then upload the code in the Ultrasonic mode.&#x20;

If the Ultrasonic code is uploaded correctly, you can see success messages printed on the [serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor) of Arduino IDE. As shown below:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F4FA6phk8SPXET7iE8eoH%2Fimage.png?alt=media&amp;token=1dbfec4d-1ef1-4ede-b502-9da2871677b5" alt=""><figcaption></figcaption></figure>

#### Arduino code demo

Ultrasonic module code realization function: The probe inside the ultrasonic module lights up with different-colored lights according to the different distances monitored by the ultrasonic module in real-time, and Nybble will make different action responses at the same time.

The demo video is as follows:

{% embed url="<https://www.youtube.com/watch?v=vhaYcKimkFY>" %}

#### Mind+ demo code

<https://github.com/PetoiCamp/Petoi_MindPlusLib/blob/main/examples/NyBoard/avoidObs_NyBoard.mp>

## BiBoard

### Hardware setup

#### BiBoard V0&#x20;

Take Bittle X for example, connecting to the BiBoard with a wire as shown in the following picture:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLCVQQoHxCnP0hI5BocZk%2FUltrasonic_BiBoard.png?alt=media&amp;token=69daf1c1-d370-4ffa-a58c-726a517c9593" alt=""><figcaption></figcaption></figure>

The dial switch on the bottom of the BiBoard extension hat is dialed to ***UART2*** .

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLivXJDXxJGJRgcfB3hLJ%2FSwitch.jpg?alt=media&amp;token=896c9a51-ee3b-4382-9a95-8492d2c4d2a0" alt=""><figcaption></figcaption></figure>

#### BiBoard V1

The sensor should connect to the first Grove socket from the top.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLEQMI2WvAGDqvm5tRYvv%2FUltrasonic_BiBoard_V1.jpg?alt=media&amp;token=62034d03-ba67-4913-97a3-f0754fc6d140" alt=""><figcaption></figcaption></figure>

### Software setup

There are two methods to upload the firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Standard**, so press the **Upgrade the Firmware** button. \
  For example, Bittle, BiBoard\_V0\_2, COM5 as follows:

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FaleqWtxk5PSH9bWe9CfF%2Fimage.png?alt=media&amp;token=c92b21ff-992f-4163-a981-86078e26eedd" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to [upload the sketch](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)(***OpenCatEsp32.ino***). \
  Use the latest OpenCatESP32 code to finish the setup. For example,  to modify the code for ***Bittle*** as shown below:<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FGu37FwV2ge9LKHORqrUl%2Fimage.png?alt=media&amp;token=6b0f5ed3-eb4b-4668-8f5a-3e7462718519" alt=""><figcaption></figcaption></figure>

After uploading, there are two methods to ***activate/deactivate*** the ultrasonic mode:

* Serial Monitor
  * [Open the serial monitor](/arduino-ide/serial-monitor.md#biboard) and use the serial command "***XU***" to activate the ultrasonic mode.
  * Open the serial monitor and use the serial command "***Xu***" to deactivate the ultrasonic mode.
* Mobile App
  * Create [a mobile app command](https://docs.petoi.com/mobile-app/controller#create-a-single-command) called "**Activate ultrasonic**" and use the code: *`X85`*
  * Create a mobile app command called "**Deactivate ultrasonic**" and use the code: *`X117`*

#### Mind+ demo code

<https://github.com/PetoiCamp/Petoi_MindPlusLib/blob/main/examples/BiBoard/avoidObs_BiBoard.mp>
