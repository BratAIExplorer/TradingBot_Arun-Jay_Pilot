"""
Test script to verify dashboard rendering and button visibility
"""
import sys
import re

def test_button_code_exists():
    """Test 1: Verify button code is in dashboard_v2.py"""
    print("Test 1: Checking if button code exists in dashboard_v2.py...")
    
    with open('dashboard_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for button code
    has_start_button = 'self.btn_start = ctk.CTkButton' in content
    has_panic_button = 'self.btn_panic = ctk.CTkButton' in content
    has_system_controls = 'SYSTEM CONTROLS' in content
    
    print(f"  - START button code found: {has_start_button}")
    print(f"  - PANIC button code found: {has_panic_button}")
    print(f"  - SYSTEM CONTROLS card found: {has_system_controls}")
    
    if all([has_start_button, has_panic_button, has_system_controls]):
        print("✅ Test 1 PASSED: Button code exists\n")
        return True
    else:
        print("❌ Test 1 FAILED: Button code missing\n")
        return False

def test_sector_watchlist_naming():
    """Test 2: Verify naming change"""
    print("Test 2: Checking SECTOR WATCHLIST naming...")
    
    with open('dashboard_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_new_name = 'SECTOR WATCHLIST' in content
    has_old_name = 'SECTOR BASKETS (BUCKETS)' in content
    
    print(f"  - New name 'SECTOR WATCHLIST' found: {has_new_name}")
    print(f"  - Old name 'SECTOR BASKETS (BUCKETS)' found: {has_old_name}")
    
    if has_new_name and not has_old_name:
        print("✅ Test 2 PASSED: Naming updated correctly\n")
        return True
    else:
        print("❌ Test 2 FAILED: Naming not updated\n")
        return False

def test_scrollable_frame():
    """Test 3: Verify scrollable frame in stock dialog"""
    print("Test 3: Checking scrollable frame in settings_gui.py...")
    
    with open('settings_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_scrollable = 'CTkScrollableFrame' in content and 'show_stock_dialog' in content
    has_cancel_button = 'Cancel' in content and 'dialog.destroy' in content
    
    print(f"  - CTkScrollableFrame found: {has_scrollable}")
    print(f"  - Cancel button found: {has_cancel_button}")
    
    if has_scrollable and has_cancel_button:
        print("✅ Test 3 PASSED: UI improvements present\n")
        return True
    else:
        print("❌ Test 3 FAILED: UI improvements missing\n")
        return False

def test_validation_improvements():
    """Test 4: Verify validation improvements"""
    print("Test 4: Checking validation improvements...")
    
    with open('symbol_validator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_retry = 'retries' in content
    has_tuple_return = 'Tuple[bool, str]' in content
    has_timeout = 'timeout' in content
    has_smart_exchange = '_try_validate_symbol' in content
    
    print(f"  - Retry logic found: {has_retry}")
    print(f"  - Tuple return type found: {has_tuple_return}")
    print(f"  - Timeout handling found: {has_timeout}")
    print(f"  - Smart exchange detection found: {has_smart_exchange}")
    
    if all([has_retry, has_tuple_return, has_timeout, has_smart_exchange]):
        print("✅ Test 4 PASSED: Validation improvements present\n")
        return True
    else:
        print("❌ Test 4 FAILED: Validation improvements incomplete\n")
        return False

def test_capital_display_code():
    """Test 5: Check if capital display code exists"""
    print("Test 5: Checking capital display code...")
    
    with open('dashboard_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for Safety Box or capital display code
    has_safety_box = 'Safety Box' in content or 'SAFETY BOX' in content
    has_capital_limit = 'allocated_limit' in content or 'capital' in content.lower()
    
    print(f"  - Safety Box display found: {has_safety_box}")
    print(f"  - Capital limit code found: {has_capital_limit}")
    
    if has_safety_box:
        print("✅ Test 5 PASSED: Capital display code exists\n")
        return True
    else:
        print("⚠️  Test 5 WARNING: Need to verify capital display location\n")
        return False

if __name__ == "__main__":
    print("="*60)
    print("DASHBOARD & SETTINGS VERIFICATION TEST SUITE")
    print("="*60)
    print()
    
    results = []
    results.append(("Button Code", test_button_code_exists()))
    results.append(("Naming Change", test_sector_watchlist_naming()))
    results.append(("UI Improvements", test_scrollable_frame()))
    results.append(("Validation", test_validation_improvements()))
    results.append(("Capital Display", test_capital_display_code()))
    
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Code changes are in place!")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED - Code changes incomplete!")
        sys.exit(1)
