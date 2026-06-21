"""
Market Context Scheduler
Runs market context fetcher on a schedule (every 5 minutes).
Can be run as a background daemon or integrated with main bot.
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from market_context_fetcher import MarketContextFetcher
from database.analytics_migration import AnalyticsDatabase

logger = logging.getLogger("market_scheduler")


class MarketContextScheduler:
    """
    Schedules market context fetching at regular intervals.
    Thread-safe, can run alongside main trading engine.
    """

    def __init__(self, interval_seconds: int = 300):
        """
        Initialize scheduler.

        Args:
            interval_seconds: How often to fetch market context (default: 300 = 5 min)
        """
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.fetcher = None
        self.last_fetch_time = None
        self.fetch_count = 0
        self.error_count = 0

    def start(self):
        """Start the scheduler (runs in background thread)"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.fetcher = MarketContextFetcher()

        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="MarketContextScheduler"
        )
        self.thread.start()
        logger.info(f"Market context scheduler started (interval: {self.interval}s)")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Market context scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop (runs in background thread)"""
        logger.info("Scheduler loop started")

        while self.running:
            try:
                start_time = time.time()

                # Fetch and store market snapshot
                snapshot_id = self.fetcher.store_snapshot()

                if snapshot_id:
                    elapsed = time.time() - start_time
                    self.last_fetch_time = datetime.now()
                    self.fetch_count += 1
                    logger.info(
                        f"Market snapshot #{self.fetch_count} stored "
                        f"(ID: {snapshot_id}, took {elapsed:.2f}s)"
                    )
                else:
                    self.error_count += 1
                    logger.warning(f"Failed to store market snapshot (error #{self.error_count})")

            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in scheduler loop: {e}")

            # Wait for next interval
            time.sleep(self.interval)

    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            'running': self.running,
            'interval_seconds': self.interval,
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
            'last_fetch': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'uptime_seconds': time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the latest market snapshot from database"""
        if not self.fetcher:
            return None

        try:
            snapshots = self.fetcher.analytics_db.get_recent_market_snapshots(limit=1)
            return snapshots[0] if snapshots else None
        except Exception as e:
            logger.error(f"Error fetching latest snapshot: {e}")
            return None


def integrate_with_kickstart():
    """
    Integration point for kickstart.py
    Call this to enable market context fetching during trading.
    """
    scheduler = MarketContextScheduler(interval_seconds=300)  # 5 minutes
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    """Test scheduler"""
    import sys
    from typing import Dict, Optional

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s'
    )

    print("Starting Market Context Scheduler Test...\n")

    scheduler = MarketContextScheduler(interval_seconds=5)  # 5 seconds for testing
    scheduler.start_time = time.time()
    scheduler.start()

    print("Scheduler running. Fetching market context every 5 seconds...")
    print("Press Ctrl+C to stop.\n")

    try:
        for i in range(6):  # Run for ~30 seconds (6 iterations)
            time.sleep(5)
            status = scheduler.get_status()
            print(f"\n[{i+1}] Scheduler Status:")
            print(f"   Fetches: {status['fetch_count']}")
            print(f"   Errors: {status['error_count']}")
            print(f"   Last fetch: {status['last_fetch']}")

            latest = scheduler.get_latest_snapshot()
            if latest:
                print(f"   Latest snapshot: Nifty {latest['nifty_50_value']:.0f} "
                      f"({latest['nifty_50_change_pct']:+.2f}%), "
                      f"Regime: {latest['market_regime']}")

    except KeyboardInterrupt:
        print("\n\nShutting down...")
        scheduler.stop()
        print("Scheduler stopped")
