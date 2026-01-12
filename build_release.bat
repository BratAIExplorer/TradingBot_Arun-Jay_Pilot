@echo off
echo ===================================================
echo 🏗️ Building ARUN Bot (Desktop Edition)
echo ===================================================

echo 🧹 Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist

echo 📦 Packaging...
pyinstaller build.spec

echo ===================================================
echo ✅ Build Complete!
echo 📂 Output: dist\ARUN_Bot.exe
echo ===================================================
pause
