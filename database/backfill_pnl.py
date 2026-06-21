import sys
import pandas as pd
import sqlite3
import re
import os
from datetime import timedelta

# Force UTF-8 output so ₹ symbol doesn't crash on Windows
sys.stdout.reconfigure(encoding='utf-8')

DRY_RUN = True

# Paths resolve correctly regardless of which directory you run from
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(_BASE, "database", "trades.db")
CSV_PATH = os.path.join(_BASE, "mstock_statement.csv")

def clean_symbol(scrip):
    # Strip suffixes like -EQ, -A, -BE, -IF, -X
    return re.sub(r'-(EQ|A|BE|IF|X)$', '', scrip)

def estimate_buy_fees(buy_gross):
    return 20.0 + (buy_gross * 0.001)

def main():
    print(f"--- P&L Backfill Script ---")
    if DRY_RUN:
        print("MODE: DRY RUN (No changes will be saved to the database)\n")
    else:
        print("MODE: LIVE RUN (Database will be updated)\n")

    try:
        # 1. Read mStock statement, skipping first 16 rows
        mstock_df = pd.read_csv(CSV_PATH, skiprows=16)
        
        # Clean up column names by stripping whitespace
        mstock_df.columns = mstock_df.columns.str.strip()
        
        # Parse Dates (ignore bad footer rows)
        mstock_df['Trade Date'] = pd.to_datetime(mstock_df['Trade Date'], format='%d-%m-%Y', errors='coerce')
        mstock_df = mstock_df.dropna(subset=['Trade Date'])
        
        # Clean symbols
        mstock_df['Symbol'] = mstock_df['Scrip / Contract'].apply(clean_symbol)
        
        # Filter only Buys and sort by date ascending (FIFO)
        buys_df = mstock_df[mstock_df['Buy / Sell'].str.upper() == 'BUY'].copy()
        buys_df = buys_df.sort_values(by='Trade Date')
        
        # Build FIFO queues per symbol
        buy_queues = {}
        for _, row in buys_df.iterrows():
            sym = row['Symbol']
            if sym not in buy_queues:
                buy_queues[sym] = []
            buy_queues[sym].append({
                'date': row['Trade Date'],
                'price': float(row['Price']),
                'qty': int(row['Qty']),
                'used': False
            })

    except Exception as e:
        print(f"Error reading {CSV_PATH}: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Find SELLs with missing P&L and that are real trades
        cursor.execute('''
            SELECT * FROM trades 
            WHERE action = 'SELL' 
              AND pnl_gross IS NULL 
              AND broker != 'PAPER'
            ORDER BY timestamp ASC
        ''')
        missing_pnl_trades = cursor.fetchall()
        
        updated_count = 0
        unmatched_count = 0

        for trade in missing_pnl_trades:
            trade_id = trade['id']
            sym = trade['symbol']
            sell_date = pd.to_datetime(trade['timestamp']).tz_localize(None)
            sell_qty = trade['quantity']
            sell_price = trade['price']
            sell_net = trade['net_amount']
            current_strategy = trade['strategy'] or ""

            # Try to find a matching buy
            matched_buy = None
            if sym in buy_queues:
                for buy in buy_queues[sym]:
                    if not buy['used']:
                        # Check date <= sell_date (allow broker settlement/timezone drift if needed)
                        if buy['date'] <= sell_date + timedelta(days=1):
                            matched_buy = buy
                            buy['used'] = True # Mark as used for FIFO
                            break
            
            if matched_buy:
                buy_price = matched_buy['price']
                buy_gross = buy_price * sell_qty
                estimated_fees = estimate_buy_fees(buy_gross)
                buy_net_per_unit = (buy_gross + estimated_fees) / sell_qty
                
                sell_net_per_unit = sell_net / sell_qty

                pnl_gross = (sell_price - buy_price) * sell_qty
                pnl_net = (sell_net_per_unit - buy_net_per_unit) * sell_qty
                
                pnl_pct_gross = (pnl_gross / buy_gross) * 100
                pnl_pct_net = (pnl_net / (buy_net_per_unit * sell_qty)) * 100
                
                new_strategy = f"{current_strategy} [backfilled]".strip()

                if DRY_RUN:
                    print(f"DRY RUN - Update {sym} (ID: {trade_id}): Buy@₹{buy_price:.2f} -> P&L Net: ₹{pnl_net:.2f} ({pnl_pct_net:.1f}%)")
                else:
                    cursor.execute('''
                        UPDATE trades 
                        SET pnl_gross = ?, pnl_net = ?, pnl_pct_gross = ?, pnl_pct_net = ?, strategy = ?
                        WHERE id = ?
                    ''', (pnl_gross, pnl_net, pnl_pct_gross, pnl_pct_net, new_strategy, trade_id))
                    print(f"UPDATED - {sym} (ID: {trade_id}): Buy@₹{buy_price:.2f} -> P&L Net: ₹{pnl_net:.2f}")

                updated_count += 1
            else:
                unmatched_count += 1
                if DRY_RUN:
                    print(f"NOT FOUND - No buy found for {sym} (ID: {trade_id}) on/before {sell_date.date()}")
                else:
                    print(f"WARNING: Could not find matching buy for {sym} (ID: {trade_id})")

        if not DRY_RUN:
            confirm = input(f"\n  Write {updated_count} P&L updates to trades.db? (yes/no): ")
            if confirm.strip().lower() != 'yes':
                print("  Aborted. No changes saved.")
                conn.rollback()
                return
            conn.commit()
            print("\nDatabase changes saved.")
            
        print(f"\n--- Backfill Summary ---")
        print(f"Rows updated: {updated_count}")
        print(f"Still unmatched: {unmatched_count}")

        if DRY_RUN:
            print("\nTo apply these changes, change DRY_RUN = False in the script and re-run.")

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
