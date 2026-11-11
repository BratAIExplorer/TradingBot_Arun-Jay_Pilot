"""
TDD for strategies/scan_and_store.py — the read-only "run the scan, keep the
result" entrypoint. No orders, no positions; just scan -> rank -> persist.

Run:  python -m pytest strategies/tests/test_scan_and_store.py -q
"""
import os
import tempfile

import pandas as pd

from strategies.framework.store import Store
from strategies.framework.registry import build
from strategies.tests.test_screens import _cfg
from strategies.scan_and_store import scan_and_store


class _StubScanner:
    """Stands in for SmallCapScanner: returns fixed scored rows, no network."""
    def __init__(self, rows):
        self._rows = rows

    def scan_market(self, mode="SMALLCAP"):
        return self._rows


def _row(t, score):
    return {"ticker": t, "company": t, "price": 100.0 + score, "signal": "BUY",
            "confluence_score": score, "macd_cross_date": "01-Sep-2026", "days_ago": 2,
            "above_20ma": True, "above_50ma": True, "ma_20": 1.0, "ma_50": 1.0, "rsi": 55}


def _store():
    p = os.path.join(tempfile.mkdtemp(), "s.db")
    s = Store(p)
    s._create()
    return s


def test_persists_every_candidate_and_ranks_by_score():
    strat = build(_cfg())
    scanner = _StubScanner([_row("A.NS", 62), _row("B.NS", 88), _row("C.NS", 71)])
    store = _store()

    ranked = scan_and_store(strat, store, scanner=scanner)

    assert [r["ticker"] for r in ranked] == ["B.NS", "C.NS", "A.NS"]
    saved = store.get_scan("small_cap_dryrun")
    assert [r["ticker"] for r in saved] == ["B.NS", "C.NS", "A.NS"]
    assert saved[0]["rank"] == 1


def test_top_5_and_top_10_come_straight_off_the_store():
    strat = build(_cfg())
    rows = [_row(f"T{i}.NS", 60 + i) for i in range(12)]      # scores 60..71
    store = _store()
    scan_and_store(strat, store, scanner=_StubScanner(rows))

    top5 = store.get_scan("small_cap_dryrun", limit=5)
    top10 = store.get_scan("small_cap_dryrun", limit=10)
    assert len(top5) == 5 and len(top10) == 10
    assert top5[0]["ticker"] == "T11.NS"        # highest score first
    assert top5[-1]["ticker"] == "T7.NS"


def test_empty_scan_persists_nothing_and_returns_empty():
    strat = build(_cfg())
    store = _store()
    assert scan_and_store(strat, store, scanner=_StubScanner([])) == []
    assert store.get_scan("small_cap_dryrun") == []
