"""
TDD tests for the SmallCapDryRun.decide() decision logic (pure, offline).

decide(ticker, candles, position):
  position is None  -> entry question  -> BUY / HOLD
  position is set   -> manage question -> SCALE_OUT (half or rest) / HOLD

Manage is the trailing 2% profit rope with a 2-tranche scale-out and a
+2% net-of-costs floor below which nothing sells (no stop-loss).

Run:  python -m pytest strategies/tests/test_strategy.py -q
"""
import pandas as pd

from strategies.framework.config import (
    StrategyConfig, BudgetConfig, RulesConfig, ExitConfig, EntryConfig,
)
from strategies.framework.base import Position
from strategies.small_cap_dryrun import SmallCapDryRun


def _cfg(entry=None, **exit_over):
    return StrategyConfig(
        name="small_cap_dryrun", enabled=True,
        budget=BudgetConfig(per_stock_amount=5000, total_budget=25000,
                            max_names_cap=5, pct_of_account_cap=2.0, max_names=5),
        rules=RulesConfig(ma_period=50, rsi_period=14, divergence_lookback=10, swing_fractal_bars=5),
        exit=ExitConfig(**exit_over),
        entry=entry or EntryConfig(),
        replay_stop_levels_pct=[5, 8, 10], universe="starter",
    )


def _dates(n):
    return pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)


def _frame(closes, highs=None, lows=None):
    closes = [float(c) for c in closes]
    idx = _dates(len(closes))
    return pd.DataFrame(
        {
            "Close": closes,
            "High": highs or [c * 1.01 for c in closes],
            "Low": lows or [c * 0.99 for c in closes],
        },
        index=idx,
    )


def _pos(entry=100.0, hwm=None, tranches_left=2, half2=None):
    return Position(ticker="X.NS", exchange="NSE", qty=10, avg_entry=entry,
                    tranches=1, entry_cross_date="01-Jan-2020", opened_at="2026-09-01T10:00:00",
                    high_water_mark=hwm, exit_tranches_remaining=tranches_left,
                    locked_half2_price=half2)


# --- entry ------------------------------------------------------------- #
def test_entry_buy_on_a_fresh_cross_this_bar_in_an_uptrend():
    # 50 flat bars then one sharp up bar -> MACD crosses on the last bar,
    # 200EMA trend satisfied. Default entry: cross must be within 1 trading day.
    df = _frame([100] * 50 + [130])
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, position=None)
    assert act.kind == "BUY"


def test_entry_hold_when_the_cross_is_older_than_the_max_age():
    # cross printed ~14 bars ago; default fresh_cross_max_age_days = 1 -> stale
    df = _frame([100] * 40 + [100 + 2 * i for i in range(1, 16)])
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, position=None)
    assert act.kind == "HOLD"


def test_entry_buy_when_max_age_is_widened_to_cover_an_older_cross():
    df = _frame([100] * 40 + [100 + 2 * i for i in range(1, 16)])
    cfg = _cfg(entry=EntryConfig(fresh_cross_max_age_days=30))
    act = SmallCapDryRun(cfg).decide("X.NS", df, position=None)
    assert act.kind == "BUY"


def test_entry_hold_when_downtrend_no_cross():
    df = _frame([130 - i for i in range(60)])                        # steady decline
    act = SmallCapDryRun(_cfg()).decide("X.NS", df, position=None)
    assert act.kind == "HOLD"


def test_entry_hold_when_50ema_still_below_200ema_despite_a_fresh_cross():
    # long decline then a short sharp pop: MACD can cross up, but 50EMA is still
    # under 200EMA -> the 200EMA trend filter blocks the entry
    df = _frame([200 - i for i in range(80)] + [121 + 5 * i for i in range(1, 9)])
    cfg = _cfg(entry=EntryConfig(fresh_cross_max_age_days=30))
    act = SmallCapDryRun(cfg).decide("X.NS", df, position=None)
    assert act.kind == "HOLD"


# --- manage: rope inactive (profit too thin) -------------------------- #
def test_manage_hold_when_rope_sits_below_the_net_floor():
    # entry 100 -> floor 102. hwm 103 -> rope = 103 * 0.98 = 100.94 < 102 -> hold
    act = SmallCapDryRun(_cfg()).decide("X.NS", _frame([103]), _pos(entry=100.0, hwm=103.0))
    assert act.kind == "HOLD"
    assert "rope" in act.reason.lower()


# --- manage: rope active ------------------------------------------- #
def test_manage_hold_when_price_is_above_the_rope():
    # hwm 120 -> rope 117.6; today's close 119 is above it -> hold
    act = SmallCapDryRun(_cfg()).decide("X.NS", _frame([119]), _pos(entry=100.0, hwm=120.0))
    assert act.kind == "HOLD"


def test_manage_scale_out_first_half_when_price_touches_the_rope():
    # hwm 120 -> rope 117.6 (>= floor 102); close 117 <= rope -> sell half
    act = SmallCapDryRun(_cfg()).decide("X.NS", _frame([117]), _pos(entry=100.0, hwm=120.0, tranches_left=2))
    assert act.kind == "SCALE_OUT"
    assert act.fraction == 0.5


def test_manage_scale_out_remaining_half_at_the_second_trigger():
    # first half gone; second trigger locked at 114.07; close 114 <= it -> sell the rest
    act = SmallCapDryRun(_cfg()).decide(
        "X.NS", _frame([114]), _pos(entry=100.0, hwm=120.0, tranches_left=1, half2=114.072),
    )
    assert act.kind == "SCALE_OUT"
    assert act.fraction == 1.0


def test_manage_holds_last_half_when_its_trigger_is_below_the_floor():
    # entry 100 -> floor 102; locked second trigger 101 < floor, never_sell_at_loss -> hold + flag
    act = SmallCapDryRun(_cfg()).decide(
        "X.NS", _frame([100]), _pos(entry=100.0, hwm=120.0, tranches_left=1, half2=101.0),
    )
    assert act.kind == "HOLD"
    assert "strand" in act.reason.lower()


# --- manage: hard stop (off by default, on when configured) ---------- #
def test_manage_hard_stop_is_off_by_default():
    # deep loss, but hard_stop_pct is None -> rope/floor logic holds, no sell
    act = SmallCapDryRun(_cfg()).decide("X.NS", _frame([70]), _pos(entry=100.0, hwm=100.0))
    assert act.kind == "HOLD"


def test_manage_hard_stop_sells_all_when_configured():
    act = SmallCapDryRun(_cfg(hard_stop_pct=8.0)).decide(
        "X.NS", _frame([91]), _pos(entry=100.0, hwm=100.0),
    )
    assert act.kind == "SCALE_OUT"
    assert act.fraction == 1.0
    assert "hard stop" in act.reason.lower()


# --- describe ------------------------------------------------- #
def test_describe_is_plain_english_and_mentions_no_stop_loss():
    text = SmallCapDryRun(_cfg()).describe()
    assert isinstance(text, str) and len(text) > 100
    assert "stop-loss" in text.lower() or "stop loss" in text.lower()
    assert "rope" in text.lower()
