
import yfinance as yf
from utils import get_yfinance_session

def test_fetch_with_fix(symbol):
    print(f"Testing fetch for {symbol} with get_yfinance_session()...")
    try:
        session = get_yfinance_session()
        
        # Test Ticker(session=...)
        print("  Testing with yf.Ticker(session=...)...")
        t = yf.Ticker(symbol, session=session)
        hist = t.history(period="5d")
        
        if hist.empty:
            print("    Warning: History is empty (but no crash).")
        else:
            print(f"    Success: Fetched {len(hist)} rows.")
            print(f"    Last close: {hist['Close'].iloc[-1]}")

    except Exception as e:
        print(f"    FAIL: {e}")

if __name__ == "__main__":
    test_fetch_with_fix("^NSEI")
    test_fetch_with_fix("MOSCHIP.NS")
    test_fetch_with_fix("MOSCHIP.BO")
