import requests
import time

try:
    print("Testing /api/logs endpoint...")
    response = requests.get("http://127.0.0.1:8000/api/logs")
    if response.status_code == 200:
        data = response.json()
        logs = data.get("logs", [])
        print(f"✅ Success! Received {len(logs)} logs.")
        if logs:
            print("--- Sample Log ---")
            print(logs[-1])
            print("------------------")
        else:
            print("⚠️ Response valid but log list is EMPTY.")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
