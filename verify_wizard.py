from settings_manager import SettingsManager
from first_run_wizard import should_show_wizard

print("--- Wizard Logic Verification ---")
try:
    s = SettingsManager()
    s.load()

    has_key = bool(s.get("broker.api_key"))
    has_code = bool(s.get("broker.client_code"))
    first_run_flag = s.get("app_settings.first_run_completed", False)

    print(f"Settings Present: API Key={has_key}, Client Code={has_code}")
    print(f"First Run Flag: {first_run_flag}")

    should_show = should_show_wizard()
    print(f"RESULT: Should Show Wizard? -> {should_show}")

    if has_key and has_code and not should_show:
        print("✅ SUCCESS: Wizard skipped because credentials exist.")
    elif not has_key and should_show:
        print("✅ SUCCESS: Wizard shown because credentials missing.")
    else:
        print("⚠️  CHECK LOGIC: Unexpected result.")

except Exception as e:
    print(f"❌ FAIL: Script error - {e}")
