"""Dashboard API for Voyager buy-dip/sell-% rules. Edit rules; preview what the engine WOULD do.
Never sends orders — that is brokers/dip_engine.py, gated by env VOYAGER_ORDERS_ENABLED=1."""
from __future__ import annotations

import hmac
import os
import time

from fastapi import APIRouter, Body, HTTPException

from brokers import dip_engine

# Starter list: liquid names under $100/share (checked 2026-09-21) so a $100 buy can afford a whole share.
# The dashboard adds these switched OFF.
SEED = ["HPQ", "CMCSA", "PYPL", "T", "VZ", "F", "NKE", "SBUX", "KO", "KHC", "PFE", "VTRS", "BAC", "WFC", "OXY"]


def _check_pin(pin) -> None:
    """Same rule as backend/main.py _check_pin (kept local: main imports this module). Empty env = no gate."""
    required = os.environ.get("TRADINGBOT_PIN", "")
    if required and not hmac.compare_digest(str(pin or ""), required):
        raise HTTPException(status_code=403, detail="wrong or missing PIN")


def _engine_view(state: dict | None) -> dict:
    return {"health": dip_engine.engine_health(state),
            "mode": state["mode"] if state else None,
            "interval_min": state["interval_min"] if state else None,
            "last_cycle_ts": state["ts"] if state else None,
            "error": state.get("error") if state else None,
            "readonly": dip_engine.readonly(),
            "now": time.time()}


def build_router() -> APIRouter:
    r = APIRouter(prefix="/api/voyager")

    @r.get("/rules")
    def get_rules():
        return {"rules": dip_engine.load_rules(), "max": dip_engine.MAX_RULES, "seed": SEED,
                "engine": _engine_view(dip_engine.read_state())}

    @r.get("/state")
    def get_state():
        st = dip_engine.read_state()
        return {"engine": _engine_view(st), "rows": st["rows"] if st else []}

    @r.put("/rules")
    def put_rules(body: dict = Body(...)):
        _check_pin(body.get("pin"))
        try:
            return {"rules": dip_engine.save_rules(body.get("rules"))}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @r.post("/preview")
    def preview():
        from brokers.ibkr_broker import IBKRBroker
        b = IBKRBroker(client_id=int(os.environ.get("IBKR_DASHBOARD_CLIENT_ID", "9")))
        try:
            b.connect()
            rows = dip_engine.run_once(b, live=False, state=dip_engine.load_dip_state(), preview=True)
            return {"rows": rows, "ts": time.time(), "readonly": dip_engine.readonly(),
                    "degraded": any(not x["account_ok"] for x in rows)}
        except Exception as e:
            return {"error": str(e), "rows": []}
        finally:
            b.disconnect()

    return r
