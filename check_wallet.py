import sqlite3
import os

def check_wallet_state():
    db_path = "database/trades.db"
    if not os.path.exists(db_path):
        print("❌ DB not found")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check Open Positions
    print("--- Open Positions ---")
    query = """
    SELECT symbol, 
           SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as net_qty,
           SUM(CASE WHEN action = 'BUY' THEN net_amount ELSE 0 END) as total_buy_cost,
           SUM(CASE WHEN action = 'SELL' THEN net_amount ELSE 0 END) as total_sell_value
    FROM trades 
    GROUP BY symbol 
    HAVING net_qty > 0
    """
    cursor.execute(query)
    positions = cursor.fetchall()
    if not positions:
        print("✅ No open positions found. Bot is flat.")
    for pos in positions:
        print(f"📍 {pos['symbol']}: {pos['net_qty']} units (Invested: ₹{pos['total_buy_cost']:.2f})")
    
    # 2. Check Total P&L from Database
    print("\n--- P&L Analysis ---")
    cursor.execute("SELECT SUM(pnl_net) as total_pnl FROM trades WHERE action = 'SELL'")
    total_pnl = cursor.fetchone()['total_pnl'] or 0
    print(f"💰 Total Realized P&L: ₹{total_pnl:.2f}")
    
    # 3. Check Today's P&L
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT SUM(pnl_net) as today_pnl FROM trades WHERE action = 'SELL' AND timestamp LIKE ?", (f"{today}%",))
    today_pnl = cursor.fetchone()['today_pnl'] or 0
    print(f"📅 Today's Realized P&L: ₹{today_pnl:.2f}")

    conn.close()

if __name__ == "__main__":
    check_wallet_state()
