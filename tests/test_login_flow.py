"""Minimal test for mStock Login API"""
import json
import requests
import pyotp
import hashlib

# Load credentials
with open("settings.json", "r") as f:
    config = json.load(f)

broker = config.get("broker", {})
client_code = broker.get("client_code")
password = broker.get("password")
api_key = broker.get("api_key")
api_secret = broker.get("api_secret")
totp_secret = broker.get("totp_secret")

print(f"Client: {client_code}")
print(f"API Key: {api_key[:10]}...")

# Step 1: Login
print("\n📡 Step 1: Calling Login API...")
login_url = "https://api.mstock.trade/openapi/typea/connect/login"
login_resp = requests.post(login_url, data={"username": client_code, "password": password}, headers={"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
print(f"   Status: {login_resp.status_code}")
print(f"   Response: {login_resp.text}")

if login_resp.status_code == 200:
    login_data = login_resp.json()
    print(f"   Parsed: {json.dumps(login_data, indent=2)}")
    
    # Check if request_token exists
    request_token = None
    if "data" in login_data and isinstance(login_data["data"], dict):
        request_token = login_data["data"].get("request_token")
    
    if request_token:
        print(f"✅ Got request_token: {request_token[:20]}...")
        
        # Step 2: Verify TOTP
        print("\n📡 Step 2: Verifying TOTP...")
        totp = pyotp.TOTP(totp_secret)
        otp_code = totp.now()
        print(f"   TOTP: {otp_code}")
        
        totp_url = "https://api.mstock.trade/openapi/typea/session/verifytotp"
        totp_resp = requests.post(totp_url, data={"request_token": request_token, "totp": otp_code}, headers={"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
        print(f"   Status: {totp_resp.status_code}")
        print(f"   Response: {totp_resp.text}")
        
        if totp_resp.status_code == 200:
            totp_data = totp_resp.json()
            if totp_data.get("status") == "success":
                print("✅ TOTP verified!")
                
                # Step 3: Get Session Token
                print("\n📡 Step 3: Getting Session Token...")
                checksum = hashlib.sha256((api_key + request_token + api_secret).encode()).hexdigest()
                session_url = "https://api.mstock.trade/openapi/typea/session/token"
                session_resp = requests.post(session_url, data={"api_key": api_key, "request_token": request_token, "checksum": checksum}, headers={"X-Mirae-Version": "1", "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
                print(f"   Status: {session_resp.status_code}")
                print(f"   Response: {session_resp.text}")
    else:
        print("❌ No request_token in response!")
