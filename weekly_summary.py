
import pandas as pd
from database.trades_db import db
from datetime import datetime, timedelta

def generate_report():
    print(f"\n📊 WEEKLY TRADING REPORT (Last 7 Days)")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 1. Fetch Data
    df = db.get_trade_history(days=7)
    
    if df.empty:
        print("❌ No trades recorded in the database for the last 7 days.")
        return

    # Ensure sorts
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 2. FIFO PnL Config
    inventory = {} # {symbol: [{'qty': q, 'price': p, 'fees': f}, ...]}
    
    realized_pnl = 0.0
    total_buy_val = 0.0
    total_sell_val = 0.0
    total_fees = 0.0
    
    trades_log = []

    for idx, row in df.iterrows():
        sym = row['symbol']
        action = row['action'].upper()
        qty = row['quantity']
        price = row['price']
        fees = row['total_fees'] if row['total_fees'] else 0.0
        amount = row['gross_amount']
        
        total_fees += fees
        
        if action == 'BUY':
            total_buy_val += amount
            # Add to inventory
            if sym not in inventory: inventory[sym] = []
            inventory[sym].append({'qty': qty, 'price': price})
            
            trades_log.append(f"[{row['timestamp'].strftime('%d-%b %H:%M')}] 🟢 BUY  {sym:<10} {qty:>4} @ ₹{price:>8.2f}")

        elif action == 'SELL':
            total_sell_val += amount
            
            # FIFO Matching
            matched_qty = 0
            cost_basis = 0.0
            
            remaining_sell = qty
            if sym in inventory:
                while remaining_sell > 0 and inventory[sym]:
                    batch = inventory[sym][0]
                    
                    if batch['qty'] <= remaining_sell:
                        # Consume entire batch
                        matched = batch['qty']
                        cost_basis += matched * batch['price']
                        remaining_sell -= matched
                        matched_qty += matched
                        inventory[sym].pop(0)
                    else:
                        # Partial batch consumption
                        matched = remaining_sell
                        cost_basis += matched * batch['price']
                        batch['qty'] -= matched
                        matched_qty += matched
                        remaining_sell = 0
            
            trade_pnl = 0.0
            pnl_str = ""
            if matched_qty > 0:
                # PnL = Sell Value - Cost Basis - Fees (approx allocated fees)
                # Gross PnL
                gross_pnl = (matched_qty * price) - cost_basis
                # Net PnL (deducting this trade's fees)
                net_pnl_trade = gross_pnl - fees
                
                realized_pnl += net_pnl_trade
                trade_pnl = net_pnl_trade
                
                color = "🟢" if net_pnl_trade > 0 else "🔴"
                pnl_str = f" | P&L: {color} ₹{net_pnl_trade:>.2f}"
            else:
                pnl_str = " | (Short/Unmatched)"
                
            trades_log.append(f"[{row['timestamp'].strftime('%d-%b %H:%M')}] 🔴 SELL {sym:<10} {qty:>4} @ ₹{price:>8.2f}{pnl_str}")

    print("--- 📜 TRADE LOG ---")
    for log in trades_log:
        print(log)
    print("-" * 60)
    
    # 3. Summary Stats
    print("\n--- 📈 SUMMARY METRICS ---")
    print(f"Total Trades:      {len(df)}")
    print(f"Total Buy Value:   ₹{total_buy_val:,.2f}")
    print(f"Total Sell Value:  ₹{total_sell_val:,.2f}")
    print(f"Total Fees:        ₹{total_fees:,.2f}")
    print(f"------------------------------")
    
    pnl_color = "🟢" if realized_pnl >= 0 else "🔴"
    print(f"Est. Realized P&L: {pnl_color} ₹{realized_pnl:,.2f}")
    print(f"(Note: Realized P&L matches Sell trades against earliest Buys using FIFO)")

if __name__ == "__main__":
    generate_report()
