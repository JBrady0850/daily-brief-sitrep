#!/bin/sh
# Daily Brief: double-click to start the desktop app on a Mac.
# The first time, macOS may refuse a downloaded script: right-click it, choose
# Open, then Open again.
cd "$(dirname "$0")" || exit 1
# On a new Mac, python3 can be a stub that offers to install developer tools;
# the version check fails there, and the web version opens instead.
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
  python3 -m dailybrief serve || { echo; echo "The Daily Brief stopped with an error. Read the message above."; read -r _; }
  exit 0
fi
echo "Python 3.9 or newer was not found. Opening the web version instead (no live news or email sending)."
echo "Install Python from https://www.python.org/downloads/ for the full desktop app."
open "app/index.html"
