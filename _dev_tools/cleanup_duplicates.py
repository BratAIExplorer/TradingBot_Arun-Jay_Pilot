"""
Utility script to clean duplicate stocks from config_table.csv
Keeps only the first occurrence of each Symbol+Exchange pair
"""
import pandas as pd
import os

csv_path = 'config_table.csv'

if not os.path.exists(csv_path):
    print(f"❌ File not found: {csv_path}")
    exit(1)

# Load CSV
df = pd.read_csv(csv_path)
print(f"📊 Loaded {len(df)} rows from CSV")

# Find duplicates
duplicates = df[df.duplicated(subset=['Symbol', 'Exchange'], keep='first')]
print(f"\n🔍 Found {len(duplicates)} duplicate rows:")
print(duplicates[['Symbol', 'Exchange', 'Quantity', 'Buy RSI', 'Sell RSI']])

# Remove duplicates, keeping first occurrence
df_clean = df.drop_duplicates(subset=['Symbol', 'Exchange'], keep='first')
print(f"\n✅ After cleanup: {len(df_clean)} unique rows")

# Backup original
backup_path = 'config_table.csv.backup'
df.to_csv(backup_path, index=False)
print(f"💾 Backup saved to: {backup_path}")

# Save cleaned version
df_clean.to_csv(csv_path, index=False)
print(f"✅ Cleaned CSV saved to: {csv_path}")

print("\n📋 Final stocks:")
print(df_clean[['Symbol', 'Exchange', 'Enabled', 'Quantity']])
