@echo off
title ARUN Mobile Dashboard
color 0B
echo ====================================
echo   ARUN Bot - Mobile Dashboard
echo ====================================
echo.

cd /d "%~dp0"

echo Starting mobile dashboard...
echo.
echo Dashboard will open in your browser at:
echo http://localhost:8501
echo.
echo Password: arun2026
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run mobile_dashboard.py --server.port 8501

pause
