"""
Simulated rendering test - check if button section would execute
"""
import re

def find_try_except_blocks(filepath):
    """Find if button code is wrapped in try/except"""
    print(f"Analyzing{filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the button section
    button_start = None
    button_end = None
    
    for i, line in enumerate(lines):
        if 'ROW 3: CONTROLS' in line:
            button_start = i
        if button_start and 'def build_strategies_view' in line:
            button_end = i
            break
    
    if not button_start:
        print("❌ Button section not found!")
        return False
    
    print(f"✅ Button section found: lines {button_start+1} to {button_end}")
    
    #Check for try/except around this section
    section = lines[max(0, button_start-10):min(len(lines), button_end+5)]
    section_text = ''.join(section)
    
    has_try = 'try:' in section_text
    has_except = 'except' in section_text
    
    if has_try or has_except:
        print(f"⚠️  WARNING: Found try/except in or near button section")
        print(f"   This could be catching errors silently!")
        return False
    else:
        print("✅ No try/except wrapping button code")
        return True

def check_indentation(filepath):
    """Check if button code has correct indentation"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find button lines
    for i, line in enumerate(lines):
        if 'self.btn_start = ctk.CTkButton' in line:
            indent = len(line) - len(line.lstrip())
            print(f"✅ btn_start indentation: {indent} spaces (line {i+1})")
            return True
    
    return False

def check_pack_calls(filepath):
    """Verify pack() is called on buttons"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_start_pack = 'self.btn_start.pack' in content
    has_panic_pack = 'self.btn_panic.pack' in content
    
    print(f"✅ START button .pack() called: {has_start_pack}")
    print(f"✅ PANIC button .pack() called: {has_panic_pack}")
    
    return has_start_pack and has_panic_pack

if __name__ == "__main__":
    print("="*60)
    print("DASHBOARD RENDERING LOGIC TEST")
    print("="*60)
    print()
    
    filepath = 'dashboard_v2.py'
    
    print("Test 1: Check for silent error handling")
    test1 = find_try_except_blocks(filepath)
    print()
    
    print("Test 2: Check button indentation")
    test2 = check_indentation(filepath)
    print()
    
    print("Test 3: Check pack() calls")
    test3 = check_pack_calls(filepath)
    print()
    
    print("="*60)
    if all([test1, test2, test3]):
        print("✅ All rendering logic tests passed!")
        print("\nConclusion: Code SHOULD render. Issue might be:")
        print(" 1. Python caching old .pyc files")
        print(" 2. Dashboard loading different file")
        print(" 3. Runtime error before reaching button code")
    else:
        print("❌ Found potential rendering issues!")
