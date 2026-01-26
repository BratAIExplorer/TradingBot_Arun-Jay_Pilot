@echo off
TITLE ARUN HEADLESS ENGINE (Performance Mode)
cd /d "%~dp0"

echo [INFO] Launching ARUN Engine in Headless Mode...
echo [INFO] This mode has minimal latency and maximum reliability.
echo.

if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python kickstart.py

echo.
echo [INFO] Engine closed.
pause
