@echo off
title ARUN Bot Daemon
color 0A
echo ====================================
echo   ARUN Trading Bot - Daemon Launcher
echo ====================================
echo.

cd /d "%~dp0"

echo Starting bot daemon...
python bot_daemon.py start

echo.
echo ✅ Bot started successfully!
echo.
echo To check status: python bot_daemon.py status
echo To stop: python bot_daemon.py stop
echo.
pause
