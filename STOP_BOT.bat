@echo off
title ARUN Bot - Stop
color 0C
echo ====================================
echo   ARUN Bot - Stop Daemon
echo ====================================
echo.

cd /d "%~dp0"

python bot_daemon.py stop

echo.
echo ✅ Bot stopped successfully!
echo.
pause
