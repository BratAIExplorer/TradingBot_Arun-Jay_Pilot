@echo off
echo Starting ARUN Titan System...

echo 1. Starting Backend Brain...
start cmd /k "cd backend && python -m uvicorn main:app --reload --port 8000"

echo 2. Starting Frontend Face...
start cmd /k "cd web-frontend && npm run dev"

echo System Online. Access at http://localhost:3000
pause
