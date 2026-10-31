@echo off
cd /d "%~dp0"
echo ---------------------------------------------------
echo      ARUN TITAN TRADING BOT V2 (Launcher)
echo ---------------------------------------------------
echo.
echo [INFO] Launching V2 Dashboard...
call .venv\Scripts\activate
python dashboard_v2.py
pause
