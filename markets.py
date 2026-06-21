"""
Market specifications and hours - Phase 2 multi-market support.

Provides timezone-aware market hours, holiday calendars, and DST-safe checking.
Pure functions with zero broker or kickstart dependencies.
"""

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional


@dataclass(frozen=True)
class MarketSpec:
    """Immutable market specification."""

    code: str  # 'IN' | 'US'
    tz: str  # IANA timezone string
    open_t: time  # Market open time (local)
    close_t: time  # Market close time (local)
    currency: str  # 'INR' | 'USD'
    default_exchange: str  # 'NSE' | 'SMART'


# Market registry
MARKETS = {
    "IN": MarketSpec(
        code="IN",
        tz="Asia/Kolkata",
        open_t=time(9, 15),
        close_t=time(15, 30),
        currency="INR",
        default_exchange="NSE",
    ),
    "US": MarketSpec(
        code="US",
        tz="America/New_York",
        open_t=time(9, 30),
        close_t=time(16, 0),
        currency="USD",
        default_exchange="SMART",
    ),
}

# US market holidays (fixed + observed, curated for 2025-2026)
US_HOLIDAYS = {
    date(2025, 1, 1),   # New Year's Day
    date(2025, 1, 20),  # MLK Day (3rd Monday)
    date(2025, 2, 17),  # Presidents Day (3rd Monday)
    date(2025, 3, 17),  # Good Friday (Easter)
    date(2025, 5, 26),  # Memorial Day (last Monday)
    date(2025, 7, 4),   # Independence Day
    date(2025, 9, 1),   # Labor Day (1st Monday)
    date(2025, 11, 27), # Thanksgiving (4th Thursday)
    date(2025, 12, 25), # Christmas
    # 2026 (partial)
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # MLK Day
    date(2026, 2, 16),  # Presidents Day
    date(2026, 4, 3),   # Good Friday
}

# India market holidays (NSE calendar, curated for 2025-2026)
IN_HOLIDAYS = {
    date(2025, 1, 26),  # Republic Day
    date(2025, 3, 8),   # Maha Shivaratri
    date(2025, 3, 11),  # Holi (moved)
    date(2025, 3, 29),  # Good Friday
    date(2025, 4, 11),  # Eid ul-Fitr
    date(2025, 4, 17),  # Ram Navami
    date(2025, 4, 21),  # Mahavir Jayanti
    date(2025, 5, 23),  # Buddha Purnima
    date(2025, 8, 15),  # Independence Day
    date(2025, 8, 27),  # Janmashtami
    date(2025, 9, 16),  # Milad-un-Nabi
    date(2025, 10, 2),  # Gandhi Jayanti
    date(2025, 10, 20), # Dussehra
    date(2025, 10, 30), # Diwali
    date(2025, 11, 1),  # Diwali (Day 2)
    date(2025, 11, 15), # Guru Nanak Jayanti
    date(2025, 12, 25), # Christmas
    # 2026 (partial)
    date(2026, 1, 26),  # Republic Day
}

HOLIDAYS = {
    "US": US_HOLIDAYS,
    "IN": IN_HOLIDAYS,
}


def is_market_open(market: str, now: Optional[datetime] = None) -> bool:
    """
    Check if a market is open at a given time.

    Handles:
    - Market hours (open_t to close_t in local time)
    - Weekends (Saturday/Sunday closed)
    - Holidays (per market calendar)
    - DST transitions (via zoneinfo)

    Args:
        market: 'IN' or 'US'
        now: datetime to check (if None, uses datetime.now() in market TZ)

    Returns:
        True if market is open, False otherwise.
    """
    if market not in MARKETS:
        return False

    spec = MARKETS[market]
    tz = ZoneInfo(spec.tz)

    # Default to now in market timezone
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        # Naive datetime — assume UTC (weak but safe)
        now = now.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    else:
        # Convert to market timezone
        now = now.astimezone(tz)

    # Check weekday (0=Mon, 5=Sat, 6=Sun)
    if now.weekday() >= 5:
        return False

    # Check holiday
    if is_holiday(market, now.date()):
        return False

    # Check market hours (local wall-clock time)
    now_time = now.time()
    if now_time < spec.open_t or now_time >= spec.close_t:
        return False

    return True


def next_open(market: str, now: Optional[datetime] = None) -> datetime:
    """
    Calculate the next market open time.

    Skips weekends and holidays.

    Args:
        market: 'IN' or 'US'
        now: reference time (if None, uses now)

    Returns:
        Next market open as aware datetime in market timezone.
    """
    if market not in MARKETS:
        raise ValueError(f"Unknown market: {market}")

    spec = MARKETS[market]
    tz = ZoneInfo(spec.tz)

    # Default to now
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    else:
        now = now.astimezone(tz)

    # Start from tomorrow
    check_date = (now + timedelta(days=1)).date()

    # Skip weekends and holidays until we find an open day
    max_iterations = 30  # Safety limit
    iterations = 0
    while iterations < max_iterations:
        if check_date.weekday() < 5 and not is_holiday(market, check_date):
            # Found an open day; return at market open
            return datetime.combine(check_date, spec.open_t, tzinfo=tz)

        check_date += timedelta(days=1)
        iterations += 1

    # Fallback (should never reach here)
    return datetime.combine(check_date, spec.open_t, tzinfo=tz)


def is_holiday(market: str, d: date) -> bool:
    """
    Check if a date is a market holiday.

    Args:
        market: 'IN' or 'US'
        d: date to check

    Returns:
        True if holiday, False otherwise.
    """
    if market not in HOLIDAYS:
        return False

    return d in HOLIDAYS[market]


def is_market_open_now_ist() -> bool:
    """
    Backward-compatible shim for kickstart.py calls.

    Returns True if India (IN) market is open now.
    This is the function existing code calls at line ~1772.
    """
    return is_market_open("IN")


def get_market_spec(market: str) -> Optional[MarketSpec]:
    """Get market spec by code."""
    return MARKETS.get(market)
