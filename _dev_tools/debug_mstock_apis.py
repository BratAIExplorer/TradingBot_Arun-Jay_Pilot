import json
import requests
import pyotp
import os

# Load credentials
config_path = "settings.json"
if not os.path.exists(config_path):
    print("❌ settings.json not found")
    exit(1)

with open(config_path, "r") as f:
    config = json.load(f)

broker = config.get("broker", {})
api_key = broker.get("api_key")
totp_secret = broker.get("totp_secret")
access_token = broker.get("access_token") # Try cached first

if not access_token and totp_secret:
    print("📡 Getting fresh access_token via TOTP...")
    totp = pyotp.TOTP(totp_secret)
    otp_code = totp.now()
    totp_resp = requests.post(
        "https://api.mstock.trade/openapi/typea/session/verifytotp",
        data={"api_key": api_key, "totp": otp_code},
        headers={"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    if totp_resp.status_code == 200:
        access_token = totp_resp.json().get("data", {}).get("access_token")

if not access_token:
    print("❌ No access token available")
    exit(1)

headers = {
    "X-Mirae-Version": "1",
    "Authorization": f"token {api_key}:{access_token}"
}

print("\n--- 📦 HOLDINGS (CNC/Settled) ---")
holdings_url = "https://api.mstock.trade/openapi/typea/portfolio/holdings"
resp = requests.get(holdings_url, headers=headers, timeout=10)
if resp.status_code == 200:
    data = resp.json().get("data", [])
    print(f"Found {len(data)} items")
    for pos in data[:5]: # Show first 5
        print(f"  📍 {pos.get('tradingsymbol')}: qty={pos.get('quantity')}, ltp={pos.get('last_price')}")
else:
    print(f"❌ Error: {resp.status_code} - {resp.text}")

print("\n--- 📊 POSITIONS (MIS/Active) ---")
pos_url = "https://api.mstock.trade/openapi/typea/portfolio/positions"
resp = requests.get(pos_url, headers=headers, timeout=10)
if resp.status_code == 200:
    data = resp.json().get("data", [])
    print(f"Found {len(data)} items")
    for pos in data[:5]: # Show first 5
        print(f"  📍 {pos.get('tradingsymbol')}: qty={pos.get('netQty')}, ltp={pos.get('lastPrice')}")
else:
    print(f"❌ Error: {resp.status_code} - {resp.text}")

print("\n--- 💰 FUND SUMMARY ---")
fund_url = "https://api.mstock.trade/openapi/typea/user/fundsummary"
resp = requests.get(fund_url, headers=headers, timeout=10)
if resp.status_code == 200:
    data = resp.json().get("data", [])
    if data:
        f = data[0]
        print(f"  Available: ₹{f.get('AVAILABLE_BALANCE')}")
        print(f"  Utilized: ₹{f.get('AMOUNT_UTILIZED')}")
else:
     print(f"❌ Error: {resp.status_code} - {resp.text}")
