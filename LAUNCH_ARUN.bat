TITLE SENSEI V1 DASHBOARD (Launcher)
cd /d "%~dp0"

echo [INFO] Launching Sensei V1 Dashboard...
call .venv\Scripts\activate
python sensei_v1_dashboard.py

echo.
echo [INFO] Dashboard closed. Exiting...
exit
