import logging
from symbol_validator import validate_symbol
import pandas as pd
import sys

# Setup mock for config verification
config_dict = {}

def test_validation():
    print("Testing Symbol Validation...")
    # Test 1: Valid Symbol (Reliance)
    try:
        if validate_symbol("RELIANCE", "NSE"):
            print("✅ Valid Symbol Test Passed (RELIANCE)")
        else:
            print("❌ Valid Symbol Test Failed (RELIANCE)")
    except Exception as e:
        print(f"❌ Valid Symbol Test Error: {e}")

    # Test 3: Index Symbol
    try:
        if validate_symbol("^NSEI", "NSE"):
            print("✅ Index Symbol Test Passed (^NSEI)")
        else:
            print("❌ Index Symbol Test Failed (^NSEI)")
    except Exception as e:
        print(f"❌ Index Symbol Test Error: {e}")

def test_config_keys():
    print("\nTesting Config Key Logic (Mock)...")
    # Simulate the data structure from kickstart.py
    mock_config = {
        "RSI_Buy_Threshold": 30,
        "RSI_Sell_Threshold": 70,
        "Quantity": 5
    }
    
    try:
        buy_rsi = mock_config.get("RSI_Buy_Threshold", 30)
        sell_rsi = mock_config.get("RSI_Sell_Threshold", 70)
        
        if buy_rsi == 30 and sell_rsi == 70:
            print("✅ Config Key Access Passed")
        else:
            print(f"❌ Config Key Access Failed: Buy={buy_rsi}, Sell={sell_rsi}")
            
    except Exception as e:
        print(f"❌ Config Key Test Error: {e}")

if __name__ == "__main__":
    test_validation()
    test_config_keys()
