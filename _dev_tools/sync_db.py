
import sys
import os
import kickstart
from database.trades_db import db
from datetime import datetime

def sync_trades():
    print("🔄 Starting Trade Sync (Broker -> DB)...")
    
    # 1. Ensure Authentication
    if not kickstart.ACCESS_TOKEN:
        print("🔑 refreshing token...")
        if not kickstart.handle_token_exception_and_refresh_token():
            print("❌ Failed to obtain access token. Cannot sync.")
            return

    # 2. Fetch Broker Orders
    try:
        orders = kickstart.get_orders_today()
        print(f"📡 Fetched {len(orders)} executed orders from Broker for today.")
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    # 3. Fetch Existing DB Trades
    existing_df = db.get_today_trades()
    if existing_df is None:
        import pandas as pd
        existing_df = pd.DataFrame()
        
    existing_count = len(existing_df)
    print(f"💾 Found {existing_count} trades already in DB.")

    # Convert existing to a set of signatures for easy checking
    # Signature: (Symbol, Action, Quantity) - Timestamp might slightly differ so we'll be lenient or just trust these 3 are unique enough for a single day usually
    # Better: (Symbol, Action, Quantity, Price) is safer.
    existing_sigs = set()
    if not existing_df.empty:
        for idx, row in existing_df.iterrows():
            # row is a Series
            sig = (
                str(row['symbol']).upper(), 
                str(row['action']).upper(), 
                int(row['quantity'])
            )
            existing_sigs.add(sig)

    # 4. Sync Missing
    added = 0
    for o in orders:
        symbol = str(o.get('tradingsymbol')).upper()
        action = str(o.get('transaction_type')).upper()
        qty = int(o.get('quantity', 0))
        price = float(o.get('average_price') or o.get('price') or 0.0)
        exchange = str(o.get('exchange') or 'NSE')
        
        # Deduplication Check
        sig = (symbol, action, qty)
        
        if sig in existing_sigs:
            print(f"⚠️ Skipping duplicate (already in DB): {action} {symbol} ({qty})")
            continue
            
        # Insert into DB
        print(f"📝 Inserting missing trade: {action} {symbol} ({qty}) @ {price}")
        
        # Calculate fees (approximate for log)
        gross_amount = price * qty
        brokerage = max(20, gross_amount * 0.0003)
        total_fees = brokerage * 1.18 # Basic est
        net = gross_amount + total_fees if action == 'BUY' else gross_amount - total_fees
        
        db.insert_trade(
            symbol=symbol,
            exchange=exchange,
            action=action,
            quantity=qty,
            price=price,
            gross_amount=gross_amount,
            total_fees=total_fees,
            net_amount=net,
            strategy="Manual/Synced", # Mark as synced
            reason="Synced from Broker",
            broker="mstock",
            source="BOT"
        )
        added += 1
        
    print(f"✅ Sync Complete. Added {added} missing trades to Database.")

if __name__ == "__main__":
    sync_trades()
