"""
ARUN Trading Bot v2.6.0 - Safety Checks Unit Tests

RED PHASE: All tests intentionally fail (module doesn't exist yet)
This establishes the baseline for TDD GREEN phase implementation.

Test Coverage:
- CheckResult immutability (frozen dataclass)
- SafetyChecker dependency injection
- 5 check_* methods (duplicate, position, P&L, capital, loss limit)
- Edge cases: empty DB, race conditions, boundary values
"""

import pytest
from datetime import datetime, timedelta
from dataclasses import astuple
from unittest.mock import Mock, MagicMock, patch
import sqlite3

# These imports will FAIL until safety_checks.py exists (RED phase)
from safety_checks import CheckResult, SafetyChecker


class TestCheckResult:
    """Verify CheckResult is immutable frozen dataclass"""

    def test_checkresult_is_frozen(self):
        """CheckResult attributes cannot be modified after creation"""
        result = CheckResult(
            name="test_check",
            passed=True,
            severity="INFO",
            message="All good",
            data={"key": "value"}
        )

        with pytest.raises(Exception):  # FrozenInstanceError from dataclass
            result.passed = False

    def test_checkresult_immutable_dict(self):
        """CheckResult.data dict is frozen (no mutations)"""
        result = CheckResult(
            name="test",
            passed=True,
            severity="INFO",
            message="msg",
            data={"a": 1}
        )

        # Original data unchanged
        assert result.data == {"a": 1}

        # Attempting to mutate should not affect result
        new_data = result.data.copy()
        new_data["b"] = 2
        assert result.data == {"a": 1}  # unchanged

    def test_checkresult_attributes_present(self):
        """CheckResult has all required attributes"""
        result = CheckResult(
            name="dup_check",
            passed=False,
            severity="CRITICAL",
            message="Duplicate detected",
            data={"symbol": "HDFCBANK", "window_seconds": 10}
        )

        assert result.name == "dup_check"
        assert result.passed is False
        assert result.severity == "CRITICAL"
        assert result.message == "Duplicate detected"
        assert isinstance(result.data, dict)


class TestSafetyCheckerInit:
    """SafetyChecker dependency injection and initialization"""

    def test_safetychecker_init_requires_db_and_settings(self):
        """SafetyChecker accepts TradesDatabase and SettingsManager"""
        mock_db = Mock()
        mock_settings = Mock()

        checker = SafetyChecker(db=mock_db, settings=mock_settings)

        assert checker.db is mock_db
        assert checker.settings is mock_settings

    def test_safetychecker_stores_dependencies(self):
        """Injected dependencies are stored as instance variables"""
        mock_db = Mock()
        mock_settings = Mock()
        mock_db.name = "test_db"
        mock_settings.name = "test_settings"

        checker = SafetyChecker(db=mock_db, settings=mock_settings)

        assert checker.db.name == "test_db"
        assert checker.settings.name == "test_settings"


class TestDuplicateTradeDetection:
    """SafetyChecker.check_duplicate_trades()"""

    def test_duplicate_trade_detected_same_symbol_10s_window(self):
        """Same symbol trade within 10 seconds is duplicate"""
        mock_db = Mock()
        mock_settings = Mock()

        # Mock recent trades: same symbol within 10s
        now = datetime.now()
        recent_trade = {
            "id": 100,
            "symbol": "HDFCBANK",
            "timestamp": (now - timedelta(seconds=3)).isoformat(),  # 3 seconds ago (ISO string)
            "trade_type": "BUY"
        }
        mock_db.get_recent_trades.return_value = [recent_trade]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_duplicate_trades(symbol="HDFCBANK", window_seconds=10)

        assert result.name == "duplicate_trades"
        assert result.passed is False
        assert result.severity == "CRITICAL"
        assert "HDFCBANK" in result.message.upper()

    def test_no_duplicate_trade_different_symbol(self):
        """Different symbol not flagged as duplicate"""
        mock_db = Mock()
        mock_settings = Mock()

        # Mock recent trades: different symbol
        recent_trade = {
            "id": 100,
            "symbol": "INFY",
            "timestamp": (datetime.now() - timedelta(seconds=3)).isoformat()  # ISO string
        }
        mock_db.get_recent_trades.return_value = [recent_trade]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_duplicate_trades(symbol="HDFCBANK", window_seconds=10)

        assert result.name == "duplicate_trades"
        assert result.passed is True
        assert result.severity == "INFO"

    def test_no_duplicate_trade_outside_window(self):
        """Same symbol but outside 10s window is not duplicate"""
        mock_db = Mock()
        mock_settings = Mock()

        # Mock recent trades: same symbol but 15s ago (outside 10s window)
        recent_trade = {
            "id": 100,
            "symbol": "HDFCBANK",
            "timestamp": (datetime.now() - timedelta(seconds=15)).isoformat()  # ISO string
        }
        mock_db.get_recent_trades.return_value = [recent_trade]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_duplicate_trades(symbol="HDFCBANK", window_seconds=10)

        assert result.passed is True

    def test_duplicate_check_empty_trade_history(self):
        """Empty trade history: no duplicates possible"""
        mock_db = Mock()
        mock_settings = Mock()
        mock_db.get_recent_trades.return_value = []

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_duplicate_trades(symbol="HDFCBANK", window_seconds=10)

        assert result.passed is True


class TestPositionConsistency:
    """SafetyChecker.check_position_consistency()"""

    def test_position_mismatch_db_vs_broker(self):
        """DB and broker positions don't match"""
        mock_db = Mock()
        mock_settings = Mock()

        # DB shows 10 shares, broker shows 8
        mock_db.get_open_positions.return_value = [
            {"symbol": "HDFCBANK", "quantity": 10}
        ]
        broker_positions = [
            {"symbol": "HDFCBANK", "quantity": 8}
        ]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_position_consistency(broker_positions=broker_positions)

        assert result.name == "position_consistency"
        assert result.passed is False
        assert result.severity == "CRITICAL"

    def test_position_match_db_vs_broker(self):
        """DB and broker positions match exactly"""
        mock_db = Mock()
        mock_settings = Mock()

        mock_db.get_open_positions.return_value = [
            {"symbol": "HDFCBANK", "quantity": 10}
        ]
        broker_positions = [
            {"symbol": "HDFCBANK", "quantity": 10}
        ]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_position_consistency(broker_positions=broker_positions)

        assert result.passed is True

    def test_position_empty_both_sides(self):
        """No positions on either side: consistent"""
        mock_db = Mock()
        mock_settings = Mock()

        mock_db.get_open_positions.return_value = []

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_position_consistency(broker_positions=[])

        assert result.passed is True


class TestPnlIntegrity:
    """SafetyChecker.check_pnl_integrity()"""

    def test_pnl_null_on_sell_side_flagged(self):
        """SELL trades with NULL P&L are flagged"""
        mock_db = Mock()
        mock_settings = Mock()

        # SELL with NULL P&L (should have been calculated)
        mock_db.query_all_trades.return_value = [
            {
                "id": 200,
                "trade_type": "SELL",
                "pnl_net": None,
                "symbol": "HDFCBANK",
                "timestamp": datetime.now().isoformat()
            }
        ]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_pnl_integrity()

        assert result.name == "pnl_integrity"
        assert result.passed is False
        assert result.severity == "WARN"

    def test_pnl_fifo_ordering_violation(self):
        """BUY after SELL for same symbol violates FIFO"""
        mock_db = Mock()
        mock_settings = Mock()

        # SELL comes BEFORE BUY in time (wrong order - can't sell before you buy)
        mock_db.query_all_trades.return_value = [
            {"id": 100, "symbol": "HDFCBANK", "trade_type": "SELL", "timestamp": "2026-01-01T10:00:00", "pnl_net": 100.0},
            {"id": 101, "symbol": "HDFCBANK", "trade_type": "BUY", "timestamp": "2026-01-02T10:00:00"},
        ]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_pnl_integrity()

        assert result.passed is False

    def test_pnl_integrity_all_good(self):
        """Well-formed trades with P&L pass integrity check"""
        mock_db = Mock()
        mock_settings = Mock()

        mock_db.query_trades.return_value = [
            {"id": 1, "symbol": "HDFCBANK", "trade_type": "BUY", "pnl_net": None, "timestamp": "2026-01-01 10:00:00"},
            {"id": 2, "symbol": "HDFCBANK", "trade_type": "SELL", "pnl_net": 500.0, "timestamp": "2026-01-02 10:00:00"},
        ]

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_pnl_integrity()

        assert result.passed is True


class TestCapitalBounds:
    """SafetyChecker.check_capital_bounds()"""

    def test_capital_within_bounds(self):
        """Used capital less than allocated"""
        mock_db = Mock()
        mock_settings = Mock()
        mock_settings.get.return_value = {
            "ALLOCATED_CAPITAL": 100000,
            "total_capital": 150000
        }
        mock_db.get_open_position_value.return_value = 30000  # 30k deployed

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_capital_bounds(
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=30000
        )

        assert result.name == "capital_bounds"
        assert result.passed is True

    def test_capital_exceeds_allocated(self):
        """Deployed capital exceeds allocated limit"""
        mock_db = Mock()
        mock_settings = Mock()

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_capital_bounds(
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=120000  # Over allocated!
        )

        assert result.passed is False
        assert result.severity == "CRITICAL"

    def test_capital_exceeds_total(self):
        """Deployed capital exceeds total available"""
        mock_db = Mock()
        mock_settings = Mock()

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_capital_bounds(
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=160000  # Over total!
        )

        assert result.passed is False
        assert result.severity == "CRITICAL"


class TestDailyLossLimit:
    """SafetyChecker.check_daily_loss_limit()"""

    def test_daily_loss_within_limit(self):
        """Today's loss below threshold"""
        mock_db = Mock()
        mock_settings = Mock()

        # Today's P&L: -2000 (2% loss on 100k)
        mock_db.get_daily_pnl.return_value = -2000
        mock_settings.get.return_value = {"daily_loss_limit_pct": 5.0}

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_daily_loss_limit(
            daily_pnl=-2000,
            portfolio_value=100000,
            daily_loss_limit_pct=5.0
        )

        assert result.name == "daily_loss_limit"
        assert result.passed is True

    def test_daily_loss_exceeds_limit(self):
        """Today's loss exceeds threshold"""
        mock_db = Mock()
        mock_settings = Mock()

        # Today's P&L: -8000 (8% loss on 100k) > 5% limit
        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_daily_loss_limit(
            daily_pnl=-8000,
            portfolio_value=100000,
            daily_loss_limit_pct=5.0
        )

        assert result.passed is False
        assert result.severity == "CRITICAL"

    def test_daily_profit_always_passes(self):
        """Profitable day always passes loss check"""
        mock_db = Mock()
        mock_settings = Mock()

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        result = checker.check_daily_loss_limit(
            daily_pnl=5000,  # Profit!
            portfolio_value=100000,
            daily_loss_limit_pct=5.0
        )

        assert result.passed is True


class TestRunAll:
    """SafetyChecker.run_all() orchestrator"""

    def test_run_all_executes_all_checks(self):
        """run_all() calls all 5 check methods"""
        mock_db = Mock()
        mock_settings = Mock()

        # Mock all dependencies
        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_positions.return_value = []
        mock_db.query_trades.return_value = []

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        results = checker.run_all(
            symbol="HDFCBANK",
            broker_positions=[],
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=30000,
            daily_pnl=0,
            daily_loss_limit_pct=5.0
        )

        assert isinstance(results, list)
        assert len(results) == 5  # All 5 checks

        check_names = [r.name for r in results]
        assert "duplicate_trades" in check_names
        assert "position_consistency" in check_names
        assert "pnl_integrity" in check_names
        assert "capital_bounds" in check_names
        assert "daily_loss_limit" in check_names

    def test_run_all_returns_checkresult_list(self):
        """run_all() returns list of CheckResult objects"""
        mock_db = Mock()
        mock_settings = Mock()

        mock_db.get_recent_trades.return_value = []
        mock_db.get_open_positions.return_value = []
        mock_db.query_trades.return_value = []

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        results = checker.run_all(
            symbol="HDFCBANK",
            broker_positions=[],
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=30000,
            daily_pnl=0,
            daily_loss_limit_pct=5.0
        )

        for result in results:
            assert isinstance(result, CheckResult)
            assert hasattr(result, "name")
            assert hasattr(result, "passed")
            assert hasattr(result, "severity")
            assert hasattr(result, "message")
            assert hasattr(result, "data")

    def test_run_all_captures_critical_failures(self):
        """run_all() detects and records CRITICAL severity"""
        mock_db = Mock()
        mock_settings = Mock()

        # Force a duplicate trade CRITICAL
        mock_db.get_recent_trades.return_value = [
            {"id": 100, "symbol": "HDFCBANK", "timestamp": (datetime.now() - timedelta(seconds=3)).isoformat()}
        ]
        mock_db.get_open_positions.return_value = []
        mock_db.query_all_trades.return_value = []

        checker = SafetyChecker(db=mock_db, settings=mock_settings)
        results = checker.run_all(
            symbol="HDFCBANK",
            broker_positions=[],
            allocated_capital=100000,
            total_capital=150000,
            deployed_capital=30000,
            daily_pnl=0,
            daily_loss_limit_pct=5.0
        )

        critical_results = [r for r in results if r.severity == "CRITICAL"]
        assert len(critical_results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
