import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("MATCH_VERIFICATION: Importing kickstart...")
    # Mocking dependencies if needed, but simple import should catch syntax errors
    import kickstart
    print("MATCH_VERIFICATION: kickstart imported successfully.")
    
    print("MATCH_VERIFICATION: Checking new functions...")
    if hasattr(kickstart, 'fetch_all_open_orders'):
        print("MATCH_VERIFICATION: fetch_all_open_orders FOUND.")
    else:
        print("MATCH_VERIFICATION: fetch_all_open_orders NOT FOUND.")
        sys.exit(1)

    print("MATCH_VERIFICATION: Checking Modified signatures...")
    import inspect
    sig_orders = inspect.signature(kickstart.check_existing_orders)
    if 'orders_cache' in sig_orders.parameters:
        print("MATCH_VERIFICATION: check_existing_orders accepts orders_cache.")
    else:
        print("MATCH_VERIFICATION: check_existing_orders MISSING orders_cache.")
        sys.exit(1)

    sig_rsi = inspect.signature(kickstart.get_stabilized_rsi)
    # Just checking it exists and compiles
    
    print("MATCH_VERIFICATION: Importing risk_manager...")
    import risk_manager
    sig_risk = inspect.signature(risk_manager.RiskManager.check_all_positions)
    if 'market_data_cache' in sig_risk.parameters:
        print("MATCH_VERIFICATION: RiskManager.check_all_positions accepts market_data_cache.")
    else:
         print("MATCH_VERIFICATION: RiskManager.check_all_positions MISSING market_data_cache.")
         sys.exit(1)

    print("MATCH_VERIFICATION: ALL CHECKS PASSED.")

except ImportError as e:
    print(f"MATCH_VERIFICATION: Import Failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"MATCH_VERIFICATION: Verification Failed: {e}")
    sys.exit(1)
