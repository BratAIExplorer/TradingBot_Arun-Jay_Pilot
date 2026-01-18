@echo off
TITLE 🚀 ARUN Bot - Quick Launch
color 0B
cd /d "%~dp0"

echo.
echo ========================================================
echo        🚀 ARUN TRADING BOT - LAUNCHER
echo ========================================================
echo.
echo    Version: 2.1 (P1 + P2 Features)
echo    Branch: feature/p1-p2-enhancements
echo.
echo ========================================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ⚠️  Virtual environment not found!
    echo.
    echo Please run START_HERE.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Launch Dashboard V2
echo [2/2] Launching ARUN Titan V2 Dashboard...
echo.
echo ========================================================
echo     ✅ DASHBOARD LOADING...
echo ========================================================
echo.

python dashboard_v2.py

:: If dashboard closes
echo.
echo ========================================================
echo     Dashboard closed.
echo ========================================================
echo.
pause
