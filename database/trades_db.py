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
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        # self.cursor removed to prevent recursive cursor usage
        
        # Create tables
        self._create_tables()
        self._run_migrations()
        print(f"✅ Database initialized: {db_path} (v2 with get_recent_trades)")
    
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
                print("🔄 Migrating database: Adding 'broker' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN broker TEXT DEFAULT 'mstock'")
                self.conn.commit()

            if 'source' not in columns:
                print("🔄 Migrating database: Adding 'source' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN source TEXT DEFAULT 'BOT'")
                self.conn.commit()
                print("✅ Migration 'source' complete")

            if 'rsi' not in columns:
                print("🔄 Migrating database: Adding 'rsi' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN rsi REAL")
                self.conn.commit()
                print("✅ Migration 'rsi' complete")

        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
        finally:
            cursor.close()
    
    def insert_trade(self,
                    symbol: str,
                    exchange: str,
                    action: str,
                    quantity: int,
                    price: float,
                    gross_amount: float,
                    total_fees: float,
                    net_amount: float,
                    strategy: str = "RSI",
                    reason: str = "",
                    broker: str = "mstock",
                    source: str = "BOT",
                    rsi: float = 0.0,
                    fee_breakdown: Optional[Dict] = None) -> int:
        """
        Insert a trade record
        
        Returns: trade_id
        """
        timestamp = datetime.now().isoformat()
        
        # Extract fee breakdown if provided
        brokerage = fee_breakdown.get('brokerage', 0) if fee_breakdown else 0
        stt = fee_breakdown.get('stt', 0) if fee_breakdown else 0
        exchange_fee = fee_breakdown.get('exchange_charges', 0) if fee_breakdown else 0
        gst = fee_breakdown.get('gst', 0) if fee_breakdown else 0
        sebi = fee_breakdown.get('sebi_charges', 0) if fee_breakdown else 0
        stamp = fee_breakdown.get('stamp_duty', 0) if fee_breakdown else 0
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO trades (
                    timestamp, symbol, exchange, action, quantity, price,
                    gross_amount, brokerage_fee, stt_fee, exchange_fee,
                    gst_fee, sebi_fee, stamp_duty_fee, total_fees, net_amount,
                    strategy, reason, broker, source, rsi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, symbol, exchange, action, quantity, price,
                gross_amount, brokerage, stt, exchange_fee,
                gst, sebi, stamp, total_fees, net_amount,
                strategy, reason, broker, source, rsi
            ))
            
            self.conn.commit()
            trade_id = cursor.lastrowid
            print(f"✅ Trade logged: {action} {symbol} @ ₹{price} (ID: {trade_id})")
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

    def get_recent_trades(self, limit: int = 10, is_paper: bool = None) -> List[Dict]:
        """
        Get list of recent trades
        """
        query = "SELECT * FROM trades"
        params = []
        
        if is_paper is not None:
            query += " WHERE broker = 'PAPER'" if is_paper else " WHERE broker != 'PAPER'"
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error fetching recent trades: {e}")
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
        winning_trades = len(sells[sells['pnl_net'] > 0])
        losing_trades = len(sells[sells['pnl_net'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sells['pnl_gross'].sum() if 'pnl_gross' in sells.columns else 0
        total_fees = sells['total_fees'].sum()
        net_profit = sells['pnl_net'].sum() if 'pnl_net' in sells.columns else 0
        avg_profit = net_profit / total_trades if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
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
        print("✅ Database connection closed")


# Global database instance
db = TradesDatabase()


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
