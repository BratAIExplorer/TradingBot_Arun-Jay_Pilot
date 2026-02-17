
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.trades_db import TradesDatabase

def test_analytics_insertion():
    print("Testing Analytics Insertion...")
    db = TradesDatabase("database/test_analytics.db")
    
    try:
        trade_id = db.insert_trade(
            symbol="TEST_ANALYTICS",
            exchange="NSE",
            action="BUY",
            quantity=10,
            price=100.0,
            gross_amount=1000.0,
            total_fees=10.0,
            net_amount=1010.0,
            strategy="Test",
            reason="Validation",
            rsi=55.5,
            market_trend=0.5,
            atr=10.2,
            adx=25.0,
            macd_val=1.5,
            macd_signal=1.2,
            macd_hist=0.3
        )
        print(f"✅ Trade inserted successfully with ID: {trade_id}")
        
        # Verify data
        conn = db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT market_trend, atr, adx, macd_val FROM trades WHERE id=?", (trade_id,))
        row = cursor.fetchone()
        
        print(f"Retrieved Row: {dict(row)}")
        
        if row['market_trend'] == 0.5 and row['macd_val'] == 1.5:
             print("✅ Data verification passed!")
        else:
             print("❌ Data verification FAILED!")
             
    except Exception as e:
        print(f"❌ Insertion Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        # Clean up
        if os.path.exists("database/test_analytics.db"):
            os.remove("database/test_analytics.db")

if __name__ == "__main__":
    test_analytics_insertion()
