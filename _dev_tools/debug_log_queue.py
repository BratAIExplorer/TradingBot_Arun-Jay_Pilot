import sys
import os
import time
import logging

# Setup path
sys.path.append(os.getcwd())

print("--- Starting Isolation Test ---\n")

try:
    from backend.bot_manager import bot_manager
    from kickstart import log_ok, set_log_callback, LOG_CALLBACK
    
    print(f"Initial LOG_CALLBACK in kickstart: {LOG_CALLBACK}")
    
    print("Starting Bot via Manager...")
    bot_manager.start_bot()
    
    # Check callback again
    from kickstart import LOG_CALLBACK as UPDATED_CALLBACK
    print(f"Post-Start LOG_CALLBACK in kickstart: {UPDATED_CALLBACK}")
    
    if UPDATED_CALLBACK is None:
        print("CRITICAL: LOG_CALLBACK is still None after start_bot()!")
    else:
        print("Callback registered successfully.")
        
    print("\nSending Test Log...")
    log_ok("TEST LOGGER MESSAGE 123")
    
    # Check Queue
    q_items = list(bot_manager.log_queue.queue)
    print(f"\nQueue contains {len(q_items)} items.")
    
    found = False
    for item in q_items:
        if "TEST LOGGER MESSAGE 123" in item:
            found = True
            print(f"Found matching log in queue: {item}")
            break
            
    if not found:
        print("Log message NOT found in queue.")
        print("Dumping queue:", q_items)

    print("\nStopping Bot...")
    bot_manager.stop_bot()

except Exception as e:
    print(f"Test Failed with Exception: {e}")
    import traceback
    traceback.print_exc()
