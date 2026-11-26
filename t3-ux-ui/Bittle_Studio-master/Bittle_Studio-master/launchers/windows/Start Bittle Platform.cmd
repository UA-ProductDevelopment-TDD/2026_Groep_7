@echo off
rem Starts the Bittle Platform: map, camera, 3D robot and robot control in one page.
cd /d "%~dp0..\.."
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup first to install Bittle Studio.
  pause
  exit /b 1
)
echo Het Bittle Platform start op http://127.0.0.1:8790 (open het in Chrome of Edge voor Bluetooth).
echo Laat dit venster open. Druk hier Ctrl+C om te stoppen.
".venv\Scripts\python.exe" app\platform_launcher.py
pause
