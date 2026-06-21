#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for ORBIT v2.6.0 UX fixes
Verifies BUG-010, BUG-011, BUG-012 without needing GUI
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 70)
print("[TEST] ORBIT v2.6.0 - UX Fixes Verification")
print("=" * 70)
print()

# ============================================================================
# TEST 1: BUG-010 - Dashboard Title
# ============================================================================
print("[TEST 1] BUG-010 - Dashboard Title Rebrand")
print("-" * 70)

try:
    import re

    with open('sensei_v1_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Look for window title
    title_match = re.search(r'self\.root\.title\("([^"]+)"\)', content)

    if title_match:
        title = title_match.group(1)
        print(f"[OK] Found window title: {title}")

        if "ORBIT TRADING" in title:
            print("[PASS] Title correctly shows 'ORBIT TRADING'")
            test1_pass = True
        else:
            print("[FAIL] Title does NOT show 'ORBIT TRADING'")
            test1_pass = False

        if "ARUN TITAN" in title:
            print("[FAIL] Title still contains 'ARUN TITAN' (old name)")
            test1_pass = False
    else:
        print("[FAIL] Could not find window title in code")
        test1_pass = False

except Exception as e:
    print(f"[ERROR] {e}")
    test1_pass = False

print()

# ============================================================================
# TEST 2: BUG-011 - IBKR Broker Option
# ============================================================================
print("[TEST 2] BUG-011 - Settings Missing IBKR")
print("-" * 70)

try:
    with open('settings_gui.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Look for broker menu values
    broker_match = re.search(r'values=\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\]', content)

    if broker_match:
        brokers = [broker_match.group(i) for i in range(1, 5)]
        print(f"[OK] Found broker options: {brokers}")

        if "ibkr" in brokers:
            print("[PASS] IBKR option is available in broker dropdown")
            test2_pass = True
        else:
            print("[FAIL] IBKR option NOT found in broker dropdown")
            test2_pass = False

        if "mstock" in brokers and "zerodha" in brokers:
            print("[PASS] mStock and Zerodha also available")
        else:
            print("[WARN] mStock or Zerodha missing")
    else:
        print("[FAIL] Could not find broker options in code")
        test2_pass = False

except Exception as e:
    print(f"[ERROR] {e}")
    test2_pass = False

print()

# ============================================================================
# TEST 3: BUG-012 - Market Context Label
# ============================================================================
print("[TEST 3] BUG-012 - Market Context Label Missing")
print("-" * 70)

try:
    with open('sensei_v1_dashboard.py', 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')

    # Check for market context label
    has_label = "lbl_market_context" in content
    has_configure = "lbl_market_context.configure" in content
    has_market_name = "market_name = self.current_market_config.name" in content

    print(f"[OK] Market context label variable: {'Found' if has_label else 'Missing'}")
    print(f"[OK] Label configuration method: {'Found' if has_configure else 'Missing'}")
    print(f"[OK] Market name extraction: {'Found' if has_market_name else 'Missing'}")

    if has_label and has_configure and has_market_name:
        print("[PASS] Market context label is implemented")

        # Check that label updates on market change
        has_on_market_changed = "def _on_market_changed" in content
        label_update_in_change = content.find("lbl_market_context.configure") > content.find("def _on_market_changed")

        if has_on_market_changed:
            print("[OK] Market change handler: Found")
            if label_update_in_change:
                print("[OK] Label updates on market change: Yes")
            else:
                print("[WARN] Label might not update on market change")

        test3_pass = True
    else:
        print("[FAIL] Market context label not fully implemented")
        test3_pass = False

except Exception as e:
    print(f"[ERROR] {e}")
    test3_pass = False

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("[SUMMARY] Test Results")
print("=" * 70)

results = [
    ("BUG-010: Dashboard Title Rebrand", test1_pass),
    ("BUG-011: IBKR Broker Option", test2_pass),
    ("BUG-012: Market Context Label", test3_pass),
]

passed = sum(1 for _, result in results if result)
total = len(results)

for test_name, result in results:
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} | {test_name}")

print()
print(f"Result: {passed}/{total} tests passed")
print()

if passed == total:
    print("[SUCCESS] All UX fixes are working correctly!")
    print()
    print("Next steps:")
    print("  1. Run: python launcher.py")
    print("  2. Verify visual appearance in GUI:")
    print("     - Window title shows 'ORBIT TRADING V2'")
    print("     - Settings -> Broker includes 'ibkr' option")
    print("     - Market selector shows context (Market: ...)")
    print()
    sys.exit(0)
else:
    print("[WARNING] Some tests failed. Please review the errors above.")
    print()
    sys.exit(1)
