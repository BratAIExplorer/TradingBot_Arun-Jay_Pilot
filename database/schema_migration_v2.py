"""
Database Schema Migration v2
Adds 'strategy' column to trades and positions tables for multi-strategy support.
"""

import sqlite3
import os
import sys

# Add parent directory to path to import trades_db
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.trades_db import TradesDatabase


def migrate_add_strategy_column():
    """
    Add 'strategy' column to trades table.
    Defaults to 'RSI_MEAN_REVERSION' for backward compatibility.
    """
    print("🔄 Running Schema Migration v2: Adding 'strategy' column...")
    
    db_path = "database/trades.db"
    
    try:
        # Initialize database connection
        db = TradesDatabase(db_path)
        conn = db.conn
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'strategy' in columns:
            print("✅ Column 'strategy' already exists in trades table. Skipping migration.")
        else:
            # Add strategy column with default value
            cursor.execute("""
                ALTER TABLE trades 
                ADD COLUMN strategy TEXT DEFAULT 'RSI_MEAN_REVERSION'
            """)
            conn.commit()
            print("✅ Added 'strategy' column to trades table")
        
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"📊 Trades table now has {trade_count} records with strategy column")
        
        # Create index on strategy column for faster queries
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_strategy 
                ON trades(strategy)
            """)
            conn.commit()
            print("✅ Created index on 'strategy' column for performance")
        except Exception as e:
            print(f"⚠️ Index creation skipped: {e}")
        
        print("\n🎉 Migration v2 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def rollback_migration():
    """
    Rollback migration (SQLite doesn't support DROP COLUMN before 3.35.0)
    This creates a new table without the strategy column and copies data.
    """
    print("🔄 Rolling back Schema Migration v2...")
    
    db_path = "database/trades.db"
    
    try:
        db = TradesDatabase(db_path)
        conn = db.conn
        cursor = conn.cursor()
        
        # Create backup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades_backup AS 
            SELECT * FROM trades
        """)
        
        # Drop original table
        cursor.execute("DROP TABLE trades")
        
        # Recreate without strategy column
        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT DEFAULT 'MANUAL'
            )
        """)
        
        # Copy data back (excluding strategy column)
        cursor.execute("""
            INSERT INTO trades (id, symbol, action, quantity, price, timestamp, source)
            SELECT id, symbol, action, quantity, price, timestamp, source
            FROM trades_backup
        """)
        
        conn.commit()
        print("✅ Migration rolled back successfully")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Schema Migration v2")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        migrate_add_strategy_column()
