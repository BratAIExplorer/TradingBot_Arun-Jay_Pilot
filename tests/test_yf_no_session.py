
import yfinance as yf

def test_simple_download():
    print("Testing yf.download WITHOUT session...")
    try:
        data = yf.download("RELIANCE.NS", period="5d", progress=False)
        if not data.empty:
            print(f"✅ Success! Downloaded {len(data)} rows.")
            print(data.head())
        else:
            print("⚠️ Downloaded empty data.")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_simple_download()
