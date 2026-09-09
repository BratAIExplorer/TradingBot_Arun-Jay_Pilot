"""
Tests for the keyword-only screens on SmallCapDryRun.decide():
  - liquidity gate         (avg_daily_value_cr)
  - fundamentals gate      (fundamentals row -> passes_gate)
  - re-entry cooldown      (last_exit_cross_date)
  - frozen lower circuit   (manage path: never emit a sell on a locked day)
  - strand_final_half=False (the "one real leak" — final half sells anyway)

Run:  python -m pytest strategies/tests/test_screens.py -q
"""
import pandas as pd

from strategies.framework.config import (
    StrategyConfig, BudgetConfig, RulesConfig, ExitConfig, EntryConfig,
    LiquidityConfig, FundamentalsConfig, CostsConfig,
)
from strategies.framework.fundamentals import FundamentalsRow
from strategies.framework.base import Position
from strategies.small_cap_dryrun import SmallCapDryRun


def _cfg(**over):
    base = dict(
        name="small_cap_dryrun", enabled=True,
        budget=BudgetConfig(5000, 25000, 5, 2.0, 5),
        rules=RulesConfig(), exit=ExitConfig(), entry=EntryConfig(),
        liquidity=LiquidityConfig(), fundamentals=FundamentalsConfig(), costs=CostsConfig(),
        replay_stop_levels_pct=[5, 8, 10], universe="starter",
    )
    base.update(over)
    return StrategyConfig(**base)


def _idx(n):
    return pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)


def _uptrend_with_fresh_cross():
    closes = [100.0] * 50 + [130.0]
    return pd.DataFrame({"Close": closes,
                         "High": [c * 1.01 for c in closes],
                         "Low": [c * 0.99 for c in closes]}, index=_idx(len(closes)))


def _pos(entry=100.0, hwm=120.0, tranches_left=1, half2=101.0):
    return Position(ticker="X.NS", exchange="NSE", qty=10, avg_entry=entry, tranches=1,
                    entry_cross_date="01-Jan-2020", opened_at="2026-09-01T10:00:00",
                    high_water_mark=hwm, exit_tranches_remaining=tranches_left,
                    locked_half2_price=half2)


# --- liquidity gate --------------------------------------------------- #
def test_thin_stock_is_skipped_when_value_supplied():
    act = SmallCapDryRun(_cfg()).decide("X.NS", _uptrend_with_fresh_cross(), None,
                                        avg_daily_value_cr=0.2)
    assert act.kind == "HOLD" and "liquidity" in act.reason.lower()


def test_liquid_stock_still_buys():
    act = SmallCapDryRun(_cfg()).decide("X.NS", _uptrend_with_fresh_cross(), None,
                                        avg_daily_value_cr=5.0)
    assert act.kind == "BUY"


def test_no_value_supplied_means_gate_not_enforced_here():
    act = SmallCapDryRun(_cfg()).decide("X.NS", _uptrend_with_fresh_cross(), None)
    assert act.kind == "BUY"


# --- fundamentals gate ---------------------------------------------- #
def _row(**o):
    base = dict(ticker="X.NS", roe_pct=18.0, debt_equity=0.3, positive_earnings=True,
                market_cap_cr=2000.0, avg_daily_value_cr=5.0, source="test", as_of="2026-09-09")
    base.update(o)
    return FundamentalsRow(**base)


def test_weak_fundamentals_block_the_buy():
    act = SmallCapDryRun(_cfg()).decide("X.NS", _uptrend_with_fresh_cross(), None,
                                        fundamentals=_row(roe_pct=3.0))
    assert act.kind == "HOLD" and "health check" in act.reason.lower()


def test_good_fundamentals_pass():
    act = SmallCapDryRun(_cfg()).decide("X.NS", _uptrend_with_fresh_cross(), None,
                                        fundamentals=_row())
    assert act.kind == "BUY"


# --- re-entry cooldown -------------------------------------------- #
def test_reentry_blocked_until_a_newer_cross():
    df = _uptrend_with_fresh_cross()
    future = (pd.Timestamp.today().normalize() + pd.Timedelta(days=10)).strftime("%d-%b-%Y")
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, None, last_exit_cross_date=future)
    assert act.kind == "HOLD" and "fresh signal" in act.reason.lower()


def test_reentry_allowed_when_cross_is_newer_than_last_exit():
    df = _uptrend_with_fresh_cross()
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, None, last_exit_cross_date="01-Jan-2000")
    assert act.kind == "BUY"


# --- frozen lower circuit (manage path) --------------------------- #
def test_no_sell_when_the_stock_is_locked_lower_circuit():
    # prev close 100, today locked at ~90 (10% band), no range -> frozen
    closes = [100.0, 90.0]
    df = pd.DataFrame({"Close": closes, "High": [101.0, 90.0], "Low": [99.0, 90.0]}, index=_idx(2))
    # position whose rope would otherwise fire a sell
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, _pos(entry=80.0, hwm=120.0, tranches_left=2))
    assert act.kind == "HOLD" and "frozen" in act.reason.lower()


# --- the "one real leak": stranded final half ------------------- #
def test_final_half_strands_by_default():
    df = pd.DataFrame({"Close": [100.0], "High": [101.0], "Low": [99.0]}, index=_idx(1))
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, _pos(entry=100.0, half2=101.0))
    assert act.kind == "HOLD" and "strand" in act.reason.lower()


def test_final_half_sells_anyway_when_strand_final_half_is_false():
    df = pd.DataFrame({"Close": [100.0], "High": [101.0], "Low": [99.0]}, index=_idx(1))
    cfg = _cfg(exit=ExitConfig(strand_final_half=False))
    act = SmallCapDryRun(cfg).decide("X.NS", df, _pos(entry=100.0, half2=101.0))
    assert act.kind == "SCALE_OUT" and act.fraction == 1.0
