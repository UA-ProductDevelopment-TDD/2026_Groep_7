#!/usr/bin/env bash
# Starts the Bittle Platform: map, camera, 3D robot and robot control in one page.
cd "$(dirname "$0")/../.." || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Run Setup first to install Bittle Studio."
  exit 1
fi
echo "Het Bittle Platform start op http://127.0.0.1:8790 (open het in Chrome of Edge voor Bluetooth)."
echo "Laat dit venster open. Druk hier Ctrl+C om te stoppen."
.venv/bin/python app/platform_launcher.py "$@"
