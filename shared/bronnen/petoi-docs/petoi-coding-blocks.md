# petoi-coding-blocks

| | |
|---|---|
| Link in de slides | https://docs.petoi.com/block-based-programming/petoi-coding-blocks |
| Opgehaald van | https://docs.petoi.com/block-based-programming/petoi-coding-blocks.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Petoi Coding Blocks

How to use the extension library specially developed for the Petoi robot in Mind+

{% hint style="info" %}

## We are shifting our block-based programming interface to [Web Coding Blocks](/web-block-base-programming/petoi-web-coding-blocks.md), a dedicated platform for Petoi robots that our team developed and maintains.

{% endhint %}

## Prepare Mind+

* Download the latest version from the [Mind+ official website](https://mindplus.cc/en/download.html).
  * For Windows: Mind+ version **>= V1.7.0**
  * For Mac O&#x53;**:** Mind+ version **>= V1.7.3 RC2.0**

{% hint style="warning" %}
Mind+ is a complex IDE designed for many 3rd-party products. The new version (V2.X) incorporates numerous changes to the UI and underlying drivers. We recommend using the previous version (V1.X), which matches our manual. \
![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FPiN2R5eaYKL8Mh0rCzI0%2Fimage.png?alt=media\&token=3b825deb-097b-4827-bf21-b017419bf2e1)
{% endhint %}

{% hint style="warning" %}
If you can not download the software from Mind+'s official website, you can download a stable version from [the Google Drive folder](https://drive.google.com/drive/folders/1V9WSnNiEOKZznP05W_RPxUD0TqAFFK7T). However, we strongly recommend that you download and use the official latest version.
{% endhint %}

{% hint style="info" %}
**For macOS only:** If you have already installed the old Mind+ version (**<=**&#x56;1.7.2 RC3.0), we recommend that

1. You uninstall it first
2. Delete this folder /Users/\[vour username]/Documents/mindplus-pv/environment/Python3.6.5.64/ib/python3.6/site-packages/
3. Download and install the latest version of **Mind+**.
   {% endhint %}

* After the installation is complete, you can open Mind+

{% hint style="info" %}
If the default installation language is Chinese, you can switch to **English** as follows:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F76FF99j3mZ03G5VSDdPT%2FSwithEnglish.png?alt=media&amp;token=546d4aa9-3263-4c19-bac5-bb269509bbe4" alt="" data-size="original">
{% endhint %}

## Watch the video tutorials

We provide [a series of video tutorials](https://www.youtube.com/playlist?list=PLHMFXft_rV6POrzm8O12Nybdy1-FS1ymg) on using Petoi Coding Blocks with [the free Scratch-like robotics coding curriculum](https://www.petoi.com/pages/free-quadruped-robotics-curriculum-scratch-coding).   Be sure to click next to go through all the videos.

{% embed url="<https://www.youtube.com/playlist?list=PLHMFXft_rV6POrzm8O12Nybdy1-FS1ymg>" %}

## Prepare Petoi Robot

Please follow the instructions in the subpages to prepare according to the robot's mainboard.

## Import Petoi Mind+ extension library

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FM067JlcUJoBWJES8XWDw%2Fimage.png?alt=media&amp;token=f2331863-f03a-4daa-930f-b3fbb1567d39" alt=""><figcaption></figcaption></figure>

Paste the GitHub URL(<https://github.com/PetoiCamp/Petoi_MindPlusLib>) in the text box of the import interface:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F9DZWqwlc3IceqvGuGAE8%2Fimage.png?alt=media&amp;token=ca2e8841-d4fc-4efc-961a-2f1881dddd5d" alt=""><figcaption></figcaption></figure>

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FTAXOhGWiAFpSbsfhE2Gu%2Fimage.png?alt=media&amp;token=116a9b0d-e0a4-4048-9da2-b084b203ec16" alt=""><figcaption></figcaption></figure>

## Programming and Running

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FXQveDsHbsfe2GOIRffKM%2Fimage.png?alt=media&amp;token=2ffda9c1-2f1b-47e8-8e25-e4fa8943e1ff" alt=""><figcaption></figcaption></figure>

{% hint style="warning" %}
Petoi Coding Blocks is a user-extended library of Mind+.&#x20;

If you open **Mind+** by double-clicking the icon![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FB4ohi41Bllp4OsNWZMMh%2Fimage.png?alt=media\&token=5fd0db57-f11c-4ed4-bd1a-56c55cc44ce7), it will not automatically load this extension library, and you need to re-import it manually every time you open the app.&#x20;

If you open Mind+ by double-clicking the code file(suffix **mp** or **sb3**) that uses this extension library or load these code files after opening Mind+, Mind+ will automatically load this extension library.
{% endhint %}

## The principle and process

This extension library can control the robot without compiling and uploading the code to the robot's main board. Click the "Run" button directly to run the program on the Python level and send instructions to the robot's serial port. If you need to stop the program while running, you can click the "Stop" button anytime. The process of the program can be divided into three steps:

1. &#x20;Open the serial port
2. &#x20;Control the robot
3. &#x20;Close the serial port

## The instructions for blocks

### Open the serial port

There are two ways to open the serial port:

* Automatically identify and open the serial port\
  ![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FFIKBc1voBqyzjOW5iYm4%2Fimage.png?alt=media\&token=578f4830-8b8b-4c4d-a9cd-0327349fe781)
* Enter the name of the serial port to open the serial port\
  ![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZHrCnGPcWeCM1ks2eTpA%2Fimage.png?alt=media\&token=a0721c60-aa3d-4bc4-b8d9-02b58b480818)

{% hint style="info" %}
If it fails to open the serial port, you can refer to the printed information in the terminal window to replace the name of the serial port:

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FrZZTebKm74EdgzUD9Vpy%2Fimage.png?alt=media\&token=f572ed0f-9be2-44ca-bd55-2e8efcffef37)
{% endhint %}

### Deactivate Gyro

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fs4jRdN82xSkC4g90PEbp%2Fimage.png?alt=media\&token=5bdb97b3-17f8-4526-8392-0295c035ea71)

When the gyroscope function is turned on, the robot can balance its body in real-time. It may be seen that when the robot is doing preset actions (especially when performing more violent actions), the body will shake back and forth, and even the body will tip over. The robot will automatically perform recovery actions, which may disrupt your preset steps.

If the uploaded sketch is **Mind+ mode** sketch(**`#define GROVE_SERIAL_PASS_THROUGH`** this line is activated), the gyroscope function will be turned off, and the robot will not be able to balance or auto-recover, so there is no need to add this block.

{% hint style="info" %}
If the robot is in [**standard mode**](https://docs.petoi.com/arduino-ide/upload-sketch-for-nyboard#11.-the-module-macro-in-the-code), you'd better deactivate the Gyro after the serial port-opening block. It deactivates the gyroscope function to prevent the robot from performing balance feedback actions in real-time. For example:

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FPujjprGoNWpR0bM8phkJ%2Fimage.png?alt=media\&token=ef9da238-024a-41bf-9d50-8ba206530dee)
{% endhint %}

### Perform inherent skills

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FmAohz3kqDf13igcnT8ag%2Fimage.png?alt=media&amp;token=b3cf9926-1f53-4d88-92a3-5dca7e6414ca" alt=""><figcaption></figcaption></figure></div>

Use this block to let the robot perform skills pre-built on the robot's main board. Skills from "**sit**" to "**zero**" are **postures** (containing only one action frame).  Skills from "**boxing**" to "**sniff**" are **behaviors** (containing multiple posture frames and are performed only once).  Skills from "**stepping**" to "**trotRight**" are **gaits** (containing multiple posture frames, and are repeated in periodical loops until stopped).&#x20;

After finishing the current block's task, the program will wait a short time (delay xx seconds) before moving to the next block.&#x20;

### Perform the last skill exported from the Skill Composer

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FyfHnLA7BZCSXnUFVgHOJ%2Fimage.png?alt=media&amp;token=192c15ff-2d98-4926-9b48-52894a162693" alt=""><figcaption></figcaption></figure></div>

Use this block to let the robot perform the last skill exported from the [Skill Composer](https://docs.petoi.com/desktop-app/skill-composer#export-the-skill).&#x20;

{% hint style="info" %}
It is equivalent to inputting the serial command 'T' in the [serial monitor](https://docs.petoi.com/arduino-ide/serial-monitor) and then delaying the preset time.
{% endhint %}

### Perform the skill in the file

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FixUdBCUW7s0rI0Ql9Inu%2Fimage.png?alt=media&amp;token=13778e68-c3e9-45ab-8f89-e45e04452c0a" alt=""><figcaption></figcaption></figure></div>

Use this block to let the robot perform the skill in the skill files, which are in the following directory:

* **Windows**: C:\Users\\{your user name}\\.config\Petoi\SkillLibrary\\{model}
* **MacOS** : /Users/{your user name}/.config/Petoi/SkillLibrary/{model}
* **Linux**: /home/{your user name}/.config/Petoi/SkillLibrary/{model}

The folder name **{model}** is Bittle or Nybble. When [exporting](https://docs.petoi.com/desktop-app/skill-composer#export-the-skill) a skill file from the **Skill Composer**, it will automatically save the skill file to this directory.

{% hint style="info" %}
Tips: you can also copy & paste the [SkillLibrary](https://github.com/PetoiCamp/OpenCat/tree/main/SkillLibrary) folder from the source code of the OpenCat project on GitHub to the ***.config/Petoi*** directory. Therefore, you can use some sample skills for your Mind+ program, and there is no need to use the export function in the Skill Composer.

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FnHCJfsOcrwEK9P8NXYny%2Fimage.png?alt=media\&token=c4d0ac7b-0761-4406-9f1c-6b231cbe4c20)
{% endhint %}

{% hint style="info" %}
The folder **.config** is a hidden directory on MacOS/Linux but can be visited in the terminal or through a specific view setting:

* MacOS\
  open the directory /Users/{username} in Finder, then press the “**Command**” + “**Shift**” + “**.**” (period) keys at the same time.<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fi1bvYygyLl333W4wYYCI%2Fimage.png?alt=media&amp;token=4835c116-be30-46f8-9e7d-053249b580e3" alt=""><figcaption></figcaption></figure>

{% endhint %}

### Rotate joints in a sequence.

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FqVQO6v6iaU9sWra22DOc%2Fimage.png?alt=media&amp;token=f600cc89-7977-4f39-b79c-0cbf9847fd83" alt=""><figcaption></figcaption></figure></div>

Use this block to control one joint or multiple joints to rotate in sequence. There are several ways to use the blocks for reference:

* Controls individual joint rotations to an absolute angle value.<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3DCHpXSEBP9LVIl3Jvm7%2Fimage.png?alt=media&amp;token=f5143c64-a5a8-4e1d-8938-1b6fbe855b64" alt=""><figcaption></figcaption></figure>
* Controls individual joint rotations to a relative angle value.<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FcDjKp9hs9LzDGZaAQpSH%2Fimage.png?alt=media&amp;token=6e08ed26-562d-4200-a38e-105882f0bd6d" alt=""><figcaption></figcaption></figure>
* Control multiple joints to rotate sequentially to **absolute** angle values or **relative** angle values.<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FYTdKuYHtj6HhPZP6q9E1%2Fimage.png?alt=media&amp;token=054a6430-569d-4760-828e-a4058e2388fa" alt=""><figcaption></figcaption></figure>
* Use the joint angle list to control multiple joints to rotate to absolute angle values in a sequence.<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FEIlvVBe7zkToDeFTkGrI%2Fimage.png?alt=media&amp;token=3615ceca-a8df-42af-a317-09460f0ff13a" alt=""><figcaption></figcaption></figure></div>

{% hint style="info" %}

* <img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZgsqCYieFm87l9CUT93x%2Fimage.png?alt=media&amp;token=53400d44-f38f-4da4-a3d9-c7d9a8e95328" alt="" data-size="original">, <img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FBkbYNDiwvBgvMR5kHa75%2Fimage.png?alt=media&amp;token=f18690cd-0c99-4cea-857d-4866c52e2e9f" alt="" data-size="original">represents a list consisting of a [joint index](https://docs.petoi.com/petoi-robot-joint-index) and an angle value. For example, \[Head panning to 30 degrees] represents the list \[0, 30].
* <img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F6zKRSaaI0EFJT7jXMNh3%2Fimage.png?alt=media&amp;token=f9c48168-00b1-4a71-98a0-90e97260a7f4" alt="" data-size="original">\
  It consists of one or more pairs of[ joint index](https://docs.petoi.com/petoi-robot-joint-index) + angle value, and the specific format is as follows: \
  \[joint index, angle value, joint index, angle value...]
  {% endhint %}

### Rotate joints simultaneously&#x20;

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FvXrAKbyj9iDAJm7EYx7L%2Fimage.png?alt=media&amp;token=6098859d-57d0-431f-8926-b402f1f70b57" alt=""><figcaption></figcaption></figure></div>

Using this block can control multiple joints to rotate at the same time. There are several ways to use the blocks for reference:

* Control multiple joints to rotate to absolute angle values or relative angle values at the same time<br>

  <figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FhZxUg6OoHsKYp56cK7IK%2Fimage.png?alt=media&amp;token=8e5885c6-f328-4392-b70d-3e12bbbe1824" alt=""><figcaption></figcaption></figure>
* Use the joint angle list to control the simultaneous rotation of multiple joints to absolute angle values.<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FxGzW0LMX2SbKdDpmaUP6%2Fimage.png?alt=media&amp;token=cd007501-533e-4366-9c1d-11496904b436" alt=""><figcaption></figcaption></figure></div>

### Get the current angle value of a joint.

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FB4doLLUo6aHXZcR5fNMS%2Fimage.png?alt=media&amp;token=0d06f06f-6aca-47cd-9697-52f2bc8cccf6" alt=""><figcaption></figcaption></figure></div>

Use this block to get the current angle value of the selected joint. It is recommended to assign it to a variable first and then use the variable and algorithm to control other joints to rotate.

{% hint style="info" %}
The return value of this block is only an angle value, which cannot be filled in the "Turn sequentially" and "'Turn simultaneously" blocks alone.
{% endhint %}

Demo code:

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLSSvP2gdZmoWCXUbk88d%2Fimage.png?alt=media&amp;token=841d0996-b41b-4d10-bc60-de35607329db" alt=""><figcaption></figcaption></figure>

{% file src="/files/dTxtuiDyT9RbbPkwqO4S" %}

### Transform to frame

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FoxnF7bx3JFjLo2UADdN2%2Fimage.png?alt=media&amp;token=8fb4af49-b1e5-4daa-adfb-b7b60183943e" alt=""><figcaption></figcaption></figure></div>

Use this block to control all joints to rotate at the same time. Please use it with the "Action frame" block. As shown below:

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FTKQtWCczMhfuaN54Bub7%2Fimage.png?alt=media&amp;token=a838e1b8-81fa-4f69-a306-0ea2b21250e6" alt=""><figcaption></figcaption></figure></div>

{% hint style="info" %}
The "Action frame" block represents a list of 16 angle values. Each angle value corresponds to the absolute angle value to which the corresponding [joint index](https://docs.petoi.com/petoi-robot-joint-index) servo rotates.
{% endhint %}

### Play a melody

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FOo2UQBfXrdxpZY5Oy8F6%2Fimage.png?alt=media\&token=84f48bfe-91bf-4dc1-8047-769cf3de4d27)

Use this block to control the robot to play music. There are several ways to use  blocks together for reference:

* A list made up of multiple "Tone + Duration" blocks<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FPSsenMeEG4Q5hx9KNZoN%2Fimage.png?alt=media&amp;token=797b287d-3874-44b3-81be-aa9a8f980f66" alt=""><figcaption></figcaption></figure></div>
* Using a tone duration list<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FZbut4OALuYzDoRoaQts1%2Fimage.png?alt=media&amp;token=5a8b45cc-c2b6-4f11-ae77-0bc6ff6b77bd" alt=""><figcaption></figcaption></figure></div>

{% hint style="info" %}
![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FLogOjCaoQBRIxYIjkn7v%2Fimage.png?alt=media\&token=d55566d6-a2dd-4909-b742-593785316df0)

Consists of one or more pairs of Tone + Duration, the specific format is as follows:

\[tone, duration, tone, duration, tone, duration...]
{% endhint %}

#### Tutorials

For more detailed tutorials, please refer to [Melody Creation](https://docs.petoi.com/applications/melody-creation).

### Execute a serial command

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FOXar2Y4DHB7PKbtIby3M%2Fimage.png?alt=media&amp;token=19922e1d-2087-4940-8c64-d83d932b2895" alt=""><figcaption></figcaption></figure></div>

Use this block to send a serial command to the robot, which can provide you with more and more flexible control methods. For example, you can input "**kkcL**" (kick the left front leg), and "**khiR**" (raise the right front leg to say hello). For more serial port commands, please refer to [the serial protocol](https://docs.petoi.com/api/serial-protocol).&#x20;

### Write analog value

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FD0vF5M854vNziizbmyyn%2Fimage.png?alt=media&amp;token=58a41e82-c068-4708-a5d6-a40cd1c1f327" alt=""><figcaption></figcaption></figure></div>

Use this block to write an analog value to a specified pin. Analog value range: 0\~255

### Read analog value

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FiK4qhjJWPAR61PvvZL5a%2Fimage.png?alt=media\&token=fc497196-dd81-45e7-bef0-01c457eb94a4)

Use this block to read an analog value from a specified pin.

### Write digital value

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FDf3agZw6IGombz8dHYzi%2Fimage.png?alt=media\&token=2a02f390-6c8c-46d3-a632-2919d1c8757f)

Use this block to write a high/low-level value to the specified pin. High-level: 1; Low-level: 0.

### Read digital value

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FVWDicHxXXkwfkBUxgISY%2Fimage.png?alt=media\&token=c9c81d54-eb4d-4d4f-9a28-9bdc82e42224)

Use this block to read the high/low-level value of the specified pin.

### Read Ultrasonic sensor distance

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fsu1v4eeYhKTBgt19AW17%2Fimage.png?alt=media&amp;token=47dcd06a-4f66-419d-9da3-ad0aa308c7da" alt=""><figcaption></figcaption></figure></div>

Use this block to read the distance value from the ultrasonic sensor.

For the [Petoi RGB Ultrasonic Sensor](https://docs.petoi.com/extensible-modules/ultrasonic-sensor) (or **RUS-04**), you can set the two pins ( Trigger and Echo) like this:

* **NyBoard** (connects to the D6 and D7 pins)<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FR35YKhiXfDRKOpg3nKtF%2Fimage.png?alt=media&amp;token=815bac37-55d7-4279-addc-57e288965f9d" alt=""><figcaption></figcaption></figure></div>
* **BiBoard** (connects to the Rx and Tx pins)<br>

  <div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FvGhqyywDwxCduIkAHEjA%2Fimage.png?alt=media&amp;token=13029c2d-f028-4f15-8511-c7cb0b15aacb" alt=""><figcaption></figcaption></figure></div>

{% hint style="info" %}
For other ultrasonic sensor models (e.g., **HC-SR04** connects to the D6 and D7 pins), you can set the two pins like this:

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F5Px4u9OPPJepv5CZchHZ%2Fimage.png?alt=media&amp;token=b584eebf-b2c4-4e97-ae25-a48a4d99339c" alt="" data-size="original">
{% endhint %}

### Read the target coordinates <a href="#read-the-target-coordinates" id="read-the-target-coordinates"></a>

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FwlIa7TeKd24z6wiq8scp%2Fimage.png?alt=media&amp;token=34c70870-99e9-40e4-b5ad-543f09deaf2a" alt="" width="510"><figcaption></figcaption></figure></div>

Use this block to Read the coordinates of the identified target from the camera module([MU camera](https://docs.petoi.com/extensible-modules/mu-camera) / [Petoi AI Vision module](https://docs.petoi.com/extensible-modules/petoi-ai-vision-module)) which connect to the BiBoard.

#### Test code screenshot

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FFnov9SLvttRlnytC7QNq%2Fimage.png?alt=media&amp;token=c14f3d6e-fd68-449b-9ca3-1b240e373000" alt=""><figcaption></figcaption></figure>

You can download this test code ([**testCamera.mp**](https://github.com/PetoiCamp/Petoi_MindPlusLib/raw/refs/heads/main/examples/BiBoard/testCamera.mp)) and run in the Mind+.

### Get the gesture value

<div align="left"><figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F3E6DYW6M4bbaAlD1CBqa%2Fimage.png?alt=media&amp;token=b7cf7d6f-47ad-4bb0-81ab-17bed5182f22" alt=""><figcaption></figcaption></figure></div>

Use this block to Read the gesture value from the [gesture sensor](https://docs.petoi.com/extensible-modules/gesture-sensor#biboard) which connect to the BiBoard.

the gesture value meaning is as following:

```
0: Up; 
1: Down; 
2: Left;
3: Right;
```

#### Test code screenshot

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2Fk5bt5Udj1oL0Iwr5MCCp%2Fimage.png?alt=media&amp;token=1f775cc3-20df-4121-9764-6206806587b6" alt=""><figcaption></figcaption></figure>

You can download this test code ([**testGesture.mp**](https://github.com/PetoiCamp/Petoi_MindPlusLib/raw/refs/heads/main/examples/BiBoard/testGesture.mp)) and run in the Mind+.

### Close the serial port

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FqyPEZdplyO5NMeDWEpKx%2Fimage.png?alt=media\&token=7d2b59be-6443-4328-88c1-8d6c01c4507e)

Generally, at the end of the program, it is recommended to use this block to close the serial port communication.

### Demos

We provide some demos to download for reference in the GitHub repository (Petoi\_MindPlusLib/examples).

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FeDRc2lFi2Bo8NXxdnvZj%2Fimage.png?alt=media&amp;token=3d4270dc-e23b-4d9b-9c15-35794f835ecf" alt=""><figcaption></figcaption></figure>

### Free block-based robotics coding curriculum

{% embed url="<https://drive.google.com/drive/folders/1vcdMiLY90WVypL1oHU-082e1qkAn8qW7>" %}
