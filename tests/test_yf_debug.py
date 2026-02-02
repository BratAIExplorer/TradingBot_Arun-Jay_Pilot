
import yfinance as yf
import requests

def test_fetch(symbol):
    print(f"Testing fetch for {symbol}...")
    try:
        # Create a session with custom headers
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        # Method 1: Standard
        print("  Method 1: Standard fetch")
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if hist.empty:
            print("    Empty history (Method 1)")
        else:
            print(f"    Success (Method 1): {len(hist)} rows")
            
    except Exception as e:
        print(f"    Error (Method 1): {e}")

    try:
        # Method 2: With Session (if supported by installed yf version)
        print("  Method 2: Fetch with Session")
        try:
            t = yf.Ticker(symbol, session=session)
            hist = t.history(period="5d")
            if hist.empty:
                print("    Empty history (Method 2)")
            else:
                print(f"    Success (Method 2): {len(hist)} rows")
        except TypeError:
             print("    yfinance installed version might not support 'session' arg in Ticker constructor.")

    except Exception as e:
        print(f"    Error (Method 2): {e}")

if __name__ == "__main__":
    test_fetch("^NSEI")
    test_fetch("MOSCHIP.NS")
    test_fetch("MOSCHIP.BO")
