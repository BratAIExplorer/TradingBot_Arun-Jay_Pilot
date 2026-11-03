"""
TDD tests for the fundamentals gate (strategies/framework/fundamentals.py).

The curated CSV is the source of truth; yfinance auto-fills; a still-blank
required field means the name fails the gate ("can't verify -> don't trade").

Run:  python -m pytest strategies/tests/test_fundamentals.py -q
"""
from strategies.framework.config import FundamentalsConfig
from strategies.framework.fundamentals import (
    FundamentalsRow, passes_gate, build_csv, load_csv,
)


def _row(**over):
    base = dict(ticker="AAA.NS", roe_pct=18.0, debt_equity=0.4, positive_earnings=True,
                market_cap_cr=1200.0, avg_daily_value_cr=3.0, source="stub", as_of="2026-09-09")
    base.update(over)
    return FundamentalsRow(**base)


_GATE = FundamentalsConfig()          # enabled, min_roe 10, max_de 1.0, positive earnings


def test_passes_gate_accepts_a_healthy_row():
    ok, why = passes_gate(_row(), _GATE, 500.0, 5000.0)
    assert ok is True
    assert why == "passes"


def test_passes_gate_rejects_low_roe():
    ok, why = passes_gate(_row(roe_pct=6.0), _GATE, 500.0, 5000.0)
    assert ok is False
    assert "roe" in why.lower()


def test_passes_gate_rejects_high_debt_equity():
    ok, why = passes_gate(_row(debt_equity=1.8), _GATE, 500.0, 5000.0)
    assert ok is False
    assert "d/e" in why.lower() or "debt" in why.lower()


def test_passes_gate_rejects_negative_earnings():
    ok, why = passes_gate(_row(positive_earnings=False), _GATE, 500.0, 5000.0)
    assert ok is False
    assert "earnings" in why.lower()


def test_passes_gate_rejects_a_missing_required_field_as_unverified():
    ok, why = passes_gate(_row(roe_pct=None), _GATE, 500.0, 5000.0)
    assert ok is False
    assert "unknown" in why.lower() or "verif" in why.lower()


def test_passes_gate_rejects_market_cap_outside_band():
    ok, why = passes_gate(_row(market_cap_cr=200.0), _GATE, 500.0, 5000.0)
    assert ok is False
    assert "cap" in why.lower()


def test_gate_off_passes_everything_even_a_blank_row():
    off = FundamentalsConfig(enabled=False)
    ok, why = passes_gate(None, off, 500.0, 5000.0)
    assert ok is True


def test_missing_row_fails_when_gate_on():
    ok, why = passes_gate(None, _GATE, 500.0, 5000.0)
    assert ok is False


def test_build_and_load_csv_roundtrip(tmp_path):
    def fake_fetch(ticker):
        return {"roe_pct": 15.0, "debt_equity": 0.5, "positive_earnings": True,
                "market_cap_cr": 900.0, "avg_daily_value_cr": 2.0}

    path = str(tmp_path / "fund.csv")
    n = build_csv(["AAA.NS", "BBB.NS"], path, fetch=fake_fetch, sleep=0)
    assert n == 2

    rows = load_csv(path)
    assert set(rows) == {"AAA.NS", "BBB.NS"}
    assert rows["AAA.NS"].roe_pct == 15.0
    assert rows["AAA.NS"].positive_earnings is True
    assert rows["AAA.NS"].source == "yfinance"


def test_build_csv_writes_blanks_when_fetch_returns_nothing(tmp_path):
    path = str(tmp_path / "fund.csv")
    build_csv(["AAA.NS"], path, fetch=lambda t: {}, sleep=0)
    row = load_csv(path)["AAA.NS"]
    assert row.roe_pct is None
    assert row.market_cap_cr is None
    # a blank row must fail the gate
    ok, _ = passes_gate(row, _GATE, 500.0, 5000.0)
    assert ok is False
