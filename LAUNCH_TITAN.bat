@echo off
echo Starting ARUN Titan System...

echo 1. Starting Backend Brain (Public Access)...
start cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo 2. Starting Frontend Face (Public Access)...
start cmd /k "cd web-frontend && npm run dev -- -H 0.0.0.0"

echo System Online.
echo Local: http://localhost:3000
echo VPS:   http://72.60.40.29:3000
pause
