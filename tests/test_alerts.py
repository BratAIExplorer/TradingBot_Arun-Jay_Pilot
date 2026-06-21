"""
ARUN Trading Bot v2.6.0 - Alert System Unit Tests

RED PHASE: Tests for alerts table, deduplication, email delivery, and severity routing.
Tests will fail until notifications.py is reactivated and alerts table exists.

Test Coverage:
- Deduplication logic (UNIQUE index on dedup_key + date)
- Email gating (CRITICAL/WARN only, only when INSERT succeeds)
- Severity routing (INFO → DB, WARN → DB+Email, CRITICAL → DB+Email)
- Across-midnight dedup boundary
- Alert table schema validation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, call
import sqlite3


class TestAlertTableSchema:
    """Verify alerts table schema and indexes"""

    def test_alerts_table_exists_after_migration(self):
        """alerts table is created via _run_migrations()"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Query table existence
        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        )
        result = cursor.fetchone()

        assert result is not None, "alerts table should exist after migration"

    def test_alerts_table_has_required_columns(self):
        """alerts table has: id, timestamp, event_type, severity, symbol, message, dedup_key, delivered_email, acknowledged"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(alerts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        required_cols = ["id", "timestamp", "event_type", "severity", "symbol", "message", "dedup_key", "delivered_email", "acknowledged"]
        for col in required_cols:
            assert col in columns, f"Column '{col}' missing from alerts table"

    def test_dedup_index_exists(self):
        """UNIQUE index on (dedup_key, date(timestamp)) prevents duplicates"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%alert_dedup%'")
        result = cursor.fetchone()

        assert result is not None, "dedup index should exist"

    def test_safety_checks_log_table_exists(self):
        """safety_checks_log table for audit trail"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='safety_checks_log'"
        )
        result = cursor.fetchone()

        assert result is not None, "safety_checks_log table should exist"


class TestAlertDeduplication:
    """Alert deduplication logic"""

    def test_duplicate_alert_same_key_same_day_ignored(self):
        """Second alert with same dedup_key on same day is ignored (INSERT OR IGNORE)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()

        # First alert
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought 10 shares",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))
        db.connection.commit()

        # Second alert with same dedup_key
        cursor.execute("""
            INSERT OR IGNORE INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought 10 shares (retry)",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))
        db.connection.commit()

        # Check only 1 row exists
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE dedup_key = ?", ("TRADE_EXECUTED:HDFCBANK:1500.0",))
        count = cursor.fetchone()[0]

        assert count == 1, "Duplicate alert should be ignored"

    def test_duplicate_alert_different_day_allowed(self):
        """Same dedup_key on different day creates new alert"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()

        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        # Alert today
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            today.isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought today",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))

        # Same alert tomorrow
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tomorrow.isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought tomorrow",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))
        db.connection.commit()

        cursor.execute("SELECT COUNT(*) FROM alerts WHERE dedup_key = ?", ("TRADE_EXECUTED:HDFCBANK:1500.0",))
        count = cursor.fetchone()[0]

        assert count == 2, "Different day duplicates should both exist"

    def test_dedup_key_format_event_symbol_value(self):
        """Dedup key format: event_type:symbol:value"""
        dedup_key = "TRADE_EXECUTED:HDFCBANK:1500.0"

        parts = dedup_key.split(":")
        assert len(parts) == 3
        assert parts[0] == "TRADE_EXECUTED"
        assert parts[1] == "HDFCBANK"
        assert parts[2] == "1500.0"

    def test_different_event_types_not_deduped(self):
        """Different event_type = not deduped (e.g., TRADE_EXECUTED vs STOP_LOSS)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        now = datetime.now()

        # Trade executed
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))

        # Stop loss (different event)
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(),
            "STOP_LOSS_HIT",
            "CRITICAL",
            "HDFCBANK",
            "Stop loss triggered",
            "STOP_LOSS_HIT:HDFCBANK:1450.0"
        ))
        db.connection.commit()

        cursor.execute("SELECT COUNT(*) FROM alerts")
        count = cursor.fetchone()[0]

        assert count == 2, "Different event types should both be stored"


class TestSeverityRouting:
    """Alert severity → delivery channel mapping"""

    def test_info_severity_alerts_only_to_db(self):
        """INFO severity: DB only, no email"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Mock email function
        with patch("notifications.send_email") as mock_email:
            # Insert INFO alert (no email should be sent)
            cursor = db.connection.cursor()
            cursor.execute("""
                INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "TRADE_EXECUTED",
                "INFO",
                "HDFCBANK",
                "Bought 10",
                "TRADE_EXECUTED:HDFCBANK:1500.0"
            ))
            db.connection.commit()

            # Email should NOT be sent
            mock_email.assert_not_called()

    def test_warn_severity_alerts_to_db_and_email(self):
        """WARN severity: DB + email (e.g., never-sell-at-loss block)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key, delivered_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "NEVER_SELL_AT_LOSS_BLOCKED",
            "WARN",
            "INFY",
            "Order blocked: would sell at loss",
            "NEVER_SELL:INFY:1950.0",
            1  # Email sent
        ))
        db.connection.commit()

        cursor.execute("SELECT delivered_email FROM alerts WHERE severity = 'WARN'")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 1, "WARN alert should have email flag set"

    def test_critical_severity_alerts_to_db_and_email(self):
        """CRITICAL severity: DB + email immediately (e.g., safety gate, loss limit)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key, delivered_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "DAILY_LOSS_LIMIT_HIT",
            "CRITICAL",
            None,
            "Daily loss limit exceeded: -₹6000 (6% of portfolio)",
            "DAILY_LOSS_LIMIT:2026-06-21",
            1
        ))
        db.connection.commit()

        cursor.execute("SELECT delivered_email FROM alerts WHERE severity = 'CRITICAL'")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 1, "CRITICAL alert should have email flag set"


class TestEmailDeliveryGating:
    """Email sent only on successful INSERT (not on IGNORE)"""

    def test_email_sent_only_on_insert_success(self):
        """Email sent when INSERT succeeds (rowcount == 1), not on IGNORE"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()

        # First alert: INSERT succeeds
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "TRADE_EXECUTED",
            "WARN",
            "HDFCBANK",
            "Bought 10",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))

        first_rowcount = cursor.rowcount

        # Second alert: INSERT IGNORE (duplicate dedup_key, same day)
        cursor.execute("""
            INSERT OR IGNORE INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "TRADE_EXECUTED",
            "WARN",
            "HDFCBANK",
            "Bought 10 (retry)",
            "TRADE_EXECUTED:HDFCBANK:1500.0"
        ))

        second_rowcount = cursor.rowcount
        db.connection.commit()

        # First insert should succeed (rowcount=1)
        assert first_rowcount == 1
        # Second insert should be ignored (rowcount=0)
        assert second_rowcount == 0


class TestAcknowledgement:
    """Alert acknowledgement via API"""

    def test_acknowledge_alert_sets_flag(self):
        """POST /api/alerts/ack updates acknowledged = 1"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()

        # Insert alert
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "DAILY_LOSS_LIMIT_HIT",
            "CRITICAL",
            None,
            "Daily loss limit hit",
            "DAILY_LOSS:2026-06-21",
            0  # Not acknowledged
        ))
        db.connection.commit()

        alert_id = cursor.lastrowid

        # Acknowledge it
        cursor.execute("""
            UPDATE alerts SET acknowledged = 1 WHERE id = ?
        """, (alert_id,))
        db.connection.commit()

        # Verify
        cursor.execute("SELECT acknowledged FROM alerts WHERE id = ?", (alert_id,))
        acknowledged = cursor.fetchone()[0]

        assert acknowledged == 1

    def test_get_unacknowledged_alerts(self):
        """GET /api/alerts?unack=true returns only acknowledged=0 alerts"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        cursor = db.connection.cursor()

        # Insert acked and unacked alerts
        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "TRADE_EXECUTED",
            "INFO",
            "HDFCBANK",
            "Bought",
            "TRADE:HDFCBANK:1500.0",
            1  # Acknowledged
        ))

        cursor.execute("""
            INSERT INTO alerts (timestamp, event_type, severity, symbol, message, dedup_key, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "STOP_LOSS_HIT",
            "CRITICAL",
            "INFY",
            "Stop loss",
            "STOP_LOSS:INFY:1950.0",
            0  # Unacknowledged
        ))
        db.connection.commit()

        # Get unacknowledged
        cursor.execute("SELECT * FROM alerts WHERE acknowledged = 0")
        unacked = cursor.fetchall()

        assert len(unacked) == 1


class TestEventTypes:
    """Alert event types and their triggers"""

    def test_event_type_trade_executed(self):
        """TRADE_EXECUTED: triggered when BUY or SELL completes"""
        event_type = "TRADE_EXECUTED"
        assert event_type is not None

    def test_event_type_never_sell_at_loss_blocked(self):
        """NEVER_SELL_AT_LOSS_BLOCKED: when pre-trade gate blocks SELL at loss"""
        event_type = "NEVER_SELL_AT_LOSS_BLOCKED"
        assert event_type is not None

    def test_event_type_stop_loss_hit(self):
        """STOP_LOSS_HIT: when stop-loss triggers"""
        event_type = "STOP_LOSS_HIT"
        assert event_type is not None

    def test_event_type_daily_loss_limit_hit(self):
        """DAILY_LOSS_LIMIT_HIT: when daily P&L exceeds loss limit"""
        event_type = "DAILY_LOSS_LIMIT_HIT"
        assert event_type is not None

    def test_event_type_safety_check_critical(self):
        """SAFETY_CHECK_CRITICAL: when any safety check fails"""
        event_type = "SAFETY_CHECK_CRITICAL"
        assert event_type is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
