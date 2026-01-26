import yfinance as yf
import pandas as pd

symbol = "RELIANCE.NS"
print(f"Fetching {symbol}...")
try:
    df = yf.download(symbol, period="1y", interval="1d", progress=False)
    print(f"Dataframe shape: {df.shape}")
    print("Columns:", df.columns)
    if df.empty:
        print("❌ Dataframe is empty.")
    else:
        print("✅ Data fetched successfully.")
        print(df.head())
        
        # Check specific column access (common issue with yfinance updates)
        try:
            close = df['Close']
            print("✅ 'Close' column accessed.")
        except KeyError:
            print("❌ 'Close' column NOT found. Available columns:", df.columns)
            
except Exception as e:
    print(f"❌ Exception: {e}")
