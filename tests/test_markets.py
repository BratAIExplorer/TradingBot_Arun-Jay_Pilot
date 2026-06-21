"""
Test markets module - Phase 2 pure market metadata (hours, holidays, DST).

RED PHASE: Tests will fail until markets.py is implemented.
"""

import pytest
from datetime import datetime, date, time
from zoneinfo import ZoneInfo


class TestMarketSpec:
    """MarketSpec dataclass."""

    def test_market_spec_in_creation(self):
        """India market spec has correct hours."""
        from markets import MarketSpec, MARKETS

        spec = MARKETS["IN"]
        assert spec.code == "IN"
        assert spec.tz == "Asia/Kolkata"
        assert spec.open_t == time(9, 15)  # 9:15 AM
        assert spec.close_t == time(15, 30)  # 3:30 PM
        assert spec.currency == "INR"
        assert spec.default_exchange == "NSE"

    def test_market_spec_us_creation(self):
        """US market spec has correct hours."""
        from markets import MarketSpec, MARKETS

        spec = MARKETS["US"]
        assert spec.code == "US"
        assert spec.tz == "America/New_York"
        assert spec.open_t == time(9, 30)  # 9:30 AM ET
        assert spec.close_t == time(16, 0)  # 4:00 PM ET
        assert spec.currency == "USD"
        assert spec.default_exchange == "SMART"


class TestIsMarketOpen:
    """Market hours checking."""

    def test_india_market_open_during_trading_hours(self):
        """IN market is open at 12:00 PM IST on a trading day."""
        from markets import is_market_open

        # 2025-06-21 is a Saturday (NSE closed)
        # Use 2025-06-20 (Friday)
        trading_day = datetime(2025, 6, 20, 12, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        assert is_market_open("IN", trading_day) is True

    def test_india_market_closed_before_hours(self):
        """IN market closed before 9:15 AM."""
        from markets import is_market_open

        before_open = datetime(2025, 6, 20, 9, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        assert is_market_open("IN", before_open) is False

    def test_india_market_closed_after_hours(self):
        """IN market closed after 3:30 PM."""
        from markets import is_market_open

        after_close = datetime(2025, 6, 20, 16, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        assert is_market_open("IN", after_close) is False

    def test_india_market_closed_on_weekend(self):
        """IN market closed on Saturday."""
        from markets import is_market_open

        saturday = datetime(2025, 6, 21, 12, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        assert is_market_open("IN", saturday) is False

    def test_us_market_open_during_trading_hours(self):
        """US market open at 2:00 PM EST on trading day."""
        from markets import is_market_open

        trading_day = datetime(2025, 6, 20, 14, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", trading_day) is True

    def test_us_market_closed_before_hours(self):
        """US market closed before 9:30 AM ET."""
        from markets import is_market_open

        before_open = datetime(2025, 6, 20, 9, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", before_open) is False

    def test_us_market_closed_after_hours(self):
        """US market closed after 4:00 PM ET."""
        from markets import is_market_open

        after_close = datetime(2025, 6, 20, 17, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", after_close) is False

    def test_us_market_closed_on_weekend(self):
        """US market closed on Saturday."""
        from markets import is_market_open

        saturday = datetime(2025, 6, 21, 14, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", saturday) is False

    def test_market_open_without_timezone_uses_utc(self):
        """If no TZ provided, assumes UTC (bad but safe)."""
        from markets import is_market_open

        # This is a weak test — in real use, always provide TZ
        utc_noon = datetime(2025, 6, 20, 12, 0, 0)  # no tzinfo
        # Should not crash
        result = is_market_open("IN", utc_noon)
        assert isinstance(result, bool)


class TestNextOpen:
    """Next market open time calculation."""

    def test_next_open_during_trading_hours(self):
        """Next open from within trading hours is today's close + next day's open."""
        from markets import next_open

        during_trading = datetime(2025, 6, 20, 12, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        next_opening = next_open("IN", during_trading)

        # Next open is tomorrow (2025-06-21) at 9:15 AM IST
        assert next_opening.date() == date(2025, 6, 23)  # Skip to Monday (Sat closed)
        assert next_opening.time() == time(9, 15)

    def test_next_open_after_hours(self):
        """Next open after market close is tomorrow's open."""
        from markets import next_open

        after_close = datetime(2025, 6, 20, 16, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        next_opening = next_open("IN", after_close)

        assert next_opening.date() == date(2025, 6, 23)  # Skip weekend
        assert next_opening.time() == time(9, 15)

    def test_next_open_friday_evening_skips_weekend(self):
        """Next open from Friday evening is Monday."""
        from markets import next_open

        friday_evening = datetime(2025, 6, 20, 16, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        next_opening = next_open("IN", friday_evening)

        assert next_opening.weekday() == 0  # Monday


class TestIsHoliday:
    """Holiday checks (uses curated calendars)."""

    def test_us_independence_day_is_holiday(self):
        """July 4 is US market holiday."""
        from markets import is_holiday

        july_4 = date(2025, 7, 4)
        assert is_holiday("US", july_4) is True

    def test_us_christmas_is_holiday(self):
        """Dec 25 is US market holiday."""
        from markets import is_holiday

        christmas = date(2025, 12, 25)
        assert is_holiday("US", christmas) is True

    def test_us_regular_friday_not_holiday(self):
        """Regular Friday is not a holiday."""
        from markets import is_holiday

        regular_friday = date(2025, 6, 20)
        assert is_holiday("US", regular_friday) is False

    def test_india_republic_day_is_holiday(self):
        """Jan 26 is India market holiday."""
        from markets import is_holiday

        republic_day = date(2025, 1, 26)
        assert is_holiday("IN", republic_day) is True

    def test_india_independence_day_is_holiday(self):
        """Aug 15 is India market holiday."""
        from markets import is_holiday

        independence_day = date(2025, 8, 15)
        assert is_holiday("IN", independence_day) is True

    def test_india_regular_friday_not_holiday(self):
        """Regular Friday is not a holiday."""
        from markets import is_holiday

        regular_friday = date(2025, 6, 20)
        assert is_holiday("IN", regular_friday) is False


class TestDSTHandling:
    """Daylight Saving Time transitions (US only)."""

    def test_us_spring_forward_march_2025_trading_day(self):
        """US DST springs forward on March 9, 2025 (Sunday). Test trading day after."""
        from markets import is_market_open

        # March 10, 2025 (Monday) after DST change: 9:30 AM EDT
        after_dst = datetime(2025, 3, 10, 9, 30, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", after_dst) is True

    def test_us_fall_back_november_2025_trading_day(self):
        """US DST falls back on November 2, 2025 (Sunday). Test trading day after."""
        from markets import is_market_open

        # November 3, 2025 (Monday) after DST change: 9:30 AM EST
        after_fallback = datetime(2025, 11, 3, 9, 30, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", after_fallback) is True


class TestMarketTimezoneCrossover:
    """Time zone conversions (IN and US overlap ~1 hour)."""

    def test_simultaneous_check_both_markets(self):
        """Check both markets open/closed at same UTC instant."""
        from markets import is_market_open

        # 9:45 AM IST = 12:15 AM UTC = 7:15 PM EDT (previous day)
        ist_morning = datetime(2025, 6, 20, 9, 45, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        assert is_market_open("IN", ist_morning) is True

        edt_evening = datetime(2025, 6, 19, 19, 15, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_market_open("US", edt_evening) is False


class TestBackwardCompatShim:
    """Backward compatibility with existing is_market_open_now_ist()."""

    def test_is_market_open_now_ist_delegates_to_is_market_open(self):
        """Existing kickstart.py code calls is_market_open_now_ist() for IN."""
        from markets import is_market_open_now_ist

        # Should work (delegates to is_market_open('IN', now))
        result = is_market_open_now_ist()
        assert isinstance(result, bool)
