@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" launcher.py
) else (
  python --version >nul 2>&1
  if errorlevel 1 (
    py -3 launcher.py
  ) else (
    python launcher.py
  )
)
if errorlevel 1 pause
endlocal
