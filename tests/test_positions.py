import traceback
from kickstart import safe_get_live_positions_merged

print("Testing safe_get_live_positions_merged()...")
try:
    result = safe_get_live_positions_merged()
    print(f"✅ Success! Result: {result}")
    print(f"   Type: {type(result)}")
    print(f"   Length: {len(result)}")
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
