"""Minimal test for mStock TOTP-based Login API"""
import json
import requests
import pyotp
from settings_manager import SettingsManager

# Initialize Settings Manager
settings = SettingsManager()

# Load credentials using SettingsManager for decryption
api_key = settings.get_decrypted("broker.api_key")
totp_secret = settings.get_decrypted("broker.totp_secret")

if not api_key or not totp_secret:
    print("❌ Error: API Key or TOTP Secret missing in settings.json")
    exit(1)

print(f"API Key: {api_key[:10]}... (Decrypted)")
print(f"TOTP Secret: {totp_secret[:10]}... (Decrypted)")

# Generate TOTP
totp = pyotp.TOTP(totp_secret)
otp_code = totp.now()
print(f"Generated TOTP: {otp_code}")

# Call Verify TOTP API
print("\n📡 Calling Verify TOTP API...")
url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://trade.mstock.com",
    "Referer": "https://trade.mstock.com/",
    "X-Mirae-Version": "1",
    "Content-Type": "application/x-www-form-urlencoded"
}
payload = {"api_key": api_key, "totp": otp_code}

resp = requests.post(url, data=payload, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

if resp.status_code == 200:
    data = resp.json()
    if data.get("status") == "success":
        token = data.get("data", {}).get("access_token")
        if token:
            print(f"\n✅ SUCCESS! access_token: {token[:50]}...")
        else:
            print("❌ No access_token in response!")
    else:
        print(f"❌ API Error: {data.get('message')}")
else:
    print(f"❌ HTTP Error {resp.status_code}")
