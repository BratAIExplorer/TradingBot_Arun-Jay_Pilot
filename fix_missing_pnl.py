import sqlite3
import os

def fix_pnl():
    db_path = "database/trades.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all SELL trades with missing P&L
    cursor.execute("SELECT * FROM trades WHERE action = 'SELL' AND pnl_net IS NULL")
    sells = cursor.fetchall()
    
    if not sells:
        print("✅ No trades found requiring P&L backfill.")
        return

    print(f"🔄 Found {len(sells)} SELL trades to process...")
    
    updates = 0
    for sell in sells:
        symbol = sell['symbol']
        timestamp = sell['timestamp']
        sell_id = sell['id']
        sell_price = sell['price']
        sell_qty = sell['quantity']
        sell_net = sell['net_amount']
        
        # Find the matching BUY
        cursor.execute("""
            SELECT price, net_amount, quantity FROM trades 
            WHERE symbol = ? AND action = 'BUY' AND timestamp < ?
            ORDER BY timestamp DESC LIMIT 1
        """, (symbol, timestamp))
        
        buy = cursor.fetchone()
        if buy:
            buy_price = buy['price']
            buy_net_per_unit = buy['net_amount'] / buy['quantity']
            
            sell_net_per_unit = sell_net / sell_qty
            
            pnl_gross = (sell_price - buy_price) * sell_qty
            pnl_net = (sell_net_per_unit - buy_net_per_unit) * sell_qty
            
            pnl_pct_gross = (pnl_gross / (buy_price * sell_qty)) * 100 if buy_price > 0 else 0
            pnl_pct_net = (pnl_net / (buy_net_per_unit * sell_qty)) * 100 if buy_net_per_unit > 0 else 0
            
            cursor.execute("""
                UPDATE trades SET 
                    pnl_gross = ?, pnl_net = ?, 
                    pnl_pct_gross = ?, pnl_pct_net = ?
                WHERE id = ?
            """, (pnl_gross, pnl_net, pnl_pct_gross, pnl_pct_net, sell_id))
            updates += 1
            print(f"  ✅ Fixed {symbol} (ID: {sell_id}): P&L = ₹{pnl_net:.2f}")

    conn.commit()
    conn.close()
    print(f"\n✨ Successfully backfilled {updates} trades.")

if __name__ == "__main__":
    fix_pnl()
