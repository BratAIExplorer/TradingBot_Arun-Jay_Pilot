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

import json
import os

from fastapi import APIRouter, Body, Query
from fastapi.responses import HTMLResponse, JSONResponse

# Dashboard-editable settings: flat key -> (JSON path, kind).
# orders_enabled is deliberately absent — the live-money switch stays file-only.
_EDITABLE = {
    "per_stock_amount":         (("budget", "per_stock_amount"), "num+"),
    "total_budget":             (("budget", "total_budget"), "num+"),
    "max_names_cap":            (("budget", "max_names_cap"), "int+"),
    "fresh_cross_max_age_days": (("entry", "fresh_cross_max_age_days"), "int0"),
    "require_200ema_uptrend":   (("entry", "require_200ema_uptrend"), "bool"),
    "fundamentals_gate":        (("fundamentals_gate", "enabled"), "bool"),
    "min_roe":                  (("fundamentals_gate", "min_roe"), "num"),
    "max_debt_equity":          (("fundamentals_gate", "max_debt_equity"), "num+"),
    "min_market_cap_cr":        (("fundamentals_gate", "min_market_cap_cr"), "num+"),
    "max_market_cap_cr":        (("fundamentals_gate", "max_market_cap_cr"), "num+"),
    "min_avg_daily_value_cr":   (("liquidity_gate", "min_avg_daily_value_cr"), "num+"),
    "trail_giveback_pct":       (("exit", "trail_giveback_pct"), "num+"),
    "min_profit_floor_pct":     (("exit", "min_profit_floor_pct"), "num"),
    "scale_out_step_pct":       (("exit", "scale_out_step_pct"), "num+"),
    "hard_stop_pct":            (("exit", "hard_stop_pct"), "nullnum"),
    "strand_final_half":        (("exit", "strand_final_half"), "bool"),
    "circuit_band_pct":         (("rules", "circuit_band_pct"), "num+"),
    "fill_assumption":          (("costs", "fill_assumption"), "enum:best,realistic"),
}


def _coerce(kind: str, v):
    if kind == "bool":
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("1", "true", "yes", "on")
    if kind.startswith("enum:"):
        opts = kind[5:].split(",")
        if str(v) not in opts:
            raise ValueError(f"must be one of {', '.join(opts)}")
        return str(v)
    if kind == "nullnum":
        if v in (None, "", "null", "OFF", "off"):
            return None
        return float(v)
    f = float(v)
    if kind in ("num+", "int+") and f <= 0:
        raise ValueError("must be greater than 0")
    if kind == "int0" and f < 0:
        raise ValueError("must be 0 or more")
    if kind in ("int+", "int0"):
        return int(f)
    return int(f) if f.is_integer() else f  # keep 10000, not 10000.0

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
            return list(reversed(s.get_fills(_NAME)))[:limit]  # newest first, capped
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
            "min_market_cap_cr": c.min_market_cap_cr,
            "max_market_cap_cr": c.max_market_cap_cr,
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

    @r.post("/api/settings")
    def save_settings(patch: dict = Body(...)):
        if not os.path.exists(cfg_path):
            return JSONResponse({"error": "no config file"}, status_code=404)
        if "orders_enabled" in patch:
            return JSONResponse(
                {"error": "orders_enabled is the live-money switch — edit the JSON file directly, not the dashboard"},
                status_code=403)
        with open(cfg_path, encoding="utf-8") as fh:
            data = json.load(fh)
        changes = {}
        for k, val in patch.items():
            if k not in _EDITABLE:
                return JSONResponse({"error": f"unknown or non-editable setting: {k}"}, status_code=400)
            path, kind = _EDITABLE[k]
            try:
                cv = _coerce(kind, val)
            except (TypeError, ValueError) as e:
                return JSONResponse({"error": f"{k}: {e}"}, status_code=400)
            d = data
            for p in path[:-1]:
                d = d.setdefault(p, {})
            d[path[-1]] = cv
            changes[k] = cv
        fgd = data.get("fundamentals_gate", {})
        if fgd.get("min_market_cap_cr", 0) >= fgd.get("max_market_cap_cr", float("inf")):
            return JSONResponse({"error": "min_market_cap_cr must be below max_market_cap_cr"}, status_code=400)
        tmp = cfg_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        try:
            from strategies.framework.config import load_strategy_config
            load_strategy_config(tmp)
        except Exception as e:  # noqa: BLE001 — reject anything the loader won't accept
            os.remove(tmp)
            return JSONResponse({"error": f"rejected — config would not load: {e}"}, status_code=400)
        os.replace(tmp, cfg_path)
        return {"saved": changes, "note": "takes effect on the next runner start"}

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
