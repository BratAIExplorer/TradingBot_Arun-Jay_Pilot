"""
TDD tests for the framework-owned MACD bullish-crossover detector
(strategies.small_cap_dryrun.fresh_macd_cross).

Replaces scanner_engine.detect_macd_crossover, which calls `.tail()` on a
DatetimeIndex (no such method), swallows the AttributeError in a bare `except`,
and therefore always reports "no crossover".

Run:  python -m pytest strategies/tests/test_macd_cross.py -q
"""
import pandas as pd

from strategies.small_cap_dryrun import fresh_macd_cross


def _df(closes):
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=len(closes))
    return pd.DataFrame({"Close": [float(c) for c in closes]}, index=idx)


def test_bullish_cross_is_detected_with_a_date():
    fresh, date = fresh_macd_cross(_df([100] * 30 + [100 + 3 * i for i in range(1, 20)]))
    assert fresh is True
    assert date is not None


def test_bearish_only_cross_is_ignored():
    # a long rise (one early bullish cross) then a long fall; the 10-bar window
    # sees only the fall, where MACD stays below signal -> nothing fresh
    closes = [100 + 3 * i for i in range(25)] + [172 - 3 * i for i in range(25)]
    fresh, date = fresh_macd_cross(_df(closes), within_bars=10)
    assert fresh is False
    assert date is None


def test_multi_cross_returns_the_latest():
    closes = (
        [100] * 20
        + [100 + 5 * i for i in range(1, 6)]      # cross #1
        + [120, 110, 104, 100, 98]               # bearish dip
        + [104 + 6 * i for i in range(1, 9)]      # cross #2
    )
    df = _df(closes)
    fresh, date = fresh_macd_cross(df)
    assert fresh is True
    assert pd.Timestamp(date) >= df.index[-9]     # date belongs to the second rally


def test_cross_outside_the_window_is_not_fresh():
    closes = [100] * 15 + [100 + 4 * i for i in range(1, 10)] + [136] * 30
    fresh, date = fresh_macd_cross(_df(closes), within_bars=10)
    assert fresh is False
    assert date is None
