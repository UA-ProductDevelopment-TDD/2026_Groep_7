#!/usr/bin/env bash
# Starts the Coop Guard simulator: Bittle patrolling a chicken coop, with sensors and the module hub.
cd "$(dirname "$0")/../.." || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Run Setup first to install Bittle Studio."
  exit 1
fi
echo "Starting the Coop simulator at http://127.0.0.1:8780"
echo "Keep this window open. Press Ctrl+C here to stop."
.venv/bin/python app/coop_launcher.py
read -r -p "Press Enter to close this window." _
