# module-touch-sensor

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/touch-sensor.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Touch Sensor

{% embed url="<https://youtu.be/wDd5okeHDMA>" %}

## Function introduction

The sensor contains two touch parts (left and right) and can detect changes in capacitance when a finger approaches. This means the touch sensor will output a high level whether your finger touches lightly or presses hard. You can realize the function you want by judging the detected value (1 for high level, 0 for low level).

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FCr4NM3ErzF1Zxb2DRZfk%2FDoubleTouch_New.png?alt=media&amp;token=08dc7c74-eaaf-451f-9ef8-d6c213e0e59a" alt=""><figcaption></figcaption></figure>

## NyBoard

### Hardware setup

Connecting to the NyBoard with wire as shown in the following picture, connect to the NyBoard Grove interface, which includes D6, D7:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FndcBuaZ8LXgqvZaUvKoJ%2FPANA0498%20%E6%8B%B7%E8%B4%9D.jpg?alt=media&amp;token=54d06114-2df5-4063-8bb4-0afb97a28533" alt=""><figcaption></figcaption></figure>

### Software setup

There are two methods to upload the touch mode firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader ](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware)within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Touch**, so press the **Upgrade the Firmware** button. \
  For example, Nybble, NyBoard\_V1\_2, COM5 as follows:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FTqufPF0AgOuhtbWFuEj8%2Fimage.png?alt=media&amp;token=8f8b8ae1-5ec5-4786-bf45-e9ffdbcbaa8d" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to upload and modify the source code.&#x20;

The code using this sensor has been integrated into the [**OpenCat**](https://github.com/PetoiCamp/OpenCat) project. Uncomment the line **`#define DOUBLE_TOUCH`**  in the **OpenCat.ino**, as shown in the figure below, use the Arduino IDE to upload the sketch to the robot main board, which can reproduce the example function of integrating the robot action.

#### Prepare the Arduino UNO development environment.

With **NyBoard V1\_\***, you can choose **Arduino Uno**.&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXDvIUhP1OotHdF3rFSZN%2Fimage.png?alt=media&amp;token=4170cb44-69cd-4d52-9701-83618dbfb59c" alt=""><figcaption></figcaption></figure>

For example,  to modify the code for ***Bittle*** as shown below:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FBenMEHhRC9iVEql4rdRd%2Fimage.png?alt=media&amp;token=488340c4-da65-46c7-8790-e71d24bbf78d" alt=""><figcaption></figcaption></figure>

#### Arduino module test code

If you want to test a touch sensor's function alone or learn more about its principles. You can use the Arduino IDE to upload the test code(**testDoubleTouch.ino**):

The test code is in the **OpenCat** project source code ([ModuleTests/testDoubleTouch](https://github.com/PetoiCamp/OpenCat/blob/main/ModuleTests/testDoubleTouch/testDoubleTouch.ino))

This demo sketch implements real-time printing of the detection values of D6 and D7 pins in the [serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor):&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F55olenuVmTeBwzFP5tvY%2FTouch_serial_monitor.png?alt=media&amp;token=f5adb967-1a2a-4299-bdf8-1ea0b5910c61" alt=""><figcaption></figcaption></figure>

#### Mind+ Demo

1. &#x20;You can upload the firmware via the Petoi Desktop App:

   ![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FwETLwGeqX6qTrtxw3jS9%2Fimage.png?alt=media\&token=8f193192-0fab-442f-8497-88d404f73833)

{% hint style="info" %}
Or you can upload the **OpenCat.ino** as follows, uncomment the line **`#define GROVE_SERIAL_PASS_THROUGH`** in the **OpenCat.ino:**

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fgtn3N4DylaG35o8OmvC1%2Fimage.png?alt=media&amp;token=eb98fbed-0f71-433b-a2a5-18b9553f4b92" alt="" data-size="original">
{% endhint %}

{% hint style="success" %}
For BiBoard, you can skip this step.
{% endhint %}

&#x20;2\.    Follow [the instructions](https://docs.petoi.com/block-based-programming/petoi-coding-blocks#import-petoi-mind+-extension-library) to import the Petoi Coding Blocks in the app **Mind+**, and load the Mind+ code file.

3. &#x20;Connect the robot and computer with the [USB adapter](https://docs.petoi.com/communication-modules/usb-downloader-ch340c)(USB uploader) or [Bluetooth module](https://docs.petoi.com/communication-modules/dual-mode-bluetooth).
4. &#x20;Power on the robot and click the **Run** button ![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fabs4l2yCGlies3GJQw2n%2Fimage.png?alt=media\&token=7c812eb5-bd0f-4549-840d-ae4044967a2a) in **Mind+.**<br>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FcUEkw0PPer4dOOr730yo%2FTouch_mind%2B.png?alt=media&amp;token=6c4de59f-2e86-4f1d-883e-3be549b1fe37" alt=""><figcaption></figcaption></figure>

#### Mind+ Demo code

<https://github.com/PetoiCamp/Petoi_MindPlusLib/blob/main/examples/NyBoard/DoubleTouch_NyBoard.mp>

## BiBoard

### Hardware setup

#### BiBoard V0&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F2tLqArkIjBTxgUlGZbWM%2FDoubleTouch_BiBoard.png?alt=media&amp;token=581e71f6-b74c-4dbb-92d3-8897e564f1cf" alt=""><figcaption></figcaption></figure>

#### BiBoard V1

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FV4ojCpX0cdIZzxB4nB3f%2F%E8%A7%A6%E6%91%B8%E4%BC%A0%E6%84%9F%E5%99%A8%E8%BF%9E%E6%8E%A5%E5%9B%BE.png?alt=media&amp;token=b3cfd6a1-f1c6-4968-81e5-b7652a9701df" alt="" width="375"><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F5F9qW1HCWvPIUXhGnGbv%2FDouble_Tonch_BiBoard_V1.jpg?alt=media&amp;token=ec419ec8-13dc-4ba2-b946-c7b98687807a" alt=""><figcaption></figcaption></figure>

For specific use, the end connected to the sensor can be fixed on the robot's head (included in Bittle's mouth or attached to the top of Nybble's head). Of course, you can also use your creativity according to your needs.

### Software setup

There are two methods to upload the firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.

  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Standard**, so press the **Upgrade the Firmware** button. \
  For example, Bittle, BiBoard\_V0\_2, COM5 as follows:

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FaleqWtxk5PSH9bWe9CfF%2Fimage.png?alt=media&amp;token=c92b21ff-992f-4163-a981-86078e26eedd" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to [upload the sketch](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)(***OpenCatEsp32.ino***).&#x20;

  Use the latest OpenCatESP32 code to finish the setup. For example,  to modify the code for ***Bittle*** as shown below:<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FGu37FwV2ge9LKHORqrUl%2Fimage.png?alt=media&amp;token=6b0f5ed3-eb4b-4668-8f5a-3e7462718519" alt=""><figcaption></figcaption></figure>

After uploading, there are two methods to ***activate/deactivate*** the touch mode:

* Serial Monitor
  * [Open the serial monitor](/arduino-ide/serial-monitor.md#biboard) and use the serial command "***XT***" to activate the touch mode.
  * Open the serial monitor and use the serial command "***Xt***" to deactivate the touch mode.
* Mobile App
  * Create [a mobile app command](https://docs.petoi.com/mobile-app/controller#create-a-single-command) called "**Activate touch**" and use the code: *`X84`*
  * Create a mobile app command called "**Deactivate touch**" and use the code: *`X116`*

#### Arduino module test code

The test code is in the **OpenCatESP32** project source code ([ModuleTests/testDoubleTouch](https://github.com/PetoiCamp/OpenCatEsp32/blob/main/ModuleTests/testDoubleTouch/testDoubleTouch.ino))

#### Mind+ Demo code

<https://github.com/PetoiCamp/Petoi_MindPlusLib/blob/main/examples/BiBoard/DoubleTouch_BiBoard.mp>
