"""
Signal Logger - captures bot decisions for ML training.

Every decision the bot evaluates (RSI check, volume check, etc.) is logged
with full feature snapshot. This enables offline training later.

Phase 1: Log-only (no predictions). Phase 4: ML training on accumulated signals.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """
    Represents a single bot decision signal.

    Attributes:
        timestamp: When the decision was made (ISO 8601)
        symbol: Stock symbol (e.g., 'RELIANCE', 'AAPL')
        market: Market code ('IN' for India, 'US' for USA)
        action: The action the bot decided ('BUY', 'SKIP', 'SELL')
        source: 'BOT' (bot decided) or 'MANUAL' (user entered, bot learning from)
        rsi: RSI value at time of decision
        current_price: Stock price at time of decision
        features: Full feature dict (RSI, volume, MA, etc.) for training
        execution_id: Unique ID for this decision (for auditing)
        future_return: Return % after N hours (populated later during training)
    """

    timestamp: str  # ISO 8601
    symbol: str
    market: str
    action: str  # 'BUY', 'SKIP', 'SELL'
    source: str  # 'BOT' or 'MANUAL'
    rsi: float
    current_price: float
    features: dict[str, Any]
    execution_id: str
    future_return: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for DB persistence."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON for storage."""
        data = asdict(self)
        # Serialize nested dicts/lists as JSON string
        data["features"] = json.dumps(data["features"])
        return json.dumps(data, default=str)


class SignalLogger:
    """
    Phase 1 signal capture for ML training pipeline.

    Logs every bot decision (BUY/SKIP/SELL) with full feature snapshot.
    Accumulates data for offline ML training in Phase 4.

    Usage:
        logger = SignalLogger(db)
        logger.log_decision(
            symbol='RELIANCE',
            market='IN',
            action='BUY',
            source='BOT',
            rsi=28.5,
            current_price=2500.0,
            features={'volume': 15000000, 'ma_20': 2480.0, ...}
        )
    """

    def __init__(self, db_connection: Any = None):
        """
        Initialize signal logger.

        Args:
            db_connection: Database connection (trades_db.TradesDatabase).
                          If None, logs to console only (testing).
        """
        self.db = db_connection
        self._log = logging.getLogger(__name__)

    def log_decision(
        self,
        symbol: str,
        market: str,
        action: str,
        rsi: float,
        current_price: float,
        features: dict[str, Any],
        source: str = "BOT",
        execution_id: Optional[str] = None,
    ) -> Optional[int]:
        """
        Log a bot decision signal.

        Args:
            symbol: Stock symbol
            market: Market code ('IN', 'US')
            action: Decision action ('BUY', 'SKIP', 'SELL')
            rsi: RSI value at decision time
            current_price: Stock price at decision time
            features: Full feature dict (volume, moving averages, etc.)
            source: 'BOT' or 'MANUAL' (defaults to 'BOT')
            execution_id: Unique ID for this decision (auto-generated if None)

        Returns:
            Signal ID (int) if successfully persisted, None otherwise.
        """
        import uuid

        if execution_id is None:
            execution_id = str(uuid.uuid4())[:8]

        signal = Signal(
            timestamp=datetime.utcnow().isoformat(),
            symbol=symbol.upper(),
            market=market.upper(),
            action=action.upper(),
            source=source.upper(),
            rsi=float(rsi),
            current_price=float(current_price),
            features=features or {},
            execution_id=execution_id,
        )

        # Attempt DB persistence
        if self.db:
            try:
                signal_id = self.db.insert_signal(signal.to_dict())
                self._log.debug(
                    f"Signal logged: {symbol} {action} (ID: {signal_id}, exec: {execution_id})"
                )
                return signal_id
            except Exception as e:
                self._log.error(f"Failed to log signal for {symbol}: {e}")
                # Fall through to console log (best-effort)

        # Fallback: console log
        self._log.info(
            f"Signal: {symbol} {action} RSI={rsi:.1f} Price={current_price} ({source})"
        )
        return None

    def log_manual_trade(
        self,
        symbol: str,
        market: str,
        action: str,
        price: float,
        quantity: int,
        features: dict[str, Any],
        execution_id: Optional[str] = None,
    ) -> Optional[int]:
        """
        Log a manual trade (user-entered, bot learns from it).

        Used to tag user trades for feature capture (learning signal).

        Args:
            symbol: Stock symbol
            market: Market code
            action: 'BUY' or 'SELL'
            price: Execution price
            quantity: Shares traded
            features: Feature snapshot at trade time
            execution_id: Trade ID (e.g., order_id from broker)

        Returns:
            Signal ID if persisted, None otherwise.
        """
        features_with_metadata = {
            **features,
            "trade_quantity": quantity,
            "trade_price": price,
        }

        return self.log_decision(
            symbol=symbol,
            market=market,
            action=action,
            rsi=features.get("rsi", 0.0),
            current_price=price,
            features=features_with_metadata,
            source="MANUAL",
            execution_id=execution_id,
        )

    def get_signals_for_training(
        self,
        market: Optional[str] = None,
        days: int = 30,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        """
        Retrieve accumulated signals for ML training (Phase 4).

        Args:
            market: Filter by market ('IN', 'US', or None for all)
            days: Look back N days
            limit: Max signals to return

        Returns:
            List of signal dicts ready for feature engineering.
        """
        if not self.db:
            self._log.warning("No DB connection; cannot retrieve signals for training")
            return []

        try:
            signals = self.db.get_signals(
                market=market, days_back=days, limit=limit
            )
            self._log.info(f"Retrieved {len(signals)} signals for training")
            return signals
        except Exception as e:
            self._log.error(f"Failed to retrieve signals: {e}")
            return []
