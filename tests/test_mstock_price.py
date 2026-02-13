import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kickstart import fetch_market_data, log_ok

def test_mstock_prices():
    symbols = [
        ("GOLDBEES", "NSE"), 
        ("ITBEES", "NSE"), 
        ("TATASTEEL", "NSE"),
        ("EMBASSY", "NSE"),
        ("BIRET", "NSE"),
        ("EMBASSY-RR", "NSE"),
        ("BIRET-RR", "NSE"),
        ("542602", "BSE"), # EMBASSY on BSE
        ("543217", "BSE")  # BIRET on BSE
    ]
    print(f"🧪 Testing mStock Price Fetch for {len(symbols)} symbols...")
    
    for symbol, exchange in symbols:
        print(f"\n🔍 Fetching {symbol}:{exchange}...")
        try:
            result, ex = fetch_market_data(symbol, exchange)
            if result:
                print(f"✅ Success! LTP: {result.get('last_price')}")
            else:
                print(f"❌ Failed to fetch price for {symbol}")
        except Exception as e:
            print(f"❌ Exception for {symbol}: {e}")

if __name__ == "__main__":
    test_mstock_prices()
