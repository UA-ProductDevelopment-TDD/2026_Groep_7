# sw-urdf-exporter

| | |
|---|---|
| Link in de slides | https://wiki.ros.org/sw_urdf_exporter |
| Opgehaald van | https://wiki.ros.org/sw_urdf_exporter |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | zichtbare tekst van de gerenderde pagina (Chromium, innerText van <main> of <body>); opmaak, afbeeldingen en links niet overgenomen |

---

Paginatitel: sw_urdf_exporter - ROS Wiki

```text
×
The last ROS 1 release Noetic will go end of life on May 31st with that the ROS Wiki (this website) will also be EOL and transition to being an archive. Maintainers:Please migrate any wiki content into your package's README.md file. If you need more help on migrating code please see this migration guide. Or watch Shane's Lightning Talk from ROSCon 2024.
	About | Support | Discussion Forum | Index | Service Status | ros @ Robotics Stack Exchange

sw_urdf_exporter
ROS 2 Documentation

The ROS Wiki is for ROS 1. Are you using ROS 2 (Humble, Iron, or Rolling)?
Check out the ROS 2 Project Documentation
Package specific documentation can be found on index.ros.org

Wiki
Distributions
ROS/Installation
ROS/Tutorials
RecentChanges
sw_urdf_exporter
Page
Immutable Page
Info
Attachments
More Actions:
Raw Text
Print View
Render as Docbook
Delete Cache
------------------------
Check Spelling
Like Pages
Local Site Map
------------------------
Rename Page
Copy Page
Delete Page
------------------------
My Pages
Subscribe User
------------------------
Remove Spam
Revert to this revision
Package Pages
Sync Pages
------------------------
CreatePdfDocument
Load
RawFile
Save
SlideShow
User
Login

SolidWorks to URDF Exporter

The SolidWorks to URDF exporter is a SolidWorks add-in that allows for the convenient export of SW Parts and Assemblies into a URDF file. The exporter will create a ROS-like package that contains a directory for meshes, textures and robots (urdf files). For single SolidWorks parts, the part exporter will pull the material properties and create a single link in the URDF. For assemblies, the exporter will build the links and create a tree based on the SW assembly hierarchy. The exporter can automatically determine the proper joint type, joint transforms, and axes.




If the above provided download fails to work on your system, please install by source before reporting an issue. If installing by source does work, please submit an Update Installer Request

SolidWorks Version Compatibility

There is a known STL export bug with SolidWorks 2018 that exists up to Service Pack 4 that renders this add-in unusable. If you are using 2018, please update to service pack 5 or use SolidWorks 2019 or later. 2017 and below may also work

Some Important Items

Development on this plugin as of recently has come from the generous donations of several ROS community members. Without this support or from pull requests from communities members, development would not be able to continue. We also appreciate any bugs or feature requests so that we can work on them when the resources become available.

This project is not dependent on ROS and can be used for exporting SolidWorks files for any URDF needs. The URDF will include rospack URI file locations ('package://'), so you will need to change those for non-ROS systems (some Gazebo systems can handle 'package' URIs).

This add-in has been tested on Windows 10 64bit with SolidWorks 2018 SP 5 64bit. It currently does not install on 32bit machines. The add-in makes use of the most up-to-date SW API so it may not work with versions earlier than SolidWorks 2018 (but this hasn't been confirmed).

To learn more about URDF, please review its documentation.

If you have questions about the SolidWorks to URDF Exporter after reading this documentation please check ROS Answers for possible answers. If you don't find your answer, please submit a question with the tag 'sw_urdf_exporter'.

The code has been migrated to Github from its original BitBucket page. Use Github's

issue tracker.

Details of bug fixes and new features are put in the Change Log.

Installing

The download is available as a pre-compiled installer or as source as a Visual Studio C# project.

This sounds made up, but you cannot install the files into a directory labeled "SW2URDF". For some reason, Windows struggles to find the supporting plug-ins, and will throw an unhandled exception error. If anyone has some suggestion as to why, I'd love to know.

Pre-compiled Installer

This installs the most current stable release.

Upgrade to at least .NET Framework V4.7.2 if you don't have it already.

Download the installer linked above.

Run the installer. It will ask for permission to make changes to your computer. Your Windows account will need to have sufficient privileges to make these changes. It should install into the SolidWorks directory in program files.

Open SolidWorks, under "Tools>Add-ins" you will see a SW2URDF item at the very bottom. If this setup file doesn't work, try installing manually as described below.

Compile source

These are the most up-to-date source files. Because this is checked in regularly, there may be bugs or un-finished code in the source files. If you need a stable version of the source, check-out the revision tied to the installer.

To build the source, you'll need to download Visual Studio Community.

Checkout the source with git.

Run Visual Studio as administrator. Your Windows account needs to have these privileges to register the .dll. To do this, right click on Visual C# in your start menu and click, 'run as administrator'.

Click on "Debug>Start Debugging" or press F5. It will compile and run SolidWorks together. After doing this once, you only need to run from Visual Studio to re-compile. Otherwise, to just use the tool, you can start SW normally.

When SolidWorks is open, under "Tools>Add-ins" you will see a SW2URDF item at the very bottom. If this setup file doesn't work try installing manually as described below.

The exporter has two separate forms, one for exporting single SW parts as a single link and the second for exporting assemblies as a set of links and joints.

Tutorials

Proceed to the tutorials for instructions on how to use the exporter.

Wiki: sw_urdf_exporter (last edited 2021-11-21 22:27:26 by StephenBrawner)

Except where otherwise noted, the ROS wiki is licensed under the
Creative Commons Attribution 3.0
```
