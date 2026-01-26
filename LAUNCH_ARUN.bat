@echo off
TITLE ARUN TITAN V2 (Launcher)
cd /d "%~dp0"

echo [INFO] Launching V2 Dashboard...
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python dashboard_v2.py

echo.
echo [INFO] Dashboard closed. Exiting...
exit
