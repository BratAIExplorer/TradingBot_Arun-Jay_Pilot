import yfinance as yf
import pandas as pd

symbols = ["EMBASSY.NS", "BIRET.NS", "MINDSPACE.NS", "GOLDBEES.NS"]

print(f"🧪 Testing yfinance for {len(symbols)} symbols...")

for sym in symbols:
    print(f"\n--- Testing {sym} ---")
    try:
        ticker = yf.Ticker(sym)
        # Try fast_info
        info = ticker.fast_info
        print(f"Fast Info LTP: {info.get('last_price')}")
        
        # Try history
        hist = ticker.history(period="1d")
        if not hist.empty:
            print(f"History LTP: {hist['Close'].iloc[-1]}")
        else:
            print("History empty")
    except Exception as e:
        print(f"Error: {e}")
