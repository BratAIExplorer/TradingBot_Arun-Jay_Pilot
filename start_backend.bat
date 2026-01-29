@echo off
echo Starting ARUN Titan Brain (Backend)...
cd backend
python -m uvicorn main:app --reload --port 8000
pause
