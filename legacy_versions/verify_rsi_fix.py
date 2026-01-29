import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from getRSI import calculate_intraday_rsi_tv
    print("✅ Successfully imported calculate_intraday_rsi_tv")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def test_rsi():
    symbol = "RELIANCE"
    print(f"Testing RSI for {symbol} using yfinance...")
    try:
        # Use 1d interval for stability in test
        ts, rsi, df = calculate_intraday_rsi_tv(symbol, period=14, interval="1d")
        print(f"✅ RSI Calculated: {rsi:.2f} at {ts}")
        print("Last 3 rows:")
        print(df.tail(3))
        return True
    except Exception as e:
        print(f"❌ RSI Calculation Failed: {e}")
        return False

if __name__ == "__main__":
    if test_rsi():
        print("\n🎉 Verification Passed: yfinance is working.")
    else:
        print("\n🔥 Verification Failed.")
