"""
Read-only dashboard API for the small-cap strategy.

Mounted into backend/main.py with one line:
    from backend.strategy_routes import build_router
    app.include_router(build_router())

Everything here READS database/strategies.db + the strategy config. The only
write is POST /strategy/api/stop, which drops a stop-flag file the runner checks.
No prices are fetched live, no orders are placed.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB = os.path.join(_ROOT, "database", "strategies.db")
_DEFAULT_CFG = os.path.join(_ROOT, "strategies", "configs", "small_cap_dryrun.json")
_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "strategy.html")
_NAME = "small_cap_dryrun"


def build_router(db_path: str = _DEFAULT_DB, cfg_path: str = _DEFAULT_CFG) -> APIRouter:
    r = APIRouter(prefix="/strategy", tags=["small-cap"])
    stop_flag = os.path.join(os.path.dirname(db_path), "strategy_stop.flag")

    def _store():
        from strategies.framework.store import Store
        s = Store(db_path)
        s._create()
        return s

    def _cfg():
        from strategies.framework.registry import load
        return load(cfg_path).cfg if os.path.exists(cfg_path) else None

    @r.get("", response_class=HTMLResponse)
    @r.get("/", response_class=HTMLResponse)
    def page():
        if os.path.exists(_HTML):
            with open(_HTML, encoding="utf-8") as fh:
                return HTMLResponse(fh.read())
        return HTMLResponse("<h1>strategy.html missing</h1>", status_code=500)

    @r.get("/api/scan")
    def scan(limit: int = Query(10, ge=1, le=100)):
        s = _store()
        try:
            return s.get_scan(_NAME, limit=limit)
        finally:
            s.close()

    @r.get("/api/positions")
    def positions():
        s = _store()
        try:
            return s.open_positions(_NAME)
        finally:
            s.close()

    @r.get("/api/activity")
    def activity(limit: int = Query(20, ge=1, le=200)):
        s = _store()
        try:
            return s.get_fills(_NAME, limit=limit)
        finally:
            s.close()

    @r.get("/api/howitworks")
    def howitworks():
        from strategies.framework.registry import load
        if not os.path.exists(cfg_path):
            return {"text": "config not set up yet"}
        return {"text": load(cfg_path).describe()}

    @r.get("/api/settings")
    def settings():
        c = _cfg()
        if c is None:
            return JSONResponse({"error": "no config file"}, status_code=404)
        return {
            "per_stock_amount": c.budget.per_stock_amount,
            "total_budget": c.budget.total_budget,
            "max_names": c.budget.max_names,
            "max_names_cap": c.budget.max_names_cap,
            "pct_of_account_cap": c.budget.pct_of_account_cap,
            "fresh_cross_max_age_days": c.entry.fresh_cross_max_age_days,
            "require_200ema_uptrend": c.entry.require_200ema_uptrend,
            "fundamentals_gate": c.fundamentals.enabled,
            "min_roe": c.fundamentals.min_roe,
            "max_debt_equity": c.fundamentals.max_debt_equity,
            "market_cap_band_cr": [c.min_market_cap_cr, c.max_market_cap_cr],
            "min_avg_daily_value_cr": c.liquidity.min_avg_daily_value_cr,
            "trail_giveback_pct": c.exit.trail_giveback_pct,
            "min_profit_floor_pct": c.exit.min_profit_floor_pct,
            "scale_out_step_pct": c.exit.scale_out_step_pct,
            "hard_stop_pct": c.exit.hard_stop_pct,
            "strand_final_half": c.exit.strand_final_half,
            "circuit_band_pct": c.rules.circuit_band_pct,
            "fill_assumption": c.costs.fill_assumption,
            "orders_enabled": c.orders_enabled,
        }

    @r.get("/api/status")
    def status():
        stopped = os.path.exists(stop_flag)
        line = ""
        sp = os.path.join(os.path.dirname(db_path), "..", "status.txt")
        if os.path.exists(sp):
            with open(sp, encoding="utf-8") as fh:
                line = fh.read().strip()
        return {"stopped": stopped, "last_cycle": line}

    @r.post("/api/stop")
    def stop():
        with open(stop_flag, "w", encoding="utf-8") as fh:
            fh.write("stopped by dashboard\n")
        return {"stopped": True}

    @r.post("/api/start")
    def start():
        if os.path.exists(stop_flag):
            os.remove(stop_flag)
        return {"stopped": False}

    return r
