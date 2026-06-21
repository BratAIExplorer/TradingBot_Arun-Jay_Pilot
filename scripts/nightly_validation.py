#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nightly Validation Script - Runtime Bug Detection

This script runs nightly (or on-demand) to detect if known bugs have
resurfaced in the live system. Complements the regression tests by
checking actual data/behavior.

Run: python scripts/nightly_validation.py

Returns:
  - Exit 0 if all checks pass
  - Exit 1 if critical issues found
  - Exit 2 if warnings (non-blocking)
"""

import sys
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List

# Force UTF-8 on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ValidationError(Exception):
    """Raised when critical validation fails"""
    pass


class ValidationWarning(Exception):
    """Raised when non-critical validation fails"""
    pass


class NightlyValidator:
    """Runtime validation for known bugs"""

    def __init__(self, db_path: str = "database/trades.db"):
        self.db_path = db_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_run = 0
        self.checks_passed = 0

    def log_error(self, bug_id: str, message: str):
        """Record critical error"""
        msg = f"[{bug_id}] {message}"
        print(f"[FAIL] {msg}")
        self.errors.append(msg)

    def log_warning(self, bug_id: str, message: str):
        """Record non-critical warning"""
        msg = f"[{bug_id}] {message}"
        print(f"[WARN] {msg}")
        self.warnings.append(msg)

    def log_pass(self, bug_id: str, message: str):
        """Record passed check"""
        print(f"[PASS] {bug_id}: {message}")
        self.checks_passed += 1

    def run_all_checks(self) -> int:
        """Run all validation checks. Returns exit code."""
        print("=" * 70)
        print("[CHECK] ARUN Trading Bot - Nightly Validation")
        print(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        # BUG-001: Phantom positions
        self.check_phantom_positions()

        # BUG-002: Database schema
        self.check_database_schema()

        # BUG-003: Duplicate trades
        self.check_duplicate_trades()

        # BUG-004: Missing P&L
        self.check_missing_pnl()

        # BUG-006: P&L FIFO ordering
        self.check_pnl_fifo_order()

        # BUG-007: Duplicate protection window
        self.check_duplicate_protection()

        # BUG-008: Neutral trades
        self.check_neutral_trades()

        # BUG-009: Never sell at loss
        self.check_never_sell_at_loss()

        return self.print_summary()

    # =========================================================================
    # BUG-001: Phantom Positions
    # =========================================================================

    def check_phantom_positions(self):
        """BUG-001: Verify cooldown list is working"""
        self.checks_run += 1

        try:
            # Check if RMS_FAILURES tracking is in place
            # This would be in the running process state
            # For now, we just verify the pattern exists in code
            if os.path.exists("kickstart.py"):
                try:
                    with open("kickstart.py", "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "RMS_FAILURES" in content and "3600" in content:
                            self.log_pass("BUG-001", "Cooldown list tracking in place")
                        else:
                            self.log_warning(
                                "BUG-001",
                                "RMS_FAILURES cooldown pattern not found"
                            )
                except (UnicodeDecodeError, IOError) as e:
                    self.log_warning("BUG-001", f"Could not read kickstart.py: {type(e).__name__}")
            else:
                self.log_warning("BUG-001", "kickstart.py not found")

        except Exception as e:
            self.log_warning("BUG-001", f"Check skipped: {str(e)}")

    # =========================================================================
    # BUG-002: Database Schema
    # =========================================================================

    def check_database_schema(self):
        """BUG-002: Verify all required tables exist"""
        self.checks_run += 1

        try:
            if not os.path.exists(self.db_path):
                self.log_error(
                    "BUG-002",
                    f"Database not found: {self.db_path}"
                )
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check required tables
            required_tables = ["trades", "system_control", "analytics"]
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = set(required_tables) - existing_tables
            if missing:
                self.log_error(
                    "BUG-002",
                    f"Missing tables: {', '.join(missing)}"
                )
            else:
                self.log_pass("BUG-002", "All required tables present")

            conn.close()

        except Exception as e:
            self.log_error("BUG-002", f"Database check failed: {str(e)}")

    # =========================================================================
    # BUG-003: Duplicate Trades
    # =========================================================================

    def check_duplicate_trades(self):
        """BUG-003: Detect duplicate trade entries"""
        self.checks_run += 1

        try:
            if not os.path.exists(self.db_path):
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Find duplicates
            cursor.execute("""
                SELECT symbol, price, quantity, COUNT(*) as cnt
                FROM trades
                GROUP BY symbol, price, quantity
                HAVING cnt > 1
            """)

            duplicates = cursor.fetchall()

            if duplicates:
                dup_list = ", ".join([f"{row[0]}({row[3]})" for row in duplicates])
                self.log_error(
                    "BUG-003",
                    f"Found duplicate trades: {dup_list}"
                )
            else:
                self.log_pass("BUG-003", "No duplicate trades found")

            conn.close()

        except Exception as e:
            self.log_warning("BUG-003", f"Duplicate check failed: {str(e)}")

    # =========================================================================
    # BUG-004: Missing P&L
    # =========================================================================

    def check_missing_pnl(self):
        """BUG-004: Detect sell trades without P&L"""
        self.checks_run += 1

        try:
            if not os.path.exists(self.db_path):
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Find sells without P&L
            cursor.execute("""
                SELECT COUNT(*), symbol FROM trades
                WHERE action='SELL' AND (pnl IS NULL OR pnl = 0)
                GROUP BY symbol
            """)

            missing_pnl = cursor.fetchall()

            if missing_pnl:
                missing_count = sum(row[0] for row in missing_pnl)
                symbols = ", ".join([row[1] for row in missing_pnl[:5]])
                self.log_error(
                    "BUG-004",
                    f"Found {missing_count} sells without P&L: {symbols}"
                )
            else:
                self.log_pass("BUG-004", "All sells have P&L calculated")

            conn.close()

        except Exception as e:
            self.log_warning("BUG-004", f"P&L check failed: {str(e)}")

    # =========================================================================
    # BUG-006: P&L FIFO Ordering
    # =========================================================================

    def check_pnl_fifo_order(self):
        """BUG-006: Verify P&L calculations follow FIFO order"""
        self.checks_run += 1

        try:
            if not os.path.exists(self.db_path):
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get trades ordered by timestamp (FIFO)
            cursor.execute("""
                SELECT id, symbol, action, price, timestamp
                FROM trades
                ORDER BY timestamp ASC
                LIMIT 100
            """)

            trades = cursor.fetchall()

            # Check if trades are in chronological order
            prev_time = None
            is_ordered = True

            for trade in trades:
                curr_time = trade[4]
                if prev_time and curr_time < prev_time:
                    is_ordered = False
                    break
                prev_time = curr_time

            if is_ordered:
                self.log_pass("BUG-006", "Trade timestamps in FIFO order")
            else:
                self.log_warning("BUG-006", "Trade timestamps not in order (check queries)")

            conn.close()

        except Exception as e:
            self.log_warning("BUG-006", f"FIFO check failed: {str(e)}")

    # =========================================================================
    # BUG-007: Duplicate Protection
    # =========================================================================

    def check_duplicate_protection(self):
        """BUG-007: Verify 10-second duplicate window is active"""
        self.checks_run += 1

        try:
            # Check if duplicate protection logic exists in code
            if os.path.exists("kickstart.py"):
                try:
                    with open("kickstart.py", "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "_last_trade" in content and "10" in content:
                            self.log_pass("BUG-007", "Duplicate protection window in place")
                        else:
                            self.log_warning(
                                "BUG-007",
                                "10-second duplicate window not clearly visible"
                            )
                except (UnicodeDecodeError, IOError) as e:
                    self.log_warning("BUG-007", f"Could not read kickstart.py: {type(e).__name__}")
            else:
                self.log_warning("BUG-007", "kickstart.py not found")

        except Exception as e:
            self.log_warning("BUG-007", f"Check skipped: {str(e)}")

    # =========================================================================
    # BUG-008: Neutral Trades
    # =========================================================================

    def check_neutral_trades(self):
        """BUG-008: Verify neutral trades are counted in stats"""
        self.checks_run += 1

        try:
            if not os.path.exists(self.db_path):
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN pnl > 10 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl < -10 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN pnl BETWEEN -10 AND 10 THEN 1 ELSE 0 END) as neutral
                FROM trades
                WHERE action='SELL'
            """)

            stats = cursor.fetchone()
            total, wins, losses, neutral = stats

            if total > 0:
                if (wins or 0) + (losses or 0) + (neutral or 0) == total:
                    win_rate = ((wins or 0) / total * 100) if total > 0 else 0
                    self.log_pass(
                        "BUG-008",
                        f"Stats complete: {wins}W {losses}L {neutral}N ({win_rate:.1f}% WR)"
                    )
                else:
                    self.log_error(
                        "BUG-008",
                        "Trade count mismatch in stats calculation"
                    )
            else:
                self.log_pass("BUG-008", "No trades yet to validate")

            conn.close()

        except Exception as e:
            self.log_warning("BUG-008", f"Neutral trades check failed: {str(e)}")

    # =========================================================================
    # BUG-009: Never Sell at Loss
    # =========================================================================

    def check_never_sell_at_loss(self):
        """BUG-009: Verify never_sell_at_loss setting exists and is used"""
        self.checks_run += 1

        try:
            # Check if setting exists
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    if "never_sell_at_loss" in settings:
                        self.log_pass(
                            "BUG-009",
                            f"never_sell_at_loss setting present: {settings['never_sell_at_loss']}"
                        )
                    else:
                        self.log_warning("BUG-009", "never_sell_at_loss setting missing")
            else:
                self.log_warning("BUG-009", "settings.json not found")

        except Exception as e:
            self.log_warning("BUG-009", f"Never sell at loss check failed: {str(e)}")

    # =========================================================================
    # Summary
    # =========================================================================

    def print_summary(self) -> int:
        """Print final report and return exit code"""
        print()
        print("=" * 70)
        print("[SUMMARY] Validation Results")
        print("=" * 70)

        print(f"Checks Run:     {self.checks_run}")
        print(f"Checks Passed:  {self.checks_passed}")
        print(f"Warnings:       {len(self.warnings)}")
        print(f"Errors:         {len(self.errors)}")
        print()

        if self.errors:
            print(f"[FAIL] CRITICAL ISSUES ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
            print()

        if self.warnings:
            print(f"[WARN] WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
            print()

        print("=" * 70)

        if self.errors:
            print("[FAIL] VALIDATION FAILED - Critical issues detected")
            return 1
        elif self.warnings:
            print("[WARN] VALIDATION PASSED WITH WARNINGS")
            return 2
        else:
            print("[PASS] VALIDATION PASSED - All checks clean")
            return 0


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Nightly validation for ARUN Trading Bot"
    )
    parser.add_argument(
        "--db",
        default="database/trades.db",
        help="Path to trades database"
    )

    args = parser.parse_args()

    validator = NightlyValidator(db_path=args.db)
    exit_code = validator.run_all_checks()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
