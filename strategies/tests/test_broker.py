"""
TDD for framework/broker.py — the Zerodha CNC broker, log-only until keys land.

No network in these tests. `orders_enabled=False` -> place_order returns a
simulated fill priced through the cost model; validate_session with no session
fails cleanly (never raises).

Run:  python -m pytest strategies/tests/test_broker.py -q
"""
from strategies.framework.config import CostsConfig
from strategies.framework.broker import Broker

REAL = CostsConfig(stt_pct=0.1, entry_slippage_bps=40, exit_slippage_bps_thin=300)
ZERO = CostsConfig()


def test_log_only_buy_returns_a_simulated_fill_no_network():
    b = Broker(orders_enabled=False, costs=REAL)
    f = b.place_order("CDSL.NS", "NSE", "BUY", qty=10, price=100.0)
    assert f["mode"] == "LOGGED" and f["orders_enabled"] is False
    assert f["fill_price"] > 100.0                      # slippage makes a buy worse
    assert f["fee_estimate"] > 0
    assert f["order_value"] == round(f["fill_price"] * 10, 2)


def test_log_only_sell_fills_below_the_quote():
    b = Broker(orders_enabled=False, costs=REAL)
    f = b.place_order("CDSL.NS", "NSE", "SELL", qty=10, price=100.0)
    assert f["fill_price"] < 100.0


def test_zero_cost_config_fills_at_the_quote():
    b = Broker(orders_enabled=False, costs=ZERO)
    f = b.place_order("X.NS", "NSE", "BUY", qty=5, price=200.0)
    assert f["fill_price"] == 200.0 and f["fee_estimate"] == 0


def test_validate_session_without_credentials_fails_cleanly():
    b = Broker(orders_enabled=False, costs=ZERO)
    ok, reason = b.validate_session()
    assert ok is False
    assert "credential" in reason.lower() or ".env" in reason.lower()


def test_orders_enabled_but_no_session_will_not_pretend_to_trade():
    b = Broker(orders_enabled=True, costs=ZERO)
    f = b.place_order("X.NS", "NSE", "BUY", qty=1, price=10.0)
    assert f["mode"] == "ERROR" and "session" in f["reason"].lower()
