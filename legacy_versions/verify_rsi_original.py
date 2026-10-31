import sys
import os

# Add JAY - Copy to path
sys.path.append(os.path.join(os.getcwd(), "JAY - Copy"))

try:
    from getRSI import calculate_intraday_rsi_tv
    print("✅ Successfully imported calculate_intraday_rsi_tv from JAY - Copy")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def test_rsi():
    symbol = "RELIANCE"
    print(f"Testing RSI for {symbol} using ORIGINAL yfinance code...")
    try:
        ts, rsi, df = calculate_intraday_rsi_tv(symbol, period=14, interval="1d")
        print(f"✅ RSI Calculated: {rsi:.2f} at {ts}")
        return True
    except Exception as e:
        print(f"❌ RSI Calculation Failed: {e}")
        return False

if __name__ == "__main__":
    if test_rsi():
        print("\n🎉 Original Code Works.")
    else:
        print("\n🔥 Original Code Also Failed.")
