import sys
import os
import requests
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kickstart import API_KEY, ACCESS_TOKEN

def find_reit_symbols():
    url = "https://api.mstock.trade/openapi/typea/instruments/scriptmaster"
    headers = {"Authorization": f"token {API_KEY}:{ACCESS_TOKEN}", "X-Mirae-Version": "1"}
    
    print(f"📡 Downloading Scrip Master from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            print("✅ Download successful. Searching for REITs...")
            # Usually it's a CSV or text file. Let's look at the first 1000 chars
            content = response.text
            lines = content.splitlines()
            print(f"📄 Total lines: {len(lines)}")
            
            targets = ["EMBASSY", "BIRET", "MINDSPACE", "BROOKFIELD"]
            found = []
            
            for line in lines:
                for target in targets:
                    if target in line.upper():
                        found.append(line)
            
            if found:
                print("\n🎯 Found Matches:")
                for f in found:
                    print(f)
            else:
                print("\n❌ No matches found for REITs in the master file.")
                # Show first few lines to see format
                print("\n📋 Header/First lines:")
                for i in range(min(5, len(lines))):
                    print(f"{i}: {lines[i]}")
        else:
            print(f"❌ Failed to download: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    find_reit_symbols()
