"""
Analytics Database Migration - Phase 1
Non-destructive creation of trade analysis tables.
Can be run multiple times safely (idempotent).

This module creates a NEW database file (trades_analysis.db) for analytics,
WITHOUT modifying the existing trades.db. All data is linked by (symbol, timestamp).
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger("analytics_migration")


class AnalyticsDatabase:
    """
    Separate database for trade analysis and market context.
    Designed to complement trades.db without modifying it.
    """

    def __init__(self, db_path: str = "database/trades_analysis.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Create connection with WAL mode for concurrency safety
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row

        # Enable WAL mode for concurrent access with kickstart.py
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self._create_tables()
        logger.info(f"✅ Analytics database initialized: {db_path}")

    def _create_tables(self):
        """Create analytics tables (idempotent - safe to call multiple times)"""
        cursor = self.conn.cursor()

        try:
            # Table 1: trade_analysis - Detailed analysis of each trade
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- Link to original trade
                    trade_id INTEGER,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,

                    -- Trade Action & Context
                    action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
                    reason TEXT,                      -- "RSI < 35", "Hit target", "Stop-loss", etc.
                    exit_reason TEXT,                 -- For SELL: why exited? (NEW)

                    -- Position Sizing Parameters (NEW)
                    quantity INTEGER,                 -- How many shares (NEW)
                    position_size_mode TEXT,          -- 'FIXED' or 'DYNAMIC' (NEW)
                    base_position_size INTEGER,       -- Base before adjustment (NEW)
                    volatility_adjustment_pct REAL,   -- Size multiplier based on vol (NEW)

                    -- Technical Parameters Used
                    timeframe TEXT,                   -- '5T', '15T', '30T', '1H' etc (NEW)
                    rsi_value REAL,
                    rsi_threshold_buy REAL,
                    rsi_threshold_sell REAL,

                    -- Additional Technical Indicators (NEW - moved from trades table)
                    atr REAL,                         -- Average True Range (volatility measure)
                    adx REAL,                         -- Average Directional Index (trend strength)
                    macd_value REAL,                  -- MACD line value
                    macd_signal REAL,                 -- MACD signal line
                    macd_histogram REAL,              -- MACD histogram

                    -- Market Context at Entry
                    entry_market_regime TEXT,         -- Market regime at BUY
                    entry_nifty_50_change_pct REAL,
                    entry_volatility REAL,            -- Volatility at entry
                    entry_sector_performance TEXT,    -- JSON: sector performance at entry

                    -- Market Context at Exit (NEW - for SELL analysis)
                    exit_market_regime TEXT,          -- Market regime at SELL (NEW)
                    exit_nifty_50_change_pct REAL,    -- Nifty change at SELL (NEW)
                    exit_volatility REAL,             -- Volatility at SELL (NEW)
                    exit_sector_performance TEXT,     -- JSON: sector performance at exit (NEW)
                    market_regime_changed TEXT,       -- 'YES'/'NO' - did regime change? (NEW)

                    -- Strategy Info
                    strategy TEXT,
                    parameters_used TEXT,             -- JSON: all params used
                    confidence_level TEXT,            -- HIGH/MEDIUM/LOW

                    -- Trade Outcome
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    pnl_pct REAL,
                    hold_duration_minutes INTEGER,    -- Minutes held (NEW)
                    hold_duration_bars INTEGER,       -- Number of candles held (NEW)

                    -- Time Analysis (NEW)
                    entry_hour INTEGER,               -- Hour of entry (0-23)
                    entry_day_of_week TEXT,           -- 'Monday', 'Tuesday', etc.
                    exit_hour INTEGER,                -- Hour of exit (for SELL)
                    exit_day_of_week TEXT,            -- Day of exit (for SELL)

                    -- Tags for pattern detection
                    tags TEXT,                        -- JSON array

                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    analyzed_at TEXT,

                    -- Composite unique constraint
                    UNIQUE(symbol, timestamp)
                )
            """)

            # Table 2: market_snapshot - Market state snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    timestamp TEXT NOT NULL UNIQUE,

                    -- Market Indexes
                    nifty_50_value REAL,
                    nifty_50_change_pct REAL,
                    nifty_500_change_pct REAL,
                    bank_nifty_change_pct REAL,

                    -- Volatility
                    market_volatility REAL,           -- VIX-like (0-100)
                    market_regime TEXT,               -- UPTREND/DOWNTREND/SIDEWAYS/OVERBOUGHT/OVERSOLD

                    -- Sectors
                    sector_performance TEXT,          -- JSON
                    top_gainers TEXT,                 -- JSON
                    top_losers TEXT,                  -- JSON

                    -- Events
                    upcoming_events TEXT,             -- JSON

                    -- Market Quality
                    advance_decline_ratio REAL,
                    market_breadth TEXT,              -- POSITIVE/NEUTRAL/NEGATIVE

                    data_source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table 3: recommendations - AI advisor recommendations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    symbol TEXT,
                    signal TEXT CHECK(signal IN ('BUY', 'SELL', 'HOLD', 'AVOID', 'TWEAK_PARAMS')),
                    reason TEXT,

                    -- Confidence metrics
                    confluence_score REAL,            -- 0-100
                    confidence REAL,                  -- 0-1

                    -- Recommendation details
                    recommended_action TEXT,
                    stop_loss_pct REAL,
                    profit_target_pct REAL,
                    why_we_like_it TEXT,              -- Detailed explanation

                    -- Timing
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,                  -- When recommendation is no longer valid
                    status TEXT DEFAULT 'NEW' CHECK(status IN ('NEW', 'ACCEPTED', 'REJECTED', 'EXECUTED')),

                    -- Feedback
                    trader_feedback TEXT,
                    feedback_at TEXT
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ta_symbol_timestamp
                ON trade_analysis(symbol, timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ta_created_at
                ON trade_analysis(created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ms_timestamp
                ON market_snapshot(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rec_symbol_created
                ON recommendations(symbol, created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rec_status
                ON recommendations(status)
            """)

            self.conn.commit()
            logger.info("✅ All analytics tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error creating analytics tables: {e}")
            raise

    def insert_trade_analysis(
        self,
        symbol: str,
        timestamp: str,
        action: str,
        trade_id: Optional[int] = None,
        reason: Optional[str] = None,
        exit_reason: Optional[str] = None,
        # Position Sizing
        quantity: Optional[int] = None,
        position_size_mode: Optional[str] = None,
        base_position_size: Optional[int] = None,
        volatility_adjustment_pct: Optional[float] = None,
        # Technical Parameters
        timeframe: Optional[str] = None,
        rsi_value: Optional[float] = None,
        rsi_threshold_buy: Optional[float] = None,
        rsi_threshold_sell: Optional[float] = None,
        atr: Optional[float] = None,
        adx: Optional[float] = None,
        macd_value: Optional[float] = None,
        macd_signal: Optional[float] = None,
        macd_histogram: Optional[float] = None,
        # Market Context at Entry
        entry_market_regime: Optional[str] = None,
        entry_nifty_50_change_pct: Optional[float] = None,
        entry_volatility: Optional[float] = None,
        entry_sector_performance: Optional[Dict] = None,
        # Market Context at Exit
        exit_market_regime: Optional[str] = None,
        exit_nifty_50_change_pct: Optional[float] = None,
        exit_volatility: Optional[float] = None,
        exit_sector_performance: Optional[Dict] = None,
        market_regime_changed: Optional[str] = None,
        # Strategy & Outcome
        strategy: Optional[str] = None,
        parameters_used: Optional[Dict] = None,
        confidence_level: Optional[str] = None,
        entry_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        pnl_pct: Optional[float] = None,
        hold_duration_minutes: Optional[int] = None,
        hold_duration_bars: Optional[int] = None,
        # Time Analysis
        entry_hour: Optional[int] = None,
        entry_day_of_week: Optional[str] = None,
        exit_hour: Optional[int] = None,
        exit_day_of_week: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Insert trade analysis record. Returns ID or -1 if duplicate.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trade_analysis (
                    trade_id, symbol, timestamp, action, reason, exit_reason,
                    quantity, position_size_mode, base_position_size, volatility_adjustment_pct,
                    timeframe, rsi_value, rsi_threshold_buy, rsi_threshold_sell,
                    atr, adx, macd_value, macd_signal, macd_histogram,
                    entry_market_regime, entry_nifty_50_change_pct, entry_volatility, entry_sector_performance,
                    exit_market_regime, exit_nifty_50_change_pct, exit_volatility, exit_sector_performance,
                    market_regime_changed,
                    strategy, parameters_used, confidence_level,
                    entry_price, exit_price, pnl, pnl_pct,
                    hold_duration_minutes, hold_duration_bars,
                    entry_hour, entry_day_of_week, exit_hour, exit_day_of_week,
                    tags
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?
                )
            """, (
                trade_id, symbol, timestamp, action, reason, exit_reason,
                quantity, position_size_mode, base_position_size, volatility_adjustment_pct,
                timeframe, rsi_value, rsi_threshold_buy, rsi_threshold_sell,
                atr, adx, macd_value, macd_signal, macd_histogram,
                entry_market_regime, entry_nifty_50_change_pct, entry_volatility,
                json.dumps(entry_sector_performance) if entry_sector_performance else None,
                exit_market_regime, exit_nifty_50_change_pct, exit_volatility,
                json.dumps(exit_sector_performance) if exit_sector_performance else None,
                market_regime_changed,
                strategy, json.dumps(parameters_used) if parameters_used else None,
                confidence_level,
                entry_price, exit_price, pnl, pnl_pct,
                hold_duration_minutes, hold_duration_bars,
                entry_hour, entry_day_of_week, exit_hour, exit_day_of_week,
                json.dumps(tags) if tags else None
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                return -1  # Duplicate, not an error
            logger.error(f"❌ Error inserting trade analysis: {e}")
            raise

    def insert_market_snapshot(
        self,
        timestamp: str,
        nifty_50_value: Optional[float] = None,
        nifty_50_change_pct: Optional[float] = None,
        nifty_500_change_pct: Optional[float] = None,
        bank_nifty_change_pct: Optional[float] = None,
        market_volatility: Optional[float] = None,
        market_regime: Optional[str] = None,
        sector_performance: Optional[Dict] = None,
        top_gainers: Optional[List] = None,
        top_losers: Optional[List] = None,
        upcoming_events: Optional[List] = None,
        advance_decline_ratio: Optional[float] = None,
        market_breadth: Optional[str] = None,
        data_source: str = "manual",
    ) -> int:
        """Insert market snapshot. Returns ID or -1 if duplicate timestamp."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO market_snapshot (
                    timestamp, nifty_50_value, nifty_50_change_pct,
                    nifty_500_change_pct, bank_nifty_change_pct,
                    market_volatility, market_regime,
                    sector_performance, top_gainers, top_losers,
                    upcoming_events, advance_decline_ratio,
                    market_breadth, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, nifty_50_value, nifty_50_change_pct,
                nifty_500_change_pct, bank_nifty_change_pct,
                market_volatility, market_regime,
                json.dumps(sector_performance) if sector_performance else None,
                json.dumps(top_gainers) if top_gainers else None,
                json.dumps(top_losers) if top_losers else None,
                json.dumps(upcoming_events) if upcoming_events else None,
                advance_decline_ratio, market_breadth, data_source
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1  # Duplicate timestamp

    def get_trade_analysis(self, symbol: str, days: int = 7) -> List[Dict]:
        """Fetch trade analysis for a symbol (last N days)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trade_analysis
            WHERE symbol = ? AND datetime(created_at) >= datetime('now', ?)
            ORDER BY created_at DESC
        """, (symbol, f"-{days} days"))
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_market_snapshots(self, limit: int = 50) -> List[Dict]:
        """Fetch recent market snapshots"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM market_snapshot
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def insert_recommendation(
        self,
        symbol: str,
        signal: str,
        reason: str,
        confluence_score: float,
        confidence: float,
        recommended_action: Optional[str] = None,
        stop_loss_pct: Optional[float] = None,
        profit_target_pct: Optional[float] = None,
        why_we_like_it: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> int:
        """Insert AI recommendation"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO recommendations (
                symbol, signal, reason, confluence_score, confidence,
                recommended_action, stop_loss_pct, profit_target_pct,
                why_we_like_it, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, signal, reason, confluence_score, confidence,
            recommended_action, stop_loss_pct, profit_target_pct,
            why_we_like_it, expires_at
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_recommendations(
        self,
        symbol: Optional[str] = None,
        min_confidence: float = 0.6,
        signal: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Fetch active recommendations with filters"""
        query = "SELECT * FROM recommendations WHERE status = 'NEW' AND confidence >= ?"
        params = [min_confidence]

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if signal:
            query += " AND signal = ?"
            params.append(signal)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class AnalyticsMigration:
    """
    Migration runner with dry-run mode.
    Backfills analytics from existing trades.
    """

    def __init__(self, trades_db_path: str = "database/trades.db",
                 analytics_db_path: str = "database/trades_analysis.db"):
        self.trades_db_path = trades_db_path
        self.analytics_db_path = analytics_db_path

    def run(self, dry_run: bool = True) -> Dict[str, any]:
        """
        Execute migration. Returns result summary.

        Args:
            dry_run: If True, don't modify databases, just report what would happen

        Returns:
            {
                'status': 'success' | 'error',
                'trades_analyzed': int,
                'analysis_created': int,
                'errors': [str],
                'took_seconds': float
            }
        """
        import time
        start = time.time()
        result = {
            'status': 'success',
            'trades_analyzed': 0,
            'analysis_created': 0,
            'errors': [],
            'dry_run': dry_run,
            'took_seconds': 0
        }

        try:
            # Connect to existing trades database
            trades_conn = sqlite3.connect(self.trades_db_path)
            trades_conn.row_factory = sqlite3.Row
            trades_cursor = trades_conn.cursor()

            # Count existing trades
            trades_cursor.execute("SELECT COUNT(*) as cnt FROM trades")
            total_trades = trades_cursor.fetchone()['cnt']
            result['trades_analyzed'] = total_trades

            if total_trades == 0:
                logger.warning("⚠️ No trades found to backfill")
                return result

            if not dry_run:
                # Create analytics database
                analytics_db = AnalyticsDatabase(self.analytics_db_path)

            # Fetch all trades for analysis
            trades_cursor.execute("""
                SELECT id, symbol, timestamp, action, price, strategy, reason,
                       rsi, market_trend, atr, adx,
                       macd_val, macd_signal, macd_hist, pnl_net, pnl_pct_net
                FROM trades
                ORDER BY timestamp ASC
            """)

            trades = trades_cursor.fetchall()

            for idx, trade in enumerate(trades):
                trade_dict = dict(trade)

                if not dry_run:
                    try:
                        analysis_id = analytics_db.insert_trade_analysis(
                            symbol=trade_dict['symbol'],
                            timestamp=trade_dict['timestamp'],
                            action=trade_dict['action'],
                            trade_id=trade_dict['id'],
                            rsi_value=trade_dict.get('rsi'),
                            reason=trade_dict.get('reason'),
                            strategy=trade_dict.get('strategy'),
                            entry_price=trade_dict.get('price'),
                            pnl=trade_dict.get('pnl_net'),
                            pnl_pct=trade_dict.get('pnl_pct_net'),
                            confidence_level='MEDIUM',  # Default for backfill
                            tags=['backfill']
                        )

                        if analysis_id > 0:
                            result['analysis_created'] += 1
                    except Exception as e:
                        result['errors'].append(f"Trade {trade_dict['id']}: {str(e)}")
                        logger.error(f"❌ Error analyzing trade {trade_dict['id']}: {e}")

            if not dry_run:
                analytics_db.close()

            trades_conn.close()

            # Verify no data loss
            if not dry_run:
                assert result['analysis_created'] == total_trades, \
                    f"Data loss detected! Analyzed {result['analysis_created']} but had {total_trades} trades"

            result['took_seconds'] = time.time() - start
            logger.info(f"✅ Migration complete: {result['analysis_created']} trades analyzed in {result['took_seconds']:.2f}s")

        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))
            logger.error(f"❌ Migration failed: {e}")

        return result


if __name__ == "__main__":
    """Test migration with dry-run first"""
    logging.basicConfig(level=logging.INFO)

    # Dry-run: See what would happen
    print("\n🔍 DRY-RUN: Testing migration...")
    migration = AnalyticsMigration()
    dry_result = migration.run(dry_run=True)
    print(json.dumps(dry_result, indent=2))

    # If dry-run successful, run for real
    if dry_result['status'] == 'success':
        print("\n✅ Dry-run successful. Running migration...")
        real_result = migration.run(dry_run=False)
        print(json.dumps(real_result, indent=2))
    else:
        print("\n❌ Dry-run failed. Fix errors before running migration.")
