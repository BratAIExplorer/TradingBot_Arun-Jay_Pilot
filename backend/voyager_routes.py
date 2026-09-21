"""Dashboard API for Voyager buy-dip/sell-% rules. Edit rules; preview what the engine WOULD do.
Never sends orders — that is brokers/dip_engine.py, gated by env VOYAGER_ORDERS_ENABLED=1."""
from __future__ import annotations

import os

from fastapi import APIRouter, Body, HTTPException

from brokers import dip_engine


def build_router() -> APIRouter:
    r = APIRouter(prefix="/api/voyager")

    @r.get("/rules")
    def get_rules():
        return {"rules": dip_engine.load_rules(), "max": dip_engine.MAX_RULES,
                "orders_enabled": dip_engine.orders_enabled()}

    @r.put("/rules")
    def put_rules(body: dict = Body(...)):
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
            return {"rows": dip_engine.run_once(b, live=False)}
        except Exception as e:
            return {"error": str(e), "rows": []}
        finally:
            b.disconnect()

    return r
