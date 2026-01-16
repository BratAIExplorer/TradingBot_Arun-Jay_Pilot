@echo off
echo ================================================
echo Building ARUN Bot Professional Installer
echo ================================================
echo.

:: Clean previous builds
if exist "build_installer" rmdir /s /q "build_installer"
if exist "dist\ARUN_Bot_Installer.exe" del "dist\ARUN_Bot_Installer.exe"

echo [1/3] Activating virtual environment...
call .venv\Scripts\activate

echo [2/3] Installing PyInstaller (if needed)...
pip install pyinstaller >nul 2>&1

echo [3/3] Building installer EXE...

:: Check for icon file
if exist "installer_icon.ico" (
    set ICON_PARAM=--icon=installer_icon.ico
) else if exist "installer_icon.png" (
    set ICON_PARAM=--icon=installer_icon.png
) else (
    set ICON_PARAM=
)

pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "ARUN_Bot_Installer" ^
    %ICON_PARAM% ^
    --add-data "requirements.txt;." ^
    --hidden-import=customtkinter ^
    --clean ^
    installer_gui.py

echo.
if exist "dist\ARUN_Bot_Installer.exe" (
    echo ================================================
    echo ✅ BUILD SUCCESSFUL!
    echo ================================================
    echo.
    echo Installer location: dist\ARUN_Bot_Installer.exe
    echo File size:
    dir dist\ARUN_Bot_Installer.exe | findstr "ARUN"
    echo.
    echo Users only need this ONE file to install ARUN Bot.
) else (
    echo ❌ Build failed. Check errors above.
)

pause
