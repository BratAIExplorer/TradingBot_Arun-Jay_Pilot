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
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://72.60.40.29:3000",  # Your VPS IP
    "http://72.60.40.29",       # For production build access
    "*"                         # Fallback
]

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

    try:
        db.set_control_flag("bot_status", new_status)
        return {"status": "success", "new_state": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Phase 6: Settings & Stock Management APIs ---

@app.get("/api/settings")
def get_settings():
    """Get full system settings"""
    try:
        # Reload to get latest from disk
        from settings_manager import SettingsManager
        mgr = SettingsManager()
        mgr.load()
        return mgr.settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")

@app.post("/api/settings")
def update_settings(new_settings: dict):
    """Update system settings (Full Replace or Partial Merge)"""
    try:
        from settings_manager import SettingsManager
        mgr = SettingsManager()
        mgr.load()
        
        # Deep merge or replace could be complex. 
        # For simplicity in this iteration, we trust the frontend to send valid structure
        # or we accept partial updates.
        # Let's support updating top-level keys.
        
        for key, value in new_settings.items():
            # Basic validation could go here
            mgr.set(key, value)
            
        mgr.save()
        return {"status": "success", "message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

@app.get("/api/stocks")
def get_stocks():
    """Get configured stocks list"""
    try:
        from settings_manager import SettingsManager
        mgr = SettingsManager()
        mgr.load()
        return mgr.get_stock_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks")
def add_update_stock(stock: dict):
    """
    Add or Update a stock configuration.
    Expects: { "symbol": "RELIANCE", "exchange": "NSE", ... }
    """
    if "symbol" not in stock:
        raise HTTPException(status_code=400, detail="Symbol is required")
        
    try:
        from settings_manager import SettingsManager
        mgr = SettingsManager()
        mgr.load()
        
        # Check if exists to update, else add
        stocks = mgr.get_stock_configs()
        symbol = stock["symbol"].upper()
        exchange = stock.get("exchange", "NSE").upper()
        
        # Remove existing if any (to replace)
        stocks = [s for s in stocks if not (s["symbol"] == symbol and s.get("exchange", "NSE") == exchange)]
        
        # Add new/updated
        stock["symbol"] = symbol # Enforce upper
        stock["exchange"] = exchange
        stocks.append(stock)
        
        mgr.set("stocks", stocks)
        mgr.save()
        
        return {"status": "success", "message": f"Stock {symbol} saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/{symbol}")
def delete_stock(symbol: str, exchange: str = "NSE"):
    """Delete a stock configuration"""
    try:
        from settings_manager import SettingsManager
        mgr = SettingsManager()
        mgr.load()
        
        stocks = mgr.get_stock_configs()
        # Filter out the target
        new_stocks = [s for s in stocks if not (s["symbol"] == symbol.upper() and s.get("exchange", "NSE") == exchange.upper())]
        
        if len(new_stocks) == len(stocks):
             raise HTTPException(status_code=404, detail="Stock not found")
             
        mgr.set("stocks", new_stocks)
        mgr.save()
        
        return {"status": "success", "message": f"Stock {symbol} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
