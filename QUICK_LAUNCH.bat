@echo off
:: =================================================================
:: QUICK LAUNCH - No checks, instant start
:: Use this if you're sure everything is set up correctly
:: =================================================================

title ARUN Dashboard - Quick Launch
cd /d "%~dp0"

echo 🚀 Quick Launch - Starting Dashboard...
call .venv\Scripts\activate
python dashboard_v2.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Dashboard crashed!
    echo    Use LAUNCH_DASHBOARD_ENHANCED.bat for full diagnostics.
    pause
)
exit
