import requests
import json

BASE_URL = "http://localhost:8000"

def test_settings_api():
    print("🧪 Testing Settings API...")
    
    # 1. READ Settings
    try:
        res = requests.get(f"{BASE_URL}/api/settings")
        if res.status_code == 200:
            print("✅ GET /api/settings: Success")
            # print(json.dumps(res.json(), indent=2))
        else:
            print(f"❌ GET /api/settings: Failed ({res.status_code})")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. UPDATE Settings
    new_settings = {
        "risk": {
            "stop_loss_pct": 9.9,  # Unique value for testing
            "profit_target_pct": 15.5
        }
    }
    try:
        res = requests.post(f"{BASE_URL}/api/settings", json=new_settings)
        if res.status_code == 200:
             print("✅ POST /api/settings: Success")
        else:
             print(f"❌ POST /api/settings: Failed ({res.status_code}) {res.text}")
             
        # Verify update
        res = requests.get(f"{BASE_URL}/api/settings")
        data = res.json()
        if data.get("risk", {}).get("stop_loss_pct") == 9.9:
            print("✅ Verification: Settings persisted correctly.")
        else:
            print(f"❌ Verification: Settings NOT persisted. Got: {data.get('risk', {})}")
            
    except Exception as e:
        print(f"❌ Update Error: {e}")

    # 3. STOCK Operations
    test_stock = {
        "symbol": "TEST_STOCK_APIV2",
        "exchange": "NSE",
        "strategy": "MOCK",
        "enabled": True
    }
    
    # Add
    try:
        res = requests.post(f"{BASE_URL}/api/stocks", json=test_stock)
        print(f"✅ ADD Stock: {res.status_code}")
    except: pass
    
    # List
    try:
        res = requests.get(f"{BASE_URL}/api/stocks")
        stocks = res.json()
        found = any(s["symbol"] == "TEST_STOCK_APIV2" for s in stocks)
        if found: print("✅ Stock found in list")
        else: print("❌ Stock NOT found in list")
    except: pass
    
    # Delete
    try:
        res = requests.delete(f"{BASE_URL}/api/stocks/TEST_STOCK_APIV2")
        print(f"✅ DELETE Stock: {res.status_code}")
    except: pass

if __name__ == "__main__":
    test_settings_api()
