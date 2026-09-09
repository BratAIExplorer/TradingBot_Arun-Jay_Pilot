"""
TDD tests for the pure signal-rule functions of the small-cap dry-run strategy.

Every function here is offline: it takes a price frame/series and returns a bool
or a small tuple. No network, no DB, no broker.

Run:  python -m pytest strategies/tests/test_rules.py -q
"""
import numpy as np
import pandas as pd
import pytest

from strategies.small_cap_dryrun import (
    rsi_series,
    above_ma,
    bearish_rsi_divergence,
    swing_break_exit,
)


# --------------------------------------------------------------------------- #
# helpers to build synthetic candle data
# --------------------------------------------------------------------------- #
def _series(values):
    return pd.Series([float(v) for v in values])


def _frame(closes, highs=None, lows=None):
    closes = [float(c) for c in closes]
    highs = highs or [c * 1.01 for c in closes]
    lows = lows or [c * 0.99 for c in closes]
    return pd.DataFrame({"Close": closes, "High": highs, "Low": lows})


# --------------------------------------------------------------------------- #
# rsi_series
# --------------------------------------------------------------------------- #
def test_rsi_series_is_high_for_pure_uptrend():
    s = _series(range(1, 40))               # strictly rising
    rsi = rsi_series(s, period=14)
    assert rsi.iloc[-1] > 95               # all gains, no losses


def test_rsi_series_is_low_for_pure_downtrend():
    s = _series(range(40, 1, -1))           # strictly falling
    rsi = rsi_series(s, period=14)
    assert rsi.iloc[-1] < 5


def test_rsi_series_matches_scanner_engine_last_value():
    # our series' last value must equal scanner_engine.get_rsi (same definition)
    from scanner_engine import MACDScanner
    s = _series([100, 102, 101, 105, 107, 106, 110, 109, 112, 115,
                 114, 118, 120, 119, 122, 125, 121, 124, 128, 130])
    ours = round(rsi_series(s, period=14).iloc[-1], 2)
    theirs = MACDScanner().get_rsi(s, period=14)
    assert ours == theirs


# --------------------------------------------------------------------------- #
# above_ma
# --------------------------------------------------------------------------- #
def test_above_ma_true_when_last_close_over_average():
    s = _series([10] * 49 + [20])
    assert above_ma(s, period=50) is True


def test_above_ma_false_when_last_close_under_average():
    s = _series([20] * 49 + [10])
    assert above_ma(s, period=50) is False


def test_above_ma_false_when_not_enough_bars():
    s = _series([10] * 10)
    assert above_ma(s, period=50) is False   # cannot confirm -> False


# --------------------------------------------------------------------------- #
# bearish_rsi_divergence
#   True  = today is a new `lookback`-bar closing high, but today's RSI is
#           below the best RSI of the prior `lookback-1` bars.
# --------------------------------------------------------------------------- #
def test_divergence_true_price_new_high_rsi_lower_high():
    # strong early rally (RSI peaks), then a slow grind to a marginally new high
    closes = ([100, 104, 108, 113, 119, 126, 134, 143, 153, 164, 176, 189,
               203, 218, 234, 251]                      # steep -> RSI ~ very high
              + [250, 252, 251, 253, 252, 254, 253, 255, 254, 256])  # drift to new high, weak momentum
    s = _series(closes)
    assert bearish_rsi_divergence(s, lookback=10, rsi_period=14) is True


def test_divergence_false_when_rsi_also_makes_new_high():
    s = _series([100 + i * 2 for i in range(40)])   # steady strong uptrend
    assert bearish_rsi_divergence(s, lookback=10, rsi_period=14) is False


def test_divergence_false_when_today_not_a_new_high():
    closes = [100 + i for i in range(30)] + [110]   # last bar well below recent highs
    s = _series(closes)
    assert bearish_rsi_divergence(s, lookback=10, rsi_period=14) is False


def test_divergence_false_when_insufficient_data():
    s = _series([100, 101, 102, 103, 104])
    assert bearish_rsi_divergence(s, lookback=10, rsi_period=14) is False


# --------------------------------------------------------------------------- #
# swing_break_exit
#   True = last 2 closes are BOTH below the most recent 5-bar-fractal swing low
#          AND the last close is below the `ma_period` moving average.
# --------------------------------------------------------------------------- #
def _with_swing_low_then(tail_closes):
    """
    Build a frame with a clean 5-bar fractal swing low at value 90
    (bar low strictly lower than the 2 bars each side), an uptrend after it,
    then `tail_closes` appended as the recent action.
    """
    base_closes = [100, 98, 95, 92, 90, 93, 96, 99, 103, 108, 113, 118,
                   123, 128, 133, 138, 143, 148, 153, 158]
    base_lows = [c - 2 for c in base_closes]
    base_lows[4] = 88          # the swing low (bar index 4): 88 < neighbours
    closes = base_closes + list(tail_closes)
    lows = base_lows + [c - 2 for c in tail_closes]
    highs = [c + 2 for c in closes]
    return pd.DataFrame({"Close": closes, "High": highs, "Low": lows})


def test_swing_exit_true_two_closes_below_swing_low_and_below_ma():
    # swing low is 88; drop last two closes below 88 and below the MA
    df = _with_swing_low_then([80, 78])
    assert swing_break_exit(df, fractal_bars=5, ma_period=10) is True


def test_swing_exit_false_only_one_close_below_swing_low():
    df = _with_swing_low_then([120, 80])     # only the final close is below 88
    assert swing_break_exit(df, fractal_bars=5, ma_period=10) is False


def test_swing_exit_false_below_swing_low_but_above_ma():
    # both closes below 88 but engineer MA to sit under them: use tiny ma window
    # on a frame whose recent average is < 80 is hard; instead assert the AND:
    df = _with_swing_low_then([80, 78])
    # ma_period=2 -> MA ~= 79, last close 78 -> below MA still... use ma_period=1
    assert swing_break_exit(df, fractal_bars=5, ma_period=1) is False  # close==MA, not below


def test_swing_exit_false_when_no_swing_low_detected():
    df = _frame([100 + i for i in range(8)])   # monotonic, too short for a fractal
    assert swing_break_exit(df, fractal_bars=5, ma_period=10) is False
