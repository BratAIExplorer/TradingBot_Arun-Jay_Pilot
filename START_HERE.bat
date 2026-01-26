@echo off
setlocal enabledelayedexpansion
title ARUN Bot - One-Click Installer
color 0A

:: ---------------------------------------------------------
:: INSTALLER LOGGING - Start
:: ---------------------------------------------------------
set LOG_FILE=install.log
echo. > %LOG_FILE%
echo ================================================ >> %LOG_FILE%
echo ARUN Bot Installation Log >> %LOG_FILE%
echo Started: %date% %time% >> %LOG_FILE%
echo ================================================ >> %LOG_FILE%
echo. >> %LOG_FILE%

:: ---------------------------------------------------------
:: QUICK START MODE DETECTION
:: ---------------------------------------------------------
set QUICK_START=0
if /i "%1"=="--quick" set QUICK_START=1
if /i "%1"=="-q" set QUICK_START=1

echo ========================================================
echo        🚀 ARUN TRADING BOT - START HERE
echo ========================================================
if %QUICK_START%==1 (
    echo [QUICK START MODE - Auto-launching after install]
    echo [QUICK START MODE] >> %LOG_FILE%
)
echo.
echo Please wait while we set everything up for you...
echo.

:: ---------------------------------------------------------
:: 1. Check for Python Installation
:: ---------------------------------------------------------
echo [Step 1/5] Checking System Requirements...
echo [Step 1/5] Checking Python... >> %LOG_FILE%

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Python not found. Installing Python 3.11... >> %LOG_FILE%
    echo.
    echo ⚠️  Python was not found on your system.
    echo ⬇️  Downloading and Installing Python 3.11 automatically...
    
    powershell -Command "Start-BitsTransfer -Source https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -Destination python_installer.exe" >> %LOG_FILE% 2>&1
    
    if exist python_installer.exe (
        echo 💿 Running Python Installer...
        echo Installing Python... >> %LOG_FILE%
        python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 >> %LOG_FILE% 2>&1
        if %errorlevel% neq 0 (
            echo ❌ Python installation failed. >> %LOG_FILE%
            echo ❌ Python installation failed.
            pause
            exit /b 1
        )
        echo ✅ Python installed successfully. >> %LOG_FILE%
        del python_installer.exe
    ) else (
        echo ❌ Failed to download Python. >> %LOG_FILE%
        echo ❌ Failed to download Python.
        pause
        exit /b 1
    )
    call RefreshEnv.cmd >nul 2>&1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
    echo ✅ Python is already installed: !PYTHON_VER! >> %LOG_FILE%
    echo ✅ Python is already installed.
)

:: ---------------------------------------------------------
:: 2. Set up Virtual Environment
:: ---------------------------------------------------------
echo.
echo [Step 2/5] Setting up Isolated Environment...
echo [Step 2/5] Creating virtual environment... >> %LOG_FILE%

if not exist ".venv" (
    echo 📦 Creating .venv folder...
    python -m venv .venv >> %LOG_FILE% 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment. >> %LOG_FILE%
        echo ❌ Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created. >> %LOG_FILE%
) else (
    echo ℹ️  Virtual environment already exists. >> %LOG_FILE%
)

:: ---------------------------------------------------------
:: 3. Install Dependencies
:: ---------------------------------------------------------
echo.
echo [Step 3/5] Installing Dependencies...
echo [Step 3/5] Installing dependencies from requirements.txt... >> %LOG_FILE%
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
pip install --prefer-binary -r requirements.txt >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo ❌ Dependency installation failed. See install.log for details. >> %LOG_FILE%
    echo ❌ Dependency installation failed. Check install.log
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully. >> %LOG_FILE%

:: ---------------------------------------------------------
:: 4. Create Desktop Shortcut
:: ---------------------------------------------------------
echo.
echo [Step 4/5] Creating Launcher Shortcut...
echo [Step 4/5] Creating shortcuts... >> %LOG_FILE%

:: Create a VBScript to create the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%CD%\LAUNCH_ARUN.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CD%\LAUNCH_ARUN.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Shortcut creation encountered an issue. >> %LOG_FILE%
) else (
    echo ✅ Shortcut created successfully. >> %LOG_FILE%
)
del CreateShortcut.vbs

echo ✅ Created 'LAUNCH_ARUN' shortcut in this folder!

:: ---------------------------------------------------------
:: 5. Launch Application
:: ---------------------------------------------------------
echo.
echo [Step 5/5] Launching ARUN Bot...
echo [Step 5/5] Finalizing setup... >> %LOG_FILE%
echo ========================================================
echo ✅ INSTALLATION COMPLETE!
echo ========================================================
echo.
echo 📋 Installation log saved to: install.log
echo 🚀 You can use 'LAUNCH_ARUN' shortcut to start the bot.
echo.

echo Installation completed successfully at %date% %time% >> %LOG_FILE%

:: Launch the bot using the reliable launcher
echo.
echo 🚀 Starting ARUN Bot...
call LAUNCH_ARUN.bat

endlocal
