@echo off
title ARUN Bot - One-Click Installer
echo ==========================================================
echo 🚀 ARUN Trading Bot - Automatic Installer & Builder
echo ==========================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not found in PATH!
    echo Please install Python 3.10+ from python.org and try again.
    echo.
    pause
    exit /b
)
echo ✅ Python found.

:: 2. Create Virtual Environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo 📦 Virtual environment exists.
)

:: 3. Install Dependencies
echo ⬇️ Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

:: 4. Build .exe
echo 🏗️ Building Application...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
pyinstaller build.spec

:: 5. Create Desktop Shortcut
echo 🔗 Creating Desktop Shortcut...
set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\ARUN Bot.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%CD%\dist\ARUN_Bot.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%\dist" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ==========================================================
echo ✅ SUCCESS!
echo.
echo You can now run "ARUN Bot" directly from your Desktop.
echo The actual .exe is located in: %CD%\dist\ARUN_Bot.exe
echo.
echo Press any key to exit...
pause >nul
