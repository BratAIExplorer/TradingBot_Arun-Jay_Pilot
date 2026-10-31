from settings_manager import SettingsManager
import json
import os

print("--- Settings Diagnostic ---")
try:
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as f:
            raw = json.load(f)
            print("Raw settings.json keys:", list(raw.keys()))
            if "broker" in raw:
                print("Broker keys:", list(raw["broker"].keys()))
                print(f"API Key present: {bool(raw['broker'].get('api_key'))}")
                print(f"Client Code present: {bool(raw['broker'].get('client_code'))}")
            else:
                print("❌ 'broker' section MISSING in settings.json")
    else:
        print("❌ settings.json NOT FOUND")

    s = SettingsManager()
    val_key = s.get("broker.api_key")
    val_code = s.get("broker.client_code")
    
    print(f"\nSettingsManager.get('broker.api_key'): {bool(val_key)} (Type: {type(val_key)})")
    print(f"SettingsManager.get('broker.client_code'): {bool(val_code)} (Type: {type(val_code)})")
    
    from first_run_wizard import should_show_wizard
    print(f"\nshould_show_wizard() returns: {should_show_wizard()}")

except Exception as e:
    print(f"❌ Error: {e}")
