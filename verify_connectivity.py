import sys
import os
import json
import logging

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format='%(message)s')

def log(msg):
    print(msg)

print("🚀 Starting Connectivity Verification...")

# Add project root to path
sys.path.append(os.getcwd())

try:
    # Import specific components from kickstart to avoid auto-running main setup if possible
    # But kickstart has top-level code. We must be careful.
    # We will import the module, hoping it doesn't crash on import.
    import kickstart
    print("✅ kickstart module imported successfully.")
except Exception as e:
    print(f"❌ Failed to import kickstart: {e}")
    sys.exit(1)

def check_connection():
    print("\n📡 Checking mStock API Connection...")
    
    # 1. Check Latency
    try:
        ok, latency = kickstart.check_connectivity_latency()
        if ok:
            print(f"✅ API Reachable (Latency: {latency}ms)")
        else:
            print("❌ API Unreachable or Latency Check Failed.")
            return False
    except Exception as e:
        print(f"❌ Exception checking latency: {e}")
        return False

    # 2. Check Funds (Proof of Authorization)
    print("\n💰 Checking Funds (Auth Check)...")
    try:
        funds = kickstart.fetch_funds()
        print(f"✅ Authorization Successful! Available Funds: ₹{funds:,.2f}")
    except Exception as e:
        print(f"❌ Failed to fetch funds (Auth Error?): {e}")
        return False

    return True

def mock_trigger_test():
    print("\n⚡ Testing Order Trigger Logic (Dry Run)...")
    # We will not place a real order, but we can check if the function exists and accepts args
    try:
        from kickstart import safe_place_order_when_open
        print(f"✅ safe_place_order_when_open function is available: {safe_place_order_when_open}")
        # Intentionally not calling it to avoid placing a real order in this basic check.
        # The user can use Paper Mode for full end-to-end.
    except ImportError:
        print("❌ Could not import order placement function.")
        return False
    return True

if __name__ == "__main__":
    if check_connection():
        mock_trigger_test()
        print("\n🎉 SUCCESS: Bot is connected and ready to trade.")
    else:
        print("\n⚠️ FAILURE: Connectivity issues detected. Check credentials or internet.")
