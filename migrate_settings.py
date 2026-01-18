import json
import os

SETTINGS_FILE = "settings.json"

def migrate_settings():
    print("🔄 Checking settings version...")
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            
            # Check if Reset has been applied
            if data.get("app_settings", {}).get("version") != "2.1":
                print("⚠️  Older settings detected. Applying Zero-Default Policy...")
                
                # Apply Zero Defaults
                if "capital" not in data: data["capital"] = {}
                data["capital"]["allocated_limit"] = 0.0
                data["capital"]["per_trade_pct"] = 0.0
                
                if "app_settings" not in data: data["app_settings"] = {}
                data["app_settings"]["use_regime_monitor"] = False  # OFF by default
                data["app_settings"]["version"] = "2.1"
                
                # Save
                with open(SETTINGS_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                    
                print("✅ Settings reset to Zero Defaults (Capital: 0, Regime: OFF).")
                print("   User must now configure them in the GUI.")
            else:
                print("✅ Settings are up to date (v2.1).")
                
        except Exception as e:
            print(f"❌ Error migrating settings: {e}")

if __name__ == "__main__":
    migrate_settings()
