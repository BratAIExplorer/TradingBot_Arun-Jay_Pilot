import requests
import json

# Load credentials
with open("settings.json", "r") as f:
    settings = json.load(f)

api_key = settings["broker"]["api_key"]
access_token = settings["broker"]["access_token"]

# Mirae Master URL
url = "https://api.mstock.trade/openapi/typea/instruments/scriptmaster"
headers = {
    "Authorization": f"token {api_key}:{access_token}",
    "X-Mirae-Version": "1"
}

print(f"📡 Attempting to download NSE Master...")
try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        content = resp.text
        print(f"✅ Success! Content length: {len(content)}")
        with open("nse_master.csv", "w", encoding="utf-8") as f:
            f.write(content)
        print("💾 Saved to nse_master.csv")
    else:
        print(f"❌ Failed: {resp.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")
