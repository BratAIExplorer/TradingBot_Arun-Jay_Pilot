import sqlite3
import os

def debug_trades():
    db_path = "database/trades.db"
    if not os.path.exists(db_path):
        print("❌ DB not found")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, timestamp, action, pnl_net, reason FROM trades WHERE action = 'SELL' ORDER BY id")
    rows = cursor.fetchall()
    
    print(f"{'ID':<4} | {'Sym':<10} | {'Date':<20} | {'PnL':<10} | {'Reason'}")
    print("-" * 60)
    for row in rows:
        pnl = row['pnl_net']
        pnl_str = f"₹{pnl:.2f}" if pnl is not None else "NULL"
        print(f"{row['id']:<4} | {row['symbol']:<10} | {row['timestamp'][:19]:<20} | {pnl_str:<10} | {row['reason']}")
    
    conn.close()

if __name__ == "__main__":
    debug_trades()
