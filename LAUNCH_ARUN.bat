@echo off
echo Starting ARUN Trading Bot...
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run START_HERE.bat first to install.
    pause
    exit /b 1
)

if not exist "settings.json" (
    echo First-time setup detected.
    echo Launching Setup Wizard...
    .venv\Scripts\python.exe setup_wizard.py
    if errorlevel 1 (
        echo Setup wizard failed or was cancelled.
        pause
        exit /b 1
    )
)

echo Launching GUI...
.venv\Scripts\python.exe kickstart_gui.py

if errorlevel 1 (
    echo.
    echo Bot crashed or closed with errors.
    echo Check logs\bot.log for details.
    pause
)
