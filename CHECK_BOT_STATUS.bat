@echo off
title ARUN Bot Status
color 0C
echo ====================================
echo   ARUN Bot - Status Checker
echo ====================================
echo.

cd /d "%~dp0"

python bot_daemon.py status

echo.
pause
