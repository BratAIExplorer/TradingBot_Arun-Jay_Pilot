"""
Trade Parameter Integration Module
Integrates parameter capture with kickstart.py trade execution.

Handles:
1. Open trades cache (track BUY trades until SELL)
2. Entry parameter capture (at BUY time)
3. Exit parameter capture (at SELL time)
4. Database storage with all 40+ fields

Principles: Plan → Test → Deploy → Verify → Document
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
import threading

logger = logging.getLogger("trade_parameter_integration")


class OpenTradesCache:
    """
    Thread-safe cache for tracking open trades.
    Stores entry parameters and timestamp until trade exits.
    """

    def __init__(self):
        """Initialize cache with thread safety"""
        self._lock = threading.Lock()
        self._trades: Dict[str, Dict[str, Any]] = {}

    def store_entry(self, symbol: str, entry_params: Dict[str, Any], entry_time: datetime):
        """Store entry parameters for a newly opened trade"""
        with self._lock:
            self._trades[symbol] = {
                'entry_params': entry_params,
                'entry_time': entry_time,
                'stored_at': datetime.now()
            }
            logger.info(f"Cached entry for {symbol}")

    def get_entry(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve entry parameters for a trade"""
        with self._lock:
            if symbol in self._trades:
                return self._trades[symbol]
            return None

    def remove_entry(self, symbol: str):
        """Remove entry from cache (after SELL)"""
        with self._lock:
            if symbol in self._trades:
                del self._trades[symbol]
                logger.info(f"Removed {symbol} from cache")

    def get_all_open(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently open trades"""
        with self._lock:
            return self._trades.copy()

    def cleanup_stale(self, max_age_hours: int = 24):
        """Remove stale entries (shouldn't happen in normal operation)"""
        with self._lock:
            now = datetime.now()
            stale_symbols = [
                sym for sym, data in self._trades.items()
                if (now - data['stored_at']).total_seconds() > (max_age_hours * 3600)
            ]

            for symbol in stale_symbols:
                logger.warning(f"Cleaning up stale entry: {symbol}")
                del self._trades[symbol]

            return stale_symbols


# Global cache instance
open_trades_cache = OpenTradesCache()


def integrate_entry_capture(
    db,
    parameter_capture,
    symbol: str,
    exchange: str,
    qty: int,
    entry_price: float,
    rsi_value: float,
    atr: float,
    adx: float,
    macd_val: float,
    macd_signal: float,
    macd_hist: float,
    side: str  # 'BUY' or 'buy'
) -> Optional[int]:
    """
    Capture and store entry parameters for a BUY trade.

    This replaces the simple db.insert_trade() call in kickstart.py with
    a comprehensive parameter capture.

    Args:
        db: Database instance
        parameter_capture: ParameterCapture instance
        symbol: Stock symbol
        exchange: Exchange (NSE, BSE, etc.)
        qty: Quantity
        entry_price: Price at entry
        rsi_value: RSI value at entry
        atr: ATR at entry
        adx: ADX at entry
        macd_val: MACD value
        macd_signal: MACD signal
        macd_hist: MACD histogram
        side: BUY or buy

    Returns:
        Trade ID from database, or None if failed
    """
    try:
        now = datetime.now()

        # Step 1: Capture all entry parameters
        entry_params = parameter_capture.get_all_parameters_for_buy(
            symbol=symbol,
            exchange=exchange,
            qty=qty,
            entry_price=entry_price,
            rsi_value=rsi_value,
            atr=atr,
            adx=adx,
            macd_val=macd_val,
            macd_signal=macd_signal,
            macd_hist=macd_hist
        )

        # Step 2: Store entry in database (trades table - existing behavior)
        # This is STILL needed for backward compatibility and analytics
        trade_id = db.insert_trade(
            symbol=symbol,
            exchange=exchange,
            action=side.upper(),
            quantity=qty,
            price=round(entry_price, 2),
            strategy="RSI",
            reason=f"RSI={rsi_value:.1f}",
            broker="mstock",
            rsi=rsi_value,
            atr=atr,
            adx=adx,
            macd_val=macd_val,
            macd_signal=macd_signal,
            macd_hist=macd_hist
        )

        # Step 3: Cache entry parameters for later retrieval at SELL time
        if trade_id and trade_id > 0:
            open_trades_cache.store_entry(
                symbol=symbol,
                entry_params=entry_params,
                entry_time=now
            )

            logger.info(
                f"Entry captured for {symbol}: "
                f"ID={trade_id}, Qty={qty}, Price={entry_price}, "
                f"Regime={entry_params.get('entry_market_regime')}"
            )

        return trade_id if trade_id and trade_id > 0 else None

    except Exception as e:
        logger.error(f"Error capturing entry parameters: {e}")
        return None


def integrate_exit_capture(
    db,
    parameter_capture,
    symbol: str,
    exit_price: float,
    exit_reason: str,  # 'Profit Target Hit', 'Stop-Loss Triggered', etc.
    pnl: float,
    pnl_pct: float
) -> Optional[int]:
    """
    Capture and store exit parameters for a SELL trade.

    This should be called after a SELL trade completes to capture
    all exit-time parameters.

    Args:
        db: Database instance
        parameter_capture: ParameterCapture instance
        symbol: Stock symbol
        exit_price: Price at exit
        exit_reason: Why we exited ('Profit Target Hit', 'Stop-Loss', etc.)
        pnl: Profit/loss amount
        pnl_pct: Profit/loss percentage

    Returns:
        Analysis record ID, or None if failed
    """
    try:
        # Step 1: Retrieve cached entry data
        cached_entry = open_trades_cache.get_entry(symbol)
        if not cached_entry:
            logger.warning(f"No cached entry found for {symbol}, using fallback")
            entry_time = datetime.now()
        else:
            entry_time = cached_entry['entry_time']
            entry_params = cached_entry['entry_params']

        # Step 2: Capture exit parameters
        exit_params = parameter_capture.get_all_parameters_for_sell(
            symbol=symbol,
            exit_price=exit_price,
            exit_reason=exit_reason,
            entry_time=entry_time,
            pnl=pnl,
            pnl_pct=pnl_pct
        )

        # Step 3: Combine entry + exit parameters
        full_params = {}
        if cached_entry:
            full_params.update(entry_params)
        full_params.update(exit_params)

        # Step 4: Store in trade_analysis table (NEW)
        # This provides the comprehensive 40+ field record for AI analysis
        if hasattr(db, 'analytics_db'):
            analysis_id = db.analytics_db.insert_trade_analysis(
                symbol=symbol,
                timestamp=entry_time.isoformat(),
                action='SELL',
                **full_params
            )

            logger.info(
                f"Exit captured for {symbol}: "
                f"Reason={exit_reason}, P&L={pnl_pct:.2f}%, "
                f"Duration={full_params.get('hold_duration_minutes', 0)}min"
            )

            # Step 5: Clean up cache
            open_trades_cache.remove_entry(symbol)

            return analysis_id
        else:
            logger.warning("analytics_db not available on database object")
            return None

    except Exception as e:
        logger.error(f"Error capturing exit parameters: {e}")
        return None


def get_open_trades_summary() -> str:
    """Get human-readable summary of open trades"""
    open_trades = open_trades_cache.get_all_open()

    if not open_trades:
        return "No open trades"

    summary_lines = [f"Open trades: {len(open_trades)}"]
    for symbol, data in open_trades.items():
        entry_time = data['entry_time']
        hold_minutes = (datetime.now() - entry_time).total_seconds() / 60
        regime = data['entry_params'].get('entry_market_regime', 'Unknown')
        summary_lines.append(f"  {symbol}: {hold_minutes:.0f}min, Regime={regime}")

    return "\n".join(summary_lines)


# ============================================================================
# INTEGRATION EXAMPLES (Show how to use in kickstart.py)
# ============================================================================

def example_buy_integration():
    """
    Example of how to modify safe_place_order_when_open() in kickstart.py

    BEFORE (current code at line 1986):
    ```python
    trade_id = db.insert_trade(
        symbol=symbol,
        exchange=exchange,
        action=side.upper(),
        quantity=qty,
        ... # other fields
    )
    ```

    AFTER (with parameter capture):
    ```python
    from trade_parameter_integration import integrate_entry_capture
    from parameter_capture import ParameterCapture

    # At the top of the function/module, initialize once:
    # parameter_capture = ParameterCapture(market_fetcher=market_context_fetcher)

    trade_id = integrate_entry_capture(
        db=db,
        parameter_capture=parameter_capture,
        symbol=symbol,
        exchange=exchange,
        qty=qty,
        entry_price=current_price,
        rsi_value=rsi,
        atr=atr,
        adx=adx,
        macd_val=macd_val,
        macd_signal=macd_signal,
        macd_hist=macd_hist,
        side=side
    )
    ```
    """
    pass


def example_sell_integration():
    """
    Example of how to call integrate_exit_capture() when SELL happens

    This would be called in the code that handles stop-loss, profit-target,
    or manual exit scenarios.

    EXAMPLE (pseudocode):
    ```python
    from trade_parameter_integration import integrate_exit_capture

    # When profit target is hit:
    integrate_exit_capture(
        db=db,
        parameter_capture=parameter_capture,
        symbol="INFY",
        exit_price=1925.50,
        exit_reason="Profit Target Hit",
        pnl=75.00,
        pnl_pct=4.05
    )

    # When stop-loss is triggered:
    integrate_exit_capture(
        db=db,
        parameter_capture=parameter_capture,
        symbol="INFY",
        exit_price=1800.00,
        exit_reason="Stop-Loss Triggered",
        pnl=-50.00,
        pnl_pct=-2.70
    )

    # When manually exited:
    integrate_exit_capture(
        db=db,
        parameter_capture=parameter_capture,
        symbol="INFY",
        exit_price=1850.00,
        exit_reason="Manual Exit",
        pnl=0.00,
        pnl_pct=0.00
    )
    ```
    """
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(__doc__)
    print("\nSee example_buy_integration() and example_sell_integration() for usage")
    print("Full integration requires modifying kickstart.py to call these functions")
