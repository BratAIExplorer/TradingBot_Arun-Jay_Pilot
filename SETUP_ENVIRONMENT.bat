@echo off
setlocal
echo ===================================================
echo      🛠️ ARUN TRADING BOT - SETUP WIZARD           
echo ===================================================
echo.
echo This script will set up your local environment.
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! 
    echo Please install Python 3.10 or higher from python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo ✅ Python detected.
echo 🔄 Creating Virtual Environment (.venv)...
python -m venv .venv

if %errorlevel% neq 0 (
    echo ❌ Failed to create Virtual Environment.
    pause
    exit /b
)

echo ✅ Virtual Environment created.
echo 🔄 Installing dependencies (this may take a minute)...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies.
    pause
    exit /b
)

echo.
echo ===================================================
echo      🎉 SETUP COMPLETE!
echo ===================================================
echo.
echo You can now use LAUNCH_V2.bat to start the bot.
echo.
pause
