#!/usr/bin/env python3
"""
ARUN Trading Bot Daemon
=======================
Headless runner for VPS deployment.

Usage:
    python bot_daemon.py start      # Start daemon in background
    python bot_daemon.py stop       # Stop daemon gracefully
    python bot_daemon.py restart    # Restart daemon
    python bot_daemon.py status     # Check if running
    python bot_daemon.py run        # Run in foreground (for testing)

Features:
    - Runs kickstart.py trading engine without GUI
    - Logs to daemon.log
    - PID file management
    - Graceful shutdown handling
    - Signal handling (SIGTERM, SIGINT)
    - Paper trading mode compatible
"""

import sys
import os
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
import atexit

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configuration
PID_FILE = project_root / "bot_daemon.pid"
LOG_FILE = project_root / "daemon.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

# Global flag for graceful shutdown
shutdown_requested = False


class DaemonLogger:
    """Custom logger for daemon operations"""

    def __init__(self, log_file):
        self.log_file = log_file
        self.setup_logging()

    def setup_logging(self):
        """Setup file logging with rotation"""
        # Check log file size and rotate if needed
        if self.log_file.exists() and self.log_file.stat().st_size > MAX_LOG_SIZE:
            backup = self.log_file.with_suffix('.log.old')
            if backup.exists():
                backup.unlink()
            self.log_file.rename(backup)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(self.log_file, mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)


class BotDaemon:
    """ARUN Trading Bot Daemon Manager"""

    def __init__(self):
        self.pid_file = PID_FILE
        self.log_file = LOG_FILE
        self.logger = DaemonLogger(self.log_file)
        self.kickstart_module = None

    def write_pid(self, pid):
        """Write PID to file"""
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        self.logger.info(f"PID {pid} written to {self.pid_file}")

    def read_pid(self):
        """Read PID from file"""
        if not self.pid_file.exists():
            return None
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, IOError):
            return None

    def remove_pid(self):
        """Remove PID file"""
        if self.pid_file.exists():
            self.pid_file.unlink()
            self.logger.info(f"PID file removed: {self.pid_file}")

    def is_running(self):
        """Check if daemon is running"""
        pid = self.read_pid()
        if pid is None:
            return False

        # Check if process exists
        try:
            os.kill(pid, 0)  # Doesn't kill, just checks if process exists
            return True
        except OSError:
            # Process doesn't exist, clean up stale PID file
            self.remove_pid()
            return False

    def get_status(self):
        """Get daemon status"""
        if self.is_running():
            pid = self.read_pid()
            return {
                'running': True,
                'pid': pid,
                'log_file': str(self.log_file),
                'message': f"Bot daemon is RUNNING (PID: {pid})"
            }
        else:
            return {
                'running': False,
                'pid': None,
                'log_file': str(self.log_file),
                'message': "Bot daemon is NOT running"
            }

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            global shutdown_requested
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            shutdown_requested = True

            # Stop the trading engine
            if self.kickstart_module:
                try:
                    self.kickstart_module.STOP_REQUESTED = True
                    self.logger.info("Trading engine stop flag set")
                except Exception as e:
                    self.logger.error(f"Error setting stop flag: {e}")

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Cleanup on exit
        atexit.register(self.cleanup)

    def cleanup(self):
        """Cleanup on exit"""
        self.logger.info("Daemon cleanup: removing PID file")
        self.remove_pid()

    def start(self, foreground=False):
        """Start the daemon"""
        # Check if already running
        if self.is_running():
            self.logger.error("Daemon is already running!")
            pid = self.read_pid()
            self.logger.info(f"Current PID: {pid}")
            return False

        if foreground:
            # Run in foreground (for testing)
            self.logger.info("Starting bot in FOREGROUND mode (for testing)")
            self.write_pid(os.getpid())
            self.setup_signal_handlers()
            self.run_trading_engine()
        else:
            # Fork to background
            self.logger.info("Starting bot daemon in BACKGROUND mode")
            try:
                # Fork process
                pid = os.fork()
                if pid > 0:
                    # Parent process
                    self.logger.info(f"Daemon started with PID: {pid}")
                    self.write_pid(pid)
                    print(f"✅ Bot daemon started successfully (PID: {pid})")
                    print(f"📄 Logs: {self.log_file}")
                    print(f"💡 Use 'python bot_daemon.py status' to check status")
                    print(f"💡 Use 'tail -f {self.log_file}' to view live logs")
                    return True
            except OSError as e:
                self.logger.error(f"Failed to fork daemon: {e}")
                return False

            # Child process continues here
            # Decouple from parent environment
            os.chdir('/')
            os.setsid()
            os.umask(0)

            # Second fork to prevent zombies
            try:
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
            except OSError as e:
                self.logger.error(f"Second fork failed: {e}")
                sys.exit(1)

            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()

            # Run daemon
            self.write_pid(os.getpid())
            self.setup_signal_handlers()
            self.run_trading_engine()

    def run_trading_engine(self):
        """Run the trading engine (main loop)"""
        global shutdown_requested

        self.logger.info("=" * 60)
        self.logger.info("ARUN Trading Bot Daemon - Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"PID: {os.getpid()}")
        self.logger.info(f"Log File: {self.log_file}")
        self.logger.info(f"Working Directory: {os.getcwd()}")

        try:
            # Import kickstart module
            self.logger.info("Loading kickstart module...")
            import kickstart
            self.kickstart_module = kickstart

            # Check if paper trading mode is enabled
            if hasattr(kickstart, 'settings') and kickstart.settings:
                paper_mode = kickstart.settings.get("app_settings.paper_trading_mode", False)
                self.logger.info(f"Paper Trading Mode: {paper_mode}")

            # Run auto-login if configured
            self.logger.info("Performing auto-login...")
            try:
                if kickstart.perform_auto_login():
                    self.logger.info("✅ Auto-login successful")
                else:
                    self.logger.warning("⚠️ Auto-login not configured or failed")
            except Exception as e:
                self.logger.error(f"Auto-login error: {e}")

            # Load state
            if kickstart.state_mgr:
                try:
                    state = kickstart.state_mgr.load()
                    if state and state.get('circuit_breaker_active'):
                        self.logger.warning("🛑 Circuit breaker is ACTIVE. Bot will not trade.")
                        return
                except Exception as e:
                    self.logger.error(f"State load failed: {e}")

            # Start trading loop
            self.logger.info("🚀 Starting trading engine (connectivity monitor)")
            self.logger.info("Press Ctrl+C or send SIGTERM to stop gracefully")

            # Run connectivity monitor (continuous loop)
            kickstart.connectivity_monitor()

        except KeyboardInterrupt:
            self.logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ Fatal error in trading engine: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.info("Trading engine stopped")
            self.cleanup()

    def stop(self):
        """Stop the daemon"""
        if not self.is_running():
            self.logger.error("Daemon is not running")
            print("❌ Bot daemon is not running")
            return False

        pid = self.read_pid()
        self.logger.info(f"Stopping daemon (PID: {pid})...")
        print(f"🛑 Stopping bot daemon (PID: {pid})...")

        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait for process to exit (max 10 seconds)
            for i in range(10):
                time.sleep(1)
                if not self.is_running():
                    self.logger.info("✅ Daemon stopped gracefully")
                    print("✅ Bot daemon stopped successfully")
                    return True
                print(f"⏳ Waiting for graceful shutdown... ({i+1}/10)")

            # If still running, force kill
            if self.is_running():
                self.logger.warning("Graceful shutdown timeout, forcing kill...")
                print("⚠️ Graceful shutdown timeout, forcing kill...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
                self.remove_pid()
                print("✅ Bot daemon killed")
                return True

        except ProcessLookupError:
            self.logger.info("Process already stopped, cleaning up PID file")
            self.remove_pid()
            print("✅ Process already stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping daemon: {e}")
            print(f"❌ Error stopping daemon: {e}")
            return False

    def restart(self):
        """Restart the daemon"""
        self.logger.info("Restarting daemon...")
        print("🔄 Restarting bot daemon...")

        if self.is_running():
            if not self.stop():
                return False
            time.sleep(2)

        return self.start()


def print_usage():
    """Print usage information"""
    print("""
ARUN Trading Bot Daemon - Headless VPS Runner
==============================================

Usage:
    python bot_daemon.py start      # Start daemon in background
    python bot_daemon.py stop       # Stop daemon gracefully
    python bot_daemon.py restart    # Restart daemon
    python bot_daemon.py status     # Check if running
    python bot_daemon.py run        # Run in foreground (for testing)

Examples:
    # Start bot and monitor logs
    python bot_daemon.py start
    tail -f daemon.log

    # Check status
    python bot_daemon.py status

    # Stop bot
    python bot_daemon.py stop

Configuration:
    - Edit settings.json for broker credentials
    - Enable paper_trading_mode for testing
    - Check daemon.log for runtime logs

Files:
    - daemon.log: Runtime logs (rotated at 10MB)
    - bot_daemon.pid: Process ID file
    - settings.json: Bot configuration

For help: See Documentation/VPS_DEPLOYMENT.md
    """)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    daemon = BotDaemon()

    if command == 'start':
        success = daemon.start(foreground=False)
        sys.exit(0 if success else 1)

    elif command == 'run':
        # Run in foreground (for testing)
        daemon.start(foreground=True)
        sys.exit(0)

    elif command == 'stop':
        success = daemon.stop()
        sys.exit(0 if success else 1)

    elif command == 'restart':
        success = daemon.restart()
        sys.exit(0 if success else 1)

    elif command == 'status':
        status = daemon.get_status()
        print("=" * 50)
        print("ARUN Bot Daemon Status")
        print("=" * 50)
        print(f"Status: {'🟢 RUNNING' if status['running'] else '🔴 STOPPED'}")
        if status['running']:
            print(f"PID: {status['pid']}")
        print(f"Log File: {status['log_file']}")
        print("=" * 50)

        # Show last 10 lines of log
        if Path(status['log_file']).exists():
            print("\nLast 10 log entries:")
            print("-" * 50)
            with open(status['log_file'], 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(line.rstrip())

        sys.exit(0 if status['running'] else 1)

    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
