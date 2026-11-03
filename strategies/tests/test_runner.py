"""
TDD for strategies/framework/runner.py — one log-only cycle.

scan -> persist -> for each name: decide (+ screens) -> plan_entry -> log-only
BUY -> fills/positions; for each holding: decide -> advance_rope -> log-only
SCALE_OUT. No orders, no network. trades.db is never touched (different DB).

Run:  python -m pytest strategies/tests/test_runner.py -q
"""
import os
import tempfile

import pandas as pd

from strategies.framework.config import CostsConfig
from strategies.framework.store import Store
from strategies.framework.broker import Broker
from strategies.framework.registry import load
from strategies.framework.runner import run_cycle

_CFG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "configs", "small_cap_dryrun.json")


def _strat():
    return load(_CFG_PATH)      # the shipped config: Rs 10k/name, Rs 100k cap -> 10 names


class _Scanner:
    def __init__(self, tickers):
        self._t = tickers

    def scan_market(self, mode="SMALLCAP"):
        return [{"ticker": t, "company": t, "price": 130.0, "signal": "BUY",
                 "confluence_score": 70, "macd_cross_date": "01-Sep-2026", "days_ago": 2,
                 "above_20ma": True, "above_50ma": True, "ma_20": 1.0, "ma_50": 1.0,
                 "rsi": 55} for t in self._t]


def _uptrend_fresh_cross():
    closes = [100.0] * 50 + [130.0]
    return pd.DataFrame({"Close": closes, "High": [c * 1.01 for c in closes],
                         "Low": [c * 0.99 for c in closes]},
                        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=51))


def _store():
    d = tempfile.mkdtemp()
    s = Store(os.path.join(d, "s.db"))
    s._create()
    return s, d


def _broker():
    return Broker(orders_enabled=False, costs=CostsConfig())


def test_a_full_cycle_buys_a_qualifying_name_log_only():
    strat = _strat()
    store, d = _store()
    status = os.path.join(d, "status.txt")

    summary = run_cycle(
        strat, store, _broker(),
        account_value=100_000,
        candle_provider=lambda t: _uptrend_fresh_cross(),
        universe_scanner=_Scanner(["AAA.NS"]),
        status_path=status,
    )

    assert summary["scanned"] == 1
    assert summary["bought"] == 1
    assert store.get_scan("small_cap_dryrun")                      # scan persisted
    pos = store.get_position("small_cap_dryrun", "AAA.NS")
    assert pos is not None and pos["qty"] >= 1
    fills = store.get_fills("small_cap_dryrun")
    assert fills and fills[0]["side"] == "BUY" and fills[0]["orders_enabled"] == 0
    assert os.path.exists(status)


def test_budget_cap_stops_the_eleventh_name():
    # config caps at Rs 100,000 / Rs 10,000 = 10 names; scanner offers 11
    strat = _strat()
    store, d = _store()
    offered = [f"{c}.NS" for c in "ABCDEFGHIJK"]   # 11 names
    summary = run_cycle(
        strat, store, _broker(),
        account_value=200_000,
        candle_provider=lambda t: _uptrend_fresh_cross(),
        universe_scanner=_Scanner(offered),
        status_path=os.path.join(d, "status.txt"),
    )
    assert summary["bought"] == 10
    assert len(store.open_positions("small_cap_dryrun")) == 10


def test_a_holding_that_hits_the_rope_scales_out():
    strat = _strat()
    store, d = _store()
    # open a position by hand: entry 100, high-water 120 already recorded
    store.upsert_position("small_cap_dryrun", "HELD.NS", "NSE", qty=10, avg_entry=100.0,
                          tranches=1, entry_cross_date="01-Aug-2026",
                          opened_at="2026-08-01T10:00:00")
    store.update_position_metrics("small_cap_dryrun", "HELD.NS",
                                  high_water_mark=120.0, exit_tranches_remaining=2)

    # today's close 117 <= rope (120*0.98=117.6) -> sell first half
    down = pd.DataFrame({"Close": [119.0, 117.0], "High": [120.0, 118.0], "Low": [118.0, 116.0]},
                        index=pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=2))
    summary = run_cycle(
        strat, store, _broker(),
        account_value=100_000,
        candle_provider=lambda t: down,
        universe_scanner=_Scanner([]),
        status_path=os.path.join(d, "status.txt"),
    )
    assert summary["sold"] == 1
    sell = [f for f in store.get_fills("small_cap_dryrun") if f["side"] == "SELL"]
    assert sell and sell[0]["qty"] == 5
