@echo off
rem Daily Brief: double-click to start the desktop app on Windows.
cd /d "%~dp0"
rem The py launcher comes with Python from python.org. "python" alone may be the
rem Microsoft Store shortcut, which opens the Store instead of running Python.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
  if not errorlevel 1 (
    py -3 -m dailybrief serve
    if errorlevel 1 goto failed
    goto :eof
  )
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 (
  python -m dailybrief serve
  if errorlevel 1 goto failed
  goto :eof
)
echo Python 3.9 or newer was not found. Opening the web version instead (no live news or email sending).
echo Install Python from https://www.python.org/downloads/ for the full desktop app.
start "" "%~dp0app\index.html"
pause
goto :eof
:failed
echo.
echo The Daily Brief stopped with an error. Read the message above, then press a key to close this window.
pause
