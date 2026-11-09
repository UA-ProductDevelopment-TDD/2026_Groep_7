@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Start eerst start-dashboard.cmd voor de eenmalige installatie.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pytest tests -q
pause
endlocal
