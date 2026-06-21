"""
Zepp Web API — ARUN Trading Bot Remote Dashboard
=================================================
FastAPI server for remote monitoring and control via phone/browser.

Runs independently from kickstart.py. Shares only:
  - database/trades.db  (read-mostly, uses WAL mode for concurrency)
  - settings.json       (read/write for strategy settings)
  - system_control table in trades.db (for panic stop signal)

Port: 8001 (isolated from other VPS services)
Access: http://<VPS_IP>:8001

Environment variables (set in .env or systemd service):
  ZEPP_PIN          - Required PIN for write operations (panic, settings changes)
  ZEPP_DB_PATH      - Override DB path (default: ./database/trades.db)
  ZEPP_SETTINGS_PATH - Override settings path (default: ./settings.json)
"""

import sqlite3
import json
import os
import re
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get(
    "ZEPP_DB_PATH",
    os.path.join(BASE_DIR, "database", "trades.db")
)
SETTINGS_PATH = os.environ.get(
    "ZEPP_SETTINGS_PATH",
    os.path.join(BASE_DIR, "settings.json")
)
ZEPP_PIN = os.environ.get("ZEPP_PIN", "")  # Must be set in .env on VPS

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Zepp — ARUN Bot API",
    description="Remote monitoring and control for ARUN Trading Bot",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Database helper
# ---------------------------------------------------------------------------
@contextmanager
def get_db():
    """SQLite connection with WAL mode for safe concurrent access with kickstart.py."""
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def verify_pin(pin: str):
    if not ZEPP_PIN:
        raise HTTPException(status_code=503, detail="ZEPP_PIN not configured on server. Set it in .env")
    if pin != ZEPP_PIN:
        raise HTTPException(status_code=403, detail="Invalid PIN")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class PanicRequest(BaseModel):
    pin: str

class TrendFilterUpdate(BaseModel):
    pin: str
    enabled: bool
    ma_period: int = 50
    ma_type: str = "SMA"   # "SMA" or "EMA"

class BotControlRequest(BaseModel):
    pin: str
    action: str   # "START" or "STOP"


# ---------------------------------------------------------------------------
# Routes — Read
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Mobile-friendly HTML dashboard — the main entry point from any browser."""
    return HTMLResponse(content=_build_dashboard_html())


@app.get("/api/status")
async def get_status():
    """Bot status, last trade, and basic health."""
    with get_db() as conn:
        ctrl = conn.execute(
            "SELECT value, updated_at FROM system_control WHERE key = 'bot_status'"
        ).fetchone()

        last_trade = conn.execute(
            "SELECT timestamp, symbol, action, price, pnl_net FROM trades ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()

        total = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        today = datetime.now().date().isoformat()
        today_count = conn.execute(
            "SELECT COUNT(*) FROM trades WHERE DATE(timestamp) = ?", (today,)
        ).fetchone()[0]

    return {
        "bot_status": ctrl["value"] if ctrl else "UNKNOWN",
        "status_updated_at": ctrl["updated_at"] if ctrl else None,
        "last_trade": dict(last_trade) if last_trade else None,
        "total_trades_all_time": total,
        "trades_today": today_count,
        "server_time_ist": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    }


@app.get("/api/positions")
async def get_positions():
    """All open positions (bought but not yet sold), real trades only."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                symbol, exchange,
                SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) AS net_qty,
                ROUND(AVG(CASE WHEN action = 'BUY' THEN price END), 2) AS avg_entry,
                ROUND(SUM(CASE WHEN action = 'BUY' THEN net_amount ELSE 0 END), 2) AS total_invested,
                MIN(CASE WHEN action = 'BUY' THEN timestamp END) AS first_buy_at,
                broker
            FROM trades
            WHERE broker != 'PAPER'
            GROUP BY symbol, exchange
            HAVING net_qty > 0
            ORDER BY total_invested DESC
        """).fetchall()

    return {"positions": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/trades")
async def get_trades(limit: int = 20, days: Optional[int] = None, symbol: Optional[str] = None):
    """Recent trade history. Filter by days and/or symbol."""
    query = """
        SELECT id, timestamp, symbol, exchange, action, quantity, price,
               pnl_gross, pnl_net, pnl_pct_net, broker, reason
        FROM trades WHERE 1=1
    """
    params = []

    if days:
        query += " AND datetime(timestamp) >= datetime('now', ?)"
        params.append(f"-{days} days")
    if symbol:
        query += " AND UPPER(symbol) = UPPER(?)"
        params.append(symbol)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(min(limit, 200))

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return {"trades": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/performance")
async def get_performance(days: int = 30):
    """P&L summary for the period. Handles NULL P&L rows correctly."""
    with get_db() as conn:
        sells = conn.execute("""
            SELECT pnl_gross, pnl_net, pnl_pct_net, total_fees, symbol, timestamp
            FROM trades
            WHERE action = 'SELL' AND broker != 'PAPER'
              AND datetime(timestamp) >= datetime('now', ?)
            ORDER BY timestamp DESC
        """, (f"-{days} days",)).fetchall()

    if not sells:
        return {"period_days": days, "total_trades": 0, "message": "No completed trades in this period"}

    pnl_nets = [r["pnl_net"] for r in sells if r["pnl_net"] is not None]
    winning = sum(1 for p in pnl_nets if p > 0)
    losing  = sum(1 for p in pnl_nets if p < 0)
    neutral = len(sells) - len(pnl_nets)
    net_profit = sum(pnl_nets)
    fees = sum(r["total_fees"] or 0 for r in sells)
    denom = winning + losing

    return {
        "period_days": days,
        "total_trades": len(sells),
        "winning_trades": winning,
        "losing_trades": losing,
        "trades_missing_pnl": neutral,
        "win_rate_pct": round(winning / denom * 100, 1) if denom > 0 else 0,
        "net_profit_inr": round(net_profit, 2),
        "total_fees_inr": round(fees, 2),
        "avg_per_trade_inr": round(net_profit / len(sells), 2),
        "note": f"{neutral} trades have NULL P&L — run backfill_pnl.py to fix" if neutral > 0 else None,
    }


@app.get("/api/settings")
async def get_settings():
    """Current bot settings — credentials are never exposed."""
    with open(SETTINGS_PATH) as f:
        s = json.load(f)

    # Whitelist safe fields only — never return broker credentials
    return {
        "capital": s.get("capital", {}),
        "risk": s.get("risk", {}),
        "risk_controls": s.get("risk_controls", {}),
        "strategies": s.get("strategies", {}),
        "app_settings": s.get("app_settings", {}),
        "stocks": [
            {k: v for k, v in stock.items()}
            for stock in s.get("stocks", [])
        ],
    }


@app.get("/api/reports/daily")
async def get_daily_pnl_report(days: int = 30):
    """Daily P&L series — aggregated daily performance for equity curve."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                DATE(timestamp) as date,
                COALESCE(SUM(CASE WHEN pnl_net IS NOT NULL THEN pnl_net ELSE 0 END), 0) as net_pnl,
                COUNT(*) as trade_count,
                SUM(CASE WHEN pnl_net > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_net < 0 THEN 1 ELSE 0 END) as losses
            FROM trades
            WHERE action = 'SELL' AND broker != 'PAPER'
              AND datetime(timestamp) >= datetime('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) ASC
        """, (f"-{days} days",)).fetchall()

    daily_data = []
    for row in rows:
        daily_data.append({
            "date": row["date"],
            "net_pnl": row["net_pnl"],
            "trade_count": row["trade_count"],
            "wins": row["wins"],
            "losses": row["losses"],
        })

    return {
        "success": True,
        "data": daily_data,
        "period_days": days,
        "message": None,
    }


@app.get("/api/reports/equity")
async def get_equity_curve(days: int = 30):
    """Cumulative equity curve — running total P&L over time."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                DATE(timestamp) as date,
                COALESCE(SUM(CASE WHEN pnl_net IS NOT NULL THEN pnl_net ELSE 0 END), 0) as daily_pnl
            FROM trades
            WHERE action = 'SELL' AND broker != 'PAPER'
              AND datetime(timestamp) >= datetime('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp) ASC
        """, (f"-{days} days",)).fetchall()

    # Compute cumulative equity
    equity_curve = []
    cumulative = 0.0
    for row in rows:
        cumulative += row["daily_pnl"]
        equity_curve.append({
            "date": row["date"],
            "equity": round(cumulative, 2),
            "daily_pnl": row["daily_pnl"],
        })

    return {
        "success": True,
        "data": equity_curve,
        "final_equity": round(cumulative, 2) if equity_curve else 0.0,
        "period_days": days,
        "message": None,
    }


@app.get("/api/reports/by-symbol")
async def get_symbol_performance(days: int = 30):
    """Per-symbol performance breakdown — profitability by symbol."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                symbol,
                COALESCE(SUM(CASE WHEN pnl_net IS NOT NULL THEN pnl_net ELSE 0 END), 0) as net_pnl,
                COUNT(*) as trade_count,
                SUM(CASE WHEN pnl_net > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_net < 0 THEN 1 ELSE 0 END) as losses
            FROM trades
            WHERE action = 'SELL' AND broker != 'PAPER'
              AND datetime(timestamp) >= datetime('now', ?)
            GROUP BY symbol
            ORDER BY net_pnl DESC
        """, (f"-{days} days",)).fetchall()

    symbol_data = []
    for row in rows:
        win_count = row["wins"]
        loss_count = row["losses"]
        denom = win_count + loss_count
        win_rate = (win_count / denom * 100.0) if denom > 0 else 0.0

        symbol_data.append({
            "symbol": row["symbol"],
            "net_pnl": round(row["net_pnl"], 2),
            "trade_count": row["trade_count"],
            "wins": win_count,
            "losses": loss_count,
            "win_rate": round(win_rate, 2),
        })

    return {
        "success": True,
        "data": symbol_data,
        "period_days": days,
        "message": None,
    }


# ---------------------------------------------------------------------------
# Routes — Write (PIN protected)
# ---------------------------------------------------------------------------
@app.post("/api/panic")
async def panic_stop(req: PanicRequest):
    """Emergency stop. Sets bot_status=STOP in DB. kickstart.py polls this every cycle."""
    verify_pin(req.pin)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO system_control (key, value, updated_at)
            VALUES ('bot_status', 'STOP', datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value='STOP', updated_at=datetime('now')
        """)
        conn.commit()

    return {
        "success": True,
        "bot_status": "STOP",
        "message": "Panic stop signal sent. Engine will halt within one trading cycle (~30s).",
    }


@app.post("/api/control")
async def bot_control(req: BotControlRequest):
    """Start or stop the bot. Action must be 'START' or 'STOP'."""
    verify_pin(req.pin)

    action = req.action.upper()
    if action not in ("START", "STOP"):
        raise HTTPException(status_code=400, detail="action must be START or STOP")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO system_control (key, value, updated_at)
            VALUES ('bot_status', ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=?, updated_at=datetime('now')
        """, (action, action))
        conn.commit()

    return {"success": True, "bot_status": action}


@app.put("/api/settings/trend-filter")
async def update_trend_filter(update: TrendFilterUpdate):
    """
    Update trend filter settings. Changes take effect within one trading cycle.
    ma_period: 10–200 (days)
    ma_type: 'SMA' or 'EMA'
    """
    verify_pin(update.pin)

    if not (10 <= update.ma_period <= 200):
        raise HTTPException(status_code=400, detail="ma_period must be between 10 and 200")
    if update.ma_type not in ("SMA", "EMA"):
        raise HTTPException(status_code=400, detail="ma_type must be SMA or EMA")

    with open(SETTINGS_PATH) as f:
        settings = json.load(f)

    settings.setdefault("strategies", {})["trend_filter"] = {
        "enabled": update.enabled,
        "ma_period": update.ma_period,
        "ma_type": update.ma_type,
    }

    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)

    return {
        "success": True,
        "trend_filter": settings["strategies"]["trend_filter"],
        "message": "Trend filter updated. Takes effect within 30 seconds.",
    }


# ---------------------------------------------------------------------------
# Mobile HTML Dashboard
# ---------------------------------------------------------------------------
def _build_dashboard_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>Zepp — ARUN Bot</title>
<style>
  :root {
    --bg: #EFEBE3; --card: #fff; --accent: #479FB6;
    --success: #10B981; --danger: #EF4444; --warn: #F59E0B;
    --text: #1a1a2e; --muted: #6b7280; --border: #e5e7eb;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: var(--bg); color: var(--text); min-height: 100vh; }
  .header { background: var(--accent); color: #fff; padding: 16px 20px;
            display: flex; justify-content: space-between; align-items: center;
            position: sticky; top: 0; z-index: 10; }
  .header h1 { font-size: 18px; font-weight: 700; letter-spacing: -0.3px; }
  .header-right { text-align: right; }
  .header-time { font-size: 12px; opacity: 0.85; }
  .header-date { font-size: 11px; opacity: 0.65; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 14px; }
  .card { background: var(--card); border-radius: 14px; padding: 16px;
          box-shadow: 0 1px 4px rgba(0,0,0,.07); }
  .card.full { grid-column: 1 / -1; }
  .card.danger-card { border: 1.5px solid var(--danger); }

  .label { font-size: 11px; color: var(--muted); text-transform: uppercase;
           letter-spacing: 0.6px; margin-bottom: 6px; font-weight: 500; }
  .value { font-size: 24px; font-weight: 700; line-height: 1.1; }
  .value.green { color: var(--success); }
  .value.red { color: var(--danger); }
  .value.warn { color: var(--warn); }
  .sub { font-size: 11px; color: var(--muted); margin-top: 3px; }

  .pill { display: inline-flex; align-items: center; gap: 6px;
          padding: 5px 12px; border-radius: 99px; font-size: 13px; font-weight: 600; }
  .pill.running { background: #d1fae5; color: #065f46; }
  .pill.stopped { background: #fee2e2; color: #7f1d1d; }
  .pill.unknown { background: #f3f4f6; color: var(--muted); }

  .trade-row { display: flex; align-items: center; gap: 10px;
               padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
  .trade-row:last-child { border-bottom: none; padding-bottom: 0; }
  .badge { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;
           min-width: 40px; text-align: center; }
  .badge.buy  { background: #dbeafe; color: #1e40af; }
  .badge.sell { background: #dcfce7; color: #166534; }
  .trade-symbol { font-weight: 600; flex: 1; }
  .trade-price { color: var(--muted); }
  .trade-pnl { font-weight: 600; min-width: 60px; text-align: right; }

  .position-row { display: flex; justify-content: space-between; align-items: center;
                  padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
  .position-row:last-child { border-bottom: none; padding-bottom: 0; }
  .pos-sym { font-weight: 600; }
  .pos-detail { font-size: 11px; color: var(--muted); margin-top: 2px; }

  .btn { width: 100%; padding: 15px; border: none; border-radius: 12px;
         font-size: 15px; font-weight: 700; cursor: pointer; transition: opacity .15s; }
  .btn:active { opacity: 0.75; }
  .btn-panic { background: var(--danger); color: #fff; }
  .btn-start { background: var(--success); color: #fff; margin-top: 10px; }

  .settings-row { display: flex; justify-content: space-between; align-items: center;
                  padding: 12px 0; border-bottom: 1px solid var(--border); }
  .settings-row:last-child { border-bottom: none; }
  .settings-label { font-size: 13px; font-weight: 500; }
  .settings-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .toggle { position: relative; width: 44px; height: 24px; }
  .toggle input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; inset: 0; background: #d1d5db; border-radius: 99px;
            cursor: pointer; transition: .2s; }
  .slider:before { content:''; position: absolute; width: 18px; height: 18px;
                   left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: .2s; }
  input:checked + .slider { background: var(--accent); }
  input:checked + .slider:before { transform: translateX(20px); }

  input[type=range] { width: 100%; accent-color: var(--accent); }
  select { border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px;
           font-size: 13px; background: #fff; color: var(--text); }

  .footer { text-align: center; font-size: 11px; color: var(--muted); padding: 12px 16px 24px; }
  .footer a { color: var(--accent); text-decoration: none; }
  .spinner { animation: spin 1s linear infinite; display: inline-block; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-card { text-align: center; padding: 40px; color: var(--muted); }
  .error-banner { background: #fee2e2; color: #7f1d1d; padding: 12px 16px;
                  font-size: 13px; border-radius: 10px; margin: 14px; }
  .warn-note { background: #fef3c7; color: #92400e; padding: 10px 12px;
               border-radius: 8px; font-size: 12px; margin-top: 10px; }
</style>
</head>
<body>

<div class="header">
  <h1>&#9889; Zepp</h1>
  <div class="header-right">
    <div class="header-time" id="htime">--:--</div>
    <div class="header-date" id="hdate"></div>
  </div>
</div>

<div id="error-area"></div>
<div class="grid" id="grid">
  <div class="card full loading-card">
    <span class="spinner">&#9696;</span> Loading dashboard...
  </div>
</div>

<div class="footer">
  Auto-refreshes every 30s &nbsp;&middot;&nbsp;
  <a href="/api/docs">API Docs</a> &nbsp;&middot;&nbsp;
  Zepp v1.0
</div>

<script>
// ---------- State ----------
let tfSettings = { enabled: false, ma_period: 50, ma_type: 'SMA' };
let lastData = {};

// ---------- Load all data ----------
async function load() {
  try {
    const [status, perf, positions, trades] = await Promise.all([
      api('/api/status'),
      api('/api/performance?days=30'),
      api('/api/positions'),
      api('/api/trades?limit=5'),
    ]);
    lastData = { status, perf, positions, trades };
    document.getElementById('error-area').innerHTML = '';
    renderDashboard(status, perf, positions, trades);
  } catch(e) {
    document.getElementById('error-area').innerHTML =
      `<div class="error-banner">&#9888; Cannot reach Zepp server. Check VPS. (${e.message})</div>`;
  }
}

async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) { const d = await r.json(); throw new Error(d.detail || r.statusText); }
  return r.json();
}

// ---------- Render ----------
function renderDashboard(status, perf, positions, trades) {
  const isRunning = status.bot_status === 'RUNNING';
  const pillClass = isRunning ? 'running' : status.bot_status === 'STOP' ? 'stopped' : 'unknown';
  const pillLabel = isRunning ? '&#9679; RUNNING' : status.bot_status === 'STOP' ? '&#9632; STOPPED' : status.bot_status;

  const pnl = perf.net_profit_inr || 0;
  const pnlClass = pnl >= 0 ? 'green' : 'red';
  const pnlStr = (pnl >= 0 ? '+' : '') + '&#8377;' + Math.abs(pnl).toLocaleString('en-IN', {maximumFractionDigits: 0});

  const wr = perf.win_rate_pct || 0;
  const wrClass = wr >= 55 ? 'green' : wr >= 45 ? 'warn' : 'red';

  const tradeRows = (trades.trades || []).map(t => {
    const pnlColor = t.pnl_net > 0 ? 'var(--success)' : t.pnl_net < 0 ? 'var(--danger)' : 'var(--muted)';
    const pnlLabel = t.pnl_net != null ? (t.pnl_net >= 0 ? '+' : '') + '&#8377;' + Math.round(t.pnl_net) : '—';
    return `<div class="trade-row">
      <span class="badge ${t.action.toLowerCase()}">${t.action}</span>
      <span class="trade-symbol">${t.symbol}</span>
      <span class="trade-price">&#8377;${t.price}</span>
      <span class="trade-pnl" style="color:${pnlColor}">${t.action==='SELL' ? pnlLabel : ''}</span>
    </div>`;
  }).join('') || '<div style="color:var(--muted);font-size:13px;padding:8px 0">No trades yet</div>';

  const posRows = (positions.positions || []).slice(0, 5).map(p => {
    const invested = '&#8377;' + (p.total_invested || 0).toLocaleString('en-IN', {maximumFractionDigits: 0});
    return `<div class="position-row">
      <div>
        <div class="pos-sym">${p.symbol}</div>
        <div class="pos-detail">${p.net_qty} shares @ &#8377;${(p.avg_entry||0).toFixed(1)}</div>
      </div>
      <div style="text-align:right">
        <div style="font-weight:600;font-size:13px">${invested}</div>
        <div class="pos-detail">${p.exchange}</div>
      </div>
    </div>`;
  }).join('') || '<div style="color:var(--muted);font-size:13px;padding:8px 0">No open positions</div>';

  const nullNote = perf.trades_missing_pnl > 0
    ? `<div class="warn-note">&#9888; ${perf.trades_missing_pnl} trades missing P&L data. Run backfill_pnl.py to fix.</div>`
    : '';

  document.getElementById('grid').innerHTML = `
    <div class="card full">
      <div class="label">Bot Status</div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;flex-wrap:wrap;gap:8px">
        <span class="pill ${pillClass}">${pillLabel}</span>
        <span style="font-size:12px;color:var(--muted)">${status.trades_today} trades today</span>
      </div>
      ${status.last_trade ? `<div class="sub" style="margin-top:8px">Last: ${status.last_trade.action} ${status.last_trade.symbol} @ &#8377;${status.last_trade.price}</div>` : ''}
    </div>

    <div class="card">
      <div class="label">Net P&L (30d)</div>
      <div class="value ${pnlClass}">${pnlStr}</div>
      <div class="sub">${perf.total_trades || 0} trades</div>
    </div>

    <div class="card">
      <div class="label">Win Rate</div>
      <div class="value ${wrClass}">${wr}%</div>
      <div class="sub">${perf.winning_trades || 0}W / ${perf.losing_trades || 0}L</div>
    </div>

    <div class="card">
      <div class="label">Open Positions</div>
      <div class="value">${positions.count}</div>
      <div class="sub">Active holdings</div>
    </div>

    <div class="card">
      <div class="label">Avg per Trade</div>
      <div class="value ${(perf.avg_per_trade_inr||0) >= 0 ? 'green' : 'red'}">${(perf.avg_per_trade_inr||0) >= 0 ? '+' : ''}&#8377;${Math.round(perf.avg_per_trade_inr||0)}</div>
      <div class="sub">Net of fees</div>
    </div>

    <div class="card full">
      <div class="label" style="margin-bottom:10px">Open Positions</div>
      ${posRows}
    </div>

    <div class="card full">
      <div class="label" style="margin-bottom:10px">Recent Trades</div>
      ${tradeRows}
      ${nullNote}
    </div>

    <div class="card full">
      <div class="label" style="margin-bottom:10px">Trend Filter Settings</div>
      <div class="settings-row">
        <div>
          <div class="settings-label">Enable Trend Filter</div>
          <div class="settings-sub">Only buy when stock is in uptrend (above MA)</div>
        </div>
        <label class="toggle">
          <input type="checkbox" id="tf-enabled" ${tfSettings.enabled ? 'checked' : ''} onchange="tfChanged()">
          <span class="slider"></span>
        </label>
      </div>
      <div class="settings-row">
        <div>
          <div class="settings-label">MA Period: <strong id="ma-period-label">${tfSettings.ma_period}</strong> days</div>
          <div class="settings-sub">Shorter = more sensitive, longer = smoother</div>
        </div>
      </div>
      <div style="padding:4px 0 12px">
        <input type="range" id="tf-period" min="10" max="200" step="5" value="${tfSettings.ma_period}"
          oninput="document.getElementById('ma-period-label').textContent=this.value">
      </div>
      <div class="settings-row">
        <div>
          <div class="settings-label">MA Type</div>
          <div class="settings-sub">SMA = Simple average &nbsp;|&nbsp; EMA = Exponential (faster)</div>
        </div>
        <select id="tf-type">
          <option value="SMA" ${tfSettings.ma_type==='SMA'?'selected':''}>SMA</option>
          <option value="EMA" ${tfSettings.ma_type==='EMA'?'selected':''}>EMA</option>
        </select>
      </div>
      <button class="btn" style="background:var(--accent);color:#fff;margin-top:4px" onclick="saveTrendFilter()">
        Save Trend Filter Settings
      </button>
    </div>

    <div class="card full">
      <div class="label" style="margin-bottom:10px">Advanced Reports</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <button class="btn" style="background:var(--accent);color:#fff;font-size:12px;padding:10px" onclick="viewDailyPnL()">
          Daily P&L
        </button>
        <button class="btn" style="background:var(--accent);color:#fff;font-size:12px;padding:10px" onclick="viewEquityCurve()">
          Equity Curve
        </button>
        <button class="btn" style="background:var(--accent);color:#fff;font-size:12px;padding:10px" onclick="viewSymbolBreakdown()">
          Symbol Breakdown
        </button>
      </div>
      <div id="reports-area" style="margin-top:10px;display:none;font-size:12px;color:var(--muted)">
        Report data will appear here
      </div>
    </div>

    <div class="card full danger-card">
      <div class="label" style="color:var(--danger);margin-bottom:10px">Emergency Controls</div>
      <button class="btn btn-panic" onclick="panicStop()">&#128721; PANIC STOP — Halt All Trading</button>
      ${!isRunning ? `<button class="btn btn-start" onclick="startBot()">&#9654; Start Bot</button>` : ''}
    </div>
  `;
}

// ---------- Actions ----------
async function panicStop() {
  const pin = prompt('Enter Zepp PIN to confirm PANIC STOP:');
  if (!pin) return;
  if (!confirm('This will immediately halt the trading engine. Continue?')) return;
  try {
    await api('/api/panic', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pin}) });
    alert('Panic stop sent. Engine will halt within ~30 seconds.');
    load();
  } catch(e) { alert('Error: ' + e.message); }
}

async function startBot() {
  const pin = prompt('Enter Zepp PIN to start the bot:');
  if (!pin) return;
  try {
    await api('/api/control', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({pin, action:'START'}) });
    alert('Start signal sent.');
    load();
  } catch(e) { alert('Error: ' + e.message); }
}

function tfChanged() {
  tfSettings.enabled = document.getElementById('tf-enabled').checked;
}

async function saveTrendFilter() {
  const pin = prompt('Enter Zepp PIN to save settings:');
  if (!pin) return;
  const body = {
    pin,
    enabled: document.getElementById('tf-enabled').checked,
    ma_period: parseInt(document.getElementById('tf-period').value),
    ma_type: document.getElementById('tf-type').value,
  };
  try {
    const r = await api('/api/settings/trend-filter', {
      method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
    });
    tfSettings = r.trend_filter;
    alert('Trend filter saved. Takes effect within 30 seconds.');
  } catch(e) { alert('Error: ' + e.message); }
}

// ---------- Reports ----------
async function viewDailyPnL() {
  try {
    const r = await api('/api/reports/daily?days=30');
    const area = document.getElementById('reports-area');
    if (!r.data || r.data.length === 0) {
      area.innerHTML = '<div style="color:var(--muted)">No data available</div>';
    } else {
      let html = '<strong>Daily P&L (30d):</strong><div style="max-height:200px;overflow-y:auto;margin-top:8px">';
      for (const d of r.data) {
        const pnl = d.net_pnl || 0;
        const color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
        html += `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:11px">
          <span>${d.date} (${d.trade_count})</span>
          <span style="color:${color};font-weight:600">₹${pnl.toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
        </div>`;
      }
      html += '</div>';
      area.innerHTML = html;
    }
    area.style.display = 'block';
  } catch(e) { alert('Error: ' + e.message); }
}

async function viewEquityCurve() {
  try {
    const r = await api('/api/reports/equity?days=30');
    const area = document.getElementById('reports-area');
    if (!r.data || r.data.length === 0) {
      area.innerHTML = '<div style="color:var(--muted)">No data available</div>';
    } else {
      let html = `<strong>Equity Curve (30d):</strong><div style="margin-top:8px">Final: <strong style="font-size:16px">₹${(r.final_equity || 0).toLocaleString('en-IN', {maximumFractionDigits:0})}</strong></div>`;
      html += '<div style="max-height:200px;overflow-y:auto;margin-top:8px">';
      for (const d of r.data.slice(-10)) {
        const equity = d.equity || 0;
        const color = equity >= 0 ? 'var(--success)' : 'var(--danger)';
        html += `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:11px">
          <span>${d.date}</span>
          <span style="color:${color};font-weight:600">₹${equity.toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
        </div>`;
      }
      html += '</div>';
      area.innerHTML = html;
    }
    area.style.display = 'block';
  } catch(e) { alert('Error: ' + e.message); }
}

async function viewSymbolBreakdown() {
  try {
    const r = await api('/api/reports/by-symbol?days=30');
    const area = document.getElementById('reports-area');
    if (!r.data || r.data.length === 0) {
      area.innerHTML = '<div style="color:var(--muted)">No data available</div>';
    } else {
      let html = '<strong>Symbol Performance (30d):</strong><div style="max-height:200px;overflow-y:auto;margin-top:8px">';
      for (const s of r.data) {
        const pnl = s.net_pnl || 0;
        const color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
        html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:11px">
          <div>
            <div style="font-weight:600">${s.symbol}</div>
            <div style="color:var(--muted);font-size:10px">${s.wins}W/${s.losses}L (${s.win_rate}%)</div>
          </div>
          <span style="color:${color};font-weight:600">₹${pnl.toLocaleString('en-IN', {maximumFractionDigits:0})}</span>
        </div>`;
      }
      html += '</div>';
      area.innerHTML = html;
    }
    area.style.display = 'block';
  } catch(e) { alert('Error: ' + e.message); }
}

// ---------- Clock ----------
function tick() {
  const now = new Date();
  document.getElementById('htime').textContent = now.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'});
  document.getElementById('hdate').textContent = now.toLocaleDateString('en-IN', {weekday:'short', day:'numeric', month:'short'});
}

// ---------- Load trend filter settings on start ----------
async function loadTfSettings() {
  try {
    const s = await api('/api/settings');
    if (s.strategies && s.strategies.trend_filter) {
      tfSettings = s.strategies.trend_filter;
    }
  } catch(e) { /* ignore */ }
}

// ---------- Init ----------
tick();
setInterval(tick, 1000);
loadTfSettings().then(load);
setInterval(load, 30000);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point (for local testing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting Zepp Web API on http://0.0.0.0:8001")
    print(f"DB: {DB_PATH}")
    print(f"Settings: {SETTINGS_PATH}")
    print(f"PIN set: {'YES' if ZEPP_PIN else 'NO — set ZEPP_PIN in .env'}")
    uvicorn.run("web_api:app", host="0.0.0.0", port=8001, reload=False)
