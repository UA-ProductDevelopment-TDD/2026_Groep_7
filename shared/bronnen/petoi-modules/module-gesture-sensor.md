# module-gesture-sensor

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/gesture-sensor.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Gesture Sensor

{% embed url="<https://youtu.be/1sznhot5U0E>" %}

{% embed url="<https://youtu.be/namXLL7VmrQ>" %}

## Function introduction

The sensor features advanced gesture detection, proximity detection and digital ambient light sensing. Gesture detection can accurately sense "up, down, left and right" and more complex movements.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FtSN6KysyGMVmmYhnmYQn%2FGesture_New.png?alt=media&amp;token=b7f17656-7d53-4528-84e7-862889e3f0f4" alt=""><figcaption></figcaption></figure>

## NyBoard

### Software setup

There are two methods to upload the gesture mode firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader ](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware)within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Gesture**, so press the **Upgrade the Firmware** button. \
  For example, Nybble, NyBoard\_V1\_2, COM5 as follows:<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FvbECwxh2s1r597a0tvKe%2Fimage.png?alt=media&amp;token=7002b240-7058-4d41-ada8-396260960aa7" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to upload and modify the source code.&#x20;

The code using this sensor has been integrated into the [**OpenCat**](https://github.com/PetoiCamp/OpenCat) project. Uncomment the line **`#define GESTURE`**  in the **OpenCat.ino**, as shown in the figure below, and then use the Arduino IDE to upload the sketch to the robot main board, which can reproduce the example function of integrating the robot action.

#### Prepare the Arduino UNO development environment

With **NyBoard V1\_\***, you can choose **Arduino Uno**.&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXDvIUhP1OotHdF3rFSZN%2Fimage.png?alt=media&amp;token=4170cb44-69cd-4d52-9701-83618dbfb59c" alt=""><figcaption></figcaption></figure>

#### Modify the code in the OpenCat.ino

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FijiuA2yGCHHJJrJJAWoM%2Fimage.png?alt=media&amp;token=e1a55828-cf36-4434-953a-ec270b15347c" alt=""><figcaption></figcaption></figure>

### Hardware setup

After uploading the sketch, connect to the NyBoard with wire, as shown in the following picture:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FaUh1KEKMeBQAthAQA0E0%2FPANA0502%20%E6%8B%B7%E8%B4%9D.jpg?alt=media&amp;token=dfb6db2f-0d6a-4f60-8887-71d72f8915a1" alt=""><figcaption></figcaption></figure>

## BiBoard

### Software setup

There are two methods to upload the firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Standard**, so press the **Upgrade the Firmware** button. \
  For example, Bittle, BiBoard\_V0\_2, COM5 as follows:

  <figure><img src="https://docs.petoi.com/~gitbook/image?url=https%3A%2F%2F1565080149-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F-MQ6a951Q6Jn1Zzt5Ajr-887967055%252Fuploads%252FaleqWtxk5PSH9bWe9CfF%252Fimage.png%3Falt%3Dmedia%26token%3Dc92b21ff-992f-4163-a981-86078e26eedd&#x26;width=768&#x26;dpr=4&#x26;quality=100&#x26;sign=308febb4&#x26;sv=1" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to [upload the sketch](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)(***OpenCatEsp32.ino***). \
  Use the latest OpenCatESP32 code to finish the setup. For example, to modify the code for ***Bittle*** as shown below:<br>

  <figure><img src="https://docs.petoi.com/~gitbook/image?url=https%3A%2F%2F1565080149-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F-MQ6a951Q6Jn1Zzt5Ajr-887967055%252Fuploads%252FGu37FwV2ge9LKHORqrUl%252Fimage.png%3Falt%3Dmedia%26token%3D6b0f5ed3-eb4b-4668-8f5a-3e7462718519&#x26;width=768&#x26;dpr=4&#x26;quality=100&#x26;sign=fa49fffa&#x26;sv=1" alt=""><figcaption></figcaption></figure>

After uploading, there are two methods to ***activate/deactivate*** the gesture mode:

* Serial Monitor
  * [Open the serial monitor](/arduino-ide/serial-monitor.md#biboard) and use the serial command "***XG***" to activate the gesture mode.
  * Open the serial monitor and use the serial command "***Xg***" to deactivate the gesture mode.
* Mobile App
  * Create [a mobile app command](https://docs.petoi.com/mobile-app/controller#create-a-single-command) called "**Activate** gesture" and use the code: *`X71`*
  * Create a mobile app command called "**Deactivate** gesture" and use the code: *`X103`*

### Hardware setup

#### BiBoard V0&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FuoKKjkPdac7DMDJ34BUu%2FGesture_BiBoard.png?alt=media&amp;token=c75a5c6e-7f1b-4053-84a7-70117b4409e5" alt=""><figcaption></figcaption></figure>

#### BiBoard V1

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FENOPj8H9HKn6zsnnbUVq%2F%E6%89%8B%E5%8A%BF%E4%BC%A0%E6%84%9F%E5%99%A8%E8%BF%9E%E6%8E%A5%E5%9B%BE.png?alt=media&amp;token=26c6a699-cc22-4185-9023-974e1a67c955" alt="" width="375"><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZ0h16nB5ivYFXYfV1dEW%2FGesture_BiBoard_V1.jpg?alt=media&amp;token=df702767-4b56-4c5b-a2c5-fa455710a89a" alt=""><figcaption></figcaption></figure>

For specific use, the end connected to the sensor can be fixed on the robot's head (included in Bittle's mouth or attached to the top of Nybble's head); of course, you can also use your creativity according to your needs.

## Testing code

If you want to test a gesture sensor's function alone or learn more about its principles. You can upload the demo sketch([**ModuleTests/testGesture**](https://github.com/PetoiCamp/OpenCatEsp32/tree/main/ModuleTests/testGesture)) using the Arduino IDE.

{% hint style="info" %}
Note:

Before uploading the demo sketch, you must first set up the development environment:

* [NyBoard](#prepare-the-arduino-uno-development-environment)
* [BiBoard](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)
  {% endhint %}

This testing sketch implements real-time printing of various directional gestures (up, down, left, and right) made by the user in front of the gesture sensor in the serial monitor.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FahxdZuxZemJ8wMCW86MV%2Fimage.png?alt=media&amp;token=ae21860f-9192-4372-94df-11e6ee79ba67" alt=""><figcaption></figcaption></figure>
