"""
SQLite Database Manager for ARUN Trading Bot
Handles all trade logging and querying
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd


class TradesDatabase:
    """
    Simple SQLite database for logging trades
    """
    
    def __init__(self, db_path: str = "database/trades.db"):
        self.db_path = db_path

        # Create database directory if it doesn't exist (skip for :memory:)
        if db_path != ":memory:" and os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        # self.cursor removed to prevent recursive cursor usage

        # Create tables
        self._create_tables()
        self._run_migrations()
        print(f"Database initialized: {db_path} (v2 with get_recent_trades)")

    @property
    def connection(self):
        """Backward compatibility property for tests that use db.connection"""
        return self.conn
    
    def _create_tables(self):
        """
        Create trades table if it doesn't exist
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')),
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    
                    -- Fee breakdown
                    gross_amount REAL NOT NULL,
                    brokerage_fee REAL DEFAULT 0,
                    stt_fee REAL DEFAULT 0,
                    exchange_fee REAL DEFAULT 0,
                    gst_fee REAL DEFAULT 0,
                    sebi_fee REAL DEFAULT 0,
                    stamp_duty_fee REAL DEFAULT 0,
                    total_fees REAL DEFAULT 0,
                    net_amount REAL NOT NULL,
                    
                    -- Trade metadata
                    strategy TEXT,
                    pnl_gross REAL,
                    pnl_net REAL,
                    pnl_pct_gross REAL,
                    pnl_pct_net REAL,
                    reason TEXT,
                    broker TEXT,
                    source TEXT DEFAULT 'BOT', -- 'BOT' or 'MANUAL'
                    
                    -- Additional fields
                    entry_timestamp TEXT,
                    hold_duration_days REAL
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON trades(symbol, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_action_timestamp 
                ON trades(action, timestamp)
            """)

            # Create system_control table for inter-process communication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_control (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            # Initialize default RUNNING state if not exists
            cursor.execute("INSERT OR IGNORE INTO system_control (key, value, updated_at) VALUES ('bot_status', 'RUNNING', datetime('now'))")

            # Create alerts table for v2.6.0 alert system
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL CHECK(severity IN ('INFO', 'WARN', 'CRITICAL')),
                    symbol TEXT,
                    message TEXT NOT NULL,
                    dedup_key TEXT NOT NULL,
                    delivered_email INTEGER DEFAULT 0,
                    acknowledged INTEGER DEFAULT 0
                )
            """)

            # Create UNIQUE index on dedup_key + date for deduplication
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS alert_dedup_idx
                ON alerts(dedup_key, date(timestamp))
            """)

            # Create safety_checks_log table for audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS safety_checks_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    check_name TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PASS', 'FAIL', 'WARNING')),
                    details TEXT
                )
            """)

            self.conn.commit()
        finally:
            cursor.close()

    def set_control_flag(self, key: str, value: str):
        """Set a control flag in the DB"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO system_control (key, value, updated_at) 
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET value=?, updated_at=datetime('now')
            """, (key, value, value))
            self.conn.commit()
        finally:
            cursor.close()

    def get_control_flag(self, key: str, default: str = None) -> str:
        """Get a control flag from the DB"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT value FROM system_control WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
        finally:
            cursor.close()

    def _run_migrations(self):
        """
        Run schema migrations for existing databases
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(trades)")
            columns = [info[1] for info in cursor.fetchall()]

            if 'broker' not in columns:
                print("Migrating database: Adding 'broker' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN broker TEXT DEFAULT 'mstock'")
                self.conn.commit()

            if 'source' not in columns:
                print("Migrating database: Adding 'source' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN source TEXT DEFAULT 'BOT'")
                self.conn.commit()
                print("Migration 'source' complete")

            if 'rsi' not in columns:
                print("Migrating database: Adding 'rsi' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN rsi REAL")
                self.conn.commit()
                print("Migration 'rsi' complete")

            if 'market_trend' not in columns:
                print("Migrating database: Adding 'market_trend' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN market_trend REAL")
                self.conn.commit()
                
            if 'atr' not in columns:
                print("Migrating database: Adding 'atr' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN atr REAL")
                self.conn.commit()
                
            if 'adx' not in columns:
                print("Migrating database: Adding 'adx' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN adx REAL")
                self.conn.commit()

            if 'macd_hist' not in columns:
                print("Migrating database: Adding 'macd' columns...")
                cursor.execute("ALTER TABLE trades ADD COLUMN macd_val REAL")
                cursor.execute("ALTER TABLE trades ADD COLUMN macd_signal REAL")
                cursor.execute("ALTER TABLE trades ADD COLUMN macd_hist REAL")
                self.conn.commit()
                print("Migration 'analytics' complete")

            # Ensure alerts table exists (v2.6.0)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
            if not cursor.fetchone():
                print("Migrating database: Creating 'alerts' table...")
                cursor.execute("""
                    CREATE TABLE alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL CHECK(severity IN ('INFO', 'WARN', 'CRITICAL')),
                        symbol TEXT,
                        message TEXT NOT NULL,
                        dedup_key TEXT NOT NULL,
                        delivered_email INTEGER DEFAULT 0,
                        acknowledged INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX alert_dedup_idx
                    ON alerts(dedup_key, date(timestamp))
                """)
                self.conn.commit()
                print("Migration 'alerts' complete")

            # Ensure safety_checks_log table exists (v2.6.0)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='safety_checks_log'")
            if not cursor.fetchone():
                print("Migrating database: Creating 'safety_checks_log' table...")
                cursor.execute("""
                    CREATE TABLE safety_checks_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        check_name TEXT NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('PASS', 'FAIL', 'WARNING')),
                        details TEXT
                    )
                """)
                self.conn.commit()
                print("Migration 'safety_checks_log' complete")

            # Phase 1: Add 'market' column to trades table (for dual-market support)
            cursor.execute("PRAGMA table_info(trades)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'market' not in columns:
                print("Migrating database: Adding 'market' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN market TEXT DEFAULT 'IN'")
                self.conn.commit()
                print("Migration 'market' complete")

            # Phase 1: Create signals table for ML training (from signals_migration.py)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='signals'")
            if not cursor.fetchone():
                print("Migrating database: Creating 'signals' table...")
                cursor.execute("""
                    CREATE TABLE signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        market TEXT NOT NULL,
                        action TEXT NOT NULL,
                        source TEXT NOT NULL,
                        rsi REAL,
                        current_price REAL,
                        features_json TEXT,
                        execution_id TEXT UNIQUE,
                        future_return REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_signals_market_source_date
                    ON signals(market, source, timestamp DESC)
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_execution_id
                    ON signals(execution_id)
                """)
                self.conn.commit()
                print("Migration 'signals' complete")

        except Exception as e:
            print(f"Migration warning: {e}")
        finally:
            cursor.close()
    
    def insert_trade(self,
                    symbol: str,
                    exchange: str = "NSE",
                    action: str = None,
                    quantity: int = None,
                    price: float = None,
                    gross_amount: float = None,
                    total_fees: float = 0.0,
                    net_amount: float = None,
                    strategy: str = "RSI",
                    reason: str = "",
                    broker: str = "mstock",
                    source: str = "BOT",
                    rsi: float = 0.0,
                    market_trend: float = 0.0,
                    atr: float = 0.0,
                    adx: float = 0.0,
                    macd_val: float = 0.0,
                    macd_signal: float = 0.0,
                    macd_hist: float = 0.0,
                    fee_breakdown: Optional[Dict] = None,
                    fallback_entry_price: float = 0.0,
                    # Test-friendly parameter aliases
                    trade_type: str = None,
                    entry_price: float = None,
                    exit_price: float = None,
                    qty: int = None,
                    pnl_net: float = None,
                    timestamp: str = None) -> int:
        """
        Insert a trade record. Supports both full API and test-friendly aliases.

        Returns: trade_id
        """
        # Map test-friendly parameters to full API
        if trade_type is not None:
            action = trade_type
        if qty is not None:
            quantity = qty
        if entry_price is not None and price is None:
            price = entry_price
        if exit_price is not None and price is None:
            price = exit_price
        if net_amount is None and price is not None and quantity is not None:
            net_amount = price * quantity
        if gross_amount is None and net_amount is not None:
            gross_amount = net_amount

        # Use provided timestamp or current time
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # --- BUG-04: Duplicate Guard ---
        # Only check for duplicates in production (not in-memory test databases)
        if self.db_path != ":memory:":
            cursor = self.conn.cursor()
            try:
                # Check for exact same record (true duplicates within 10 seconds)
                cursor.execute("""
                    SELECT id FROM trades
                    WHERE symbol = ? AND action = ? AND quantity = ?
                      AND ABS(price - ?) < 0.01
                      AND datetime(timestamp) >= datetime('now', '-10 seconds')
                """, (symbol, action, quantity, price))
                if cursor.fetchone():
                    print(f"DUPLICATE GUARD: Skipping duplicate {action} {symbol} @ {price}")
                    return -1
            finally:
                cursor.close()

        # timestamp already set above, don't override here
        
        # Extract fee breakdown if provided
        brokerage = fee_breakdown.get('brokerage', 0) if fee_breakdown else 0
        stt = fee_breakdown.get('stt', 0) if fee_breakdown else 0
        exchange_fee = fee_breakdown.get('exchange_charges', 0) if fee_breakdown else 0
        gst = fee_breakdown.get('gst', 0) if fee_breakdown else 0
        sebi = fee_breakdown.get('sebi_charges', 0) if fee_breakdown else 0
        stamp = fee_breakdown.get('stamp_duty', 0) if fee_breakdown else 0

        # Handle test-provided P&L or calculate automatically
        pnl_gross = None
        pnl_net_param = pnl_net  # Store the test parameter
        pnl_net = None
        pnl_pct_gross = None
        pnl_pct_net = None

        cursor = self.conn.cursor()
        try:
            # Automatic P&L Calculation for SELL trades (unless already provided by test)
            if action.upper() == "SELL" and pnl_net_param is None:
                # --- BUG-01 & BUG-02: FIFO and Paper Isolation ---
                if broker.upper() == 'PAPER':
                    broker_filter = "broker = 'PAPER'"
                else:
                    broker_filter = "broker != 'PAPER'"

                cursor.execute(f"""
                    SELECT price, net_amount, quantity FROM trades
                    WHERE symbol = ? AND action = 'BUY' AND {broker_filter}
                    ORDER BY timestamp ASC LIMIT 1
                """, (symbol,))
                last_buy = cursor.fetchone()

                buy_price = 0.0
                buy_net_per_unit = 0.0

                if last_buy:
                    buy_price = last_buy['price']
                    buy_net_per_unit = last_buy['net_amount'] / last_buy['quantity']
                elif fallback_entry_price > 0:
                    buy_price = fallback_entry_price
                    buy_net_per_unit = fallback_entry_price  # Estimate without fees
                else:
                    # --- BUG-03 Part A: Warning for NULL P&L ---
                    print(f"WARNING: No matching BUY found for SELL {symbol}. P&L will be NULL. "
                          f"Run backfill_pnl.py to reconcile using mstock_statement.csv.")

                if buy_price > 0:
                    sell_price = price
                    sell_net_per_unit = net_amount / quantity

                    pnl_gross = (sell_price - buy_price) * quantity
                    pnl_net = (sell_net_per_unit - buy_net_per_unit) * quantity

                    pnl_pct_gross = (pnl_gross / (buy_price * quantity)) * 100
                    pnl_pct_net = (pnl_net / (buy_net_per_unit * quantity)) * 100
            elif pnl_net_param is not None:
                # Use provided P&L from test
                pnl_net = pnl_net_param

            cursor.execute("""
                INSERT INTO trades (
                    timestamp, symbol, exchange, action, quantity, price,
                    gross_amount, brokerage_fee, stt_fee, exchange_fee,
                    gst_fee, sebi_fee, stamp_duty_fee, total_fees, net_amount,
                    strategy, reason, broker, source, rsi,
                    market_trend, atr, adx, macd_val, macd_signal, macd_hist,
                    pnl_gross, pnl_net, pnl_pct_gross, pnl_pct_net
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, symbol, exchange, action, quantity, price,
                gross_amount, brokerage, stt, exchange_fee,
                gst, sebi, stamp, total_fees, net_amount,
                strategy, reason, broker, source, rsi,
                market_trend, atr, adx, macd_val, macd_signal, macd_hist,
                pnl_gross, pnl_net, pnl_pct_gross, pnl_pct_net
            ))
            
            self.conn.commit()
            trade_id = cursor.lastrowid
            print(f"Trade logged: {action} {symbol} @ {price} (ID: {trade_id})")
            return trade_id
        finally:
            cursor.close()
    
    def get_open_positions(self, is_paper: bool = False) -> List[Dict]:
        """
        Get all open positions (bought but not yet sold)
        Filter by paper/real trades to avoid mixing
        """
        broker_filter = "broker = 'PAPER'" if is_paper else "broker != 'PAPER'"

        query = f"""
            SELECT symbol, exchange, 
                   SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as net_quantity,
                   AVG(CASE WHEN action = 'BUY' THEN price END) as avg_entry_price,
                   MIN(CASE WHEN action = 'BUY' THEN timestamp END) as first_buy_time,
                   SUM(CASE WHEN action = 'BUY' THEN net_amount ELSE 0 END) as total_invested,
                   strategy,
                   broker
            FROM trades
            WHERE {broker_filter}
            GROUP BY symbol, exchange
            HAVING net_quantity > 0
        """
        
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            positions = []
            for row in cursor.fetchall():
                positions.append(dict(row))
            return positions
        finally:
            cursor.close()
    
    def get_trade_history(self, days: int = 30, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Get trade history as pandas DataFrame
        """
        query = """
            SELECT * FROM trades
            WHERE datetime(timestamp) >= datetime('now', ?)
        """
        params = [f'-{days} days']
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY timestamp DESC"
        
        # pandas read_sql_query handles cursor/connection safe enough usually, but prefer passing connection
        df = pd.read_sql_query(query, self.conn, params=params)
        return df
    
    def get_today_trades(self, is_paper: bool = False) -> pd.DataFrame:
        """
        Get today's trades
        """
        today = datetime.now().date().isoformat()
        broker_filter = "broker = 'PAPER'" if is_paper else "broker != 'PAPER'"

        query = f"""
            SELECT * FROM trades
            WHERE DATE(timestamp) = ? AND {broker_filter}
            ORDER BY timestamp DESC
        """
        params = [today]
        return pd.read_sql_query(query, self.conn, params=params)

    def get_recent_trades(self, limit: int = 10, is_paper: bool = None, days: Optional[int] = None) -> List[Dict]:
        """
        Get list of recent trades with optional day filter
        """
        query = "SELECT * FROM trades"
        where_clauses = []
        params = []
        
        if is_paper is not None:
            where_clauses.append("broker = 'PAPER'" if is_paper else "broker != 'PAPER'")
            
        if days is not None:
            where_clauses.append("datetime(timestamp) >= datetime('now', ?)")
            params.append(f'-{days} days')
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching recent trades: {e}")
            return []
        finally:
            cursor.close()

    def get_daily_pnl_series(self, days: int = 30) -> List[Dict]:
        """
        Get daily P&L series for the last N days.
        Groups trades by date and aggregates net_pnl, trade_count, wins, losses.

        Returns:
            List of dicts: [{"date": "2026-06-21", "net_pnl": 500.0, "trade_count": 3, "wins": 2, "losses": 1}, ...]
        """
        cursor = self.conn.cursor()
        try:
            # Query: GROUP BY DATE, aggregate P&L, count trades
            cursor.execute("""
                SELECT
                    DATE(timestamp) as date,
                    COALESCE(SUM(CASE WHEN pnl_net IS NOT NULL THEN pnl_net ELSE 0 END), 0) as net_pnl,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN pnl_net > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl_net < 0 THEN 1 ELSE 0 END) as losses
                FROM trades
                WHERE action = 'SELL' AND datetime(timestamp) >= datetime('now', ?)
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp) ASC
            """, (f"-{days} days",))

            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    "date": row["date"],
                    "net_pnl": row["net_pnl"],
                    "trade_count": row["trade_count"],
                    "wins": row["wins"],
                    "losses": row["losses"],
                })
            return result
        except Exception as e:
            print(f"Error fetching daily P&L series: {e}")
            return []
        finally:
            cursor.close()

    def get_symbol_breakdown(self, days: int = 30) -> List[Dict]:
        """
        Get per-symbol performance breakdown.
        Returns performance metrics for each symbol traded in the period.

        Returns:
            List of dicts: [{"symbol": "HDFCBANK", "net_pnl": 1000.0, "trade_count": 5, "wins": 3, "losses": 2, "win_rate": 60.0}, ...]
        """
        cursor = self.conn.cursor()
        try:
            # Query: GROUP BY symbol, aggregate P&L, count wins/losses
            cursor.execute("""
                SELECT
                    symbol,
                    COALESCE(SUM(CASE WHEN pnl_net IS NOT NULL THEN pnl_net ELSE 0 END), 0) as net_pnl,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN pnl_net > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl_net < 0 THEN 1 ELSE 0 END) as losses
                FROM trades
                WHERE action = 'SELL' AND datetime(timestamp) >= datetime('now', ?)
                GROUP BY symbol
                ORDER BY net_pnl DESC
            """, (f"-{days} days",))

            rows = cursor.fetchall()
            result = []
            for row in rows:
                win_count = row["wins"]
                loss_count = row["losses"]
                denom = win_count + loss_count
                win_rate = (win_count / denom * 100.0) if denom > 0 else 0.0

                result.append({
                    "symbol": row["symbol"],
                    "net_pnl": row["net_pnl"],
                    "trade_count": row["trade_count"],
                    "wins": win_count,
                    "losses": loss_count,
                    "win_rate": round(win_rate, 2),
                })
            return result
        except Exception as e:
            print(f"Error fetching symbol breakdown: {e}")
            return []
        finally:
            cursor.close()

    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        Get performance metrics
        """
        # Get all completed trades (buy-sell pairs)
        df = self.get_trade_history(days)
        
        if df.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'gross_profit': 0,
                'total_fees': 0,
                'net_profit': 0,
                'avg_profit_per_trade': 0
            }
        
        # Calculate metrics
        sells = df[df['action'] == 'SELL']
        
        total_trades = len(sells)
        # --- BUG-05: NULL Handling in Performance Summary ---
        winning_trades = len(sells[sells['pnl_net'].fillna(0) > 0])
        losing_trades = len(sells[sells['pnl_net'].fillna(0) < 0])
        neutral_trades = int(sells['pnl_net'].isna().sum())
        
        win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
        
        gross_profit = float(sells['pnl_gross'].dropna().sum())
        total_fees = sells['total_fees'].sum()
        net_profit = float(sells['pnl_net'].dropna().sum())
        avg_profit = net_profit / total_trades if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'neutral_trades': neutral_trades,
            'win_rate': round(win_rate, 2),
            'gross_profit': round(gross_profit, 2),
            'total_fees': round(total_fees, 2),
            'net_profit': round(net_profit, 2),
            'avg_profit_per_trade': round(avg_profit, 2)
        }
    
    def backup_to_csv(self, output_file: str = None):
        """
        Backup all trades to CSV
        """
        if output_file is None:
            today = datetime.now().strftime('%Y%m%d')
            output_file = f"database/trades_backup_{today}.csv"
        
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp", self.conn)
        df.to_csv(output_file, index=False)
        print(f"✅ Database backed up to {output_file}")
        return output_file
    
    def close(self):
        """
        Close database connection
        """
        self.conn.close()
        print("Database connection closed")

    def export_trades_csv(self, start_date: str, end_date: str, output_dir: str = "exports") -> str:
        """
        Export trades to CSV for a specific date range.
        
        Args:
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            output_dir: Directory to save the CSV file
            
        Returns:
            str: Path to the created CSV file
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate next day for end_date to include the full end date
        # (Since timestamp includes time, and we compare against YYYY-MM-DD 00:00:00)
        try:
             # Just simple string comparison works for ISO dates, but to be precise with times:
             # We want >= start_date 00:00:00 and <= end_date 23:59:59
             # Simplest SQLite way: date(timestamp) BETWEEN start AND end
             pass
        except:
             pass

        query = """
            SELECT 
                timestamp, symbol, exchange, action, quantity, price,
                gross_amount, total_fees, net_amount,
                brokerage_fee, stt_fee, exchange_fee, gst_fee, sebi_fee, stamp_duty_fee,
                strategy, reason, broker, source, rsi,
                market_trend, atr, adx, macd_val, macd_signal, macd_hist,
                pnl_gross, pnl_net, pnl_pct_net
            FROM trades
            WHERE DATE(timestamp) >= DATE(?) AND DATE(timestamp) <= DATE(?)
            ORDER BY timestamp ASC
        """
        
        try:
            df = pd.read_sql_query(query, self.conn, params=[start_date, end_date])
            
            if df.empty:
                return None
                
            filename = f"trades_{start_date}_to_{end_date}.csv"
            filepath = os.path.join(output_dir, filename)
            
            df.to_csv(filepath, index=False)
            print(f"Trades exported to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Failed to export trades: {e}")
            raise
            
    def close_position_external(self, symbol: str, exchange: str, quantity: int, price: float, reason: str = "External/Manual Exit") -> int:
        """
        Close a position that was closed externally (outside the bot).
        Logs a SELL trade with 0 fees to balance the books.
        """
        # Calculate P&L for records, but fees are likely 0 since we didn't execute it
        # (Or we could estimate fees if we knew it was a real trade, but for reconciliation safest is 0)
        
        # We assume price is the price at which it was closed, or current LTP if unknown.
        gross = quantity * price
        
        return self.insert_trade(
            symbol=symbol,
            exchange=exchange,
            action="SELL",
            quantity=quantity,
            price=price,
            gross_amount=gross,
            total_fees=0,
            net_amount=gross,
            strategy="Reconciliation",
            reason=reason,
            broker="mstock",
            source="HYBRID"
        )

    def insert_signal(self, signal_data: Dict) -> Optional[int]:
        """
        Insert a signal record for ML training (Phase 1).

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
                    signal_data.get("market", "IN"),
                    signal_data.get("action"),
                    signal_data.get("source", "BOT"),
                    signal_data.get("rsi"),
                    signal_data.get("current_price"),
                    features_json,
                    signal_data.get("execution_id"),
                    signal_data.get("future_return"),
                ),
            )
            self.conn.commit()
            signal_id = cursor.lastrowid
            return signal_id

        except sqlite3.IntegrityError:
            # Duplicate execution_id
            return None
        except Exception as e:
            print(f"Error inserting signal: {e}")
            return None

    def get_signals(
        self,
        market: Optional[str] = None,
        days_back: int = 30,
        limit: int = 10000,
        source: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve signals for ML training (Phase 4).

        Args:
            market: Filter by market ('IN', 'US', or None for all)
            days_back: Only signals from past N days
            limit: Max signals to return
            source: Filter by source ('BOT', 'MANUAL', or None for all)

        Returns:
            List of signal dicts ready for training.
        """
        import json

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

            return signals

        except Exception as e:
            print(f"Error retrieving signals: {e}")
            return []

    def get_manual_signals(
        self,
        since: Optional[str] = None,
        limit: int = 10_000,
    ) -> List[Dict]:
        """
        Retrieve MANUAL signals since a cutoff timestamp.

        Used by MLTrainingPipeline.collect_signals() to fetch raw human-entered
        trades for supervised learning.

        Args:
            since:  ISO-8601 timestamp string; only signals after this time are
                    returned.  If None, returns all signals.
            limit:  Maximum number of rows to return.

        Returns:
            List of signal dicts (same schema as get_signals()).
        """
        import json

        cursor = self.conn.cursor()
        where_clauses = []
        params: list = []

        if since:
            where_clauses.append("timestamp > ?")
            params.append(since)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        try:
            cursor.execute(
                f"SELECT * FROM signals {where_sql} ORDER BY timestamp DESC LIMIT ?",
                params + [limit],
            )
            rows = cursor.fetchall()
            signals = []
            for row in rows:
                row_dict = dict(row)
                features_raw = row_dict.pop("features_json", None)
                row_dict["features"] = json.loads(features_raw) if features_raw else {}
                signals.append(row_dict)
            return signals
        except Exception as exc:
            print(f"Error in get_manual_signals: {exc}")
            return []


if __name__ == "__main__":
    # Test database
    print("\n=== Testing Trades Database ===\n")
    
    # Create test instance
    test_db = TradesDatabase("database/test_trades.db")
    
    # Insert a BUY trade
    buy_id = test_db.insert_trade(
        symbol="HDFCBANK",
        exchange="NSE",
        action="BUY",
        quantity=10,
        price=1600,
        gross_amount=16000,
        total_fees=30.65,
        net_amount=16030.65,
        strategy="RSI Mean Reversion",
        reason="RSI 32 (Oversold)"
    )
    
    # Insert a SELL trade
    sell_id = test_db.insert_trade(
        symbol="HDFCBANK",
        exchange="NSE",
        action="SELL",
        quantity=10,
        price=1760,
        gross_amount=17600,
        total_fees=31.35,
        net_amount=17568.65,
        strategy="RSI Mean Reversion",
        reason="Profit Target Hit (10%)"
    )
    
    # Get open positions
    print("\n--- Open Positions ---")
    positions = test_db.get_open_positions()
    for pos in positions:
        print(pos)
    
    # Get trade history
    print("\n--- Trade History (Last 30 days) ---")
    history = test_db.get_trade_history(days=30)
    print(history[['timestamp', 'symbol', 'action', 'quantity', 'price', 'net_amount']])
    
    # Get performance summary
    print("\n--- Performance Summary ---")
    perf = test_db.get_performance_summary(days=30)
    for key, value in perf.items():
        print(f"{key}: {value}")
    
    # Backup to CSV
    print("\n--- Backup ---")
    test_db.backup_to_csv()
    
    test_db.close()
