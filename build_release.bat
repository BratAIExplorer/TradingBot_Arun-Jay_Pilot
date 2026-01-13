@echo off
echo ===================================================
echo 🏗️ Building ARUN Bot (Desktop Edition)
echo ===================================================

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
pyinstaller build.spec
if %errorlevel% neq 0 (
    echo ❌ Build failed.
    pause
    exit /b %errorlevel%
)

echo 🔗 Creating Shortcut...
python create_shortcut.py

echo ===================================================
echo ✅ Build Complete!
echo 📂 Output: dist\ARUN_Bot.exe
echo ===================================================
pause
