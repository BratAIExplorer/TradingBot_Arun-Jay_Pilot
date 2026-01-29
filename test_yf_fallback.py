import sys
import logging
from symbol_validator import get_symbol_price

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_fallback():
    symbol = "TATASTEEL"
    exchange = "NSE"
    print(f"Testing Fallback Price Fetch for {symbol}:{exchange}...")
    
    price = get_symbol_price(symbol, exchange)
    
    if price:
        print(f"✅ Success! Price: {price}")
    else:
        print("❌ Failed to fetch price.")

if __name__ == "__main__":
    test_fallback()
