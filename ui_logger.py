import logging
import sys

# Configure console logging if not already done
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class UILogger:
    """
    Standardized logger for UI components to track initialization and errors.
    Helps debugging "blank screen" or "frozen app" issues.
    """
    
    @staticmethod
    def log_component_start(name):
        print(f"⚪ [UI] Building {name}...")
        logging.info(f"[UI] Building {name}...")

    @staticmethod
    def log_component_success(name):
        print(f"🟢 [UI] {name} Ready ✅")
        logging.info(f"[UI] {name} Ready")

    @staticmethod
    def log_component_error(name, error):
        print(f"🔴 [UI] {name} FAILED ❌ -> {error}")
        logging.error(f"[UI] {name} FAILED: {error}", exc_info=True)

    @staticmethod
    def log_section(title):
        print(f"\n--- {title} ---")
