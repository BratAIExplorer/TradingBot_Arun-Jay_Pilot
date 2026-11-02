"""Spike shadow test: pure logic only (no Gateway). Rules: Documentation/SPIKE_TEST_RULES.md"""
from research.spike_logger import crossed_levels, heartbeat_due, is_realtime, in_session
from research.spike_scorer import simulate_trade, summarize, verdict
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def tick(bid, ask=None, halted=False):
    return {"bid": bid, "ask": ask if ask is not None else bid * 1.01, "halted": halted}


# ---- logger ---------------------------------------------------------------
def test_crossed_levels_only_new_crossings():
    assert crossed_levels(10, 35, (30, 50, 100)) == [30]
    assert crossed_levels(35, 120, (30, 50, 100)) == [50, 100]
    assert crossed_levels(120, 130, (30, 50, 100)) == []
    assert crossed_levels(None, 40, (30, 50, 100)) == [30]


def test_data_gate_only_live_type_one_with_a_real_price_passes():
    assert is_realtime(1, 759.47)
    for delayed in (2, 3, 4, None):
        assert not is_realtime(delayed, 759.47)


def test_data_gate_rejects_default_type_one_without_a_price():
    # ib_insync's Ticker defaults to marketDataType 1; a failed subscription (IBKR error 10089) leaves last = nan
    assert not is_realtime(1, float("nan"))
    assert not is_realtime(1, None)
    assert not is_realtime(1, -1)
    assert not is_realtime(1, 0)


def test_heartbeat_due_every_ten_minutes():
    assert heartbeat_due(None, 1000.0)
    assert not heartbeat_due(1000.0, 1000.0 + 599)
    assert heartbeat_due(1000.0, 1000.0 + 600)


def test_session_window_uses_eastern_time():
    assert in_session(datetime(2026, 11, 2, 4, 0, tzinfo=ET))
    assert in_session(datetime(2026, 11, 2, 15, 54, tzinfo=ET))
    assert not in_session(datetime(2026, 11, 2, 15, 55, tzinfo=ET))
    assert not in_session(datetime(2026, 11, 2, 3, 59, tzinfo=ET))
    assert not in_session(datetime(2026, 11, 1, 10, 0, tzinfo=ET))  # Sunday


# ---- simulate_trade -------------------------------------------------------
def test_forced_exit_at_last_tick_net_of_slippage_and_commission():
    # buy ask 10 +2% = 10.2 ; last bid 12 -2% = 11.76 ; gross +15.29% ; commission 2/500 = 0.4%
    t = simulate_trade(10.0, [tick(11), tick(12)], slippage=0.02, stop_pct=0.10, commission_usd=1.0, notional=500)
    assert t["exit"] == "forced"
    assert abs(t["net_pct"] - (11.76 / 10.2 - 1) * 100 + 0.4) < 1e-6


def test_stop_triggers_and_gap_through_uses_actual_bid():
    # fill 10.2, stop 9.18. bid gaps to 7.0 -> exit at 7.0 (not at the stop)
    t = simulate_trade(10.0, [tick(9.9), tick(7.0), tick(20)], slippage=0.02, stop_pct=0.10, commission_usd=0, notional=500)
    assert t["exit"] == "stop"
    assert t["gap_through"] is True
    assert t["net_pct"] < -30


def test_stop_without_gap_is_not_flagged():
    t = simulate_trade(10.0, [tick(8.95)], slippage=0.0, stop_pct=0.10, commission_usd=0, notional=500)
    assert t["exit"] == "stop" and t["gap_through"] is False


def test_halt_while_in_position_is_flagged_and_cannot_exit_on_halted_tick():
    # stop level breached only on a halted tick -> cannot sell; reopens higher -> no stop, forced exit
    t = simulate_trade(10.0, [tick(5.0, halted=True), tick(11.0)], slippage=0.0, stop_pct=0.10, commission_usd=0, notional=500)
    assert t["halt_trapped"] is True
    assert t["exit"] == "forced"


def test_no_ticks_means_no_trade():
    assert simulate_trade(10.0, [], slippage=0.02, stop_pct=0.10, commission_usd=0, notional=500) is None


# ---- summarize / verdict --------------------------------------------------
def mk(net, day="2026-11-02", sym="A", halt=False):
    return {"net_pct": net, "day": day, "symbol": sym, "halt_trapped": halt}


def test_summarize_median_top2_removal_and_stock_days():
    trades = [mk(50, sym="A"), mk(40, sym="B"), mk(1, sym="C"), mk(2, sym="D"), mk(-3, sym="E")]
    s = summarize(trades)
    assert s["n"] == 5 and s["median"] == 2 and s["median_ex_top2"] == 1
    assert s["stock_days"] == 5 and s["days"] == 1 and s["halt_share"] == 0


def test_stock_days_dedupes_repeat_flags_of_same_stock():
    s = summarize([mk(5, sym="A"), mk(6, sym="A"), mk(7, sym="A")])
    assert s["stock_days"] == 1


def test_verdict_no_conclusion_when_sample_small():
    assert verdict(summarize([mk(5)] * 3), summarize([mk(5)] * 3)) == "no conclusion"


def test_verdict_continue_vs_retire():
    good = summarize([mk(1 + i % 3, day=f"d{i % 12}", sym=f"S{i}") for i in range(120)])
    bad = summarize([mk(-2 - i % 3, day=f"d{i % 12}", sym=f"S{i}") for i in range(120)])
    assert verdict(good, good) == "continue paper"
    assert verdict(good, bad) == "retire or re-tune within budget"
