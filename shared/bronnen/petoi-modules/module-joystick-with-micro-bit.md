# module-joystick-with-micro-bit

| | |
|---|---|
| Link in de slides | (achter een foto op de slide 'What can I connect?', URL niet in de slidetekst) |
| Opgehaald van | https://docs.petoi.com/extensible-modules/joystick-with-micro-bit.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Joystick with Micro:Bit

{% embed url="<https://youtu.be/BRb4nQeWcdQ>" %}

This remote controller is a Micro: Bit-based gamepad. It includes a 4-direction joystick and four undefined buttons. To enhance the gaming experience, it is also paired with a buzzer and vibration motor. It is compact in appearance, comfortable in hand, and can be remotely controlled.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3hDz8QhenUXOx3BkeYAE%2Fimage.png?alt=media&amp;token=27ce6c09-a450-450d-99e2-4246ae7dcd4e" alt=""><figcaption></figcaption></figure>

## Hardware

{% hint style="info" %}
Micro: Bit V1 has a smaller memory. So, the full functionality requires **Micro: Bit V2**.
{% endhint %}

## Software setup

The Joystick's source code is now open-sourced. It can control Bittle X, Bittle X+Arm (Bittle with a robotic arm), and Nybble Q. For more information, please refer to our [GitHub repository](https://github.com/PetoiCamp/ESP32_Microbit_Controller).

You can download the program file([microbit-JoyStick.hex](https://raw.githubusercontent.com/PetoiCamp/ESP32_Microbit_Controller/refs/heads/main/microbit-JoyStick.hex)), then import the program to [the programming platform MakeCode](https://makecode.microbit.org) as follows:

{% hint style="info" %}
We recommend you use the **Chrome** browser.
{% endhint %}

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F5qmdwpuQcRDIVwYXbkUy%2Fimage.png?alt=media&amp;token=142631a6-16f5-4a98-89c5-efcf164ef696" alt=""><figcaption></figcaption></figure>

Alternatively, you can click "New Project" and drag the program file into the coding window to load it.&#x20;

### Download the program to the Micro: Bit V2

Connect your PC to the Micro: Bit V2 using a USB cable.

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/connect-microbit.gif)

After a successful connection, a disk drive named `MICROBIT` is recognized on the computer.

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/microbit-drive.png)

There are two ways to download the program to the Micro: Bit V2. You can choose either of these methods.

#### In the computer's file browser

This way is quite simple. Using your computer's file browser, click and hold the `.hex` firmware file. Drag it to the MICROBIT drive, which is located on the left side of the window, and then release the mouse button. This will download the `.hex` firmware file to the Micro:Bit V2 board.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fo7ekdbsH0TX66gvobqEI%2Fimage.png?alt=media&amp;token=f50e5bf0-fdfd-4960-8e10-f5358a4437f3" alt=""><figcaption></figcaption></figure>

#### In the MakeCode web page

Click on the bottom left corner of the ![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-01.png) button， Select `Connect Device`.

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-02.png)

Click ![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-03.png) button.

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-04.png)

Click![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-05.png)

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-06.png)

Select `BBC micro:bit CMSIS-DAP` in the pop-up window and then select Connect. At this point, our Micro: Bit has connected successfully.

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXhWjqLKPHao8DCKbWhlp%2Fimage.png?alt=media&amp;token=f270a060-9d8e-4286-bead-9efd52225451" alt=""><figcaption></figcaption></figure>

Click to download the program.

![](https://wiki-media-ef.oss-cn-hongkong.aliyuncs.com/docs/microbit/interesting-case/microbit-smart-climate-kit/cases-libraries/images/download-08.png)

## How to use&#x20;

1. [Upload the newest firmware](https://docs.petoi.com/upload-firmware) to the robot (mainboard type: **BiBoard**)
2. Install 2 x #7 AAA batteries and plug in the Micro: Bit V2 to the remote controller. Then, power on the remote controller as follows:\
   ![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FChBraCMq4X3tTpo5xkwN%2Fimage.png?alt=media\&token=ef72bf50-b778-4de0-882e-6097e180c20c)<br>
3. Power on the robot. During bootup, it can connect to the controller automatically via Bluetooth.\
   If there are many remote controllers and robots, the connection is one-to-one and first-come, first-served.

{% hint style="info" %}
**Timed lock feature**

This feature limits the play time for each user during exhibitions or science festivals. It is deactivated by default.

After normal startup and Bluetooth connection, you can activate the limited-time usage function for the controller by pressing and holding the middle Logo (touch button) on the Micro:bit while keeping the controller upright (with the left joystick at the bottom). Once activated, the controller will send a rest command to the robot every 20 minutes and no longer respond to subsequent operations. The LED indicator matrix will dynamically display an hourglass pattern, as shown in the figure below:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FAGA5p1kDuvQIzQQMx1ng%2Fimage.png?alt=media&amp;token=b66cb81f-bcae-49dc-89eb-0446e7fd6b8e" alt="" data-size="original">

You can reset the countdown and reactivate the controller using the same operation described above. The controller will play a prompt tone, and the LED indicator matrix will display an animation of an hourglass reversing.

Once the limited-time feature is activated, it can only be turned off by rebooting the controller. After the controller restarts, you must reset the robot (by clicking the **reset** button on the mainboard) or reboot the robot to reconnect.
{% endhint %}

## Controller function introduction

### To control Bittle X+Arm (with robot arm):

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FbuMKtuoBOPnmYBulyQks%2Fimage.png?alt=media&amp;token=d31b87a4-d497-4114-b3bd-95e6d71acfee" alt=""><figcaption></figcaption></figure>

### Demo

{% embed url="<https://youtu.be/QLI-x_8qO98>" %}

### To control Bittle X:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FJdNqowDJ84rXpap4IX8h%2FBittleX_en.png?alt=media&amp;token=dfd93147-2d05-445f-bf45-d1fb3a3717c2" alt=""><figcaption></figcaption></figure>

### To control Nybble Q:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FVJuNUefm7h57EjGCNPL5%2FNybbleQ_en.png?alt=media&amp;token=bc5b62d1-d62e-4bc5-b039-42360756d5c6" alt=""><figcaption></figcaption></figure>
