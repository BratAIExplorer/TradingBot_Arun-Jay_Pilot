import unittest
import os
import sqlite3
import pandas as pd
from datetime import datetime
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.trades_db import TradesDatabase

class TestTradesExport(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "tests/temp_test_trades.db"
        self.test_export_dir = "tests/temp_exports"
        self.db = TradesDatabase(self.test_db_path)
        
        # Clear existing data
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM trades")
        self.db.conn.commit()
        
        # Insert mock trades
        self.insert_mock_trade("2023-01-01 10:00:00", "AAPL", "BUY", 10, 150.0)
        self.insert_mock_trade("2023-01-15 14:30:00", "GOOGL", "BUY", 5, 2800.0)
        self.insert_mock_trade("2023-02-01 09:15:00", "MSFT", "SELL", 8, 300.0)
        
    def tearDown(self):
        self.db.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # Clean up exports
        if os.path.exists(self.test_export_dir):
            for f in os.listdir(self.test_export_dir):
                os.remove(os.path.join(self.test_export_dir, f))
            os.rmdir(self.test_export_dir)

    def insert_mock_trade(self, timestamp, symbol, action, qty, price):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO trades (timestamp, symbol, exchange, action, quantity, price, gross_amount, net_amount, source)
            VALUES (?, ?, 'NSE', ?, ?, ?, ?, ?, 'BOT')
        """, (timestamp, symbol, action, qty, price, qty*price, qty*price))
        self.db.conn.commit()

    def test_export_date_range(self):
        # Export for Jan 2023
        filepath = self.db.export_trades_csv("2023-01-01", "2023-01-31", self.test_export_dir)
        
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        
        df = pd.read_csv(filepath)
        self.assertEqual(len(df), 2)  # AAAPL and GOOGL
        self.assertTrue("AAPL" in df['symbol'].values)
        self.assertTrue("GOOGL" in df['symbol'].values)
        self.assertFalse("MSFT" in df['symbol'].values)
        
        # Verify columns exist
        required_cols = ['timestamp', 'symbol', 'action', 'quantity', 'price', 'gross_amount']
        for col in required_cols:
            self.assertTrue(col in df.columns)

    def test_export_empty_range(self):
        # Export for range with no trades
        filepath = self.db.export_trades_csv("2022-01-01", "2022-12-31", self.test_export_dir)
        self.assertIsNone(filepath)

if __name__ == '__main__':
    unittest.main()
