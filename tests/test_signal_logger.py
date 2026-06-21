"""
Test signal logger - Phase 1 data capture for ML training.

Tests that:
1. Signals are logged with full feature snapshots
2. Market column differentiates India vs US
3. Source column tracks BOT vs MANUAL trades
4. Signals can be retrieved for training
"""

import pytest
from datetime import datetime
from ml.signal_logger import SignalLogger, Signal
from database.trades_db import TradesDatabase


class TestSignal:
    """Test Signal dataclass."""

    def test_signal_creation(self):
        """Signal dataclass stores all decision metadata."""
        signal = Signal(
            timestamp="2025-01-01T12:00:00",
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            source="BOT",
            rsi=28.5,
            current_price=2500.0,
            features={"volume": 1500000, "ma_20": 2480.0},
            execution_id="exec_001",
        )

        assert signal.symbol == "RELIANCE"
        assert signal.market == "IN"
        assert signal.action == "BUY"
        assert signal.source == "BOT"
        assert signal.rsi == 28.5
        assert signal.features["volume"] == 1500000

    def test_signal_to_dict(self):
        """Signal converts to dict for DB insertion."""
        signal = Signal(
            timestamp="2025-01-01T12:00:00",
            symbol="AAPL",
            market="US",
            action="SKIP",
            source="BOT",
            rsi=65.0,
            current_price=150.0,
            features={"volume": 50000000},
            execution_id="exec_us_001",
        )

        signal_dict = signal.to_dict()
        assert isinstance(signal_dict, dict)
        assert signal_dict["symbol"] == "AAPL"
        assert signal_dict["market"] == "US"


class TestSignalLogger:
    """Test SignalLogger class."""

    @pytest.fixture
    def db(self):
        """In-memory test database."""
        db_instance = TradesDatabase(":memory:")
        yield db_instance

    @pytest.fixture
    def logger(self, db):
        """Signal logger with in-memory DB."""
        return SignalLogger(db)

    def test_log_decision_bot_buy(self, logger, db):
        """Log a BUY decision from the bot."""
        signal_id = logger.log_decision(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            rsi=28.5,
            current_price=2500.0,
            features={"volume": 1500000, "ma_20": 2480.0},
            source="BOT",
            execution_id="exec_001",
        )

        assert signal_id is not None
        assert isinstance(signal_id, int)

        # Verify DB persistence
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["symbol"] == "RELIANCE"
        assert row["action"] == "BUY"
        assert row["source"] == "BOT"

    def test_log_decision_manual_trade(self, logger, db):
        """Log a manual trade (user-entered)."""
        signal_id = logger.log_decision(
            symbol="INFY",
            market="IN",
            action="BUY",
            rsi=72.0,
            current_price=1800.0,
            features={"volume": 5000000},
            source="MANUAL",
            execution_id="manual_001",
        )

        assert signal_id is not None

        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row["source"] == "MANUAL"

    def test_log_decision_us_market(self, logger, db):
        """Log a decision for US market."""
        signal_id = logger.log_decision(
            symbol="AAPL",
            market="US",
            action="BUY",
            rsi=42.0,
            current_price=150.0,
            features={"volume": 50000000, "ma_20": 148.0},
            source="BOT",
            execution_id="us_001",
        )

        assert signal_id is not None

        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row["market"] == "US"
        assert row["symbol"] == "AAPL"

    def test_log_decision_skip_action(self, logger, db):
        """Log a SKIP decision (no trade)."""
        signal_id = logger.log_decision(
            symbol="HDFCBANK",
            market="IN",
            action="SKIP",
            rsi=55.0,
            current_price=1500.0,
            features={"volume": 2000000},
            source="BOT",
            execution_id="skip_001",
        )

        assert signal_id is not None

        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row["action"] == "SKIP"

    def test_duplicate_execution_id_rejected(self, logger, db):
        """Duplicate execution_id is rejected (already traded)."""
        exec_id = "unique_001"

        # First insertion succeeds
        signal_id_1 = logger.log_decision(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            rsi=30.0,
            current_price=2500.0,
            features={},
            execution_id=exec_id,
        )
        assert signal_id_1 is not None

        # Duplicate insertion fails (returns None)
        signal_id_2 = logger.log_decision(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            rsi=30.0,
            current_price=2500.0,
            features={},
            execution_id=exec_id,
        )
        assert signal_id_2 is None

    def test_execution_id_auto_generated_if_none(self, logger, db):
        """Execution ID is auto-generated if not provided."""
        signal_id = logger.log_decision(
            symbol="TCS",
            market="IN",
            action="BUY",
            rsi=35.0,
            current_price=3500.0,
            features={},
            execution_id=None,  # Auto-generate
        )

        assert signal_id is not None

        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row["execution_id"] is not None
        assert len(row["execution_id"]) > 0

    def test_get_signals_for_training_all(self, logger, db):
        """Retrieve all signals accumulated."""
        # Log several signals
        logger.log_decision("RELIANCE", "IN", "BUY", 28.0, 2500.0, {}, "BOT", "e1")
        logger.log_decision("INFY", "IN", "SKIP", 55.0, 1800.0, {}, "BOT", "e2")
        logger.log_decision("AAPL", "US", "BUY", 42.0, 150.0, {}, "BOT", "e3")

        signals = logger.get_signals_for_training()
        assert len(signals) >= 3

    def test_get_signals_filter_by_market(self, logger, db):
        """Retrieve signals for a specific market."""
        logger.log_decision("RELIANCE", "IN", "BUY", 28.0, 2500.0, {}, "BOT", "in1")
        logger.log_decision("INFY", "IN", "BUY", 30.0, 1800.0, {}, "BOT", "in2")
        logger.log_decision("AAPL", "US", "BUY", 42.0, 150.0, {}, "BOT", "us1")

        # Get only India signals
        in_signals = logger.get_signals_for_training(market="IN")
        assert all(s["market"] == "IN" for s in in_signals)

        # Get only US signals
        us_signals = logger.get_signals_for_training(market="US")
        assert all(s["market"] == "US" for s in us_signals)

    def test_get_signals_filter_by_source(self, db):
        """Retrieve signals by source (BOT vs MANUAL)."""
        logger = SignalLogger(db)

        logger.log_decision("RELIANCE", "IN", "BUY", 28.0, 2500.0, {}, "BOT", "bot1")
        logger.log_decision("INFY", "IN", "BUY", 30.0, 1800.0, {}, "BOT", "bot2")
        logger.log_decision("TCS", "IN", "BUY", 35.0, 3500.0, {}, "MANUAL", "manual1")

        # Get only BOT signals
        bot_signals = db.get_signals(source="BOT")
        assert all(s["source"] == "BOT" for s in bot_signals)

        # Get only MANUAL signals
        manual_signals = db.get_signals(source="MANUAL")
        assert all(s["source"] == "MANUAL" for s in manual_signals)

    def test_features_json_persisted_and_parsed(self, logger, db):
        """Features dict is JSON-persisted and parsed on retrieval."""
        features = {"volume": 1500000, "ma_20": 2480.0, "ma_50": 2490.0}

        signal_id = logger.log_decision(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            rsi=28.0,
            current_price=2500.0,
            features=features,
            execution_id="feat_001",
        )

        # Retrieve from DB
        signals = db.get_signals(limit=1)
        assert len(signals) > 0
        retrieved = signals[0]
        assert retrieved["features"]["volume"] == 1500000
        assert retrieved["features"]["ma_20"] == 2480.0

    def test_signal_timestamp_iso_format(self, logger, db):
        """Signal timestamp is stored in ISO 8601 format."""
        signal_id = logger.log_decision(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            rsi=28.0,
            current_price=2500.0,
            features={},
            execution_id="ts_001",
        )

        cursor = db.conn.cursor()
        cursor.execute("SELECT timestamp FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        timestamp_str = row["timestamp"]

        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed, datetime)

    def test_log_manual_trade_convenience_method(self, logger, db):
        """Use log_manual_trade convenience method."""
        signal_id = logger.log_manual_trade(
            symbol="RELIANCE",
            market="IN",
            action="BUY",
            price=2500.0,
            quantity=10,
            features={"rsi": 28.0, "volume": 1500000},
            execution_id="user_order_001",
        )

        assert signal_id is not None

        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        assert row["source"] == "MANUAL"
        assert row["action"] == "BUY"
