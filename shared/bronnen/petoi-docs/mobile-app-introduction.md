# mobile-app-introduction

| | |
|---|---|
| Link in de slides | docs.petoi.com/mobile-app/introduction |
| Opgehaald van | https://docs.petoi.com/mobile-app/introduction.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Introduction

📱🤖

Thanks for choosing Petoi's robot, Bittle or Nybble. This guide will help you set up your robot buddy and provide a simpler UI to calibrate the joints, control the robot, and program it. For advanced users, we recommend you keep the robot updated with the [OpenCat firmware](https://github.com/PetoiCamp/OpenCat) on Github for the best compatibility and the newest features.&#x20;

## Download and installation

The app works on both Android and iOS devices.

* [iOS 11+](https://apps.apple.com/us/app/petoi/id1581548095)
* [Android 4.4+](https://play.google.com/store/apps/details?id=com.petoi.petoiapp)

#### APK

For Android, you can also download the APK and install it on your phone.&#x20;

* The universal version(try this one first)\
  [v1.4.1-40-2-20251022-app-release.apk](https://github.com/PetoiCamp/MobileApp/releases/download/1.4.1/v1.4.1-40-2-20251022-app-release.apk)
* The **v8a** version of the app mainly supports most of the current new mobile phone models\
  [v1.4.1-40-2-20251022-app-arm64-v8a-release.apk](https://github.com/PetoiCamp/MobileApp/releases/download/1.4.1/v1.4.1-40-2-20251022-app-arm64-v8a-release.apk)
* The **v7a** version of the app is compatible with older mobile phone models\
  [v1.4.1-40-2-20251022-app-armeabi-v7a-release.apk](https://github.com/PetoiCamp/MobileApp/releases/download/1.4.1/v1.4.1-40-2-20251022-app-armeabi-v7a-release.apk)
* The **x86\_64** version of the app indicates that the APK is designed for Android devices using Intel or AMD 64-bit processors. This means the APK contains native code libraries optimized for the x86\_64 architecture, designed to improve performance and compatibility.\
  [v1.4.1-40-2-20251022-app-x86\_64-release.apk](https://github.com/PetoiCamp/MobileApp/releases/download/1.4.1/v1.4.1-40-2-20251022-app-x86_64-release.apk)

{% hint style="info" %}
If the Bluetooth dongle (which is plugged in NyBoard) blinks while the connection panel within the App shows a blank Bluetooth connection list, first check if you have given the Bluetooth and location permission to the App. If it still shows a blank list, you may try to install the previous stable version. \
[v1.4.0-37-1-app-release-20251006.apk](https://github.com/PetoiCamp/MobileApp/releases/download/1.4.0/v1.4.0-37-1-app-release-20251006.apk)
{% endhint %}

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FOPQOgY4hM3G0RUAVcRS4%2Fimage.png?alt=media\&token=5de7e42c-8e14-4c59-90ce-ff5592de78bb)

## Connect to your robot

You need to plug the [Bluetooth dongle](https://docs.petoi.com/modules/bluetooth-dual-mode) into the 6-pin socket on the **NyBoard**. Pay attention to the Bluetooth dongle's pin order. Long-press the button on the battery to turn on the robot's power.&#x20;

{% hint style="warning" %}
If the buzzer beeps repetitively after bootup or during use, the battery is low. Please charge it in time. The charging port is on one end of the battery.&#x20;
{% endhint %}

{% hint style="info" %}
If the main board is **BiBoard**, no need to plug the Bluetooth dongle.
{% endhint %}

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-legacy-files/o/assets%2F-MQ6a951Q6Jn1Zzt5Ajr%2F-MjZTVQG9FtL5GpEpRwK%2F-MjZV96lacYVzliIG6xN%2Fblue.jpg?alt=media\&token=99cb701d-2e10-4336-ab26-8965a0dff1dc)

The LED on the Bluetooth dongle should blink, waiting for a connection. Open the app and scan available Bluetooth devices. **Don't connect the robot with the phone's system-wide Bluetooth settings!** Connect the device with the name Bittle, Petoi, or OpenCat. Remember to open the Bluetooth service and grant the app access to the service. On some devices, you may also need to allow the location service for the app, though we are not using any of that information.

{% hint style="info" %}
On some Android OS, you need to activate the location service as following:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Ff7vweCW2RdlLH0vO0j0w%2Flocation%20service.png?alt=media&amp;token=2c23839f-2535-4f2e-bc9e-d5a7d6346bcc" alt="" data-size="original">
{% endhint %}

{% hint style="warning" %}
The app will send a greeting to the Bluetooth device and expects a response from the OpenCat firmware. You must install the full OpenCat code on your robot before connecting to the app. Otherwise, the app will consider it's "not a Petoi device". A pre-assembled robot should already have the firmware installed. Otherwise, you must configure it with Arduino IDE or the Desktop app.&#x20;
{% endhint %}

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-legacy-files/o/assets%2F-MQ6a951Q6Jn1Zzt5Ajr%2F-MjZTVQG9FtL5GpEpRwK%2F-MjZWU2EpJOmFcBOEKGH%2FconnectModel.png?alt=media\&token=3ba0659a-f8c5-481c-8a88-7c08449c19d5)

If Bluetooth is connected, its LED will light steadily. The robot will play a three-tone melody. If the robot doesn't respond or malfunctions later, press the reset button on the NyBoard to restart the program on the NyBoard.&#x20;

The App should automatically detect Nybble or Bittle with the latest OpenCat firmware. Otherwise, it will show the selections for Nybble or Bittle. The option "**Select a robot**" also can be re-visited in the control panel.

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FMMQVQoYLcUGlDt3J9ifx%2FControl_Cali_en.jpg?alt=media\&token=0c9a6f1d-c612-4de1-a284-a155324dee1f)
