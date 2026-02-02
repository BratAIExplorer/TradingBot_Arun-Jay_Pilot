from fastapi import APIRouter, HTTPException, Depends
from backend.bot_manager import bot_manager
from backend.auth import (
    get_current_user, 
    authenticate_user, 
    create_access_token, 
    Token, 
    LoginRequest,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from typing import List, Optional
from datetime import timedelta
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Try to import DB for positions
try:
    from database.trades_db import TradesDatabase
    db = TradesDatabase()
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️ Database module not found for API.")

# Try to import settings for capital data
try:
    from settings_manager import SettingsManager
    settings = SettingsManager()
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    print("⚠️ Settings module not found for API.")

router = APIRouter()


# ============================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================

@router.post("/auth/login", response_model=Token)
def login(request: LoginRequest):
    """
    Authenticate and get access token.
    
    Default credentials (CHANGE THESE via environment variables):
    - Username: admin (or ARUN_ADMIN_USER env var)
    - Password: changeme123 (or ARUN_ADMIN_PASSWORD env var)
    """
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token, 
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/health")
def health_check():
    """Public health check endpoint"""
    return {"status": "healthy", "version": "2.1.0"}


# ============================================
# READ-ONLY ENDPOINTS (Auth Required)
# ============================================

@router.get("/status")
def get_status(current_user: str = Depends(get_current_user)):
    """Get current bot status, uptime, and health"""
    return bot_manager.get_status()


@router.get("/logs")
def get_logs(limit: int = 50, current_user: str = Depends(get_current_user)):
    """Get recent log entries"""
    return {"logs": bot_manager.get_logs(limit)}


@router.get("/positions")
def get_positions(current_user: str = Depends(get_current_user)):
    """Get current active positions from Database/Memory"""
    if not DB_AVAILABLE:
        return {"error": "Database not available", "positions": []}
    
    try:
        positions = db.get_open_positions(is_paper=False)
        return {"count": len(positions), "positions": positions}
    except Exception as e:
        return {"error": str(e), "positions": []}


@router.get("/pnl")
def get_pnl(current_user: str = Depends(get_current_user)):
    """Get today's P&L summary"""
    if not DB_AVAILABLE:
        return {"error": "Database not available", "pnl": 0, "trades_count": 0}
    
    try:
        today_trades = db.get_today_trades(is_paper=False)
        total_pnl = sum(t.get('pnl_net', 0) if t.get('pnl_net') is not None else 0 for t in today_trades if t.get('action') == 'SELL')
        profitable_trades = sum(1 for t in today_trades if t.get('action') == 'SELL' and (t.get('pnl_net', 0) or 0) > 0)
        
        return {
            "pnl": round(total_pnl, 2),
            "trades_count": len(today_trades),
            "profitable_count": profitable_trades,
            "trades": today_trades[-10:]  # Last 10 trades
        }
    except Exception as e:
        return {"error": str(e), "pnl": 0, "trades_count": 0}


@router.get("/trades/history")
def get_trade_history(days: int = 7, current_user: str = Depends(get_current_user)):
    """Get trade history for charts (cumulative P&L over time)"""
    if not DB_AVAILABLE:
        return {"error": "Database not available", "data": []}
    
    try:
        # Get trade history from database
        trades = db.get_recent_trades(limit=100, is_paper=False)
        
        # Build cumulative P&L series for charts
        pnl_series = []
        cumulative_pnl = 0
        
        for trade in reversed(trades):  # Oldest first
            if trade.get('action') == 'SELL':
                # Calculate P&L for this trade
                net_amount = trade.get('net_amount', 0)
                cumulative_pnl += net_amount
            
            pnl_series.append({
                "time": trade.get('timestamp', '')[:16],  # Trim to minute
                "pnl": round(cumulative_pnl, 2),
                "symbol": trade.get('symbol', ''),
                "action": trade.get('action', '')
            })
        
        return {
            "data": pnl_series[-50:],  # Last 50 data points
            "total_pnl": round(cumulative_pnl, 2),
            "trade_count": len(trades)
        }
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/capital")
def get_capital(current_user: str = Depends(get_current_user)):
    """Get capital allocation summary"""
    if not SETTINGS_AVAILABLE:
        return {"error": "Settings not available", "total": 0, "deployed": 0}
    
    try:
        capital = settings.get_capital_summary()
        # Calculate deployed capital from open positions
        deployed = 0
        if DB_AVAILABLE:
            positions = db.get_open_positions(is_paper=False)
            deployed = sum(
                p.get('avg_entry_price', 0) * p.get('net_quantity', 0) 
                for p in positions
            )
        
        return {
            "total": capital.get('total_capital', 50000),
            "deployed": round(deployed, 2),
            "available": round(capital.get('total_capital', 50000) - deployed, 2),
            "max_per_stock_pct": capital.get('max_per_stock_pct', 10),
            "daily_loss_limit_pct": capital.get('daily_loss_limit_pct', 10)
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "deployed": 0}


# ============================================
# CONTROL ENDPOINTS (Auth Required - Critical)
# ============================================

@router.post("/control/start")
def start_bot(current_user: str = Depends(get_current_user)):
    """Start the trading engine (PROTECTED)"""
    result = bot_manager.start_bot()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/control/stop")
def stop_bot(current_user: str = Depends(get_current_user)):
    """Stop the trading engine (PROTECTED)"""
    result = bot_manager.stop_bot()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ============================================
# DEBUG ENDPOINTS (Auth Required)
# ============================================

@router.get("/debug/test_log")
def debug_test_log(current_user: str = Depends(get_current_user)):
    """Debug endpoint to verify logging internals"""
    try:
        from kickstart import log_ok
        
        log_ok(f"DEBUG LOG from API (User: {current_user})")
        
        queue_size = bot_manager.log_queue.qsize()
        queue_content = list(bot_manager.log_queue.queue)[-5:]
        
        return {
            "QUEUE_SIZE": queue_size,
            "QUEUE_CONTENT": queue_content,
            "BOT_MANAGER_ID": id(bot_manager),
            "AUTHENTICATED_USER": current_user
        }
    except Exception as e:
        return {"error": str(e)}
