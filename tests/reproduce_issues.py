
import sys
import os
import logging
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from symbol_validator import validate_symbol
    import kickstart
    # No need to import settings_manager separately if we patch kickstart's instance
except ImportError as e:
    print(f"CRITICAL: Failed to import modules: {e}")
    sys.exit(1)

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def test_reit_validation():
    print("\n--- Testing REIT Symbol Validation (Expect Failure) ---")
    reit_symbols = [("EMBASSY", "NSE"), ("BIRET", "NSE"), ("MINDSPACE", "NSE")]
    
    failed_count = 0
    for sym, ex in reit_symbols:
        print(f"Validating {sym} ({ex})...")
        is_valid = validate_symbol(sym, ex)
        if is_valid:
            print(f"✅ {sym} VALID (Unexpected)")
        else:
            print(f"❌ {sym} INVALID (Reproduction Successful)")
            failed_count += 1
            
    return failed_count

def test_startup_with_reits():
    print("\n--- Testing Engine Startup with REITs (Expect Crash/Error) ---")
    
    # Inject REITs into KICKSTART'S settings instance
    if not kickstart.settings:
        print("⚠️ Kickstart settings not initialized, attempting to init...")
        try:
            from settings_manager import SettingsManager
            kickstart.settings = SettingsManager()
        except:
            print("❌ Could not init settings manager")
            return

    print("Injecting REIT symbols into kickstart.settings...")
    original_stocks = kickstart.settings.get('stocks', [])
    
    test_stocks = [
        {"symbol": "EMBASSY", "exchange": "NSE", "enabled": True, "quantity": 10},
        {"symbol": "BIRET", "exchange": "NSE", "enabled": True, "quantity": 10}
    ]
    
    # Temporarily override settings
    kickstart.settings.settings['stocks'] = test_stocks
    
    try:
        print("Initializing stock configs with REITs...")
        kickstart.initialize_stock_configs()
        
        # Check if they were added to SYMBOLS_TO_TRACK
        print(f"SYMBOLS_TO_TRACK count: {len(kickstart.SYMBOLS_TO_TRACK)}")
        print(f"SYMBOLS: {kickstart.SYMBOLS_TO_TRACK}")
        
        reits_in_track = [s for s in kickstart.SYMBOLS_TO_TRACK if s[0] in ["EMBASSY", "BIRET"]]
        if len(reits_in_track) == 2:
             print("✅ kickstart accepted REIT symbols (Mappings exist in kickstart.py)")
        else:
             print("⚠️ kickstart initialized but symbols missing/ignored?")

        # Try to resolve token (which normally happens during cycle)
        print("Attempting to resolve tokens for REITs...")
        for sym in ["EMBASSY", "BIRET"]:
            token = kickstart.resolve_instrument_token(sym, "NSE")
            if token:
                print(f"✅ Token for {sym}: {token}")
            else:
                print(f"❌ Failed to resolve token for {sym}")

    except Exception as e:
        print(f"❌ CRASH DETECTED in startup/token resolution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore settings
        kickstart.settings.settings['stocks'] = original_stocks

if __name__ == "__main__":
    validation_failures = test_reit_validation()
    test_startup_with_reits()
    
    print("\n--- TEST SUMMARY ---")
    if validation_failures > 0:
        print(f"✅ REIT Validation Issue Reproduced ({validation_failures} failed validation).")
    else:
        print("❌ Could NOT reproduce REIT Validation Issue (Symbols are valid according to YFinance).")
