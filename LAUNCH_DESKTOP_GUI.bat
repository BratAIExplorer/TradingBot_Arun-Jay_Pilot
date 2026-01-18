@echo off
title ARUN Desktop GUI
color 0E
echo ====================================
echo   ARUN Bot - Desktop GUI
echo ====================================
echo.

cd /d "%~dp0"

echo Starting desktop application...
python dashboard_v2.py

pause
