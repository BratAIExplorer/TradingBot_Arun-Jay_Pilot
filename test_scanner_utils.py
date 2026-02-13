import pandas as pd
from utils import fetch_yahoo_history_direct

def test_fetch():
    symbol = "RELIANCE.NS"
    print(f"Testing fetch for {symbol}...")
    df = fetch_yahoo_history_direct(symbol, period="3mo", interval="1d")
    if not df.empty:
        print(f"✅ Success! Fetched {len(df)} rows.")
        print(df.head())
    else:
        print("❌ Failed to fetch data.")

if __name__ == "__main__":
    test_fetch()
