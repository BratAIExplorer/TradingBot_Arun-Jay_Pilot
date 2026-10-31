# -*- coding: utf-8 -*-
"""
Complete Trade Audit & Reconciliation
Reads mStock Excel files and compares with local database
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import sqlite3
from datetime import datetime
import os

print("=" * 80)
print("AUDIT START: Full Trade Reconciliation")
print("=" * 80)

# Step 1: Read Excel files
print("\n[1/5] READING mStock EXCEL FILES")
print("-" * 80)

file1 = r"C:\Users\user\Downloads\TradeHistory_01Apr25_to_31Mar26_MA8224736.xlsx"
file2 = r"C:\Users\user\Downloads\TradeHistory_20Mar26_to_21Jun26_MA8224736.xlsx"

dfs = []
for file in [file1, file2]:
    try:
        fname = os.path.basename(file)
        df = pd.read_excel(file, skiprows=16)
        print(f"  OK: {fname} ({len(df)} rows)")
        dfs.append(df)
    except Exception as e:
        print(f"  ERROR: {os.path.basename(file)} - {e}")

if not dfs:
    print("ERROR: No Excel files loaded")
    sys.exit(1)

# Combine Excel files
mstock = pd.concat(dfs, ignore_index=True)
before = len(mstock)

# Remove exact duplicates from overlap period
mstock = mstock.drop_duplicates()
after = len(mstock)

print(f"\n  Combined: {before} rows")
print(f"  After dedup: {after} rows (removed {before-after} duplicates from overlap)")

# Normalize columns
if 'Trade Date' in mstock.columns:
    mstock['Trade Date'] = pd.to_datetime(mstock['Trade Date'], format='%d-%m-%Y', errors='coerce')

if 'Scrip / Contract' in mstock.columns:
    mstock['Symbol'] = mstock['Scrip / Contract'].str.replace(r'-(EQ|EXT|XT|A|BE|IF|X)$', '', regex=True).str.strip()

if 'Buy / Sell' in mstock.columns:
    mstock['Action'] = mstock['Buy / Sell'].str.strip().str.upper()

if 'Qty' in mstock.columns:
    mstock['Qty'] = pd.to_numeric(mstock['Qty'], errors='coerce').astype('Int64')

if 'Price' in mstock.columns:
    mstock['Price'] = pd.to_numeric(mstock['Price'], errors='coerce')

print(f"\n  Date range: {mstock['Trade Date'].min().date()} to {mstock['Trade Date'].max().date()}")
print(f"  BUY trades: {len(mstock[mstock['Action']=='BUY'])}")
print(f"  SELL trades: {len(mstock[mstock['Action']=='SELL'])}")
print(f"  Unique symbols: {mstock['Symbol'].nunique()}")

# Step 2: Load local database
print("\n[2/5] READING LOCAL DATABASE")
print("-" * 80)

conn = sqlite3.connect('database/trades.db')
local = pd.read_sql_query("SELECT * FROM trades WHERE broker != 'PAPER'", conn)
conn.close()

local['timestamp'] = pd.to_datetime(local['timestamp'])
local['date'] = local['timestamp'].dt.date

print(f"  OK: Loaded {len(local)} real trades from database")
print(f"  BUY trades: {len(local[local['action']=='BUY'])}")
print(f"  SELL trades: {len(local[local['action']=='SELL'])}")
print(f"  Unique symbols: {local['symbol'].nunique()}")

# Step 3: Find orphaned trades (in mStock but not in DB)
print("\n[3/5] RECONCILIATION - FINDING ORPHANED TRADES")
print("-" * 80)

orphaned = []
matched = 0

for idx, row in mstock.iterrows():
    symbol = row['Symbol']
    qty = int(row['Qty']) if pd.notna(row['Qty']) else 0
    action = row['Action']
    trade_date = row['Trade Date'].date()
    price = row['Price']
    trade_id = row.get('Trade Id', '')

    # Find in local DB (allow 1 day tolerance)
    try:
        date_diff = (pd.to_datetime(local['date']) - trade_date).dt.days.abs() <= 1
    except:
        date_diff = pd.Series([False] * len(local))

    match = local[
        (local['symbol'] == symbol) &
        (local['quantity'] == qty) &
        (local['action'] == action) &
        (date_diff)
    ]

    if match.empty:
        orphaned.append({
            'Symbol': symbol,
            'Action': action,
            'Qty': qty,
            'Price': price,
            'Date': trade_date,
            'Trade_ID': trade_id
        })
    else:
        matched += 1

orphaned_df = pd.DataFrame(orphaned) if orphaned else pd.DataFrame()

print(f"  Matched: {matched}/{len(mstock)}")
print(f"  Orphaned (missing from DB): {len(orphaned_df)}")

if not orphaned_df.empty:
    orphaned_df.to_csv('AUDIT_orphaned_trades.csv', index=False)
    print(f"\n  Top orphaned trades by symbol:")
    for sym in orphaned_df['Symbol'].value_counts().head(15).index:
        count = len(orphaned_df[orphaned_df['Symbol'] == sym])
        print(f"    {sym:12} {count:3} trades missing from DB")

# Step 4: Find duplicates in local DB
print("\n[4/5] RECONCILIATION - FINDING DUPLICATES IN DB")
print("-" * 80)

duplicates = local[local.duplicated(
    subset=['symbol', 'action', 'quantity', 'price', 'date'],
    keep=False
)].sort_values(['symbol', 'timestamp'])

if not duplicates.empty:
    duplicates.to_csv('AUDIT_duplicate_trades.csv', index=False)
    print(f"  Found {len(duplicates)} duplicate records")
    print(f"  Symbols with duplicates:")
    for sym in duplicates['symbol'].unique():
        count = len(duplicates[duplicates['symbol'] == sym])
        ids = duplicates[duplicates['symbol'] == sym]['id'].tolist()
        print(f"    {sym:12} {count} records (IDs: {ids})")
else:
    print(f"  No duplicates found - OK")

# Step 5: Check for missing P&L
print("\n[5/5] RECONCILIATION - P&L COMPLETENESS")
print("-" * 80)

sells = local[local['action'] == 'SELL'].copy()
sells_with_pnl = sells[sells['pnl_gross'].notna()]
sells_no_pnl = sells[sells['pnl_gross'].isna()]

print(f"  Total SELL trades: {len(sells)}")
print(f"  With P&L calculated: {len(sells_with_pnl)}")
print(f"  Missing P&L (NULL): {len(sells_no_pnl)}")

if not sells_no_pnl.empty:
    sells_no_pnl.to_csv('AUDIT_missing_pnl.csv', index=False)
    print(f"\n  Symbols missing P&L:")
    for sym in sells_no_pnl['symbol'].value_counts().head(15).index:
        count = len(sells_no_pnl[sells_no_pnl['symbol'] == sym])
        print(f"    {sym:12} {count:2} sells missing P&L")

# Performance analysis
print("\n" + "=" * 80)
print("PERFORMANCE SUMMARY")
print("=" * 80)

if not sells_with_pnl.empty:
    wins = len(sells_with_pnl[sells_with_pnl['pnl_net'] > 0])
    losses = len(sells_with_pnl[sells_with_pnl['pnl_net'] < 0])
    breakeven = len(sells_with_pnl[sells_with_pnl['pnl_net'] == 0])

    total_pnl = sells_with_pnl['pnl_net'].sum()
    avg_pnl = sells_with_pnl['pnl_net'].mean()
    best = sells_with_pnl['pnl_net'].max()
    worst = sells_with_pnl['pnl_net'].min()

    print(f"\nTrades with P&L: {len(sells_with_pnl)}")
    print(f"  Winning trades: {wins} ({wins/len(sells_with_pnl)*100:.1f}%)")
    print(f"  Losing trades:  {losses} ({losses/len(sells_with_pnl)*100:.1f}%)")
    print(f"  Breakeven trades: {breakeven}")

    print(f"\nP&L Metrics:")
    print(f"  Total P&L: Rs {total_pnl:>12,.2f}")
    print(f"  Avg/trade: Rs {avg_pnl:>12,.2f}")
    print(f"  Best: Rs {best:>18,.2f}")
    print(f"  Worst: Rs {worst:>17,.2f}")

    # Best and worst symbols
    pnl_summary = sells_with_pnl.groupby('symbol')['pnl_net'].agg(['sum', 'count']).sort_values('sum', ascending=False)

    print(f"\nTop 10 Best Performing Symbols:")
    for sym, row in pnl_summary.head(10).iterrows():
        print(f"  {sym:12} Rs {row['sum']:>12,.2f}  ({int(row['count']):2} trades)")

    print(f"\nTop 10 Worst Performing Symbols:")
    for sym, row in pnl_summary.tail(10).iterrows():
        print(f"  {sym:12} Rs {row['sum']:>12,.2f}  ({int(row['count']):2} trades)")

# Final summary
print("\n" + "=" * 80)
print("AUDIT RESULTS - DATA QUALITY ASSESSMENT")
print("=" * 80)

match_rate = (matched / len(mstock) * 100) if len(mstock) > 0 else 0

print(f"\nReconciliation Status:")
print(f"  Matched trades: {match_rate:.1f}% ({matched}/{len(mstock)})")
print(f"  Orphaned (in mStock, missing from DB): {len(orphaned_df)}")
print(f"  Duplicates in DB: {len(duplicates)}")
print(f"  Sells missing P&L: {len(sells_no_pnl)}")

if match_rate >= 95:
    quality = "EXCELLENT"
elif match_rate >= 90:
    quality = "GOOD"
elif match_rate >= 80:
    quality = "FAIR"
else:
    quality = "POOR"

print(f"\nOVERALL DATA QUALITY: {quality}")

print(f"\nGenerated audit files:")
if not orphaned_df.empty:
    print(f"  AUDIT_orphaned_trades.csv ({len(orphaned_df)} records)")
if not duplicates.empty:
    print(f"  AUDIT_duplicate_trades.csv ({len(duplicates)} records)")
if not sells_no_pnl.empty:
    print(f"  AUDIT_missing_pnl.csv ({len(sells_no_pnl)} records)")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
