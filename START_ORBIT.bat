@echo off
REM ORBIT TRADING LAUNCHER - Windows Batch Script
REM Quick-click launcher for the trading dashboard

setlocal enabledelayedexpansion

echo ========================================
echo  ORBIT TRADING LAUNCHER
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python 3.11+ is installed
    pause
    exit /b 1
)

echo Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Navigate to project directory
cd /d "%~dp0"

echo Launching ORBIT TRADING Dashboard...
echo.

REM Start dashboard
python launcher.py

REM If launcher exits, pause to show any errors
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit.
    pause
    exit /b 1
)
