"""
🚀 ARUN HEADLESS ENGINE
Runs the trading core 24/7 without a GUI.
Use dashboard_v2.py to monitor and control.
"""

import time
import sys
import logging
from datetime import datetime
import os

# Ensure the root directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import kickstart
    from state_manager import state as state_mgr
    from utils import setup_logging
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Could not import core modules. {e}")
    sys.exit(1)

def run_headless():
    # 1. Setup Logging
    setup_logging(log_file="logs/headless_engine.log")
    logging.info("========================================")
    logging.info("🏭 STARTING ARUN HEADLESS ENGINE v1.0")
    logging.info(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("========================================")

    # 2. Reset Stop Flag (Cold Start)
    kickstart.reset_stop_flag()
    kickstart.initialize_stock_configs()

    # 3. Main Engine Loop
    try:
        logging.info("🏁 Entering Main Engine Loop...")
        while True:
            # Check for remote stop from GUI
            if state_mgr.is_stop_requested():
                logging.info("🛑 Remote STOP detected from State File. Shuting down...")
                break

            # Execute cycle
            try:
                kickstart.run_cycle()
            except Exception as e:
                logging.error(f"❌ Engine Cycle Error: {e}")
                import traceback
                logging.error(traceback.format_exc())

            # High-frequency heartbeat wait
            time.sleep(1) 

    except KeyboardInterrupt:
        logging.info("🛑 Headless Engine stopped by user (KeyboardInterrupt).")
    finally:
        logging.info("🏁 Headless Engine Offline.")

if __name__ == "__main__":
    run_headless()
