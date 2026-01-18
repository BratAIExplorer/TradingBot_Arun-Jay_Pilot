@echo off
echo ===================================================
echo      🚀 ARUN TRADING BOT - LAUNCHER V2           
echo ===================================================
echo.
echo 1. Launch Legacy UI (Stable)
echo 2. Launch TITAN V2 UI (New Bento Grid)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Launching Legacy UI...
    call .venv\Scripts\python.exe kickstart_gui.py
) else (
    echo Launching TITAN V2 UI...
    call .venv\Scripts\python.exe dashboard_v2.py
)

pause
