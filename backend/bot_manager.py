import threading
import time
import logging
import queue
from datetime import datetime
import traceback
import sys
import os

# Add project root to path to import kickstart
sys.path.append(os.getcwd())

try:
    from kickstart import run_cycle, set_log_callback, request_stop, reset_stop_flag, setup_logging
    KICKSTART_AVAILABLE = True
except ImportError:
    KICKSTART_AVAILABLE = False
    print("⚠️ Kickstart module not found. Bot logic will be mocked.")

class BotManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue(maxsize=200) # Keep last 200 logs in memory
        self.status = "STOPPED" # STOPPED, RUNNING, ERROR
        self.last_cycle_time = None
        self.start_time = None
        
        # Hook into kickstart logging
        if KICKSTART_AVAILABLE:
            set_log_callback(self.log_capture)
            
        self.initialized = True

    def log_capture(self, msg):
        """Callback to capture logs from kickstart"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg.strip()}"
        
        # Print to console for dev visibility
        print(log_entry)
        
        try:
            with open("debug_log_capture.txt", "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
            
            if self.log_queue.full():
                self.log_queue.get_nowait()
            self.log_queue.put(log_entry)
        except Exception as e:
            print(f"❌ log_capture Queue Error: {e}")

    def start_bot(self):
        try:
             with open("panic.log", "a") as f: f.write(f"{datetime.now()} - start_bot CALLED\n")
        except: pass

        try:
            if self.running:
                return {"status": "success", "message": "Already running"}

            if not KICKSTART_AVAILABLE:
                return {"status": "error", "message": "Kickstart module missing"}

            self.stop_event.clear()
            
            # Initialize logging for this session
            # DISABLED FOR DEBUGGING: Rule out lock conflicts
            # try:
            #     setup_logging()
            # except Exception as e:
            #     print(f"❌ setup_logging failed in Start Engine: {e}")
            
            # Ensure log callback is hooked
            set_log_callback(self.log_capture)

            self.running = True
            self.status = "RUNNING"
            self.start_time = datetime.now()
            
            # Reset kickstart stop flag if it controls internal state
            reset_stop_flag()
            
            try:
                 with open("panic.log", "a") as f: f.write(f"{datetime.now()} - Attempting to start thread\n")
            except: pass
            
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
            self.log_capture("🚀 Bot Engine Started via Web API")
            return {"status": "success", "message": "Bot started"}
            
        except Exception as e:
            msg = f"CRITICAL START FAILURE: {e}"
            print(msg)
            try:
                 with open("panic.log", "a") as f: f.write(f"{datetime.now()} - {msg}\n")
            except: pass
            self.running = False
            self.status = "ERROR"
            return {"status": "error", "message": str(e)}

    def stop_bot(self):
        if not self.running:
            return {"status": "error", "message": "Bot is not running"}

        self.log_capture("🛑 Stop Command Received...")
        self.status = "STOPPING"
        self.stop_event.set()
        
        # Signal kickstart directly
        request_stop()
        
        # Thread will join in the background or logic will break loop
        self.running = False
        self.status = "STOPPED"
        self.log_capture("🛑 Bot Engine Stopped")
        return {"status": "success", "message": "Bot stopped"}

    def _run_loop(self):
        """Main Thread Loop"""
        try:
             with open("panic.log", "a") as f: f.write(f"{datetime.now()} - Thread STARTED\n")
        except: pass

        while not self.stop_event.is_set():
            try:
                self.log_capture("💓 Bot Loop Heartbeat")
                self.last_cycle_time = datetime.now()
                # Run one trading cycle
                run_cycle()
                
                # Sleep between cycles (prevent CPU spin)
                # kickstart might have its own sleeps, but safely waiting here is good
                for _ in range(50): # 5 seconds wait, interruptible
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                self.log_capture(f"❌ CRITICAL ERROR in Bot Loop: {e}")
                traceback.print_exc()
                time.sleep(5) # Wait before retry on error

    def get_status(self):
        uptime = "0s"
        if self.start_time and self.running:
            delta = datetime.now() - self.start_time
            uptime = str(delta).split('.')[0]

        from state_manager import state as state_mgr
        counters = state_mgr.get_trade_counters()

        return {
            "status": self.status,
            "running": self.running,
            "uptime": uptime,
            "last_cycle": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "counters": counters
        }

    def get_logs(self, limit=50):
        """Get recent logs"""
        logs = []
        try:
            # We don't want to empty the queue, just read it
            # This is a bit inefficient for a queue, but Python Queue doesn't support peeking
            # For a production system we might use a list with a lock or deque
            pass 
        except:
            pass
        return list(self.log_queue.queue)[-limit:]

bot_manager = BotManager()
