# desktop-app-introduction

| | |
|---|---|
| Link in de slides | https://docs.petoi.com/desktop-app/introduction |
| Opgehaald van | https://docs.petoi.com/desktop-app/introduction.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Introduction

Petoi Desktop App provides a neat graphical user interface to configure the firmware, calibrate the robot, and design customized motions for your robot. The major function modules are the [Firmware Uploader](https://docs.petoi.com/desktop-app/firmware-uploader), [Joint Calibrator](https://docs.petoi.com/desktop-app/calibrator), and [Skill Composer](https://docs.petoi.com/desktop-app/skill-composer).

<figure><img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FgpFagJOOPZSMdBeNJyRJ%2Fimage.png?alt=media&amp;token=32d45fab-f963-42fb-8305-fb4ab44b56b3" alt=""><figcaption></figcaption></figure>

## Download & Installation

You can download the [latest version](https://github.com/PetoiCamp/DesktopAppRelease/releases) of the desktop App and unzip it.

Before running the app, you must use the included USB adapter or the Bluetooth dongle to connect to a Petoi robot.  You may need to [install drivers](https://docs.petoi.com/technical-support/useful-tools#nyboard-usb-driver-to-access-the-usb-uploader-adapter) for USB connection.

### Windows

Run the UI.exe in the unzipped folder.  Do NOT move the UI.exe to another location in Windows.

### Mac

After downloading the Mac version, you must drag it into the Applications folder.&#x20;

If you see the error message that "Petoi Desktop App" cannot be opened because the developer cannot be verified, you can right-click the icon, hold the **Shift** key, and click **Open**. If it still doesn't open, go to your System Settings -> Privacy and Security and scroll down. There should be an option to allow the app to run.&#x20;

![](https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2FvuPVkiYiGtTwju5yz9Ki%2Fright%20open.JPG?alt=media\&token=82004544-4dde-4d6d-91e2-1dd751efefcc)

{% hint style="warning" %}
The upgraded macOS has introduced some incompatibility with the GUI library. To click/activate an element in the app's interface, you need to click the element, hold the click, and slightly move your finger, then release. Otherwise, the event cannot be recognized. Sorry for the inconvenience. It's been a known issue between macOS and the popular Tkinter library.

<img src="https://1565080149-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F-MQ6a951Q6Jn1Zzt5Ajr-887967055%2Fuploads%2F4xn6w94osgeqArxYQCWP%2FmovingCursor.gif?alt=media&amp;token=e122ee74-5946-49ea-b010-f0d95d332dad" alt="" data-size="original">
{% endhint %}

### Linux

Please see the next chapter to run the app from a terminal.

## Run the app from the Terminal

In the case of compatibility issues, or if you want to modify the source and test, you can also run the code from the Terminal.

The Terminal is a built-in interface on macOS or Linux machines. The equivalent environment on Windows machines is called the Command-Line Tool (CMD). It's recommended that you install [Anaconda](https://www.anaconda.com/) to manage your Python environment. It can also provide the Powershell as a Terminal for the Windows machines.

Depending on your existing Python configuration, you may need to upgrade to Python 3 and install the following libraries:

* pyserial
* pillow

You can install them by entering `pip3 install pyserial pillow` in the Terminal or using the package manager in Anaconda.

To run the code:

1. In the Terminal, use the `cd` command to navigate to the `OpenCat/pyUI/` folder. You can use the Tab key to auto-complete the path name.
2. After entering the pyUI/ folder, enter `ls` and ensure you can see the UI.py and other Python source codes listed.
3. Enter `python3 UI.py`.

{% hint style="info" %}
If you encounter the Python error message "\_tkinter.TclError: no display name and no $DISPLAY environment variable", you can try to install **python3-tk**, **tk-dev**, and **idle3**. &#x20;

For Linux users,  taking Debian / Ubuntu as an example, the command is as follows:

`apt install python3-tk`

`apt install tk-dev`&#x20;

`apt install idle3`<br>

For macOS users, use the following command to install the library:

`brew install idle3`

After the installation is complete, reboot the computer.
{% endhint %}

## Open Source Codes

The source code is written with Tkinker in Python 3 and is [open-sourced](https://github.com/PetoiCamp/DesktopAppRelease).

UI.py is the general entry for all the modules:

* UI.py

-> FirmwareUploader.py

-> Calibrator.py

-> SkillComposer.py

-> Debugger.py: provides some debugging tools for the Petoi robot.

-> translate.py: provides multi-language support for the UI. You may help to translate the UI into your language.
