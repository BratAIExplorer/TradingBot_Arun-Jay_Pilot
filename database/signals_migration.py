"""
Signals Database Migration - Phase 1 / Phase 4 foundation.

Creates signals table in trades.db for ML training pipeline.
Non-destructive, idempotent (safe to run multiple times).

Signals log every bot decision (BUY/SKIP/SELL) with full feature snapshot,
enabling offline training in Phase 4.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger("signals_migration")


class SignalsMigration:
    """
    Manages signals table creation and basic persistence.

    Phase 1: Creates table, provides insert/query methods.
    Phase 4: Reads from this table for ML training.
    """

    def __init__(self, db_path: str = "database/trades.db"):
        """Initialize signals migration on existing trades.db."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Use existing trades.db connection (or create if needed)
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row

        # WAL mode for concurrent access (kickstart.py + web_api.py)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self._create_tables()
        logger.info(f"✅ Signals migration initialized: {db_path}")

    def _create_tables(self):
        """Create signals table (idempotent)."""
        cursor = self.conn.cursor()

        try:
            # Main signals table: every bot decision
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,  -- ISO 8601 UTC
                    symbol TEXT NOT NULL,      -- 'RELIANCE', 'AAPL', etc.
                    market TEXT NOT NULL,      -- 'IN' or 'US'
                    action TEXT NOT NULL,      -- 'BUY', 'SKIP', 'SELL'
                    source TEXT NOT NULL,      -- 'BOT' or 'MANUAL'
                    rsi REAL,                  -- RSI at decision time
                    current_price REAL,        -- Stock price at decision time
                    features_json TEXT,        -- JSON: {volume, ma_20, ma_50, ...}
                    execution_id TEXT UNIQUE,  -- Unique ID per decision (UUID)
                    future_return REAL,        -- Return % after N hours (populated during training)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Index: fast lookup for training (market + source + days)
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signals_market_source_date
                ON signals(market, source, timestamp DESC)
            """
            )

            # Index: dedup by execution_id
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_execution_id
                ON signals(execution_id)
            """
            )

            self.conn.commit()
            logger.info("✅ Signals table created (or already exists)")

        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                logger.debug("Signals table already exists")
            else:
                logger.error(f"❌ Failed to create signals table: {e}")
                raise

    def insert_signal(self, signal_data: dict) -> Optional[int]:
        """
        Insert a signal record.

        Args:
            signal_data: Dict with keys from Signal dataclass
                timestamp, symbol, market, action, source, rsi, current_price,
                features (dict), execution_id, [future_return]

        Returns:
            Signal ID (int) if inserted, None on failure.
        """
        import json

        cursor = self.conn.cursor()

        try:
            features_json = json.dumps(signal_data.get("features", {}))

            cursor.execute(
                """
                INSERT INTO signals
                (timestamp, symbol, market, action, source, rsi, current_price,
                 features_json, execution_id, future_return)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal_data.get("timestamp"),
                    signal_data.get("symbol"),
                    signal_data.get("market"),
                    signal_data.get("action"),
                    signal_data.get("source"),
                    signal_data.get("rsi"),
                    signal_data.get("current_price"),
                    features_json,
                    signal_data.get("execution_id"),
                    signal_data.get("future_return"),
                ),
            )
            self.conn.commit()
            signal_id = cursor.lastrowid
            logger.debug(
                f"Signal inserted: {signal_data.get('symbol')} "
                f"{signal_data.get('action')} (ID: {signal_id})"
            )
            return signal_id

        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate signal (execution_id): {signal_data.get('execution_id')}")
            return None
        except Exception as e:
            logger.error(f"Failed to insert signal: {e}")
            return None

    def get_signals(
        self,
        market: Optional[str] = None,
        days_back: int = 30,
        limit: int = 10000,
        source: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve signals for training.

        Args:
            market: Filter by market ('IN', 'US', or None for all)
            days_back: Only signals from past N days
            limit: Max signals to return
            source: Filter by source ('BOT', 'MANUAL', or None for all)

        Returns:
            List of signal dicts ready for training.
        """
        import json
        from datetime import datetime, timedelta

        cursor = self.conn.cursor()

        # Build query
        where_clauses = []
        params = []

        # Date filter
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        where_clauses.append("timestamp > ?")
        params.append(cutoff)

        # Market filter
        if market:
            where_clauses.append("market = ?")
            params.append(market.upper())

        # Source filter
        if source:
            where_clauses.append("source = ?")
            params.append(source.upper())

        where_sql = " AND ".join(where_clauses)

        try:
            cursor.execute(
                f"""
                SELECT id, timestamp, symbol, market, action, source, rsi,
                       current_price, features_json, execution_id, future_return
                FROM signals
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                params + [limit],
            )

            signals = []
            for row in cursor.fetchall():
                signal_dict = dict(row)
                # Parse features from JSON
                signal_dict["features"] = json.loads(row["features_json"] or "{}")
                signals.append(signal_dict)

            logger.info(
                f"Retrieved {len(signals)} signals for training "
                f"(market={market}, days={days_back}, source={source})"
            )
            return signals

        except Exception as e:
            logger.error(f"Failed to retrieve signals: {e}")
            return []

    def count_signals(
        self, market: Optional[str] = None, source: Optional[str] = None
    ) -> int:
        """Count total signals (for monitoring)."""
        cursor = self.conn.cursor()

        where_clauses = []
        params = []

        if market:
            where_clauses.append("market = ?")
            params.append(market.upper())

        if source:
            where_clauses.append("source = ?")
            params.append(source.upper())

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        try:
            cursor.execute(f"SELECT COUNT(*) FROM signals WHERE {where_sql}", params)
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Failed to count signals: {e}")
            return 0

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Convenience function for one-shot migration
def run_signals_migration(db_path: str = "database/trades.db") -> bool:
    """
    Run signals table creation (idempotent).

    Can be called multiple times safely.

    Args:
        db_path: Path to trades.db

    Returns:
        True if successful, False otherwise.
    """
    try:
        migration = SignalsMigration(db_path)
        migration.close()
        return True
    except Exception as e:
        logger.error(f"Signals migration failed: {e}")
        return False


if __name__ == "__main__":
    # Test: python -m database.signals_migration
    logging.basicConfig(level=logging.DEBUG)
    success = run_signals_migration()
    print(f"✅ Migration {'succeeded' if success else 'failed'}")
