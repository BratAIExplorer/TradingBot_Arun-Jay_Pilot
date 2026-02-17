"""
Order Attempts Database - Track ALL Trading Decisions
Logs every trade attempt (success, failure, skip) with full context

Part of Phase 0A - Enhanced Logging System
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


class OrderAttemptsDB:
    """Database for tracking all order attempts and trading decisions"""
    
    def __init__(self, db_path: str = "database/order_attempts.db"):
        self.db_path = db_path
        self.conn = None
        self.create_tables()
    
    def connect(self):
        """Create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def create_tables(self):
        """Create order attempts table with comprehensive tracking"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                exchange TEXT NOT NULL,
                action TEXT NOT NULL,  -- BUY, SELL
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                
                -- Status
                status TEXT NOT NULL,  -- SUCCESS, FAILED, SKIPPED
                reason TEXT NOT NULL,  -- Why this decision was made
                
                -- Context at time of decision
                rsi_value REAL,
                rsi_threshold_buy REAL,
                rsi_threshold_sell REAL,
                
                -- Risk parameters
                stop_loss_pct REAL,
                profit_target_pct REAL,
                stop_loss_price REAL,
                profit_target_price REAL,
                
                -- Market conditions
                last_price REAL,
                volume INTEGER,
                market_status TEXT,  -- OPEN, CLOSED, PRE_OPEN
                
                -- Capital management
                available_capital REAL,
                allocated_amount REAL,
                position_count INTEGER,
                
                -- Strategy
                strategy TEXT DEFAULT 'RSI',
                timeframe TEXT,
                
                -- Error details (if failed)
                error_message TEXT,
                error_code TEXT,
                
                -- Additional metadata
                metadata TEXT  -- JSON for extra data
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON order_attempts(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_status 
            ON order_attempts(symbol, status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON order_attempts(status)
        """)
        
        conn.commit()
    
    def log_attempt(
        self,
        symbol: str,
        exchange: str,
        action: str,
        quantity: int,
        price: float,
        status: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log an order attempt with full context
        
        Args:
            symbol: Stock ticker
            exchange: BSE/NSE
            action: BUY or SELL
            quantity: Number of shares
            price: Target price
            status: SUCCESS, FAILED, SKIPPED
            reason: Why this decision was made
            context: Additional context dictionary
        
        Returns:
            Attempt ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        context = context or {}
        
        cursor.execute("""
            INSERT INTO order_attempts (
                timestamp, symbol, exchange, action, quantity, price,
                status, reason,
                rsi_value, rsi_threshold_buy, rsi_threshold_sell,
                stop_loss_pct, profit_target_pct, stop_loss_price, profit_target_price,
                last_price, volume, market_status,
                available_capital, allocated_amount, position_count,
                strategy, timeframe,
                error_message, error_code,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            symbol,
            exchange,
            action.upper(),
            quantity,
            price,
            status.upper(),
            reason,
            context.get('rsi_value'),
            context.get('rsi_threshold_buy'),
            context.get('rsi_threshold_sell'),
            context.get('stop_loss_pct'),
            context.get('profit_target_pct'),
            context.get('stop_loss_price'),
            context.get('profit_target_price'),
            context.get('last_price'),
            context.get('volume'),
            context.get('market_status'),
            context.get('available_capital'),
            context.get('allocated_amount'),
            context.get('position_count'),
            context.get('strategy', 'RSI'),
            context.get('timeframe'),
            context.get('error_message'),
            context.get('error_code'),
            json.dumps(context.get('metadata', {}))
        ))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_recent_attempts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent order attempts"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM order_attempts
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_attempts_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get attempts filtered by status (SUCCESS, FAILED, SKIPPED)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM order_attempts
            WHERE status = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (status.upper(), limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_skip_reasons_summary(self) -> List[Dict[str, Any]]:
        """Get summary of why trades were skipped"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                reason,
                COUNT(*) as count,
                GROUP_CONCAT(DISTINCT symbol) as symbols
            FROM order_attempts
            WHERE status = 'SKIPPED'
            GROUP BY reason
            ORDER BY count DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_failure_reasons_summary(self) -> List[Dict[str, Any]]:
        """Get summary of why trades failed"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                error_message,
                error_code,
                COUNT(*) as count,
                GROUP_CONCAT(DISTINCT symbol) as symbols
            FROM order_attempts
            WHERE status = 'FAILED'
            GROUP BY error_message, error_code
            ORDER BY count DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_success_rate(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Calculate success rate of order attempts"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM order_attempts
                WHERE symbol = ?
                GROUP BY status
            """, (symbol,))
        else:
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM order_attempts
                GROUP BY status
            """)
        
        results = {row['status']: row['count'] for row in cursor.fetchall()}
        total = sum(results.values())
        
        return {
            'total_attempts': total,
            'successful': results.get('SUCCESS', 0),
            'failed': results.get('FAILED', 0),
            'skipped': results.get('SKIPPED', 0),
            'success_rate': (results.get('SUCCESS', 0) / total * 100) if total > 0 else 0
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Convenience functions for quick logging
def log_success(symbol: str, exchange: str, action: str, quantity: int, price: float, context: Dict):
    """Log successful order"""
    db = OrderAttemptsDB()
    return db.log_attempt(symbol, exchange, action, quantity, price, "SUCCESS", "Order executed successfully", context)


def log_failure(symbol: str, exchange: str, action: str, quantity: int, price: float, reason: str, error: str, context: Dict):
    """Log failed order"""
    context['error_message'] = error
    db = OrderAttemptsDB()
    return db.log_attempt(symbol, exchange, action, quantity, price, "FAILED", reason, context)


def log_skip(symbol: str, exchange: str, action: str, quantity: int, price: float, reason: str, context: Dict):
    """Log skipped order"""
    db = OrderAttemptsDB()
    return db.log_attempt(symbol, exchange, action, quantity, price, "SKIPPED", reason, context)


if __name__ == "__main__":
    # Test the database
    db = OrderAttemptsDB()
    
    # Test logging
    test_context = {
        'rsi_value': 32.5,
        'rsi_threshold_buy': 35,
        'rsi_threshold_sell': 65,
        'stop_loss_pct': 5.0,
        'profit_target_pct': 10.0,
        'last_price': 245.50,
        'market_status': 'OPEN',
        'strategy': 'RSI'
    }
    
    # Log a successful attempt
    attempt_id = log_success("MICEL", "BSE", "BUY", 10, 245.50, test_context)
    print(f"✅ Logged successful attempt: {attempt_id}")
    
    # Log a skipped attempt
    skip_context = test_context.copy()
    skip_attempt_id = log_skip("TITAN", "NSE", "BUY", 5, 3100, "Market closed", skip_context)
    print(f"⏭️ Logged skipped attempt: {skip_attempt_id}")
    
    # Get recent attempts
    recent = db.get_recent_attempts(limit=10)
    print(f"\n📊 Recent attempts: {len(recent)}")
    
    # Get success rate
    success_rate = db.get_success_rate()
    print(f"\n📈 Success Rate: {success_rate['success_rate']:.1f}%")
    print(f"   Successful: {success_rate['successful']}")
    print(f"   Failed: {success_rate['failed']}")
    print(f"   Skipped: {success_rate['skipped']}")
    
    db.close()
    print("\n✅ Order Attempts Database tested successfully!")
