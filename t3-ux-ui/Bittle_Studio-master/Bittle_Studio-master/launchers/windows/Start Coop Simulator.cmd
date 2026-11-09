@echo off
rem Starts the Coop Guard simulator: Bittle patrolling a chicken coop, with sensors and the module hub.
cd /d "%~dp0..\.."
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup first to install Bittle Studio.
  pause
  exit /b 1
)
echo Starting the Coop simulator at http://127.0.0.1:8780
echo Keep this window open. Press Ctrl+C here to stop.
".venv\Scripts\python.exe" app\coop_launcher.py
pause
