from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
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

from state_manager import state as state_mgr
from settings_manager import SettingsManager

settings_mgr = SettingsManager()

# Capital fields safe to edit from the dashboard — total_capital/starting_capital are
# deliberately excluded, same reasoning as strategy_routes.py excluding orders_enabled:
# the big money-at-risk levers stay file-only, edited by hand, not one tap on a phone.
_CAPITAL_EDITABLE = {
    "max_per_stock_pct": "capital.max_per_stock_value",
    "daily_loss_limit_pct": "capital.daily_loss_limit_pct",
    "max_positions": "capital.max_simultaneous_positions",
}

# PIN gate for write endpoints (start/stop). Empty in .env == no gate (local dev only;
# the deploy/.env template forces you to set one before the VPS is reachable publicly).
TRADINGBOT_PIN = os.environ.get("TRADINGBOT_PIN", "")


def _check_pin(command: dict):
    if not TRADINGBOT_PIN:
        return
    if command.get("pin") != TRADINGBOT_PIN:
        raise HTTPException(status_code=403, detail="wrong or missing PIN")


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

# Small-cap strategy dashboard (read-only; isolated DB, never touches trades.db)
try:
    from backend.strategy_routes import build_router
    app.include_router(build_router())
except Exception as e:  # noqa: BLE001 — the main API must still boot without it
    print(f"Warning: small-cap strategy routes not mounted: {e}")


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse("/dashboard")

_DASHBOARD_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "dashboard.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    if os.path.exists(_DASHBOARD_HTML):
        with open(_DASHBOARD_HTML, encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    return HTMLResponse("<h1>dashboard.html missing</h1>", status_code=500)

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

@app.get("/api/trades/summary")
def get_trades_summary(limit: int = 200):
    """Win/loss counters over the last `limit` trades. pnl_net may be absent on some
    rows (order attempts vs. filled trades) — those are counted but not scored."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    trades = db.get_recent_trades(limit=limit)
    wins = sum(1 for t in trades if (t.get("pnl_net") or 0) > 0)
    losses = sum(1 for t in trades if (t.get("pnl_net") or 0) < 0)
    return {"total": len(trades), "wins": wins, "losses": losses, "trades": trades}

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "bot.log")

@app.get("/api/logs")
def get_logs(lines: int = 200):
    """Tail of logs/bot.log. Read-only, fixed path (no user-controlled path)."""
    lines = max(1, min(lines, 1000))
    if not os.path.exists(_LOG_PATH):
        return {"lines": [], "note": "no log file yet"}
    try:
        # ponytail: whole-file readlines() — fine up to a few MB, switch to a seek-based
        # tail if bot.log grows large enough that this gets slow.
        with open(_LOG_PATH, encoding="utf-8", errors="replace") as fh:
            all_lines = fh.readlines()
        return {"lines": [l.rstrip("\n") for l in all_lines[-lines:]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks")
def get_stocks():
    """Read-only. Editing the symbol list stays in the desktop app / config_table.csv —
    same reasoning as Broker credentials: an infrequent, higher-consequence edit is
    better done deliberately than from a phone tap."""
    try:
        rows = settings_mgr.get_stock_configs()
        # config_table.csv has blank Strategy cells; pandas reads those as NaN, which
        # is not valid JSON (Starlette's encoder rejects it outright). Null it instead.
        for row in rows:
            for k, v in row.items():
                if isinstance(v, float) and v != v:  # NaN != NaN is the cheap NaN check
                    row[k] = None
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ibkr/summary")
def get_ibkr_summary():
    """
    Live IBKR balance + positions — read-only, connects fresh, disconnects after.
    Uses a different clientId (9) than the manual test scripts in brokers/ (which use
    7) so this doesn't collide if you're running check_ibkr_connection.py by hand at
    the same time — IBKR only allows one connection per clientId.

    No auto-polling from the frontend for this one: every call is a real connection
    to Gateway, which may not even be running most of the time, and hammering a live
    account's API isn't something to do on a 15-second timer. Click-to-load only.
    """
    try:
        from brokers.ibkr_broker import IBKRBroker, IBKR_PORT
    except ImportError:
        return {"connected": False, "error": "ib_insync not installed"}

    client_id = int(os.environ.get("IBKR_DASHBOARD_CLIENT_ID", "9"))
    b = IBKRBroker(client_id=client_id)
    try:
        b.connect()
        funds = b.get_funds()
        positions = b.get_portfolio()  # richer than get_positions(): live P&L, market price, purchase date
        is_live = IBKR_PORT in (4001, 7496)
        return {
            "connected": True,
            "is_live": is_live,
            "port": IBKR_PORT,
            "funds_usd": funds,
            "positions": positions,
        }
    except Exception as e:
        return {"connected": False, "error": str(e),
                "hint": "Is IB Gateway running and logged in?"}
    finally:
        b.disconnect()

@app.get("/api/control/status")
def get_bot_status():
    try:
        status = "STOPPED" if state_mgr.is_stop_requested() else "RUNNING"
        return {"status": status}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@app.get("/api/setup/status")
def setup_status():
    """
    Read-only readiness checklist. Never returns secrets — booleans only.
    Credential entry itself stays out of the web dashboard on purpose: typing an API
    key/TOTP secret into a form that transits a public VPS IP is a worse security
    posture than editing settings.json / logging in locally. Fix credentials there.
    """
    # Do NOT import kickstart here — importing it runs its full module-level engine
    # bootstrap (RiskManager, StateManager, DB connections) as a side effect, and its
    # token gate can call sys.exit(1) or block on input() for OTP if a token is
    # missing. That would kill or hang this whole web process. Read the token the
    # same way kickstart.py itself does — settings.get_decrypted — with no import.
    try:
        broker_connected = bool(settings_mgr.get_decrypted("broker.access_token"))
    except Exception:
        broker_connected = None

    capital = settings_mgr.get_capital_summary()
    stocks = settings_mgr.get_stock_configs()

    return {
        "broker_connected": broker_connected,
        "capital_configured": capital.get("total_capital", 0) > 0,
        "stocks_configured": len(stocks) > 0,
        "stock_count": len(stocks),
    }

@app.get("/api/capital")
def get_capital():
    return settings_mgr.get_capital_summary()

@app.post("/api/capital")
def set_capital(patch: dict):
    _check_pin(patch)
    changes = {}
    for key, val in patch.items():
        if key in ("pin",):
            continue
        if key not in _CAPITAL_EDITABLE:
            raise HTTPException(status_code=400, detail=f"unknown or non-editable setting: {key}")
        try:
            settings_mgr.set(_CAPITAL_EDITABLE[key], float(val))
            changes[key] = val
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"{key}: {e}")
    return {"saved": changes}

@app.get("/api/risk")
def get_risk():
    """
    Risk *settings* (static config) + live per-position risk math, computed fresh here.
    Does NOT report circuit-breaker-tripped status — that flag lives in-memory inside
    whichever RiskManager instance the live trading engine process is running, and a
    separate API process can't see it without kickstart.py persisting it somewhere
    shared. Not faked; left out.
    """
    settings_block = settings_mgr.get_risk_settings()
    positions_risk = []
    if db:
        try:
            for pos in db.get_open_positions():
                entry = pos.get("avg_entry_price") or 0
                qty = pos.get("net_quantity") or 0
                if entry <= 0:
                    continue
                sl_pct = settings_block["stop_loss_pct"]
                pt_pct = settings_block["profit_target_pct"]
                positions_risk.append({
                    "symbol": pos.get("symbol"),
                    "exchange": pos.get("exchange"),
                    "entry_price": entry,
                    "quantity": qty,
                    "stop_loss_price": round(entry * (1 - sl_pct / 100), 2),
                    "profit_target_price": round(entry * (1 + pt_pct / 100), 2),
                })
        except Exception:
            pass
    return {"settings": settings_block, "positions": positions_risk,
            "circuit_breaker_status": "unavailable — not wired cross-process yet"}

@app.post("/api/control/set")
def set_bot_status(command: dict):
    # Expects {"status": "RUNNING" | "STOPPED", "pin": "<TRADINGBOT_PIN>"}
    _check_pin(command)
    new_status = command.get("status")
    if new_status not in ["RUNNING", "STOPPED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use RUNNING or STOPPED")

    try:
        state_mgr.set_stop_requested(new_status == "STOPPED")
        return {"status": "success", "new_state": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
