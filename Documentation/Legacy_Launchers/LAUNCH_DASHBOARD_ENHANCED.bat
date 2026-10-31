@echo off
setlocal enabledelayedexpansion
title ARUN TITAN V2 - Enhanced Dashboard Launcher
color 0A

:: =================================================================
:: ENHANCED DASHBOARD LAUNCHER
:: Includes: Balance Card, Bot Wallet, Holdings Filter
:: Auto-checks updates, validates code, and launches dashboard
:: =================================================================

cd /d "%~dp0"

echo ========================================================
echo     🚀 ARUN TITAN V2 - ENHANCED DASHBOARD
echo ========================================================
echo.
echo New Features:
echo   💰 Account Balance Card (Real-time API)
echo   📊 Bot Wallet Breakdown (Capital tracking)
echo   🔍 Holdings Filter (BOT vs MANUAL)
echo.
echo ========================================================
timeout /t 2 >nul

:: ---------------------------------------------------------
:: PRE-FLIGHT CHECKS
:: ---------------------------------------------------------
echo.
echo [Pre-Flight] Running system checks...

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not installed!
    echo    Please run START_HERE.bat first to install dependencies.
    pause
    exit /b 1
)
echo ✅ Python detected

:: 2. Check Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo    Please run START_HERE.bat first to set up environment.
    pause
    exit /b 1
)
echo ✅ Virtual environment found

:: 3. Check dashboard_v2.py
if not exist "dashboard_v2.py" (
    echo ❌ dashboard_v2.py not found!
    echo    Please ensure you're in the correct directory.
    pause
    exit /b 1
)
echo ✅ Dashboard file found

:: 4. Check settings.json
if not exist "settings.json" (
    echo ⚠️  Warning: settings.json not found!
    echo    The bot will use default settings.
    timeout /t 3
)

:: ---------------------------------------------------------
:: AUTO-UPDATE CHECK (OPTIONAL)
:: ---------------------------------------------------------
echo.
echo [Update Check] Checking for updates...
git fetch origin claude/fix-ui-exchange-validation-U9IPJ >nul 2>&1

git diff --quiet HEAD origin/claude/fix-ui-exchange-validation-U9IPJ 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  New updates available!
    echo.
    choice /C YN /M "Would you like to update now? (Y/N)"
    if !errorlevel!==1 (
        echo.
        echo 🔄 Updating...
        call UPDATE_AND_FIX.bat
        if !errorlevel! neq 0 (
            echo ❌ Update failed. Continuing with current version...
            timeout /t 3
        )
    )
) else (
    echo ✅ You're running the latest version
)

:: ---------------------------------------------------------
:: VALIDATE SYNTAX
:: ---------------------------------------------------------
echo.
echo [Validation] Checking code integrity...
python -m py_compile dashboard_v2.py 2>nul
if %errorlevel% neq 0 (
    echo ❌ Syntax error detected in dashboard_v2.py!
    echo    Please run UPDATE_AND_FIX.bat to resolve issues.
    pause
    exit /b 1
)
echo ✅ Code validation passed

:: ---------------------------------------------------------
:: ACTIVATE ENVIRONMENT
:: ---------------------------------------------------------
echo.
echo [Environment] Activating virtual environment...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment!
    pause
    exit /b 1
)
echo ✅ Environment activated

:: ---------------------------------------------------------
:: CHECK DEPENDENCIES
:: ---------------------------------------------------------
echo.
echo [Dependencies] Verifying required packages...
python -c "import customtkinter, requests, pyotp" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Missing dependencies detected!
    echo    Installing required packages...
    pip install -q customtkinter requests pyotp
    if !errorlevel! neq 0 (
        echo ❌ Failed to install dependencies!
        pause
        exit /b 1
    )
)
echo ✅ All dependencies available

:: ---------------------------------------------------------
:: LAUNCH DASHBOARD
:: ---------------------------------------------------------
echo.
echo ========================================================
echo ✅ ALL CHECKS PASSED - LAUNCHING DASHBOARD
echo ========================================================
echo.
echo Dashboard Features:
echo   • Account Balance with auto-refresh (15 min)
echo   • Bot Wallet showing capital allocation
echo   • Holdings table with BOT/MANUAL filter
echo   • Market sentiment meter
echo   • Real-time P^&L tracking
echo.
echo To refresh balance manually: Click the 🔄 button
echo To filter holdings: Click ALL / BOT / MANUAL
echo.
echo ========================================================
echo.
timeout /t 2 >nul

:: Create a log file for this session
set LOG_FILE=dashboard_session_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log
echo ======================================== > %LOG_FILE%
echo ARUN Dashboard Session Log >> %LOG_FILE%
echo Started: %date% %time% >> %LOG_FILE%
echo ======================================== >> %LOG_FILE%
echo. >> %LOG_FILE%

echo [INFO] Launching Enhanced Dashboard... >> %LOG_FILE%
echo 🚀 Launching dashboard...

:: Launch the dashboard
python dashboard_v2.py 2>&1 | tee -a %LOG_FILE%

:: Capture exit code
set EXIT_CODE=%errorlevel%

echo. >> %LOG_FILE%
echo Dashboard closed at %date% %time% >> %LOG_FILE%
echo Exit code: %EXIT_CODE% >> %LOG_FILE%

:: ---------------------------------------------------------
:: POST-LAUNCH ACTIONS
:: ---------------------------------------------------------
echo.
echo ========================================================
if %EXIT_CODE% neq 0 (
    echo ⚠️  Dashboard closed with errors
    echo    Check %LOG_FILE% for details
    echo ========================================================
    echo.
    echo Common issues:
    echo   1. API credentials not configured - Check settings.json
    echo   2. Network error - Check internet connection
    echo   3. Dependency issue - Run START_HERE.bat
    echo.
) else (
    echo ✅ Dashboard closed normally
    echo ========================================================
    echo.
    echo Session log saved: %LOG_FILE%
    echo.
)

echo Press any key to exit...
pause >nul
endlocal
exit /b %EXIT_CODE%
