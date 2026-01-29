"""Test Fund Summary API with fresh token"""
import json
import requests
import pyotp

# Load credentials
with open("settings.json", "r") as f:
    config = json.load(f)

broker = config.get("broker", {})
api_key = broker.get("api_key")
totp_secret = broker.get("totp_secret")

print("📡 Step 1: Getting fresh access_token via TOTP...")
totp = pyotp.TOTP(totp_secret)
otp_code = totp.now()

totp_resp = requests.post(
    "https://api.mstock.trade/openapi/typea/session/verifytotp",
    data={"api_key": api_key, "totp": otp_code},
    headers={"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"},
    timeout=10
)

if totp_resp.status_code != 200:
    print(f"❌ TOTP failed: {totp_resp.status_code}")
    exit(1)

totp_data = totp_resp.json()
if totp_data.get("status") != "success":
    print(f"❌ TOTP error: {totp_data.get('message')}")
    exit(1)

access_token = totp_data.get("data", {}).get("access_token")
print(f"✅ Got access_token: {access_token[:30]}...")

print("\n📡 Step 2: Calling Fund Summary API...")
fund_url = "https://api.mstock.trade/openapi/typea/user/fundsummary"
fund_headers = {
    "X-Mirae-Version": "1",
    "Authorization": f"token {api_key}:{access_token}"
}

fund_resp = requests.get(fund_url, headers=fund_headers, timeout=10)
print(f"Status: {fund_resp.status_code}")
print(f"Response: {fund_resp.text[:500]}")

if fund_resp.status_code == 200:
    fund_data = fund_resp.json()
    if fund_data.get("status") == "success":
        data_list = fund_data.get("data", [])
        if data_list:
            available = data_list[0].get("AVAILABLE_BALANCE", "N/A")
            utilized = data_list[0].get("AMOUNT_UTILIZED", "N/A")
            print(f"\n✅ FUND SUMMARY:")
            print(f"   Available Balance: ₹{available}")
            print(f"   Amount Utilized: ₹{utilized}")
        else:
            print("❌ No data in response")
    else:
        print(f"❌ API Error: {fund_data.get('message')}")
else:
    print(f"❌ HTTP Error: {fund_resp.status_code}")
