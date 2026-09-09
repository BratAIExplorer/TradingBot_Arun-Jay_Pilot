"""
TDD for backend/strategy_routes.py — the read-only dashboard API.

The route handlers are plain sync functions; we call them directly off the
APIRouter (no ASGI server) against a throwaway strategies.db.

Run:  python -m pytest strategies/tests/test_strategy_routes.py -q
"""
import os
import tempfile

import pytest

from strategies.framework.store import Store
from backend.strategy_routes import build_router

_CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "configs", "small_cap_dryrun.json")


class _Router:
    """Look handlers up by (method, path) and call them directly."""
    def __init__(self, router):
        self._h = {}
        for rt in router.routes:
            for m in rt.methods:
                self._h[(m, rt.path)] = rt.endpoint

    def get(self, path, **kw):
        return self._h[("GET", "/strategy" + path)](**kw)

    def post(self, path, **kw):
        return self._h[("POST", "/strategy" + path)](**kw)


@pytest.fixture()
def api():
    d = tempfile.mkdtemp()
    db = os.path.join(d, "strategies.db")
    s = Store(db)
    s._create()
    s.save_scan("small_cap_dryrun", [
        {"ticker": "AAA.NS", "exchange": "NSE", "price": 100, "score": 90, "signal": "STRONG BUY", "reason": "x"},
        {"ticker": "BBB.NS", "exchange": "NSE", "price": 50, "score": 70, "signal": "BUY", "reason": "y"},
        {"ticker": "CCC.NS", "exchange": "NSE", "price": 20, "score": 61, "signal": "BUY", "reason": "z"},
    ])
    s.upsert_position("small_cap_dryrun", "AAA.NS", "NSE", 10, 95.0, 1, "01-Sep-2026",
                      "2026-09-01T10:00:00")
    s.close()
    return _Router(build_router(db_path=db, cfg_path=_CFG))


def test_dashboard_page_is_served(api):
    resp = api.get("")
    body = resp.body.decode()
    assert resp.status_code == 200 and "STOP" in body.upper()


def test_scan_api_returns_ranked_rows_and_honours_limit(api):
    rows = api.get("/api/scan", limit=2)
    assert [x["ticker"] for x in rows] == ["AAA.NS", "BBB.NS"]
    assert rows[0]["rank"] == 1


def test_positions_api_lists_holdings(api):
    rows = api.get("/api/positions")
    assert len(rows) == 1 and rows[0]["ticker"] == "AAA.NS" and rows[0]["qty"] == 10


def test_howitworks_api_is_plain_english(api):
    txt = api.get("/api/howitworks")["text"]
    assert "stop-loss" in txt.lower() and "rope" in txt.lower()


def test_settings_api_exposes_the_budget_cap(api):
    s = api.get("/api/settings")
    assert s["total_budget"] == 30000 and s["per_stock_amount"] == 10000
    assert s["max_names"] == 3


def test_stop_then_status_reports_stopped(api):
    assert api.post("/api/stop")["stopped"] is True
    assert api.get("/api/status")["stopped"] is True
    assert api.post("/api/start")["stopped"] is False
