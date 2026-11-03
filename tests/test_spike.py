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


# ---- 2026-11-02 pre-Day-1 amendment: never drop a trade, report more, size columns ----
import csv

from research import spike_logger
from research.spike_scorer import score_file


def test_all_halted_after_entry_is_unresolved_not_dropped():
    t = simulate_trade(10.0, [tick(9, halted=True), tick(9, halted=True)], slippage=0.0, commission_usd=0, notional=500)
    assert t is not None and t["unresolved"] is True and t["halt_trapped"] is True and t["net_pct"] is None


def test_still_halted_at_the_end_is_unresolved_with_best_case_recorded():
    t = simulate_trade(10.0, [tick(11), tick(11, halted=True)], slippage=0.0, commission_usd=0, notional=500)
    assert t["unresolved"] is True and t["exit"] == "unresolved"
    assert abs(t["best_case_pct"] - 10.0) < 1e-6          # what the old code would have reported


def test_no_bid_at_the_end_is_unresolved_too():
    t = simulate_trade(10.0, [tick(11), {"bid": None, "ask": None, "halted": False}], slippage=0.0, commission_usd=0, notional=500)
    assert t["unresolved"] is True


def test_halt_that_reopens_lower_exits_at_the_reopen_bid():
    t = simulate_trade(10.0, [tick(9.5, halted=True), tick(5.0)], slippage=0.0, commission_usd=0, notional=500)
    assert t["exit"] == "stop" and t["net_pct"] == -50.0 and t["halt_trapped"] is True and not t.get("unresolved")


def test_trailing_stop_locks_in_gains_the_fixed_stop_gives_back():
    path = [tick(10), tick(14), tick(11.5), tick(9.0)]            # peak 14 -> trail 15% = 11.9
    fixed = simulate_trade(10.0, path, slippage=0.0, commission_usd=0, notional=500)
    trail = simulate_trade(10.0, path, slippage=0.0, commission_usd=0, notional=500, trail_pct=0.15)
    assert fixed["exit"] == "stop" and abs(fixed["net_pct"] + 10.0) < 1e-9
    assert trail["exit"] == "trail" and abs(trail["net_pct"] - 15.0) < 1e-6


def test_summary_reports_unresolved_and_conservative_view():
    trades = [mk(5, sym="A"), mk(3, sym="B"), {**mk(None, sym="C", halt=True), "unresolved": True}]
    s = summarize(trades)
    assert s["n"] == 3 and s["n_realized"] == 2 and s["n_unresolved"] == 1
    assert s["median"] == 4 and s["halt_share"] == 1 / 3
    assert s["median_cons"] == 3                                  # [-50, 3, 5]
    assert s["stock_days"] == 3                                   # unresolved trades still count as evidence


def test_summary_extra_metrics():
    s = summarize([mk(10, sym="A"), mk(-5, sym="B"), mk(-5, sym="C"), mk(20, sym="D")])
    assert s["mean"] == 5 and s["profit_factor"] == 3.0
    assert abs(s["total_pnl_usd"] - 500 * 0.20) < 1e-9
    assert s["worst5"] == -5


def test_verdict_fails_when_only_the_conservative_view_is_negative():
    good = summarize([mk(2, day=f"d{i % 12}", sym=f"S{i}") for i in range(120)])
    hidden = summarize([mk(2, day=f"d{i % 12}", sym=f"S{i}") for i in range(60)] +
                       [{**mk(None, day=f"d{i % 12}", sym=f"U{i}", halt=True), "unresolved": True} for i in range(60)])
    assert hidden["median"] > 0 and hidden["median_cons"] < 0
    assert verdict(good, hidden) == "retire or re-tune within budget"


def _write_log(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=spike_logger.FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in spike_logger.FIELDS})


def test_score_file_counts_skipped_unresolved_and_sessions(tmp_path):
    p = str(tmp_path / "log.csv")
    ev = lambda ts, sym, ask: {"ts_et": ts, "kind": "event", "symbol": sym, "level": "30", "ask": ask, "bid": 1}
    tk = lambda ts, sym, bid, h=0: {"ts_et": ts, "kind": "tick", "symbol": sym, "bid": bid, "halted": h}
    _write_log(p, [
        ev("2026-11-03T05:00:00", "PRE", 10), tk("2026-11-03T05:00:05", "PRE", 11), tk("2026-11-03T05:00:10", "PRE", 12),
        ev("2026-11-03T10:00:00", "REG", 10), tk("2026-11-03T10:00:05", "REG", 9, 1),      # halted to the end
        ev("2026-11-03T11:00:00", "NOASK", ""),                                              # no ask -> skipped
        ev("2026-11-03T12:00:00", "LOST", 10),                                               # logger gap: no ticks
    ])
    trades, skipped = score_file(p, 0.0, "30")
    by = {t["symbol"]: t for t in trades}
    assert skipped == 1 and set(by) == {"PRE", "REG", "LOST"}
    assert by["PRE"]["session"] == "premarket" and by["REG"]["session"] == "regular"
    assert by["REG"]["unresolved"] and by["LOST"]["unresolved"] and not by["PRE"].get("unresolved")


# ---- logger: size columns and header safety ----
def test_fields_include_sizes_and_keep_old_columns_in_order():
    assert spike_logger.FIELDS[:12] == ["ts_et", "kind", "symbol", "level", "pct", "last", "bid", "ask", "volume", "halted", "mdtype", "note"]
    assert spike_logger.FIELDS[12:] == ["bid_size", "ask_size"]


def test_write_row_writes_sizes(tmp_path):
    p = str(tmp_path / "log.csv")
    spike_logger.write_row("tick", symbol="X", bid=1.0, ask=1.1, bid_size=300, ask_size=0, path=p)
    row = next(csv.DictReader(open(p, newline="", encoding="utf-8")))
    assert row["bid_size"] == "300" and row["ask_size"] == "0"


def test_old_header_file_is_rotated_not_corrupted(tmp_path):
    p = tmp_path / "log.csv"
    p.write_text("ts_et,kind,symbol\n2026-11-02T10:00:00,tick,OLD\n", encoding="utf-8")
    spike_logger.write_row("tick", symbol="NEW", bid_size=5, path=str(p))
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    assert [r["symbol"] for r in rows] == ["NEW"]
    assert any(f.name.startswith("log.csv.pre-") for f in tmp_path.iterdir())     # old data kept
