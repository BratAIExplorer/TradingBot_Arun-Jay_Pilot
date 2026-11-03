@echo off
REM Opens the Voyager dashboard (running on the VPS) in your browser and shows live IBKR status.
REM Keep this window open while you use the dashboard. Close it to disconnect.
echo Connecting to Voyager on the VPS...
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8011/dashboard"
start /b ssh -N -L 8011:127.0.0.1:8011 root@76.13.179.32
:loop
for /f %%s in ('ssh root@76.13.179.32 "systemctl is-active voyager-gateway"') do set S=%%s
if "%S%"=="active" (echo %time%  IBKR Gateway: CONNECTED) else (echo %time%  IBKR Gateway: DISCONNECTED ^(%S%^))
timeout /t 30 >nul
goto loop
