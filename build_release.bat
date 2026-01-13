@echo off
setlocal
echo ===================================================
echo 🏗️ Building ARUN Bot (Desktop Edition)
echo ===================================================

set VERSION=v1.0.0
set EXE_NAME=ARUN_Bot_%VERSION%

echo ℹ️ Target Version: %VERSION%

echo 🧹 Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist

echo ⬇️ Ensuring Clean Environment...
echo 🧹 Uninstalling potentially conflicting yfinance versions...
pip uninstall -y yfinance
if %errorlevel% neq 0 (
    echo ⚠️ Warning: Failed to uninstall yfinance. It might not be installed. Continuing...
)

echo ⬇️ Installing Dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies.
    pause
    exit /b %errorlevel%
)

echo 🔒 FORCING Correct yfinance version (0.2.40) for Python 3.9 compatibility...
pip install yfinance==0.2.40
if %errorlevel% neq 0 (
    echo ❌ Failed to force install yfinance 0.2.40.
    pause
    exit /b %errorlevel%
)

echo 📦 Packaging...
echo ℹ️ Running PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "%EXE_NAME%" --hidden-import=yfinance --hidden-import=PIL --hidden-import=customtkinter --hidden-import=tkinter kickstart_gui.py

if %errorlevel% neq 0 (
    echo ❌ Build failed.
    pause
    exit /b %errorlevel%
)

echo 📂 Copying Configuration Files to Distribution Folder...
set DIST_FOLDER=dist\%EXE_NAME%

if exist settings.json (
    copy settings.json "%DIST_FOLDER%\" >nul
    echo ✅ Copied settings.json
) else (
    echo ⚠️ settings.json not found in source.
)

if exist settings_default.json (
    copy settings_default.json "%DIST_FOLDER%\" >nul
    echo ✅ Copied settings_default.json
) else (
    echo ⚠️ settings_default.json not found in source.
)

if exist config_table.csv (
    copy config_table.csv "%DIST_FOLDER%\" >nul
    echo ✅ Copied config_table.csv
)

if exist database (
    echo 📂 Copying Database...
    xcopy /E /I /Y database "%DIST_FOLDER%\database" >nul
    echo ✅ Copied database folder
)

echo 🔗 Creating Shortcut...
python create_shortcut.py

echo ===================================================
echo ✅ Build Complete!
echo 🏷️ Version: %VERSION%
echo 📂 Output: %DIST_FOLDER%\%EXE_NAME%.exe
echo ===================================================
pause
endlocal
