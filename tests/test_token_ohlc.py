import sys
import os
import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kickstart import API_KEY, ACCESS_TOKEN, safe_request

def test_token_ohlc():
    # Test tokens found in scriptmaster
    # EMBASSY: 9383, BIRET: 2203
    test_cases = [
        ("9383", "NSE"),
        ("2203", "NSE"),
        ("EMBASSY", "NSE"),
        ("BIRET", "NSE")
    ]
    
    url = "https://api.mstock.trade/openapi/typea/instruments/quote/ohlc"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    
    for token, exchange in test_cases:
        params = {"i": f"{exchange}:{token}"}
        print(f"\n📡 Testing {params['i']}...")
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Success! Response: {response.json()}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_token_ohlc()
