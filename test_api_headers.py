import requests
import json
import os
import pyotp
from settings_manager import SettingsManager

settings = SettingsManager()
settings.load()

api_key = settings.get_decrypted("broker.api_key")
totp_secret = settings.get_decrypted("broker.totp_secret")

if not api_key or not totp_secret:
    print("❌ Missing credentials in settings.json")
    exit(1)

totp = pyotp.TOTP(totp_secret)
otp_code = totp.now()

url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
payload = {"api_key": api_key, "totp": otp_code}

def test_headers(name, headers):
    print(f"\n--- Testing: {name} ---")
    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

# 1. Basic Headers (Minimal)
test_headers("Minimal Headers", {
    "X-Mirae-Version": "1",
    "Content-Type": "application/x-www-form-urlencoded"
})

# 2. Browser Headers (Current kickstart logic)
test_headers("Browser Headers", {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "X-Mirae-Version": "1",
    "Content-Type": "application/x-www-form-urlencoded"
})

# 3. Browser Headers + Sec Chars
test_headers("Full Browser Headers", {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "X-Mirae-Version": "1",
    "Content-Type": "application/x-www-form-urlencoded"
})
