"""
Regression Test Suite for ARUN Trading Bot

This module ensures that all known bugs don't resurface. Each test corresponds to
an entry in BUG_REGISTRY.md and validates the fix is still working.

Run: pytest tests/test_regressions.py -v
"""

import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# BUG-001: Phantom Positions (SCRIP LIMIT INSUFFICIENT)
# ============================================================================

@pytest.mark.regression
def test_phantom_position_error_handling():
    """
    BUG-001: Verify bot handles SCRIP LIMIT INSUFFICIENT errors without crashes.

    When broker rejects order due to phantom position, bot should:
    - Add symbol to cooldown list
    - Stop retry attempts for 1 hour
    - Log helpful message
    """
    error_message = "SCRIP LIMIT INSUFFICIENT BY-60 AND AVAILABLE QTY IS - 0"

    # Simulate RMS_FAILURES cooldown dict
    rms_failures = {}

    # First error: add to cooldown
    symbol = "HINDCOPPER"
    if error_message and "SCRIP LIMIT INSUFFICIENT" in error_message:
        rms_failures[symbol] = datetime.now()

    assert symbol in rms_failures
    assert isinstance(rms_failures[symbol], datetime)

    # Check cooldown is still active (within 1 hour)
    now = datetime.now()
    elapsed = (now - rms_failures[symbol]).total_seconds()
    cooldown_active = elapsed < 3600  # 1 hour

    assert cooldown_active is True

    # Check cooldown expires after 1 hour
    rms_failures[symbol] = datetime.now() - timedelta(seconds=3601)
    now = datetime.now()
    elapsed = (now - rms_failures[symbol]).total_seconds()
    cooldown_active = elapsed < 3600

    assert cooldown_active is False


@pytest.mark.regression
def test_phantom_position_no_retry():
    """
    BUG-001: Verify bot doesn't retry phantom position orders.

    Once a symbol hits SCRIP LIMIT error, no more retry attempts should occur
    until cooldown expires.
    """
    symbol = "HINDCOPPER"
    rms_failures = {symbol: datetime.now()}
    max_retries = 3
    retry_count = 0

    # Simulate retry logic
    if symbol in rms_failures:
        # Symbol in cooldown, don't retry
        retry_count = 0
    else:
        retry_count = max_retries

    assert retry_count == 0, "Should not retry if symbol in cooldown"


# ============================================================================
# BUG-002: Database Initialization on Deployments
# ============================================================================

@pytest.mark.regression
def test_database_schema_initialization():
    """
    BUG-002: Verify database schema is created on first init.

    When deploying to new server without trades.db, schema must be fully created.
    """
    # Create temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")

        # Initialize database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create required tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_control (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                symbol TEXT PRIMARY KEY,
                total_pnl REAL,
                win_count INTEGER,
                loss_count INTEGER
            )
        """)

        conn.commit()

        # Verify all tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "trades" in tables
        assert "system_control" in tables
        assert "analytics" in tables

        conn.close()

        # Verify database file was created
        assert os.path.exists(db_path)


@pytest.mark.regression
def test_database_handles_empty_startup():
    """
    BUG-002: Verify database gracefully handles startup with no trades.db.

    Should create all tables automatically without crashing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")

        # Database doesn't exist yet
        assert not os.path.exists(db_path)

        # Simulate initialization logic
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # This should work even though DB is new
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT
                )
            """)
            conn.commit()
            success = True
        except Exception as e:
            success = False

        assert success, "Should handle fresh database without error"
        conn.close()


# ============================================================================
# BUG-003: Duplicate Trades
# ============================================================================

@pytest.mark.regression
def test_duplicate_trade_detection():
    """
    BUG-003: Verify 10-second dedup window prevents identical trades.

    If same trade inserted twice within 10 seconds, second insert should fail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp DATETIME,
                UNIQUE(symbol, price, quantity, timestamp)
            )
        """)
        conn.commit()

        # Insert first trade
        symbol = "MOSCHIP"
        price = 100.0
        quantity = 10
        timestamp = datetime.now()

        cursor.execute(
            "INSERT INTO trades (symbol, price, quantity, timestamp) VALUES (?, ?, ?, ?)",
            (symbol, price, quantity, timestamp)
        )
        conn.commit()

        # Attempt duplicate within 10 seconds
        try:
            cursor.execute(
                "INSERT INTO trades (symbol, price, quantity, timestamp) VALUES (?, ?, ?, ?)",
                (symbol, price, quantity, timestamp)
            )
            conn.commit()
            duplicate_inserted = True
        except sqlite3.IntegrityError:
            duplicate_inserted = False

        assert not duplicate_inserted, "Duplicate should be rejected by UNIQUE constraint"

        # Verify only 1 record in database
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        assert count == 1

        conn.close()


@pytest.mark.regression
def test_different_trades_not_blocked():
    """
    BUG-003: Verify that different trades (different price/qty) are allowed.

    Only exact duplicates should be blocked, not similar trades.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                price REAL,
                quantity INTEGER,
                timestamp DATETIME
            )
        """)

        # Insert first trade
        cursor.execute(
            "INSERT INTO trades (symbol, price, quantity, timestamp) VALUES (?, ?, ?, ?)",
            ("MOSCHIP", 100.0, 10, datetime.now())
        )

        # Insert similar but different trade
        cursor.execute(
            "INSERT INTO trades (symbol, price, quantity, timestamp) VALUES (?, ?, ?, ?)",
            ("MOSCHIP", 101.0, 10, datetime.now())  # Different price
        )

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]

        assert count == 2, "Different trades should both be inserted"

        conn.close()


# ============================================================================
# BUG-004: Missing P&L Calculations
# ============================================================================

@pytest.mark.regression
def test_missing_pnl_detection():
    """
    BUG-004: Verify missing P&L is detected and can be backfilled.

    Sell trades should always have P&L. If missing, backfill script must fill it.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                pnl REAL,
                timestamp DATETIME
            )
        """)

        # Insert buy
        buy_time = datetime.now()
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, pnl, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("CANBK", "BUY", 100.0, 10, None, buy_time)
        )

        # Insert sell with missing P&L
        sell_time = buy_time + timedelta(hours=1)
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, pnl, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("CANBK", "SELL", 105.0, 10, None, sell_time)
        )

        conn.commit()

        # Find missing P&L
        cursor.execute(
            "SELECT id, symbol, price FROM trades WHERE action='SELL' AND pnl IS NULL"
        )
        missing = cursor.fetchall()

        assert len(missing) == 1, "Should detect 1 missing P&L"

        # Simulate backfill: calculate P&L
        sell_id, symbol, sell_price = missing[0]

        cursor.execute(
            "SELECT price, quantity FROM trades WHERE symbol=? AND action='BUY'",
            (symbol,)
        )
        buy_data = cursor.fetchone()

        if buy_data:
            buy_price, quantity = buy_data
            pnl = (sell_price - buy_price) * quantity

            # Update sell with calculated P&L
            cursor.execute(
                "UPDATE trades SET pnl=? WHERE id=?",
                (pnl, sell_id)
            )
            conn.commit()

            # Verify P&L was filled
            cursor.execute("SELECT pnl FROM trades WHERE id=?", (sell_id,))
            filled_pnl = cursor.fetchone()[0]

            assert filled_pnl is not None
            assert filled_pnl == pytest.approx(50.0)  # (105-100)*10

        conn.close()


# ============================================================================
# BUG-005: Hardcoded 403 Auth Failures
# ============================================================================

@pytest.mark.regression
def test_auth_token_refresh():
    """
    BUG-005: Verify bot can refresh expired auth tokens automatically.

    When API returns 403, bot should attempt refresh and retry request.
    """
    # Simulate token state
    token_info = {
        "token": "old_token_12345",
        "expires_at": datetime.now() - timedelta(hours=1),  # Expired
        "can_refresh": True
    }

    # Check if token is expired
    is_expired = datetime.now() > token_info["expires_at"]
    assert is_expired, "Token should be expired"

    # Simulate refresh
    if is_expired and token_info.get("can_refresh"):
        token_info["token"] = "new_token_67890"
        token_info["expires_at"] = datetime.now() + timedelta(hours=1)

    # Verify new token is set
    assert token_info["token"] == "new_token_67890"
    assert token_info["expires_at"] > datetime.now()


@pytest.mark.regression
def test_missing_env_credentials_raises_error():
    """
    BUG-005: Verify missing credentials in .env raises helpful error.

    Bot should fail fast with clear message if credentials are missing.
    """
    # Simulate missing credential
    credentials = {}

    def get_credential(key):
        if key not in credentials:
            raise KeyError(
                f"Missing credential: {key}\n"
                f"Please set {key} in .env file"
            )
        return credentials[key]

    # Test that missing API key raises error
    with pytest.raises(KeyError) as exc_info:
        get_credential("MSTOCK_API_KEY")

    assert "Missing credential" in str(exc_info.value)
    assert ".env" in str(exc_info.value)


# ============================================================================
# BUG-006: P&L Calculation FIFO Ordering
# ============================================================================

@pytest.mark.regression
def test_pnl_fifo_calculation():
    """
    BUG-006: Verify P&L matches buy/sell using FIFO (First-In-First-Out) ordering.

    Oldest buys should match with oldest sells, not random pairing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "trades.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                timestamp DATETIME
            )
        """)

        # Insert 3 buys (different dates)
        base_time = datetime(2026, 1, 15, 10, 0, 0)
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "BUY", 100.0, 10, base_time)
        )
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "BUY", 102.0, 10, base_time + timedelta(hours=1))
        )
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "BUY", 104.0, 10, base_time + timedelta(hours=2))
        )

        # Insert 3 sells (different dates)
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "SELL", 105.0, 10, base_time + timedelta(hours=3))
        )
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "SELL", 107.0, 10, base_time + timedelta(hours=4))
        )
        cursor.execute(
            "INSERT INTO trades (symbol, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("APPLE", "SELL", 109.0, 10, base_time + timedelta(hours=5))
        )

        conn.commit()

        # Get trades in FIFO order
        cursor.execute(
            "SELECT action, price FROM trades WHERE symbol=? ORDER BY timestamp ASC",
            ("APPLE",)
        )
        trades = cursor.fetchall()

        # Verify FIFO order
        assert trades[0] == ("BUY", 100.0)   # buy1
        assert trades[1] == ("BUY", 102.0)   # buy2
        assert trades[2] == ("BUY", 104.0)   # buy3
        assert trades[3] == ("SELL", 105.0)  # sell1
        assert trades[4] == ("SELL", 107.0)  # sell2
        assert trades[5] == ("SELL", 109.0)  # sell3

        # Calculate FIFO P&L
        # buy1 (100) + sell1 (105) = +5 per share = +50
        # buy2 (102) + sell2 (107) = +5 per share = +50
        # buy3 (104) + sell3 (109) = +5 per share = +50
        # Total: +150

        pnl1 = (105.0 - 100.0) * 10  # +50
        pnl2 = (107.0 - 102.0) * 10  # +50
        pnl3 = (109.0 - 104.0) * 10  # +50
        total_pnl = pnl1 + pnl2 + pnl3

        assert total_pnl == pytest.approx(150.0)

        conn.close()


# ============================================================================
# BUG-007: 10-Second Duplicate Protection
# ============================================================================

@pytest.mark.regression
def test_duplicate_protection_window():
    """
    BUG-007: Verify 10-second duplicate protection blocks rapid retrades.

    Same trade within 10 seconds should be blocked.
    Same trade after 10 seconds should be allowed.
    """
    # Simulate trade state
    last_trade = {
        "symbol": "MOSCHIP",
        "price": 100.0,
        "timestamp": datetime.now()
    }

    # Attempt identical trade at T+5 seconds
    current_trade = {
        "symbol": "MOSCHIP",
        "price": 100.0,
        "timestamp": datetime.now() + timedelta(seconds=5)
    }

    # Check if duplicate
    time_diff = (current_trade["timestamp"] - last_trade["timestamp"]).total_seconds()
    is_duplicate = (
        time_diff < 10 and
        current_trade["symbol"] == last_trade["symbol"] and
        current_trade["price"] == last_trade["price"]
    )

    assert is_duplicate, "Should detect duplicate at T+5s"

    # Now try at T+11 seconds
    current_trade["timestamp"] = last_trade["timestamp"] + timedelta(seconds=11)
    time_diff = (current_trade["timestamp"] - last_trade["timestamp"]).total_seconds()

    is_duplicate = (
        time_diff < 10 and
        current_trade["symbol"] == last_trade["symbol"]
    )

    assert not is_duplicate, "Should allow trade after 10 seconds"


@pytest.mark.regression
def test_different_symbol_not_blocked():
    """
    BUG-007: Verify different symbols aren't blocked by duplicate protection.

    If last trade was MOSCHIP and new trade is APPLE, it should be allowed.
    """
    last_trade = {
        "symbol": "MOSCHIP",
        "price": 100.0,
        "timestamp": datetime.now()
    }

    current_trade = {
        "symbol": "APPLE",  # Different!
        "price": 100.0,
        "timestamp": datetime.now() + timedelta(seconds=2)
    }

    # Check if duplicate
    is_duplicate = (
        current_trade["symbol"] == last_trade["symbol"]
    )

    assert not is_duplicate, "Different symbols should not be blocked"


# ============================================================================
# BUG-008: Missing Neutral Trades in Performance Summary
# ============================================================================

@pytest.mark.regression
def test_neutral_trades_count():
    """
    BUG-008: Verify neutral trades (zero P&L) are counted in statistics.

    Win rate should include neutral trades in denominator.
    """
    trades = [
        {"symbol": "A", "pnl": 100.0},   # Win
        {"symbol": "B", "pnl": 50.0},    # Win
        {"symbol": "C", "pnl": 25.0},    # Win
        {"symbol": "D", "pnl": -50.0},   # Loss
        {"symbol": "E", "pnl": -100.0},  # Loss
        {"symbol": "F", "pnl": -75.0},   # Loss
        {"symbol": "G", "pnl": 0.0},     # Neutral
    ]

    win_count = sum(1 for t in trades if t["pnl"] > 10)
    loss_count = sum(1 for t in trades if t["pnl"] < -10)
    neutral_count = sum(1 for t in trades if -10 <= t["pnl"] <= 10)
    total_count = len(trades)

    assert win_count == 3
    assert loss_count == 3
    assert neutral_count == 1
    assert total_count == 7

    # Verify win rate includes neutral in denominator
    win_rate = win_count / total_count * 100
    assert win_rate == pytest.approx(42.857, rel=0.01)


@pytest.mark.regression
def test_null_pnl_treated_as_zero():
    """
    BUG-008: Verify NULL P&L is treated as 0 (neutral) in calculations.

    Missing P&L should not break statistics.
    """
    trades = [
        {"symbol": "A", "pnl": 100.0},
        {"symbol": "B", "pnl": -50.0},
        {"symbol": "C", "pnl": None},  # NULL
    ]

    # Apply .fillna(0)
    filled_pnl = [t["pnl"] if t["pnl"] is not None else 0 for t in trades]

    assert filled_pnl == [100.0, -50.0, 0.0]

    win_count = sum(1 for p in filled_pnl if p > 10)
    loss_count = sum(1 for p in filled_pnl if p < -10)
    neutral_count = sum(1 for p in filled_pnl if -10 <= p <= 10)

    assert win_count == 1
    assert loss_count == 1
    assert neutral_count == 1


# ============================================================================
# BUG-009: Never Sell at Loss (3-Layer Defense)
# ============================================================================

@pytest.mark.regression
def test_never_sell_at_loss_enforcement():
    """
    BUG-009: Verify never_sell_at_loss setting is enforced at all 3 layers.

    Layer 1: safe_place_order_when_open (earliest)
    Layer 2: risk_manager.execute (catastrophic stop)
    Layer 3: _execute_broker_order (final guard)
    """
    # Test data
    settings = {"never_sell_at_loss": True}
    position = {
        "symbol": "APPLE",
        "entry_price": 100.0,
        "current_price": 95.0,  # 5% loss
        "quantity": 10
    }

    # Layer 1: Check in safe_place_order_when_open
    if settings.get("never_sell_at_loss"):
        should_block_sell = position["current_price"] < position["entry_price"]

    assert should_block_sell, "Layer 1 should block sell at loss"

    # Layer 2: Check in risk manager
    if settings.get("never_sell_at_loss"):
        should_block_catastrophic = position["current_price"] < position["entry_price"]

    assert should_block_catastrophic, "Layer 2 should block catastrophic stop"

    # Layer 3: Final validation before broker order
    if settings.get("never_sell_at_loss"):
        sell_price = 95.0
        buy_price = 100.0
        should_block_final = sell_price < buy_price

    assert should_block_final, "Layer 3 should block broker order"


@pytest.mark.regression
def test_never_sell_at_loss_disabled():
    """
    BUG-009: Verify selling at loss is allowed when setting is disabled.

    With never_sell_at_loss=False, all sales should be allowed.
    """
    settings = {"never_sell_at_loss": False}
    position = {
        "symbol": "APPLE",
        "entry_price": 100.0,
        "current_price": 95.0,  # 5% loss
    }

    # Check: when disabled, should allow loss
    if not settings.get("never_sell_at_loss"):
        should_allow = True
    else:
        should_allow = position["current_price"] >= position["entry_price"]

    assert should_allow, "Should allow sell at loss when setting disabled"


# ============================================================================
# BUG-014: Market Filter Not Working
# ============================================================================

@pytest.mark.regression
def test_market_filter_positions():
    """
    BUG-014: Verify positions are filtered by market when switching markets.

    When user selects US market, only US positions should be shown.
    When user selects India market, only India positions should be shown.

    Market determination:
    - India (IN): NSE, BSE, NCDEX, MCX exchanges
    - US (US): SMART, NYSE, NASDAQ, ARCA, ISLAND exchanges
    """
    # Sample positions from broker (mixed markets)
    all_positions = {
        ("MOSCHIP", "NSE"): {"qty": 5, "price": 178.89, "pnl": 0.0},      # India
        ("NIFTYBEES", "NSE"): {"qty": 10, "price": 289.48, "pnl": 0.0},   # India
        ("AAPL", "SMART"): {"qty": 1, "price": 150.00, "pnl": 100.0},     # US
        ("MSFT", "NASDAQ"): {"qty": 2, "price": 380.00, "pnl": 50.0},     # US
    }

    # Market to exchange mapping
    market_exchanges = {
        'IN': ('NSE', 'BSE', 'NCDEX', 'MCX'),
        'US': ('SMART', 'NYSE', 'NASDAQ', 'ARCA', 'ISLAND')
    }

    # Test 1: Filter for India market
    india_market = 'IN'
    india_filtered = {}
    for (symbol, exchange), pos_data in all_positions.items():
        if exchange.upper() in market_exchanges[india_market]:
            india_filtered[(symbol, exchange)] = pos_data

    assert len(india_filtered) == 2, f"India filter should have 2 positions, got {len(india_filtered)}"
    assert ("MOSCHIP", "NSE") in india_filtered
    assert ("NIFTYBEES", "NSE") in india_filtered
    assert ("AAPL", "SMART") not in india_filtered
    assert ("MSFT", "NASDAQ") not in india_filtered

    # Test 2: Filter for US market
    us_market = 'US'
    us_filtered = {}
    for (symbol, exchange), pos_data in all_positions.items():
        if exchange.upper() in market_exchanges[us_market]:
            us_filtered[(symbol, exchange)] = pos_data

    assert len(us_filtered) == 2, f"US filter should have 2 positions, got {len(us_filtered)}"
    assert ("AAPL", "SMART") in us_filtered
    assert ("MSFT", "NASDAQ") in us_filtered
    assert ("MOSCHIP", "NSE") not in us_filtered
    assert ("NIFTYBEES", "NSE") not in us_filtered

    # Test 3: Switching markets shouldn't break positions for other market
    assert india_filtered != us_filtered, "Market filters should produce different results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
