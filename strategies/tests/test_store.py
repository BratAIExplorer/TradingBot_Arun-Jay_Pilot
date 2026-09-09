"""
TDD tests for the framework store (database/strategies.db).

Every row is strategy-tagged; queries never leak between strategies. This DB is
separate from trades.db and is never read by the live RSI bot.

Run:  python -m pytest strategies/tests/test_store.py -q
"""
import pytest

from strategies.framework.store import Store


@pytest.fixture()
def store(tmp_path):
    return Store(str(tmp_path / "strategies.db"))


# --- scan_results ---------------------------------------------------------- #
def test_save_and_get_scan_ranks_by_score(store):
    cands = [
        {"ticker": "AAA.NS", "exchange": "NSE", "price": 100, "score": 65,
         "signal": "BUY", "reason": "macd", "extra": {"rsi": 55}},
        {"ticker": "BBB.NS", "exchange": "NSE", "price": 200, "score": 82,
         "signal": "STRONG BUY", "reason": "macd+trend", "extra": {}},
    ]
    n = store.save_scan("small_cap_dryrun", cands, scan_date="2026-09-08")
    assert n == 2
    rows = store.get_scan("small_cap_dryrun", scan_date="2026-09-08")
    assert [r["ticker"] for r in rows] == ["BBB.NS", "AAA.NS"]
    assert rows[0]["rank"] == 1
    assert rows[0]["score"] == 82


def test_latest_scan_date(store):
    store.save_scan("s", [{"ticker": "X", "exchange": "NSE", "price": 1, "score": 1,
                           "signal": "BUY", "reason": "r"}], scan_date="2026-09-01")
    store.save_scan("s", [{"ticker": "X", "exchange": "NSE", "price": 1, "score": 1,
                           "signal": "BUY", "reason": "r"}], scan_date="2026-09-08")
    assert store.latest_scan_date("s") == "2026-09-08"
    assert store.get_scan("s") == store.get_scan("s", scan_date="2026-09-08")


# --- fills --------------------------------------------------------------- #
def test_record_and_get_fills(store):
    fid = store.record_fill("s", "AAA.NS", "NSE", "BUY", 10, 100.0, "entry", orders_enabled=False)
    assert fid > 0
    fills = store.get_fills("s")
    assert len(fills) == 1
    assert fills[0]["side"] == "BUY"
    assert fills[0]["orders_enabled"] == 0        # logged, not real


# --- positions --------------------------------------------------------- #
def test_upsert_insert_then_update_then_close(store):
    store.upsert_position("s", "AAA.NS", "NSE", qty=10, avg_entry=100.0, tranches=1,
                          entry_cross_date="01-Sep-2026", opened_at="2026-09-08T10:00:00")
    pos = store.get_position("s", "AAA.NS")
    assert pos["qty"] == 10 and pos["tranches"] == 1 and pos["status"] == "OPEN"

    store.upsert_position("s", "AAA.NS", "NSE", qty=20, avg_entry=105.0, tranches=2,
                          entry_cross_date="01-Sep-2026", opened_at="2026-09-08T10:00:00")
    pos = store.get_position("s", "AAA.NS")
    assert pos["qty"] == 20 and pos["tranches"] == 2
    assert len(store.open_positions("s")) == 1

    store.close_position("s", "AAA.NS", closed_at="2026-09-12T15:00:00")
    assert store.open_positions("s") == []
    assert store.get_position("s", "AAA.NS")["status"] == "CLOSED"


# --- daily snapshot --------------------------------------------------- #
def test_save_and_get_snapshots(store):
    store.save_snapshot("s", "2026-09-08", account_value=1_000_000, deployed=15000,
                        free=5000, n_red=1, n_green=2, n_blocked=0)
    snaps = store.get_snapshots("s")
    assert len(snaps) == 1
    assert snaps[0]["deployed"] == 15000 and snaps[0]["n_green"] == 2


# --- isolation ------------------------------------------------------- #
def test_strategies_do_not_leak_into_each_other(store):
    store.save_scan("alpha", [{"ticker": "A", "exchange": "NSE", "price": 1, "score": 9,
                               "signal": "BUY", "reason": "r"}], scan_date="2026-09-08")
    store.save_scan("beta", [{"ticker": "B", "exchange": "NSE", "price": 1, "score": 9,
                              "signal": "BUY", "reason": "r"}], scan_date="2026-09-08")
    store.record_fill("alpha", "A", "NSE", "BUY", 1, 1.0, "e", orders_enabled=False)
    store.upsert_position("beta", "B", "NSE", 1, 1.0, 1, "x", "2026-09-08T00:00:00")

    assert [r["ticker"] for r in store.get_scan("alpha")] == ["A"]
    assert [r["ticker"] for r in store.get_scan("beta")] == ["B"]
    assert store.get_fills("beta") == []
    assert store.open_positions("alpha") == []


# --- new schema: fill cost columns -------------------------------------- #
def test_record_fill_stores_cost_columns_and_defaults_order_value(store):
    fid = store.record_fill("s", "AAA.NS", "NSE", "BUY", 10, 100.0, "entry",
                            orders_enabled=False)
    row = store.get_fills("s")[0]
    assert row["order_value"] == 1000.0          # defaulted from qty*price
    assert row["realised_pnl"] is None

    store.record_fill("s", "AAA.NS", "NSE", "SELL", 5, 120.0, "scale-out",
                      orders_enabled=True, qty_after=5, realised_pnl=95.0, fee_estimate=5.0)
    sell = store.get_fills("s")[1]
    assert sell["qty_after"] == 5
    assert sell["realised_pnl"] == 95.0
    assert sell["fee_estimate"] == 5.0
    assert fid > 0


# --- new schema: position metric columns ------------------------------- #
def test_update_position_metrics_roundtrips_every_field(store):
    store.upsert_position("s", "AAA.NS", "NSE", qty=10, avg_entry=100.0, tranches=1,
                          entry_cross_date="01-Sep-2026", opened_at="2026-09-08T10:00:00")
    store.update_position_metrics(
        "s", "AAA.NS",
        high_water_mark=140.0, trailing_floor=137.2, profit_pct=12.0,
        mae_pct=-4.5, exit_drawdown_pct=-2.0,
        days_held=6, days_red=2, days_green=4, stranded=True,
    )
    pos = store.get_position("s", "AAA.NS")
    assert pos["high_water_mark"] == 140.0
    assert pos["trailing_floor"] == 137.2
    assert pos["profit_pct"] == 12.0
    assert pos["mae_pct"] == -4.5
    assert pos["exit_drawdown_pct"] == -2.0
    assert pos["days_held"] == 6 and pos["days_red"] == 2 and pos["days_green"] == 4
    assert pos["stranded"] == 1


def test_update_position_metrics_ignores_unknown_keys(store):
    store.upsert_position("s", "AAA.NS", "NSE", 10, 100.0, 1, "x", "2026-09-08T00:00:00")
    store.update_position_metrics("s", "AAA.NS", qty=999, nonsense=1, high_water_mark=110.0)
    pos = store.get_position("s", "AAA.NS")
    assert pos["qty"] == 10                       # not a metric col -> untouched
    assert pos["high_water_mark"] == 110.0


def test_position_defaults_are_zero_not_null(store):
    store.upsert_position("s", "AAA.NS", "NSE", 10, 100.0, 1, "x", "2026-09-08T00:00:00")
    pos = store.get_position("s", "AAA.NS")
    assert pos["days_held"] == 0 and pos["stranded"] == 0
    assert pos["high_water_mark"] is None


# --- new schema: position_ohlc --------------------------------------- #
def test_record_and_get_position_ohlc_upserts_by_date(store):
    store.record_ohlc("s", "AAA.NS", "2026-09-08", 100, 105, 99, 104)
    store.record_ohlc("s", "AAA.NS", "2026-09-09", 104, 108, 103, 107)
    store.record_ohlc("s", "AAA.NS", "2026-09-09", 104, 111, 103, 110)   # same date -> overwrite
    rows = store.get_ohlc("s", "AAA.NS")
    assert [r["ohlc_date"] for r in rows] == ["2026-09-08", "2026-09-09"]
    assert rows[1]["high"] == 111
    assert store.get_ohlc("s", "BBB.NS") == []
