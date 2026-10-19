# module-ir-distance-sensor-double-infrared-reflection-sensor

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/ir-distance-sensor-double-infrared-reflection-sensor.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# IR Distance Sensor(Double Infrared Reflection Sensor)

{% embed url="<https://youtu.be/oVxrlVOkKWA>" %}

## Function introduction

This module integrates two IR distance sensors; it measures distance through reflected light waves and is used to detect the presence of an object within a specific range. The sensor comprises an IR LED and a photosensor (phototransistor) pair. The light emitted by the IR LED is reflected by any object placed in front of the sensor, and this reflection is detected by the photosensor(phototransistor). Any white (or lighter) colored surface reflects more than a black (or darker) colored surface. It is suitable for measuring complex objects, such as tracing an object.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FsA3R4rP96roXiMB2Oijy%2FIRdistance_New.png?alt=media&amp;token=322c42c8-2eae-461e-8ab6-e7157dedf1e0" alt=""><figcaption></figcaption></figure>

## NyBoard

### Software setup

There are two methods to upload the infrared distance mode firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader ](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware)within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **InfraredDistance**, so press the **Upgrade the Firmware** button. \
  For example, Nybble, NyBoard\_V1\_2, COM5 as follows:<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FSpaHFKf10f7iMshNuNH9%2Fimage.png?alt=media&amp;token=3c86d5bb-dadc-444c-8c75-628485a006dc" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software)  to upload and modify the source code.&#x20;

Install the latest version of the **Adafruit NeoPixel** library using the Arduino IDE.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9m1NirKNtksZeZcprKyw%2Fimage.png?alt=media&amp;token=c92317c3-7f16-4282-8a86-ed56d80a9964" alt=""><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3UkBsPtEogLt3aIfXdAR%2Fimage.png?alt=media&amp;token=b00c9f57-51bf-47f6-a71a-2ccd2e0158de" alt=""><figcaption></figcaption></figure>

The code using this sensor has been integrated into the [**OpenCat**](https://github.com/PetoiCamp/OpenCat) project. Uncomment the line **`#define DOUBLE_INFRARED_DISTANCE`**  in the **OpenCat.ino**, as shown in the figure below, and use the Arduino IDE to upload the sketch to the robot main board. The sketch can reproduce the example function of integrating the robot action.

#### Prepare the Arduino UNO development environment.

With **NyBoard V1\_\***, you can choose **Arduino Uno**.&#x20;

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXDvIUhP1OotHdF3rFSZN%2Fimage.png?alt=media&amp;token=4170cb44-69cd-4d52-9701-83618dbfb59c" alt=""><figcaption></figcaption></figure>

#### Modify the code in the OpenCat.ino

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9LPBQsNCVFROdLeL13ZR%2Fimage.png?alt=media&amp;token=f941ebe1-e57f-4fb8-bdbf-5795601ef687" alt=""><figcaption></figcaption></figure>

### Hardware setup

Connecting to the NyBoard with wire as shown in the following picture:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fy1gRNJLdDcV0mVi1ZNvH%2FIR_Distance_Sensor.jpg?alt=media&amp;token=445a04c1-c618-43c4-9ab8-bb0c1c098d6f" alt=""><figcaption></figcaption></figure>

## BiBoard

### Software setup

There are two methods to upload the firmware :

* Using the Petoi Desktop App
* Using the Arduino IDE

#### Petoi Desktop App

* You can use the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader#select-the-correct-options-to-upload-the-latest-firmware) within the Petoi Desktop App.\
  Please select the correct ***Product*** type, ***Board version***, and ***Serial port*** according to your actual use. The mode should be **Standard**, so press the **Upgrade the Firmware** button. \
  For example, Bittle, BiBoard\_V0\_2, COM5 as follows:<br>

  <figure><img src="https://docs.petoi.com/~gitbook/image?url=https%3A%2F%2F1565080149-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F-MQ6a951Q6Jn1Zzt5Ajr-887967055%252Fuploads%252FaleqWtxk5PSH9bWe9CfF%252Fimage.png%3Falt%3Dmedia%26token%3Dc92b21ff-992f-4163-a981-86078e26eedd&#x26;width=768&#x26;dpr=4&#x26;quality=100&#x26;sign=308febb4&#x26;sv=1" alt=""><figcaption></figcaption></figure>

#### Arduino IDE

* You can use [Arduino IDE](https://www.arduino.cc/en/software) to [upload the sketch](https://docs.petoi.com/arduino-ide/upload-sketch-for-biboard#id-2.-set-up-biboard)(***OpenCatEsp32.ino***). \
  Use the latest OpenCatESP32 code to finish the setup. For example, to modify the code for ***Bittle*** as shown below:<br>

  <figure><img src="https://docs.petoi.com/~gitbook/image?url=https%3A%2F%2F1565080149-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252F-MQ6a951Q6Jn1Zzt5Ajr-887967055%252Fuploads%252FGu37FwV2ge9LKHORqrUl%252Fimage.png%3Falt%3Dmedia%26token%3D6b0f5ed3-eb4b-4668-8f5a-3e7462718519&#x26;width=768&#x26;dpr=4&#x26;quality=100&#x26;sign=fa49fffa&#x26;sv=1" alt=""><figcaption></figcaption></figure>

After uploading, there are two methods to ***activate/deactivate*** the infrared distance mode:

* Serial Monitor
  * [Open the serial monitor](/arduino-ide/serial-monitor.md#biboard) and use the serial command "***XD***" to activate the infrared distance mode.
  * Open the serial monitor and use the serial command "***Xd***" to deactivate the infrared distance mode.
* Mobile App
  * Create [a mobile app command](https://docs.petoi.com/mobile-app/controller#create-a-single-command) called "**Activate infrared distance**" and use the code: *`X68`*
  * Create a mobile app command called "**Deactivate infrared distance**" and use the code: *`X100`*

### Hardware setup

#### BiBoard V0

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FnB1cHV2T0YGUlBsfivrQ%2FDoubleIRdistance_BiBoard.png?alt=media&amp;token=1330b25d-f647-4483-907e-137804906a1a" alt=""><figcaption></figcaption></figure>

#### BiBoard V1

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FwmnjVOAtIhqNKY5b0HrH%2F%E7%BA%A2%E5%A4%96%E4%BC%A0%E6%84%9F%E5%99%A8%E8%BF%9E%E6%8E%A5%E5%9B%BE.png?alt=media&amp;token=b7033b7e-13c0-4cda-b52b-80cdf3ed0151" alt="" width="375"><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FMG3LWxX6HuOitMBoaPpi%2FIRdistance_BiBoard_V1.jpg?alt=media&amp;token=4e8bcac5-3879-4294-8486-a4168b177390" alt=""><figcaption></figcaption></figure>

For specific use, the end connected to the sensor can be fixed on the robot's head (included in Bittle's mouth or attached to the top of Nybble's head). Of course, you can also use your creativity according to your needs.

## Testing code

If you want to test this sensor's function alone or learn more about its principles. You can use the Arduino IDE to upload the demo sketch(**testDoubleInfraredDistance.ino**) :

* [For NyBoard](https://github.com/PetoiCamp/OpenCat/tree/main/ModuleTests/testDoubleInfraredDistance)
* [For BiBoard](https://github.com/PetoiCamp/OpenCatEsp32/tree/main/ModuleTests/testDoubleInfraredDistance)

This demo sketch implements real-time printing of the analog values (rL, rR) and data that have been processed (dL,dR) of the two analog pins (***A2*** and ***A3*** for **NyBoard** / ***34*** and ***35*** for **BiBoard**) in the [serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor). You can also use the serial plotter to view the two analog pins (***A2*** and ***A3*** for **NyBoard** / ***34*** and ***35*** for **BiBoard**) more intuitively. The waveform graph is generated by the analog value of the pin output along the time axis.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FwQvjRMIN3wGiz7abkn9X%2Fimage.png?alt=media&amp;token=5453f71e-ddaf-47a9-ba20-4db39d471e5c" alt=""><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F7GKM7TgZmV9IoD9QRFqY%2Fimage.png?alt=media&amp;token=0fd5ff71-2f1f-4a02-9abe-984db0758378" alt=""><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLRtyaFDtTccfIjuFxJcL%2Fimage.png?alt=media&amp;token=a3d833e1-1a86-44c5-8acf-5867d6e0feae" alt=""><figcaption></figcaption></figure>
