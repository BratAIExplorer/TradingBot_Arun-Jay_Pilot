@echo off
set LOGFILE=install_log.txt
echo ========================================================== > %LOGFILE%
echo 🚀 ARUN Trading Bot - Installer Log >> %LOGFILE%
echo Date: %DATE% %TIME% >> %LOGFILE%
echo ========================================================== >> %LOGFILE%

title ARUN Bot - One-Click Installer
echo ==========================================================
echo 🚀 ARUN Trading Bot - Automatic Installer & Builder
echo ==========================================================
echo.
echo ℹ️  A detailed log is being saved to: %LOGFILE%
echo.

:: 1. Check Python
echo [STEP 1] Checking Python...
python --version >> %LOGFILE% 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not found in PATH!
    echo ❌ ERROR: Python not found. >> %LOGFILE%
    echo Please install Python 3.10+ from python.org and try again.
    echo.
    pause
    exit /b
)
echo ✅ Python found.

:: 2. Create Virtual Environment
echo [STEP 2] Checking Virtual Environment...
if not exist "venv" (
    echo 📦 Creating virtual environment...
    echo Creating venv... >> %LOGFILE%
    python -m venv venv >> %LOGFILE% 2>&1
) else (
    echo 📦 Virtual environment exists.
)

:: 3. Install Dependencies
echo [STEP 3] Installing dependencies (this may take a while)...
echo Installing requirements... >> %LOGFILE%
call venv\Scripts\activate
pip install -r requirements.txt >> %LOGFILE% 2>&1
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies. Check %LOGFILE% for details.
    pause
    exit /b
)
echo Installing PyInstaller... >> %LOGFILE%
pip install pyinstaller >> %LOGFILE% 2>&1

:: 4. Build .exe
echo [STEP 4] Building Application...
echo Running PyInstaller... >> %LOGFILE%
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

pyinstaller build.spec >> %LOGFILE% 2>&1
if %errorlevel% neq 0 (
    echo ❌ Build FAILED!
    echo Please check %LOGFILE% to see the error.
    echo Common error: Missing files or permission issues.
    pause
    exit /b
)

:: 5. Create Desktop Shortcut
echo [STEP 5] Creating Desktop Shortcut...
set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\ARUN Bot.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%CD%\dist\ARUN_Bot.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%\dist" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT% >> %LOGFILE% 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Could not create Desktop Shortcut. (Check %LOGFILE%)
    echo    You can find the App here: dist\ARUN_Bot.exe
) else (
    echo ✅ Shortcut created on Desktop.
)
del %SCRIPT%

echo.
echo ==========================================================
echo ✅ SUCCESS!
echo ==========================================================
echo.
echo You can now run "ARUN Bot" directly from your Desktop.
echo The actual .exe is located in: %CD%\dist\ARUN_Bot.exe
echo.
echo Press any key to exit...
pause >nul
