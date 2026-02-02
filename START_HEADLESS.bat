@echo off
TITLE ARUN Titan V2 - HEADLESS LAUNCHER
color 0A

echo ===================================================
echo   🚀 ARUN TITAN V2 - HEADLESS MODE (WEB UI)
echo ===================================================
echo.
echo [1/2] Starting Backend Brain (FastAPI)...
start "ARUN BACKEND (API)" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Frontend Face (Next.js)...
cd web-frontend
start "ARUN FRONTEND (WEB)" cmd /k "npm run dev"

echo.
echo ✅ SYSTEM LAUNCHED!
echo.
echo    👉 Web Dashboard:   http://localhost:3000
echo    👉 API Documentation: http://localhost:8000/docs
echo.
echo Keep these windows open. Close them to stop the server.
pause
