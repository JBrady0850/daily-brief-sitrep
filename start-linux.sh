#!/bin/sh
# Daily Brief: start the desktop app on Linux.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m dailybrief serve
fi
echo "Python 3 was not found. Opening the web version instead (no live news or email sending)."
xdg-open "app/index.html" 2>/dev/null || echo "Open app/index.html in your browser."
