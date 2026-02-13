import requests
import json
from urllib.parse import urlencode

# Load credentials from settings.json
with open("settings.json", "r") as f:
    settings = json.load(f)

api_key = settings["broker"]["api_key"]
access_token = settings["broker"]["access_token"]

url = "https://api.mstock.trade/openapi/typea/instruments/quote/ohlc"
headers = {
    "Authorization": f"token {api_key}:{access_token}",
    "X-Mirae-Version": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

symbols = [
    ("NSE", "EMBASSY"),
    ("NSE", "EMBASSY.RR"),
    ("NSE", "EMBASSY-RR"),
    ("NSE", "BIRET"),
    ("NSE", "BIRET.RR"),
    ("NSE", "BIRET-RR"),
]

for ex, sym in symbols:
    print(f"\n--- Testing {ex}:{sym} ---")
    params = {"i": f"{ex}:{sym}"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
