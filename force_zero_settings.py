import json
import os

SETTINGS_PATH = "settings.json"

def force_zero_defaults():
    if not os.path.exists(SETTINGS_PATH):
        print("Settings file not found to reset.")
        return

    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
        
        # Force Zero Defaults
        if "capital" not in data: data["capital"] = {}
        
        data["capital"]["volume_filter_enabled"] = False
        data["capital"]["min_volume_shares"] = 0
        data["capital"]["min_volume_value"] = 0
        data["capital"]["allocated_limit"] = 0
        data["capital"]["max_per_stock_fixed_amount"] = 0
        
        if "risk" not in data: data["risk"] = {}
        data["risk"]["auto_execute_stop_loss"] = False
        data["risk"]["never_sell_at_loss"] = False
        data["risk"]["trend_filter_enabled"] = True # Keep this enabled as it's a safety net? Or disable for zero-default? 
        # User asked for "Never Sell" & "Auto Exec" specifically. Let's strictly zero out "Active" actions.
        # Trend Filter is passive safety, but consistent with "Manual Enable" philosophy, maybe it should be off? 
        # User didn't complain about Trend Filter. I'll leave it or set False. 
        # Safer to just address specific complaints: Auto Exec & Never Sell.
        
        with open(SETTINGS_PATH, "w") as f:
            json.dump(data, f, indent=4)
            
        print("✅ FORCE RESET: Settings Volume/Capital defaults set to 0/False.")
        
    except Exception as e:
        print(f"❌ Failed to reset settings: {e}")

if __name__ == "__main__":
    force_zero_defaults()
