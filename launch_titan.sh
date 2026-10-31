#!/bin/bash

echo "🚀 Starting ARUN Titan System (Linux VPS Mode)..."

# Create logs directory first
mkdir -p logs

# 1. Start Backend (The Brain)
echo "🧠 Starting Backend..."
cd backend
# Use nohup to run in background
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"
cd ..

# 2. Start Frontend (The Face)
echo "👀 Starting Frontend..."
cd web-frontend
nohup npm run dev -- -H 0.0.0.0 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
cd ..

# 3. Start Bot Engine (The Heart) - Headless Mode
echo "❤️ Starting Bot Engine..."
# Create logs directory if not exists
mkdir -p logs
nohup python3 headless_launcher.py > logs/headless_engine.log 2>&1 &
BOT_PID=$!
echo "   ✅ Bot Engine started (PID: $BOT_PID)"

echo ""
echo "🌟 System Online!"
echo "---------------------------------------------------"
echo "API:      http://$(curl -4 -s ifconfig.me):8000"
echo "WebApp:   http://$(curl -4 -s ifconfig.me):3000"
echo "---------------------------------------------------"
echo "To stop the system, run:  kill $BACKEND_PID $FRONTEND_PID $BOT_PID"
echo "Logs are being written to logs/"
