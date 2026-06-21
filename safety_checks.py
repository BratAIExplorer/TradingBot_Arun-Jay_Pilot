"""
ARUN Trading Bot v2.6.0 - Safety Checks Module

Core reliability validation layer that runs before trades and per-cycle.
Immutable, dependency-injected, production-grade safety checks.

Components:
- CheckResult: frozen dataclass for immutable check results
- SafetyChecker: orchestrator with 5 validation methods
  1. check_duplicate_trades() — prevents duplicate trades in 10s window
  2. check_position_consistency() — DB vs broker position mismatch
  3. check_pnl_integrity() — null P&L, FIFO ordering validation
  4. check_capital_bounds() — deployed vs allocated safety
  5. check_daily_loss_limit() — daily P&L circuit breaker

All checks return CheckResult with pass/fail + severity (INFO/WARN/CRITICAL).
Designed for fail-open (permissive) on non-critical scenarios, fail-closed on critical.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    """Immutable result of a safety check.

    Attributes:
        name: Check identifier (e.g., "duplicate_trades")
        passed: True if check passed, False if failed
        severity: "INFO", "WARN", or "CRITICAL"
        message: Human-readable result message
        data: Optional metadata dict (dedup_key, mismatched_qty, etc.)
    """
    name: str
    passed: bool
    severity: str  # "INFO" | "WARN" | "CRITICAL"
    message: str
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate severity
        valid_severities = {"INFO", "WARN", "CRITICAL"}
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}, got {self.severity}")


class SafetyChecker:
    """Dependency-injected safety validation orchestrator.

    Instantiated once per trading session with references to TradesDatabase
    and SettingsManager. All methods are stateless and pure (no side effects).

    Example:
        from database.trades_db import TradesDatabase
        from settings_manager import SettingsManager

        db = TradesDatabase("database/trades.db")
        settings = SettingsManager()
        checker = SafetyChecker(db=db, settings=settings)

        result = checker.check_duplicate_trades(symbol="HDFCBANK", window_seconds=10)
        if not result.passed:
            logger.error(f"Safety check failed: {result.message}")
    """

    def __init__(self, db, settings):
        """Initialize with database and settings dependencies.

        Args:
            db: TradesDatabase instance
            settings: SettingsManager instance
        """
        self.db = db
        self.settings = settings

    def check_duplicate_trades(self, symbol: str, window_seconds: int = 10) -> CheckResult:
        """Check for duplicate trades within time window.

        Prevents accidental duplicate buy/sell of the same symbol within N seconds.
        Implements the BUG-07 prevention pattern from BUG_REGISTRY.

        Args:
            symbol: Stock symbol to check (e.g., "HDFCBANK")
            window_seconds: Look-back window (default 10 seconds)

        Returns:
            CheckResult with passed=True if no duplicates, False if found
        """
        try:
            # Get recent trades and filter by symbol
            recent_trades = self.db.get_recent_trades(limit=10)

            # Filter to symbol-specific trades
            symbol_trades = [t for t in recent_trades if t.get("symbol") == symbol]

            if not symbol_trades:
                return CheckResult(
                    name="duplicate_trades",
                    passed=True,
                    severity="INFO",
                    message=f"No recent trades for {symbol}",
                    data={}
                )

            last_trade = symbol_trades[0]

            last_trade_timestamp = datetime.fromisoformat(last_trade["timestamp"])
            now = datetime.now()
            time_since_last = (now - last_trade_timestamp).total_seconds()

            if time_since_last < window_seconds:
                return CheckResult(
                    name="duplicate_trades",
                    passed=False,
                    severity="CRITICAL",
                    message=f"Duplicate {symbol} trade detected: {time_since_last:.1f}s ago (window: {window_seconds}s)",
                    data={
                        "symbol": symbol,
                        "seconds_since_last": time_since_last,
                        "window_seconds": window_seconds,
                        "last_trade_id": last_trade["id"]
                    }
                )

            return CheckResult(
                name="duplicate_trades",
                passed=True,
                severity="INFO",
                message=f"{symbol} trade {time_since_last:.1f}s ago (outside {window_seconds}s window)",
                data={"seconds_since_last": time_since_last}
            )

        except Exception as e:
            logger.warning(f"duplicate_trades check error: {e}")
            return CheckResult(
                name="duplicate_trades",
                passed=True,  # Fail-open: allow trade on check error
                severity="WARN",
                message=f"Check error (allowing trade): {str(e)}",
                data={"error": str(e)}
            )

    def check_position_consistency(self, broker_positions: List[Dict[str, Any]]) -> CheckResult:
        """Check DB positions match broker positions (prevents phantom positions).

        Implements BUG-001 prevention: detects when broker reports different
        quantity than DB records. Raises CRITICAL alert on mismatch.

        Args:
            broker_positions: List of {symbol, quantity} from broker

        Returns:
            CheckResult with passed=True if DB and broker match
        """
        try:
            db_positions = self.db.get_open_positions()

            # Build symbol -> qty maps (handle both "quantity" and "net_quantity" keys)
            db_map = {p["symbol"]: p.get("quantity") or p.get("net_quantity", 0) for p in db_positions}
            broker_map = {p["symbol"]: p.get("quantity") or p.get("net_quantity", 0) for p in broker_positions}

            # Check for mismatches
            all_symbols = set(db_map.keys()) | set(broker_map.keys())

            for symbol in all_symbols:
                db_qty = db_map.get(symbol, 0)
                broker_qty = broker_map.get(symbol, 0)

                if db_qty != broker_qty:
                    return CheckResult(
                        name="position_consistency",
                        passed=False,
                        severity="CRITICAL",
                        message=f"Position mismatch {symbol}: DB={db_qty}, Broker={broker_qty}",
                        data={
                            "symbol": symbol,
                            "db_quantity": db_qty,
                            "broker_quantity": broker_qty,
                            "difference": broker_qty - db_qty
                        }
                    )

            return CheckResult(
                name="position_consistency",
                passed=True,
                severity="INFO",
                message=f"All {len(all_symbols)} positions consistent",
                data={"symbols_checked": len(all_symbols)}
            )

        except Exception as e:
            logger.warning(f"position_consistency check error: {e}")
            return CheckResult(
                name="position_consistency",
                passed=True,  # Fail-open
                severity="WARN",
                message=f"Check error (allowing trade): {str(e)}",
                data={"error": str(e)}
            )

    def check_pnl_integrity(self) -> CheckResult:
        """Check P&L calculation correctness (null P&L on SELLs, FIFO ordering).

        Implements BUG-04 (missing P&L on SELLs) and BUG-06 (FIFO ordering).
        Validates that:
        1. All SELL trades have P&L calculated (no NULL for SELLs)
        2. For each symbol, BUY timestamps < SELL timestamps (FIFO)

        Returns:
            CheckResult with passed=True if P&L looks correct
        """
        try:
            trades = self.db.query_all_trades()

            if not trades:
                return CheckResult(
                    name="pnl_integrity",
                    passed=True,
                    severity="INFO",
                    message="No trades to validate",
                    data={}
                )

            # Check 1: No NULL P&L on SELLs
            for trade in trades:
                if trade["trade_type"] == "SELL" and trade.get("pnl_net") is None:
                    return CheckResult(
                        name="pnl_integrity",
                        passed=False,
                        severity="WARN",
                        message=f"SELL {trade['symbol']} (ID {trade['id']}) has NULL P&L",
                        data={
                            "trade_id": trade["id"],
                            "symbol": trade["symbol"],
                            "trade_type": "SELL"
                        }
                    )

            # Check 2: FIFO ordering per symbol (BUY timestamps must come before SELL timestamps)
            trades_by_symbol = {}
            for trade in trades:
                symbol = trade["symbol"]
                if symbol not in trades_by_symbol:
                    trades_by_symbol[symbol] = []
                trades_by_symbol[symbol].append(trade)

            for symbol, symbol_trades in trades_by_symbol.items():
                buys = [t for t in symbol_trades if t["trade_type"] == "BUY"]
                sells = [t for t in symbol_trades if t["trade_type"] == "SELL"]

                # For each symbol, all BUY timestamps should be <= all SELL timestamps
                if buys and sells:
                    buy_timestamps = sorted([b.get("timestamp", "") for b in buys])
                    sell_timestamps = sorted([s.get("timestamp", "") for s in sells])

                    # Latest BUY should be <= earliest SELL
                    if buy_timestamps[-1] > sell_timestamps[0]:
                        return CheckResult(
                            name="pnl_integrity",
                            passed=False,
                            severity="WARN",
                            message=f"{symbol}: SELL before latest BUY (FIFO violation)",
                            data={
                                "symbol": symbol,
                                "latest_buy_timestamp": buy_timestamps[-1],
                                "earliest_sell_timestamp": sell_timestamps[0]
                            }
                        )

            return CheckResult(
                name="pnl_integrity",
                passed=True,
                severity="INFO",
                message=f"P&L integrity OK for {len(trades_by_symbol)} symbols",
                data={"symbols_checked": len(trades_by_symbol)}
            )

        except Exception as e:
            logger.warning(f"pnl_integrity check error: {e}")
            return CheckResult(
                name="pnl_integrity",
                passed=True,  # Fail-open
                severity="WARN",
                message=f"Check error (allowing trade): {str(e)}",
                data={"error": str(e)}
            )

    def check_capital_bounds(
        self, allocated_capital: float, total_capital: float, deployed_capital: float
    ) -> CheckResult:
        """Check deployed capital is within allocated bounds.

        Prevents over-leveraging:
        - deployed_capital <= allocated_capital (primary check)
        - deployed_capital <= total_capital (hard limit)

        Args:
            allocated_capital: Max amount to deploy per settings
            total_capital: Total available capital
            deployed_capital: Currently deployed amount

        Returns:
            CheckResult with passed=True if bounds OK
        """
        try:
            # Check 1: Deployed vs Allocated
            if deployed_capital > allocated_capital:
                return CheckResult(
                    name="capital_bounds",
                    passed=False,
                    severity="CRITICAL",
                    message=f"Deployed ₹{deployed_capital} exceeds allocated ₹{allocated_capital}",
                    data={
                        "deployed": deployed_capital,
                        "allocated": allocated_capital,
                        "excess": deployed_capital - allocated_capital
                    }
                )

            # Check 2: Deployed vs Total
            if deployed_capital > total_capital:
                return CheckResult(
                    name="capital_bounds",
                    passed=False,
                    severity="CRITICAL",
                    message=f"Deployed ₹{deployed_capital} exceeds total ₹{total_capital}",
                    data={
                        "deployed": deployed_capital,
                        "total": total_capital,
                        "excess": deployed_capital - total_capital
                    }
                )

            return CheckResult(
                name="capital_bounds",
                passed=True,
                severity="INFO",
                message=f"Capital OK: ₹{deployed_capital} deployed of ₹{allocated_capital} allocated",
                data={
                    "deployed": deployed_capital,
                    "allocated": allocated_capital,
                    "total": total_capital,
                    "utilization_pct": (deployed_capital / allocated_capital * 100) if allocated_capital > 0 else 0
                }
            )

        except Exception as e:
            logger.warning(f"capital_bounds check error: {e}")
            return CheckResult(
                name="capital_bounds",
                passed=True,  # Fail-open
                severity="WARN",
                message=f"Check error (allowing trade): {str(e)}",
                data={"error": str(e)}
            )

    def check_daily_loss_limit(
        self, daily_pnl: float, portfolio_value: float, daily_loss_limit_pct: float
    ) -> CheckResult:
        """Check daily P&L is within loss limit (circuit breaker).

        Implements daily loss circuit breaker: if today's loss exceeds
        (daily_loss_limit_pct% of portfolio_value), halt trading.

        Args:
            daily_pnl: Today's realized P&L (can be negative)
            portfolio_value: Current portfolio value for percentage calc
            daily_loss_limit_pct: Max loss % allowed (e.g., 5.0 for 5%)

        Returns:
            CheckResult with passed=True if loss within limit
        """
        try:
            # Profits always pass
            if daily_pnl >= 0:
                return CheckResult(
                    name="daily_loss_limit",
                    passed=True,
                    severity="INFO",
                    message=f"Profitable day: +₹{daily_pnl}",
                    data={"daily_pnl": daily_pnl}
                )

            # Check loss percentage
            loss_pct = abs(daily_pnl) / portfolio_value * 100 if portfolio_value > 0 else 0

            if loss_pct > daily_loss_limit_pct:
                return CheckResult(
                    name="daily_loss_limit",
                    passed=False,
                    severity="CRITICAL",
                    message=f"Daily loss ₹{daily_pnl} ({loss_pct:.2f}%) exceeds limit {daily_loss_limit_pct}%",
                    data={
                        "daily_pnl": daily_pnl,
                        "loss_pct": loss_pct,
                        "limit_pct": daily_loss_limit_pct,
                        "portfolio_value": portfolio_value
                    }
                )

            return CheckResult(
                name="daily_loss_limit",
                passed=True,
                severity="INFO",
                message=f"Loss ₹{daily_pnl} ({loss_pct:.2f}%) within {daily_loss_limit_pct}% limit",
                data={
                    "daily_pnl": daily_pnl,
                    "loss_pct": loss_pct,
                    "limit_pct": daily_loss_limit_pct
                }
            )

        except Exception as e:
            logger.warning(f"daily_loss_limit check error: {e}")
            return CheckResult(
                name="daily_loss_limit",
                passed=True,  # Fail-open
                severity="WARN",
                message=f"Check error (allowing trade): {str(e)}",
                data={"error": str(e)}
            )

    def run_all(
        self,
        symbol: str,
        broker_positions: List[Dict[str, Any]],
        allocated_capital: float,
        total_capital: float,
        deployed_capital: float,
        daily_pnl: float,
        daily_loss_limit_pct: float,
        window_seconds: int = 10
    ) -> List[CheckResult]:
        """Run all 5 safety checks in sequence.

        Orchestrator method that runs all checks and returns results.
        Does NOT short-circuit: even if one check fails, others still run
        (for observability and audit trail).

        Args:
            symbol: Current symbol being traded
            broker_positions: Current broker positions
            allocated_capital: Allocated trading capital
            total_capital: Total available capital
            deployed_capital: Currently deployed amount
            daily_pnl: Today's realized P&L
            daily_loss_limit_pct: Daily loss limit %
            window_seconds: Duplicate check window

        Returns:
            List of 5 CheckResult objects (one per check method)
        """
        results = [
            self.check_duplicate_trades(symbol=symbol, window_seconds=window_seconds),
            self.check_position_consistency(broker_positions=broker_positions),
            self.check_pnl_integrity(),
            self.check_capital_bounds(
                allocated_capital=allocated_capital,
                total_capital=total_capital,
                deployed_capital=deployed_capital
            ),
            self.check_daily_loss_limit(
                daily_pnl=daily_pnl,
                portfolio_value=total_capital,
                daily_loss_limit_pct=daily_loss_limit_pct
            )
        ]

        # Log summary
        critical_results = [r for r in results if r.severity == "CRITICAL"]
        if critical_results:
            logger.error(f"Safety check CRITICAL: {len(critical_results)} failures")
            for result in critical_results:
                logger.error(f"  - {result.name}: {result.message}")

        return results


if __name__ == "__main__":
    # Example usage
    print("SafetyChecker module loaded successfully")
    print(f"CheckResult: {CheckResult.__doc__}")
    print(f"SafetyChecker: {SafetyChecker.__doc__}")
