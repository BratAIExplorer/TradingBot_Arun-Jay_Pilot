from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.trades_db import TradesDatabase
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TradesDatabase: {e}")
    DB_AVAILABLE = False

app = FastAPI(
    title="ARUN Titan Brain",
    description="Headless API for ARUN Trading Bot",
    version="2.0.0"
)

# CORS Configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB connection with corrected path
# We are in /backend, DB is in /database/trades.db from root.
# If running from root: database/trades.db is correct.
# If running from backend: ../database/trades.db
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "trades.db")
db = TradesDatabase(db_path=db_path) if DB_AVAILABLE else None

@app.get("/")
def read_root():
    return {"status": "online", "message": "ARUN Titan Brain is Active"}

@app.get("/health")
def health_check():
    if not db:
        return {"status": "degraded", "reason": "Database module not loaded"}
    try:
        # Simple query to check connection
        db.get_recent_trades(limit=1)
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/positions")
def get_positions():
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        return db.get_open_positions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/recent")
def get_trades(limit: int = 10):
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    return db.get_recent_trades(limit=limit)

@app.get("/api/control/status")
def get_bot_status():
    if not db:
        return {"status": "UNKNOWN", "reason": "Database disconnected"}
    try:
        status = db.get_control_flag("bot_status", default="STOPPED")
        return {"status": status}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@app.post("/api/control/set")
def set_bot_status(command: dict):
    # Expects {"status": "RUNNING" | "STOPPED"}
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    new_status = command.get("status")
    if new_status not in ["RUNNING", "STOPPED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use RUNNING or STOPPED")
        
    try:
        db.set_control_flag("bot_status", new_status)
        return {"status": "success", "new_state": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
